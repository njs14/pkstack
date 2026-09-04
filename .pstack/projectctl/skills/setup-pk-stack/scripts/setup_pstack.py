#!/usr/bin/env python3
"""Power-local entrypoint for project bootstrap without global installation."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
POWER_ROOT = SCRIPT_PATH.parents[3]
if not (POWER_ROOT / "src" / "pstack_kiro").is_dir():
    for ancestor in SCRIPT_PATH.parents:
        cached_controller = ancestor / ".pstack" / "projectctl"
        if cached_controller == POWER_ROOT or cached_controller.is_dir():
            POWER_ROOT = cached_controller
            break

sys.path.insert(0, str(POWER_ROOT / "src"))

from pstack_kiro.branding import DISPLAY_NAME  # noqa: E402

if sys.version_info < (3, 11):
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit(f"{DISPLAY_NAME} setup requires Python 3.11+ or uv")
    environment = os.environ.copy()
    source_root = str(POWER_ROOT / "src")
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        os.pathsep.join((source_root, existing_pythonpath)) if existing_pythonpath else source_root
    )
    os.execve(
        uv,
        [
            uv,
            "run",
            "--quiet",
            "--isolated",
            "--locked",
            "--project",
            str(POWER_ROOT),
            "python",
            "-m",
            "pstack_kiro.bootstrap",
            *sys.argv[1:],
        ],
        environment,
    )

from pstack_kiro.bootstrap import main  # noqa: E402

if __name__ == "__main__":
    main()
