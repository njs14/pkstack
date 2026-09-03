"""Regression checks for the public PK-Stack release metadata contract."""

from __future__ import annotations

import ast
import json
import re
import tomllib
from pathlib import Path

POWER_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = POWER_ROOT.parents[1]
RELEASE_VERSION = "0.2.0"


def _source_version() -> str:
    module = ast.parse((POWER_ROOT / "src/pstack_kiro/__init__.py").read_text(encoding="utf-8"))
    for statement in module.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in statement.targets
        ):
            value = ast.literal_eval(statement.value)
            assert isinstance(value, str)
            return value
    raise AssertionError("pstack_kiro.__version__ is not declared")


def _lock_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r'(?ms)^\[\[package\]\]\nname = "pstack-kiro"\nversion = "([^"]+)"',
        text,
    )
    assert match, f"pstack-kiro package entry missing from {path}"
    return match.group(1)


def test_public_version_mirrors_plugin_authority() -> None:
    manifest = json.loads((POWER_ROOT / "plugin.json").read_text(encoding="utf-8"))
    project = tomllib.loads((POWER_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert manifest["version"] == RELEASE_VERSION
    assert project["project"]["version"] == manifest["version"]
    assert _source_version() == manifest["version"]
    assert _lock_version(POWER_ROOT / "uv.lock") == manifest["version"]
    assert _lock_version(POWER_ROOT / "templates/projectctl/uv.lock") == manifest["version"]


def test_setup_docs_use_declared_power_source() -> None:
    docs = (
        REPOSITORY_ROOT / "README.md",
        POWER_ROOT / "README.md",
        POWER_ROOT / "docs/usage.md",
    )
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "/absolute/path/to" not in text
    assert "PK_STACK_POWER" in (POWER_ROOT / "docs/usage.md").read_text(encoding="utf-8")
