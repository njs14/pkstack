"""Regression checks for the public PKStack release metadata contract."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import tarfile
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
        assert "/absolute/path/to" not in text
    assert "PKSTACK_POWER" in (POWER_ROOT / "docs/usage.md").read_text(encoding="utf-8")


def test_release_reproves_tagged_default_branch_commit_and_portable_checksum() -> None:
    workflow_path = REPOSITORY_ROOT / ".github/workflows/pk-stack-release.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    parsed = yaml.safe_load(workflow)

    assert parsed["jobs"]["release"]["env"]["RELEASE_SHA"] == "${{ github.sha }}"
    assert parsed["jobs"]["release"]["env"]["EXPECTED_TAG"] == "${{ github.ref_name }}"
    trigger = parsed.get("on", parsed.get(True))
    assert trigger["push"]["tags"] == ["v[0-9]+.[0-9]+.[0-9]+"]
    assert "RELEASE_VERSION=${EXPECTED_TAG#v}" in workflow
    assert "refs/remotes/origin/$DEFAULT_BRANCH" in workflow
    assert "uv run --frozen pytest -q" in workflow
    assert "node --test .github/scripts/test_pkstack_pr_policy.js" in workflow
    assert "git archive --format=tar --prefix=pkstack/" in workflow
    assert '"$RELEASE_SHA:powers/pkstack"' in workflow
    assert "tar --create" not in workflow
    assert 'sha256sum "$(basename "$archive")"' in workflow
    assert 'sha256sum --check "$(basename "$checksum")"' in workflow
    assert 'sha256sum "$archive" >"$checksum"' not in workflow


def test_release_archive_repeats_exact_bytes_and_uses_commit_time(tmp_path: Path) -> None:
    workflow = yaml.safe_load(
        (REPOSITORY_ROOT / ".github/workflows/pk-stack-release.yml").read_text(encoding="utf-8")
    )
    build = next(
        step["run"]
        for step in workflow["jobs"]["release"]["steps"]
        if step["name"] == "Build deterministic PKStack Power archive and SHA-256"
    )
    # Exercise the actual archive/gzip commands, stopping before checksum
    # publication (sha256sum is not installed by default on macOS).
    archive_commands = build.split("\n(\n", 1)[0]
    assert archive_commands.rstrip().endswith('gzip --no-name --stdout "$raw_archive" >"$archive"')
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="Archive fixture",
        GIT_AUTHOR_EMAIL="archive@example.invalid",
        GIT_COMMITTER_NAME="Archive fixture",
        GIT_COMMITTER_EMAIL="archive@example.invalid",
        GIT_AUTHOR_DATE="2000-01-01T00:00:00+00:00",
        GIT_COMMITTER_DATE="2000-01-01T00:00:00+00:00",
    )
    repository = tmp_path / "repository"
    power = repository / "powers/pkstack"
    power.mkdir(parents=True)
    (power / "README.md").write_text("Power-only fixture\n", encoding="utf-8")
    (repository / "outside.txt").write_text("Do not ship\n", encoding="utf-8")

    def git(*arguments: str) -> str:
        return subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgSign=false", *arguments],
            cwd=repository,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    git("init", "--quiet")
    git("add", ".")
    git("commit", "--quiet", "--message", "Archive fixture")
    environment.update(RELEASE_SHA=git("rev-parse", "HEAD"), EXPECTED_TAG="v0.3.0")
    hashes = []
    for attempt in range(2):
        runner_temp = tmp_path / f"run-{attempt}"
        runner_temp.mkdir()
        subprocess.run(
            ["bash", "-c", archive_commands],
            cwd=repository,
            env={**environment, "RUNNER_TEMP": str(runner_temp)},
            check=True,
            capture_output=True,
        )
        archive = runner_temp / "pkstack-release/pkstack-v0.3.0.tar.gz"
        hashes.append(hashlib.sha256(archive.read_bytes()).hexdigest())
        with tarfile.open(archive, "r:gz") as package:
            members = package.getmembers()
            assert {member.name.rstrip("/") for member in members} == {
                "pkstack",
                "pkstack/README.md",
            }
            assert {member.mtime for member in members} == {946684800}
    assert hashes[0] == hashes[1]


def test_ci_static_analyzers_are_on_path_before_same_step_probe() -> None:
    workflow = (REPOSITORY_ROOT / ".github/workflows/pk-stack-ci.yml").read_text(encoding="utf-8")
    export_at = workflow.index('export PATH="$STATIC_TOOLS/bin:$PATH"')
    actionlint_probe_at = workflow.index("actionlint -version")
    shellcheck_probe_at = workflow.index("shellcheck --version")

    assert export_at < actionlint_probe_at < shellcheck_probe_at
