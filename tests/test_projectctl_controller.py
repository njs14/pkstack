from __future__ import annotations

import ast
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONTROLLER_ROOT = REPOSITORY_ROOT / ".pstack" / "projectctl"
CONTROLLER_SOURCE = CONTROLLER_ROOT / "src"
POWER_ROOT = REPOSITORY_ROOT / "powers" / "pk-stack"
VERIFICATION_COMMAND = "./labctl verify --output json"


@pytest.fixture(scope="module")
def controller() -> SimpleNamespace:
    """Import the vendored controller without selecting its mutable cached venv."""

    previous_path = list(sys.path)
    previous_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == "pstack_kiro" or name.startswith("pstack_kiro.")
    }
    for name in previous_modules:
        del sys.modules[name]

    # Goal tests use explicit contracts. Avoid adding PyYAML to the host lab merely
    # to satisfy the unused feature-map edge imported by pstack_kiro.goal.
    feature_stub = ModuleType("pstack_kiro.features")

    def unused_find_feature(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("feature-map resolution is outside this controller regression suite")

    feature_stub.find_feature = unused_find_feature  # type: ignore[attr-defined]

    # The root suite intentionally avoids adding PyYAML solely to import the
    # otherwise-unused feature parser. Execute the canonical helper's own AST
    # instead of copying its draft/command rule into a test stub that could
    # silently diverge from the Power implementation.
    feature_source = POWER_ROOT / "src" / "pstack_kiro" / "features.py"
    parsed = ast.parse(feature_source.read_text(encoding="utf-8"), filename=str(feature_source))
    helpers = [
        node
        for node in parsed.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "find_verifiable_feature"
    ]
    assert len(helpers) == 1

    def delegated_find_feature(root: Path, slug: str) -> Any:
        return feature_stub.find_feature(root, slug)  # type: ignore[attr-defined]

    helper_namespace: dict[str, Any] = {
        "FeatureMapError": ValueError,
        "FeatureSpec": Any,
        "Path": Path,
        "find_feature": delegated_find_feature,
    }
    exec(  # noqa: S102 - execute only the named helper AST from the tracked canonical source
        compile(ast.Module(body=helpers, type_ignores=[]), str(feature_source), "exec"),
        helper_namespace,
    )
    feature_stub.find_verifiable_feature = helper_namespace[  # type: ignore[attr-defined]
        "find_verifiable_feature"
    ]
    sys.path.insert(0, str(CONTROLLER_SOURCE))
    sys.modules[feature_stub.__name__] = feature_stub
    try:
        goal = importlib.import_module("pstack_kiro.goal")
        runner = importlib.import_module("pstack_kiro.runner")
        bootstrap = importlib.import_module("pstack_kiro.bootstrap")
        assert all(
            Path(module.__file__).resolve().is_relative_to(CONTROLLER_SOURCE)
            for module in (goal, runner, bootstrap)
        )
        yield SimpleNamespace(
            goal=goal,
            runner=runner,
            bootstrap=bootstrap,
            features=feature_stub,
        )
    finally:
        for name in tuple(sys.modules):
            if name == "pstack_kiro" or name.startswith("pstack_kiro."):
                del sys.modules[name]
        sys.modules.update(previous_modules)
        sys.path[:] = previous_path


def _write_labctl(root: Path) -> None:
    verifier = root / "labctl"
    verifier.write_text(
        """#!/bin/sh
set -eu
if [ -f verification-pass ]; then
  printf '{"ok":true}\\n'
  exit 0
fi
printf '{"ok":false}\\n'
exit 7
""",
        encoding="utf-8",
    )
    verifier.chmod(0o700)


def test_goal_records_a_real_fail_then_pass_transition(
    tmp_path: Path,
    controller: SimpleNamespace,
) -> None:
    _write_labctl(tmp_path)

    started = controller.goal.start_goal(
        tmp_path,
        "Repair the document export regression",
        command=VERIFICATION_COMMAND,
        max_attempts=3,
    )
    failed = controller.goal.verify_goal(tmp_path, timeout_seconds=5)
    (tmp_path / "verification-pass").touch()
    passed = controller.goal.verify_goal(tmp_path, timeout_seconds=5)

    assert started.status == "active"
    assert started.attempt_count == 0
    assert failed.goal_id == started.goal_id == passed.goal_id
    assert failed.status == "active"
    assert failed.attempt_count == 1
    assert failed.last_result is not None
    assert failed.last_result.passed is False
    assert failed.last_result.exit_code == 7
    assert failed.last_result.stdout == '{"ok":false}\n'
    assert passed.status == "passed"
    assert passed.attempt_count == 2
    assert [result.passed for result in passed.history] == [False, True]
    assert controller.goal.get_goal(tmp_path).to_dict() == passed.to_dict()
    assert controller.goal.clear_goal(tmp_path) == {
        "cleared": True,
        "goal_id": started.goal_id,
        "status": "passed",
    }


def test_exhausted_goal_requires_and_accepts_an_explicit_resume(
    tmp_path: Path,
    controller: SimpleNamespace,
) -> None:
    _write_labctl(tmp_path)
    started = controller.goal.start_goal(
        tmp_path,
        "Use a bounded repair budget",
        command=VERIFICATION_COMMAND,
        max_attempts=1,
    )

    exhausted = controller.goal.verify_goal(tmp_path, timeout_seconds=5)
    with pytest.raises(controller.goal.GoalError, match="goal is exhausted"):
        controller.goal.verify_goal(tmp_path, timeout_seconds=5)

    resumed = controller.goal.resume_goal(tmp_path, add_attempts=1)
    (tmp_path / "verification-pass").touch()
    passed = controller.goal.verify_goal(tmp_path, timeout_seconds=5)

    assert exhausted.goal_id == started.goal_id
    assert exhausted.status == "exhausted"
    assert exhausted.attempt_count == exhausted.max_attempts == 1
    assert resumed.goal_id == started.goal_id
    assert resumed.status == "active"
    assert resumed.max_attempts == 2
    assert passed.status == "passed"
    assert passed.attempt_count == passed.max_attempts == 2


def test_clear_goal_requires_force_while_active(
    tmp_path: Path,
    controller: SimpleNamespace,
) -> None:
    _write_labctl(tmp_path)
    started = controller.goal.start_goal(
        tmp_path,
        "Do not discard an active loop accidentally",
        command=VERIFICATION_COMMAND,
    )

    with pytest.raises(controller.goal.GoalError, match="without --force"):
        controller.goal.clear_goal(tmp_path)

    assert controller.goal.get_goal(tmp_path).goal_id == started.goal_id
    assert controller.goal.clear_goal(tmp_path, force=True) == {
        "cleared": True,
        "goal_id": started.goal_id,
        "status": "active",
    }
    assert controller.goal.clear_goal(tmp_path) == {
        "cleared": False,
        "reason": "no goal state exists",
    }


def test_verification_policy_accepts_the_document_export_contract(
    tmp_path: Path,
    controller: SimpleNamespace,
) -> None:
    argv = controller.runner.parse_command(VERIFICATION_COMMAND)

    controller.runner.enforce_verification_policy(argv, root=tmp_path)

    assert argv == ("./labctl", "verify", "--output", "json")


def test_goal_rejects_a_draft_feature_even_when_it_has_an_executable_command(
    tmp_path: Path,
    controller: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_labctl(tmp_path)
    draft = SimpleNamespace(
        command=controller.runner.parse_command(VERIFICATION_COMMAND),
        draft=True,
    )
    monkeypatch.setattr(controller.features, "find_feature", lambda _root, _slug: draft)

    with pytest.raises(ValueError, match="still a draft.*verification evidence"):
        controller.goal.start_goal(
            tmp_path,
            "Do not trust unpublished acceptance criteria",
            feature="document-export",
        )

    assert not (tmp_path / ".pstack" / "state" / "goal.json").exists()


def test_goal_accepts_and_runs_the_same_feature_after_publication(
    tmp_path: Path,
    controller: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_labctl(tmp_path)
    (tmp_path / "verification-pass").touch()
    published = SimpleNamespace(
        command=controller.runner.parse_command(VERIFICATION_COMMAND),
        draft=False,
    )
    monkeypatch.setattr(controller.features, "find_feature", lambda _root, _slug: published)

    started = controller.goal.start_goal(
        tmp_path,
        "Use the published acceptance criteria",
        feature="document-export",
    )
    passed = controller.goal.verify_goal(tmp_path, timeout_seconds=5)

    assert started.contract.source == "feature-map"
    assert started.contract.feature == "document-export"
    assert started.contract.argv == ("./labctl", "verify", "--output", "json")
    assert passed.status == "passed"
    assert passed.attempt_count == 1


def test_generated_projectctl_rejects_draft_feature_before_execution_or_goal_state(
    tmp_path: Path,
) -> None:
    feature = tmp_path / "Wiki" / "features" / "draft-sentinel.md"
    feature.parent.mkdir(parents=True)
    feature.write_text(
        """---
type: feature
slug: draft-sentinel
title: Draft sentinel
draft: true
verification:
  command:
    - ./draft-sentinel.sh
---

# Draft sentinel

## User behavior

A maintainer cannot use an unpublished contract as evidence.

## Expected path

Draft contract to fail-closed controller boundary.
""",
        encoding="utf-8",
    )
    sentinel = tmp_path / "draft-sentinel.sh"
    sentinel.write_text("#!/bin/sh\ntouch draft-ran\n", encoding="utf-8")
    sentinel.chmod(0o700)
    executable = REPOSITORY_ROOT / ".pstack" / "bin" / "projectctl"
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    commands = (
        ("feature", "verify", "draft-sentinel"),
        (
            "goal",
            "start",
            "Do not trust unpublished evidence",
            "--feature",
            "draft-sentinel",
        ),
    )
    for command in commands:
        result = subprocess.run(
            [
                str(executable),
                *command,
                "--root",
                str(tmp_path),
                "--output",
                "json",
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        assert result.returncode == 2, (result.stdout, result.stderr)
        payload = json.loads(result.stdout)
        assert payload["ok"] is False
        assert payload["error_type"] == "FeatureMapError"
        assert "still a draft" in payload["error"]

    assert not (tmp_path / "draft-ran").exists()
    assert not (tmp_path / ".pstack" / "state" / "goal.json").exists()


@pytest.mark.parametrize(
    ("command", "message"),
    [
        ("projectctl goal status", "own verification evidence"),
        ("sh -c './labctl verify --output json'", "shell interpreters"),
        ("rm -rf .", "not permitted"),
        ("echo passed", "cannot establish verification evidence"),
        ("uv run python -c 'raise SystemExit(0)'", "inline interpreter code"),
        ("python ../outside.py", "cannot escape the project root"),
    ],
)
def test_verification_policy_rejects_unsafe_or_non_evidentiary_contracts(
    tmp_path: Path,
    controller: SimpleNamespace,
    command: str,
    message: str,
) -> None:
    argv = controller.runner.parse_command(command)

    with pytest.raises(controller.runner.CommandRejected, match=message):
        controller.runner.enforce_verification_policy(argv, root=tmp_path)


def test_bootstrap_is_idempotent_and_preserves_its_receipt(
    tmp_path: Path,
    controller: SimpleNamespace,
) -> None:
    first = controller.bootstrap.bootstrap_project(tmp_path, power_root=POWER_ROOT)
    receipt = tmp_path / ".pstack" / "bootstrap.json"
    first_receipt = receipt.read_bytes()
    first_audit = controller.bootstrap.audit_bootstrap_receipt(tmp_path)

    second = controller.bootstrap.bootstrap_project(tmp_path, power_root=POWER_ROOT)
    second_audit = controller.bootstrap.audit_bootstrap_receipt(tmp_path)

    assert first.ok is True
    assert first.created
    assert first.updated == []
    assert first_audit.ok is True
    assert first_audit.managed_count > 0
    assert second.ok is True
    assert second.created == []
    assert second.updated == []
    assert second.pending_updates == []
    assert second.conflicts == []
    assert second.unchanged
    assert receipt.read_bytes() == first_receipt
    assert second_audit == first_audit
    assert not (tmp_path / ".pstack" / "projectctl" / ".venv").exists()
