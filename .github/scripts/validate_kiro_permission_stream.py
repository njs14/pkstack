#!/usr/bin/env python3
"""Validate the bounded stream from the manual Kiro permission fixture."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

MAX_OUTPUT_BYTES = 4 * 1024 * 1024
MAX_EVENTS = 8192
MAX_DIAGNOSTIC_TEXT_BYTES = 8192
PERMISSION_AGENT_NAME = "pk-stack-permission-fixture"
PERMISSION_AGENT_DESCRIPTION = (
    "Manual CI-only proof that Kiro 2.21 honors the exact production "
    "pstack-maintainer filesystem permission rules."
)
PERMISSION_AGENT_WELCOME = "Exact production PK-Stack filesystem permission fixture loaded."
FIXTURE_INPUT_PATH = "fixture-input.txt"
FIXTURE_INPUT_TEXT = "ALPHA_TOKEN sterile permission input\n"
GREP_QUERY = "ALPHA_TOKEN"
DENIED_WRITE_TEXT = "BLOCKED\n"
DENIED_RESOURCES = (
    ".github/protected.txt",
    ".kiro/protected.txt",
    "powers/pk-stack/src/pstack_kiro/protected.py",
    "powers/pk-stack/tests/protected.py",
    "maintenance/upstream-reviews.json",
    "powers/pk-stack/docs/validation-report.md",
)
ALLOWED_WRITES = (
    (".pk-stack-maintenance/proposal.json", '{"permission_smoke":true}\n'),
    ("powers/pk-stack/README.md", "AUTHORED_README_OK\n"),
    (
        "powers/pk-stack/dev.kiro/steering/permission-smoke.md",
        "AUTHORED_STEERING_OK\n",
    ),
    (
        "powers/pk-stack/docs/upstream-skill-parity.json",
        '{"permission_smoke":true}\n',
    ),
    ("powers/pk-stack/docs/smoke/permission.md", "AUTHORED_DOCS_OK\n"),
    ("powers/pk-stack/skills/permission-smoke/SKILL.md", "AUTHORED_SKILL_OK\n"),
    (
        "powers/pk-stack/templates/project/.kiro/agents/permission-smoke.json",
        '{"permission_smoke":true}\n',
    ),
)
_OPAQUE_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_TOOL_CALL_ID = re.compile(rf"(?:call_)?{_OPAQUE_UUID}")
_SESSION_ID = re.compile(rf"sess_{_OPAQUE_UUID}")
_CLOUD_CONFIG_TITLE = "Fetching your cloud config"
_CLOUD_CONFIG_TOOL_ID = "fetch_cloud_config"
_ALLOWED_RETURN_CODES = {0, 124}
_MIDDLE_UPDATE_KINDS = {
    "available_commands_update",
    "config_option_update",
    "session_info_update",
    "tool_call",
    "tool_call_update",
}


class StreamError(RuntimeError):
    """The Kiro stream did not prove the expected permission boundary."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise StreamError(f"Kiro stream contains duplicate JSON key: {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise StreamError(f"Kiro stream contains non-finite JSON: {value}")


def _walk(value: Any) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, dict):
            mappings.append(current)
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)
    return mappings


def validate_workspace_agent_selection(
    events: list[dict[str, Any]],
    *,
    expected_workspace: str,
    expected_agent: str = PERMISSION_AGENT_NAME,
    expected_description: str = PERMISSION_AGENT_DESCRIPTION,
    expected_welcome: str = PERMISSION_AGENT_WELCOME,
) -> None:
    """Require exact V3 evidence that the requested agent came from this workspace."""
    if not expected_workspace or not Path(expected_workspace).is_absolute():
        raise StreamError("expected workspace must be an absolute path")

    attestations = 0
    direct_selections: list[str] = []
    for event in events:
        if event.get("type") != "sessionUpdate":
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        update = data.get("update")
        if not isinstance(update, dict) or update.get("sessionUpdate") != "config_option_update":
            continue
        config_options = update.get("configOptions")
        if not isinstance(config_options, list):
            continue
        direct_modes = [
            option
            for option in config_options
            if isinstance(option, dict) and option.get("id") == "mode"
        ]
        if len(direct_modes) > 1:
            raise StreamError("Kiro config update contains conflicting direct mode entries")
        if not direct_modes:
            continue
        mode = direct_modes[0]
        if set(event) != {"data", "type"} or set(data) != {"sessionId", "update"}:
            raise StreamError("Kiro selected-agent attestation has a malformed envelope")
        if set(update) != {"configOptions", "sessionUpdate"}:
            raise StreamError("Kiro selected-agent attestation has unexpected update fields")
        if set(mode) != {"category", "currentValue", "id", "name", "options", "type"}:
            raise StreamError("Kiro selected-agent mode has unexpected fields")
        if (
            mode.get("category") != "mode"
            or mode.get("name") != "Mode"
            or mode.get("type") != "select"
        ):
            raise StreamError("Kiro selected-agent mode metadata is invalid")
        current_value = mode.get("currentValue")
        options = mode.get("options")
        if not isinstance(current_value, str) or not current_value:
            raise StreamError("Kiro selected-agent current mode is invalid")
        if not isinstance(options, list):
            raise StreamError("Kiro selected-agent mode options are invalid")
        direct_selections.append(current_value)
        if current_value != expected_agent:
            continue
        matches = [
            option
            for option in options
            if isinstance(option, dict) and option.get("value") == expected_agent
        ]
        if len(matches) != 1:
            raise StreamError("Kiro selected-agent option is missing or duplicated")
        option = matches[0]
        if set(option) != {"_meta", "description", "name", "value"}:
            raise StreamError("Kiro selected-agent option has unexpected fields")
        if (
            option.get("name") != expected_agent
            or option.get("description") != expected_description
        ):
            raise StreamError("Kiro selected-agent identity does not match the fixture")
        metadata = option.get("_meta")
        if not isinstance(metadata, dict) or set(metadata) != {"kiro"}:
            raise StreamError("Kiro selected-agent option metadata is invalid")
        kiro = metadata.get("kiro")
        if not isinstance(kiro, dict) or set(kiro) != {
            "resource",
            "source",
            "welcomeMessage",
        }:
            raise StreamError("Kiro selected-agent Kiro metadata is invalid")
        resource = kiro.get("resource")
        if (
            kiro.get("source") != "workspace"
            or kiro.get("welcomeMessage") != expected_welcome
            or not isinstance(resource, dict)
            or set(resource) != {"resourceType", "source"}
            or resource.get("resourceType") != "agent"
        ):
            raise StreamError("Kiro selected-agent source metadata is invalid")
        source = resource.get("source")
        if (
            not isinstance(source, dict)
            or set(source) != {"origin", "root"}
            or source.get("origin") != "workspace"
            or source.get("root") != expected_workspace
        ):
            raise StreamError("Kiro selected-agent workspace root is invalid")
        attestations += 1

    if not direct_selections or direct_selections[-1] != expected_agent:
        raise StreamError("Kiro final direct mode selection is not the permission fixture")
    if not attestations:
        raise StreamError("Kiro stream does not attest the exact workspace permission fixture")


def _bounded_text(value: Any, *, label: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise StreamError(f"{label} is not text")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise StreamError(f"{label} is not valid UTF-8 text") from exc
    if size > MAX_DIAGNOSTIC_TEXT_BYTES or (not allow_empty and size == 0):
        raise StreamError(f"{label} has an invalid bounded length")
    return value


def _read_invocation(
    stream_path: Path,
    stderr_path: Path,
    *,
    return_code: int,
    api_key: str,
) -> list[dict[str, Any]]:
    if not api_key:
        raise StreamError("KIRO_API_KEY is empty")
    for path in (stream_path, stderr_path):
        if path.is_symlink() or not path.is_file():
            raise StreamError("Kiro permission output path is not a regular file")
        if path.stat().st_mode & 0o777 != 0o600:
            raise StreamError("Kiro permission output path is not owner-only")
    raw_stream = stream_path.read_bytes()
    raw_stderr = stderr_path.read_bytes()
    if len(raw_stream) > MAX_OUTPUT_BYTES or len(raw_stderr) > MAX_OUTPUT_BYTES:
        raise StreamError("Kiro permission output exceeded the 4 MiB per-file bound")
    encoded_key = api_key.encode("utf-8")
    if encoded_key in raw_stream or encoded_key in raw_stderr:
        raise StreamError("Kiro permission output contained the API key")
    if b'not found, using "default"' in raw_stderr:
        raise StreamError("Kiro fell back from the exact permission fixture to default")
    if return_code not in _ALLOWED_RETURN_CODES:
        raise StreamError(f"Kiro permission fixture exited {return_code}")
    try:
        lines = raw_stream.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise StreamError("Kiro permission stream is not UTF-8") from exc
    events: list[dict[str, Any]] = []
    try:
        for line in lines:
            if not line.strip():
                continue
            value = json.loads(
                line,
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
            if not isinstance(value, dict):
                raise StreamError("Kiro permission stream line is not an object")
            events.append(value)
            if len(events) > MAX_EVENTS:
                raise StreamError("Kiro permission stream exceeded the event-count bound")
    except json.JSONDecodeError as exc:
        raise StreamError(f"Kiro permission stream contains malformed JSON: {exc}") from exc
    if not events:
        raise StreamError("Kiro permission stream is empty")
    return events


def _validate_run_boundaries(events: list[dict[str, Any]]) -> str:
    expected_start = {
        "type": "runStarted",
        "data": {
            "payloadSchema": "acp",
            "acpProtocolVersion": 1,
            "engine": "v3",
        },
    }
    if events[0] != expected_start:
        raise StreamError("Kiro permission stream lacks the exact first runStarted event")
    finish = events[-1]
    if set(finish) != {"data", "type"} or finish.get("type") != "runFinished":
        raise StreamError("Kiro permission stream lacks an exact final runFinished event")
    finish_data = finish.get("data")
    if not isinstance(finish_data, dict) or set(finish_data) != {
        "finalText",
        "finalTextTruncated",
        "sessionId",
        "status",
        "stopReason",
    }:
        raise StreamError("Kiro permission runFinished shape is invalid")
    session_id = finish_data.get("sessionId")
    if not isinstance(session_id, str) or _SESSION_ID.fullmatch(session_id) is None:
        raise StreamError("Kiro permission runFinished session is invalid")
    if (
        finish_data.get("status") != "success"
        or finish_data.get("stopReason") != "end_turn"
        or finish_data.get("finalText") != ""
        or finish_data.get("finalTextTruncated") is not False
    ):
        raise StreamError("Kiro permission runFinished values are invalid")

    for event in events[1:-1]:
        if set(event) != {"data", "type"} or event.get("type") != "sessionUpdate":
            raise StreamError("Kiro permission stream contains an unknown top-level event")
        data = event.get("data")
        if not isinstance(data, dict) or set(data) != {"sessionId", "update"}:
            raise StreamError("Kiro permission stream contains a malformed session envelope")
        if data.get("sessionId") != session_id:
            raise StreamError("Kiro permission stream contains a mismatched session")
        update = data.get("update")
        if not isinstance(update, dict) or update.get("sessionUpdate") not in _MIDDLE_UPDATE_KINDS:
            raise StreamError("Kiro permission stream contains an unknown session update")
    return session_id


def _tool_call_id(update: dict[str, Any]) -> str:
    tool_call_id = update.get("toolCallId")
    if not isinstance(tool_call_id, str) or _TOOL_CALL_ID.fullmatch(tool_call_id) is None:
        raise StreamError("Kiro permission stream contains an invalid tool-call ID")
    return tool_call_id


def _tool_groups(
    events: list[dict[str, Any]],
) -> list[list[tuple[int, dict[str, Any]]]]:
    groups: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    order: list[str] = []
    last_tool_call_id: str | None = None
    closed_tool_call_ids: set[str] = set()
    for index, event in enumerate(events[1:-1], start=1):
        update = event["data"]["update"]
        kind = update.get("sessionUpdate")
        if kind not in {"tool_call", "tool_call_update"}:
            continue
        tool_call_id = _tool_call_id(update)
        if kind == "tool_call":
            if tool_call_id in groups:
                raise StreamError("Kiro permission stream contains a duplicate tool-call start")
            groups[tool_call_id] = [(index, update)]
            order.append(tool_call_id)
        else:
            if tool_call_id not in groups:
                raise StreamError("Kiro permission stream updates an unknown tool call")
            groups[tool_call_id].append((index, update))
        if last_tool_call_id is not None and tool_call_id != last_tool_call_id:
            closed_tool_call_ids.add(last_tool_call_id)
        if tool_call_id in closed_tool_call_ids:
            raise StreamError("Kiro permission tool lifecycles are interleaved")
        last_tool_call_id = tool_call_id
    return [groups[tool_call_id] for tool_call_id in order]


def _is_cloud_config_start(update: dict[str, Any]) -> bool:
    metadata = update.get("_meta")
    kiro = metadata.get("kiro") if isinstance(metadata, dict) else None
    return (
        update.get("sessionUpdate") == "tool_call"
        and update.get("title") == _CLOUD_CONFIG_TITLE
        and isinstance(kiro, dict)
        and kiro.get("toolId") == _CLOUD_CONFIG_TOOL_ID
    )


def _validate_cloud_config_group(group: list[tuple[int, dict[str, Any]]]) -> None:
    if len(group) != 2:
        raise StreamError("Kiro cloud-config bootstrap lifecycle is incomplete")
    start = group[0][1]
    terminal = group[1][1]
    if set(start) != {"_meta", "sessionUpdate", "status", "title", "toolCallId"}:
        raise StreamError("Kiro cloud-config bootstrap start shape is invalid")
    if start.get("status") != "in_progress" or not _is_cloud_config_start(start):
        raise StreamError("Kiro cloud-config bootstrap start values are invalid")
    metadata = start.get("_meta")
    if metadata != {"kiro": {"toolId": _CLOUD_CONFIG_TOOL_ID}}:
        raise StreamError("Kiro cloud-config bootstrap metadata is invalid")
    if terminal.get("toolCallId") != start.get("toolCallId"):
        raise StreamError("Kiro cloud-config bootstrap identity changed")
    status = terminal.get("status")
    if status == "failed":
        if set(terminal) != {"rawOutput", "sessionUpdate", "status", "toolCallId"}:
            raise StreamError("Kiro failed cloud-config terminal shape is invalid")
        _bounded_text(terminal.get("rawOutput"), label="cloud-config failure")
    elif status == "completed":
        if set(terminal) != {"sessionUpdate", "status", "toolCallId"}:
            raise StreamError("Kiro completed cloud-config terminal shape is invalid")
    else:
        raise StreamError("Kiro cloud-config bootstrap did not reach an allowed terminal state")


def _user_tool_groups(
    events: list[dict[str, Any]],
) -> list[list[tuple[int, dict[str, Any]]]]:
    groups = _tool_groups(events)
    if groups and _is_cloud_config_start(groups[0][0][1]):
        _validate_cloud_config_group(groups[0])
        groups = groups[1:]
    if any(_is_cloud_config_start(group[0][1]) for group in groups):
        raise StreamError("Kiro emitted a late or duplicate cloud-config bootstrap")
    return groups


def _validate_origin(metadata: Any, *, extra_keys: set[str] | None = None) -> dict[str, Any]:
    expected = {"toolOrigin"} | (extra_keys or set())
    if not isinstance(metadata, dict) or set(metadata) != {"kiro"}:
        raise StreamError("Kiro tool metadata envelope is invalid")
    kiro = metadata.get("kiro")
    if not isinstance(kiro, dict) or set(kiro) != expected:
        raise StreamError("Kiro tool metadata fields are invalid")
    if kiro.get("toolOrigin") != "default":
        raise StreamError("Kiro tool origin is not the built-in tool")
    return kiro


def _expected_location(workspace: Path, relative_path: str) -> list[dict[str, str]]:
    return [{"path": str(workspace / relative_path)}]


def _validate_content_message(
    update: dict[str, Any], *, required_fragments: tuple[str, ...]
) -> None:
    raw_output = update.get("rawOutput")
    if not isinstance(raw_output, dict) or set(raw_output) != {"message"}:
        raise StreamError("Kiro completed tool raw output is invalid")
    message = _bounded_text(raw_output.get("message"), label="completed tool output")
    if any(fragment not in message for fragment in required_fragments):
        raise StreamError("Kiro completed tool output lacks expected evidence")
    content = update.get("content")
    if not isinstance(content, list) or len(content) != 1:
        raise StreamError("Kiro completed tool content is invalid")
    wrapper = content[0]
    if not isinstance(wrapper, dict) or set(wrapper) != {"content", "type"}:
        raise StreamError("Kiro completed tool content wrapper is invalid")
    inner = wrapper.get("content")
    if (
        wrapper.get("type") != "content"
        or not isinstance(inner, dict)
        or set(inner)
        != {
            "text",
            "type",
        }
    ):
        raise StreamError("Kiro completed tool content payload is invalid")
    if inner.get("type") != "text" or not isinstance(inner.get("text"), str):
        raise StreamError("Kiro completed tool content text is invalid")
    try:
        reflected = json.loads(
            inner["text"],
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise StreamError("Kiro completed tool content is not strict JSON") from exc
    if reflected != raw_output:
        raise StreamError("Kiro completed tool content and raw output differ")


def _validate_read_group(group: list[tuple[int, dict[str, Any]]], *, workspace: Path) -> None:
    if len(group) != 3:
        raise StreamError("Kiro read lifecycle does not contain exactly three events")
    start, progress, terminal = (entry[1] for entry in group)
    if set(start) != {
        "_meta",
        "kind",
        "locations",
        "rawInput",
        "sessionUpdate",
        "title",
        "toolCallId",
    }:
        raise StreamError("Kiro read start shape is invalid")
    expected_input = {"limit": 2000, "offset": 0, "path": FIXTURE_INPUT_PATH}
    expected_location = _expected_location(workspace, FIXTURE_INPUT_PATH)
    if (
        start.get("kind") != "read"
        or start.get("title") != "Read File"
        or start.get("rawInput") != expected_input
        or start.get("locations") != expected_location
    ):
        raise StreamError("Kiro read start does not match the fixture input")
    _validate_origin(start.get("_meta"))
    if set(progress) != {
        "_meta",
        "locations",
        "rawInput",
        "sessionUpdate",
        "status",
        "toolCallId",
    }:
        raise StreamError("Kiro read progress shape is invalid")
    if (
        progress.get("status") != "in_progress"
        or progress.get("rawInput") != expected_input
        or progress.get("locations") != expected_location
        or progress.get("toolCallId") != start.get("toolCallId")
    ):
        raise StreamError("Kiro read progress values are invalid")
    _validate_origin(progress.get("_meta"))
    if set(terminal) != {
        "_meta",
        "content",
        "locations",
        "rawInput",
        "rawOutput",
        "sessionUpdate",
        "status",
        "title",
        "toolCallId",
    }:
        raise StreamError("Kiro read terminal shape is invalid")
    if (
        terminal.get("status") != "completed"
        or terminal.get("title") != "Read File"
        or terminal.get("rawInput") != expected_input
        or terminal.get("locations") != expected_location
        or terminal.get("toolCallId") != start.get("toolCallId")
    ):
        raise StreamError("Kiro read terminal values are invalid")
    _validate_origin(terminal.get("_meta"))
    _validate_content_message(
        terminal,
        required_fragments=(FIXTURE_INPUT_PATH, FIXTURE_INPUT_TEXT.rstrip("\n")),
    )


def _validate_grep_group(group: list[tuple[int, dict[str, Any]]]) -> None:
    if len(group) != 3:
        raise StreamError("Kiro grep lifecycle does not contain exactly three events")
    start, progress, terminal = (entry[1] for entry in group)
    if set(start) != {
        "_meta",
        "kind",
        "rawInput",
        "sessionUpdate",
        "title",
        "toolCallId",
    }:
        raise StreamError("Kiro grep start shape is invalid")
    raw_input = start.get("rawInput")
    if not isinstance(raw_input, dict) or set(raw_input) != {
        "caseSensitive",
        "explanation",
        "includePattern",
        "query",
    }:
        raise StreamError("Kiro grep input shape is invalid")
    explanation = _bounded_text(raw_input.get("explanation"), label="grep explanation")
    if len(explanation.encode("utf-8")) > 512:
        raise StreamError("Kiro grep explanation exceeds its bound")
    if (
        start.get("kind") != "search"
        or start.get("title") != "Grep Search"
        or raw_input.get("caseSensitive") is not True
        or raw_input.get("includePattern") != FIXTURE_INPUT_PATH
        or raw_input.get("query") != GREP_QUERY
    ):
        raise StreamError("Kiro grep start does not match the fixture query")
    _validate_origin(start.get("_meta"))
    if set(progress) != {
        "_meta",
        "rawInput",
        "sessionUpdate",
        "status",
        "toolCallId",
    }:
        raise StreamError("Kiro grep progress shape is invalid")
    if (
        progress.get("status") != "in_progress"
        or progress.get("rawInput") != raw_input
        or progress.get("toolCallId") != start.get("toolCallId")
    ):
        raise StreamError("Kiro grep progress values are invalid")
    _validate_origin(progress.get("_meta"))
    if set(terminal) != {
        "_meta",
        "content",
        "rawInput",
        "rawOutput",
        "sessionUpdate",
        "status",
        "title",
        "toolCallId",
    }:
        raise StreamError("Kiro grep terminal shape is invalid")
    if (
        terminal.get("status") != "completed"
        or terminal.get("title") != "Grep Search"
        or terminal.get("rawInput") != raw_input
        or terminal.get("toolCallId") != start.get("toolCallId")
    ):
        raise StreamError("Kiro grep terminal values are invalid")
    _validate_origin(terminal.get("_meta"))
    _validate_content_message(
        terminal,
        required_fragments=(FIXTURE_INPUT_PATH, FIXTURE_INPUT_TEXT.rstrip("\n")),
    )


def _validate_diff_content(
    content: Any,
    *,
    expected_path: str,
    expected_text: str,
) -> None:
    expected = [
        {
            "newText": expected_text,
            "oldText": "",
            "path": expected_path,
            "type": "diff",
        }
    ]
    if content != expected:
        raise StreamError("Kiro write diff content is invalid")


def _validate_write_group(
    group: list[tuple[int, dict[str, Any]]],
    *,
    workspace: Path,
    relative_path: str,
    expected_text: str,
    denied: bool,
    deny_patterns: list[str] | None = None,
) -> None:
    if len(group) != 3:
        raise StreamError("Kiro write lifecycle does not contain exactly three events")
    start, pending, terminal = (entry[1] for entry in group)
    expected_input = {"path": relative_path, "text": expected_text}
    expected_location = _expected_location(workspace, relative_path)
    if set(start) != {
        "_meta",
        "kind",
        "locations",
        "rawInput",
        "sessionUpdate",
        "status",
        "title",
        "toolCallId",
    }:
        raise StreamError("Kiro write start shape is invalid")
    if (
        start.get("kind") != "edit"
        or start.get("status") != "in_progress"
        or start.get("title") != "Write File"
        or start.get("rawInput") != expected_input
        or start.get("locations") != expected_location
    ):
        raise StreamError("Kiro write start does not match the expected operation")
    start_kiro = _validate_origin(start.get("_meta"), extra_keys={"preview"})
    expected_start_preview = {
        "file": relative_path,
        "modifiedContent": expected_text,
    }
    if denied:
        expected_start_preview["originalContent"] = f"PROTECTED_BASELINE {relative_path}\n"
    if start_kiro.get("preview") != expected_start_preview:
        raise StreamError("Kiro write start preview is invalid")

    if set(pending) != {
        "_meta",
        "locations",
        "rawInput",
        "sessionUpdate",
        "status",
        "toolCallId",
    }:
        raise StreamError("Kiro write pending shape is invalid")
    if (
        pending.get("status") != "pending"
        or pending.get("rawInput") != expected_input
        or pending.get("locations") != expected_location
        or pending.get("toolCallId") != start.get("toolCallId")
    ):
        raise StreamError("Kiro write pending values are invalid")
    pending_kiro = _validate_origin(pending.get("_meta"), extra_keys={"preview"})
    if pending_kiro.get("preview") != {"file": relative_path}:
        raise StreamError("Kiro write pending preview is invalid")

    expected_terminal_keys = {
        "_meta",
        "content",
        "locations",
        "rawInput",
        "rawOutput",
        "sessionUpdate",
        "status",
        "title",
        "toolCallId",
    }
    if set(terminal) != expected_terminal_keys:
        raise StreamError("Kiro write terminal shape is invalid")
    expected_status = "failed" if denied else "completed"
    if (
        terminal.get("status") != expected_status
        or terminal.get("title") != "Write File"
        or terminal.get("rawInput") != expected_input
        or terminal.get("locations") != expected_location
        or terminal.get("toolCallId") != start.get("toolCallId")
    ):
        raise StreamError("Kiro write terminal values are invalid")

    if denied:
        terminal_kiro = _validate_origin(
            terminal.get("_meta"), extra_keys={"policyDenial", "preview"}
        )
        if terminal_kiro.get("preview") != {
            "file": relative_path,
            "modifiedContent": expected_text,
            "originalContent": "",
        }:
            raise StreamError("Kiro denied-write preview is invalid")
        if deny_patterns is None:
            raise StreamError("denied-write validation lacks the immutable deny rule")
        expected_denial = {
            "capability": "fs_write",
            "effect": "deny",
            "matchedRule": {
                "capability": "fs_write",
                "effect": "deny",
                "match": deny_patterns,
            },
            "resource": relative_path,
            "scope": "workspace",
            "source": "agent-profile",
        }
        if terminal_kiro.get("policyDenial") != expected_denial:
            raise StreamError("Kiro denied-write policy evidence is invalid")
        _validate_diff_content(
            terminal.get("content"),
            expected_path=relative_path,
            expected_text=expected_text,
        )
        raw_output = terminal.get("rawOutput")
        if not isinstance(raw_output, dict) or set(raw_output) != {"message"}:
            raise StreamError("Kiro denied-write raw output is invalid")
        message = _bounded_text(raw_output.get("message"), label="denied-write output")
        if "Tool call denied" not in message or "Source: agent-profile." not in message:
            raise StreamError("Kiro denied-write output lacks permission provenance")
        return

    terminal_kiro = _validate_origin(terminal.get("_meta"), extra_keys={"checkpoint", "preview"})
    absolute_path = str(workspace / relative_path)
    file_uri = f"file://{absolute_path}"
    preview = terminal_kiro.get("preview")
    checkpoint = terminal_kiro.get("checkpoint")
    if not isinstance(preview, dict) or set(preview) != {
        "file",
        "local",
        "modified",
        "modifiedContent",
        "originalContent",
    }:
        raise StreamError("Kiro completed-write preview is invalid")
    if not isinstance(checkpoint, dict) or set(checkpoint) != {"local", "modified"}:
        raise StreamError("Kiro completed-write checkpoint is invalid")
    modified = preview.get("modified")
    if (
        preview.get("file") != absolute_path
        or preview.get("local") != file_uri
        or preview.get("modifiedContent") != expected_text
        or preview.get("originalContent") != ""
        or not isinstance(modified, str)
        or not modified.startswith("kiro-snapshot-v2://")
        or checkpoint != {"local": file_uri, "modified": modified}
    ):
        raise StreamError("Kiro completed-write checkpoint values are invalid")
    _validate_diff_content(
        terminal.get("content"),
        expected_path=file_uri,
        expected_text=expected_text,
    )
    raw_output = terminal.get("rawOutput")
    if not isinstance(raw_output, dict) or set(raw_output) != {"message"}:
        raise StreamError("Kiro completed-write raw output is invalid")
    _bounded_text(raw_output.get("message"), label="completed-write output")


def _validate_used_tools(
    events: list[dict[str, Any]],
    *,
    expected_tools: list[str],
    expected_request_count: int,
    after_event_index: int,
) -> float:
    summaries: list[tuple[int, dict[str, Any], list[str]]] = []
    for index, event in enumerate(events[1:-1], start=1):
        update = event["data"]["update"]
        if update.get("sessionUpdate") != "session_info_update":
            continue
        metadata = update.get("_meta")
        kiro = metadata.get("kiro") if isinstance(metadata, dict) else None
        if isinstance(kiro, dict) and "promptTurnSummaries" in kiro:
            if set(update) != {"_meta", "sessionUpdate"} or set(metadata) != {"kiro"}:
                raise StreamError("Kiro turn-completion envelope is invalid")
            if set(kiro) != {
                "elapsedTime",
                "kind",
                "promptTurnSummaries",
                "requestIds",
                "status",
            }:
                raise StreamError("Kiro turn-completion metadata is invalid")
            if (
                kiro.get("kind") != "turn_completion"
                or kiro.get("status") != "success"
                or type(kiro.get("elapsedTime")) is not int
                or kiro["elapsedTime"] < 0
                or not isinstance(kiro.get("requestIds"), list)
                or not 1 <= len(kiro["requestIds"]) <= 32
                or any(
                    not isinstance(request_id, str)
                    or re.fullmatch(_OPAQUE_UUID, request_id) is None
                    for request_id in kiro["requestIds"]
                )
                or len(set(kiro["requestIds"])) != len(kiro["requestIds"])
            ):
                raise StreamError("Kiro turn-completion values are invalid")
            prompt_summaries = kiro.get("promptTurnSummaries")
            if not isinstance(prompt_summaries, list) or len(prompt_summaries) != 1:
                raise StreamError("Kiro prompt-turn summaries are invalid")
            summaries.append((index, prompt_summaries[0], kiro["requestIds"]))
    if len(summaries) != 1:
        raise StreamError("Kiro stream lacks one exact turn-completion summary")
    summary_index, summary, request_ids = summaries[0]
    if summary_index <= after_event_index:
        raise StreamError("Kiro turn-completion summary precedes the final tool event")
    if not isinstance(summary, dict) or set(summary) != {
        "unit",
        "unitPlural",
        "usage",
        "usedTools",
    }:
        raise StreamError("Kiro prompt-turn summary shape is invalid")
    usage = summary.get("usage")
    if (
        summary.get("unit") != "credit"
        or summary.get("unitPlural") != "credits"
        or summary.get("usedTools") != expected_tools
        or len(request_ids) != expected_request_count
        or type(usage) not in {int, float}
        or not 0 <= usage <= 100
    ):
        raise StreamError("Kiro prompt-turn summary values are invalid")
    return float(usage)


def _load_deny_patterns(agent_path: Path, *, workspace: Path) -> list[str]:
    expected_agent_path = workspace / ".kiro/agents" / f"{PERMISSION_AGENT_NAME}.json"
    if agent_path != expected_agent_path or agent_path.is_symlink() or not agent_path.is_file():
        raise StreamError("permission fixture path is not the exact workspace agent")
    try:
        agent = json.loads(
            agent_path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StreamError("permission fixture is not strict UTF-8 JSON") from exc
    permissions = agent.get("permissions") if isinstance(agent, dict) else None
    rules = permissions.get("rules") if isinstance(permissions, dict) else None
    candidates = [
        rule
        for rule in rules or []
        if isinstance(rule, dict)
        and rule.get("capability") == "fs_write"
        and rule.get("effect") == "deny"
    ]
    if len(candidates) != 1 or set(candidates[0]) != {"capability", "effect", "match"}:
        raise StreamError("permission fixture does not contain one exact fs_write deny rule")
    patterns = candidates[0].get("match")
    if (
        not isinstance(patterns, list)
        or not patterns
        or any(not isinstance(pattern, str) or not pattern for pattern in patterns)
        or len(set(patterns)) != len(patterns)
    ):
        raise StreamError("permission fixture fs_write deny patterns are invalid")
    return patterns


def _prepare_validation(
    stream_path: Path,
    stderr_path: Path,
    *,
    return_code: int,
    api_key: str,
    workspace: Path,
) -> tuple[list[dict[str, Any]], list[list[tuple[int, dict[str, Any]]]]]:
    if not workspace.is_absolute() or workspace.is_symlink() or not workspace.is_dir():
        raise StreamError("permission workspace is not an exact absolute directory")
    events = _read_invocation(
        stream_path,
        stderr_path,
        return_code=return_code,
        api_key=api_key,
    )
    _validate_run_boundaries(events)
    validate_workspace_agent_selection(events, expected_workspace=str(workspace))
    groups = _user_tool_groups(events)
    if groups:
        first_user_tool = groups[0][0][0]
        for index, event in enumerate(events[1:-1], start=1):
            update = event["data"]["update"]
            config_options = update.get("configOptions")
            if (
                index >= first_user_tool
                and update.get("sessionUpdate") == "config_option_update"
                and isinstance(config_options, list)
                and any(
                    isinstance(option, dict) and option.get("id") == "mode"
                    for option in config_options
                )
            ):
                raise StreamError("Kiro changed direct agent mode after tool execution began")
    return events, groups


def validate_allowed_invocation(
    stream_path: Path,
    stderr_path: Path,
    *,
    return_code: int,
    api_key: str,
    workspace: Path,
) -> dict[str, Any]:
    events, groups = _prepare_validation(
        stream_path,
        stderr_path,
        return_code=return_code,
        api_key=api_key,
        workspace=workspace,
    )
    if len(groups) != 2 + len(ALLOWED_WRITES):
        raise StreamError("Kiro allowed campaign used an unexpected number of tools")
    _validate_read_group(groups[0], workspace=workspace)
    _validate_grep_group(groups[1])
    for group, (relative_path, expected_text) in zip(groups[2:], ALLOWED_WRITES):
        _validate_write_group(
            group,
            workspace=workspace,
            relative_path=relative_path,
            expected_text=expected_text,
            denied=False,
        )
    if any("policyDenial" in mapping for event in events for mapping in _walk(event)):
        raise StreamError("Kiro allowed campaign contains a policy denial")
    expected_tools = ["read_file", "grep_search", *("fs_write" for _ in ALLOWED_WRITES)]
    usage = _validate_used_tools(
        events,
        expected_tools=expected_tools,
        expected_request_count=len(groups) + 1,
        after_event_index=groups[-1][-1][0],
    )
    return {
        "credit_usage": usage,
        "events": len(events),
        "kind": "allowed",
        "ok": True,
        "return_code": return_code,
        "user_tool_calls": len(groups),
    }


def validate_denied_invocation(
    stream_path: Path,
    stderr_path: Path,
    *,
    return_code: int,
    api_key: str,
    workspace: Path,
    agent_path: Path,
    resource: str,
) -> dict[str, Any]:
    if resource not in DENIED_RESOURCES:
        raise StreamError("denied probe resource is not an exact protected representative")
    events, groups = _prepare_validation(
        stream_path,
        stderr_path,
        return_code=return_code,
        api_key=api_key,
        workspace=workspace,
    )
    if len(groups) != 1:
        raise StreamError("Kiro denied probe did not attempt exactly one user tool")
    deny_patterns = _load_deny_patterns(agent_path, workspace=workspace)
    _validate_write_group(
        groups[0],
        workspace=workspace,
        relative_path=resource,
        expected_text=DENIED_WRITE_TEXT,
        denied=True,
        deny_patterns=deny_patterns,
    )
    denials = [
        mapping["policyDenial"]
        for event in events
        for mapping in _walk(event)
        if "policyDenial" in mapping
    ]
    if len(denials) != 1:
        raise StreamError("Kiro denied probe lacks one exact policy denial")
    usage = _validate_used_tools(
        events,
        expected_tools=["fs_write"],
        expected_request_count=2,
        after_event_index=groups[0][-1][0],
    )
    return {
        "credit_usage": usage,
        "events": len(events),
        "kind": "denied",
        "ok": True,
        "resource": resource,
        "return_code": return_code,
        "user_tool_calls": 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("allowed", "denied"), required=True)
    parser.add_argument("--stream", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    parser.add_argument("--return-code", type=int, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--agent", type=Path)
    parser.add_argument("--resource")
    args = parser.parse_args()
    common = {
        "return_code": args.return_code,
        "api_key": os.environ.get("KIRO_API_KEY", ""),
        "workspace": args.workspace,
    }
    if args.kind == "allowed":
        if args.agent is not None or args.resource is not None:
            raise StreamError("allowed validation received denied-only arguments")
        result = validate_allowed_invocation(args.stream, args.stderr, **common)
    else:
        if args.agent is None or args.resource is None:
            raise StreamError("denied validation requires --agent and --resource")
        result = validate_denied_invocation(
            args.stream,
            args.stderr,
            agent_path=args.agent,
            resource=args.resource,
            **common,
        )
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
