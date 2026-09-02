from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pstack_kiro.bootstrap import bootstrap_project
from pstack_kiro.doctor import (
    _command_check,
    _kiro_agent_check,
    _runtime_state_ignored,
    _validate_kiro_json,
    run_doctor,
)

POWER_ROOT = Path(__file__).resolve().parents[1]


def _without_optional_doctor_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pstack_kiro.doctor.shutil.which",
        lambda name: "/tools/uv" if name == "uv" else None,
    )


def test_doctor_reports_complete_bootstrap_and_optional_tools(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bootstrap_project(tmp_path, power_root=POWER_ROOT)
    monkeypatch.setattr(
        "pstack_kiro.doctor.shutil.which",
        lambda name: f"/tools/{name}" if name in {"uv", "kiro-cli"} else None,
    )

    result = run_doctor(tmp_path)

    assert result["ok"] is True
    assert result["summary"]["fail"] == 0
    checks = {check["name"]: check for check in result["checks"]}
    receipt = json.loads((tmp_path / ".pstack" / "bootstrap.json").read_text())
    assert checks["okn"]["status"] == "warn"
    assert checks["bootstrap-receipt-integrity"] == {
        "name": "bootstrap-receipt-integrity",
        "status": "pass",
        "message": f"all {len(receipt['files'])} receipt-managed files match recorded hashes",
        "remediation": None,
    }


@pytest.mark.parametrize(
    ("relative", "mutation", "message"),
    [
        (
            ".pstack/projectctl/src/pstack_kiro/models.py",
            "drift",
            "hash mismatch (1): .pstack/projectctl/src/pstack_kiro/models.py",
        ),
        (
            ".pstack/projectctl/skills/setup-pstack/SKILL.md",
            "missing",
            "missing or non-file (1): .pstack/projectctl/skills/setup-pstack/SKILL.md",
        ),
    ],
)
def test_doctor_receipt_integrity_detects_cached_drift_and_missing_owned_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative: str,
    mutation: str,
    message: str,
) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok is True
    managed = tmp_path / relative
    if mutation == "drift":
        managed.write_bytes(managed.read_bytes() + b"\n# receipt drift probe\n")
    else:
        managed.unlink()
    receipt = tmp_path / ".pstack" / "bootstrap.json"
    receipt_before = receipt.read_bytes()
    _without_optional_doctor_tools(monkeypatch)

    result = run_doctor(tmp_path)
    checks = {check["name"]: check for check in result["checks"]}

    assert result["ok"] is False
    assert result["summary"]["fail"] == 1
    assert checks["bootstrap-receipt-integrity"]["status"] == "fail"
    assert message in checks["bootstrap-receipt-integrity"]["message"]
    assert receipt.read_bytes() == receipt_before
    assert managed.exists() is (mutation == "drift")


def test_doctor_receipt_integrity_detects_identical_live_and_cached_permission_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok is True
    live = tmp_path / ".kiro" / "agents" / "pstack.json"
    cached = (
        tmp_path
        / ".pstack"
        / "projectctl"
        / "templates"
        / "project"
        / ".kiro"
        / "agents"
        / "pstack.json"
    )
    document = json.loads(live.read_text(encoding="utf-8"))
    document["description"] = "Altered but still schema-valid permission profile"
    altered = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    live.write_bytes(altered)
    cached.write_bytes(altered)
    receipt = tmp_path / ".pstack" / "bootstrap.json"
    receipt_before = receipt.read_bytes()
    _without_optional_doctor_tools(monkeypatch)

    result = run_doctor(tmp_path)
    checks = {check["name"]: check for check in result["checks"]}

    assert result["ok"] is False
    assert result["summary"]["fail"] == 1
    assert checks["pstack-agent-managed-integrity"]["status"] == "pass"
    receipt_check = checks["bootstrap-receipt-integrity"]
    assert receipt_check["status"] == "fail"
    assert "hash mismatch (2)" in receipt_check["message"]
    assert ".kiro/agents/pstack.json" in receipt_check["message"]
    assert (
        ".pstack/projectctl/templates/project/.kiro/agents/pstack.json" in receipt_check["message"]
    )
    assert receipt.read_bytes() == receipt_before
    assert live.read_bytes() == cached.read_bytes() == altered


@pytest.mark.parametrize(
    "replacement",
    [
        None,
        "{broken",
        json.dumps({"schema_version": 99, "manager": "pstack-kiro", "files": {}}),
        json.dumps({"schema_version": 1, "manager": "pstack-kiro", "files": {}}),
        json.dumps(
            {
                "schema_version": 1,
                "manager": "pstack-kiro",
                "files": {"../escape": "0" * 64},
            }
        ),
        json.dumps(
            {
                "schema_version": 1,
                "manager": "pstack-kiro",
                "files": {"projectctl": "not-a-sha256"},
            }
        ),
    ],
    ids=("missing", "malformed-json", "wrong-schema", "empty-files", "unsafe-key", "bad-hash"),
)
def test_doctor_receipt_integrity_returns_structured_failure_for_invalid_receipts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replacement: str | None,
) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok is True
    receipt = tmp_path / ".pstack" / "bootstrap.json"
    if replacement is None:
        receipt.unlink()
    else:
        receipt.write_text(replacement, encoding="utf-8")
    _without_optional_doctor_tools(monkeypatch)

    result = run_doctor(tmp_path)
    checks = {check["name"]: check for check in result["checks"]}

    assert result["ok"] is False
    assert result["summary"]["fail"] == 1
    receipt_check = checks["bootstrap-receipt-integrity"]
    assert receipt_check["status"] == "fail"
    assert receipt_check["message"].startswith("unable to validate bootstrap ownership receipt:")
    if replacement is None:
        assert not receipt.exists()
    else:
        assert receipt.read_text(encoding="utf-8") == replacement


def test_doctor_receipt_integrity_rejects_symlinked_receipt_without_disclosure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok is True
    outside = tmp_path.parent / f"{tmp_path.name}-outside-receipt"
    sentinel = "external receipt sentinel must remain unread"
    outside.write_text(sentinel, encoding="utf-8")
    receipt = tmp_path / ".pstack" / "bootstrap.json"
    receipt.unlink()
    receipt.symlink_to(outside)
    _without_optional_doctor_tools(monkeypatch)

    result = run_doctor(tmp_path)

    assert result["ok"] is False
    assert receipt.is_symlink()
    assert outside.read_text(encoding="utf-8") == sentinel
    assert sentinel not in json.dumps(result)
    receipt_check = next(
        check for check in result["checks"] if check["name"] == "bootstrap-receipt-integrity"
    )
    assert receipt_check["status"] == "fail"
    assert "symlink" in receipt_check["message"]


def test_doctor_receipt_integrity_rejects_symlinked_managed_path_without_disclosure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok is True
    outside = tmp_path.parent / f"{tmp_path.name}-outside-managed"
    sentinel = "external managed-file sentinel must remain unread"
    outside.write_text(sentinel, encoding="utf-8")
    managed = tmp_path / ".pstack" / "projectctl" / "src" / "pstack_kiro" / "models.py"
    managed.unlink()
    managed.symlink_to(outside)
    _without_optional_doctor_tools(monkeypatch)

    result = run_doctor(tmp_path)
    checks = {check["name"]: check for check in result["checks"]}

    assert result["ok"] is False
    assert checks["bootstrap-receipt-integrity"]["status"] == "fail"
    assert "unsafe or unreadable (1)" in checks["bootstrap-receipt-integrity"]["message"]
    assert sentinel not in json.dumps(result)
    assert managed.is_symlink()
    assert outside.read_text(encoding="utf-8") == sentinel


def test_bootstrapped_controller_doctor_exits_nonzero_for_cached_source_drift(
    tmp_path: Path,
) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok is True
    cached = tmp_path / ".pstack" / "projectctl" / "src" / "pstack_kiro" / "models.py"
    cached.write_bytes(cached.read_bytes() + b"\n# receipt drift probe\n")

    completed = subprocess.run(
        [str(tmp_path / ".pstack" / "bin" / "projectctl"), "doctor", "--output", "json"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(completed.stdout)
    checks = {check["name"]: check for check in payload["checks"]}

    assert completed.returncode == 1
    assert completed.stderr == ""
    assert payload["ok"] is False
    assert checks["bootstrap-receipt-integrity"]["status"] == "fail"
    assert "hash mismatch (1)" in checks["bootstrap-receipt-integrity"]["message"]


def test_doctor_detects_missing_and_invalid_assets(tmp_path: Path, monkeypatch) -> None:
    bootstrap_project(tmp_path, power_root=POWER_ROOT)
    (tmp_path / ".kiro" / "agents" / "pstack.json").write_text("{broken", encoding="utf-8")
    (tmp_path / ".kiro" / "agents" / "pstack-reviewer.json").unlink()
    monkeypatch.setattr("pstack_kiro.doctor.shutil.which", lambda _name: None)

    result = run_doctor(tmp_path)

    assert result["ok"] is False
    checks = {check["name"]: check for check in result["checks"]}
    assert checks["uv"]["status"] == "fail"
    assert checks["reviewer-agent"]["status"] == "fail"
    assert checks["pstack-agent-json"]["status"] == "fail"


def test_runtime_ignore_check_uses_git_when_present(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / ".git").mkdir()

    class Completed:
        returncode = 0

    monkeypatch.setattr("pstack_kiro.doctor.subprocess.run", lambda *args, **kwargs: Completed())

    assert _runtime_state_ignored(tmp_path).status == "pass"
    assert _command_check("definitely-missing-pstack-tool", required=False).status == "warn"


@pytest.mark.parametrize(
    "impostor",
    ["# .pstack/state/\n", "backup/.pstack/state/\n", ".pstack/state/cache\n"],
)
def test_runtime_ignore_check_rejects_impostor_match_without_git(
    tmp_path: Path,
    impostor: str,
) -> None:
    (tmp_path / ".gitignore").write_text(impostor, encoding="utf-8")

    assert _runtime_state_ignored(tmp_path).status == "fail"


def test_bootstrap_rejects_invalid_receipt_and_dry_run_is_non_mutating(tmp_path: Path) -> None:
    receipt = tmp_path / ".pstack" / "bootstrap.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({"schema_version": 99, "manager": "other"}), encoding="utf-8")

    with pytest.raises(ValueError, match="unrecognized PK-Stack ownership receipt"):
        bootstrap_project(tmp_path, power_root=POWER_ROOT, dry_run=True)
    assert not (tmp_path / "projectctl").exists()


@pytest.mark.parametrize(
    ("parent", "document", "message"),
    [
        ("agents", [], "top level"),
        ("agents", {"name": "wrong", "tools": ["read"]}, "name must match"),
        ("agents", {"name": "sample", "tools": []}, "tools must be"),
        (
            "agents",
            {"name": "sample", "tools": ["read"], "permissions": {}},
            "permissions.rules",
        ),
        ("hooks", {"version": "v2", "hooks": [{}]}, "version must be"),
        ("hooks", {"version": "v1", "hooks": []}, "hooks must be"),
        ("hooks", {"version": "v1", "hooks": [{}]}, "requires trigger and action"),
    ],
)
def test_kiro_json_schema_error_boundaries(
    tmp_path: Path,
    parent: str,
    document: object,
    message: str,
) -> None:
    path = tmp_path / parent / "sample.json"

    with pytest.raises(ValueError, match=message):
        _validate_kiro_json(path, document)


def test_doctor_handles_hostile_paths_and_feature_discovery_without_disclosure(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    sentinel = "external doctor sentinel must remain unread"
    (outside / "sentinel.txt").write_text(sentinel, encoding="utf-8")
    (project / ".pstack").symlink_to(outside, target_is_directory=True)
    (project / "projectctl").mkdir()
    (project / "Wiki").mkdir()
    (project / "Wiki" / "features").symlink_to(outside, target_is_directory=True)

    result = run_doctor(project)
    checks = {check["name"]: check for check in result["checks"]}

    assert result["ok"] is False
    assert checks["projectctl"]["status"] == "fail"
    assert checks["root-projectctl"]["status"] == "warn"
    assert checks["feature-map"]["status"] == "fail"
    assert checks["goal-state"]["status"] == "fail"
    assert sentinel not in json.dumps(result)


def test_doctor_reports_runtime_ignore_and_kiro_validation_execution_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / ".git").mkdir()

    def fail_run(*_args: object, **_kwargs: object) -> object:
        raise OSError("execution blocked")

    monkeypatch.setattr("pstack_kiro.doctor.subprocess.run", fail_run)

    assert _runtime_state_ignored(tmp_path).status == "fail"
    assert _kiro_agent_check("kiro-cli", tmp_path / "agent.json", "agent").status == "fail"

    timeout = subprocess.TimeoutExpired("kiro-cli", 30)
    monkeypatch.setattr(
        "pstack_kiro.doctor.subprocess.run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(timeout),
    )
    assert _kiro_agent_check("kiro-cli", tmp_path / "agent.json", "agent").status == "fail"
