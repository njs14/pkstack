"""Validate one bounded Kiro 2.21.0 no-tool credential-smoke stream."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

MARKER = "PK-STACK-KIRO-AUTH-OK"
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_EVENTS = 4096
_AGENT_MESSAGE_TAGS = {"agentmessagechunk", "assistantmessagechunk"}
_TOOL_TAGS = {
    "toolcall",
    "toolcallchunk",
    "toolcallupdate",
    "toolresult",
    "tooluse",
    "tooluseblock",
}
_DISCRIMINATOR_KEYS = {"kind", "sessionupdate", "type", "updatetype"}


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


def _walk_mappings(value: Any) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, dict):
            mappings.append(current)
            pending.extend(reversed(list(current.values())))
        elif isinstance(current, list):
            pending.extend(reversed(current))
    return mappings


def _structural_tags(value: dict[str, Any]) -> set[str]:
    tags: set[str] = set()
    for key, item in value.items():
        normalized_key = _tag(key)
        if normalized_key in _AGENT_MESSAGE_TAGS | _TOOL_TAGS:
            tags.add(normalized_key)
        if normalized_key in _DISCRIMINATOR_KEYS and isinstance(item, str):
            tags.add(_tag(item))
    return tags


def _content_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_content_text(item) for item in value)
    if isinstance(value, dict):
        return "".join(
            _content_text(item) for key, item in value.items() if _tag(key) in {"content", "text"}
        )
    return ""


def _agent_chunks(event: dict[str, Any]) -> list[str]:
    chunks: list[str] = []
    for mapping in _walk_mappings(event):
        tags = _structural_tags(mapping)
        if tags & _TOOL_TAGS:
            raise StreamError("Kiro attempted a tool call during the no-tool smoke")
        if not tags & _AGENT_MESSAGE_TAGS:
            continue
        for key, value in mapping.items():
            normalized_key = _tag(key)
            if normalized_key == "content" or normalized_key in _AGENT_MESSAGE_TAGS:
                chunks.append(_content_text(value))
    return chunks


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

    assistant_text = "".join(chunk for event in events for chunk in _agent_chunks(event)).strip()
    if assistant_text != MARKER:
        raise StreamError("Kiro did not emit the exact marker in agent-message content")
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
