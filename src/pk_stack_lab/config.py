"""Narrow configuration and endpoint/ownership validation for the lab."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

HOST_ENDPOINT = "http://127.0.0.1:4566"
TASK_ENDPOINT = "http://floci:4566"
REGION = "us-east-1"
FLOCI_IMAGE = (
    "floci/floci:2.0.1@sha256:4e451c39c7bb88e3cd4f87e8fc0c25d5b47695a51185d521e2241fa00486e8eb"
)
NETWORK = "pk-stack-lab-net"
PROJECT = "pk-stack-lab"
BUILD_INPUTS = (
    "Dockerfile",
    "requirements-runtime.txt",
    "src/pk_stack_lab/__init__.py",
    "src/pk_stack_lab/aws.py",
    "src/pk_stack_lab/config.py",
    "src/pk_stack_lab/runtime.py",
)
_RUN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,30}[a-z0-9])?$")


class SafetyError(ValueError):
    """A caller attempted to use an endpoint or resource outside lab policy."""


def validate_host_endpoint(value: str) -> str:
    """Accept exactly the intentional loopback emulator endpoint."""
    parsed = urlparse(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.port != 4566
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise SafetyError("endpoint must be exactly http://127.0.0.1:4566")
    return HOST_ENDPOINT


def validate_task_endpoint(value: str) -> str:
    """Task containers may only reach Floci over the dedicated Docker network."""
    parsed = urlparse(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "floci"
        or parsed.port != 4566
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise SafetyError("task endpoint must be exactly http://floci:4566")
    return TASK_ENDPOINT


def safe_name(value: str) -> str:
    if not _RUN.fullmatch(value):
        raise SafetyError("run identifier must be 1-32 lowercase alphanumeric/hyphen characters")
    return value


def state_dir(root: Path) -> Path:
    return root / ".lab-state"


def source_digest(root: Path) -> str:
    """Hash the exact Docker build-input set with unambiguous path framing."""
    digest = hashlib.sha256()
    for relative in BUILD_INPUTS:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise SafetyError(f"declared build input is missing or unsafe: {relative}")
        data = path.read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


@dataclass(frozen=True)
class RunState:
    run_id: str
    queue: str
    dlq: str
    table: str
    bucket: str
    cluster: str
    api_service: str
    worker_service: str
    api_family: str
    worker_family: str
    # The values below are populated by `up`.  The benign defaults preserve
    # deterministic unit fixtures while a real claim always supplies opaque
    # identity and the exact daemon tuple.
    claim_id: str = "local-test-claim"
    docker_context: str = ""
    docker_socket: str = ""
    docker_daemon_id: str = ""
    source_digest: str = ""
    api_image_id: str = ""
    worker_image_id: str = ""
    api_task_definition_arn: str = ""
    worker_task_definition_arn: str = ""

    @property
    def prefix(self) -> str:
        return f"pklab-{self.run_id}"

    def names(self) -> list[str]:
        return [
            self.queue,
            self.dlq,
            self.table,
            self.bucket,
            self.cluster,
            self.api_service,
            self.worker_service,
            self.api_family,
            self.worker_family,
        ]

    def to_dict(self) -> dict[str, str]:
        return self.__dict__.copy()

    @classmethod
    def create(
        cls,
        run_id: str | None = None,
        *,
        claim_id: str = "local-test-claim",
        docker_context: str = "",
        docker_socket: str = "",
        docker_daemon_id: str = "",
        source_digest: str = "",
        api_image_id: str = "",
        worker_image_id: str = "",
        api_task_definition_arn: str = "",
        worker_task_definition_arn: str = "",
    ) -> RunState:
        value = safe_name(run_id or f"r{secrets.token_hex(5)}")
        prefix = f"pklab-{value}"
        # S3 disallows upper case and has a 63 character limit.
        return cls(
            run_id=value,
            queue=f"{prefix}-exports",
            dlq=f"{prefix}-exports-dlq",
            table=f"{prefix}-exports",
            bucket=f"{prefix}-results",
            cluster=f"{prefix}-cluster",
            api_service=f"{prefix}-api",
            worker_service=f"{prefix}-worker",
            api_family=f"{prefix}-api",
            worker_family=f"{prefix}-worker",
            claim_id=claim_id,
            docker_context=docker_context,
            docker_socket=docker_socket,
            docker_daemon_id=docker_daemon_id,
            source_digest=source_digest,
            api_image_id=api_image_id,
            worker_image_id=worker_image_id,
            api_task_definition_arn=api_task_definition_arn,
            worker_task_definition_arn=worker_task_definition_arn,
        )


def state_path(root: Path) -> Path:
    return state_dir(root) / "run.json"


def _direct_state_directory(root: Path, *, create: bool) -> Path:
    directory = state_dir(root)
    if directory.is_symlink():
        raise SafetyError(".lab-state must not be a symlink")
    if directory.exists():
        if not directory.is_dir():
            raise SafetyError(".lab-state must be a directory")
    elif create:
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            # A concurrent claimer may have created it between exists() and
            # mkdir().  Re-check it below through the no-follow directory FD.
            if directory.is_symlink() or not directory.is_dir():
                raise SafetyError(".lab-state must be a direct directory")
    return directory


def _open_state_directory(root: Path, *, create: bool) -> int:
    directory = _direct_state_directory(root, create=create)
    if not directory.exists():
        raise SafetyError(".lab-state is absent")
    flags = os.O_RDONLY | os.O_DIRECTORY
    if not hasattr(os, "O_NOFOLLOW"):
        raise SafetyError("platform does not support no-follow state operations")
    try:
        descriptor = os.open(directory, flags | os.O_NOFOLLOW)
    except OSError as exc:
        raise SafetyError("unable to open direct .lab-state directory") from exc
    if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise SafetyError(".lab-state must be a direct directory")
    return descriptor


def state_directory_absent(root: Path) -> bool:
    """Return true only for an actually absent direct state directory."""
    directory = state_dir(root)
    if directory.is_symlink():
        raise SafetyError(".lab-state must not be a symlink")
    if directory.exists() and not directory.is_dir():
        raise SafetyError(".lab-state must be a directory")
    return not directory.exists()


def _direct_state_path(root: Path, *, require_present: bool) -> Path:
    directory = _direct_state_directory(root, create=False)
    path = directory / "run.json"
    if path.is_symlink():
        raise SafetyError(".lab-state/run.json must not be a symlink")
    if path.exists() and not path.is_file():
        raise SafetyError(".lab-state/run.json must be a regular file")
    if require_present and not path.exists():
        raise SafetyError("no valid lab state; run labctl up first")
    return path


def _canonical_state(raw: object) -> RunState:
    if not isinstance(raw, dict) or set(raw) != set(RunState.__dataclass_fields__):
        raise SafetyError("state manifest must have exactly the canonical fields")
    if not all(type(value) is str for value in raw.values()):
        raise SafetyError("state manifest fields must all be strings")
    try:
        state = RunState(**raw)
        expected = RunState.create(
            state.run_id,
            claim_id=state.claim_id,
            docker_context=state.docker_context,
            docker_socket=state.docker_socket,
            docker_daemon_id=state.docker_daemon_id,
            source_digest=state.source_digest,
            api_image_id=state.api_image_id,
            worker_image_id=state.worker_image_id,
            api_task_definition_arn=state.api_task_definition_arn,
            worker_task_definition_arn=state.worker_task_definition_arn,
        )
    except (TypeError, SafetyError) as exc:
        raise SafetyError("state manifest has an invalid run identifier") from exc
    if state != expected:
        raise SafetyError("state manifest does not equal canonical run ownership")
    return state


def load_state(root: Path) -> RunState:
    _direct_state_path(root, require_present=True)
    directory = _open_state_directory(root, create=False)
    try:
        descriptor = os.open("run.json", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        try:
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.geteuid()
                or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) != 0o600
            ):
                raise SafetyError(".lab-state/run.json must be a direct regular file")
            with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
                descriptor = -1
                raw = json.loads(handle.read())
        finally:
            if descriptor != -1:
                os.close(descriptor)
        state = _canonical_state(raw)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SafetyError("no valid lab state; run labctl up first") from exc
    finally:
        os.close(directory)
    return state


def save_state(root: Path, state: RunState) -> None:
    if state != RunState.create(
        state.run_id,
        claim_id=state.claim_id,
        docker_context=state.docker_context,
        docker_socket=state.docker_socket,
        docker_daemon_id=state.docker_daemon_id,
        source_digest=state.source_digest,
        api_image_id=state.api_image_id,
        worker_image_id=state.worker_image_id,
        api_task_definition_arn=state.api_task_definition_arn,
        worker_task_definition_arn=state.worker_task_definition_arn,
    ):
        raise SafetyError("refusing noncanonical state write")
    directory = _open_state_directory(root, create=True)
    path = state_path(root)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise SafetyError(".lab-state/run.json must be a direct regular file")
    # Never truncate an established claim in place.  A same-directory
    # exclusive temporary plus fsync/replace makes a crash either retain the
    # old complete manifest or expose the new complete manifest.
    temporary = f".run.{secrets.token_hex(16)}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if not hasattr(os, "O_NOFOLLOW"):
        raise SafetyError("platform does not support no-follow state writes")
    descriptor = os.open(temporary, flags | os.O_NOFOLLOW, 0o600, dir_fd=directory)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise SafetyError(".lab-state/run.json must be a direct regular file")
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(json.dumps(state.to_dict(), sort_keys=True))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, "run.json", src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        if descriptor != -1:
            os.close(descriptor)
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass
        os.close(directory)


def claim_state(root: Path, state: RunState) -> None:
    """Atomically create the first canonical manifest; exactly one caller can win."""
    if state != RunState.create(
        state.run_id,
        claim_id=state.claim_id,
        docker_context=state.docker_context,
        docker_socket=state.docker_socket,
        docker_daemon_id=state.docker_daemon_id,
        source_digest=state.source_digest,
        api_image_id=state.api_image_id,
        worker_image_id=state.worker_image_id,
        api_task_definition_arn=state.api_task_definition_arn,
        worker_task_definition_arn=state.worker_task_definition_arn,
    ):
        raise SafetyError("refusing noncanonical state claim")
    directory = _open_state_directory(root, create=True)
    descriptor = -1
    try:
        entries = os.listdir(directory)
        if entries:
            raise SafetyError(".lab-state contains existing runtime artifacts")
        descriptor = os.open(
            "run.json",
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory,
        )
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise SafetyError(".lab-state/run.json must be a direct regular file")
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(json.dumps(state.to_dict(), sort_keys=True))
            handle.flush()
            os.fsync(handle.fileno())
        os.fsync(directory)
    except FileExistsError as exc:
        raise SafetyError(".lab-state already has a manifest") from exc
    except OSError as exc:
        raise SafetyError("unable to claim .lab-state manifest") from exc
    finally:
        if descriptor != -1:
            os.close(descriptor)
        os.close(directory)


def remove_state_manifest(root: Path) -> None:
    """Remove only the direct regular manifest after successful lifecycle cleanup."""
    directory = _open_state_directory(root, create=False)
    try:
        info = os.stat("run.json", dir_fd=directory, follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode):
            raise SafetyError(".lab-state/run.json must be a direct regular file")
        os.unlink("run.json", dir_fd=directory)
    except OSError as exc:
        raise SafetyError("unable to remove direct state manifest") from exc
    finally:
        os.close(directory)


def ownership_tags(state: RunState) -> list[dict[str, str]]:
    return [
        {"Key": "pk-stack-lab:managed", "Value": "true"},
        {"Key": "pk-stack-lab:project", "Value": PROJECT},
        {"Key": "pk-stack-lab:run", "Value": state.run_id},
        {"Key": "pk-stack-lab:claim", "Value": state.claim_id},
    ]


def ownership_hash(state: RunState) -> str:
    return hashlib.sha256(json.dumps(state.to_dict(), sort_keys=True).encode()).hexdigest()


def runtime_env() -> dict[str, str]:
    """Only explicit dummy local settings, never AWS SDK ambient resolution."""
    return {
        "PK_STACK_LAB_ENDPOINT": validate_task_endpoint(
            os.environ.get("PK_STACK_LAB_ENDPOINT", TASK_ENDPOINT)
        ),
        "PK_STACK_LAB_REGION": REGION,
    }
