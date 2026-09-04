#!/usr/bin/env python3
"""Focused tests for the deterministic PK-Stack update controller."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("pk_stack_update_controller.py")
SPEC = importlib.util.spec_from_file_location("pk_stack_update_controller", SCRIPT)
assert SPEC and SPEC.loader
controller = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(controller)


class ControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.detector = Path(self.temporary.name) / "detector.json"
        self.detector.write_text("{}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def decide(self, payload: dict[str, object]) -> dict[str, object]:
        with mock.patch.object(controller.guard, "validate_detector", return_value=payload):
            return controller.decide(self.detector)

    def test_selects_lexicographically_first_validated_drift(self) -> None:
        result = self.decide(
            {
                "ok": False,
                "validated_drift_sources": [
                    {"source_id": "alpha", "expected_head": "a" * 40},
                    {"source_id": "zeta", "expected_head": "b" * 40},
                ],
            }
        )
        self.assertEqual(result["action"], "reconcile-source")
        self.assertEqual(result["selected_source_id"], "alpha")
        self.assertEqual(result["goal"]["kind"], "command")
        self.assertIn("--source-id alpha", result["goal"]["value"])

    def test_parity_without_remote_drift_requires_reviewed_setup_not_a_model(self) -> None:
        result = self.decide({"ok": False, "validated_drift_sources": []})
        self.assertEqual(result["action"], "manual-parity")
        self.assertIsNone(result["goal"])

    def test_current_state_is_an_explicit_noop(self) -> None:
        result = self.decide({"ok": True, "validated_drift_sources": []})
        self.assertEqual(result["action"], "current")
        self.assertIsNone(result["goal"])

    def test_rejects_detector_that_changes_during_decision(self) -> None:
        original = controller.hashlib.sha256
        calls = 0

        def changed(value: bytes):
            nonlocal calls
            calls += 1
            digest = original(value)
            if calls == 2:
                digest = mock.Mock(hexdigest=lambda: "f" * 64)
            return digest

        with (
            mock.patch.object(
                controller.guard,
                "validate_detector",
                return_value={"ok": True, "validated_drift_sources": []},
            ),
            mock.patch.object(controller.hashlib, "sha256", side_effect=changed),
            self.assertRaisesRegex(controller.guard.GuardError, "changed while"),
        ):
            controller.decide(self.detector)


if __name__ == "__main__":
    unittest.main()
