"""Regression coverage for typed rejection of malformed Kiro focus metadata."""

from __future__ import annotations

import unittest
from typing import Any

import validate_kiro_credential_stream as stream


def focus_event() -> dict[str, Any]:
    return {
        "type": "sessionUpdate",
        "data": {
            "sessionId": "sess_11111111-1111-4111-8111-111111111111",
            "update": {
                "sessionUpdate": "session_info_update",
                "title": "Review Python tooling",
                "_meta": {
                    "kiro": {
                        "kind": "focus_update",
                        "title": "Review Python tooling",
                        "focus": {"title": "Review Python tooling"},
                    }
                },
            },
        },
    }


class FocusTitleTests(unittest.TestCase):
    def test_rejects_non_string_titles_through_the_validation_error_contract(self) -> None:
        for level in ("update", "kiro", "focus"):
            for value in (None, [], {}, False, 1):
                event = focus_event()
                update = event["data"]["update"]
                target = {
                    "update": update,
                    "kiro": update["_meta"]["kiro"],
                    "focus": update["_meta"]["kiro"]["focus"],
                }[level]
                target["title"] = value
                with self.subTest(level=level, value=value), self.assertRaises(stream.StreamError):
                    stream._focus_update_title(event)

    def test_preserves_the_validated_title(self) -> None:
        self.assertEqual(stream._focus_update_title(focus_event()), "Review Python tooling")


if __name__ == "__main__":
    unittest.main()
