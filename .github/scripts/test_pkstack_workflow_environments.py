"""Trusted workflow interpreters must stay separate from the development environment."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = (
    ".github/workflows/pk-stack-upstream-maintenance-kiro.yml",
    ".github/workflows/pk-stack-upstream-candidate.yml",
)


class TrustedEnvironmentTests(unittest.TestCase):
    def test_each_trusted_sync_creates_its_own_working_interpreter(self):
        commands = []
        for name in WORKFLOWS:
            text = (ROOT / name).read_text().replace("\\\n", " ")
            commands.extend(
                (name, shlex.split(line.strip()))
                for line in text.splitlines()
                if "uv sync " in line and '--project "$TRUSTED' in line
            )
        self.assertEqual(len(commands), 4, "cover every trusted-controller synchronization")
        for index, (name, words) in enumerate(commands):
            with (
                self.subTest(workflow=name, site=index),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                trusted_root = root / "trusted"
                project = trusted_root / ".pkstack/projectctl"
                project.mkdir(parents=True)
                (project / "pyproject.toml").write_text(
                    '[project]\nname="trusted-environment-probe"\nversion="0.0.0"\n'
                    'requires-python=">=3.11"\ndependencies=[]\n'
                )
                candidate_environment = root / "candidate/.venv"
                environment = {
                    key: value
                    for key, value in os.environ.items()
                    if not key.startswith("UV_") and key != "VIRTUAL_ENV"
                }
                environment.update(
                    UV_PROJECT_ENVIRONMENT=str(candidate_environment),
                    UV_OFFLINE="1",
                    UV_PYTHON=sys.executable,
                )
                subprocess.run(
                    ["uv", "lock", "--no-config", "--project", str(project)],
                    env=environment,
                    check=True,
                    capture_output=True,
                    timeout=30,
                )
                # Interpret only the reviewed uv argv and leading environment assignment.
                # No workflow shell, candidate code, dependencies or hooks are executed.
                argv = [
                    word.replace("$TRUSTED_ROOT", str(trusted_root)).replace(
                        "$TRUSTED_PROJECTCTL_ROOT", str(project)
                    )
                    for word in words
                ]
                while argv and argv[0].startswith("UV_PROJECT_ENVIRONMENT="):
                    key, value = argv.pop(0).split("=", 1)
                    environment[key] = value
                self.assertEqual(argv[:2], ["uv", "sync"])
                subprocess.run(argv, env=environment, check=True, capture_output=True, timeout=30)
                interpreter = project / ".venv/bin/python"
                self.assertTrue(interpreter.is_file(), "trusted interpreter is missing")
                self.assertFalse(
                    candidate_environment.exists(), "trusted sync touched candidate env"
                )
                result = subprocess.run(
                    [str(interpreter), "-B", "-c", "import sys; print(sys.prefix)"],
                    env=environment,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                self.assertEqual(Path(result.stdout.strip()), project / ".venv")


if __name__ == "__main__":
    unittest.main()
