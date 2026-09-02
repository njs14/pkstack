import copy
import json
import subprocess
import sys
import threading
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError

from pk_stack_lab import cli
from pk_stack_lab.config import (
    DISCARD_TEARDOWN_PHASES,
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
    artifact_ledger_hash,
    claim_state,
    load_state,
    save_state,
    state_directory_absent,
)


def _complete_deployment_state(
    run_id: str = "ci-001",
    *,
    digest: str = "a" * 64,
    image_id: str = "sha256:" + "b" * 64,
    revision: int = 1,
) -> RunState:
    """Build one valid active state with its complete eight-event provenance."""
    base = RunState.create(run_id)
    operation_id = "d" * 32
    refs = {
        "api": f"{base.prefix}-api:{digest[:24]}",
        "worker": f"{base.prefix}-worker:{digest[:24]}",
    }
    api_arn = (
        "arn:aws:ecs:us-east-1:000000000000:task-definition/"
        f"{base.api_family}:{revision}"
    )
    worker_arn = (
        "arn:aws:ecs:us-east-1:000000000000:task-definition/"
        f"{base.worker_family}:{revision}"
    )
    ledger = (
        ArtifactEvent(1, "image_planned", operation_id, "api", digest, refs["api"]),
        ArtifactEvent(2, "image_planned", operation_id, "worker", digest, refs["worker"]),
        ArtifactEvent(
            3,
            "image_observed",
            operation_id,
            "api",
            digest,
            refs["api"],
            image_id=image_id,
        ),
        ArtifactEvent(
            4,
            "image_observed",
            operation_id,
            "worker",
            digest,
            refs["worker"],
            image_id=image_id,
        ),
        ArtifactEvent(
            5,
            "task_definition_planned",
            operation_id,
            "api",
            digest,
            refs["api"],
            family=base.api_family,
        ),
        ArtifactEvent(
            6,
            "task_definition_planned",
            operation_id,
            "worker",
            digest,
            refs["worker"],
            family=base.worker_family,
        ),
        ArtifactEvent(
            7,
            "task_definition_observed",
            operation_id,
            "api",
            digest,
            refs["api"],
            image_id=image_id,
            family=base.api_family,
            task_definition_arn=api_arn,
        ),
        ArtifactEvent(
            8,
            "task_definition_observed",
            operation_id,
            "worker",
            digest,
            refs["worker"],
            image_id=image_id,
            family=base.worker_family,
            task_definition_arn=worker_arn,
        ),
    )
    return RunState.create(
        run_id,
        source_digest=digest,
        api_image_id=image_id,
        worker_image_id=image_id,
        api_task_definition_arn=api_arn,
        worker_task_definition_arn=worker_arn,
        artifact_ledger=ledger,
    )


def test_run_state_has_single_safe_prefix() -> None:
    state = RunState.create("ci-001")
    assert all(name.startswith("pklab-ci-001") for name in state.names())


def test_tampered_state_cannot_authorize_cleanup(tmp_path: Path) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    path = tmp_path / ".lab-state" / "run.json"
    path.write_text(
        path.read_text().replace("pklab-ci-001-results", "foreign-bucket"), encoding="utf-8"
    )
    with pytest.raises(SafetyError):
        load_state(tmp_path)


def test_state_manifest_requires_exact_canonical_schema(tmp_path: Path) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    path = tmp_path / ".lab-state" / "run.json"
    path.write_text(
        path.read_text(encoding="utf-8").replace("}", ',"extra":"x"}'), encoding="utf-8"
    )
    with pytest.raises(SafetyError, match="no valid lab state"):
        load_state(tmp_path)


def test_bucket_create_intent_manifest_field_requires_a_boolean(tmp_path: Path) -> None:
    save_state(tmp_path, RunState.create("ci-intent-type"))
    path = tmp_path / ".lab-state" / "run.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["bucket_create_intent"] = "true"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SafetyError, match="no valid lab state"):
        load_state(tmp_path)


def test_safe_empty_state_directory_is_reusable_after_manifest_unlink(tmp_path: Path) -> None:
    directory = tmp_path / ".lab-state"
    directory.mkdir(mode=0o700)
    assert state_directory_absent(tmp_path) is True
    (directory / "evidence").write_text("retain", encoding="utf-8")
    assert state_directory_absent(tmp_path) is False


def test_atomic_state_claim_has_one_winner(tmp_path: Path) -> None:
    claim_state(tmp_path, RunState.create("ci-001"))
    with pytest.raises(SafetyError, match="artifacts|manifest"):
        claim_state(tmp_path, RunState.create("ci-002"))


def test_concurrent_atomic_state_claim_has_exactly_one_winner(tmp_path: Path) -> None:
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def claim(run_id: str) -> None:
        barrier.wait()
        try:
            claim_state(tmp_path, RunState.create(run_id))
        except SafetyError:
            outcomes.append("rejected")
        else:
            outcomes.append("claimed")

    threads = [threading.Thread(target=claim, args=(f"ci-00{i}",)) for i in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(outcomes) == ["claimed", "rejected"]
    assert load_state(tmp_path).run_id in {"ci-001", "ci-002"}


def test_symlinked_state_directory_never_reads_or_writes_external_target(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    external_state = outside / "run.json"
    external_state.write_text('{"external":true}', encoding="utf-8")
    (tmp_path / ".lab-state").symlink_to(outside, target_is_directory=True)
    with pytest.raises(SafetyError, match="must not be a symlink"):
        load_state(tmp_path)
    with pytest.raises(SafetyError, match="must not be a symlink"):
        save_state(tmp_path, RunState.create("ci-001"))
    assert external_state.read_text(encoding="utf-8") == '{"external":true}'


def test_symlinked_run_manifest_never_reads_or_writes_external_target(tmp_path: Path) -> None:
    outside = tmp_path / "outside.json"
    outside.write_text('{"external":true}', encoding="utf-8")
    state = tmp_path / ".lab-state"
    state.mkdir(mode=0o700)
    (state / "run.json").symlink_to(outside)
    with pytest.raises(SafetyError, match="must not be a symlink"):
        load_state(tmp_path)
    with pytest.raises(SafetyError, match="direct regular file"):
        save_state(tmp_path, RunState.create("ci-001"))
    assert outside.read_text(encoding="utf-8") == '{"external":true}'


@pytest.mark.parametrize(
    "contents",
    [
        "not-json",
        '{"run_id":"ci-001","queue":"foreign","dlq":"pklab-ci-001-exports-dlq"}',
    ],
)
def test_up_preserves_invalid_direct_manifest_without_reaching_docker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contents: str
) -> None:
    state = tmp_path / ".lab-state"
    state.mkdir(mode=0o700)
    manifest = state / "run.json"
    manifest.write_text(contents, encoding="utf-8")
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(
        cli,
        "_docker_socket",
        lambda: (_ for _ in ()).throw(AssertionError("Docker must not be reached")),
    )
    with pytest.raises(cli.LabError, match="existing .lab-state is invalid"):
        cli.command_up(SimpleNamespace(run_id="ci-002"))
    assert manifest.read_text(encoding="utf-8") == contents


def test_task_definition_has_no_socket_or_host_mounts() -> None:
    state = RunState.create("ci-001")
    definition = cli._task_definition(
        state, role="api", image="pklab-ci-001-api:0.1", queue_url="http://floci:4566/q"
    )
    container = definition["containerDefinitions"][0]
    assert "mountPoints" not in container
    assert "volumesFrom" not in container
    assert "volumes" not in definition
    assert all("SOCKET" not in item["name"] for item in container["environment"])


def test_task_definition_requests_all_mandatory_security_fields() -> None:
    state = RunState.create("ci-001")
    definition = cli._task_definition(
        state, role="worker", image="pklab-ci-001-worker:hash", queue_url="http://floci:4566/q"
    )
    container = definition["containerDefinitions"][0]
    assert container["user"] == "65532:65532"
    assert container["readonlyRootFilesystem"] is True
    assert container["linuxParameters"]["capabilities"]["drop"] == ["ALL"]
    assert container["dockerSecurityOptions"] == ["no-new-privileges"]


def test_deploy_create_service_requests_service_tag_propagation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    calls: list[dict[str, object]] = []

    class Sqs:
        def get_queue_url(self, **kwargs):
            return {"QueueUrl": "http://floci:4566/queue"}

    class Ecs:
        def list_task_definitions(self, **kwargs):
            return {"taskDefinitionArns": []}

        def register_task_definition(self, **kwargs):
            return {
                "taskDefinition": {
                    "taskDefinitionArn": (
                        "arn:aws:ecs:us-east-1:000000000000:task-definition/"
                        f"{kwargs['family']}:1"
                    )
                }
            }

        def create_service(self, **kwargs):
            calls.append(kwargs)

        def describe_services(self, **kwargs):
            return {"services": []}

    services = [
        {"serviceName": state.api_service, "runningCount": 1},
        {"serviceName": state.worker_service, "runningCount": 1},
    ]
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_claimed_outer", lambda _: "unix:///tmp/docker.sock")
    monkeypatch.setattr(
        cli, "_docker_identity", lambda: ("test", "unix:///tmp/docker.sock", "daemon")
    )
    monkeypatch.setattr(cli, "source_digest", lambda root: "a" * 64)
    monkeypatch.setattr(
        cli,
        "_ensure_operation_image_pair",
        lambda *args, **kwargs: "sha256:" + "b" * 64,
    )
    monkeypatch.setattr(
        cli,
        "_run",
        lambda args, **kwargs: (
            "sha256:" + "b" * 64 + "\n" if args[:3] == ["docker", "image", "inspect"] else ""
        ),
    )
    monkeypatch.setattr(cli, "_wait_services", lambda value: services)
    monkeypatch.setattr(
        cli,
        "_validate_registered_task_definition",
        lambda ecs, state, **kwargs: kwargs["registered"]["taskDefinitionArn"],
    )
    monkeypatch.setattr(cli, "client", lambda name: Sqs() if name == "sqs" else Ecs())
    cli.command_deploy(SimpleNamespace())
    assert len(calls) == 2
    assert all(call["propagateTags"] == "SERVICE" for call in calls)


def test_deploy_repeat_update_requests_service_tag_propagation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    calls: list[dict[str, object]] = []

    class Sqs:
        def get_queue_url(self, **kwargs):
            return {"QueueUrl": "http://floci:4566/queue"}

    class Ecs:
        def list_task_definitions(self, **kwargs):
            return {"taskDefinitionArns": []}

        def register_task_definition(self, **kwargs):
            return {
                "taskDefinition": {
                    "taskDefinitionArn": (
                        "arn:aws:ecs:us-east-1:000000000000:task-definition/"
                        f"{kwargs['family']}:1"
                    )
                }
            }

        def create_service(self, **kwargs):
            raise AssertionError("existing service must be discovered before mutation")

        def describe_services(self, **kwargs):
            return {"services": [{"tags": cli._ecs_tags(state)}]}

        def update_service(self, **kwargs):
            calls.append(kwargs)

    services = [
        {"serviceName": state.api_service, "runningCount": 1},
        {"serviceName": state.worker_service, "runningCount": 1},
    ]
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_claimed_outer", lambda _: "unix:///tmp/docker.sock")
    monkeypatch.setattr(
        cli, "_docker_identity", lambda: ("test", "unix:///tmp/docker.sock", "daemon")
    )
    monkeypatch.setattr(cli, "source_digest", lambda root: "a" * 64)
    monkeypatch.setattr(
        cli,
        "_ensure_operation_image_pair",
        lambda *args, **kwargs: "sha256:" + "b" * 64,
    )
    monkeypatch.setattr(
        cli,
        "_run",
        lambda args, **kwargs: (
            "sha256:" + "b" * 64 + "\n" if args[:3] == ["docker", "image", "inspect"] else ""
        ),
    )
    monkeypatch.setattr(cli, "_wait_services", lambda value: services)
    monkeypatch.setattr(
        cli,
        "_validate_registered_task_definition",
        lambda ecs, state, **kwargs: kwargs["registered"]["taskDefinitionArn"],
    )
    monkeypatch.setattr(cli, "client", lambda name: Sqs() if name == "sqs" else Ecs())
    cli.command_deploy(SimpleNamespace())
    assert len(calls) == 2
    assert all(call["propagateTags"] == "SERVICE" for call in calls)


def test_deploy_refuses_foreign_deterministic_image_refs_before_state_or_docker_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-image-collision")
    save_state(tmp_path, state)
    before = (tmp_path / ".lab-state/run.json").read_bytes()
    reached: list[str] = []

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_claimed_outer", lambda _: "unix:///tmp/docker.sock")
    monkeypatch.setattr(cli, "_reconcile_pending_task_definitions", lambda value, _ecs: value)
    monkeypatch.setattr(cli, "source_digest", lambda _root: "a" * 64)
    monkeypatch.setattr(cli, "_image_ref_exists", lambda _ref: True)
    monkeypatch.setattr(cli, "client", lambda _name: object())
    monkeypatch.setattr(cli, "_run", lambda *_args, **_kwargs: reached.append("docker"))

    with pytest.raises(cli.LabError, match="outside the artifact ledger"):
        cli.command_deploy(SimpleNamespace())

    assert reached == []
    assert (tmp_path / ".lab-state/run.json").read_bytes() == before
    assert load_state(tmp_path) == state


def test_current_operation_partial_image_pair_resumes_without_overwrite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-image-resume", claim_id="c" * 32)
    digest = "a" * 64
    operation_id = "b" * 32
    refs = {
        "api": f"{state.prefix}-api:{digest[:24]}",
        "worker": f"{state.prefix}-worker:{digest[:24]}",
    }
    state = replace(
        state,
        artifact_ledger=cli._deployment_events(
            state,
            operation_id=operation_id,
            kind="image_planned",
            digest=digest,
            image_refs=refs,
        ),
    )
    image_id = "sha256:" + "d" * 64
    present = {refs["api"]}
    mutations: list[list[str]] = []
    labels = {
        "pk-stack-lab.project": cli.PROJECT,
        "pk-stack-lab.run": state.run_id,
        "pk-stack-lab.claim": state.claim_id,
        "pk-stack-lab.source-digest": digest,
        "pk-stack-lab.operation": operation_id,
    }

    def run(args: list[str], **_: object) -> str:
        if args[:3] == ["docker", "image", "inspect"]:
            return json.dumps(labels) if "{{json .Config.Labels}}" in args else image_id + "\n"
        if args[:3] == ["docker", "tag", refs["api"]]:
            mutations.append(args)
            present.add(refs["worker"])
            return ""
        raise AssertionError(f"unexpected Docker command: {args}")

    monkeypatch.setattr(cli, "_image_ref_exists", lambda ref: ref in present)
    monkeypatch.setattr(cli, "_run", run)

    result = cli._ensure_operation_image_pair(
        state,
        digest=digest,
        image_refs=refs,
        operation_id=operation_id,
    )

    assert result == image_id
    assert mutations == [["docker", "tag", refs["api"], refs["worker"]]]
    assert present == set(refs.values())


def test_ledgered_image_ref_with_wrong_id_fails_before_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-image-drift", claim_id="c" * 32)
    digest = "a" * 64
    operation_id = "b" * 32
    refs = {
        "api": f"{state.prefix}-api:{digest[:24]}",
        "worker": f"{state.prefix}-worker:{digest[:24]}",
    }
    plans = cli._deployment_events(
        state,
        operation_id=operation_id,
        kind="image_planned",
        digest=digest,
        image_refs=refs,
    )
    state = replace(state, artifact_ledger=plans)
    expected = "sha256:" + "d" * 64
    observed = cli._deployment_events(
        state,
        operation_id=operation_id,
        kind="image_observed",
        digest=digest,
        image_refs=refs,
        image_id=expected,
    )
    state = replace(state, artifact_ledger=state.artifact_ledger + observed)
    actual = "sha256:" + "e" * 64
    labels = {
        "pk-stack-lab.project": cli.PROJECT,
        "pk-stack-lab.run": state.run_id,
        "pk-stack-lab.claim": state.claim_id,
        "pk-stack-lab.source-digest": digest,
        "pk-stack-lab.operation": operation_id,
    }
    mutations: list[list[str]] = []

    def run(args: list[str], **_: object) -> str:
        if args[:3] == ["docker", "image", "inspect"]:
            return json.dumps(labels) if "{{json .Config.Labels}}" in args else actual + "\n"
        mutations.append(args)
        return ""

    monkeypatch.setattr(cli, "_image_ref_exists", lambda _ref: True)
    monkeypatch.setattr(cli, "_run", run)

    with pytest.raises(cli.LabError, match="persisted provenance"):
        cli._ensure_operation_image_pair(
            state,
            digest=digest,
            image_refs=refs,
            operation_id=operation_id,
            expected_image_id=expected,
        )

    assert mutations == []


@pytest.mark.parametrize("command", ["deploy", "status", "verify", "evidence"])
def test_post_up_commands_reject_outer_claim_drift_before_aws_or_source_access(
    monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    state = RunState.create("ci-claim-drift")
    reached: list[str] = []
    monkeypatch.setattr(cli, "load_state", lambda _root: state)
    monkeypatch.setattr(
        cli,
        "_bind_claimed_outer",
        lambda _state: (_ for _ in ()).throw(cli.LabError("outer claim drifted")),
    )
    monkeypatch.setattr(cli, "_assert_deployed_source", lambda _state: reached.append("source"))
    monkeypatch.setattr(cli, "client", lambda _name: reached.append("aws"))

    with pytest.raises(cli.LabError, match="outer claim drifted"):
        cli.COMMANDS[command](SimpleNamespace())
    assert reached == []


@pytest.mark.parametrize(
    "mutation", ["missing-tags", "wrong-image", "mount", "wrong-role", "wrong-family"]
)
def test_registered_task_definition_must_match_requested_owned_contract(
    mutation: str,
) -> None:
    # command_deploy constructs this unpublished candidate before activating
    # all five immutable deployment pointers atomically.
    state = replace(RunState.create("ci-001"), source_digest="a" * 64)
    request = cli._task_definition(
        state,
        role="api",
        image=f"{state.prefix}-api:{state.source_digest[:24]}",
        queue_url="http://floci:4566/queue",
    )
    arn = f"arn:aws:ecs:us-east-1:000000000000:task-definition/{state.api_family}:1"
    registered = {"taskDefinitionArn": arn}
    definition = copy.deepcopy(request)
    definition.pop("tags")
    definition.update(taskDefinitionArn=arn, revision=1)
    response: dict[str, object] = {
        "taskDefinition": definition,
        "tags": cli._ecs_tags(state),
    }
    if mutation == "missing-tags":
        response["tags"] = []
    elif mutation == "wrong-image":
        definition["containerDefinitions"][0]["image"] = "foreign:latest"
    elif mutation == "mount":
        definition["containerDefinitions"][0]["mountPoints"] = [{"sourceVolume": "socket"}]
    elif mutation == "wrong-role":
        definition["containerDefinitions"][0]["name"] = "worker"
    elif mutation == "wrong-family":
        registered["taskDefinitionArn"] = arn.replace(state.api_family, "foreign")

    class Ecs:
        def describe_task_definition(self, **kwargs):
            return response

    with pytest.raises(cli.LabError, match="task-definition|task definition"):
        cli._validate_registered_task_definition(
            Ecs(), state, role="api", requested=request, registered=registered
        )


def test_registered_task_definition_accepts_exact_owned_contract() -> None:
    state = replace(RunState.create("ci-001"), source_digest="a" * 64)
    request = cli._task_definition(
        state,
        role="worker",
        image=f"{state.prefix}-worker:{state.source_digest[:24]}",
        queue_url="http://floci:4566/queue",
    )
    arn = f"arn:aws:ecs:us-east-1:000000000000:task-definition/{state.worker_family}:2"
    definition = copy.deepcopy(request)
    definition.pop("tags")
    definition.update(taskDefinitionArn=arn, revision=2)

    class Ecs:
        def describe_task_definition(self, **kwargs):
            return {"taskDefinition": definition, "tags": cli._ecs_tags(state)}

    assert (
        cli._validate_registered_task_definition(
            Ecs(),
            state,
            role="worker",
            requested=request,
            registered={"taskDefinitionArn": arn},
        )
        == arn
    )


def test_foreign_outer_resources_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli,
        "_inspect_labels",
        lambda kind, name, missing_ok=False: (
            {"pk-stack-lab.managed": "false"} if kind == "container" else None
        ),
    )
    monkeypatch.setattr(cli, "_run", lambda *args, **kwargs: "")
    with pytest.raises(cli.LabError, match="outside the current run claim"):
        cli._assert_outer_ownership(RunState.create("ci-001"))


def test_outer_inspection_does_not_turn_generic_docker_failure_into_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "_run",
        lambda *args, **kwargs: (_ for _ in ()).throw(cli.LabError("daemon unavailable")),
    )
    with pytest.raises(cli.LabError, match="daemon unavailable"):
        cli._inspect_labels("container", "pk-stack-lab-floci", missing_ok=True)


def test_outer_inspection_accepts_only_positive_exact_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_run", lambda *args, **kwargs: "")
    assert cli._inspect_labels("network", cli.NETWORK, missing_ok=True) is None


def test_startup_refuses_any_existing_floci_outer_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "_inspect_labels",
        lambda kind, name, missing_ok=False: ({"pk-stack-lab.managed": "true"}),
    )
    monkeypatch.setattr(cli, "_run", lambda *args, **kwargs: "")
    with pytest.raises(cli.LabError, match="refusing startup"):
        cli._assert_outer_ownership(require_absent=True)


def test_compose_environment_binds_the_opaque_run_claim() -> None:
    env = cli._compose_env("unix:///tmp/docker.sock", "a" * 32)
    assert env["PK_STACK_LAB_CLAIM"] == "a" * 32
    assert env["DOCKER_HOST"] == "unix:///tmp/docker.sock"


@pytest.mark.parametrize("collision", ["bucket", "cluster", "service"])
def test_aws_startup_collision_inventory_precedes_mutation(
    monkeypatch: pytest.MonkeyPatch, collision: str
) -> None:
    state = RunState.create("ci-001")
    missing_queue = ClientError({"Error": {"Code": "QueueDoesNotExist"}}, "GetQueueUrl")
    missing_table = ClientError({"Error": {"Code": "ResourceNotFoundException"}}, "DescribeTable")
    missing_bucket = ClientError({"Error": {"Code": "NoSuchBucket"}}, "HeadBucket")

    class Sqs:
        def get_queue_url(self, **kwargs):
            raise missing_queue

    class Ddb:
        def describe_table(self, **kwargs):
            raise missing_table

    class S3:
        def head_bucket(self, **kwargs):
            if collision == "bucket":
                return {}
            raise missing_bucket

    class Ecs:
        def describe_clusters(self, **kwargs):
            if collision == "cluster":
                return {"clusters": [{"clusterName": state.cluster}], "failures": []}
            return {"clusters": [], "failures": [{"reason": "MISSING"}]}

        def list_task_definitions(self, **kwargs):
            return {"taskDefinitionArns": []}

        def describe_services(self, **kwargs):
            if collision == "service":
                return {"services": [{"serviceName": state.api_service}], "failures": []}
            return {"services": [], "failures": [{"reason": "MISSING"}]}

    clients = {"sqs": Sqs(), "dynamodb": Ddb(), "s3": S3(), "ecs": Ecs()}
    monkeypatch.setattr(cli, "client", lambda name: clients[name])
    with pytest.raises(cli.LabError, match=f"startup collision: .*{collision}"):
        cli._assert_aws_targets_absent(state)


@pytest.mark.parametrize("collision", ["bucket", "cluster"])
def test_command_up_never_provisions_after_collision_inventory_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, collision: str
) -> None:
    reached: list[str] = []
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "compose_digest", lambda _root: "a" * 64)
    monkeypatch.setattr(
        cli, "_docker_identity", lambda: ("test", "unix:///tmp/docker.sock", "daemon")
    )
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_compose_image", lambda _socket: cli.FLOCI_IMAGE)
    monkeypatch.setattr(cli, "_compose", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(cli, "_wait_health", lambda: None)
    monkeypatch.setattr(
        cli,
        "_assert_aws_targets_absent",
        lambda _state: (_ for _ in ()).throw(cli.LabError(f"startup collision: {collision}")),
    )
    monkeypatch.setattr(cli, "_provision", lambda _state: reached.append("provision"))

    with pytest.raises(cli.LabError, match=f"startup collision: {collision}"):
        cli.command_up(
            SimpleNamespace(run_id=f"ci-{collision}", acknowledge_docker_socket=True)
        )
    assert reached == []


@pytest.mark.parametrize("tag_mode", ["absent", "foreign"])
def test_untagged_or_foreign_bucket_without_exact_intent_fails_closed(
    tag_mode: str,
) -> None:
    state = RunState.create("ci-bucket-intent")

    class S3:
        def head_bucket(self, **request: object) -> dict[str, object]:
            assert request == {"Bucket": state.bucket}
            return {}

        def get_bucket_tagging(self, **request: object) -> dict[str, object]:
            assert request == {"Bucket": state.bucket}
            if tag_mode == "absent":
                raise ClientError(
                    {"Error": {"Code": "NoSuchTagSet"}}, "GetBucketTagging"
                )
            return {
                "TagSet": [
                    {"Key": "pk-stack-lab:managed", "Value": "false"},
                    {"Key": "pk-stack-lab:run", "Value": state.run_id},
                ]
            }

    with pytest.raises(cli.LabError, match="untagged bucket|foreign S3 bucket"):
        cli._bucket_ownership_mode(S3(), state)


def test_task_container_evidence_requires_exact_resource_id_and_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "a" * 32
    task = {
        "taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/cluster/{task_id}",
        "containers": [{"image": "example:1"}],
    }
    labels = {
        "floci": "true",
        "floci_emulator": "floci-aws",
        "io.floci": "aws",
        "io.floci.service": "ecs",
        "io.floci.resource-id": task_id,
    }
    monkeypatch.setattr(cli, "_inspect_labels", lambda *args, **kwargs: labels)
    monkeypatch.setattr(
        cli,
        "_docker_json",
        lambda args, **kwargs: [] if ".Mounts" in args[4] else {cli.NETWORK: {}},
    )
    monkeypatch.setattr(
        cli,
        "_run",
        lambda args, **kwargs: (
            '65532:65532|true|["ALL"]|["no-new-privileges"]\n'
            if ".HostConfig.ReadonlyRootfs" in args[4]
            else "example:1\n"
        ),
    )
    evidence = cli._task_container_evidence(task, "api")
    assert evidence["network"] == cli.NETWORK
    labels["io.floci.resource-id"] = "b" * 32
    with pytest.raises(cli.LabError, match="exact Floci ECS task"):
        cli._task_container_evidence(task, "api")


def test_task_container_evidence_rejects_socket_mount(monkeypatch: pytest.MonkeyPatch) -> None:
    task_id = "c" * 32
    task = {
        "taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/cluster/{task_id}",
        "containers": [{"image": "example:1"}],
    }
    labels = {
        "floci": "true",
        "floci_emulator": "floci-aws",
        "io.floci": "aws",
        "io.floci.service": "ecs",
        "io.floci.resource-id": task_id,
    }
    monkeypatch.setattr(cli, "_inspect_labels", lambda *args, **kwargs: labels)
    monkeypatch.setattr(cli, "_run", lambda *args, **kwargs: "example:1\n")
    monkeypatch.setattr(
        cli,
        "_docker_json",
        lambda args, **kwargs: (
            [{"Destination": "/var/run/docker.sock"}] if ".Mounts" in args[4] else {cli.NETWORK: {}}
        ),
    )
    with pytest.raises(cli.LabError, match="no mounts"):
        cli._task_container_evidence(task, "api")


def test_task_container_evidence_records_floci_unenforced_security(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "b" * 32
    task = {
        "taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/cluster/{task_id}",
        "containers": [{"image": "example:1"}],
    }
    labels = {
        "floci": "true",
        "floci_emulator": "floci-aws",
        "io.floci": "aws",
        "io.floci.service": "ecs",
        "io.floci.resource-id": task_id,
    }
    monkeypatch.setattr(cli, "_inspect_labels", lambda *args, **kwargs: labels)
    monkeypatch.setattr(
        cli,
        "_docker_json",
        lambda args, **kwargs: [] if ".Mounts" in args[4] else {cli.NETWORK: {}},
    )
    monkeypatch.setattr(
        cli,
        "_run",
        lambda args, **kwargs: (
            "65532:65532|false|null|null\n"
            if ".HostConfig.ReadonlyRootfs" in args[4]
            else "example:1\n"
        ),
    )
    evidence = cli._task_container_evidence(task, "api")
    assert evidence["security"] == {
        "user": "65532:65532",
        "non_root": True,
        "mounts": [],
        "requested": {
            "readonly_root_filesystem": True,
            "cap_drop_all": True,
            "no_new_privileges": True,
        },
        "effective": {
            "readonly_root_filesystem": False,
            "cap_drop_all": False,
            "no_new_privileges": False,
        },
        "emulator_limitations": [
            "readonly_root_filesystem",
            "cap_drop_all",
            "no_new_privileges",
        ],
    }


def test_task_container_evidence_still_rejects_root_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "b" * 32
    task = {
        "taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/cluster/{task_id}",
        "containers": [{"image": "example:1"}],
    }
    labels = {
        "floci": "true",
        "floci_emulator": "floci-aws",
        "io.floci": "aws",
        "io.floci.service": "ecs",
        "io.floci.resource-id": task_id,
    }
    monkeypatch.setattr(cli, "_inspect_labels", lambda *args, **kwargs: labels)
    monkeypatch.setattr(
        cli,
        "_docker_json",
        lambda args, **kwargs: [] if ".Mounts" in args[4] else {cli.NETWORK: {}},
    )
    monkeypatch.setattr(
        cli,
        "_run",
        lambda args, **kwargs: (
            "|false|null|null\n" if ".HostConfig.ReadonlyRootfs" in args[4] else "example:1\n"
        ),
    )
    with pytest.raises(cli.LabError, match="required non-root user"):
        cli._task_container_evidence(task, "api")


def test_verify_proves_both_containers_before_docker_exec_or_aws_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-001")
    task_id = "e" * 32
    api = {"taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/{state.cluster}/{task_id}"}
    worker = {"taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/{state.cluster}/" + "f" * 32}
    calls: list[str] = []
    monkeypatch.setattr(cli, "load_state", lambda root: state)
    monkeypatch.setattr(cli, "_bind_claimed_outer", lambda _: "unix:///tmp/docker.sock")
    monkeypatch.setattr(cli, "_service_tasks", lambda value: (api, worker))
    monkeypatch.setattr(
        cli,
        "_task_container_evidence",
        lambda *args: (_ for _ in ()).throw(
            cli.LabError("API and worker task containers must have no mounts")
        ),
    )
    monkeypatch.setattr(cli, "_api_http", lambda *args, **kwargs: calls.append("docker-exec"))
    monkeypatch.setattr(cli, "client", lambda name: calls.append(f"aws-{name}"))
    with pytest.raises(cli.LabError, match="immutable deployment identity"):
        cli.command_verify(SimpleNamespace())
    assert calls == []


def test_api_http_rejects_unproven_container_without_docker_exec(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "e" * 32
    task = {"taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/cluster/{task_id}"}
    monkeypatch.setattr(
        cli,
        "_run",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("docker exec must not run")),
    )
    with pytest.raises(cli.LabError, match="prior exact API container proof"):
        cli._api_http(task, {"name": "wrong", "role": "api"}, method="GET", path="/healthz")


def test_api_http_uses_immutable_image_id_and_cleans_normally(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _complete_deployment_state(image_id="sha256:" + "a" * 64)
    task_id = "e" * 32
    task = {"taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/x/{task_id}"}
    container = {"name": f"floci-ecs-{task_id}-api", "role": "api", "image": "mutable:tag"}
    calls: list[list[str]] = []
    monkeypatch.setattr(cli, "load_state", lambda root: state)
    monkeypatch.setattr(cli, "_exact_docker_object_exists", lambda *args: False)

    def run(args: list[str], **kwargs: object) -> str:
        calls.append(args)
        return json.dumps({"status": 200, "body": {"ok": True}})

    monkeypatch.setattr(cli, "_run", run)
    assert cli._api_http(task, container, method="GET", path="/healthz") == (200, {"ok": True})
    command = calls[0]
    assert command[command.index("--pull") + 1] == "never"
    assert command[command.index("--entrypoint") + 2] == state.api_image_id
    assert "mutable:tag" not in command


def test_api_http_forced_cleanup_runs_after_transport_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _complete_deployment_state(image_id="sha256:" + "a" * 64)
    task_id = "e" * 32
    task = {"taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/x/{task_id}"}
    container = {"name": f"floci-ecs-{task_id}-api", "role": "api"}
    existence = iter([False, True])
    removed: list[str] = []
    monkeypatch.setattr(cli, "load_state", lambda root: state)
    monkeypatch.setattr(cli, "_exact_docker_object_exists", lambda *args: next(existence))

    def run(args: list[str], **kwargs: object) -> str:
        if args[:3] == ["docker", "container", "rm"]:
            removed.append(args[-1])
            return ""
        raise cli.LabError("transport failed")

    monkeypatch.setattr(cli, "_run", run)
    with pytest.raises(cli.LabError, match="transport failed"):
        cli._api_http(task, container, method="GET", path="/healthz")
    assert removed == [f"{state.prefix}-verifier"]


class _Body:
    def __init__(self, value: bytes) -> None:
        self.value = value

    def read(self, limit: int) -> bytes:
        return self.value[:limit]


@pytest.mark.parametrize(
    "mutation",
    ["wrong-key", "wrong-type", "wrong-body", "too-large", "missing-etag"],
)
def test_result_object_rejects_each_contract_mutation(mutation: str) -> None:
    state = RunState.create("ci-001")
    tenant, export_id = "tenant-a", "e-" + "a" * 16
    key = f"exports/{tenant}/{export_id}.json"
    body = json.dumps({"tenant": tenant, "export_id": export_id}).encode()
    head: dict[str, object] = {
        "ContentLength": len(body),
        "ContentType": "application/json",
        "ETag": '"etag"',
    }
    requested_key = key
    if mutation == "wrong-key":
        requested_key = "exports/tenant-a/wrong.json"
    elif mutation == "wrong-type":
        head["ContentType"] = "text/plain"
    elif mutation == "wrong-body":
        body = json.dumps({"tenant": "tenant-b", "export_id": export_id}).encode()
        head["ContentLength"] = len(body)
    elif mutation == "too-large":
        head["ContentLength"] = cli.MAX_RESULT_BYTES + 1
    elif mutation == "missing-etag":
        head["ETag"] = ""

    class S3:
        def head_object(self, **kwargs):
            return head

        def get_object(self, **kwargs):
            return {"Body": _Body(body)}

    with pytest.raises(cli.LabError):
        cli._verify_result_object(
            S3(), state, tenant=tenant, export_id=export_id, object_key=requested_key
        )


def test_result_object_returns_exact_body_and_identity() -> None:
    state = RunState.create("ci-001")
    tenant, export_id = "tenant-a", "e-" + "a" * 16
    key = f"exports/{tenant}/{export_id}.json"
    expected = {"tenant": tenant, "export_id": export_id}
    body = json.dumps(expected, separators=(",", ":")).encode()

    class S3:
        def head_object(self, **kwargs):
            return {
                "ContentLength": len(body),
                "ContentType": "application/json",
                "ETag": '"etag"',
            }

        def get_object(self, **kwargs):
            return {"Body": _Body(body)}

    assert cli._verify_result_object(
        S3(), state, tenant=tenant, export_id=export_id, object_key=key
    ) == (expected, '"etag"')


def test_post_business_reproof_rejects_manifest_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    state = RunState.create("ci-001")
    drifted = RunState.create("ci-001", claim_id="b" * 32)
    touched: list[str] = []
    monkeypatch.setattr(cli, "load_state", lambda root: drifted)
    monkeypatch.setattr(cli, "_bind_claimed_outer", lambda value: touched.append("daemon"))
    with pytest.raises(cli.LabError, match="manifest changed"):
        cli._reprove_deployment_identity(state, {}, {}, [])
    assert touched == []


def test_post_business_reproof_rejects_daemon_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    state = RunState.create("ci-001")
    touched: list[str] = []
    monkeypatch.setattr(cli, "load_state", lambda root: state)
    monkeypatch.setattr(
        cli,
        "_bind_claimed_outer",
        lambda value: (_ for _ in ()).throw(cli.LabError("daemon identity drifted")),
    )
    monkeypatch.setattr(cli, "_service_tasks", lambda value: touched.append("tasks"))
    with pytest.raises(cli.LabError, match="daemon identity drifted"):
        cli._reprove_deployment_identity(state, {}, {}, [])
    assert touched == []


def test_current_claim_task_inventory_is_bound_to_exact_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-001", claim_id="a" * 32)
    operation_id = "b" * 32
    source_digest = "c" * 64
    state = replace(
        state,
        artifact_ledger=(
            ArtifactEvent(
                seq=1,
                kind="task_definition_observed",
                operation_id=operation_id,
                role="api",
                source_digest=source_digest,
                image_ref=f"{state.prefix}-api:{source_digest[:24]}",
                image_id="sha256:" + "e" * 64,
                family=state.api_family,
                task_definition_arn=(
                    "arn:aws:ecs:us-east-1:000000000000:task-definition/"
                    f"{state.api_family}:1"
                ),
            ),
        ),
    )
    task_id = "d" * 32
    name = f"floci-ecs-{task_id}-api"
    image_ref = f"{state.prefix}-api:{source_digest[:24]}"
    image_id = "sha256:" + "e" * 64

    def run(args: list[str], **_: object) -> str:
        if args[:3] == ["docker", "ps", "-a"]:
            return f"{name}\n"
        if args[-2:] == ["{{.Config.Image}}", name]:
            return image_ref + "\n"
        if args[-2:] == ["{{.Image}}", name]:
            return image_id + "\n"
        raise AssertionError(f"unexpected task inventory command: {args}")

    monkeypatch.setattr(cli, "_run", run)
    monkeypatch.setattr(
        cli,
        "_inspect_labels",
        lambda *args, **kwargs: {
            "floci": "true",
            "floci_emulator": "floci-aws",
            "io.floci": "aws",
            "io.floci.account": "000000000000",
            "io.floci.region": cli.REGION,
            "io.floci.service": "ecs",
            "io.floci.resource-id": task_id,
            "pk-stack-lab.project": cli.PROJECT,
            "pk-stack-lab.run": state.run_id,
            "pk-stack-lab.claim": state.claim_id,
            "pk-stack-lab.source-digest": source_digest,
        },
    )
    monkeypatch.setattr(
        cli,
        "_container_environment",
        lambda value: {
            "PK_STACK_LAB_CLAIM": state.claim_id,
            "PK_STACK_LAB_RUN": state.run_id,
            "PK_STACK_LAB_ROLE": "api",
            "PK_STACK_LAB_OPERATION": operation_id,
            "PK_STACK_LAB_SOURCE_DIGEST": source_digest,
        },
    )
    assert cli._docker_task_targets(state, set()) == (name,)


def test_verified_resource_evidence_is_fixed_size_across_ledger_growth() -> None:
    state = RunState.create("ci-bounded-verify")
    event = ArtifactEvent(
        seq=1,
        kind="image_planned",
        operation_id="a" * 32,
        role="api",
        source_digest="b" * 64,
        image_ref=f"{state.prefix}-api:{'b' * 24}",
    )
    baseline = cli._verified_resource_evidence(state)
    grown = cli._verified_resource_evidence(replace(state, artifact_ledger=(event,) * 500))
    assert grown == baseline
    assert "artifact_ledger" not in grown
    assert "schema_version" not in grown
    assert "teardown" not in grown
    assert len(json.dumps(grown)) < 4096


def test_frozen_image_cleanup_removes_only_plan_refs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-001")
    digest = "a" * 64
    image_id = "sha256:" + "b" * 64
    targets = (
        ImageTarget(f"{state.prefix}-api:{digest[:24]}", image_id, digest),
        ImageTarget(f"{state.prefix}-worker:{digest[:24]}", image_id, digest),
    )
    commands: list[list[str]] = []
    present = {target.ref for target in targets} | {"foreign:1"}

    def run(args: list[str], **kwargs: object) -> str:
        commands.append(args)
        if args[:3] == ["docker", "image", "rm"]:
            present.remove(args[-1])
        return ""

    monkeypatch.setattr(cli, "_run", run)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_validate_image_target", lambda *args: None)
    monkeypatch.setattr(cli, "_image_ref_exists", lambda ref: ref in present)
    monkeypatch.setattr(cli, "_docker_outer_postcondition", lambda *_args: True)
    plan = SimpleNamespace(docker=SimpleNamespace(images=targets))
    cli._phase_docker_images_absent(state, plan)
    assert [command[-1] for command in commands if command[:3] == ["docker", "image", "rm"]] == [
        target.ref for target in targets
    ]
    assert present == {"foreign:1"}


@pytest.mark.parametrize("apply", [False, True])
def test_stale_image_recovery_is_dry_run_first_and_exactly_scoped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, apply: bool
) -> None:
    run_id = "ci-stale"
    claim_id = "a" * 32
    source_digest = "b" * 64
    image_id = "sha256:" + "c" * 64
    prefix = f"pklab-{run_id}"
    tags = {
        f"{prefix}-api:{source_digest[:24]}",
        f"{prefix}-worker:{source_digest[:24]}",
    }
    present = set(tags) | {"foreign:1"}
    removed: list[str] = []
    labels = {
        "pk-stack-lab.project": cli.PROJECT,
        "pk-stack-lab.run": run_id,
        "pk-stack-lab.claim": claim_id,
        "pk-stack-lab.source-digest": source_digest,
    }

    def run(args: list[str], **_: object) -> str:
        if args[:3] == ["docker", "ps", "-a"]:
            return ""
        if args[:3] == ["docker", "image", "ls"]:
            reference = next(
                value.removeprefix("reference=")
                for value in args
                if value.startswith("reference=")
            )
            return reference + "\n" if reference in present else ""
        if args[:3] == ["docker", "image", "inspect"]:
            return image_id + "\n" if "{{.Id}}" in args else json.dumps(labels)
        if args[:3] == ["docker", "image", "rm"]:
            removed.append(args[-1])
            present.remove(args[-1])
            return ""
        raise AssertionError(f"unexpected stale recovery command: {args}")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(
        cli, "_docker_identity", lambda: ("test", "unix:///tmp/docker.sock", "daemon")
    )
    monkeypatch.setattr(cli, "_exact_docker_object_exists", lambda *_args: False)
    monkeypatch.setattr(cli, "_run", run)
    result = cli._recover_stale_images(
        SimpleNamespace(
            run_id=run_id,
            claim_id=claim_id,
            source_digest=source_digest,
            image_id=image_id,
            apply_stale_recovery=apply,
        )
    )

    if apply:
        assert set(removed) == tags
        assert present == {"foreign:1"}
        assert result["recovery"]["dry_run"] is False
    else:
        assert removed == []
        assert present == tags | {"foreign:1"}
        assert result["recovery"]["dry_run"] is True


def test_stale_image_recovery_rejects_label_mismatch_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_id = "ci-stale-mismatch"
    claim_id = "a" * 32
    source_digest = "b" * 64
    image_id = "sha256:" + "c" * 64
    mutations: list[list[str]] = []

    def run(args: list[str], **_: object) -> str:
        if args[:3] == ["docker", "ps", "-a"]:
            return ""
        if args[:3] == ["docker", "image", "ls"]:
            reference = next(
                value.removeprefix("reference=")
                for value in args
                if value.startswith("reference=")
            )
            return reference + "\n"
        if args[:3] == ["docker", "image", "inspect"]:
            if "{{.Id}}" in args:
                return image_id
            return json.dumps(
                {
                    "pk-stack-lab.project": cli.PROJECT,
                    "pk-stack-lab.run": "foreign",
                    "pk-stack-lab.claim": claim_id,
                    "pk-stack-lab.source-digest": source_digest,
                }
            )
        mutations.append(args)
        return ""

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(
        cli, "_docker_identity", lambda: ("test", "unix:///tmp/docker.sock", "daemon")
    )
    monkeypatch.setattr(cli, "_exact_docker_object_exists", lambda *_args: False)
    monkeypatch.setattr(cli, "_run", run)

    with pytest.raises(cli.LabError, match="provenance labels"):
        cli._recover_stale_images(
            SimpleNamespace(
                run_id=run_id,
                claim_id=claim_id,
                source_digest=source_digest,
                image_id=image_id,
                apply_stale_recovery=True,
            )
        )
    assert mutations == []


def test_stale_image_recovery_rejects_an_initial_fully_absent_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(
        cli, "_docker_identity", lambda: ("test", "unix:///tmp/docker.sock", "daemon")
    )
    monkeypatch.setattr(cli, "_exact_docker_object_exists", lambda *_args: False)

    def run(args: list[str], **_: object) -> str:
        if args[:3] in (["docker", "ps", "-a"], ["docker", "image", "ls"]):
            return ""
        raise AssertionError(f"unexpected stale recovery command: {args}")

    monkeypatch.setattr(cli, "_run", run)
    with pytest.raises(cli.LabError, match="no claimed immutable image tags"):
        cli._recover_stale_images(
            SimpleNamespace(
                run_id="ci-stale-absent",
                claim_id="a" * 32,
                source_digest="b" * 64,
                image_id="sha256:" + "c" * 64,
                apply_stale_recovery=True,
            )
        )


def test_stale_image_recovery_retries_after_first_tag_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_id = "ci-stale-retry"
    claim_id = "a" * 32
    source_digest = "b" * 64
    image_id = "sha256:" + "c" * 64
    tags = [
        f"pklab-{run_id}-api:{source_digest[:24]}",
        f"pklab-{run_id}-worker:{source_digest[:24]}",
    ]
    present = set(tags) | {"foreign:1"}
    removed: list[str] = []
    injected = False
    labels = {
        "pk-stack-lab.project": cli.PROJECT,
        "pk-stack-lab.run": run_id,
        "pk-stack-lab.claim": claim_id,
        "pk-stack-lab.source-digest": source_digest,
        "pk-stack-lab.operation": "d" * 32,
    }

    def run(args: list[str], **_: object) -> str:
        nonlocal injected
        if args[:3] == ["docker", "ps", "-a"]:
            return ""
        if args[:3] == ["docker", "image", "ls"]:
            reference = next(
                value.removeprefix("reference=")
                for value in args
                if value.startswith("reference=")
            )
            return reference + "\n" if reference in present else ""
        if args[:3] == ["docker", "image", "inspect"]:
            return image_id + "\n" if "{{.Id}}" in args else json.dumps(labels)
        if args[:3] == ["docker", "image", "rm"]:
            tag = args[-1]
            present.remove(tag)
            removed.append(tag)
            if not injected:
                injected = True
                raise RuntimeError("hard exit after first stale tag removal")
            return ""
        raise AssertionError(f"unexpected stale recovery command: {args}")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(
        cli, "_docker_identity", lambda: ("test", "unix:///tmp/docker.sock", "daemon")
    )
    monkeypatch.setattr(cli, "_exact_docker_object_exists", lambda *_args: False)
    monkeypatch.setattr(cli, "_run", run)
    args = SimpleNamespace(
        run_id=run_id,
        claim_id=claim_id,
        source_digest=source_digest,
        image_id=image_id,
        apply_stale_recovery=True,
    )

    with pytest.raises(RuntimeError, match="hard exit after first stale tag removal"):
        cli._recover_stale_images(args)

    assert present == {tags[1], "foreign:1"}
    result = cli._recover_stale_images(args)
    assert result["recovery"]["removed"] == [{"tag": tags[1], "image_id": image_id}]
    assert present == {"foreign:1"}
    assert removed == tags


@pytest.mark.parametrize("argv", [["not-a-command", "--output", "json"], ["--output=json"]])
def test_json_parser_failures_are_single_stdout_object(argv: list[str]) -> None:
    program = "from pk_stack_lab.cli import main; main(" + repr(argv) + ")"
    result = subprocess.run(
        [sys.executable, "-c", program], text=True, capture_output=True, check=False
    )
    assert result.returncode != 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False and payload["command"] is None


def test_json_mode_bounds_an_ordinary_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setitem(
        cli.COMMANDS, "doctor", lambda args: (_ for _ in ()).throw(RuntimeError("ordinary failure"))
    )
    with pytest.raises(SystemExit) as stopped:
        cli.main(["doctor", "--output", "json"])
    assert stopped.value.code == 1
    assert capsys.readouterr().err == ""


def test_service_tasks_rejects_service_tag_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    class Ecs:
        def describe_services(self, **kwargs):
            return {"services": [{"tags": []}]}

    monkeypatch.setattr(cli, "client", lambda name: Ecs())
    with pytest.raises(cli.LabError, match="service lacks"):
        cli._service_tasks(RunState.create("ci-001"))


def test_service_tasks_rejects_task_tag_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    state = RunState.create("ci-001")
    tags = cli._ecs_tags(state)
    task_id = "a" * 32

    class Ecs:
        def describe_services(self, **kwargs):
            return {"services": [{"tags": tags}]}

        def list_tasks(self, **kwargs):
            return {
                "taskArns": [f"arn:aws:ecs:us-east-1:000000000000:task/{state.cluster}/{task_id}"]
            }

        def describe_tasks(self, **kwargs):
            return {
                "tasks": [
                    {
                        "tags": [],
                        "taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/{state.cluster}/{task_id}",
                        "taskDefinitionArn": f"arn:aws:ecs:us-east-1:000000000000:task-definition/{state.api_family}:1",
                    }
                ]
            }

    monkeypatch.setattr(cli, "client", lambda name: Ecs())
    with pytest.raises(cli.LabError, match="task does not"):
        cli._service_tasks(state)


@pytest.mark.parametrize(
    "task",
    [
        {
            "taskArn": "arn:aws:ecs:us-east-1:000000000000:task/foreign/" + "a" * 32,
            "taskDefinitionArn": "arn:aws:ecs:us-east-1:000000000000:task-definition/pklab-ci-001-api:1",
        },
        {
            "taskArn": "arn:aws:ecs:us-east-1:000000000000:task/pklab-ci-001-cluster/" + "a" * 32,
            "taskDefinitionArn": "arn:aws:ecs:us-east-1:000000000000:task-definition/foreign:1",
        },
    ],
)
def test_service_tasks_rejects_wrong_cluster_or_task_definition_family(
    monkeypatch: pytest.MonkeyPatch, task: dict[str, str]
) -> None:
    state = RunState.create("ci-001")
    tags = cli._ecs_tags(state)

    class Ecs:
        def describe_services(self, **kwargs):
            return {"services": [{"tags": tags}]}

        def list_tasks(self, **kwargs):
            return {"taskArns": [task["taskArn"]]}

        def describe_tasks(self, **kwargs):
            return {"tasks": [{**task, "tags": tags}]}

    monkeypatch.setattr(cli, "client", lambda name: Ecs())
    with pytest.raises(cli.LabError, match="task does not"):
        cli._service_tasks(state)


@pytest.mark.parametrize(
    ("code", "allowed", "expected"),
    [
        ("ClusterNotFoundException", {"ClusterNotFoundException"}, True),
        (
            "ServiceNotFoundException",
            {"ServiceNotFoundException", "ClusterNotFoundException"},
            True,
        ),
        ("QueueDoesNotExist", {"QueueDoesNotExist"}, True),
        ("ResourceNotFoundException", {"ResourceNotFoundException"}, True),
        ("NoSuchBucket", {"NoSuchBucket"}, True),
        ("NoSuchTagSet", {"NoSuchBucket"}, False),
        ("AccessDenied", {"NoSuchBucket"}, False),
    ],
)
def test_cleanup_missing_codes_are_operation_specific(
    code: str, allowed: set[str], expected: bool
) -> None:
    error = ClientError({"Error": {"Code": code, "Message": "x"}}, "test")
    assert cli._is_missing(error, allowed) is expected


def test_up_data_directory_failure_retains_manifest_and_returns_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "compose_digest", lambda _root: "a" * 64)
    monkeypatch.setattr(
        cli, "_docker_identity", lambda: ("test", "unix:///tmp/docker.sock", "daemon")
    )
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "_compose_image", lambda socket: cli.FLOCI_IMAGE)
    monkeypatch.setattr(
        cli, "_floci_data_path", lambda **kwargs: (_ for _ in ()).throw(OSError("disk error"))
    )
    with pytest.raises(SystemExit) as stopped:
        cli.main(["up", "--run-id", "ci-003", "--acknowledge-docker-socket", "--output", "json"])
    assert stopped.value.code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is False and result["command"] == "up"
    assert load_state(tmp_path).run_id == "ci-003"


def test_down_data_directory_failure_retains_manifest_and_returns_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    state = RunState.create("ci-003")
    claim_state(tmp_path, state)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(
        cli,
        "_docker_identity",
        lambda: (state.docker_context, state.docker_socket, state.docker_daemon_id),
    )
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        cli,
        "_wait_health_once",
        lambda: (_ for _ in ()).throw(cli.LabError("endpoint unreachable")),
    )
    aws = AwsTeardownTargets(
        cluster=NamedArnTarget(state.cluster),
        services=(NamedArnTarget(state.api_service), NamedArnTarget(state.worker_service)),
        queues=(QueueTarget(state.queue), QueueTarget(state.dlq)),
        table=NamedArnTarget(state.table),
        bucket=BucketTarget(state.bucket, False, "none"),
        task_definition_families=(state.api_family, state.worker_family),
    )
    plan = TeardownPlan(
        version=1,
        claim_id=state.claim_id,
        ledger_seq=0,
        ledger_sha256=artifact_ledger_hash(()),
        compose_sha256=state.compose_sha256,
        aws_mode="discard-unreachable",
        aws=aws,
        docker=DockerTeardownTargets(
            outer_container="pk-stack-lab-floci",
            network=cli.NETWORK,
            verifier=f"{state.prefix}-verifier",
        ),
        phases=DISCARD_TEARDOWN_PHASES,
    )
    monkeypatch.setattr(cli, "_build_teardown_plan", lambda *args, **kwargs: (state, plan))
    monkeypatch.setattr(cli, "_docker_outer_postcondition", lambda *_args: True)
    monkeypatch.setattr(
        cli,
        "_remove_floci_data_path",
        lambda **kwargs: (_ for _ in ()).throw(OSError("permission error")),
    )
    monkeypatch.setattr(
        cli,
        "_execute_teardown_phase",
        lambda current, frozen, phase, socket: (
            cli._phase_floci_data_absent(current, frozen)
            if phase == "floci_data_absent"
            else None
        ),
    )
    with pytest.raises(SystemExit) as stopped:
        cli.main(["down", "--teardown-unreachable-emulator", "--output", "json"])
    assert stopped.value.code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is False and result["command"] == "down"
    assert "permission error" in result["error"]
    persisted = load_state(tmp_path)
    assert persisted.teardown is not None
    assert persisted.teardown.plan == plan
    assert persisted.teardown.completed_phases == ("docker_outer_absent",)


def test_doctor_fails_when_required_tool_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: None if name == "uv" else "/bin/docker")
    with pytest.raises(cli.LabError, match="required tools"):
        cli.command_doctor(object())


def test_task_image_has_complete_locked_runtime_closure() -> None:
    dockerfile = (cli.ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "pip install --no-cache-dir --require-hashes" in dockerfile
    requirements = (cli.ROOT / "requirements-runtime.txt").read_text(encoding="utf-8")
    for pin in (
        "boto3==1.43.86",
        "botocore==1.43.86",
        "jmespath==1.1.0",
        "python-dateutil==2.9.0.post0",
        "s3transfer==0.19.2",
        "six==1.17.0",
        "urllib3==2.7.0",
    ):
        assert pin in requirements


def test_floci_data_path_is_direct_repository_local_and_cleanup_is_exact(tmp_path: Path) -> None:
    data = cli._floci_data_path(root=tmp_path, create=True)
    assert data == tmp_path / ".lab-state" / "floci-data"
    (data / "owned-state.json").write_text("{}", encoding="utf-8")
    cli._remove_floci_data_path(root=tmp_path)
    assert not data.exists()
    cli._remove_empty_state_dir(root=tmp_path)
    assert not (tmp_path / ".lab-state").exists()


def test_floci_data_path_resolves_monkeypatched_runtime_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)

    data = cli._floci_data_path(create=True)

    assert data == tmp_path / ".lab-state" / "floci-data"
    cli._remove_floci_data_path()
    cli._remove_empty_state_dir()
    assert not (tmp_path / ".lab-state").exists()


def test_floci_data_path_rejects_symlink(tmp_path: Path) -> None:
    state = tmp_path / ".lab-state"
    state.mkdir(mode=0o700)
    target = tmp_path / "outside"
    target.mkdir()
    (state / "floci-data").symlink_to(target, target_is_directory=True)
    with pytest.raises(cli.LabError, match="direct directory"):
        cli._floci_data_path(root=tmp_path, create=False)


def test_compose_binds_only_socket_and_repository_local_floci_data() -> None:
    compose = (cli.ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert "target: /var/run/docker.sock" in compose
    assert "source: ${PK_STACK_LAB_FLOCI_DATA" in compose
    assert "target: /app/data" in compose
