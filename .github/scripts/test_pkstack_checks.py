"""Behavioral coverage for CI selection and fail-closed aggregate evidence."""

import copy
import json
from types import SimpleNamespace
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import pkstack_checks as checks
import pkstack_pytest_partition as plugin


def change(path, status="M", other=None):
    return {"status": status, "paths": [path] + ([other] if other else [])}


def plan_and_receipts():
    plan = {
        "schema": checks.SCHEMA,
        "commit": "a" * 40,
        "config_digest": "b" * 64,
        "profile": "normal",
        "browser_profile": "full",
        "run_id": "42",
        "run_attempt": "1",
        "scheduled": list(checks.LANES),
        "unscheduled": [],
    }
    ids = [
        "tests/test_branding.py::test_contract",
        "tests/test_archify_reader_layout.py::test_browser",
        "tests/test_packaging.py::test_install",
        checks.KIRO_SENTINEL,
    ]
    ids.extend(f"tests/test_core.py::test_behavior_{i}" for i in range(60))
    receipts = []
    for lane in checks.LANES:
        receipt = checks.receipt_base(plan, lane)
        receipt.update(outcome="passed", duration_seconds=1)
        if lane != "policy":
            results = []
            for nodeid in ids:
                if checks.lane_for(nodeid) != lane:
                    continue
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
            receipt.update(
                collection=ids,
                collection_digest=checks.digest(ids),
                results=results,
                issues=[],
                exit_status=0,
            )
        receipts.append(receipt)
    return plan, receipts


class ProfileTests(unittest.TestCase):
    def test_only_enumerated_reports_take_fast_path(self):
        for path in (
            "reviews/release-status.md",
            "reviews/release-030-composition.md",
            "powers/pkstack/reviews/kiro-final-campaign.md",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    checks.execution_profile("pull_request", [change(path)]),
                    ("reports", "none"),
                )
        for path in (
            "powers/pkstack/reviews/fable-review-prompt.md",
            "powers/pkstack/reviews/acceptance-criteria.md",
            "powers/pkstack/reviews/new-report.md",
            "reviews/release-030-future.md",
            "reviews/release-status.json",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    checks.execution_profile("pull_request", [change(path)])[0],
                    "normal",
                )

    def test_main_mixed_unknown_and_cross_boundary_renames_get_normal(self):
        report = change("reviews/release-status.md")
        cases = [
            ("push", [report]),
            ("pull_request", []),
            ("pull_request", [report, change("powers/pkstack/src/pkstack/cli.py")]),
            ("pull_request", [change("reviews/release-status.md", "U")]),
            (
                "pull_request",
                [
                    change(
                        "powers/pkstack/src/pkstack/cli.py",
                        "R100",
                        "reviews/release-status.md",
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
            "powers/pkstack/tests/test_archify_reader_layout.py",
            "powers/pkstack/tests/fixtures/archify.json",
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
            checks.execution_profile(
                "pull_request", [change("powers/pkstack/src/pkstack/cli.py")]
            ),
            ("normal", "smoke"),
        )

    def test_git_nul_records_preserve_spaces_and_renames(self):
        raw = "R100\0reviews/old report.md\0reviews/release-status.md\0M\0source.py\0"
        self.assertEqual(
            checks.parse_changes(raw)[0]["paths"],
            ["reviews/old report.md", "reviews/release-status.md"],
        )
        for raw in ("R100\0one\0", "Z\0path\0", "M\0"):
            with self.assertRaises(ValueError):
                checks.parse_changes(raw)

    def test_partition_is_stable_and_module_overrides_preserve_categories(self):
        self.assertEqual(
            checks.lane_for("tests/test_packaging.py::test_install"), "package"
        )
        self.assertEqual(checks.lane_for("tests/test_branding.py::new_test"), "fast")
        self.assertEqual(
            checks.lane_for("tests/test_archify_reader_layout.py::test_startup"),
            "browser",
        )
        # A known hash gives a stable allocation across Python hash randomization and test additions.
        self.assertEqual(
            checks.lane_for("tests/test_core.py::test_behavior_0"), "core-4"
        )


class ReceiptTests(unittest.TestCase):
    def test_complete_disjoint_execution_and_documented_sentinel_pass(self):
        plan, receipts = plan_and_receipts()
        summary = checks.verify_receipts(plan, receipts)
        self.assertEqual(summary["tests"], 64)
        self.assertEqual(len(summary["lane_seconds"]), 10)

    def test_missing_duplicate_failed_or_foreign_lane_fail(self):
        for mode in (
            "missing",
            "duplicate",
            "failure",
            "identity",
            "config",
            "attempt",
        ):
            with self.subTest(mode=mode):
                plan, receipts = plan_and_receipts()
                if mode == "missing":
                    receipts.pop()
                elif mode == "duplicate":
                    receipts.append(copy.deepcopy(receipts[0]))
                elif mode == "failure":
                    receipts[0]["outcome"] = "failed"
                elif mode == "identity":
                    receipts[0]["commit"] = "c" * 40
                elif mode == "config":
                    receipts[0]["config_digest"] = "c" * 64
                else:
                    receipts[0]["run_attempt"] = "2"
                with self.assertRaises(ValueError):
                    checks.verify_receipts(plan, receipts)

    def test_missing_overlap_collection_mismatch_and_incomplete_phases_fail(self):
        for mode in ("missing", "overlap", "collection", "phases", "exit", "issue"):
            with self.subTest(mode=mode):
                plan, receipts = plan_and_receipts()
                if mode == "missing":
                    receipts[0]["results"] = []
                elif mode == "overlap":
                    receipts[1]["results"].append(receipts[0]["results"][0])
                elif mode == "collection":
                    receipts[0]["collection"] = list(
                        reversed(receipts[0]["collection"])
                    )
                    receipts[0]["collection_digest"] = checks.digest(
                        receipts[0]["collection"]
                    )
                elif mode == "phases":
                    receipts[0]["results"][0]["phases"].pop("teardown")
                elif mode == "exit":
                    receipts[0]["exit_status"] = 2
                else:
                    receipts[0]["issues"] = ["duplicate phase"]
                with self.assertRaises(ValueError):
                    checks.verify_receipts(plan, receipts)

    def test_any_skip_other_than_exact_kiro_sentinel_fails(self):
        for mode in ("test", "reason", "teardown"):
            plan, receipts = plan_and_receipts()
            result = next(
                r
                for rec in receipts
                for r in rec.get("results", [])
                if r["nodeid"] == checks.KIRO_SENTINEL
            )
            if mode == "test":
                result = receipts[0]["results"][0]
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
                checks.verify_receipts(plan, receipts)

    def test_cancelled_or_skipped_required_job_fails(self):
        plan, receipts = plan_and_receipts()
        needs = {
            job: {"result": "success"}
            for job in ("classify", "fast", "browser", "package", "core", "policy")
        }
        checks.verify_receipts(plan, receipts, needs)
        for result in ("cancelled", "skipped", "failure"):
            needs["core"]["result"] = result
            with self.subTest(result=result), self.assertRaises(ValueError):
                checks.verify_receipts(plan, receipts, needs)

    def test_report_profile_accounts_for_unscheduled_lanes(self):
        plan, _ = plan_and_receipts()
        plan.update(
            profile="reports",
            browser_profile="none",
            scheduled=["fast"],
            unscheduled=list(checks.LANES[1:]),
        )
        receipt = checks.receipt_base(plan, "fast")
        receipt["outcome"] = "passed"
        needs = {
            job: {"result": "success" if job in {"classify", "fast"} else "skipped"}
            for job in ("classify", "fast", "browser", "package", "core", "policy")
        }
        self.assertEqual(checks.verify_receipts(plan, [receipt], needs)["tests"], 0)
        needs["browser"]["result"] = "success"
        with self.assertRaises(ValueError):
            checks.verify_receipts(plan, [receipt], needs)


class PluginTests(unittest.TestCase):
    def test_collection_and_phase_reports_detect_incomplete_or_repeated_execution(self):
        for mode in ("passed", "missing-teardown", "duplicate-call", "failed-setup"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                plan, _ = plan_and_receipts()
                receipt_path = Path(folder) / "receipt.json"
                env = {
                    "PKSTACK_CHECK_PLAN": json.dumps(plan),
                    "PKSTACK_CHECK_LANE": "fast",
                    "PKSTACK_CHECK_RECEIPT": str(receipt_path),
                }
                with patch.dict(checks.os.environ, env):
                    deselected = []
                    config = SimpleNamespace(
                        hook=SimpleNamespace(
                            pytest_deselected=lambda items: deselected.extend(items)
                        )
                    )
                    # Match pytest's keyword name while retaining the observed callback items.
                    config.hook.pytest_deselected = lambda **kwargs: deselected.extend(
                        kwargs["items"]
                    )
                    plugin.pytest_configure(config)
                    session = SimpleNamespace(config=config)
                    ids = [
                        "tests/test_branding.py::test_contract",
                        "tests/test_core.py::test_behavior",
                    ]
                    items = [SimpleNamespace(nodeid=nodeid) for nodeid in ids]
                    plugin.pytest_collection_modifyitems(session, config, items)
                    self.assertEqual(config._pkstack_collection, ids)
                    self.assertEqual([item.nodeid for item in items], ids[:1])
                    self.assertEqual([item.nodeid for item in deselected], ids[1:])
                    phases = ["setup", "call", "teardown"]
                    if mode == "missing-teardown":
                        phases.pop()
                    if mode == "duplicate-call":
                        phases.insert(2, "call")
                    if mode == "failed-setup":
                        phases = ["setup", "teardown"]
                    for phase in phases:
                        outcome = (
                            "failed"
                            if mode == "failed-setup" and phase == "setup"
                            else "passed"
                        )
                        report = SimpleNamespace(
                            nodeid=ids[0],
                            when=phase,
                            outcome=outcome,
                            skipped=False,
                            duration=0.25,
                        )
                        plugin.pytest_runtest_logreport(report)
                    plugin.pytest_sessionfinish(
                        session, 0 if mode != "failed-setup" else 1
                    )
                    receipt = json.loads(receipt_path.read_text())
                    result = receipt["results"][0]
                    self.assertEqual(result["duration_seconds"], 0.25 * len(phases))
                    self.assertEqual(
                        result["outcome"],
                        "failed"
                        if mode in {"missing-teardown", "failed-setup"}
                        else "passed",
                    )
                    self.assertEqual(bool(receipt["issues"]), mode == "duplicate-call")


class GitPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in (
            ".github/scripts/check.py",
            "powers/pkstack/pyproject.toml",
            "powers/pkstack/uv.lock",
            "reviews/release-status.md",
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
        return subprocess.check_output(
            ["git", "-C", str(self.root), *args], text=True
        ).strip()

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-qm", message)

    def test_plan_rejects_forged_changes_and_changed_configuration(self):
        (self.root / "reviews/release-status.md").write_text("updated\n")
        self.commit("report")
        plan = checks.make_plan(self.root, "pull_request", self.base)
        checks.validate_plan(plan, self.root)
        altered = copy.deepcopy(plan)
        altered["changes"] = []
        with self.assertRaises(ValueError):
            checks.validate_plan(altered, self.root)
        (self.root / ".github/scripts/check.py").write_text("changed\n")
        with self.assertRaises(ValueError):
            checks.validate_plan(plan, self.root)

    def test_report_check_sees_whitespace_in_earlier_pr_commit(self):
        path = self.root / "reviews/release-status.md"
        path.write_text("bad trailing space \n")
        self.commit("earlier whitespace")
        (self.root / "reviews/release-030-cli.md").write_text("later valid report\n")
        self.commit("later clean")
        plan = checks.make_plan(self.root, "pull_request", self.base)
        with self.assertRaises(subprocess.CalledProcessError):
            checks.check_reports(self.root, plan["changes"], plan["base"])

    def test_reports_validate_relative_links_and_allow_machine_evidence(self):
        path = self.root / "reviews/release-status.md"
        path.write_text(
            "[config](../powers/pkstack/pyproject.toml) [web](https://example.com) [machine](/private/tmp/old-log)\n"
        )
        self.commit("valid links")
        changes = [change("reviews/release-status.md")]
        self.assertEqual(
            checks.check_reports(self.root, changes, self.base),
            ["reviews/release-status.md"],
        )
        path.write_text("[missing](missing.md)\n")
        with self.assertRaises(ValueError):
            checks.check_reports(self.root, changes, self.base)
        path.write_text("[outside](../../outside.md)\n")
        with self.assertRaises(ValueError):
            checks.check_reports(self.root, changes, self.base)


if __name__ == "__main__":
    unittest.main()
