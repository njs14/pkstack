from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

from pk_stack.bootstrap import (
    REQUIRED_POWER_ASSETS,
    REQUIRED_SOURCE_MODULES,
    bootstrap_project,
)
from pk_stack.branding import DISTRIBUTION_NAME, identity_payload

POWER_ROOT = Path(__file__).parents[1]


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return completed.stdout


def _run_clean_json(
    command: list[str], *, cwd: Path, env: dict[str, str] | None = None
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert completed.stderr == ""
    return json.loads(completed.stdout)


def test_wheel_assets_and_offline_bootstrap_runtime(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    assert uv is not None
    dist = tmp_path / "dist"
    _run(
        [uv, "build", "--wheel", "--out-dir", str(dist), "--no-build-logs"],
        cwd=POWER_ROOT,
    )

    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as archive:
        members = set(archive.namelist())
    assert any(name.endswith(".dist-info/licenses/THIRD_PARTY_NOTICES.md") for name in members)
    for name in REQUIRED_SOURCE_MODULES:
        assert f"pk_stack/{name}" in members
    for relative in REQUIRED_POWER_ASSETS:
        assert f"pk_stack/_assets/{relative}" in members
    for source in (POWER_ROOT / "skills").rglob("*"):
        if source.is_file():
            relative = source.relative_to(POWER_ROOT).as_posix()
            assert f"pk_stack/_assets/{relative}" in members

    clean_env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COV_CORE_", "COVERAGE_"))
    }
    clean_env["UV_OFFLINE"] = "1"
    install_venv = tmp_path / "install-venv"
    _run([uv, "venv", "--python", sys.executable, str(install_venv)], cwd=tmp_path)
    install_python = install_venv / "bin" / "python"
    _run(
        [uv, "pip", "install", "--python", str(install_python), str(wheels[0])],
        cwd=tmp_path,
    )

    target = tmp_path / "target"
    target.mkdir()
    setup_output = _run(
        [str(install_venv / "bin" / "pk-stack-setup"), "--root", str(target), "--output", "json"],
        cwd=target,
        env=clean_env,
    )
    assert json.loads(setup_output)["ok"] is True

    controller = target / ".pk-stack" / "bin" / "projectctl"
    version_output = _run_clean_json(
        [str(controller), "version", "--output", "json"], cwd=target, env=clean_env
    )
    assert version_output == {**identity_payload(), "version": "0.2.0"}
    doctor_output = _run(
        [str(controller), "doctor", "--output", "json"],
        cwd=target,
        env=clean_env,
    )
    assert json.loads(doctor_output)["ok"] is True
    cached_source = target / ".pk-stack" / "projectctl" / "src"
    assert not list(cached_source.rglob("__pycache__"))
    assert not list(cached_source.rglob("*.py[co]"))

    runtime_python = target / ".pk-stack" / "projectctl" / ".venv" / "bin" / "python"
    installed = json.loads(
        _run(
            [
                str(runtime_python),
                "-c",
                "import importlib.metadata as m, json; "
                "print(json.dumps(sorted(d.metadata['Name'].lower() for d in m.distributions())))",
            ],
            cwd=target,
            env=clean_env,
        )
    )
    assert "hatchling" not in installed
    assert DISTRIBUTION_NAME not in installed


def test_bootstrapped_wrapper_preserves_host_verifier_environment(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    assert bootstrap_project(target, power_root=POWER_ROOT).ok is True
    controller = target / ".pk-stack" / "bin" / "projectctl"
    probe = target / "envprobe.py"
    probe.write_text(
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "print(json.dumps({\n"
        "  'path': os.environ.get('PATH'),\n"
        "  'pythonpath_present': 'PYTHONPATH' in os.environ,\n"
        "  'pythonpath': os.environ.get('PYTHONPATH'),\n"
        "  'virtual_env': os.environ.get('VIRTUAL_ENV'),\n"
        "  'uv': {k: v for k, v in os.environ.items() if k.startswith('UV_')},\n"
        "  'executable': str(Path(sys.executable).resolve()),\n"
        "  'prefix': str(Path(sys.prefix).resolve()),\n"
        "  'markers': sorted(k for k in os.environ if k.startswith('PK_STACK_CALLER_')),\n"
        "}, sort_keys=True))\n",
        encoding="utf-8",
    )
    host_env = os.environ.copy()
    host_env["PYTHONPATH"] = str(tmp_path / "host-pythonpath")
    host_env["VIRTUAL_ENV"] = str(tmp_path / "host-venv")
    host_env["UV_PK_STACK_HOST_SENTINEL"] = "preserved"
    baseline = json.loads(_run(["python3", "envprobe.py"], cwd=target, env=host_env))

    generated = _run_clean_json(
        [
            str(controller),
            "feature",
            "generate",
            "environment-probe",
            "--title",
            "Environment probe",
            "--behavior",
            "A verifier receives the host environment.",
            "--expected-path",
            "Host shell to verifier process",
            "--command",
            "python3 envprobe.py",
            "--ready",
            "--output",
            "json",
        ],
        cwd=target,
        env=host_env,
    )
    verified = _run_clean_json(
        [str(controller), "feature", "verify", "environment-probe", "--output", "json"],
        cwd=target,
        env=host_env,
    )

    initial_probe = json.loads(generated["initial_verification"]["stdout"])
    repeated_probe = json.loads(verified["result"]["stdout"])
    assert initial_probe == baseline
    assert repeated_probe == baseline
    assert initial_probe["markers"] == []
    assert ".pk-stack/projectctl" not in json.dumps(initial_probe)


def test_bootstrapped_wrapper_ignores_unchecked_controller_bytecode(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    assert bootstrap_project(target, power_root=POWER_ROOT).ok is True
    controller = target / ".pk-stack" / "bin" / "projectctl"
    expected = {**identity_payload(), "version": "0.2.0"}
    command = [str(controller), "version", "--output", "json"]
    assert _run_clean_json(command, cwd=target) == expected

    cached_branding = target / ".pk-stack" / "projectctl" / "src" / "pk_stack" / "branding.py"
    cached_source = cached_branding.read_bytes()
    malicious_source = target / "unchecked-cache-payload.py"
    malicious_source.write_text(
        'DISPLAY_NAME = "HIJACKED"\n'
        'DISTRIBUTION_NAME = "hijacked"\n'
        'EXPANDED_NAME = "HIJACKED"\n'
        'POWER_ID = "hijacked"\n'
        'RECEIPT_MANAGER = "hijacked"\n'
        "def identity_payload():\n"
        '    return {"name": "hijacked", "display_name": "HIJACKED", '
        '"expanded_name": "HIJACKED", "power_id": "hijacked"}\n',
        encoding="utf-8",
    )
    runtime_python = target / ".pk-stack" / "projectctl" / ".venv" / "bin" / "python"
    _run(
        [
            str(runtime_python),
            "-c",
            "import importlib.util, py_compile, sys; "
            "py_compile.compile(sys.argv[1], "
            "cfile=importlib.util.cache_from_source(sys.argv[2]), doraise=True, "
            "invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)",
            str(malicious_source),
            str(cached_branding),
        ],
        cwd=target,
    )
    caches = list(cached_branding.parent.glob("__pycache__/branding.*.pyc"))
    assert len(caches) == 1
    assert cached_branding.read_bytes() == cached_source

    unprotected_env = os.environ.copy()
    unprotected_env["PYTHONPATH"] = str(cached_branding.parents[1])
    unprotected = _run_clean_json(
        [str(runtime_python), "-B", "-m", "pk_stack", "version", "--output", "json"],
        cwd=target,
        env=unprotected_env,
    )
    assert unprotected["name"] == "hijacked"

    assert _run_clean_json(command, cwd=target) == expected


def test_bootstrapped_wrapper_keeps_malformed_feature_json_structured(tmp_path: Path) -> None:
    fixtures: dict[str, str | bytes] = {
        "bad-command": (
            "---\ntype: feature\nslug: broken\ntitle: Broken\ndraft: true\n"
            'verification:\n  command: "echo \'unterminated"\n---\n\n'
            "## User behavior\n\nA caller sees a result.\n\n"
            "## Expected path\n\nInput to output.\n"
        ),
        "bad-utf8": b"\xff\xfe\x00",
    }
    commands = {
        ("feature", "list"): (2, {"error", "error_type", "ok"}),
        ("feature", "show", "broken"): (2, {"error", "error_type", "ok"}),
        ("feature", "validate"): (
            1,
            {"errors", "feature_count", "features", "ok", "warnings"},
        ),
    }

    for fixture_name, content in fixtures.items():
        target = tmp_path / fixture_name
        target.mkdir()
        assert bootstrap_project(target, power_root=POWER_ROOT).ok is True
        feature = target / "Wiki" / "features" / "broken.md"
        if isinstance(content, bytes):
            feature.write_bytes(content)
        else:
            feature.write_text(content, encoding="utf-8")
        controller = target / ".pk-stack" / "bin" / "projectctl"

        for command, (expected_code, expected_keys) in commands.items():
            completed = subprocess.run(
                [str(controller), *command, "--output", "json"],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            payload = json.loads(completed.stdout)
            assert completed.returncode == expected_code
            assert completed.stderr == ""
            assert set(payload) == expected_keys
            assert payload["ok"] is False


def test_bootstrapped_wrapper_rejects_outside_executable_and_cache_setup(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    assert bootstrap_project(target, power_root=POWER_ROOT).ok is True
    controller = target / ".pk-stack" / "bin" / "projectctl"
    selected_directory = tmp_path / "selected"
    other_directory = tmp_path / "other"
    selected_directory.mkdir()
    other_directory.mkdir()
    selected = selected_directory / "verifier"
    outside = other_directory / "verifier"
    for path in (selected, outside):
        path.write_text('#!/bin/sh\ntest -f "$PWD/proof.txt"\n', encoding="utf-8")
        path.chmod(0o755)
    (target / "proof.txt").write_text("present\n", encoding="utf-8")
    controlled_env = os.environ.copy()
    controlled_env["PATH"] = os.pathsep.join((str(selected_directory), controlled_env["PATH"]))
    receipt = target / ".pk-stack" / "bootstrap.json"
    profile = target / ".kiro" / "agents" / "pk-stack.json"
    managed_before = (receipt.read_bytes(), profile.read_bytes())

    setup = subprocess.run(
        [str(controller), "setup", "--dry-run", "--output", "json"],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
        env=controlled_env,
    )
    assert setup.returncode == 2
    assert setup.stderr == ""
    setup_payload = json.loads(setup.stdout)
    assert setup_payload == {
        "error": (
            "projectctl setup requires --power-root; use the Power-local "
            "/setup-pk-stack skill for setup or refresh, or pass a reviewed "
            "Power root explicitly"
        ),
        "error_type": "ValueError",
        "ok": False,
    }
    assert (receipt.read_bytes(), profile.read_bytes()) == managed_before

    for verifier in ("true", "echo ok"):
        placeholder_goal = subprocess.run(
            [
                str(controller),
                "goal",
                "start",
                "Reject placeholder evidence",
                "--command",
                verifier,
                "--output",
                "json",
            ],
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
            env=controlled_env,
        )
        assert placeholder_goal.returncode == 2
        assert placeholder_goal.stderr == ""
        assert json.loads(placeholder_goal.stdout)["error_type"] == "CommandRejected"
        assert not (target / ".pk-stack" / "state" / "goal.json").exists()

    for slug, verifier in (
        ("placeholder-proof", "true"),
        ("echo-proof", "echo PASS"),
        ("self-proof", ".pk-stack/bin/projectctl version --output json"),
    ):
        placeholder_feature = subprocess.run(
            [
                str(controller),
                "feature",
                "generate",
                slug,
                "--title",
                "Rejected proof",
                "--behavior",
                "A caller observes implemented behavior.",
                "--expected-path",
                "Request to result",
                "--command",
                verifier,
                "--ready",
                "--output",
                "json",
            ],
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
            env=controlled_env,
        )
        assert placeholder_feature.returncode == 2
        assert placeholder_feature.stderr == ""
        assert json.loads(placeholder_feature.stdout)["error_type"] == "CommandRejected"
        assert not (target / "Wiki" / "features" / f"{slug}.md").exists()

    started = subprocess.run(
        [
            str(controller),
            "goal",
            "start",
            "Reject outside executable",
            "--command",
            str(outside),
            "--output",
            "json",
        ],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
        env=controlled_env,
    )
    assert started.returncode == 2
    assert started.stderr == ""
    assert json.loads(started.stdout)["error_type"] == "CommandRejected"
    assert not (target / ".pk-stack" / "state" / "goal.json").exists()

    generated = subprocess.run(
        [
            str(controller),
            "feature",
            "generate",
            "outside-proof",
            "--title",
            "Outside proof",
            "--behavior",
            "A caller observes a bounded proof.",
            "--expected-path",
            "Project to verifier",
            "--command",
            str(outside),
            "--ready",
            "--output",
            "json",
        ],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
        env=controlled_env,
    )
    assert generated.returncode == 2
    assert generated.stderr == ""
    assert json.loads(generated.stdout)["error_type"] == "CommandRejected"
    assert not (target / "Wiki" / "features" / "outside-proof.md").exists()

    planted = target / "Wiki" / "features" / "planted-proof.md"
    planted.write_text(
        "---\n"
        "type: feature\n"
        "slug: planted-proof\n"
        "title: Planted proof\n"
        "draft: false\n"
        "verification:\n"
        f"  command: [{json.dumps(str(outside))}]\n"
        "related: []\n"
        "---\n\n"
        "## User behavior\n\nA caller observes a bounded proof.\n\n"
        "## Expected path\n\nProject to verifier.\n",
        encoding="utf-8",
    )
    validated = subprocess.run(
        [str(controller), "feature", "validate", "--output", "json"],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
        env=controlled_env,
    )
    assert validated.returncode == 1
    assert validated.stderr == ""
    validation_payload = json.loads(validated.stdout)
    assert validation_payload["ok"] is False
    assert any(
        "planted-proof.md: rejected verification command" in error
        for error in validation_payload["errors"]
    )

    control = subprocess.run(
        [
            str(controller),
            "goal",
            "start",
            "Allow PATH-selected executable",
            "--command",
            str(selected),
            "--output",
            "json",
        ],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
        env=controlled_env,
    )
    assert control.returncode == 0, control.stderr or control.stdout
    assert control.stderr == ""
    assert json.loads(control.stdout)["goal"]["contract"]["argv"] == [str(selected)]
