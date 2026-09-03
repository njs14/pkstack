#!/usr/bin/env python3
"""Validate one no-tool Kiro peer-review turn and its exact-candidate verdict."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

from validate_kiro_credential_stream import (
    StreamError,
    parse_no_tool_stream_bytes,
)

MAX_STREAM_BYTES = 16 * 1024 * 1024
MAX_STDERR_BYTES = 16 * 1024 * 1024
MAX_RESPONSE_BYTES = 128 * 1024
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_MODEL = "claude-opus-5"
REQUIRED_EFFORT = "xhigh"
REQUIRED_AGENT = "pstack-ci-reviewer"


class ReviewError(RuntimeError):
    """The Kiro review did not prove a bound, clean approval."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ReviewError(f"review verdict contains duplicate key: {key!r}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise ReviewError(f"review verdict contains non-finite JSON: {value}")


def _read_regular(path: Path, maximum: int, label: str) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ReviewError(f"{label} is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > maximum:
        raise ReviewError(f"{label} must be a bounded regular file")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ReviewError(f"{label} could not be read") from exc


def _bounded_response(text: str) -> bool:
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError:
        return False
    return 0 < size <= MAX_RESPONSE_BYTES


def _validate_model_event(events: list[dict[str, Any]], expected_model: str) -> None:
    current_models: list[str] = []
    advertised = False
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
            if isinstance(choices, list):
                advertised = advertised or any(
                    isinstance(choice, dict)
                    and choice.get("value") == expected_model
                    and isinstance(choice.get("_meta", {}).get("kiro"), dict)
                    and choice["_meta"]["kiro"].get("hasEffort") is True
                    for choice in choices
                )
    if (
        not current_models
        or current_models[-1] != expected_model
        or expected_model not in current_models
        or any(model not in {"auto", expected_model} for model in current_models)
        or not advertised
    ):
        raise ReviewError("Kiro stream did not bind the peer review to the required model")


def _validate_agent_event(events: list[dict[str, Any]]) -> None:
    current_modes: list[str] = []
    for event in events:
        update = event.get("data", {}).get("update", {})
        if not isinstance(update, dict):
            continue
        for option in update.get("configOptions", []):
            if not isinstance(option, dict) or option.get("id") != "mode":
                continue
            current = option.get("currentValue")
            if isinstance(current, str):
                current_modes.append(current)
    if (
        not current_modes
        or current_modes[-1] != REQUIRED_AGENT
        or REQUIRED_AGENT not in current_modes
        or any(mode not in {"vibe", REQUIRED_AGENT} for mode in current_modes)
    ):
        raise ReviewError("Kiro stream did not bind the peer review to the required agent")


def _validate_bundle(
    raw: bytes,
    *,
    base_sha: str,
    head_sha: str,
    content_sha256: str,
    patch_sha256: str,
) -> tuple[int, str]:
    if hashlib.sha256(raw).hexdigest() != content_sha256:
        raise ReviewError("candidate review bundle content digest changed")
    try:
        bundle = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewError("candidate review bundle is not strict UTF-8 JSON") from exc
    expected_keys = {
        "schema_version",
        "review_type",
        "base_sha",
        "head_sha",
        "requires_review",
        "changed_files",
        "changed_lines",
        "paths",
        "paths_sha256",
        "patch_sha256",
        "patch",
    }
    if not isinstance(bundle, dict) or set(bundle) != expected_keys:
        raise ReviewError("candidate review bundle contract changed")
    if (
        bundle.get("schema_version") != 1
        or bundle.get("review_type") != "mandatory-independent-exact-candidate"
        or bundle.get("requires_review") is not True
        or bundle.get("base_sha") != base_sha
        or bundle.get("head_sha") != head_sha
        or bundle.get("patch_sha256") != patch_sha256
    ):
        raise ReviewError("candidate review bundle identity changed")
    paths = bundle.get("paths")
    paths_sha256 = bundle.get("paths_sha256")
    changed_files = bundle.get("changed_files")
    changed_lines = bundle.get("changed_lines")
    patch = bundle.get("patch")
    if (
        not isinstance(paths, list)
        or not paths
        or paths != sorted(paths)
        or len(paths) != len(set(paths))
        or not all(isinstance(path, str) and path for path in paths)
        or type(changed_files) is not int
        or changed_files != len(paths)
        or type(changed_lines) is not int
        or changed_lines < 1
        or not isinstance(patch, str)
        or hashlib.sha256(patch.encode("utf-8")).hexdigest() != patch_sha256
    ):
        raise ReviewError("candidate review bundle facts are malformed")
    paths_raw = json.dumps(paths, ensure_ascii=False, separators=(",", ":")).encode()
    computed_paths_sha256 = hashlib.sha256(paths_raw).hexdigest()
    if paths_sha256 != computed_paths_sha256:
        raise ReviewError("candidate review bundle paths digest changed")
    return changed_files, computed_paths_sha256


def _validate_verdict(
    text: str,
    *,
    base_sha: str,
    head_sha: str,
    content_sha256: str,
    patch_sha256: str,
    changed_files: int,
    paths_sha256: str,
) -> tuple[dict[str, Any], bytes]:
    try:
        raw = text.encode("utf-8")
        verdict = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeEncodeError, json.JSONDecodeError) as exc:
        raise ReviewError("Kiro peer-review response is not strict JSON") from exc
    expected_keys = {
        "verdict",
        "reviewed_base_sha",
        "reviewed_head_sha",
        "reviewed_content_sha256",
        "reviewed_patch_sha256",
        "reviewed_changed_files",
        "reviewed_paths_sha256",
        "material_findings",
        "summary",
    }
    if not isinstance(verdict, dict) or set(verdict) != expected_keys:
        raise ReviewError("Kiro peer-review verdict has unexpected or missing keys")
    expected = {
        "reviewed_base_sha": base_sha,
        "reviewed_head_sha": head_sha,
        "reviewed_content_sha256": content_sha256,
        "reviewed_patch_sha256": patch_sha256,
        "reviewed_changed_files": changed_files,
        "reviewed_paths_sha256": paths_sha256,
    }
    for key, value in expected.items():
        if verdict.get(key) != value:
            raise ReviewError(f"Kiro peer-review verdict is not bound to exact {key}")
    findings = verdict.get("material_findings")
    if (
        not isinstance(findings, list)
        or len(findings) > 32
        or not all(
            isinstance(item, str)
            and item == item.strip()
            and 1 <= len(item.encode("utf-8")) <= 2_000
            for item in findings
        )
    ):
        raise ReviewError("Kiro peer-review material findings are malformed")
    summary = verdict.get("summary")
    if (
        not isinstance(summary, str)
        or summary != summary.strip()
        or not 1 <= len(summary.encode("utf-8")) <= 4_000
    ):
        raise ReviewError("Kiro peer-review summary is malformed")
    if verdict.get("verdict") != "approved" or findings:
        raise ReviewError("Kiro peer reviewer did not approve without material findings")
    return verdict, raw


def validate(args: argparse.Namespace) -> dict[str, str]:
    if args.model != REQUIRED_MODEL or args.effort != REQUIRED_EFFORT:
        raise ReviewError(
            "Kiro peer review must use claude-opus-5 at xhigh effort"
        )
    for value, pattern, label in (
        (args.base, SHA1, "base SHA"),
        (args.head, SHA1, "head SHA"),
        (args.content_sha256, SHA256, "content digest"),
        (args.patch_sha256, SHA256, "patch digest"),
    ):
        if pattern.fullmatch(value) is None:
            raise ReviewError(f"invalid {label}")
    stream_raw = _read_regular(args.stream, MAX_STREAM_BYTES, "Kiro review stream")
    stderr_raw = _read_regular(args.stderr, MAX_STDERR_BYTES, "Kiro review stderr")
    bundle_raw = _read_regular(args.bundle, MAX_STREAM_BYTES, "candidate review bundle")
    changed_files, paths_sha256 = _validate_bundle(
        bundle_raw,
        base_sha=args.base,
        head_sha=args.head,
        content_sha256=args.content_sha256,
        patch_sha256=args.patch_sha256,
    )
    api_key = os.environ.get("KIRO_API_KEY", "")
    if not api_key:
        raise ReviewError("KIRO_API_KEY is empty during review validation")
    encoded_key = api_key.encode("utf-8")
    if encoded_key in stream_raw or encoded_key in stderr_raw:
        raise ReviewError("Kiro review output contained the API key")
    if b'not found, using "default"' in stderr_raw:
        raise ReviewError("Kiro fell back from the required reviewer agent")
    if args.return_code != 0:
        raise ReviewError(f"Kiro peer review failed with exit code {args.return_code}")
    try:
        assistant_text, events = parse_no_tool_stream_bytes(
            stream_raw,
            maximum_bytes=MAX_STREAM_BYTES,
            response_validator=_bounded_response,
        )
    except StreamError as exc:
        raise ReviewError(str(exc)) from exc
    _validate_model_event(events, args.model)
    _validate_agent_event(events)
    _, verdict_raw = _validate_verdict(
        assistant_text,
        base_sha=args.base,
        head_sha=args.head,
        content_sha256=args.content_sha256,
        patch_sha256=args.patch_sha256,
        changed_files=changed_files,
        paths_sha256=paths_sha256,
    )
    stream_sha256 = hashlib.sha256(stream_raw).hexdigest()
    verdict_sha256 = hashlib.sha256(verdict_raw).hexdigest()
    attestation = json.dumps(
        {
            "base_sha": args.base,
            "head_sha": args.head,
            "content_sha256": args.content_sha256,
            "patch_sha256": args.patch_sha256,
            "changed_files": changed_files,
            "paths_sha256": paths_sha256,
            "stream_sha256": stream_sha256,
            "verdict_sha256": verdict_sha256,
            "model": args.model,
            "configured_effort": args.effort,
            "agent": REQUIRED_AGENT,
            "provider": "kiro",
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return {
        "reviewed_base_sha": args.base,
        "reviewed_head_sha": args.head,
        "reviewed_content_sha256": args.content_sha256,
        "reviewed_patch_sha256": args.patch_sha256,
        "reviewed_changed_files": str(changed_files),
        "reviewed_paths_sha256": paths_sha256,
        "reviewed_agent": REQUIRED_AGENT,
        "reviewed_model": args.model,
        "reviewed_effort": args.effort,
        "execution_evidence_sha256": stream_sha256,
        "verdict_sha256": verdict_sha256,
        "attestation_sha256": hashlib.sha256(attestation).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--return-code", type=int, required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--content-sha256", required=True)
    parser.add_argument("--patch-sha256", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", required=True)
    parser.add_argument("--github-output")
    args = parser.parse_args()
    try:
        result = validate(args)
    except ReviewError as exc:
        print(f"Kiro peer-review validation failed: {exc}", file=sys.stderr)
        return 1
    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as output:
            output.writelines(f"{key}={value}\n" for key, value in result.items())
    print(json.dumps({**result, "approved": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
