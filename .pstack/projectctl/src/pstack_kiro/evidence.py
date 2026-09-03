"""Bounded append-only evidence trails for visible PK-Stack decisions.

The ledger records public requirements, evidence, decisions, artifacts, and
verdicts.  It intentionally has no field for private reasoning or transcripts.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any

from pstack_kiro.models import EvidenceEvent, EvidenceReference, EvidenceVerdict
from pstack_kiro.paths import WorkspacePathError, workspace_path

try:
    import fcntl
except ImportError:  # pragma: no cover - PK-Stack currently targets macOS/Linux
    fcntl = None  # type: ignore[assignment]

EVIDENCE_SCHEMA_VERSION = 1
DEFAULT_EVIDENCE_DIRECTORY = Path(".pstack/state/evidence")
COMMITTED_EVIDENCE_DIRECTORY = Path("Wiki/evidence")
EVIDENCE_FILE_NAME = "decision-log.jsonl"
MAX_EVIDENCE_FILE_BYTES = 4 * 1024 * 1024
MAX_EVIDENCE_EVENTS = 2_048
MAX_EVIDENCE_LINE_BYTES = 24 * 1024
MAX_EVIDENCE_FIELD_BYTES = 4_096
MAX_REFERENCE_PATH_BYTES = 1_024
MAX_HASHED_ARTIFACT_BYTES = 32 * 1024 * 1024

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")
_VERDICTS = {"VERIFIED", "NOT VERIFIED", "INCONCLUSIVE"}
_EVENT_KEYS = {
    "schema_version",
    "sequence",
    "timestamp",
    "requirement",
    "evidence",
    "decision",
    "artifact",
    "verification",
    "verdict",
}
_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}=*\b", re.IGNORECASE),
    re.compile(
        r"\b(?:api[_-]?key|access[_-]?token|secret|password|passwd)\b"
        r"\s*[:=]\s*[\"']?[^\s\"']{8,}",
        re.IGNORECASE,
    ),
    re.compile(r"https?://[^/\s:@]+:[^/\s@]+@", re.IGNORECASE),
)


class EvidenceError(RuntimeError):
    """Raised when an evidence trail is unsafe, malformed, or inconsistent."""


def _canonical_relative_path(path: Path) -> str:
    return PurePosixPath(*path.parts).as_posix()


def _evidence_path(
    root: Path,
    slug: str,
    *,
    committed: bool,
    target: Path | None,
) -> tuple[Path, str]:
    if not _SLUG.fullmatch(slug):
        raise EvidenceError("evidence slug must contain lowercase letters, numbers, and hyphens")
    if committed and target is None:
        raise EvidenceError("--committed requires an explicit --target under Wiki/evidence")
    if target is not None and not committed:
        raise EvidenceError("--target is accepted only with the explicit --committed flag")

    expected = (
        COMMITTED_EVIDENCE_DIRECTORY / slug / EVIDENCE_FILE_NAME
        if committed
        else DEFAULT_EVIDENCE_DIRECTORY / slug / EVIDENCE_FILE_NAME
    )
    relative = target if target is not None else expected
    if relative.is_absolute() or _canonical_relative_path(relative) != str(relative):
        raise EvidenceError("evidence target must be a canonical workspace-relative path")
    if committed and relative != expected:
        raise EvidenceError(f"committed evidence target must be exactly {expected.as_posix()}")
    try:
        resolved = workspace_path(root, relative)
    except WorkspacePathError as exc:
        raise EvidenceError(str(exc)) from exc
    return resolved, expected.as_posix()


def _lock_path(root: Path, evidence_relative: str) -> Path:
    digest = hashlib.sha256(evidence_relative.encode("utf-8")).hexdigest()
    try:
        return workspace_path(root, Path(".pstack/state/evidence-locks") / f"{digest}.lock")
    except WorkspacePathError as exc:
        raise EvidenceError(str(exc)) from exc


@contextmanager
def _locked(root: Path, evidence_relative: str) -> Iterator[None]:
    if fcntl is None:
        raise EvidenceError("evidence locking requires POSIX fcntl")
    path = _lock_path(root, evidence_relative)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    with path.open("a+", encoding="utf-8") as handle:
        path.chmod(0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _bounded_text(value: object, *, field: str, limit: int = MAX_EVIDENCE_FIELD_BYTES) -> str:
    if type(value) is not str:
        raise EvidenceError(f"evidence {field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise EvidenceError(f"evidence {field} must be non-empty")
    if len(normalized.encode("utf-8")) > limit:
        raise EvidenceError(f"evidence {field} exceeds the {limit}-byte limit")
    if "\x00" in normalized:
        raise EvidenceError(f"evidence {field} contains a NUL byte")
    if any(pattern.search(normalized) for pattern in _SECRET_PATTERNS):
        raise EvidenceError(
            f"evidence {field} appears to contain secret material; record a redacted pointer"
        )
    return normalized


def _parse_timestamp(value: object) -> datetime:
    text = _bounded_text(value, field="timestamp", limit=64)
    if not _TIMESTAMP.fullmatch(text):
        raise EvidenceError("evidence timestamp must be canonical UTC ISO 8601")
    try:
        return datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise EvidenceError("evidence timestamp must be canonical UTC ISO 8601") from exc


def _canonical_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise EvidenceError("evidence timestamp source must be timezone-aware")
    utc = value.astimezone(UTC)
    return utc.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _reference_from_object(root: Path, value: object) -> EvidenceReference | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise EvidenceError("evidence artifact must be null or an exact path/sha256 object")
    raw_path = _bounded_text(value["path"], field="artifact path", limit=MAX_REFERENCE_PATH_BYTES)
    candidate = Path(raw_path)
    if (
        candidate.is_absolute()
        or "\\" in raw_path
        or ".." in candidate.parts
        or _canonical_relative_path(candidate) != raw_path
    ):
        raise EvidenceError("evidence artifact path must be canonical and workspace-relative")
    try:
        resolved = workspace_path(root, candidate)
    except WorkspacePathError as exc:
        raise EvidenceError(str(exc)) from exc
    if not resolved.is_file():
        raise EvidenceError(f"evidence artifact does not exist as a regular file: {raw_path}")

    raw_sha = value["sha256"]
    if raw_sha is not None and (type(raw_sha) is not str or not _SHA256.fullmatch(raw_sha)):
        raise EvidenceError("evidence artifact sha256 must be null or 64 lowercase hex characters")
    if raw_sha is not None:
        size = resolved.stat().st_size
        if size > MAX_HASHED_ARTIFACT_BYTES:
            raise EvidenceError(
                f"evidence artifact exceeds the {MAX_HASHED_ARTIFACT_BYTES}-byte hashing limit"
            )
        digest = hashlib.sha256()
        total = 0
        with resolved.open("rb") as handle:
            while chunk := handle.read(64 * 1024):
                total += len(chunk)
                if total > MAX_HASHED_ARTIFACT_BYTES:
                    raise EvidenceError("evidence artifact grew beyond the bounded hashing limit")
                digest.update(chunk)
        if digest.hexdigest() != raw_sha:
            raise EvidenceError(f"evidence artifact sha256 mismatch: {raw_path}")
    return EvidenceReference(path=raw_path, sha256=raw_sha)


def _event_from_object(root: Path, value: object) -> EvidenceEvent:
    if not isinstance(value, dict) or set(value) != _EVENT_KEYS:
        raise EvidenceError("evidence event does not match the exact schema")
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != EVIDENCE_SCHEMA_VERSION
    ):
        raise EvidenceError(f"evidence schema_version must be exactly {EVIDENCE_SCHEMA_VERSION}")
    if type(value["sequence"]) is not int or value["sequence"] < 1:
        raise EvidenceError("evidence sequence must be a positive integer")
    timestamp = _parse_timestamp(value["timestamp"])
    verdict = value["verdict"]
    if type(verdict) is not str or verdict not in _VERDICTS:
        raise EvidenceError("evidence verdict must be VERIFIED, NOT VERIFIED, or INCONCLUSIVE")
    event = EvidenceEvent(
        schema_version=EVIDENCE_SCHEMA_VERSION,
        sequence=value["sequence"],
        timestamp=_canonical_timestamp(timestamp),
        requirement=_bounded_text(value["requirement"], field="requirement"),
        evidence=_bounded_text(value["evidence"], field="evidence"),
        decision=_bounded_text(value["decision"], field="decision"),
        artifact=_reference_from_object(root, value["artifact"]),
        verification=_bounded_text(value["verification"], field="verification"),
        verdict=verdict,
    )
    return event


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            # Key names are untrusted evidence bytes too.  Keep corruption errors
            # generic so a planted secret cannot be reflected through the CLI.
            raise EvidenceError("evidence JSON contains a duplicate key")
        value[key] = item
    return value


def _canonical_line(event: EvidenceEvent) -> bytes:
    return (
        json.dumps(
            event.to_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _read_bounded(path: Path, *, allow_missing: bool) -> bytes:
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        if allow_missing:
            return b""
        raise EvidenceError(f"evidence trail does not exist: {path}") from None
    if not path.is_file():
        raise EvidenceError(f"evidence trail is not a regular file: {path}")
    if size == 0:
        raise EvidenceError("evidence trail contains no events")
    if size > MAX_EVIDENCE_FILE_BYTES:
        raise EvidenceError(f"evidence trail exceeds the {MAX_EVIDENCE_FILE_BYTES}-byte limit")
    with path.open("rb") as handle:
        data = handle.read(MAX_EVIDENCE_FILE_BYTES + 1)
    if len(data) > MAX_EVIDENCE_FILE_BYTES:
        raise EvidenceError(f"evidence trail exceeds the {MAX_EVIDENCE_FILE_BYTES}-byte limit")
    return data


def _parse_events(root: Path, data: bytes) -> list[EvidenceEvent]:
    if not data:
        return []
    if not data.endswith(b"\n"):
        raise EvidenceError("evidence JSONL must end with a newline")
    lines = data[:-1].split(b"\n")
    if len(lines) > MAX_EVIDENCE_EVENTS:
        raise EvidenceError(f"evidence trail exceeds the {MAX_EVIDENCE_EVENTS}-event limit")

    events: list[EvidenceEvent] = []
    previous_time: datetime | None = None
    for expected_sequence, raw_line in enumerate(lines, 1):
        if not raw_line:
            raise EvidenceError("evidence JSONL contains a blank line")
        if len(raw_line) + 1 > MAX_EVIDENCE_LINE_BYTES:
            raise EvidenceError(
                f"evidence event {expected_sequence} exceeds the "
                f"{MAX_EVIDENCE_LINE_BYTES}-byte limit"
            )
        try:
            line = raw_line.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise EvidenceError("evidence trail is not valid UTF-8") from exc
        try:
            value = json.loads(line, object_pairs_hook=_object_without_duplicate_keys)
        except (json.JSONDecodeError, EvidenceError) as exc:
            raise EvidenceError(f"invalid evidence event {expected_sequence}: {exc}") from exc
        event = _event_from_object(root, value)
        if event.sequence != expected_sequence:
            raise EvidenceError(
                f"evidence sequence must be contiguous: expected {expected_sequence}, "
                f"found {event.sequence}"
            )
        timestamp = _parse_timestamp(event.timestamp)
        if previous_time is not None and timestamp <= previous_time:
            raise EvidenceError("evidence timestamps must increase monotonically")
        previous_time = timestamp
        if raw_line + b"\n" != _canonical_line(event):
            raise EvidenceError(f"evidence event {expected_sequence} is not canonical JSONL")
        events.append(event)
    return events


def _atomic_replace(path: Path, data: bytes, *, committed: bool) -> None:
    directory_mode = 0o755 if committed else 0o700
    file_mode = 0o644 if committed else 0o600
    path.parent.mkdir(parents=True, exist_ok=True, mode=directory_mode)
    if not committed:
        path.parent.chmod(directory_mode)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, file_mode)
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _audit_payload(
    *,
    relative: str,
    committed: bool,
    data: bytes,
    events: list[EvidenceEvent],
) -> dict[str, Any]:
    verdict_counts = {verdict: 0 for verdict in sorted(_VERDICTS)}
    for event in events:
        verdict_counts[event.verdict] += 1
    return {
        "ok": True,
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "path": relative,
        "committed": committed,
        "event_count": len(events),
        "next_sequence": len(events) + 1,
        "verdict_counts": verdict_counts,
        "file_bytes": len(data),
        "file_sha256": hashlib.sha256(data).hexdigest(),
    }


def append_evidence(
    root: Path,
    slug: str,
    *,
    requirement: str,
    evidence: str,
    decision: str,
    verification: str,
    verdict: EvidenceVerdict,
    artifact: Path | None = None,
    artifact_sha256: str | None = None,
    committed: bool = False,
    target: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Append one validated event under an exclusive lock and durable replace."""

    project_root = root.resolve()
    path, relative = _evidence_path(
        project_root,
        slug,
        committed=committed,
        target=target,
    )
    if artifact is None and artifact_sha256 is not None:
        raise EvidenceError("--artifact-sha256 requires --artifact")
    artifact_value = (
        None if artifact is None else {"path": str(artifact), "sha256": artifact_sha256}
    )
    timestamp_source = now or datetime.now(UTC)
    if timestamp_source.tzinfo is None:
        raise EvidenceError("evidence timestamp source must be timezone-aware")
    _event_from_object(
        project_root,
        {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "sequence": 1,
            "timestamp": _canonical_timestamp(timestamp_source),
            "requirement": requirement,
            "evidence": evidence,
            "decision": decision,
            "artifact": artifact_value,
            "verification": verification,
            "verdict": verdict,
        },
    )

    with _locked(project_root, relative):
        path, relative = _evidence_path(
            project_root,
            slug,
            committed=committed,
            target=target,
        )
        data = _read_bounded(path, allow_missing=True)
        events = _parse_events(project_root, data)
        if len(events) >= MAX_EVIDENCE_EVENTS:
            raise EvidenceError(f"evidence trail reached the {MAX_EVIDENCE_EVENTS}-event limit")

        if events:
            previous = _parse_timestamp(events[-1].timestamp)
            if timestamp_source.astimezone(UTC) <= previous:
                try:
                    timestamp_source = previous + timedelta(microseconds=1)
                except OverflowError as exc:
                    raise EvidenceError("evidence timestamp range is exhausted") from exc
        raw_event = {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "sequence": len(events) + 1,
            "timestamp": _canonical_timestamp(timestamp_source),
            "requirement": requirement,
            "evidence": evidence,
            "decision": decision,
            "artifact": artifact_value,
            "verification": verification,
            "verdict": verdict,
        }
        event = _event_from_object(project_root, raw_event)
        line = _canonical_line(event)
        if len(line) > MAX_EVIDENCE_LINE_BYTES:
            raise EvidenceError(f"evidence event exceeds the {MAX_EVIDENCE_LINE_BYTES}-byte limit")
        updated = data + line
        if len(updated) > MAX_EVIDENCE_FILE_BYTES:
            raise EvidenceError(
                f"evidence trail would exceed the {MAX_EVIDENCE_FILE_BYTES}-byte limit"
            )
        parsed = _parse_events(project_root, updated)
        _atomic_replace(path, updated, committed=committed)

    return {
        **_audit_payload(
            relative=relative,
            committed=committed,
            data=updated,
            events=parsed,
        ),
        "event": event.to_dict(),
    }


def audit_evidence(
    root: Path,
    slug: str,
    *,
    committed: bool = False,
    target: Path | None = None,
) -> dict[str, Any]:
    """Validate every event, reference, hash, sequence, timestamp, and bound."""

    project_root = root.resolve()
    path, relative = _evidence_path(
        project_root,
        slug,
        committed=committed,
        target=target,
    )
    data = _read_bounded(path, allow_missing=False)
    events = _parse_events(project_root, data)
    return _audit_payload(
        relative=relative,
        committed=committed,
        data=data,
        events=events,
    )
