"""Validate one bounded Kiro 2.21.0 no-tool credential-smoke stream."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

MARKER = "PK-STACK-KIRO-AUTH-OK"
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_EVENTS = 4096
MAX_MARKER_DIAGNOSTIC_PATHS = 8
MAX_MARKER_DIAGNOSTIC_PATH_LENGTH = 256
MAX_FOCUS_TITLE_BYTES = 512
MAX_ASSISTANT_RESPONSE_BYTES = 256
_AGENT_MESSAGE_TAGS = {"agentmessagechunk", "assistantmessagechunk"}
_DISCRIMINATOR_KEYS = {"kind", "sessionupdate", "type", "updatetype"}
_SESSION_UPDATE_KINDS = {
    "agent_message_chunk",
    "agent_thought_chunk",
    "available_commands_update",
    "config_option_update",
    "session_info_update",
    "tool_call",
    "tool_call_update",
}
_CLOUD_CONFIG_TITLE = "Fetching your cloud config"
_CLOUD_CONFIG_TOOL_ID = "fetch_cloud_config"
_REQUIRED_SMOKE_MODEL = "gpt-5.6-sol"
_REQUIRED_REVIEW_MODEL = "claude-opus-5"
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
_TOOL_CALL_ID = re.compile(_UUID)
_SESSION_ID = re.compile(rf"sess_{_UUID}")
_REPLAY_ID = re.compile(r"[A-Za-z0-9_-]{40}")
_SAFE_PATH_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{0,63}")
_RUN_STATUS_DIAGNOSTIC_VALUES = {
    "cancelled",
    "completed",
    "error",
    "failed",
    "success",
}
_STOP_REASON_DIAGNOSTIC_VALUES = {
    "cancelled",
    "end_turn",
    "error",
    "max_tokens",
    "stop_sequence",
    "tool_use",
}
_FOCUS_TITLE_MARKER_PATHS = {
    "$.data.update._meta.kiro.focus.title",
    "$.data.update._meta.kiro.title",
    "$.data.update.title",
}


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


def _format_marker_path(path: tuple[str | int, ...]) -> str:
    rendered = "$"
    for segment in path:
        if isinstance(segment, int):
            rendered += f"[{segment}]"
        elif (
            _SAFE_PATH_KEY.fullmatch(segment) is not None
            and _SESSION_ID.fullmatch(segment) is None
            and _TOOL_CALL_ID.fullmatch(segment) is None
        ):
            rendered += f".{segment}"
        else:
            rendered += ".<redacted-key>"
        if len(rendered) > MAX_MARKER_DIAGNOSTIC_PATH_LENGTH:
            return "$.<path-too-long>"
    return rendered


def _marker_diagnostic(value: Any) -> tuple[list[str], int]:
    paths: list[str] = []
    match_count = 0
    pending: list[tuple[Any, tuple[str | int, ...]]] = [(value, ())]
    while pending:
        current, path = pending.pop()
        if isinstance(current, str) and MARKER in current:
            match_count += 1
            if len(paths) < MAX_MARKER_DIAGNOSTIC_PATHS:
                paths.append(_format_marker_path(path))
        if isinstance(current, dict):
            pending.extend((item, (*path, key)) for key, item in reversed(list(current.items())))
        elif isinstance(current, list):
            pending.extend(
                (item, (*path, index)) for index, item in reversed(list(enumerate(current)))
            )
    return paths, match_count


def _is_bounded_challenge_response(text: str) -> bool:
    try:
        response_bytes = len(text.encode("utf-8"))
    except UnicodeEncodeError:
        return False
    return 0 < response_bytes <= MAX_ASSISTANT_RESPONSE_BYTES and text.count(MARKER) == 1


def _focus_update_title(event: dict[str, Any]) -> str | None:
    _, update = _session_envelope(event, label="focus-update")
    if update.get("sessionUpdate") != "session_info_update":
        return None
    metadata = update.get("_meta")
    if not isinstance(metadata, dict):
        return None
    kiro_metadata = metadata.get("kiro")
    if not isinstance(kiro_metadata, dict) or kiro_metadata.get("kind") != "focus_update":
        return None
    if set(update) != {"_meta", "sessionUpdate", "title"}:
        raise StreamError("Kiro emitted a malformed focus-update event")
    if set(metadata) != {"kiro"} or set(kiro_metadata) != {"focus", "kind", "title"}:
        raise StreamError("Kiro emitted malformed focus-update metadata")
    focus = kiro_metadata.get("focus")
    if not isinstance(focus, dict) or set(focus) != {"title"}:
        raise StreamError("Kiro emitted malformed focus-update focus metadata")
    titles = (update.get("title"), kiro_metadata.get("title"), focus.get("title"))
    if (
        any(not isinstance(title, str) or not title for title in titles)
        or len(set(titles)) != 1
        or len(titles[0].encode("utf-8")) > MAX_FOCUS_TITLE_BYTES
    ):
        raise StreamError("Kiro emitted invalid or mismatched focus-update titles")
    return titles[0]


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
            base_keys = {"sessionUpdate", "status", "toolCallId"}
            if set(update) == base_keys:
                return "terminal", session_id, call_id
            if (
                set(update) != base_keys | {"rawOutput"}
                or update.get("rawOutput")
                != {"kind": "notEnabled", "retracted": False}
            ):
                raise StreamError(
                    "Kiro emitted a malformed completed cloud-config bootstrap terminal"
                )
            return "terminal", session_id, call_id
        raise StreamError("Kiro emitted an unexpected cloud-config bootstrap status")
    raise StreamError("Kiro attempted a non-bootstrap tool call during the no-tool smoke")


def _agent_text_event(
    event: dict[str, Any], *, expected_kind: str
) -> tuple[str, str, str]:
    label = "agent-thought" if expected_kind == "agent_thought_chunk" else "agent-message"
    session_id, update = _session_envelope(event, label=f"{label} chunk")
    if set(update) != {"_meta", "content", "sessionUpdate"}:
        raise StreamError(f"Kiro emitted a malformed {label} chunk")
    if update.get("sessionUpdate") != expected_kind:
        raise StreamError(f"Kiro emitted a legacy or nested {label} chunk")
    metadata = update.get("_meta")
    if not isinstance(metadata, dict) or set(metadata) != {"kiro"}:
        raise StreamError(f"Kiro emitted malformed {label} metadata")
    kiro_metadata = metadata.get("kiro")
    if not isinstance(kiro_metadata, dict) or set(kiro_metadata) != {"replayId"}:
        raise StreamError(f"Kiro emitted malformed {label} Kiro metadata")
    replay_id = kiro_metadata.get("replayId")
    if not isinstance(replay_id, str) or _REPLAY_ID.fullmatch(replay_id) is None:
        raise StreamError(f"Kiro emitted an invalid {label} replay ID")
    content = update.get("content")
    if not isinstance(content, dict) or set(content) != {"text", "type"}:
        raise StreamError(f"Kiro emitted malformed {label} content")
    text = content.get("text")
    if content.get("type") != "text" or not isinstance(text, str) or not text:
        raise StreamError(f"Kiro emitted a non-text or empty {label} chunk")
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


def _run_finished_diagnostic(data: dict[str, Any], *, assistant_text: str | None) -> dict[str, Any]:
    final_text = data.get("finalText")
    try:
        final_text_bytes = len(final_text.encode("utf-8")) if isinstance(final_text, str) else None
    except UnicodeEncodeError:
        final_text_bytes = None
    return {
        "assistant_final_equal": (
            assistant_text == final_text
            if assistant_text is not None and isinstance(final_text, str)
            else None
        ),
        "finalTextTruncated": (
            data.get("finalTextTruncated") if type(data.get("finalTextTruncated")) is bool else None
        ),
        "final_text_utf8_bytes": final_text_bytes,
        "marker_occurrence_count": (
            final_text.count(MARKER) if isinstance(final_text, str) else None
        ),
        "status": (
            data.get("status")
            if isinstance(data.get("status"), str)
            and data.get("status") in _RUN_STATUS_DIAGNOSTIC_VALUES
            else None
        ),
        "stopReason": (
            data.get("stopReason")
            if isinstance(data.get("stopReason"), str)
            and data.get("stopReason") in _STOP_REASON_DIAGNOSTIC_VALUES
            else None
        ),
    }


def _raise_run_finished_failure(data: dict[str, Any], *, assistant_text: str | None) -> None:
    diagnostic = _run_finished_diagnostic(data, assistant_text=assistant_text)
    raise StreamError(
        "Kiro runFinished did not attest one bounded successful challenge; "
        f"run_finished_diagnostic={json.dumps(diagnostic, separators=(',', ':'), sort_keys=True)}"
    )


def _validate_run_finished(event: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
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
        or not isinstance(final_text, str)
    ):
        _raise_run_finished_failure(data, assistant_text=None)
    return session_id, final_text, data


def _validated_assistant_text(
    events: list[dict[str, Any]],
    *,
    response_validator: Callable[[str], bool] = _is_bounded_challenge_response,
) -> str:
    if len(events) < 3:
        raise StreamError("Kiro stream is too short for a complete authenticated turn")
    _validate_run_started(events[0])
    finished_session, finished_text, finished_data = _validate_run_finished(events[-1])

    bootstrap_seen = False
    bootstrap_pending: tuple[str, str] | None = None
    bootstrap_session: str | None = None
    agent_session: str | None = None
    replay_id: str | None = None
    thought_replay_id: str | None = None
    agent_seen = False
    chunks: list[str] = []

    for event_index, event in enumerate(events[1:-1], start=1):
        if event.get("type") in {"runStarted", "runFinished"}:
            raise StreamError("Kiro emitted a duplicate or out-of-order run boundary")
        if event.get("type") != "sessionUpdate":
            raise StreamError("Kiro emitted an unknown top-level stream event")
        session_id, update = _session_envelope(event, label="session-update")
        if session_id != finished_session:
            raise StreamError("Kiro sessionUpdate and runFinished sessions do not match")
        if update.get("sessionUpdate") not in _SESSION_UPDATE_KINDS:
            raise StreamError("Kiro emitted an unknown session-update kind")
        focus_title = _focus_update_title(event)
        tags = _wire_tags(event)
        tool_event = any(tag.startswith("tool") for tag in tags)
        message_event = any(tag in _AGENT_MESSAGE_TAGS for tag in tags)

        if tool_event:
            if agent_seen or thought_replay_id is not None:
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

        if update.get("sessionUpdate") == "agent_thought_chunk":
            if bootstrap_pending is not None or agent_seen:
                raise StreamError("Kiro emitted agent thoughts outside the pre-answer phase")
            _, current_replay_id, _ = _agent_text_event(
                event, expected_kind="agent_thought_chunk"
            )
            if thought_replay_id is not None and thought_replay_id != current_replay_id:
                raise StreamError("Kiro agent-thought identity changed between chunks")
            thought_replay_id = current_replay_id
            # Observed Opus thoughts have their own replay ID. They are never
            # assistant-response chunks and cannot satisfy the final verdict.
            continue

        if message_event:
            if bootstrap_pending is not None:
                raise StreamError("Kiro agent text straddled cloud-config bootstrap metadata")
            session_id, current_replay_id, text = _agent_text_event(
                event, expected_kind="agent_message_chunk"
            )
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

        marker_paths, marker_path_count = _marker_diagnostic(event)
        if marker_path_count:
            if (
                focus_title is not None
                and marker_path_count == 3
                and set(marker_paths) == _FOCUS_TITLE_MARKER_PATHS
                and focus_title.count(MARKER) == 1
            ):
                continue
            diagnostic = {
                "event_index_0_based": event_index,
                "marker_path_count": marker_path_count,
                "marker_paths": marker_paths,
                "session_update_kind": update.get("sessionUpdate"),
            }
            raise StreamError(
                "Kiro marker appeared outside an exact agent-message event; "
                f"structural_diagnostic={json.dumps(diagnostic, separators=(',', ':'), sort_keys=True)}"
            )

    if bootstrap_pending is not None:
        raise StreamError("Kiro cloud-config bootstrap did not reach a terminal update")
    if not chunks or agent_session is None:
        raise StreamError("Kiro emitted no exact agent-message chunks")
    assistant_text = "".join(chunks)
    if finished_session != agent_session:
        raise StreamError("Kiro runFinished does not match the agent-message session")
    if finished_text != assistant_text or not response_validator(assistant_text):
        _raise_run_finished_failure(finished_data, assistant_text=assistant_text)
    if bootstrap_session is not None and bootstrap_session != finished_session:
        raise StreamError("Kiro bootstrap and runFinished sessions do not match")
    return assistant_text


def parse_no_tool_stream_bytes(
    stream_raw: bytes,
    *,
    maximum_bytes: int,
    maximum_events: int = MAX_EVENTS,
    response_validator: Callable[[str], bool],
) -> tuple[str, list[dict[str, Any]]]:
    """Parse one successful v3 turn that used no agent-visible tools."""

    if not stream_raw or len(stream_raw) > maximum_bytes:
        raise StreamError("Kiro stream is empty or exceeds its byte limit")
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
            if len(events) > maximum_events:
                raise StreamError("Kiro stream exceeded the event-count bound")
    except json.JSONDecodeError as exc:
        raise StreamError(f"Kiro stream contains malformed JSON: {exc}") from exc
    if not events:
        raise StreamError("Kiro emitted no stream-json events")
    return (
        _validated_assistant_text(events, response_validator=response_validator),
        events,
    )


def _validate_review_model_advertised(events: list[dict[str, Any]]) -> None:
    current_models: list[str] = []
    review_advertised = False
    for event in events:
        update = event.get("data", {}).get("update", {})
        if not isinstance(update, dict):
            continue
        for option in update.get("configOptions", []):
            if not isinstance(option, dict) or option.get("id") != "model":
                continue
            current = option.get("currentValue")
            if isinstance(current, str):
                current_models.append(current)
            choices = option.get("options")
            if not isinstance(choices, list):
                continue
            for choice in choices:
                if not isinstance(choice, dict) or choice.get("value") != _REQUIRED_REVIEW_MODEL:
                    continue
                kiro = choice.get("_meta", {}).get("kiro", {})
                if (
                    isinstance(kiro, dict)
                    and kiro.get("hasEffort") is True
                    and isinstance(kiro.get("effortLevels"), list)
                    and "xhigh" in kiro["effortLevels"]
                ):
                    review_advertised = True
    if (
        not current_models
        or current_models[-1] != _REQUIRED_SMOKE_MODEL
        or _REQUIRED_SMOKE_MODEL not in current_models
        or any(model not in {"auto", _REQUIRED_SMOKE_MODEL} for model in current_models)
        or not review_advertised
    ):
        raise StreamError(
            "Kiro credential stream did not advertise the required peer-review model"
        )


def validate_stream_bytes(
    stream_raw: bytes,
    stderr_raw: bytes,
    *,
    return_code: int,
    api_key: str,
    require_review_model: bool = False,
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
    _, events = parse_no_tool_stream_bytes(
        stream_raw,
        maximum_bytes=MAX_OUTPUT_BYTES,
        response_validator=_is_bounded_challenge_response,
    )
    if require_review_model:
        _validate_review_model_advertised(events)
    return {
        "ok": True,
        "events": len(events),
        **({"peer_review_model_advertised": True} if require_review_model else {}),
    }


def validate_stream_paths(
    stream_path: Path,
    stderr_path: Path,
    *,
    return_code: int,
    api_key: str,
    require_review_model: bool = False,
) -> dict[str, int | bool]:
    for path in (stream_path, stderr_path):
        if path.is_symlink() or not path.is_file():
            raise StreamError("Kiro output path is not a regular file")
    return validate_stream_bytes(
        stream_path.read_bytes(),
        stderr_path.read_bytes(),
        return_code=return_code,
        api_key=api_key,
        require_review_model=require_review_model,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    parser.add_argument("--return-code", type=int, required=True)
    parser.add_argument("--require-review-model", action="store_true")
    args = parser.parse_args()
    result = validate_stream_paths(
        args.stream,
        args.stderr,
        return_code=args.return_code,
        api_key=os.environ.get("KIRO_API_KEY", ""),
        require_review_model=args.require_review_model,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
