"""Exercise the human onboarding example through its installed controller."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

POWER_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = POWER_ROOT.parents[1]


def _json_documents(output: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    documents = []
    while output.strip():
        document, end = decoder.raw_decode(output.lstrip())
        assert isinstance(document, dict)
        documents.append(document)
        output = output.lstrip()[end:]
    return documents


def test_readme_demo_records_failure_before_repair_and_pass(tmp_path: Path) -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    blocks = re.findall(r"^```sh\n(.*?)^```", readme, flags=re.MULTILINE | re.DOTALL)
    walkthroughs = [block for block in blocks if block.startswith("PK_STACK_DEMO=$(mktemp")]
    assert len(walkthroughs) == 1, "Keep one complete executable first-run block in the README"
    source = POWER_ROOT / "examples/verified-goal-demo/account.py"
    source_before = source.read_bytes()
    environment = {
        key: value
        for key, value in os.environ.items()
        if key != "PYTHONPATH" and not key.startswith(("COV_CORE_", "COVERAGE_"))
    }
    environment.update(
        PK_STACK_POWER=str(POWER_ROOT),
        TMPDIR=str(tmp_path),
        PATH=os.pathsep.join((str(Path(sys.executable).parent), os.environ.get("PATH", ""))),
        UV_OFFLINE="1",
    )
    first_run = subprocess.run(
        ["/bin/sh", "-eu", "-c", walkthroughs[0]],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
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

    projects = list(tmp_path.glob("pk-stack-demo.*"))
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
        [".pk-stack/bin/projectctl", "goal", "verify", "--output", "json"],
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
