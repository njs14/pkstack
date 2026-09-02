from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
POWER_ROOT = REPOSITORY_ROOT / "powers" / "pk-stack"
CACHED_ROOT = REPOSITORY_ROOT / ".pstack" / "projectctl"


def _portable_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and ".venv" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    }


def test_power_package_has_current_agent_plugins_manifest() -> None:
    payload = json.loads((POWER_ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert payload["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert payload["name"] == "pk-stack"
    assert payload["version"] == "0.1.0"
    assert payload["author"]["name"]
    assert {"PK-Stack", "Poteto Kiro", "verified goal", "Kiro CLI"} <= set(
        payload["keywords"]
    )
    assert (POWER_ROOT / "skills" / "setup-pstack" / "SKILL.md").is_file()
    assert (POWER_ROOT / "skills" / "setup-pstack" / "scripts" / "setup_pstack.py").is_file()


def test_canonical_power_and_generated_fixture_are_byte_identical() -> None:
    pairs = (
        (POWER_ROOT / "src" / "pstack_kiro", CACHED_ROOT / "src" / "pstack_kiro"),
        (POWER_ROOT / "skills", CACHED_ROOT / "skills"),
        (POWER_ROOT / "dev.kiro" / "steering", CACHED_ROOT / "dev.kiro" / "steering"),
        (POWER_ROOT / "templates" / "project", CACHED_ROOT / "templates" / "project"),
        (
            POWER_ROOT / "templates" / "projectctl",
            CACHED_ROOT / "templates" / "projectctl",
        ),
    )

    for canonical, generated in pairs:
        assert _portable_files(generated) == _portable_files(canonical), (
            canonical,
            generated,
        )


def test_power_local_setup_bootstraps_and_rechecks_a_fresh_project(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    setup = POWER_ROOT / "skills" / "setup-pstack" / "scripts" / "setup_pstack.py"
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    first = subprocess.run(
        [sys.executable, str(setup), "--root", str(target), "--output", "json"],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert first.returncode == 0, (first.stdout, first.stderr)
    assert json.loads(first.stdout)["ok"] is True
    receipt = target / ".pstack" / "bootstrap.json"
    first_receipt = receipt.read_bytes()

    second = subprocess.run(
        [sys.executable, str(setup), "--root", str(target), "--output", "json"],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert second.returncode == 0, (second.stdout, second.stderr)
    second_payload = json.loads(second.stdout)
    assert second_payload["ok"] is True
    assert second_payload["created"] == []
    assert second_payload["updated"] == []
    assert receipt.read_bytes() == first_receipt

    doctor = subprocess.run(
        [str(target / ".pstack" / "bin" / "projectctl"), "doctor", "--output", "json"],
        cwd=target,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert doctor.returncode == 0, (doctor.stdout, doctor.stderr)
    doctor_payload = json.loads(doctor.stdout)
    assert doctor_payload["ok"] is True
    assert doctor_payload["summary"]["fail"] == 0
