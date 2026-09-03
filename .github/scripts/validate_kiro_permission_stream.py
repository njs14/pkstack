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
