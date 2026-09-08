#!/usr/bin/env python3
"""The shared Python static gate must cover every embedded body and fail closed."""

from __future__ import annotations

import shutil
import textwrap
import unittest
from pathlib import Path

import pkstack_python_static as static

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_BODIES = {
    (".github/scripts/run_kiro_maintenance_attempt.sh", 15),
    (".github/scripts/verify_pkstack_attempt.sh", 128),
    (".github/scripts/verify_pkstack_attempt.sh", 399),
    (".github/workflows/pk-stack-kiro-permission-smoke.yml", 99),
    (".github/workflows/pk-stack-kiro-permission-smoke.yml", 240),
    (".github/workflows/pk-stack-upstream-maintenance-kiro.yml", 220),
}


def body(text: str, origin: str = "fixture.sh", line: int = 1) -> static.EmbeddedBody:
    return static.EmbeddedBody(origin, line, textwrap.dedent(text).lstrip("\n"))


def extract(source: str, *, workflow: bool = False) -> list[static.EmbeddedBody]:
    lines = textwrap.dedent(source).lstrip("\n").splitlines()
    allowed = static._run_block_ranges(lines, "fixture") if workflow else None
    return static._extract_from_lines(lines, "fixture", allowed)


class ExtractionTests(unittest.TestCase):
    def test_every_maintained_embedded_body_is_found_with_a_stable_identity(self) -> None:
        bodies = static.embedded_bodies(ROOT)
        self.assertEqual({(item.origin, item.line) for item in bodies}, EXPECTED_BODIES)
        self.assertEqual(len({item.name for item in bodies}), len(bodies))
        for item in bodies:
            with self.subTest(origin=item.origin, line=item.line):
                self.assertTrue(item.name.endswith(f"__L{item.line}.py"))
                self.assertTrue(item.text.endswith("\n"))
                compile(item.text, item.name, "exec")  # parse only; never executed

    def test_multiline_commands_and_indented_run_blocks_are_recognized(self) -> None:
        continued = extract(
            """
            python3 - "$one" \\
              "$two" <<'PY'
            import sys

            print(sys.argv)
            PY
            """
        )
        self.assertEqual(len(continued), 1)
        self.assertEqual(continued[0].text, "import sys\n\nprint(sys.argv)\n")
        indented = extract(
            """
            jobs:
              step:
                run: |
                  helper() {
                    python3 - <<'PY'
                  import sys

                  print(sys.argv)
                  PY
                  }
            """,
            workflow=True,
        )
        self.assertEqual(len(indented), 1)
        self.assertEqual(indented[0].text, "import sys\n\nprint(sys.argv)\n")

    def test_here_strings_and_non_python_here_documents_are_left_alone(self) -> None:
        self.assertEqual(extract('jq -e ".ok" <<<"$payload"\n'), [])
        self.assertEqual(extract("python3 - <<<'PY'\n"), [])
        self.assertEqual(extract("cat >file <<'EOF'\nplain text\nEOF\n"), [])


class AmbiguityTests(unittest.TestCase):
    def test_unrecognized_or_ambiguous_python_here_documents_are_rejected(self) -> None:
        cases = {
            "multiple heredocs": "python3 - <<'PY' <<'OTHER'\nprint(1)\nPY\nprint(2)\nOTHER\n",
            "unrecognized command": "runner - <<'PY'\nimport sys\nPY\n",
            "unquoted delimiter": "python3 - <<PY\nimport sys\nPY\n",
            "tab stripping": "python3 - <<-'PY'\nimport sys\nPY\n",
            "unterminated": "python3 - <<'PY'\nimport sys\n",
            "outside block indent": (
                "jobs:\n  step:\n    run: |\n      python3 - <<'PY'\nimport sys\n      PY\n"
            ),
        }
        for label, source in cases.items():
            with self.subTest(case=label), self.assertRaises(static.StaticCheckError):
                extract(source, workflow=label not in {"unrecognized command", "multiple heredocs"})

    def test_python_here_document_outside_a_run_script_is_rejected(self) -> None:
        for label, source in {
            "no run block": (
                "jobs:\n  step:\n    with:\n      x: python3 - <<'PY'\nimport sys\nPY\n"
            ),
            "folded run block": "jobs:\n  step:\n    run: >\n      python3 - <<'PY'\n",
        }.items():
            with self.subTest(case=label), self.assertRaises(static.StaticCheckError):
                extract(source, workflow=True)

    def test_an_empty_surface_is_a_failure_rather_than_a_silent_pass(self) -> None:
        with self.assertRaises(static.StaticCheckError):
            static.check_bodies(ROOT, [])


@unittest.skipUnless(shutil.which("uv"), "uv is required for the locked analyzers")
class StagedAnalysisTests(unittest.TestCase):
    """The staged copies are analyzed with the locked tools, and never executed."""

    def test_the_maintained_embedded_bodies_pass_every_locked_check(self) -> None:
        static.check_bodies(ROOT, static.embedded_bodies(ROOT))

    def test_a_lint_failure_cannot_be_accepted(self) -> None:
        with self.assertRaises(static.StaticCheckError):
            static.check_bodies(ROOT, [body("import sys\nimport json\nprint(sys, json)\n")])

    def test_a_format_failure_cannot_be_accepted(self) -> None:
        with self.assertRaises(static.StaticCheckError):
            static.check_bodies(ROOT, [body("import sys\n\nprint( sys.argv )\n")])

    def test_a_type_error_cannot_be_accepted(self) -> None:
        with self.assertRaises(static.StaticCheckError):
            static.check_bodies(ROOT, [body("import sys\n\nprint(len(sys.maxsize))\n")])


if __name__ == "__main__":
    unittest.main()
