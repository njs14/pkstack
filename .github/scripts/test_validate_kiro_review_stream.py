#!/usr/bin/env python3
"""Regression tests for the no-tool Kiro candidate-review attestation."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import validate_kiro_review_stream as review

BASE = "1" * 40
HEAD = "2" * 40
CONTENT = "3" * 64
PATCH = "4" * 64
MODEL = "claude-opus-5"
EFFORT = "xhigh"


def verdict(*, head: str = HEAD, findings: list[str] | None = None) -> str:
    material = [] if findings is None else findings
    return json.dumps(
        {
            "verdict": "approved" if not material else "rejected",
            "reviewed_base_sha": BASE,
            "reviewed_head_sha": head,
            "reviewed_content_sha256": CONTENT,
            "reviewed_patch_sha256": PATCH,
            "material_findings": material,
            "summary": "Exact candidate has no material unresolved findings.",
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def model_event(model: str = MODEL) -> dict[str, object]:
    return {
        "data": {
            "update": {
                "configOptions": [
                    {
                        "id": "model",
                        "currentValue": model,
                        "options": [
                            {
                                "value": MODEL,
                                "_meta": {"kiro": {"hasEffort": True}},
                            }
                        ],
                    }
                ]
            }
        }
    }


class KiroReviewStreamTests(unittest.TestCase):
    def _args(self, root: Path) -> argparse.Namespace:
        stream = root / "stream.jsonl"
        stderr = root / "stderr"
        stream.write_text("{}\n", encoding="utf-8")
        stderr.write_text("", encoding="utf-8")
        return argparse.Namespace(
            stream=stream,
            stderr=stderr,
            return_code=0,
            base=BASE,
            head=HEAD,
            content_sha256=CONTENT,
            patch_sha256=PATCH,
            model=MODEL,
            effort=EFFORT,
            github_output=None,
        )

    def test_exact_approved_model_bound_verdict_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            args = self._args(Path(directory))
            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                mock.patch.object(
                    review,
                    "parse_no_tool_stream_bytes",
                    return_value=(
                        verdict(),
                        [model_event("auto"), model_event("auto"), model_event()],
                    ),
                ),
            ):
                result = review.validate(args)
        self.assertEqual(result["reviewed_head_sha"], HEAD)
        self.assertRegex(result["attestation_sha256"], r"^[0-9a-f]{64}$")

    def test_stale_or_rejected_verdict_fails_closed(self) -> None:
        for response in (
            verdict(head="5" * 40),
            verdict(findings=["Material safety gap"]),
        ):
            with self.subTest(response=response), tempfile.TemporaryDirectory() as directory:
                args = self._args(Path(directory))
                with (
                    mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                    mock.patch.object(
                        review,
                        "parse_no_tool_stream_bytes",
                        return_value=(response, [model_event()]),
                    ),
                    self.assertRaises(review.ReviewError),
                ):
                    review.validate(args)

    def test_wrong_model_effort_or_secret_leak_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            args = self._args(Path(directory))
            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                mock.patch.object(
                    review,
                    "parse_no_tool_stream_bytes",
                    return_value=(verdict(), [model_event("auto")]),
                ),
                self.assertRaises(review.ReviewError),
            ):
                review.validate(args)
            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                mock.patch.object(
                    review,
                    "parse_no_tool_stream_bytes",
                    return_value=(
                        verdict(),
                        [model_event(), model_event("auto")],
                    ),
                ),
                self.assertRaises(review.ReviewError),
            ):
                review.validate(args)
            args.model = MODEL
            args.effort = "high"
            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                self.assertRaisesRegex(review.ReviewError, "xhigh effort"),
            ):
                review.validate(args)
            args.effort = EFFORT
            args.stream.write_text("sentinel-secret\n", encoding="utf-8")
            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                self.assertRaisesRegex(review.ReviewError, "contained the API key"),
            ):
                review.validate(args)


if __name__ == "__main__":
    unittest.main()
