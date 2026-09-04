"""Regression checks for the public PK-Stack release metadata contract."""

from __future__ import annotations

import ast
import json
import re
import tomllib
from pathlib import Path

import yaml

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


def test_release_reproves_tagged_default_branch_commit_and_portable_checksum() -> None:
    workflow_path = REPOSITORY_ROOT / ".github/workflows/pk-stack-release.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    parsed = yaml.safe_load(workflow)

    assert parsed["jobs"]["release"]["env"]["RELEASE_SHA"] == "${{ github.sha }}"
    assert "refs/remotes/origin/$DEFAULT_BRANCH" in workflow
    assert "uv run --frozen pytest -q" in workflow
    assert "node --test .github/scripts/test_pk_stack_pr_policy.js" in workflow
    assert "git archive --format=tar --prefix=pk-stack/" in workflow
    assert '"$RELEASE_SHA:powers/pk-stack"' in workflow
    assert "tar --create" not in workflow
    assert 'sha256sum "$(basename "$archive")"' in workflow
    assert 'sha256sum --check "$(basename "$checksum")"' in workflow
    assert 'sha256sum "$archive" >"$checksum"' not in workflow


def test_ci_static_analyzers_are_on_path_before_same_step_probe() -> None:
    workflow = (REPOSITORY_ROOT / ".github/workflows/pk-stack-ci.yml").read_text(encoding="utf-8")
    export_at = workflow.index('export PATH="$STATIC_TOOLS/bin:$PATH"')
    actionlint_probe_at = workflow.index("actionlint -version")
    shellcheck_probe_at = workflow.index("shellcheck --version")

    assert export_at < actionlint_probe_at < shellcheck_probe_at
