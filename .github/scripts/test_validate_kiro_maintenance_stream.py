from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any

import validate_kiro_maintenance_stream as validator

ROOT = Path(__file__).resolve().parents[2]
SESSION = "sess_00000000-0000-4000-8000-000000000001"
PROFILE = json.loads((ROOT / ".kiro/agents/pkstack-maintainer.json").read_text())


def envelope(update: dict[str, Any]) -> dict[str, Any]:
    return {"type": "sessionUpdate", "data": {"sessionId": SESSION, "update": update}}


def attested_events() -> list[dict[str, Any]]:
    """Synthetic maintainer contract, using observed 2.21.1 global option metadata."""
    option = {
        "name": "pkstack-maintainer",
        "value": "pkstack-maintainer",
        "description": PROFILE["description"],
        "_meta": {
            "kiro": {
                "source": "global",
                "welcomeMessage": PROFILE["welcomeMessage"],
                "resource": {"resourceType": "agent", "source": {"origin": "user"}},
            }
        },
    }
    selection = envelope(
        {
            "sessionUpdate": "config_option_update",
            "configOptions": [
                {
                    "id": "mode",
                    "name": "Mode",
                    "category": "mode",
                    "type": "select",
                    "currentValue": "pkstack-maintainer",
                    "options": [option],
                }
            ],
        }
    )
    initial = copy.deepcopy(selection)
    initial["data"]["update"]["configOptions"][0]["currentValue"] = "vibe"
    return [
        {
            "type": "runStarted",
            "data": {
                "payloadSchema": "acp",
                "acpProtocolVersion": 1,
                "engine": "v3",
            },
        },
        initial,
        selection,
        envelope(
            {
                "sessionUpdate": "agent_message_chunk",
                "content": {"type": "text", "text": "Done."},
                "_meta": {"kiro": {"replayId": "a" * 40}},
            }
        ),
        {
            "type": "runFinished",
            "data": {
                "sessionId": SESSION,
                "status": "success",
                "stopReason": "end_turn",
                "finalText": "Done.",
                "finalTextTruncated": False,
            },
        },
    ]


def stream_bytes(events: list[dict[str, Any]]) -> bytes:
    return b"".join((json.dumps(event) + "\n").encode() for event in events)


class MaintenanceAgentAttestationTests(unittest.TestCase):
    def test_complete_fixed_category_diagnostics(self) -> None:
        machine = validator.StreamValidator(PROFILE, "secret-sentinel")
        events = attested_events()
        events.insert(-1, envelope({"sessionUpdate": "private-unknown-category"}))
        raw = stream_bytes(events)
        for offset in range(0, len(raw), 7):
            machine.feed(raw[offset : offset + 7])
        machine.finish(0)
        report = machine.report(0, None)
        self.assertEqual(report["bytes"]["stdout"], len(raw))
        self.assertEqual(sum(report["event_bytes"].values()), len(raw))
        self.assertEqual(sum(report["event_counts"].values()), len(events))
        self.assertEqual(report["event_counts"]["other"], 1)
        self.assertNotIn("private-unknown-category", json.dumps(report))
        self.assertEqual(report["candidate_acceptance"], "not-evaluated")
        self.assertLess(len(json.dumps(report).encode()), validator.MAX_REPORT_BYTES)

    def test_secret_and_fallback_split_across_chunks(self) -> None:
        for text, stderr, reason in (
            (b"secret-sentinel", True, "secret-detected"),
            (b'not found, using "default"', True, "fallback"),
            (b"secret-sentinel", False, "secret-detected"),
        ):
            for split in range(1, len(text)):
                machine = validator.StreamValidator(PROFILE, "secret-sentinel")
                machine.feed(text[:split], stderr=stderr)
                with self.assertRaisesRegex(validator.AttestationError, reason):
                    machine.feed(text[split:], stderr=stderr)

    def test_duplicate_terminal_and_events_after_completion_fail(self) -> None:
        for extra in (attested_events()[-1], attested_events()[3]):
            with self.assertRaisesRegex(validator.AttestationError, "after-terminal"):
                self.validate([*attested_events(), extra])

    def validate(self, events: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        return validator.validate_stream_bytes(
            stream_bytes(events),
            kwargs.pop("stderr", b""),
            profile=PROFILE,
            return_code=0,
            api_key="test-only-noncredential",
            **kwargs,
        )

    def test_accepts_direct_global_selection_and_internal_bootstrap(self) -> None:
        events = attested_events()
        call_id = "00000000-0000-4000-8000-000000000002"
        events.insert(
            1,
            envelope(
                {
                    "sessionUpdate": "tool_call",
                    "toolCallId": call_id,
                    "status": "in_progress",
                    "title": "Fetching your cloud config",
                    "_meta": {"kiro": {"toolId": "fetch_cloud_config"}},
                }
            ),
        )
        events.insert(
            4,
            envelope(
                {"sessionUpdate": "tool_call_update", "toolCallId": call_id, "status": "completed"}
            ),
        )
        events.insert(
            5,
            envelope(
                {"sessionUpdate": "tool_call", "toolCallId": "user-call", "title": "Read source"}
            ),
        )
        self.assertEqual(
            self.validate(events),
            {
                "ok": True,
                "selected_agent": "pkstack-maintainer",
                "agent_source": "global",
            },
        )

    def test_rejects_empty_object_missing_and_advertised_only(self) -> None:
        advertised = attested_events()
        advertised[2] = copy.deepcopy(advertised[1])
        missing = attested_events()
        del missing[1:3]
        for events in ([], [{}], missing, advertised):
            with self.subTest(events=events), self.assertRaises(validator.AttestationError):
                self.validate(events)

    def test_rejects_wrong_identity_source_and_duplicate_mode_or_option(self) -> None:
        cases = []
        for path, replacement in (
            (("name",), "other"),
            (("description",), "other"),
            (("_meta", "kiro", "source"), "workspace"),
            (("_meta", "kiro", "welcomeMessage"), "other"),
            (("_meta", "kiro", "resource", "source", "origin"), "workspace"),
            (("_meta", "kiro", "resource", "source", "root"), "/untrusted"),
        ):
            events = attested_events()
            target = events[2]["data"]["update"]["configOptions"][0]["options"][0]
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = replacement
            cases.append(events)
        for duplicate in ("mode", "option"):
            events = attested_events()
            options = events[2]["data"]["update"]["configOptions"]
            target = options if duplicate == "mode" else options[0]["options"]
            target.append(copy.deepcopy(target[0]))
            cases.append(events)
        for events in cases:
            with self.subTest(events=events), self.assertRaises(validator.AttestationError):
                self.validate(events)

    def test_rejects_late_selection_fallback_and_cross_session(self) -> None:
        cases = []
        for kind in ("agent_message_chunk", "agent_thought_chunk", "tool_call", "tool_call_update"):
            events = attested_events()
            events.insert(2, envelope({"sessionUpdate": kind}))
            cases.append(events)
        fallback = attested_events()
        fallback.insert(-1, copy.deepcopy(fallback[1]))
        cases.append(fallback)
        wrong = attested_events()
        wrong[2]["data"]["update"]["configOptions"][0]["currentValue"] = "other"
        cases.append(wrong)
        wrong_session = attested_events()
        wrong_session[2]["data"]["sessionId"] = "sess_00000000-0000-4000-8000-000000000099"
        cases.append(wrong_session)
        for events in cases:
            with self.subTest(events=events), self.assertRaises(validator.AttestationError):
                self.validate(events)
        with self.assertRaisesRegex(validator.AttestationError, "maintenance-agent-fallback"):
            self.validate(attested_events(), stderr=b'Agent not found, using "default"\n')

    def test_nested_copies_cannot_attest_selection(self) -> None:
        for kind in ("agent_message_chunk", "tool_call_update", "session_info_update"):
            events = attested_events()
            events[2] = envelope({"sessionUpdate": kind, "untrusted": events[2]})
            with self.subTest(kind=kind), self.assertRaises(validator.AttestationError):
                self.validate(events)

    def test_requires_successful_exact_run_boundaries(self) -> None:
        for field, replacement in (
            ("status", "failed"),
            ("stopReason", "max_tokens"),
            ("finalTextTruncated", True),
            ("sessionId", "wrong"),
        ):
            events = attested_events()
            events[-1]["data"][field] = replacement
            with self.subTest(field=field), self.assertRaises(validator.AttestationError):
                self.validate(events)
        events = attested_events()
        events[0]["data"]["engine"] = "v2"
        with self.assertRaises(validator.AttestationError):
            self.validate(events)

    def test_malformed_json_and_limits_return_fixed_safe_codes(self) -> None:
        sensitive = "SENSITIVE-CANDIDATE-TEXT"
        cases = [
            b'{"bad":',
            ('{"' + sensitive + '":0,"' + sensitive + '":1}').encode(),
            b'{"x":NaN}',
            b'{"x":' + b"1" * 5000 + b"}",
            b'{"x":' + b"[" * 2000 + b"0" + b"]" * 2000 + b"}",
            b"\xff",
            b" " * (validator.MAX_OUTPUT_BYTES + 1),
        ]
        for raw in cases:
            with (
                self.subTest(size=len(raw)),
                self.assertRaises(validator.AttestationError) as caught,
            ):
                validator.validate_stream_bytes(
                    raw, b"", profile=PROFILE, return_code=0, api_key="test-key"
                )
            self.assertRegex(str(caught.exception), r"^maintenance-agent-[a-z-]+$")
            self.assertNotIn(sensitive, str(caught.exception))

    def test_return_code_and_raw_or_encoded_secrets_fail(self) -> None:
        raw = stream_bytes(attested_events())
        for stream, stderr, rc in (
            (raw, b"", 1),
            (raw, b"test-key", 0),
            (raw.replace(b"Done.", b"test-key"), b"", 0),
            (raw.replace(b"Done.", b"test-\\u006bey"), b"", 0),
        ):
            with self.subTest(rc=rc), self.assertRaises(validator.AttestationError):
                validator.validate_stream_bytes(
                    stream, stderr, profile=PROFILE, return_code=rc, api_key="test-key"
                )


if __name__ == "__main__":
    unittest.main()
