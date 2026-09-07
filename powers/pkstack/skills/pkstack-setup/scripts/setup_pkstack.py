#!/usr/bin/env python3
"""Power-local entrypoint for project bootstrap without global installation."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
POWER_ROOT = SCRIPT_PATH.parents[3]
if not (POWER_ROOT / "src" / "pkstack").is_dir():
    raise SystemExit("Run /pkstack-setup from the loaded Power source")
sys.path.insert(0, str(POWER_ROOT / "src"))

from pkstack.branding import DISPLAY_NAME  # noqa: E402

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
            "pkstack.bootstrap",
            *sys.argv[1:],
        ],
        environment,
    )

from pkstack.bootstrap import main  # noqa: E402

if __name__ == "__main__":
    main()
