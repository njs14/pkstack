"""Exercise documented onboarding mechanically, without claiming Kiro repair proof."""

from __future__ import annotations

import ast
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

POWER_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = POWER_ROOT.parents[1]


def _shell_blocks(path: Path) -> list[str]:
    return re.findall(r"^```sh\n(.*?)^```", path.read_text(), flags=re.MULTILINE | re.DOTALL)


def _clean_environment(tmp_path: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PKSTACK_POWER", "PKSTACK_PACKAGE", "VIRTUAL_ENV"}
        and not key.startswith(("COV_CORE_", "COVERAGE_", "UV_"))
    }
    environment.update(
        TMPDIR=str(tmp_path),
        PATH=os.pathsep.join((str(Path(sys.executable).parent), os.environ.get("PATH", ""))),
        # uvx resolves package metadata; a locked sync alone does not warm it.
        # These walkthroughs run in the dependency-enabled packaging lane.
        UV_CACHE_DIR=str(tmp_path / "uv-cache"),
        UV_TOOL_DIR=str(tmp_path / "uv-tools"),
        UV_TOOL_BIN_DIR=str(tmp_path / "uv-tool-bin"),
    )
    return environment


def _copy_power(destination: Path) -> None:
    shutil.copytree(
        POWER_ROOT,
        destination,
        ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", ".ruff_cache"),
    )


def _run_blocks(
    blocks: list[str], *, cwd: Path, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/sh", "-eu", "-c", "\n".join(blocks)],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


@pytest.mark.parametrize("layout", ["checkout", "standalone"])
def test_documented_source_and_install_blocks_work_independently(
    tmp_path: Path, layout: str
) -> None:
    source = tmp_path / "source with spaces" / "pkstack"
    power = source / "powers/pkstack" if layout == "checkout" else source
    _copy_power(power)
    environment = _clean_environment(tmp_path)
    usage = _shell_blocks(POWER_ROOT / "docs/usage.md")
    assignment = (
        'export PKSTACK_POWER="$PWD/powers/pkstack"'
        if layout == "checkout"
        else 'export PKSTACK_POWER="$PWD"'
    )
    capture = next(block for block in usage if block.startswith(assignment + "\n"))
    if layout == "checkout":
        # Substitute a local fixture origin; execute the README clone/cd/assignment literally.
        for command in (
            ["git", "init", "-q", str(source)],
            ["git", "-C", str(source), "add", "."],
            [
                "git",
                "-C",
                str(source),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-qm",
                "fixture",
            ],
        ):
            subprocess.run(command, check=True, capture_output=True)
        source_block = next(
            block
            for block in _shell_blocks(REPOSITORY_ROOT / "README.md")
            if block.startswith("git clone ")
        ).replace("https://github.com/njs14/pkstack.git", shlex.quote(str(source)))
        cwd = tmp_path / "clone parent with spaces"
        cwd.mkdir()
    else:
        source_block = next(
            block
            for block in _shell_blocks(POWER_ROOT / "README.md")
            if block.startswith(assignment + "\n")
        )
        cwd = source
    target = tmp_path / "application with spaces"
    target.mkdir()
    preview = next(block for block in usage if "setup --dry-run --output json" in block)
    apply = next(block for block in usage if "setup --output json" in block)
    check = next(block for block in usage if block.startswith('cd "$PKSTACK_PROJECT"\n'))
    target_capture = next(
        block for block in usage if block.startswith('cd "/absolute/path/to/your/project"\n')
    ).replace('"/absolute/path/to/your/project"', shlex.quote(str(target)))
    result = _run_blocks(
        [
            source_block,
            'test -f "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py"',
            capture,
            target_capture,
            preview,
            apply,
            check,
            apply,
        ],
        cwd=cwd,
        environment=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    inventory = _json_documents(result.stdout[result.stdout.index("{") :])
    preflight, installed, version, doctor, knowledge, repeated = inventory
    assert preflight["ok"] and preflight["dry_run"]
    assert installed["ok"] and installed["created"]
    assert version["name"] == "pkstack"
    assert doctor["ok"] and knowledge["ok"]
    assert repeated["ok"] and not repeated["created"] and not repeated["updated"]
    assert Path(installed["root"]) == target


def _json_documents(output: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    documents = []
    while output.strip():
        document, end = decoder.raw_decode(output.lstrip())
        assert isinstance(document, dict)
        documents.append(document)
        output = output.lstrip()[end:]
    return documents


def test_linked_first_task_records_failure_before_repair_and_pass(tmp_path: Path) -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    assert "powers/pkstack/docs/first-task.md" in readme
    blocks = _shell_blocks(POWER_ROOT / "docs/first-task.md")
    walkthroughs = [block for block in blocks if block.startswith("PKSTACK_DEMO=$(mktemp")]
    goals = [
        block for block in blocks if "pkstack goal start" in block and block.startswith("uvx ")
    ]
    assert len(walkthroughs) == len(goals) == 1, "Keep one setup and one failure block in the guide"
    checkout = tmp_path / "checkout with spaces"
    _copy_power(checkout / "powers/pkstack")
    source = checkout / "powers/pkstack/examples/verified-goal-demo/account.py"
    source_before = source.read_bytes()
    environment = _clean_environment(tmp_path)
    capture = next(
        block
        for block in _shell_blocks(POWER_ROOT / "docs/usage.md")
        if block.startswith('export PKSTACK_POWER="$PWD/powers/pkstack"\n')
    )
    apply = next(
        block for block in blocks if "pkstack setup --output" in block and block.startswith("uvx ")
    )
    guard = next(block for block in blocks if block.startswith(': "${PKSTACK_POWER:?'))
    first_run = _run_blocks(
        [capture, guard, walkthroughs[0], apply, goals[0]],
        cwd=checkout,
        environment=environment,
    )
    assert first_run.returncode == 1, first_run.stdout + first_run.stderr
    documents = _json_documents(first_run.stdout)
    assert len(documents) == 5, first_run.stdout
    preview, setup, doctor, started, failed = documents
    assert preview["ok"] and preview["dry_run"]
    assert setup["ok"] and not setup["dry_run"]
    assert doctor["ok"], doctor
    assert started["goal"]["attempt_count"] == 0
    assert failed["goal"]["status"] == "active"
    assert failed["goal"]["attempt_count"] == 1
    assert failed["goal"]["history"][0]["passed"] is False
    assert "Ran 4 tests" in failed["goal"]["last_result"]["stderr"]

    projects = list(tmp_path.glob("pkstack-demo.*"))
    assert len(projects) == 1
    project = projects[0]
    tests = project / "tests/test_account.py"
    tests_before = tests.read_bytes()
    test_names = {
        node.name
        for node in ast.walk(ast.parse(tests_before))
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }
    assert test_names == {
        "test_accepts_plain_twelve_digit_identifier",
        "test_removes_spaces_and_hyphens",
        "test_rejects_non_digits",
        "test_rejects_wrong_length",
    }
    (project / "account.py").write_text(
        "def normalize_account_id(value: str) -> str:\n"
        "    normalized = value.replace(' ', '').replace('-', '')\n"
        "    if len(normalized) != 12 or not normalized.isdecimal():\n"
        "        raise ValueError('Account ID must contain 12 digits')\n"
        "    return normalized\n",
        encoding="utf-8",
    )
    verified = subprocess.run(
        [
            "uvx",
            "--python",
            ">=3.11",
            "--from",
            str(checkout / "powers/pkstack"),
            "pkstack",
            "goal",
            "verify",
            "--output",
            "json",
        ],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert verified.returncode == 0, verified.stdout + verified.stderr
    passed = json.loads(verified.stdout)["goal"]
    assert passed["status"] == "passed"
    assert passed["contract"] == started["goal"]["contract"]
    assert [attempt["passed"] for attempt in passed["history"]] == [False, True]
    assert "Ran 4 tests" in passed["last_result"]["stderr"]
    assert tests.read_bytes() == tests_before
    assert source.read_bytes() == source_before
