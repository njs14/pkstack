from __future__ import annotations

import json
import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from pkstack import __version__, launcher
from pkstack.bootstrap import INTERNAL_WRAPPER, bootstrap_project

POWER_ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def pristine_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Bootstrap one project per module; mutating tests copy it."""

    target = tmp_path_factory.mktemp("pristine") / "project"
    target.mkdir()
    assert bootstrap_project(target, power_root=POWER_ROOT).ok is True
    return target


@pytest.fixture
def project(pristine_project: Path, tmp_path: Path) -> Path:
    target = tmp_path / "project"
    shutil.copytree(pristine_project, target, symlinks=True)
    return target


@pytest.fixture
def delegation(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    """Capture the delegation instead of replacing this test process."""

    captured: dict[str, Any] = {}
    real_chdir = os.chdir
    original_cwd = os.getcwd()

    def fake_execve(path: str, args: list[str], env: dict[str, str]) -> None:
        captured["path"] = path
        captured["args"] = list(args)
        captured["env"] = dict(env)

    def fake_chdir(path: Any) -> None:
        captured["cwd"] = str(path)
        real_chdir(path)

    monkeypatch.setattr(os, "execve", fake_execve)
    monkeypatch.setattr(os, "chdir", fake_chdir)
    yield captured
    real_chdir(original_cwd)


def _run(argv: list[str]) -> None:
    launcher.main(argv)


def _expect_failure(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        launcher.main(argv)
    assert exit_info.value.code == 2


def _error_payload(argv: list[str], capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    _expect_failure(argv)
    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert set(payload) == {"ok", "error", "error_type"}
    assert payload["ok"] is False
    return payload


def test_help_documents_project_selection_versions_and_uvx(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(["--help"])
    help_text = capsys.readouterr().out
    _run([])
    assert capsys.readouterr().out == help_text
    assert '--from "$PKSTACK_PACKAGE" pkstack' in help_text
    assert "uvx pkstack" not in help_text
    assert "--project PATH" in help_text
    assert "pkstack --version" in help_text
    assert "pkstack version" in help_text
    assert "not a signature" in help_text


def test_launcher_version_reports_the_package_and_points_at_the_controller(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run(["--version"])
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == f"pkstack {__version__}"
    assert "pkstack version" in lines[1]


def test_version_command_is_forwarded_rather_than_answered_locally(
    project: Path, delegation: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    _run(["--project", str(project), "version", "--output", "json"])
    assert capsys.readouterr().out == ""
    assert delegation["args"][1:] == ["version", "--output", "json"]


def test_unknown_launcher_option_fails_with_text_on_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _expect_failure(["--verbose", "doctor"])
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unknown launcher option" in captured.err


def test_parse_failure_stays_structured_for_both_json_forms(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for tokens in (
        ["doctor", "--root", "/tmp", "--output", "json"],
        ["doctor", "--root=/tmp", "--output=json"],
    ):
        payload = _error_payload(tokens, capsys)
        assert payload["error_type"] == "LauncherError"
        assert "--project" in payload["error"]


def test_project_default_is_exactly_cwd_without_ancestor_search(
    project: Path, delegation: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(project)
    _run(["doctor"])
    assert delegation["cwd"] == str(project)

    child = project / "nested" / "deeper"
    child.mkdir(parents=True)
    monkeypatch.chdir(child)
    delegation.clear()
    with pytest.raises(SystemExit):
        launcher.main(["doctor"])
    assert delegation == {}


def test_project_paths_with_spaces_are_selected_verbatim(
    pristine_project: Path, tmp_path: Path, delegation: dict[str, Any]
) -> None:
    spaced = tmp_path / "a project dir"
    shutil.copytree(pristine_project, spaced, symlinks=True)
    _run(["--project", str(spaced), "doctor"])
    assert delegation["cwd"] == str(spaced)
    assert delegation["path"] == str(spaced / ".pkstack" / "bin" / "projectctl")

    delegation.clear()
    _run([f"--project={spaced}", "goal", "status"])
    assert delegation["args"][1:] == ["goal", "status"]


def test_missing_project_directory_is_reported_and_never_created(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    absent = tmp_path / "absent"
    payload = _error_payload(["--project", str(absent), "doctor", "--output", "json"], capsys)
    assert "never creates it" in payload["error"]
    assert not absent.exists()

    _expect_failure(["--project", str(absent), "setup"])
    capsys.readouterr()
    assert not absent.exists()


def test_forwarded_root_is_rejected_before_delegation(
    project: Path, delegation: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    for tokens in (["doctor", "--root", str(project)], ["doctor", f"--root={project}"]):
        _expect_failure([*tokens])
        assert "--project" in capsys.readouterr().err
    assert delegation == {}


def test_misplaced_project_after_the_command_is_rejected(
    project: Path, delegation: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    _expect_failure(["doctor", "--project", str(project)])
    assert "must come before the command" in capsys.readouterr().err
    assert delegation == {}


def test_root_inside_an_option_value_or_after_a_terminator_is_forwarded(
    project: Path, delegation: dict[str, Any]
) -> None:
    verifier = "pytest tests --root ./fixtures"
    _run(["--project", str(project), "goal", "start", "Check", "--command", verifier])
    assert delegation["args"][1:] == ["goal", "start", "Check", "--command", verifier]

    delegation.clear()
    _run(["--project", str(project), "feature", "verify", "slug", "--", "--root", "x"])
    assert delegation["args"][1:] == ["feature", "verify", "slug", "--", "--root", "x"]


def test_unknown_forwarded_command_is_delegated_unchanged(
    project: Path, delegation: dict[str, Any]
) -> None:
    _run(["--project", str(project), "not-a-command", "--output", "json"])
    assert delegation["args"][1:] == ["not-a-command", "--output", "json"]


def test_execve_uses_the_exact_controller_argv_and_caller_environment(
    project: Path, delegation: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VIRTUAL_ENV", "/caller/venv")
    monkeypatch.setenv("PYTHONPATH", "/caller/pythonpath")
    monkeypatch.setenv("UV_PKSTACK_SENTINEL", "preserved")
    wrapper = project / ".pkstack" / "bin" / "projectctl"

    _run(["--project", str(project), "feature", "list", "--output", "json"])

    assert delegation["path"] == str(wrapper)
    assert delegation["args"] == [str(wrapper), "feature", "list", "--output", "json"]
    assert delegation["cwd"] == str(project)
    assert delegation["env"]["VIRTUAL_ENV"] == "/caller/venv"
    assert delegation["env"]["PYTHONPATH"] == "/caller/pythonpath"
    assert delegation["env"]["UV_PKSTACK_SENTINEL"] == "preserved"


def test_delegation_never_upgrades_or_writes_managed_files(
    project: Path, delegation: dict[str, Any]
) -> None:
    before = {
        path.relative_to(project).as_posix(): path.read_bytes()
        for path in sorted(project.rglob("*"))
        if path.is_file()
    }
    _run(["--project", str(project), "doctor"])
    after = {
        path.relative_to(project).as_posix(): path.read_bytes()
        for path in sorted(project.rglob("*"))
        if path.is_file()
    }
    assert after == before
    assert delegation["args"][1:] == ["doctor"]


@pytest.mark.parametrize(
    ("tokens", "expected"),
    [
        (["setup", "--root", "/tmp"], "does not accept --root"),
        (["setup", "--root=/tmp"], "does not accept --root"),
        (["setup", "--power-root", "/tmp"], "--power-root is not accepted"),
        (["setup", "--update-managed"], "pkstack upgrade"),
        (["upgrade", "--update-managed"], "already replaces"),
        (["setup", "--force"], "unknown option"),
        (["setup", "extra"], "no positional arguments"),
        (["setup", "--output", "yaml"], "accepts json or text"),
        (["setup", "--output"], "requires json or text"),
    ],
)
def test_setup_and_upgrade_argument_boundaries(
    project: Path, tokens: list[str], expected: str, capsys: pytest.CaptureFixture[str]
) -> None:
    _expect_failure(["--project", str(project), *tokens])
    assert expected in capsys.readouterr().err


def test_setup_and_upgrade_use_wheel_assets_and_the_selected_root(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(launcher, "bootstrap_main", lambda argv: calls.append(list(argv)))

    _run(["--project", str(project), "setup", "--dry-run", "--output", "json"])
    _run(["--project", str(project), "upgrade", "--output=text"])

    assert calls[0] == ["--root", str(project), "--output", "json", "--dry-run"]
    assert calls[1] == ["--root", str(project), "--output", "text", "--update-managed"]
    assert not any("--power-root" in call for call in calls)


def test_setup_runs_the_reviewed_bootstrap_end_to_end(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "fresh"
    target.mkdir()
    _run(["--project", str(target), "setup", "--output", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["root"] == str(target)
    assert (target / ".pkstack" / "bin" / "projectctl").read_text() == INTERNAL_WRAPPER


def test_missing_altered_and_symlinked_controllers_fail_before_delegation(
    project: Path, delegation: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    wrapper = project / ".pkstack" / "bin" / "projectctl"
    original = wrapper.read_bytes()

    wrapper.unlink()
    payload = _error_payload(["--project", str(project), "doctor", "--output=json"], capsys)
    assert "no PKStack controller" in payload["error"]

    wrapper.write_bytes(original + b"# edited\n")
    wrapper.chmod(0o755)
    payload = _error_payload(["--project", str(project), "doctor", "--output=json"], capsys)
    assert "differs from the reviewed wrapper" in payload["error"]

    wrapper.unlink()
    elsewhere = project / "elsewhere-projectctl"
    elsewhere.write_bytes(original)
    elsewhere.chmod(0o755)
    wrapper.symlink_to(elsewhere)
    payload = _error_payload(["--project", str(project), "doctor", "--output=json"], capsys)
    assert "symlink" in payload["error"]

    wrapper.unlink()
    wrapper.write_bytes(original)
    wrapper.chmod(0o644)
    payload = _error_payload(["--project", str(project), "doctor", "--output=json"], capsys)
    assert "not executable" in payload["error"]

    assert delegation == {}


def test_receipt_membership_and_runtime_integrity_are_required(
    project: Path, delegation: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    receipt_path = project / ".pkstack" / "bootstrap.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    reduced = dict(receipt)
    reduced["files"] = {
        key: value
        for key, value in receipt["files"].items()
        if key != ".pkstack/projectctl/uv.lock"
    }
    receipt_path.write_text(json.dumps(reduced, indent=2, sort_keys=True), encoding="utf-8")
    payload = _error_payload(["--project", str(project), "doctor", "--output=json"], capsys)
    assert "does not record the controller runtime" in payload["error"]
    assert ".pkstack/projectctl/uv.lock" in payload["error"]

    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    controller_module = project / ".pkstack" / "projectctl" / "src" / "pkstack" / "cli.py"
    controller_module.write_text("raise SystemExit(0)\n", encoding="utf-8")
    payload = _error_payload(["--project", str(project), "doctor", "--output=json"], capsys)
    assert ".pkstack/projectctl/src/pkstack/cli.py" in payload["error"]

    receipt_path.unlink()
    payload = _error_payload(["--project", str(project), "doctor", "--output=json"], capsys)
    assert "receipt" in payload["error"]
    assert delegation == {}


def test_edited_unrelated_managed_file_does_not_block_delegation(
    project: Path, delegation: dict[str, Any]
) -> None:
    skill = project / ".kiro" / "skills" / "pkstack" / "SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8") + "\nLocal note.\n", encoding="utf-8")
    _run(["--project", str(project), "doctor", "--output", "json"])
    assert delegation["args"][1:] == ["doctor", "--output", "json"]


def _own_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    tool_bin = tmp_path / "tool-env" / "bin"
    tool_bin.mkdir(parents=True)
    monkeypatch.setattr(launcher.sys, "prefix", str(tmp_path / "tool-env"))
    monkeypatch.setattr(launcher.sys, "base_prefix", "/usr")
    monkeypatch.setattr(launcher.sys, "executable", str(tool_bin / "python"))
    return tool_bin


def test_only_the_leading_launcher_bin_entry_is_removed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    tool_bin = _own_environment(monkeypatch, tmp_path)
    caller_path = os.pathsep.join([str(tool_bin), "/usr/local/bin", "/usr/bin", str(tool_bin), ""])
    env = launcher.delegated_environment({"PATH": caller_path, "VIRTUAL_ENV": "/caller/venv"})
    assert env["PATH"] == os.pathsep.join(["/usr/local/bin", "/usr/bin", str(tool_bin), ""])
    assert env["VIRTUAL_ENV"] == "/caller/venv"


def test_foreign_leading_path_entry_and_missing_path_are_preserved(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _own_environment(monkeypatch, tmp_path)
    unchanged = os.pathsep.join(["/opt/tools/bin", "/usr/bin"])
    assert launcher.delegated_environment({"PATH": unchanged})["PATH"] == unchanged
    assert "PATH" not in launcher.delegated_environment({"HOME": "/home/user"})


def test_a_base_interpreter_launcher_never_strips_a_system_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    tool_bin = _own_environment(monkeypatch, tmp_path)
    monkeypatch.setattr(launcher.sys, "base_prefix", launcher.sys.prefix)
    caller_path = os.pathsep.join([str(tool_bin), "/usr/bin"])
    assert launcher.delegated_environment({"PATH": caller_path})["PATH"] == caller_path


@pytest.mark.parametrize(
    "tokens", [["--project", ""], ["--project="], ["--project", "--output", "json"]]
)
def test_empty_or_missing_project_value_does_not_select_cwd(
    tokens: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    payload = _error_payload([*tokens, "doctor", "--output=json"], capsys)
    assert "requires" in payload["error"]


def test_adjacent_caller_path_entry_is_not_removed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    tool_bin = _own_environment(monkeypatch, tmp_path)
    original = os.pathsep.join([str(tool_bin), str(tool_bin), "/usr/bin"])
    assert launcher.delegated_environment({"PATH": original})["PATH"] == os.pathsep.join(
        [str(tool_bin), "/usr/bin"]
    )


def test_exec_failure_preserves_structured_error_contract(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(project)

    def failed_exec(*args: Any) -> None:
        raise PermissionError("controller became unavailable")

    monkeypatch.setattr(os, "execve", failed_exec)
    payload = _error_payload(["doctor", "--output=json"], capsys)
    assert payload["error_type"] == "PermissionError"
    assert "controller became unavailable" in payload["error"]
