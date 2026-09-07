"""Regression checks for the public PKStack release metadata contract."""

from __future__ import annotations

import ast
import json
import re
import tomllib
from pathlib import Path

import yaml

POWER_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = POWER_ROOT.parents[1]


def _source_version() -> str:
    module = ast.parse((POWER_ROOT / "src/pkstack/__init__.py").read_text(encoding="utf-8"))
    for statement in module.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in statement.targets
        ):
            value = ast.literal_eval(statement.value)
            assert isinstance(value, str)
            return value
    raise AssertionError("pkstack.__version__ is not declared")


def _lock_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r'(?ms)^\[\[package\]\]\nname = "pkstack"\nversion = "([^"]+)"',
        text,
    )
    assert match, f"pkstack package entry missing from {path}"
    return match.group(1)


def test_public_version_mirrors_plugin_authority() -> None:
    manifest = json.loads((POWER_ROOT / "plugin.json").read_text(encoding="utf-8"))
    project = tomllib.loads((POWER_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", manifest["version"])
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
        assert "https://kiro.dev/docs/powers/installation/" in text
        assert "Import power from a folder" in text
        assert "plugin.json" in text
        assert "/pkstack-setup" in text
        assert "PKSTACK_POWER" not in text
        assert "PKSTACK_PACKAGE" not in text
        assert "uvx " not in text


def test_release_isolates_publication_authority_after_verification() -> None:
    workflow = yaml.safe_load(
        (REPOSITORY_ROOT / ".github/workflows/pk-stack-release.yml").read_text(encoding="utf-8")
    )
    trigger = workflow.get("on", workflow.get(True))
    assert trigger["push"]["tags"] == ["v[0-9]+.[0-9]+.[0-9]+"]
    assert workflow["permissions"] == {}
    jobs = workflow["jobs"]
    assert set(jobs) == {"verify", "publish"}
    assert jobs["verify"]["permissions"] == {"actions": "read", "contents": "read"}
    assert jobs["publish"]["permissions"] == {"actions": "read", "contents": "write"}
    assert jobs["publish"]["needs"] == "verify"
    assert " ".join(jobs["publish"]["if"].split()) == (
        "needs.verify.result == 'success' && needs.verify.outputs.publication_eligible == 'true'"
    )
    for job in jobs.values():
        for step in job["steps"]:
            if step.get("uses", "").startswith("actions/checkout@"):
                assert step["with"]["persist-credentials"] is False
                assert step["with"]["ref"] == "${{ github.ref }}"


def test_release_promotes_the_verified_artifact_without_rebuilding() -> None:
    workflow = yaml.safe_load(
        (REPOSITORY_ROOT / ".github/workflows/pk-stack-release.yml").read_text(encoding="utf-8")
    )
    jobs = workflow["jobs"]
    helper = ".github/scripts/pkstack_ci_package.py verify"
    calls = {}
    for name, job in jobs.items():
        steps = [step for step in job["steps"] if helper in step.get("run", "")]
        assert len(steps) == 1
        calls[name] = steps[0]
        assert steps[0]["env"]["RELEASE_SHA"] == "${{ github.sha }}"
        assert steps[0]["env"]["EXPECTED_TAG"] == "${{ github.ref_name }}"
        assert steps[0]["env"]["RELEASE_REF"] == "${{ github.ref }}"
        run = "\n".join(step.get("run", "") for step in job["steps"])
        for forbidden in ("--pre-tag", "git archive", "uv build", "pytest", "unittest"):
            assert forbidden not in run
        assert "pkstack_ci_package.py build" not in run
        assert '--sha "$RELEASE_SHA" --tag "$EXPECTED_TAG"' in steps[0]["run"]
        if name != "publish":
            assert "gh release create" not in run
    publish = calls["publish"]
    for variable, output, flag in (
        ("SOURCE_RUN_ID", "source_run_id", "--run-id"),
        ("SOURCE_RUN_ATTEMPT", "source_run_attempt", "--run-attempt"),
        ("PACKAGE_ARTIFACT_ID", "artifact_id", "--artifact-id"),
        ("PACKAGE_ARTIFACT_DIGEST", "artifact_digest", "--artifact-digest"),
    ):
        assert publish["env"][variable] == "${{ needs.verify.outputs." + output + " }}"
        assert f'{flag} "${variable}"' in publish["run"]
    assert "--verify-tag" in publish["run"]
    assert 'cmp package.tar.gz "$archive"' in publish["run"]
    assert '--notes-file "$verified/notes.md"' in publish["run"]
