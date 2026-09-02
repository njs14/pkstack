"""The intentionally small, deterministic `labctl` control surface."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
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
    state_dir,
    state_directory_absent,
    validate_host_endpoint,
)

ROOT = Path(__file__).resolve().parents[2]
MAX_READ = 8192
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


class LabError(RuntimeError):
    """A controlled lifecycle failure suitable for machine-readable output."""


def _run(args: list[str], *, env: dict[str, str] | None = None, timeout: int = 90) -> str:
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            env=env,
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


def _safe_text(value: str) -> str:
    return " ".join(value.replace("\x00", "").split())[:1000]


def _is_missing(exc: ClientError, codes: set[str]) -> bool:
    return exc.response.get("Error", {}).get("Code") in codes


def _docker_socket() -> str:
    context = _run(["docker", "context", "show"]).strip()
    raw = _run(["docker", "context", "inspect", context, "--format", "{{json .Endpoints.docker.Host}}"]).strip()
    try:
        endpoint = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LabError("Docker context did not return a JSON socket endpoint") from exc
    if not isinstance(endpoint, str) or not endpoint.startswith("unix://"):
        raise LabError("active Docker context must use a unix socket")
    path = endpoint.removeprefix("unix://")
    if not path.startswith("/") or not Path(path).exists():
        raise LabError("active Docker socket is missing")
    return endpoint


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
    return {str(key): str(item) for key, item in value.items() if isinstance(key, str) and isinstance(item, str)}


def _assert_outer_ownership() -> None:
    container = _inspect_labels("container", "pk-stack-lab-floci", missing_ok=True)
    if container is not None and any(container.get(key) != value for key, value in _OUTER_LABELS.items()):
        raise LabError("refusing a pre-existing foreign container named pk-stack-lab-floci")
    network = _inspect_labels("network", NETWORK, missing_ok=True)
    if network is not None and any(network.get(key) != value for key, value in _NETWORK_LABELS.items()):
        raise LabError("refusing a pre-existing foreign network named pk-stack-lab-net")


def _compose_image(socket_endpoint: str) -> str:
    values = [line.strip() for line in _compose(socket_endpoint, "config", "--images").splitlines() if line.strip()]
    if values != [FLOCI_IMAGE]:
        raise LabError("Compose does not resolve to the required immutable Floci image")
    return values[0]


def _compose_env(socket_endpoint: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PK_STACK_LAB_DOCKER_SOCKET"] = socket_endpoint.removeprefix("unix://")
    environment["PK_STACK_LAB_FLOCI_DATA"] = str(_floci_data_path(create=False))
    return environment


def _compose(socket_endpoint: str, *args: str, timeout: int = 120) -> str:
    return _run(["docker", "compose", "-f", "compose.yaml", *args], env=_compose_env(socket_endpoint), timeout=timeout)


def _http_json(url: str, *, method: str = "GET", body: dict[str, object] | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body, separators=(",", ":")).encode() if body is not None else None
    request = Request(url, method=method, data=data, headers={"Content-Type": "application/json", **(headers or {})})
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
    dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
    queue_url = sqs.create_queue(
        QueueName=state.queue,
        Attributes={"VisibilityTimeout": "8", "RedrivePolicy": json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "2"})},
        tags=_tags_dict(state),
    )["QueueUrl"]
    ddb.create_table(
        TableName=state.table,
        AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}, {"AttributeName": "sk", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
        BillingMode="PAY_PER_REQUEST",
        Tags=ownership_tags(state),
    )
    ddb.get_waiter("table_exists").wait(TableName=state.table, WaiterConfig={"Delay": 1, "MaxAttempts": 30})
    s3.create_bucket(Bucket=state.bucket)
    s3.put_bucket_tagging(Bucket=state.bucket, Tagging={"TagSet": ownership_tags(state)})
    ecs.create_cluster(clusterName=state.cluster, tags=_ecs_tags(state))
    return {"queue_url": queue_url, "dlq_url": dlq_url}


def command_doctor(_: argparse.Namespace) -> dict[str, Any]:
    endpoint = validate_host_endpoint(HOST_ENDPOINT)
    required = {name: bool(shutil.which(name)) for name in ("docker", "uv")}
    if not all(required.values()):
        raise LabError("required tools are missing")
    socket_endpoint = _docker_socket()
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
        "docker_ready": bool(json.loads(version)),
        "required_tools": required,
    }


def command_up(args: argparse.Namespace) -> dict[str, Any]:
    try:
        existing = load_state(ROOT)
    except SafetyError:
        if not state_directory_absent(ROOT):
            raise LabError("existing .lab-state is invalid; preserve it and resolve before starting")
        existing = None
    if existing:
        raise LabError("existing lab state found; run labctl down before a new run")
    socket_endpoint = _docker_socket()
    _assert_outer_ownership()
    _compose_image(socket_endpoint)
    state = RunState.create(args.run_id)
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
        "containerDefinitions": [{
            "name": role,
            "image": image,
            "essential": True,
            "environment": environment,
            "dockerLabels": {"pk-stack-lab.managed": "true", "pk-stack-lab.run": state.run_id, "pk-stack-lab.role": role},
        }],
        "tags": _ecs_tags(state),
    }
    if role == "api":
        definition["containerDefinitions"][0]["portMappings"] = [{"containerPort": 8080, "hostPort": 0, "protocol": "tcp"}]
    return definition


def _wait_services(state: RunState) -> list[dict[str, Any]]:
    ecs = client("ecs")
    for _ in range(45):
        response = ecs.describe_services(cluster=state.cluster, services=[state.api_service, state.worker_service], include=["TAGS"])
        services = response.get("services", [])
        if len(services) == 2 and all(service.get("runningCount") == 1 and service.get("pendingCount") == 0 for service in services):
            return services
        time.sleep(2)
    raise LabError("ECS services did not stabilize within 90 seconds")


def command_deploy(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    _docker_socket()  # Fail before building if Docker is not usable.
    api_image, worker_image = f"{state.prefix}-api:0.1", f"{state.prefix}-worker:0.1"
    _run(["docker", "build", "--platform", "linux/arm64", "-t", api_image, "."], timeout=300)
    _run(["docker", "tag", api_image, worker_image])
    sqs, ecs = client("sqs"), client("ecs")
    queue_url = sqs.get_queue_url(QueueName=state.queue)["QueueUrl"]
    # Floci returns the task-reachable hostname because FLOCI_HOSTNAME is set.
    parsed = urlparse(queue_url)
    if parsed.hostname != "floci" or parsed.username or parsed.password:
        raise LabError("Floci did not return a task-network SQS URL")
    api_td = ecs.register_task_definition(**_task_definition(state, role="api", image=api_image, queue_url=queue_url))["taskDefinition"]
    worker_td = ecs.register_task_definition(**_task_definition(state, role="worker", image=worker_image, queue_url=queue_url))["taskDefinition"]
    for name, task_definition in ((state.api_service, api_td["taskDefinitionArn"]), (state.worker_service, worker_td["taskDefinitionArn"])):
        try:
            ecs.create_service(
                cluster=state.cluster,
                serviceName=name,
                taskDefinition=task_definition,
                desiredCount=1,
                launchType="EC2",
                tags=_ecs_tags(state),
                propagateTags="SERVICE",
            )
        except ClientError as exc:
            if not any(marker in str(exc).lower() for marker in ("already exists", "not idempotent")):
                raise
            ecs.update_service(
                cluster=state.cluster,
                service=name,
                taskDefinition=task_definition,
                desiredCount=1,
                forceNewDeployment=True,
                propagateTags="SERVICE",
            )
    services = _wait_services(state)
    return {"ok": True, "run": state.run_id, "task_definitions": {"api": api_td["taskDefinitionArn"], "worker": worker_td["taskDefinitionArn"]}, "services": [{"name": s["serviceName"], "running": s["runningCount"]} for s in services]}


def _service_tasks(state: RunState) -> tuple[dict[str, Any], dict[str, Any]]:
    ecs = client("ecs")
    result: dict[str, dict[str, Any]] = {}
    for role, service in (("api", state.api_service), ("worker", state.worker_service)):
        services = ecs.describe_services(cluster=state.cluster, services=[service], include=["TAGS"]).get("services", [])
        if len(services) != 1 or not _owned(state, services[0].get("tags")):
            raise LabError(f"{role} ECS service lacks exact current-run ownership tags")
        arns = ecs.list_tasks(cluster=state.cluster, serviceName=service, desiredStatus="RUNNING").get("taskArns", [])
        if not arns:
            raise LabError(f"no running {role} ECS task")
        tasks = ecs.describe_tasks(cluster=state.cluster, tasks=arns, include=["TAGS"]).get("tasks", [])
        if not tasks:
            raise LabError(f"unable to describe {role} ECS task")
        task = tasks[0]
        expected_family = state.api_family if role == "api" else state.worker_family
        if (
            (task.get("tags") is not None and not _owned(state, task.get("tags")))
            or f":task/{state.cluster}/" not in str(task.get("taskArn"))
            or f"task-definition/{expected_family}:" not in str(task.get("taskDefinitionArn"))
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


def _api_http(task: dict[str, Any], container: dict[str, Any], *, method: str, path: str, body: dict[str, object] | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    """Reach HTTP only through the real API task when Floci publishes no host port."""
    if not path.startswith("/") or len(path) > 256:
        raise LabError("invalid fixed API request path")
    name = container.get("name")
    if name != _task_container_name(task, "api") or container.get("role") != "api":
        raise LabError("bounded API HTTP requires prior exact API container proof")
    request = {"method": method, "path": path, "body": body, "headers": headers or {}}
    script = (
        "import json,os; from urllib.error import HTTPError; from urllib.request import Request,urlopen; "
        "r=json.loads(os.environ['PK_STACK_LAB_VERIFY_REQUEST']); d=json.dumps(r['body']).encode() if r['body'] is not None else None; "
        "q=Request('http://127.0.0.1:8080'+r['path'],method=r['method'],data=d,headers={'Content-Type':'application/json',**r['headers']}); "
        "\ntry:\n f=urlopen(q,timeout=5); print(json.dumps({'status':f.status,'body':json.loads(f.read(8192))}))\n"
        "except HTTPError as e: print(json.dumps({'status':e.code,'body':json.loads(e.read(8192))}))"
    )
    raw = _run(
        [
            "docker", "exec", "-e", f"PK_STACK_LAB_VERIFY_REQUEST={json.dumps(request, separators=(',', ':'))}",
            name, "python", "-c", script,
        ],
        timeout=15,
    )
    try:
        response = json.loads(raw)
        status, response_body = response["status"], response["body"]
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise LabError("API task returned malformed bounded HTTP evidence") from exc
    if not isinstance(status, int) or not isinstance(response_body, dict):
        raise LabError("API task returned malformed HTTP response")
    return status, response_body


def _task_container_evidence(task: dict[str, Any], role: str) -> dict[str, Any]:
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
    mounts = _docker_json(["docker", "container", "inspect", "--format", "{{json .Mounts}}", name])
    if mounts != []:
        raise LabError("API and worker task containers must have no mounts")
    return {
        "name": name,
        "role": role,
        "image": image,
        "network": NETWORK,
        "labels": _label_subset(labels, set(required)),
    }


def _owned_container_proof(state: RunState, api: dict[str, Any], worker: dict[str, Any]) -> list[dict[str, Any]]:
    containers: list[dict[str, str]] = []
    for task, role in ((api, "api"), (worker, "worker")):
        containers.append(_task_container_evidence(task, role))
    return containers


def command_status(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    api, worker = _service_tasks(state)
    return {"ok": True, "run": state.run_id, "resources": state.to_dict(), "services": {"api": {"task": api["taskArn"], "status": api["lastStatus"]}, "worker": {"task": worker["taskArn"], "status": worker["lastStatus"]}}}


def command_verify(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    api_task, worker_task = _service_tasks(state)
    # Prove both concrete task containers before any API request, Docker exec,
    # or AWS emulator mutation.  The API transport receives that proof rather
    # than deriving an unvalidated container name itself.
    containers = _owned_container_proof(state, api_task, worker_task)
    api_container = containers[0]
    tenant, other = "tenant-a", "tenant-b"
    idem = f"verify-{secrets.token_hex(8)}"
    status, created = _api_http(api_task, api_container, method="POST", path="/exports", body={"tenant": tenant}, headers={"Idempotency-Key": idem})
    if status != 202 or created.get("status") not in {"QUEUED", "COMPLETE"}:
        raise LabError("deployed API did not accept the export")
    export_id = created.get("id")
    if not isinstance(export_id, str):
        raise LabError("deployed API returned no export id")
    if not _EXPORT_ID.fullmatch(export_id):
        raise LabError("deployed API returned an invalid export id")
    duplicate_status, duplicate = _api_http(api_task, api_container, method="POST", path="/exports", body={"tenant": tenant}, headers={"Idempotency-Key": idem})
    if duplicate_status != 202 or duplicate.get("id") != export_id:
        raise LabError("API idempotency did not preserve the original export")
    final: dict[str, Any] | None = None
    for _ in range(30):
        response_status, response = _api_http(api_task, api_container, method="GET", path=f"/exports?tenant={tenant}&id={export_id}")
        if response_status == 200 and response.get("status") == "COMPLETE":
            final = response
            break
        time.sleep(1)
    if not final or not isinstance(final.get("object_key"), str):
        raise LabError("worker did not produce a terminal export in time")
    isolated_status, _ = _api_http(api_task, api_container, method="GET", path=f"/exports?tenant={other}&id={export_id}")
    if isolated_status != 404:
        raise LabError("tenant isolation check failed")
    s3 = client("s3")
    object_result = s3.head_object(Bucket=state.bucket, Key=final["object_key"])
    if not object_result.get("ContentLength"):
        raise LabError("terminal DynamoDB state was not backed by an S3 result")
    original_etag = object_result.get("ETag")
    ddb = client("dynamodb")
    key = {"pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}}
    before = ddb.get_item(TableName=state.table, Key=key).get("Item", {})
    if before.get("attempts", {}).get("N") != "1":
        raise LabError("happy-path worker attempts were not exactly one")
    sqs = client("sqs")
    queue_url = sqs.get_queue_url(QueueName=state.queue)["QueueUrl"]
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps({"tenant": tenant, "id": export_id}))
    duplicate_noop = False
    for _ in range(16):
        current = ddb.get_item(TableName=state.table, Key=key).get("Item", {})
        current_object = s3.head_object(Bucket=state.bucket, Key=final["object_key"])
        if (
            current.get("attempts", {}).get("N") == "1"
            and current.get("duplicate_deliveries", {}).get("N") == "1"
            and current_object.get("ETag") == original_etag
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
        messages = sqs.receive_message(QueueUrl=dlq_url, MaxNumberOfMessages=10, WaitTimeSeconds=1).get("Messages", [])
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
    return {"ok": True, "run": state.run_id, "api_transport": "bounded HTTP inside exact real ECS API task (Floci did not publish host port)", "business": {"export_id": export_id, "terminal_status": final["status"], "s3_object": final["object_key"], "tenant_isolation": True, "api_idempotency": True, "worker_duplicate_delivery": {"attempts": 1, "s3_identity_unchanged": True, "consumed_noop": True}, "dlq": {"current_invocation": True, "message_id": dlq_message_id}}, "task_proof": {"api": api_task["taskArn"], "worker": worker_task["taskArn"], "containers": containers}}


def command_evidence(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    api, worker = _service_tasks(state)
    socket_endpoint = _docker_socket()
    floci_labels = _inspect_labels("container", "pk-stack-lab-floci")
    assert floci_labels is not None
    if any(floci_labels.get(key) != value for key, value in _OUTER_LABELS.items()):
        raise LabError("Floci container ownership labels are invalid")
    services = client("ecs").describe_services(
        cluster=state.cluster, services=[state.api_service, state.worker_service]
    ).get("services", [])
    by_name = {service.get("serviceName"): service for service in services}
    return {"ok": True, "lab_version": __version__, "floci_image": FLOCI_IMAGE, "endpoint": HOST_ENDPOINT, "task_endpoint": TASK_ENDPOINT, "region": REGION, "docker_socket": socket_endpoint, "docker": {"server_version": _run(["docker", "version", "--format", "{{.Server.Version}}"]).strip(), "compose_version": _run(["docker", "compose", "version", "--short"]).strip()}, "floci": {"container": "pk-stack-lab-floci", "labels": _label_subset(floci_labels, set(_OUTER_LABELS)), "image": _run(["docker", "container", "inspect", "--format", "{{.Config.Image}}", "pk-stack-lab-floci"]).strip()}, "network": NETWORK, "resources": state.to_dict(), "ownership": {"run": state.run_id, "labels": {"pk-stack-lab.managed": "true", "pk-stack-lab.run": state.run_id}, "manifest_sha256": ownership_hash(state)}, "services": {role: {"name": name, "status": by_name.get(name, {}).get("status"), "running": by_name.get(name, {}).get("runningCount"), "task_definition": by_name.get(name, {}).get("taskDefinition")} for role, name in (("api", state.api_service), ("worker", state.worker_service))}, "tasks": {"api": {"arn": api["taskArn"], "definition": api["taskDefinitionArn"], "status": api["lastStatus"], "container": _task_container_evidence(api, "api")}, "worker": {"arn": worker["taskArn"], "definition": worker["taskDefinitionArn"], "status": worker["lastStatus"], "container": _task_container_evidence(worker, "worker")}}}


def _delete_owned_resources(state: RunState) -> list[str]:
    ecs, sqs, ddb, s3 = (client(name) for name in ("ecs", "sqs", "dynamodb", "s3"))
    leaked_container_names: list[str] = []
    try:
        cluster = ecs.describe_clusters(clusters=[state.cluster], include=["TAGS"]).get("clusters", [])
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
            s3.delete_objects(Bucket=state.bucket, Delete={"Objects": [{"Key": entry["Key"]} for entry in objects], "Quiet": True})
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
    task_ids = {match.group(1) for name in task_container_names if (match := _TASK_CONTAINER.fullmatch(name))}
    if not task_ids:
        return []
    names = [line.strip() for line in _run(["docker", "ps", "-a", "--filter", "label=floci=true", "--format", "{{.Names}}"]).splitlines() if line.strip()]
    leaks: list[str] = []
    for name in names:
        if not _TASK_CONTAINER.fullmatch(name):
            continue
        labels = _inspect_labels("container", name)
        assert labels is not None
        if labels.get("io.floci.service") == "ecs" and labels.get("io.floci.resource-id") in task_ids:
            leaks.append(name)
    return leaks


def _owned_image_tags(state: RunState) -> list[str]:
    """The only two mutable image tags constructed by deploy for this run."""
    tags = [f"{state.prefix}-api:0.1", f"{state.prefix}-worker:0.1"]
    if any(not re.fullmatch(r"pklab-[a-z0-9-]{1,32}-(?:api|worker):0\.1", tag) for tag in tags):
        raise LabError("refusing unsafe local image cleanup name")
    return tags


def _remove_owned_images(state: RunState) -> None:
    """Remove only exact current-run application tags, never image IDs or globs."""
    tags = _owned_image_tags(state)
    listed = {line.strip() for line in _run(["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"]).splitlines() if line.strip()}
    for tag in tags:
        if tag in listed:
            _run(["docker", "image", "rm", tag])
    remaining = {line.strip() for line in _run(["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"]).splitlines() if line.strip()}
    leaked = sorted(set(tags) & remaining)
    if leaked:
        raise LabError("cleanup leak detected: owned local application image remains")


def command_down(_: argparse.Namespace) -> dict[str, Any]:
    state = load_state(ROOT)
    socket_endpoint = _docker_socket()
    _assert_outer_ownership()
    task_container_names = _delete_owned_resources(state)
    _compose(socket_endpoint, "down", "--remove-orphans")
    network = _run(["docker", "network", "ls", "--filter", "name=^" + NETWORK + "$", "--format", "{{.Name}}"])
    containers = "\n".join(
        _run(["docker", "ps", "-a", "--filter", "name=^" + name + "$", "--format", "{{.ID}}"])
        for name in task_container_names
    )
    floci = _run(["docker", "ps", "-a", "--filter", "name=^pk-stack-lab-floci$", "--format", "{{.ID}}"])
    remaining = _remaining_owned_task_leaks(task_container_names)
    if network.strip() or containers.strip() or floci.strip() or remaining:
        raise LabError("cleanup leak detected: owned Docker container or network remains")
    # Keep the canonical manifest until every external and local cleanup has
    # succeeded.  That makes a failed data-directory removal recoverable.
    _remove_floci_data_path(root=ROOT)
    _remove_owned_images(state)
    remove_state_manifest(ROOT)
    _remove_empty_state_dir(root=ROOT)
    return {"ok": True, "run": state.run_id, "cleanup": {"ecs_tasks": 0, "floci_container": 0, "network": 0, "floci_data": 0, "images": 0}}


COMMANDS = {"doctor": command_doctor, "up": command_up, "deploy": command_deploy, "status": command_status, "verify": command_verify, "evidence": command_evidence, "down": command_down}


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
    try:
        args = parser.parse_args(raw_argv)
    except _ArgumentFailure as exc:
        if _json_requested(raw_argv):
            print(json.dumps({"ok": False, "error": _safe_text(str(exc)), "command": None}, sort_keys=True))
            raise SystemExit(2)
        argparse.ArgumentParser.error(parser, str(exc))
    try:
        result = COMMANDS[args.command](args)
    except (LabError, SafetyError, ClientError, BotoCoreError, OSError) as exc:
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
