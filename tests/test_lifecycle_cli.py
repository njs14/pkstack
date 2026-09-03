from __future__ import annotations

import errno
import json
import socket
from dataclasses import replace
from types import SimpleNamespace
from typing import Any, Self
from urllib.error import HTTPError, URLError

import pytest
from botocore.exceptions import ClientError

from pk_stack_lab import cli
from pk_stack_lab.config import (
    DISCARD_TEARDOWN_PHASES,
    REACHABLE_TEARDOWN_PHASES,
    AwsTeardownTargets,
    BucketTarget,
    DockerTeardownTargets,
    NamedArnTarget,
    QueueTarget,
    RunState,
    TeardownPlan,
    activate_deployment,
    append_artifact_events,
    artifact_ledger_hash,
    claim_state,
    complete_teardown_phase,
    install_teardown_plan,
    load_state,
    state_directory_absent,
)


class InjectedCrash(RuntimeError):
    """A deterministic process-boundary failure used by lifecycle tests."""


def _raise_transport_unreachable() -> None:
    transport = URLError(ConnectionRefusedError(errno.ECONNREFUSED, "connection refused"))
    raise cli._HealthTransportUnreachable("bounded HTTP probe failed") from transport


def _missing(code: str, operation: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "missing"}}, operation)


def _teardown_plan(
    state: RunState,
    *,
    aws_mode: str = "reachable",
    bucket_present: bool = False,
    object_keys: tuple[str, ...] = (),
) -> TeardownPlan:
    phases = REACHABLE_TEARDOWN_PHASES if aws_mode == "reachable" else DISCARD_TEARDOWN_PHASES
    observed_definitions = tuple(
        sorted(
            event.task_definition_arn
            for event in state.artifact_ledger
            if event.kind == "task_definition_observed"
        )
    )
    return TeardownPlan(
        version=1,
        claim_id=state.claim_id,
        ledger_seq=len(state.artifact_ledger),
        ledger_sha256=artifact_ledger_hash(state.artifact_ledger),
        compose_sha256=state.compose_sha256,
        aws_mode=aws_mode,
        aws=AwsTeardownTargets(
            cluster=NamedArnTarget(state.cluster),
            services=(
                NamedArnTarget(state.api_service),
                NamedArnTarget(state.worker_service),
            ),
            queues=(QueueTarget(state.queue), QueueTarget(state.dlq)),
            table=NamedArnTarget(state.table),
            bucket=BucketTarget(
                state.bucket,
                bucket_present,
                "drain-all-unversioned" if bucket_present else "none",
            ),
            task_definition_families=(state.api_family, state.worker_family),
            task_definition_arns=observed_definitions,
            object_keys=object_keys,
        ),
        docker=DockerTeardownTargets(
            outer_container="pk-stack-lab-floci",
            network=cli.NETWORK,
            verifier=f"{state.prefix}-verifier",
            images=cli._image_targets(state),
        ),
        phases=phases,
    )


@pytest.mark.parametrize("key", ["clusters", "services", "tasks"])
def test_every_ecs_describe_inventory_rejects_unexpected_structured_failures(key: str) -> None:
    with pytest.raises(cli.LabError, match="unexpected structured failure"):
        cli._ecs_described_items(
            {key: [], "failures": [{"reason": "ACCESS_DENIED", "detail": "injected"}]},
            key,
            label=f"{key} audit",
            allow_missing=True,
        )

    assert (
        cli._ecs_described_items(
            {key: [], "failures": [{"reason": "MISSING"}]},
            key,
            label=f"{key} audit",
            allow_missing=True,
        )
        == []
    )


def test_ecs_list_inventory_rejects_structured_failures() -> None:
    def failed_page(**_: object) -> dict[str, object]:
        return {"taskArns": [], "failures": [{"reason": "ACCESS_DENIED"}]}

    with pytest.raises(cli.LabError, match="listing returned structured failures"):
        cli._tokenized_items(failed_page, "taskArns", maxResults=100)


def test_compute_postcondition_never_treats_unexpected_cluster_failure_as_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-cluster-failure")
    plan = _teardown_plan(state)

    class Ecs:
        def describe_clusters(self, **_: object) -> dict[str, object]:
            return {
                "clusters": [],
                "failures": [{"reason": "ACCESS_DENIED", "detail": "injected"}],
            }

    monkeypatch.setattr(
        cli,
        "_task_container_postcondition",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("structured ECS failure was treated as cluster absence")
        ),
    )

    with pytest.raises(cli.LabError, match="unexpected structured failure"):
        cli._compute_postcondition(Ecs(), state, plan)


def test_first_down_refuses_compose_drift_before_inventory(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-compose-before-down", compose_sha256="a" * 64)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "compose_digest", lambda _root: "b" * 64)
    monkeypatch.setattr(
        cli,
        "client",
        lambda _name: (_ for _ in ()).throw(
            AssertionError("Compose drift reached teardown inventory")
        ),
    )

    with pytest.raises(cli.LabError, match="original run claim"):
        cli._build_teardown_plan(state, aws_mode="reachable")


def test_resumed_outer_teardown_refuses_unbound_compose_before_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-compose-resume-drift", compose_sha256="a" * 64)
    plan = _teardown_plan(state)
    docker_calls: list[list[str]] = []
    monkeypatch.setattr(
        cli,
        "_exact_docker_object_exists",
        lambda kind, name: (
            (kind, name)
            in {
                ("container", plan.docker.outer_container),
                ("network", plan.docker.network),
            }
        ),
    )
    monkeypatch.setattr(cli, "_inspect_labels", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_remove_frozen_task_containers", lambda *_args: None)
    monkeypatch.setattr(cli, "_aws_postcondition", lambda *_args: None)
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "compose_digest", lambda _root: "b" * 64)
    monkeypatch.setattr(cli, "_run", lambda args, **_kwargs: docker_calls.append(args) or "")

    with pytest.raises(cli.LabError, match="frozen teardown plan"):
        cli._phase_docker_outer_absent(state, plan, "unix:///test/docker.sock")
    assert docker_calls == []


def _record_complete_deployment(
    root: Any,
    state: RunState,
    *,
    digest: str,
    operation_id: str,
    image_id: str,
    revision: int,
) -> RunState:
    refs = {
        "api": f"{state.prefix}-api:{digest[:24]}",
        "worker": f"{state.prefix}-worker:{digest[:24]}",
    }
    state = append_artifact_events(
        root,
        state,
        *cli._deployment_events(
            state,
            operation_id=operation_id,
            kind="image_planned",
            digest=digest,
            image_refs=refs,
        ),
    )
    state = append_artifact_events(
        root,
        state,
        *cli._deployment_events(
            state,
            operation_id=operation_id,
            kind="image_observed",
            digest=digest,
            image_refs=refs,
            image_id=image_id,
        ),
    )
    state = append_artifact_events(
        root,
        state,
        *cli._deployment_events(
            state,
            operation_id=operation_id,
            kind="task_definition_planned",
            digest=digest,
            image_refs=refs,
        ),
    )
    arns: dict[str, str] = {}
    for role in ("api", "worker"):
        family = state.api_family if role == "api" else state.worker_family
        arn = f"arn:aws:ecs:us-east-1:000000000000:task-definition/{family}:{revision}"
        arns[role] = arn
        state = append_artifact_events(
            root,
            state,
            *cli._deployment_events(
                state,
                operation_id=operation_id,
                kind="task_definition_observed",
                digest=digest,
                image_refs=refs,
                image_id=image_id,
                role=role,
                task_definition_arn=arn,
            ),
        )
    return activate_deployment(
        root,
        state,
        source_digest=digest,
        image_id=image_id,
        api_task_definition_arn=arns["api"],
        worker_task_definition_arn=arns["worker"],
    )


class EmptyEcsInventory:
    def list_task_definitions(self, **_: object) -> dict[str, list[str]]:
        return {"taskDefinitionArns": []}


def test_deploy_persists_image_plans_before_first_docker_mutation(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-plan-first")
    claim_state(tmp_path, state)
    digest = "a" * 64
    observed_at_build: list[RunState] = []

    def run(args: list[str], **_: object) -> str:
        if args[:2] == ["docker", "build"]:
            observed_at_build.append(load_state(tmp_path))
            raise InjectedCrash("after durable plan, before Docker mutation")
        raise AssertionError(f"unexpected command before build: {args}")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_claimed_outer", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "source_digest", lambda _: digest)
    monkeypatch.setattr(cli, "_image_ref_exists", lambda _ref: False)
    monkeypatch.setattr(cli, "_run", run)
    monkeypatch.setattr(cli, "client", lambda name: EmptyEcsInventory())

    with pytest.raises(InjectedCrash, match="durable plan"):
        cli.command_deploy(SimpleNamespace())

    assert len(observed_at_build) == 1
    persisted = observed_at_build[0]
    assert [(event.kind, event.role) for event in persisted.artifact_ledger] == [
        ("image_planned", "api"),
        ("image_planned", "worker"),
    ]
    assert {event.operation_id for event in persisted.artifact_ledger}.__len__() == 1
    assert all(event.source_digest == digest for event in persisted.artifact_ledger)
    assert (
        persisted.source_digest,
        persisted.api_image_id,
        persisted.worker_image_id,
        persisted.api_task_definition_arn,
        persisted.worker_task_definition_arn,
    ) == ("", "", "", "", "")


def test_failed_redeploy_keeps_last_good_active_identity_and_ledgers_candidate_artifacts(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-redeploy")
    claim_state(tmp_path, state)
    old_digest = "1" * 64
    old_image_id = "sha256:" + "2" * 64
    state = _record_complete_deployment(
        tmp_path,
        state,
        digest=old_digest,
        operation_id="3" * 32,
        image_id=old_image_id,
        revision=1,
    )
    old_active = (
        state.source_digest,
        state.api_image_id,
        state.worker_image_id,
        state.api_task_definition_arn,
        state.worker_task_definition_arn,
    )
    new_digest = "4" * 64
    new_image_id = "sha256:" + "5" * 64
    present_images: set[str] = set()

    class Sqs:
        def get_queue_url(self, **_: object) -> dict[str, str]:
            return {"QueueUrl": f"http://floci:4566/000000000000/{state.queue}"}

    class Ecs(EmptyEcsInventory):
        def __init__(self) -> None:
            self.requests: list[dict[str, Any]] = []

        def register_task_definition(self, **request: Any) -> dict[str, object]:
            self.requests.append(request)
            arn = f"arn:aws:ecs:us-east-1:000000000000:task-definition/{request['family']}:2"
            return {"taskDefinition": {"taskDefinitionArn": arn}}

        def describe_services(self, **_: object) -> dict[str, list[object]]:
            return {"services": []}

        def create_service(self, **_: object) -> None:
            return None

    ecs = Ecs()

    def client(name: str) -> object:
        return Sqs() if name == "sqs" else ecs

    def run(args: list[str], **_: object) -> str:
        if args[:3] == ["docker", "image", "inspect"]:
            return new_image_id + "\n"
        if args[:2] == ["docker", "build"]:
            present_images.add(args[args.index("-t") + 1])
            return ""
        if args[:2] == ["docker", "tag"]:
            present_images.add(args[-1])
            return ""
        raise AssertionError(f"unexpected Docker command: {args}")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_claimed_outer", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "source_digest", lambda _: new_digest)
    monkeypatch.setattr(cli, "_image_ref_exists", lambda ref: ref in present_images)
    monkeypatch.setattr(cli, "_validate_image_target", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_run", run)
    monkeypatch.setattr(cli, "client", client)
    monkeypatch.setattr(
        cli,
        "_validate_registered_task_definition",
        lambda _ecs, _state, **kwargs: kwargs["registered"]["taskDefinitionArn"],
    )
    monkeypatch.setattr(
        cli,
        "_wait_services",
        lambda _: (_ for _ in ()).throw(InjectedCrash("services did not stabilize")),
    )

    with pytest.raises(InjectedCrash, match="did not stabilize"):
        cli.command_deploy(SimpleNamespace())

    persisted = load_state(tmp_path)
    assert (
        persisted.source_digest,
        persisted.api_image_id,
        persisted.worker_image_id,
        persisted.api_task_definition_arn,
        persisted.worker_task_definition_arn,
    ) == old_active
    candidate_events = [
        event for event in persisted.artifact_ledger if event.source_digest == new_digest
    ]
    assert [(event.kind, event.role) for event in candidate_events] == [
        ("image_planned", "api"),
        ("image_planned", "worker"),
        ("image_observed", "api"),
        ("image_observed", "worker"),
        ("task_definition_planned", "api"),
        ("task_definition_planned", "worker"),
        ("task_definition_observed", "api"),
        ("task_definition_observed", "worker"),
    ]
    assert len(ecs.requests) == 2
    assert all(
        request["containerDefinitions"][0]["dockerLabels"]["pk-stack-lab.source-digest"]
        == new_digest
        for request in ecs.requests
    )


def test_reconcile_pending_task_definition_durably_records_prior_registration(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-register-crash")
    claim_state(tmp_path, state)
    digest = "6" * 64
    image_id = "sha256:" + "7" * 64
    operation_id = "8" * 32
    refs = {
        "api": f"{state.prefix}-api:{digest[:24]}",
        "worker": f"{state.prefix}-worker:{digest[:24]}",
    }
    for kind, observed_id in (
        ("image_planned", ""),
        ("image_observed", image_id),
        ("task_definition_planned", ""),
    ):
        state = append_artifact_events(
            tmp_path,
            state,
            *cli._deployment_events(
                state,
                operation_id=operation_id,
                kind=kind,
                digest=digest,
                image_refs=refs,
                image_id=observed_id,
            ),
        )

    candidate = replace(
        state,
        source_digest=digest,
        api_image_id=image_id,
        worker_image_id=image_id,
    )
    queue_url = f"http://floci:4566/000000000000/{state.queue}"
    request = cli._task_definition(
        candidate,
        role="api",
        image=refs["api"],
        queue_url=queue_url,
        operation_id=operation_id,
    )
    arn = f"arn:aws:ecs:us-east-1:000000000000:task-definition/{state.api_family}:1"
    definition = {key: value for key, value in request.items() if key != "tags"}
    definition.update(taskDefinitionArn=arn, revision=1, status="ACTIVE")

    class Ecs:
        def list_task_definitions(self, **request: object) -> dict[str, list[str]]:
            if request["familyPrefix"] == state.api_family and request["status"] == "ACTIVE":
                return {"taskDefinitionArns": [arn]}
            return {"taskDefinitionArns": []}

        def describe_task_definition(self, **_: object) -> dict[str, object]:
            return {"taskDefinition": definition, "tags": cli._ecs_tags(state)}

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    reconciled = cli._reconcile_pending_task_definitions(state, Ecs())
    observed = [
        event for event in reconciled.artifact_ledger if event.kind == "task_definition_observed"
    ]

    assert len(observed) == 1
    assert observed[0].operation_id == operation_id
    assert observed[0].role == "api"
    assert observed[0].task_definition_arn == arn
    assert load_state(tmp_path) == reconciled
    assert cli._reconcile_pending_task_definitions(reconciled, Ecs()) == reconciled


def test_deploy_refuses_frozen_teardown_before_external_access(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-deploy-frozen")
    claim_state(tmp_path, state)
    state = install_teardown_plan(tmp_path, state, _teardown_plan(state))
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(
        cli,
        "_bind_daemon",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("frozen deployment reached Docker")
        ),
    )
    monkeypatch.setattr(
        cli,
        "client",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("frozen deployment reached AWS")
        ),
    )

    with pytest.raises(cli.LabError, match="teardown has started"):
        cli.command_deploy(SimpleNamespace())
    assert load_state(tmp_path) == state


def test_down_installs_frozen_plan_before_first_mutation(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-frozen-first")
    claim_state(tmp_path, state)
    plan = _teardown_plan(state)
    observed: list[str] = []

    def execute(current: RunState, frozen: TeardownPlan, phase: str, _: str) -> None:
        persisted = load_state(tmp_path)
        assert persisted.teardown is not None
        assert persisted.teardown.plan == frozen == plan
        assert persisted.teardown.completed_phases == ()
        observed.append(phase)
        raise InjectedCrash("first external mutation boundary")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "compose_digest", lambda _root: state.compose_sha256)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        cli,
        "_build_teardown_plan",
        lambda current, *, aws_mode: (current, plan),
    )
    monkeypatch.setattr(cli, "_execute_teardown_phase", execute)

    with pytest.raises(InjectedCrash, match="mutation boundary"):
        cli.command_down(SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=False))

    persisted = load_state(tmp_path)
    assert persisted.teardown is not None
    assert persisted.teardown.plan == plan
    assert persisted.teardown.completed_phases == ()
    assert observed == [REACHABLE_TEARDOWN_PHASES[0]]


@pytest.mark.parametrize("failed_index", range(len(REACHABLE_TEARDOWN_PHASES)))
def test_down_crash_boundary_retains_exact_prefix_and_resume_skips_completed_phases(
    failed_index: int, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create(f"ci-resume-{failed_index}")
    claim_state(tmp_path, state)
    plan = _teardown_plan(state)
    state = install_teardown_plan(tmp_path, state, plan)
    first_calls: list[str] = []
    second_calls: list[str] = []
    terminal_checks: list[str] = []

    def first_execute(_: RunState, __: TeardownPlan, phase: str, ___: str) -> None:
        first_calls.append(phase)
        if phase == plan.phases[failed_index]:
            raise InjectedCrash("phase boundary")

    def forbidden_reinventory(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("a persisted teardown plan must not be rebuilt")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "compose_digest", lambda _root: state.compose_sha256)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_build_teardown_plan", forbidden_reinventory)
    monkeypatch.setattr(cli, "_execute_teardown_phase", first_execute)
    monkeypatch.setattr(
        cli,
        "_local_postcondition",
        lambda *_args: terminal_checks.append("terminal-local-proof"),
    )

    args = SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=False)
    with pytest.raises(InjectedCrash, match="phase boundary"):
        cli.command_down(args)

    persisted = load_state(tmp_path)
    assert persisted.teardown is not None
    assert persisted.teardown.completed_phases == plan.phases[:failed_index]
    assert first_calls == list(plan.phases[: failed_index + 1])

    monkeypatch.setattr(
        cli,
        "_execute_teardown_phase",
        lambda _state, _plan, phase, _socket: second_calls.append(phase),
    )
    result = cli.command_down(args)

    assert second_calls == list(plan.phases[failed_index:])
    assert terminal_checks == ["terminal-local-proof"]
    assert result["cleanup"]["completed_phases"] == list(plan.phases)
    assert state_directory_absent(tmp_path)


def test_resumed_down_rejects_foreign_task_before_any_phase_mutation(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-foreign-task")
    claim_state(tmp_path, state)
    plan = _teardown_plan(state)
    state = install_teardown_plan(tmp_path, state, plan)
    task_id = "a" * 32
    task_name = f"floci-ecs-{task_id}-api"
    reached: list[str] = []

    def inspect(kind: str, name: str, *, missing_ok: bool = False) -> dict[str, str]:
        if kind == "network":
            return {**cli._NETWORK_LABELS, "pk-stack-lab.claim": state.claim_id}
        if name == "pk-stack-lab-floci":
            return {**cli._OUTER_LABELS, "pk-stack-lab.claim": state.claim_id}
        return {
            "floci": "true",
            "floci_emulator": "floci-aws",
            "io.floci": "aws",
            "io.floci.service": "ecs",
            "io.floci.resource-id": task_id,
        }

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_inspect_labels", inspect)
    monkeypatch.setattr(cli, "_run", lambda *_args, **_kwargs: task_name + "\n")
    monkeypatch.setattr(
        cli, "_container_environment", lambda _name: {"PK_STACK_LAB_CLAIM": "f" * 32}
    )
    monkeypatch.setattr(
        cli,
        "_execute_teardown_phase",
        lambda *_args: reached.append("phase-mutation"),
    )

    with pytest.raises(cli.LabError, match="foreign Floci ECS task"):
        cli.command_down(SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=False))

    assert reached == []
    assert load_state(tmp_path) == state


def test_down_explicit_discard_plan_never_constructs_aws_clients(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-discard")
    claim_state(tmp_path, state)
    phases: list[str] = []

    def no_aws_clients(name: str) -> object:
        raise AssertionError(f"discard teardown constructed forbidden AWS client: {name}")

    def execute(_: RunState, plan: TeardownPlan, phase: str, __: str) -> None:
        persisted = load_state(tmp_path)
        assert persisted.teardown is not None
        assert plan == persisted.teardown.plan
        assert plan.aws_mode == "discard-unreachable"
        phases.append(phase)
        raise InjectedCrash("inspect persisted discard plan")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "compose_digest", lambda _root: state.compose_sha256)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        cli,
        "_wait_health_once",
        _raise_transport_unreachable,
    )
    monkeypatch.setattr(cli, "client", no_aws_clients)
    monkeypatch.setattr(cli, "_inspect_labels", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_run", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(cli, "_execute_teardown_phase", execute)

    with pytest.raises(InjectedCrash, match="discard plan"):
        cli.command_down(SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=True))

    persisted = load_state(tmp_path)
    assert persisted.teardown is not None
    assert persisted.teardown.plan.aws_mode == "discard-unreachable"
    assert persisted.teardown.plan.phases == DISCARD_TEARDOWN_PHASES
    assert phases == [DISCARD_TEARDOWN_PHASES[0]]


@pytest.mark.parametrize(
    "error",
    [
        URLError(ConnectionRefusedError(errno.ECONNREFUSED, "connection refused")),
        TimeoutError("timed out"),
        URLError(socket.gaierror(socket.EAI_NONAME, "name not known")),
        OSError(errno.EHOSTUNREACH, "host unreachable"),
    ],
    ids=("connection-refused", "timeout", "dns", "socket-unreachable"),
)
def test_discard_transport_classifier_accepts_only_typed_unreachability(
    error: BaseException,
) -> None:
    assert cli._is_transport_unreachable(error)


@pytest.mark.parametrize(
    "error",
    [
        HTTPError("http://127.0.0.1/health", 503, "unavailable", None, None),
        json.JSONDecodeError("invalid", "not-json", 0),
        URLError("opaque failure"),
        PermissionError(errno.EACCES, "permission denied"),
    ],
    ids=("http-response", "malformed-json", "untyped-url-error", "permission-error"),
)
def test_discard_transport_classifier_rejects_responses_and_ambiguous_errors(
    error: BaseException,
) -> None:
    assert not cli._is_transport_unreachable(error)


@pytest.mark.parametrize(
    "error",
    [
        URLError(ConnectionRefusedError(errno.ECONNREFUSED, "connection refused")),
        TimeoutError("timed out"),
        URLError(socket.gaierror(socket.EAI_NONAME, "name not known")),
        OSError(errno.ENETUNREACH, "network unreachable"),
    ],
    ids=("connection-refused", "timeout", "dns", "socket-unreachable"),
)
def test_http_health_probe_emits_typed_transport_unreachability(
    error: BaseException, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FailingOpener:
        def open(self, *_args: object, **_kwargs: object) -> object:
            raise error

    monkeypatch.setattr(cli, "build_opener", lambda *_args: FailingOpener())

    with pytest.raises(cli._HealthTransportUnreachable):
        cli._http_json("http://127.0.0.1/health")


@pytest.mark.parametrize("response_kind", ["http-404", "http-503", "malformed-json"])
def test_http_health_probe_never_types_a_response_failure_as_unreachable(
    response_kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Response:
        status = 200

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return b"not-json"

    class RespondingOpener:
        def open(self, *_args: object, **_kwargs: object) -> object:
            if response_kind.startswith("http-"):
                code = int(response_kind.removeprefix("http-"))
                raise HTTPError(
                    "http://127.0.0.1/health",
                    code,
                    "endpoint responded",
                    None,
                    None,
                )
            return Response()

    monkeypatch.setattr(cli, "build_opener", lambda *_args: RespondingOpener())

    with pytest.raises(cli.LabError) as stopped:
        cli._http_json("http://127.0.0.1/health")

    assert type(stopped.value) is cli.LabError


@pytest.mark.parametrize("frozen_reachable_plan", [False, True], ids=("initial", "frozen"))
@pytest.mark.parametrize("response_kind", ["http-404", "http-503", "malformed-json"])
def test_discard_refuses_responding_or_malformed_health_endpoint_without_mutation(
    response_kind: str,
    frozen_reachable_plan: bool,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create(f"ci-refuse-{response_kind}-{int(frozen_reachable_plan)}")
    claim_state(tmp_path, state)
    if frozen_reachable_plan:
        state = install_teardown_plan(tmp_path, state, _teardown_plan(state))

    def response_failure() -> None:
        if response_kind.startswith("http-"):
            code = int(response_kind.removeprefix("http-"))
            cause: BaseException = HTTPError(
                "http://127.0.0.1/health",
                code,
                "endpoint responded",
                None,
                None,
            )
        else:
            cause = json.JSONDecodeError("invalid", "not-json", 0)
        raise cli.LabError("bounded HTTP probe failed") from cause

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("failed health authorization crossed a mutation boundary")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_wait_health_once", response_failure)
    monkeypatch.setattr(cli, "_build_teardown_plan", forbidden)
    monkeypatch.setattr(cli, "transition_teardown_to_discard", forbidden)
    monkeypatch.setattr(cli, "_execute_teardown_phase", forbidden)

    with pytest.raises(cli.LabError, match="without proving transport unreachability"):
        cli.command_down(SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=True))

    assert load_state(tmp_path) == state


def test_down_transitions_frozen_reachable_plan_without_reinventory_or_aws(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-frozen-discard")
    claim_state(tmp_path, state)
    reachable = _teardown_plan(state)
    state = install_teardown_plan(tmp_path, state, reachable)
    for phase in REACHABLE_TEARDOWN_PHASES[:2]:
        state = complete_teardown_phase(tmp_path, state, phase)

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("transition re-inventoried frozen targets or constructed AWS clients")

    def execute(_: RunState, plan: TeardownPlan, phase: str, __: str) -> None:
        persisted = load_state(tmp_path)
        assert persisted.teardown is not None
        assert persisted.teardown.transition is not None
        assert persisted.teardown.transition.from_plan_sha256 == state.teardown.plan_sha256
        assert (
            persisted.teardown.transition.from_completed_phases == (REACHABLE_TEARDOWN_PHASES[:2])
        )
        assert plan.aws == reachable.aws
        assert plan.docker == reachable.docker
        assert plan.claim_id == reachable.claim_id
        assert plan.compose_sha256 == reachable.compose_sha256
        assert plan.aws_mode == "discard-unreachable"
        assert plan.phases == DISCARD_TEARDOWN_PHASES
        assert phase == DISCARD_TEARDOWN_PHASES[0]
        raise InjectedCrash("post-transition phase boundary")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        cli,
        "_wait_health_once",
        _raise_transport_unreachable,
    )
    monkeypatch.setattr(cli, "_build_teardown_plan", forbidden)
    monkeypatch.setattr(cli, "client", forbidden)
    monkeypatch.setattr(cli, "_execute_teardown_phase", execute)

    with pytest.raises(InjectedCrash, match="post-transition"):
        cli.command_down(SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=True))

    persisted = load_state(tmp_path)
    assert persisted.teardown is not None
    assert persisted.teardown.plan.aws_mode == "discard-unreachable"
    assert persisted.teardown.completed_phases == ()


def test_down_refuses_frozen_reachable_transition_while_floci_is_reachable(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-frozen-still-reachable")
    claim_state(tmp_path, state)
    state = install_teardown_plan(tmp_path, state, _teardown_plan(state))

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("reachable refusal crossed the transition or mutation boundary")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_wait_health_once", lambda: None)
    monkeypatch.setattr(cli, "transition_teardown_to_discard", forbidden)
    monkeypatch.setattr(cli, "_execute_teardown_phase", forbidden)

    with pytest.raises(cli.LabError, match="endpoint responded; refuse control-plane discard"):
        cli.command_down(SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=True))

    assert load_state(tmp_path) == state


def test_transitioned_discard_crash_retries_canonical_suffix_without_health_or_aws(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-frozen-discard-retry")
    claim_state(tmp_path, state)
    reachable = _teardown_plan(state)
    state = install_teardown_plan(tmp_path, state, reachable)
    first_calls: list[str] = []
    retry_calls: list[str] = []

    def first_execute(_: RunState, plan: TeardownPlan, phase: str, __: str) -> None:
        assert plan.aws_mode == "discard-unreachable"
        first_calls.append(phase)
        if phase == DISCARD_TEARDOWN_PHASES[1]:
            raise InjectedCrash("discard phase boundary")

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("discard retry attempted health, inventory, or AWS access")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        cli,
        "_wait_health_once",
        _raise_transport_unreachable,
    )
    monkeypatch.setattr(cli, "_execute_teardown_phase", first_execute)

    with pytest.raises(InjectedCrash, match="discard phase"):
        cli.command_down(SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=True))

    interrupted = load_state(tmp_path)
    assert interrupted.teardown is not None
    assert interrupted.teardown.completed_phases == DISCARD_TEARDOWN_PHASES[:1]

    monkeypatch.setattr(cli, "_wait_health_once", forbidden)
    monkeypatch.setattr(cli, "_build_teardown_plan", forbidden)
    monkeypatch.setattr(cli, "client", forbidden)

    def retry_execute(_: RunState, plan: TeardownPlan, phase: str, __: str) -> None:
        assert plan.aws_mode == "discard-unreachable"
        retry_calls.append(phase)

    monkeypatch.setattr(
        cli,
        "_execute_teardown_phase",
        retry_execute,
    )
    monkeypatch.setattr(cli, "_local_postcondition", lambda *_args: None)
    result = cli.command_down(
        SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=False)
    )

    assert retry_calls == list(DISCARD_TEARDOWN_PHASES[1:])
    assert result["cleanup"]["control_plane"] == "discarded"
    transition = result["cleanup"]["control_plane_transition"]
    assert transition["from_aws_mode"] == "reachable"
    assert transition["to_aws_mode"] == "discard-unreachable"
    assert transition["reason"] == "floci-unreachable-control-plane-discard"
    assert transition["from_plan_sha256"] == state.teardown.plan_sha256
    assert state_directory_absent(tmp_path)


def test_compute_phase_removes_task_containers_before_accepting_postcondition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-compute-order")
    plan = _teardown_plan(state)
    events: list[str] = []

    monkeypatch.setattr(cli, "client", lambda name: object())
    monkeypatch.setattr(cli, "_service_target", lambda *_args: None)
    monkeypatch.setattr(
        cli,
        "_remove_frozen_task_containers",
        lambda *_args: events.append("task-containers-absent"),
    )

    def postcondition(*_: object) -> bool:
        assert events == ["task-containers-absent"]
        events.append("compute-proved")
        return True

    monkeypatch.setattr(cli, "_compute_postcondition", postcondition)
    cli._phase_aws_compute_absent(state, plan)

    assert events == ["task-containers-absent", "compute-proved"]


def test_task_container_removal_is_exact_and_rechecks_current_claim(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-task-remove", claim_id="a" * 32)
    claim_state(tmp_path, state)
    state = _record_complete_deployment(
        tmp_path,
        state,
        digest="b" * 64,
        operation_id="c" * 32,
        image_id="sha256:" + "d" * 64,
        revision=1,
    )
    name = f"floci-ecs-{'e' * 32}-api"
    base = _teardown_plan(state)
    plan = replace(base, docker=replace(base.docker, task_containers=(name,)))
    present = {name}
    validated: list[str] = []

    monkeypatch.setattr(
        cli,
        "_exact_docker_object_exists",
        lambda kind, value: kind == "container" and value in present,
    )
    monkeypatch.setattr(
        cli,
        "_current_claim_task_containers",
        lambda _state: tuple(sorted(present)),
    )
    monkeypatch.setattr(cli, "_inspect_labels", lambda *_args, **_kwargs: {"bound": "yes"})
    monkeypatch.setattr(
        cli,
        "_validate_task_container_claim",
        lambda _state, value, _labels: validated.append(value),
    )

    def run(args: list[str], **_: object) -> str:
        assert args == ["docker", "container", "rm", "-f", name]
        present.remove(name)
        return ""

    monkeypatch.setattr(cli, "_run", run)
    cli._remove_frozen_task_containers(state, plan)

    assert validated == [name]
    assert present == set()


def test_data_phase_refuses_when_compute_or_task_container_absence_regresses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-data-guard")
    plan = _teardown_plan(state)
    requested: list[str] = []

    def client(name: str) -> object:
        requested.append(name)
        return object()

    monkeypatch.setattr(cli, "client", client)
    monkeypatch.setattr(cli, "_compute_postcondition", lambda *_args: False)

    with pytest.raises(cli.LabError, match="compute prerequisite regressed"):
        cli._phase_aws_data_absent(state, plan)
    assert requested == ["ecs"]


@pytest.mark.parametrize("kind", ["cluster", "service"])
def test_compute_postcondition_rejects_resource_that_appeared_after_freeze(
    kind: str,
) -> None:
    state = RunState.create(f"ci-late-{kind}")
    plan = _teardown_plan(state)
    if kind == "service":
        plan = replace(
            plan,
            aws=replace(plan.aws, cluster=NamedArnTarget(state.cluster, "arn:frozen-cluster")),
        )

    class Ecs:
        def describe_clusters(self, **_: object) -> dict[str, list[dict[str, object]]]:
            if kind == "cluster":
                return {
                    "clusters": [
                        {
                            "clusterName": state.cluster,
                            "clusterArn": "arn:late-cluster",
                            "tags": cli.ownership_tags(state),
                        }
                    ]
                }
            return {
                "clusters": [
                    {
                        "clusterName": state.cluster,
                        "clusterArn": "arn:frozen-cluster",
                        "tags": cli.ownership_tags(state),
                    }
                ]
            }

        def describe_services(self, **request: object) -> dict[str, list[dict[str, object]]]:
            if kind == "service" and request["services"] == [state.api_service]:
                return {
                    "services": [
                        {
                            "serviceName": state.api_service,
                            "serviceArn": "arn:late-service",
                            "tags": cli.ownership_tags(state),
                        }
                    ]
                }
            return {"services": []}

    with pytest.raises(cli.LabError, match=f"{kind} appeared after"):
        cli._compute_postcondition(Ecs(), state, plan)


def test_outer_phase_reproves_aws_before_any_docker_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-outer-reproof")
    plan = _teardown_plan(state)
    monkeypatch.setattr(
        cli,
        "_aws_postcondition",
        lambda *_args: (_ for _ in ()).throw(cli.LabError("AWS regressed")),
    )
    monkeypatch.setattr(
        cli,
        "_exact_docker_object_exists",
        lambda kind, name: kind == "container" and name == plan.docker.outer_container,
    )
    monkeypatch.setattr(
        cli,
        "_inspect_labels",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("Docker inspection preceded AWS reproof")
        ),
    )

    with pytest.raises(cli.LabError, match="AWS regressed"):
        cli._phase_docker_outer_absent(state, plan, "unix:///test/docker.sock")


def test_outer_phase_resumes_after_exact_removal_without_calling_dead_aws(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-outer-resume")
    plan = _teardown_plan(state)
    monkeypatch.setattr(cli, "_exact_docker_object_exists", lambda *_args: False)
    monkeypatch.setattr(cli, "_current_claim_task_containers", lambda _state: ())
    monkeypatch.setattr(
        cli,
        "_aws_postcondition",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("resume after outer removal must not call dead AWS")
        ),
    )
    monkeypatch.setattr(
        cli,
        "_run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("already-absent outer objects must not be mutated")
        ),
    )

    cli._phase_docker_outer_absent(state, plan, "unix:///test/docker.sock")


@pytest.mark.parametrize("phase", ["floci-data", "images"])
def test_later_local_phases_refuse_reappeared_outer_boundary(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    state = RunState.create(f"ci-outer-guard-{phase}")
    plan = _teardown_plan(state)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_docker_outer_postcondition", lambda *_args: False)
    monkeypatch.setattr(
        cli,
        "_remove_floci_data_path",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("Floci data mutation preceded outer proof")
        ),
    )
    monkeypatch.setattr(
        cli,
        "_validate_image_target",
        lambda *_args: (_ for _ in ()).throw(AssertionError("image mutation preceded outer proof")),
    )

    with pytest.raises(cli.LabError, match="outer prerequisite regressed"):
        if phase == "floci-data":
            cli._phase_floci_data_absent(state, plan)
        else:
            cli._phase_docker_images_absent(state, plan)


def test_fully_checkpointed_resume_rechecks_local_state_before_manifest_unlink(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-terminal-resume")
    claim_state(tmp_path, state)
    plan = _teardown_plan(state)
    state = install_teardown_plan(tmp_path, state, plan)
    for phase in plan.phases:
        state = complete_teardown_phase(tmp_path, state, phase)

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        cli,
        "_local_postcondition",
        lambda *_args: (_ for _ in ()).throw(cli.LabError("reappeared local artifact")),
    )

    with pytest.raises(cli.LabError, match="reappeared local artifact"):
        cli.command_down(SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=False))
    assert load_state(tmp_path) == state


@pytest.mark.parametrize("kind", ["service", "task"])
def test_compute_postcondition_is_cluster_wide(monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    state = RunState.create(f"ci-cluster-wide-{kind}")
    base = _teardown_plan(state)
    cluster_arn = f"arn:aws:ecs:us-east-1:000000000000:cluster/{state.cluster}"
    plan = replace(base, aws=replace(base.aws, cluster=NamedArnTarget(state.cluster, cluster_arn)))

    class Ecs:
        def describe_clusters(self, **_: object) -> dict[str, list[dict[str, object]]]:
            return {
                "clusters": [
                    {
                        "clusterName": state.cluster,
                        "clusterArn": cluster_arn,
                        "tags": cli.ownership_tags(state),
                    }
                ]
            }

        def describe_services(self, **_: object) -> dict[str, list[object]]:
            return {"services": []}

        def list_services(self, **_: object) -> dict[str, list[str]]:
            return {"serviceArns": ["arn:unplanned-service"] if kind == "service" else []}

        def list_tasks(self, **request: object) -> dict[str, list[str]]:
            return {
                "taskArns": ["arn:unplanned-task"]
                if kind == "task" and request["desiredStatus"] == "RUNNING"
                else []
            }

    monkeypatch.setattr(cli, "_task_container_postcondition", lambda *_args: True)
    assert cli._compute_postcondition(Ecs(), state, plan) is False


def test_compute_phase_times_out_without_checkpoint_when_compute_stays_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-compute-stuck")
    plan = _teardown_plan(state)
    probes = 0

    def postcondition(*_: object) -> bool:
        nonlocal probes
        probes += 1
        return False

    monkeypatch.setattr(cli, "client", lambda _name: object())
    monkeypatch.setattr(cli, "_service_target", lambda *_args: None)
    monkeypatch.setattr(cli, "_remove_frozen_task_containers", lambda *_args: None)
    monkeypatch.setattr(cli, "_compute_postcondition", postcondition)
    monkeypatch.setattr(cli.time, "sleep", lambda _seconds: None)

    with pytest.raises(cli.LabError, match="did not reach the stopped postcondition"):
        cli._phase_aws_compute_absent(state, plan)
    assert probes == 90


def test_aws_data_phase_drains_more_than_one_thousand_objects_before_checkpoint(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-s3-drain")
    claim_state(tmp_path, state)
    keys = tuple(f"exports/object-{index:04d}.json" for index in range(1001))
    plan = _teardown_plan(state, bucket_present=True, object_keys=keys)
    state = install_teardown_plan(tmp_path, state, plan)
    state = complete_teardown_phase(tmp_path, state, REACHABLE_TEARDOWN_PHASES[0])

    class Sqs:
        def get_queue_url(self, **_: object) -> object:
            raise _missing("QueueDoesNotExist", "GetQueueUrl")

    class Ddb:
        def describe_table(self, **_: object) -> object:
            raise _missing("ResourceNotFoundException", "DescribeTable")

    class S3:
        def __init__(self) -> None:
            self.present = True
            self.objects = list(keys)
            self.list_calls = 0
            self.deleted_batches: list[int] = []

        def head_bucket(self, **_: object) -> dict[str, object]:
            if not self.present:
                raise _missing("NoSuchBucket", "HeadBucket")
            return {}

        def get_bucket_tagging(self, **_: object) -> dict[str, object]:
            return {"TagSet": cli.ownership_tags(state)}

        def list_objects_v2(self, **_: object) -> dict[str, object]:
            self.list_calls += 1
            page = self.objects[:1000]
            return {
                "Contents": [{"Key": key} for key in page],
                "IsTruncated": len(self.objects) > len(page),
            }

        def delete_objects(self, **request: Any) -> dict[str, object]:
            batch = [item["Key"] for item in request["Delete"]["Objects"]]
            self.deleted_batches.append(len(batch))
            selected = set(batch)
            self.objects = [key for key in self.objects if key not in selected]
            return {"Deleted": [{"Key": key} for key in batch]}

        def delete_bucket(self, **_: object) -> None:
            if self.objects:
                raise AssertionError("bucket deletion preceded complete object drain")
            self.present = False

    sqs, ddb, s3 = Sqs(), Ddb(), S3()

    def client(name: str) -> object:
        return {"ecs": object(), "sqs": sqs, "dynamodb": ddb, "s3": s3}[name]

    real_checkpoint = cli.complete_teardown_phase
    checkpointed: list[str] = []

    def checkpoint(root: Any, current: RunState, phase: str) -> RunState:
        if phase == "aws_data_absent":
            assert not s3.present
            assert s3.objects == []
            assert s3.deleted_batches == [1000, 1]
            assert s3.list_calls == 3
        checkpointed.append(phase)
        return real_checkpoint(root, current, phase)

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        cli,
        "_build_teardown_plan",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("a frozen plan must not be rebuilt")
        ),
    )
    monkeypatch.setattr(cli, "client", client)
    monkeypatch.setattr(cli, "_compute_postcondition", lambda *_args: True)
    monkeypatch.setattr(cli, "complete_teardown_phase", checkpoint)
    monkeypatch.setattr(
        cli, "_phase_aws_definitions_cluster_absent", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(cli, "_aws_postcondition", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_phase_docker_outer_absent", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_phase_floci_data_absent", lambda *_args: None)
    monkeypatch.setattr(cli, "_phase_docker_images_absent", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_local_postcondition", lambda *_args, **_kwargs: None)

    result = cli.command_down(
        SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=False)
    )

    assert result["ok"] is True
    assert s3.deleted_batches == [1000, 1]
    assert checkpointed[0] == "aws_data_absent"
    assert checkpointed == list(REACHABLE_TEARDOWN_PHASES[1:])
    assert state_directory_absent(tmp_path)


def test_untagged_bucket_create_gap_is_durable_and_down_retry_is_exact(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    order: list[str] = []
    queues: dict[str, str] = {}
    table_present = False
    target_bucket_present = False
    foreign_bucket_present = True
    delete_crash_pending = True
    captured_state: RunState | None = None

    class Sqs:
        def create_queue(self, **request: Any) -> dict[str, str]:
            name = request["QueueName"]
            url = f"http://floci:4566/000000000000/{name}"
            queues[name] = url
            return {"QueueUrl": url}

        def get_queue_attributes(self, **request: Any) -> dict[str, object]:
            name = request["QueueUrl"].rsplit("/", 1)[-1]
            return {"Attributes": {"QueueArn": f"arn:aws:sqs:us-east-1:000000000000:{name}"}}

        def get_queue_url(self, **request: Any) -> dict[str, str]:
            name = request["QueueName"]
            if name not in queues:
                raise _missing("QueueDoesNotExist", "GetQueueUrl")
            return {"QueueUrl": queues[name]}

        def list_queue_tags(self, **_: object) -> dict[str, dict[str, str]]:
            assert captured_state is not None
            return {"Tags": cli._tags_dict(captured_state)}

        def delete_queue(self, **request: Any) -> None:
            name = request["QueueUrl"].rsplit("/", 1)[-1]
            queues.pop(name)

    class Waiter:
        def wait(self, **_: object) -> None:
            return None

    class Ddb:
        def create_table(self, **_: object) -> None:
            nonlocal table_present
            table_present = True

        def get_waiter(self, _name: str) -> Waiter:
            return Waiter()

        def describe_table(self, **_: object) -> dict[str, dict[str, str]]:
            assert captured_state is not None
            if not table_present:
                raise _missing("ResourceNotFoundException", "DescribeTable")
            return {
                "Table": {
                    "TableArn": (
                        f"arn:aws:dynamodb:us-east-1:000000000000:table/{captured_state.table}"
                    )
                }
            }

        def list_tags_of_resource(self, **_: object) -> dict[str, object]:
            assert captured_state is not None
            return {"Tags": cli.ownership_tags(captured_state)}

        def delete_table(self, **_: object) -> None:
            nonlocal table_present
            table_present = False

    class S3:
        def create_bucket(self, **request: object) -> None:
            nonlocal target_bucket_present
            assert captured_state is not None
            assert request == {"Bucket": captured_state.bucket}
            order.append("create-bucket")
            target_bucket_present = True
            raise InjectedCrash("hard exit after create_bucket")

        def put_bucket_tagging(self, **_: object) -> None:
            raise AssertionError("tagging must not run after the injected hard exit")

        def head_bucket(self, **request: object) -> dict[str, object]:
            assert captured_state is not None
            assert request == {"Bucket": captured_state.bucket}
            if not target_bucket_present:
                raise _missing("NoSuchBucket", "HeadBucket")
            return {}

        def get_bucket_tagging(self, **request: object) -> dict[str, object]:
            assert captured_state is not None
            assert request == {"Bucket": captured_state.bucket}
            if not target_bucket_present:
                raise _missing("NoSuchBucket", "GetBucketTagging")
            raise _missing("NoSuchTagSet", "GetBucketTagging")

        def list_objects_v2(self, **_: object) -> dict[str, object]:
            return {"Contents": [], "IsTruncated": False}

        def delete_bucket(self, **request: object) -> None:
            nonlocal target_bucket_present, delete_crash_pending
            assert captured_state is not None
            assert request == {"Bucket": captured_state.bucket}
            target_bucket_present = False
            if delete_crash_pending:
                delete_crash_pending = False
                raise InjectedCrash("hard exit after intended bucket deletion")

    class Ecs:
        def create_cluster(self, **_: object) -> None:
            raise AssertionError("cluster creation must not follow the injected hard exit")

        def list_task_definitions(self, **_: object) -> dict[str, object]:
            return {"taskDefinitionArns": []}

        def describe_clusters(self, **_: object) -> dict[str, object]:
            return {"clusters": [], "failures": [{"reason": "MISSING"}]}

    clients = {"sqs": Sqs(), "dynamodb": Ddb(), "s3": S3(), "ecs": Ecs()}
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "compose_digest", lambda _root: "a" * 64)
    monkeypatch.setattr(
        cli, "_docker_identity", lambda: ("test", "unix:///tmp/docker.sock", "daemon")
    )
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_compose_image", lambda _socket: cli.FLOCI_IMAGE)
    monkeypatch.setattr(cli, "_ensure_floci_image", lambda: "sha256:" + "a" * 64)
    monkeypatch.setattr(cli, "_compose", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(cli, "_wait_health", lambda: None)

    def preflight(state: RunState) -> None:
        nonlocal captured_state
        captured_state = state
        order.append("preflight-complete")

    real_intent_transition = cli.set_bucket_create_intent

    def intent_transition(root: Any, state: RunState, *, active: bool) -> RunState:
        if active:
            order.append("intent-durable")
        return real_intent_transition(root, state, active=active)

    monkeypatch.setattr(cli, "_assert_aws_targets_absent", preflight)
    monkeypatch.setattr(cli, "set_bucket_create_intent", intent_transition)
    monkeypatch.setattr(cli, "client", lambda name: clients[name])

    with pytest.raises(InjectedCrash, match="after create_bucket"):
        cli.command_up(SimpleNamespace(run_id="ci-s3-gap", acknowledge_docker_socket=True))

    persisted = load_state(tmp_path)
    assert order == ["preflight-complete", "intent-durable", "create-bucket"]
    assert persisted.bucket_create_intent is True
    assert target_bucket_present is True
    assert foreign_bucket_present is True

    monkeypatch.setattr(cli, "_bind_daemon", lambda _state: "unix:///tmp/docker.sock")
    monkeypatch.setattr(cli, "_inspect_labels", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_docker_task_targets", lambda *_args: ())
    monkeypatch.setattr(cli, "_compute_postcondition", lambda *_args: True)
    monkeypatch.setattr(cli, "_local_postcondition", lambda *_args: None)

    def execute(state: RunState, plan: TeardownPlan, phase: str, _socket: str) -> None:
        if phase == "aws_data_absent":
            cli._phase_aws_data_absent(state, plan)
        elif phase == "floci_data_absent":
            cli._remove_floci_data_path(root=tmp_path)

    monkeypatch.setattr(cli, "_execute_teardown_phase", execute)
    down_args = SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=False)
    with pytest.raises(InjectedCrash, match="after intended bucket deletion"):
        cli.command_down(down_args)

    interrupted = load_state(tmp_path)
    assert interrupted.teardown is not None
    assert interrupted.teardown.completed_phases == ("aws_compute_absent",)
    assert target_bucket_present is False
    assert foreign_bucket_present is True

    result = cli.command_down(down_args)
    assert result["ok"] is True
    assert not (tmp_path / ".lab-state").exists()
    assert target_bucket_present is False
    assert foreign_bucket_present is True


def test_successful_provision_clears_bucket_create_intent_after_tagging(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-s3-intent-clear")
    claim_state(tmp_path, state)
    observed: list[str] = []

    class Sqs:
        def create_queue(self, **request: Any) -> dict[str, str]:
            return {"QueueUrl": f"http://floci:4566/{request['QueueName']}"}

        def get_queue_attributes(self, **_: object) -> dict[str, object]:
            return {"Attributes": {"QueueArn": "arn:aws:sqs:us-east-1:000000000000:dlq"}}

    class Waiter:
        def wait(self, **_: object) -> None:
            return None

    class Ddb:
        def create_table(self, **_: object) -> None:
            return None

        def get_waiter(self, _name: str) -> Waiter:
            return Waiter()

    class S3:
        def create_bucket(self, **_: object) -> None:
            assert load_state(tmp_path).bucket_create_intent is True
            observed.append("created")

        def put_bucket_tagging(self, **request: Any) -> None:
            assert request["Tagging"] == {"TagSet": cli.ownership_tags(state)}
            assert load_state(tmp_path).bucket_create_intent is True
            observed.append("tagged")

    class Ecs:
        def create_cluster(self, **_: object) -> None:
            assert load_state(tmp_path).bucket_create_intent is False
            observed.append("cluster")

    clients = {"sqs": Sqs(), "dynamodb": Ddb(), "s3": S3(), "ecs": Ecs()}
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "client", lambda name: clients[name])

    updated, urls = cli._provision(state)

    assert observed == ["created", "tagged", "cluster"]
    assert updated.bucket_create_intent is False
    assert load_state(tmp_path) == updated
    assert set(urls) == {"queue_url", "dlq_url"}


@pytest.mark.parametrize("crash_after", ["update", "delete"])
def test_compute_phase_retries_after_service_mutation_and_converges(
    monkeypatch: pytest.MonkeyPatch, crash_after: str
) -> None:
    state = RunState.create(f"ci-service-{crash_after}")
    cluster_arn = f"arn:aws:ecs:us-east-1:000000000000:cluster/{state.cluster}"
    service_arn = f"arn:aws:ecs:us-east-1:000000000000:service/{state.api_service}"
    base = _teardown_plan(state)
    plan = replace(
        base,
        aws=replace(
            base.aws,
            cluster=NamedArnTarget(state.cluster, cluster_arn),
            services=(
                NamedArnTarget(state.api_service, service_arn),
                NamedArnTarget(state.worker_service),
            ),
        ),
    )
    service_present = True
    desired_count = 1
    injected = False
    calls = {"update": 0, "delete": 0}

    class Ecs:
        def describe_clusters(self, **_: object) -> dict[str, list[dict[str, object]]]:
            return {
                "clusters": [
                    {
                        "clusterName": state.cluster,
                        "clusterArn": cluster_arn,
                        "tags": cli.ownership_tags(state),
                    }
                ]
            }

        def describe_services(self, **request: object) -> dict[str, list[dict[str, object]]]:
            if request["services"] == [state.api_service] and service_present:
                return {
                    "services": [
                        {
                            "serviceName": state.api_service,
                            "serviceArn": service_arn,
                            "status": "ACTIVE",
                            "desiredCount": desired_count,
                            "tags": cli.ownership_tags(state),
                        }
                    ]
                }
            return {"services": []}

        def update_service(self, **request: object) -> None:
            nonlocal desired_count, injected
            assert request == {
                "cluster": state.cluster,
                "service": state.api_service,
                "desiredCount": 0,
            }
            calls["update"] += 1
            desired_count = 0
            if crash_after == "update" and not injected:
                injected = True
                raise InjectedCrash("after service update")

        def delete_service(self, **request: object) -> None:
            nonlocal service_present, injected
            assert request == {
                "cluster": state.cluster,
                "service": state.api_service,
                "force": True,
            }
            calls["delete"] += 1
            service_present = False
            if crash_after == "delete" and not injected:
                injected = True
                raise InjectedCrash("after service delete")

        def list_services(self, **_: object) -> dict[str, list[str]]:
            return {"serviceArns": [service_arn] if service_present else []}

        def list_tasks(self, **_: object) -> dict[str, list[str]]:
            return {"taskArns": []}

    ecs = Ecs()
    monkeypatch.setattr(cli, "client", lambda name: ecs if name == "ecs" else object())
    monkeypatch.setattr(cli, "_remove_frozen_task_containers", lambda *_args: None)
    monkeypatch.setattr(cli, "_task_container_postcondition", lambda *_args: True)

    with pytest.raises(InjectedCrash, match=f"after service {crash_after}"):
        cli._phase_aws_compute_absent(state, plan)

    assert desired_count == 0
    assert service_present is (crash_after == "update")

    cli._phase_aws_compute_absent(state, plan)

    assert service_present is False
    assert cli._compute_postcondition(ecs, state, plan) is True
    assert calls["update"] == (2 if crash_after == "update" else 1)
    assert calls["delete"] == 1


@pytest.mark.parametrize(
    "crash_after",
    ["queue_delete", "table_delete", "bucket_object_drain", "bucket_delete"],
)
def test_data_phase_retries_after_each_resource_mutation_and_converges(
    monkeypatch: pytest.MonkeyPatch, crash_after: str
) -> None:
    state = RunState.create(f"ci-data-{crash_after.replace('_', '-')}")
    queue_url = f"http://floci:4566/000000000000/{state.queue}"
    table_arn = f"arn:aws:dynamodb:us-east-1:000000000000:table/{state.table}"
    queue_present = crash_after == "queue_delete"
    table_present = crash_after == "table_delete"
    bucket_present = crash_after.startswith("bucket_")
    objects = ["exports/tenant-a/result.json"] if bucket_present else []
    base = _teardown_plan(state)
    plan = replace(
        base,
        aws=replace(
            base.aws,
            queues=(
                QueueTarget(state.queue, queue_url if queue_present else ""),
                QueueTarget(state.dlq),
            ),
            table=NamedArnTarget(state.table, table_arn if table_present else ""),
            bucket=BucketTarget(
                state.bucket,
                bucket_present,
                "drain-all-unversioned" if bucket_present else "none",
            ),
        ),
    )
    injected = False
    calls = {"queue_delete": 0, "table_delete": 0, "bucket_object_drain": 0, "bucket_delete": 0}

    def maybe_crash(boundary: str) -> None:
        nonlocal injected
        if crash_after == boundary and not injected:
            injected = True
            raise InjectedCrash(f"after {boundary}")

    class Sqs:
        def get_queue_url(self, **request: object) -> dict[str, str]:
            if request["QueueName"] == state.queue and queue_present:
                return {"QueueUrl": queue_url}
            raise _missing("QueueDoesNotExist", "GetQueueUrl")

        def list_queue_tags(self, **_: object) -> dict[str, dict[str, str]]:
            return {"Tags": cli._tags_dict(state)}

        def delete_queue(self, **request: object) -> None:
            nonlocal queue_present
            assert request == {"QueueUrl": queue_url}
            calls["queue_delete"] += 1
            queue_present = False
            maybe_crash("queue_delete")

    class Ddb:
        def describe_table(self, **_: object) -> dict[str, dict[str, str]]:
            if not table_present:
                raise _missing("ResourceNotFoundException", "DescribeTable")
            return {"Table": {"TableArn": table_arn}}

        def list_tags_of_resource(self, **request: object) -> dict[str, object]:
            assert request == {"ResourceArn": table_arn}
            return {"Tags": cli.ownership_tags(state)}

        def delete_table(self, **request: object) -> None:
            nonlocal table_present
            assert request == {"TableName": state.table}
            calls["table_delete"] += 1
            table_present = False
            maybe_crash("table_delete")

    class S3:
        def head_bucket(self, **_: object) -> dict[str, object]:
            if not bucket_present:
                raise _missing("NoSuchBucket", "HeadBucket")
            return {}

        def get_bucket_tagging(self, **_: object) -> dict[str, object]:
            return {"TagSet": cli.ownership_tags(state)}

        def list_objects_v2(self, **_: object) -> dict[str, object]:
            return {"Contents": [{"Key": key} for key in objects]}

        def delete_objects(self, **request: Any) -> dict[str, object]:
            requested = [item["Key"] for item in request["Delete"]["Objects"]]
            assert requested == objects
            calls["bucket_object_drain"] += 1
            objects.clear()
            maybe_crash("bucket_object_drain")
            return {"Deleted": [{"Key": key} for key in requested]}

        def delete_bucket(self, **request: object) -> None:
            nonlocal bucket_present
            assert request == {"Bucket": state.bucket}
            assert objects == []
            calls["bucket_delete"] += 1
            bucket_present = False
            maybe_crash("bucket_delete")

    clients = {"sqs": Sqs(), "dynamodb": Ddb(), "s3": S3(), "ecs": object()}
    monkeypatch.setattr(cli, "client", lambda name: clients[name])
    monkeypatch.setattr(cli, "_compute_postcondition", lambda *_args: True)

    with pytest.raises(InjectedCrash, match=f"after {crash_after}"):
        cli._phase_aws_data_absent(state, plan)

    cli._phase_aws_data_absent(state, plan)

    assert cli._data_postcondition(state, plan) is True
    assert queue_present is False
    assert table_present is False
    assert bucket_present is False
    assert objects == []
    assert calls[crash_after] == 1
    if crash_after.startswith("bucket_"):
        assert calls["bucket_object_drain"] == 1
        assert calls["bucket_delete"] == 1


@pytest.mark.parametrize("crash_after", ["deregister", "definition_delete", "cluster_delete"])
def test_definition_cluster_phase_retries_after_each_mutation_and_converges(
    monkeypatch: pytest.MonkeyPatch, crash_after: str
) -> None:
    state = RunState.create(f"ci-definitions-{crash_after.replace('_', '-')}")
    definition_arn = f"arn:aws:ecs:us-east-1:000000000000:task-definition/{state.api_family}:1"
    cluster_arn = f"arn:aws:ecs:us-east-1:000000000000:cluster/{state.cluster}"
    base = _teardown_plan(state)
    plan = replace(
        base,
        aws=replace(
            base.aws,
            cluster=NamedArnTarget(state.cluster, cluster_arn),
            task_definition_arns=(definition_arn,),
        ),
    )
    active = True
    inactive = False
    cluster_present = True
    injected = False
    calls = {"deregister": 0, "definition_delete": 0, "cluster_delete": 0}

    def maybe_crash(boundary: str) -> None:
        nonlocal injected
        if crash_after == boundary and not injected:
            injected = True
            raise InjectedCrash(f"after {boundary}")

    class Ecs:
        def list_task_definitions(self, **request: object) -> dict[str, list[str]]:
            matches_family = request["familyPrefix"] == state.api_family
            if request["status"] == "ACTIVE" and matches_family and active:
                return {"taskDefinitionArns": [definition_arn]}
            if request["status"] == "INACTIVE" and matches_family and inactive:
                return {"taskDefinitionArns": [definition_arn]}
            return {"taskDefinitionArns": []}

        def describe_task_definition(self, **_: object) -> dict[str, object]:
            return {"taskDefinition": {"status": "ACTIVE" if active else "INACTIVE"}}

        def deregister_task_definition(self, **request: object) -> None:
            nonlocal active, inactive
            assert request == {"taskDefinition": definition_arn}
            calls["deregister"] += 1
            active = False
            inactive = True
            maybe_crash("deregister")

        def delete_task_definitions(self, **request: object) -> dict[str, list[object]]:
            nonlocal active, inactive
            assert request == {"taskDefinitions": [definition_arn]}
            calls["definition_delete"] += 1
            active = False
            inactive = False
            maybe_crash("definition_delete")
            return {"failures": []}

        def describe_clusters(self, **_: object) -> dict[str, list[dict[str, object]]]:
            if not cluster_present:
                return {"clusters": []}
            return {
                "clusters": [
                    {
                        "clusterName": state.cluster,
                        "clusterArn": cluster_arn,
                        "tags": cli.ownership_tags(state),
                    }
                ]
            }

        def delete_cluster(self, **request: object) -> None:
            nonlocal cluster_present
            assert request == {"cluster": state.cluster}
            calls["cluster_delete"] += 1
            cluster_present = False
            maybe_crash("cluster_delete")

    ecs = Ecs()
    monkeypatch.setattr(cli, "client", lambda name: ecs if name == "ecs" else object())
    monkeypatch.setattr(cli, "_compute_postcondition", lambda *_args: True)
    monkeypatch.setattr(cli, "_data_postcondition", lambda *_args: True)
    monkeypatch.setattr(cli, "_task_definition_artifact", lambda *_args: ("api", "", "", ""))

    with pytest.raises(InjectedCrash, match=f"after {crash_after}"):
        cli._phase_aws_definitions_cluster_absent(state, plan)

    cli._phase_aws_definitions_cluster_absent(state, plan)
    cli._aws_postcondition(state, plan)

    assert active is False
    assert inactive is False
    assert cluster_present is False
    assert calls == {"deregister": 1, "definition_delete": 1, "cluster_delete": 1}


def test_docker_outer_phase_retries_after_exact_removal_and_converges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-outer-removal-crash")
    plan = _teardown_plan(state)
    present = {
        ("container", plan.docker.outer_container),
        ("network", plan.docker.network),
    }
    injected = False
    docker_calls: list[tuple[str, ...]] = []
    aws_checks = 0

    def run(args: list[str], **_: object) -> str:
        nonlocal injected
        command = tuple(args)
        docker_calls.append(command)
        if command == ("docker", "container", "rm", "-f", plan.docker.outer_container):
            present.discard(("container", plan.docker.outer_container))
        elif command == ("docker", "network", "rm", plan.docker.network):
            present.discard(("network", plan.docker.network))
        else:
            raise AssertionError(f"unexpected Docker mutation: {command}")
        if not injected and command[1] == "container":
            injected = True
            raise InjectedCrash("after exact outer-container removal")
        return ""

    def aws_postcondition(*_: object) -> None:
        nonlocal aws_checks
        aws_checks += 1

    monkeypatch.setattr(
        cli, "_exact_docker_object_exists", lambda kind, name: (kind, name) in present
    )
    monkeypatch.setattr(cli, "_inspect_labels", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_remove_frozen_task_containers", lambda *_args: None)
    monkeypatch.setattr(cli, "_task_container_postcondition", lambda *_args: True)
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args: None)
    monkeypatch.setattr(cli, "_aws_postcondition", aws_postcondition)
    monkeypatch.setattr(cli, "_run", run)
    monkeypatch.setattr(cli, "compose_digest", lambda _root: plan.compose_sha256)

    with pytest.raises(InjectedCrash, match="after exact outer-container removal"):
        cli._phase_docker_outer_absent(state, plan, "unix:///test/docker.sock")

    assert present == {("network", plan.docker.network)}
    cli._phase_docker_outer_absent(state, plan, "unix:///test/docker.sock")

    assert cli._docker_outer_postcondition(state, plan) is True
    assert docker_calls == [
        ("docker", "container", "rm", "-f", plan.docker.outer_container),
        ("docker", "network", "rm", plan.docker.network),
    ]
    assert aws_checks == 1


def test_outer_phase_never_targets_foreign_compose_project_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-foreign-compose-member")
    plan = _teardown_plan(state)
    foreign = "foreign-container-with-compose-project-label"
    present = {
        ("container", plan.docker.outer_container),
        ("container", foreign),
        ("network", plan.docker.network),
    }
    docker_calls: list[tuple[str, ...]] = []

    def exists(kind: str, name: str) -> bool:
        return (kind, name) in present

    def run(args: list[str], **_: object) -> str:
        command = tuple(args)
        docker_calls.append(command)
        if command == ("docker", "container", "rm", "-f", plan.docker.outer_container):
            present.remove(("container", plan.docker.outer_container))
            return ""
        if command == ("docker", "network", "rm", plan.docker.network):
            raise cli.LabError("network has active endpoints")
        raise AssertionError(f"foreign Compose member was targeted: {command}")

    monkeypatch.setattr(cli, "_exact_docker_object_exists", exists)
    monkeypatch.setattr(cli, "_inspect_labels", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_remove_frozen_task_containers", lambda *_args: None)
    monkeypatch.setattr(cli, "_aws_postcondition", lambda *_args: None)
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "compose_digest", lambda _root: plan.compose_sha256)
    monkeypatch.setattr(cli, "_run", run)

    with pytest.raises(cli.LabError, match="active endpoints"):
        cli._phase_docker_outer_absent(state, plan, "unix:///test/docker.sock")

    assert ("container", foreign) in present
    assert all(foreign not in command for command in docker_calls)
    assert docker_calls == [
        ("docker", "container", "rm", "-f", plan.docker.outer_container),
        ("docker", "network", "rm", plan.docker.network),
    ]


def test_floci_data_phase_retries_after_directory_removal_and_converges(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-floci-data-crash")
    claim_state(tmp_path, state)
    plan = _teardown_plan(state)
    data = cli._floci_data_path(root=tmp_path, create=True)
    (data / "persisted-emulator-state").write_text("owned", encoding="utf-8")
    real_rmtree = cli.shutil.rmtree
    injected = False
    removals = 0

    def remove_then_crash(path: Any) -> None:
        nonlocal injected, removals
        real_rmtree(path)
        removals += 1
        if not injected:
            injected = True
            raise InjectedCrash("after Floci data removal")

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_docker_outer_postcondition", lambda *_args: True)
    monkeypatch.setattr(cli.shutil, "rmtree", remove_then_crash)

    with pytest.raises(InjectedCrash, match="after Floci data removal"):
        cli._phase_floci_data_absent(state, plan)

    assert not data.exists()
    cli._phase_floci_data_absent(state, plan)

    assert not data.exists()
    assert removals == 1


def test_docker_image_phase_retries_after_first_removal_and_converges(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-image-remove-crash")
    claim_state(tmp_path, state)
    state = _record_complete_deployment(
        tmp_path,
        state,
        digest="a" * 64,
        operation_id="b" * 32,
        image_id="sha256:" + "c" * 64,
        revision=1,
    )
    plan = _teardown_plan(state)
    present = {target.ref for target in plan.docker.images}
    removed: list[str] = []
    injected = False

    def run(args: list[str], **_: object) -> str:
        nonlocal injected
        assert args[:3] == ["docker", "image", "rm"]
        ref = args[3]
        present.remove(ref)
        removed.append(ref)
        if not injected:
            injected = True
            raise InjectedCrash("after first image removal")
        return ""

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_docker_outer_postcondition", lambda *_args: True)
    monkeypatch.setattr(cli, "_validate_image_target", lambda *_args: None)
    monkeypatch.setattr(cli, "_image_ref_exists", lambda ref: ref in present)
    monkeypatch.setattr(cli, "_run", run)

    with pytest.raises(InjectedCrash, match="after first image removal"):
        cli._phase_docker_images_absent(state, plan)

    assert len(present) == 1
    cli._phase_docker_images_absent(state, plan)

    assert present == set()
    assert sorted(removed) == sorted(target.ref for target in plan.docker.images)


def _fully_checkpointed_teardown(tmp_path: Any, run_id: str) -> RunState:
    state = RunState.create(run_id)
    claim_state(tmp_path, state)
    state = install_teardown_plan(tmp_path, state, _teardown_plan(state))
    assert state.teardown is not None
    for phase in state.teardown.plan.phases:
        state = complete_teardown_phase(tmp_path, state, phase)
    return state


def test_fully_checkpointed_down_removes_safe_atomic_orphan_and_is_reusable(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _fully_checkpointed_teardown(tmp_path, "ci-safe-orphan")
    orphan = tmp_path / ".lab-state" / f".run.{'d' * 32}.tmp"
    orphan.write_text("durable-but-uncommitted", encoding="utf-8")
    orphan.chmod(0o600)

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args: None)
    monkeypatch.setattr(cli, "_docker_outer_postcondition", lambda *_args: True)
    monkeypatch.setattr(cli, "_image_ref_exists", lambda _ref: False)

    result = cli.command_down(
        SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=False)
    )

    assert result["ok"] is True
    assert result["cleanup"]["completed_phases"] == list(state.teardown.plan.phases)
    assert not (tmp_path / ".lab-state").exists()
    assert state_directory_absent(tmp_path)

    replacement = RunState.create("ci-safe-orphan-reused")
    claim_state(tmp_path, replacement)
    assert load_state(tmp_path) == replacement


def test_fully_checkpointed_down_fails_closed_on_unknown_state_entry(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _fully_checkpointed_teardown(tmp_path, "ci-unsafe-orphan")
    unknown = tmp_path / ".lab-state" / "unrecognized-runtime-entry"
    unknown.write_text("preserve me", encoding="utf-8")
    unknown.chmod(0o600)

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_bind_daemon", lambda _: "unix:///test/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda *_args: None)
    monkeypatch.setattr(cli, "_docker_outer_postcondition", lambda *_args: True)
    monkeypatch.setattr(cli, "_image_ref_exists", lambda _ref: False)

    with pytest.raises(cli.SafetyError, match="unexpected runtime artifact"):
        cli.command_down(SimpleNamespace(recover_stale=False, teardown_unreachable_emulator=False))

    assert unknown.read_text(encoding="utf-8") == "preserve me"
    assert load_state(tmp_path) == state
