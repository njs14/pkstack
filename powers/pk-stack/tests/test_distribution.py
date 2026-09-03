from __future__ import annotations

import json
from pathlib import Path

from pstack_kiro.discovery import discover_repository

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
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


def test_canonical_power_and_generated_controller_are_byte_identical() -> None:
    pairs = (
        (POWER_ROOT / "src" / "pstack_kiro", CACHED_ROOT / "src" / "pstack_kiro"),
        (POWER_ROOT / "skills", CACHED_ROOT / "skills"),
        (POWER_ROOT / "dev.kiro" / "steering", CACHED_ROOT / "dev.kiro" / "steering"),
        (POWER_ROOT / "templates" / "project", CACHED_ROOT / "templates" / "project"),
        (POWER_ROOT / "templates" / "projectctl", CACHED_ROOT / "templates" / "projectctl"),
    )

    for canonical, generated in pairs:
        assert _portable_files(generated) == _portable_files(canonical), (
            canonical,
            generated,
        )


def test_committed_discovery_matches_fresh_repository_discovery() -> None:
    committed = json.loads(
        (REPOSITORY_ROOT / ".pstack" / "discovery.json").read_text(encoding="utf-8")
    )
    assert committed == discover_repository(REPOSITORY_ROOT)
