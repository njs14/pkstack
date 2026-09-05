from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pkstack.bootstrap import bootstrap_project
from pkstack.doctor import (
    _command_check,
    _kiro_agent_check,
    _kiro_agent_discovery_check,
    _parse_workspace_agent_rows,
    _runtime_state_ignored,
    _validate_kiro_json,
    run_doctor,
)

POWER_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = POWER_ROOT.parents[1]


def _agent_list_output(names: list[str], *, ansi: bool = False) -> str:
    reset = "\x1b[m" if ansi else ""
    rows = "\n".join(f"  {name:<30} {reset}Workspace{reset}     test profile" for name in names)
    return (
        f"{reset}Workspace: {reset}/tmp/project/.kiro/agents\n"
        f"{reset}Global:    {reset}/tmp/home/.kiro/agents\n\n"
        f"{rows}\n"
    )


def _write_workspace_agents(root: Path, names: list[str]) -> None:
    agents = root / ".kiro" / "agents"
    agents.mkdir(parents=True)
    for name in names:
        (agents / f"{name}.json").write_text(
            json.dumps({"name": name}),
            encoding="utf-8",
        )


def _without_optional_doctor_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pkstack.doctor.shutil.which",
        lambda name: "/tools/uv" if name == "uv" else None,
    )


def test_doctor_reports_complete_bootstrap_and_optional_tools(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bootstrap_project(tmp_path, power_root=POWER_ROOT)
    fake_kiro = tmp_path / "tools" / "kiro-cli"
    fake_kiro.parent.mkdir()
    fake_kiro.write_text("test executable sentinel\n", encoding="utf-8")
    monkeypatch.setattr(
        "pkstack.doctor.shutil.which",
        lambda name: (
            str(fake_kiro) if name == "kiro-cli" else "/tools/uv" if name == "uv" else None
        ),
    )
    calls: list[tuple[list[str], Path | None]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        cwd = kwargs.get("cwd")
        assert cwd is None or isinstance(cwd, Path)
        calls.append((command, cwd))
        if command[1:] == ["agent", "list"]:
            names = sorted(path.stem for path in (tmp_path / ".kiro/agents").glob("*.json"))
            return subprocess.CompletedProcess(command, 0, _agent_list_output(names, ansi=True), "")
        assert command[1:3] == ["agent", "validate"]
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("pkstack.doctor.subprocess.run", run)

    result = run_doctor(tmp_path)

    assert result["ok"] is True
    assert result["summary"]["fail"] == 0
    checks = {check["name"]: check for check in result["checks"]}
    receipt = json.loads((tmp_path / ".pkstack" / "bootstrap.json").read_text())
    assert checks["okn"]["status"] == "warn"
    assert checks["kiro-workspace-agent-discovery"]["status"] == "pass"
    for steering in (
        "pkstack-core-steering",
        "pkstack-safety-steering",
        "pkstack-typescript-steering",
        "pkstack-unslop-steering",
    ):
        assert checks[steering]["status"] == "pass"
    assert calls[0] == ([str(fake_kiro), "agent", "list"], tmp_path.resolve())
    assert all(call[0][1:3] == ["agent", "validate"] for call in calls[1:])
    assert {Path(call[0][-1]).stem for call in calls[1:]} == {
        path.stem for path in (tmp_path / ".kiro/agents").glob("*.json")
    }
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
            ".pkstack/projectctl/src/pkstack/models.py",
            "drift",
            "hash mismatch (1): .pkstack/projectctl/src/pkstack/models.py",
        ),
        (
            ".pkstack/projectctl/uv.lock",
            "drift",
            "hash mismatch (1): .pkstack/projectctl/uv.lock",
        ),
        (
            ".kiro/skills/archify/upstream/schemas/workflow.schema.json",
            "missing",
            "missing or non-file (1): .kiro/skills/archify/upstream/schemas/workflow.schema.json",
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
    receipt = tmp_path / ".pkstack" / "bootstrap.json"
    receipt_before = receipt.read_bytes()
    _without_optional_doctor_tools(monkeypatch)

    result = run_doctor(tmp_path)
    checks = {check["name"]: check for check in result["checks"]}

    assert result["ok"] is False
    assert result["summary"]["fail"] >= 1
    assert checks["bootstrap-receipt-integrity"]["status"] == "fail"
    assert message in checks["bootstrap-receipt-integrity"]["message"]
    assert receipt.read_bytes() == receipt_before
    assert managed.exists() is (mutation == "drift")


def test_doctor_receipt_integrity_detects_live_permission_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok is True
    live = tmp_path / ".kiro" / "agents" / "pkstack.json"
    document = json.loads(live.read_text(encoding="utf-8"))
    document["description"] = "Altered but still schema-valid permission profile"
    altered = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    live.write_bytes(altered)
    receipt = tmp_path / ".pkstack" / "bootstrap.json"
    receipt_before = receipt.read_bytes()
    _without_optional_doctor_tools(monkeypatch)

    result = run_doctor(tmp_path)
    checks = {check["name"]: check for check in result["checks"]}

    assert result["ok"] is False
    assert result["summary"]["fail"] == 1
    receipt_check = checks["bootstrap-receipt-integrity"]
    assert receipt_check["status"] == "fail"
    assert "hash mismatch (1)" in receipt_check["message"]
    assert ".kiro/agents/pkstack.json" in receipt_check["message"]
    assert receipt.read_bytes() == receipt_before
    assert live.read_bytes() == altered


@pytest.mark.parametrize(
    "replacement",
    [
        None,
        "{broken",
        json.dumps({"schema_version": 99, "manager": "pkstack", "files": {}}),
        json.dumps({"schema_version": 1, "manager": "pkstack", "files": {}}),
        json.dumps(
            {
                "schema_version": 1,
                "manager": "pkstack",
                "files": {"../escape": "0" * 64},
            }
        ),
        json.dumps(
            {
                "schema_version": 1,
                "manager": "pkstack",
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
    receipt = tmp_path / ".pkstack" / "bootstrap.json"
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
    receipt = tmp_path / ".pkstack" / "bootstrap.json"
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
    managed = tmp_path / ".pkstack" / "projectctl" / "src" / "pkstack" / "models.py"
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
    cached = tmp_path / ".pkstack" / "projectctl" / "src" / "pkstack" / "models.py"
    cached.write_bytes(cached.read_bytes() + b"\n# receipt drift probe\n")

    completed = subprocess.run(
        [str(tmp_path / ".pkstack" / "bin" / "projectctl"), "doctor", "--output", "json"],
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
    (tmp_path / ".kiro" / "agents" / "pkstack.json").write_text("{broken", encoding="utf-8")
    (tmp_path / ".kiro" / "agents" / "pkstack-reviewer.json").unlink()
    monkeypatch.setattr("pkstack.doctor.shutil.which", lambda _name: None)

    result = run_doctor(tmp_path)

    assert result["ok"] is False
    checks = {check["name"]: check for check in result["checks"]}
    assert checks["uv"]["status"] == "fail"
    assert checks["reviewer-agent"]["status"] == "fail"
    assert checks["pkstack-agent-json"]["status"] == "fail"


def test_runtime_ignore_check_uses_git_when_present(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / ".git").mkdir()

    class Completed:
        returncode = 0

    monkeypatch.setattr("pkstack.doctor.subprocess.run", lambda *args, **kwargs: Completed())

    assert _runtime_state_ignored(tmp_path).status == "pass"
    assert _command_check("definitely-missing-pkstack-tool", required=False).status == "warn"


@pytest.mark.parametrize(
    "impostor",
    ["# .pkstack/state/\n", "backup/.pkstack/state/\n", ".pkstack/state/cache\n"],
)
def test_runtime_ignore_check_rejects_impostor_match_without_git(
    tmp_path: Path,
    impostor: str,
) -> None:
    (tmp_path / ".gitignore").write_text(impostor, encoding="utf-8")

    assert _runtime_state_ignored(tmp_path).status == "fail"


def test_bootstrap_rejects_invalid_receipt_and_dry_run_is_non_mutating(tmp_path: Path) -> None:
    receipt = tmp_path / ".pkstack" / "bootstrap.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({"schema_version": 99, "manager": "other"}), encoding="utf-8")

    with pytest.raises(ValueError, match="unrecognized PKStack ownership receipt"):
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
    (project / ".pkstack").symlink_to(outside, target_is_directory=True)
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

    monkeypatch.setattr("pkstack.doctor.subprocess.run", fail_run)

    assert _runtime_state_ignored(tmp_path).status == "fail"
    assert _kiro_agent_check("kiro-cli", tmp_path / "agent.json", "agent").status == "fail"

    timeout = subprocess.TimeoutExpired("kiro-cli", 30)
    monkeypatch.setattr(
        "pkstack.doctor.subprocess.run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(timeout),
    )
    assert _kiro_agent_check("kiro-cli", tmp_path / "agent.json", "agent").status == "fail"


def test_kiro_workspace_agent_discovery_accepts_all_exact_ansi_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = [
        "pkstack",
        "pkstack-architect",
        "pkstack-maintainer",
        "pkstack-reviewer",
        "pkstack-verifier",
    ]
    _write_workspace_agents(tmp_path, expected)
    observed: dict[str, object] = {}

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed.update(kwargs)
        return subprocess.CompletedProcess(command, 0, _agent_list_output(expected, ansi=True), "")

    monkeypatch.setattr("pkstack.doctor.subprocess.run", run)

    check = _kiro_agent_discovery_check("/opt/kiro-cli", tmp_path)

    assert check.status == "pass"
    assert "all 5 workspace agent profile(s)" in check.message
    assert observed["command"] == ["/opt/kiro-cli", "agent", "list"]
    assert observed["cwd"] == tmp_path
    assert observed["timeout"] == 30
    assert observed["check"] is False


def test_kiro_workspace_agent_discovery_accepts_real_cli_stderr_renderer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = [
        "pkstack",
        "pkstack-architect",
        "pkstack-maintainer",
        "pkstack-reviewer",
        "pkstack-verifier",
    ]
    _write_workspace_agents(tmp_path, expected)
    output = _agent_list_output(expected, ansi=True)
    monkeypatch.setattr(
        "pkstack.doctor.subprocess.run",
        lambda command, **_kwargs: subprocess.CompletedProcess(command, 0, "", output),
    )

    check = _kiro_agent_discovery_check("kiro-cli", tmp_path)

    assert check.status == "pass"
    assert "all 5 workspace agent profile(s)" in check.message


def test_kiro_workspace_agent_discovery_fails_when_expected_agent_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = ["pkstack", "pkstack-reviewer", "pkstack-verifier"]
    _write_workspace_agents(tmp_path, expected)
    output = _agent_list_output(["pkstack", "pkstack-reviewer"])
    monkeypatch.setattr(
        "pkstack.doctor.subprocess.run",
        lambda command, **_kwargs: subprocess.CompletedProcess(command, 0, output, ""),
    )

    check = _kiro_agent_discovery_check("kiro-cli", tmp_path)

    assert check.status == "fail"
    assert check.message == "workspace agents missing from kiro-cli agent list: pkstack-verifier"


@pytest.mark.parametrize(
    "output",
    [
        "Global: /tmp/home/.kiro/agents\n  pkstack Workspace test\n",
        "Workspace: /tmp/project/.kiro/agents\n  pkstack Workspace\n  pkstack Workspace\n",
        "Workspace: /tmp/project/.kiro/agents\nno loader rows\n",
    ],
    ids=("missing-header", "duplicate-row", "no-exact-row"),
)
def test_kiro_workspace_agent_discovery_fails_on_malformed_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    output: str,
) -> None:
    _write_workspace_agents(tmp_path, ["pkstack"])
    monkeypatch.setattr(
        "pkstack.doctor.subprocess.run",
        lambda command, **_kwargs: subprocess.CompletedProcess(command, 0, output, ""),
    )

    check = _kiro_agent_discovery_check("kiro-cli", tmp_path)

    assert check.status == "fail"
    assert check.message.startswith("malformed kiro-cli agent list output:")


def test_kiro_workspace_agent_discovery_fails_closed_on_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_workspace_agents(tmp_path, ["pkstack"])

    def timeout(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        timeout_seconds = kwargs["timeout"]
        assert isinstance(timeout_seconds, (int, float))
        raise subprocess.TimeoutExpired(command, timeout_seconds)

    monkeypatch.setattr("pkstack.doctor.subprocess.run", timeout)

    check = _kiro_agent_discovery_check("kiro-cli", tmp_path)

    assert check.status == "fail"
    assert check.message == "kiro-cli agent list timed out after 30 seconds"


def test_kiro_workspace_agent_discovery_fails_closed_on_nonzero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_workspace_agents(tmp_path, ["pkstack"])
    monkeypatch.setattr(
        "pkstack.doctor.subprocess.run",
        lambda command, **_kwargs: subprocess.CompletedProcess(
            command,
            23,
            "",
            "sensitive local diagnostics stay out of the doctor payload",
        ),
    )

    check = _kiro_agent_discovery_check("kiro-cli", tmp_path)

    assert check.status == "fail"
    assert check.message == "kiro-cli agent list exited 23"
    assert "sensitive" not in check.message


def test_agent_discovery_probe_records_bounded_221_evidence() -> None:
    evidence = json.loads(
        (REPOSITORY_ROOT / "reviews" / "kiro-v3-agent-discovery-probe.json").read_text(
            encoding="utf-8"
        )
    )

    assert evidence["schema_version"] == 1
    assert evidence["observed_at"] == "2026-09-03T00:40:00Z"
    assert evidence["runtime"] == {
        "client": "Kiro CLI",
        "client_version": "2.21.0",
        "executable_sha256": "0a24ebce53f4dc5cea6fbc74e5e95e9df9787aa4ec76a5eb459959c200c59225",
        "probe_command": "kiro-cli agent list",
    }
    probe = evidence["controlled_probe"]
    assert probe["expected_workspace_agents"] == [
        "pstack",
        "pstack-architect",
        "pstack-maintainer",
        "pstack-reviewer",
        "pstack-verifier",
    ]
    assert probe["workspace_agent_set_sha256"] == (
        "2122ae5b1beb677694e05d73007e9d0a20261b69456d54fc6307036c47f2472f"
    )
    assert probe["field_absent_output_sha256"] == (
        "acfd2441dcf8671873c9a362d8da53e5e692727a91c76c50e52575cdd06b0cc1"
    )
    assert probe["empty_object_output_sha256"] == (
        "8e8b7681321235e8d01d37a0445c2536b89537bf4086beb339c88f12fc018489"
    )
    assert evidence["documentation"]["retrieved_at"] == "2026-09-03T00:40:00Z"
    assert {page["url"]: page["sha256"] for page in evidence["documentation"]["pages"]} == {
        "https://kiro.dev/llms.txt": (
            "e260760ef80a9be25c6a4bf02c1aaf0915a5233412c3cb7af59d54575506da77"
        ),
        "https://kiro.dev/docs/cli/v3/agent-config.md": (
            "3a6bba711ab56db59070466f599e590feda68730607ce00706155beac023190c"
        ),
        "https://kiro.dev/docs/custom-agents/configuration-reference.md": (
            "80484017b11180fe9e27f9ee5f71c0e8812afa53591793d162bfb7027b99a4c3"
        ),
        "https://kiro.dev/docs/custom-agents/subagents.md": (
            "31365d7e0996a3844be19e35db031c9676593f81d7e1f58e360a41170a29afac"
        ),
        "https://kiro.dev/docs/custom-agents.md": (
            "4901ef1d9bb61a831849697619ca484a4b0517ac23ea3afd94de5fd399799400"
        ),
        "https://kiro.dev/docs/ide/whats-new-v1/agent-config.md": (
            "55ff4294e193171bd7f1104912592f588b682e3852f44b2df824119781b55397"
        ),
        "https://kiro.dev/docs/crew/capabilities/agents.md": (
            "f9be9521cfcf0f73e6aa11ba692e65f32f13c54c790901adaff6331bbc799f0d"
        ),
    }
    compatibility = " ".join(
        (POWER_ROOT / "docs" / "kiro-v3-compatibility.md").read_text(encoding="utf-8").split()
    )
    assert "Crew's direct KAS projection" in compatibility
    assert "does not preserve inline permission or native subagent parity" in compatibility


def test_parse_workspace_agent_rows_does_not_promote_global_or_builtin_rows() -> None:
    output = _agent_list_output(["pkstack"], ansi=True)
    output += "  pkstack-global                  Global        unrelated\n"
    output += "  kiro_default                   (Built-in)    default\n"

    assert _parse_workspace_agent_rows(output) == {"pkstack"}
