from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def test_archify_cdp_lifecycle() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Archify requires optional Node.js 18+")
    result = subprocess.run(
        [node, "--test", str(Path(__file__).with_suffix(".mjs"))],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
