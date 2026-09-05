from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pkstack_review_feedback as feedback
import pkstack_update_controller as controller


def report(run: int = 10, source_id: str = "alpha", tree: str = "a" * 40) -> dict:
    return {
        "schema_version": 1,
        "source_id": source_id,
        "source_commit": "b" * 40,
        "source_subtree_sha": tree,
        "source_run_id": run - 1,
        "candidate_run_id": run,
        "base_sha": "c" * 40,
        "head_sha": "d" * 40,
        "content_sha256": "e" * 64,
        "patch_sha256": "f" * 64,
        "verdict": "rejected",
        "material_findings": ["Preserve the existing permission boundary."],
        "summary": "One material finding requires remediation.",
    }


class FeedbackTests(unittest.TestCase):
    def test_only_valid_substantive_rejections_consume_a_bounded_budget(self) -> None:
        ledger = {"schema_version": 1, "sources": {}}
        for run in range(10, 13):
            ledger = feedback.record_rejection(
                ledger, report(run), retry_override=False
            )
        self.assertEqual(feedback.source_feedback(ledger, "alpha", "a" * 40)[0], 3)
        self.assertEqual(
            feedback.record_rejection(ledger, report(12), retry_override=False), ledger
        )
        with self.assertRaisesRegex(ValueError, "exhausted"):
            feedback.record_rejection(ledger, report(13), retry_override=False)
        retried = feedback.record_rejection(ledger, report(13), retry_override=True)
        self.assertEqual(feedback.source_feedback(retried, "alpha", "a" * 40)[0], 1)
        fresh = feedback.record_rejection(
            ledger, report(13, tree="1" * 40), retry_override=False
        )
        self.assertEqual(feedback.source_feedback(fresh, "alpha", "1" * 40)[0], 1)
        self.assertEqual(len(fresh["sources"]), 1)

    def test_missing_or_invalid_history_does_not_reset_the_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feedback.json"
            with self.assertRaises(FileNotFoundError):
                feedback.load_ledger(path)
            path.write_text('{"schema_version":1,"sources":{"alpha":{}}}')
            with self.assertRaises(ValueError):
                feedback.load_ledger(path)
            path.write_text('{"schema_version":1,"schema_version":1,"sources":{}}')
            with self.assertRaises(ValueError):
                feedback.load_ledger(path)

    def test_malformed_or_non_substantive_verdict_cannot_be_recorded(self) -> None:
        for change in (
            {"verdict": "approved", "material_findings": []},
            {"verdict": "rejected", "material_findings": []},
            {"material_findings": ["bad\ncontrol"]},
            {"candidate_run_id": True},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                feedback.record_rejection(
                    {"schema_version": 1, "sources": {}},
                    {**report(), **change},
                    retry_override=False,
                )

    def test_new_candidate_cannot_replace_newer_or_conflicting_report(self) -> None:
        ledger = feedback.record_rejection(
            {"schema_version": 1, "sources": {}}, report(12), retry_override=False
        )
        with self.assertRaisesRegex(ValueError, "older"):
            feedback.record_rejection(ledger, report(11), retry_override=False)
        with self.assertRaisesRegex(ValueError, "older"):
            feedback.record_rejection(
                ledger, report(11, tree="0" * 40), retry_override=False
            )
        with self.assertRaisesRegex(ValueError, "conflicting"):
            feedback.record_rejection(
                ledger,
                {**report(12), "summary": "Changed verdict"},
                retry_override=False,
            )

    def test_parity_only_work_never_uses_a_model_budget(self) -> None:
        ledger = {"schema_version": 1, "sources": {}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sensor = root / "detector.json"
            sensor.write_text("{}")
            history = root / "feedback.json"
            history.write_text(json.dumps(ledger))
            with mock.patch.object(
                controller.guard,
                "validate_detector",
                return_value={
                    "ok": False,
                    "validated_drift_sources": [],
                    "sources": [],
                },
            ):
                plan = controller.decide(sensor, history)
            self.assertEqual(plan["action"], "manual-parity")
            self.assertIsNone(plan["goal"])

    def test_controller_skips_exhausted_source_and_binds_explicit_retry_to_content(
        self,
    ) -> None:
        detector = {
            "ok": False,
            "validated_drift_sources": [
                {"source_id": "alpha", "expected_head": "b" * 40},
                {"source_id": "zeta", "expected_head": "b" * 40},
            ],
            "sources": [
                {"id": source, "current": {"subtree_sha": "a" * 40}, "drift": True}
                for source in ("alpha", "zeta")
            ],
        }
        ledger = {
            "schema_version": 1,
            "sources": {"alpha": {"rejection_count": 3, "report": report()}},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sensor = root / "detector.json"
            sensor.write_text("{}")
            history = root / "feedback.json"
            history.write_text(json.dumps(ledger))
            with mock.patch.object(
                controller.guard,
                "validate_detector",
                return_value=copy.deepcopy(detector),
            ):
                plan = controller.decide(sensor, history)
                self.assertEqual(plan["selected_source_id"], "zeta")
                self.assertEqual(plan["exhausted_sources"], ["alpha"])
                retry = controller.decide(sensor, history, "alpha@" + "a" * 40)
                self.assertEqual(retry["selected_source_id"], "alpha")
                self.assertTrue(retry["retry_override"])
                self.assertEqual(
                    retry["review_feedback"]["material_findings"],
                    report()["material_findings"],
                )
                with self.assertRaisesRegex(ValueError, "exact-subtree"):
                    controller.decide(sensor, history, "alpha@" + "0" * 40)
                with self.assertRaisesRegex(ValueError, "exact-subtree"):
                    controller.decide(sensor, history, "zeta@" + "a" * 40)
            ledger["sources"]["zeta"] = {
                "rejection_count": 3,
                "report": report(source_id="zeta"),
            }
            history.write_text(json.dumps(ledger))
            with mock.patch.object(
                controller.guard, "validate_detector", return_value=detector
            ):
                self.assertEqual(
                    controller.decide(sensor, history)["action"], "exhausted"
                )


if __name__ == "__main__":
    unittest.main()
