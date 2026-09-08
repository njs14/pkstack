"""Attest the direct global agent selected for one bounded maintenance turn.

Global option metadata follows an observed Kiro 2.21.1 stream. Positive
maintainer fixtures are contract tests, not proof of live global discovery.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

from validate_kiro_credential_stream import (
    StreamError,
    _bootstrap_tool_event,
    _reject_constant,
    _session_envelope,
    _strict_object,
    _validate_run_finished,
    _validate_run_started,
)

REQUIRED_AGENT = "pkstack-maintainer"
MAX_OUTPUT_BYTES = 64 * 1024 * 1024
MAX_EVENT_BYTES = 16 * 1024 * 1024
MAX_STDERR_BYTES = 16 * 1024 * 1024
MAX_EVENTS = 65536
DEADLINE_SECONDS = 25 * 60
GRACE_SECONDS = 30
MAX_REPORT_BYTES = 8192
CATEGORIES = (
    "runStarted",
    "runFinished",
    "config_option_update",
    "agent_message_chunk",
    "agent_thought_chunk",
    "tool_call",
    "tool_call_update",
    "other",
    "invalid",
)


class AttestationError(ValueError):
    """Only fixed, non-sensitive failure codes leave this validator."""


def _json(raw: bytes) -> Any:
    return json.loads(
        raw.decode("utf-8"), object_pairs_hook=_strict_object, parse_constant=_reject_constant
    )


def _read_regular(path: Path, maximum: int) -> bytes:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > maximum:
        raise AttestationError("maintenance-agent-evidence-invalid")
    with path.open("rb") as handle:
        raw = handle.read(maximum + 1)
    if len(raw) > maximum:
        raise AttestationError("maintenance-agent-evidence-invalid")
    return raw


class StreamValidator:
    """One JSON event of buffering; every byte and event is inspected before disposal."""

    def __init__(self, profile: dict[str, Any], api_key: str):
        if not api_key:
            raise AttestationError("maintenance-agent-evidence-invalid")
        if (
            not isinstance(profile, dict)
            or profile.get("name") != REQUIRED_AGENT
            or not isinstance(profile.get("description"), str)
            or not profile["description"]
            or ("welcomeMessage" in profile and not isinstance(profile["welcomeMessage"], str))
        ):
            raise AttestationError("maintenance-agent-profile-invalid")
        self.profile = profile
        self.api_key = api_key
        self.secret = api_key.encode("utf-8")
        self.tails = {"stdout": b"", "stderr": b""}
        self.bytes = {"stdout": 0, "stderr": 0}
        self.counts = dict.fromkeys(CATEGORIES, 0)
        self.category_bytes = dict.fromkeys(CATEGORIES, 0)
        self.largest_event = 0
        self.events = 0
        self.discarded_bytes = {"stdout": 0, "stderr": 0}
        self.buffer = bytearray()
        self.session: str | None = None
        self.started = False
        self.terminal = False
        self.selected = False
        self.bootstrap_id: str | None = None
        self.bootstrap_closed = False

    def feed(self, chunk: bytes, *, stderr: bool = False) -> None:
        label = "stderr" if stderr else "stdout"
        self.bytes[label] += len(chunk)
        maximum = MAX_STDERR_BYTES if stderr else MAX_OUTPUT_BYTES
        if self.bytes[label] > maximum:
            raise AttestationError(f"maintenance-agent-{label}-limit")
        combined = self.tails[label] + chunk
        decoded = re.sub(
            rb"\\u00([0-9a-fA-F]{2})", lambda match: bytes([int(match[1], 16)]), combined
        ).replace(b"\\/", b"/")
        if self.secret in combined or self.secret in decoded:
            raise AttestationError("maintenance-agent-secret-detected")
        fallback = b'not found, using "default"'
        if stderr and fallback in combined:
            raise AttestationError("maintenance-agent-fallback")
        self.tails[label] = combined[-max(len(self.secret) * 6, len(fallback)) :]
        if stderr:
            return
        # Callers supply bounded chunks. Never split the whole transcript or retain events.
        for piece in chunk.splitlines(keepends=True):
            self.buffer.extend(piece)
            self.largest_event = max(self.largest_event, len(self.buffer))
            if len(self.buffer) > MAX_EVENT_BYTES:
                raise AttestationError("maintenance-agent-event-byte-limit")
            if self.buffer.endswith(b"\n"):
                self._line(bytes(self.buffer))
                self.buffer.clear()

    def _line(self, line: bytes) -> None:
        if not line.strip():
            self.category_bytes["other"] += len(line)
            return
        self.events += 1
        if self.events > MAX_EVENTS:
            raise AttestationError("maintenance-agent-event-count-limit")
        label = "invalid"
        try:
            event = _json(line)
            if not isinstance(event, dict):
                raise AttestationError("maintenance-agent-stream-invalid")
            kind = event.get("type")
            if kind == "sessionUpdate":
                data = event.get("data")
                update = data.get("update") if isinstance(data, dict) else None
                kind = update.get("sessionUpdate") if isinstance(update, dict) else None
            label = kind if isinstance(kind, str) and kind in CATEGORIES else "other"
            if self.api_key in json.dumps(event, ensure_ascii=False):
                raise AttestationError("maintenance-agent-secret-detected")
            self._event(event)
        except AttestationError:
            raise
        except (StreamError, ValueError, TypeError, RecursionError, OverflowError):
            raise AttestationError("maintenance-agent-stream-invalid") from None
        finally:
            self.counts[label] += 1
            self.category_bytes[label] += len(line)

    def _event(self, event: dict[str, Any]) -> None:
        if self.terminal:
            raise AttestationError("maintenance-agent-after-terminal")
        if not self.started:
            _validate_run_started(event)
            self.started = True
            return
        if event.get("type") == "runFinished":
            session, _, _ = _validate_run_finished(event)
            if self.session != session:
                raise AttestationError("maintenance-agent-session-mismatch")
            self.terminal = True
            return
        event_session, update = _session_envelope(event, label="maintenance")
        if self.session is None:
            self.session = event_session
        if event_session != self.session:
            raise AttestationError("maintenance-agent-session-mismatch")
        kind = update.get("sessionUpdate")
        if not isinstance(kind, str):
            raise AttestationError("maintenance-agent-stream-invalid")
        if kind == "config_option_update":
            if set(update) != {"sessionUpdate", "configOptions"}:
                raise AttestationError("maintenance-agent-selection-invalid")
            options = update["configOptions"]
            if not isinstance(options, list) or any(not isinstance(o, dict) for o in options):
                raise AttestationError("maintenance-agent-selection-invalid")
            modes = [o for o in options if o.get("id") == "mode"]
            if len(modes) > 1:
                raise AttestationError("maintenance-agent-selection-invalid")
            if not modes:
                return
            mode = modes[0]
            if (
                set(mode) != {"category", "currentValue", "id", "name", "options", "type"}
                or mode.get("category") != "mode"
                or mode.get("name") != "Mode"
                or mode.get("type") != "select"
                or not isinstance(mode.get("options"), list)
            ):
                raise AttestationError("maintenance-agent-selection-invalid")
            current = mode.get("currentValue")
            if current == "vibe" and not self.selected:
                return
            if current != REQUIRED_AGENT:
                raise AttestationError("maintenance-agent-fallback")
            matches = [
                o
                for o in mode["options"]
                if isinstance(o, dict) and o.get("value") == REQUIRED_AGENT
            ]
            kiro: dict[str, Any] = {
                "source": "global",
                "resource": {"resourceType": "agent", "source": {"origin": "user"}},
            }
            if "welcomeMessage" in self.profile:
                kiro["welcomeMessage"] = self.profile["welcomeMessage"]
            expected = {
                "name": REQUIRED_AGENT,
                "value": REQUIRED_AGENT,
                "description": self.profile["description"],
                "_meta": {"kiro": kiro},
            }
            if matches != [expected]:
                raise AttestationError("maintenance-agent-selection-invalid")
            self.selected = True
            return
        if kind in {"available_commands_update", "session_info_update"}:
            return
        # The one exact internal cloud-config lifecycle may precede agent
        # selection. User tools or model content never receive this exemption.
        if kind == "tool_call" and update.get("_meta") == {
            "kiro": {"toolId": "fetch_cloud_config"}
        }:
            phase, _, call_id = _bootstrap_tool_event(event)
            if self.bootstrap_id is not None or phase != "start":
                raise AttestationError("maintenance-agent-stream-invalid")
            self.bootstrap_id = call_id
            return
        if (
            kind == "tool_call_update"
            and self.bootstrap_id is not None
            and update.get("toolCallId") == self.bootstrap_id
        ):
            phase, _, _ = _bootstrap_tool_event(event)
            if self.bootstrap_closed or phase != "terminal":
                raise AttestationError("maintenance-agent-stream-invalid")
            self.bootstrap_closed = True
            return
        if not self.selected:
            raise AttestationError("maintenance-agent-selection-late")

    def finish(self, return_code: int) -> dict[str, Any]:
        if self.buffer:
            self._line(bytes(self.buffer))
            self.buffer.clear()
        if return_code != 0:
            raise AttestationError("maintenance-agent-run-failed")
        if not self.selected:
            raise AttestationError("maintenance-agent-selection-missing")
        if not self.terminal or (self.bootstrap_id is not None and not self.bootstrap_closed):
            raise AttestationError("maintenance-agent-stream-invalid")
        return {"ok": True, "selected_agent": REQUIRED_AGENT, "agent_source": "global"}

    def report(self, return_code: int | None, failure: str | None) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "bytes": self.bytes,
            "event_counts": self.counts,
            "event_bytes": self.category_bytes,
            "largest_event_bytes": self.largest_event,
            "events": self.events,
            "process_exit_status": return_code,
            "process_completed": return_code is not None,
            "process_succeeded": return_code == 0,
            "discarded_after_failure_bytes": self.discarded_bytes,
            "unclassified_stdout_bytes": self.bytes["stdout"] - sum(self.category_bytes.values()),
            "validation_complete": failure is None,
            "terminal_event_present": self.terminal,
            "agent_attestation": "passed" if failure is None else "failed",
            "candidate_acceptance": "not-evaluated",
            "reason": failure,
        }


def validate_stream_bytes(
    raw: bytes,
    stderr: bytes,
    *,
    profile: dict[str, Any],
    return_code: int,
    api_key: str,
) -> dict[str, Any]:
    validator = StreamValidator(profile, api_key)
    for data, is_stderr in ((raw, False), (stderr, True)):
        for offset in range(0, len(data), 65536):
            validator.feed(data[offset : offset + 65536], stderr=is_stderr)
    return validator.finish(return_code)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stream", required=True, type=Path)
    parser.add_argument("--stderr", required=True, type=Path)
    parser.add_argument("--agent", required=True, type=Path)
    parser.add_argument("--return-code", required=True, type=int)
    args = parser.parse_args()
    try:
        validator = StreamValidator(
            _json(_read_regular(args.agent, 128 * 1024)), os.environ.get("KIRO_API_KEY", "")
        )
        for path, is_stderr in ((args.stream, False), (args.stderr, True)):
            if not stat.S_ISREG(path.lstat().st_mode):
                raise AttestationError("maintenance-agent-evidence-invalid")
            with path.open("rb") as handle:
                while chunk := handle.read(65536):
                    validator.feed(chunk, stderr=is_stderr)
        result = validator.finish(args.return_code)
    except (
        AttestationError,
        OSError,
        StreamError,
        ValueError,
        RecursionError,
        OverflowError,
    ) as exc:
        code = (
            str(exc) if isinstance(exc, AttestationError) else "maintenance-agent-evidence-invalid"
        )
        print(code, file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
