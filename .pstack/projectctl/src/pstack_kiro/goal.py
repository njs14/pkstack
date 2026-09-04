"""Deterministic state for the current-session ``/verified-goal`` skill."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pstack_kiro.features import find_verifiable_feature
from pstack_kiro.models import CommandSpec, GoalState, SpecArtifactDigest
from pstack_kiro.paths import WorkspacePathError, ensure_tree_no_symlinks, workspace_path
from pstack_kiro.runner import (
    CommandRejected,
    display_command,
    enforce_verification_policy,
    parse_command,
    run_command,
)

try:
    import fcntl
except ImportError:  # pragma: no cover - project currently targets macOS/Linux
    fcntl = None  # type: ignore[assignment]

STATE_DIRECTORY = Path(".pstack/state")
STATE_FILE = "goal.json"
SCHEMA_VERSION = 2
DEFAULT_MAX_ATTEMPTS = 4
_SPEC_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
SPEC_BRIDGE_SCHEMA_VERSION = 1
MAX_SPEC_BRIDGE_BYTES = 16 * 1024
MAX_SPEC_ARTIFACT_BYTES = 1024 * 1024
_SPEC_SHARED_ARTIFACTS = ("design.md", "tasks.md")
_SPEC_INTENT_ARTIFACTS = ("requirements.md", "bugfix.md")


class GoalError(RuntimeError):
    """Raised when a goal transition is invalid or state is corrupt."""


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise GoalError(f"spec verification bridge contains duplicate key {key!r}")
        value[key] = item
    return value


def _spec_directory(root: Path, spec: str) -> Path:
    if not _SPEC_NAME.fullmatch(spec):
        raise GoalError("spec name must not contain path separators or traversal")
    try:
        directory = ensure_tree_no_symlinks(root, Path(".kiro") / "specs" / spec)
    except WorkspacePathError as exc:
        raise GoalError(str(exc)) from exc
    if not directory.is_dir():
        raise GoalError(f"Kiro spec {spec!r} does not exist at {directory}")
    return directory


def _read_bounded_spec_file(path: Path, *, label: str, limit: int) -> bytes:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise GoalError(f"cannot inspect {label} at {path}: {exc}") from exc
    if not path.is_file():
        raise GoalError(f"{label} is not a regular file: {path}")
    if size > limit:
        raise GoalError(f"{label} exceeds the {limit}-byte limit: {path}")
    try:
        with path.open("rb") as handle:
            data = handle.read(limit + 1)
    except OSError as exc:
        raise GoalError(f"cannot read {label} at {path}: {exc}") from exc
    if len(data) > limit:
        raise GoalError(f"{label} exceeds the {limit}-byte limit: {path}")
    return data


def inspect_native_spec(root: Path, spec: str) -> dict[str, Any]:
    """Validate the native artifact boundary without pretending to own Spec planning."""

    directory = _spec_directory(root.resolve(), spec)
    present_intent = [name for name in _SPEC_INTENT_ARTIFACTS if (directory / name).is_file()]
    if len(present_intent) != 1:
        raise GoalError(
            f"Kiro spec {spec!r} must contain exactly one of requirements.md or bugfix.md"
        )
    artifacts = [present_intent[0], *_SPEC_SHARED_ARTIFACTS]
    artifact_sha256: dict[str, str] = {}
    for name in artifacts:
        path = directory / name
        if not path.is_file():
            raise GoalError(f"Kiro spec {spec!r} is incomplete; missing {name}")
        raw = _read_bounded_spec_file(
            path,
            label=f"Kiro spec artifact {name}",
            limit=MAX_SPEC_ARTIFACT_BYTES,
        )
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise GoalError(f"Kiro spec artifact is not valid UTF-8 at {path}: {exc}") from exc
        if not text.strip():
            raise GoalError(f"Kiro spec artifact must be non-empty: {path}")
        artifact_sha256[name] = hashlib.sha256(raw).hexdigest()
    return {
        "spec": spec,
        "kind": "feature" if present_intent[0] == "requirements.md" else "bugfix",
        "directory": str(directory),
        "artifacts": artifacts,
        "artifact_sha256": artifact_sha256,
    }


def _load_spec_bridge(root: Path, spec: str) -> tuple[dict[str, Any], Path, dict[str, Any], bytes]:
    native = inspect_native_spec(root, spec)
    directory = Path(native["directory"])
    bridge = directory / "pk-stack-verification.json"
    if not bridge.is_file():
        raise GoalError(f"spec {spec!r} has no executable bridge at {bridge}")
    raw = _read_bounded_spec_file(
        bridge,
        label="spec verification bridge",
        limit=MAX_SPEC_BRIDGE_BYTES,
    )
    try:
        payload = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoalError(f"invalid spec verification bridge at {bridge}: {exc}") from exc
    if not isinstance(payload, dict):
        raise GoalError(f"invalid spec verification bridge at {bridge}: expected an object")
    keys = set(payload)
    if (
        payload.get("schema_version") != SPEC_BRIDGE_SCHEMA_VERSION
        or type(payload.get("schema_version")) is not int
    ):
        raise GoalError(
            f"invalid spec verification bridge at {bridge}: expected schema_version "
            f"{SPEC_BRIDGE_SCHEMA_VERSION}"
        )
    if keys not in (
        {"schema_version", "feature"},
        {"schema_version", "command"},
    ):
        raise GoalError(
            f"invalid spec verification bridge at {bridge}: use exactly one of feature or command"
        )
    return payload, bridge, native, raw


def _resolve_spec_contract(root: Path, spec: str) -> CommandSpec:
    payload, bridge, native, bridge_raw = _load_spec_bridge(root, spec)
    try:
        feature = payload.get("feature")
        if feature is not None:
            if type(feature) is not str:
                raise TypeError("feature must be a string")
            item = find_verifiable_feature(root, feature)
            assert item.command is not None
            argv = item.command
        else:
            argv = parse_command(payload["command"])
    except (KeyError, TypeError, ValueError) as exc:
        raise GoalError(f"invalid spec verification bridge at {bridge}: {exc}") from exc
    intent = "requirements.md" if native["kind"] == "feature" else "bugfix.md"
    snapshot = (
        SpecArtifactDigest(
            path=(Path(".kiro") / "specs" / spec / intent).as_posix(),
            sha256=native["artifact_sha256"][intent],
        ),
        SpecArtifactDigest(
            path=(Path(".kiro") / "specs" / spec / "design.md").as_posix(),
            sha256=native["artifact_sha256"]["design.md"],
        ),
        SpecArtifactDigest(
            path=(Path(".kiro") / "specs" / spec / "pk-stack-verification.json").as_posix(),
            sha256=hashlib.sha256(bridge_raw).hexdigest(),
        ),
    )
    return CommandSpec(
        argv=argv,
        display=display_command(argv),
        source="spec",
        feature=feature,
        spec=spec,
        spec_artifacts=snapshot,
    )


def _assert_spec_snapshot(root: Path, contract: CommandSpec) -> None:
    """Reject native acceptance/design/bridge drift without hashing mutable tasks."""

    assert contract.spec is not None
    native = inspect_native_spec(root, contract.spec)
    expected_intent = "requirements.md" if native["kind"] == "feature" else "bugfix.md"
    expected_paths = {
        (Path(".kiro") / "specs" / contract.spec / expected_intent).as_posix(),
        (Path(".kiro") / "specs" / contract.spec / "design.md").as_posix(),
        (Path(".kiro") / "specs" / contract.spec / "pk-stack-verification.json").as_posix(),
    }
    actual_paths = {item.path for item in contract.spec_artifacts}
    if len(actual_paths) != len(contract.spec_artifacts) or actual_paths != expected_paths:
        raise GoalError("stored spec snapshot does not name its intent, design, and bridge exactly")
    for item in contract.spec_artifacts:
        relative = Path(item.path)
        limit = (
            MAX_SPEC_BRIDGE_BYTES
            if relative.name == "pk-stack-verification.json"
            else MAX_SPEC_ARTIFACT_BYTES
        )
        try:
            path = workspace_path(root, relative)
        except WorkspacePathError as exc:
            raise GoalError(str(exc)) from exc
        raw = _read_bounded_spec_file(
            path,
            label=f"bound Kiro spec artifact {relative.name}",
            limit=limit,
        )
        if hashlib.sha256(raw).hexdigest() != item.sha256:
            raise GoalError(f"bound Kiro spec artifact changed after goal start: {item.path}")


def bind_spec_contract(
    root: Path,
    spec: str,
    *,
    feature: str | None = None,
    command: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Bind native Spec artifacts to one reviewed executable contract."""

    native = inspect_native_spec(root, spec)
    supplied = sum(value is not None for value in (feature, command))
    if supplied != 1:
        raise GoalError("provide exactly one of --feature or --command")
    if feature is not None:
        item = find_verifiable_feature(root, feature)
        assert item.command is not None
        argv = item.command
        payload: dict[str, Any] = {
            "schema_version": SPEC_BRIDGE_SCHEMA_VERSION,
            "feature": feature,
        }
    else:
        assert command is not None
        argv = parse_command(command)
        enforce_verification_policy(argv, root=root.resolve())
        payload = {
            "schema_version": SPEC_BRIDGE_SCHEMA_VERSION,
            "command": list(argv),
        }
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    bridge = Path(native["directory"]) / "pk-stack-verification.json"
    changed = True
    if bridge.exists():
        existing = _read_bounded_spec_file(
            bridge,
            label="spec verification bridge",
            limit=MAX_SPEC_BRIDGE_BYTES,
        )
        if existing == data:
            changed = False
        elif not overwrite:
            raise GoalError(
                "refusing to replace existing spec verification bridge without "
                f"--overwrite: {bridge}"
            )
    if changed:
        descriptor, temporary = tempfile.mkstemp(
            prefix=".pk-stack-verification.", dir=bridge.parent
        )
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o644)
            if overwrite:
                os.replace(temporary, bridge)
            else:
                try:
                    os.link(temporary, bridge)
                except FileExistsError as exc:
                    raise GoalError(
                        f"spec verification bridge appeared during binding: {bridge}"
                    ) from exc
                Path(temporary).unlink()
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
    contract = _resolve_spec_contract(root, spec)
    return {
        "ok": True,
        **native,
        "bridge": str(bridge),
        "changed": changed,
        "contract": contract.to_dict(),
    }


def _now() -> str:
    return datetime.now(UTC).isoformat()


class GoalStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        try:
            self.directory = workspace_path(self.root, STATE_DIRECTORY)
            self.path = workspace_path(self.root, STATE_DIRECTORY / STATE_FILE)
            self.lock_path = workspace_path(self.root, STATE_DIRECTORY / ".goal.lock")
            self.verification_lock_path = workspace_path(
                self.root,
                STATE_DIRECTORY / ".goal.verify.lock",
            )
        except WorkspacePathError as exc:
            raise GoalError(str(exc)) from exc

    @contextmanager
    def locked(self) -> Iterator[None]:
        with self._lock(self.lock_path):
            yield

    @contextmanager
    def verification_locked(self) -> Iterator[None]:
        """Serialize verifier runs without blocking read-only goal status."""

        with self._lock(self.verification_lock_path):
            yield

    @contextmanager
    def _lock(self, path: Path) -> Iterator[None]:
        if fcntl is None:
            raise GoalError("goal-state locking requires POSIX fcntl")
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.directory.chmod(0o700)
        with path.open("a+", encoding="utf-8") as lock:
            path.chmod(0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def load(self, *, check_command_policy: bool = True) -> GoalState | None:
        if not self.path.exists():
            return None
        try:
            serialized = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise GoalError(f"goal state is corrupt at {self.path}: {exc}") from exc
        try:
            payload = json.loads(serialized)
            state = GoalState.from_dict(payload)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise GoalError(f"goal state is corrupt at {self.path}: {exc}") from exc
        if state.schema_version != SCHEMA_VERSION:
            raise GoalError(
                f"unsupported goal state schema {state.schema_version}; expected {SCHEMA_VERSION}"
            )
        _validate_state(state, root=self.root, check_command_policy=check_command_policy)
        return state

    def save(self, state: GoalState) -> None:
        try:
            payload = state.to_dict()
            validated = GoalState.from_dict(payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise GoalError(f"refusing to save invalid goal state: {exc}") from exc
        if validated.schema_version != SCHEMA_VERSION:
            raise GoalError(
                f"unsupported goal state schema {validated.schema_version}; "
                f"expected {SCHEMA_VERSION}"
            )
        _validate_state(validated, root=self.root)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.directory.chmod(0o700)
        descriptor, temporary = tempfile.mkstemp(
            prefix=".goal.", suffix=".json", dir=self.directory, text=True
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(validated.to_dict(), handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, self.path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)


def resolve_contract(
    root: Path,
    *,
    command: str | None = None,
    feature: str | None = None,
    spec: str | None = None,
) -> CommandSpec:
    """Resolve the strongest executable acceptance contract available.

    Priority is explicit command, matching feature map, then an explicit active
    Kiro spec bridge.  The bridge is deliberately a small JSON file because a
    prose acceptance criterion is not itself executable proof.
    """

    supplied = sum(value is not None for value in (command, feature, spec))
    if supplied > 1:
        raise GoalError("provide exactly one of --command, --feature, or --spec")
    if command:
        argv = parse_command(command)
        return CommandSpec(argv=argv, display=display_command(argv), source="explicit")
    if feature:
        item = find_verifiable_feature(root, feature)
        assert item.command is not None  # guaranteed by find_verifiable_feature
        return CommandSpec(
            argv=item.command,
            display=display_command(item.command),
            source="feature-map",
            feature=feature,
        )
    if spec:
        return _resolve_spec_contract(root, spec)
    raise GoalError("no executable acceptance contract: provide --command, --feature, or --spec")


def start_goal(
    root: Path,
    objective: str,
    *,
    command: str | None = None,
    feature: str | None = None,
    spec: str | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> GoalState:
    if not objective.strip():
        raise GoalError("objective must be non-empty")
    if not 1 <= max_attempts <= 20:
        raise GoalError("max_attempts must be between 1 and 20")
    contract = resolve_contract(root, command=command, feature=feature, spec=spec)
    enforce_verification_policy(contract.argv, root=root.resolve())
    store = GoalStore(root)
    with store.locked():
        existing = store.load()
        if existing:
            raise GoalError(
                f"goal {existing.goal_id} already exists with status {existing.status}; "
                "clear it explicitly before starting another"
            )
        timestamp = _now()
        state = GoalState(
            schema_version=SCHEMA_VERSION,
            goal_id=str(uuid.uuid4()),
            objective=objective.strip(),
            status="active",
            contract=contract,
            contract_digest=_contract_digest(contract),
            attempt_count=0,
            max_attempts=max_attempts,
            created_at=timestamp,
            updated_at=timestamp,
        )
        store.save(state)
        return state


def get_goal(root: Path) -> GoalState:
    store = GoalStore(root)
    state = store.load()
    if state is None:
        raise GoalError("no goal state exists")
    return state


def verify_goal(
    root: Path,
    *,
    timeout_seconds: float = 300.0,
    output_limit: int = 64_000,
) -> GoalState:
    store = GoalStore(root)
    with store.verification_locked():
        with store.locked():
            state = store.load()
            if state is None:
                raise GoalError("no goal state exists")
            if state.status == "passed":
                raise GoalError("goal already passed; verification is complete")
            if state.status == "exhausted":
                raise GoalError("goal is exhausted; resume it with additional attempts first")
            if state.contract.source == "spec":
                _assert_spec_snapshot(store.root, state.contract)
            goal_id = state.goal_id
            contract = state.contract
            prior_state = state.to_dict()

        result = run_command(
            contract,
            root=store.root,
            timeout_seconds=timeout_seconds,
            output_limit=output_limit,
        )

        with store.locked():
            state = store.load()
            if state is None or state.goal_id != goal_id:
                raise GoalError("goal changed while its verifier was running; result was discarded")
            if state.to_dict() != prior_state:
                raise GoalError("goal state changed during verification; result was discarded")
            if state.contract.source == "spec":
                _assert_spec_snapshot(store.root, state.contract)
            state.attempt_count += 1
            state.last_result = result
            state.history.append(result)
            if result.passed:
                state.status = "passed"
            elif state.attempt_count >= state.max_attempts:
                state.status = "exhausted"
            else:
                state.status = "active"
            state.updated_at = _now()
            store.save(state)
            return state


def resume_goal(
    root: Path,
    *,
    add_attempts: int = 0,
    max_attempts: int | None = None,
) -> GoalState:
    if add_attempts < 0:
        raise GoalError("add_attempts cannot be negative")
    store = GoalStore(root)
    with store.locked():
        state = store.load()
        if state is None:
            raise GoalError("no goal state exists")
        if state.status == "passed":
            raise GoalError("a passed goal cannot be resumed")
        proposed = state.max_attempts + add_attempts
        if max_attempts is not None:
            proposed = max_attempts
        if not 1 <= proposed <= 20:
            raise GoalError("max attempts after resume must be between 1 and 20")
        if proposed < state.attempt_count:
            raise GoalError("max attempts cannot be lower than attempts already used")
        if state.status == "active" and proposed == state.attempt_count:
            raise GoalError("max attempts must leave an active goal at least one remaining attempt")
        if state.status == "exhausted" and proposed <= state.attempt_count:
            raise GoalError("an exhausted goal requires at least one additional attempt")
        state.max_attempts = proposed
        state.status = "active"
        state.updated_at = _now()
        store.save(state)
        return state


def clear_goal(root: Path, *, force: bool = False) -> dict[str, Any]:
    store = GoalStore(root)
    with store.locked():
        state = store.load(check_command_policy=not force)
        if state is None:
            return {"cleared": False, "reason": "no goal state exists"}
        if state.status == "active" and not force:
            raise GoalError("refusing to clear an active goal without --force")
        store.clear()
        return {"cleared": True, "goal_id": state.goal_id, "status": state.status}


def tripwire(root: Path) -> dict[str, Any]:
    """Return advisory stop-hook status; never acts as a control-flow blocker."""

    store = GoalStore(root)
    state = store.load()
    if state is None:
        return {"active": False, "message": "No verified goal is active."}
    if state.status == "active":
        remaining = state.max_attempts - state.attempt_count
        return {
            "active": True,
            "goal_id": state.goal_id,
            "message": (
                "Verified goal is still active. Do not claim success; continue the same-session "
                f"repair loop ({remaining} attempt(s) remain)."
            ),
        }
    return {
        "active": False,
        "goal_id": state.goal_id,
        "status": state.status,
        "message": f"Verified goal reached terminal status: {state.status}.",
    }


def state_payload(state: GoalState) -> dict[str, Any]:
    payload = state.to_dict()
    payload["remaining_attempts"] = state.max_attempts - state.attempt_count
    return payload


def _contract_digest(contract: CommandSpec) -> str:
    payload = json.dumps(contract.to_dict(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _validate_state(
    state: GoalState,
    *,
    root: Path,
    check_command_policy: bool = True,
) -> None:
    """Reject impossible or accidentally weakened state before any transition."""

    if state.status not in {"active", "passed", "exhausted"}:
        raise GoalError(f"invalid goal status: {state.status!r}")
    if not state.goal_id or not state.objective.strip():
        raise GoalError("goal id and objective must be non-empty")
    try:
        uuid.UUID(state.goal_id)
    except ValueError as exc:
        raise GoalError("goal id must be a UUID") from exc
    if not 1 <= state.max_attempts <= 20:
        raise GoalError("stored max_attempts must be between 1 and 20")
    if not 0 <= state.attempt_count <= state.max_attempts:
        raise GoalError("stored attempt_count is outside its allowed budget")
    if len(state.history) != state.attempt_count:
        raise GoalError("stored attempt_count does not match verification history")
    expected_last = state.history[-1] if state.history else None
    if state.last_result != expected_last:
        raise GoalError("stored last_result does not match verification history")
    if state.contract_digest != _contract_digest(state.contract):
        raise GoalError("stored verifier contract digest does not match its command")
    if not state.contract.argv or state.contract.display != display_command(state.contract.argv):
        raise GoalError("stored verifier command is empty or has inconsistent display text")
    if check_command_policy:
        try:
            enforce_verification_policy(state.contract.argv, root=root)
        except CommandRejected as exc:
            raise GoalError(f"stored verifier command is rejected: {exc}") from exc
    if state.contract.source not in {"explicit", "feature-map", "spec"}:
        raise GoalError(f"invalid verifier contract source: {state.contract.source!r}")
    if state.contract.source == "feature-map" and not state.contract.feature:
        raise GoalError("feature-map verifier state is missing its feature provenance")
    if state.contract.source == "spec":
        if not state.contract.spec:
            raise GoalError("spec verifier state is missing its spec provenance")
        if not state.contract.spec_artifacts:
            raise GoalError("spec verifier state is missing its bound artifact snapshot")
        base = Path(".kiro") / "specs" / state.contract.spec
        paths = {item.path for item in state.contract.spec_artifacts}
        shared = {
            (base / "design.md").as_posix(),
            (base / "pk-stack-verification.json").as_posix(),
        }
        intents = {
            (base / "requirements.md").as_posix(),
            (base / "bugfix.md").as_posix(),
        }
        if (
            len(paths) != len(state.contract.spec_artifacts)
            or len(paths) != 3
            or not shared <= paths
            or len(paths & intents) != 1
            or paths - shared - intents
        ):
            raise GoalError("spec verifier state has an invalid artifact snapshot")
        for item in state.contract.spec_artifacts:
            if not _SHA256.fullmatch(item.sha256):
                raise GoalError("spec verifier state contains an invalid artifact SHA-256")
    elif state.contract.spec_artifacts:
        raise GoalError("non-spec verifier state must not contain spec artifact snapshots")
    if any(
        result.passed != (result.exit_code == 0 and not result.timed_out)
        for result in state.history
    ):
        raise GoalError("stored verification result has inconsistent pass and exit status")
    if any(result.passed for result in state.history[:-1]):
        raise GoalError("stored history contains a pass before its final attempt")
    if state.status == "active" and (
        state.attempt_count >= state.max_attempts
        or (state.last_result and state.last_result.passed)
    ):
        raise GoalError("active goal state contradicts its attempt evidence")
    if state.status == "passed" and (not state.last_result or not state.last_result.passed):
        raise GoalError("passed goal state lacks passing verifier evidence")
    if state.status == "exhausted" and (
        state.attempt_count != state.max_attempts
        or state.last_result is None
        or state.last_result.passed
    ):
        raise GoalError("exhausted goal state contradicts its attempt evidence")
