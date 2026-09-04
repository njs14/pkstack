from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, cast

import pytest

from pk_stack.features import FeatureMapError, generate_feature
from pk_stack.goal import (
    GoalError,
    GoalStore,
    bind_spec_contract,
    clear_goal,
    get_goal,
    resolve_contract,
    resume_goal,
    start_goal,
    tripwire,
    verify_goal,
)
from pk_stack.models import CommandSpec, VerificationResult


def _contract_digest(contract: CommandSpec) -> str:
    payload = json.dumps(contract.to_dict(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _sentinel_command(tmp_path: Path) -> str:
    checker = tmp_path / "check.py"
    checker.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "if not Path('fixed.txt').exists():\n"
        "    print('missing fixed.txt', file=sys.stderr)\n"
        "    raise SystemExit(9)\n"
        "print('verified')\n",
        encoding="utf-8",
    )
    return f"{sys.executable} check.py"


def _write_native_spec(root: Path, name: str, *, bugfix: bool = False) -> Path:
    directory = root / ".kiro" / "specs" / name
    directory.mkdir(parents=True)
    intent = "bugfix.md" if bugfix else "requirements.md"
    (directory / intent).write_text("# Intent\n\nObservable acceptance.\n", encoding="utf-8")
    (directory / "design.md").write_text("# Design\n\nA bounded design.\n", encoding="utf-8")
    (directory / "tasks.md").write_text("# Tasks\n\n- [ ] Implement.\n", encoding="utf-8")
    return directory


def test_goal_failure_repair_success_path(tmp_path: Path) -> None:
    state = start_goal(
        tmp_path,
        "Create the sentinel",
        command=_sentinel_command(tmp_path),
        max_attempts=3,
    )
    first = verify_goal(tmp_path)
    (tmp_path / "fixed.txt").write_text("done\n", encoding="utf-8")
    second = verify_goal(tmp_path)

    assert state.status == "active"
    assert first.status == "active"
    assert first.attempt_count == 1
    assert first.last_result is not None and first.last_result.exit_code == 9
    assert second.status == "passed"
    assert second.attempt_count == 2
    assert second.last_result is not None and second.last_result.stdout == "verified\n"
    assert len(get_goal(tmp_path).history) == 2


def test_goal_exhaustion_and_resume(tmp_path: Path) -> None:
    start_goal(tmp_path, "Fix later", command=_sentinel_command(tmp_path), max_attempts=1)
    exhausted = verify_goal(tmp_path)

    assert exhausted.status == "exhausted"
    with pytest.raises(GoalError, match="exhausted"):
        verify_goal(tmp_path)
    with pytest.raises(GoalError, match="additional"):
        resume_goal(tmp_path)

    resumed = resume_goal(tmp_path, add_attempts=1)
    assert resumed.status == "active"
    assert resumed.max_attempts == 2


def test_goal_can_resolve_feature_contract(tmp_path: Path) -> None:
    (tmp_path / "health.py").write_text("print('healthy')\n", encoding="utf-8")
    generate_feature(
        tmp_path,
        "health",
        title="Health",
        behavior="A maintainer checks health.",
        expected_path="Command -> healthy result",
        command=[sys.executable, "health.py"],
        draft=False,
    )
    state = start_goal(tmp_path, "Keep health green", feature="health")

    assert state.contract.source == "feature-map"
    assert state.contract.feature == "health"
    assert verify_goal(tmp_path).status == "passed"


def test_goal_rejects_draft_feature_with_command_before_creating_state(tmp_path: Path) -> None:
    (tmp_path / "would-pass.py").write_text("print('not evidence yet')\n", encoding="utf-8")
    generate_feature(
        tmp_path,
        "draft-health",
        title="Draft health",
        behavior="A maintainer will check health after review.",
        expected_path="Draft -> review -> published proof",
        command=[sys.executable, "would-pass.py"],
        draft=True,
    )

    with pytest.raises(FeatureMapError, match=r"still a draft.*verification evidence"):
        start_goal(tmp_path, "Do not trust a draft", feature="draft-health")

    assert not (tmp_path / ".pk-stack" / "state" / "goal.json").exists()


def test_spec_bridge_rejects_non_string_argv_elements(tmp_path: Path) -> None:
    bridge = _write_native_spec(tmp_path, "typed") / "pk-stack-verification.json"
    bridge.write_text('{"schema_version":1,"command":["pytest",true]}\n', encoding="utf-8")

    with pytest.raises(GoalError, match="argv must contain only strings"):
        resolve_contract(tmp_path, spec="typed")


def test_spec_bridge_rejects_schema_free_legacy_shape(tmp_path: Path) -> None:
    bridge = _write_native_spec(tmp_path, "legacy") / "pk-stack-verification.json"
    bridge.write_text('{"command":["pytest"]}\n', encoding="utf-8")

    with pytest.raises(GoalError, match="schema_version 1"):
        resolve_contract(tmp_path, spec="legacy")


def test_spec_binding_prefers_published_feature_and_preserves_both_provenances(
    tmp_path: Path,
) -> None:
    _write_native_spec(tmp_path, "account-lookup")
    (tmp_path / "health.py").write_text("print('healthy')\n", encoding="utf-8")
    generate_feature(
        tmp_path,
        "account-lookup",
        title="Account lookup",
        behavior="A caller can retrieve account health.",
        expected_path="Spec -> feature -> public verifier",
        command=[sys.executable, "health.py"],
        draft=False,
    )

    first = bind_spec_contract(tmp_path, "account-lookup", feature="account-lookup")
    second = bind_spec_contract(tmp_path, "account-lookup", feature="account-lookup")
    contract = resolve_contract(tmp_path, spec="account-lookup")

    assert first["changed"] is True
    assert second["changed"] is False
    assert first["kind"] == "feature"
    assert contract.source == "spec"
    assert contract.spec == "account-lookup"
    assert contract.feature == "account-lookup"
    assert contract.argv == (sys.executable, "health.py")
    assert {Path(item.path).name for item in contract.spec_artifacts} == {
        "requirements.md",
        "design.md",
        "pk-stack-verification.json",
    }
    assert all(len(item.sha256) == 64 for item in contract.spec_artifacts)
    assert json.loads(
        (tmp_path / ".kiro/specs/account-lookup/pk-stack-verification.json").read_text()
    ) == {"schema_version": 1, "feature": "account-lookup"}


def test_spec_binding_supports_reviewed_command_only_when_no_feature_applies(
    tmp_path: Path,
) -> None:
    _write_native_spec(tmp_path, "one-off", bugfix=True)
    checker = _sentinel_command(tmp_path)

    result = bind_spec_contract(tmp_path, "one-off", command=checker)
    contract = resolve_contract(tmp_path, spec="one-off")

    assert result["kind"] == "bugfix"
    assert contract.source == "spec"
    assert contract.spec == "one-off"
    assert contract.feature is None
    assert contract.argv == (sys.executable, "check.py")


def test_spec_binding_requires_complete_native_artifacts_and_exact_source(
    tmp_path: Path,
) -> None:
    directory = tmp_path / ".kiro/specs/incomplete"
    directory.mkdir(parents=True)
    (directory / "requirements.md").write_text("# Requirements\n", encoding="utf-8")

    with pytest.raises(GoalError, match=r"missing design\.md"):
        bind_spec_contract(tmp_path, "incomplete", command=f"{sys.executable} check.py")
    assert not (directory / "pk-stack-verification.json").exists()

    _write_native_spec(tmp_path, "ambiguous")
    (tmp_path / ".kiro/specs/ambiguous/bugfix.md").write_text("# Bug\n", encoding="utf-8")
    with pytest.raises(GoalError, match="exactly one"):
        bind_spec_contract(tmp_path, "ambiguous", command=f"{sys.executable} check.py")


def test_spec_binding_refuses_changed_bridge_without_explicit_overwrite(tmp_path: Path) -> None:
    directory = _write_native_spec(tmp_path, "stable")
    (tmp_path / "one.py").write_text("pass\n", encoding="utf-8")
    (tmp_path / "two.py").write_text("pass\n", encoding="utf-8")
    bind_spec_contract(tmp_path, "stable", command=f"{sys.executable} one.py")
    before = (directory / "pk-stack-verification.json").read_bytes()

    with pytest.raises(GoalError, match="without --overwrite"):
        bind_spec_contract(tmp_path, "stable", command=f"{sys.executable} two.py")
    assert (directory / "pk-stack-verification.json").read_bytes() == before

    replaced = bind_spec_contract(
        tmp_path,
        "stable",
        command=f"{sys.executable} two.py",
        overwrite=True,
    )
    assert replaced["changed"] is True
    assert resolve_contract(tmp_path, spec="stable").argv == (sys.executable, "two.py")


@pytest.mark.parametrize(
    "artifact",
    ["requirements.md", "design.md", "pk-stack-verification.json"],
)
def test_spec_goal_rejects_bound_artifact_drift_without_consuming_attempt(
    tmp_path: Path,
    artifact: str,
) -> None:
    directory = _write_native_spec(tmp_path, "drift")
    bind_spec_contract(tmp_path, "drift", command=_sentinel_command(tmp_path))
    start_goal(tmp_path, "Keep native acceptance bound", spec="drift")
    before = GoalStore(tmp_path).path.read_bytes()
    with (directory / artifact).open("a", encoding="utf-8") as handle:
        handle.write("\nchanged after goal start\n")

    with pytest.raises(GoalError, match="changed after goal start"):
        verify_goal(tmp_path)

    assert GoalStore(tmp_path).path.read_bytes() == before
    state = get_goal(tmp_path)
    assert state.attempt_count == 0
    assert state.history == []


def test_spec_goal_allows_mutable_task_progress(tmp_path: Path) -> None:
    directory = _write_native_spec(tmp_path, "task-progress")
    bind_spec_contract(tmp_path, "task-progress", command=_sentinel_command(tmp_path))
    start_goal(tmp_path, "Allow native task progress", spec="task-progress")
    (directory / "tasks.md").write_text("# Tasks\n\n- [x] Implement.\n", encoding="utf-8")
    (tmp_path / "fixed.txt").write_text("done\n", encoding="utf-8")

    result = verify_goal(tmp_path)

    assert result.status == "passed"
    assert result.attempt_count == 1


def test_spec_goal_discards_result_when_artifact_drifts_during_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = _write_native_spec(tmp_path, "racing-spec")
    bind_spec_contract(tmp_path, "racing-spec", command=_sentinel_command(tmp_path))
    start_goal(tmp_path, "Discard proof after spec drift", spec="racing-spec")

    def drift_during_verification(*_args: object, **_kwargs: object) -> VerificationResult:
        (directory / "design.md").write_text("# Design\n\nChanged during proof.\n")
        return VerificationResult(
            passed=True,
            exit_code=0,
            stdout="stale proof\n",
            stderr="",
            duration_ms=0,
        )

    monkeypatch.setattr("pk_stack.goal.run_command", drift_during_verification)
    with pytest.raises(GoalError, match="changed after goal start"):
        verify_goal(tmp_path)

    state = get_goal(tmp_path)
    assert state.status == "active"
    assert state.attempt_count == 0
    assert state.history == []


def test_goal_state_is_atomic_private_and_tripwire_is_advisory(tmp_path: Path) -> None:
    state = start_goal(tmp_path, "Test", command=_sentinel_command(tmp_path))
    store = GoalStore(tmp_path)

    assert tripwire(tmp_path)["active"] is True
    assert oct(store.path.stat().st_mode & 0o777) == "0o600"
    payload = json.loads(store.path.read_text(encoding="utf-8"))
    assert payload["goal_id"] == state.goal_id


def test_goal_state_locking_fails_closed_without_fcntl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("pk_stack.goal.fcntl", None)

    with pytest.raises(GoalError, match="requires POSIX fcntl"):
        start_goal(tmp_path, "Do not run unlocked", command=_sentinel_command(tmp_path))

    assert not (tmp_path / ".pk-stack").exists()


def test_clear_requires_force_for_active_goal(tmp_path: Path) -> None:
    start_goal(tmp_path, "Test", command=_sentinel_command(tmp_path))

    with pytest.raises(GoalError, match="--force"):
        clear_goal(tmp_path)
    assert clear_goal(tmp_path, force=True)["cleared"] is True
    assert clear_goal(tmp_path)["cleared"] is False


def test_read_only_goal_queries_do_not_create_state_artifacts(tmp_path: Path) -> None:
    with pytest.raises(GoalError, match="no goal state"):
        get_goal(tmp_path)
    assert tripwire(tmp_path)["active"] is False
    assert not (tmp_path / ".pk-stack").exists()


def test_start_rejects_ambiguous_contract_sources(tmp_path: Path) -> None:
    with pytest.raises(GoalError, match="exactly one"):
        start_goal(
            tmp_path,
            "Ambiguous",
            command=f"{sys.executable} -c pass",
            feature="something",
        )


def test_goal_resume_and_terminal_tripwire_reject_invalid_budgets(tmp_path: Path) -> None:
    with pytest.raises(GoalError, match="negative"):
        resume_goal(tmp_path, add_attempts=-1)
    with pytest.raises(GoalError, match="no goal"):
        resume_goal(tmp_path)

    start_goal(tmp_path, "Use the budget", command=_sentinel_command(tmp_path), max_attempts=2)
    verify_goal(tmp_path)
    exhausted = verify_goal(tmp_path)

    assert exhausted.status == "exhausted"
    assert tripwire(tmp_path)["status"] == "exhausted"
    with pytest.raises(GoalError, match="between 1 and 20"):
        resume_goal(tmp_path, max_attempts=0)
    with pytest.raises(GoalError, match="lower than attempts"):
        resume_goal(tmp_path, max_attempts=1)


def test_active_goal_resume_cannot_consume_its_remaining_budget(tmp_path: Path) -> None:
    start_goal(tmp_path, "Keep valid state", command=_sentinel_command(tmp_path), max_attempts=4)
    failed = verify_goal(tmp_path)
    store = GoalStore(tmp_path)
    before = store.path.read_bytes()

    assert failed.status == "active"
    assert failed.attempt_count == 1
    with pytest.raises(GoalError, match="remaining attempt"):
        resume_goal(tmp_path, max_attempts=1)

    assert store.path.read_bytes() == before
    preserved = get_goal(tmp_path)
    assert preserved.status == "active"
    assert (preserved.attempt_count, preserved.max_attempts) == (1, 4)


def test_goal_store_rejects_unreloadable_state_before_replacing_evidence(tmp_path: Path) -> None:
    state = start_goal(tmp_path, "Preserve valid evidence", command=_sentinel_command(tmp_path))
    store = GoalStore(tmp_path)
    before = store.path.read_bytes()
    state.created_at = cast(Any, 7)

    with pytest.raises(GoalError, match="refusing to save invalid goal state"):
        store.save(state)

    assert store.path.read_bytes() == before
    assert get_goal(tmp_path).objective == "Preserve valid evidence"


def test_goal_store_rejects_unsupported_schema_before_replacing_evidence(tmp_path: Path) -> None:
    state = start_goal(tmp_path, "Preserve current schema", command=_sentinel_command(tmp_path))
    store = GoalStore(tmp_path)
    before = store.path.read_bytes()
    state.schema_version = 1

    with pytest.raises(GoalError, match="unsupported goal state schema"):
        store.save(state)

    assert store.path.read_bytes() == before
    assert get_goal(tmp_path).schema_version == 2


def test_goal_store_and_loader_reject_policy_invalid_stored_contract(tmp_path: Path) -> None:
    (tmp_path / "passes.py").write_text("pass\n", encoding="utf-8")
    passed = start_goal(
        tmp_path,
        "Preserve meaningful proof",
        command=f"{sys.executable} passes.py",
    )
    passed = verify_goal(tmp_path)
    assert passed.status == "passed"
    store = GoalStore(tmp_path)
    valid_bytes = store.path.read_bytes()
    invalid_contract = CommandSpec(argv=("true",), display="true", source="explicit")
    passed.contract = invalid_contract
    passed.contract_digest = _contract_digest(invalid_contract)

    with pytest.raises(GoalError, match="stored verifier command is rejected"):
        store.save(passed)
    assert store.path.read_bytes() == valid_bytes

    payload = json.loads(valid_bytes)
    payload["contract"] = invalid_contract.to_dict()
    payload["contract_digest"] = _contract_digest(invalid_contract)
    store.path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(GoalError, match="stored verifier command is rejected"):
        get_goal(tmp_path)

    cleared = clear_goal(tmp_path, force=True)
    assert cleared == {"cleared": True, "goal_id": passed.goal_id, "status": "passed"}
    assert not store.path.exists()


def test_verifier_result_is_discarded_when_resume_changes_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start_goal(tmp_path, "Do not race resume", command=_sentinel_command(tmp_path))

    def resume_during_verification(*_args: object, **_kwargs: object) -> VerificationResult:
        resume_goal(tmp_path, max_attempts=5)
        return VerificationResult(
            passed=True,
            exit_code=0,
            stdout="stale proof\n",
            stderr="",
            duration_ms=0,
        )

    monkeypatch.setattr("pk_stack.goal.run_command", resume_during_verification)
    with pytest.raises(GoalError, match="state changed during verification"):
        verify_goal(tmp_path)

    preserved = get_goal(tmp_path)
    assert preserved.status == "active"
    assert preserved.max_attempts == 5
    assert preserved.attempt_count == 0
    assert preserved.history == []


def test_goal_contract_and_store_error_boundaries(tmp_path: Path) -> None:
    generate_feature(
        tmp_path,
        "draft-only",
        title="Draft only",
        behavior="A draft is reviewed.",
        expected_path="Draft -> review",
        command=None,
    )
    with pytest.raises(FeatureMapError, match="still a draft"):
        resolve_contract(tmp_path, feature="draft-only")

    bridge = _write_native_spec(tmp_path, "broken") / "pk-stack-verification.json"
    bridge.write_text("{broken", encoding="utf-8")
    with pytest.raises(GoalError, match="invalid spec verification bridge"):
        resolve_contract(tmp_path, spec="broken")

    hostile = tmp_path / "hostile"
    outside = tmp_path / "outside"
    hostile.mkdir()
    outside.mkdir()
    (hostile / ".pk-stack").symlink_to(outside, target_is_directory=True)
    with pytest.raises(GoalError, match="symlink"):
        GoalStore(hostile)


def test_goal_rejects_unsupported_schema_and_discards_removed_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _sentinel_command(tmp_path)
    start_goal(tmp_path, "Reject old state", command=command)
    store = GoalStore(tmp_path)
    payload = json.loads(store.path.read_text(encoding="utf-8"))
    payload["schema_version"] = 1
    store.path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(GoalError, match="unsupported goal state schema"):
        get_goal(tmp_path)

    store.clear()
    start_goal(tmp_path, "Discard stale proof", command=command)

    def remove_state(*_args: object, **_kwargs: object) -> VerificationResult:
        GoalStore(tmp_path).clear()
        return VerificationResult(
            passed=True,
            exit_code=0,
            stdout="",
            stderr="",
            duration_ms=0,
        )

    monkeypatch.setattr("pk_stack.goal.run_command", remove_state)
    with pytest.raises(GoalError, match="changed while its verifier was running"):
        verify_goal(tmp_path)
