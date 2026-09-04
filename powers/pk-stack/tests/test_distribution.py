from __future__ import annotations

import json
from pathlib import Path

from pk_stack.discovery import discover_repository

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
POWER_ROOT = REPOSITORY_ROOT / "powers" / "pk-stack"
CACHED_ROOT = REPOSITORY_ROOT / ".pk-stack" / "projectctl"


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
        (POWER_ROOT / "src" / "pk_stack", CACHED_ROOT / "src" / "pk_stack"),
        (POWER_ROOT / "dev.kiro" / "steering", REPOSITORY_ROOT / ".kiro" / "steering"),
    )

    for canonical, generated in pairs:
        assert _portable_files(generated) == _portable_files(canonical), (
            canonical,
            generated,
        )
    skills = _portable_files(POWER_ROOT / "skills")
    expected_skills = {
        key: value for key, value in skills.items() if not key.startswith("setup-pk-stack/")
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
        (REPOSITORY_ROOT / ".pk-stack" / "discovery.json").read_text(encoding="utf-8")
    )
    assert committed == discover_repository(REPOSITORY_ROOT)
