"""The intentionally small, deterministic `labctl` control surface."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from botocore.exceptions import BotoCoreError, ClientError

from . import __version__
from .aws import client
from .config import (
    FLOCI_IMAGE,
    HOST_ENDPOINT,
    NETWORK,
    PROJECT,
    REGION,
    TASK_ENDPOINT,
    RunState,
    SafetyError,
    claim_state,
    load_state,
    ownership_hash,
    ownership_tags,
    remove_state_manifest,
    save_state,
    source_digest,
    state_dir,
    state_directory_absent,
    validate_host_endpoint,
)

ROOT = Path(__file__).resolve().parents[2]
MAX_READ = 8192
MAX_RESULT_BYTES = 4096
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


class LabError(RuntimeError):
    """A controlled lifecycle failure suitable for machine-readable output."""


def _run(args: list[str], *, env: dict[str, str] | None = None, timeout: int = 90) -> str:
    clean = _clean_subprocess_env(env)
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            env=clean,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LabError(f"command failed: {args[0]}") from exc
    if completed.returncode:
        raise LabError(f"command failed ({args[0]}): {_safe_text(completed.stdout)}")
    return completed.stdout[:MAX_READ]


def _clean_subprocess_env(extra: dict[str, str] | None = None) -> dict[str, str]:
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
    if _BOUND_SOCKET:
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


def _docker_identity() -> tuple[str, str, str]:
    """Discover an actual Unix Docker socket and immutable daemon identity."""
    context = _run(["docker", "context", "show"]).strip()
    raw = _run(
        ["docker", "context", "inspect", context, "--format", "{{json .Endpoints.docker.Host}}"]
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
    daemon_id = _run(["docker", "info", "--format", "{{.ID}}"]).strip()
    if not daemon_id or len(daemon_id) > 256:
        raise LabError("Docker daemon did not provide a valid identity")
    return context, f"unix://{resolved}", daemon_id


def _docker_socket() -> str:
    """Compatibility helper retained for focused unit tests."""
    return _docker_identity()[1]


def _bind_daemon(state: RunState) -> str:
    """Bind all later Docker/Compose operations to the claim's exact daemon."""
    global _BOUND_SOCKET
    # Deterministic unit fixtures created before `up` gained daemon metadata
    # deliberately use the empty sentinel.  Real `up` never emits it.
    if not state.docker_socket:
        _BOUND_SOCKET = _docker_socket()
        return _BOUND_SOCKET
    context, socket, daemon_id = _docker_identity()
    if (
        state.docker_context != context
        or state.docker_socket != socket
        or state.docker_daemon_id != daemon_id
    ):
        raise LabError("Docker context, socket, or daemon identity drifted from the run claim")
    _BOUND_SOCKET = socket
    return socket


def _floci_data_path(*, root: Path = ROOT, create: bool) -> Path:
    """Return the sole repository-local persistent path mounted into Floci."""
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


def _remove_floci_data_path(*, root: Path = ROOT) -> None:
    state = state_dir(root)
    data = _floci_data_path(root=root, create=False)
    if data.is_symlink() or (data.exists() and (not data.is_dir() or data.parent != state)):
        raise LabError("refusing unsafe Floci data cleanup path")
    if not data.exists():
        return
    # `data` is the exact validated repository-local bind mount, never a glob or external path.
    shutil.rmtree(data)


def _remove_empty_state_dir(*, root: Path = ROOT) -> None:
    """Best-effort removal of exactly an empty direct state directory.

    The manifest is intentionally removed immediately before this call.  A
    non-empty directory is never traversed or deleted; it remains as evidence
    for an operator rather than widening cleanup scope.
    """
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


def _assert_outer_ownership() -> None:
    container = _inspect_labels("container", "pk-stack-lab-floci", missing_ok=True)
    if container is not None and any(
        container.get(key) != value for key, value in _OUTER_LABELS.items()
    ):
        raise LabError("refusing a pre-existing foreign container named pk-stack-lab-floci")
    network = _inspect_labels("network", NETWORK, missing_ok=True)
    if network is not None and any(
        network.get(key) != value for key, value in _NETWORK_LABELS.items()
    ):
        raise LabError("refusing a pre-existing foreign network named pk-stack-lab-net")


def _compose_image(socket_endpoint: str) -> str:
    values = [
        line.strip()
        for line in _compose(socket_endpoint, "config", "--images").splitlines()
        if line.strip()
    ]
    if values != [FLOCI_IMAGE]:
        raise LabError("Compose does not resolve to the required immutable Floci image")
    return values[0]


def _compose_env(socket_endpoint: str) -> dict[str, str]:
    return {
        "DOCKER_HOST": socket_endpoint,
        "PK_STACK_LAB_DOCKER_SOCKET": socket_endpoint.removeprefix("unix://"),
        # `compose config` used by doctor must also work before `up` creates
        # disposable state.  `up` creates and validates this exact path before
        # any compose mutation.
        "PK_STACK_LAB_FLOCI_DATA": str(state_dir(ROOT) / "floci-data"),
    }


def _compose(socket_endpoint: str, *args: str, timeout: int = 120) -> str:
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
        env=_compose_env(socket_endpoint),
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
        with urlopen(request, timeout=5) as response:
            payload = response.read(MAX_READ)
            return response.status, json.loads(payload)
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
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


def _provision(state: RunState) -> dict[str, str]:
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
    s3.create_bucket(Bucket=state.bucket)
    s3.put_bucket_tagging(Bucket=state.bucket, Tagging={"TagSet": ownership_tags(state)})
    ecs.create_cluster(clusterName=state.cluster, tags=_ecs_tags(state))
    return {"queue_url": queue_url, "dlq_url": dlq_url}


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
    _assert_outer_ownership()
    _compose_image(socket_endpoint)
    state = RunState.create(
        args.run_id,
        claim_id=secrets.token_hex(16),
        docker_context=context,
        docker_socket=socket_endpoint,
        docker_daemon_id=daemon_id,
    )
    # Persist before provisioning so `down` can recover any partially-created tagged resource.
    claim_state(ROOT, state)
    _floci_data_path(create=True)
    _compose(socket_endpoint, "up", "-d", "--wait")
    _wait_health()
    resources = _provision(state)
    return {"ok": True, "run": state.run_id, "resources": state.to_dict(), "queue_urls": resources}


def _task_definition(state: RunState, *, role: str, image: str, queue_url: str) -> dict[str, Any]:
    environment = [
        {"name": "PK_STACK_LAB_ROLE", "value": role},
        {"name": "PK_STACK_LAB_ENDPOINT", "value": TASK_ENDPOINT},
        {"name": "PK_STACK_LAB_REGION", "value": REGION},
        {"name": "PK_STACK_LAB_QUEUE_URL", "value": queue_url},
        {"name": "PK_STACK_LAB_TABLE", "value": state.table},
        {"name": "PK_STACK_LAB_BUCKET", "value": state.bucket},
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
        services = response.get("services", [])
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
                arns = ecs.list_tasks(
                    cluster=state.cluster, serviceName=name, desiredStatus="RUNNING"
                ).get("taskArns", [])
                tasks = ecs.describe_tasks(cluster=state.cluster, tasks=arns).get("tasks", [])
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


def command_deploy(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    _bind_daemon(state)  # Fail before building if Docker is not usable.
    digest = source_digest(ROOT)
    state = replace(
        state,
        source_digest=digest,
        api_image_id="",
        worker_image_id="",
        api_task_definition_arn="",
        worker_task_definition_arn="",
    )
    api_image, worker_image = (
        f"{state.prefix}-api:{digest[:24]}",
        f"{state.prefix}-worker:{digest[:24]}",
    )
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
            "-t",
            api_image,
            str(ROOT),
        ],
        timeout=300,
    )
    _run(["docker", "tag", api_image, worker_image])
    api_image_id = _run(["docker", "image", "inspect", "--format", "{{.Id}}", api_image]).strip()
    worker_image_id = _run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", worker_image]
    ).strip()
    if not api_image_id or api_image_id != worker_image_id:
        raise LabError("Docker build did not produce one concrete immutable image identity")
    state = replace(state, api_image_id=api_image_id, worker_image_id=worker_image_id)
    save_state(ROOT, state)
    sqs, ecs = client("sqs"), client("ecs")
    queue_url = sqs.get_queue_url(QueueName=state.queue)["QueueUrl"]
    # Floci returns the task-reachable hostname because FLOCI_HOSTNAME is set.
    parsed = urlparse(queue_url)
    if parsed.hostname != "floci" or parsed.username or parsed.password:
        raise LabError("Floci did not return a task-network SQS URL")
    api_td = ecs.register_task_definition(
        **_task_definition(state, role="api", image=api_image, queue_url=queue_url)
    )["taskDefinition"]
    state = replace(state, api_task_definition_arn=api_td["taskDefinitionArn"])
    save_state(ROOT, state)
    worker_td = ecs.register_task_definition(
        **_task_definition(state, role="worker", image=worker_image, queue_url=queue_url)
    )["taskDefinition"]
    state = replace(state, worker_task_definition_arn=worker_td["taskDefinitionArn"])
    save_state(ROOT, state)
    for name, task_definition in (
        (state.api_service, api_td["taskDefinitionArn"]),
        (state.worker_service, worker_td["taskDefinitionArn"]),
    ):
        existing = ecs.describe_services(
            cluster=state.cluster, services=[name], include=["TAGS"]
        ).get("services", [])
        if len(existing) > 1:
            raise LabError("ECS service inventory returned an ambiguous exact name")
        if existing:
            if not _owned(state, existing[0].get("tags")):
                raise LabError("refusing to update ECS service without exact current-claim tags")
            ecs.update_service(
                cluster=state.cluster,
                service=name,
                taskDefinition=task_definition,
                desiredCount=1,
                forceNewDeployment=True,
                propagateTags="SERVICE",
            )
        else:
            ecs.create_service(
                cluster=state.cluster,
                serviceName=name,
                taskDefinition=task_definition,
                desiredCount=1,
                launchType="EC2",
                tags=_ecs_tags(state),
                propagateTags="SERVICE",
            )
    state = replace(
        state,
        api_image_id=api_image_id,
        worker_image_id=worker_image_id,
        api_task_definition_arn=api_td["taskDefinitionArn"],
        worker_task_definition_arn=worker_td["taskDefinitionArn"],
    )
    services = _wait_services(state)
    save_state(ROOT, state)
    return {
        "ok": True,
        "run": state.run_id,
        "source_digest": digest,
        "image_id": api_image_id,
        "task_definitions": {
            "api": api_td["taskDefinitionArn"],
            "worker": worker_td["taskDefinitionArn"],
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
        services = ecs.describe_services(
            cluster=state.cluster, services=[service], include=["TAGS"]
        ).get("services", [])
        if len(services) != 1 or not _owned(state, services[0].get("tags")):
            raise LabError(f"{role} ECS service lacks exact current-run ownership tags")
        arns = ecs.list_tasks(
            cluster=state.cluster, serviceName=service, desiredStatus="RUNNING"
        ).get("taskArns", [])
        if len(arns) != 1:
            raise LabError(f"expected exactly one running {role} ECS task")
        tasks = ecs.describe_tasks(cluster=state.cluster, tasks=arns, include=["TAGS"]).get(
            "tasks", []
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
    try:
        raw = _run(
            [
                "docker",
                "run",
                "--rm",
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
                container["image"],
                "-c",
                script,
            ],
            timeout=15,
        )
    finally:
        # `--rm` covers normal completion; errors and timeouts still receive
        # exact-name cleanup before a later verifier can be attempted.
        try:
            if _exact_docker_object_exists("container", verifier_name):
                _run(["docker", "container", "rm", "-f", verifier_name])
        except LabError:
            if sys.exc_info()[0] is None:
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
    if not isinstance(networks, dict) or NETWORK not in networks:
        raise LabError("real ECS task container is not on the dedicated lab network")
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
    if (
        user != "65532:65532"
        or readonly != "true"
        or not isinstance(cap_drop, list)
        or "ALL" not in cap_drop
        or not isinstance(security_opt, list)
        or "no-new-privileges" not in security_opt
    ):
        raise LabError("real ECS task container did not enforce required security fields")
    return {
        "name": name,
        "role": role,
        "image": image,
        "image_id": image_id,
        "network": NETWORK,
        "security": {
            "user": user,
            "readonly": True,
            "cap_drop": cap_drop,
            "security_opt": security_opt,
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


def command_status(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    _bind_daemon(state)
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


def command_verify(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    _bind_daemon(state)
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
    if status != 202 or created.get("status") not in {"QUEUED", "COMPLETE"}:
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
    if duplicate_status != 202 or duplicate.get("id") != export_id:
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
        raise LabError("tenant isolation check failed")
    s3 = client("s3")
    _, original_etag = _verify_result_object(
        s3, state, tenant=tenant, export_id=export_id, object_key=final["object_key"]
    )
    ddb = client("dynamodb")
    key = {"pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}}
    before = ddb.get_item(TableName=state.table, Key=key).get("Item", {})
    if before.get("attempts", {}).get("N") != "1":
        raise LabError("happy-path worker attempts were not exactly one")
    sqs = client("sqs")
    queue_url = sqs.get_queue_url(QueueName=state.queue)["QueueUrl"]
    sqs.send_message(
        QueueUrl=queue_url, MessageBody=json.dumps({"tenant": tenant, "id": export_id})
    )
    duplicate_noop = False
    for _ in range(16):
        current = ddb.get_item(TableName=state.table, Key=key).get("Item", {})
        _, current_etag = _verify_result_object(
            s3, state, tenant=tenant, export_id=export_id, object_key=final["object_key"]
        )
        if (
            current.get("attempts", {}).get("N") == "1"
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
    return {
        "ok": True,
        "run": state.run_id,
        "api_transport": "bounded HTTP from a transient hardened verifier container to the exact real ECS API task",
        "resources": state.to_dict(),
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
            "s3_object": final["object_key"],
            "tenant_key_partition_separation": True,
            "api_idempotency": True,
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
        },
    }


def command_evidence(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    _assert_deployed_source(state)
    api, worker = _service_tasks(state)
    socket_endpoint = _bind_daemon(state)
    floci_labels = _inspect_labels("container", "pk-stack-lab-floci")
    assert floci_labels is not None
    if any(floci_labels.get(key) != value for key, value in _OUTER_LABELS.items()):
        raise LabError("Floci container ownership labels are invalid")
    services = (
        client("ecs")
        .describe_services(
            cluster=state.cluster, services=[state.api_service, state.worker_service]
        )
        .get("services", [])
    )
    by_name = {service.get("serviceName"): service for service in services}
    return {
        "ok": True,
        "lab_version": __version__,
        "floci_image": FLOCI_IMAGE,
        "endpoint": HOST_ENDPOINT,
        "task_endpoint": TASK_ENDPOINT,
        "region": REGION,
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


def _delete_owned_resources(state: RunState) -> list[str]:
    ecs, sqs, ddb, s3 = (client(name) for name in ("ecs", "sqs", "dynamodb", "s3"))
    leaked_container_names: list[str] = []
    try:
        cluster = ecs.describe_clusters(clusters=[state.cluster], include=["TAGS"]).get(
            "clusters", []
        )
        if cluster and not _owned(state, cluster[0].get("tags")):
            raise LabError("refusing to delete ECS cluster without exact ownership tags")
        for role, service_name in (("api", state.api_service), ("worker", state.worker_service)):
            services = ecs.describe_services(
                cluster=state.cluster, services=[service_name], include=["TAGS"]
            ).get("services", [])
            if services:
                if not _owned(state, services[0].get("tags")):
                    raise LabError("refusing to delete ECS service without exact ownership tags")
                for desired in ("RUNNING", "STOPPED"):
                    for arn in ecs.list_tasks(
                        cluster=state.cluster, serviceName=service_name, desiredStatus=desired
                    ).get("taskArns", []):
                        task_id = arn.rsplit("/", 1)[-1]
                        if not _TASK_ID.fullmatch(task_id):
                            raise LabError("unexpected owned ECS task identity")
                        described = ecs.describe_tasks(
                            cluster=state.cluster, tasks=[arn], include=["TAGS"]
                        ).get("tasks", [])
                        if len(described) != 1 or (
                            described[0].get("tags") is not None
                            and not _owned(state, described[0].get("tags"))
                        ):
                            raise LabError("refusing cleanup of task without exact ownership tags")
                        candidate = f"floci-ecs-{task_id}-{role}"
                        if candidate not in leaked_container_names:
                            leaked_container_names.append(candidate)
    except ClientError as exc:
        if not _is_missing(exc, {"ClusterNotFoundException"}):
            raise
    for service in (state.api_service, state.worker_service):
        try:
            ecs.update_service(cluster=state.cluster, service=service, desiredCount=0)
            ecs.delete_service(cluster=state.cluster, service=service, force=True)
        except ClientError as exc:
            if not _is_missing(exc, {"ServiceNotFoundException", "ClusterNotFoundException"}):
                raise
    try:
        for _ in range(45):
            pending = sum(
                len(
                    ecs.list_tasks(
                        cluster=state.cluster, serviceName=service, desiredStatus="RUNNING"
                    ).get("taskArns", [])
                )
                for service in (state.api_service, state.worker_service)
            )
            if not pending:
                break
            time.sleep(1)
        else:
            raise LabError("owned ECS tasks did not stop before cleanup")
    except ClientError as exc:
        if not _is_missing(exc, {"ClusterNotFoundException"}):
            raise
    for name in (state.queue, state.dlq):
        try:
            url = sqs.get_queue_url(QueueName=name)["QueueUrl"]
            tags = sqs.list_queue_tags(QueueUrl=url).get("Tags", {})
            if tags != _tags_dict(state):
                raise LabError("refusing to delete queue without exact ownership tags")
            sqs.delete_queue(QueueUrl=url)
        except ClientError as exc:
            if not _is_missing(exc, {"QueueDoesNotExist"}):
                raise
    try:
        description = ddb.describe_table(TableName=state.table)["Table"]
        if not _owned(state, description.get("Tags")):
            # DynamoDB DescribeTable may omit tags; retrieve separately.
            arn = description["TableArn"]
            if not _owned(state, ddb.list_tags_of_resource(ResourceArn=arn).get("Tags")):
                raise LabError("refusing to delete table without exact ownership tags")
        ddb.delete_table(TableName=state.table)
    except ClientError as exc:
        if not _is_missing(exc, {"ResourceNotFoundException"}):
            raise
    try:
        tags = s3.get_bucket_tagging(Bucket=state.bucket).get("TagSet", [])
        if not _owned(state, tags):
            raise LabError("refusing to delete bucket without exact ownership tags")
        objects = s3.list_objects_v2(Bucket=state.bucket, MaxKeys=1000).get("Contents", [])
        if objects:
            s3.delete_objects(
                Bucket=state.bucket,
                Delete={"Objects": [{"Key": entry["Key"]} for entry in objects], "Quiet": True},
            )
        s3.delete_bucket(Bucket=state.bucket)
    except ClientError as exc:
        if not _is_missing(exc, {"NoSuchBucket"}):
            raise
    try:
        ecs.delete_cluster(cluster=state.cluster)
    except ClientError as exc:
        if not _is_missing(exc, {"ClusterNotFoundException"}):
            raise
    return leaked_container_names


def _remaining_owned_task_leaks(task_container_names: list[str]) -> list[str]:
    """Find only Floci ECS containers whose resource ID was captured from this run."""
    task_ids = {
        match.group(1)
        for name in task_container_names
        if (match := _TASK_CONTAINER.fullmatch(name))
    }
    if not task_ids:
        return []
    names = [
        line.strip()
        for line in _run(
            ["docker", "ps", "-a", "--filter", "label=floci=true", "--format", "{{.Names}}"]
        ).splitlines()
        if line.strip()
    ]
    leaks: list[str] = []
    for name in names:
        if not _TASK_CONTAINER.fullmatch(name):
            continue
        labels = _inspect_labels("container", name)
        assert labels is not None
        if (
            labels.get("io.floci.service") == "ecs"
            and labels.get("io.floci.resource-id") in task_ids
        ):
            leaks.append(name)
    return leaks


def _owned_image_tags(state: RunState) -> list[str]:
    """Only exact persisted content-derived tags are eligible for removal."""
    suffix = state.source_digest[:24] if state.source_digest else "0.1"
    tags = [f"{state.prefix}-api:{suffix}", f"{state.prefix}-worker:{suffix}"]
    if any(
        not re.fullmatch(r"pklab-[a-z0-9-]{1,32}-(?:api|worker):(?:0\.1|[0-9a-f]{24})", tag)
        for tag in tags
    ):
        raise LabError("refusing unsafe local image cleanup name")
    return tags


def _build_deletion_plan(state: RunState) -> dict[str, Any]:
    """Read and validate every currently claim-addressable target before mutation.

    The plan contains only exact names/ARNs derived from the canonical manifest;
    it never performs a prefix scan or treats an arbitrary service error as
    absence.  A caller must complete this pass before issuing any lifecycle
    delete/update/compose/image command.
    """
    ecs, sqs, ddb, s3 = (client(name) for name in ("ecs", "sqs", "dynamodb", "s3"))
    plan: dict[str, Any] = {"tasks": [], "images": [], "definitions": [], "objects": []}
    clusters = ecs.describe_clusters(clusters=[state.cluster], include=["TAGS"]).get("clusters", [])
    if len(clusters) > 1 or (clusters and not _owned(state, clusters[0].get("tags"))):
        raise LabError("deletion preflight found a foreign or ambiguous ECS cluster")
    for role, service in (("api", state.api_service), ("worker", state.worker_service)):
        services = ecs.describe_services(
            cluster=state.cluster, services=[service], include=["TAGS"]
        ).get("services", [])
        if len(services) > 1 or (services and not _owned(state, services[0].get("tags"))):
            raise LabError("deletion preflight found a foreign or ambiguous ECS service")
        for desired in ("RUNNING", "STOPPED"):
            arns = ecs.list_tasks(
                cluster=state.cluster, serviceName=service, desiredStatus=desired
            ).get("taskArns", [])
            for arn in arns:
                described = ecs.describe_tasks(
                    cluster=state.cluster, tasks=[arn], include=["TAGS"]
                ).get("tasks", [])
                if len(described) != 1:
                    raise LabError("deletion preflight could not describe an exact ECS task")
                task = described[0]
                task_id = str(task.get("taskArn", "")).rsplit("/", 1)[-1]
                if not _TASK_ID.fullmatch(task_id) or (
                    task.get("tags") is not None and not _owned(state, task.get("tags"))
                ):
                    raise LabError("deletion preflight found a foreign ECS task")
                plan["tasks"].append(f"floci-ecs-{task_id}-{role}")
    for arn in (state.api_task_definition_arn, state.worker_task_definition_arn):
        if not arn:
            continue
        response = ecs.describe_task_definition(taskDefinition=arn, include=["TAGS"])
        definition = response.get("taskDefinition")
        expected_family = state.api_family if arn == state.api_task_definition_arn else state.worker_family
        tags = response.get("tags", definition.get("tags") if isinstance(definition, dict) else None)
        if (
            not isinstance(definition, dict)
            or definition.get("taskDefinitionArn") != arn
            or definition.get("family") != expected_family
            or not isinstance(definition.get("revision"), int)
            or not _owned(state, tags)
        ):
            raise LabError("deletion preflight task-definition identity mismatch")
        plan["definitions"].append(arn)
    for name in (state.queue, state.dlq):
        try:
            url = sqs.get_queue_url(QueueName=name)["QueueUrl"]
        except ClientError as exc:
            if _is_missing(exc, {"QueueDoesNotExist"}):
                continue
            raise
        if sqs.list_queue_tags(QueueUrl=url).get("Tags", {}) != _tags_dict(state):
            raise LabError("deletion preflight found a foreign queue")
    try:
        table = ddb.describe_table(TableName=state.table)["Table"]
        if not _owned(state, ddb.list_tags_of_resource(ResourceArn=table["TableArn"]).get("Tags")):
            raise LabError("deletion preflight found a foreign table")
    except ClientError as exc:
        if not _is_missing(exc, {"ResourceNotFoundException"}):
            raise
    try:
        if not _owned(state, s3.get_bucket_tagging(Bucket=state.bucket).get("TagSet", [])):
            raise LabError("deletion preflight found a foreign bucket")
        plan["objects"] = [
            item["Key"]
            for item in s3.list_objects_v2(Bucket=state.bucket, MaxKeys=1000).get("Contents", [])
        ]
    except ClientError as exc:
        if not _is_missing(exc, {"NoSuchBucket"}):
            raise
    for tag, expected_id in zip(
        _owned_image_tags(state), (state.api_image_id, state.worker_image_id), strict=True
    ):
        listed = _run(
            ["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"]
        ).splitlines()
        if tag not in listed:
            continue
        image_id = _run(["docker", "image", "inspect", "--format", "{{.Id}}", tag]).strip()
        labels = _docker_json(
            ["docker", "image", "inspect", "--format", "{{json .Config.Labels}}", tag]
        )
        required = {
            "pk-stack-lab.project": PROJECT,
            "pk-stack-lab.run": state.run_id,
            "pk-stack-lab.claim": state.claim_id,
            "pk-stack-lab.source-digest": state.source_digest,
        }
        if (
            image_id != expected_id
            or not isinstance(labels, dict)
            or {key: labels.get(key) for key in required} != required
        ):
            raise LabError("deletion preflight image provenance mismatch")
        plan["images"].append(tag)
    verifier = f"{state.prefix}-verifier"
    if _exact_docker_object_exists("container", verifier):
        labels = _inspect_labels("container", verifier)
        assert labels is not None
        if (
            labels.get("pk-stack-lab.claim") != state.claim_id
            or labels.get("pk-stack-lab.component") != "verifier"
        ):
            raise LabError("deletion preflight found a foreign verifier")
    plan["verifier"] = verifier
    return plan


def _remove_owned_images(state: RunState) -> None:
    """Remove only exact current-run application tags, never image IDs or globs."""
    tags = _owned_image_tags(state)
    listed = {
        line.strip()
        for line in _run(
            ["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"]
        ).splitlines()
        if line.strip()
    }
    required = {
        "pk-stack-lab.project": PROJECT,
        "pk-stack-lab.run": state.run_id,
        "pk-stack-lab.claim": state.claim_id,
        "pk-stack-lab.source-digest": state.source_digest,
    }
    for tag, expected_id in zip(tags, (state.api_image_id, state.worker_image_id), strict=True):
        if tag not in listed:
            continue
        image_id = _run(["docker", "image", "inspect", "--format", "{{.Id}}", tag]).strip()
        labels = _docker_json(
            ["docker", "image", "inspect", "--format", "{{json .Config.Labels}}", tag]
        )
        if (
            image_id != expected_id
            or not isinstance(labels, dict)
            or {key: labels.get(key) for key in required} != required
        ):
            raise LabError("refusing image cleanup without exact persisted provenance")
    for tag in tags:
        if tag in listed:
            _run(["docker", "image", "rm", tag])
    remaining = {
        line.strip()
        for line in _run(
            ["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"]
        ).splitlines()
        if line.strip()
    }
    leaked = sorted(set(tags) & remaining)
    if leaked:
        raise LabError("cleanup leak detected: owned local application image remains")


def _recover_stale_images(args: argparse.Namespace) -> dict[str, Any]:
    """Inventory or remove a state-less claim's two exact immutable image tags.

    This deliberately does not try to rediscover ownership by a prefix, image
    ID alone, dangling layers, or timestamps.  It is a narrowly scoped recovery
    application path under `labctl down`, usable only after normal `down` has
    removed a manifest but left both application tags behind.
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
        source_digest=digest,
        api_image_id=image_id,
        worker_image_id=image_id,
    )
    tags = _owned_image_tags(state)
    if _exact_docker_object_exists(
        "container", "pk-stack-lab-floci"
    ) or _exact_docker_object_exists("network", NETWORK):
        raise LabError("stale recovery refuses while the outer lab container or network is present")
    task_names = [
        line.strip()
        for line in _run(["docker", "ps", "-a", "--format", "{{.Names}}"]).splitlines()
        if line.strip()
    ]
    if any(name.startswith("floci-ecs-") for name in task_names):
        # Without the canonical state/task ARN capture, a Floci ECS container
        # cannot be attributed safely.  Preserve it for normal recovery.
        raise LabError("stale recovery refuses while any Floci ECS task container is present")
    expected_labels = {
        "pk-stack-lab.project": PROJECT,
        "pk-stack-lab.run": state.run_id,
        "pk-stack-lab.claim": state.claim_id,
        "pk-stack-lab.source-digest": state.source_digest,
    }
    proven: list[dict[str, str]] = []
    for tag in tags:
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
    plan = {"run": state.run_id, "claim": state.claim_id, "images": proven, "state_absent": True}
    if not getattr(args, "apply_stale_recovery", False):
        return {"ok": True, "recovery": {"dry_run": True, "plan": plan}}
    # Every target has been fully proven before the first Docker mutation.
    for tag in tags:
        _run(["docker", "image", "rm", tag])
    remaining = {
        line.strip()
        for line in _run(
            ["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"]
        ).splitlines()
        if line.strip()
    }
    if set(tags) & remaining:
        raise LabError("stale recovery deletion left a claimed immutable image tag")
    return {"ok": True, "recovery": {"dry_run": False, "removed": proven}}


def command_down(_: argparse.Namespace) -> dict[str, Any]:
    if getattr(_, "recover_stale", False):
        return _recover_stale_images(_)
    state = load_state(ROOT)
    socket_endpoint = _bind_daemon(state)
    _assert_outer_ownership()
    # Complete read-only ownership pass: no service update/delete, AWS delete,
    # compose down, image remove, or local-state removal may precede this.
    deletion_plan = _build_deletion_plan(state)
    try:
        task_container_names = _delete_owned_resources(state)
    except BotoCoreError:
        if not getattr(_, "teardown_unreachable_emulator", False):
            raise
        # This is only for the documented Floci/internal-network incompatibility:
        # no real AWS is reachable, and stopping the exact local emulator is the
        # sole way to discard its unreachable in-memory control plane.  It is
        # explicit so a normal teardown never silently abandons an inventory.
        task_container_names = []
    for definition in deletion_plan["definitions"]:
        client("ecs").deregister_task_definition(taskDefinition=definition)
    _compose(socket_endpoint, "down")
    network = _run(
        ["docker", "network", "ls", "--filter", "name=^" + NETWORK + "$", "--format", "{{.Name}}"]
    )
    containers = "\n".join(
        _run(["docker", "ps", "-a", "--filter", "name=^" + name + "$", "--format", "{{.ID}}"])
        for name in task_container_names
    )
    floci = _run(
        ["docker", "ps", "-a", "--filter", "name=^pk-stack-lab-floci$", "--format", "{{.ID}}"]
    )
    remaining = _remaining_owned_task_leaks(task_container_names)
    if network.strip() or containers.strip() or floci.strip() or remaining:
        raise LabError("cleanup leak detected: owned Docker container or network remains")
    # Keep the canonical manifest until every external and local cleanup has
    # succeeded.  That makes a failed data-directory removal recoverable.
    _remove_floci_data_path(root=ROOT)
    _remove_owned_images(state)
    remove_state_manifest(ROOT)
    _remove_empty_state_dir(root=ROOT)
    return {
        "ok": True,
        "run": state.run_id,
        "cleanup": {
            "ecs_tasks": len(task_container_names),
            "floci_container": 0,
            "network": 0,
            "floci_data": 0,
            "images": len(deletion_plan["images"]),
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
