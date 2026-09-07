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
from typing import Any
from unittest import mock

import validate_kiro_review_stream as review

BASE = "1" * 40
HEAD = "2" * 40
PATCH_TEXT = "diff --git a/README.md b/README.md\n-old\n+new\n"
PATCH = hashlib.sha256(PATCH_TEXT.encode()).hexdigest()
PATHS = ["README.md"]
PATHS_SHA256 = hashlib.sha256(json.dumps(PATHS, separators=(",", ":")).encode()).hexdigest()
BUNDLE = {
    "schema_version": 3,
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
    "skill_compatibility": {},
    "source_inventory": [],
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


def model_event(model: str = MODEL) -> dict[str, Any]:
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


def mode_event(mode: str = review.REQUIRED_AGENT) -> dict[str, Any]:
    return {"data": {"update": {"configOptions": [{"id": "mode", "currentValue": mode}]}}}


class KiroReviewStreamTests(unittest.TestCase):
    def test_reviewer_prompt_states_existing_verdict_contract(self) -> None:
        profile = json.loads(
            (
                Path(__file__).resolve().parents[2] / ".kiro/agents/pkstack-ci-reviewer.json"
            ).read_text(encoding="utf-8")
        )
        prompt = profile["prompt"]
        for guidance in (
            "exactly these required fields",
            "strings matching the exact candidate bindings",
            "reviewed_changed_files must be the bundle's integer count",
            "array of 0 to 32 trimmed, nonempty strings",
            "each at most 2000 UTF-8 bytes; never objects or null",
            '["path/to/file: Concrete issue and required fix."]',
            "summary must be a trimmed, nonempty string of at most 4000 UTF-8 bytes",
            '"approved" if and only if material_findings is []',
            'otherwise use "rejected"',
            "schema v3 skill_compatibility context",
            "complete changed file records at base and head, keyed by upstream path",
            "An unchanged retrieved_on is valid for multiple inventory retrievals on the "
            "same UTC date",
            "Do not invent omitted context",
            "immutable base fixture",
            "Block supported conflicting instructions",
            "duplicated mandatory work or competing ownership",
            "unauthorized effects, and weakened verification",
            "Allow documented composition with one primary owner and useful helpers",
            "shared vocabulary or overlapping descriptions alone are not defects",
            "Missing, inconsistent, or insufficient context is an unresolved finding",
        ):
            with self.subTest(guidance=guidance):
                self.assertIn(guidance, prompt)
        for field in json.loads(verdict()):
            self.assertIn(field, prompt)

    def test_documented_findings_and_summary_limits_remain_strict(self) -> None:
        def validate(payload: dict[str, Any]) -> None:
            review._validate_verdict(
                json.dumps(payload),
                base_sha=BASE,
                head_sha=HEAD,
                content_sha256=CONTENT,
                patch_sha256=PATCH,
                changed_files=1,
                paths_sha256=PATHS_SHA256,
            )

        approved = json.loads(verdict())
        validate(approved)
        composition = dict(
            approved,
            summary=(
                "Intentional composition retains one primary owner and a bounded evidence helper."
            ),
        )
        validate(composition)
        rejected = json.loads(verdict(findings=["é" * 1000] * 32))
        rejected["summary"] = "é" * 2000
        validate(rejected)
        invalid = [
            ("material_findings", value)
            for value in (
                None,
                {},
                [None],
                [{"issue": "Unsafe"}],
                [""],
                [" padded "],
                ["é" * 1001],
                ["Issue"] * 33,
            )
        ] + [("summary", value) for value in (None, {}, "", " padded ", "é" * 2001)]
        for field, value in invalid:
            with self.subTest(field=field, value=value):
                payload = {**approved, field: value}
                with self.assertRaisesRegex(review.ReviewError, "malformed"):
                    validate(payload)
        for payload in (
            {**approved, "verdict": "rejected"},
            {**approved, "material_findings": ["Material issue"]},
        ):
            with (
                self.subTest(verdict=payload["verdict"]),
                self.assertRaisesRegex(review.ReviewError, "contradicts"),
            ):
                validate(payload)

    def test_captured_kiro_221_model_projection_and_legacy_agent_rejection(
        self,
    ) -> None:
        fixture = json.loads(
            (
                Path(__file__).resolve().parents[2] / "reviews/kiro-v3-review-stream-shape.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(fixture["cli_version"], "2.21.0")
        review._validate_model_event(fixture["events"], fixture["command_model"])
        with self.assertRaisesRegex(review.ReviewError, "required agent"):
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
            with (
                self.subTest(response=response),
                tempfile.TemporaryDirectory() as directory,
            ):
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

    def test_valid_rejection_is_reported_for_remediation_but_never_approval(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self._args(root)
            args.report_path = root / "report.json"
            args.source_id = "alpha"
            args.source_commit = "a" * 40
            args.source_subtree_sha = "b" * 40
            args.source_run_id = 10
            args.candidate_run_id = 11
            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                mock.patch.object(
                    review,
                    "parse_no_tool_stream_bytes",
                    return_value=(
                        verdict(findings=["Fix boundary\nthen rerun"]),
                        [mode_event(), model_event()],
                    ),
                ),
            ):
                result = review.validate(args)
            self.assertEqual(result["review_verdict"], "rejected")
            report = json.loads(args.report_path.read_bytes())
            self.assertEqual(report["material_findings"], ["Fix boundary then rerun"])
            self.assertEqual(report["head_sha"], HEAD)
            self.assertEqual(report["source_subtree_sha"], "b" * 40)
            self.assertNotIn("sentinel-secret", args.report_path.read_text())

    def test_json_escaped_secret_cannot_reach_a_published_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self._args(root)
            args.report_path = root / "report.json"
            escaped = verdict(findings=["sentinel-secret"]).replace("sentinel", r"\u0073entinel")
            self.assertNotIn("sentinel-secret", escaped)
            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                mock.patch.object(
                    review,
                    "parse_no_tool_stream_bytes",
                    return_value=(escaped, [mode_event(), model_event()]),
                ),
                self.assertRaisesRegex(review.ReviewError, "decoded review output"),
            ):
                review.validate(args)
            self.assertFalse(args.report_path.exists())

    def test_cli_rejected_result_does_not_claim_approval(self) -> None:
        with (
            mock.patch.object(
                review.argparse.ArgumentParser,
                "parse_args",
                return_value=argparse.Namespace(github_output=None),
            ),
            mock.patch.object(review, "validate", return_value={"review_verdict": "rejected"}),
            mock.patch("builtins.print") as printed,
        ):
            self.assertEqual(review.main(), 0)
        self.assertFalse(json.loads(printed.call_args.args[0])["approved"])

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

    THOUGHT_SENTINEL = "INERT_THOUGHT_SENTINEL_DO_NOT_PUBLISH"
    THOUGHT_SESSION = "sess_00000000-0000-4000-8000-000000000001"

    def _review_envelope(self, update: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "sessionUpdate",
            "data": {"sessionId": self.THOUGHT_SESSION, "update": update},
        }

    def _review_bootstrap(self) -> list[dict[str, Any]]:
        call_id = "00000000-0000-4000-8000-000000000002"
        return [
            self._review_envelope(
                {
                    "sessionUpdate": "tool_call",
                    "toolCallId": call_id,
                    "status": "in_progress",
                    "title": "Fetching your cloud config",
                    "_meta": {"kiro": {"toolId": "fetch_cloud_config"}},
                }
            ),
            self._review_envelope(
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": call_id,
                    "status": "completed",
                }
            ),
        ]

    def _review_thought_events(self, thought_count: int = 2) -> list[dict[str, Any]]:
        profile = json.loads(
            (
                Path(__file__).resolve().parents[2] / ".kiro/agents/pkstack-ci-reviewer.json"
            ).read_text(encoding="utf-8")
        )
        mode = {
            "id": "mode",
            "name": "Mode",
            "category": "mode",
            "type": "select",
            "currentValue": review.REQUIRED_AGENT,
            "options": [
                {
                    "name": review.REQUIRED_AGENT,
                    "value": review.REQUIRED_AGENT,
                    "description": profile["description"],
                    "_meta": {
                        "kiro": {
                            "source": "global",
                            "welcomeMessage": profile["welcomeMessage"],
                            "resource": {"resourceType": "agent", "source": {"origin": "user"}},
                        }
                    },
                }
            ],
        }
        model = model_event()["data"]["update"]
        model["sessionUpdate"] = "config_option_update"
        return [
            {
                "type": "runStarted",
                "data": {
                    "payloadSchema": "acp",
                    "acpProtocolVersion": 1,
                    "engine": "v3",
                },
            },
            self._review_envelope(
                {"sessionUpdate": "config_option_update", "configOptions": [mode]}
            ),
            self._review_envelope(model),
            *[
                self._review_envelope(
                    {
                        "sessionUpdate": "agent_thought_chunk",
                        "_meta": {"kiro": {"replayId": "t" * 40}},
                        "content": {"type": "text", "text": self.THOUGHT_SENTINEL},
                    }
                )
                for _ in range(thought_count)
            ],
            self._review_envelope(
                {
                    "sessionUpdate": "agent_message_chunk",
                    "_meta": {"kiro": {"replayId": "m" * 40}},
                    "content": {"type": "text", "text": verdict()},
                }
            ),
            {
                "type": "runFinished",
                "data": {
                    "sessionId": self.THOUGHT_SESSION,
                    "status": "success",
                    "stopReason": "end_turn",
                    "finalText": verdict(),
                    "finalTextTruncated": False,
                },
            },
        ]

    def _review_lifecycle_args(
        self, root: Path, events: list[dict[str, Any]]
    ) -> argparse.Namespace:
        args = self._args(root)
        args.stream.write_text(
            "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
        )
        args.report_path = root / "report.json"
        args.source_id = "alpha"
        args.source_commit = "a" * 40
        args.source_subtree_sha = "b" * 40
        args.source_run_id = 10
        args.candidate_run_id = 11
        return args

    def test_unmocked_review_thoughts_are_excluded_from_verdict_and_report(self) -> None:
        for count in (1, 2):
            with self.subTest(thoughts=count), tempfile.TemporaryDirectory() as directory:
                events = self._review_thought_events(count)
                events[3:3] = self._review_bootstrap()
                args = self._review_lifecycle_args(Path(directory), events)
                with mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}):
                    result = review.validate(args)
                report_raw = args.report_path.read_text(encoding="utf-8")
                report = json.loads(report_raw)
                self.assertEqual(result["review_verdict"], "approved")
                self.assertEqual(result["reviewed_agent"], review.REQUIRED_AGENT)
                self.assertEqual(result["reviewed_model"], MODEL)
                self.assertEqual(result["reviewed_effort"], EFFORT)
                self.assertEqual(
                    result["verdict_sha256"], hashlib.sha256(verdict().encode()).hexdigest()
                )
                self.assertEqual(report["material_findings"], [])
                self.assertEqual(report["summary"], json.loads(verdict())["summary"])
                self.assertNotIn(self.THOUGHT_SENTINEL, report_raw + json.dumps(result))

    def test_unmocked_review_rejects_malformed_and_spoofed_thoughts(self) -> None:
        missing = object()
        cases = (
            ("extra_update_key", ("unexpected",), self.THOUGHT_SENTINEL),
            ("missing_metadata", ("_meta",), missing),
            ("missing_content", ("content",), missing),
            ("missing_kind", ("sessionUpdate",), missing),
            ("extra_metadata_key", ("_meta", "unexpected"), self.THOUGHT_SENTINEL),
            ("missing_kiro_metadata", ("_meta", "kiro"), missing),
            ("missing_replay", ("_meta", "kiro", "replayId"), missing),
            ("extra_kiro_key", ("_meta", "kiro", "unexpected"), self.THOUGHT_SENTINEL),
            ("invalid_replay", ("_meta", "kiro", "replayId"), "short"),
            ("null_content", ("content",), None),
            ("missing_content_type", ("content", "type"), missing),
            ("missing_content_text", ("content", "text"), missing),
            ("null_text", ("content", "text"), None),
            ("empty_text", ("content", "text"), ""),
            ("non_string_text", ("content", "text"), [self.THOUGHT_SENTINEL]),
            ("wrong_content_type", ("content", "type"), "image"),
            ("nested_tool", ("content", "nested"), {"sessionUpdate": "tool_call"}),
            ("nested_message", ("content", "nested"), {"sessionUpdate": "agent_message_chunk"}),
            ("unknown_kind", ("sessionUpdate",), "agent_unknown_chunk"),
        )
        for name, path, replacement in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as directory:
                events = self._review_thought_events()
                target = events[3]["data"]["update"]
                for key in path[:-1]:
                    target = target[key]
                if replacement is missing:
                    del target[path[-1]]
                else:
                    target[path[-1]] = replacement
                args = self._review_lifecycle_args(Path(directory), events)
                with (
                    mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                    self.assertRaises(review.ReviewError) as caught,
                ):
                    review.validate(args)
                self.assertNotIn(self.THOUGHT_SENTINEL, str(caught.exception))
                self.assertFalse(args.report_path.exists())

    def test_unmocked_review_rejects_thought_identity_and_ordering_failures(self) -> None:
        cases = (
            "wrong_session",
            "changed_replay",
            "pending_bootstrap",
            "after_message",
            "late_bootstrap",
            "thought_only",
            "mismatched_final_text",
        )
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                events = self._review_thought_events()
                if case == "wrong_session":
                    events[3]["data"]["sessionId"] = "sess_00000000-0000-4000-8000-000000000099"
                elif case == "changed_replay":
                    events[4]["data"]["update"]["_meta"]["kiro"]["replayId"] = "q" * 40
                elif case == "pending_bootstrap":
                    start, terminal = self._review_bootstrap()
                    events[3:5] = [start, *events[3:5], terminal]
                elif case == "after_message":
                    events[4], events[5] = events[5], events[4]
                elif case == "late_bootstrap":
                    events[4:4] = self._review_bootstrap()
                elif case == "thought_only":
                    del events[5]
                elif case == "mismatched_final_text":
                    events[-1]["data"]["finalText"] = verdict(head="5" * 40)
                args = self._review_lifecycle_args(Path(directory), events)
                with (
                    mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}),
                    self.assertRaises(review.ReviewError) as caught,
                ):
                    review.validate(args)
                self.assertNotIn(self.THOUGHT_SENTINEL, str(caught.exception))
                self.assertFalse(args.report_path.exists())


if __name__ == "__main__":
    unittest.main()
