"""Narrow configuration and endpoint/ownership validation for the lab."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
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
_HEX_32 = re.compile(r"^[0-9a-f]{32}$")
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_STATE_TEMP = re.compile(r"^\.run\.[0-9a-f]{32}\.tmp$")
_DOCKER_CONTEXT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DOCKER_DAEMON_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}$")
_TEST_CLAIM_ID = "0" * 32
_TEST_DOCKER_CONTEXT = "pk-stack-test"
_TEST_DOCKER_SOCKET = "unix:///tmp/pk-stack-lab-test.sock"
_TEST_DOCKER_DAEMON_ID = "pk-stack-test-daemon"
_TEST_COMPOSE_SHA256 = "0" * 64
STATE_SCHEMA_VERSION = 2
ARTIFACT_KINDS = frozenset(
    {
        "image_planned",
        "image_observed",
        "task_definition_planned",
        "task_definition_observed",
    }
)
REACHABLE_TEARDOWN_PHASES = (
    "aws_compute_absent",
    "aws_data_absent",
    "aws_definitions_cluster_absent",
    "aws_postconditions_passed",
    "docker_outer_absent",
    "floci_data_absent",
    "docker_images_absent",
    "local_postconditions_passed",
)
DISCARD_TEARDOWN_PHASES = (
    "docker_outer_absent",
    "floci_data_absent",
    "docker_images_absent",
    "local_postconditions_passed",
)


class SafetyError(ValueError):
    """A caller attempted to use an endpoint or resource outside lab policy."""


def _exact_object(raw: object, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != fields:
        raise SafetyError(f"{label} must have exactly the canonical fields")
    return raw


def _string(raw: dict[str, Any], key: str, label: str) -> str:
    value = raw[key]
    if type(value) is not str:
        raise SafetyError(f"{label}.{key} must be a string")
    return value


def _string_tuple(raw: dict[str, Any], key: str, label: str) -> tuple[str, ...]:
    value = raw[key]
    if not isinstance(value, list) or not all(type(item) is str for item in value):
        raise SafetyError(f"{label}.{key} must be a list of strings")
    return tuple(value)


@dataclass(frozen=True)
class ArtifactEvent:
    """One immutable, append-only observation in a claim's artifact history."""

    seq: int
    kind: str
    operation_id: str
    role: str
    source_digest: str
    image_ref: str
    image_id: str = ""
    family: str = ""
    task_definition_arn: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "seq": self.seq,
            "kind": self.kind,
            "operation_id": self.operation_id,
            "role": self.role,
            "source_digest": self.source_digest,
            "image_ref": self.image_ref,
            "image_id": self.image_id,
            "family": self.family,
            "task_definition_arn": self.task_definition_arn,
        }

    @classmethod
    def from_dict(cls, raw: object) -> ArtifactEvent:
        value = _exact_object(raw, set(cls.__dataclass_fields__), "artifact event")
        seq = value["seq"]
        if type(seq) is not int:
            raise SafetyError("artifact event.seq must be an integer")
        return cls(
            seq=seq,
            kind=_string(value, "kind", "artifact event"),
            operation_id=_string(value, "operation_id", "artifact event"),
            role=_string(value, "role", "artifact event"),
            source_digest=_string(value, "source_digest", "artifact event"),
            image_ref=_string(value, "image_ref", "artifact event"),
            image_id=_string(value, "image_id", "artifact event"),
            family=_string(value, "family", "artifact event"),
            task_definition_arn=_string(value, "task_definition_arn", "artifact event"),
        )


@dataclass(frozen=True)
class NamedArnTarget:
    name: str
    arn: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "arn": self.arn}

    @classmethod
    def from_dict(cls, raw: object) -> NamedArnTarget:
        value = _exact_object(raw, {"name", "arn"}, "named ARN target")
        return cls(
            name=_string(value, "name", "named ARN target"),
            arn=_string(value, "arn", "named ARN target"),
        )


@dataclass(frozen=True)
class QueueTarget:
    name: str
    url: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "url": self.url}

    @classmethod
    def from_dict(cls, raw: object) -> QueueTarget:
        value = _exact_object(raw, {"name", "url"}, "queue target")
        return cls(
            name=_string(value, "name", "queue target"),
            url=_string(value, "url", "queue target"),
        )


@dataclass(frozen=True)
class BucketTarget:
    name: str
    present: bool
    object_strategy: str = "drain-all-unversioned"

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "present": self.present,
            "object_strategy": self.object_strategy,
        }

    @classmethod
    def from_dict(cls, raw: object) -> BucketTarget:
        value = _exact_object(raw, {"name", "present", "object_strategy"}, "bucket target")
        present = value["present"]
        if type(present) is not bool:
            raise SafetyError("bucket target.present must be a boolean")
        return cls(
            name=_string(value, "name", "bucket target"),
            present=present,
            object_strategy=_string(value, "object_strategy", "bucket target"),
        )


@dataclass(frozen=True)
class ImageTarget:
    ref: str
    image_id: str
    source_digest: str

    def to_dict(self) -> dict[str, str]:
        return {
            "ref": self.ref,
            "image_id": self.image_id,
            "source_digest": self.source_digest,
        }

    @classmethod
    def from_dict(cls, raw: object) -> ImageTarget:
        value = _exact_object(raw, {"ref", "image_id", "source_digest"}, "image target")
        return cls(
            ref=_string(value, "ref", "image target"),
            image_id=_string(value, "image_id", "image target"),
            source_digest=_string(value, "source_digest", "image target"),
        )


@dataclass(frozen=True)
class AwsTeardownTargets:
    cluster: NamedArnTarget
    services: tuple[NamedArnTarget, ...]
    queues: tuple[QueueTarget, ...]
    table: NamedArnTarget
    bucket: BucketTarget
    task_arns: tuple[str, ...] = ()
    task_definition_families: tuple[str, ...] = ()
    task_definition_arns: tuple[str, ...] = ()
    object_keys: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster": self.cluster.to_dict(),
            "services": [target.to_dict() for target in self.services],
            "queues": [target.to_dict() for target in self.queues],
            "table": self.table.to_dict(),
            "bucket": self.bucket.to_dict(),
            "task_arns": list(self.task_arns),
            "task_definition_families": list(self.task_definition_families),
            "task_definition_arns": list(self.task_definition_arns),
            "object_keys": list(self.object_keys),
        }

    @classmethod
    def from_dict(cls, raw: object) -> AwsTeardownTargets:
        fields = set(cls.__dataclass_fields__)
        value = _exact_object(raw, fields, "AWS teardown targets")
        services = value["services"]
        queues = value["queues"]
        if not isinstance(services, list) or not isinstance(queues, list):
            raise SafetyError("AWS teardown service and queue targets must be lists")
        return cls(
            cluster=NamedArnTarget.from_dict(value["cluster"]),
            services=tuple(NamedArnTarget.from_dict(item) for item in services),
            queues=tuple(QueueTarget.from_dict(item) for item in queues),
            table=NamedArnTarget.from_dict(value["table"]),
            bucket=BucketTarget.from_dict(value["bucket"]),
            task_arns=_string_tuple(value, "task_arns", "AWS teardown targets"),
            task_definition_families=_string_tuple(
                value, "task_definition_families", "AWS teardown targets"
            ),
            task_definition_arns=_string_tuple(
                value, "task_definition_arns", "AWS teardown targets"
            ),
            object_keys=_string_tuple(value, "object_keys", "AWS teardown targets"),
        )


@dataclass(frozen=True)
class DockerTeardownTargets:
    outer_container: str
    network: str
    verifier: str
    task_containers: tuple[str, ...] = ()
    images: tuple[ImageTarget, ...] = ()
    task_strategy: str = "remove-current-claim-ecs-containers"

    def to_dict(self) -> dict[str, object]:
        return {
            "outer_container": self.outer_container,
            "network": self.network,
            "verifier": self.verifier,
            "task_containers": list(self.task_containers),
            "images": [target.to_dict() for target in self.images],
            "task_strategy": self.task_strategy,
        }

    @classmethod
    def from_dict(cls, raw: object) -> DockerTeardownTargets:
        value = _exact_object(raw, set(cls.__dataclass_fields__), "Docker teardown targets")
        images = value["images"]
        if not isinstance(images, list):
            raise SafetyError("Docker teardown targets.images must be a list")
        return cls(
            outer_container=_string(value, "outer_container", "Docker teardown targets"),
            network=_string(value, "network", "Docker teardown targets"),
            verifier=_string(value, "verifier", "Docker teardown targets"),
            task_containers=_string_tuple(value, "task_containers", "Docker teardown targets"),
            images=tuple(ImageTarget.from_dict(item) for item in images),
            task_strategy=_string(value, "task_strategy", "Docker teardown targets"),
        )


@dataclass(frozen=True)
class TeardownPlan:
    version: int
    claim_id: str
    ledger_seq: int
    ledger_sha256: str
    compose_sha256: str
    aws_mode: str
    aws: AwsTeardownTargets
    docker: DockerTeardownTargets
    phases: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "claim_id": self.claim_id,
            "ledger_seq": self.ledger_seq,
            "ledger_sha256": self.ledger_sha256,
            "compose_sha256": self.compose_sha256,
            "aws_mode": self.aws_mode,
            "aws": self.aws.to_dict(),
            "docker": self.docker.to_dict(),
            "phases": list(self.phases),
        }

    @classmethod
    def from_dict(cls, raw: object) -> TeardownPlan:
        value = _exact_object(raw, set(cls.__dataclass_fields__), "teardown plan")
        version, ledger_seq = value["version"], value["ledger_seq"]
        if type(version) is not int or type(ledger_seq) is not int:
            raise SafetyError("teardown plan version and ledger_seq must be integers")
        return cls(
            version=version,
            claim_id=_string(value, "claim_id", "teardown plan"),
            ledger_seq=ledger_seq,
            ledger_sha256=_string(value, "ledger_sha256", "teardown plan"),
            compose_sha256=_string(value, "compose_sha256", "teardown plan"),
            aws_mode=_string(value, "aws_mode", "teardown plan"),
            aws=AwsTeardownTargets.from_dict(value["aws"]),
            docker=DockerTeardownTargets.from_dict(value["docker"]),
            phases=_string_tuple(value, "phases", "teardown plan"),
        )


@dataclass(frozen=True)
class TeardownTransition:
    """Durable audit record for the sole supported teardown mode change."""

    from_aws_mode: str
    from_plan_sha256: str
    from_completed_phases: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "from_aws_mode": self.from_aws_mode,
            "from_plan_sha256": self.from_plan_sha256,
            "from_completed_phases": list(self.from_completed_phases),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, raw: object) -> TeardownTransition:
        value = _exact_object(raw, set(cls.__dataclass_fields__), "teardown transition")
        return cls(
            from_aws_mode=_string(value, "from_aws_mode", "teardown transition"),
            from_plan_sha256=_string(value, "from_plan_sha256", "teardown transition"),
            from_completed_phases=_string_tuple(
                value, "from_completed_phases", "teardown transition"
            ),
            reason=_string(value, "reason", "teardown transition"),
        )


@dataclass(frozen=True)
class TeardownState:
    plan: TeardownPlan
    plan_sha256: str
    completed_phases: tuple[str, ...] = ()
    transition: TeardownTransition | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "plan": self.plan.to_dict(),
            "plan_sha256": self.plan_sha256,
            "completed_phases": list(self.completed_phases),
            "transition": self.transition.to_dict() if self.transition is not None else None,
        }

    @classmethod
    def create(cls, plan: TeardownPlan) -> TeardownState:
        return cls(plan=plan, plan_sha256=teardown_plan_hash(plan))

    @classmethod
    def from_dict(cls, raw: object) -> TeardownState:
        current_fields = set(cls.__dataclass_fields__)
        legacy_fields = current_fields - {"transition"}
        if isinstance(raw, dict) and set(raw) == legacy_fields:
            # Schema v2 teardown manifests written before transition journaling
            # are still valid recovery inputs.  The missing field has the same
            # meaning as the canonical current representation's explicit null.
            value = _exact_object(raw, legacy_fields, "teardown state")
            transition = None
        else:
            value = _exact_object(raw, current_fields, "teardown state")
            transition = value["transition"]
        if transition is not None and not isinstance(transition, dict):
            raise SafetyError("teardown state.transition must be an object or null")
        return cls(
            plan=TeardownPlan.from_dict(value["plan"]),
            plan_sha256=_string(value, "plan_sha256", "teardown state"),
            completed_phases=_string_tuple(value, "completed_phases", "teardown state"),
            transition=(
                TeardownTransition.from_dict(transition) if transition is not None else None
            ),
        )


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


def compose_digest(root: Path) -> str:
    """Hash the direct Compose definition that teardown may execute later."""
    path = root / "compose.yaml"
    if not path.is_file() or path.is_symlink():
        raise SafetyError("Compose definition is missing or unsafe")
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    # `up` replaces these valid deterministic fixture identities with an
    # opaque claim and the exact selected Docker daemon tuple.  Keeping the
    # defaults canonical means tests exercise the same persisted-state
    # invariants instead of relying on an invalid sentinel manifest.
    claim_id: str = _TEST_CLAIM_ID
    docker_context: str = _TEST_DOCKER_CONTEXT
    docker_socket: str = _TEST_DOCKER_SOCKET
    docker_daemon_id: str = _TEST_DOCKER_DAEMON_ID
    compose_sha256: str = _TEST_COMPOSE_SHA256
    source_digest: str = ""
    api_image_id: str = ""
    worker_image_id: str = ""
    api_task_definition_arn: str = ""
    worker_task_definition_arn: str = ""
    # Durable, narrowly scoped authorization for recovering the one exact S3
    # bucket if the process dies after create_bucket and before tagging.
    bucket_create_intent: bool = False
    schema_version: int = STATE_SCHEMA_VERSION
    artifact_ledger: tuple[ArtifactEvent, ...] = ()
    teardown: TeardownState | None = None

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

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "queue": self.queue,
            "dlq": self.dlq,
            "table": self.table,
            "bucket": self.bucket,
            "cluster": self.cluster,
            "api_service": self.api_service,
            "worker_service": self.worker_service,
            "api_family": self.api_family,
            "worker_family": self.worker_family,
            "claim_id": self.claim_id,
            "docker_context": self.docker_context,
            "docker_socket": self.docker_socket,
            "docker_daemon_id": self.docker_daemon_id,
            "compose_sha256": self.compose_sha256,
            "source_digest": self.source_digest,
            "api_image_id": self.api_image_id,
            "worker_image_id": self.worker_image_id,
            "api_task_definition_arn": self.api_task_definition_arn,
            "worker_task_definition_arn": self.worker_task_definition_arn,
            "bucket_create_intent": self.bucket_create_intent,
            "schema_version": self.schema_version,
            "artifact_ledger": [event.to_dict() for event in self.artifact_ledger],
            "teardown": self.teardown.to_dict() if self.teardown is not None else None,
        }

    @classmethod
    def create(
        cls,
        run_id: str | None = None,
        *,
        claim_id: str = _TEST_CLAIM_ID,
        docker_context: str = _TEST_DOCKER_CONTEXT,
        docker_socket: str = _TEST_DOCKER_SOCKET,
        docker_daemon_id: str = _TEST_DOCKER_DAEMON_ID,
        compose_sha256: str = _TEST_COMPOSE_SHA256,
        source_digest: str = "",
        api_image_id: str = "",
        worker_image_id: str = "",
        api_task_definition_arn: str = "",
        worker_task_definition_arn: str = "",
        bucket_create_intent: bool = False,
        artifact_ledger: tuple[ArtifactEvent, ...] = (),
        teardown: TeardownState | None = None,
    ) -> RunState:
        value = safe_name(run_id or f"r{secrets.token_hex(5)}")
        prefix = f"pklab-{value}"
        # S3 disallows upper case and has a 63 character limit.
        state = cls(
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
            compose_sha256=compose_sha256,
            source_digest=source_digest,
            api_image_id=api_image_id,
            worker_image_id=worker_image_id,
            api_task_definition_arn=api_task_definition_arn,
            worker_task_definition_arn=worker_task_definition_arn,
            bucket_create_intent=bucket_create_intent,
            artifact_ledger=tuple(artifact_ledger),
            teardown=teardown,
        )
        _validate_state(state)
        return state


def artifact_ledger_hash(events: tuple[ArtifactEvent, ...]) -> str:
    payload = [event.to_dict() for event in events]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def teardown_plan_hash(plan: TeardownPlan) -> str:
    return hashlib.sha256(
        json.dumps(plan.to_dict(), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def next_artifact_sequence(state: RunState) -> int:
    return len(state.artifact_ledger) + 1


def _task_definition_family(arn: str) -> str:
    match = re.fullmatch(
        rf"arn:aws:ecs:{re.escape(REGION)}:000000000000:task-definition/([^/:]+):([1-9][0-9]*)",
        arn,
    )
    if match is None:
        return ""
    return match.group(1)


def _validate_docker_identity(state: RunState) -> None:
    if not _DOCKER_CONTEXT.fullmatch(state.docker_context):
        raise SafetyError("Docker context identity is empty, unsafe, or too long")
    if not _DOCKER_DAEMON_ID.fullmatch(state.docker_daemon_id):
        raise SafetyError("Docker daemon identity is empty, unsafe, or too long")

    endpoint = state.docker_socket
    if (
        len(endpoint.encode("utf-8")) > 4096
        or not endpoint.startswith("unix:///")
        or any(ord(character) < 32 or ord(character) == 127 for character in endpoint)
    ):
        raise SafetyError("Docker socket identity must be a bounded absolute unix endpoint")
    path = endpoint.removeprefix("unix://")
    if (
        not path.startswith("/")
        or path.startswith("//")
        or path == "/"
        or os.path.normpath(path) != path
        or any(part in {".", ".."} for part in path.split("/"))
    ):
        raise SafetyError("Docker socket identity must be a canonical absolute unix path")


def _validate_active_deployment(state: RunState) -> None:
    pointer = (
        state.source_digest,
        state.api_image_id,
        state.worker_image_id,
        state.api_task_definition_arn,
        state.worker_task_definition_arn,
    )
    if not any(pointer):
        return
    if not all(pointer):
        raise SafetyError("active deployment identity must be entirely empty or complete")
    if (
        not _HEX_64.fullmatch(state.source_digest)
        or not _IMAGE_ID.fullmatch(state.api_image_id)
        or state.worker_image_id != state.api_image_id
        or _task_definition_family(state.api_task_definition_arn) != state.api_family
        or _task_definition_family(state.worker_task_definition_arn) != state.worker_family
    ):
        raise SafetyError("active deployment identity contains invalid immutable values")

    expected_keys = {
        (kind, role)
        for kind in ARTIFACT_KINDS
        for role in ("api", "worker")
    }
    by_operation: dict[str, list[ArtifactEvent]] = {}
    for event in state.artifact_ledger:
        by_operation.setdefault(event.operation_id, []).append(event)

    matching_operations: list[str] = []
    for operation_id, events in by_operation.items():
        keyed = {(event.kind, event.role): event for event in events}
        if len(events) != len(expected_keys) or set(keyed) != expected_keys:
            continue
        if any(event.source_digest != state.source_digest for event in events):
            continue
        if any(
            keyed[(kind, role)].image_ref
            != f"{state.prefix}-{role}:{state.source_digest[:24]}"
            for kind in ARTIFACT_KINDS
            for role in ("api", "worker")
        ):
            continue
        if any(
            keyed[(kind, role)].image_id != state.api_image_id
            for kind in ("image_observed", "task_definition_observed")
            for role in ("api", "worker")
        ):
            continue
        if (
            keyed[("task_definition_observed", "api")].task_definition_arn
            != state.api_task_definition_arn
            or keyed[("task_definition_observed", "worker")].task_definition_arn
            != state.worker_task_definition_arn
        ):
            continue
        matching_operations.append(operation_id)

    if len(matching_operations) != 1:
        raise SafetyError(
            "active deployment identity must match exactly one complete artifact operation"
        )


def _validate_artifact_ledger(state: RunState) -> None:
    if type(state.artifact_ledger) is not tuple:
        raise SafetyError("artifact ledger must be an immutable tuple")
    planned_images: set[tuple[str, str, str, str]] = set()
    observed_images: set[tuple[str, str, str, str, str]] = set()
    planned_definitions: set[tuple[str, str, str, str, str]] = set()
    observed_arns: set[str] = set()
    observed_image_ids: dict[tuple[str, str], str] = {}
    for expected_seq, event in enumerate(state.artifact_ledger, start=1):
        if not isinstance(event, ArtifactEvent):
            raise SafetyError("artifact ledger entries must be ArtifactEvent values")
        if event.seq != expected_seq:
            raise SafetyError("artifact ledger sequence must be contiguous and append-only")
        if event.kind not in ARTIFACT_KINDS:
            raise SafetyError("artifact event has an unknown kind")
        if not _HEX_32.fullmatch(event.operation_id):
            raise SafetyError("artifact operation ID must be 32 lowercase hexadecimal characters")
        if event.role not in {"api", "worker"}:
            raise SafetyError("artifact role must be api or worker")
        if not _HEX_64.fullmatch(event.source_digest):
            raise SafetyError("artifact source digest must be a lowercase SHA-256")
        expected_ref = f"{state.prefix}-{event.role}:{event.source_digest[:24]}"
        if event.image_ref != expected_ref:
            raise SafetyError("artifact image reference is not canonical for this run")
        expected_family = state.api_family if event.role == "api" else state.worker_family
        image_key = (
            event.operation_id,
            event.role,
            event.source_digest,
            event.image_ref,
        )
        definition_key = (*image_key, expected_family)
        if event.kind == "image_planned":
            if event.image_id or event.family or event.task_definition_arn:
                raise SafetyError("planned image event contains observed-only fields")
            planned_images.add(image_key)
        elif event.kind == "image_observed":
            if (
                image_key not in planned_images
                or not _IMAGE_ID.fullmatch(event.image_id)
                or event.family
                or event.task_definition_arn
            ):
                raise SafetyError("observed image event has no valid preceding image plan")
            ref_key = (event.image_ref, event.source_digest)
            prior_id = observed_image_ids.setdefault(ref_key, event.image_id)
            if prior_id != event.image_id:
                raise SafetyError("one planned image reference resolved to conflicting image IDs")
            observed_images.add((*image_key, event.image_id))
        elif event.kind == "task_definition_planned":
            if (
                image_key not in planned_images
                or event.image_id
                or event.family != expected_family
                or event.task_definition_arn
            ):
                raise SafetyError("planned task definition has no valid preceding image plan")
            planned_definitions.add(definition_key)
        else:
            if (
                definition_key not in planned_definitions
                or not _IMAGE_ID.fullmatch(event.image_id)
                or (*image_key, event.image_id) not in observed_images
                or event.family != expected_family
                or _task_definition_family(event.task_definition_arn) != expected_family
                or event.task_definition_arn in observed_arns
            ):
                raise SafetyError(
                    "observed task definition has no valid unique preceding artifact plan"
                )
            observed_arns.add(event.task_definition_arn)


def _validate_named_target(target: NamedArnTarget, expected_name: str, label: str) -> None:
    if target.name != expected_name:
        raise SafetyError(f"{label} name is not canonical for this run")
    if target.arn and (
        not target.arn.startswith("arn:") or not target.arn.endswith(f"/{target.name}")
    ):
        raise SafetyError(f"{label} ARN does not identify its exact name")


def _sorted_unique(values: tuple[str, ...], label: str) -> None:
    if tuple(sorted(set(values))) != values:
        raise SafetyError(f"{label} must be sorted and unique")


def _validate_teardown(state: RunState) -> None:
    teardown = state.teardown
    if teardown is None:
        return
    if not isinstance(teardown, TeardownState) or not isinstance(teardown.plan, TeardownPlan):
        raise SafetyError("teardown state must use the canonical nested types")
    plan = teardown.plan
    if plan.version != 1 or plan.claim_id != state.claim_id:
        raise SafetyError("teardown plan version or claim does not match the run")
    if plan.ledger_seq != len(state.artifact_ledger) or plan.ledger_sha256 != artifact_ledger_hash(
        state.artifact_ledger
    ):
        raise SafetyError("teardown plan is not frozen at the artifact-ledger head")
    if plan.compose_sha256 != state.compose_sha256 or not _HEX_64.fullmatch(
        plan.compose_sha256
    ):
        raise SafetyError("teardown plan does not bind the claimed Compose definition")
    if plan.aws_mode == "reachable":
        expected_phases = REACHABLE_TEARDOWN_PHASES
    elif plan.aws_mode == "discard-unreachable":
        expected_phases = DISCARD_TEARDOWN_PHASES
    else:
        raise SafetyError("teardown plan has an unknown AWS mode")
    if plan.phases != expected_phases:
        raise SafetyError("teardown plan phases are not canonical for its AWS mode")
    if teardown.plan_sha256 != teardown_plan_hash(plan):
        raise SafetyError("teardown plan hash does not match its frozen contents")
    if plan.phases[: len(teardown.completed_phases)] != teardown.completed_phases:
        raise SafetyError("completed teardown phases must be an ordered plan prefix")

    transition = teardown.transition
    if transition is not None:
        if not isinstance(transition, TeardownTransition):
            raise SafetyError("teardown transition must use the canonical nested type")
        if (
            transition.from_aws_mode != "reachable"
            or plan.aws_mode != "discard-unreachable"
            or transition.reason != "floci-unreachable-control-plane-discard"
        ):
            raise SafetyError("teardown transition is not the canonical reachable-to-discard move")
        if not _HEX_64.fullmatch(transition.from_plan_sha256):
            raise SafetyError("teardown transition prior-plan hash is invalid")
        prior_plan = replace(
            plan,
            aws_mode="reachable",
            phases=REACHABLE_TEARDOWN_PHASES,
        )
        if teardown_plan_hash(prior_plan) != transition.from_plan_sha256:
            raise SafetyError("teardown transition does not bind the prior reachable plan")
        if (
            REACHABLE_TEARDOWN_PHASES[: len(transition.from_completed_phases)]
            != transition.from_completed_phases
        ):
            raise SafetyError("teardown transition prior phases are not an ordered prefix")
        carried_prefix = tuple(
            phase
            for phase in transition.from_completed_phases
            if phase in DISCARD_TEARDOWN_PHASES
        )
        if teardown.completed_phases[: len(carried_prefix)] != carried_prefix:
            raise SafetyError("teardown transition did not preserve its completed local prefix")

    aws, docker = plan.aws, plan.docker
    _validate_named_target(aws.cluster, state.cluster, "cluster target")
    if tuple(target.name for target in aws.services) != (
        state.api_service,
        state.worker_service,
    ):
        raise SafetyError("service targets are not the canonical ordered pair")
    for target in aws.services:
        _validate_named_target(target, target.name, "service target")
    if tuple(target.name for target in aws.queues) != (state.queue, state.dlq):
        raise SafetyError("queue targets are not the canonical ordered pair")
    for target in aws.queues:
        if target.url:
            parsed = urlparse(target.url)
            if parsed.scheme not in {"http", "https"} or not parsed.path.rstrip("/").endswith(
                f"/{target.name}"
            ):
                raise SafetyError("queue target URL does not identify its exact name")
    _validate_named_target(aws.table, state.table, "table target")
    expected_strategy = "drain-all-unversioned" if aws.bucket.present else "none"
    if (
        aws.bucket.name != state.bucket
        or type(aws.bucket.present) is not bool
        or aws.bucket.object_strategy != expected_strategy
    ):
        raise SafetyError("bucket target is not canonical for this run")
    if aws.task_definition_families != (state.api_family, state.worker_family):
        raise SafetyError("task-definition families are not the canonical ordered pair")
    _sorted_unique(aws.task_arns, "task ARNs")
    _sorted_unique(aws.task_definition_arns, "task-definition ARNs")
    _sorted_unique(aws.object_keys, "S3 object keys")
    if any(not arn.startswith("arn:") for arn in aws.task_arns):
        raise SafetyError("task target must be an ARN")
    if any(not key or len(key.encode("utf-8")) > 1024 for key in aws.object_keys):
        raise SafetyError("S3 object key target is invalid")

    observed_definition_arns = {
        event.task_definition_arn
        for event in state.artifact_ledger
        if event.kind == "task_definition_observed"
    }
    if aws.task_definition_arns != tuple(sorted(observed_definition_arns)):
        raise SafetyError("teardown plan does not exactly cover every observed task definition")

    if docker.outer_container != "pk-stack-lab-floci" or docker.network != NETWORK:
        raise SafetyError("Docker outer targets are not canonical")
    if docker.verifier != f"{state.prefix}-verifier":
        raise SafetyError("Docker verifier target is not canonical")
    if docker.task_strategy != "remove-current-claim-ecs-containers":
        raise SafetyError("Docker task cleanup strategy is not canonical")
    _sorted_unique(docker.task_containers, "task containers")
    if any(not value.startswith("floci-ecs-") for value in docker.task_containers):
        raise SafetyError("Docker task-container target is not canonical")

    planned_images: dict[tuple[str, str], str] = {}
    for event in state.artifact_ledger:
        key = (event.image_ref, event.source_digest)
        if event.kind == "image_planned":
            planned_images.setdefault(key, "")
        elif event.kind == "image_observed":
            planned_images[key] = event.image_id
    expected_images = tuple(
        ImageTarget(ref=ref, source_digest=digest, image_id=image_id)
        for (ref, digest), image_id in sorted(planned_images.items())
    )
    if docker.images != expected_images:
        raise SafetyError("Docker image targets do not exactly cover the artifact ledger")


def _validate_state(state: RunState) -> None:
    if not isinstance(state, RunState) or type(state.schema_version) is not int:
        raise SafetyError("state manifest does not use the canonical schema")
    if state.schema_version != STATE_SCHEMA_VERSION:
        raise SafetyError("unsupported state manifest schema version")
    string_fields = (
        "run_id",
        "queue",
        "dlq",
        "table",
        "bucket",
        "cluster",
        "api_service",
        "worker_service",
        "api_family",
        "worker_family",
        "claim_id",
        "docker_context",
        "docker_socket",
        "docker_daemon_id",
        "compose_sha256",
        "source_digest",
        "api_image_id",
        "worker_image_id",
        "api_task_definition_arn",
        "worker_task_definition_arn",
    )
    if any(type(getattr(state, field)) is not str for field in string_fields):
        raise SafetyError("state manifest scalar fields must all be strings")
    if type(state.bucket_create_intent) is not bool:
        raise SafetyError("bucket create intent must be a boolean")
    value = safe_name(state.run_id)
    prefix = f"pklab-{value}"
    expected_names = (
        f"{prefix}-exports",
        f"{prefix}-exports-dlq",
        f"{prefix}-exports",
        f"{prefix}-results",
        f"{prefix}-cluster",
        f"{prefix}-api",
        f"{prefix}-worker",
        f"{prefix}-api",
        f"{prefix}-worker",
    )
    if tuple(state.names()) != expected_names:
        raise SafetyError("state manifest does not equal canonical run ownership")
    if not _HEX_32.fullmatch(state.claim_id):
        raise SafetyError("run claim ID must be 32 lowercase hexadecimal characters")
    _validate_docker_identity(state)
    if not _HEX_64.fullmatch(state.compose_sha256):
        raise SafetyError("run state does not bind a Compose definition SHA-256")
    _validate_artifact_ledger(state)
    _validate_active_deployment(state)
    _validate_teardown(state)


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
    info = os.fstat(descriptor)
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        os.close(descriptor)
        raise SafetyError(".lab-state must be an owner-only direct directory")
    return descriptor


def state_directory_absent(root: Path) -> bool:
    """Return true for absent state or a safe empty post-unlink directory."""
    directory = state_dir(root)
    if directory.is_symlink():
        raise SafetyError(".lab-state must not be a symlink")
    if directory.exists() and not directory.is_dir():
        raise SafetyError(".lab-state must be a directory")
    if not directory.exists():
        return True
    info = directory.stat()
    return (
        info.st_uid == os.geteuid()
        and stat.S_IMODE(info.st_mode) == 0o700
        and not any(directory.iterdir())
    )


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
    value = _exact_object(raw, set(RunState.__dataclass_fields__), "state manifest")
    ledger = value["artifact_ledger"]
    if not isinstance(ledger, list):
        raise SafetyError("state manifest artifact_ledger must be a list")
    teardown_raw = value["teardown"]
    if teardown_raw is not None and not isinstance(teardown_raw, dict):
        raise SafetyError("state manifest teardown must be an object or null")
    try:
        scalar_fields = {
            field: _string(value, field, "state manifest")
            for field in RunState.__dataclass_fields__
            if field
            not in {
                "schema_version",
                "artifact_ledger",
                "teardown",
                "bucket_create_intent",
            }
        }
        bucket_create_intent = value["bucket_create_intent"]
        if type(bucket_create_intent) is not bool:
            raise SafetyError("state manifest bucket_create_intent must be a boolean")
        schema_version = value["schema_version"]
        if type(schema_version) is not int:
            raise SafetyError("state manifest schema_version must be an integer")
        state = RunState(
            **scalar_fields,
            bucket_create_intent=bucket_create_intent,
            schema_version=schema_version,
            artifact_ledger=tuple(ArtifactEvent.from_dict(item) for item in ledger),
            teardown=TeardownState.from_dict(teardown_raw) if teardown_raw is not None else None,
        )
        _validate_state(state)
    except (KeyError, TypeError, SafetyError) as exc:
        raise SafetyError("state manifest has an invalid run identifier") from exc
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


def _remove_orphaned_state_temporaries(
    directory: int, *, allowed_entries: frozenset[str]
) -> None:
    """Remove only proven remnants of this module's atomic state writer.

    A SIGKILL can occur after the temporary file is durable but before
    ``os.replace``.  The prior canonical manifest remains valid in that case,
    so replaying the transition is safe.  Unknown or structurally unsafe
    entries are preserved and rejected instead of broadening cleanup scope.
    """
    stale: list[str] = []
    for name in os.listdir(directory):
        if name in allowed_entries:
            continue
        if not _STATE_TEMP.fullmatch(name):
            raise SafetyError(".lab-state contains an unexpected runtime artifact")
        info = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise SafetyError("atomic state temporary is not an owner-only direct regular file")
        stale.append(name)
    for name in stale:
        os.unlink(name, dir_fd=directory)
    if stale:
        os.fsync(directory)


def save_state(root: Path, state: RunState) -> None:
    try:
        _validate_state(state)
    except SafetyError as exc:
        raise SafetyError("refusing noncanonical state write") from exc
    directory = _open_state_directory(root, create=True)
    descriptor = -1
    temporary = ""
    try:
        path = state_path(root)
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise SafetyError(".lab-state/run.json must be a direct regular file")
        _remove_orphaned_state_temporaries(
            directory, allowed_entries=frozenset({"run.json", "floci-data"})
        )
        # Never truncate an established claim in place.  A same-directory
        # exclusive temporary plus fsync/replace makes a crash either retain
        # the old complete manifest or expose the new complete manifest.
        temporary = f".run.{secrets.token_hex(16)}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if not hasattr(os, "O_NOFOLLOW"):
            raise SafetyError("platform does not support no-follow state writes")
        descriptor = os.open(temporary, flags | os.O_NOFOLLOW, 0o600, dir_fd=directory)
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
            if temporary:
                try:
                    os.unlink(temporary, dir_fd=directory)
                except FileNotFoundError:
                    pass
        finally:
            os.close(directory)


def claim_state(root: Path, state: RunState) -> None:
    """Atomically create the first canonical manifest; exactly one caller can win."""
    try:
        _validate_state(state)
    except SafetyError as exc:
        raise SafetyError("refusing noncanonical state claim") from exc
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
        _remove_orphaned_state_temporaries(
            directory, allowed_entries=frozenset({"run.json"})
        )
        info = os.stat("run.json", dir_fd=directory, follow_symlinks=False)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise SafetyError(".lab-state/run.json must be a direct regular file")
        os.unlink("run.json", dir_fd=directory)
        os.fsync(directory)
    except OSError as exc:
        raise SafetyError("unable to remove direct state manifest") from exc
    finally:
        os.close(directory)


def _save_transition(root: Path, prior: RunState, updated: RunState) -> RunState:
    """Persist one atomic state transition, refusing an already-stale caller snapshot."""
    if load_state(root) != prior:
        raise SafetyError("run state changed before lifecycle transition")
    save_state(root, updated)
    return updated


def append_artifact_events(root: Path, state: RunState, *events: ArtifactEvent) -> RunState:
    """Atomically append already-sequenced artifact facts to an active claim."""
    if state.teardown is not None:
        raise SafetyError("artifact history is frozen after teardown planning")
    if not events:
        return state
    updated = replace(state, artifact_ledger=state.artifact_ledger + tuple(events))
    _validate_state(updated)
    return _save_transition(root, state, updated)


def set_bucket_create_intent(root: Path, state: RunState, *, active: bool) -> RunState:
    """Durably bracket the S3 create/tag gap for the exact claimed bucket."""
    if type(active) is not bool:
        raise SafetyError("bucket create intent transition requires a boolean")
    if state.teardown is not None:
        raise SafetyError("bucket create intent is frozen after teardown planning")
    if state.bucket_create_intent is active:
        return state
    updated = replace(state, bucket_create_intent=active)
    _validate_state(updated)
    return _save_transition(root, state, updated)


def install_teardown_plan(root: Path, state: RunState, plan: TeardownPlan) -> RunState:
    """Atomically freeze the first teardown plan at the current ledger head."""
    if state.teardown is not None:
        if state.teardown.plan == plan:
            return state
        raise SafetyError("a different teardown plan is already frozen")
    updated = replace(state, teardown=TeardownState.create(plan))
    _validate_state(updated)
    return _save_transition(root, state, updated)


def transition_teardown_to_discard(root: Path, state: RunState) -> RunState:
    """Atomically project one frozen reachable plan into its local-only sequence.

    The prior plan hash and completed prefix remain in the transition record. The
    Docker, image, AWS-inventory, claim, ledger, and Compose targets are not rebuilt or
    rediscovered; only the mode, canonical phase list, and mapped local prefix change.
    """
    teardown = state.teardown
    if teardown is None or teardown.plan.aws_mode != "reachable":
        raise SafetyError("only a frozen reachable teardown can transition to discard")
    if teardown.transition is not None:
        raise SafetyError("teardown mode has already transitioned")
    prior_plan = teardown.plan
    discard_plan = replace(
        prior_plan,
        aws_mode="discard-unreachable",
        phases=DISCARD_TEARDOWN_PHASES,
    )
    carried_prefix = tuple(
        phase for phase in teardown.completed_phases if phase in DISCARD_TEARDOWN_PHASES
    )
    transition = TeardownTransition(
        from_aws_mode="reachable",
        from_plan_sha256=teardown.plan_sha256,
        from_completed_phases=teardown.completed_phases,
        reason="floci-unreachable-control-plane-discard",
    )
    updated = replace(
        state,
        teardown=TeardownState(
            plan=discard_plan,
            plan_sha256=teardown_plan_hash(discard_plan),
            completed_phases=carried_prefix,
            transition=transition,
        ),
    )
    _validate_state(updated)
    return _save_transition(root, state, updated)


def complete_teardown_phase(root: Path, state: RunState, phase: str) -> RunState:
    """Durably append one successfully verified teardown phase in plan order."""
    teardown = state.teardown
    if teardown is None:
        raise SafetyError("no teardown plan is installed")
    if phase in teardown.completed_phases:
        return state
    index = len(teardown.completed_phases)
    if index >= len(teardown.plan.phases) or teardown.plan.phases[index] != phase:
        raise SafetyError("teardown phase completion is out of order")
    updated_teardown = replace(teardown, completed_phases=teardown.completed_phases + (phase,))
    updated = replace(state, teardown=updated_teardown)
    _validate_state(updated)
    return _save_transition(root, state, updated)


def activate_deployment(
    root: Path,
    state: RunState,
    *,
    source_digest: str,
    image_id: str,
    api_task_definition_arn: str,
    worker_task_definition_arn: str,
) -> RunState:
    """Atomically publish one fully stabilized deployment identity."""
    if state.teardown is not None:
        raise SafetyError("deployment activation is frozen after teardown planning")
    if not _HEX_64.fullmatch(source_digest) or not _IMAGE_ID.fullmatch(image_id):
        raise SafetyError("deployment activation has invalid immutable identities")
    if (
        _task_definition_family(api_task_definition_arn) != state.api_family
        or _task_definition_family(worker_task_definition_arn) != state.worker_family
    ):
        raise SafetyError("deployment activation task definitions are not canonical")
    observed = {
        event.task_definition_arn
        for event in state.artifact_ledger
        if event.kind == "task_definition_observed"
    }
    if {api_task_definition_arn, worker_task_definition_arn} - observed:
        raise SafetyError("deployment activation is not covered by the artifact ledger")
    updated = replace(
        state,
        source_digest=source_digest,
        api_image_id=image_id,
        worker_image_id=image_id,
        api_task_definition_arn=api_task_definition_arn,
        worker_task_definition_arn=worker_task_definition_arn,
    )
    _validate_state(updated)
    return _save_transition(root, state, updated)


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
