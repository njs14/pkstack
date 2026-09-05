"""Execute the real secretless verifier shell with isolated controller doubles."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

import pkstack_maintenance_guard as guard_module


SCRIPT = Path(__file__).with_name("verify_pkstack_attempt.sh")
SENTINEL = "UNTRUSTED_STDOUT_secret_like_value_123"


@unittest.skipUnless(
    shutil.which("bash") and shutil.which("jq"), "requires bash and jq"
)
class VerifierExecutionTests(unittest.TestCase):
    def execute(
        self,
        *,
        failure: bool = False,
        cleanup_failure: bool = False,
        proposal_reason: str = "",
        wrong_control_head: bool = False,
    ):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        project = root / "project"
        runner = root / "runner"
        trusted = root / "trusted"
        binary = root / "bin"
        for directory in (project, runner, trusted / ".venv/bin", binary):
            directory.mkdir(parents=True)
        (trusted / ".venv/bin/python").symlink_to(sys.executable)
        module = trusted / "src/pkstack"
        module.mkdir(parents=True)
        (module / "__main__.py").write_text(
            textwrap.dedent("""
            import json
            import os
            from pathlib import Path
            import sys

            args = sys.argv[1:]
            if args[0] == "setup" and os.environ["TEST_FAILURE"] == "true":
                print(os.environ["TEST_SENTINEL"])
                raise SystemExit(17)
            result = {"ok": True}
            if args[0] == "setup":
                result.update({key: [] for key in (
                    "conflicts", "created", "updated", "pending_updates", "stale_managed"
                )})
            elif args[:2] == ["upstream", "accept"]:
                result.update(source_id="alpha", expected_head="b" * 40, accepted=True)
                if "--dry-run" not in args:
                    Path(".pkstack-maintenance/proposal.json").unlink()
                    Path(".pkstack-maintenance").rmdir()
            elif args[:2] == ["goal", "status"]:
                result["goal"] = {"status": "passed", "max_attempts": 5, "attempt_count": 2}
            print(json.dumps(result))
        """),
            encoding="utf-8",
        )
        guard = root / "guard.py"
        guard.write_text(
            textwrap.dedent("""
            import json
            import os
            import sys

            args = sys.argv[1:]
            if "finalize-git-state" in args and os.environ["TEST_CLEANUP_FAILURE"] == "true":
                print(os.environ["TEST_SENTINEL"])
                raise SystemExit(19)
            result = {"ok": True}
            if "validate-detector" in args:
                result["drift_count"] = 0 if "post-accept" in args[-1] else 1
            elif "validate-proposal" in args:
                if os.environ["TEST_PROPOSAL_REASON"]:
                    print(os.environ["TEST_SENTINEL"], file=sys.stderr)
                    print(json.dumps({"ok": False, "reason": os.environ["TEST_PROPOSAL_REASON"]}))
                    raise SystemExit(1)
                result.update(source_id="alpha", expected_head="b" * 40)
            print(json.dumps(result))
        """),
            encoding="utf-8",
        )
        for name in ("git", "uv"):
            command = binary / name
            command.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            command.chmod(0o700)
        policy_test = project / ".github/scripts/test_pkstack_maintenance_guard.py"
        policy_test.parent.mkdir(parents=True)
        policy_test.write_text(
            "# Isolated immutable policy-test double.\n", encoding="utf-8"
        )
        (project / "powers/pkstack").mkdir(parents=True)
        (project / ".pkstack-maintenance").mkdir()
        (project / ".pkstack-maintenance/proposal.json").write_text(
            "{}", encoding="utf-8"
        )
        detector = runner / "detector.json"
        detector.write_text("{}", encoding="utf-8")
        control = runner / "control.json"
        control.write_text(
            json.dumps({
                "selected_source_id": "alpha",
                "expected_head": ("c" if wrong_control_head else "b") * 40,
            }),
            encoding="utf-8",
        )
        output = runner / "output"
        feedback = runner / "feedback"
        feedback.write_text("previous feedback", encoding="utf-8")
        environment = {
            "PATH": str(binary) + os.pathsep + os.environ["PATH"],
            "HOME": str(root),
            "BASE_SHA": "a" * 40,
            "RUNNER_TEMP": str(runner),
            "DETECTOR_PATH": str(detector),
            "CONTROL_PLAN_PATH": str(control),
            "FEEDBACK_PATH": str(feedback),
            "GOAL_STATUS_PATH": str(runner / "goal.json"),
            "GUARD_PATH": str(guard),
            "TRUSTED_PROJECTCTL_ROOT": str(trusted),
            "TRUSTED_ROOT": str(trusted),
            "ATTEMPT_NUMBER": "1",
            "GITHUB_RUN_ID": "9876",
            "GITHUB_OUTPUT": str(output),
            "READONLY_GITHUB_TOKEN": "noncredential-test-double",
            "GIT_BOUNDARY_STATE": str(runner / "boundary"),
            "TEST_FAILURE": str(failure).lower(),
            "TEST_CLEANUP_FAILURE": str(cleanup_failure).lower(),
            "TEST_PROPOSAL_REASON": proposal_reason,
            "TEST_SENTINEL": SENTINEL,
        }
        for key, name in (
            ("KIRO_BIN_DIR", "kiro-bin"),
            ("KIRO_HOME", "kiro-home"),
            ("KIRO_USER_HOME", "kiro-user"),
        ):
            (runner / name).mkdir()
            environment[key] = str(runner / name)
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            cwd=project,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        diagnostic_root = runner / "pkstack-verification-results"
        reports = list(diagnostic_root.glob("*.json"))
        self.assertEqual(len(reports), 1, result.stdout + result.stderr)
        raw = reports[0].read_text(encoding="utf-8")
        self.assertLess(len(raw.encode()), 2048)
        self.assertNotIn(SENTINEL, raw + result.stdout + result.stderr)
        self.assertIn(raw.strip(), result.stdout.splitlines())
        self.assertEqual(list(diagnostic_root.glob("*.stage")), [])
        self.assertEqual(list(diagnostic_root.glob("*.reason")), [])
        return result, json.loads(raw), output, feedback, runner

    def test_real_shell_success_reaches_complete_and_emits_only_fixed_metadata(self):
        result, report, output, feedback, runner = self.execute()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            report,
            {
                "schema_version": 1,
                "source_run_id": 9876,
                "base_sha": "a" * 40,
                "attempt": 1,
                "stage": "complete",
                "exit_code": 0,
                "cleanup_exit_code": 0,
                "passed": True,
                "reason": None,
            },
        )
        self.assertEqual(output.read_text(), "passed=true\nattempt=1\n")
        self.assertFalse(feedback.exists())
        self.assertFalse((runner / "pkstack-verify-1.log").exists())

    def test_real_shell_failure_keeps_untrusted_output_out_of_retained_report(self):
        result, report, output, feedback, runner = self.execute(failure=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            (
                report["stage"],
                report["exit_code"],
                report["cleanup_exit_code"],
                report["passed"],
            ),
            ("setup", 17, 0, False),
        )
        self.assertEqual(output.read_text(), "passed=false\nattempt=1\n")
        self.assertIn(
            SENTINEL, feedback.read_text()
        )  # Private repair input, never uploaded.
        self.assertFalse((runner / "pkstack-verify-1.log").exists())

    def test_cleanup_failure_is_retained_but_cannot_report_success(self):
        result, report, output, _, _ = self.execute(failure=True, cleanup_failure=True)
        self.assertEqual(result.returncode, 19, result.stdout + result.stderr)
        self.assertEqual(
            (report["exit_code"], report["cleanup_exit_code"], report["passed"]),
            (17, 19, False),
        )
        self.assertFalse(output.exists())


    def test_proposal_failures_retain_only_allowlisted_reason_codes(self):
        for reason in sorted(guard_module.PROPOSAL_FAILURE_REASONS):
            with self.subTest(reason=reason):
                result, report, output, feedback, _ = self.execute(proposal_reason=reason)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(
                    (report["stage"], report["reason"], report["exit_code"], report["passed"]),
                    ("proposal", reason, 1, False),
                )
                self.assertEqual(output.read_text(), "passed=false\nattempt=1\n")
                self.assertIn(SENTINEL, feedback.read_text())
                self.assertIn(f"Proposal validation failed: {reason}", feedback.read_text())

    def test_candidate_controlled_reason_cannot_escape_to_public_diagnostics(self):
        result, report, _, _, _ = self.execute(proposal_reason=SENTINEL + "\n::warning::injection")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((report["stage"], report["reason"]), ("proposal", "proposal-invalid"))
        self.assertNotIn("injection", result.stdout + result.stderr + json.dumps(report))

    def test_proposal_guard_success_must_still_match_control_plan_head(self):
        result, report, _, feedback, _ = self.execute(wrong_control_head=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            (report["stage"], report["reason"], report["passed"]),
            ("proposal", "proposal-control-mismatch", False),
        )
        self.assertIn("Proposal validation failed: proposal-control-mismatch", feedback.read_text())


if __name__ == "__main__":
    unittest.main()
