"""Real uvx acceptance against a disposable application project."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

POWER_ROOT = Path(__file__).parents[1]
POWER_VERSION = json.loads((POWER_ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
NEXT_VERSION = f"{POWER_VERSION.rsplit('.', 1)[0]}.{int(POWER_VERSION.rsplit('.', 1)[1]) + 1}"
BUILD_IGNORE = shutil.ignore_patterns(
    ".git", ".venv", "dist", "tests", "benchmarks", "__pycache__", "*.pyc"
)


@dataclass(frozen=True, slots=True)
class UvxTool:
    """A uv installation confined to this module's cache and tool directories."""

    uv: str
    wheel: Path
    next_wheel: Path
    env: dict[str, str]

    def command(self, *arguments: str, wheel: Path | None = None) -> list[str]:
        return [
            self.uv,
            "tool",
            "run",
            "--python",
            sys.executable,
            "--from",
            str(wheel or self.wheel),
            "pkstack",
            *arguments,
        ]


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=900
    )


def _ok(completed: subprocess.CompletedProcess[str]) -> subprocess.CompletedProcess[str]:
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return completed


def _json(completed: subprocess.CompletedProcess[str], *, code: int = 0) -> dict[str, Any]:
    assert completed.returncode == code, completed.stderr or completed.stdout
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert isinstance(payload, dict)
    return payload


def _build_wheel(source: Path, uv: str, out_dir: Path, env: dict[str, str]) -> Path:
    _ok(
        _run(
            [uv, "build", "--wheel", "--no-sources", "--out-dir", str(out_dir), "--no-build-logs"],
            cwd=source,
            env=env,
        )
    )
    wheels = sorted(out_dir.glob("*.whl"))
    assert len(wheels) == 1, wheels
    return wheels[0]


@pytest.fixture(scope="module")
def uvx_tool(tmp_path_factory: pytest.TempPathFactory) -> UvxTool:
    """Build the shipped wheel and one bumped-version wheel exactly once."""

    uv = shutil.which("uv")
    assert uv is not None
    base = tmp_path_factory.mktemp("uvx-tool")
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COV_CORE_", "COVERAGE_", "UV_"))
        and key not in {"PYTHONPATH", "VIRTUAL_ENV"}
    }
    # Never touch the developer's global uv tool or cache state.
    env["UV_CACHE_DIR"] = str(base / "cache")
    env["UV_TOOL_DIR"] = str(base / "tools")
    env["UV_TOOL_BIN_DIR"] = str(base / "tool-bin")

    wheel = _build_wheel(POWER_ROOT, uv, base / "dist", env)

    upgrade_source = base / "power-next"
    shutil.copytree(POWER_ROOT, upgrade_source, ignore=BUILD_IGNORE)
    for relative, old, new in (
        ("pyproject.toml", f'version = "{POWER_VERSION}"', f'version = "{NEXT_VERSION}"'),
        (
            "src/pkstack/__init__.py",
            f'__version__ = "{POWER_VERSION}"',
            f'__version__ = "{NEXT_VERSION}"',
        ),
        (
            "templates/projectctl/uv.lock",
            f'name = "pkstack"\nversion = "{POWER_VERSION}"',
            f'name = "pkstack"\nversion = "{NEXT_VERSION}"',
        ),
    ):
        path = upgrade_source / relative
        text = path.read_text(encoding="utf-8")
        assert text.count(old) == 1, relative
        path.write_text(text.replace(old, new), encoding="utf-8")
    next_wheel = _build_wheel(upgrade_source, uv, base / "dist-next", env)
    tool = UvxTool(uv=uv, wheel=wheel, next_wheel=next_wheel, env=env)
    # Warm each isolated tool environment before JSON-output assertions. uv's
    # package preparation messages are stderr, separate from our CLI contract.
    for selected in (wheel, next_wheel):
        _ok(_run(tool.command("--version", wheel=selected), cwd=base, env=env))
    return tool


def _application(root: Path) -> Path:
    """Create a disposable application with a real, repairable verifier."""

    root.mkdir(parents=True)
    (root / "value.txt").write_text("broken\n", encoding="utf-8")
    (root / "check.py").write_text(
        "import pathlib, sys\n"
        'value = pathlib.Path("value.txt").read_text(encoding="utf-8").strip()\n'
        'print(f"account value: {value}")\n'
        'sys.exit(0 if value == "normalized" else 1)\n',
        encoding="utf-8",
    )
    (root / "envprobe.py").write_text(
        "import importlib.util, json, os, sys\n"
        "from pathlib import Path\n"
        "print(json.dumps({\n"
        "  'path': os.environ.get('PATH'),\n"
        "  'pythonpath': os.environ.get('PYTHONPATH'),\n"
        "  'virtual_env': os.environ.get('VIRTUAL_ENV'),\n"
        "  'executable': str(Path(sys.executable).resolve()),\n"
        "  'pkstack_origin': (\n"
        "      importlib.util.find_spec('pkstack').origin\n"
        "      if importlib.util.find_spec('pkstack') else None),\n"
        "  'sys_path': [entry for entry in sys.path if entry],\n"
        "}, sort_keys=True))\n",
        encoding="utf-8",
    )
    return root


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_uvx_launcher_operates_a_disposable_application(uvx_tool: UvxTool, tmp_path: Path) -> None:
    application = _application(tmp_path / "app")
    caller_venv = tmp_path / "app-venv"
    caller_env = dict(uvx_tool.env)
    caller_env["VIRTUAL_ENV"] = str(caller_venv)
    caller_env["PKSTACK_ACCEPTANCE_SENTINEL"] = "preserved"

    launcher_version = _ok(
        _run(uvx_tool.command("--version"), cwd=application, env=caller_env)
    ).stdout
    assert launcher_version.splitlines()[0] == f"pkstack {POWER_VERSION}"

    before_setup = _snapshot(application)
    dry_run = _json(
        _run(
            uvx_tool.command("setup", "--dry-run", "--output", "json"),
            cwd=application,
            env=caller_env,
        )
    )
    assert dry_run["ok"] is True
    assert dry_run["dry_run"] is True
    assert dry_run["created"]
    assert _snapshot(application) == before_setup

    first = _json(
        _run(uvx_tool.command("setup", "--output", "json"), cwd=application, env=caller_env)
    )
    assert first["ok"] is True
    assert first["root"] == str(application)
    controller = application / ".pkstack" / "bin" / "projectctl"
    assert controller.is_file() and os.access(controller, os.X_OK)

    repeated = _json(
        _run(uvx_tool.command("setup", "--output", "json"), cwd=application, env=caller_env)
    )
    assert repeated["ok"] is True
    assert repeated["created"] == [] and repeated["updated"] == []
    assert repeated["unchanged"]

    version = _json(
        _run(uvx_tool.command("version", "--output", "json"), cwd=application, env=caller_env)
    )
    assert version["version"] == POWER_VERSION
    assert version["name"] == "pkstack"

    doctor = _json(
        _run(uvx_tool.command("doctor", "--output", "json"), cwd=application, env=caller_env)
    )
    assert doctor["ok"] is True
    features = _json(
        _run(
            uvx_tool.command("feature", "validate", "--output", "json"),
            cwd=application,
            env=caller_env,
        )
    )
    assert features["ok"] is True

    unknown = _run(
        uvx_tool.command("not-a-command", "--output", "json"), cwd=application, env=caller_env
    )
    assert unknown.returncode == 2
    assert unknown.stderr == ""
    unknown_payload = json.loads(unknown.stdout)
    assert unknown_payload["ok"] is False and unknown_payload["error_type"]

    root_conflict = _run(
        uvx_tool.command("doctor", "--root", str(application), "--output", "json"),
        cwd=application,
        env=caller_env,
    )
    assert root_conflict.returncode == 2
    assert root_conflict.stderr == ""
    assert "--project" in json.loads(root_conflict.stdout)["error"]

    # The verifier must observe the caller environment, not the uvx tool
    # environment or the controller's own interpreter.
    baseline = json.loads(
        _ok(_run([sys.executable, "envprobe.py"], cwd=application, env=caller_env)).stdout
    )
    probe_goal = _json(
        _run(
            uvx_tool.command(
                "goal",
                "start",
                "Observe the verifier environment",
                "--command",
                f"{sys.executable} envprobe.py",
                "--output",
                "json",
            ),
            cwd=application,
            env=caller_env,
        )
    )
    assert probe_goal["goal"]["contract"]["argv"] == [sys.executable, "envprobe.py"]
    probe = json.loads(
        _json(
            _run(
                uvx_tool.command("goal", "verify", "--output", "json"),
                cwd=application,
                env=caller_env,
            )
        )["goal"]["last_result"]["stdout"]
    )
    assert probe == baseline
    assert probe["virtual_env"] == str(caller_venv)
    # No controller runtime, uvx tool environment, or launcher import path leaks
    # into the verifier that the generated controller actually executes.
    assert ".pkstack" not in (probe["pkstack_origin"] or "")
    assert not any(".pkstack" in entry for entry in probe["sys_path"])
    assert not any(uvx_tool.env["UV_TOOL_DIR"] in entry for entry in probe["sys_path"])
    assert ".pkstack/projectctl" not in json.dumps(probe)
    assert uvx_tool.env["UV_TOOL_DIR"] not in (probe["path"] or "")
    assert str(application / ".pkstack") not in (probe["path"] or "")

    # A failing verifier is repaired in the application, never in the controller.
    verifier_before = (application / "check.py").read_bytes()
    _json(
        _run(
            uvx_tool.command("goal", "clear", "--output", "json"),
            cwd=application,
            env=caller_env,
        )
    )
    _ok(
        _run(
            uvx_tool.command(
                "goal",
                "start",
                "Normalize the account value",
                "--command",
                f"{sys.executable} check.py",
                "--output",
                "json",
            ),
            cwd=application,
            env=caller_env,
        )
    )
    failed = _run(
        uvx_tool.command("goal", "verify", "--output", "json"), cwd=application, env=caller_env
    )
    assert failed.returncode == 1
    failed_payload = json.loads(failed.stdout)
    assert failed_payload["ok"] is False
    assert failed_payload["goal"]["last_result"]["passed"] is False
    (application / "value.txt").write_text("normalized\n", encoding="utf-8")
    passed = _json(
        _run(
            uvx_tool.command("goal", "verify", "--output", "json"), cwd=application, env=caller_env
        )
    )
    assert passed["ok"] is True
    assert passed["goal"]["status"] == "passed"
    assert passed["goal"]["last_result"]["passed"] is True
    assert (application / "check.py").read_bytes() == verifier_before

    # A locally edited managed file is preserved, and setup refuses to overwrite it.
    profile = application / ".kiro" / "agents" / "pkstack.json"
    reviewed_profile = profile.read_bytes()
    edited_profile = reviewed_profile.replace(b'"name": "pkstack"', b'"name": "pkstack"  ')
    assert edited_profile != reviewed_profile
    profile.write_bytes(edited_profile)
    conflicted = _run(
        uvx_tool.command("setup", "--output", "json"), cwd=application, env=caller_env
    )
    assert conflicted.returncode == 2
    conflict_payload = json.loads(conflicted.stdout)
    assert conflict_payload["ok"] is False
    assert any(".kiro/agents/pkstack.json" in entry for entry in conflict_payload["conflicts"])
    assert profile.read_bytes() == edited_profile
    profile.write_bytes(reviewed_profile)

    # The launcher version and the installed controller version differ until upgrade.
    next_launcher = _ok(
        _run(
            uvx_tool.command("--version", wheel=uvx_tool.next_wheel),
            cwd=application,
            env=caller_env,
        )
    ).stdout
    assert next_launcher.splitlines()[0] == f"pkstack {NEXT_VERSION}"
    still_installed = _json(
        _run(
            uvx_tool.command("version", "--output", "json", wheel=uvx_tool.next_wheel),
            cwd=application,
            env=caller_env,
        )
    )
    assert still_installed["version"] == POWER_VERSION

    controller_pyproject = application / ".pkstack" / "projectctl" / "pyproject.toml"
    before_upgrade = _snapshot(application)
    preview = _json(
        _run(
            uvx_tool.command("upgrade", "--dry-run", "--output", "json", wheel=uvx_tool.next_wheel),
            cwd=application,
            env=caller_env,
        )
    )
    assert preview["update_managed"] is True
    assert preview["dry_run"] is True
    assert any("projectctl/pyproject.toml" in entry for entry in preview["updated"])
    assert _snapshot(application) == before_upgrade

    applied = _json(
        _run(
            uvx_tool.command("upgrade", "--output", "json", wheel=uvx_tool.next_wheel),
            cwd=application,
            env=caller_env,
        )
    )
    assert applied["ok"] is True
    assert any("projectctl/pyproject.toml" in entry for entry in applied["updated"])
    assert f'version = "{NEXT_VERSION}"' in controller_pyproject.read_text(encoding="utf-8")
    upgraded = _json(
        _run(uvx_tool.command("version", "--output", "json"), cwd=application, env=caller_env)
    )
    assert upgraded["version"] == NEXT_VERSION


def test_uvx_forwarded_command_is_cancelled_by_a_signal(uvx_tool: UvxTool, tmp_path: Path) -> None:
    application = _application(tmp_path / "signal-app")
    (application / "sleeper.py").write_text(
        "import os, pathlib, sys, time\n"
        'pathlib.Path("started.txt").write_text(str(os.getpid()), encoding="utf-8")\n'
        "sys.stdout.flush()\n"
        "time.sleep(120)\n",
        encoding="utf-8",
    )
    _json(_run(uvx_tool.command("setup", "--output", "json"), cwd=application, env=uvx_tool.env))
    _ok(
        _run(
            uvx_tool.command(
                "goal",
                "start",
                "Cancel a long verifier",
                "--command",
                f"{sys.executable} sleeper.py",
                "--output",
                "json",
            ),
            cwd=application,
            env=uvx_tool.env,
        )
    )

    started = application / "started.txt"
    process = subprocess.Popen(
        uvx_tool.command("goal", "verify", "--output", "json"),
        cwd=application,
        env=uvx_tool.env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 300
        while not started.exists() and time.monotonic() < deadline:
            assert process.poll() is None, process.communicate()
            time.sleep(0.2)
        assert started.exists(), "the forwarded verifier never started"
        child_pid = int(started.read_text())
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        stdout, _ = process.communicate(timeout=120)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            # This PID belongs to the sleeper created by this disposable test.
            os.kill(child_pid, signal.SIGKILL)
            raise AssertionError("the cancelled verifier process survived its controller")
    finally:
        if process.poll() is None:  # pragma: no cover - only on an unexpected hang
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            process.communicate(timeout=60)

    assert process.returncode != 0
    assert stdout.strip() == ""
    # The cancelled run records no attempt and leaves the application intact.
    status = _json(
        _run(
            uvx_tool.command("goal", "status", "--output", "json"),
            cwd=application,
            env=uvx_tool.env,
        )
    )
    assert status["goal"]["attempt_count"] == 0
    assert status["goal"]["last_result"] is None
    assert (application / "sleeper.py").is_file()
    survivor = _json(
        _run(uvx_tool.command("version", "--output", "json"), cwd=application, env=uvx_tool.env)
    )
    assert survivor["version"] == POWER_VERSION


def test_uvx_verifier_uses_real_application_python_and_imports(
    uvx_tool: UvxTool, tmp_path: Path
) -> None:
    application = _application(tmp_path / "application with spaces")
    venv = application / ".venv"
    _ok(
        _run(
            [uvx_tool.uv, "venv", "--python", sys.executable, str(venv)],
            cwd=application,
            env=uvx_tool.env,
        )
    )
    python = venv / "bin" / "python"
    purelib = Path(
        _ok(
            _run(
                [str(python), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
                cwd=application,
                env=uvx_tool.env,
            )
        ).stdout.strip()
    )
    (purelib / "pkstack_app_probe.py").write_text(
        "import json, os, sys\n"
        "print(json.dumps({'prefix': sys.prefix, 'module': __file__, "
        "'virtual_env': os.environ.get('VIRTUAL_ENV'), "
        "'marker': 'application-only dependency'}, sort_keys=True))\n"
    )
    environment = dict(uvx_tool.env)
    environment["PATH"] = os.pathsep.join([str(venv / "bin"), environment.get("PATH", "")])
    environment["VIRTUAL_ENV"] = str(venv)
    baseline = json.loads(
        _ok(_run(["python", "-m", "pkstack_app_probe"], cwd=application, env=environment)).stdout
    )
    assert Path(baseline["prefix"]) == venv
    assert Path(baseline["module"]).is_relative_to(venv)
    _json(_run(uvx_tool.command("setup", "--output", "json"), cwd=application, env=environment))
    _json(
        _run(
            uvx_tool.command(
                "goal",
                "start",
                "Use the application environment",
                "--command",
                "python -m pkstack_app_probe",
                "--output",
                "json",
            ),
            cwd=application,
            env=environment,
        )
    )
    result = _json(
        _run(
            uvx_tool.command("goal", "verify", "--output", "json"), cwd=application, env=environment
        )
    )
    assert json.loads(result["goal"]["last_result"]["stdout"]) == baseline
    wrapper = application / ".pkstack/bin/projectctl"
    direct = _json(
        _run([str(wrapper), "version", "--output", "json"], cwd=application, env=environment)
    )
    through_uvx = _json(
        _run(uvx_tool.command("version", "--output", "json"), cwd=application, env=environment)
    )
    assert through_uvx == direct
