from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, cast

import pytest

from pstack_kiro.features import FeatureMapError, generate_feature
from pstack_kiro.goal import (
    GoalError,
    GoalStore,
    clear_goal,
    get_goal,
    resolve_contract,
    resume_goal,
    start_goal,
    tripwire,
    verify_goal,
)
from pstack_kiro.models import CommandSpec, VerificationResult


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

    assert not (tmp_path / ".pstack" / "state" / "goal.json").exists()


def test_spec_bridge_rejects_non_string_argv_elements(tmp_path: Path) -> None:
    bridge = tmp_path / ".kiro" / "specs" / "typed" / "pstack-verification.json"
    bridge.parent.mkdir(parents=True)
    bridge.write_text('{"command":["pytest",true]}\n', encoding="utf-8")

    with pytest.raises(GoalError, match="argv must contain only strings"):
        resolve_contract(tmp_path, spec="typed")


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
    monkeypatch.setattr("pstack_kiro.goal.fcntl", None)

    with pytest.raises(GoalError, match="requires POSIX fcntl"):
        start_goal(tmp_path, "Do not run unlocked", command=_sentinel_command(tmp_path))

    assert not (tmp_path / ".pstack").exists()


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
    assert not (tmp_path / ".pstack").exists()


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

    monkeypatch.setattr("pstack_kiro.goal.run_command", resume_during_verification)
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

    bridge = tmp_path / ".kiro" / "specs" / "broken" / "pstack-verification.json"
    bridge.parent.mkdir(parents=True)
    bridge.write_text("{broken", encoding="utf-8")
    with pytest.raises(GoalError, match="invalid spec verification bridge"):
        resolve_contract(tmp_path, spec="broken")

    hostile = tmp_path / "hostile"
    outside = tmp_path / "outside"
    hostile.mkdir()
    outside.mkdir()
    (hostile / ".pstack").symlink_to(outside, target_is_directory=True)
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

    monkeypatch.setattr("pstack_kiro.goal.run_command", remove_state)
    with pytest.raises(GoalError, match="changed while its verifier was running"):
        verify_goal(tmp_path)
