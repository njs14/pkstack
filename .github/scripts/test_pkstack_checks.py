"""Behavioral coverage for CI selection and complete shared execution evidence."""

import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pkstack_checks as checks
import pkstack_pytest_evidence as plugin


def change(path, status="M", other=None):
    return {"status": status, "paths": [path] + ([other] if other else [])}


def context_and_evidence():
    context = {
        "schema": checks.SCHEMA,
        "commit": "a" * 40,
        "config_digest": "b" * 64,
        "profile": "normal",
        "browser_profile": "full",
        "run_id": "42",
        "run_attempt": "1",
    }
    ids = [
        "tests/test_branding.py::test_contract",
        "tests/test_archify_reader_layout.py::test_browser",
        "tests/test_packaging.py::test_install",
        checks.KIRO_SENTINEL,
        *[f"tests/test_core.py::test_behavior_{i}" for i in range(60)],
    ]
    results = []
    for nodeid in ids:
        skipped = nodeid == checks.KIRO_SENTINEL
        result = {
            "nodeid": nodeid,
            "outcome": "skipped" if skipped else "passed",
            "phases": {"setup": "skipped", "teardown": "passed"}
            if skipped
            else {"setup": "passed", "call": "passed", "teardown": "passed"},
        }
        if skipped:
            result["skip_reason"] = checks.KIRO_SKIP_REASON
        results.append(result)
    return context, {
        "collection": ids,
        "collection_digest": checks.digest(ids),
        "results": results,
        "issues": [],
        "exit_status": 0,
        "outcome": "passed",
    }


class ProfileTests(unittest.TestCase):
    def test_stacked_pr_checks_keep_artifact_promotion_main_only(self):
        workflow = (Path(__file__).resolve().parents[1] / "workflows/pk-stack-ci.yml").read_text()
        triggers = workflow.split("permissions:", 1)[0]
        self.assertIn("  push:\n    branches: [main]", triggers)
        self.assertIn("  pull_request:\n", triggers)
        self.assertNotIn("branches:", triggers.split("  pull_request:\n", 1)[1])
        self.assertNotIn("pull_request_target", workflow)
        jobs = [
            line[2:-1]
            for line in workflow.split("\njobs:\n", 1)[1].splitlines()
            if line.startswith("  ") and not line.startswith("   ") and line.endswith(":")
        ]
        self.assertEqual(jobs, ["deterministic", "package"])
        package = workflow.split("\n  package:\n", 1)[1]
        self.assertIn("needs: deterministic", package)
        self.assertIn(
            "(github.event_name == 'push' || github.event_name == 'workflow_dispatch') "
            "&& github.ref == 'refs/heads/main'",
            package,
        )
        self.assertIn("needs.deterministic.result == 'success'", package)
        self.assertNotIn("matrix:", workflow)
        self.assertNotIn("download-artifact", workflow)
        self.assertNotIn("aggregate", workflow)

    def test_only_enumerated_reports_take_fast_path(self):
        for path in (
            "Wiki/knowledge/pkstack/release-record.md",
            "reviews/fable-final.md",
            "reviews/kiro-final-campaign.md",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    checks.execution_profile("pull_request", [change(path)]),
                    ("reports", "none"),
                )
        for path in (
            "reviews/fable-review-prompt.md",
            "reviews/acceptance-criteria.md",
            "reviews/new-report.md",
            "reviews/release-030-future.md",
            "reviews/release-status.md",
            "reviews/release-030-composition.md",
            "reviews/release-status.json",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    checks.execution_profile("pull_request", [change(path)])[0],
                    "normal",
                )

    def test_main_mixed_unknown_and_cross_boundary_renames_get_normal(self):
        report = change("Wiki/knowledge/pkstack/release-record.md")
        cases = [
            ("push", [report]),
            ("pull_request", []),
            ("pull_request", [report, change("powers/pkstack/src/pkstack/cli.py")]),
            ("pull_request", [change("Wiki/knowledge/pkstack/release-record.md", "U")]),
            (
                "pull_request",
                [
                    change(
                        "powers/pkstack/src/pkstack/cli.py",
                        "R100",
                        "Wiki/knowledge/pkstack/release-record.md",
                    )
                ],
            ),
        ]
        for event, changes in cases:
            with self.subTest(event=event, changes=changes):
                self.assertEqual(checks.execution_profile(event, changes)[0], "normal")
        self.assertEqual(checks.execution_profile("push", [report])[1], "full")

    def test_browser_expands_for_all_runtime_harness_and_lock_inputs(self):
        for path in (
            "powers/pkstack/skills/archify/upstream/viewer.js",
            ".kiro/skills/archify/viewer.js",
            "tests/test_archify_reader_layout.py",
            "tests/fixtures/archify.json",
            "powers/pkstack/uv.lock",
            "pyproject.toml",
            ".github/scripts/pkstack_checks.py",
            "tests/conftest.py",
            "package.json",
            "bun.lockb",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    checks.execution_profile("pull_request", [change(path)]),
                    ("normal", "full"),
                )
        self.assertEqual(
            checks.execution_profile("pull_request", [change("powers/pkstack/src/pkstack/cli.py")]),
            ("normal", "smoke"),
        )

    def test_git_nul_records_preserve_spaces_and_renames(self):
        raw = (
            "R100\0reviews/old report.md\0Wiki/knowledge/pkstack/release-record.md\0M\0source.py\0"
        )
        self.assertEqual(
            checks.parse_changes(raw)[0]["paths"],
            ["reviews/old report.md", "Wiki/knowledge/pkstack/release-record.md"],
        )
        for raw in ("R100\0one\0", "Z\0path\0", "M\0"):
            with self.assertRaises(ValueError):
                checks.parse_changes(raw)

    def test_full_scope_includes_every_product_test_and_fast_is_explicit(self):
        _, evidence = context_and_evidence()
        for nodeid in evidence["collection"]:
            self.assertTrue(checks.selected_test(nodeid, "full"))
        self.assertTrue(checks.selected_test("tests/test_branding.py::new_test", "fast"))
        self.assertFalse(checks.selected_test("tests/test_core.py::new_test", "fast"))


class EvidenceTests(unittest.TestCase):
    def test_complete_execution_and_documented_sentinel_pass(self):
        _, evidence = context_and_evidence()
        self.assertEqual(checks.verify_tests(evidence, "full"), 64)

    def test_missing_duplicate_failed_cancelled_or_partial_results_fail(self):
        for mode in (
            "missing",
            "duplicate",
            "failure",
            "collection",
            "phases",
            "exit",
            "issue",
            "empty",
        ):
            with self.subTest(mode=mode):
                _, evidence = context_and_evidence()
                if mode == "missing":
                    evidence["results"].pop()
                elif mode == "duplicate":
                    evidence["results"].append(copy.deepcopy(evidence["results"][0]))
                elif mode == "failure":
                    evidence["outcome"] = "failed"
                elif mode == "collection":
                    evidence["collection"] = list(reversed(evidence["collection"]))
                    evidence["collection_digest"] = checks.digest(evidence["collection"])
                elif mode == "phases":
                    evidence["results"][0]["phases"].pop("teardown")
                elif mode == "exit":
                    evidence["exit_status"] = 2
                elif mode == "empty":
                    evidence["collection"] = []
                    evidence["collection_digest"] = checks.digest([])
                else:
                    evidence["issues"] = ["duplicate phase"]
                with self.assertRaises(ValueError):
                    checks.verify_tests(evidence, "full")

    def test_any_skip_other_than_exact_kiro_sentinel_fails(self):
        for mode in ("test", "reason", "teardown"):
            _, evidence = context_and_evidence()
            result = next(r for r in evidence["results"] if r["nodeid"] == checks.KIRO_SENTINEL)
            if mode == "test":
                result = evidence["results"][0]
                result.update(
                    outcome="skipped",
                    skip_reason=checks.KIRO_SKIP_REASON,
                    phases={"setup": "skipped", "teardown": "passed"},
                )
            elif mode == "reason":
                result["skip_reason"] = "Chrome unavailable"
            else:
                result["phases"].pop("teardown")
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                checks.verify_tests(evidence, "full")


class PluginTests(unittest.TestCase):
    def test_collection_and_phase_reports_detect_incomplete_or_repeated_execution(self):
        for mode in ("passed", "missing-teardown", "duplicate-call", "failed-setup", "cancelled"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "product.json"
                env = {"PKSTACK_CHECK_SCOPE": "full", "PKSTACK_CHECK_EVIDENCE": str(path)}
                with patch.dict(checks.os.environ, env):
                    deselected = []
                    config = SimpleNamespace(
                        hook=SimpleNamespace(
                            pytest_deselected=lambda sink=deselected, **kw: sink.extend(kw["items"])
                        )
                    )
                    plugin.pytest_configure(config)
                    session = SimpleNamespace(config=config)
                    ids = [
                        "tests/test_branding.py::test_contract",
                        "tests/test_core.py::test_behavior",
                    ]
                    items = [SimpleNamespace(nodeid=nodeid) for nodeid in ids]
                    plugin.pytest_collection_modifyitems(session, config, items)
                    self.assertEqual([item.nodeid for item in items], ids)
                    self.assertEqual(deselected, [])
                    for nodeid in ids:
                        phases = ["setup", "call", "teardown"]
                        if mode == "missing-teardown":
                            phases.pop()
                        if mode == "duplicate-call":
                            phases.insert(2, "call")
                        if mode == "failed-setup":
                            phases = ["setup", "teardown"]
                        for phase in phases:
                            plugin.pytest_runtest_logreport(
                                SimpleNamespace(
                                    nodeid=nodeid,
                                    when=phase,
                                    skipped=False,
                                    duration=0.25,
                                    outcome="failed"
                                    if mode == "failed-setup" and phase == "setup"
                                    else "passed",
                                )
                            )
                    plugin.pytest_sessionfinish(session, 2 if mode == "cancelled" else 0)
                    evidence = json.loads(path.read_text())
                    if mode == "passed":
                        self.assertEqual(checks.verify_tests(evidence, "full"), 2)
                    else:
                        with self.assertRaises(ValueError):
                            checks.verify_tests(evidence, "full")


class PytestProcessTests(unittest.TestCase):
    def test_real_runner_rejects_skips_failures_interruptions_and_early_exit(self):
        repository = Path(__file__).resolve().parents[2]
        cases = {
            "passed": "assert True",
            "failed": "assert False",
            "skip": "pytest.skip('Chrome is unavailable')",
            "cancelled": "raise KeyboardInterrupt()",
            "early-exit": "pytest.exit('incomplete', returncode=0)",
        }
        real_run = subprocess.run
        for mode, body in cases.items():
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                tests = root / "tests"
                tests.mkdir()
                # Only the test collection is replaced; exercise the actual shared
                # runner, locked tooling, evidence plugin and basetemp creation.
                (root / ".github").symlink_to(repository / ".github", target_is_directory=True)
                (root / "powers").mkdir()
                (root / "powers/pkstack").symlink_to(
                    repository / "powers/pkstack", target_is_directory=True
                )
                (tests / "test_probe.py").write_text(
                    f"import pytest\ndef test_first(tmp_path):\n    {body}\n"
                    "def test_second(tmp_path):\n    assert tmp_path.is_dir()\n"
                )
                output = root / "checks"
                output.mkdir()

                def capture(command, **kwargs):
                    return real_run(command, capture_output=True, text=True, timeout=30, **kwargs)

                with (
                    patch.dict(os.environ, {"UV_PROJECT_ENVIRONMENT": str(repository / ".venv")}),
                    patch.object(checks.subprocess, "run", side_effect=capture),
                ):
                    if mode == "passed":
                        data = checks.run_product(root, {"browser_profile": "full"}, "full", output)
                        self.assertEqual(checks.verify_tests(data, "full"), 2)
                    else:
                        with self.assertRaises(subprocess.CalledProcessError):
                            checks.run_product(root, {"browser_profile": "full"}, "full", output)
                        data = json.loads((output / "diagnostics/product.json").read_text())
                        with self.assertRaises(ValueError):
                            checks.verify_tests(data, "full")


class GitPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in (
            ".github/scripts/check.py",
            "powers/pkstack/pyproject.toml",
            "powers/pkstack/uv.lock",
            ".coveragerc",
            "pytest.ini",
            "maintenance/package-content.json",
            "ruff.toml",
            "ty.toml",
            "maintenance/knowledge-coverage.json",
            "Wiki/knowledge/pkstack/release-record.md",
        ):
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("baseline\n")
        for args in (
            ("init", "-q"),
            ("config", "user.email", "test@example.com"),
            ("config", "user.name", "Test"),
        ):
            self.git(*args)
        self.commit("base")
        self.base = self.git("rev-parse", "HEAD")
        self.environment = patch.dict(checks.os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True).strip()

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-qm", message)

    def test_local_candidate_checks_bind_checkout_under_workflow_run(self):
        with patch.dict(
            checks.os.environ, {"GITHUB_EVENT_NAME": "workflow_run", "GITHUB_SHA": "f" * 40}
        ):
            context = checks.make_context(self.root, "local")
            checks.validate_context(context, self.root)
            (self.root / "new.py").write_text("changed\n")
            self.commit("moved candidate")
            with self.assertRaises(ValueError):
                checks.validate_context(context, self.root)

    def test_dispatched_ci_requires_its_exact_main_commit_and_complete_coverage(self):
        event = self.root / "event.json"
        event.write_text(json.dumps({"inputs": {"expected_sha": self.base}}))
        with patch.dict(
            checks.os.environ,
            {
                "GITHUB_EVENT_NAME": "workflow_dispatch",
                "GITHUB_EVENT_PATH": str(event),
                "GITHUB_SHA": self.base,
                "GITHUB_REF": "refs/heads/main",
            },
        ):
            context = checks.make_context(self.root, "workflow_dispatch")
            self.assertEqual((context["profile"], context["browser_profile"]), ("normal", "full"))
            checks.validate_context(context, self.root)
            for expected in ("f" * 40, "", None):
                event.write_text(json.dumps({"inputs": {"expected_sha": expected}}))
                with self.assertRaisesRegex(ValueError, "expected main commit"):
                    checks.validate_context(context, self.root)
            event.write_text(json.dumps({"inputs": {"expected_sha": self.base}}))
            checks.os.environ["GITHUB_REF"] = "refs/heads/other"
            with self.assertRaisesRegex(ValueError, "expected main commit"):
                checks.validate_context(context, self.root)

    def test_hosted_identity_still_rejects_the_wrong_github_sha(self):
        context = checks.make_context(self.root, "push")
        with (
            patch.dict(checks.os.environ, {"GITHUB_EVENT_NAME": "push", "GITHUB_SHA": "f" * 40}),
            self.assertRaises(ValueError),
        ):
            checks.validate_context(context, self.root)

    def test_plan_rejects_forged_changes_and_changed_configuration(self):
        (self.root / "Wiki/knowledge/pkstack/release-record.md").write_text("updated\n")
        self.commit("report")
        plan = checks.make_context(self.root, "pull_request", self.base)
        checks.validate_context(plan, self.root)
        altered = copy.deepcopy(plan)
        altered["changes"] = []
        with self.assertRaises(ValueError):
            checks.validate_context(altered, self.root)
        (self.root / ".github/scripts/check.py").write_text("changed\n")
        with self.assertRaises(ValueError):
            checks.validate_context(plan, self.root)

    def test_report_check_sees_whitespace_in_earlier_pr_commit(self):
        path = self.root / "Wiki/knowledge/pkstack/release-record.md"
        path.write_text("bad trailing space \n")
        self.commit("earlier whitespace")
        (self.root / "Wiki/knowledge/pkstack/later.md").write_text("later valid report\n")
        self.commit("later clean")
        plan = checks.make_context(self.root, "pull_request", self.base)
        with self.assertRaises(subprocess.CalledProcessError):
            checks.check_reports(self.root, plan["changes"], plan["base"])

    def test_changed_coverage_manifest_invalidates_the_plan(self):
        plan = checks.make_context(self.root, "local")
        (self.root / "maintenance/knowledge-coverage.json").write_text("changed\n")
        with self.assertRaises(ValueError):
            checks.validate_context(plan, self.root)

    def test_reports_validate_relative_links_and_allow_machine_evidence(self):
        path = self.root / "Wiki/knowledge/pkstack/release-record.md"
        path.write_text(
            "[config](../../../powers/pkstack/pyproject.toml) [web](https://example.com) "
            "[machine](/private/tmp/old-log)\n"
        )
        self.commit("valid links")
        changes = [change("Wiki/knowledge/pkstack/release-record.md")]
        self.assertEqual(
            checks.check_reports(self.root, changes, self.base),
            ["Wiki/knowledge/pkstack/release-record.md"],
        )
        path.write_text("[missing](missing.md)\n")
        with self.assertRaises(ValueError):
            checks.check_reports(self.root, changes, self.base)
        path.write_text("[outside](../../../../outside.md)\n")
        with self.assertRaises(ValueError):
            checks.check_reports(self.root, changes, self.base)


class SharedGateTests(unittest.TestCase):
    def test_shared_policy_retains_static_workflow_shell_and_knowledge_gates(self):
        root = Path(__file__).resolve().parents[2]
        with (
            patch.object(checks, "run_commands") as commands,
            patch.object(checks.static, "run_static_checks") as static,
        ):
            checks.run_policy(root)
        static.assert_called_once_with(root)
        argv = [command for call in commands.call_args_list for command in call.args[0]]
        self.assertEqual(argv[0][0], "actionlint")
        self.assertEqual(argv[1][0], "shellcheck")
        self.assertIn("unittest", argv[2])
        self.assertEqual(argv[3], ["node", "--test", ".github/scripts/test_pkstack_pr_policy.js"])
        self.assertEqual([command[1] for command in argv[4:]], ["version", "feature", "knowledge"])

    def test_absent_tools_cannot_silently_skip_policy_coverage(self):
        for missing in ("uv", "bash", "jq", "node", "actionlint", "shellcheck"):
            with (
                self.subTest(missing=missing),
                patch.object(
                    checks.shutil,
                    "which",
                    side_effect=lambda name, absent=missing: None if name == absent else "/fixture",
                ),
                self.assertRaisesRegex(FileNotFoundError, missing),
            ):
                checks.run_policy(Path("/unused"))

    def test_full_runs_product_collection_once_and_all_other_gates(self):
        context, evidence = context_and_evidence()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "checks"
            with (
                patch.object(checks, "validate_context") as validate,
                patch.object(checks, "run_commands") as coverage,
                patch.object(checks, "run_product", return_value=evidence) as product,
                patch.object(checks, "run_policy") as policy,
            ):
                self.assertEqual(checks.run_checks(Path(folder), context, "full", output), 0)
            product.assert_called_once()
            coverage.assert_called_once()
            policy.assert_called_once()
            self.assertEqual(validate.call_count, 2)
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["outcome"], "passed")
            self.assertEqual(summary["tests"], 64)
            self.assertEqual(
                summary["checks"],
                ["knowledge_coverage", "product", "policy_static_metadata_knowledge"],
            )

    def test_failures_missing_tooling_and_cancellation_cannot_succeed(self):
        for failure in (
            FileNotFoundError("uv"),
            subprocess.CalledProcessError(1, ["pytest"]),
            KeyboardInterrupt(),
            InterruptedError("SIGTERM"),
        ):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as folder:
                context, _ = context_and_evidence()
                output = Path(folder) / "checks"
                with (
                    patch.object(checks, "validate_context"),
                    patch.object(checks, "run_commands"),
                    patch.object(checks, "run_product", side_effect=failure),
                    patch.object(checks, "run_policy") as policy,
                ):
                    self.assertNotEqual(checks.run_checks(Path(folder), context, "full", output), 0)
                policy.assert_not_called()
                self.assertNotEqual(
                    json.loads((output / "summary.json").read_text())["outcome"], "passed"
                )

    def test_missing_static_tooling_invalidates_successful_product_results(self):
        context, evidence = context_and_evidence()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "checks"
            with (
                patch.object(checks, "validate_context"),
                patch.object(checks, "run_commands"),
                patch.object(checks, "run_product", return_value=evidence),
                patch.object(checks, "run_policy", side_effect=FileNotFoundError("actionlint")),
            ):
                self.assertEqual(checks.run_checks(Path(folder), context, "full", output), 1)
            self.assertEqual(json.loads((output / "summary.json").read_text())["outcome"], "failed")

    def test_reports_run_coverage_before_report_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            context, _ = context_and_evidence()
            context.update(profile="reports", base="a" * 40, changes=[])
            order = []
            with (
                patch.object(checks, "validate_context"),
                patch.object(
                    checks, "run_commands", side_effect=lambda *_: order.append("coverage")
                ),
                patch.object(
                    checks, "check_reports", side_effect=lambda *_: order.append("reports")
                ),
                patch.object(checks, "run_product") as product,
            ):
                code = checks.run_checks(Path(folder), context, "full", Path(folder) / "checks")
            self.assertEqual(code, 0)
            self.assertEqual(order, ["coverage", "reports"])
            product.assert_not_called()

    def test_coverage_failure_stops_both_profiles(self):
        for profile in ("normal", "reports"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as folder:
                context, _ = context_and_evidence()
                context.update(profile=profile, base="a" * 40, changes=[])
                with (
                    patch.object(checks, "validate_context"),
                    patch.object(checks, "run_commands", side_effect=FileNotFoundError("coverage")),
                    patch.object(checks, "run_product") as product,
                    patch.object(checks, "check_reports") as reports,
                ):
                    self.assertEqual(
                        checks.run_checks(Path(folder), context, "full", Path(folder) / "checks"), 1
                    )
                reports.assert_not_called()
                product.assert_not_called()

    def test_report_profile_has_the_locked_validation_environment(self):
        workflow = (Path(__file__).resolve().parents[1] / "workflows/pk-stack-ci.yml").read_text()
        deterministic = workflow.split("\n  deterministic:\n", 1)[1].split("\n  package:\n", 1)[0]
        for name in ("Install uv", "Materialize the locked Power environment"):
            step = deterministic.split("- name: " + name, 1)[1].split("- name:", 1)[0]
            self.assertNotIn("if:", step)


if __name__ == "__main__":
    unittest.main()
