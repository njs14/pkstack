from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pstack_kiro", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_feature_and_goal_json_round_trip(tmp_path: Path) -> None:
    (tmp_path / "check.py").write_text("print('healthy')\n", encoding="utf-8")
    generated = _cli(
        "feature",
        "generate",
        "health",
        "--title",
        "Health",
        "--behavior",
        "A maintainer checks health.",
        "--expected-path",
        "Command to result",
        "--command",
        f"{sys.executable} check.py",
        "--ready",
        "--output",
        "json",
        cwd=tmp_path,
    )
    started = _cli(
        "goal",
        "start",
        "Keep health green",
        "--feature",
        "health",
        "--output",
        "json",
        cwd=tmp_path,
    )
    verified = _cli("goal", "verify", "--output", "json", cwd=tmp_path)

    assert generated.returncode == 0, generated.stderr
    assert started.returncode == 0, started.stderr
    assert verified.returncode == 0, verified.stderr
    assert json.loads(generated.stdout)["ok"] is True
    assert json.loads(started.stdout)["goal"]["status"] == "active"
    assert json.loads(verified.stdout)["goal"]["status"] == "passed"


def test_cli_failure_returns_structured_json_and_nonzero(tmp_path: Path) -> None:
    result = _cli("goal", "status", "--output", "json", cwd=tmp_path)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["error_type"] == "GoalError"


@pytest.mark.parametrize(
    ("content", "binary"),
    [
        (
            "---\ntype: feature\nslug: broken\ntitle: Broken\ndraft: true\n"
            'verification:\n  command: "echo \'unterminated"\n---\n\n'
            "## User behavior\n\nA caller sees a result.\n\n"
            "## Expected path\n\nInput to output.\n",
            False,
        ),
        ("", True),
    ],
)
@pytest.mark.parametrize(
    "command", [("feature", "list"), ("feature", "show", "broken"), ("feature", "validate")]
)
def test_malformed_feature_is_one_clean_json_error(
    tmp_path: Path,
    content: str,
    binary: bool,
    command: tuple[str, ...],
) -> None:
    path = tmp_path / "Wiki" / "features" / "broken.md"
    path.parent.mkdir(parents=True)
    if binary:
        path.write_bytes(b"\xff\xfe\x00")
    else:
        path.write_text(content, encoding="utf-8")

    result = _cli(*command, "--output", "json", cwd=tmp_path)

    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "Traceback" not in result.stdout
    if command[-1] == "validate":
        assert result.returncode == 1
        assert set(payload) == {"errors", "feature_count", "features", "ok", "warnings"}
        assert payload["errors"]
    else:
        assert result.returncode == 2
        assert set(payload) == {"error", "error_type", "ok"}
        assert payload["error_type"] == "FeatureMapError"


@pytest.mark.parametrize("output_args", [("--output", "json"), ("--output=json",)])
def test_cli_parser_errors_are_one_clean_json_object(
    tmp_path: Path,
    output_args: tuple[str, ...],
) -> None:
    result = _cli(
        "goal",
        "start",
        "Malformed budget",
        "--command",
        "true",
        "--max-attempts",
        "not-a-number",
        *output_args,
        cwd=tmp_path,
    )

    assert result.returncode == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["error_type"] == "CoercionError"
