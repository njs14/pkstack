"""Repository-owned allowlist for the complete consumer Power, with no exclusions."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

CONTRACT = "maintenance/package-content.json"
ROOT = Path(__file__).resolve().parents[2]


class ContentError(RuntimeError):
    """The source or archive differs from its reviewed consumer content contract."""


def load_contract(root: Path = ROOT) -> set[str]:
    path = root / CONTRACT
    if path.is_symlink() or not path.is_file():
        raise ContentError("missing or unsafe package-content contract")
    data = json.loads(path.read_text())
    if (
        not isinstance(data, dict)
        or set(data) != {"schema_version", "files"}
        or type(data["schema_version"]) is not int
        or data["schema_version"] != 1
        or not isinstance(data["files"], list)
        or not data["files"]
    ):
        raise ContentError("invalid package-content contract")
    files: list[Any] = data["files"]
    if any(
        not isinstance(name, str)
        or not name
        or "\\" in name
        or any(part in {"", ".", ".."} for part in name.split("/"))
        or PurePosixPath(name).is_absolute()
        for name in files
    ):
        raise ContentError("unsafe package-content contract path")
    if files != sorted(set(files)):
        raise ContentError("package-content contract must be sorted and unique")
    return set(files)


def validate_paths(files: set[str], directories: set[str], allowed: set[str]) -> None:
    expected_directories = {
        str(parent)
        for name in allowed
        for parent in PurePosixPath(name).parents
        if str(parent) != "."
    }
    unexpected = (files - allowed) | (directories - expected_directories)
    missing = allowed - files
    if unexpected or missing:
        raise ContentError(
            f"consumer package content mismatch; unexpected={sorted(unexpected)}; "
            f"missing={sorted(missing)}"
        )


def validate_source(power: Path, allowed: set[str]) -> None:
    """Inspect all on-disk content, including ignored clutter and empty directories."""
    if power.is_symlink() or not power.is_dir():
        raise ContentError("missing or unsafe consumer Power directory")
    files: set[str] = set()
    directories: set[str] = set()
    for path in power.rglob("*"):
        name = path.relative_to(power).as_posix()
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ContentError(f"consumer package contains a link or special file: {name}")
        (directories if path.is_dir() else files).add(name)
    validate_paths(files, directories, allowed)
