"""Private evidence delivery is bounded, credential-free and fail-closed."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pkstack_verification_feedback as feedback


class FeedbackTests(unittest.TestCase):
    def test_byte_budget_and_detail_priority(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log, detail, target = (root / name for name in ("log", "detail", "target"))
            log.write_text("incidental " * 100000)
            detail.write_text("Actual failing detail: " + "界" * 16000)
            feedback.build(log, detail, target, 1, b"private-secret")
            self.assertIn("Actual failing detail", target.read_text())
            self.assertLessEqual(target.stat().st_size, 32768)

    def test_missing_invalid_and_credential_bearing_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log, detail, target = (root / name for name in ("log", "detail", "target"))
            detail.write_text("private detail")
            for content in (b"secret-value", b"secret-\\u0076alue", b"ghp_" + b"a" * 36):
                log.write_bytes(b"x" * 65530 + content + b"x" * 65536)
                target.write_text("stale prior feedback")
                with self.assertRaises(feedback.FeedbackError):
                    feedback.build(log, detail, target, 1, b"secret-value")
                self.assertFalse(target.exists())
            log.unlink()
            with self.assertRaises(OSError):
                feedback.build(log, detail, target, 1, b"secret-value")
            log.symlink_to(detail)
            with self.assertRaises(feedback.FeedbackError):
                feedback.build(log, detail, target, 1, b"secret-value")

    def test_sanitizing_and_assembling_cannot_reconstruct_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log, detail, target = (root / name for name in ("log", "detail", "target"))
            log.write_text("")
            for content in ("sentinel-\x1b[31msecret", "sentinel-\x00secret"):
                detail.write_text(content)
                with self.assertRaises(feedback.FeedbackError):
                    feedback.build(log, detail, target, 1, b"sentinel-secret")
                self.assertFalse(target.exists())
            raw = root / "raw"
            raw.write_bytes(
                b"x" * (12288 - 9) + b"sentinel-" + b"y" * 30000 + b"secret" + b"z" * (12288 - 6)
            )
            feedback.retain(raw, detail, b"sentinel-secret")
            with self.assertRaises(feedback.FeedbackError):
                feedback.build(log, detail, target, 1, b"sentinel-secret")
            self.assertFalse(target.exists())

    def test_delivery_rechecks_limit_type_and_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "feedback"
            for content in (b"x" * 32769, b"sk-" + b"a" * 48):
                path.write_bytes(content)
                with self.assertRaises(feedback.FeedbackError):
                    feedback.validate_delivery(path)


if __name__ == "__main__":
    unittest.main()
