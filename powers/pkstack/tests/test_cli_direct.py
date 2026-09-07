from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from feature_fixtures import generate_fixture_cli_feature

from pkstack import __version__, cli
from pkstack.branding import identity_payload

POWER_ROOT = Path(__file__).resolve().parents[1]


def _json(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    return json.loads(capsys.readouterr().out)


def test_renderers_and_version_cover_text_and_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli._emit({"nested": {"ok": True}, "plain": "value"}, "text")
    cli._emit(["one", "two"], "text")
    cli._emit("done", "text")
    cli.version_command(output="json")

    output = capsys.readouterr().out
    assert 'nested: {"ok": true}' in output
    assert "one\ntwo\ndone" in output
    for key, value in identity_payload().items():
        assert f'"{key}": "{value}"' in output

    cli.version_command(output="text")
    expected = {**identity_payload(), "version": __version__}
    expected_text = "".join(f"{key}: {value}\n" for key, value in expected.items())
    assert capsys.readouterr().out == expected_text


def test_fail_renderer_is_structured_in_both_modes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit, match="2"):
        cli._fail(ValueError("bad json"), "json")
    assert _json(capsys)["error_type"] == "ValueError"

    with pytest.raises(SystemExit, match="3"):
        cli._fail(ValueError("bad text"), "text", code=3)
    assert "error: bad text" in capsys.readouterr().err


def test_direct_feature_commands_cover_success_and_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "pass.py").write_text("print('healthy')\n", encoding="utf-8")
    (tmp_path / "fail.py").write_text(
        "from pathlib import Path\nPath('draft-ran').write_text('bad')\nraise SystemExit(7)\n",
        encoding="utf-8",
    )
    generate_fixture_cli_feature(
        "health",
        title="Health",
        behavior="A maintainer checks health.",
        expected_path="Command to healthy result",
        command=f"{sys.executable} pass.py",
        ready=True,
        root=tmp_path,
        output="json",
    )
    assert _json(capsys)["draft"] is False

    cli.feature_list(root=tmp_path, output="json")
    assert _json(capsys)["count"] == 1
    cli.feature_show("health", root=tmp_path, output="json")
    assert _json(capsys)["feature"]["slug"] == "health"
    cli.feature_validate(root=tmp_path, output="json")
    assert _json(capsys)["ok"] is True
    cli.feature_verify("health", root=tmp_path, output="json")
    assert _json(capsys)["ok"] is True

    generate_fixture_cli_feature(
        "broken",
        title="Broken",
        behavior="A check fails.",
        expected_path="Command to failure",
        command=f"{sys.executable} fail.py",
        root=tmp_path,
        output="json",
    )
    _json(capsys)
    with pytest.raises(SystemExit, match="2"):
        cli.feature_verify("broken", root=tmp_path, output="json")
    draft_error = _json(capsys)
    assert draft_error["error_type"] == "FeatureMapError"
    assert "still a draft" in draft_error["error"]
    assert not (tmp_path / "draft-ran").exists()

    with pytest.raises(SystemExit, match="2"):
        cli.goal_start("Do not trust a draft", feature="broken", root=tmp_path, output="json")
    goal_error = _json(capsys)
    assert goal_error["error_type"] == "FeatureMapError"
    assert "still a draft" in goal_error["error"]
    assert not (tmp_path / ".pkstack" / "state" / "goal.json").exists()
    assert not (tmp_path / "draft-ran").exists()

    with pytest.raises(SystemExit, match="2"):
        cli.feature_show("missing", root=tmp_path, output="json")
    assert _json(capsys)["error_type"] == "FeatureMapError"


def test_direct_goal_commands_cover_failure_resume_pass_and_clear(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checker = tmp_path / "check.py"
    checker.write_text(
        "from pathlib import Path\nraise SystemExit(0 if Path('ready').exists() else 9)\n",
        encoding="utf-8",
    )

    cli.goal_start(
        "Make the check pass",
        command=f"{sys.executable} check.py",
        max_attempts=1,
        root=tmp_path,
        output="json",
    )
    assert _json(capsys)["goal"]["status"] == "active"

    with pytest.raises(SystemExit, match="1"):
        cli.goal_verify(root=tmp_path, output="json")
    assert _json(capsys)["goal"]["status"] == "exhausted"

    cli.goal_resume(add_attempts=1, root=tmp_path, output="json")
    assert _json(capsys)["goal"]["status"] == "active"
    cli.goal_tripwire(root=tmp_path, output="json")
    assert _json(capsys)["active"] is True

    (tmp_path / "ready").write_text("yes\n", encoding="utf-8")
    cli.goal_verify(root=tmp_path, output="json")
    assert _json(capsys)["goal"]["status"] == "passed"
    cli.goal_status(root=tmp_path, output="json")
    assert _json(capsys)["goal"]["attempt_count"] == 2
    cli.goal_clear(root=tmp_path, output="json")
    assert _json(capsys)["cleared"] is True

    cli.goal_tripwire(root=tmp_path, output="json")
    assert _json(capsys)["active"] is False
    with pytest.raises(SystemExit, match="2"):
        cli.goal_status(root=tmp_path, output="json")
    assert _json(capsys)["error_type"] == "GoalError"


def test_direct_active_goal_resume_rejection_preserves_status(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checker = tmp_path / "check.py"
    checker.write_text("raise SystemExit(9)\n", encoding="utf-8")
    cli.goal_start(
        "Preserve active goal",
        command=f"{sys.executable} check.py",
        max_attempts=4,
        root=tmp_path,
        output="json",
    )
    _json(capsys)
    with pytest.raises(SystemExit, match="1"):
        cli.goal_verify(root=tmp_path, output="json")
    assert _json(capsys)["goal"]["attempt_count"] == 1

    with pytest.raises(SystemExit, match="2"):
        cli.goal_resume(max_attempts=1, root=tmp_path, output="json")
    error = _json(capsys)
    assert error["error_type"] == "GoalError"
    assert "remaining attempt" in error["error"]

    cli.goal_status(root=tmp_path, output="json")
    preserved = _json(capsys)["goal"]
    assert preserved["status"] == "active"
    assert (preserved["attempt_count"], preserved["max_attempts"]) == (1, 4)


def test_setup_doctor_and_knowledge_cli_boundaries(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli.setup_command(root=tmp_path, power_root=POWER_ROOT, dry_run=True, output="json")
    assert _json(capsys)["dry_run"] is True
    cli.setup_command(root=tmp_path, power_root=POWER_ROOT, output="json")
    assert _json(capsys)["ok"] is True

    cli.doctor_command(root=tmp_path, output="json")
    assert _json(capsys)["ok"] is True
    cli.knowledge_status_command(root=tmp_path, output="json")
    assert "mode" in _json(capsys)

    monkeypatch.setattr("pkstack.knowledge_acp.shutil.which", lambda _name: None)
    cli.knowledge_validate_command(root=tmp_path, output="json")
    payload = _json(capsys)
    assert payload["ok"] is True
    assert payload["mode"] == "local"

    with pytest.raises(SystemExit, match="2"):
        cli.knowledge_search_command("health", root=tmp_path, output="json")
    assert _json(capsys)["error_type"] == "KnowledgeError"


def test_main_dispatches_through_cyclopts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit, match="0"):
        cli.main(["version", "--output", "json"])
    payload = _json(capsys)
    assert {key: payload[key] for key in identity_payload()} == identity_payload()
