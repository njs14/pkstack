from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from pk_stack_lab import config
from pk_stack_lab.config import (
    DISCARD_TEARDOWN_PHASES,
    REACHABLE_TEARDOWN_PHASES,
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
    complete_teardown_phase,
    install_teardown_plan,
    load_state,
    remove_state_manifest,
    save_state,
    teardown_plan_hash,
    transition_teardown_to_discard,
)


def _events(
    state: RunState,
    *,
    operation_id: str = "a" * 32,
    digest: str = "b" * 64,
    image_id: str = "sha256:" + "c" * 64,
    revision: int = 1,
) -> tuple[ArtifactEvent, ...]:
    api_ref = f"{state.prefix}-api:{digest[:24]}"
    worker_ref = f"{state.prefix}-worker:{digest[:24]}"
    return (
        ArtifactEvent(1, "image_planned", operation_id, "api", digest, api_ref),
        ArtifactEvent(2, "image_planned", operation_id, "worker", digest, worker_ref),
        ArtifactEvent(3, "image_observed", operation_id, "api", digest, api_ref, image_id=image_id),
        ArtifactEvent(
            4,
            "image_observed",
            operation_id,
            "worker",
            digest,
            worker_ref,
            image_id=image_id,
        ),
        ArtifactEvent(
            5,
            "task_definition_planned",
            operation_id,
            "api",
            digest,
            api_ref,
            family=state.api_family,
        ),
        ArtifactEvent(
            6,
            "task_definition_planned",
            operation_id,
            "worker",
            digest,
            worker_ref,
            family=state.worker_family,
        ),
        ArtifactEvent(
            7,
            "task_definition_observed",
            operation_id,
            "api",
            digest,
            api_ref,
            image_id=image_id,
            family=state.api_family,
            task_definition_arn=(
                f"arn:aws:ecs:us-east-1:000000000000:task-definition/{state.api_family}:{revision}"
            ),
        ),
        ArtifactEvent(
            8,
            "task_definition_observed",
            operation_id,
            "worker",
            digest,
            worker_ref,
            image_id=image_id,
            family=state.worker_family,
            task_definition_arn=(
                "arn:aws:ecs:us-east-1:000000000000:task-definition/"
                f"{state.worker_family}:{revision}"
            ),
        ),
    )


def _plan(state: RunState, *, aws_mode: str = "reachable") -> TeardownPlan:
    observed_arns = tuple(
        sorted(
            event.task_definition_arn
            for event in state.artifact_ledger
            if event.kind == "task_definition_observed"
        )
    )
    images: dict[tuple[str, str], str] = {}
    for event in state.artifact_ledger:
        key = (event.image_ref, event.source_digest)
        if event.kind == "image_planned":
            images.setdefault(key, "")
        elif event.kind == "image_observed":
            images[key] = event.image_id
    phases = (
        REACHABLE_TEARDOWN_PHASES if aws_mode == "reachable" else config.DISCARD_TEARDOWN_PHASES
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
            services=(NamedArnTarget(state.api_service), NamedArnTarget(state.worker_service)),
            queues=(QueueTarget(state.queue), QueueTarget(state.dlq)),
            table=NamedArnTarget(state.table),
            bucket=BucketTarget(state.bucket, True),
            task_definition_families=(state.api_family, state.worker_family),
            task_definition_arns=observed_arns,
        ),
        docker=DockerTeardownTargets(
            outer_container="pk-stack-lab-floci",
            network=config.NETWORK,
            verifier=f"{state.prefix}-verifier",
            images=tuple(
                ImageTarget(ref=ref, source_digest=digest, image_id=image_id)
                for (ref, digest), image_id in sorted(images.items())
            ),
        ),
        phases=phases,
    )


def test_schema_v2_nested_state_round_trips_exactly(tmp_path: Path) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    state = append_artifact_events(tmp_path, state, *_events(state))
    state = install_teardown_plan(tmp_path, state, _plan(state))

    assert load_state(tmp_path) == state
    raw = json.loads((tmp_path / ".lab-state" / "run.json").read_text(encoding="utf-8"))
    assert raw["schema_version"] == 2
    assert len(raw["artifact_ledger"]) == 8
    assert raw["teardown"]["plan_sha256"] == state.teardown.plan_sha256


def test_run_and_teardown_plan_require_the_same_compose_digest(tmp_path: Path) -> None:
    state = RunState.create("ci-compose-binding", compose_sha256="a" * 64)
    save_state(tmp_path, state)

    with pytest.raises(SafetyError, match="noncanonical state write"):
        save_state(tmp_path, replace(state, compose_sha256="not-a-digest"))
    with pytest.raises(SafetyError, match="claimed Compose definition"):
        install_teardown_plan(
            tmp_path,
            state,
            replace(_plan(state), compose_sha256="b" * 64),
        )


def test_create_defaults_are_valid_deterministic_claim_and_docker_identities() -> None:
    first = RunState.create("ci-default-identity")
    second = RunState.create("ci-default-identity")

    assert first == second
    assert first.claim_id == "0" * 32
    assert first.docker_context == "pk-stack-test"
    assert first.docker_socket == "unix:///tmp/pk-stack-lab-test.sock"
    assert first.docker_daemon_id == "pk-stack-test-daemon"
    assert first.compose_sha256 == "0" * 64
    assert not any(
        (
            first.source_digest,
            first.api_image_id,
            first.worker_image_id,
            first.api_task_definition_arn,
            first.worker_task_definition_arn,
        )
    )


@pytest.mark.parametrize(
    "claim_id",
    ["", "a" * 31, "a" * 33, "A" * 32, "g" * 32, "a" * 31 + "-"],
)
def test_state_rejects_noncanonical_claim_identity(claim_id: str) -> None:
    with pytest.raises(SafetyError, match="claim ID"):
        RunState.create("ci-bad-claim", claim_id=claim_id)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("docker_context", ""),
        ("docker_context", "-option"),
        ("docker_context", "unsafe context"),
        ("docker_context", "a" * 129),
        ("docker_daemon_id", ""),
        ("docker_daemon_id", "unsafe\nidentity"),
        ("docker_daemon_id", "a" * 257),
        ("docker_socket", ""),
        ("docker_socket", "tcp://127.0.0.1:2375"),
        ("docker_socket", "unix://relative/docker.sock"),
        ("docker_socket", "unix:////tmp/docker.sock"),
        ("docker_socket", "unix:///tmp/../docker.sock"),
        ("docker_socket", "unix:///" + "a" * 4090),
    ],
)
def test_state_rejects_incomplete_or_unsafe_docker_identity(field: str, value: str) -> None:
    with pytest.raises(SafetyError, match="Docker"):
        RunState.create("ci-bad-docker", **{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_digest", "a" * 64),
        ("api_image_id", "sha256:" + "b" * 64),
        ("worker_image_id", "sha256:" + "b" * 64),
        (
            "api_task_definition_arn",
            ("arn:aws:ecs:us-east-1:000000000000:task-definition/pklab-ci-partial-pointer-api:1"),
        ),
        (
            "worker_task_definition_arn",
            (
                "arn:aws:ecs:us-east-1:000000000000:task-definition/"
                "pklab-ci-partial-pointer-worker:1"
            ),
        ),
    ],
)
def test_active_deployment_pointer_rejects_every_partial_shape(field: str, value: str) -> None:
    with pytest.raises(SafetyError, match="entirely empty or complete"):
        RunState.create("ci-partial-pointer", **{field: value})


def test_active_deployment_round_trips_only_when_one_operation_matches_exactly(
    tmp_path: Path,
) -> None:
    state = RunState.create("ci-active-pointer")
    save_state(tmp_path, state)
    events = _events(state)
    state = append_artifact_events(tmp_path, state, *events)

    state = activate_deployment(
        tmp_path,
        state,
        source_digest=events[0].source_digest,
        image_id=events[2].image_id,
        api_task_definition_arn=events[6].task_definition_arn,
        worker_task_definition_arn=events[7].task_definition_arn,
    )

    assert load_state(tmp_path) == state


def test_active_deployment_rejects_cross_wired_definition_operations(tmp_path: Path) -> None:
    state = RunState.create("ci-cross-wired-arns")
    save_state(tmp_path, state)
    first = _events(state, operation_id="a" * 32, revision=1)
    state = append_artifact_events(tmp_path, state, *first)
    second = tuple(
        replace(event, seq=event.seq + len(state.artifact_ledger))
        for event in _events(state, operation_id="d" * 32, revision=2)
    )
    state = append_artifact_events(tmp_path, state, *second)

    with pytest.raises(SafetyError, match="exactly one complete artifact operation"):
        activate_deployment(
            tmp_path,
            state,
            source_digest=first[0].source_digest,
            image_id=first[2].image_id,
            api_task_definition_arn=first[6].task_definition_arn,
            worker_task_definition_arn=second[7].task_definition_arn,
        )


def test_active_deployment_rejects_digest_and_image_cross_wiring(tmp_path: Path) -> None:
    state = RunState.create("ci-cross-wired-image")
    save_state(tmp_path, state)
    first = _events(state, operation_id="a" * 32, revision=1)
    state = append_artifact_events(tmp_path, state, *first)
    second = tuple(
        replace(event, seq=event.seq + len(state.artifact_ledger))
        for event in _events(
            state,
            operation_id="d" * 32,
            digest="e" * 64,
            image_id="sha256:" + "f" * 64,
            revision=2,
        )
    )
    state = append_artifact_events(tmp_path, state, *second)

    with pytest.raises(SafetyError, match="exactly one complete artifact operation"):
        RunState.create(
            state.run_id,
            source_digest=first[0].source_digest,
            api_image_id=second[2].image_id,
            worker_image_id=second[2].image_id,
            api_task_definition_arn=first[6].task_definition_arn,
            worker_task_definition_arn=first[7].task_definition_arn,
            artifact_ledger=state.artifact_ledger,
        )


def test_active_deployment_rejects_duplicate_event_in_matching_operation(tmp_path: Path) -> None:
    state = RunState.create("ci-duplicate-active-event")
    save_state(tmp_path, state)
    events = _events(state)
    state = append_artifact_events(tmp_path, state, *events)
    state = append_artifact_events(tmp_path, state, replace(events[0], seq=9))

    with pytest.raises(SafetyError, match="exactly one complete artifact operation"):
        activate_deployment(
            tmp_path,
            state,
            source_digest=events[0].source_digest,
            image_id=events[2].image_id,
            api_task_definition_arn=events[6].task_definition_arn,
            worker_task_definition_arn=events[7].task_definition_arn,
        )


def test_state_operations_reject_world_writable_state_directory(tmp_path: Path) -> None:
    state = RunState.create("ci-state-mode")
    save_state(tmp_path, state)
    directory = tmp_path / ".lab-state"
    directory.chmod(0o777)
    try:
        with pytest.raises(SafetyError, match="owner-only direct directory"):
            load_state(tmp_path)
        with pytest.raises(SafetyError, match="owner-only direct directory"):
            save_state(tmp_path, state)
        with pytest.raises(SafetyError, match="owner-only direct directory"):
            remove_state_manifest(tmp_path)
    finally:
        directory.chmod(0o700)


def test_decoder_rejects_v1_and_nested_field_smuggling(tmp_path: Path) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    path = tmp_path / ".lab-state" / "run.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("schema_version")
    raw.pop("artifact_ledger")
    raw.pop("teardown")
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SafetyError):
        load_state(tmp_path)

    save_state(tmp_path, state)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["artifact_ledger"] = [_events(state)[0].to_dict() | {"smuggled": "value"}]
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(SafetyError):
        load_state(tmp_path)


def test_artifact_ledger_requires_contiguous_planned_observed_history(tmp_path: Path) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    plan, observed = _events(state)[:3:2]
    with pytest.raises(SafetyError, match="sequence"):
        append_artifact_events(tmp_path, state, replace(plan, seq=2))
    with pytest.raises(SafetyError, match="preceding image plan"):
        append_artifact_events(tmp_path, state, replace(observed, seq=1))

    state = append_artifact_events(tmp_path, state, plan, replace(observed, seq=2))
    assert [event.kind for event in state.artifact_ledger] == [
        "image_planned",
        "image_observed",
    ]


def test_teardown_plan_is_hash_bound_and_phases_are_an_ordered_prefix(tmp_path: Path) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    state = append_artifact_events(tmp_path, state, *_events(state))
    plan = _plan(state)
    state = install_teardown_plan(tmp_path, state, plan)

    with pytest.raises(SafetyError, match="out of order"):
        complete_teardown_phase(tmp_path, state, plan.phases[1])
    state = complete_teardown_phase(tmp_path, state, plan.phases[0])
    assert state.teardown is not None
    assert state.teardown.completed_phases == plan.phases[:1]
    assert complete_teardown_phase(tmp_path, state, plan.phases[0]) == state

    tampered = replace(state, teardown=replace(state.teardown, plan_sha256="0" * 64))
    with pytest.raises(SafetyError, match="noncanonical"):
        save_state(tmp_path, tampered)


def test_legacy_schema_v2_teardown_can_transition_and_resume_strictly(tmp_path: Path) -> None:
    state = RunState.create("ci-legacy-switch")
    save_state(tmp_path, state)
    state = append_artifact_events(tmp_path, state, *_events(state))
    state = install_teardown_plan(tmp_path, state, _plan(state))
    state = complete_teardown_phase(tmp_path, state, REACHABLE_TEARDOWN_PHASES[0])

    path = tmp_path / ".lab-state" / "run.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["schema_version"] == 2
    assert isinstance(raw["teardown"], dict)
    assert raw["teardown"].pop("transition") is None
    path.write_text(json.dumps(raw), encoding="utf-8")

    legacy = load_state(tmp_path)
    assert legacy == state
    transitioned = transition_teardown_to_discard(tmp_path, legacy)
    resumed = complete_teardown_phase(tmp_path, transitioned, DISCARD_TEARDOWN_PHASES[0])
    assert load_state(tmp_path) == resumed
    assert resumed.teardown is not None
    assert resumed.teardown.completed_phases == DISCARD_TEARDOWN_PHASES[:1]
    assert resumed.teardown.transition is not None
    assert resumed.teardown.transition.from_completed_phases == (REACHABLE_TEARDOWN_PHASES[0],)

    smuggled = resumed.to_dict()
    assert isinstance(smuggled["teardown"], dict)
    smuggled["teardown"]["unexpected"] = True
    with pytest.raises(SafetyError, match="invalid run identifier") as rejected:
        config._canonical_state(smuggled)
    assert isinstance(rejected.value.__cause__, SafetyError)
    assert "canonical fields" in str(rejected.value.__cause__)


@pytest.mark.parametrize("completed_count", range(len(REACHABLE_TEARDOWN_PHASES) + 1))
def test_reachable_to_discard_transition_preserves_plan_and_maps_completed_prefix(
    completed_count: int, tmp_path: Path
) -> None:
    state = RunState.create(f"ci-switch-{completed_count}")
    save_state(tmp_path, state)
    state = append_artifact_events(tmp_path, state, *_events(state))
    reachable = _plan(state)
    state = install_teardown_plan(tmp_path, state, reachable)
    for phase in reachable.phases[:completed_count]:
        state = complete_teardown_phase(tmp_path, state, phase)

    transitioned = transition_teardown_to_discard(tmp_path, state)

    assert transitioned.teardown is not None
    teardown = transitioned.teardown
    assert teardown.plan == replace(
        reachable,
        aws_mode="discard-unreachable",
        phases=DISCARD_TEARDOWN_PHASES,
    )
    assert teardown.plan.aws == reachable.aws
    assert teardown.plan.docker == reachable.docker
    assert teardown.plan.claim_id == reachable.claim_id
    assert teardown.plan.compose_sha256 == reachable.compose_sha256
    assert teardown.plan.ledger_sha256 == reachable.ledger_sha256
    assert teardown.plan_sha256 == teardown_plan_hash(teardown.plan)
    assert teardown.completed_phases == tuple(
        phase for phase in reachable.phases[:completed_count] if phase in DISCARD_TEARDOWN_PHASES
    )
    assert teardown.transition is not None
    assert teardown.transition.from_aws_mode == "reachable"
    assert teardown.transition.from_plan_sha256 == teardown_plan_hash(reachable)
    assert teardown.transition.from_completed_phases == reachable.phases[:completed_count]
    assert teardown.transition.reason == "floci-unreachable-control-plane-discard"
    assert load_state(tmp_path) == transitioned


def test_teardown_transition_rejects_wrong_source_mode_and_hash_tampering(tmp_path: Path) -> None:
    state = RunState.create("ci-switch-invalid")
    save_state(tmp_path, state)
    discard = _plan(state, aws_mode="discard-unreachable")
    state = install_teardown_plan(tmp_path, state, discard)
    with pytest.raises(SafetyError, match="only a frozen reachable"):
        transition_teardown_to_discard(tmp_path, state)

    remove_state_manifest(tmp_path)
    reachable = _plan(state, aws_mode="reachable")
    state = replace(state, teardown=None)
    save_state(tmp_path, state)
    state = install_teardown_plan(tmp_path, state, reachable)
    transitioned = transition_teardown_to_discard(tmp_path, state)
    assert transitioned.teardown is not None
    assert transitioned.teardown.transition is not None
    tampered = replace(
        transitioned,
        teardown=replace(
            transitioned.teardown,
            transition=replace(
                transitioned.teardown.transition,
                from_plan_sha256="f" * 64,
            ),
        ),
    )
    with pytest.raises(SafetyError, match="noncanonical"):
        save_state(tmp_path, tampered)

    wrong_prefix = replace(
        transitioned,
        teardown=replace(
            transitioned.teardown,
            transition=replace(
                transitioned.teardown.transition,
                from_completed_phases=(REACHABLE_TEARDOWN_PHASES[1],),
            ),
        ),
    )
    with pytest.raises(SafetyError, match="noncanonical"):
        save_state(tmp_path, wrong_prefix)


def test_teardown_freezes_artifact_history(tmp_path: Path) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    state = append_artifact_events(tmp_path, state, *_events(state))
    state = install_teardown_plan(tmp_path, state, _plan(state))
    extra = replace(_events(state)[0], seq=len(state.artifact_ledger) + 1)
    with pytest.raises(SafetyError, match="frozen"):
        append_artifact_events(tmp_path, state, extra)


def test_atomic_append_failure_retains_prior_complete_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    before = (tmp_path / ".lab-state" / "run.json").read_bytes()

    def fail_replace(*args: object, **kwargs: object) -> None:
        raise OSError("injected hard boundary")

    monkeypatch.setattr(config.os, "replace", fail_replace)
    with pytest.raises(OSError, match="hard boundary"):
        append_artifact_events(tmp_path, state, _events(state)[0])
    assert (tmp_path / ".lab-state" / "run.json").read_bytes() == before


def test_next_transition_and_terminal_unlink_remove_safe_sigkill_temporary(
    tmp_path: Path,
) -> None:
    state = RunState.create("ci-orphan")
    save_state(tmp_path, state)
    state_dir = tmp_path / ".lab-state"
    first = state_dir / f".run.{'a' * 32}.tmp"
    first.write_text("durable but not replaced", encoding="utf-8")
    first.chmod(0o600)

    save_state(tmp_path, state)

    assert not first.exists()
    second = state_dir / f".run.{'b' * 32}.tmp"
    second.write_text("durable but not replaced", encoding="utf-8")
    second.chmod(0o600)
    remove_state_manifest(tmp_path)
    assert not second.exists()
    assert list(state_dir.iterdir()) == []


@pytest.mark.parametrize("kind", ["unknown", "symlink", "wrong-mode", "multiply-linked"])
def test_state_transition_preserves_and_rejects_unsafe_or_unknown_temporary(
    tmp_path: Path, kind: str
) -> None:
    state = RunState.create("ci-unsafe-temp")
    save_state(tmp_path, state)
    state_dir = tmp_path / ".lab-state"
    name = "unexpected" if kind == "unknown" else f".run.{'c' * 32}.tmp"
    candidate = state_dir / name
    if kind == "symlink":
        target = tmp_path / "external"
        target.write_text("external", encoding="utf-8")
        candidate.symlink_to(target)
    else:
        candidate.write_text("preserve", encoding="utf-8")
        candidate.chmod(0o644 if kind == "wrong-mode" else 0o600)
        if kind == "multiply-linked":
            os.link(candidate, tmp_path / "second-link")

    with pytest.raises(SafetyError, match="unexpected|owner-only"):
        save_state(tmp_path, state)

    assert candidate.exists() or candidate.is_symlink()
    assert load_state(tmp_path) == state


def test_plan_must_cover_every_planned_image_and_observed_definition(tmp_path: Path) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    state = append_artifact_events(tmp_path, state, *_events(state))
    plan = _plan(state)
    incomplete_docker = replace(plan.docker, images=plan.docker.images[:-1])
    with pytest.raises(SafetyError, match="image targets"):
        install_teardown_plan(tmp_path, state, replace(plan, docker=incomplete_docker))

    incomplete_aws = replace(plan.aws, task_definition_arns=plan.aws.task_definition_arns[:-1])
    with pytest.raises(SafetyError, match="task definition"):
        install_teardown_plan(tmp_path, state, replace(plan, aws=incomplete_aws))
