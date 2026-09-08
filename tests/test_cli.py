from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pkstack", *args],
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
        "--sub-feature",
        "health-check=The health result is observable.",
        "--entrypoint",
        "cli=Run the public health command.",
        "--drive",
        f"cli=Run {sys.executable} check.py.",
        "--entrypoint-proof",
        "cli=The command exits zero and prints healthy.",
        "--gotcha",
        "A process-only check does not prove the returned health value.",
        "--evidence-boundary",
        "Capture exit status and bounded output.",
        "--cleanup-boundary",
        "The check owns no persistent state.",
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
    assert json.loads(generated.stdout)["schema_version"] == 2
    assert json.loads(started.stdout)["goal"]["status"] == "active"
    assert json.loads(verified.stdout)["goal"]["status"] == "passed"


def test_cli_binds_native_spec_to_feature_before_verified_goal(tmp_path: Path) -> None:
    (tmp_path / "check.py").write_text("print('healthy')\n", encoding="utf-8")
    generated = _cli(
        "feature",
        "generate",
        "native-health",
        "--title",
        "Native health",
        "--behavior",
        "A caller observes health through the planned native feature.",
        "--expected-path",
        "Kiro Spec to feature contract to public verifier",
        "--command",
        f"{sys.executable} check.py",
        "--sub-feature",
        "health-check=The public health result is observable.",
        "--entrypoint",
        "cli=Run the public health command.",
        "--drive",
        f"cli=Run {sys.executable} check.py.",
        "--entrypoint-proof",
        "cli=The command exits zero and prints healthy.",
        "--gotcha",
        "A task checkbox alone is not executable acceptance evidence.",
        "--evidence-boundary",
        "Capture bounded public output and exit status.",
        "--cleanup-boundary",
        "The check owns no persistent state.",
        "--ready",
        "--output",
        "json",
        cwd=tmp_path,
    )
    spec = tmp_path / ".kiro/specs/native-health"
    spec.mkdir(parents=True)
    for name in ("requirements.md", "design.md", "tasks.md"):
        (spec / name).write_text(f"# {name}\n\nNative Kiro artifact.\n", encoding="utf-8")

    bound = _cli(
        "goal",
        "bind-spec",
        "native-health",
        "--feature",
        "native-health",
        "--output",
        "json",
        cwd=tmp_path,
    )
    started = _cli(
        "goal",
        "start",
        "Prove the native health spec",
        "--spec",
        "native-health",
        "--output",
        "json",
        cwd=tmp_path,
    )
    verified = _cli("goal", "verify", "--output", "json", cwd=tmp_path)

    assert generated.returncode == 0, generated.stdout
    assert bound.returncode == 0, bound.stdout
    assert started.returncode == 0, started.stdout
    assert verified.returncode == 0, verified.stdout
    contract = json.loads(started.stdout)["goal"]["contract"]
    assert contract["source"] == "spec"
    assert contract["spec"] == "native-health"
    assert contract["feature"] == "native-health"


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
            "---\ntype: feature\nschema_version: 2\nslug: broken\ntitle: Broken\ndraft: true\n"
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


def test_cli_evidence_append_and_audit_use_ignored_default(tmp_path: Path) -> None:
    artifact = tmp_path / "result.txt"
    artifact.write_text("verified\n", encoding="utf-8")

    appended = _cli(
        "evidence",
        "append",
        "health-campaign",
        "--requirement",
        "The health command returns a healthy result.",
        "--evidence",
        "Exit code zero and bounded stdout show healthy.",
        "--decision",
        "Keep the current implementation.",
        "--verification",
        f"{sys.executable} check.py passed.",
        "--verdict",
        "VERIFIED",
        "--artifact",
        "result.txt",
        "--output",
        "json",
        cwd=tmp_path,
    )
    audited = _cli(
        "evidence",
        "audit",
        "health-campaign",
        "--output",
        "json",
        cwd=tmp_path,
    )

    assert appended.returncode == 0, appended.stderr
    assert audited.returncode == 0, audited.stderr
    append_payload = json.loads(appended.stdout)
    audit_payload = json.loads(audited.stdout)
    assert append_payload["event"]["sequence"] == 1
    assert append_payload["path"] == ".pkstack/state/evidence/health-campaign/decision-log.jsonl"
    assert audit_payload["event_count"] == 1
    assert not (tmp_path / "Wiki/evidence").exists()


def test_cli_committed_evidence_requires_flag_and_exact_target(tmp_path: Path) -> None:
    result = _cli(
        "evidence",
        "append",
        "review",
        "--requirement",
        "The release is independently reviewed.",
        "--evidence",
        "The review verdict is recorded.",
        "--decision",
        "Hold the release until acceptance.",
        "--verification",
        "Reviewer returned INCONCLUSIVE.",
        "--verdict",
        "INCONCLUSIVE",
        "--target",
        "Wiki/evidence/review/decision-log.jsonl",
        "--output",
        "json",
        cwd=tmp_path,
    )

    assert result.returncode == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["error_type"] == "EvidenceError"
    assert "--committed" in payload["error"]
