from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from feature_fixtures import generate_fixture_feature

from pk_stack import bootstrap
from pk_stack.features import (
    FeatureMapError,
    load_feature,
    validate_feature_map,
)
from pk_stack.goal import (
    GoalError,
    get_goal,
    resolve_contract,
    resume_goal,
    start_goal,
    verify_goal,
)
from pk_stack.knowledge import KnowledgeError
from pk_stack.knowledge import search as search_knowledge
from pk_stack.knowledge import validate as validate_knowledge
from pk_stack.runner import CommandRejected, parse_command, run_command

POWER_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("# no frontmatter\n", "expected YAML"),
        ("---\ntype: feature\n", "unterminated"),
        ("---\n[broken\n---\n", "invalid YAML"),
        ("---\n- feature\n---\n", "must be a mapping"),
        ("---\ntype: other\n---\n", "type must be"),
    ],
)
def test_feature_loader_rejects_malformed_documents(
    tmp_path: Path, content: str, message: str
) -> None:
    path = tmp_path / "Wiki" / "features" / "broken.md"
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")

    with pytest.raises(FeatureMapError, match=message):
        load_feature(path, root=tmp_path)


def test_feature_loader_rejects_schema_errors_and_escape(tmp_path: Path) -> None:
    directory = tmp_path / "Wiki" / "features"
    directory.mkdir(parents=True)
    wrong_suffix = directory / "health.txt"
    wrong_suffix.write_text("---\ntype: feature\n---\n", encoding="utf-8")
    with pytest.raises(FeatureMapError, match="Markdown"):
        load_feature(wrong_suffix, root=tmp_path)

    mismatch = directory / "health.md"
    mismatch.write_text(
        "---\ntype: feature\nschema_version: 2\nslug: other\ntitle: Health\n---\n\n"
        "## User behavior\n\nCheck.\n\n## Expected path\n\nCommand -> result.\n",
        encoding="utf-8",
    )
    with pytest.raises(FeatureMapError, match="file name"):
        load_feature(mismatch, root=tmp_path)

    generated = generate_fixture_feature(
        tmp_path,
        "escape",
        title="Escape",
        behavior="A path is checked.",
        expected_path="Input -> result",
        command=None,
    )
    generated.write_text(
        generated.read_text(encoding="utf-8").replace(
            "draft: true\n",
            "draft: true\nrelated:\n- ../../../../outside\n",
        ),
        encoding="utf-8",
    )
    assert generated.is_file()
    result = validate_feature_map(tmp_path)
    assert result["ok"] is False
    assert any("escapes the project" in error for error in result["errors"])

    with pytest.raises(FeatureMapError, match="non-empty"):
        generate_fixture_feature(
            tmp_path,
            "empty",
            title="",
            behavior="Behavior",
            expected_path="Path",
            command=None,
        )


def test_goal_spec_bridge_and_transition_errors(tmp_path: Path) -> None:
    (tmp_path / "pass.py").write_text("pass\n", encoding="utf-8")
    bridge = tmp_path / ".kiro" / "specs" / "health" / "pk-stack-verification.json"
    bridge.parent.mkdir(parents=True)
    for name in ("requirements.md", "design.md", "tasks.md"):
        (bridge.parent / name).write_text(f"# {name}\n\nBounded artifact.\n", encoding="utf-8")
    bridge.write_text(
        json.dumps({"schema_version": 1, "command": [sys.executable, "pass.py"]}),
        encoding="utf-8",
    )

    contract = resolve_contract(tmp_path, spec="health")
    assert contract.source == "spec"
    assert contract.spec == "health"

    state = start_goal(tmp_path, "Prove health", spec="health", max_attempts=2)
    assert state.status == "active"
    with pytest.raises(GoalError, match="already exists"):
        start_goal(tmp_path, "Duplicate", command=f"{sys.executable} pass.py")
    assert verify_goal(tmp_path).status == "passed"
    with pytest.raises(GoalError, match="already passed"):
        verify_goal(tmp_path)
    with pytest.raises(GoalError, match="cannot be resumed"):
        resume_goal(tmp_path)

    with pytest.raises(GoalError, match="non-empty"):
        start_goal(tmp_path / "empty", " ", command=f"{sys.executable} pass.py")
    with pytest.raises(GoalError, match="between 1 and 20"):
        start_goal(tmp_path / "budget", "Bad budget", command="true", max_attempts=21)
    with pytest.raises(GoalError, match="no executable"):
        resolve_contract(tmp_path)
    with pytest.raises(GoalError, match="does not exist"):
        resolve_contract(tmp_path, spec="missing")
    assert get_goal(tmp_path).goal_id == state.goal_id


@pytest.mark.parametrize(
    "value",
    ["", "unterminated '", "bad\ncommand", "nul\x00command"],
)
def test_command_parser_rejects_invalid_values(value: str) -> None:
    with pytest.raises(CommandRejected):
        parse_command(value)


def test_runner_rejects_more_destructive_forms_and_reports_exec_errors(tmp_path: Path) -> None:
    for command in (["gh", "repo", "delete"], ["tofu", "import"], ["python", "-c", "pass\x00"]):
        with pytest.raises(CommandRejected):
            run_command(command, root=tmp_path)

    missing = run_command(["definitely-missing-pk-stack-executable"], root=tmp_path)
    assert missing.exit_code == 127
    assert missing.error and "unable to execute" in missing.error
    with pytest.raises(ValueError, match="positive"):
        run_command(["test", "-d", "."], root=tmp_path, timeout_seconds=0)
    with pytest.raises(ValueError, match="1024"):
        run_command(["test", "-d", "."], root=tmp_path, output_limit=100)


def test_knowledge_delegates_to_available_okn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "Wiki/features").mkdir(parents=True)
    okn = tmp_path / "tools" / "okn"
    okn.parent.mkdir()
    okn.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "args = sys.argv[1:]\n"
        "if args == ['version']:\n"
        "    print('0.13.0')\n"
        "elif 'validate' in args:\n"
        f"    print(json.dumps({{'schemaVersion': '1', 'root': {str(workspace / 'Wiki')!r}, "
        "'specVersion': '0.2', 'profile': 'okf', 'files': 1, 'concepts': 0, "
        "'indexes': 1, 'logs': 0, 'summary': {'status': 'pass', 'errorCount': 0, "
        "'warningCount': 0, 'issueCount': 0}, 'issues': []}))\n"
        "elif 'search' in args:\n"
        f"    print(json.dumps({{'schemaVersion': '1', 'root': {str(workspace / 'Wiki')!r}, "
        "'revision': "
        "{'specVersion': '0.2', 'indexSha256': '0' * 64}, 'query': args[-1], "
        "'budget': int(args[args.index('--budget') + 1]), 'estimatedTokens': 0, "
        "'limit': 12, 'route': ['bm25'], 'sources': [], 'issues': []}))\n"
        "else:\n"
        "    raise SystemExit(83)\n",
        encoding="utf-8",
    )
    okn.chmod(0o755)
    monkeypatch.setattr("pk_stack.knowledge.shutil.which", lambda _name: str(okn))

    assert validate_knowledge(workspace)["mode"] == "canonical-okn"
    assert search_knowledge(workspace, "account")["ok"] is True
    with pytest.raises(KnowledgeError, match="non-empty"):
        search_knowledge(workspace, " ")
    with pytest.raises(KnowledgeError, match="must not begin"):
        search_knowledge(workspace, "--help")


def test_bootstrap_main_and_missing_asset_paths(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bootstrap.main(
        [
            "--root",
            str(tmp_path),
            "--power-root",
            str(POWER_ROOT),
            "--dry-run",
            "--output",
            "json",
        ]
    )
    assert json.loads(capsys.readouterr().out)["dry_run"] is True

    with pytest.raises(ValueError, match="source package"):
        bootstrap.bootstrap_project(tmp_path, power_root=tmp_path / "missing")

    minimal_power = tmp_path / "minimal-power"
    source = minimal_power / "src" / "pk_stack"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text("", encoding="utf-8")
    lock = minimal_power / "templates" / "projectctl" / "uv.lock"
    lock.parent.mkdir(parents=True)
    lock.write_bytes((POWER_ROOT / "templates" / "projectctl" / "uv.lock").read_bytes())
    minimal_target = tmp_path / "minimal-target"
    minimal_target.mkdir()
    with pytest.raises(ValueError, match="required PK-Stack Power assets are missing"):
        bootstrap.bootstrap_project(minimal_target, power_root=minimal_power)
    assert list(minimal_target.iterdir()) == []
