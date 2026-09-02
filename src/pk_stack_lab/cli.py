"""The intentionally small, deterministic `labctl` control surface."""

from __future__ import annotations

import argparse
import codecs
import errno
import fcntl
import json
import os
import re
import secrets
import selectors
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from botocore.exceptions import ClientError

from . import __version__
from .aws import client
from .config import (
    DISCARD_TEARDOWN_PHASES,
    FLOCI_IMAGE,
    HOST_ENDPOINT,
    NETWORK,
    PROJECT,
    REACHABLE_TEARDOWN_PHASES,
    REGION,
    TASK_ENDPOINT,
    ArtifactEvent,
    AwsTeardownTargets,
    BucketTarget,
    DockerTeardownTargets,
    ImageTarget,
    NamedArnTarget,
    QueueTarget,
    RunState,
    SafetyError,
    TeardownPlan,
    activate_deployment,
    append_artifact_events,
    artifact_ledger_hash,
    claim_state,
    complete_teardown_phase,
    compose_digest,
    install_teardown_plan,
    load_state,
    next_artifact_sequence,
    ownership_hash,
    ownership_tags,
    remove_state_manifest,
    set_bucket_create_intent,
    source_digest,
    state_dir,
    state_directory_absent,
    transition_teardown_to_discard,
    validate_host_endpoint,
)

_LAUNCH_ROOT = os.environ.get("PK_STACK_LAB_ROOT")
if _LAUNCH_ROOT:
    _candidate_root = Path(_LAUNCH_ROOT)
    ROOT = _candidate_root.resolve(strict=True)
    if (
        not _candidate_root.is_absolute()
        or _candidate_root != ROOT
        or _candidate_root.is_symlink()
        or Path.cwd().resolve() != ROOT
    ):
        raise RuntimeError("PK_STACK_LAB_ROOT must be the direct current repository directory")
else:
    ROOT = Path(__file__).resolve().parents[2]
MAX_READ = 8192
MAX_RESULT_BYTES = 4096
_READ_CHUNK_BYTES = 64 * 1024
_REAP_TIMEOUT_SECONDS = 1.0
_TASK_ID = re.compile(r"^[0-9a-f]{32}$")
_EXPORT_ID = re.compile(r"^e-[0-9a-f]{16}$")
_TASK_CONTAINER = re.compile(r"^floci-ecs-([0-9a-f]{32})-(api|worker)$")
_OUTER_LABELS = {
    "pk-stack-lab.managed": "true",
    "pk-stack-lab.component": "floci",
    "pk-stack-lab.version": "2.0.1",
    "pk-stack-lab.source": "compose",
}
_NETWORK_LABELS = {
    "pk-stack-lab.managed": "true",
    "pk-stack-lab.component": "network",
    "pk-stack-lab.source": "compose",
}
_BLOCKED_ENV_PREFIXES = ("COMPOSE_", "DOCKER_", "AWS_", "UV_")
_BLOCKED_ENV_NAMES = {
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
}
_BOUND_SOCKET: str | None = None
_LOCK_FILE = ".lab-lifecycle.lock"
_TRANSPORT_UNREACHABLE_ERRNOS = frozenset(
    code
    for name in (
        "ECONNABORTED",
        "ECONNREFUSED",
        "ECONNRESET",
        "EHOSTDOWN",
        "EHOSTUNREACH",
        "ENETDOWN",
        "ENETUNREACH",
        "ENOTCONN",
        "ETIMEDOUT",
    )
    if (code := getattr(errno, name, None)) is not None
)


class LabError(RuntimeError):
    """A controlled lifecycle failure suitable for machine-readable output."""


class _HealthTransportUnreachable(LabError):
    """The health endpoint failed with a specifically recognized transport error."""


class _RefuseHealthRedirects(HTTPRedirectHandler):
    """Keep an HTTP redirect from being mistaken for an unreachable final target."""

    def redirect_request(
        self,
        request: Request,
        _file_pointer: Any,
        code: int,
        _message: str,
        headers: Any,
        _new_url: str,
    ) -> None:
        raise HTTPError(request.full_url, code, "health redirect refused", headers, _file_pointer)


@contextmanager
def _lifecycle_lock() -> Any:
    """Serialize all control-surface commands against one direct repository lock."""
    path = ROOT / _LOCK_FILE
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise LabError("lifecycle lock must be a direct regular file")
    flags = os.O_RDWR | os.O_CREAT
    if not hasattr(os, "O_NOFOLLOW"):
        raise LabError("platform does not support no-follow lifecycle locking")
    try:
        descriptor = os.open(path, flags | os.O_NOFOLLOW, 0o600)
    except OSError as exc:
        raise LabError("unable to open lifecycle lock") from exc
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise LabError("lifecycle lock must be an owner-only direct regular file")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise LabError("another PK-Stack lifecycle command is already running") from exc
        yield
    finally:
        os.close(descriptor)


def _run(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int = 90,
    bind_socket: bool = True,
) -> str:
    clean = _clean_subprocess_env(env, bind_socket=bind_socket)
    try:
        process = subprocess.Popen(
            args,
            cwd=ROOT,
            env=clean,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as exc:
        raise LabError(f"command failed: {args[0]}") from exc

    stdout = bytearray()
    stderr_prefix = bytearray()
    stderr_truncated = False
    deadline = time.monotonic() + max(0.0, float(timeout))

    try:
        assert process.stdout is not None
        assert process.stderr is not None
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    _kill_process_group(process)
                    raise LabError(f"command failed: {args[0]}")
                events = selector.select(remaining)
                if not events:
                    if time.monotonic() < deadline:
                        continue
                    _kill_process_group(process)
                    raise LabError(f"command failed: {args[0]}")
                for key, _mask in events:
                    if key.data == "stdout":
                        read_size = min(_READ_CHUNK_BYTES, MAX_READ + 1 - len(stdout))
                    else:
                        read_size = _READ_CHUNK_BYTES
                    chunk = os.read(key.fd, read_size)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    if key.data == "stdout":
                        stdout.extend(chunk)
                        if len(stdout) > MAX_READ:
                            _kill_process_group(process)
                            raise LabError(f"command output exceeded {MAX_READ} bytes: {args[0]}")
                    else:
                        available = MAX_READ - len(stderr_prefix)
                        if available > 0:
                            stderr_prefix.extend(chunk[:available])
                        if len(chunk) > available:
                            stderr_truncated = True

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _kill_process_group(process)
            raise LabError(f"command failed: {args[0]}")
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            _kill_process_group(process)
            raise LabError(f"command failed: {args[0]}") from exc
    except LabError:
        raise
    except OSError as exc:
        _kill_process_group(process)
        raise LabError(f"command failed: {args[0]}") from exc
    finally:
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()

    stdout_text = _decode_command_bytes(bytes(stdout), args[0])
    if returncode:
        stderr_text = _decode_command_bytes(
            bytes(stderr_prefix), args[0], prefix_truncated=stderr_truncated
        )
        detail = "\n".join(part for part in (stdout_text, stderr_text) if part)
        raise LabError(f"command failed ({args[0]}): {_safe_text(detail)}")
    return stdout_text


def _kill_process_group(process: subprocess.Popen[bytes]) -> None:
    """Kill the isolated child group and reap its leader after a bounded-run failure."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=_REAP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except OSError:
            pass
        try:
            process.wait(timeout=_REAP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            # Preserve the bounded command failure rather than masking it with
            # a second cleanup timeout. The group has already received SIGKILL.
            pass


def _decode_command_bytes(value: bytes, command: str, *, prefix_truncated: bool = False) -> str:
    """Strictly decode complete output, or the complete characters in a bounded prefix."""
    decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
    try:
        return decoder.decode(value, final=not prefix_truncated)
    except UnicodeDecodeError as exc:
        raise LabError(f"command emitted invalid UTF-8: {command}") from exc


def _clean_subprocess_env(
    extra: dict[str, str] | None = None, *, bind_socket: bool = True
) -> dict[str, str]:
    """Return the small explicit environment used by every child process.

    We do not copy the parent environment, so neither a repository `.env` nor
    ambient Docker/Compose/AWS/proxy/uv configuration can redirect a command.
    Docker calls after a claim are pinned to the recorded Unix socket.
    """
    allowed = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "LANG", "LC_ALL", "LC_CTYPE", "TERM"}
    }
    if bind_socket and _BOUND_SOCKET:
        allowed["DOCKER_HOST"] = _BOUND_SOCKET
    for key, value in (extra or {}).items():
        if (key in _BLOCKED_ENV_NAMES or key.startswith(_BLOCKED_ENV_PREFIXES)) and not (
            key == "DOCKER_HOST"
            and isinstance(value, str)
            and value.startswith("unix:///")
            and ((_BOUND_SOCKET is None) or value == _BOUND_SOCKET)
        ):
            raise LabError("refusing ambient-sensitive subprocess environment")
        allowed[key] = value
    return allowed


def _safe_text(value: str) -> str:
    return " ".join(value.replace("\x00", "").split())[:1000]


def _is_missing(exc: ClientError, codes: set[str]) -> bool:
    return exc.response.get("Error", {}).get("Code") in codes


def _error_code(exc: ClientError) -> str:
    code = exc.response.get("Error", {}).get("Code")
    return code if isinstance(code, str) else ""


def _ecs_described_items(
    response: object,
    key: str,
    *,
    label: str,
    allow_missing: bool,
) -> list[Any]:
    """Parse one ECS describe response without treating service failures as absence."""
    if not isinstance(response, dict):
        raise LabError(f"{label} returned a malformed response")
    items = response.get(key, [])
    failures = response.get("failures", [])
    if not isinstance(items, list) or not isinstance(failures, list):
        raise LabError(f"{label} returned a malformed inventory")
    allowed_reasons = {"MISSING", "NOT_FOUND"} if allow_missing else set()
    for failure in failures:
        reason = failure.get("reason") if isinstance(failure, dict) else None
        if reason not in allowed_reasons:
            raise LabError(f"{label} returned an unexpected structured failure")
    if items and failures:
        raise LabError(f"{label} returned both objects and structured failures")
    return items


def _docker_identity() -> tuple[str, str, str]:
    """Discover an actual Unix Docker socket and immutable daemon identity."""
    context = _run(["docker", "context", "show"], bind_socket=False).strip()
    raw = _run(
        ["docker", "context", "inspect", context, "--format", "{{json .Endpoints.docker.Host}}"],
        bind_socket=False,
    ).strip()
    try:
        endpoint = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LabError("Docker context did not return a JSON socket endpoint") from exc
    if not isinstance(endpoint, str) or not endpoint.startswith("unix://"):
        raise LabError("active Docker context must use a unix socket")
    path = endpoint.removeprefix("unix://")
    if not path.startswith("/") or not Path(path).exists():
        raise LabError("active Docker socket is missing")
    resolved = Path(path).resolve(strict=True)
    if not stat.S_ISSOCK(resolved.stat().st_mode):
        raise LabError("active Docker endpoint is not a Unix socket")
    daemon_id = _run(
        ["docker", "--context", context, "info", "--format", "{{.ID}}"],
        bind_socket=False,
    ).strip()
    if not daemon_id or len(daemon_id) > 256:
        raise LabError("Docker daemon did not provide a valid identity")
    return context, f"unix://{resolved}", daemon_id


def _bind_daemon(state: RunState) -> str:
    """Bind all later Docker/Compose operations to the claim's exact daemon."""
    global _BOUND_SOCKET
    context, socket, daemon_id = _docker_identity()
    if (
        state.docker_context != context
        or state.docker_socket != socket
        or state.docker_daemon_id != daemon_id
    ):
        raise LabError("Docker context, socket, or daemon identity drifted from the run claim")
    _BOUND_SOCKET = socket
    return socket


def _floci_data_path(*, root: Path | None = None, create: bool) -> Path:
    """Return the sole repository-local persistent path mounted into Floci."""
    root = ROOT if root is None else root
    state = state_dir(root)
    if state.is_symlink():
        raise LabError(".lab-state must be a direct directory")
    if state.exists():
        if not state.is_dir():
            raise LabError(".lab-state must be a direct directory")
    elif create:
        state.mkdir(mode=0o700)
    data = state / "floci-data"
    if data.is_symlink():
        raise LabError(".lab-state/floci-data must be a direct directory")
    if data.exists():
        if not data.is_dir():
            raise LabError(".lab-state/floci-data must be a direct directory")
    elif create:
        data.mkdir(mode=0o700)
    return data


def _remove_floci_data_path(*, root: Path | None = None) -> None:
    root = ROOT if root is None else root
    state = state_dir(root)
    data = _floci_data_path(root=root, create=False)
    if data.is_symlink() or (data.exists() and (not data.is_dir() or data.parent != state)):
        raise LabError("refusing unsafe Floci data cleanup path")
    if not data.exists():
        return
    # `data` is the exact validated repository-local bind mount, never a glob or external path.
    shutil.rmtree(data)


def _remove_empty_state_dir(*, root: Path | None = None) -> None:
    """Best-effort removal of exactly an empty direct state directory.

    The manifest is intentionally removed immediately before this call.  A
    non-empty directory is never traversed or deleted; it remains as evidence
    for an operator rather than widening cleanup scope.
    """
    root = ROOT if root is None else root
    state = state_dir(root)
    if state.is_symlink() or (state.exists() and not state.is_dir()):
        raise LabError("refusing unsafe .lab-state cleanup path")
    if state.exists():
        try:
            state.rmdir()
        except OSError:
            pass


def _docker_json(args: list[str]) -> Any:
    raw = _run(args).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LabError("Docker returned malformed JSON") from exc


def _label_subset(value: Any, allowed: set[str]) -> dict[str, str]:
    if not isinstance(value, dict):
        raise LabError("Docker labels were not an object")
    return {key: value[key] for key in sorted(allowed) if isinstance(value.get(key), str)}


def _exact_docker_object_exists(kind: str, name: str) -> bool:
    if kind == "container":
        args = ["docker", "ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}}"]
    elif kind == "network":
        args = ["docker", "network", "ls", "--filter", f"name=^{name}$", "--format", "{{.Name}}"]
    else:
        raise LabError("unsupported Docker object kind")
    values = [line.strip() for line in _run(args).splitlines() if line.strip()]
    if not values:
        return False
    if values == [name]:
        return True
    raise LabError("Docker exact-name probe returned unexpected objects")


def _inspect_labels(kind: str, name: str, *, missing_ok: bool = False) -> dict[str, str] | None:
    if missing_ok and not _exact_docker_object_exists(kind, name):
        return None
    template = "{{json .Config.Labels}}" if kind == "container" else "{{json .Labels}}"
    value = _docker_json(["docker", kind, "inspect", "--format", template, name])
    if not isinstance(value, dict):
        raise LabError("Docker labels were not an object")
    return {
        str(key): str(item)
        for key, item in value.items()
        if isinstance(key, str) and isinstance(item, str)
    }


def _expected_outer_labels(state: RunState) -> tuple[dict[str, str], dict[str, str]]:
    return (
        {**_OUTER_LABELS, "pk-stack-lab.claim": state.claim_id},
        {**_NETWORK_LABELS, "pk-stack-lab.claim": state.claim_id},
    )


def _assert_outer_ownership(
    state: RunState | None = None, *, require_absent: bool = False, require_present: bool = False
) -> None:
    container = _inspect_labels("container", "pk-stack-lab-floci", missing_ok=True)
    network = _inspect_labels("network", NETWORK, missing_ok=True)
    task_names = [
        line.strip()
        for line in _run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                "label=io.floci.service=ecs",
                "--format",
                "{{.Names}}",
            ]
        ).splitlines()
        if line.strip()
    ]
    if require_absent:
        if container is not None or network is not None or task_names:
            raise LabError("refusing startup while a Floci container, network, or ECS task exists")
        return
    if state is None:
        raise LabError("outer ownership validation requires the canonical run claim")
    if require_present and (container is None or network is None):
        raise LabError("current run Floci container or network is missing")
    expected_container, expected_network = _expected_outer_labels(state)
    if container is not None and any(
        container.get(key) != value for key, value in expected_container.items()
    ):
        raise LabError("refusing a Floci container outside the current run claim")
    if network is not None and any(
        network.get(key) != value for key, value in expected_network.items()
    ):
        raise LabError("refusing a Floci network outside the current run claim")
    # This singleton lab never permits another claim's ECS task containers to
    # share its daemon-level execution boundary.  This check also applies when
    # a resumed teardown has already removed the outer Floci objects.
    _validate_claim_task_container_names(state, task_names)


def _bind_claimed_outer(state: RunState) -> str:
    """Bind the claimed daemon and require both outer objects for live commands."""
    socket_endpoint = _bind_daemon(state)
    _assert_outer_ownership(state, require_present=True)
    return socket_endpoint


def _compose_image(socket_endpoint: str) -> str:
    values = [
        line.strip()
        for line in _compose(socket_endpoint, "config", "--images").splitlines()
        if line.strip()
    ]
    if values != [FLOCI_IMAGE]:
        raise LabError("Compose does not resolve to the required immutable Floci image")
    return values[0]


def _inspect_floci_image() -> str:
    """Return the exact pinned Floci image ID or fail closed."""
    raw = _run(
        [
            "docker",
            "image",
            "inspect",
            "--format",
            '{"repo_digests":{{json .RepoDigests}},"image_id":{{json .Id}}}',
            FLOCI_IMAGE,
        ]
    ).strip()
    try:
        evidence = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LabError("Docker returned malformed pinned Floci image evidence") from exc
    repository_and_tag, manifest_digest = FLOCI_IMAGE.rsplit("@", 1)
    repository = repository_and_tag.rsplit(":", 1)[0]
    expected_repo_digest = f"{repository}@{manifest_digest}"
    if (
        not isinstance(evidence, dict)
        or set(evidence) != {"repo_digests", "image_id"}
        or not isinstance(evidence["repo_digests"], list)
        or any(not isinstance(value, str) for value in evidence["repo_digests"])
        or expected_repo_digest not in evidence["repo_digests"]
        or not isinstance(evidence["image_id"], str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", evidence["image_id"])
    ):
        raise LabError("Docker did not prove the exact pinned Floci image identity")
    return evidence["image_id"]


def _ensure_floci_image() -> str:
    """Resolve the shared immutable Floci dependency before creating a run claim."""
    try:
        return _inspect_floci_image()
    except LabError as exc:
        expected_missing = (
            f"command failed (docker): Error response from daemon: No such image: {FLOCI_IMAGE}"
        )
        if str(exc) != expected_missing:
            raise
    # A pull mutates only Docker's shared content-addressed cache. It cannot
    # create a Compose project object and the digest pin prevents tag drift.
    _run(["docker", "image", "pull", "--quiet", FLOCI_IMAGE], timeout=600)
    return _inspect_floci_image()


def _compose_env(socket_endpoint: str, claim_id: str) -> dict[str, str]:
    return {
        "DOCKER_HOST": socket_endpoint,
        "PK_STACK_LAB_DOCKER_SOCKET": socket_endpoint.removeprefix("unix://"),
        # `compose config` used by doctor must also work before `up` creates
        # disposable state.  `up` creates and validates this exact path before
        # any compose mutation.
        "PK_STACK_LAB_FLOCI_DATA": str(state_dir(ROOT) / "floci-data"),
        "PK_STACK_LAB_CLAIM": claim_id,
    }


def _compose(
    socket_endpoint: str,
    *args: str,
    timeout: int = 120,
    claim_id: str = "preflight",
) -> str:
    return _run(
        [
            "docker",
            "compose",
            "--env-file",
            os.devnull,
            "--project-directory",
            str(ROOT),
            "-p",
            PROJECT,
            "-f",
            str(ROOT / "compose.yaml"),
            *args,
        ],
        env=_compose_env(socket_endpoint, claim_id),
        timeout=timeout,
    )


def _http_json(
    url: str,
    *,
    method: str = "GET",
    body: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body, separators=(",", ":")).encode() if body is not None else None
    request = Request(
        url,
        method=method,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with build_opener(ProxyHandler({}), _RefuseHealthRedirects()).open(
            request, timeout=5
        ) as response:
            payload = response.read(MAX_READ)
            return response.status, json.loads(payload)
    except HTTPError as exc:
        # HTTP errors are responses, not evidence of transport unreachability.
        raise LabError("bounded HTTP probe failed") from exc
    except json.JSONDecodeError as exc:
        raise LabError("bounded HTTP probe failed") from exc
    except (URLError, OSError) as exc:
        if _is_transport_unreachable(exc):
            raise _HealthTransportUnreachable("bounded HTTP probe failed") from exc
        raise LabError("bounded HTTP probe failed") from exc


def _wait_health() -> None:
    for _ in range(30):
        try:
            status, body = _http_json(f"{HOST_ENDPOINT}/_floci/health")
            if status < 500 and isinstance(body, dict):
                return
        except LabError:
            pass
        time.sleep(1)
    raise LabError("Floci health endpoint did not become reachable")


def _wait_health_once() -> None:
    status, body = _http_json(f"{HOST_ENDPOINT}/_floci/health")
    if status >= 500 or not isinstance(body, dict):
        raise LabError("Floci health endpoint is not currently reachable")


def _is_transport_unreachable(error: BaseException) -> bool:
    """Recognize only typed endpoint transport failures, never response failures."""
    if isinstance(error, HTTPError):
        # HTTPError is also a URLError, but it proves that an HTTP endpoint answered.
        return False
    if isinstance(error, URLError):
        reason = error.reason
        return isinstance(reason, BaseException) and _is_transport_unreachable(reason)
    if isinstance(error, (TimeoutError, socket.gaierror, ConnectionError)):
        return True
    if isinstance(error, OSError) and error.errno in _TRANSPORT_UNREACHABLE_ERRNOS:
        return True
    cause = error.__cause__
    return cause is not None and _is_transport_unreachable(cause)


def _require_unreachable_health_endpoint() -> None:
    """Authorize destructive discard only after a typed transport failure."""
    try:
        _wait_health_once()
    except _HealthTransportUnreachable:
        return
    except Exception as exc:
        raise LabError(
            "Floci health probe failed without proving transport unreachability; "
            "refuse control-plane discard"
        ) from exc
    raise LabError("Floci health endpoint responded; refuse control-plane discard")


def _tags_dict(state: RunState) -> dict[str, str]:
    return {tag["Key"]: tag["Value"] for tag in ownership_tags(state)}


def _ecs_tags(state: RunState) -> list[dict[str, str]]:
    return [{"key": tag["Key"], "value": tag["Value"]} for tag in ownership_tags(state)]


def _owned(state: RunState, tags: list[dict[str, str]] | None) -> bool:
    got = {
        entry.get("Key", entry.get("key")): entry.get("Value", entry.get("value"))
        for entry in tags or []
    }
    return got == _tags_dict(state)


def _provision(state: RunState) -> tuple[RunState, dict[str, str]]:
    sqs, ddb, s3, ecs = (client(name) for name in ("sqs", "dynamodb", "s3", "ecs"))
    dlq_url = sqs.create_queue(QueueName=state.dlq, tags=_tags_dict(state))["QueueUrl"]
    dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=["QueueArn"])["Attributes"][
        "QueueArn"
    ]
    queue_url = sqs.create_queue(
        QueueName=state.queue,
        Attributes={
            "VisibilityTimeout": "8",
            "RedrivePolicy": json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "2"}),
        },
        tags=_tags_dict(state),
    )["QueueUrl"]
    ddb.create_table(
        TableName=state.table,
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
        Tags=ownership_tags(state),
    )
    ddb.get_waiter("table_exists").wait(
        TableName=state.table, WaiterConfig={"Delay": 1, "MaxAttempts": 30}
    )
    # S3 create and tagging are separate APIs.  Persist the one exact pending
    # create only after startup's complete collision scan and immediately
    # before the untagged resource can come into existence.
    state = set_bucket_create_intent(ROOT, state, active=True)
    s3.create_bucket(Bucket=state.bucket)
    s3.put_bucket_tagging(Bucket=state.bucket, Tagging={"TagSet": ownership_tags(state)})
    state = set_bucket_create_intent(ROOT, state, active=False)
    ecs.create_cluster(clusterName=state.cluster, tags=_ecs_tags(state))
    return state, {"queue_url": queue_url, "dlq_url": dlq_url}


def _assert_aws_targets_absent(state: RunState) -> None:
    """Inventory every deterministic AWS name before the first AWS mutation."""
    sqs, ddb, s3, ecs = (client(name) for name in ("sqs", "dynamodb", "s3", "ecs"))
    for name in (state.queue, state.dlq):
        try:
            sqs.get_queue_url(QueueName=name)
        except ClientError as exc:
            if _is_missing(exc, {"QueueDoesNotExist", "AWS.SimpleQueueService.NonExistentQueue"}):
                continue
            raise
        raise LabError(f"startup collision: SQS queue already exists: {name}")
    try:
        ddb.describe_table(TableName=state.table)
    except ClientError as exc:
        if not _is_missing(exc, {"ResourceNotFoundException"}):
            raise
    else:
        raise LabError(f"startup collision: DynamoDB table already exists: {state.table}")
    try:
        s3.head_bucket(Bucket=state.bucket)
    except ClientError as exc:
        if not _is_missing(exc, {"NoSuchBucket", "404", "NotFound"}):
            raise
    else:
        raise LabError(f"startup collision: S3 bucket already exists: {state.bucket}")
    cluster_result = ecs.describe_clusters(clusters=[state.cluster], include=["TAGS"])
    clusters = _ecs_described_items(
        cluster_result,
        "clusters",
        label="startup ECS cluster inventory",
        allow_missing=True,
    )
    if clusters:
        raise LabError(f"startup collision: ECS cluster already exists: {state.cluster}")
    try:
        service_result = ecs.describe_services(
            cluster=state.cluster,
            services=[state.api_service, state.worker_service],
            include=["TAGS"],
        )
    except ClientError as exc:
        if not _is_missing(exc, {"ClusterNotFoundException", "ServiceNotFoundException"}):
            raise
    else:
        services = _ecs_described_items(
            service_result,
            "services",
            label="startup ECS service inventory",
            allow_missing=True,
        )
        if services:
            raise LabError("startup collision: ECS service already exists")
    for family in (state.api_family, state.worker_family):
        for status in ("ACTIVE", "INACTIVE"):
            arns = _tokenized_items(
                ecs.list_task_definitions,
                "taskDefinitionArns",
                familyPrefix=family,
                status=status,
                sort="ASC",
                maxResults=100,
            )
            exact = [arn for arn in arns if f"task-definition/{family}:" in str(arn)]
            if exact:
                raise LabError(f"startup collision: ECS task-definition family exists: {family}")


def command_doctor(_: argparse.Namespace) -> dict[str, Any]:
    endpoint = validate_host_endpoint(HOST_ENDPOINT)
    required = {name: bool(shutil.which(name)) for name in ("docker", "uv")}
    if not all(required.values()):
        raise LabError("required tools are missing")
    context, socket_endpoint, daemon_id = _docker_identity()
    version = _run(["docker", "version", "--format", "{{json .Server.Version}}"])
    compose_image = _compose_image(socket_endpoint)
    return {
        "ok": True,
        "project": PROJECT,
        "lab_version": __version__,
        "endpoint": endpoint,
        "task_endpoint": TASK_ENDPOINT,
        "region": REGION,
        "floci_image": compose_image,
        "docker_socket": socket_endpoint,
        "docker_context": context,
        "docker_daemon_id": daemon_id,
        "docker_ready": bool(json.loads(version)),
        "required_tools": required,
    }


def command_up(args: argparse.Namespace) -> dict[str, Any]:
    try:
        existing = load_state(ROOT)
    except SafetyError:
        if not state_directory_absent(ROOT):
            raise LabError(
                "existing .lab-state is invalid; preserve it and resolve before starting"
            )
        existing = None
    if existing:
        raise LabError("existing lab state found; run labctl down before a new run")
    if not getattr(args, "acknowledge_docker_socket", False):
        raise LabError(
            "up requires --acknowledge-docker-socket (the Docker socket is root-equivalent)"
        )
    context, socket_endpoint, daemon_id = _docker_identity()
    global _BOUND_SOCKET
    _BOUND_SOCKET = socket_endpoint
    _assert_outer_ownership(require_absent=True)
    claimed_compose_sha256 = compose_digest(ROOT)
    _compose_image(socket_endpoint)
    _ensure_floci_image()
    if compose_digest(ROOT) != claimed_compose_sha256:
        raise LabError("Compose definition changed during pinned-image startup preflight")
    state = RunState.create(
        args.run_id,
        claim_id=secrets.token_hex(16),
        docker_context=context,
        docker_socket=socket_endpoint,
        docker_daemon_id=daemon_id,
        compose_sha256=claimed_compose_sha256,
    )
    # Persist before provisioning so `down` can recover any partially-created tagged resource.
    claim_state(ROOT, state)
    _floci_data_path(create=True)
    if compose_digest(ROOT) != state.compose_sha256:
        raise LabError("Compose definition changed after the startup claim")
    _compose(
        socket_endpoint,
        "up",
        "-d",
        "--wait",
        "--pull",
        "never",
        claim_id=state.claim_id,
    )
    _assert_outer_ownership(state, require_present=True)
    _wait_health()
    _assert_aws_targets_absent(state)
    state, resources = _provision(state)
    return {"ok": True, "run": state.run_id, "resources": state.to_dict(), "queue_urls": resources}


def _task_definition(
    state: RunState,
    *,
    role: str,
    image: str,
    queue_url: str,
    operation_id: str = "00000000000000000000000000000000",
) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{32}", operation_id):
        raise LabError("task definition requires a valid deployment operation ID")
    environment = [
        {"name": "PK_STACK_LAB_ROLE", "value": role},
        {"name": "PK_STACK_LAB_ENDPOINT", "value": TASK_ENDPOINT},
        {"name": "PK_STACK_LAB_REGION", "value": REGION},
        {"name": "PK_STACK_LAB_QUEUE_URL", "value": queue_url},
        {"name": "PK_STACK_LAB_TABLE", "value": state.table},
        {"name": "PK_STACK_LAB_BUCKET", "value": state.bucket},
        {"name": "PK_STACK_LAB_RUN", "value": state.run_id},
        {"name": "PK_STACK_LAB_CLAIM", "value": state.claim_id},
        {"name": "PK_STACK_LAB_OPERATION", "value": operation_id},
        {"name": "PK_STACK_LAB_SOURCE_DIGEST", "value": state.source_digest},
    ]
    definition: dict[str, Any] = {
        "family": state.api_family if role == "api" else state.worker_family,
        "networkMode": "bridge",
        "requiresCompatibilities": ["EC2"],
        "runtimePlatform": {"cpuArchitecture": "ARM64", "operatingSystemFamily": "LINUX"},
        "cpu": "256",
        "memory": "512",
        "containerDefinitions": [
            {
                "name": role,
                "image": image,
                "essential": True,
                "user": "65532:65532",
                "readonlyRootFilesystem": True,
                "linuxParameters": {"capabilities": {"drop": ["ALL"]}},
                "dockerSecurityOptions": ["no-new-privileges"],
                "environment": environment,
                "dockerLabels": {
                    "pk-stack-lab.managed": "true",
                    "pk-stack-lab.project": PROJECT,
                    "pk-stack-lab.run": state.run_id,
                    "pk-stack-lab.claim": state.claim_id,
                    "pk-stack-lab.source-digest": state.source_digest,
                    "pk-stack-lab.operation": operation_id,
                    "pk-stack-lab.role": role,
                },
            }
        ],
        "tags": _ecs_tags(state),
    }
    if role == "api":
        definition["containerDefinitions"][0]["portMappings"] = [
            {"containerPort": 8080, "hostPort": 0, "protocol": "tcp"}
        ]
    return definition


def _wait_services(state: RunState) -> list[dict[str, Any]]:
    ecs = client("ecs")
    for _ in range(45):
        response = ecs.describe_services(
            cluster=state.cluster,
            services=[state.api_service, state.worker_service],
            include=["TAGS"],
        )
        services = _ecs_described_items(
            response,
            "services",
            label="ECS service stabilization",
            allow_missing=True,
        )
        by_name = {service.get("serviceName"): service for service in services}
        expected = {
            state.api_service: state.api_task_definition_arn,
            state.worker_service: state.worker_task_definition_arn,
        }
        if len(services) == 2 and all(
            by_name.get(name, {}).get("runningCount") == 1
            and by_name.get(name, {}).get("pendingCount") == 0
            and by_name.get(name, {}).get("taskDefinition") == definition
            for name, definition in expected.items()
        ):
            current = True
            for name, definition in expected.items():
                arns = _tokenized_items(
                    ecs.list_tasks,
                    "taskArns",
                    cluster=state.cluster,
                    serviceName=name,
                    desiredStatus="RUNNING",
                    maxResults=100,
                )
                tasks = _ecs_described_items(
                    ecs.describe_tasks(cluster=state.cluster, tasks=arns),
                    "tasks",
                    label="ECS task stabilization",
                    allow_missing=True,
                )
                if (
                    len(arns) != 1
                    or len(tasks) != 1
                    or tasks[0].get("taskDefinitionArn") != definition
                ):
                    current = False
                    break
            if current:
                return services
        time.sleep(2)
    raise LabError("ECS services did not stabilize within 90 seconds")


def _validate_registered_task_definition(
    ecs: Any,
    state: RunState,
    *,
    role: str,
    requested: dict[str, Any],
    registered: dict[str, Any],
) -> str:
    """Re-read and validate a registered definition before service adoption."""
    arn = registered.get("taskDefinitionArn")
    family = state.api_family if role == "api" else state.worker_family
    if not isinstance(arn, str):
        raise LabError("task-definition registration returned no concrete ARN")
    match = re.fullmatch(
        rf"arn:aws:ecs:{re.escape(REGION)}:[0-9]{{12}}:task-definition/{re.escape(family)}:([1-9][0-9]*)",
        arn,
    )
    if not match:
        raise LabError("registered task-definition ARN does not match the requested family")
    response = ecs.describe_task_definition(taskDefinition=arn, include=["TAGS"])
    definition = response.get("taskDefinition")
    tags = response.get("tags", definition.get("tags") if isinstance(definition, dict) else None)
    if tags is None:
        tags = ecs.list_tags_for_resource(resourceArn=arn).get("tags")
    if (
        not isinstance(definition, dict)
        or definition.get("taskDefinitionArn") != arn
        or definition.get("family") != family
        or definition.get("revision") != int(match.group(1))
        or not _owned(state, tags)
        or not _owned(state, requested.get("tags"))
        or definition.get("networkMode") != requested["networkMode"]
        or definition.get("cpu") != requested["cpu"]
        or definition.get("memory") != requested["memory"]
        or definition.get("runtimePlatform") != requested["runtimePlatform"]
        or set(definition.get("requiresCompatibilities", [])) != {"EC2"}
        or definition.get("volumes", []) != []
    ):
        raise LabError("registered task definition failed identity or ownership validation")
    containers = definition.get("containerDefinitions")
    expected = requested["containerDefinitions"][0]
    if not isinstance(containers, list) or len(containers) != 1:
        raise LabError("registered task definition has an unexpected container inventory")
    container = containers[0]
    if not isinstance(container, dict):
        raise LabError("registered task definition has malformed container metadata")
    preserved_exact = {
        "name": role,
        "image": expected["image"],
        "essential": True,
        "environment": expected["environment"],
    }
    projected_controls = {
        "user": "65532:65532",
        "readonlyRootFilesystem": True,
        "linuxParameters": expected["linuxParameters"],
        "dockerSecurityOptions": ["no-new-privileges"],
        "dockerLabels": expected["dockerLabels"],
    }
    if (
        any(container.get(key) != value for key, value in preserved_exact.items())
        or any(
            key in container and container.get(key) != value
            for key, value in projected_controls.items()
        )
        or container.get("mountPoints", []) != []
        or container.get("volumesFrom", []) != []
        or container.get("portMappings", []) != expected.get("portMappings", [])
    ):
        raise LabError("registered task definition drifted from the requested container contract")
    return arn


def _deployment_events(
    state: RunState,
    *,
    operation_id: str,
    kind: str,
    digest: str,
    image_refs: dict[str, str],
    image_id: str = "",
    role: str | None = None,
    task_definition_arn: str = "",
) -> tuple[ArtifactEvent, ...]:
    """Create one or two correctly sequenced append-only deployment events."""
    roles = (role,) if role is not None else ("api", "worker")
    first = next_artifact_sequence(state)
    events: list[ArtifactEvent] = []
    for offset, current_role in enumerate(roles):
        family = ""
        if kind.startswith("task_definition_"):
            family = state.api_family if current_role == "api" else state.worker_family
        events.append(
            ArtifactEvent(
                seq=first + offset,
                kind=kind,
                operation_id=operation_id,
                role=current_role,
                source_digest=digest,
                image_ref=image_refs[current_role],
                image_id=image_id,
                family=family,
                task_definition_arn=task_definition_arn,
            )
        )
    return tuple(events)


def _activate_deployment(
    state: RunState,
    *,
    digest: str,
    image_id: str,
    api_arn: str,
    worker_arn: str,
) -> RunState:
    """Atomically publish a candidate only after both services stabilized."""
    return activate_deployment(
        ROOT,
        state,
        source_digest=digest,
        image_id=image_id,
        api_task_definition_arn=api_arn,
        worker_task_definition_arn=worker_arn,
    )


def _operation_events(state: RunState, operation_id: str) -> dict[tuple[str, str], ArtifactEvent]:
    values: dict[tuple[str, str], ArtifactEvent] = {}
    for event in state.artifact_ledger:
        if event.operation_id != operation_id:
            continue
        key = (event.kind, event.role)
        if key in values:
            raise LabError("deployment operation contains a duplicate artifact event")
        values[key] = event
    return values


def _resumable_operation(state: RunState, digest: str) -> str | None:
    ordered: dict[str, int] = {}
    for event in state.artifact_ledger:
        if event.source_digest == digest:
            ordered[event.operation_id] = event.seq
    if not ordered:
        return None
    operation_id = max(ordered, key=ordered.__getitem__)
    events = _operation_events(state, operation_id)
    if not all(("image_planned", role) in events for role in ("api", "worker")):
        raise LabError("latest deployment operation lacks its durable image plans")
    definitions = {
        role: events.get(("task_definition_observed", role)) for role in ("api", "worker")
    }
    if not all(definitions.values()):
        return operation_id
    # A complete operation for the same digest is reused, including when it is
    # already active.  Creating another operation would target the same
    # deterministic tags and could overwrite their immutable association.
    return operation_id


def _build_and_identify_image(
    state: RunState,
    digest: str,
    api_image: str,
    worker_image: str,
    operation_id: str,
) -> str:
    if _image_ref_exists(api_image) or _image_ref_exists(worker_image):
        raise LabError("refusing to build over an existing deterministic image reference")
    _run(
        [
            "docker",
            "build",
            "--platform",
            "linux/arm64",
            "--label",
            f"pk-stack-lab.project={PROJECT}",
            "--label",
            f"pk-stack-lab.run={state.run_id}",
            "--label",
            f"pk-stack-lab.claim={state.claim_id}",
            "--label",
            f"pk-stack-lab.source-digest={digest}",
            "--label",
            f"pk-stack-lab.operation={operation_id}",
            "-t",
            api_image,
            str(ROOT),
        ],
        timeout=300,
    )
    if _image_ref_exists(worker_image):
        raise LabError("worker image reference appeared during the protected build")
    _run(["docker", "tag", api_image, worker_image])
    api_image_id = _run(["docker", "image", "inspect", "--format", "{{.Id}}", api_image]).strip()
    worker_image_id = _run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", worker_image]
    ).strip()
    if api_image_id != worker_image_id or not re.fullmatch(r"sha256:[0-9a-f]{64}", api_image_id):
        raise LabError("Docker build did not produce one concrete immutable image identity")
    return api_image_id


def _ensure_operation_image_pair(
    state: RunState,
    *,
    digest: str,
    image_refs: dict[str, str],
    operation_id: str,
    expected_image_id: str = "",
) -> str:
    """Build, reuse, or finish only the current operation's exact image pair."""
    present = {role: _image_ref_exists(ref) for role, ref in image_refs.items()}
    if not any(present.values()):
        built = _build_and_identify_image(
            state,
            digest,
            image_refs["api"],
            image_refs["worker"],
            operation_id,
        )
        if expected_image_id and built != expected_image_id:
            raise LabError("recreated image does not match the journaled immutable identity")
        for ref in image_refs.values():
            _validate_image_target(
                state,
                ImageTarget(ref, built, digest),
                operation_id=operation_id,
                require_present=True,
            )
        return built

    ids: dict[str, str] = {}
    for role, exists in present.items():
        if not exists:
            continue
        target = ImageTarget(image_refs[role], expected_image_id, digest)
        _validate_image_target(state, target, operation_id=operation_id, require_present=True)
        ids[role] = _run(
            ["docker", "image", "inspect", "--format", "{{.Id}}", image_refs[role]]
        ).strip()
    if len(set(ids.values())) != 1:
        raise LabError("deterministic image references resolve to conflicting image IDs")
    image_id = next(iter(ids.values()))
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise LabError("deterministic image reference has no concrete image ID")

    missing = [role for role, exists in present.items() if not exists]
    if missing:
        missing_role = missing[0]
        source_role = next(role for role, exists in present.items() if exists)
        missing_ref = image_refs[missing_role]
        if _image_ref_exists(missing_ref):
            raise LabError("missing image reference appeared during protected recovery")
        _run(["docker", "tag", image_refs[source_role], missing_ref])
        _validate_image_target(
            state,
            ImageTarget(missing_ref, image_id, digest),
            operation_id=operation_id,
            require_present=True,
        )
    return image_id


def command_deploy(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    if state.teardown is not None:
        raise LabError("deployment is frozen because teardown has started")
    _bind_claimed_outer(state)  # Fail before planning/building if the control plane drifted.
    ecs = client("ecs")
    # Reconcile a prior register/journal hard-exit before another revision can
    # be created. Exact family, claim, config, image, and digest must all agree.
    state = _reconcile_pending_task_definitions(state, ecs)
    digest = source_digest(ROOT)
    image_refs = {
        "api": f"{state.prefix}-api:{digest[:24]}",
        "worker": f"{state.prefix}-worker:{digest[:24]}",
    }
    operation_id = _resumable_operation(state, digest)
    if operation_id is None:
        # A new operation has no provenance for either deterministic ref.  Any
        # pre-existing tag is therefore foreign or stale and must survive a
        # fail-closed refusal unchanged.
        if any(_image_ref_exists(ref) for ref in image_refs.values()):
            raise LabError(
                "deterministic image reference already exists outside the artifact ledger"
            )
        operation_id = secrets.token_hex(16)
        # Persist both exact tags before the first Docker mutation. A hard exit
        # at any later boundary therefore leaves a recoverable cleanup target.
        state = append_artifact_events(
            ROOT,
            state,
            *_deployment_events(
                state,
                operation_id=operation_id,
                kind="image_planned",
                digest=digest,
                image_refs=image_refs,
            ),
        )
    events = _operation_events(state, operation_id)
    api_image, worker_image = image_refs["api"], image_refs["worker"]
    image_events = [events.get(("image_observed", role)) for role in ("api", "worker")]
    if any(image_events) and not all(image_events):
        raise LabError("deployment operation has a partial image observation")
    if all(image_events):
        api_event, worker_event = image_events
        assert api_event is not None and worker_event is not None
        if api_event.image_id != worker_event.image_id:
            raise LabError("deployment operation recorded conflicting image identities")
        api_image_id = _ensure_operation_image_pair(
            state,
            digest=digest,
            image_refs=image_refs,
            operation_id=operation_id,
            expected_image_id=api_event.image_id,
        )
    else:
        api_image_id = _ensure_operation_image_pair(
            state,
            digest=digest,
            image_refs=image_refs,
            operation_id=operation_id,
        )
        state = append_artifact_events(
            ROOT,
            state,
            *_deployment_events(
                state,
                operation_id=operation_id,
                kind="image_observed",
                digest=digest,
                image_refs=image_refs,
                image_id=api_image_id,
            ),
        )
        events = _operation_events(state, operation_id)
    definition_plans = [events.get(("task_definition_planned", role)) for role in ("api", "worker")]
    if any(definition_plans) and not all(definition_plans):
        raise LabError("deployment operation has partial task-definition plans")
    if not all(definition_plans):
        state = append_artifact_events(
            ROOT,
            state,
            *_deployment_events(
                state,
                operation_id=operation_id,
                kind="task_definition_planned",
                digest=digest,
                image_refs=image_refs,
            ),
        )
        events = _operation_events(state, operation_id)
    candidate = replace(
        state,
        source_digest=digest,
        api_image_id=api_image_id,
        worker_image_id=api_image_id,
    )
    sqs = client("sqs")
    queue_url = sqs.get_queue_url(QueueName=state.queue)["QueueUrl"]
    # Floci returns the task-reachable hostname because FLOCI_HOSTNAME is set.
    parsed = urlparse(queue_url)
    if parsed.hostname != "floci" or parsed.username or parsed.password:
        raise LabError("Floci did not return a task-network SQS URL")
    arns: dict[str, str] = {}
    for role, image in (("api", api_image), ("worker", worker_image)):
        prior = events.get(("task_definition_observed", role))
        if prior is not None:
            if prior.task_definition_arn not in _exact_task_definition_arns(ecs, state):
                raise LabError("journaled candidate task definition is no longer available")
            observed_role, observed_digest, observed_ref, observed_operation = (
                _task_definition_artifact(ecs, state, prior.task_definition_arn)
            )
            if (observed_role, observed_digest, observed_ref, observed_operation) != (
                role,
                digest,
                image,
                operation_id,
            ):
                raise LabError("journaled candidate task definition drifted")
            arns[role] = prior.task_definition_arn
            continue
        request = _task_definition(
            candidate,
            role=role,
            image=image,
            queue_url=queue_url,
            operation_id=operation_id,
        )
        registered = ecs.register_task_definition(**request)["taskDefinition"]
        arn = _validate_registered_task_definition(
            ecs, candidate, role=role, requested=request, registered=registered
        )
        state = append_artifact_events(
            ROOT,
            state,
            *_deployment_events(
                state,
                operation_id=operation_id,
                kind="task_definition_observed",
                digest=digest,
                image_refs=image_refs,
                image_id=api_image_id,
                role=role,
                task_definition_arn=arn,
            ),
        )
        events = _operation_events(state, operation_id)
        candidate = replace(candidate, artifact_ledger=state.artifact_ledger)
        arns[role] = arn
    api_arn, worker_arn = arns["api"], arns["worker"]
    candidate = replace(
        state,
        source_digest=digest,
        api_image_id=api_image_id,
        worker_image_id=api_image_id,
        api_task_definition_arn=api_arn,
        worker_task_definition_arn=worker_arn,
    )
    for name, task_definition in (
        (candidate.api_service, api_arn),
        (candidate.worker_service, worker_arn),
    ):
        existing = _ecs_described_items(
            ecs.describe_services(cluster=candidate.cluster, services=[name], include=["TAGS"]),
            "services",
            label="deployment ECS service inventory",
            allow_missing=True,
        )
        if len(existing) > 1:
            raise LabError("ECS service inventory returned an ambiguous exact name")
        if existing:
            if not _owned(candidate, existing[0].get("tags")):
                raise LabError("refusing to update ECS service without exact current-claim tags")
            ecs.update_service(
                cluster=candidate.cluster,
                service=name,
                taskDefinition=task_definition,
                desiredCount=1,
                forceNewDeployment=True,
                propagateTags="SERVICE",
            )
        else:
            ecs.create_service(
                cluster=candidate.cluster,
                serviceName=name,
                taskDefinition=task_definition,
                desiredCount=1,
                launchType="EC2",
                tags=_ecs_tags(candidate),
                propagateTags="SERVICE",
            )
    services = _wait_services(candidate)
    state = _activate_deployment(
        state,
        digest=digest,
        image_id=api_image_id,
        api_arn=api_arn,
        worker_arn=worker_arn,
    )
    return {
        "ok": True,
        "run": state.run_id,
        "source_digest": digest,
        "image_id": api_image_id,
        "task_definitions": {
            "api": api_arn,
            "worker": worker_arn,
        },
        "services": [{"name": s["serviceName"], "running": s["runningCount"]} for s in services],
    }


def _assert_deployed_source(state: RunState) -> None:
    if not state.source_digest or not state.api_image_id or not state.worker_image_id:
        raise LabError("no immutable deployment identity is recorded; run labctl deploy")
    if source_digest(ROOT) != state.source_digest:
        raise LabError("declared Docker build inputs drifted; redeploy before verification")


def _service_tasks(state: RunState) -> tuple[dict[str, Any], dict[str, Any]]:
    ecs = client("ecs")
    result: dict[str, dict[str, Any]] = {}
    for role, service in (("api", state.api_service), ("worker", state.worker_service)):
        services = _ecs_described_items(
            ecs.describe_services(cluster=state.cluster, services=[service], include=["TAGS"]),
            "services",
            label=f"{role} ECS service proof",
            allow_missing=True,
        )
        if len(services) != 1 or not _owned(state, services[0].get("tags")):
            raise LabError(f"{role} ECS service lacks exact current-run ownership tags")
        arns = _tokenized_items(
            ecs.list_tasks,
            "taskArns",
            cluster=state.cluster,
            serviceName=service,
            desiredStatus="RUNNING",
            maxResults=100,
        )
        if len(arns) != 1:
            raise LabError(f"expected exactly one running {role} ECS task")
        tasks = _ecs_described_items(
            ecs.describe_tasks(cluster=state.cluster, tasks=arns, include=["TAGS"]),
            "tasks",
            label=f"{role} ECS task proof",
            allow_missing=True,
        )
        if not tasks:
            raise LabError(f"unable to describe {role} ECS task")
        task = tasks[0]
        expected_family = state.api_family if role == "api" else state.worker_family
        expected_definition = (
            state.api_task_definition_arn if role == "api" else state.worker_task_definition_arn
        )
        if (
            (task.get("tags") is not None and not _owned(state, task.get("tags")))
            or f":task/{state.cluster}/" not in str(task.get("taskArn"))
            or f"task-definition/{expected_family}:" not in str(task.get("taskDefinitionArn"))
            or (expected_definition and task.get("taskDefinitionArn") != expected_definition)
        ):
            raise LabError(f"{role} ECS task does not match current-run ownership or definition")
        result[role] = task
    return result["api"], result["worker"]


def _task_container_name(task: dict[str, Any], role: str) -> str:
    arn = task.get("taskArn", "")
    task_id = arn.rsplit("/", 1)[-1] if isinstance(arn, str) else ""
    if not _TASK_ID.fullmatch(task_id) or role not in {"api", "worker"}:
        raise LabError("unexpected ECS task identity")
    return f"floci-ecs-{task_id}-{role}"


def _api_http(
    task: dict[str, Any],
    container: dict[str, Any],
    *,
    method: str,
    path: str,
    body: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Use a transient hardened verifier, never `docker exec` in an app task."""
    if not path.startswith("/") or len(path) > 256:
        raise LabError("invalid fixed API request path")
    name = container.get("name")
    if name != _task_container_name(task, "api") or container.get("role") != "api":
        raise LabError("bounded API HTTP requires prior exact API container proof")
    state = load_state(ROOT)
    if not state.api_image_id:
        raise LabError("hardened verifier requires persisted immutable API image identity")
    verifier_name = f"{state.prefix}-verifier"
    if _exact_docker_object_exists("container", verifier_name):
        raise LabError("refusing a pre-existing verifier container name")
    request = {"method": method, "path": path, "body": body, "headers": headers or {}}
    script = (
        "import json,os\nfrom urllib.error import HTTPError\nfrom urllib.request import HTTPRedirectHandler,ProxyHandler,Request,build_opener\n"
        "class R(HTTPRedirectHandler):\n def redirect_request(self,*a,**k): raise HTTPError(a[0].full_url, 599, 'redirect refused', a[2], a[3])\n"
        "r=json.loads(os.environ['PK_STACK_LAB_VERIFY_REQUEST']); d=json.dumps(r['body'],separators=(',',':')).encode() if r['body'] is not None else None; "
        "q=Request(os.environ['PK_STACK_LAB_API_DNS']+r['path'],method=r['method'],data=d,headers={'Content-Type':'application/json',**r['headers']}); o=build_opener(ProxyHandler({}),R()); "
        "\ntry:\n f=o.open(q,timeout=5); print(json.dumps({'status':f.status,'body':json.loads(f.read(8192))}))\n"
        "except HTTPError as e: print(json.dumps({'status':e.code,'body':json.loads(e.read(8192))}))"
    )
    request_completed = False
    try:
        raw = _run(
            [
                "docker",
                "run",
                "--rm",
                "--pull",
                "never",
                "--name",
                verifier_name,
                "--network",
                NETWORK,
                "--user",
                "65532:65532",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--pids-limit",
                "32",
                "--memory",
                "64m",
                "--cpus",
                "0.25",
                "--label",
                "pk-stack-lab.managed=true",
                "--label",
                f"pk-stack-lab.project={PROJECT}",
                "--label",
                f"pk-stack-lab.run={state.run_id}",
                "--label",
                f"pk-stack-lab.claim={state.claim_id}",
                "--label",
                "pk-stack-lab.component=verifier",
                "-e",
                f"PK_STACK_LAB_VERIFY_REQUEST={json.dumps(request, separators=(',', ':'))}",
                "-e",
                f"PK_STACK_LAB_API_DNS=http://{name}:8080",
                "--entrypoint",
                "python",
                state.api_image_id,
                "-c",
                script,
            ],
            timeout=15,
        )
        request_completed = True
    finally:
        # `--rm` covers normal completion; errors and timeouts still receive
        # exact-name cleanup before a later verifier can be attempted.
        try:
            if _exact_docker_object_exists("container", verifier_name):
                _run(["docker", "container", "rm", "-f", verifier_name])
        except LabError:
            if request_completed:
                raise
    if _exact_docker_object_exists("container", verifier_name):
        raise LabError("hardened verifier container was not cleaned up")
    try:
        response = json.loads(raw)
        status, response_body = response["status"], response["body"]
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise LabError("API task returned malformed bounded HTTP evidence") from exc
    if not isinstance(status, int) or not isinstance(response_body, dict):
        raise LabError("API task returned malformed HTTP response")
    return status, response_body


def _task_container_evidence(
    task: dict[str, Any], role: str, state: RunState | None = None
) -> dict[str, Any]:
    task_id = task.get("taskArn", "").rsplit("/", 1)[-1]
    if not isinstance(task_id, str) or not _TASK_ID.fullmatch(task_id):
        raise LabError("unexpected ECS task identity")
    name = _task_container_name(task, role)
    labels = _inspect_labels("container", name)
    assert labels is not None
    required = {
        "floci": "true",
        "floci_emulator": "floci-aws",
        "io.floci": "aws",
        "io.floci.service": "ecs",
        "io.floci.resource-id": task_id,
    }
    if any(labels.get(key) != value for key, value in required.items()):
        raise LabError("Docker task container labels do not prove the exact Floci ECS task")
    networks = _docker_json(
        ["docker", "container", "inspect", "--format", "{{json .NetworkSettings.Networks}}", name]
    )
    if not isinstance(networks, dict) or set(networks) != {NETWORK}:
        raise LabError("real ECS task container is not exclusively on the dedicated lab network")
    observed_network = next(iter(networks))
    image = _run(["docker", "container", "inspect", "--format", "{{.Config.Image}}", name]).strip()
    expected_image = str(task.get("containers", [{}])[0].get("image", ""))
    if not image or image != expected_image:
        raise LabError("Docker task image does not match ECS task metadata")
    image_id = _run(["docker", "container", "inspect", "--format", "{{.Image}}", name]).strip()
    if not image_id:
        raise LabError("Docker task container has no concrete image ID")
    if state is not None:
        expected_id = state.api_image_id if role == "api" else state.worker_image_id
        if expected_id and image_id != expected_id:
            raise LabError("Docker task image ID drifted from the immutable deployment claim")
        expected_definition = (
            state.api_task_definition_arn if role == "api" else state.worker_task_definition_arn
        )
        events = [
            event
            for event in state.artifact_ledger
            if event.kind == "task_definition_observed"
            and event.role == role
            and event.task_definition_arn == expected_definition
        ]
        if len(events) != 1:
            raise LabError("active task definition is not uniquely bound to the artifact ledger")
        environment = _container_environment(name)
        event = events[0]
        if (
            environment.get("PK_STACK_LAB_RUN") != state.run_id
            or environment.get("PK_STACK_LAB_CLAIM") != state.claim_id
            or environment.get("PK_STACK_LAB_ROLE") != role
            or environment.get("PK_STACK_LAB_OPERATION") != event.operation_id
            or environment.get("PK_STACK_LAB_SOURCE_DIGEST") != state.source_digest
        ):
            raise LabError("Docker task environment drifted from the immutable deployment claim")
    mounts = _docker_json(["docker", "container", "inspect", "--format", "{{json .Mounts}}", name])
    if mounts != []:
        raise LabError("API and worker task containers must have no mounts")
    raw_security = _run(
        [
            "docker",
            "container",
            "inspect",
            "--format",
            "{{.Config.User}}|{{.HostConfig.ReadonlyRootfs}}|{{json .HostConfig.CapDrop}}|{{json .HostConfig.SecurityOpt}}",
            name,
        ]
    ).strip()
    try:
        user, readonly, encoded_caps, encoded_options = raw_security.split("|", 3)
        cap_drop = json.loads(encoded_caps)
        security_opt = json.loads(encoded_options)
    except (ValueError, json.JSONDecodeError) as exc:
        raise LabError("Docker task security inspection was malformed") from exc
    if user != "65532:65532":
        raise LabError("real ECS task container did not enforce the required non-root user")
    readonly_effective = readonly == "true"
    cap_drop_effective = isinstance(cap_drop, list) and "ALL" in cap_drop
    no_new_privileges_effective = (
        isinstance(security_opt, list) and "no-new-privileges" in security_opt
    )
    limitations = [
        name
        for name, effective in (
            ("readonly_root_filesystem", readonly_effective),
            ("cap_drop_all", cap_drop_effective),
            ("no_new_privileges", no_new_privileges_effective),
        )
        if not effective
    ]
    return {
        "name": name,
        "role": role,
        "image": image,
        "image_id": image_id,
        "network": observed_network,
        "security": {
            "user": user,
            "non_root": True,
            "mounts": [],
            "requested": {
                "readonly_root_filesystem": True,
                "cap_drop_all": True,
                "no_new_privileges": True,
            },
            "effective": {
                "readonly_root_filesystem": readonly_effective,
                "cap_drop_all": cap_drop_effective,
                "no_new_privileges": no_new_privileges_effective,
            },
            "emulator_limitations": limitations,
        },
        "labels": _label_subset(labels, set(required)),
    }


def _owned_container_proof(
    state: RunState, api: dict[str, Any], worker: dict[str, Any]
) -> list[dict[str, Any]]:
    containers: list[dict[str, str]] = []
    for task, role in ((api, "api"), (worker, "worker")):
        containers.append(_task_container_evidence(task, role, state))
    return containers


def _verify_result_object(
    s3: Any, state: RunState, *, tenant: str, export_id: str, object_key: object
) -> tuple[dict[str, Any], str]:
    """Validate the complete deterministic result contract, not just its ETag."""
    expected_key = f"exports/{tenant}/{export_id}.json"
    if object_key != expected_key:
        raise LabError("terminal export did not use the deterministic result key")
    try:
        head = s3.head_object(Bucket=state.bucket, Key=expected_key)
        length = head.get("ContentLength")
        if not isinstance(length, int) or not 1 <= length <= MAX_RESULT_BYTES:
            raise LabError("result object length is outside the strict bound")
        if head.get("ContentType") != "application/json":
            raise LabError("result object has an unexpected content type")
        body = s3.get_object(Bucket=state.bucket, Key=expected_key)["Body"].read(
            MAX_RESULT_BYTES + 1
        )
    except (ClientError, KeyError, OSError, TypeError) as exc:
        raise LabError("unable to fetch exact terminal result object") from exc
    if not isinstance(body, bytes) or not 1 <= len(body) <= MAX_RESULT_BYTES:
        raise LabError("result object body is outside the strict bound")
    try:
        parsed = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LabError("result object is not strict JSON") from exc
    expected = {"tenant": tenant, "export_id": export_id}
    if parsed != expected:
        raise LabError("result object does not match the exact export schema")
    etag = head.get("ETag")
    if not isinstance(etag, str) or not etag:
        raise LabError("result object has no concrete identity")
    return parsed, etag


def _reprove_deployment_identity(
    state: RunState,
    api_task: dict[str, Any],
    worker_task: dict[str, Any],
    containers: list[dict[str, Any]],
) -> None:
    """Re-read every mutable identity root after business verification."""
    post_state = load_state(ROOT)
    if post_state != state:
        raise LabError("canonical deployment manifest changed during verification")
    _bind_claimed_outer(post_state)
    _assert_deployed_source(post_state)
    post_api_task, post_worker_task = _service_tasks(post_state)
    post_containers = _owned_container_proof(post_state, post_api_task, post_worker_task)
    if (
        post_api_task.get("taskArn") != api_task.get("taskArn")
        or post_worker_task.get("taskArn") != worker_task.get("taskArn")
        or post_containers != containers
    ):
        raise LabError("deployed task or container identity changed during verification")


def command_status(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    _bind_claimed_outer(state)
    _assert_deployed_source(state)
    api, worker = _service_tasks(state)
    return {
        "ok": True,
        "run": state.run_id,
        "resources": state.to_dict(),
        "services": {
            "api": {"task": api["taskArn"], "status": api["lastStatus"]},
            "worker": {"task": worker["taskArn"], "status": worker["lastStatus"]},
        },
    }


def _verified_resource_evidence(state: RunState) -> dict[str, str]:
    """Return the fixed, bounded resource schema consumed by the external judge.

    The append-only artifact ledger and teardown journal remain in the canonical
    local state. Emitting either here would make a verifier result grow with
    every deployment and eventually violate the independent judge's bound.
    """
    return {
        "run_id": state.run_id,
        "queue": state.queue,
        "dlq": state.dlq,
        "table": state.table,
        "bucket": state.bucket,
        "cluster": state.cluster,
        "api_service": state.api_service,
        "worker_service": state.worker_service,
        "api_family": state.api_family,
        "worker_family": state.worker_family,
        "claim_id": state.claim_id,
        "docker_context": state.docker_context,
        "docker_socket": state.docker_socket,
        "docker_daemon_id": state.docker_daemon_id,
        "source_digest": state.source_digest,
        "api_image_id": state.api_image_id,
        "worker_image_id": state.worker_image_id,
        "api_task_definition_arn": state.api_task_definition_arn,
        "worker_task_definition_arn": state.worker_task_definition_arn,
    }


def command_verify(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    _bind_claimed_outer(state)
    _assert_deployed_source(state)
    api_task, worker_task = _service_tasks(state)
    # Prove both concrete task containers before any verifier-container request
    # or AWS emulator mutation. The transport receives that proof rather than
    # deriving an unvalidated API DNS name itself.
    containers = _owned_container_proof(state, api_task, worker_task)
    api_container = containers[0]
    tenant, other = "tenant-a", "tenant-b"
    idem = f"verify-{secrets.token_hex(8)}"
    status, created = _api_http(
        api_task,
        api_container,
        method="POST",
        path="/exports",
        body={"tenant": tenant},
        headers={"Idempotency-Key": idem},
    )
    if (
        status != 202
        or created.get("tenant") != tenant
        or created.get("status") not in ("QUEUED", "COMPLETE")
    ):
        raise LabError("deployed API did not accept the export")
    export_id = created.get("id")
    if not isinstance(export_id, str):
        raise LabError("deployed API returned no export id")
    if not _EXPORT_ID.fullmatch(export_id):
        raise LabError("deployed API returned an invalid export id")
    duplicate_status, duplicate = _api_http(
        api_task,
        api_container,
        method="POST",
        path="/exports",
        body={"tenant": tenant},
        headers={"Idempotency-Key": idem},
    )
    duplicate_marker = duplicate.get("duplicate") is True
    duplicate_status_value = duplicate.get("status")
    duplicate_same_export = duplicate.get("id") == export_id
    if (
        duplicate_status != 202
        or duplicate.get("tenant") != tenant
        or not duplicate_same_export
        or not duplicate_marker
        or duplicate_status_value not in ("QUEUED", "COMPLETE")
    ):
        raise LabError("API idempotency did not preserve the original export")
    final: dict[str, Any] | None = None
    for _ in range(30):
        response_status, response = _api_http(
            api_task, api_container, method="GET", path=f"/exports?tenant={tenant}&id={export_id}"
        )
        if response_status == 200 and response.get("status") == "COMPLETE":
            final = response
            break
        time.sleep(1)
    if not final or not isinstance(final.get("object_key"), str):
        raise LabError("worker did not produce a terminal export in time")
    isolated_status, _ = _api_http(
        api_task, api_container, method="GET", path=f"/exports?tenant={other}&id={export_id}"
    )
    if isolated_status != 404:
        raise LabError("tenant-key partition separation check failed")
    s3 = client("s3")
    result_body, original_etag = _verify_result_object(
        s3, state, tenant=tenant, export_id=export_id, object_key=final["object_key"]
    )
    ddb = client("dynamodb")
    key = {"pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}}
    before = ddb.get_item(TableName=state.table, Key=key, ConsistentRead=True).get("Item", {})
    row_idempotency_matches = before.get("idempotency", {}).get("S") == idem
    if not row_idempotency_matches:
        raise LabError("terminal export row did not preserve the request idempotency key")
    row_attempts = before.get("attempts", {}).get("N")
    if row_attempts != "1":
        raise LabError("happy-path worker attempts were not exactly one")
    enqueue_confirmed = before.get("enqueue_confirmed", {}).get("BOOL") is True
    if not enqueue_confirmed:
        raise LabError("terminal export row did not preserve durable enqueue confirmation")
    if before.get("status", {}).get("S") != "COMPLETE":
        raise LabError("terminal export row did not preserve terminal status")
    sqs = client("sqs")
    queue_url = sqs.get_queue_url(QueueName=state.queue)["QueueUrl"]
    sqs.send_message(
        QueueUrl=queue_url, MessageBody=json.dumps({"tenant": tenant, "id": export_id})
    )
    duplicate_noop = False
    for _ in range(16):
        current = ddb.get_item(TableName=state.table, Key=key, ConsistentRead=True).get("Item", {})
        _, current_etag = _verify_result_object(
            s3, state, tenant=tenant, export_id=export_id, object_key=final["object_key"]
        )
        if (
            current.get("idempotency", {}).get("S") == idem
            and current.get("status", {}).get("S") == "COMPLETE"
            and current.get("enqueue_confirmed", {}).get("BOOL") is True
            and current.get("attempts", {}).get("N") == "1"
            and current.get("duplicate_deliveries", {}).get("N") == "1"
            and current_etag == original_etag
        ):
            duplicate_noop = True
            break
        time.sleep(1)
    if not duplicate_noop:
        raise LabError("worker duplicate SQS delivery was not consumed as a no-op")
    marker = f"verify-invalid-{secrets.token_hex(8)}"
    invalid_body = json.dumps({"marker": marker}, separators=(",", ":"))
    sqs.send_message(QueueUrl=queue_url, MessageBody=invalid_body)
    dlq_url = sqs.get_queue_url(QueueName=state.dlq)["QueueUrl"]
    dlq_message_id: str | None = None
    for _ in range(24):
        messages = sqs.receive_message(
            QueueUrl=dlq_url, MaxNumberOfMessages=10, WaitTimeSeconds=1
        ).get("Messages", [])
        for message in messages:
            if message.get("Body") == invalid_body:
                sqs.delete_message(QueueUrl=dlq_url, ReceiptHandle=message["ReceiptHandle"])
                dlq_message_id = message.get("MessageId")
                break
        if dlq_message_id:
            break
        time.sleep(1)
    if not dlq_message_id:
        raise LabError("current invocation invalid message was not observed on the DLQ")
    # Re-prove the entire source -> service -> task -> Docker-container chain
    # after the business mutations. A rollout or tag/image swap during the
    # verifier run must never inherit the proof captured at the beginning.
    _reprove_deployment_identity(state, api_task, worker_task, containers)
    return {
        "ok": True,
        "run": state.run_id,
        "api_transport": "bounded HTTP from a transient hardened verifier container to the exact real ECS API task",
        "resources": _verified_resource_evidence(state),
        "immutable": {
            "source_digest": state.source_digest,
            "api_image_id": state.api_image_id,
            "worker_image_id": state.worker_image_id,
            "api_task_definition_arn": state.api_task_definition_arn,
            "worker_task_definition_arn": state.worker_task_definition_arn,
        },
        "business": {
            "export_id": export_id,
            "terminal_status": final["status"],
            "s3_result": {
                "key": final["object_key"],
                "content_type": "application/json",
                "body": result_body,
                "etag": original_etag,
            },
            "tenant_key_partition_separation": True,
            "api_idempotency": {
                "duplicate_marker": duplicate_marker,
                "duplicate_status": duplicate_status_value,
                "same_export_id": duplicate_same_export,
                "row_idempotency_matches": row_idempotency_matches,
                "enqueue_confirmed": enqueue_confirmed,
                "attempts": int(row_attempts),
            },
            "worker_duplicate_delivery": {
                "attempts": 1,
                "s3_identity_unchanged": True,
                "consumed_noop": True,
            },
            "dlq": {"current_invocation": True, "message_id": dlq_message_id},
        },
        "task_proof": {
            "api": api_task["taskArn"],
            "worker": worker_task["taskArn"],
            "containers": containers,
            "post_business_reproof": True,
        },
    }


def command_evidence(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    socket_endpoint = _bind_claimed_outer(state)
    _assert_deployed_source(state)
    api, worker = _service_tasks(state)
    floci_labels = _inspect_labels("container", "pk-stack-lab-floci")
    assert floci_labels is not None
    expected_floci_labels, _ = _expected_outer_labels(state)
    if any(floci_labels.get(key) != value for key, value in expected_floci_labels.items()):
        raise LabError("Floci container ownership labels are invalid")
    services = _ecs_described_items(
        client("ecs").describe_services(
            cluster=state.cluster, services=[state.api_service, state.worker_service]
        ),
        "services",
        label="ECS evidence service inventory",
        allow_missing=True,
    )
    by_name = {service.get("serviceName"): service for service in services}
    return {
        "ok": True,
        "lab_version": __version__,
        "floci_image": FLOCI_IMAGE,
        "endpoint": HOST_ENDPOINT,
        "task_endpoint": TASK_ENDPOINT,
        "region": REGION,
        "source_digest": state.source_digest,
        "docker_socket": socket_endpoint,
        "docker": {
            "server_version": _run(
                ["docker", "version", "--format", "{{.Server.Version}}"]
            ).strip(),
            "compose_version": _run(["docker", "compose", "version", "--short"]).strip(),
        },
        "floci": {
            "container": "pk-stack-lab-floci",
            "labels": _label_subset(floci_labels, set(_OUTER_LABELS)),
            "image": _run(
                [
                    "docker",
                    "container",
                    "inspect",
                    "--format",
                    "{{.Config.Image}}",
                    "pk-stack-lab-floci",
                ]
            ).strip(),
        },
        "network": NETWORK,
        "resources": state.to_dict(),
        "ownership": {
            "run": state.run_id,
            "claim": state.claim_id,
            "labels": {
                "pk-stack-lab.managed": "true",
                "pk-stack-lab.run": state.run_id,
                "pk-stack-lab.claim": state.claim_id,
            },
            "manifest_sha256": ownership_hash(state),
        },
        "services": {
            role: {
                "name": name,
                "status": by_name.get(name, {}).get("status"),
                "running": by_name.get(name, {}).get("runningCount"),
                "task_definition": by_name.get(name, {}).get("taskDefinition"),
            }
            for role, name in (("api", state.api_service), ("worker", state.worker_service))
        },
        "tasks": {
            "api": {
                "arn": api["taskArn"],
                "definition": api["taskDefinitionArn"],
                "status": api["lastStatus"],
                "container": _task_container_evidence(api, "api", state),
            },
            "worker": {
                "arn": worker["taskArn"],
                "definition": worker["taskDefinitionArn"],
                "status": worker["lastStatus"],
                "container": _task_container_evidence(worker, "worker", state),
            },
        },
    }


def _tokenized_items(method: Any, key: str, **kwargs: Any) -> list[Any]:
    """Collect one AWS nextToken listing with cycle and shape checks."""
    token: str | None = None
    seen: set[str] = set()
    values: list[Any] = []
    for _ in range(10_000):
        request = dict(kwargs)
        if token is not None:
            request["nextToken"] = token
        response = method(**request)
        if not isinstance(response, dict):
            raise LabError("AWS listing returned a malformed response")
        failures = response.get("failures", [])
        if not isinstance(failures, list) or failures:
            raise LabError("AWS listing returned structured failures")
        page = response.get(key, [])
        if not isinstance(page, list):
            raise LabError("AWS listing returned a malformed item page")
        values.extend(page)
        next_token = response.get("nextToken")
        if next_token in (None, ""):
            return values
        if not isinstance(next_token, str) or next_token in seen:
            raise LabError("AWS listing returned an invalid pagination token")
        seen.add(next_token)
        token = next_token
    raise LabError("AWS listing exceeded the bounded page count")


def _exact_task_definition_arns(ecs: Any, state: RunState) -> tuple[str, ...]:
    """List every active or inactive revision for the two exact claim families."""
    values: set[str] = set()
    for family in (state.api_family, state.worker_family):
        pattern = re.compile(
            rf"^arn:aws:ecs:{re.escape(REGION)}:[0-9]{{12}}:task-definition/"
            rf"{re.escape(family)}:([1-9][0-9]*)$"
        )
        for status in ("ACTIVE", "INACTIVE"):
            arns = _tokenized_items(
                ecs.list_task_definitions,
                "taskDefinitionArns",
                familyPrefix=family,
                status=status,
                sort="ASC",
                maxResults=100,
            )
            for arn in arns:
                if not isinstance(arn, str):
                    raise LabError("task-definition inventory returned a malformed ARN")
                if pattern.fullmatch(arn):
                    values.add(arn)
    return tuple(sorted(values))


def _task_definition_artifact(ecs: Any, state: RunState, arn: str) -> tuple[str, str, str, str]:
    """Prove a Floci-projected definition and return role, digest, ref, and operation."""
    response = ecs.describe_task_definition(taskDefinition=arn, include=["TAGS"])
    definition = response.get("taskDefinition")
    tags = response.get("tags", definition.get("tags") if isinstance(definition, dict) else None)
    if tags is None:
        tags = ecs.list_tags_for_resource(resourceArn=arn).get("tags")
    if not isinstance(definition, dict) or not _owned(state, tags):
        raise LabError("task-definition inventory found foreign ownership")
    family = definition.get("family")
    role = (
        "api" if family == state.api_family else "worker" if family == state.worker_family else ""
    )
    pattern = re.compile(
        rf"^arn:aws:ecs:{re.escape(REGION)}:[0-9]{{12}}:task-definition/"
        rf"{re.escape(str(family))}:([1-9][0-9]*)$"
    )
    match = pattern.fullmatch(arn)
    containers = definition.get("containerDefinitions")
    if (
        not role
        or not match
        or definition.get("taskDefinitionArn") != arn
        or definition.get("revision") != int(match.group(1))
        or definition.get("networkMode") != "bridge"
        or definition.get("cpu") != "256"
        or definition.get("memory") != "512"
        or definition.get("runtimePlatform")
        != {"cpuArchitecture": "ARM64", "operatingSystemFamily": "LINUX"}
        or set(definition.get("requiresCompatibilities", [])) != {"EC2"}
        or definition.get("volumes", []) != []
        or not isinstance(containers, list)
        or len(containers) != 1
        or not isinstance(containers[0], dict)
    ):
        raise LabError("task-definition inventory failed the immutable contract")
    container = containers[0]
    environment = container.get("environment")
    labels = container.get("dockerLabels")
    if (
        not isinstance(environment, list)
        or any(not isinstance(item, dict) or set(item) != {"name", "value"} for item in environment)
        or (labels is not None and not isinstance(labels, dict))
    ):
        raise LabError("task-definition inventory has malformed container metadata")
    env_map = {item["name"]: item["value"] for item in environment}
    if len(env_map) != len(environment):
        raise LabError("task-definition inventory has duplicate environment keys")
    digest = env_map.get("PK_STACK_LAB_SOURCE_DIGEST")
    operation_id = env_map.get("PK_STACK_LAB_OPERATION")
    if (
        not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
        or not isinstance(operation_id, str)
        or not re.fullmatch(r"[0-9a-f]{32}", operation_id)
    ):
        raise LabError("task-definition inventory lacks immutable deployment identities")
    image_ref = f"{state.prefix}-{role}:{digest[:24]}"
    queue_url = env_map.get("PK_STACK_LAB_QUEUE_URL")
    parsed = urlparse(queue_url) if isinstance(queue_url, str) else None
    expected_env = {
        "PK_STACK_LAB_ROLE": role,
        "PK_STACK_LAB_ENDPOINT": TASK_ENDPOINT,
        "PK_STACK_LAB_REGION": REGION,
        "PK_STACK_LAB_QUEUE_URL": queue_url,
        "PK_STACK_LAB_TABLE": state.table,
        "PK_STACK_LAB_BUCKET": state.bucket,
        "PK_STACK_LAB_RUN": state.run_id,
        "PK_STACK_LAB_CLAIM": state.claim_id,
        "PK_STACK_LAB_OPERATION": operation_id,
        "PK_STACK_LAB_SOURCE_DIGEST": digest,
    }
    expected_labels = {
        "pk-stack-lab.managed": "true",
        "pk-stack-lab.project": PROJECT,
        "pk-stack-lab.run": state.run_id,
        "pk-stack-lab.claim": state.claim_id,
        "pk-stack-lab.source-digest": digest,
        "pk-stack-lab.operation": operation_id,
        "pk-stack-lab.role": role,
    }
    projected_controls = {
        "user": "65532:65532",
        "readonlyRootFilesystem": True,
        "linuxParameters": {"capabilities": {"drop": ["ALL"]}},
        "dockerSecurityOptions": ["no-new-privileges"],
        "dockerLabels": expected_labels,
    }
    expected_ports = (
        [{"containerPort": 8080, "hostPort": 0, "protocol": "tcp"}] if role == "api" else []
    )
    if (
        container.get("name") != role
        or container.get("image") != image_ref
        or container.get("essential") is not True
        or any(
            key in container and container.get(key) != value
            for key, value in projected_controls.items()
        )
        or container.get("mountPoints", []) != []
        or container.get("volumesFrom", []) != []
        or container.get("portMappings", []) != expected_ports
        or env_map != expected_env
        or parsed is None
        or parsed.scheme != "http"
        or parsed.hostname != "floci"
        or parsed.port != 4566
        or parsed.username
        or parsed.password
        or not parsed.path.rstrip("/").endswith(f"/{state.queue}")
    ):
        raise LabError("task-definition inventory drifted from its claimed artifact")
    return role, digest, image_ref, operation_id


def _reconcile_pending_task_definitions(state: RunState, ecs: Any) -> RunState:
    """Journal exact claimed revisions created before a prior hard exit."""
    observed_by_arn = {
        event.task_definition_arn: event
        for event in state.artifact_ledger
        if event.kind == "task_definition_observed"
    }
    observed_operations = {
        (event.operation_id, event.role)
        for event in state.artifact_ledger
        if event.kind == "task_definition_observed"
    }
    planned = [
        event
        for event in state.artifact_ledger
        if event.kind == "task_definition_planned"
        and (event.operation_id, event.role) not in observed_operations
    ]
    image_ids = {
        (event.operation_id, event.role): event.image_id
        for event in state.artifact_ledger
        if event.kind == "image_observed"
    }
    additions: list[ArtifactEvent] = []
    for arn in _exact_task_definition_arns(ecs, state):
        role, digest, image_ref, operation_id = _task_definition_artifact(ecs, state, arn)
        prior = observed_by_arn.get(arn)
        if prior is not None:
            if (
                prior.role,
                prior.source_digest,
                prior.image_ref,
                prior.operation_id,
            ) != (role, digest, image_ref, operation_id):
                raise LabError("observed task-definition artifact identity drifted")
            continue
        matches = [
            event
            for event in planned
            if (
                event.role,
                event.source_digest,
                event.image_ref,
                event.operation_id,
            )
            == (role, digest, image_ref, operation_id)
        ]
        if len(matches) != 1:
            raise LabError("unable to uniquely reconcile a claimed task-definition revision")
        plan = matches[0]
        image_id = image_ids.get((plan.operation_id, role), "")
        if not image_id:
            raise LabError("task-definition reconciliation lacks an observed image identity")
        additions.append(
            ArtifactEvent(
                seq=next_artifact_sequence(state) + len(additions),
                kind="task_definition_observed",
                operation_id=plan.operation_id,
                role=role,
                source_digest=digest,
                image_ref=image_ref,
                image_id=image_id,
                family=plan.family,
                task_definition_arn=arn,
            )
        )
        planned.remove(plan)
    if additions:
        state = append_artifact_events(ROOT, state, *additions)
    return state


def _image_targets(state: RunState) -> tuple[ImageTarget, ...]:
    targets: dict[tuple[str, str], str] = {}
    for event in state.artifact_ledger:
        key = (event.image_ref, event.source_digest)
        if event.kind == "image_planned":
            targets.setdefault(key, "")
        elif event.kind == "image_observed":
            targets[key] = event.image_id
    return tuple(
        ImageTarget(ref=ref, source_digest=digest, image_id=image_id)
        for (ref, digest), image_id in sorted(targets.items())
    )


def _image_ref_exists(ref: str) -> bool:
    values = [
        line.strip()
        for line in _run(
            [
                "docker",
                "image",
                "ls",
                "--filter",
                f"reference={ref}",
                "--format",
                "{{.Repository}}:{{.Tag}}",
            ]
        ).splitlines()
        if line.strip()
    ]
    if not values:
        return False
    if set(values) == {ref}:
        return True
    raise LabError("Docker image probe returned an ambiguous exact reference")


def _validate_image_target(
    state: RunState,
    target: ImageTarget,
    *,
    operation_id: str | None = None,
    require_present: bool = False,
) -> None:
    if not _image_ref_exists(target.ref):
        if require_present:
            raise LabError("required deterministic image reference is absent")
        return
    image_id = _run(["docker", "image", "inspect", "--format", "{{.Id}}", target.ref]).strip()
    labels = _docker_json(
        ["docker", "image", "inspect", "--format", "{{json .Config.Labels}}", target.ref]
    )
    required = {
        "pk-stack-lab.project": PROJECT,
        "pk-stack-lab.run": state.run_id,
        "pk-stack-lab.claim": state.claim_id,
        "pk-stack-lab.source-digest": target.source_digest,
    }
    planned_operations = {
        event.operation_id
        for event in state.artifact_ledger
        if event.kind == "image_planned"
        and event.image_ref == target.ref
        and event.source_digest == target.source_digest
    }
    if operation_id is not None:
        planned_operations &= {operation_id}
    if (
        (target.image_id and image_id != target.image_id)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id)
        or not isinstance(labels, dict)
        or {key: labels.get(key) for key in required} != required
        or labels.get("pk-stack-lab.operation") not in planned_operations
    ):
        raise LabError("Docker image target failed exact persisted provenance")


def _s3_object_keys(s3: Any, bucket: str) -> tuple[str, ...]:
    token: str | None = None
    seen: set[str] = set()
    keys: set[str] = set()
    for _ in range(10_000):
        request: dict[str, Any] = {"Bucket": bucket, "MaxKeys": 1000}
        if token is not None:
            request["ContinuationToken"] = token
        response = s3.list_objects_v2(**request)
        contents = response.get("Contents", [])
        if not isinstance(contents, list):
            raise LabError("S3 inventory returned a malformed object page")
        for item in contents:
            key = item.get("Key") if isinstance(item, dict) else None
            if not isinstance(key, str) or not key or len(key.encode("utf-8")) > 1024:
                raise LabError("S3 inventory returned an invalid object key")
            keys.add(key)
        if not response.get("IsTruncated", False):
            return tuple(sorted(keys))
        next_token = response.get("NextContinuationToken")
        if not isinstance(next_token, str) or not next_token or next_token in seen:
            raise LabError("S3 inventory returned an invalid continuation token")
        seen.add(next_token)
        token = next_token
    raise LabError("S3 inventory exceeded the bounded page count")


def _container_environment(name: str) -> dict[str, str]:
    raw = _docker_json(["docker", "container", "inspect", "--format", "{{json .Config.Env}}", name])
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise LabError("Docker task environment inventory was malformed")
    values: dict[str, str] = {}
    for item in raw:
        key, separator, value = item.partition("=")
        if not separator or not key or key in values:
            raise LabError("Docker task environment inventory was ambiguous")
        values[key] = value
    return values


def _validate_task_container_claim(state: RunState, name: str, labels: dict[str, str]) -> None:
    match = _TASK_CONTAINER.fullmatch(name)
    environment = _container_environment(name)
    role = match.group(2) if match is not None else ""
    identity = (
        environment.get("PK_STACK_LAB_OPERATION"),
        role,
        environment.get("PK_STACK_LAB_SOURCE_DIGEST"),
    )
    observed = [
        event
        for event in state.artifact_ledger
        if event.kind == "task_definition_observed"
        and (event.operation_id, event.role, event.source_digest) == identity
    ]
    image_ref = _run(
        ["docker", "container", "inspect", "--format", "{{.Config.Image}}", name]
    ).strip()
    image_id = _run(["docker", "container", "inspect", "--format", "{{.Image}}", name]).strip()
    if (
        match is None
        or len(observed) != 1
        or labels.get("floci") != "true"
        or labels.get("floci_emulator") != "floci-aws"
        or labels.get("io.floci") != "aws"
        or labels.get("io.floci.account") != "000000000000"
        or labels.get("io.floci.region") != REGION
        or labels.get("io.floci.service") != "ecs"
        or labels.get("io.floci.resource-id") != match.group(1)
        or labels.get("pk-stack-lab.project") != PROJECT
        or labels.get("pk-stack-lab.run") != state.run_id
        or labels.get("pk-stack-lab.claim") != state.claim_id
        or labels.get("pk-stack-lab.source-digest") != environment.get("PK_STACK_LAB_SOURCE_DIGEST")
        or environment.get("PK_STACK_LAB_CLAIM") != state.claim_id
        or environment.get("PK_STACK_LAB_RUN") != state.run_id
        or environment.get("PK_STACK_LAB_ROLE") != role
        or not re.fullmatch(r"[0-9a-f]{32}", environment.get("PK_STACK_LAB_OPERATION", ""))
        or not re.fullmatch(r"[0-9a-f]{64}", environment.get("PK_STACK_LAB_SOURCE_DIGEST", ""))
        or image_ref != (observed[0].image_ref if observed else "")
        or image_id != (observed[0].image_id if observed else "")
    ):
        raise LabError("Docker task target lacks exact current-claim identity")


def _validate_claim_task_container_names(state: RunState, names: list[str]) -> tuple[str, ...]:
    """Validate an already-complete daemon-wide Floci task inventory."""
    current: list[str] = []
    for raw_name in names:
        name = raw_name.strip()
        if not name:
            continue
        if not _TASK_CONTAINER.fullmatch(name):
            raise LabError("Docker task inventory returned an invalid exact name")
        labels = _inspect_labels("container", name, missing_ok=True)
        if labels is None:
            continue
        environment = _container_environment(name)
        if environment.get("PK_STACK_LAB_CLAIM") != state.claim_id:
            raise LabError("foreign Floci ECS task container shares the singleton lab daemon")
        _validate_task_container_claim(state, name, labels)
        current.append(name)
    return tuple(sorted(set(current)))


def _current_claim_task_containers(state: RunState) -> tuple[str, ...]:
    names = _run(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            "label=io.floci.service=ecs",
            "--format",
            "{{.Names}}",
        ]
    ).splitlines()
    return _validate_claim_task_container_names(state, names)


def _docker_task_targets(state: RunState, known: set[str]) -> tuple[str, ...]:
    """Bind task containers by exact persisted environment identity."""
    candidates = known | set(_current_claim_task_containers(state))
    for name in candidates:
        labels = _inspect_labels("container", name, missing_ok=True)
        if labels is not None:
            _validate_task_container_claim(state, name, labels)
    return tuple(sorted(candidates))


def _bucket_ownership_mode(s3: Any, state: RunState) -> str:
    """Classify only the exact bucket as absent, owned, or crash-intended."""
    try:
        s3.head_bucket(Bucket=state.bucket)
    except ClientError as exc:
        if _is_missing(exc, {"NoSuchBucket", "404", "NotFound"}):
            return "absent"
        raise
    try:
        response = s3.get_bucket_tagging(Bucket=state.bucket)
    except ClientError as exc:
        code = _error_code(exc)
        if code in {"NoSuchBucket", "404", "NotFound"}:
            # The exact bucket disappeared between the positive head and tag
            # probes.  Absence is the only safe conclusion.
            return "absent"
        if code not in {"NoSuchTagSet", "NoSuchTagSetError"}:
            raise
        if not state.bucket_create_intent:
            raise LabError("teardown inventory found an untagged bucket without create intent")
        # A missing tag set proves only that the exact requested bucket exists
        # without tags.  The persisted pre-create intent is the additional
        # authority needed to adopt that narrow crash remnant.
        return "create-intent"
    tags = response.get("TagSet") if isinstance(response, dict) else None
    if not isinstance(tags, list) or any(not isinstance(tag, dict) for tag in tags):
        raise LabError("S3 bucket tagging inventory was malformed")
    if _owned(state, tags):
        return "owned"
    if not tags and state.bucket_create_intent:
        return "create-intent"
    raise LabError("teardown inventory found a foreign S3 bucket")


def _reachable_aws_targets(state: RunState) -> tuple[RunState, AwsTeardownTargets, set[str]]:
    ecs, sqs, ddb, s3 = (client(name) for name in ("ecs", "sqs", "dynamodb", "s3"))
    state = _reconcile_pending_task_definitions(state, ecs)
    clusters = _ecs_described_items(
        ecs.describe_clusters(clusters=[state.cluster], include=["TAGS"]),
        "clusters",
        label="teardown ECS cluster inventory",
        allow_missing=True,
    )
    if len(clusters) > 1 or (clusters and not _owned(state, clusters[0].get("tags"))):
        raise LabError("teardown inventory found a foreign or ambiguous ECS cluster")
    cluster = NamedArnTarget(
        state.cluster, str(clusters[0].get("clusterArn", "")) if clusters else ""
    )
    services: list[NamedArnTarget] = []
    task_arns: set[str] = set()
    task_containers: set[str] = set()
    if clusters:
        for role, name in (("api", state.api_service), ("worker", state.worker_service)):
            found = _ecs_described_items(
                ecs.describe_services(cluster=state.cluster, services=[name], include=["TAGS"]),
                "services",
                label="teardown ECS service inventory",
                allow_missing=True,
            )
            if len(found) > 1 or (found and not _owned(state, found[0].get("tags"))):
                raise LabError("teardown inventory found a foreign or ambiguous ECS service")
            services.append(
                NamedArnTarget(name, str(found[0].get("serviceArn", "")) if found else "")
            )
            for desired in ("RUNNING", "STOPPED"):
                for arn in _tokenized_items(
                    ecs.list_tasks,
                    "taskArns",
                    cluster=state.cluster,
                    serviceName=name,
                    desiredStatus=desired,
                    maxResults=100,
                ):
                    if not isinstance(arn, str):
                        raise LabError("teardown inventory returned a malformed ECS task ARN")
                    described = _ecs_described_items(
                        ecs.describe_tasks(cluster=state.cluster, tasks=[arn], include=["TAGS"]),
                        "tasks",
                        label="teardown ECS task inventory",
                        allow_missing=False,
                    )
                    task_id = arn.rsplit("/", 1)[-1]
                    expected_family = state.api_family if role == "api" else state.worker_family
                    if (
                        len(described) != 1
                        or not _TASK_ID.fullmatch(task_id)
                        or (cluster.arn and described[0].get("clusterArn") != cluster.arn)
                        or f"task-definition/{expected_family}:"
                        not in str(described[0].get("taskDefinitionArn", ""))
                        or (
                            described[0].get("tags") is not None
                            and not _owned(state, described[0].get("tags"))
                        )
                    ):
                        raise LabError("teardown inventory found a foreign ECS task")
                    task_arns.add(arn)
                    task_containers.add(f"floci-ecs-{task_id}-{role}")
    else:
        services = [NamedArnTarget(state.api_service), NamedArnTarget(state.worker_service)]

    queues: list[QueueTarget] = []
    for name in (state.queue, state.dlq):
        try:
            url = sqs.get_queue_url(QueueName=name)["QueueUrl"]
        except ClientError as exc:
            if _is_missing(exc, {"QueueDoesNotExist", "AWS.SimpleQueueService.NonExistentQueue"}):
                queues.append(QueueTarget(name))
                continue
            raise
        if sqs.list_queue_tags(QueueUrl=url).get("Tags", {}) != _tags_dict(state):
            raise LabError("teardown inventory found a foreign queue")
        queues.append(QueueTarget(name, url))

    try:
        table_raw = ddb.describe_table(TableName=state.table)["Table"]
    except ClientError as exc:
        if not _is_missing(exc, {"ResourceNotFoundException"}):
            raise
        table = NamedArnTarget(state.table)
    else:
        table_arn = table_raw.get("TableArn")
        if not isinstance(table_arn, str) or not _owned(
            state, ddb.list_tags_of_resource(ResourceArn=table_arn).get("Tags")
        ):
            raise LabError("teardown inventory found a foreign DynamoDB table")
        table = NamedArnTarget(state.table, table_arn)

    bucket_mode = _bucket_ownership_mode(s3, state)
    if bucket_mode == "absent":
        bucket = BucketTarget(state.bucket, False, "none")
        object_keys: tuple[str, ...] = ()
    else:
        bucket = BucketTarget(state.bucket, True, "drain-all-unversioned")
        object_keys = _s3_object_keys(s3, state.bucket)

    definitions = _exact_task_definition_arns(ecs, state)
    observed = tuple(
        sorted(
            event.task_definition_arn
            for event in state.artifact_ledger
            if event.kind == "task_definition_observed"
        )
    )
    if set(definitions) - set(observed):
        raise LabError("task-definition inventory exceeds the reconciled artifact ledger")
    return (
        state,
        AwsTeardownTargets(
            cluster=cluster,
            services=tuple(services),
            queues=tuple(queues),
            table=table,
            bucket=bucket,
            task_arns=tuple(sorted(task_arns)),
            task_definition_families=(state.api_family, state.worker_family),
            task_definition_arns=observed,
            object_keys=object_keys,
        ),
        task_containers,
    )


def _build_teardown_plan(state: RunState, *, aws_mode: str) -> tuple[RunState, TeardownPlan]:
    if compose_digest(ROOT) != state.compose_sha256:
        raise LabError("Compose definition drifted from the original run claim")
    if aws_mode == "reachable":
        state, aws, known_task_containers = _reachable_aws_targets(state)
        phases = REACHABLE_TEARDOWN_PHASES
    elif aws_mode == "discard-unreachable":
        observed = tuple(
            sorted(
                event.task_definition_arn
                for event in state.artifact_ledger
                if event.kind == "task_definition_observed"
            )
        )
        aws = AwsTeardownTargets(
            cluster=NamedArnTarget(state.cluster),
            services=(NamedArnTarget(state.api_service), NamedArnTarget(state.worker_service)),
            queues=(QueueTarget(state.queue), QueueTarget(state.dlq)),
            table=NamedArnTarget(state.table),
            bucket=BucketTarget(state.bucket, False, "none"),
            task_definition_families=(state.api_family, state.worker_family),
            task_definition_arns=observed,
        )
        known_task_containers = set()
        phases = DISCARD_TEARDOWN_PHASES
    else:
        raise LabError("unknown teardown AWS mode")
    images = _image_targets(state)
    for target in images:
        _validate_image_target(state, target)
    verifier = f"{state.prefix}-verifier"
    labels = _inspect_labels("container", verifier, missing_ok=True)
    if labels is not None and (
        labels.get("pk-stack-lab.claim") != state.claim_id
        or labels.get("pk-stack-lab.component") != "verifier"
    ):
        raise LabError("teardown inventory found a foreign verifier")
    docker = DockerTeardownTargets(
        outer_container="pk-stack-lab-floci",
        network=NETWORK,
        verifier=verifier,
        task_containers=_docker_task_targets(state, known_task_containers),
        images=images,
    )
    return state, TeardownPlan(
        version=1,
        claim_id=state.claim_id,
        ledger_seq=len(state.artifact_ledger),
        ledger_sha256=artifact_ledger_hash(state.artifact_ledger),
        compose_sha256=state.compose_sha256,
        aws_mode=aws_mode,
        aws=aws,
        docker=docker,
        phases=phases,
    )


def _stale_image_tags(state: RunState, *, source_digest: str | None = None) -> list[str]:
    """Derive the two exact immutable tags for narrow state-less recovery."""
    digest = state.source_digest if source_digest is None else source_digest
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise LabError("stale recovery requires a concrete source digest")
    suffix = digest[:24]
    tags = [f"{state.prefix}-api:{suffix}", f"{state.prefix}-worker:{suffix}"]
    if any(
        not re.fullmatch(r"pklab-[a-z0-9-]{1,32}-(?:api|worker):[0-9a-f]{24}", tag) for tag in tags
    ):
        raise LabError("refusing unsafe local image cleanup name")
    return tags


def _service_target(ecs: Any, state: RunState, target: NamedArnTarget) -> dict[str, Any] | None:
    try:
        values = _ecs_described_items(
            ecs.describe_services(cluster=state.cluster, services=[target.name], include=["TAGS"]),
            "services",
            label="ECS service teardown postcondition",
            allow_missing=True,
        )
    except ClientError as exc:
        if _is_missing(exc, {"ClusterNotFoundException", "ServiceNotFoundException"}):
            return None
        raise
    if not values:
        return None
    if len(values) != 1:
        raise LabError("ECS service postcondition returned an ambiguous exact target")
    service = values[0]
    if not target.arn:
        raise LabError("an ECS service appeared after the teardown plan was frozen")
    if (
        service.get("serviceName") != target.name
        or service.get("serviceArn") != target.arn
        or not _owned(state, service.get("tags"))
    ):
        raise LabError("ECS service target drifted from the frozen teardown plan")
    return service


def _cluster_target(ecs: Any, state: RunState, target: NamedArnTarget) -> dict[str, Any] | None:
    values = _ecs_described_items(
        ecs.describe_clusters(clusters=[target.name], include=["TAGS"]),
        "clusters",
        label="ECS cluster teardown postcondition",
        allow_missing=True,
    )
    if not values:
        return None
    if len(values) != 1:
        raise LabError("ECS cluster postcondition returned an ambiguous exact target")
    cluster = values[0]
    if not target.arn:
        raise LabError("an ECS cluster appeared after the teardown plan was frozen")
    if (
        cluster.get("clusterName") != target.name
        or cluster.get("clusterArn") != target.arn
        or not _owned(state, cluster.get("tags"))
    ):
        raise LabError("ECS cluster target drifted from the frozen teardown plan")
    return cluster


def _compute_postcondition(ecs: Any, state: RunState, plan: TeardownPlan) -> bool:
    # An absent-at-freeze cluster must stay absent, and a present cluster must
    # remain bound to the exact frozen ARN and ownership tags.
    cluster = _cluster_target(ecs, state, plan.aws.cluster)
    if cluster is None:
        return _task_container_postcondition(state, plan)
    for target in plan.aws.services:
        service = _service_target(ecs, state, target)
        if service is not None and service.get("status") != "INACTIVE":
            return False
        if service is not None:
            running = _tokenized_items(
                ecs.list_tasks,
                "taskArns",
                cluster=state.cluster,
                serviceName=target.name,
                desiredStatus="RUNNING",
                maxResults=100,
            )
            if running:
                return False
    # The frozen cluster is dedicated to this run. Data deletion is allowed
    # only after *all* active services and compute disappear, including work
    # introduced after the plan was persisted under another name.
    if _tokenized_items(
        ecs.list_services,
        "serviceArns",
        cluster=state.cluster,
        maxResults=100,
    ):
        return False
    for desired_status in ("RUNNING", "PENDING"):
        if _tokenized_items(
            ecs.list_tasks,
            "taskArns",
            cluster=state.cluster,
            desiredStatus=desired_status,
            maxResults=100,
        ):
            return False
    for arn in plan.aws.task_arns:
        response = ecs.describe_tasks(cluster=state.cluster, tasks=[arn], include=["TAGS"])
        tasks = _ecs_described_items(
            response,
            "tasks",
            label="ECS task teardown postcondition",
            allow_missing=True,
        )
        if not tasks:
            continue
        if len(tasks) != 1:
            raise LabError("ECS task postcondition returned an ambiguous exact target")
        task = tasks[0]
        if (
            task.get("taskArn") != arn
            or task.get("lastStatus") != "STOPPED"
            or (plan.aws.cluster.arn and task.get("clusterArn") != plan.aws.cluster.arn)
            or task.get("taskDefinitionArn") not in plan.aws.task_definition_arns
            or (task.get("tags") is not None and not _owned(state, task.get("tags")))
        ):
            return False
    return _task_container_postcondition(state, plan)


def _phase_aws_compute_absent(state: RunState, plan: TeardownPlan) -> None:
    ecs = client("ecs")
    for target in plan.aws.services:
        service = _service_target(ecs, state, target)
        if service is None or service.get("status") == "INACTIVE":
            continue
        ecs.update_service(cluster=state.cluster, service=target.name, desiredCount=0)
        ecs.delete_service(cluster=state.cluster, service=target.name, force=True)
    # Floci can mark ECS tasks STOPPED even when its Docker removal failed.
    # Remove only the exact frozen, environment-bound task containers before
    # any queue/table/bucket deletion and make their absence part of the phase.
    _remove_frozen_task_containers(state, plan)
    for _ in range(90):
        if _compute_postcondition(ecs, state, plan):
            return
        time.sleep(1)
    raise LabError("frozen ECS services or tasks did not reach the stopped postcondition")


def _queue_is_absent(sqs: Any, target: QueueTarget) -> bool:
    try:
        sqs.get_queue_url(QueueName=target.name)
    except ClientError as exc:
        if _is_missing(exc, {"QueueDoesNotExist", "AWS.SimpleQueueService.NonExistentQueue"}):
            return True
        raise
    return False


def _table_is_absent(ddb: Any, target: NamedArnTarget) -> bool:
    try:
        ddb.describe_table(TableName=target.name)
    except ClientError as exc:
        if _is_missing(exc, {"ResourceNotFoundException"}):
            return True
        raise
    return False


def _bucket_is_absent(s3: Any, target: BucketTarget) -> bool:
    try:
        s3.head_bucket(Bucket=target.name)
    except ClientError as exc:
        if _is_missing(exc, {"404", "NoSuchBucket", "NotFound"}):
            return True
        raise
    return False


def _data_postcondition(state: RunState, plan: TeardownPlan) -> bool:
    sqs, ddb, s3 = (client(name) for name in ("sqs", "dynamodb", "s3"))
    return (
        all(_queue_is_absent(sqs, target) for target in plan.aws.queues)
        and _table_is_absent(ddb, plan.aws.table)
        and _bucket_is_absent(s3, plan.aws.bucket)
    )


def _phase_aws_data_absent(state: RunState, plan: TeardownPlan) -> None:
    if not _compute_postcondition(client("ecs"), state, plan):
        raise LabError("ECS compute prerequisite regressed before data deletion")
    sqs, ddb, s3 = (client(name) for name in ("sqs", "dynamodb", "s3"))
    for target in plan.aws.queues:
        if not target.url:
            if not _queue_is_absent(sqs, target):
                raise LabError("an SQS queue appeared after the teardown plan was frozen")
            continue
        if _queue_is_absent(sqs, target):
            continue
        url = sqs.get_queue_url(QueueName=target.name)["QueueUrl"]
        if url != target.url or sqs.list_queue_tags(QueueUrl=url).get("Tags", {}) != _tags_dict(
            state
        ):
            raise LabError("SQS queue drifted from the frozen teardown plan")
        sqs.delete_queue(QueueUrl=url)

    if not plan.aws.table.arn:
        if not _table_is_absent(ddb, plan.aws.table):
            raise LabError("a DynamoDB table appeared after the teardown plan was frozen")
    elif not _table_is_absent(ddb, plan.aws.table):
        raw = ddb.describe_table(TableName=plan.aws.table.name)["Table"]
        if raw.get("TableArn") != plan.aws.table.arn or not _owned(
            state,
            ddb.list_tags_of_resource(ResourceArn=plan.aws.table.arn).get("Tags"),
        ):
            raise LabError("DynamoDB table drifted from the frozen teardown plan")
        ddb.delete_table(TableName=plan.aws.table.name)

    bucket_mode = _bucket_ownership_mode(s3, state)
    if not plan.aws.bucket.present:
        if bucket_mode != "absent":
            raise LabError("an S3 bucket appeared after the teardown plan was frozen")
    elif bucket_mode != "absent":
        if plan.aws.bucket.object_strategy != "drain-all-unversioned":
            raise LabError("S3 bucket drifted from the frozen teardown plan")
        # The frozen target is the whole exact owned, unversioned bucket. Stop
        # compute first, then drain bounded pages from the beginning so an
        # in-flight write cannot escape a literal pre-compute key snapshot.
        for _ in range(10_000):
            response = s3.list_objects_v2(Bucket=plan.aws.bucket.name, MaxKeys=1000)
            contents = response.get("Contents", [])
            if not isinstance(contents, list):
                raise LabError("S3 deletion returned a malformed object page")
            if not contents:
                break
            keys = []
            for item in contents:
                key = item.get("Key") if isinstance(item, dict) else None
                if not isinstance(key, str) or not key:
                    raise LabError("S3 deletion returned an invalid object key")
                keys.append({"Key": key})
            deleted = s3.delete_objects(
                Bucket=plan.aws.bucket.name,
                Delete={"Objects": keys, "Quiet": True},
            )
            if deleted.get("Errors"):
                raise LabError("S3 object deletion returned one or more errors")
        else:
            raise LabError("S3 deletion exceeded the bounded batch count")
        s3.delete_bucket(Bucket=plan.aws.bucket.name)

    for _ in range(90):
        if (
            all(_queue_is_absent(sqs, target) for target in plan.aws.queues)
            and _table_is_absent(ddb, plan.aws.table)
            and _bucket_is_absent(s3, plan.aws.bucket)
        ):
            return
        time.sleep(1)
    raise LabError("frozen SQS, DynamoDB, or S3 targets remain after deletion")


def _phase_aws_definitions_cluster_absent(state: RunState, plan: TeardownPlan) -> None:
    ecs = client("ecs")
    if not _compute_postcondition(ecs, state, plan):
        raise LabError("ECS compute prerequisite regressed before definition deletion")
    if not _data_postcondition(state, plan):
        raise LabError("AWS data prerequisite regressed before definition deletion")
    current = set(_exact_task_definition_arns(ecs, state))
    planned = set(plan.aws.task_definition_arns)
    if current - planned:
        raise LabError("a task-definition revision appeared after the teardown plan was frozen")
    for arn in sorted(current):
        _task_definition_artifact(ecs, state, arn)
        response = ecs.describe_task_definition(taskDefinition=arn, include=["TAGS"])
        if response.get("taskDefinition", {}).get("status") == "ACTIVE":
            ecs.deregister_task_definition(taskDefinition=arn)
    remaining = [
        arn
        for arn in plan.aws.task_definition_arns
        if arn in set(_exact_task_definition_arns(ecs, state))
    ]
    for offset in range(0, len(remaining), 10):
        response = ecs.delete_task_definitions(taskDefinitions=remaining[offset : offset + 10])
        if response.get("failures"):
            raise LabError("task-definition deletion returned one or more failures")
    for _ in range(30):
        current = set(_exact_task_definition_arns(ecs, state))
        if not current:
            break
        if current - planned:
            raise LabError("an unplanned task-definition revision remains")
        time.sleep(1)
    else:
        raise LabError("frozen task-definition revisions remain active or inactive")

    cluster = _cluster_target(ecs, state, plan.aws.cluster)
    if cluster is not None:
        ecs.delete_cluster(cluster=plan.aws.cluster.name)
    for _ in range(30):
        if _cluster_target(ecs, state, plan.aws.cluster) is None:
            return
        time.sleep(1)
    raise LabError("frozen ECS cluster remains after deletion")


def _aws_postcondition(state: RunState, plan: TeardownPlan) -> None:
    ecs = client("ecs")
    if not _compute_postcondition(ecs, state, plan):
        raise LabError("ECS compute postcondition regressed after deletion")
    if not _data_postcondition(state, plan):
        raise LabError("AWS data postcondition regressed after deletion")
    if _exact_task_definition_arns(ecs, state):
        raise LabError("task-definition postcondition regressed after deletion")
    if _cluster_target(ecs, state, plan.aws.cluster) is not None:
        raise LabError("cluster postcondition regressed after deletion")


def _docker_task_container_absent(name: str) -> bool:
    return not _exact_docker_object_exists("container", name)


def _task_container_postcondition(state: RunState, plan: TeardownPlan) -> bool:
    if plan.docker.task_strategy != "remove-current-claim-ecs-containers":
        raise LabError("unknown Docker task cleanup strategy")
    if any(not _docker_task_container_absent(name) for name in plan.docker.task_containers):
        return False
    return not _current_claim_task_containers(state)


def _remove_frozen_task_containers(state: RunState, plan: TeardownPlan) -> None:
    if plan.docker.task_strategy != "remove-current-claim-ecs-containers":
        raise LabError("unknown Docker task cleanup strategy")
    targets = set(plan.docker.task_containers) | set(_current_claim_task_containers(state))
    for name in sorted(targets):
        labels = _inspect_labels("container", name, missing_ok=True)
        if labels is None:
            continue
        _validate_task_container_claim(state, name, labels)
        _run(["docker", "container", "rm", "-f", name])
    if not _task_container_postcondition(state, plan):
        raise LabError("frozen or current-claim Docker task container remains")


def _docker_outer_postcondition(state: RunState, plan: TeardownPlan) -> bool:
    return (
        not _exact_docker_object_exists("container", plan.docker.verifier)
        and not _exact_docker_object_exists("container", plan.docker.outer_container)
        and not _exact_docker_object_exists("network", plan.docker.network)
        and _task_container_postcondition(state, plan)
    )


def _phase_docker_outer_absent(state: RunState, plan: TeardownPlan, socket: str) -> None:
    outer_present = _exact_docker_object_exists("container", plan.docker.outer_container)
    network_present = _exact_docker_object_exists("network", plan.docker.network)
    if plan.aws_mode == "reachable" and outer_present:
        # Keep the final exact AWS proof adjacent to the irreversible emulator
        # stop. If the outer container is already absent, this phase is being
        # resumed after the stop boundary and relies on the durable preceding
        # aws_postconditions_passed checkpoint instead of calling dead AWS.
        _aws_postcondition(state, plan)
    labels = _inspect_labels("container", plan.docker.verifier, missing_ok=True)
    if labels is not None:
        if (
            labels.get("pk-stack-lab.claim") != state.claim_id
            or labels.get("pk-stack-lab.component") != "verifier"
        ):
            raise LabError("verifier drifted from the frozen teardown plan")
        _run(["docker", "container", "rm", "-f", plan.docker.verifier])
    # Idempotent backstop for a resumed phase; the compute phase already made
    # this a prerequisite for deleting queues, tables, and buckets.
    _remove_frozen_task_containers(state, plan)
    if outer_present or network_present:
        _assert_outer_ownership(state)
        if compose_digest(ROOT) != plan.compose_sha256:
            raise LabError("Compose definition drifted from the frozen teardown plan")
        _compose(socket, "down", claim_id=state.claim_id)
    if not _docker_outer_postcondition(state, plan):
        raise LabError("frozen Docker container or network target remains")


def _phase_floci_data_absent(state: RunState, plan: TeardownPlan) -> None:
    if not _docker_outer_postcondition(state, plan):
        raise LabError("Docker outer prerequisite regressed before Floci data deletion")
    _remove_floci_data_path(root=ROOT)
    if _floci_data_path(root=ROOT, create=False).exists():
        raise LabError("repository-local Floci data remains after deletion")


def _phase_docker_images_absent(state: RunState, plan: TeardownPlan) -> None:
    if not _docker_outer_postcondition(state, plan):
        raise LabError("Docker outer prerequisite regressed before image deletion")
    if _floci_data_path(root=ROOT, create=False).exists():
        raise LabError("Floci data prerequisite regressed before image deletion")
    for target in plan.docker.images:
        _validate_image_target(state, target)
    for target in plan.docker.images:
        if _image_ref_exists(target.ref):
            _run(["docker", "image", "rm", target.ref])
    if any(_image_ref_exists(target.ref) for target in plan.docker.images):
        raise LabError("one or more frozen Docker image references remain")


def _local_postcondition(state: RunState, plan: TeardownPlan) -> None:
    if (
        not _docker_outer_postcondition(state, plan)
        or any(_image_ref_exists(target.ref) for target in plan.docker.images)
        or _floci_data_path(root=ROOT, create=False).exists()
    ):
        raise LabError("local teardown postcondition found a frozen owned target")
    if load_state(ROOT) != state:
        raise LabError("run state changed before the terminal teardown checkpoint")


def _execute_teardown_phase(state: RunState, plan: TeardownPlan, phase: str, socket: str) -> None:
    if phase == "aws_compute_absent":
        _phase_aws_compute_absent(state, plan)
    elif phase == "aws_data_absent":
        _phase_aws_data_absent(state, plan)
    elif phase == "aws_definitions_cluster_absent":
        _phase_aws_definitions_cluster_absent(state, plan)
    elif phase == "aws_postconditions_passed":
        _aws_postcondition(state, plan)
    elif phase == "docker_outer_absent":
        _phase_docker_outer_absent(state, plan, socket)
    elif phase == "floci_data_absent":
        _phase_floci_data_absent(state, plan)
    elif phase == "docker_images_absent":
        _phase_docker_images_absent(state, plan)
    elif phase == "local_postconditions_passed":
        _local_postcondition(state, plan)
    else:
        raise LabError("teardown plan contained an unknown phase")


def _recover_stale_images(args: argparse.Namespace) -> dict[str, Any]:
    """Inventory or remove a state-less claim's two exact immutable image tags.

    This deliberately does not try to rediscover ownership by a prefix, image
    ID alone, dangling layers, or timestamps.  It is a narrowly scoped recovery
    application path under `labctl down`, usable only after normal `down` has
    removed a manifest but left one or both application tags behind.
    """
    run_id = getattr(args, "run_id", None)
    claim_id = getattr(args, "claim_id", None)
    digest = getattr(args, "source_digest", None)
    image_id = getattr(args, "image_id", None)
    if not all(isinstance(value, str) for value in (run_id, claim_id, digest, image_id)):
        raise LabError(
            "stale recovery requires --run-id, --claim-id, --source-digest, and --image-id"
        )
    if not re.fullmatch(r"[0-9a-f]{32}", claim_id):
        raise LabError("stale recovery claim ID must be 32 lowercase hexadecimal characters")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise LabError("stale recovery source digest must be a lowercase SHA-256")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise LabError("stale recovery image ID must be a concrete sha256 image ID")
    if not state_directory_absent(ROOT):
        raise LabError(
            "stale recovery requires absent .lab-state; use normal labctl down for a live claim"
        )
    # Bind the read-only Docker inventory to one actual local Unix daemon.
    _, socket, _ = _docker_identity()
    global _BOUND_SOCKET
    _BOUND_SOCKET = socket
    state = RunState.create(
        run_id,
        claim_id=claim_id,
    )
    tags = _stale_image_tags(state, source_digest=digest)
    if _exact_docker_object_exists(
        "container", "pk-stack-lab-floci"
    ) or _exact_docker_object_exists("network", NETWORK):
        raise LabError("stale recovery refuses while the outer lab container or network is present")
    task_names = [
        line.strip()
        for line in _run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                "name=^floci-ecs-",
                "--format",
                "{{.Names}}",
            ]
        ).splitlines()
        if line.strip()
    ]
    if any(not name.startswith("floci-ecs-") for name in task_names):
        raise LabError("stale recovery Docker filter returned an unexpected container name")
    if task_names:
        # Without the canonical state/task ARN capture, a Floci ECS container
        # cannot be attributed safely.  Preserve it for normal recovery.
        raise LabError("stale recovery refuses while any Floci ECS task container is present")
    expected_labels = {
        "pk-stack-lab.project": PROJECT,
        "pk-stack-lab.run": state.run_id,
        "pk-stack-lab.claim": state.claim_id,
        "pk-stack-lab.source-digest": digest,
    }
    # Probe each immutable ref independently.  A prior recovery process can be
    # killed after removing one tag, so absence of one member of the pair is a
    # valid retry state; absence of the entire pair is not sufficient evidence
    # to authorize a new recovery operation.
    present_tags = [tag for tag in tags if _image_ref_exists(tag)]
    if not present_tags:
        raise LabError("stale recovery found no claimed immutable image tags")
    proven: list[dict[str, str]] = []
    for tag in present_tags:
        actual_id = _run(["docker", "image", "inspect", "--format", "{{.Id}}", tag]).strip()
        labels = _docker_json(
            ["docker", "image", "inspect", "--format", "{{json .Config.Labels}}", tag]
        )
        if actual_id != image_id or not isinstance(labels, dict):
            raise LabError("stale recovery image ID or labels did not match the supplied claim")
        normalized = {str(key): str(value) for key, value in labels.items()}
        if {key: normalized.get(key) for key in expected_labels} != expected_labels:
            raise LabError(
                "stale recovery image provenance labels did not exactly match the supplied claim"
            )
        proven.append({"tag": tag, "image_id": actual_id})
    plan = {
        "run": state.run_id,
        "claim": state.claim_id,
        "images": proven,
        "already_absent": [tag for tag in tags if tag not in present_tags],
        "state_absent": True,
    }
    if not getattr(args, "apply_stale_recovery", False):
        return {"ok": True, "recovery": {"dry_run": True, "plan": plan}}
    # Every target has been fully proven before the first Docker mutation.
    for item in proven:
        _run(["docker", "image", "rm", item["tag"]])
    if any(_image_ref_exists(tag) for tag in tags):
        raise LabError("stale recovery deletion left a claimed immutable image tag")
    return {"ok": True, "recovery": {"dry_run": False, "removed": proven}}


def command_down(_: argparse.Namespace) -> dict[str, Any]:
    if getattr(_, "recover_stale", False):
        return _recover_stale_images(_)
    state = load_state(ROOT)
    socket_endpoint = _bind_daemon(state)
    _assert_outer_ownership(state)
    discard = bool(getattr(_, "teardown_unreachable_emulator", False))
    if state.teardown is None:
        if discard:
            _require_unreachable_health_endpoint()
        mode = "discard-unreachable" if discard else "reachable"
        state, plan = _build_teardown_plan(state, aws_mode=mode)
        # This durable hash-bound plan precedes the first delete/update/down/rm.
        state = install_teardown_plan(ROOT, state, plan)
    else:
        plan = state.teardown.plan
        if discard and plan.aws_mode == "reachable":
            _require_unreachable_health_endpoint()
            # Preserve every target from the frozen reachable inventory. This atomic,
            # hash-bound transition is the only supported teardown mode change.
            state = transition_teardown_to_discard(ROOT, state)
            assert state.teardown is not None
            plan = state.teardown.plan

    assert state.teardown is not None
    for phase in plan.phases[len(state.teardown.completed_phases) :]:
        _execute_teardown_phase(state, plan, phase, socket_endpoint)
        state = complete_teardown_phase(ROOT, state, phase)
    # Terminal state is checkpointed while the recovery manifest still exists.
    # Re-run the complete local proof even when a previous process checkpointed
    # every phase but crashed before unlinking the recovery manifest.
    _local_postcondition(state, plan)
    remove_state_manifest(ROOT)
    _remove_empty_state_dir(root=ROOT)
    if not state_directory_absent(ROOT):
        raise LabError("local state directory is not empty after terminal teardown")
    transition = state.teardown.transition
    return {
        "ok": True,
        "run": state.run_id,
        "cleanup": {
            "aws_mode": plan.aws_mode,
            "control_plane": "deleted" if plan.aws_mode == "reachable" else "discarded",
            "ecs_tasks": len(plan.aws.task_arns),
            "floci_container": 0,
            "network": 0,
            "floci_data": 0,
            "images": len(plan.docker.images),
            "completed_phases": list(plan.phases),
            "control_plane_transition": (
                {
                    "from_aws_mode": transition.from_aws_mode,
                    "to_aws_mode": plan.aws_mode,
                    "reason": transition.reason,
                    "from_plan_sha256": transition.from_plan_sha256,
                    "to_plan_sha256": state.teardown.plan_sha256,
                    "completed_before": list(transition.from_completed_phases),
                }
                if transition is not None
                else None
            ),
        },
    }


COMMANDS = {
    "doctor": command_doctor,
    "up": command_up,
    "deploy": command_deploy,
    "status": command_status,
    "verify": command_verify,
    "evidence": command_evidence,
    "down": command_down,
}


class _ArgumentFailure(ValueError):
    """A bounded parser error that main can render as requested JSON."""


class _LabArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _ArgumentFailure(_safe_text(message))


def _json_requested(argv: list[str]) -> bool:
    """Recognize only the two exact JSON switches before argparse can exit."""
    return "--output=json" in argv or any(
        index + 1 < len(argv) and value == "--output" and argv[index + 1] == "json"
        for index, value in enumerate(argv)
    )


def main(argv: list[str] | None = None) -> None:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parser = _LabArgumentParser(prog="pk-stack-lab")
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("--output", choices=("text", "json"), default="text")
    parser.add_argument("--run-id", help="optional safe deterministic run id (up only)")
    parser.add_argument(
        "--acknowledge-docker-socket",
        action="store_true",
        help="required for up: the Docker socket grants root-equivalent daemon control",
    )
    parser.add_argument(
        "--recover-stale",
        action="store_true",
        help="inventory state-less exact image recovery under down",
    )
    parser.add_argument(
        "--apply-stale-recovery",
        action="store_true",
        help="apply a fully proven stale-image recovery plan",
    )
    parser.add_argument("--claim-id", help="opaque 32-hex claim ID required by stale recovery")
    parser.add_argument("--source-digest", help="64-hex build digest required by stale recovery")
    parser.add_argument("--image-id", help="concrete sha256 image ID required by stale recovery")
    parser.add_argument(
        "--teardown-unreachable-emulator",
        action="store_true",
        help="explicitly tear down an unreachable local Floci emulator after a documented endpoint failure",
    )
    try:
        args = parser.parse_args(raw_argv)
    except _ArgumentFailure as exc:
        if _json_requested(raw_argv):
            print(
                json.dumps(
                    {"ok": False, "error": _safe_text(str(exc)), "command": None}, sort_keys=True
                )
            )
            raise SystemExit(2)
        argparse.ArgumentParser.error(parser, str(exc))
    try:
        with _lifecycle_lock():
            result = COMMANDS[args.command](args)
    except Exception as exc:  # noqa: BLE001 - JSON mode must bound every ordinary failure.
        result = {"ok": False, "error": _safe_text(str(exc)), "command": args.command}
        if args.output == "json":
            print(json.dumps(result, sort_keys=True))
        else:
            print(f"{args.command}: {result['error']}", file=sys.stderr)
        raise SystemExit(1)
    if args.output == "json":
        print(json.dumps(result, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
