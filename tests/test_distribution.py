from __future__ import annotations

import json
import tomllib
from pathlib import Path

from pkstack.discovery import discover_repository

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
POWER_ROOT = REPOSITORY_ROOT / "powers" / "pkstack"
CACHED_ROOT = REPOSITORY_ROOT / ".pkstack" / "projectctl"


def _portable_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and ".venv" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    }


def test_canonical_power_and_generated_controller_are_byte_identical() -> None:
    pairs = (
        (POWER_ROOT / "src" / "pkstack", CACHED_ROOT / "src" / "pkstack"),
        (POWER_ROOT / "dev.kiro" / "steering", REPOSITORY_ROOT / ".kiro" / "steering"),
    )

    for canonical, generated in pairs:
        assert _portable_files(generated) == _portable_files(canonical), (
            canonical,
            generated,
        )
    skills = _portable_files(POWER_ROOT / "skills")
    expected_skills = {
        key: value for key, value in skills.items() if not key.startswith("pkstack-setup/")
    }
    assert _portable_files(REPOSITORY_ROOT / ".kiro" / "skills") == expected_skills
    for relative, content in _portable_files(POWER_ROOT / "templates" / "project").items():
        assert (REPOSITORY_ROOT / relative).read_bytes() == content
    assert (CACHED_ROOT / "uv.lock").read_bytes() == (
        POWER_ROOT / "templates" / "projectctl" / "uv.lock"
    ).read_bytes()
    for directory in ("skills", "dev.kiro", "templates"):
        assert not (CACHED_ROOT / directory).exists()


def test_committed_discovery_matches_fresh_repository_discovery() -> None:
    committed = json.loads(
        (REPOSITORY_ROOT / ".pkstack" / "discovery.json").read_text(encoding="utf-8")
    )
    assert committed == discover_repository(REPOSITORY_ROOT)


def test_power_distribution_has_no_global_command_entrypoints() -> None:
    manifest = tomllib.loads((POWER_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert not manifest["project"].get("scripts")
    assert not (POWER_ROOT / "src" / "pkstack" / "launcher.py").exists()
    assert not (REPOSITORY_ROOT / "projectctl").exists()
    assert (REPOSITORY_ROOT / ".pkstack" / "bin" / "projectctl").is_file()
