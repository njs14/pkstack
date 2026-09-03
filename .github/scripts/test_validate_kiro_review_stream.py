#!/usr/bin/env python3
"""Regression tests for the no-tool Kiro candidate-review attestation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import validate_kiro_review_stream as review

BASE = "1" * 40
HEAD = "2" * 40
PATCH_TEXT = "diff --git a/README.md b/README.md\n-old\n+new\n"
PATCH = hashlib.sha256(PATCH_TEXT.encode()).hexdigest()
PATHS = ["README.md"]
PATHS_SHA256 = hashlib.sha256(
    json.dumps(PATHS, separators=(",", ":")).encode()
).hexdigest()
BUNDLE = {
    "schema_version": 1,
    "review_type": "mandatory-independent-exact-candidate",
    "base_sha": BASE,
    "head_sha": HEAD,
    "requires_review": True,
    "changed_files": 1,
    "changed_lines": 2,
    "paths": PATHS,
    "paths_sha256": PATHS_SHA256,
    "patch_sha256": PATCH,
    "patch": PATCH_TEXT,
}
BUNDLE_RAW = (json.dumps(BUNDLE, sort_keys=True, separators=(",", ":")) + "\n").encode()
CONTENT = hashlib.sha256(BUNDLE_RAW).hexdigest()
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
            "reviewed_changed_files": 1,
            "reviewed_paths_sha256": PATHS_SHA256,
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


def mode_event(mode: str = review.REQUIRED_AGENT) -> dict[str, object]:
    return {
        "data": {
            "update": {
                "configOptions": [{"id": "mode", "currentValue": mode}]
            }
        }
    }


class KiroReviewStreamTests(unittest.TestCase):
    def test_captured_kiro_221_model_and_agent_projection(self) -> None:
        fixture = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "reviews/kiro-v3-review-stream-shape.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(fixture["cli_version"], "2.21.0")
        review._validate_model_event(fixture["events"], fixture["command_model"])
        review._validate_agent_event(fixture["events"])

    def _args(self, root: Path) -> argparse.Namespace:
        stream = root / "stream.jsonl"
        stderr = root / "stderr"
        bundle = root / "review-input.json"
        stream.write_text("{}\n", encoding="utf-8")
        stderr.write_text("", encoding="utf-8")
        bundle.write_bytes(BUNDLE_RAW)
        return argparse.Namespace(
            stream=stream,
            stderr=stderr,
            bundle=bundle,
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
                        [
                            mode_event("vibe"),
                            model_event("auto"),
                            model_event("auto"),
                            mode_event(),
                            model_event(),
                        ],
                    ),
                ),
            ):
                result = review.validate(args)
        self.assertEqual(result["reviewed_head_sha"], HEAD)
        self.assertEqual(result["reviewed_agent"], review.REQUIRED_AGENT)
        self.assertEqual(result["reviewed_model"], MODEL)
        self.assertEqual(result["reviewed_effort"], EFFORT)
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
                    return_value=(verdict(), [mode_event(), model_event("auto")]),
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
                        [mode_event(), model_event(), model_event("auto")],
                    ),
                ),
                self.assertRaises(review.ReviewError),
            ):
                review.validate(args)
            args.stderr.write_text('agent not found, using "default"\n', encoding="utf-8")
            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                self.assertRaisesRegex(review.ReviewError, "fell back"),
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

    def test_wrong_agent_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            args = self._args(Path(directory))
            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                mock.patch.object(
                    review,
                    "parse_no_tool_stream_bytes",
                    return_value=(verdict(), [mode_event("vibe"), model_event()]),
                ),
                self.assertRaisesRegex(review.ReviewError, "required agent"),
            ):
                review.validate(args)

    def test_bundle_facts_are_recomputed_before_verdict_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            args = self._args(Path(directory))
            tampered = {**BUNDLE, "changed_files": 2}
            raw = (json.dumps(tampered, sort_keys=True, separators=(",", ":")) + "\n").encode()
            args.bundle.write_bytes(raw)
            args.content_sha256 = hashlib.sha256(raw).hexdigest()
            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                self.assertRaisesRegex(review.ReviewError, "bundle facts are malformed"),
            ):
                review.validate(args)


if __name__ == "__main__":
    unittest.main()
