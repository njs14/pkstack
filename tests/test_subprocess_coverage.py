from __future__ import annotations

import configparser
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_coverage_patch_records_code_executed_only_in_child_process(tmp_path: Path) -> None:
    config = configparser.ConfigParser()
    config.read(ROOT / ".coveragerc")
    config["run"]["source"] = "child_behavior"
    configuration = tmp_path / ".coveragerc"
    with configuration.open("w") as stream:
        config.write(stream)
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "child_behavior.py").write_text(
        'def run():\n    return "child observed"\n\nprint(run())\n'
    )
    (tmp_path / "test_child.py").write_text(
        "import subprocess, sys\n"
        "def test_child():\n"
        '    result = subprocess.check_output([sys.executable, "child_behavior.py"], text=True)\n'
        '    assert result == "child observed\\n"\n'
    )
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COV_CORE_", "COVERAGE_", "PYTEST_", "PKSTACK_CHECK_"))
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-c",
            "pytest.ini",
            "--cov=child_behavior",
            "--cov-config=.coveragerc",
            "--cov-report=json:coverage.json",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    coverage = json.loads((tmp_path / "coverage.json").read_text())
    child = coverage["files"]["child_behavior.py"]
    assert child["executed_lines"] == [1, 2, 4]
    assert child["missing_lines"] == []
    assert coverage["totals"]["percent_covered"] == 100
