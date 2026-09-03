"""Validate one bounded Kiro 2.21.0 no-tool credential-smoke stream."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

MARKER = "PK-STACK-KIRO-AUTH-OK"
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_EVENTS = 4096
_AGENT_MESSAGE_TAGS = {"agentmessagechunk", "assistantmessagechunk"}
_DISCRIMINATOR_KEYS = {"kind", "sessionupdate", "type", "updatetype"}
_SESSION_UPDATE_KINDS = {
    "agent_message_chunk",
    "available_commands_update",
    "config_option_update",
    "session_info_update",
    "tool_call",
    "tool_call_update",
}
_CLOUD_CONFIG_TITLE = "Fetching your cloud config"
_CLOUD_CONFIG_TOOL_ID = "fetch_cloud_config"
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
_TOOL_CALL_ID = re.compile(_UUID)
_SESSION_ID = re.compile(rf"sess_{_UUID}")
_REPLAY_ID = re.compile(r"[A-Za-z0-9_-]{40}")


class StreamError(RuntimeError):
    """The Kiro stream did not prove a safe authenticated exchange."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise StreamError(f"Kiro stream contains duplicate JSON key: {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise StreamError(f"Kiro stream contains non-finite JSON: {value}")


def _tag(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _is_usage_bucket(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"percent", "tokens"}:
        return False
    percent = value.get("percent")
    tokens = value.get("tokens")
    return (
        type(percent) in {int, float}
        and 0.0 <= percent <= 100.0
        and type(tokens) is int
        and tokens >= 0
    )


def _is_exact_tools_metric(event: dict[str, Any], path: tuple[str, ...], value: Any) -> bool:
    if path != ("data", "update", "_meta", "kiro", "breakdown", "tools"):
        return False
    if set(event) != {"data", "type"} or event.get("type") != "sessionUpdate":
        return False
    data = event.get("data")
    if not isinstance(data, dict) or set(data) != {"sessionId", "update"}:
        return False
    update = data.get("update")
    if not isinstance(update, dict) or update.get("sessionUpdate") != "session_info_update":
        return False
    metadata = update.get("_meta")
    if not isinstance(metadata, dict):
        return False
    kiro_metadata = metadata.get("kiro")
    if not isinstance(kiro_metadata, dict) or kiro_metadata.get("kind") != "context_usage":
        return False
    if not isinstance(value, dict) or set(value) != {
        "builtin",
        "mcp",
        "percent",
        "tokens",
    }:
        return False
    tokens = value.get("tokens")
    percent = value.get("percent")
    return (
        type(tokens) is int
        and tokens >= 0
        and type(percent) in {int, float}
        and 0.0 <= percent <= 100.0
        and _is_usage_bucket(value.get("builtin"))
        and _is_usage_bucket(value.get("mcp"))
    )


def _wire_tags(event: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    pending: list[tuple[Any, tuple[str, ...]]] = [(event, ())]
    while pending:
        current, path = pending.pop()
        if isinstance(current, dict):
            for key, item in current.items():
                next_path = (*path, key)
                normalized_key = _tag(key)
                if normalized_key in _AGENT_MESSAGE_TAGS:
                    tags.append(normalized_key)
                if normalized_key.startswith("tool") and not _is_exact_tools_metric(
                    event, next_path, item
                ):
                    tags.append(normalized_key)
                if normalized_key in _DISCRIMINATOR_KEYS and isinstance(item, str):
                    tags.append(_tag(item))
                pending.append((item, next_path))
        elif isinstance(current, list):
            pending.extend((item, (*path, str(index))) for index, item in enumerate(current))
    return tags


def _contains_marker(value: Any) -> bool:
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, str) and MARKER in current:
            return True
        if isinstance(current, dict):
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)
    return False


def _session_envelope(event: dict[str, Any], *, label: str) -> tuple[str, dict[str, Any]]:
    if set(event) != {"data", "type"} or event.get("type") != "sessionUpdate":
        raise StreamError(f"Kiro emitted a malformed {label} event")
    data = event.get("data")
    if not isinstance(data, dict) or set(data) != {"sessionId", "update"}:
        raise StreamError(f"Kiro emitted a malformed {label} envelope")
    session_id = data.get("sessionId")
    update = data.get("update")
    if not isinstance(session_id, str) or _SESSION_ID.fullmatch(session_id) is None:
        raise StreamError(f"Kiro emitted an invalid {label} session ID")
    if not isinstance(update, dict):
        raise StreamError(f"Kiro emitted a malformed {label} update")
    return session_id, update


def _bootstrap_tool_event(event: dict[str, Any]) -> tuple[str, str, str]:
    session_id, update = _session_envelope(event, label="cloud-config bootstrap")
    kind = update.get("sessionUpdate")
    call_id = update.get("toolCallId")
    if not isinstance(call_id, str) or _TOOL_CALL_ID.fullmatch(call_id) is None:
        raise StreamError("Kiro emitted an invalid cloud-config bootstrap call ID")
    if kind == "tool_call":
        if set(update) != {"_meta", "sessionUpdate", "status", "title", "toolCallId"}:
            raise StreamError("Kiro emitted a malformed cloud-config bootstrap start")
        if update.get("status") != "in_progress" or update.get("title") != _CLOUD_CONFIG_TITLE:
            raise StreamError("Kiro emitted an unexpected cloud-config bootstrap start")
        if update.get("_meta") != {"kiro": {"toolId": _CLOUD_CONFIG_TOOL_ID}}:
            raise StreamError("Kiro emitted an unexpected internal bootstrap tool ID")
        return "start", session_id, call_id
    if kind == "tool_call_update":
        status = update.get("status")
        if status == "failed":
            if set(update) != {"rawOutput", "sessionUpdate", "status", "toolCallId"}:
                raise StreamError("Kiro emitted a malformed failed cloud-config bootstrap terminal")
            raw_output = update.get("rawOutput")
            if not isinstance(raw_output, str) or not raw_output:
                raise StreamError("Kiro emitted an invalid failed cloud-config bootstrap terminal")
            return "terminal", session_id, call_id
        if status == "completed":
            if set(update) != {"sessionUpdate", "status", "toolCallId"}:
                raise StreamError(
                    "Kiro emitted a malformed completed cloud-config bootstrap terminal"
                )
            return "terminal", session_id, call_id
        raise StreamError("Kiro emitted an unexpected cloud-config bootstrap status")
    raise StreamError("Kiro attempted a non-bootstrap tool call during the no-tool smoke")


def _agent_message_event(event: dict[str, Any]) -> tuple[str, str, str]:
    session_id, update = _session_envelope(event, label="agent-message chunk")
    if set(update) != {"_meta", "content", "sessionUpdate"}:
        raise StreamError("Kiro emitted a malformed agent-message chunk")
    if update.get("sessionUpdate") != "agent_message_chunk":
        raise StreamError("Kiro emitted a legacy or nested agent-message chunk")
    metadata = update.get("_meta")
    if not isinstance(metadata, dict) or set(metadata) != {"kiro"}:
        raise StreamError("Kiro emitted malformed agent-message metadata")
    kiro_metadata = metadata.get("kiro")
    if not isinstance(kiro_metadata, dict) or set(kiro_metadata) != {"replayId"}:
        raise StreamError("Kiro emitted malformed agent-message Kiro metadata")
    replay_id = kiro_metadata.get("replayId")
    if not isinstance(replay_id, str) or _REPLAY_ID.fullmatch(replay_id) is None:
        raise StreamError("Kiro emitted an invalid agent-message replay ID")
    content = update.get("content")
    if not isinstance(content, dict) or set(content) != {"text", "type"}:
        raise StreamError("Kiro emitted malformed agent-message content")
    text = content.get("text")
    if content.get("type") != "text" or not isinstance(text, str) or not text:
        raise StreamError("Kiro emitted a non-text or empty agent-message chunk")
    return session_id, replay_id, text


def _validate_run_started(event: dict[str, Any]) -> None:
    if set(event) != {"data", "type"} or event.get("type") != "runStarted":
        raise StreamError("Kiro stream does not begin with the exact v3 runStarted event")
    data = event.get("data")
    if not isinstance(data, dict) or set(data) != {
        "acpProtocolVersion",
        "engine",
        "payloadSchema",
    }:
        raise StreamError("Kiro stream does not begin with the exact v3 runStarted event")
    if (
        data.get("payloadSchema") != "acp"
        or type(data.get("acpProtocolVersion")) is not int
        or data.get("acpProtocolVersion") != 1
        or data.get("engine") != "v3"
    ):
        raise StreamError("Kiro stream does not begin with the exact v3 runStarted event")


def _validate_run_finished(event: dict[str, Any]) -> tuple[str, str]:
    if set(event) != {"data", "type"} or event.get("type") != "runFinished":
        raise StreamError("Kiro stream does not end with the exact runFinished event")
    data = event.get("data")
    if not isinstance(data, dict) or set(data) != {
        "finalText",
        "finalTextTruncated",
        "sessionId",
        "status",
        "stopReason",
    }:
        raise StreamError("Kiro emitted a malformed runFinished event")
    session_id = data.get("sessionId")
    if not isinstance(session_id, str) or _SESSION_ID.fullmatch(session_id) is None:
        raise StreamError("Kiro emitted an invalid runFinished session ID")
    final_text = data.get("finalText")
    if (
        data.get("status") != "success"
        or data.get("stopReason") != "end_turn"
        or data.get("finalTextTruncated") is not False
        or final_text != MARKER
    ):
        raise StreamError("Kiro runFinished did not attest the exact successful marker")
    return session_id, final_text


def _validated_assistant_text(events: list[dict[str, Any]]) -> str:
    if len(events) < 3:
        raise StreamError("Kiro stream is too short for a complete authenticated turn")
    _validate_run_started(events[0])
    finished_session, finished_text = _validate_run_finished(events[-1])

    bootstrap_seen = False
    bootstrap_pending: tuple[str, str] | None = None
    bootstrap_session: str | None = None
    agent_session: str | None = None
    replay_id: str | None = None
    agent_seen = False
    chunks: list[str] = []

    for event in events[1:-1]:
        if event.get("type") in {"runStarted", "runFinished"}:
            raise StreamError("Kiro emitted a duplicate or out-of-order run boundary")
        if event.get("type") != "sessionUpdate":
            raise StreamError("Kiro emitted an unknown top-level stream event")
        session_id, update = _session_envelope(event, label="session-update")
        if session_id != finished_session:
            raise StreamError("Kiro sessionUpdate and runFinished sessions do not match")
        if update.get("sessionUpdate") not in _SESSION_UPDATE_KINDS:
            raise StreamError("Kiro emitted an unknown session-update kind")
        tags = _wire_tags(event)
        tool_event = any(tag.startswith("tool") for tag in tags)
        message_event = any(tag in _AGENT_MESSAGE_TAGS for tag in tags)

        if tool_event:
            if agent_seen:
                raise StreamError("Kiro emitted cloud-config bootstrap metadata after agent text")
            kind, session_id, call_id = _bootstrap_tool_event(event)
            if kind == "start":
                if bootstrap_seen or bootstrap_pending is not None:
                    raise StreamError("Kiro emitted a duplicate cloud-config bootstrap start")
                bootstrap_seen = True
                bootstrap_session = session_id
                bootstrap_pending = session_id, call_id
                continue
            if bootstrap_pending is None:
                raise StreamError("Kiro emitted an unpaired cloud-config bootstrap terminal")
            if bootstrap_pending != (session_id, call_id):
                raise StreamError("Kiro cloud-config bootstrap IDs changed before termination")
            bootstrap_pending = None
            continue

        if message_event:
            if bootstrap_pending is not None:
                raise StreamError("Kiro agent text straddled cloud-config bootstrap metadata")
            session_id, current_replay_id, text = _agent_message_event(event)
            if agent_session is None:
                agent_session = session_id
                replay_id = current_replay_id
            elif agent_session != session_id or replay_id != current_replay_id:
                raise StreamError("Kiro agent-message identity changed between chunks")
            if bootstrap_session is not None and bootstrap_session != session_id:
                raise StreamError("Kiro bootstrap and agent-message sessions do not match")
            agent_seen = True
            chunks.append(text)
            continue

        if _contains_marker(event):
            raise StreamError("Kiro marker appeared outside an exact agent-message event")

    if bootstrap_pending is not None:
        raise StreamError("Kiro cloud-config bootstrap did not reach a terminal update")
    if not chunks or agent_session is None:
        raise StreamError("Kiro emitted no exact agent-message chunks")
    assistant_text = "".join(chunks)
    if assistant_text != MARKER:
        raise StreamError("Kiro did not emit the exact marker in agent-message content")
    if finished_text != assistant_text or finished_session != agent_session:
        raise StreamError("Kiro runFinished does not match the exact agent-message result")
    if bootstrap_session is not None and bootstrap_session != finished_session:
        raise StreamError("Kiro bootstrap and runFinished sessions do not match")
    return assistant_text


def validate_stream_bytes(
    stream_raw: bytes,
    stderr_raw: bytes,
    *,
    return_code: int,
    api_key: str,
) -> dict[str, int | bool]:
    if not api_key:
        raise StreamError("KIRO_API_KEY is empty")
    if len(stream_raw) > MAX_OUTPUT_BYTES or len(stderr_raw) > MAX_OUTPUT_BYTES:
        raise StreamError("Kiro output exceeded the 2 MiB per-file bound")
    encoded_key = api_key.encode("utf-8")
    if encoded_key in stream_raw or encoded_key in stderr_raw:
        raise StreamError("Kiro output contained the API key")
    if return_code != 0:
        raise StreamError(f"Kiro credential smoke failed with exit code {return_code}")
    try:
        stream = stream_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StreamError("Kiro stream is not UTF-8") from exc

    events: list[dict[str, Any]] = []
    try:
        for line in stream.splitlines():
            if not line.strip():
                continue
            value = json.loads(
                line,
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
            if not isinstance(value, dict):
                raise StreamError("Kiro stream-json line was not an object")
            events.append(value)
            if len(events) > MAX_EVENTS:
                raise StreamError("Kiro stream exceeded the event-count bound")
    except json.JSONDecodeError as exc:
        raise StreamError(f"Kiro stream contains malformed JSON: {exc}") from exc
    if not events:
        raise StreamError("Kiro emitted no stream-json events")

    _validated_assistant_text(events)
    return {"ok": True, "events": len(events)}


def validate_stream_paths(
    stream_path: Path,
    stderr_path: Path,
    *,
    return_code: int,
    api_key: str,
) -> dict[str, int | bool]:
    for path in (stream_path, stderr_path):
        if path.is_symlink() or not path.is_file():
            raise StreamError("Kiro output path is not a regular file")
    return validate_stream_bytes(
        stream_path.read_bytes(),
        stderr_path.read_bytes(),
        return_code=return_code,
        api_key=api_key,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    parser.add_argument("--return-code", type=int, required=True)
    args = parser.parse_args()
    result = validate_stream_paths(
        args.stream,
        args.stderr,
        return_code=args.return_code,
        api_key=os.environ.get("KIRO_API_KEY", ""),
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
