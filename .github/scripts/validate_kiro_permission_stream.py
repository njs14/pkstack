#!/usr/bin/env python3
"""Validate the bounded stream from the manual Kiro permission fixture."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

MAX_OUTPUT_BYTES = 4 * 1024 * 1024
MAX_EVENTS = 8192
PERMISSION_AGENT_NAME = "pk-stack-permission-fixture"
PERMISSION_AGENT_DESCRIPTION = (
    "Manual CI-only proof that Kiro 2.21 honors the exact production "
    "pstack-maintainer filesystem permission rules."
)
PERMISSION_AGENT_WELCOME = "Exact production PK-Stack filesystem permission fixture loaded."


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


def validate(
    stream_path: Path, stderr_path: Path, return_code: int, api_key: str
) -> dict[str, Any]:
    if not api_key:
        raise StreamError("KIRO_API_KEY is empty")
    raw_stream = stream_path.read_bytes()
    raw_stderr = stderr_path.read_bytes()
    if len(raw_stream) > MAX_OUTPUT_BYTES or len(raw_stderr) > MAX_OUTPUT_BYTES:
        raise StreamError("Kiro permission output exceeded the 4 MiB per-file bound")
    encoded_key = api_key.encode("utf-8")
    if encoded_key in raw_stream or encoded_key in raw_stderr:
        raise StreamError("Kiro permission output contained the API key")
    if return_code != 0:
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

    mappings = [mapping for event in events for mapping in _walk(event)]
    denials = [mapping.get("policyDenial") for mapping in mappings if "policyDenial" in mapping]
    exact_denial = {
        "capability": "fs_write",
        "resource": "protected/blocked.txt",
        "effect": "deny",
        "scope": "workspace",
        "source": "agent-profile",
    }
    if exact_denial not in denials:
        raise StreamError("Kiro stream lacks the exact protected-write agent-profile denial")
    used_tools = {
        tool
        for mapping in mappings
        for tool in mapping.get("usedTools", [])
        if isinstance(tool, str)
    }
    if not {"read_file", "grep_search", "fs_write"} <= used_tools:
        raise StreamError("Kiro completion did not attest read, grep, and write tool use")
    finished = any(
        (
            isinstance(mapping.get("runFinished"), dict)
            and mapping["runFinished"].get("status") == "success"
        )
        or (
            mapping.get("status") == "success"
            and any(
                str(mapping.get(key, "")).lower().replace("_", "") == "runfinished"
                for key in ("type", "kind", "sessionUpdate", "updateType")
            )
        )
        for mapping in mappings
    )
    if not finished:
        raise StreamError("Kiro permission stream lacks a successful runFinished event")
    return {"ok": True, "events": len(events)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    parser.add_argument("--return-code", type=int, required=True)
    args = parser.parse_args()
    result = validate(
        args.stream,
        args.stderr,
        args.return_code,
        os.environ.get("KIRO_API_KEY", ""),
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
