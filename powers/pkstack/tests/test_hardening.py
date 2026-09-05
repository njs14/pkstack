from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from contextlib import suppress
from pathlib import Path

import pytest
from feature_fixtures import (
    generate_fixture_cli_feature,
    generate_fixture_feature,
    plant_fixture_feature,
)

from pkstack.bootstrap import bootstrap_project
from pkstack.discovery import discover_repository
from pkstack.doctor import run_doctor
from pkstack.features import (
    FeatureMapError,
    load_feature,
    validate_feature_map,
)
from pkstack.goal import (
    GoalError,
    GoalStore,
    get_goal,
    resolve_contract,
    start_goal,
    verify_goal,
)
from pkstack.paths import WorkspacePathError
from pkstack.runner import CommandRejected, run_command

POWER_ROOT = Path(__file__).resolve().parents[1]


def _copy_power_fixture(destination: Path) -> None:
    for relative in ("src/pkstack", "skills", "dev.kiro", "templates", "docs"):
        shutil.copytree(POWER_ROOT / relative, destination / relative)


def test_bootstrap_rejects_symlink_escape_before_writing(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / ".pkstack").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink"):
        bootstrap_project(project, power_root=POWER_ROOT)

    assert list(outside.iterdir()) == []
    assert not (project / ".kiro").exists()


@pytest.mark.parametrize("link_path", [".kiro", ".kiro/skills", "Wiki/features"])
def test_bootstrap_discovery_rejects_hostile_nested_symlinks_without_disclosure(
    tmp_path: Path,
    link_path: str,
) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    sentinel_name = "external-secret-sentinel.txt"
    sentinel_content = "external sentinel content must remain unread"
    (outside / sentinel_name).write_text(sentinel_content, encoding="utf-8")
    link = project / link_path
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(WorkspacePathError, match="symlink") as bootstrap_error:
        bootstrap_project(project, power_root=POWER_ROOT)
    with pytest.raises(WorkspacePathError, match="symlink") as discovery_error:
        discover_repository(project)

    evidence = f"{bootstrap_error.value}\n{discovery_error.value}"
    assert sentinel_name not in evidence
    assert sentinel_content not in evidence
    assert not (project / ".pkstack" / "bin" / "projectctl").exists()


@pytest.mark.parametrize(
    "missing_asset",
    [
        "src/pkstack/goal.py",
        "skills/pkstack-verified-goal/SKILL.md",
        "templates/project/.kiro/agents/pkstack.json",
    ],
)
def test_bootstrap_rejects_incomplete_power_before_writing(
    tmp_path: Path,
    missing_asset: str,
) -> None:
    power = tmp_path / "power"
    _copy_power_fixture(power)
    (power / missing_asset).unlink()
    target = tmp_path / "target"
    target.mkdir()

    with pytest.raises(ValueError) as exc_info:
        bootstrap_project(target, power_root=power)

    message = str(exc_info.value)
    if missing_asset == "skills/pkstack-verified-goal/SKILL.md":
        assert "PKStack skill catalog mismatch" in message
        assert "missing pkstack-verified-goal" in message
    else:
        assert "required PKStack Power assets are missing" in message
        assert missing_asset in message
    assert list(target.iterdir()) == []


def test_bootstrap_rejects_required_source_asset_symlink_before_writing(
    tmp_path: Path,
) -> None:
    power = tmp_path / "power"
    _copy_power_fixture(power)
    outside = tmp_path / "outside-goal.py"
    sentinel = "external source sentinel must remain unread"
    outside.write_text(sentinel, encoding="utf-8")
    source = power / "src" / "pkstack" / "goal.py"
    source.unlink()
    source.symlink_to(outside)
    target = tmp_path / "target"
    target.mkdir()

    with pytest.raises(WorkspacePathError, match="symlink") as exc_info:
        bootstrap_project(target, power_root=power)

    assert sentinel not in str(exc_info.value)
    assert list(target.iterdir()) == []


def test_bootstrap_rejects_source_package_root_symlink_before_writing(tmp_path: Path) -> None:
    power = tmp_path / "power"
    (power / "src").mkdir(parents=True)
    (power / "src" / "pkstack").symlink_to(
        POWER_ROOT / "src" / "pkstack",
        target_is_directory=True,
    )
    for relative in ("skills", "dev.kiro", "templates"):
        shutil.copytree(POWER_ROOT / relative, power / relative)
    target = tmp_path / "target"
    target.mkdir()

    with pytest.raises(WorkspacePathError, match="symlink"):
        bootstrap_project(target, power_root=power)

    assert list(target.iterdir()) == []


def test_bootstrap_symlink_loop_returns_structured_cli_error(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / ".pkstack").symlink_to(".pkstack", target_is_directory=True)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pkstack.bootstrap",
            "--root",
            str(project),
            "--power-root",
            str(POWER_ROOT),
            "--dry-run",
            "--output",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert payload["ok"] is False
    assert payload["error_type"] == "WorkspacePathError"
    assert "symlink" in payload["error"]
    assert not (project / ".kiro").exists()


@pytest.mark.parametrize("receipt_key", ["../outside", ""])
def test_bootstrap_rejects_traversal_or_empty_receipt_keys_before_writing(
    tmp_path: Path,
    receipt_key: str,
) -> None:
    receipt = tmp_path / ".pkstack" / "bootstrap.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "manager": "pkstack",
                "files": {receipt_key: "0" * 64},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid managed-file hashes"):
        bootstrap_project(tmp_path, power_root=POWER_ROOT)

    assert not (tmp_path / ".pkstack" / "bin" / "projectctl").exists()


def test_forged_receipt_cannot_authorize_automatic_overwrite(tmp_path: Path) -> None:
    foreign = tmp_path / "projectctl"
    foreign.write_text("foreign\n", encoding="utf-8")
    receipt = tmp_path / ".pkstack" / "bootstrap.json"
    receipt.parent.mkdir(parents=True)
    digest = hashlib.sha256(foreign.read_bytes()).hexdigest()
    receipt.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "manager": "pkstack",
                "files": {"projectctl": digest},
            }
        ),
        encoding="utf-8",
    )

    result = bootstrap_project(tmp_path, power_root=POWER_ROOT)

    assert result.ok is False
    assert "projectctl" in result.pending_updates
    assert foreign.read_text(encoding="utf-8") == "foreign\n"
    assert not (tmp_path / ".kiro").exists()


def test_bootstrap_preflights_non_file_conflict_without_partial_install(tmp_path: Path) -> None:
    conflict = tmp_path / ".kiro" / "agents" / "pkstack.json"
    conflict.mkdir(parents=True)

    result = bootstrap_project(tmp_path, power_root=POWER_ROOT)

    assert result.ok is False
    assert ".kiro/agents/pkstack.json" in result.conflicts
    assert not (tmp_path / ".pkstack" / "bin" / "projectctl").exists()


def test_bootstrap_preflights_non_directory_parent_without_partial_install(
    tmp_path: Path,
) -> None:
    (tmp_path / ".kiro").mkdir()
    (tmp_path / ".kiro" / "agents").write_text("occupied\n", encoding="utf-8")

    result = bootstrap_project(tmp_path, power_root=POWER_ROOT)

    assert result.ok is False
    assert ".kiro/agents" in result.conflicts
    assert not (tmp_path / ".pkstack" / "bin" / "projectctl").exists()
    assert not (tmp_path / ".pkstack" / "bootstrap.json").exists()


def test_managed_upgrade_requires_preview_then_explicit_opt_in(tmp_path: Path) -> None:
    power_v2 = tmp_path / "power-v2"
    _copy_power_fixture(power_v2)

    first = bootstrap_project(tmp_path, power_root=POWER_ROOT)
    assert first.ok is True
    managed = tmp_path / ".pkstack" / "projectctl" / "src" / "pkstack" / "__init__.py"
    before = managed.read_bytes()
    source_v2 = power_v2 / "src" / "pkstack" / "__init__.py"
    source_v2.write_bytes(source_v2.read_bytes() + b"\n# v2 fixture\n")

    pending = bootstrap_project(tmp_path, power_root=power_v2)
    assert pending.ok is False
    assert ".pkstack/projectctl/src/pkstack/__init__.py" in pending.pending_updates
    assert managed.read_bytes() == before

    updated = bootstrap_project(tmp_path, power_root=power_v2, update_managed=True)
    assert updated.ok is True
    assert managed.read_bytes() == source_v2.read_bytes()


def test_owned_discovery_refreshes_without_managed_upgrade_gate(tmp_path: Path) -> None:
    first = bootstrap_project(tmp_path, power_root=POWER_ROOT)
    assert first.ok is True

    (tmp_path / "package.json").write_text("{}\n", encoding="utf-8")
    second = bootstrap_project(tmp_path, power_root=POWER_ROOT)

    assert second.ok is True
    assert ".pkstack/discovery.json" in second.updated
    discovery = json.loads((tmp_path / ".pkstack" / "discovery.json").read_text())
    assert discovery["root"] == "."
    assert "okn_available" not in discovery["knowledge"]


def test_retired_managed_asset_is_reported_until_explicitly_removed(tmp_path: Path) -> None:
    power_v1 = tmp_path / "power-v1"
    _copy_power_fixture(power_v1)
    retired = power_v1 / "skills" / "retired" / "SKILL.md"
    retired.parent.mkdir()
    retired.write_text("---\nname: retired\ndescription: Retired.\n---\n", encoding="utf-8")
    parity_path = power_v1 / "docs" / "upstream-skill-parity.json"
    parity = json.loads(parity_path.read_text(encoding="utf-8"))
    parity["pk_only_skills"] = sorted([*parity["pk_only_skills"], "retired"])
    parity["summary"]["shipped_skill_directories"] += 1
    parity_path.write_text(json.dumps(parity, indent=2) + "\n", encoding="utf-8")

    first = bootstrap_project(tmp_path, power_root=power_v1)
    assert first.ok is True
    live = tmp_path / ".kiro" / "skills" / "retired" / "SKILL.md"
    assert live.is_file()

    retired.unlink()
    retired.parent.rmdir()
    parity["pk_only_skills"].remove("retired")
    parity["summary"]["shipped_skill_directories"] -= 1
    parity_path.write_text(json.dumps(parity, indent=2) + "\n", encoding="utf-8")
    blocked = bootstrap_project(tmp_path, power_root=power_v1, update_managed=True)
    assert blocked.ok is False
    assert ".kiro/skills/retired/SKILL.md" in blocked.stale_managed
    receipt = json.loads((tmp_path / ".pkstack" / "bootstrap.json").read_text())
    assert ".kiro/skills/retired/SKILL.md" in receipt["files"]

    live.unlink()
    resolved = bootstrap_project(tmp_path, power_root=power_v1, update_managed=True)
    assert resolved.ok is True
    receipt = json.loads((tmp_path / ".pkstack" / "bootstrap.json").read_text())
    assert ".kiro/skills/retired/SKILL.md" not in receipt["files"]


@pytest.mark.parametrize(
    "frontmatter",
    [
        "slug: []",
        "slug: health",
        "draft: 'false'",
        "verification: []",
        "verification:\n  command: []",
        "related: ''",
    ],
)
def test_feature_loader_rejects_falsey_or_coerced_schema_values(
    tmp_path: Path,
    frontmatter: str,
) -> None:
    path = tmp_path / "Wiki" / "features" / "health.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"---\ntype: feature\ntitle: Health\n{frontmatter}\n---\n\n"
        "## User behavior\n\nCheck health.\n\n## Expected path\n\nCommand -> result.\n",
        encoding="utf-8",
    )

    with pytest.raises(FeatureMapError):
        load_feature(path, root=tmp_path)


def test_ready_generation_proves_before_write_and_pure_validation_runs_first(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    failing = tmp_path / "fail.py"
    failing.write_text("raise SystemExit(7)\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        generate_fixture_cli_feature(
            "new-feature",
            title="New feature",
            behavior="A behavior.",
            expected_path="Input -> result",
            command=f"{sys.executable} fail.py",
            ready=True,
            root=tmp_path,
            output="json",
        )
    assert json.loads(capsys.readouterr().out)["created"] is False
    assert not (tmp_path / "Wiki" / "features" / "new-feature.md").exists()

    side_effect = tmp_path / "proof-ran"
    proof = tmp_path / "proof.py"
    proof.write_text("from pathlib import Path\nPath('proof-ran').write_text('yes')\n")
    with pytest.raises(SystemExit, match="2"):
        generate_fixture_cli_feature(
            "invalid",
            title="",
            behavior="A behavior.",
            expected_path="Input -> result",
            command=f"{sys.executable} proof.py",
            ready=True,
            root=tmp_path,
            output="json",
        )
    capsys.readouterr()
    assert not side_effect.exists()


def test_rejected_overwrite_never_runs_ready_verifier(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    generate_fixture_feature(
        tmp_path,
        "existing",
        title="Existing",
        behavior="A behavior.",
        expected_path="Input -> result",
        command=None,
    )
    proof = tmp_path / "proof.py"
    proof.write_text("from pathlib import Path\nPath('proof-ran').write_text('yes')\n")

    with pytest.raises(SystemExit, match="2"):
        generate_fixture_cli_feature(
            "existing",
            title="Existing",
            behavior="A behavior.",
            expected_path="Input -> result",
            command=f"{sys.executable} proof.py",
            ready=True,
            root=tmp_path,
            output="json",
        )
    capsys.readouterr()
    assert not (tmp_path / "proof-ran").exists()


@pytest.mark.parametrize("spec", ["../hooks", "../../outside", "/tmp/outside", "a/b"])
def test_spec_bridge_rejects_traversal_names(tmp_path: Path, spec: str) -> None:
    with pytest.raises(GoalError, match="path separators or traversal"):
        resolve_contract(tmp_path, spec=spec)


def test_goal_state_rejects_tampering_and_impossible_terminal_status(tmp_path: Path) -> None:
    checker = tmp_path / "check.py"
    checker.write_text("pass\n", encoding="utf-8")
    start_goal(tmp_path, "Prove it", command=f"{sys.executable} check.py")
    store = GoalStore(tmp_path)
    payload = json.loads(store.path.read_text(encoding="utf-8"))
    payload["contract"]["argv"] = ["false"]
    store.path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(GoalError, match="digest"):
        get_goal(tmp_path)

    start_root = tmp_path / "impossible"
    start_root.mkdir()
    (start_root / "check.py").write_text("pass\n", encoding="utf-8")
    start_goal(start_root, "Prove it", command=f"{sys.executable} check.py")
    impossible = GoalStore(start_root)
    payload = json.loads(impossible.path.read_text(encoding="utf-8"))
    payload["status"] = "passed"
    impossible.path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(GoalError, match="lacks passing verifier evidence"):
        get_goal(start_root)


def test_goal_status_remains_responsive_while_verifier_runs(tmp_path: Path) -> None:
    checker = tmp_path / "slow.py"
    checker.write_text("import time\ntime.sleep(0.5)\n", encoding="utf-8")
    start_goal(tmp_path, "Wait for proof", command=f"{sys.executable} slow.py")
    thread = threading.Thread(target=verify_goal, args=(tmp_path,))
    thread.start()
    time.sleep(0.1)

    started = time.monotonic()
    state = get_goal(tmp_path)
    elapsed = time.monotonic() - started
    thread.join(timeout=2)

    assert elapsed < 0.25
    assert state.status == "active"
    assert not thread.is_alive()
    assert get_goal(tmp_path).status == "passed"


@pytest.mark.parametrize(
    "command",
    [
        "find . -delete",
        "uv run rm -rf build",
        "kubectl apply -f manifest.yaml",
        "docker rm test-container",
        f"{sys.executable} --version",
    ],
)
def test_goal_start_enforces_verifier_policy_before_persisting_state(
    tmp_path: Path,
    command: str,
) -> None:
    with pytest.raises(CommandRejected):
        start_goal(tmp_path, "Unsafe verifier", command=command)

    assert not GoalStore(tmp_path).path.exists()


def test_feature_validation_reports_policy_rejection(tmp_path: Path) -> None:
    plant_fixture_feature(
        tmp_path,
        "unsafe-proof",
        title="Unsafe proof",
        behavior="A maintainer verifies behavior.",
        expected_path="Command to result.",
        command=["oc", "delete", "pod", "example"],
    )

    result = validate_feature_map(tmp_path)

    assert result["ok"] is False
    assert result["feature_count"] == 1
    assert any("rejected verification command" in error for error in result["errors"])


def test_runner_kills_descendants_and_decodes_invalid_utf8(tmp_path: Path) -> None:
    detached = tmp_path / "detached.py"
    detached.write_text(
        "import subprocess, sys\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], "
        "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        "open('child.pid', 'w').write(str(child.pid))\n",
        encoding="utf-8",
    )
    result = run_command([sys.executable, "detached.py"], root=tmp_path, timeout_seconds=1)
    child_pid = int((tmp_path / "child.pid").read_text())
    time.sleep(0.05)
    try:
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
    finally:
        with suppress(ProcessLookupError):
            os.kill(child_pid, signal.SIGKILL)
    assert result.passed is True

    invalid = tmp_path / "invalid.py"
    invalid.write_text("import os\nos.write(1, b'\\xff')\n", encoding="utf-8")
    decoded = run_command([sys.executable, "invalid.py"], root=tmp_path)
    assert decoded.passed is True
    assert "\ufffd" in decoded.stdout


def test_goal_rejects_relative_script_escape_before_state_is_created(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("print('outside')\n", encoding="utf-8")

    with pytest.raises(CommandRejected, match="path operands"):
        start_goal(
            project,
            "Do not execute outside the project",
            command=f"{sys.executable} ../outside.py",
        )

    assert not (project / ".pkstack" / "state" / "goal.json").exists()

    link = project / "linked.py"
    link.symlink_to(outside)
    with pytest.raises(CommandRejected, match="path operands"):
        start_goal(
            project,
            "Do not follow an outside script symlink",
            command=f"{sys.executable} linked.py",
        )

    assert not (project / ".pkstack" / "state" / "goal.json").exists()


def test_outside_absolute_executable_is_rejected_before_contract_persistence(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside-verifier"
    outside.write_text('#!/bin/sh\ntest -d "$PWD"\n', encoding="utf-8")
    outside.chmod(0o755)

    with pytest.raises(CommandRejected, match="path operands"):
        start_goal(project, "Reject outside executable", command=str(outside))
    assert not (project / ".pkstack" / "state" / "goal.json").exists()

    with pytest.raises(CommandRejected, match="path operands"):
        generate_fixture_feature(
            project,
            "outside-proof",
            title="Outside proof",
            behavior="A caller observes a bounded proof.",
            expected_path="Project to verifier",
            command=[str(outside)],
            draft=False,
        )
    assert not (project / "Wiki" / "features" / "outside-proof.md").exists()

    plant_fixture_feature(
        project,
        "planted-proof",
        title="Planted proof",
        behavior="A caller observes a bounded proof.",
        expected_path="Project to verifier.",
        command=[str(outside)],
    )

    validation = validate_feature_map(project)
    assert validation["ok"] is False
    assert any(
        "planted-proof.md: rejected verification command" in error for error in validation["errors"]
    )

    selected_test = shutil.which("test")
    assert selected_test is not None
    (project / "proof.txt").write_text("present\n", encoding="utf-8")
    accepted = start_goal(
        project,
        "Allow PATH-selected executable",
        command=f"{selected_test} -f proof.txt",
    )
    assert accepted.status == "active"


def test_doctor_detects_missing_assets_runtime_drift_and_corrupt_goal(tmp_path: Path) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok is True
    (tmp_path / ".kiro" / "agents" / "pkstack-architect.json").unlink()
    (tmp_path / ".kiro" / "hooks" / "pkstack-session.json").unlink()
    internal = tmp_path / ".pkstack" / "bin" / "projectctl"
    internal.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    state = tmp_path / ".pkstack" / "state" / "goal.json"
    state.parent.mkdir(parents=True)
    state.write_text("{}", encoding="utf-8")

    result = run_doctor(tmp_path)
    checks = {check["name"]: check for check in result["checks"]}

    assert result["ok"] is False
    assert checks["architect-agent"]["status"] == "fail"
    assert checks["session-hook"]["status"] == "fail"
    assert checks["projectctl-runtime-integrity"]["status"] == "fail"
    assert checks["goal-state"]["status"] == "fail"


def test_hostile_wiki_symlink_returns_structured_cli_json(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / "Wiki").symlink_to(outside, target_is_directory=True)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pkstack",
            "feature",
            "validate",
            "--root",
            str(project),
            "--output",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert json.loads(completed.stdout)["ok"] is False
    assert "Traceback" not in completed.stderr
