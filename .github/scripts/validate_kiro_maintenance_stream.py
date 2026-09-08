"""Attest the direct global agent selected for one bounded maintenance turn.

Global option metadata follows an observed Kiro 2.21.1 stream. Positive
maintainer fixtures are contract tests, not proof of live global discovery.
"""

from __future__ import annotations

import argparse
import json
import os
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
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
MAX_EVENTS = 65536
DIAGNOSTIC_SAMPLE_BYTES = 8 * 1024 * 1024


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
    return path.read_bytes()


def summarize_private_evidence(stream: Path, stderr: Path, return_code: int) -> dict[str, Any]:
    """Emit only fixed labels and numeric observations, never private content."""
    counts = dict.fromkeys(
        (
            "runStarted",
            "runFinished",
            "config_option_update",
            "agent_message_chunk",
            "agent_thought_chunk",
            "tool_call",
            "tool_call_update",
            "other",
            "invalid",
        ),
        0,
    )
    tool_counts = dict.fromkeys(("fs_read", "fs_write", "grep", "other"), 0)
    sizes: dict[str, int | None] = {}
    sample = b""
    tail = b""
    for label, path in (("stream", stream), ("stderr", stderr)):
        metadata = path.lstat()
        sizes[label] = metadata.st_size if stat.S_ISREG(metadata.st_mode) else None
        if label == "stream" and sizes[label] is not None:
            with path.open("rb") as handle:
                sample = handle.read(DIAGNOSTIC_SAMPLE_BYTES)
                handle.seek(max(0, metadata.st_size - 65536))
                tail = handle.read(65536)
    lines = sample.split(b"\n")
    if sizes["stream"] != len(sample) and not sample.endswith(b"\n"):
        lines.pop()
    for line in lines[:MAX_EVENTS]:
        if not line.strip():
            continue
        try:
            event = _json(line)
            if not isinstance(event, dict):
                raise ValueError
            kind = event.get("type")
            update = {}
            if kind == "sessionUpdate":
                update = event.get("data", {}).get("update", {})
                kind = update.get("sessionUpdate")
            label = kind if isinstance(kind, str) and kind in counts else "other"
            counts[label] += 1
            if label == "tool_call":
                tool = update.get("_meta", {}).get("kiro", {}).get("toolId")
                tool_counts[tool if isinstance(tool, str) and tool in tool_counts else "other"] += 1
        except (StreamError, ValueError, TypeError, AttributeError, RecursionError, OverflowError):
            counts["invalid"] += 1
    terminal = False
    try:
        last = _json(tail.rstrip(b"\n").rsplit(b"\n", 1)[-1])
        terminal = isinstance(last, dict) and last.get("type") == "runFinished"
    except (StreamError, ValueError, TypeError, RecursionError, OverflowError):
        pass
    return {
        "diagnostic": "maintenance-private-evidence",
        "return_code": return_code,
        "bytes": sizes,
        "sampled_stream_bytes": len(sample),
        "sample_incomplete": sizes["stream"] != len(sample) or len(lines) > MAX_EVENTS,
        "sample_event_counts": counts,
        "sample_tool_counts": tool_counts,
        "terminal_event_present": terminal,
    }


def validate_stream_bytes(
    raw: bytes,
    stderr: bytes,
    *,
    profile: dict[str, Any],
    return_code: int,
    api_key: str,
) -> dict[str, Any]:
    """Validate selection, not repair semantics or the model's claimed outcome."""
    try:
        if not api_key or len(raw) > MAX_OUTPUT_BYTES or len(stderr) > MAX_OUTPUT_BYTES:
            raise AttestationError("maintenance-agent-evidence-invalid")
        if api_key.encode("utf-8") in raw or api_key.encode("utf-8") in stderr:
            raise AttestationError("maintenance-agent-secret-detected")
        if b'not found, using "default"' in stderr:
            raise AttestationError("maintenance-agent-fallback")
        if return_code != 0:
            raise AttestationError("maintenance-agent-run-failed")
        if (
            not isinstance(profile, dict)
            or profile.get("name") != REQUIRED_AGENT
            or not isinstance(profile.get("description"), str)
            or not profile["description"]
            or ("welcomeMessage" in profile and not isinstance(profile["welcomeMessage"], str))
        ):
            raise AttestationError("maintenance-agent-profile-invalid")
        events = []
        for line in raw.splitlines():
            if line.strip():
                event = _json(line)
                if not isinstance(event, dict) or len(events) >= MAX_EVENTS:
                    raise AttestationError("maintenance-agent-stream-invalid")
                if api_key in json.dumps(event, ensure_ascii=False):
                    raise AttestationError("maintenance-agent-secret-detected")
                events.append(event)
        if len(events) < 3:
            raise AttestationError("maintenance-agent-selection-missing")
        _validate_run_started(events[0])
        session, _, _ = _validate_run_finished(events[-1])
        selected = False
        bootstrap_id: str | None = None
        bootstrap_closed = False
        for event in events[1:-1]:
            event_session, update = _session_envelope(event, label="maintenance")
            if event_session != session:
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
                    continue
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
                if current == "vibe" and not selected:
                    continue
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
                if "welcomeMessage" in profile:
                    kiro["welcomeMessage"] = profile["welcomeMessage"]
                expected = {
                    "name": REQUIRED_AGENT,
                    "value": REQUIRED_AGENT,
                    "description": profile["description"],
                    "_meta": {"kiro": kiro},
                }
                if matches != [expected]:
                    raise AttestationError("maintenance-agent-selection-invalid")
                selected = True
                continue
            if kind in {"available_commands_update", "session_info_update"}:
                continue
            # The one exact internal cloud-config lifecycle may precede agent
            # selection. User tools or model content never receive this exemption.
            if kind == "tool_call" and update.get("_meta") == {
                "kiro": {"toolId": "fetch_cloud_config"}
            }:
                phase, _, call_id = _bootstrap_tool_event(event)
                if bootstrap_id is not None or phase != "start":
                    raise AttestationError("maintenance-agent-stream-invalid")
                bootstrap_id = call_id
                continue
            if (
                kind == "tool_call_update"
                and bootstrap_id is not None
                and update.get("toolCallId") == bootstrap_id
            ):
                phase, _, _ = _bootstrap_tool_event(event)
                if bootstrap_closed or phase != "terminal":
                    raise AttestationError("maintenance-agent-stream-invalid")
                bootstrap_closed = True
                continue
            if not selected:
                raise AttestationError("maintenance-agent-selection-late")
        if not selected:
            raise AttestationError("maintenance-agent-selection-missing")
        if bootstrap_id is not None and not bootstrap_closed:
            raise AttestationError("maintenance-agent-stream-invalid")
        return {"ok": True, "selected_agent": REQUIRED_AGENT, "agent_source": "global"}
    except AttestationError:
        raise
    except (StreamError, ValueError, TypeError, RecursionError, OverflowError):
        raise AttestationError("maintenance-agent-stream-invalid") from None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stream", required=True, type=Path)
    parser.add_argument("--stderr", required=True, type=Path)
    parser.add_argument("--agent", required=True, type=Path)
    parser.add_argument("--return-code", required=True, type=int)
    parser.add_argument("--diagnostics-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.diagnostics_only:
            print(
                json.dumps(
                    summarize_private_evidence(args.stream, args.stderr, args.return_code),
                    sort_keys=True,
                )
            )
            return 0
        result = validate_stream_bytes(
            _read_regular(args.stream, MAX_OUTPUT_BYTES),
            _read_regular(args.stderr, MAX_OUTPUT_BYTES),
            profile=_json(_read_regular(args.agent, 128 * 1024)),
            return_code=args.return_code,
            api_key=os.environ.get("KIRO_API_KEY", ""),
        )
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
