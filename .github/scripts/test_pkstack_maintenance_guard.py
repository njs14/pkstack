#!/usr/bin/env python3
"""Deterministic regressions for the immutable PKStack maintenance boundary."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import itertools
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import Any, NamedTuple
from unittest import mock

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]


def require_match(match: re.Match[str] | None) -> re.Match[str]:
    """Fail the assertion when an expected workflow pattern is absent, and narrow it."""
    if match is None:
        raise AssertionError("expected regular expression match")
    return match


GUARD_PATH = ROOT / ".github" / "scripts" / "pkstack_maintenance_guard.py"
SPEC = importlib.util.spec_from_file_location("pkstack_maintenance_guard", GUARD_PATH)
assert SPEC is not None and SPEC.loader is not None
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
STREAM_GUARD_PATH = ROOT / ".github" / "scripts" / "validate_kiro_credential_stream.py"
STREAM_SPEC = importlib.util.spec_from_file_location(
    "validate_kiro_credential_stream", STREAM_GUARD_PATH
)
assert STREAM_SPEC is not None and STREAM_SPEC.loader is not None
stream_guard = importlib.util.module_from_spec(STREAM_SPEC)
STREAM_SPEC.loader.exec_module(stream_guard)
PERMISSION_STREAM_GUARD_PATH = ROOT / ".github" / "scripts" / "validate_kiro_permission_stream.py"
PERMISSION_STREAM_SPEC = importlib.util.spec_from_file_location(
    "validate_kiro_permission_stream", PERMISSION_STREAM_GUARD_PATH
)
assert PERMISSION_STREAM_SPEC is not None and PERMISSION_STREAM_SPEC.loader is not None
permission_stream_guard = importlib.util.module_from_spec(PERMISSION_STREAM_SPEC)
PERMISSION_STREAM_SPEC.loader.exec_module(permission_stream_guard)

VALID_PATCH = "@@ -0,0 +1 @@\n+new"
KIRO_ISOLATED_SETTINGS = (
    b"{\n"
    b'  "app.disableAutoupdates": true,\n'
    b'  "chat.disableInheritingDefaultResources": true,\n'
    b'  "telemetry.enabled": false\n'
    b"}\n"
)
KIRO_ISOLATED_SETTINGS_SHA256 = hashlib.sha256(KIRO_ISOLATED_SETTINGS).hexdigest()

MAINTENANCE_JOB_PROPERTIES = {
    "plan": ("runs-on", "permissions", "outputs", "steps"),
    "detect": ("needs", "if", "runs-on", "permissions", "outputs", "steps"),
    "maintain": (
        "needs",
        "if",
        "runs-on",
        "timeout-minutes",
        "permissions",
        "outputs",
        "env",
        "steps",
    ),
    "publish": ("needs", "if", "runs-on", "permissions", "steps"),
}
MAINTENANCE_JOB_CONTROL_FLOW = {
    "plan": {"needs": None, "if": None},
    "detect": {
        "needs": "plan",
        "if": "needs.plan.outputs.should_run == 'true'",
    },
    "maintain": {
        "needs": "[plan, detect]",
        "if": "needs.detect.outputs.needs_maintenance == 'true'",
    },
    "publish": {
        "needs": "[plan, detect, maintain]",
        "if": "needs.maintain.outputs.has_changes == 'true'",
    },
}
EXPECTED_SECRET_CONTEXT_EXPRESSIONS = (*("${{ secrets.KIRO_API_KEY }}",) * 2,)
CANDIDATE_SECRET_CONTEXT_EXPRESSIONS = (*("${{ secrets.KIRO_API_KEY }}",) * 2,)
CANDIDATE_REVIEW_ENV_BLOCKS = {
    "Independent Kiro-hosted Claude Opus 5 review": (
        "        env:\n"
        "          KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}\n"
        "          BASE_SHA: ${{ needs.resolve.outputs.base_sha }}\n"
        "          HEAD_SHA: ${{ needs.resolve.outputs.head_sha }}\n"
        "          CONTENT_SHA256: ${{ needs.candidate_prepare.outputs.review_content_sha256 }}\n"
        "          PATCH_SHA256: ${{ needs.candidate_prepare.outputs.review_patch_sha256 }}\n"
    ),
    "Validate exact no-tool approval and publish only bound hashes": (
        "        env:\n"
        "          KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}\n"
        "          BASE_SHA: ${{ needs.resolve.outputs.base_sha }}\n"
        "          HEAD_SHA: ${{ needs.resolve.outputs.head_sha }}\n"
        "          CONTENT_SHA256: ${{ needs.candidate_prepare.outputs.review_content_sha256 }}\n"
        "          PATCH_SHA256: ${{ needs.candidate_prepare.outputs.review_patch_sha256 }}\n"
        "          REVIEW_RETURN_CODE: ${{ steps.invoke.outputs.return_code }}\n"
        "          REVIEW_BUNDLE: ${{ runner.temp }}/pkstack-peer-review-workspace"
        "/.pkstack-ci/review-input.json\n"
        "          SELECTED_SOURCE_ID: ${{ needs.candidate_prepare.outputs.selected_source_id }}\n"
        "          SOURCE_SUBTREE_SHA: ${{ needs.candidate_prepare.outputs.source_subtree_sha }}\n"
        "          SOURCE_COMMIT: ${{ needs.candidate_prepare.outputs.source_commit }}\n"
        "          SOURCE_RUN_ID: ${{ github.event.workflow_run.id }}\n"
    ),
}
MAINTENANCE_MAINTAIN_STEPS = (
    ("Harden runner networking", ("uses", "with")),
    ("Bind ephemeral maintenance paths", ("run",)),
    ("Check out immutable source", ("uses", "with")),
    ("Download detector evidence", ("uses", "with")),
    ("Verify detector artifact identity", ("env", "run")),
    ("Install uv and materialize protected lockfiles", ("uses", "with")),
    ("Materialize locked environments and trusted scripts", ("run",)),
    ("Restore pinned Kiro CLI archive", ("uses", "with")),
    ("Verify checksum-pinned Kiro CLI 2.21.1 archive", ("run",)),
    ("Start immutable goal and record the required pre-edit failure", ("env", "run")),
    ("Prepare repair 1 without workspace hooks", ("run",)),
    ("Kiro repair 1 of 2", ("env", "run")),
    ("Secretless verification 1 of 2", ("id", "env", "run")),
    ("Prepare repair 2 without workspace hooks", ("if", "run")),
    ("Kiro repair 2 of 2", ("if", "env", "run")),
    ("Secretless verification 2 of 2", ("id", "if", "env", "run")),
    ("Require a terminal verified candidate", ("env", "run")),
    ("Package the immutable candidate", ("id", "env", "run")),
    ("Close the trusted Git finalizer boundary", ("if", "run")),
    ("Upload verified candidate package", ("id", "if", "uses", "with")),
)
MAINTENANCE_PUBLISH_STEPS = (
    ("Harden runner networking", ("uses", "with")),
    ("Check out trusted base only", ("uses", "with")),
    ("Download candidate package", ("uses", "with")),
    ("Reconstruct and validate candidate without executing it", ("env", "run")),
    (
        "Create one exact candidate commit and non-draft PR through the API",
        ("uses", "env", "with"),
    ),
)


class WorkflowContractError(ValueError):
    """The security-sensitive workflow no longer has its closed static shape."""


class _YamlLine(NamedTuple):
    number: int
    raw: str
    code: str
    indent: int
    block_scalar: bool


def _mask_yaml_comments_and_quotes(line: str) -> str:
    """Mask YAML comments and quoted scalars while preserving source columns."""

    masked = list(line)
    index = 0
    while index < len(line):
        character = line[index]
        if character == "#" and (index == 0 or line[index - 1].isspace()):
            masked[index:] = " " * (len(line) - index)
            break
        quote_can_start = index == 0 or line[index - 1].isspace() or line[index - 1] in "[{,:?-"
        if character not in {"'", '"'} or not quote_can_start:
            index += 1
            continue
        quote = character
        masked[index] = " "
        index += 1
        while index < len(line):
            masked[index] = " "
            if quote == "'" and line[index] == "'":
                if index + 1 < len(line) and line[index + 1] == "'":
                    masked[index + 1] = " "
                    index += 2
                    continue
                index += 1
                break
            if quote == '"' and line[index] == "\\":
                if index + 1 < len(line):
                    masked[index + 1] = " "
                    index += 2
                    continue
            elif quote == '"' and line[index] == '"':
                index += 1
                break
            index += 1
    return "".join(masked)


def _yaml_structural_lines(source: str) -> list[_YamlLine]:
    """Return YAML structure while excluding literal/folded scalar payloads."""

    result: list[_YamlLine] = []
    block_header_indent: int | None = None
    block_indicator = re.compile(r"(?:^|:\s+|-\s+)[|>](?:[1-9][+-]?|[+-][1-9]?|[+-])?\s*$")
    for number, raw in enumerate(source.splitlines(), start=1):
        leading = raw[: len(raw) - len(raw.lstrip(" \t"))]
        if "\t" in leading:
            raise WorkflowContractError(f"line {number}: tab indentation is forbidden")
        indent = len(leading)
        if block_header_indent is not None:
            if not raw.strip() or indent > block_header_indent:
                result.append(_YamlLine(number, raw, "", indent, True))
                continue
            block_header_indent = None
        code = _mask_yaml_comments_and_quotes(raw)
        result.append(_YamlLine(number, raw, code, indent, False))
        if code.strip() and block_indicator.search(code.rstrip()):
            block_header_indent = indent
    return result


def _yaml_node_can_start_at(text: str, index: int) -> bool:
    """Return whether ``index`` can begin a YAML node in the current line."""

    prefix = text[:index].rstrip()
    if not prefix or prefix in {"---", "..."}:
        return True
    if prefix[-1] in ":[{,":
        return True
    if prefix[-1] not in "-?":
        return False
    before_indicator = prefix[:-1].rstrip()
    return not before_indicator or before_indicator[-1] in ":[{,"


def _reject_yaml_indirection(lines: list[_YamlLine]) -> None:
    """Reject YAML features that can synthesize mappings outside static review."""

    merge_key = re.compile(r"(?:^|[\s\[{,?-])<<\s*:")

    for line in lines:
        if line.block_scalar or not line.code.strip():
            continue
        stripped = line.code.lstrip()
        if re.match(r"^[?:](?:\s|$)", stripped):
            raise WorkflowContractError(
                f"line {line.number}: explicit YAML mapping syntax is forbidden"
            )
        if merge_key.search(line.code):
            raise WorkflowContractError(f"line {line.number}: YAML merge keys are forbidden")
        for index, character in enumerate(line.code):
            inside_expression = line.code.rfind("${{", 0, index) > line.code.rfind("}}", 0, index)
            if (
                character not in {"&", "*", "!"}
                or inside_expression
                or not _yaml_node_can_start_at(line.code, index)
            ):
                continue
            following = line.code[index + 1] if index + 1 < len(line.code) else ""
            if character in {"&", "*"} and (
                not following or following.isspace() or following in "[]{},"
            ):
                continue
            construct = {"&": "anchor", "*": "alias", "!": "tag"}[character]
            raise WorkflowContractError(f"line {line.number}: YAML {construct} syntax is forbidden")


def _reject_yaml_scalar_decoding_escapes(lines: list[_YamlLine]) -> None:
    """Reject YAML quote escapes that can synthesize expression tokens."""

    yaml_quote: str | None = None
    github_expression = False
    github_quote = False
    for line in lines:
        if line.block_scalar and yaml_quote is None and not github_expression:
            continue
        index = 0
        while index < len(line.raw):
            character = line.raw[index]
            if yaml_quote == '"':
                if character == "\\":
                    raise WorkflowContractError(
                        f"line {line.number}: YAML double-quoted backslash escapes are forbidden"
                    )
                if character == '"':
                    yaml_quote = None
                index += 1
                continue
            if yaml_quote == "'":
                if character == "'":
                    if index + 1 < len(line.raw) and line.raw[index + 1] == "'":
                        raise WorkflowContractError(
                            f"line {line.number}: YAML doubled single-quote escapes are forbidden"
                        )
                    yaml_quote = None
                index += 1
                continue

            if github_expression:
                if github_quote:
                    if character == "'":
                        if index + 1 < len(line.raw) and line.raw[index + 1] == "'":
                            index += 2
                            continue
                        github_quote = False
                    index += 1
                    continue
                if character == "'":
                    github_quote = True
                    index += 1
                    continue
                if line.raw.startswith("}}", index):
                    github_expression = False
                    index += 2
                    continue
                index += 1
                continue

            if character == "#" and (index == 0 or line.raw[index - 1].isspace()):
                break
            if line.raw.startswith("${{", index):
                github_expression = True
                index += 3
                continue
            if character in {"'", '"'} and _yaml_node_can_start_at(line.raw, index):
                yaml_quote = character
            index += 1


def _mask_yaml_comment_only(line: str) -> str:
    """Mask a YAML comment without hiding executable scalar contents."""

    masked = list(line)
    quote: str | None = None
    index = 0
    while index < len(line):
        character = line[index]
        if quote == "'":
            if character == "'":
                if index + 1 < len(line) and line[index + 1] == "'":
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if quote == '"':
            if character == "\\":
                index += 2
                continue
            if character == '"':
                quote = None
            index += 1
            continue
        quote_can_start = index == 0 or line[index - 1].isspace() or line[index - 1] in "[{,:?-"
        if character in {"'", '"'} and quote_can_start:
            quote = character
            index += 1
            continue
        if character == "#" and (index == 0 or line[index - 1].isspace()):
            masked[index:] = " " * (len(line) - index)
            break
        index += 1
    return "".join(masked)


def _mask_expression_string_literals(expression: str) -> str:
    """Mask strings inside a GitHub expression before context-token checks."""

    masked = list(expression)
    quote: str | None = None
    index = 0
    while index < len(expression):
        character = expression[index]
        if quote is None:
            if character in {"'", '"'}:
                quote = character
                masked[index] = " "
            index += 1
            continue
        masked[index] = " "
        if quote == "'" and character == "'":
            if index + 1 < len(expression) and expression[index + 1] == "'":
                masked[index + 1] = " "
                index += 2
                continue
            quote = None
        elif quote == '"' and character == "\\":
            if index + 1 < len(expression):
                masked[index + 1] = " "
                index += 2
                continue
        elif quote == '"' and character == '"':
            quote = None
        index += 1
    return "".join(masked)


def _unwrap_yaml_scalar_quotes(value: str) -> str:
    """Remove one YAML scalar quote layer before implicit-expression checks."""

    if len(value) < 2 or value[0] != value[-1] or value[0] not in {"'", '"'}:
        return value
    inner = value[1:-1]
    if value[0] == "'":
        return inner.replace("''", "'")
    return inner


def _github_expressions(text: str) -> tuple[str, ...]:
    """Extract GitHub expressions while respecting strings in their bodies."""

    expressions: list[str] = []
    cursor = 0
    while True:
        start = text.find("${{", cursor)
        if start < 0:
            return tuple(expressions)
        index = start + 3
        quote: str | None = None
        while index < len(text):
            character = text[index]
            if quote is None:
                if character in {"'", '"'}:
                    quote = character
                    index += 1
                    continue
                if text.startswith("}}", index):
                    end = index + 2
                    expressions.append(text[start:end])
                    cursor = end
                    break
                index += 1
                continue
            if quote == "'" and character == "'":
                if index + 1 < len(text) and text[index + 1] == "'":
                    index += 2
                    continue
                quote = None
            elif quote == '"' and character == "\\":
                index += 2
                continue
            elif quote == '"' and character == '"':
                quote = None
            index += 1
        else:
            return tuple(expressions)


def _secret_context_expressions(lines: list[_YamlLine]) -> tuple[str, ...]:
    """Return active GitHub expressions that access the secrets context."""

    executable_text = "\n".join(
        line.raw if line.block_scalar else _mask_yaml_comment_only(line.raw) for line in lines
    )
    return tuple(
        expression
        for expression in _github_expressions(executable_text)
        if re.search(
            r"\bsecrets\b",
            _mask_expression_string_literals(expression[3:-2]),
            flags=re.IGNORECASE,
        )
    )


def _secret_context_line_numbers(lines: list[_YamlLine]) -> set[int]:
    """Return source lines containing an active GitHub ``secrets`` expression."""

    result: set[int] = set()
    for line in lines:
        executable_text = line.raw if line.block_scalar else _mask_yaml_comment_only(line.raw)
        if any(
            re.search(
                r"\bsecrets\b",
                _mask_expression_string_literals(expression[3:-2]),
                flags=re.IGNORECASE,
            )
            for expression in _github_expressions(executable_text)
        ):
            result.add(line.number)
    return result


def _reject_implicit_if_secret_context(lines: list[_YamlLine]) -> None:
    """Reject the secrets context in GitHub's implicit-expression ``if`` form."""

    block_body: list[str] | None = None
    for line in lines:
        if block_body is not None:
            if line.block_scalar:
                block_body.append(line.raw)
                continue
            body = "\n".join(block_body)
            if re.search(
                r"\bsecrets\b",
                _mask_expression_string_literals(body),
                flags=re.IGNORECASE,
            ):
                raise WorkflowContractError(
                    "secrets context is forbidden in implicit if expressions"
                )
            block_body = None

        if line.block_scalar or not line.code.strip():
            continue
        active = _mask_yaml_comment_only(line.raw)
        match = re.match(r"^\s*(?:-\s+)?if:\s*(?P<body>.*?)\s*$", active)
        if match is None:
            continue
        body = match.group("body")
        if re.fullmatch(r"[|>](?:[1-9][+-]?|[+-][1-9]?|[+-])?", body):
            block_body = []
            continue
        body = _unwrap_yaml_scalar_quotes(body)
        if re.search(
            r"\bsecrets\b",
            _mask_expression_string_literals(body),
            flags=re.IGNORECASE,
        ):
            raise WorkflowContractError(
                f"line {line.number}: secrets context is forbidden in implicit if expressions"
            )

    if block_body is not None:
        body = "\n".join(block_body)
        if re.search(
            r"\bsecrets\b",
            _mask_expression_string_literals(body),
            flags=re.IGNORECASE,
        ):
            raise WorkflowContractError("secrets context is forbidden in implicit if expressions")


def _bare_mapping_keys(
    lines: list[_YamlLine],
    *,
    start: int,
    end: int,
    indent: int,
    context: str,
) -> tuple[str, ...]:
    keys: list[str] = []
    pattern = re.compile(rf"^ {{{indent}}}([A-Za-z_][A-Za-z0-9_-]*):(?:\s.*)?$")
    for line in lines[start:end]:
        if line.block_scalar or not line.code.strip() or line.indent != indent:
            continue
        match = pattern.fullmatch(line.code.rstrip())
        if match is None:
            raise WorkflowContractError(
                f"line {line.number}: {context} requires a bare mapping key"
            )
        keys.append(match.group(1))
    return tuple(keys)


def _require_job_control_flow(
    lines: list[_YamlLine],
    *,
    job: str,
    start: int,
    end: int,
) -> None:
    """Pin a job's dependency edge and gate as exact scalar values."""

    for property_name, expected in MAINTENANCE_JOB_CONTROL_FLOW[job].items():
        pattern = re.compile(rf"^    {re.escape(property_name)}:(?: (?P<value>.*))?$")
        matches = [
            match
            for line in lines[start:end]
            if not line.block_scalar and line.indent == 4
            if (match := pattern.fullmatch(_mask_yaml_comment_only(line.raw).rstrip())) is not None
        ]
        if expected is None:
            if matches:
                raise WorkflowContractError(
                    f"{job} must not define a {property_name} control-flow value"
                )
            continue
        if len(matches) != 1 or matches[0].group("value") != expected:
            raise WorkflowContractError(
                f"{job} {property_name} control-flow value must be exactly {expected!r}"
            )


def _workflow_job_ranges(lines: list[_YamlLine]) -> dict[str, tuple[int, int]]:
    """Return all bare workflow job ranges without imposing a job allowlist."""

    jobs_headers = [
        index
        for index, line in enumerate(lines)
        if not line.block_scalar and line.indent == 0 and line.code.rstrip() == "jobs:"
    ]
    if len(jobs_headers) != 1:
        raise WorkflowContractError("workflow must contain one bare jobs mapping")
    jobs_start = jobs_headers[0] + 1
    jobs_end = len(lines)
    for index in range(jobs_start, len(lines)):
        line = lines[index]
        if not line.block_scalar and line.code.strip() and line.indent == 0:
            jobs_end = index
            break

    header_pattern = re.compile(r"^  ([A-Za-z_][A-Za-z0-9_-]*):$")
    headers: list[tuple[str, int]] = []
    for index in range(jobs_start, jobs_end):
        line = lines[index]
        if line.block_scalar or not line.code.strip() or line.indent != 2:
            continue
        match = header_pattern.fullmatch(line.code.rstrip())
        if match is None:
            raise WorkflowContractError(
                f"line {line.number}: jobs require bare, empty mapping headers"
            )
        headers.append((match.group(1), index))
    if not headers:
        raise WorkflowContractError("workflow must contain at least one job")
    names = [name for name, _ in headers]
    if len(names) != len(set(names)):
        raise WorkflowContractError("workflow job names must be unique")
    ranges: dict[str, tuple[int, int]] = {}
    for position, (name, index) in enumerate(headers):
        end = headers[position + 1][1] if position + 1 < len(headers) else jobs_end
        ranges[name] = (index + 1, end)
    return ranges


def _maintenance_job_ranges(lines: list[_YamlLine]) -> dict[str, tuple[int, int]]:
    ranges = _workflow_job_ranges(lines)
    expected = tuple(MAINTENANCE_JOB_PROPERTIES)
    if tuple(ranges) != expected:
        raise WorkflowContractError(f"workflow jobs must be exactly {expected!r} in order")
    return ranges


def _named_step_ranges(
    lines: list[_YamlLine],
    *,
    job: str,
    start: int,
    end: int,
) -> list[tuple[str, int, int]]:
    steps_headers = [
        index
        for index in range(start, end)
        if not lines[index].block_scalar
        and lines[index].indent == 4
        and lines[index].code.rstrip() == "    steps:"
    ]
    if len(steps_headers) != 1:
        raise WorkflowContractError(f"{job} must contain one bare steps mapping")
    first = steps_headers[0] + 1
    header_pattern = re.compile(r"^      - name: (\S(?:.*\S)?)$")
    headers: list[tuple[str, int]] = []
    for index in range(first, end):
        line = lines[index]
        if line.block_scalar or not line.code.strip() or line.indent != 6:
            continue
        match = header_pattern.fullmatch(line.code.rstrip())
        if match is None:
            raise WorkflowContractError(
                f"line {line.number}: {job} steps require bare '- name:' headers"
            )
        headers.append((match.group(1), index))
    ranges: list[tuple[str, int, int]] = []
    for position, (name, index) in enumerate(headers):
        step_end = headers[position + 1][1] if position + 1 < len(headers) else end
        ranges.append((name, index, step_end))
    return ranges


def _raw_source_range(source_lines: list[str], start: int, end: int) -> str:
    return "".join(source_lines[start:end])


def _protected_env_block(
    source_lines: list[str],
    lines: list[_YamlLine],
    *,
    step_name: str,
    start: int,
    end: int,
) -> str:
    env_headers = [
        index
        for index in range(start + 1, end)
        if not lines[index].block_scalar
        and lines[index].indent == 8
        and lines[index].code.rstrip() == "        env:"
    ]
    if len(env_headers) != 1:
        raise WorkflowContractError(f"{step_name} must contain one bare env mapping")
    env_start = env_headers[0]
    env_end = end
    for index in range(env_start + 1, end):
        line = lines[index]
        if not line.block_scalar and line.code.strip() and line.indent == 8:
            env_end = index
            break
    _bare_mapping_keys(
        lines,
        start=env_start + 1,
        end=env_end,
        indent=10,
        context=f"{step_name} environment",
    )
    return _raw_source_range(source_lines, env_start, env_end)


def validate_maintenance_workflow_security_contract(source: str) -> None:
    """Enforce the closed static workflow shape that guards repair credentials."""

    source_lines = source.splitlines(keepends=True)
    lines = _yaml_structural_lines(source)
    _reject_yaml_indirection(lines)
    _reject_yaml_scalar_decoding_escapes(lines)
    _reject_implicit_if_secret_context(lines)
    secret_expressions = _secret_context_expressions(lines)
    if secret_expressions != EXPECTED_SECRET_CONTEXT_EXPRESSIONS:
        raise WorkflowContractError(
            "secret context expressions must be exactly the two approved Kiro bindings"
        )
    job_ranges = _maintenance_job_ranges(lines)
    step_ranges_by_job: dict[str, list[tuple[str, int, int]]] = {}
    for job, (start, end) in job_ranges.items():
        properties = _bare_mapping_keys(
            lines,
            start=start,
            end=end,
            indent=4,
            context=f"{job} job",
        )
        expected_properties = MAINTENANCE_JOB_PROPERTIES[job]
        if properties != expected_properties:
            raise WorkflowContractError(f"{job} properties must be exactly {expected_properties!r}")
        _require_job_control_flow(
            lines,
            job=job,
            start=start,
            end=end,
        )
        step_ranges_by_job[job] = _named_step_ranges(
            lines,
            job=job,
            start=start,
            end=end,
        )

    expected_steps = {
        "maintain": MAINTENANCE_MAINTAIN_STEPS,
        "publish": MAINTENANCE_PUBLISH_STEPS,
    }
    for job, expected in expected_steps.items():
        actual: list[tuple[str, tuple[str, ...]]] = []
        for name, start, end in step_ranges_by_job[job]:
            properties = _bare_mapping_keys(
                lines,
                start=start + 1,
                end=end,
                indent=8,
                context=f"{job} step {name!r}",
            )
            actual.append((name, properties))
        if tuple(actual) != expected:
            raise WorkflowContractError(
                f"{job} step names and properties must be exactly enumerated"
            )

    repair_steps = {
        name: (start, end)
        for name, start, end in step_ranges_by_job["maintain"]
        if re.fullmatch(r"Kiro repair [1-2] of 2", name)
    }
    expected_repair_names = tuple(f"Kiro repair {attempt} of 2" for attempt in range(1, 3))
    if tuple(repair_steps) != expected_repair_names:
        raise WorkflowContractError("exactly two ordered Kiro repair steps are required")
    secret_line_numbers: set[int] = set()
    for attempt, name in enumerate(expected_repair_names, start=1):
        start, end = repair_steps[name]
        actual_env = _protected_env_block(
            source_lines,
            lines,
            step_name=name,
            start=start,
            end=end,
        )
        expected_env = (
            "        env:\n"
            f'          ATTEMPT_NUMBER: "{attempt}"\n'
            "          KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}\n"
        )
        if actual_env != expected_env:
            raise WorkflowContractError(f"{name} env mapping changed")
        secret_line_numbers.update(
            lines[index].number
            for index in range(start, end)
            if re.search(r"KIRO_API_KEY", lines[index].raw, flags=re.IGNORECASE)
        )

    all_secret_lines = {
        line.number for line in lines if re.search(r"KIRO_API_KEY", line.raw, flags=re.IGNORECASE)
    }
    if all_secret_lines != secret_line_numbers or len(all_secret_lines) != 2:
        raise WorkflowContractError(
            "only the two enumerated Kiro repair env mappings may hold KIRO_API_KEY"
        )


def validate_candidate_workflow_secret_contract(source: str) -> None:
    """Enforce the candidate workflow's closed Kiro review secret boundary.

    Candidate tests execute the untrusted candidate checkout and must remain
    secretless.  The only permitted secret expressions are the two explicit
    ``KIRO_API_KEY`` bindings on the trusted Kiro review steps.  The same
    source-level YAML indirection and scalar-decoding guards used for the
    maintenance workflow run before this scope check.
    """

    source_lines = source.splitlines(keepends=True)
    lines = _yaml_structural_lines(source)
    _reject_yaml_indirection(lines)
    _reject_yaml_scalar_decoding_escapes(lines)
    _reject_implicit_if_secret_context(lines)

    secret_expressions = _secret_context_expressions(lines)
    if secret_expressions != CANDIDATE_SECRET_CONTEXT_EXPRESSIONS:
        raise WorkflowContractError(
            "candidate secret context expressions must be exactly the two scoped Kiro bindings"
        )

    job_ranges = _workflow_job_ranges(lines)
    for job in ("candidate_prepare", "candidate_tests", "kiro_peer_review"):
        if job not in job_ranges:
            raise WorkflowContractError(f"candidate workflow must contain {job!r} job")

    candidate_start, candidate_end = job_ranges["candidate_tests"]
    candidate_secret_lines = _secret_context_line_numbers(lines[candidate_start:candidate_end])
    if candidate_secret_lines:
        raise WorkflowContractError("candidate_tests must not expose the secrets context")

    review_start, review_end = job_ranges["kiro_peer_review"]
    review_steps = _named_step_ranges(
        lines,
        job="kiro_peer_review",
        start=review_start,
        end=review_end,
    )
    for step_name in CANDIDATE_REVIEW_ENV_BLOCKS:
        matches = [(start, end) for name, start, end in review_steps if name == step_name]
        if len(matches) != 1:
            raise WorkflowContractError(
                f"candidate review must contain exactly one {step_name!r} step"
            )
        start, end = matches[0]
        actual_env = _protected_env_block(
            source_lines,
            lines,
            step_name=step_name,
            start=start,
            end=end,
        )
        if actual_env != CANDIDATE_REVIEW_ENV_BLOCKS[step_name]:
            raise WorkflowContractError(f"{step_name} Kiro environment mapping changed")

    allowed_secret_lines = {
        lines[index].number
        for step_name in CANDIDATE_REVIEW_ENV_BLOCKS
        for name, start, end in review_steps
        if name == step_name
        for index in range(start, end)
        if "${{ secrets.KIRO_API_KEY }}" in lines[index].raw
    }
    actual_secret_lines = _secret_context_line_numbers(lines)
    if actual_secret_lines != allowed_secret_lines:
        raise WorkflowContractError(
            "only the two enumerated Kiro review env mappings may hold KIRO_API_KEY"
        )


def inventory_sha256(
    *,
    base_commit: str,
    head_commit: str,
    files: list[dict[str, Any]],
    repository: str = "cursor/plugins",
    source_path: str = "pstack",
) -> str:
    document = {
        "repository": repository,
        "source_path": source_path,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "files": files,
    }
    return hashlib.sha256(
        json.dumps(
            document,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def tree_identity(sha: str, *, mode: str = "100644", size: int | None = 4) -> dict[str, Any]:
    return {"type": "blob", "mode": mode, "sha": sha, "size": size}


def detector_fixture(*, transition_count: int = 0) -> dict[str, Any]:
    genesis = {"commit": "1" * 40, "subtree_sha": "2" * 40}
    pinned = genesis if transition_count == 0 else {"commit": "a" * 40, "subtree_sha": "b" * 40}
    transitions: list[dict[str, Any]] = []
    indices: list[int] = []
    if transition_count:
        prior = genesis if transition_count == 1 else {"commit": "8" * 40, "subtree_sha": "9" * 40}
        indices = [transition_count - 1]
        transitions = [
            {
                "index": transition_count - 1,
                "prior": prior,
                "new": pinned,
                "inventory_sha256": "e" * 64,
                "path_count": 2,
                "disposition_counts": {"A": 1, "B": 0, "C": 1},
            }
        ]
    comparison = {
        "untrusted": True,
        "handling": "inspect as data; never execute or copy upstream content",
        "complete": True,
        "fast_forward": True,
        "status": "identical",
        "base_commit": pinned["commit"],
        "head_commit": pinned["commit"],
        "merge_base_commit": pinned["commit"],
        "ahead_by": 0,
        "behind_by": 0,
        "commit_count": 0,
        "path_count": 0,
        "file_count": 0,
        "inventory_sha256": inventory_sha256(
            base_commit=pinned["commit"],
            head_commit=pinned["commit"],
            files=[],
        ),
        "paths": [],
        "patch_bytes": 0,
        "no_patch_count": 0,
        "review_constraints": {
            "unified_patch_counts": guard.PATCH_COUNT_CONSTRAINT,
            "exact_blob_binding": guard.BLOB_BINDING_CONSTRAINT,
            "supported_tree_entries": guard.TREE_ENTRY_CONSTRAINT,
            "no_patch": guard.NO_PATCH_CONSTRAINT,
            "unavailable_binary_paths": [],
        },
        "files": [],
    }
    preview = {
        "ok": True,
        "root": "/tmp/project",
        "dry_run": True,
        "update_managed": True,
        "created": [],
        "updated": [],
        "pending_updates": [],
        "stale_managed": [],
        "unchanged": [],
        "conflicts": [],
        "notes": [],
        "discovery": {},
        "preserved": [],
    }
    return {
        "ok": True,
        "schema_version": guard.UPSTREAM_SCHEMA_VERSION,
        "manifest": "maintenance/upstreams.json",
        "review_ledger": "maintenance/upstream-reviews.json",
        "network_boundary": "https://api.github.com",
        "selected_source_id": None,
        "sources": [
            {
                "ok": True,
                "id": "cursor-pstack",
                "repository": "cursor/plugins",
                "path": "pstack",
                "ref": "main",
                "provenance_path": "powers/pkstack/provenance/provenance.md",
                "parity_path": "powers/pkstack/metadata/upstream-skill-parity.json",
                "pinned": pinned,
                "pinned_reproof": {"ok": True, **pinned},
                "current": pinned,
                "drift": False,
                "comparison": comparison,
                "review_reproof": {
                    "ok": True,
                    "source_id": "cursor-pstack",
                    "genesis": genesis,
                    "tip": pinned,
                    "transition_count": transition_count,
                    "remote_transition_indices": indices,
                    "history_validation": (
                        "all entries form a strict local contiguous chain; repository "
                        "history is the tamper-evident authority for older reviewed "
                        "transitions"
                    ),
                    "transitions": transitions,
                },
                "source_parity": {
                    "ok": True,
                    "candidate_ready": False,
                    "artifact_type": "skill-catalog",
                    "status": "accepted-baseline",
                    "path": "powers/pkstack/metadata/upstream-skill-parity.json",
                    "errors": [],
                    "pinned_resource_count": 1,
                    "current_resource_count": 1,
                    "classified_resource_count": 1,
                },
            }
        ],
        "bootstrap_preview": preview,
        "generated_parity": {
            "ok": True,
            "dry_run": True,
            "update_managed": True,
            "differences": {},
        },
    }


def drift_detector_fixture(*, transition_count: int = 0) -> dict[str, Any]:
    payload = detector_fixture(transition_count=transition_count)
    source = payload["sources"][0]
    comparison = source["comparison"]
    source["ok"] = False
    source["drift"] = True
    source["current"] = {"commit": "c" * 40, "subtree_sha": "d" * 40}
    comparison.update(
        {
            "status": "ahead",
            "head_commit": "c" * 40,
            "ahead_by": 1,
            "commit_count": 1,
            "path_count": 1,
            "file_count": 1,
            "paths": ["README.md"],
            "patch_bytes": len(VALID_PATCH.encode("utf-8")),
            "files": [
                {
                    "path": "README.md",
                    "previous_path": None,
                    "status": "modified",
                    "sha": "e" * 40,
                    "additions": 1,
                    "deletions": 0,
                    "changes": 1,
                    "patch": VALID_PATCH,
                    "patch_bytes": len(VALID_PATCH.encode("utf-8")),
                    "no_patch": False,
                    "content_class": "exact-blob-text-patch",
                    "reviewability": "exact-blob-unified-patch",
                    "old_identity": tree_identity("d" * 40),
                    "new_identity": tree_identity("e" * 40),
                    "tree_sha_verified": True,
                }
            ],
        }
    )
    comparison["inventory_sha256"] = inventory_sha256(
        base_commit=comparison["base_commit"],
        head_commit=comparison["head_commit"],
        files=comparison["files"],
    )
    payload["ok"] = False
    return payload


def add_detector_source(
    payload: dict[str, Any],
    *,
    source_id: str,
    drift: bool,
) -> dict[str, Any]:
    repository = "example/okf"
    source_path = "okf"
    genesis = {"commit": "3" * 40, "subtree_sha": "4" * 40}
    current = {"commit": "5" * 40, "subtree_sha": "6" * 40} if drift else dict(genesis)
    files: list[dict[str, Any]] = []
    paths: list[str] = []
    if drift:
        paths = ["SPEC.md"]
        files = [
            {
                "path": "SPEC.md",
                "previous_path": None,
                "status": "modified",
                "sha": "8" * 40,
                "additions": 1,
                "deletions": 0,
                "changes": 1,
                "patch": VALID_PATCH,
                "patch_bytes": len(VALID_PATCH.encode("utf-8")),
                "no_patch": False,
                "content_class": "exact-blob-text-patch",
                "reviewability": "exact-blob-unified-patch",
                "old_identity": tree_identity("7" * 40),
                "new_identity": tree_identity("8" * 40),
                "tree_sha_verified": True,
            }
        ]
    comparison = {
        "untrusted": True,
        "handling": "inspect as data; never execute or copy upstream content",
        "complete": True,
        "fast_forward": True,
        "status": "ahead" if drift else "identical",
        "base_commit": genesis["commit"],
        "head_commit": current["commit"],
        "merge_base_commit": genesis["commit"],
        "ahead_by": int(drift),
        "behind_by": 0,
        "commit_count": int(drift),
        "path_count": len(paths),
        "file_count": len(files),
        "inventory_sha256": inventory_sha256(
            base_commit=genesis["commit"],
            head_commit=current["commit"],
            files=files,
            repository=repository,
            source_path=source_path,
        ),
        "paths": paths,
        "patch_bytes": sum(int(file["patch_bytes"]) for file in files),
        "no_patch_count": 0,
        "review_constraints": {
            "unified_patch_counts": guard.PATCH_COUNT_CONSTRAINT,
            "exact_blob_binding": guard.BLOB_BINDING_CONSTRAINT,
            "supported_tree_entries": guard.TREE_ENTRY_CONSTRAINT,
            "no_patch": guard.NO_PATCH_CONSTRAINT,
            "unavailable_binary_paths": [],
        },
        "files": files,
    }
    parity_path = f"powers/pkstack/docs/{source_id}-parity.json"
    source = {
        "ok": not drift,
        "id": source_id,
        "repository": repository,
        "path": source_path,
        "ref": "main",
        "provenance_path": f"powers/pkstack/docs/{source_id}-provenance.md",
        "parity_path": parity_path,
        "pinned": genesis,
        "pinned_reproof": {"ok": True, **genesis},
        "current": current,
        "drift": drift,
        "comparison": comparison,
        "review_reproof": {
            "ok": True,
            "source_id": source_id,
            "genesis": genesis,
            "tip": genesis,
            "transition_count": 0,
            "remote_transition_indices": [],
            "history_validation": (
                "all entries form a strict local contiguous chain; repository history is the "
                "tamper-evident authority for older reviewed transitions"
            ),
            "transitions": [],
        },
        "source_parity": {
            "ok": True,
            "candidate_ready": False,
            "artifact_type": "source-inventory",
            "status": "accepted-baseline",
            "path": parity_path,
            "errors": [],
            "pinned_resource_count": 1,
            "current_resource_count": 1,
            "classified_resource_count": 1,
        },
    }
    payload["sources"].append(source)
    payload["ok"] = all(item["ok"] for item in payload["sources"])
    return source


def accepted_detector_fixture(
    payload: dict[str, Any],
    *,
    selected_source_id: str,
) -> dict[str, Any]:
    accepted = json.loads(json.dumps(payload))
    source = next(item for item in accepted["sources"] if item["id"] == selected_source_id)
    prior = source["pinned"]
    new = source["current"]
    comparison = source["comparison"]
    inventory_digest = comparison["inventory_sha256"]
    path_count = comparison["path_count"]
    before_count = source["review_reproof"]["transition_count"]
    source["pinned"] = new
    source["pinned_reproof"] = {"ok": True, **new}
    source["ok"] = True
    source["drift"] = False
    source["comparison"] = {
        "untrusted": True,
        "handling": "inspect as data; never execute or copy upstream content",
        "complete": True,
        "fast_forward": True,
        "status": "identical",
        "base_commit": new["commit"],
        "head_commit": new["commit"],
        "merge_base_commit": new["commit"],
        "ahead_by": 0,
        "behind_by": 0,
        "commit_count": 0,
        "path_count": 0,
        "file_count": 0,
        "inventory_sha256": inventory_sha256(
            base_commit=new["commit"],
            head_commit=new["commit"],
            files=[],
            repository=source["repository"],
            source_path=source["path"],
        ),
        "paths": [],
        "patch_bytes": 0,
        "no_patch_count": 0,
        "review_constraints": {
            "unified_patch_counts": guard.PATCH_COUNT_CONSTRAINT,
            "exact_blob_binding": guard.BLOB_BINDING_CONSTRAINT,
            "supported_tree_entries": guard.TREE_ENTRY_CONSTRAINT,
            "no_patch": guard.NO_PATCH_CONSTRAINT,
            "unavailable_binary_paths": [],
        },
        "files": [],
    }
    source["review_reproof"].update(
        {
            "tip": new,
            "transition_count": before_count + 1,
            "remote_transition_indices": [before_count],
            "transitions": [
                {
                    "index": before_count,
                    "prior": prior,
                    "new": new,
                    "inventory_sha256": inventory_digest,
                    "path_count": path_count,
                    "disposition_counts": {"A": path_count, "B": 0, "C": 0},
                }
            ],
        }
    )
    source["source_parity"].update(
        {
            "ok": True,
            "candidate_ready": False,
            "status": "accepted-baseline",
            "errors": [],
        }
    )
    accepted["ok"] = all(item["ok"] for item in accepted["sources"])
    return accepted


def comparison_file_fixture(
    *,
    path: str | None,
    previous_path: str | None,
    status: str,
    tree_sha_verified: bool,
) -> dict[str, Any]:
    old_identity = (
        tree_identity("d" * 40)
        if status in {"removed", "modified", "changed"} or (status == "renamed" and previous_path)
        else None
    )
    new_identity = (
        tree_identity("e" * 40)
        if status in {"added", "copied", "modified", "changed"} or (status == "renamed" and path)
        else None
    )
    return {
        "path": path,
        "previous_path": previous_path,
        "status": status,
        "sha": "e" * 40,
        "additions": 1,
        "deletions": 0,
        "changes": 1,
        "patch": VALID_PATCH,
        "patch_bytes": len(VALID_PATCH.encode("utf-8")),
        "no_patch": False,
        "content_class": "exact-blob-text-patch",
        "reviewability": "exact-blob-unified-patch",
        "old_identity": old_identity,
        "new_identity": new_identity,
        "tree_sha_verified": tree_sha_verified,
    }


def set_comparison_files(payload: dict[str, Any], files: list[dict[str, Any]]) -> None:
    comparison = payload["sources"][0]["comparison"]
    paths = sorted(
        {
            identity
            for file in files
            for identity in (
                file["path"],
                file["previous_path"] if file["status"] == "renamed" else None,
            )
            if isinstance(identity, str)
        }
    )
    comparison.update(
        {
            "path_count": len(paths),
            "file_count": len(files),
            "paths": paths,
            "patch_bytes": sum(int(file["patch_bytes"]) for file in files),
            "no_patch_count": sum(bool(file["no_patch"]) for file in files),
            "review_constraints": {
                "unified_patch_counts": guard.PATCH_COUNT_CONSTRAINT,
                "exact_blob_binding": guard.BLOB_BINDING_CONSTRAINT,
                "supported_tree_entries": guard.TREE_ENTRY_CONSTRAINT,
                "no_patch": guard.NO_PATCH_CONSTRAINT,
                "unavailable_binary_paths": sorted(
                    {
                        identity
                        for file in files
                        if file["reviewability"] == "unavailable-nonsemantic-image"
                        for identity in (file["path"], file["previous_path"])
                        if isinstance(identity, str)
                    }
                ),
            },
            "files": files,
        }
    )
    comparison["inventory_sha256"] = inventory_sha256(
        base_commit=comparison["base_commit"],
        head_commit=comparison["head_commit"],
        files=comparison["files"],
    )


def proposal_fixture(
    payload: dict[str, Any],
    *,
    source_id: str | None = None,
) -> dict[str, Any]:
    drift_sources = sorted(
        (source for source in payload["sources"] if source["drift"]),
        key=lambda item: item["id"],
    )
    if source_id is None:
        source = drift_sources[0]
    else:
        source = next(item for item in payload["sources"] if item["id"] == source_id)
    comparison = source["comparison"]
    unavailable = comparison["review_constraints"]["unavailable_binary_paths"]
    return {
        "source_id": source["id"],
        "prior": source["pinned"],
        "new": source["current"],
        "inventory_sha256": comparison["inventory_sha256"],
        "dispositions": [
            {
                "path": path,
                "disposition": "B" if path in unavailable else "A",
                "rationale": "Reviewed against the exact detector inventory.",
            }
            for path in comparison["paths"]
        ],
    }


def review_ledger_fixture(payload: dict[str, Any]) -> dict[str, Any]:
    sources = []
    for source in payload["sources"]:
        reproof = source["review_reproof"]
        transition_count = reproof["transition_count"]
        if transition_count not in {0, 1}:
            raise AssertionError("test ledger helper supports zero or one accepted transition")
        transitions = []
        if transition_count == 1:
            summary = reproof["transitions"][0]
            counts = summary["disposition_counts"]
            dispositions = []
            for disposition in ("A", "B", "C"):
                dispositions.extend(
                    {
                        "path": f"accepted-{disposition.lower()}-{index:03d}.md",
                        "disposition": disposition,
                        "rationale": "Accepted in the prior exact review.",
                    }
                    for index in range(counts[disposition])
                )
            dispositions.sort(key=lambda item: item["path"])
            transitions = [
                {
                    "prior": summary["prior"],
                    "new": summary["new"],
                    "inventory_sha256": summary["inventory_sha256"],
                    "dispositions": dispositions,
                }
            ]
        sources.append(
            {
                "id": source["id"],
                "repository": source["repository"],
                "path": source["path"],
                "provenance_path": source["provenance_path"],
                "parity_path": source["parity_path"],
                "genesis": reproof["genesis"],
                "transitions": transitions,
            }
        )
    return {
        "schema_version": guard.UPSTREAM_SCHEMA_VERSION,
        "sources": sources,
    }


def review_marker_line(marker: dict[str, Any]) -> str:
    canonical = json.dumps(marker, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"<!-- pk-stack-upstream-review: {canonical} -->"


def pending_marker_line(payload: dict[str, Any], *, source_id: str | None = None) -> str:
    if source_id is None:
        source = min(
            (item for item in payload["sources"] if item["drift"]),
            key=lambda item: item["id"],
        )
    else:
        source = next(item for item in payload["sources"] if item["id"] == source_id)
    return review_marker_line(
        {
            "source_id": source["id"],
            "repository": source["repository"],
            "path": source["path"],
            "prior": source["pinned"],
            "new": source["current"],
            "inventory_sha256": source["comparison"]["inventory_sha256"],
        }
    )


def accepted_marker_lines(
    payload: dict[str, Any],
    *,
    source_id: str = "cursor-pstack",
) -> list[str]:
    ledger_source = next(
        source for source in review_ledger_fixture(payload)["sources"] if source["id"] == source_id
    )
    return [
        review_marker_line(
            {
                "source_id": ledger_source["id"],
                "repository": ledger_source["repository"],
                "path": ledger_source["path"],
                "prior": transition["prior"],
                "new": transition["new"],
                "inventory_sha256": transition["inventory_sha256"],
            }
        )
        for transition in ledger_source["transitions"]
    ]


class StrictJsonTests(unittest.TestCase):
    def test_duplicate_keys_and_non_finite_numbers_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.json"
            for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
                path.write_bytes(raw)
                with self.assertRaises(guard.GuardError):
                    guard._load_json(path, maximum=1024, label="test input")

    def test_fable_verdict_is_bound_to_exact_candidate_and_content(self) -> None:
        _, policy = guard.load_policy(ROOT / ".github/pkstack-maintenance-policy.json")
        base_sha = "1" * 40
        head_sha = "2" * 40
        content_sha256 = "3" * 64
        patch_sha256 = "4" * 64
        verdict = {
            "verdict": "approved",
            "reviewed_base_sha": base_sha,
            "reviewed_head_sha": head_sha,
            "reviewed_content_sha256": content_sha256,
            "reviewed_patch_sha256": patch_sha256,
            "material_findings": [],
            "summary": "No material unresolved findings in the exact candidate.",
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "verdict.json"
            execution_path = Path(temporary) / "execution.json"

            def execution(
                structured: dict[str, Any],
                *,
                init_model: str = "claude-fable-5-1",
                usage_models: tuple[str, ...] = ("claude-fable-5-1",),
                duplicate_init: bool = False,
            ) -> list[dict[str, Any]]:
                messages: list[dict[str, Any]] = [
                    {"type": "system", "subtype": "init", "model": init_model}
                ]
                if duplicate_init:
                    messages.append({"type": "system", "subtype": "init", "model": init_model})
                messages.append(
                    {
                        "type": "result",
                        "subtype": "success",
                        "is_error": False,
                        "modelUsage": {model: {} for model in usage_models},
                        "structured_output": structured,
                    }
                )
                return messages

            path.write_text(json.dumps(verdict), encoding="utf-8")
            execution_path.write_text(json.dumps(execution(verdict)), encoding="utf-8")
            result = guard.validate_fable_verdict(
                path,
                execution_path,
                policy,
                base_sha=base_sha,
                head_sha=head_sha,
                content_sha256=content_sha256,
                patch_sha256=patch_sha256,
            )
            self.assertTrue(result["approved"])
            real_companion_usage = {
                "inputTokens": 917,
                "outputTokens": 16,
                "cacheReadInputTokens": 0,
                "cacheCreationInputTokens": 0,
                "webSearchRequests": 0,
                "costUSD": 0.000997,
                "contextWindow": 200000,
                "maxOutputTokens": 32000,
                "thinkingTokens": 0,
                "canonicalModel": "claude-haiku-4-5",
                "provider": "firstParty",
                "costBasis": "list",
            }
            companion_execution = execution(verdict)
            companion_execution[-1]["modelUsage"] = {
                "claude-fable-5-1": {
                    "canonicalModel": "claude-fable-5-1",
                    "provider": "firstParty",
                },
                "claude-haiku-4-5-20251001": real_companion_usage,
            }
            execution_path.write_text(json.dumps(companion_execution), encoding="utf-8")
            self.assertTrue(
                guard.validate_fable_verdict(
                    path,
                    execution_path,
                    policy,
                    base_sha=base_sha,
                    head_sha=head_sha,
                    content_sha256=content_sha256,
                    patch_sha256=patch_sha256,
                )["approved"]
            )
            companion_execution[-1]["modelUsage"]["claude-haiku-4-5-20251001"]["outputTokens"] = 65
            execution_path.write_text(json.dumps(companion_execution), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.validate_fable_verdict(
                    path,
                    execution_path,
                    policy,
                    base_sha=base_sha,
                    head_sha=head_sha,
                    content_sha256=content_sha256,
                    patch_sha256=patch_sha256,
                )
            execution_path.write_text(json.dumps(execution(verdict)), encoding="utf-8")
            for field, replacement in (
                ("reviewed_head_sha", "5" * 40),
                ("reviewed_content_sha256", "6" * 64),
                ("reviewed_patch_sha256", "7" * 64),
            ):
                poisoned = {**verdict, field: replacement}
                path.write_text(json.dumps(poisoned), encoding="utf-8")
                with self.assertRaises(guard.GuardError):
                    guard.validate_fable_verdict(
                        path,
                        execution_path,
                        policy,
                        base_sha=base_sha,
                        head_sha=head_sha,
                        content_sha256=content_sha256,
                        patch_sha256=patch_sha256,
                    )
            rejected = {**verdict, "verdict": "rejected", "material_findings": ["unsafe skill"]}
            path.write_text(json.dumps(rejected), encoding="utf-8")
            execution_path.write_text(json.dumps(execution(rejected)), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.validate_fable_verdict(
                    path,
                    execution_path,
                    policy,
                    base_sha=base_sha,
                    head_sha=head_sha,
                    content_sha256=content_sha256,
                    patch_sha256=patch_sha256,
                )
            path.write_text(json.dumps(verdict), encoding="utf-8")
            invalid_execution_shapes = (
                execution(verdict, init_model="claude-other-model"),
                execution(verdict, duplicate_init=True),
                execution(verdict, usage_models=()),
                execution(verdict, usage_models=("claude-fable-5-1", "claude-other-model")),
            )
            for messages in invalid_execution_shapes:
                execution_path.write_text(json.dumps(messages), encoding="utf-8")
                with self.assertRaises(guard.GuardError):
                    guard.validate_fable_verdict(
                        path,
                        execution_path,
                        policy,
                        base_sha=base_sha,
                        head_sha=head_sha,
                        content_sha256=content_sha256,
                        patch_sha256=patch_sha256,
                    )


class KiroCredentialStreamTests(unittest.TestCase):
    SESSION_ID = "sess_11111111-1111-4111-8111-111111111111"
    OTHER_SESSION_ID = "sess_22222222-2222-4222-8222-222222222222"
    CALL_ID = "12345678-1234-4123-8123-123456789abc"
    REPLAY_ID = "sanitizedReplayId_1234567890123456789012"
    FOCUS_TITLE = stream_guard.MARKER

    @staticmethod
    def stream(*events: dict[str, Any]) -> bytes:
        return b"".join(
            json.dumps(event, separators=(",", ":")).encode() + b"\n" for event in events
        )

    @staticmethod
    def run_started() -> dict[str, Any]:
        return {
            "type": "runStarted",
            "data": {
                "payloadSchema": "acp",
                "acpProtocolVersion": 1,
                "engine": "v3",
            },
        }

    @classmethod
    def run_finished(
        cls,
        *,
        session_id: str | None = None,
        final_text: str | None = None,
        status: str = "success",
        stop_reason: str = "end_turn",
        truncated: bool = False,
    ) -> dict[str, Any]:
        return {
            "type": "runFinished",
            "data": {
                "sessionId": session_id or cls.SESSION_ID,
                "status": status,
                "stopReason": stop_reason,
                "finalText": (final_text if final_text is not None else stream_guard.MARKER),
                "finalTextTruncated": truncated,
            },
        }

    @classmethod
    def agent_chunk(
        cls,
        text: str,
        *,
        session_id: str | None = None,
        replay_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": session_id or cls.SESSION_ID,
                "update": {
                    "_meta": {"kiro": {"replayId": replay_id or cls.REPLAY_ID}},
                    "content": {"type": "text", "text": text},
                    "sessionUpdate": "agent_message_chunk",
                },
            },
        }

    @classmethod
    def cloud_config_start(cls, *, session_id: str | None = None) -> dict[str, Any]:
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": session_id or cls.SESSION_ID,
                "update": {
                    "_meta": {"kiro": {"toolId": "fetch_cloud_config"}},
                    "sessionUpdate": "tool_call",
                    "status": "in_progress",
                    "title": "Fetching your cloud config",
                    "toolCallId": cls.CALL_ID,
                },
            },
        }

    @classmethod
    def cloud_config_terminal(
        cls,
        *,
        status: str = "failed",
        session_id: str | None = None,
        observed_completed_output: bool = False,
    ) -> dict[str, Any]:
        update: dict[str, Any] = {
            "sessionUpdate": "tool_call_update",
            "status": status,
            "toolCallId": cls.CALL_ID,
        }
        if status == "failed":
            update["rawOutput"] = "sanitized isolated cloud-config lookup failure"
        elif status == "completed" and observed_completed_output:
            update["rawOutput"] = {"kind": "notEnabled", "retracted": False}
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": session_id or cls.SESSION_ID,
                "update": update,
            },
        }

    @classmethod
    def unrelated_update(cls) -> dict[str, Any]:
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": cls.SESSION_ID,
                "update": {
                    "sessionUpdate": "session_info_update",
                    "_meta": {
                        "kiro": {
                            "kind": "context_usage",
                            "breakdown": {
                                "tools": {
                                    "builtin": {"percent": 0.6, "tokens": 6},
                                    "mcp": {"percent": 0, "tokens": 0},
                                    "percent": 0.0,
                                    "tokens": 6,
                                }
                            },
                        }
                    },
                },
            },
        }

    @classmethod
    def focus_update(cls, *, title: str | None = None) -> dict[str, Any]:
        current_title = title or cls.FOCUS_TITLE
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": cls.SESSION_ID,
                "update": {
                    "sessionUpdate": "session_info_update",
                    "title": current_title,
                    "_meta": {
                        "kiro": {
                            "kind": "focus_update",
                            "title": current_title,
                            "focus": {"title": current_title},
                        }
                    },
                },
            },
        }

    def complete(self, *events: dict[str, Any]) -> bytes:
        return self.stream(self.run_started(), *events, self.run_finished())

    def validate(self, raw: bytes) -> dict[str, int | bool]:
        return stream_guard.validate_stream_bytes(
            raw,
            b"",
            return_code=0,
            api_key="not-present-in-stream",
        )

    def test_accepts_sanitized_real_agent_message_wire_shape(self) -> None:
        chunks = ["PK", "-", "STACK", "-K", "IRO", "-A", "UTH", "-", "OK"]
        raw = self.complete(*(self.agent_chunk(chunk) for chunk in chunks))
        self.assertEqual(self.validate(raw), {"ok": True, "events": 11})

    def test_accepts_one_bounded_challenge_with_exact_assistant_final_equality(self) -> None:
        response = f"{stream_guard.MARKER}\nAcknowledged."
        raw = self.stream(
            self.run_started(),
            self.agent_chunk(response),
            self.run_finished(final_text=response),
        )
        self.assertEqual(self.validate(raw), {"ok": True, "events": 3})

    def test_hosted_smoke_requires_advertised_opus_5_xhigh(self) -> None:
        config = {
            "type": "sessionUpdate",
            "data": {
                "sessionId": self.SESSION_ID,
                "update": {
                    "sessionUpdate": "config_option_update",
                    "configOptions": [
                        {
                            "id": "model",
                            "currentValue": "gpt-5.6-sol",
                            "options": [
                                {
                                    "value": "claude-opus-5",
                                    "_meta": {
                                        "kiro": {
                                            "hasEffort": True,
                                            "effortLevels": [
                                                "low",
                                                "medium",
                                                "high",
                                                "xhigh",
                                                "max",
                                            ],
                                        }
                                    },
                                }
                            ],
                        }
                    ],
                },
            },
        }
        raw = self.complete(config, self.agent_chunk(stream_guard.MARKER))
        result = stream_guard.validate_stream_bytes(
            raw,
            b"",
            return_code=0,
            api_key="not-present-in-stream",
            require_review_model=True,
        )
        self.assertTrue(result["peer_review_model_advertised"])

    def test_rejects_missing_duplicate_or_overlong_challenge_response(self) -> None:
        responses = (
            "no challenge present",
            f"{stream_guard.MARKER} {stream_guard.MARKER}",
            stream_guard.MARKER
            + "x"
            * (stream_guard.MAX_ASSISTANT_RESPONSE_BYTES - len(stream_guard.MARKER.encode()) + 1),
        )
        for response in responses:
            with (
                self.subTest(response_bytes=len(response.encode())),
                self.assertRaises(stream_guard.StreamError),
            ):
                self.validate(
                    self.stream(
                        self.run_started(),
                        self.agent_chunk(response),
                        self.run_finished(final_text=response),
                    )
                )

    def test_accepts_exact_failed_and_completed_bootstrap_pairs(self) -> None:
        for terminal in (
            self.cloud_config_terminal(status="failed"),
            self.cloud_config_terminal(status="completed"),
            self.cloud_config_terminal(status="completed", observed_completed_output=True),
        ):
            with self.subTest(status=terminal["data"]["update"]["status"]):
                raw = self.complete(
                    self.cloud_config_start(),
                    self.unrelated_update(),
                    terminal,
                    self.agent_chunk(stream_guard.MARKER),
                )
                self.assertEqual(self.validate(raw), {"ok": True, "events": 6})

    def test_rejects_nested_legacy_and_user_marker_spoofs(self) -> None:
        nested = {
            "type": "telemetry",
            "data": {
                "wrapper": {
                    "sessionUpdate": "agent_message_chunk",
                    "content": {"type": "text", "text": stream_guard.MARKER},
                }
            },
        }
        legacy = {
            "sessionUpdate": {
                "sessionId": self.SESSION_ID,
                "update": {
                    "sessionUpdate": "agent_message_chunk",
                    "content": {"type": "text", "text": stream_guard.MARKER},
                },
            }
        }
        user_echo = {
            "type": "sessionUpdate",
            "data": {
                "sessionId": self.SESSION_ID,
                "update": {
                    "sessionUpdate": "user_message_chunk",
                    "content": {"type": "text", "text": stream_guard.MARKER},
                },
            },
        }
        for spoof in (nested, legacy, user_echo):
            with self.subTest(spoof=spoof), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(spoof))

    def test_marker_rejection_reports_only_bounded_structural_provenance(self) -> None:
        echoed_prompt = {
            "type": "sessionUpdate",
            "data": {
                "sessionId": self.SESSION_ID,
                "update": {
                    "sessionUpdate": "session_info_update",
                    "_meta": {
                        "kiro": {
                            "kind": "prompt_echo",
                            "prompt": f"untrusted-prefix {stream_guard.MARKER} untrusted-suffix",
                        }
                    },
                },
            },
        }
        with self.assertRaises(stream_guard.StreamError) as caught:
            self.validate(self.complete(echoed_prompt))

        message = str(caught.exception)
        self.assertIn('"event_index_0_based":1', message)
        self.assertIn('"marker_path_count":1', message)
        self.assertIn('"marker_paths":["$.data.update._meta.kiro.prompt"]', message)
        self.assertIn('"session_update_kind":"session_info_update"', message)
        self.assertNotIn(self.SESSION_ID, message)
        self.assertNotIn(stream_guard.MARKER, message)
        self.assertNotIn("untrusted-prefix", message)
        self.assertNotIn("untrusted-suffix", message)

        many_echoes = {
            "type": "sessionUpdate",
            "data": {
                "sessionId": self.SESSION_ID,
                "update": {
                    "sessionUpdate": "config_option_update",
                    "configOptions": [{"description": stream_guard.MARKER} for _ in range(12)],
                },
            },
        }
        with self.assertRaises(stream_guard.StreamError) as many_caught:
            self.validate(self.complete(many_echoes))
        diagnostic = json.loads(str(many_caught.exception).split("structural_diagnostic=", 1)[1])
        self.assertEqual(diagnostic["marker_path_count"], 12)
        self.assertEqual(len(diagnostic["marker_paths"]), 8)
        self.assertTrue(
            all(
                path.startswith("$.data.update.configOptions[")
                for path in diagnostic["marker_paths"]
            )
        )

        long_key = "untrusted-structural-key-" + "x" * 64
        nonstandard_key_echo = {
            "type": "sessionUpdate",
            "data": {
                "sessionId": self.SESSION_ID,
                "update": {
                    "sessionUpdate": "session_info_update",
                    "_meta": {"kiro": {"kind": "prompt_echo", long_key: stream_guard.MARKER}},
                },
            },
        }
        with self.assertRaises(stream_guard.StreamError) as redacted_caught:
            self.validate(self.complete(nonstandard_key_echo))
        redacted_message = str(redacted_caught.exception)
        self.assertIn("$.data.update._meta.kiro.<redacted-key>", redacted_message)
        self.assertNotIn(long_key, redacted_message)

    def test_accepts_only_exact_focus_update_title_echo_as_non_evidence(self) -> None:
        raw = self.complete(self.focus_update(), self.agent_chunk(stream_guard.MARKER))
        self.assertEqual(self.validate(raw), {"ok": True, "events": 4})

        with self.assertRaises(stream_guard.StreamError):
            self.validate(self.complete(self.focus_update()))

    def test_rejects_focus_update_title_echo_shape_drift(self) -> None:
        def clone(event: dict[str, Any]) -> dict[str, Any]:
            return json.loads(json.dumps(event))

        extra_update = clone(self.focus_update())
        extra_update["data"]["update"]["unexpected"] = True
        extra_metadata = clone(self.focus_update())
        extra_metadata["data"]["update"]["_meta"]["unexpected"] = True
        extra_kiro = clone(self.focus_update())
        extra_kiro["data"]["update"]["_meta"]["kiro"]["unexpected"] = True
        extra_focus = clone(self.focus_update())
        extra_focus["data"]["update"]["_meta"]["kiro"]["focus"]["unexpected"] = True
        mismatched_title = clone(self.focus_update())
        mismatched_title["data"]["update"]["_meta"]["kiro"]["title"] += " mismatch"
        wrong_kind = clone(self.focus_update())
        wrong_kind["data"]["update"]["_meta"]["kiro"]["kind"] = "prompt_echo"
        wrong_path = clone(self.focus_update())
        wrong_path["data"]["update"]["_meta"]["kiro"]["other"] = stream_guard.MARKER
        empty_title = self.focus_update(title="placeholder")
        empty_title["data"]["update"]["title"] = ""
        overlong_title = self.focus_update(title="x" * (stream_guard.MAX_FOCUS_TITLE_BYTES + 1))

        for event in (
            extra_update,
            extra_metadata,
            extra_kiro,
            extra_focus,
            mismatched_title,
            wrong_kind,
            wrong_path,
            empty_title,
            overlong_title,
        ):
            with self.subTest(event=event), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(event, self.agent_chunk(stream_guard.MARKER)))

    def test_rejects_bootstrap_order_and_identity_failures(self) -> None:
        cases = (
            (
                self.agent_chunk(stream_guard.MARKER),
                self.cloud_config_start(),
                self.cloud_config_terminal(),
            ),
            (
                self.cloud_config_start(),
                self.agent_chunk(stream_guard.MARKER),
                self.cloud_config_terminal(),
            ),
            (
                self.cloud_config_start(session_id=self.OTHER_SESSION_ID),
                self.cloud_config_terminal(session_id=self.OTHER_SESSION_ID),
                self.agent_chunk(stream_guard.MARKER),
            ),
            (self.cloud_config_start(),),
            (self.cloud_config_terminal(), self.agent_chunk(stream_guard.MARKER)),
            (
                self.cloud_config_start(),
                self.cloud_config_start(),
                self.cloud_config_terminal(),
                self.agent_chunk(stream_guard.MARKER),
            ),
            (
                self.cloud_config_start(),
                self.cloud_config_terminal(),
                self.cloud_config_terminal(),
                self.agent_chunk(stream_guard.MARKER),
            ),
        )
        for events in cases:
            with self.subTest(events=events), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(*events))

    def test_rejects_bootstrap_extra_missing_and_status_shape_confusion(self) -> None:
        def clone(event: dict[str, Any]) -> dict[str, Any]:
            return json.loads(json.dumps(event))

        extra_start = clone(self.cloud_config_start())
        extra_start["data"]["update"]["unexpected"] = True
        missing_failed = clone(self.cloud_config_terminal())
        del missing_failed["data"]["update"]["rawOutput"]
        empty_failed = clone(self.cloud_config_terminal())
        empty_failed["data"]["update"]["rawOutput"] = ""
        non_string_failed = clone(self.cloud_config_terminal())
        non_string_failed["data"]["update"]["rawOutput"] = {"error": "sanitized"}
        completed_with_output = clone(self.cloud_config_terminal(status="completed"))
        completed_with_output["data"]["update"]["rawOutput"] = "unexpected"
        wrong_title = clone(self.cloud_config_start())
        wrong_title["data"]["update"]["title"] = "Fetching another config"
        wrong_tool = clone(self.cloud_config_start())
        wrong_tool["data"]["update"]["_meta"]["kiro"]["toolId"] = "read"
        mismatched_terminal = clone(self.cloud_config_terminal())
        mismatched_terminal["data"]["update"]["toolCallId"] = "abcdefab-cdef-4abc-8def-abcdefabcdef"

        cases = (
            (extra_start, self.cloud_config_terminal()),
            (self.cloud_config_start(), missing_failed),
            (self.cloud_config_start(), empty_failed),
            (self.cloud_config_start(), non_string_failed),
            (self.cloud_config_start(), completed_with_output),
            (wrong_title, self.cloud_config_terminal()),
            (wrong_tool, self.cloud_config_terminal()),
            (self.cloud_config_start(), mismatched_terminal),
        )
        for start, terminal in cases:
            with self.subTest(start=start, terminal=terminal):
                raw = self.complete(
                    start,
                    terminal,
                    self.agent_chunk(stream_guard.MARKER),
                )
                with self.assertRaises(stream_guard.StreamError):
                    self.validate(raw)

    def test_rejects_unknown_tool_prefix_discriminators_and_keys(self) -> None:
        def tool_update(kind: str) -> dict[str, Any]:
            return {
                "type": "sessionUpdate",
                "data": {
                    "sessionId": self.SESSION_ID,
                    "update": {
                        "sessionUpdate": kind,
                        "toolCallId": self.CALL_ID,
                    },
                },
            }

        prefixed_key = self.unrelated_update()
        prefixed_key["data"]["update"]["toolCallStart"] = {"sanitized": True}
        arbitrary_tools_key = {
            "type": "telemetry",
            "data": {
                "tools": {
                    "builtin": {"percent": 0.0, "tokens": 0},
                    "mcp": {"percent": 0.0, "tokens": 0},
                    "percent": 0.0,
                    "tokens": 0,
                }
            },
        }
        for event in (
            tool_update("tool_call_start"),
            tool_update("tool_call_delta"),
            prefixed_key,
            {"type": "telemetry", "data": {"toolCallStart": {}}},
            arbitrary_tools_key,
        ):
            with self.subTest(event=event), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(event, self.agent_chunk(stream_guard.MARKER)))

    def test_rejects_unknown_top_level_and_session_update_kinds(self) -> None:
        def unknown_session_update(kind: str) -> dict[str, Any]:
            return {
                "type": "sessionUpdate",
                "data": {
                    "sessionId": self.SESSION_ID,
                    "update": {"sessionUpdate": kind},
                },
            }

        for event in (
            {"type": "commandExecution", "data": {}},
            {"type": "function_call", "data": {}},
            unknown_session_update("commandExecution"),
            unknown_session_update("function_call"),
        ):
            with self.subTest(event=event), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(event, self.agent_chunk(stream_guard.MARKER)))

    def test_rejects_malformed_metrics_and_ignored_session_updates(self) -> None:
        def clone(event: dict[str, Any]) -> dict[str, Any]:
            return json.loads(json.dumps(event))

        wrong_metric_keys = clone(self.unrelated_update())
        wrong_metric_keys["data"]["update"]["_meta"]["kiro"]["breakdown"]["tools"]["calls"] = 0
        wrong_metric_type = clone(self.unrelated_update())
        wrong_metric_type["data"]["update"]["_meta"]["kiro"]["breakdown"]["tools"]["percent"] = True
        wrong_metric_kind = clone(self.unrelated_update())
        wrong_metric_kind["data"]["update"]["_meta"]["kiro"]["kind"] = "other"
        arbitrary_nested_metric = clone(self.unrelated_update())
        arbitrary_nested_metric["data"]["update"]["_meta"]["kiro"]["breakdown"]["tools"]["builtin"][
            "calls"
        ] = 0
        invalid_nested_percent = clone(self.unrelated_update())
        invalid_nested_percent["data"]["update"]["_meta"]["kiro"]["breakdown"]["tools"]["mcp"][
            "percent"
        ] = 101
        invalid_nested_tokens = clone(self.unrelated_update())
        invalid_nested_tokens["data"]["update"]["_meta"]["kiro"]["breakdown"]["tools"]["builtin"][
            "tokens"
        ] = -1
        wrong_session = clone(self.unrelated_update())
        wrong_session["data"]["sessionId"] = self.OTHER_SESSION_ID
        malformed_envelope = clone(self.unrelated_update())
        malformed_envelope["data"]["unexpected"] = True

        for event in (
            wrong_metric_keys,
            wrong_metric_type,
            wrong_metric_kind,
            arbitrary_nested_metric,
            invalid_nested_percent,
            invalid_nested_tokens,
            wrong_session,
            malformed_envelope,
        ):
            with self.subTest(event=event), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(event, self.agent_chunk(stream_guard.MARKER)))

    def test_rejects_agent_and_run_boundary_shape_or_identity_drift(self) -> None:
        def clone(event: dict[str, Any]) -> dict[str, Any]:
            return json.loads(json.dumps(event))

        extra_agent = clone(self.agent_chunk(stream_guard.MARKER))
        extra_agent["data"]["update"]["unexpected"] = True
        nested_content = clone(self.agent_chunk(stream_guard.MARKER))
        nested_content["data"]["update"]["content"]["unexpected"] = True
        changed_replay = self.agent_chunk(
            "-STACK-KIRO-AUTH-OK",
            replay_id="otherReplayId_12345678901234567890123456",
        )
        identity_cases = (
            (extra_agent,),
            (nested_content,),
            (
                self.agent_chunk("PK"),
                self.agent_chunk("-STACK-KIRO-AUTH-OK", session_id=self.OTHER_SESSION_ID),
            ),
            (self.agent_chunk("PK"), changed_replay),
            (self.agent_chunk(stream_guard.MARKER + " "),),
        )
        for events in identity_cases:
            with self.subTest(events=events), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(*events))

        with self.assertRaises(stream_guard.StreamError):
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(stream_guard.MARKER),
                    self.run_finished(session_id=self.OTHER_SESSION_ID),
                )
            )
        with self.assertRaises(stream_guard.StreamError):
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(stream_guard.MARKER),
                    self.run_finished(),
                    self.unrelated_update(),
                )
            )
        malformed_start = self.run_started()
        malformed_start["data"]["unexpected"] = True
        wrong_protocol_type = self.run_started()
        wrong_protocol_type["data"]["acpProtocolVersion"] = True
        malformed_finish = self.run_finished()
        malformed_finish["data"]["unexpected"] = True
        for start, finish in (
            (malformed_start, self.run_finished()),
            (wrong_protocol_type, self.run_finished()),
            (self.run_started(), malformed_finish),
        ):
            with (
                self.subTest(start=start, finish=finish),
                self.assertRaises(stream_guard.StreamError),
            ):
                self.validate(
                    self.stream(
                        start,
                        self.agent_chunk(stream_guard.MARKER),
                        finish,
                    )
                )

    def test_run_finished_failure_reports_only_bounded_non_content_metadata(self) -> None:
        unexpected_final = f"sensitive-prefix {stream_guard.MARKER} sensitive-suffix"
        with self.assertRaises(stream_guard.StreamError) as mismatch_caught:
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(stream_guard.MARKER),
                    self.run_finished(final_text=unexpected_final),
                )
            )
        mismatch_message = str(mismatch_caught.exception)
        mismatch_diagnostic = json.loads(mismatch_message.split("run_finished_diagnostic=", 1)[1])
        self.assertEqual(
            mismatch_diagnostic,
            {
                "assistant_final_equal": False,
                "finalTextTruncated": False,
                "final_text_utf8_bytes": len(unexpected_final.encode()),
                "marker_occurrence_count": 1,
                "status": "success",
                "stopReason": "end_turn",
            },
        )
        self.assertNotIn(unexpected_final, mismatch_message)
        self.assertNotIn(stream_guard.MARKER, mismatch_message)
        self.assertNotIn(self.SESSION_ID, mismatch_message)
        self.assertNotIn("sensitive-prefix", mismatch_message)

        equal_non_marker = "sensitive-equal-non-marker"
        with self.assertRaises(stream_guard.StreamError) as equal_caught:
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(equal_non_marker),
                    self.run_finished(final_text=equal_non_marker),
                )
            )
        equal_message = str(equal_caught.exception)
        equal_diagnostic = json.loads(equal_message.split("run_finished_diagnostic=", 1)[1])
        self.assertTrue(equal_diagnostic["assistant_final_equal"])
        self.assertEqual(equal_diagnostic["marker_occurrence_count"], 0)
        self.assertNotIn(equal_non_marker, equal_message)

        with self.assertRaises(stream_guard.StreamError) as failed_caught:
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(stream_guard.MARKER),
                    self.run_finished(status="failed"),
                )
            )
        failed_diagnostic = json.loads(
            str(failed_caught.exception).split("run_finished_diagnostic=", 1)[1]
        )
        self.assertEqual(failed_diagnostic["status"], "failed")
        self.assertIsNone(failed_diagnostic["assistant_final_equal"])

        unsafe_status = "sensitiveRawStatus"
        with self.assertRaises(stream_guard.StreamError) as unsafe_caught:
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(stream_guard.MARKER),
                    self.run_finished(status=unsafe_status),
                )
            )
        unsafe_message = str(unsafe_caught.exception)
        unsafe_diagnostic = json.loads(unsafe_message.split("run_finished_diagnostic=", 1)[1])
        self.assertIsNone(unsafe_diagnostic["status"])
        self.assertNotIn(unsafe_status, unsafe_message)

    def test_rejects_malformed_duplicate_and_non_finite_json(self) -> None:
        for raw in (
            b'{"broken":\n',
            b'{"type":"x","type":"y"}\n',
            b'{"value":NaN}\n',
        ):
            with self.assertRaises(stream_guard.StreamError):
                self.validate(raw)


class KiroPermissionStreamTests(unittest.TestCase):
    @staticmethod
    def selection_event(workspace: str) -> dict[str, Any]:
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": "sanitized-session",
                "update": {
                    "sessionUpdate": "config_option_update",
                    "configOptions": [
                        {
                            "id": "mode",
                            "name": "Mode",
                            "type": "select",
                            "category": "mode",
                            "currentValue": permission_stream_guard.PERMISSION_AGENT_NAME,
                            "options": [
                                {
                                    "name": permission_stream_guard.PERMISSION_AGENT_NAME,
                                    "value": permission_stream_guard.PERMISSION_AGENT_NAME,
                                    "description": (
                                        permission_stream_guard.PERMISSION_AGENT_DESCRIPTION
                                    ),
                                    "_meta": {
                                        "kiro": {
                                            "source": "workspace",
                                            "welcomeMessage": (
                                                permission_stream_guard.PERMISSION_AGENT_WELCOME
                                            ),
                                            "resource": {
                                                "resourceType": "agent",
                                                "source": {
                                                    "origin": "workspace",
                                                    "root": workspace,
                                                },
                                            },
                                        }
                                    },
                                }
                            ],
                        }
                    ],
                },
            },
        }

    def test_requires_exact_workspace_agent_selection_attestation(self) -> None:
        workspace = "/tmp/pkstack-permission-workspace"
        event = self.selection_event(workspace)
        initial_vibe = json.loads(json.dumps(event))
        initial_vibe["data"]["update"]["configOptions"][0]["currentValue"] = "vibe"
        permission_stream_guard.validate_workspace_agent_selection(
            [initial_vibe, event], expected_workspace=workspace
        )

        def clone() -> dict[str, Any]:
            return json.loads(json.dumps(event))

        wrong_root = clone()
        wrong_root["data"]["update"]["configOptions"][0]["options"][0]["_meta"]["kiro"]["resource"][
            "source"
        ]["root"] = "/tmp/other-workspace"
        global_source = clone()
        global_source["data"]["update"]["configOptions"][0]["options"][0]["_meta"]["kiro"][
            "source"
        ] = "global"
        extra_option_key = clone()
        extra_option_key["data"]["update"]["configOptions"][0]["options"][0]["unexpected"] = True
        duplicate_option = clone()
        duplicate_option["data"]["update"]["configOptions"][0]["options"].append(
            duplicate_option["data"]["update"]["configOptions"][0]["options"][0]
        )
        fallback = clone()
        fallback["data"]["update"]["configOptions"][0]["currentValue"] = "vibe"
        conflicting_mode = clone()
        second_mode = json.loads(json.dumps(conflicting_mode["data"]["update"]["configOptions"][0]))
        second_mode["currentValue"] = "vibe"
        conflicting_mode["data"]["update"]["configOptions"].append(second_mode)

        for malformed in (
            wrong_root,
            global_source,
            extra_option_key,
            duplicate_option,
            fallback,
        ):
            with (
                self.subTest(malformed=malformed),
                self.assertRaises(permission_stream_guard.StreamError),
            ):
                permission_stream_guard.validate_workspace_agent_selection(
                    [malformed], expected_workspace=workspace
                )

        for events in (
            [event, fallback],
            [conflicting_mode],
        ):
            with (
                self.subTest(events=events),
                self.assertRaises(permission_stream_guard.StreamError),
            ):
                permission_stream_guard.validate_workspace_agent_selection(
                    events, expected_workspace=workspace
                )

    SESSION_ID = "sess_00000000-0000-0000-0000-000000000001"

    @staticmethod
    def tool_call_id(index: int) -> str:
        return f"call_00000000-0000-0000-0000-{index:012x}"

    @classmethod
    def envelope(cls, update: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "sessionUpdate",
            "data": {"sessionId": cls.SESSION_ID, "update": update},
        }

    @staticmethod
    def reflected_content(raw_output: dict[str, str]) -> list[dict[str, Any]]:
        return [
            {
                "type": "content",
                "content": {"type": "text", "text": json.dumps(raw_output)},
            }
        ]

    @classmethod
    def read_group(cls, workspace: Path, index: int) -> list[dict[str, Any]]:
        tool_call_id = cls.tool_call_id(index)
        raw_input = {
            "limit": 2000,
            "offset": 0,
            "path": permission_stream_guard.FIXTURE_INPUT_PATH,
        }
        locations = [{"path": str(workspace / permission_stream_guard.FIXTURE_INPUT_PATH)}]
        origin = {"kiro": {"toolOrigin": "default"}}
        raw_output = {
            "message": (
                "fixture-input.txt: " + permission_stream_guard.FIXTURE_INPUT_TEXT.rstrip("\n")
            )
        }
        return [
            cls.envelope(
                {
                    "sessionUpdate": "tool_call",
                    "toolCallId": tool_call_id,
                    "title": "Read File",
                    "kind": "read",
                    "rawInput": raw_input,
                    "locations": locations,
                    "_meta": origin,
                }
            ),
            cls.envelope(
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": tool_call_id,
                    "status": "in_progress",
                    "rawInput": raw_input,
                    "locations": locations,
                    "_meta": origin,
                }
            ),
            cls.envelope(
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": tool_call_id,
                    "status": "completed",
                    "title": "Read File",
                    "rawInput": raw_input,
                    "rawOutput": raw_output,
                    "content": cls.reflected_content(raw_output),
                    "locations": locations,
                    "_meta": origin,
                }
            ),
        ]

    @classmethod
    def grep_group(cls, index: int) -> list[dict[str, Any]]:
        tool_call_id = cls.tool_call_id(index)
        raw_input = {
            "caseSensitive": True,
            "explanation": "Find the exact sterile token.",
            "includePattern": permission_stream_guard.FIXTURE_INPUT_PATH,
            "query": permission_stream_guard.GREP_QUERY,
        }
        origin = {"kiro": {"toolOrigin": "default"}}
        raw_output = {
            "message": (
                "fixture-input.txt: " + permission_stream_guard.FIXTURE_INPUT_TEXT.rstrip("\n")
            )
        }
        return [
            cls.envelope(
                {
                    "sessionUpdate": "tool_call",
                    "toolCallId": tool_call_id,
                    "title": "Grep Search",
                    "kind": "search",
                    "rawInput": raw_input,
                    "_meta": origin,
                }
            ),
            cls.envelope(
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": tool_call_id,
                    "status": "in_progress",
                    "rawInput": raw_input,
                    "_meta": origin,
                }
            ),
            cls.envelope(
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": tool_call_id,
                    "status": "completed",
                    "title": "Grep Search",
                    "rawInput": raw_input,
                    "rawOutput": raw_output,
                    "content": cls.reflected_content(raw_output),
                    "_meta": origin,
                }
            ),
        ]

    @classmethod
    def write_group(
        cls,
        workspace: Path,
        index: int,
        relative_path: str,
        text: str,
        *,
        denied: bool,
        deny_patterns: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        tool_call_id = cls.tool_call_id(index)
        raw_input = {"path": relative_path, "text": text}
        locations = [{"path": str(workspace / relative_path)}]
        start_preview = {"file": relative_path, "modifiedContent": text}
        if denied:
            start_preview["originalContent"] = f"PROTECTED_BASELINE {relative_path}\n"
        start = cls.envelope(
            {
                "sessionUpdate": "tool_call",
                "toolCallId": tool_call_id,
                "status": "in_progress",
                "title": "Write File",
                "kind": "edit",
                "rawInput": raw_input,
                "locations": locations,
                "_meta": {"kiro": {"toolOrigin": "default", "preview": start_preview}},
            }
        )
        pending = cls.envelope(
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "status": "pending",
                "rawInput": raw_input,
                "locations": locations,
                "_meta": {
                    "kiro": {
                        "toolOrigin": "default",
                        "preview": {"file": relative_path},
                    }
                },
            }
        )
        if denied:
            assert deny_patterns is not None
            policy_denial = {
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
            terminal = cls.envelope(
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": tool_call_id,
                    "status": "failed",
                    "title": "Write File",
                    "rawInput": raw_input,
                    "rawOutput": {"message": "Tool call denied. Source: agent-profile."},
                    "content": [
                        {
                            "type": "diff",
                            "path": relative_path,
                            "oldText": "",
                            "newText": text,
                        }
                    ],
                    "locations": locations,
                    "_meta": {
                        "kiro": {
                            "toolOrigin": "default",
                            "preview": {
                                "file": relative_path,
                                "modifiedContent": text,
                                "originalContent": "",
                            },
                            "policyDenial": policy_denial,
                        }
                    },
                }
            )
            return [start, pending, terminal]

        absolute_path = str(workspace / relative_path)
        file_uri = f"file://{absolute_path}"
        snapshot = f"kiro-snapshot-v2://{cls.SESSION_ID}/{index}"
        terminal = cls.envelope(
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "status": "completed",
                "title": "Write File",
                "rawInput": raw_input,
                "rawOutput": {"message": "File written successfully."},
                "content": [
                    {
                        "type": "diff",
                        "path": file_uri,
                        "oldText": "",
                        "newText": text,
                    }
                ],
                "locations": locations,
                "_meta": {
                    "kiro": {
                        "toolOrigin": "default",
                        "preview": {
                            "file": absolute_path,
                            "local": file_uri,
                            "modified": snapshot,
                            "modifiedContent": text,
                            "originalContent": "",
                        },
                        "checkpoint": {"local": file_uri, "modified": snapshot},
                    }
                },
            }
        )
        return [start, pending, terminal]

    @classmethod
    def complete_events(
        cls, workspace: Path, *, denied_resource: str | None = None
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = [
            {
                "type": "runStarted",
                "data": {
                    "payloadSchema": "acp",
                    "acpProtocolVersion": 1,
                    "engine": "v3",
                },
            }
        ]
        selection = cls.selection_event(str(workspace))
        selection["data"]["sessionId"] = cls.SESSION_ID
        events.append(selection)
        if denied_resource is not None:
            fixture = json.loads(
                (ROOT / ".github/fixtures/kiro-permission-agent.json").read_text(encoding="utf-8")
            )
            deny_patterns = fixture["permissions"]["rules"][3]["match"]
            events.extend(
                cls.write_group(
                    workspace,
                    1,
                    denied_resource,
                    permission_stream_guard.DENIED_WRITE_TEXT,
                    denied=True,
                    deny_patterns=deny_patterns,
                )
            )
            used_tools = ["fs_write"]
        else:
            events.extend(cls.read_group(workspace, 1))
            events.extend(cls.grep_group(2))
            for index, (relative_path, text) in enumerate(
                permission_stream_guard.ALLOWED_WRITES, start=3
            ):
                events.extend(
                    cls.write_group(
                        workspace,
                        index,
                        relative_path,
                        text,
                        denied=False,
                    )
                )
            used_tools = [
                "read_file",
                "grep_search",
                *("fs_write" for _ in permission_stream_guard.ALLOWED_WRITES),
            ]
        request_ids = [
            f"00000000-0000-0000-0001-{index:012x}" for index in range(len(used_tools) + 1)
        ]
        events.append(
            cls.envelope(
                {
                    "sessionUpdate": "session_info_update",
                    "_meta": {
                        "kiro": {
                            "kind": "turn_completion",
                            "status": "success",
                            "elapsedTime": 1,
                            "requestIds": request_ids,
                            "promptTurnSummaries": [
                                {
                                    "unit": "credit",
                                    "unitPlural": "credits",
                                    "usage": 0.25,
                                    "usedTools": used_tools,
                                }
                            ],
                        }
                    },
                }
            )
        )
        events.append(
            {
                "type": "runFinished",
                "data": {
                    "sessionId": cls.SESSION_ID,
                    "status": "success",
                    "stopReason": "end_turn",
                    "finalText": "",
                    "finalTextTruncated": False,
                },
            }
        )
        return events

    @staticmethod
    def write_stream(path: Path, events: list[dict[str, Any]]) -> None:
        path.write_text(
            "".join(f"{json.dumps(event, separators=(',', ':'))}\n" for event in events),
            encoding="utf-8",
        )
        path.chmod(0o600)

    @staticmethod
    def fixture_workspace(temporary: str) -> tuple[Path, Path, Path, Path]:
        root = Path(temporary)
        workspace = root / "workspace"
        agent = workspace / ".kiro/agents/pkstack-permission-fixture.json"
        agent.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / ".github/fixtures/kiro-permission-agent.json", agent)
        stream = root / "stream.jsonl"
        stderr = root / "stderr.log"
        stderr.write_text("", encoding="utf-8")
        stderr.chmod(0o600)
        return workspace, agent, stream, stderr

    def test_real_shape_allowed_and_isolated_denied_streams_validate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, agent, stream, stderr = self.fixture_workspace(temporary)
            allowed_events = self.complete_events(workspace)
            self.write_stream(stream, allowed_events)
            allowed = permission_stream_guard.validate_allowed_invocation(
                stream,
                stderr,
                return_code=124,
                api_key="test-secret",
                workspace=workspace,
            )
            self.assertEqual(allowed["user_tool_calls"], 9)
            self.assertEqual(allowed["credit_usage"], 0.25)

            without_explanation = self.complete_events(workspace)
            for event in without_explanation[5:8]:
                event["data"]["update"]["rawInput"].pop("explanation", None)
            self.write_stream(stream, without_explanation)
            optional_explanation = permission_stream_guard.validate_allowed_invocation(
                stream,
                stderr,
                return_code=0,
                api_key="test-secret",
                workspace=workspace,
            )
            self.assertEqual(optional_explanation["user_tool_calls"], 9)

            resource = permission_stream_guard.DENIED_RESOURCES[0]
            denied_events = self.complete_events(workspace, denied_resource=resource)
            self.write_stream(stream, denied_events)
            denied = permission_stream_guard.validate_denied_invocation(
                stream,
                stderr,
                return_code=0,
                api_key="test-secret",
                workspace=workspace,
                agent_path=agent,
                resource=resource,
            )
            self.assertEqual(denied["user_tool_calls"], 1)
            self.assertEqual(denied["resource"], resource)
            self.assertEqual(denied["preview_original_content"], {"start": True, "terminal": True})
            self.assertEqual(denied["diff_original_content"], "empty")

    def test_denied_previews_accept_optional_original_content_at_each_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, agent, stream, stderr = self.fixture_workspace(temporary)
            cases = itertools.product(
                permission_stream_guard.DENIED_RESOURCES,
                (False, True),
                (False, True),
                (None, ""),
            )
            for resource, start_present, terminal_present, old_text in cases:
                with self.subTest(
                    resource=resource,
                    start=start_present,
                    terminal=terminal_present,
                    old_text=old_text,
                ):
                    events = self.complete_events(workspace, denied_resource=resource)
                    for event_index, present in ((2, start_present), (-3, terminal_present)):
                        preview = events[event_index]["data"]["update"]["_meta"]["kiro"]["preview"]
                        if not present:
                            preview.pop("originalContent")
                            self.assertEqual(
                                preview,
                                {
                                    "file": resource,
                                    "modifiedContent": permission_stream_guard.DENIED_WRITE_TEXT,
                                },
                            )
                    events[-3]["data"]["update"]["content"][0]["oldText"] = old_text
                    self.write_stream(stream, events)
                    denied = permission_stream_guard.validate_denied_invocation(
                        stream,
                        stderr,
                        return_code=0,
                        api_key="test-secret",
                        workspace=workspace,
                        agent_path=agent,
                        resource=resource,
                    )
                    self.assertEqual(denied["user_tool_calls"], 1)
                    self.assertEqual(denied["resource"], resource)
                    self.assertEqual(
                        denied["preview_original_content"],
                        {"start": start_present, "terminal": terminal_present},
                    )
                    self.assertEqual(
                        denied["diff_original_content"], "unknown" if old_text is None else "empty"
                    )

    def test_denied_diff_rejects_malformed_originals_and_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, agent, stream, stderr = self.fixture_workspace(temporary)
            resource = permission_stream_guard.DENIED_RESOURCES[0]
            valid = {
                "type": "diff",
                "path": resource,
                "oldText": None,
                "newText": permission_stream_guard.DENIED_WRITE_TEXT,
            }
            cases = [
                ("wrong_original", {**valid, "oldText": "UNTRUSTED_DIFF"}),
                ("baseline_original", {**valid, "oldText": f"PROTECTED_BASELINE {resource}\n"}),
                ("boolean_original", {**valid, "oldText": False}),
                ("numeric_original", {**valid, "oldText": 0}),
                (
                    "missing_original",
                    {key: value for key, value in valid.items() if key != "oldText"},
                ),
                ("extra_key", {**valid, "UNTRUSTED_DIFF": "UNTRUSTED_DIFF"}),
                ("wrong_path", {**valid, "path": "UNTRUSTED_DIFF"}),
                ("wrong_content", {**valid, "newText": "UNTRUSTED_DIFF"}),
                ("wrong_type", {**valid, "type": "UNTRUSTED_DIFF"}),
            ]
            for case, content in cases:
                with self.subTest(case=case):
                    events = self.complete_events(workspace, denied_resource=resource)
                    events[-3]["data"]["update"]["content"] = [content]
                    self.write_stream(stream, events)
                    with self.assertRaises(permission_stream_guard.StreamError) as caught:
                        permission_stream_guard.validate_denied_invocation(
                            stream,
                            stderr,
                            return_code=0,
                            api_key="test-secret",
                            workspace=workspace,
                            agent_path=agent,
                            resource=resource,
                        )
                    self.assertEqual(str(caught.exception), "Kiro write diff content is invalid")

    def test_denied_terminal_preview_rejects_malformed_originals_and_extra_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, agent, stream, stderr = self.fixture_workspace(temporary)
            resource = permission_stream_guard.DENIED_RESOURCES[0]
            valid = {
                "file": resource,
                "modifiedContent": permission_stream_guard.DENIED_WRITE_TEXT,
            }
            cases = [
                ("wrong_original", {**valid, "originalContent": "UNTRUSTED_PREVIEW"}),
                (
                    "baseline_original",
                    {**valid, "originalContent": f"PROTECTED_BASELINE {resource}\n"},
                ),
                ("null_original", {**valid, "originalContent": None}),
                ("boolean_original", {**valid, "originalContent": False}),
                ("extra_without_original", {**valid, "UNTRUSTED_PREVIEW": "UNTRUSTED_PREVIEW"}),
                (
                    "extra_with_original",
                    {**valid, "originalContent": "", "UNTRUSTED_PREVIEW": None},
                ),
                ("wrong_file", {**valid, "file": "UNTRUSTED_PREVIEW"}),
                ("wrong_modified", {**valid, "modifiedContent": "UNTRUSTED_PREVIEW"}),
            ]
            for case, preview in cases:
                with self.subTest(case=case):
                    events = self.complete_events(workspace, denied_resource=resource)
                    events[-3]["data"]["update"]["_meta"]["kiro"]["preview"] = preview
                    self.write_stream(stream, events)
                    with self.assertRaises(permission_stream_guard.StreamError) as caught:
                        permission_stream_guard.validate_denied_invocation(
                            stream,
                            stderr,
                            return_code=0,
                            api_key="test-secret",
                            workspace=workspace,
                            agent_path=agent,
                            resource=resource,
                        )
                    self.assertEqual(str(caught.exception), "Kiro denied-write preview is invalid")

    @staticmethod
    def read_start_diagnostic_from_error(
        error: permission_stream_guard.StreamError,
    ) -> dict[str, Any]:
        marker = "read_start_diagnostic="
        message = str(error)
        if marker not in message:
            raise AssertionError("read-start diagnostic is missing")
        return json.loads(message.split(marker, 1)[1])

    def test_read_start_diagnostic_is_bounded_and_never_echoes_values(self) -> None:
        sensitive = "SENSITIVE-RAW-VALUE-MUST-NEVER-APPEAR"
        opaque_tool_id = "call_deadbeef-dead-beef-dead-deadbeefdead"
        with tempfile.TemporaryDirectory() as temporary:
            workspace, _, stream, stderr = self.fixture_workspace(temporary)
            events = self.complete_events(workspace)
            for event in events[2:5]:
                event["data"]["update"]["toolCallId"] = opaque_tool_id
            read_start = events[2]["data"]["update"]
            read_start["title"] = sensitive
            read_start["kind"] = sensitive
            read_start["rawInput"]["path"] = sensitive
            read_start["rawInput"]["offset"] = 424242
            read_start["rawInput"][sensitive] = sensitive
            read_start["locations"] = [{"path": sensitive, sensitive: sensitive}]
            self.write_stream(stream, events)

            with self.assertRaises(permission_stream_guard.StreamError) as caught:
                permission_stream_guard.validate_allowed_invocation(
                    stream,
                    stderr,
                    return_code=124,
                    api_key="test-secret",
                    workspace=workspace,
                )
            message = str(caught.exception)
            for forbidden in (
                sensitive,
                "424242",
                str(workspace),
                opaque_tool_id,
                self.SESSION_ID,
            ):
                self.assertNotIn(forbidden, message)
            self.assertLessEqual(
                len(message.encode("utf-8")),
                permission_stream_guard.MAX_READ_START_DIAGNOSTIC_BYTES + 256,
            )
            diagnostic = self.read_start_diagnostic_from_error(caught.exception)
            self.assertEqual(
                diagnostic["schema"],
                "pkstack-permission-read-start-diagnostic-v1",
            )
            start = diagnostic["start"]
            self.assertFalse(start["kind"]["matches_expected"])
            self.assertFalse(start["title"]["matches_expected"])
            self.assertEqual(
                start["raw_input"]["path"]["classification"],
                "other_string",
            )
            self.assertEqual(start["raw_input"]["unexpected_key_count"], 1)
            self.assertEqual(
                start["raw_input"]["offset"]["classification"],
                "other_positive_integer",
            )
            self.assertFalse(start["locations"]["matches_expected"])
            self.assertEqual(
                start["locations"]["first_path"]["classification"],
                "other_string",
            )
            expected_classes = {
                permission_stream_guard.FIXTURE_INPUT_PATH: "exact_relative",
                f"./{permission_stream_guard.FIXTURE_INPUT_PATH}": "dot_relative",
                str(workspace / permission_stream_guard.FIXTURE_INPUT_PATH): (
                    "exact_workspace_absolute"
                ),
                f"file://{workspace / permission_stream_guard.FIXTURE_INPUT_PATH}": (
                    "exact_workspace_file_uri"
                ),
            }
            for value, expected in expected_classes.items():
                self.assertEqual(
                    permission_stream_guard._diagnostic_path(value, workspace=workspace)[
                        "classification"
                    ],
                    expected,
                )

    def test_grep_input_diagnostic_is_bounded_and_never_echoes_values(self) -> None:
        sensitive = "SENSITIVE-GREP-VALUE-MUST-NEVER-APPEAR"
        opaque_tool_id = "call_feedface-feed-face-feed-feedfacefeed"
        with tempfile.TemporaryDirectory() as temporary:
            workspace, _, stream, stderr = self.fixture_workspace(temporary)
            events = self.complete_events(workspace)
            for event in events[5:8]:
                event["data"]["update"]["toolCallId"] = opaque_tool_id
            raw_input = events[5]["data"]["update"]["rawInput"]
            raw_input.pop("explanation")
            raw_input["caseSensitive"] = sensitive
            raw_input["includePattern"] = sensitive
            raw_input["query"] = sensitive
            raw_input[sensitive] = sensitive
            self.write_stream(stream, events)

            with self.assertRaises(permission_stream_guard.StreamError) as caught:
                permission_stream_guard.validate_allowed_invocation(
                    stream,
                    stderr,
                    return_code=124,
                    api_key="test-secret",
                    workspace=workspace,
                )
            message = str(caught.exception)
            for forbidden in (
                sensitive,
                "test-secret",
                str(workspace),
                opaque_tool_id,
                self.SESSION_ID,
            ):
                self.assertNotIn(forbidden, message)
            self.assertLessEqual(
                len(message.encode("utf-8")),
                permission_stream_guard.MAX_GREP_INPUT_DIAGNOSTIC_BYTES + 256,
            )
            diagnostic = json.loads(message.split("grep_input_diagnostic=", 1)[1])
            self.assertEqual(
                diagnostic["schema"],
                "pkstack-permission-grep-input-diagnostic-v1",
            )
            facts = diagnostic["raw_input"]
            self.assertEqual(facts["key_count"], 4)
            self.assertFalse(facts["expected_keys_present"]["explanation"])
            self.assertEqual(facts["unexpected_key_count"], 1)
            self.assertFalse(facts["case_sensitive"]["matches_expected"])
            self.assertEqual(facts["case_sensitive"]["type"], "string")
            self.assertTrue(facts["explanation"]["matches_validator_contract"])
            self.assertEqual(facts["explanation"]["type"], "null")
            self.assertEqual(facts["include_pattern"]["classification"], "other_string")
            self.assertFalse(facts["query"]["matches_expected"])
            self.assertEqual(facts["query"]["type"], "string")

    def test_write_start_preview_diagnostic_is_bounded_and_never_echoes_values(self) -> None:
        sensitive = "SENSITIVE-PREVIEW-VALUE-MUST-NEVER-APPEAR"
        large = sensitive * 1000
        with tempfile.TemporaryDirectory() as temporary:
            workspace, agent, stream, stderr = self.fixture_workspace(temporary)
            resource = permission_stream_guard.DENIED_RESOURCES[0]
            for denied in (False, True):
                with self.subTest(denied=denied):
                    events = self.complete_events(
                        workspace, denied_resource=resource if denied else None
                    )
                    start = events[2 if denied else 8]["data"]["update"]
                    start["_meta"]["kiro"]["preview"] = {
                        "file": f"file://{workspace}/{sensitive}",
                        "modifiedContent": {sensitive: large},
                        "originalContent": [large, "f" * 64],
                        large: sensitive,
                    }
                    self.write_stream(stream, events)
                    with self.assertRaises(permission_stream_guard.StreamError) as caught:
                        if denied:
                            permission_stream_guard.validate_denied_invocation(
                                stream,
                                stderr,
                                return_code=0,
                                api_key="test-secret",
                                workspace=workspace,
                                agent_path=agent,
                                resource=resource,
                            )
                        else:
                            permission_stream_guard.validate_allowed_invocation(
                                stream,
                                stderr,
                                return_code=0,
                                api_key="test-secret",
                                workspace=workspace,
                            )
                    message = str(caught.exception)
                    for forbidden in (
                        sensitive,
                        "f" * 64,
                        str(workspace),
                        self.SESSION_ID,
                        "test-secret",
                    ):
                        self.assertNotIn(forbidden, message)
                    raw = message.split("write_start_preview_diagnostic=", 1)[1]
                    self.assertLessEqual(
                        len(raw.encode("utf-8")),
                        permission_stream_guard.MAX_WRITE_START_PREVIEW_DIAGNOSTIC_BYTES,
                    )
                    diagnostic = json.loads(raw)
                    self.assertEqual(
                        diagnostic["schema"],
                        "pkstack-permission-write-start-preview-diagnostic-v1",
                    )
                    self.assertIs(diagnostic["denied"], denied)
                    facts = diagnostic["preview"]
                    self.assertEqual(facts["type"], "object")
                    self.assertTrue(facts["unexpected_keys_present"])
                    self.assertTrue(all(facts["expected_keys_present"].values()))
                    self.assertEqual(facts["file"]["classification"], "other_string")
                    self.assertEqual(
                        facts["modified_content"],
                        {"type": "object", "matches_expected": False},
                    )
                    self.assertEqual(
                        facts["original_content"],
                        {
                            "present": True,
                            "type": "array",
                            "matches_expected": False,
                            "is_empty": False,
                        },
                    )

    def test_write_start_preview_variants_remain_rejected_with_structural_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, agent, stream, stderr = self.fixture_workspace(temporary)
            resource = permission_stream_guard.DENIED_RESOURCES[0]
            valid = {
                "file": resource,
                "modifiedContent": permission_stream_guard.DENIED_WRITE_TEXT,
                "originalContent": f"PROTECTED_BASELINE {resource}\n",
            }
            cases = [
                ("wrong_original", {**valid, "originalContent": "UNTRUSTED_PREVIEW"}),
                ("empty_original", {**valid, "originalContent": ""}),
                ("null_original", {**valid, "originalContent": None}),
                ("dot_relative", {**valid, "file": f"./{resource}"}),
                ("exact_workspace_absolute", {**valid, "file": str(workspace / resource)}),
                ("exact_workspace_file_uri", {**valid, "file": f"file://{workspace / resource}"}),
                ("null", None),
                ("array", ["UNTRUSTED_PREVIEW"]),
                ("string", "UNTRUSTED_PREVIEW"),
            ]
            for case, preview in cases:
                with self.subTest(case=case):
                    events = self.complete_events(workspace, denied_resource=resource)
                    events[2]["data"]["update"]["_meta"]["kiro"]["preview"] = preview
                    self.write_stream(stream, events)
                    with self.assertRaises(permission_stream_guard.StreamError) as caught:
                        permission_stream_guard.validate_denied_invocation(
                            stream,
                            stderr,
                            return_code=0,
                            api_key="test-secret",
                            workspace=workspace,
                            agent_path=agent,
                            resource=resource,
                        )
                    message = str(caught.exception)
                    self.assertNotIn("UNTRUSTED_PREVIEW", message)
                    self.assertNotIn(str(workspace), message)
                    diagnostic = json.loads(message.split("write_start_preview_diagnostic=", 1)[1])
                    facts = diagnostic["preview"]
                    if case in {"null", "array", "string"}:
                        self.assertEqual(facts, {"type": case})
                    elif case.endswith("original"):
                        original = facts["original_content"]
                        self.assertTrue(original["present"])
                        self.assertEqual(original["is_empty"], case == "empty_original")
                        self.assertFalse(original["matches_expected"])
                        self.assertTrue(facts["expected_keys_present"]["originalContent"])
                    else:
                        self.assertEqual(facts["file"]["classification"], case)

    def test_denied_stream_rejects_policy_and_lifecycle_lookalikes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, agent, stream, stderr = self.fixture_workspace(temporary)
            resource = permission_stream_guard.DENIED_RESOURCES[0]
            baseline = self.complete_events(workspace, denied_resource=resource)

            def clone() -> list[dict[str, Any]]:
                return json.loads(json.dumps(baseline))

            malformed_streams: list[list[dict[str, Any]]] = []
            for mutation in ("missing", "extra", "resource", "rule"):
                events = clone()
                terminal = events[-3]["data"]["update"]
                denial = terminal["_meta"]["kiro"]["policyDenial"]
                if mutation == "missing":
                    denial.pop("matchedRule")
                elif mutation == "extra":
                    denial["unexpected"] = True
                elif mutation == "resource":
                    denial["resource"] = permission_stream_guard.DENIED_RESOURCES[1]
                else:
                    denial["matchedRule"]["match"] = [resource]
                malformed_streams.append(events)

            mismatched_id = clone()
            mismatched_id[-3]["data"]["update"]["toolCallId"] = self.tool_call_id(9)
            malformed_streams.append(mismatched_id)
            late_selection = clone()
            late_selection.insert(-2, late_selection[1])
            malformed_streams.append(late_selection)
            unknown_update = clone()
            unknown_update.insert(
                -1,
                self.envelope({"sessionUpdate": "command_execution", "status": "done"}),
            )
            malformed_streams.append(unknown_update)
            extra_tool = clone()
            extra_tool[-2:-2] = self.write_group(
                workspace,
                2,
                resource,
                permission_stream_guard.DENIED_WRITE_TEXT,
                denied=True,
                deny_patterns=json.loads(agent.read_text(encoding="utf-8"))["permissions"]["rules"][
                    3
                ]["match"],
            )
            malformed_streams.append(extra_tool)

            for events in malformed_streams:
                with (
                    self.subTest(events=events),
                    self.assertRaises(permission_stream_guard.StreamError),
                ):
                    self.write_stream(stream, events)
                    permission_stream_guard.validate_denied_invocation(
                        stream,
                        stderr,
                        return_code=124,
                        api_key="test-secret",
                        workspace=workspace,
                        agent_path=agent,
                        resource=resource,
                    )

    def test_allowed_stream_rejects_missing_reordered_or_denied_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, _, stream, stderr = self.fixture_workspace(temporary)
            baseline = self.complete_events(workspace)

            def clone() -> list[dict[str, Any]]:
                return json.loads(json.dumps(baseline))

            missing_write = clone()
            missing_id = self.tool_call_id(9)
            missing_write[:] = [
                event
                for event in missing_write
                if event.get("data", {}).get("update", {}).get("toolCallId") != missing_id
            ]
            wrong_order = clone()
            first_write = next(
                event
                for event in wrong_order
                if event.get("data", {}).get("update", {}).get("toolCallId") == self.tool_call_id(3)
            )
            first_write["data"]["update"]["rawInput"]["path"] = "wrong.txt"
            wrong_used_tools = clone()
            wrong_used_tools[-2]["data"]["update"]["_meta"]["kiro"]["promptTurnSummaries"][0][
                "usedTools"
            ].append("execute_bash")
            hidden_denial = clone()
            hidden_denial.insert(
                -1,
                self.envelope(
                    {
                        "sessionUpdate": "session_info_update",
                        "_meta": {"kiro": {"policyDenial": {"effect": "deny"}}},
                    }
                ),
            )
            nonempty_final = clone()
            nonempty_final[-1]["data"]["finalText"] = "done"
            unknown_original = clone()
            unknown_original[-3]["data"]["update"]["content"][0]["oldText"] = None

            for events in (
                missing_write,
                wrong_order,
                wrong_used_tools,
                hidden_denial,
                nonempty_final,
                unknown_original,
            ):
                with (
                    self.subTest(events=events),
                    self.assertRaises(permission_stream_guard.StreamError),
                ):
                    self.write_stream(stream, events)
                    permission_stream_guard.validate_allowed_invocation(
                        stream,
                        stderr,
                        return_code=124,
                        api_key="test-secret",
                        workspace=workspace,
                    )

    def test_invocation_bounds_fallback_and_secret_checks_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, agent, stream, stderr = self.fixture_workspace(temporary)
            resource = permission_stream_guard.DENIED_RESOURCES[0]
            events = self.complete_events(workspace, denied_resource=resource)
            self.write_stream(stream, events)
            common = {
                "stream_path": stream,
                "stderr_path": stderr,
                "api_key": "test-secret",
                "workspace": workspace,
                "agent_path": agent,
                "resource": resource,
            }
            with self.assertRaises(permission_stream_guard.StreamError):
                permission_stream_guard.validate_denied_invocation(return_code=1, **common)
            stream.chmod(0o644)
            with self.assertRaises(permission_stream_guard.StreamError):
                permission_stream_guard.validate_denied_invocation(return_code=0, **common)
            stream.chmod(0o600)
            stderr.write_text('not found, using "default"', encoding="utf-8")
            with self.assertRaises(permission_stream_guard.StreamError):
                permission_stream_guard.validate_denied_invocation(return_code=0, **common)
            stderr.write_text("test-secret", encoding="utf-8")
            with self.assertRaises(permission_stream_guard.StreamError):
                permission_stream_guard.validate_denied_invocation(return_code=0, **common)
            stderr.write_text("", encoding="utf-8")
            with self.assertRaises(permission_stream_guard.StreamError):
                permission_stream_guard.validate_denied_invocation(
                    return_code=0,
                    **(common | {"resource": "unapproved/protected.txt"}),
                )


class GitControlBoundaryTests(unittest.TestCase):
    @staticmethod
    def make_repo(sandbox: Path) -> tuple[Path, str]:
        root = sandbox / "repo"
        (root / ".kiro/agents").mkdir(parents=True)
        (root / ".kiro/agents/base.json").write_text("{}\n", encoding="utf-8")
        (root / "README.md").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=PKStack Test",
                "-c",
                "user.email=pkstack@example.invalid",
                "commit",
                "-qm",
                "base",
            ],
            cwd=root,
            check=True,
        )
        base_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        return root, base_sha

    @staticmethod
    def record_model_boundary(root: Path, base_sha: str, state_root: Path) -> None:
        shutil.rmtree(root / ".kiro")
        guard._record_git_state(root, base_sha, state_root)

    def test_close_refuses_all_model_visible_git_control_changes_before_git(self) -> None:
        _, policy = guard.load_policy(ROOT / ".github/pkstack-maintenance-policy.json")

        def mutate_config(root: Path) -> None:
            with (root / ".git/config").open("a", encoding="utf-8") as stream:
                stream.write("\n[core]\n\tfsmonitor = planted\n")

        def mutate_replace_ref(root: Path) -> None:
            replacement = root / ".git/refs/replace" / ("a" * 40)
            replacement.parent.mkdir()
            replacement.write_text(f"{'b' * 40}\n", encoding="ascii")

        mutations = {
            "config": mutate_config,
            "hooks": lambda root: (root / ".git/hooks/post-index-change").write_text(
                "#!/bin/sh\nexit 0\n", encoding="utf-8"
            ),
            "info": lambda root: (root / ".git/info/planted").write_text(
                "planted\n", encoding="utf-8"
            ),
            "index": lambda root: (root / ".git/index").write_bytes(
                (root / ".git/index").read_bytes() + b"planted"
            ),
            "HEAD": lambda root: (root / ".git/HEAD").write_text(f"{'a' * 40}\n", encoding="ascii"),
            "replacement-ref": mutate_replace_ref,
            "packed-refs": lambda root: (root / ".git/packed-refs").write_text(
                f"{'a' * 40} refs/replace/{'b' * 40}\n", encoding="ascii"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                sandbox = Path(temporary)
                root, base_sha = self.make_repo(sandbox)
                state_root = sandbox / "git-state"
                self.record_model_boundary(root, base_sha, state_root)
                try:
                    mutate(root)
                    with mock.patch.object(
                        guard,
                        "_git_run",
                        side_effect=AssertionError("Git ran before control-state rejection"),
                    ) as git_run:
                        with self.assertRaisesRegex(guard.GuardError, "Git control metadata"):
                            guard.close_attempt(root, base_sha, policy, state_root)
                        git_run.assert_not_called()
                finally:
                    guard._remove_git_state(root, state_root)

    def test_close_rejects_skip_worktree_and_assume_unchanged_index_attacks(self) -> None:
        _, policy = guard.load_policy(ROOT / ".github/pkstack-maintenance-policy.json")
        for flag in ("--skip-worktree", "--assume-unchanged"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as temporary:
                sandbox = Path(temporary)
                root, base_sha = self.make_repo(sandbox)
                state_root = sandbox / "git-state"
                self.record_model_boundary(root, base_sha, state_root)
                subprocess.run(["git", "update-index", flag, "README.md"], cwd=root, check=True)
                (root / "README.md").write_text("protected mutation\n", encoding="utf-8")
                with mock.patch.object(
                    guard,
                    "_git_run",
                    side_effect=AssertionError("Git ran before index-state rejection"),
                ) as git_run:
                    with self.assertRaisesRegex(guard.GuardError, "Git control metadata"):
                        guard.close_attempt(root, base_sha, policy, state_root)
                    git_run.assert_not_called()
                guard._remove_git_state(root, state_root)

    def test_trusted_git_disables_repo_and_ambient_executable_config(self) -> None:
        _, policy = guard.load_policy(ROOT / ".github/pkstack-maintenance-policy.json")
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            root, base_sha = self.make_repo(sandbox)
            tripwire = root / ".git/hooks/post-index-change"
            tripwire.write_text(
                "#!/bin/sh\nprintf executed >.git/pkstack-tripwire-executed\nexit 1\n",
                encoding="utf-8",
            )
            tripwire.chmod(0o700)
            subprocess.run(["git", "config", "core.hooksPath", "hooks"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "core.fsmonitor", ".git/hooks/post-index-change"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "diff.external", ".git/hooks/post-index-change"],
                cwd=root,
                check=True,
            )
            global_config = sandbox / "hostile-global-config"
            global_config.write_text(
                "[core]\n\thooksPath = hooks\n\tfsmonitor = .git/hooks/post-index-change\n"
                "[diff]\n\texternal = .git/hooks/post-index-change\n",
                encoding="utf-8",
            )
            state_root = sandbox / "git-state"
            self.record_model_boundary(root, base_sha, state_root)
            recorded = guard._read_git_state(root, base_sha, state_root)["snapshot"]
            self.assertEqual(
                recorded["targets"]["config"]["sha256"],
                hashlib.sha256((root / ".git/config").read_bytes()).hexdigest(),
            )
            self.assertEqual(recorded["targets"]["config.worktree"], {"kind": "absent"})
            for target in ("hooks", "info", "refs"):
                self.assertEqual(recorded["targets"][target]["kind"], "directory")
                for entry in recorded["targets"][target]["entries"]:
                    if entry["entry"]["kind"] == "file":
                        self.assertRegex(entry["entry"]["sha256"], r"^[0-9a-f]{64}$")
            hostile_environment = {
                "GIT_CONFIG_GLOBAL": str(global_config),
                "GIT_CONFIG_SYSTEM": str(global_config),
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.hooksPath",
                "GIT_CONFIG_VALUE_0": "hooks",
                "GIT_EXTERNAL_DIFF": str(tripwire),
            }
            with mock.patch.dict(os.environ, hostile_environment, clear=False):
                guard.close_attempt(root, base_sha, policy, state_root)
            self.assertFalse((root / ".git/pkstack-tripwire-executed").exists())
            self.assertTrue(state_root.exists())
            guard._read_git_state(root, base_sha, state_root, phase="open")
            guard.finalize_git_state(root, base_sha, state_root)
            self.assertFalse(state_root.exists())
            self.assertTrue((root / ".kiro/agents/base.json").is_file())

    def test_external_finalizer_blocks_clean_filter_and_textconv_execution(self) -> None:
        _, policy = guard.load_policy(ROOT / ".github/pkstack-maintenance-policy.json")
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            root, _ = self.make_repo(sandbox)
            target = root / "powers/pkstack/README.md"
            target.parent.mkdir(parents=True)
            target.write_text("base\n", encoding="utf-8")
            (root / ".gitattributes").write_text(
                "powers/pkstack/README.md filter=trip diff=trip\n", encoding="utf-8"
            )
            subprocess.run(
                ["git", "add", ".gitattributes", "powers/pkstack/README.md"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=PKStack Test",
                    "-c",
                    "user.email=pkstack@example.invalid",
                    "commit",
                    "-qm",
                    "attributes",
                ],
                cwd=root,
                check=True,
            )
            base_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            marker = sandbox / "filter-or-textconv-executed"
            tripwire = sandbox / "git-driver.sh"
            tripwire.write_text(
                "#!/bin/sh\n"
                f"printf '%s\\n' \"$1\" >>{shlex.quote(str(marker))}\n"
                'if [ "$1" = textconv ]; then cat "$2"; else cat; fi\n',
                encoding="utf-8",
            )
            tripwire.chmod(0o700)
            subprocess.run(
                ["git", "config", "filter.trip.clean", f"{tripwire} clean"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "diff.trip.textconv", f"{tripwire} textconv"],
                cwd=root,
                check=True,
            )

            # Prove that the planted local drivers are genuinely executable by
            # ordinary Git before testing the trusted finalizer isolation.
            target.write_text("raw hostile path\n", encoding="utf-8")
            subprocess.run(
                ["git", "diff", "--", "powers/pkstack/README.md"],
                cwd=root,
                check=True,
                stdout=subprocess.DEVNULL,
            )
            subprocess.run(["git", "add", "powers/pkstack/README.md"], cwd=root, check=True)
            self.assertIn("textconv", marker.read_text(encoding="utf-8"))
            self.assertIn("clean", marker.read_text(encoding="utf-8"))
            subprocess.run(
                ["git", "reset", "-q", "HEAD", "--", "powers/pkstack/README.md"],
                cwd=root,
                check=True,
            )
            target.write_text("base\n", encoding="utf-8")
            marker.unlink()

            state_root = sandbox / "git-state"
            self.record_model_boundary(root, base_sha, state_root)
            original_index = hashlib.sha256((root / ".git/index").read_bytes()).hexdigest()
            target.write_text("candidate\n", encoding="utf-8")
            guard.close_attempt(root, base_sha, policy, state_root)
            self.assertFalse(marker.exists())
            self.assertEqual(
                hashlib.sha256((root / ".git/index").read_bytes()).hexdigest(),
                original_index,
            )
            self.assertNotEqual(
                hashlib.sha256((state_root / "index").read_bytes()).hexdigest(),
                guard._read_git_state(root, base_sha, state_root, phase="open")[
                    "trusted_index_sha256"
                ],
            )
            guard.finalize_git_state(root, base_sha, state_root)

    def test_trusted_git_wrapper_pins_config_and_no_ext_diff(self) -> None:
        completed = subprocess.CompletedProcess(args=(), returncode=0, stdout=b"", stderr=b"")
        with mock.patch.object(guard.subprocess, "run", return_value=completed) as run:
            guard._git_run(
                Path("/tmp"),
                "diff",
                "--name-only",
                env={
                    "PATH": os.environ.get("PATH", ""),
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "core.hooksPath",
                    "GIT_CONFIG_VALUE_0": "hooks",
                },
            )
        command = run.call_args.args[0]
        environment = run.call_args.kwargs["env"]
        self.assertIn("--no-ext-diff", command)
        self.assertIn("--no-textconv", command)
        for setting in (
            "core.hooksPath=/dev/null",
            "core.fsmonitor=false",
            "diff.external=",
        ):
            self.assertIn(setting, command)
        self.assertEqual(environment["GIT_CONFIG_GLOBAL"], "/dev/null")
        self.assertEqual(environment["GIT_CONFIG_SYSTEM"], "/dev/null")
        self.assertEqual(environment["GIT_CONFIG_NOSYSTEM"], "1")
        self.assertEqual(environment["GIT_EXTERNAL_DIFF"], "")
        self.assertEqual(environment["GIT_NO_REPLACE_OBJECTS"], "1")
        self.assertEqual(environment["GIT_CONFIG_VALUE_0"], "/dev/null")

    def test_git_control_snapshot_rejects_unsafe_and_racing_entries(self) -> None:
        unsafe_mutations = {
            "symlink": lambda root, sandbox: (root / ".git/hooks/unsafe").symlink_to(
                sandbox / "outside"
            ),
            "hardlink": lambda root, sandbox: os.link(
                root / ".git/config", root / ".git/hooks/unsafe"
            ),
            "oversized": lambda root, sandbox: (root / ".git/info/oversized").write_bytes(
                b"x" * (guard.GIT_CONTROL_ENTRY_MAX_BYTES + 1)
            ),
        }
        for label, mutate in unsafe_mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                sandbox = Path(temporary)
                root, base_sha = self.make_repo(sandbox)
                mutate(root, sandbox)
                with self.assertRaises(guard.GuardError):
                    guard._record_git_state(root, base_sha, sandbox / "git-state")

        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            root, base_sha = self.make_repo(sandbox)
            with self.assertRaisesRegex(guard.GuardError, "outside the model-visible checkout"):
                guard._record_git_state(root, base_sha, root / "git-state")

        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            root, _ = self.make_repo(sandbox)
            config = root / ".git/config"
            original_read = guard.os.read
            mutated = False

            def racing_read(descriptor: int, count: int) -> bytes:
                nonlocal mutated
                chunk = original_read(descriptor, count)
                if not mutated:
                    with config.open("ab") as stream:
                        stream.write(b"\n# raced\n")
                    mutated = True
                return chunk

            with (
                mock.patch.object(guard.os, "read", side_effect=racing_read),
                self.assertRaisesRegex(guard.GuardError, "changed while hashing"),
            ):
                guard._snapshot_git_controls(root)


class DetectorTests(unittest.TestCase):
    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "detector.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return guard.validate_detector(path)

    def test_large_detector_is_reviewed_in_complete_bounded_batches(self) -> None:
        payload = drift_detector_fixture()
        files = []
        # Exceeds both the old 256 KiB patch cap and 1 MiB detector cap.
        for number in range(40):
            file = comparison_file_fixture(
                path=f"skills/example-{number:03d}/SKILL.md",
                previous_path=None,
                status="added",
                tree_sha_verified=True,
            )
            patch = "@@ -0,0 +1 @@\n+" + "read me as data " * (60_000 if number == 0 else 6800)
            file.update(patch=patch, patch_bytes=len(patch.encode()))
            files.append(file)
        set_comparison_files(payload, files)
        self.assertGreater(len(json.dumps(payload).encode()), 1024 * 1024)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            detector = root / "detector.json"
            detector.write_text(json.dumps(payload), encoding="utf-8")
            before = detector.read_bytes()
            output = root / "review"
            result = guard.prepare_upstream_review(detector, output)
            index = json.loads((output / "upstream-delta.json").read_bytes())
            self.assertEqual(index["artifact_type"], "upstream-review-index")
            comparison = index["sources"][0]["comparison"]
            self.assertNotIn("files", comparison)
            self.assertLess((output / "upstream-delta.json").stat().st_size, 64 * 1024)
            reconstructed = []
            for entry in comparison["review_batches"]:
                raw = (output / entry["file"]).read_bytes()
                self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(entry["bytes"], len(raw))
                self.assertLessEqual(len(raw), guard.UPSTREAM_REVIEW_BATCH_MAX_BYTES)
                batch = json.loads(raw)
                self.assertTrue(batch["untrusted"])
                self.assertEqual(batch["inventory_sha256"], comparison["inventory_sha256"])
                self.assertEqual(batch["prior"], payload["sources"][0]["pinned"])
                self.assertEqual(batch["new"], payload["sources"][0]["current"])
                self.assertLessEqual(len(batch["files"]), guard.UPSTREAM_REVIEW_BATCH_FILES)
                self.assertLessEqual(
                    sum(item["patch_bytes"] for item in batch["files"]),
                    guard.UPSTREAM_REVIEW_BATCH_PATCH_BYTES,
                )
                reconstructed.extend(batch["files"])
            self.assertEqual(reconstructed, files)
            self.assertEqual(result["batch_count"], len(comparison["review_batches"]))
            self.assertEqual(detector.read_bytes(), before)
            # A review index cannot be submitted as detector/acceptance proof.
            with self.assertRaises(guard.GuardError):
                guard.validate_detector(output / "upstream-delta.json")
            with self.assertRaises(FileExistsError):
                guard.prepare_upstream_review(detector, output)
            bad = json.loads(before)
            bad["sources"][0]["comparison"]["files"][-1]["patch"] += "\n+unreported"
            detector.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.prepare_upstream_review(detector, root / "invalid")
            self.assertFalse((root / "invalid").exists())

    def test_review_batches_preserve_no_patch_records_and_source_separation(self) -> None:
        payload = drift_detector_fixture()
        mode_change = comparison_file_fixture(
            path="script.md", previous_path=None, status="modified", tree_sha_verified=True
        )
        mode_change.update(
            additions=0,
            deletions=0,
            changes=0,
            patch=None,
            patch_bytes=0,
            no_patch=True,
            content_class="exact-blob-identity",
            reviewability="exact-blob-mode-change",
            old_identity=tree_identity("e" * 40, mode="100644"),
            new_identity=tree_identity("e" * 40, mode="100755"),
        )
        set_comparison_files(payload, [mode_change])
        add_detector_source(payload, source_id="okf-skills", drift=True)
        add_detector_source(payload, source_id="current-source", drift=False)
        validated = self.validate(payload)
        documents = guard._upstream_review_documents(validated)
        index = json.loads(documents["upstream-delta.json"])
        for source, original in zip(index["sources"], payload["sources"], strict=True):
            files = []
            for entry in source["comparison"]["review_batches"]:
                batch = json.loads(documents[entry["file"]])
                self.assertEqual(batch["source_id"], original["id"])
                self.assertEqual(batch["repository"], original["repository"])
                files.extend(batch["files"])
            self.assertEqual(files, original["comparison"]["files"])
        self.assertEqual(documents, guard._upstream_review_documents(validated))

    def test_detector_execution_errors_remain_failures_with_safe_diagnostics(self) -> None:
        cases = (
            (
                "UpstreamError",
                "GitHub comparison file patch exceeds the 65536-byte limit",
                "GitHub comparison file patch exceeds the 65536-byte limit",
            ),
            (
                "UpstreamError",
                "GitHub API response exceeds the 1048576-byte limit",
                "GitHub API response exceeds the 1048576-byte limit",
            ),
            (
                "UpstreamError",
                "GitHub comparison file without a patch must report zero additions and deletions",
                "GitHub comparison file without a patch must report zero additions and deletions",
            ),
            (
                "UpstreamError",
                "GitHub comparison file patch exceeds the 1048576-byte limit",
                "GitHub comparison file patch exceeds the 1048576-byte limit",
            ),
            ("UpstreamError", "GitHub API returned HTTP 403", "GitHub API returned HTTP 403"),
            (
                "UpstreamError",
                "upstream network time budget was exhausted",
                "upstream network time budget was exhausted",
            ),
            (
                "UpstreamError",
                "upstream comparison patches exceed the 262144-byte limit",
                "upstream comparison patches exceed the 262144-byte limit",
            ),
            ("OSError", "private path or credential sentinel", "OSError"),
            ("ValueError", "private path or credential sentinel", "ValueError"),
        )
        for error_type, message, expected in cases:
            with self.subTest(error_type=error_type, message=message):
                with self.assertRaises(guard.GuardError) as caught:
                    self.validate({"ok": False, "error": message, "error_type": error_type})
                self.assertIn("detector execution failed", str(caught.exception))
                self.assertIn(expected, str(caught.exception))
                self.assertNotIn("sentinel", str(caught.exception))

    def test_detector_error_diagnostics_do_not_echo_untrusted_values(self) -> None:
        for payload in (
            {"ok": False, "error": "secret", "error_type": "secret"},
            {
                "ok": False,
                "error": "GitHub API returned HTTP 403\nsecret",
                "error_type": "UpstreamError",
            },
            {
                "ok": False,
                "error": "upstream comparison patches exceed the 262144-byte limit\nsecret",
                "error_type": "UpstreamError",
            },
            {"ok": False, "error": ["secret"], "error_type": "UpstreamError"},
            {"ok": 0, "error": "secret", "error_type": "UpstreamError"},
            {"ok": False, "error": "secret", "error_type": ["secret"]},
            {"ok": False, "error": "secret", "error_type": "UpstreamError", "extra": "secret"},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(guard.GuardError) as caught:
                    self.validate(payload)
                self.assertNotIn("secret", str(caught.exception))

    def validate_proposal(
        self,
        detector: dict[str, Any],
        proposal: dict[str, Any],
        *,
        extra_pending_source_id: str | None = None,
        controller_source_id: str | None = None,
    ) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            detector_path = root / "detector.json"
            proposal_path = root / "proposal.json"
            ledger_path = root / "maintenance/upstream-reviews.json"
            ledger_path.parent.mkdir(parents=True)
            detector_path.write_text(json.dumps(detector), encoding="utf-8")
            proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
            ledger_path.write_text(
                json.dumps(review_ledger_fixture(detector)),
                encoding="utf-8",
            )
            selected_source_id = proposal["source_id"]
            for source in detector["sources"]:
                provenance_path = root / source["provenance_path"]
                provenance_path.parent.mkdir(parents=True, exist_ok=True)
                markers = accepted_marker_lines(detector, source_id=source["id"])
                if source["id"] == selected_source_id:
                    markers.append(pending_marker_line(detector, source_id=source["id"]))
                if source["id"] == extra_pending_source_id:
                    markers.append(pending_marker_line(detector, source_id=source["id"]))
                provenance_path.write_text(
                    "# Provenance\n\n" + "\n".join(markers) + "\n",
                    encoding="utf-8",
                )
            return guard.validate_proposal(root, detector_path, proposal_path, controller_source_id)

    def validate_serialized(
        self,
        before: dict[str, Any],
        after: dict[str, Any],
        *,
        mutate_deferred_provenance: bool = False,
        mutate_deferred_ledger: bool = False,
        controller_source_id: str | None = None,
    ) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before_path = root / "before.json"
            after_path = root / "after.json"
            before_path.write_text(json.dumps(before), encoding="utf-8")
            after_path.write_text(json.dumps(after), encoding="utf-8")
            ledger_path = root / "maintenance/upstream-reviews.json"
            ledger_path.parent.mkdir(parents=True)
            ledger_path.write_text(json.dumps(review_ledger_fixture(before)), encoding="utf-8")
            for source in before["sources"]:
                provenance_path = root / source["provenance_path"]
                provenance_path.parent.mkdir(parents=True, exist_ok=True)
                provenance_path.write_text(
                    "# Provenance\n\n"
                    + "\n".join(accepted_marker_lines(before, source_id=source["id"]))
                    + "\n",
                    encoding="utf-8",
                )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=PKStack Test",
                    "-c",
                    "user.email=pkstack@example.invalid",
                    "commit",
                    "-qm",
                    "before serialized acceptance",
                ],
                cwd=root,
                check=True,
            )
            base_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            ledger_path = root / "maintenance/upstream-reviews.json"
            ledger_path.parent.mkdir(parents=True, exist_ok=True)
            ledger_path.write_text(
                json.dumps(review_ledger_fixture(after)),
                encoding="utf-8",
            )
            if mutate_deferred_ledger:
                ledger = json.loads(ledger_path.read_text())
                ledger["sources"][0]["genesis"]["commit"] = "9" * 40
                ledger_path.write_text(json.dumps(ledger))
            for source in after["sources"]:
                provenance_path = root / source["provenance_path"]
                provenance_path.parent.mkdir(parents=True, exist_ok=True)
                provenance_path.write_text(
                    "# Provenance\n\n"
                    + "\n".join(accepted_marker_lines(after, source_id=source["id"]))
                    + "\n",
                    encoding="utf-8",
                )
            if mutate_deferred_provenance:
                selected_source_id = min(
                    source["id"] for source in before["sources"] if source["drift"]
                )
                deferred = next(
                    source for source in after["sources"] if source["id"] != selected_source_id
                )
                with (root / deferred["provenance_path"]).open("a", encoding="utf-8") as stream:
                    stream.write("Deferred prose changed.\n")
            return guard.validate_serialized_acceptance(
                root,
                base_sha,
                before_path,
                after_path,
                controller_source_id,
            )

    def test_multiple_drift_sources_are_sorted_for_serialized_selection(self) -> None:
        payload = drift_detector_fixture()
        add_detector_source(payload, source_id="alpha-okf", drift=True)

        validated = self.validate(payload)

        self.assertEqual(
            validated["validated_drift_sources"],
            [
                {"source_id": "alpha-okf", "expected_head": "5" * 40},
                {"source_id": "cursor-pstack", "expected_head": "c" * 40},
            ],
        )
        self.assertEqual(validated["validated_drift_heads"], ["5" * 40, "c" * 40])

    def test_detector_source_capacity_accepts_32_and_rejects_33(self) -> None:
        payload = detector_fixture()
        for index in range(31):
            add_detector_source(payload, source_id=f"capacity-{index}", drift=False)
        self.assertTrue(self.validate(payload)["ok"])
        add_detector_source(payload, source_id="capacity-overflow", drift=False)
        with self.assertRaisesRegex(guard.GuardError, "bounded non-empty source list"):
            self.validate(payload)

    def test_source_ids_match_the_bounded_controller_contract(self) -> None:
        for source_id in ("-alpha", "alpha-", "alpha--okf", "Alpha", "a" * 65):
            with self.subTest(source_id=source_id):
                payload = detector_fixture()
                payload["sources"][0]["id"] = source_id
                with self.assertRaisesRegex(guard.GuardError, "source id is invalid"):
                    self.validate(payload)

    def test_invalid_source_parity_is_typed_and_can_trigger_parity_only_repair(self) -> None:
        payload = detector_fixture()
        source = payload["sources"][0]
        source["ok"] = False
        source["source_parity"] = {
            "ok": False,
            "candidate_ready": False,
            "artifact_type": "unknown",
            "status": "invalid",
            "path": source["parity_path"],
            "errors": ["Parity artifact is unavailable."],
            "pinned_resource_count": 0,
            "current_resource_count": 0,
            "classified_resource_count": 0,
        }
        payload["ok"] = False

        self.assertEqual(self.validate(payload)["validated_drift_sources"], [])

        source["source_parity"]["errors"] = []
        with self.assertRaisesRegex(guard.GuardError, "errors are not bounded"):
            self.validate(payload)

        payload = detector_fixture()
        source = payload["sources"][0]
        source["source_parity"]["candidate_ready"] = True
        source["source_parity"]["status"] = "candidate-ready"
        with self.assertRaisesRegex(guard.GuardError, "non-drifting upstream"):
            self.validate(payload)

    def test_proposal_must_name_controller_selected_drift_source(self) -> None:
        payload = drift_detector_fixture()
        add_detector_source(payload, source_id="alpha-okf", drift=True)

        selected = proposal_fixture(payload)
        self.assertEqual(selected["source_id"], "alpha-okf")
        self.assertEqual(self.validate_proposal(payload, selected)["source_id"], "alpha-okf")

        wrong = proposal_fixture(payload, source_id="cursor-pstack")
        with self.assertRaisesRegex(guard.GuardError, "controller-selected"):
            self.validate_proposal(payload, wrong, controller_source_id="alpha-okf")
        self.assertEqual(
            self.validate_proposal(payload, wrong, controller_source_id="cursor-pstack")[
                "source_id"
            ],
            "cursor-pstack",
        )

        with self.assertRaisesRegex(guard.GuardError, "marker count"):
            self.validate_proposal(
                payload,
                selected,
                extra_pending_source_id="cursor-pstack",
            )

    def test_serialized_acceptance_advances_only_selected_source(self) -> None:
        before = drift_detector_fixture()
        add_detector_source(before, source_id="alpha-okf", drift=True)
        after = accepted_detector_fixture(before, selected_source_id="alpha-okf")

        result = self.validate_serialized(before, after)

        self.assertEqual(result["source_id"], "alpha-okf")
        self.assertEqual(result["initial_drift_count"], 2)
        self.assertEqual(result["remaining_drift_count"], 1)
        with self.assertRaisesRegex(guard.GuardError, "deferred review ledger"):
            self.validate_serialized(before, after, mutate_deferred_ledger=True)

        after["sources"][0]["source_parity"]["pinned_resource_count"] = 2
        with self.assertRaisesRegex(guard.GuardError, "deferred upstream source"):
            self.validate_serialized(before, after)

        after = accepted_detector_fixture(before, selected_source_id="alpha-okf")
        with self.assertRaisesRegex(guard.GuardError, "modified deferred upstream provenance"):
            self.validate_serialized(
                before,
                after,
                mutate_deferred_provenance=True,
            )

    def test_serialized_acceptance_binds_latest_transition_to_selected_inventory(self) -> None:
        before = drift_detector_fixture()
        add_detector_source(before, source_id="alpha-okf", drift=True)
        after = accepted_detector_fixture(before, selected_source_id="alpha-okf")
        selected = next(source for source in after["sources"] if source["id"] == "alpha-okf")
        selected["review_reproof"]["transitions"][0]["inventory_sha256"] = "f" * 64

        with self.assertRaisesRegex(guard.GuardError, "not detector-bound"):
            self.validate_serialized(before, after)

    def test_serialized_acceptance_obeys_controller_choice_not_lexical_order(self) -> None:
        before = drift_detector_fixture()
        add_detector_source(before, source_id="alpha-okf", drift=True)
        after = accepted_detector_fixture(before, selected_source_id="cursor-pstack")
        result = self.validate_serialized(before, after, controller_source_id="cursor-pstack")
        self.assertEqual(result["source_id"], "cursor-pstack")
        with self.assertRaisesRegex(guard.GuardError, "controller-selected"):
            self.validate_serialized(before, after, controller_source_id="alpha-okf")

    def test_zero_one_and_multi_transition_reproof_shapes(self) -> None:
        for count in (0, 1, 7, 33, guard.REVIEW_TRANSITION_MAX):
            validated = self.validate(detector_fixture(transition_count=count))
            self.assertEqual(validated["validated_drift_heads"], [])

        with self.assertRaises(guard.GuardError):
            self.validate(detector_fixture(transition_count=guard.REVIEW_TRANSITION_MAX + 1))

    def test_arbitrary_ok_false_and_typed_boolean_are_rejected(self) -> None:
        payload = detector_fixture()
        payload.pop("sources")
        payload["ok"] = False
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

        payload = detector_fixture()
        payload["sources"][0]["drift"] = 1
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_inventory_counts_must_be_exact(self) -> None:
        payload = detector_fixture()
        payload["sources"][0]["comparison"]["path_count"] = 1
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_cross_boundary_rename_out_is_the_only_unverified_tree_sha(self) -> None:
        payload = drift_detector_fixture()
        rename_out = comparison_file_fixture(
            path=None,
            previous_path="old.md",
            status="renamed",
            tree_sha_verified=False,
        )
        set_comparison_files(payload, [rename_out])
        self.assertEqual(self.validate(payload)["validated_drift_heads"], ["c" * 40])

        rename_out["status"] = "removed"
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_rename_in_and_copy_require_verified_current_tree_sha(self) -> None:
        for file in (
            comparison_file_fixture(
                path="new.md",
                previous_path=None,
                status="renamed",
                tree_sha_verified=True,
            ),
            comparison_file_fixture(
                path="copied.md",
                previous_path=None,
                status="copied",
                tree_sha_verified=True,
            ),
        ):
            payload = drift_detector_fixture()
            set_comparison_files(payload, [file])
            self.validate(payload)
            file["tree_sha_verified"] = False
            with self.assertRaises(guard.GuardError):
                self.validate(payload)

    def test_comparison_may_omit_changes_wholly_outside_source_subtree(self) -> None:
        payload = drift_detector_fixture()
        set_comparison_files(payload, [])
        source = payload["sources"][0]
        source["current"]["subtree_sha"] = source["pinned"]["subtree_sha"]
        source["drift"] = False
        source["ok"] = True
        payload["ok"] = True
        source["source_parity"]["candidate_ready"] = False
        source["source_parity"]["status"] = "accepted-baseline"
        self.assertEqual(self.validate(payload)["validated_drift_heads"], [])

    def test_patch_body_and_review_constraints_are_recomputed(self) -> None:
        payload = drift_detector_fixture()
        self.validate(payload)

        file = payload["sources"][0]["comparison"]["files"][0]
        file["patch"] = "@@ -0,0 +1 @@\n+new\n+hidden"
        file["patch_bytes"] = len(file["patch"].encode("utf-8"))
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_exact_blob_identities_modes_and_inventory_are_independently_bound(self) -> None:
        payload = drift_detector_fixture()
        file = payload["sources"][0]["comparison"]["files"][0]
        file["new_identity"]["mode"] = "100755"
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

        for entry_type, mode in (("commit", "160000"), ("blob", "120000")):
            payload = drift_detector_fixture()
            file = payload["sources"][0]["comparison"]["files"][0]
            file["new_identity"].update(type=entry_type, mode=mode)
            set_comparison_files(payload, [file])
            with self.assertRaises(guard.GuardError):
                self.validate(payload)

    def test_exact_blob_rename_and_mode_only_changes_are_reviewable(self) -> None:
        rename = comparison_file_fixture(
            path="new.md",
            previous_path="old.md",
            status="renamed",
            tree_sha_verified=True,
        )
        rename.update(
            additions=0,
            deletions=0,
            changes=0,
            patch=None,
            patch_bytes=0,
            no_patch=True,
            content_class="exact-blob-identity",
            reviewability="exact-blob-pure-rename",
            old_identity=tree_identity("e" * 40),
            new_identity=tree_identity("e" * 40),
        )
        payload = drift_detector_fixture()
        set_comparison_files(payload, [rename])
        self.validate(payload)

        mode_change = comparison_file_fixture(
            path="script.md",
            previous_path=None,
            status="modified",
            tree_sha_verified=True,
        )
        mode_change.update(
            additions=0,
            deletions=0,
            changes=0,
            patch=None,
            patch_bytes=0,
            no_patch=True,
            content_class="exact-blob-identity",
            reviewability="exact-blob-mode-change",
            old_identity=tree_identity("e" * 40, mode="100644"),
            new_identity=tree_identity("e" * 40, mode="100755"),
        )
        payload = drift_detector_fixture()
        set_comparison_files(payload, [mode_change])
        self.validate(payload)

        mode_change["new_identity"]["mode"] = "100644"
        set_comparison_files(payload, [mode_change])
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

        payload = drift_detector_fixture()
        payload["sources"][0]["comparison"]["review_constraints"]["unavailable_binary_paths"] = [
            "README.md"
        ]
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_unavailable_image_requires_disposition_b(self) -> None:
        payload = drift_detector_fixture()
        unavailable = {
            "path": "assets/logo.png",
            "previous_path": None,
            "status": "added",
            "sha": "e" * 40,
            "additions": 0,
            "deletions": 0,
            "changes": 0,
            "patch": None,
            "patch_bytes": 0,
            "no_patch": True,
            "content_class": "binary-or-patch-unavailable",
            "reviewability": "unavailable-nonsemantic-image",
            "old_identity": None,
            "new_identity": tree_identity("e" * 40),
            "tree_sha_verified": True,
        }
        set_comparison_files(payload, [unavailable])
        self.validate(payload)
        proposal = proposal_fixture(payload)
        self.assertEqual(self.validate_proposal(payload, proposal)["disposition_count"], 1)

        proposal["dispositions"][0]["disposition"] = "A"
        with self.assertRaises(guard.GuardError):
            self.validate_proposal(payload, proposal)

        unavailable["path"] = "skills/evil.png"
        set_comparison_files(payload, [unavailable])
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_retry_cleanup_preserves_accepted_marker_prefix_and_authored_prose(self) -> None:
        payload = drift_detector_fixture(transition_count=1)
        accepted = accepted_marker_lines(payload)
        self.assertEqual(len(accepted), 1)
        pending = pending_marker_line(payload)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ledger = root / "maintenance/upstream-reviews.json"
            provenance = root / "powers/pkstack/provenance/provenance.md"
            detector_path = root / "detector.json"
            ledger.parent.mkdir(parents=True)
            provenance.parent.mkdir(parents=True)
            ledger.write_text(json.dumps(review_ledger_fixture(payload)), encoding="utf-8")
            detector_path.write_text(json.dumps(payload), encoding="utf-8")
            validated_detector = guard.validate_detector(detector_path)
            provenance.write_text(
                "# Provenance\n\n"
                f"{accepted[0]}\n\n"
                "Authored reconciliation detail before the retry marker.\n\n"
                f"{pending}\n\n"
                "Authored reconciliation detail after the retry marker.\n",
                encoding="utf-8",
            )

            guard._cleanup_unaccepted_provenance_tail(root, validated_detector)

            cleaned = provenance.read_text(encoding="utf-8")
            self.assertIn(accepted[0], cleaned)
            self.assertNotIn(pending, cleaned)
            self.assertIn("detail before", cleaned)
            self.assertIn("detail after", cleaned)

            provenance.write_text(
                f"# Provenance\n{accepted[0]}\n{pending}\n{pending}\n",
                encoding="utf-8",
            )
            duplicate_tail = provenance.read_bytes()
            with self.assertRaises(guard.GuardError):
                guard._cleanup_unaccepted_provenance_tail(
                    root,
                    validated_detector,
                )
            self.assertEqual(provenance.read_bytes(), duplicate_tail)

            altered_accepted = accepted[0].replace(
                f'"inventory_sha256":"{"e" * 64}"',
                f'"inventory_sha256":"{"f" * 64}"',
            )
            provenance.write_text(
                f"# Provenance\n{altered_accepted}\n{pending}\n",
                encoding="utf-8",
            )
            replaced_prefix = provenance.read_bytes()
            with self.assertRaises(guard.GuardError):
                guard._cleanup_unaccepted_provenance_tail(
                    root,
                    validated_detector,
                )
            self.assertEqual(provenance.read_bytes(), replaced_prefix)


class SkillCompatibilityReviewTests(unittest.TestCase):
    """Exercise real Git sources and the no-tool consumer without calling a model."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.policy = json.loads((ROOT / ".github/pkstack-maintenance-policy.json").read_text())
        self.cases: dict[str, Any] = {
            "schema_version": 1,
            "cases": [
                {
                    "id": "explain-with-evidence",
                    "prompt": "Explain how the cache works and show evidence.",
                    "primary": "how",
                    "helpers": ["show-me-your-work"],
                    "expected_output": (
                        "One explanation owned by how with an evidence trail from its helper."
                    ),
                    "forbidden_effects": [
                        "Editing implementation files.",
                        "Duplicating the explanation.",
                    ],
                }
            ],
        }
        self.put(guard.SKILL_REVIEW_FIXTURE, json.dumps(self.cases))
        for name in (
            "how",
            "pkstack",
            "pkstack-helper",
            "show-me-your-work",
            "unrelated",
        ):
            self.put(
                f"powers/pkstack/skills/{name}/SKILL.md",
                self.skill(name, "Base instruction."),
            )
        self.put(
            "powers/pkstack/skills/show-me-your-work/references/evidence.md",
            "Preserve citations.\n",
        )
        self.put(
            "powers/pkstack/dev.kiro/steering/pkstack-core.md",
            "Use the current session.\n",
        )
        self.put("powers/pkstack/provenance/provenance.md", "Base provenance.\n")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        self.base = self.commit("base")

    def put(self, path: str, content: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def skill(self, name: str, body: str) -> str:
        return f"---\nname: {name}\ndescription: A bounded {name} task.\n---\n{body}\n"

    def commit(self, message: str) -> str:
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=PKStack Test",
                "-c",
                "user.email=pkstack@example.invalid",
                "commit",
                "-qm",
                message,
            ],
            cwd=self.root,
            check=True,
        )
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()

    def build(self, path: str = "powers/pkstack/skills/how/SKILL.md") -> tuple[dict, dict]:
        if path.endswith("/SKILL.md"):
            self.put(
                path,
                self.skill(
                    "how",
                    "Own the explanation; the evidence helper only supplies citations.",
                ),
            )
        else:
            self.put(path, "Updated provenance.\n")
        self.head = self.commit("candidate")
        output = self.root / ".git/review.json"
        result = guard.build_candidate_review_bundle(
            self.root, self.base, self.head, self.policy, output
        )
        return json.loads(output.read_text()), result

    def validate_bundle(self, bundle: dict, *, digest: str | None = None) -> None:
        import validate_kiro_review_stream as consumer

        raw = guard._review_json_bytes(bundle) + b"\n"
        consumer._validate_bundle(
            raw,
            base_sha=self.base,
            head_sha=self.head,
            content_sha256=digest or hashlib.sha256(raw).hexdigest(),
            patch_sha256=bundle["patch_sha256"],
        )

    def test_context_contains_unchanged_neighbors_and_exact_base_scenarios(
        self,
    ) -> None:
        bundle, result = self.build()
        context = bundle["skill_compatibility"]
        self.assertEqual(bundle["schema_version"], 3)
        self.assertEqual(context["fixture"]["commit_sha"], self.base)
        self.assertEqual(context["scenario_ids"], ["explain-with-evidence"])
        self.assertEqual(
            [item["name"] for item in context["catalog"]],
            ["how", "pkstack", "pkstack-helper", "show-me-your-work", "unrelated"],
        )
        self.assertEqual(
            [item["path"] for item in context["instructions"]],
            [
                "powers/pkstack/dev.kiro/steering/pkstack-core.md",
                "powers/pkstack/skills/how/SKILL.md",
                "powers/pkstack/skills/pkstack/SKILL.md",
                "powers/pkstack/skills/show-me-your-work/SKILL.md",
            ],
        )
        helper = next(item for item in context["catalog"] if item["name"] == "show-me-your-work")
        self.assertEqual(helper["references"], ["references/evidence.md"])
        self.assertLessEqual(len(guard._review_json_bytes(context)), 65536)
        self.validate_bundle(bundle, digest=result["content_sha256"])

    def inventory_bundle(self) -> tuple[dict, dict]:
        path = "powers/pkstack/metadata/okf-skills-parity.json"
        source = {
            "pinned": {"commit": "a" * 40},
            "current": {"commit": "b" * 40},
            "retrieved_on": "2026-09-05",
        }
        records: list[dict[str, Any]] = []
        for name in ("backfill/SKILL.md", "backfill/scripts/okf_backfill_events.py"):
            records.append(
                {
                    "path": name,
                    "pinned": {
                        "type": "blob",
                        "mode": "100644",
                        "object_sha": "1" * 40,
                        "size": 10577,
                    },
                    "current": {
                        "type": "blob",
                        "mode": "100644",
                        "object_sha": "2" * 40,
                        "size": 21302,
                    },
                    "disposition": "B",
                    "rationale": "Keep excluded.",
                }
            )
        document = {"artifact_type": "source-inventory", "source": source, "files": records}
        self.put(path, json.dumps(document, indent=2) + "\n")
        self.base = self.commit("inventory base")
        records[0]["pinned"] = dict(records[0]["current"])
        records[0]["current"] = {
            "type": "blob",
            "mode": "100644",
            "object_sha": "3" * 40,
            "size": 14817,
        }
        records[1]["current"] = {
            "type": "blob",
            "mode": "100644",
            "object_sha": "4" * 40,
            "size": 35417,
        }
        source["pinned"] = source["current"]
        source["current"] = {"commit": "c" * 40}
        self.put(path, json.dumps(document, indent=2) + "\n")
        self.head = self.commit("inventory candidate")
        output = self.root / ".git/inventory-review.json"
        result = guard.build_candidate_review_bundle(
            self.root, self.base, self.head, self.policy, output
        )
        return json.loads(output.read_text()), result

    def test_inventory_context_keeps_record_identity_and_same_day_date(self) -> None:
        bundle, result = self.inventory_bundle()
        # Reproduce the real rejected candidate's short-hunk ambiguity.
        self.assertNotIn('"path": "backfill/', bundle["patch"])
        context = bundle["source_inventory"][0]
        before = {item["path"]: item for item in context["base"]["files"]}
        after = {item["path"]: item for item in context["head"]["files"]}
        self.assertEqual(
            after["backfill/SKILL.md"]["pinned"], before["backfill/SKILL.md"]["current"]
        )
        self.assertEqual(
            after["backfill/scripts/okf_backfill_events.py"]["pinned"],
            before["backfill/scripts/okf_backfill_events.py"]["pinned"],
        )
        self.assertEqual(
            context["base"]["source"]["retrieved_on"], context["head"]["source"]["retrieved_on"]
        )
        self.validate_bundle(bundle, digest=result["content_sha256"])
        bundle["source_inventory"][0]["head"]["files"][0]["path"] = "invented/path"
        with self.assertRaisesRegex(Exception, "digest changed"):
            self.validate_bundle(bundle, digest=result["content_sha256"])

    def test_inventory_context_rejects_unrelated_duplicate_and_oversized_records(self) -> None:
        bundle, _ = self.inventory_bundle()
        context = bundle["source_inventory"]
        for changed in (
            [dict(context[0], path="unrelated.json")],
            context + context,
            [
                {
                    **context[0],
                    "head": {
                        "source": context[0]["head"]["source"],
                        "files": [{"path": "a", "rationale": "x" * 65536}],
                    },
                }
            ],
        ):
            with self.subTest(context_kind=list(changed[0])), self.assertRaises(guard.GuardError):
                guard.validate_source_inventory_context(changed, bundle["paths"])
        with (
            mock.patch.object(guard, "SOURCE_INVENTORY_CONTEXT_MAX_BYTES", 1),
            self.assertRaisesRegex(guard.GuardError, "exceeds 64 KiB"),
        ):
            guard._build_source_inventory_context(self.root, self.base, self.head, bundle["paths"])

    def test_inventory_and_skill_context_share_existing_budget(self) -> None:
        import pkstack_maintenance_guard as consumer_guard

        skills = {"instructions": "s" * 35_000}
        inventory = [{"source": "i" * 35_000}]
        self.assertLess(len(guard._review_json_bytes(skills)), 65_536)
        self.assertLess(len(guard._review_json_bytes(inventory)), 65_536)
        with self.assertRaisesRegex(guard.GuardError, "combined review context exceeds 64 KiB"):
            guard.validate_combined_review_context(skills, inventory)
        bundle, _ = self.inventory_bundle()
        combined_size = len(
            guard._review_json_bytes(
                {
                    "skill_compatibility": bundle["skill_compatibility"],
                    "source_inventory": bundle["source_inventory"],
                }
            )
        )
        with (
            mock.patch.object(guard, "SKILL_REVIEW_CONTEXT_MAX_BYTES", combined_size - 1),
            mock.patch.object(consumer_guard, "SKILL_REVIEW_CONTEXT_MAX_BYTES", combined_size - 1),
        ):
            with self.assertRaisesRegex(Exception, "combined review context exceeds 64 KiB"):
                self.validate_bundle(bundle)
            with self.assertRaisesRegex(guard.GuardError, "combined review context exceeds 64 KiB"):
                guard.build_candidate_review_bundle(
                    self.root,
                    self.base,
                    self.head,
                    self.policy,
                    self.root / ".git/budget-bundle.json",
                )

    def test_unaffected_metadata_has_empty_context(self) -> None:
        bundle, _ = self.build("powers/pkstack/provenance/provenance.md")
        self.assertEqual(bundle["skill_compatibility"], {})
        self.validate_bundle(bundle)

    def test_changed_reference_includes_its_whole_current_body(self) -> None:
        path = "powers/pkstack/skills/show-me-your-work/references/evidence.md"
        bundle, _ = self.build(path)
        record = next(
            item for item in bundle["skill_compatibility"]["instructions"] if item["path"] == path
        )
        self.assertEqual(record["content"], "Updated provenance.\n")
        self.assertEqual(record["commit_sha"], self.head)
        self.validate_bundle(bundle)

    def test_base_scenario_can_require_the_full_workflow_handoff_reference(
        self,
    ) -> None:
        path = "powers/pkstack/skills/pkstack/references/workflows.md"
        self.put(path, "Keep native planning and the handoff in one conversation.\n")
        self.cases["cases"][0]["expected_output"] += (
            " Apply the references/workflows.md handoff contract."
        )
        self.put(guard.SKILL_REVIEW_FIXTURE, json.dumps(self.cases))
        self.base = self.commit("reviewed workflow scenario")
        bundle, _ = self.build()
        self.assertIn(
            path,
            [item["path"] for item in bundle["skill_compatibility"]["instructions"]],
        )
        self.validate_bundle(bundle)

    def test_aggregate_context_limit_fails_without_truncating_files(self) -> None:
        self.put("powers/pkstack/skills/pkstack/SKILL.md", self.skill("pkstack", "p" * 32000))
        self.put(
            "powers/pkstack/skills/show-me-your-work/SKILL.md",
            self.skill("show-me-your-work", "s" * 32000),
        )
        self.base = self.commit("large unchanged neighbors")
        with self.assertRaisesRegex(guard.GuardError, "context exceeds 64 KiB"):
            self.build()

    def test_missing_base_fixture_cannot_be_bootstrapped_from_candidate(self) -> None:
        subprocess.run(
            ["git", "rm", "--", guard.SKILL_REVIEW_FIXTURE],
            cwd=self.root,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        self.base = self.commit("old baseline without fixture")
        self.put(guard.SKILL_REVIEW_FIXTURE, json.dumps(self.cases))
        head = self.commit("untrusted candidate fixture")
        with self.assertRaisesRegex(guard.GuardError, "promote a reviewed fixture"):
            guard._build_skill_review_context(
                self.root, self.base, head, ["powers/pkstack/skills/how/SKILL.md"]
            )

    def test_candidate_fixture_changes_never_replace_base_expectations(self) -> None:
        altered = json.loads(json.dumps(self.cases))
        altered["cases"][0]["forbidden_effects"] = ["Do not ask before publication."]
        self.put(guard.SKILL_REVIEW_FIXTURE, json.dumps(altered))
        head = self.commit("candidate expectation tampering")
        context = guard._build_skill_review_context(
            self.root, self.base, head, ["powers/pkstack/skills/how/SKILL.md"]
        )
        self.assertEqual(context["fixture"]["cases"], self.cases["cases"])

    def test_missing_base_case_fails_instead_of_skipping_semantic_review(self) -> None:
        self.put(
            "powers/pkstack/skills/unrelated/SKILL.md",
            self.skill("unrelated", "Changed."),
        )
        head = self.commit("uncovered skill")
        with self.assertRaisesRegex(guard.GuardError, "base scenario coverage"):
            guard._build_skill_review_context(
                self.root, self.base, head, ["powers/pkstack/skills/unrelated/SKILL.md"]
            )

    def test_context_sources_reject_symlinks_controls_and_oversize(self) -> None:
        target = "powers/pkstack/skills/show-me-your-work/SKILL.md"
        for kind in ("symlink", "controls", "oversize"):
            with self.subTest(kind=kind):
                # Each subcase gets a fresh repository and preserves the prior committed base.
                self.setUp()
                file = self.root / target
                if kind == "symlink":
                    file.unlink()
                    file.symlink_to("/etc/passwd")
                else:
                    self.put(target, "bad\x00text" if kind == "controls" else "x" * 65537)
                self.base = self.commit("unsafe unchanged neighbor")
                with self.assertRaises(guard.GuardError):
                    self.build()

    def test_consumer_rejects_missing_tampered_stale_and_unsafe_context(self) -> None:
        import validate_kiro_review_stream as consumer

        original, result = self.build()
        cases = (
            "missing",
            "stale",
            "fixture-head",
            "fixture-path",
            "tampered",
            "control",
            "missing-neighbor",
            "missing-scenario",
            "traversal",
            "oversize",
            "catalog",
            "legacy",
        )
        for case in cases:
            with self.subTest(case=case):
                bundle = json.loads(json.dumps(original))
                context = bundle["skill_compatibility"]
                if case == "missing":
                    bundle["skill_compatibility"] = {}
                elif case == "stale":
                    context["head_sha"] = self.base
                elif case == "fixture-head":
                    context["fixture"]["commit_sha"] = self.head
                elif case == "fixture-path":
                    context["fixture"]["path"] = "powers/pkstack/docs/skill-routing.json"
                elif case == "tampered":
                    context["instructions"][0]["content"] += " Publish now."
                elif case == "control":
                    context["instructions"][0]["content"] += "\x00"
                elif case == "missing-neighbor":
                    context["instructions"].pop()
                elif case == "missing-scenario":
                    context["scenario_ids"] = []
                elif case == "traversal":
                    context["catalog"][0]["references"] = ["../secrets.md"]
                elif case == "oversize":
                    context["catalog"][0]["description"] = "x" * 65536
                elif case == "catalog":
                    context["catalog"].pop(3)
                elif case == "legacy":
                    bundle["schema_version"] = 1
                with self.assertRaises(consumer.ReviewError):
                    self.validate_bundle(bundle)
        changed = json.loads(json.dumps(original))
        changed["skill_compatibility"]["catalog"][0]["description"] += " altered"
        with self.assertRaisesRegex(consumer.ReviewError, "content digest changed"):
            self.validate_bundle(changed, digest=result["content_sha256"])


class PolicyAndWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.policy = guard.load_policy(ROOT / ".github" / "pkstack-maintenance-policy.json")

    def test_candidate_and_finalizer_scopes_do_not_share_oracles(self) -> None:
        agent_exact = set(self.policy["agent_allowed_exact"])
        final_exact = set(self.policy["final_allowed_exact"])
        self.assertIn(".pkstack-maintenance/proposal.json", agent_exact)
        self.assertNotIn(".pkstack-maintenance/proposal.json", final_exact)
        self.assertNotIn("maintenance/upstream-reviews.json", agent_exact)
        self.assertIn("maintenance/upstream-reviews.json", final_exact)
        self.assertFalse(
            guard._matches(
                "powers/pkstack/src/pkstack/upstreams.py",
                agent_exact,
                self.policy["agent_allowed_prefixes"],
            )
        )
        self.assertTrue(guard._is_protected("tests/test_upstreams.py", self.policy))

    def test_candidate_package_has_one_exact_bounded_size_contract(self) -> None:
        self.assertEqual(
            self.policy["limits"]["max_candidate_package_bytes"],
            33_554_432,
        )
        self.assertEqual(self.policy["limits"]["max_review_ledger_bytes"], 8 * 1024 * 1024)
        self.assertEqual(self.policy["limits"]["max_review_transitions"], 512)
        source = GUARD_PATH.read_text(encoding="utf-8")
        self.assertGreaterEqual(
            source.count('policy["limits"]["max_candidate_package_bytes"]'),
            2,
        )
        self.assertNotIn('policy["limits"]["max_patch_bytes"] * 3 + 65_536', source)

    def test_ci_agent_matches_immutable_policy(self) -> None:
        guard.validate_ci_agent(
            ROOT / ".kiro" / "agents" / "pkstack-maintainer.json",
            self.policy,
        )

    def test_candidate_review_overlaps_tests_but_publication_waits(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-candidate.yml").read_text()
        lines = _yaml_structural_lines(workflow)
        jobs = _workflow_job_ranges(lines)

        def block(name: str) -> str:
            start, end = jobs[name]
            return "\n".join(line.raw for line in lines[start:end])

        for name in ("candidate_tests", "kiro_peer_review"):
            self.assertIn("    needs: [resolve, candidate_prepare]", block(name))
        for name in ("merge", "record_rejection", "cleanup_failed_candidate"):
            dependency_line = next(
                line for line in block(name).splitlines() if line.startswith("    needs:")
            )
            for required in (
                "candidate_prepare",
                "base_ci",
                "candidate_tests",
                "kiro_peer_review",
            ):
                self.assertIn(required, dependency_line)
        self.assertIn("needs.candidate_tests.result == 'success'", block("record_rejection"))
        self.assertIn(
            "needs.candidate_tests.result != 'success'", block("cleanup_failed_candidate")
        )
        self.assertNotIn("secrets.", block("candidate_prepare"))
        self.assertNotIn("github.token", block("candidate_tests"))
        self.assertNotIn("pytest", block("candidate_prepare"))
        self.assertIn("validate-serialized-acceptance", block("candidate_prepare"))

    def test_trusted_snapshot_archives_include_exact_required_prefixes(self) -> None:
        for filename, step_name in (
            (
                "pk-stack-upstream-maintenance-kiro.yml",
                "Materialize locked environments and trusted scripts",
            ),
            (
                "pk-stack-upstream-candidate.yml",
                "Snapshot immutable base controller and review guards",
            ),
        ):
            with self.subTest(workflow=filename):
                workflow = (ROOT / ".github/workflows" / filename).read_text()
                marker = f"      - name: {step_name}\n"
                expected = 2 if filename == "pk-stack-upstream-candidate.yml" else 1
                self.assertEqual(workflow.count(marker), expected)
                for section in workflow.split(marker)[1:]:
                    step = section.split("\n      - name: ", 1)[0]
                    self.assertIn("validate-trusted-snapshot", step)
                    archive = step.split('git archive "$BASE_SHA"', 1)[1].split(
                        '| tar -x -C "$TRUSTED_ROOT"', 1
                    )[0]
                    paths = shlex.split(archive.replace("\\\n", " "))
                    self.assertCountEqual(paths, guard.TRUSTED_SNAPSHOT_PREFIXES)

    def test_detector_snapshot_executes_its_controller_entrypoints(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml").read_text()
        step = workflow.split("      - name: Snapshot immutable sensor and controller\n", 1)[1]
        archive = step.split('git archive "$BASE_SHA"', 1)[1].split(
            '| tar -x -C "$TRUSTED_ROOT"', 1
        )[0]
        paths = shlex.split(archive.replace("\\\n", " "))
        packed = subprocess.run(
            ["git", "archive", "HEAD", *paths], cwd=ROOT, capture_output=True, check=True
        ).stdout
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = Path(temporary)
            subprocess.run(["tar", "-x", "-C", temporary], input=packed, check=True)
            environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
            for name in ("pkstack_maintenance_guard.py", "pkstack_update_controller.py"):
                result = subprocess.run(
                    [sys.executable, "-B", str(snapshot / ".github/scripts" / name), "--help"],
                    cwd=snapshot,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)

    def test_trusted_inventory_preflight_leaves_snapshot_unchanged(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml").read_text()
        commands = [
            line.strip()
            for line in workflow.splitlines()
            if line.strip().startswith("python3 ")
            and any(
                name in line
                for name in (
                    "/test_validate_kiro_model_inventory.py",
                    "/test_validate_kiro_maintenance_stream.py",
                )
            )
        ]
        self.assertEqual(len(commands), 2)
        for command in commands:
            self.assertEqual(shlex.split(command)[:2], ["python3", "-B"])
            following = workflow.split(command, 1)[1].split('chmod -R a-w "$TRUSTED_ROOT"', 1)[0]
            self.assertIn("validate-trusted-snapshot", following)
        candidate = (ROOT / ".github/workflows/pk-stack-upstream-candidate.yml").read_text()
        self.assertIn('python3 -B "$TRUSTED_ROOT/.github/scripts/pkstack_checks.py"', candidate)
        self.assertIn('local full --output "$RUNNER_TEMP/pkstack-candidate-checks"', candidate)

        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "trusted"
            shutil.copytree(
                ROOT / ".github",
                snapshot / ".github",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            profile = Path(".kiro/agents/pkstack-maintainer.json")
            (snapshot / profile).parent.mkdir(parents=True)
            shutil.copyfile(ROOT / profile, snapshot / profile)

            def inventory() -> dict[str, str]:
                return {
                    str(path.relative_to(snapshot)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in snapshot.rglob("*")
                    if path.is_file()
                }

            before = inventory()
            environment = {
                key: value
                for key, value in os.environ.items()
                if key not in {"PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX"}
            }
            # Apple Python relocates bytecode caches by default. Force Linux's
            # in-tree cache behavior so this regression cannot be masked locally.
            runner = (
                "import runpy,sys; from pathlib import Path; sys.pycache_prefix=None; "
                "sys.argv=[sys.argv[1]]; sys.path.insert(0,str(Path(sys.argv[0]).parent)); "
                "runpy.run_path(sys.argv[0], run_name='__main__')"
            )
            guard_result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    runner.replace("sys.argv=[sys.argv[1]]", "sys.argv=[sys.argv[1], '--help']"),
                    str(snapshot / ".github/scripts/pkstack_maintenance_guard.py"),
                ],
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(guard_result.returncode, 0, guard_result.stderr)
            self.assertEqual(inventory(), before)
            for command in commands:
                arguments = shlex.split(command)
                result = subprocess.run(
                    [
                        sys.executable,
                        *arguments[1:-1],
                        "-c",
                        runner,
                        arguments[-1].replace("$TRUSTED_ROOT", str(snapshot)),
                    ],
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(inventory(), before)
            self.assertFalse(list(snapshot.rglob("*.pyc")))

    def test_permission_smoke_fixture_matches_production_and_policy_exactly(self) -> None:
        fixture = json.loads(
            (ROOT / ".github/fixtures/kiro-permission-agent.json").read_text(encoding="utf-8")
        )
        production = json.loads(
            (ROOT / ".kiro/agents/pkstack-maintainer.json").read_text(encoding="utf-8")
        )
        authority = self.policy["ci_authority"]
        self.assertIn(".git/**", authority["deny_patterns"])
        expected_rules = [
            {"capability": "fs_read", "match": ["./**"], "effect": "allow"},
            {"capability": "grep", "match": ["./**"], "effect": "allow"},
            {
                "capability": "fs_write",
                "match": authority["write_patterns"],
                "effect": "allow",
            },
            {
                "capability": "fs_write",
                "match": authority["deny_patterns"],
                "effect": "deny",
            },
        ]
        self.assertEqual(set(fixture["permissions"]), {"rules"})
        self.assertEqual(fixture["permissions"]["rules"], expected_rules)
        self.assertEqual(fixture["permissions"], production["permissions"])
        self.assertEqual(fixture["toolsSettings"], authority["tools_settings"])
        self.assertEqual(production["toolsSettings"], fixture["toolsSettings"])

        prompt = fixture["prompt"]
        self.assertIn(
            "exactly and only the ordered filesystem operations enumerated in the current "
            "user prompt",
            prompt,
        )
        self.assertIn("Do not infer, retry, or add operations", prompt)
        self.assertIn("Emit no assistant prose before or after tool use", prompt)
        self.assertIn("including when that operation is denied", prompt)
        self.assertNotIn("continue after each expected denial", prompt)
        self.assertNotIn("all thirteen writes", prompt)
        for path in permission_stream_guard.ALLOWED_WRITES:
            self.assertNotIn(path[0], prompt)
        for path in permission_stream_guard.DENIED_RESOURCES:
            self.assertNotIn(path, prompt)

    def test_ci_agent_rejects_nonempty_v3_discovery_settings(self) -> None:
        document = json.loads(
            (ROOT / ".kiro/agents/pkstack-maintainer.json").read_text(encoding="utf-8")
        )
        document["toolsSettings"] = {"shell": {"allowedCommands": ["*"]}}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "agent.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.validate_ci_agent(path, self.policy)

    def test_ci_agent_cannot_replace_prior_provenance_markers(self) -> None:
        document = json.loads(
            (ROOT / ".kiro/agents/pkstack-maintainer.json").read_text(encoding="utf-8")
        )
        document["prompt"] = document["prompt"].replace(
            "preserve every prior review marker unchanged and in order",
            "replace prior review markers",
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "agent.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.validate_ci_agent(path, self.policy)

    def test_ci_agent_cannot_choose_an_ambiguous_drift_source(self) -> None:
        document = json.loads(
            (ROOT / ".kiro/agents/pkstack-maintainer.json").read_text(encoding="utf-8")
        )
        required = "use the exact selected_source_id from the immutable control plan"
        self.assertIn(required, document["prompt"])
        document["prompt"] = document["prompt"].replace(
            required,
            "select any drifting source",
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "agent.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.validate_ci_agent(path, self.policy)

    def test_ci_agent_uses_supplied_control_action_not_an_absent_detector_count(self) -> None:
        document = json.loads(
            (ROOT / ".kiro/agents/pkstack-maintainer.json").read_text(encoding="utf-8")
        )
        detector = drift_detector_fixture()
        self.assertNotIn("drift_count", detector)
        self.assertNotIn("drift_count", document["prompt"])
        required = (
            "The immutable control plan action reconcile-source requires exactly one proposal"
        )
        self.assertIn(required, document["prompt"])
        document["prompt"] = document["prompt"].replace(required, "Create no proposal")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "agent.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.validate_ci_agent(path, self.policy)

    def test_ci_agent_preserves_parity_safety_and_provenance_format(self) -> None:
        document = json.loads(
            (ROOT / ".kiro/agents/pkstack-maintainer.json").read_text(encoding="utf-8")
        )
        for requirement in (
            "Preserve existing parity rationale verbatim",
            "put delta-specific explanations in the new proposal and provenance prose",
            "authorization, redaction, and bounded-migration requirements",
            "source.retrieved_on only from the trusted inventory_retrieved_on value",
            "UTC date of this inventory retrieval, not the initial baseline date",
            "Never infer it from candidate content or your clock",
            "Terminate the new final marker line with one LF newline",
            "preserve the genesis marker and all accepted history unchanged",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, document["prompt"])
        guard.validate_ci_agent(ROOT / ".kiro/agents/pkstack-maintainer.json", self.policy)

    def test_workflow_supplies_date_from_same_day_trusted_inventory_retrieval(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml").read_text()
        capture = "          retrieved_on=$(date -u +%F)\n"
        boundary = '          if [[ "$(date -u +%F)" != "$retrieved_on" ]]; then\n'
        self.assertLess(workflow.index(capture), workflow.index("-m pkstack upstream check"))
        self.assertLess(workflow.index("validate-detector --detector"), workflow.index(boundary))
        self.assertIn("retrieved_on: ${{ steps.detect.outputs.retrieved_on }}", workflow)
        self.assertIn("printf 'retrieved_on=%s\\n' \"$retrieved_on\"", workflow)
        self.assertIn(
            "PKSTACK_UPSTREAM_RETRIEVED_ON: ${{ needs.detect.outputs.retrieved_on }}",
            workflow,
        )
        script = textwrap.dedent(
            boundary
            + workflow.split(boundary, 1)[1].split("          fi\n", 1)[0]
            + "          fi\n"
        )
        for current_date, expected_rc in (("2026-09-05", 0), ("2026-09-06", 1)):
            with self.subTest(current_date=current_date):
                result = subprocess.run(
                    [
                        "bash",
                        "-c",
                        f'retrieved_on=2026-09-05; date() {{ printf "%s\\n" {current_date}; }};\n'
                        + script,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self.assertEqual(result.returncode, expected_rc, result.stderr)

    def test_operational_skill_patch_builds_mandatory_exact_review_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "powers/pkstack/skills/example/SKILL.md"
            skill.parent.mkdir(parents=True)
            header = "---\nname: example\ndescription: A bounded example.\n---\n"
            skill.write_text(header + "base instruction\n", encoding="utf-8")
            primary = root / "powers/pkstack/skills/pkstack/SKILL.md"
            primary.parent.mkdir()
            primary.write_text(
                "---\nname: pkstack\ndescription: Route the request.\n---\n",
                encoding="utf-8",
            )
            fixture = root / guard.SKILL_REVIEW_FIXTURE
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "cases": [
                            {
                                "id": "example",
                                "prompt": "Explain this example.",
                                "primary": "example",
                                "helpers": [],
                                "expected_output": "A clear explanation.",
                                "forbidden_effects": ["Editing files."],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            commit = [
                "git",
                "-c",
                "user.name=PKStack Test",
                "-c",
                "user.email=pkstack@example.invalid",
                "commit",
                "-qm",
            ]
            subprocess.run([*commit, "base"], cwd=root, check=True)
            base_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            skill.write_text(header + "changed operational instruction\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run([*commit, "candidate"], cwd=root, check=True)
            head_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            bundle_path = root / ".git/fable-review-input.json"
            result = guard.build_candidate_review_bundle(
                root,
                base_sha,
                head_sha,
                self.policy,
                bundle_path,
            )
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            self.assertEqual(bundle["paths"], ["powers/pkstack/skills/example/SKILL.md"])
            self.assertTrue(bundle["requires_review"])
            self.assertEqual(bundle["base_sha"], base_sha)
            self.assertEqual(bundle["head_sha"], head_sha)
            self.assertEqual(bundle["schema_version"], 3)
            self.assertEqual(bundle["skill_compatibility"]["scenario_ids"], ["example"])
            self.assertEqual(bundle["paths_sha256"], result["paths_sha256"])
            verdict_echoes = {
                "base_sha",
                "head_sha",
                "patch_sha256",
                "paths_sha256",
                "changed_files",
            }
            self.assertLessEqual(verdict_echoes, bundle.keys())
            self.assertEqual(
                result["content_sha256"],
                hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
            )

    def test_reviewer_instruction_paths_are_protected_under_every_allowed_prefix(self) -> None:
        prefixes = set(self.policy["agent_allowed_prefixes"]) | set(
            self.policy["final_allowed_prefixes"]
        )
        dangerous_suffixes = (
            "AGENTS.md",
            "CLAUDE.md",
            "CLAUDE.local.md",
            "GEMINI.md",
            ".claude/settings.json",
            ".codex/config.toml",
            ".cursor/rules.md",
            ".gemini/settings.json",
        )
        for prefix in prefixes:
            for suffix in dangerous_suffixes:
                with self.subTest(prefix=prefix, suffix=suffix):
                    self.assertTrue(guard._is_protected(prefix + suffix, self.policy))

    def test_boundaries_and_review_bundle_reject_nested_reviewer_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            safe = root / "powers/pkstack/docs/guide.md"
            safe.parent.mkdir(parents=True)
            safe.write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            commit = [
                "git",
                "-c",
                "user.name=PKStack Test",
                "-c",
                "user.email=pkstack@example.invalid",
                "commit",
                "-qm",
            ]
            subprocess.run([*commit, "base"], cwd=root, check=True)
            base_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            injected = root / "powers/pkstack/docs/CLAUDE.md"
            injected.write_text("untrusted reviewer instruction\n", encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard._validate_worktree_paths(root, base_sha, self.policy, scope="agent")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run([*commit, "candidate"], cwd=root, check=True)
            head_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            with self.assertRaises(guard.GuardError):
                guard.build_candidate_review_bundle(
                    root,
                    base_sha,
                    head_sha,
                    self.policy,
                    root / ".git/fable-review-input.json",
                )

    def test_goal_status_uses_attempt_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            status = Path(temporary) / "goal.json"
            status.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "goal": {
                            "goal_id": "goal",
                            "status": "passed",
                            "attempt_count": 2,
                            "max_attempts": 3,
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(guard._goal_status(status)["attempt_count"], 2)

    def test_isolated_kiro_settings_are_exact_and_never_written_via_cli(self) -> None:
        sources = {
            "maintenance setup": (
                ROOT / ".github/scripts/prepare_kiro_maintenance_runtime.sh"
            ).read_text(),
            "credential smoke": (
                ROOT / ".github/workflows/pk-stack-kiro-credential-smoke.yml"
            ).read_text(),
            "permission smoke": (
                ROOT / ".github/workflows/pk-stack-kiro-permission-smoke.yml"
            ).read_text(),
        }
        payload_pattern = re.compile(
            r"(?m)^\s*printf '%s\\n' \\\n"
            r'(?P<lines>(?:^\s*\'[^\']*\'(?: \\| >"\$settings_path")\n)+)'
        )
        for label, source in sources.items():
            with self.subTest(label=label):
                payload_match = payload_pattern.search(source)
                payload_match = require_match(payload_match)
                values = re.findall(
                    r'(?m)^\s*\'([^\']*)\'(?: \\| >"\$settings_path")$',
                    payload_match.group("lines"),
                )
                payload = ("\n".join(values) + "\n").encode()
                self.assertEqual(payload, KIRO_ISOLATED_SETTINGS)
                self.assertEqual(
                    json.loads(payload),
                    {
                        "app.disableAutoupdates": True,
                        "chat.disableInheritingDefaultResources": True,
                        "telemetry.enabled": False,
                    },
                )
                self.assertIn(KIRO_ISOLATED_SETTINGS_SHA256, source)
                self.assertIn('install -m 0600 /dev/null "$settings_path"', source)
                self.assertIn("stat -c '%a'", source)
                self.assertIn("settings/mcp.json", source)
                if label == "maintenance setup":
                    self.assertIn('[[ "$KIRO_HOME" == "$KIRO_USER_HOME/.kiro" ]]', source)
                    self.assertIn('test -d "$KIRO_USER_HOME/.kiro"', source)
                else:
                    self.assertTrue(
                        'test ! -e "$SMOKE_ROOT/user-home/.kiro"' in source
                        or 'test ! -e "$case_root/user-home/.kiro"' in source
                    )
                for key in (
                    "app.disableAutoupdates",
                    "chat.disableInheritingDefaultResources",
                    "telemetry.enabled",
                ):
                    self.assertEqual(source.count(f'"{key}"'), 1)
                    self.assertNotIn(f" settings {key} ", source)

    def test_global_runtime_agent_uses_one_fresh_home_for_both_cli_lookups(self) -> None:
        setup = (ROOT / ".github/scripts/prepare_kiro_maintenance_runtime.sh").read_text()
        for filename, home_name in (
            ("pk-stack-upstream-maintenance-kiro.yml", "kiro-user-home"),
            ("pk-stack-upstream-candidate.yml", "kiro-review-user-home"),
        ):
            workflow = (ROOT / ".github/workflows" / filename).read_text()
            self.assertIn(f"printf 'KIRO_HOME=%s\\n' \"$RUNNER_TEMP/{home_name}/.kiro\"", workflow)
            self.assertIn(f"printf 'KIRO_USER_HOME=%s\\n' \"$RUNNER_TEMP/{home_name}\"", workflow)
        self.assertEqual(setup.count('install -m 0600 "$trusted_agent"'), 1)
        self.assertEqual(setup.count('"$KIRO_HOME/agents/${agent_name}.json"'), 1)
        self.assertEqual(setup.count('settings_path="$KIRO_HOME/settings/cli.json"'), 1)
        marker = '[[ -f "$KIRO_ARCHIVE" && ! -L "$KIRO_ARCHIVE" ]]'
        self.assertEqual(setup.count(marker), 1)
        guards = setup.split(marker, maxsplit=1)[0]
        for case in (
            "valid",
            "sibling_home",
            "existing_user",
            "symlink_user",
            "nested_user",
            "shared_bin_user",
        ):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                runner = Path(temporary) / "runner"
                runner.mkdir()
                user = runner / "kiro-user-home"
                binary = runner / "kiro-bin"
                if case == "existing_user":
                    user.mkdir()
                elif case == "symlink_user":
                    user.symlink_to(runner, target_is_directory=True)
                elif case == "nested_user":
                    user = runner / "nested" / "kiro-user-home"
                elif case == "shared_bin_user":
                    binary = user
                kiro_home = runner / "kiro-home" if case == "sibling_home" else user / ".kiro"
                environment = {
                    "PATH": os.environ["PATH"],
                    "RUNNER_TEMP": str(runner),
                    "KIRO_BIN_DIR": str(binary),
                    "KIRO_USER_HOME": str(user),
                    "KIRO_HOME": str(kiro_home),
                    "KIRO_ARCHIVE": str(runner / "archive"),
                    "TRUSTED_ROOT": str(runner / "trusted"),
                }
                result = subprocess.run(
                    ["bash", "-c", guards],
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(result.returncode == 0, case == "valid", result.stderr)
                self.assertFalse(binary.exists())
                self.assertFalse(kiro_home.exists())

    def test_reviewer_schema_validation_uses_secretless_direct_chat_binary(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-candidate.yml").read_text()
        marker = "      - name: Prepare immutable no-tool Kiro reviewer\n"
        self.assertEqual(workflow.count(marker), 1)
        preparation = workflow.split(marker, 1)[1].split("\n      - name: ", 1)[0]
        commands = [line.strip() for line in preparation.splitlines() if " agent validate " in line]
        self.assertEqual(len(commands), 1)
        self.assertEqual(
            shlex.split(commands[0]),
            [
                "env",
                "-i",
                "HOME=$KIRO_USER_HOME",
                "KIRO_HOME=$KIRO_HOME",
                "PATH=$KIRO_BIN_DIR:/usr/local/bin:/usr/bin:/bin",
                "LANG=C.UTF-8",
                "$KIRO_BIN_DIR/kiro-cli-chat",
                "agent",
                "validate",
                "--path",
                "$TRUSTED_REVIEW_ROOT/.kiro/agents/pkstack-ci-reviewer.json",
            ],
        )
        self.assertNotIn("KIRO_API_KEY", preparation)
        self.assertEqual(workflow.count('"$KIRO_BIN_DIR/kiro-cli" chat'), 2)
        validate_candidate_workflow_secret_contract(workflow)

    def test_candidate_review_cleanup_validates_nested_home_before_deleting_roots(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-candidate.yml").read_text()
        marker = "      - name: Remove private Kiro review state\n"
        self.assertEqual(workflow.count(marker), 1)
        step = workflow.split(marker, maxsplit=1)[1].split("\n  merge:", maxsplit=1)[0]
        cleanup = textwrap.dedent(step.split("        run: |\n", maxsplit=1)[1])
        for targets in re.findall(r"(?m)^for target in (.*); do$", cleanup):
            self.assertNotIn('"$KIRO_HOME"', targets)
        for case in (
            "valid",
            "sibling_home",
            "symlink_home",
            "symlink_user",
            "wrong_private",
            "file_bin",
        ):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                runner = Path(temporary) / "runner"
                runner.mkdir()
                roots = {
                    "REVIEW_PRIVATE": runner / "pkstack-peer-review-private",
                    "REVIEW_WORKSPACE": runner / "pkstack-peer-review-workspace",
                    "KIRO_USER_HOME": runner / "kiro-review-user-home",
                    "KIRO_BIN_DIR": runner / "kiro-review-bin",
                }
                for directory in roots.values():
                    directory.mkdir()
                    (directory / "retained.txt").write_text("private fixture")
                kiro_home = roots["KIRO_USER_HOME"] / ".kiro"
                kiro_home.mkdir()
                (kiro_home / "settings.json").write_text("private fixture")
                sentinel = runner / "unrelated.txt"
                sentinel.write_text("keep")
                if case == "sibling_home":
                    kiro_home = runner / "kiro-home"
                elif case == "symlink_home":
                    shutil.rmtree(kiro_home)
                    kiro_home.symlink_to(runner, target_is_directory=True)
                elif case == "symlink_user":
                    shutil.rmtree(roots["KIRO_USER_HOME"])
                    roots["KIRO_USER_HOME"].symlink_to(runner, target_is_directory=True)
                elif case == "wrong_private":
                    roots["REVIEW_PRIVATE"] = runner
                elif case == "file_bin":
                    shutil.rmtree(roots["KIRO_BIN_DIR"])
                    roots["KIRO_BIN_DIR"].write_text("keep invalid file")
                environment = {
                    "PATH": os.environ["PATH"],
                    "RUNNER_TEMP": str(runner),
                    "KIRO_HOME": str(kiro_home),
                    **{key: str(path) for key, path in roots.items()},
                }
                result = subprocess.run(
                    ["bash", "-c", cleanup],
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(result.returncode == 0, case == "valid", result.stderr)
                self.assertEqual(sentinel.read_text(), "keep")
                for directory in roots.values():
                    self.assertEqual(directory.exists(), case != "valid")

    def test_two_attempt_budget_and_terminal_gate_cover_success_exhaustion_and_cancellation(self):
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml").read_text()
        self.assertIn("timeout-minutes: 30", workflow)
        self.assertIn('test "$max_attempts" = "3"', workflow)
        self.assertNotIn("steps.verify3", workflow)
        for prefix in (
            "Prepare repair 2 without workspace hooks",
            "Kiro repair 2 of 2",
            "Secretless verification 2 of 2",
        ):
            step = workflow.split("      - name: " + prefix, 1)[1].split("      - name:", 1)[0]
            self.assertIn("if: steps.verify1.outputs.passed != 'true'", step)
        terminal = workflow.split("      - name: Require a terminal verified candidate", 1)[1]
        shell = terminal.split("        run: |\n", 1)[1].split("      - name:", 1)[0]
        shell = textwrap.dedent(shell)
        for first, second, passed in (
            ("true", "", True),
            ("false", "true", True),
            ("false", "false", False),
            ("", "", False),
        ):
            with self.subTest(first=first, second=second):
                result = subprocess.run(
                    ["bash", "-c", shell],
                    env={**os.environ, "PASS1": first, "PASS2": second},
                    capture_output=True,
                    timeout=5,
                )
                self.assertEqual(result.returncode == 0, passed)
        # Goal evidence from a third/fourth repair must also fail after packaging.
        with tempfile.TemporaryDirectory() as folder:
            goal_path = Path(folder) / "goal.json"
            for count in (1, 2, 3, 4, 5):
                goal_path.write_text(
                    json.dumps(
                        {
                            "ok": True,
                            "goal": {"status": "passed", "max_attempts": 3, "attempt_count": count},
                        }
                    )
                )
                if count in {2, 3}:
                    self.assertEqual(guard._goal_status(goal_path)["attempt_count"], count)
                else:
                    with self.assertRaises(guard.GuardError):
                        guard._goal_status(goal_path)

    def test_maintenance_uses_only_two_scoped_kiro_credentials(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml").read_text()
        validate_maintenance_workflow_security_contract(workflow)
        self.assertNotIn("reviewer_readiness:", workflow)
        self.assertIn("needs: [plan, detect]", workflow)
        self.assertIn("if: needs.detect.outputs.needs_maintenance == 'true'", workflow)
        key_binding = "KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}"
        self.assertEqual(workflow.count(key_binding), 2)
        self.assertNotRegex(
            workflow,
            r"(ANTHROPIC_API_KEY|CLAUDE_CODE_OAUTH_TOKEN|OPENAI_API_KEY|XAI_API_KEY|copilot)",
        )

    def test_candidate_uses_only_two_scoped_kiro_review_credentials(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-candidate.yml").read_text()
        validate_candidate_workflow_secret_contract(workflow)
        self.assertEqual(
            _secret_context_expressions(_yaml_structural_lines(workflow)),
            CANDIDATE_SECRET_CONTEXT_EXPRESSIONS,
        )
        self.assertIn("REVIEW_MODEL: claude-opus-5", workflow)
        self.assertIn("REVIEW_EFFORT: xhigh", workflow)
        self.assertNotRegex(
            workflow,
            r"(ANTHROPIC_API_KEY|CLAUDE_CODE_OAUTH_TOKEN|OPENAI_API_KEY|XAI_API_KEY|copilot)",
        )

        direct_leak = workflow.replace(
            "          KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}\n",
            "          LEAK: ${{ secrets.KIRO_API_KEY }}\n",
            1,
        )
        extra_direct_leak = workflow.replace(
            "      REVIEW_MODEL: claude-opus-5\n",
            "      REVIEW_MODEL: claude-opus-5\n      LEAK: ${{ secrets.KIRO_API_KEY }}\n",
            1,
        )
        anchor = workflow.replace(
            "      - name: Independent Kiro-hosted Claude Opus 5 review\n"
            "        id: invoke\n"
            "        env:\n",
            "      - name: Independent Kiro-hosted Claude Opus 5 review\n"
            "        id: invoke\n"
            "        env: &review_env\n",
            1,
        )
        alias = workflow.replace(
            "      - name: Validate exact no-tool approval and publish only bound hashes\n"
            "        id: validate\n"
            "        env:\n",
            "      - name: Validate exact no-tool approval and publish only bound hashes\n"
            "        id: validate\n"
            "        env: *review_env\n",
            1,
        )
        merge = workflow.replace(
            "      - name: Validate exact no-tool approval and publish only bound hashes\n"
            "        id: validate\n"
            "        env:\n",
            "      - name: Validate exact no-tool approval and publish only bound hashes\n"
            "        id: validate\n"
            "        env:\n"
            "          <<: *review_env\n",
            1,
        )
        tag = workflow.replace(
            "      - name: Independent Kiro-hosted Claude Opus 5 review\n"
            "        id: invoke\n"
            "        env:\n",
            "      - name: Independent Kiro-hosted Claude Opus 5 review\n"
            "        id: invoke\n"
            "        env: !!map {}\n",
            1,
        )
        unicode_escape = workflow.replace(
            "          BASE_SHA: ${{ needs.resolve.outputs.base_sha }}\n",
            '          LEAK: "${{ secrets.\\u004bIRO_API_KEY }}"\n',
            1,
        )
        doubled_single_quote = workflow.replace(
            "          BASE_SHA: ${{ needs.resolve.outputs.base_sha }}\n",
            "          LEAK: '${{ secrets[''KIRO_API_KEY''] }}'\n",
            1,
        )
        quoted_direct_leak = workflow.replace(
            "          KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}\n",
            '          LEAK: "${{ secrets.KIRO_API_KEY }}"\n',
            1,
        )
        mutations = {
            "direct alternate env name": (
                direct_leak,
                "Kiro environment mapping changed",
            ),
            "extra direct leak": (
                extra_direct_leak,
                "candidate secret context expressions must be exactly",
            ),
            "env anchor": (anchor, "YAML anchor"),
            "env alias": (alias, "YAML alias"),
            "env merge": (merge, "YAML merge"),
            "env tag": (tag, "YAML tag"),
            "unicode quote escape": (
                unicode_escape,
                "YAML double-quoted backslash escapes",
            ),
            "doubled single-quote escape": (
                doubled_single_quote,
                "YAML doubled single-quote escapes",
            ),
            "quoted direct leak": (
                quoted_direct_leak,
                "Kiro environment mapping changed",
            ),
        }
        for label, (mutated, error) in mutations.items():
            with self.subTest(mutation=label):
                self.assertNotEqual(mutated, workflow)
                with self.assertRaisesRegex(WorkflowContractError, error):
                    validate_candidate_workflow_secret_contract(mutated)

    def test_maintenance_workflow_rejects_yaml_indirection_and_scope_bypasses(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml").read_text()
        validate_maintenance_workflow_security_contract(workflow)

        anchored_repair = workflow.replace(
            "      - name: Kiro repair 1 of 2\n        env:\n",
            "      - name: Kiro repair 1 of 2\n        env: &kiro_env\n",
            1,
        )
        exact_bypass = anchored_repair.replace(
            "      - name: Prepare repair 2 without workspace hooks\n",
            "      - name: Fifth effective Kiro credential scope\n"
            "        env: *kiro_env\n"
            "        run: echo bypass\n"
            "      - name: Prepare repair 2 without workspace hooks\n",
            1,
        )
        anchored_step = workflow.replace(
            "      - name: Kiro repair 1 of 2\n",
            "      - &kiro_repair_step\n        name: Kiro repair 1 of 2\n",
            1,
        )
        whole_step_bypass = anchored_step.replace(
            "      - name: Prepare repair 2 without workspace hooks\n",
            "      - *kiro_repair_step\n      - name: Prepare repair 2 without workspace hooks\n",
            1,
        )
        for bypass in (exact_bypass, whole_step_bypass):
            # Both are valid YAML graphs with an extra effective Kiro-secret scope,
            # yet retain the two literal bindings.
            self.assertEqual(
                bypass.count("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}"),
                2,
            )
            self.assertEqual(bypass.count("KIRO_API_KEY"), 4)
            with self.assertRaisesRegex(WorkflowContractError, "YAML anchor"):
                validate_maintenance_workflow_security_contract(bypass)

        mutations = {
            "anchor": workflow.replace(
                "permissions: {}\n",
                "permissions: &workflow_permissions {}\n",
                1,
            ),
            "alias": workflow.replace(
                "permissions: {}\n",
                "permissions: *workflow_permissions\n",
                1,
            ),
            "anchor-name-leading-ampersand": workflow.replace(
                "permissions: {}\n",
                "permissions: &&workflow_permissions {}\n",
                1,
            ),
            "alias-name-leading-asterisk": workflow.replace(
                "permissions: {}\n",
                "permissions: **workflow_permissions\n",
                1,
            ),
            "primary-tag": workflow.replace(
                "permissions: {}\n",
                "permissions: !workflow_permissions {}\n",
                1,
            ),
            "secondary-tag": workflow.replace(
                "permissions: {}\n",
                "permissions: !!map {}\n",
                1,
            ),
            "merge": workflow.replace(
                "permissions: {}\n",
                "permissions:\n  <<: {}\n",
                1,
            ),
            "explicit-key": workflow.replace(
                "permissions: {}\n",
                "? permissions\n: {}\n",
                1,
            ),
            "quoted-protected-env": workflow.replace(
                "      - name: Kiro repair 1 of 2\n        env:\n",
                '      - name: Kiro repair 1 of 2\n        "env":\n',
                1,
            ),
            "fifth-secret-scope": workflow.replace(
                "          READONLY_GITHUB_TOKEN: ${{ github.token }}\n",
                "          READONLY_GITHUB_TOKEN: ${{ github.token }}\n"
                "          KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}\n",
                1,
            ),
            "maintain-extra-property": workflow.replace(
                "      - name: Prepare repair 1 without workspace hooks\n",
                "      - name: Prepare repair 1 without workspace hooks\n"
                "        timeout-minutes: 1\n",
                1,
            ),
            "publish-renamed-step": workflow.replace(
                "      - name: Download candidate package\n",
                "      - name: Download aliased candidate package\n",
                1,
            ),
        }
        for label, mutated in mutations.items():
            with self.subTest(mutation=label):
                self.assertNotEqual(mutated, workflow)
                with self.assertRaises(WorkflowContractError):
                    validate_maintenance_workflow_security_contract(mutated)

        for job in MAINTENANCE_JOB_PROPERTIES:
            with self.subTest(job=job, mutation="extra-job-property"):
                mutated = workflow.replace(
                    f"  {job}:\n",
                    f"  {job}:\n    continue-on-error: false\n",
                    1,
                )
                self.assertNotEqual(mutated, workflow)
                with self.assertRaisesRegex(
                    WorkflowContractError,
                    rf"{job} properties must be exactly",
                ):
                    validate_maintenance_workflow_security_contract(mutated)

        control_flow_mutations = {
            "detect-needs": (
                "    needs: plan\n",
                "    needs: [plan]\n",
            ),
            "detect-if": (
                "    if: needs.plan.outputs.should_run == 'true'\n",
                "    if: always()\n",
            ),
            "maintain-needs": (
                "    needs: [plan, detect]\n",
                "    needs: detect\n",
            ),
            "maintain-if": (
                "    if: needs.detect.outputs.needs_maintenance == 'true'\n",
                "    if: always()\n",
            ),
            "publish-needs": (
                "    needs: [plan, detect, maintain]\n",
                "    needs: maintain\n",
            ),
            "publish-if": (
                "    if: needs.maintain.outputs.has_changes == 'true'\n",
                "    if: always()\n",
            ),
        }
        for label, (before, after) in control_flow_mutations.items():
            with self.subTest(mutation=label):
                mutated = workflow.replace(before, after, 1)
                self.assertNotEqual(mutated, workflow)
                with self.assertRaisesRegex(WorkflowContractError, "control-flow value"):
                    validate_maintenance_workflow_security_contract(mutated)

    def test_actionlint_valid_yaml_scalar_decoding_bypasses_are_rejected(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml").read_text()
        plan_step = (
            "      - name: Harden runner networking\n        uses: step-security/harden-runner@"
        )
        self.assertEqual(workflow.count(plan_step), 4)
        self.assertLess(workflow.index(plan_step), workflow.index("\n  detect:\n"))

        def add_plan_step_env(value: str) -> str:
            return workflow.replace(
                plan_step,
                "      - name: Harden runner networking\n"
                "        env:\n"
                f"          UNAPPROVED: {value}\n"
                "        uses: step-security/harden-runner@",
                1,
            )

        unicode_escape = r'"\u0024{{ toJSON(se\u0063rets) }}"'
        doubled_single_quote = "'${{ ''}}'' && toJSON(secrets) }}'"
        # Actionlint 1.7.7 accepts both full-workflow mutations. Decode the
        # relevant YAML scalar semantics here without requiring Go at unit-test
        # runtime, then require the source-level guard to reject each document.
        self.assertEqual(json.loads(unicode_escape), "${{ toJSON(secrets) }}")
        self.assertEqual(
            doubled_single_quote[1:-1].replace("''", "'"),
            "${{ '}}' && toJSON(secrets) }}",
        )

        decoding_escapes = {
            "exact-unicode-counterexample": unicode_escape,
            "exact-doubled-quote-counterexample": doubled_single_quote,
            "hex-escape": r'"\x24{{ toJSON(secrets) }}"',
            "long-unicode-escape": r'"\U00000024{{ toJSON(secrets) }}"',
            "multiline-backslash-continuation": ('"${{ toJSON(se\\\n            crets) }}"'),
            "multiline-double-quoted-escape": (
                '"prefix\n'
                r'            \u0024{{ toJSON(secrets) }}"'
            ),
            "multiline-single-quoted-escape": (
                "'prefix\n            ${{ ''}}'' && toJSON(secrets) }}'"
            ),
        }
        for label, value in decoding_escapes.items():
            with (
                self.subTest(yaml_escape=label),
                self.assertRaisesRegex(
                    WorkflowContractError,
                    r"YAML .* escapes are forbidden",
                ),
            ):
                validate_maintenance_workflow_security_contract(add_plan_step_env(value))

        inert_comment = (
            "# inert YAML comment: "
            + unicode_escape
            + " and "
            + doubled_single_quote
            + "\n"
            + workflow
        )
        inert_plain_scalar = workflow.replace(
            "name: PKStack Upstream Maintenance (Kiro)\n",
            r"name: literal \u0024 and '' are not decoded here" + "\n",
            1,
        )
        inert_block_scalar = workflow.replace(
            "            api.github.com:443\n",
            "            api.github.com:443\n"
            r"            literal \u0024 and '' stay bytes in a block scalar" + "\n",
            1,
        )
        for label, mutated in {
            "yaml-comment": inert_comment,
            "plain-scalar": inert_plain_scalar,
            "block-scalar": inert_block_scalar,
        }.items():
            with self.subTest(inert_escape=label):
                validate_maintenance_workflow_security_contract(mutated)

    def test_maintenance_validator_owns_secret_context_allowlist(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml").read_text()
        validate_maintenance_workflow_security_contract(workflow)

        insertion_point = "      - name: Resolve trusted base and open-PR guard\n"
        secret_payloads = {
            "whole-context": "${{ secrets }}",
            "serialized-context": "${{ toJSON(secrets) }}",
            "dot-member": "${{ secrets.KIRO_API_KEY }}",
            "single-quoted-bracket-member": "${{ secrets['KIRO_API_KEY'] }}",
            "double-quoted-bracket-member": '${{ secrets["KIRO_API_KEY"] }}',
            "computed-bracket-member": "${{ secrets[format('{0}', 'KIRO_API_KEY')] }}",
            "case-variant": "${{ toJson(SeCrEtS) }}",
        }
        for label, payload in secret_payloads.items():
            with self.subTest(secret_access=label):
                mutated = workflow.replace(
                    insertion_point,
                    "      - name: Unapproved credential context\n"
                    "        env:\n"
                    f"          UNAPPROVED: {payload}\n"
                    "        run: echo guarded\n" + insertion_point,
                    1,
                )
                self.assertNotEqual(mutated, workflow)
                with self.assertRaisesRegex(
                    WorkflowContractError,
                    "secret context expressions must be exactly",
                ):
                    validate_maintenance_workflow_security_contract(mutated)

        quoted_expression = workflow.replace(
            insertion_point,
            '      - name: "${{ toJSON(secrets) }}"\n        run: echo guarded\n' + insertion_point,
            1,
        )
        block_scalar_expression = workflow.replace(
            "          set -euo pipefail\n",
            "          set -euo pipefail\n"
            "          # GitHub expands this before the shell sees its comment.\n"
            "          # ${{ toJSON(secrets) }}\n",
            1,
        )
        for label, mutated in {
            "quoted-yaml-scalar": quoted_expression,
            "block-scalar-shell-comment": block_scalar_expression,
        }.items():
            with (
                self.subTest(secret_access=label),
                self.assertRaisesRegex(
                    WorkflowContractError,
                    "secret context expressions must be exactly",
                ),
            ):
                validate_maintenance_workflow_security_contract(mutated)

        implicit_if_mutations = {
            "plain": "secrets.KIRO_API_KEY != ''",
            "bracket": "secrets['KIRO_API_KEY'] != ''",
            "serialized": "fromJSON(toJSON(secrets)).KIRO_API_KEY != ''",
            "yaml-quoted": "\"secrets['KIRO_API_KEY'] != ''\"",
        }
        for label, condition in implicit_if_mutations.items():
            with self.subTest(implicit_if=label):
                mutated = workflow.replace(
                    insertion_point,
                    "      - name: Unapproved implicit secret condition\n"
                    f"        if: {condition}\n"
                    "        run: echo guarded\n" + insertion_point,
                    1,
                )
                with self.assertRaisesRegex(
                    WorkflowContractError,
                    "secrets context is forbidden in implicit if expressions",
                ):
                    validate_maintenance_workflow_security_contract(mutated)

        block_implicit_if = workflow.replace(
            insertion_point,
            "      - name: Unapproved multiline secret condition\n"
            "        if: |\n"
            "          fromJSON(toJSON(secrets)).KIRO_API_KEY != ''\n"
            "        run: echo guarded\n" + insertion_point,
            1,
        )
        with self.assertRaisesRegex(
            WorkflowContractError,
            "secrets context is forbidden in implicit if expressions",
        ):
            validate_maintenance_workflow_security_contract(block_implicit_if)

        inert_variants = (
            "# ${{ toJSON(secrets) }} is inert YAML commentary.\n" + workflow,
            workflow.replace(
                "name: PKStack Upstream Maintenance (Kiro)\n",
                'name: "PKStack literal toJSON(secrets) documentation"\n',
                1,
            ),
            workflow.replace(
                insertion_point,
                "      - name: ${{ 'literal toJSON(secrets)' }}\n"
                "        run: |\n"
                "          printf '%s\\n' 'literal toJSON(secrets)'\n" + insertion_point,
                1,
            ),
        )
        for index, mutated in enumerate(inert_variants, start=1):
            with self.subTest(inert_variant=index):
                validate_maintenance_workflow_security_contract(mutated)

    def test_yaml_indirection_scanner_ignores_inert_text(self) -> None:
        inert = textwrap.dedent(
            """\
            name: "literal &anchor *alias <<: *merge"
            single: '&anchor *alias <<: *merge'
            # &comment_anchor *comment_alias <<: *comment_merge
            if: left && right
            expression: ${{ !cancelled() }}
            comparison: left != right
            glob: path/**/file
            run: |
              background_task &
              printf '%s\\n' '*alias <<: &anchor !tag'
            """
        )
        _reject_yaml_indirection(_yaml_structural_lines(inert))

    def test_yaml_indirection_scanner_rejects_indicator_prefixed_names_and_tags(
        self,
    ) -> None:
        active_constructs = {
            "anchor-name-leading-ampersand": "node: &&edge {}\n",
            "anchor-name-leading-asterisk": "node: &*edge {}\n",
            "alias-name-leading-asterisk": "node: **edge\n",
            "alias-name-leading-ampersand": "node: *&edge\n",
            "anchor-name-leading-tag": "node: &!edge {}\n",
            "alias-name-leading-tag": "node: *!edge\n",
            "primary-tag": "node: !edge value\n",
            "secondary-tag": "node: !!str value\n",
            "verbatim-tag": "node: !<tag:yaml.org,2002:str> value\n",
        }
        expected_construct = {
            "anchor-name-leading-ampersand": "anchor",
            "anchor-name-leading-asterisk": "anchor",
            "alias-name-leading-asterisk": "alias",
            "alias-name-leading-ampersand": "alias",
            "anchor-name-leading-tag": "anchor",
            "alias-name-leading-tag": "alias",
            "primary-tag": "tag",
            "secondary-tag": "tag",
            "verbatim-tag": "tag",
        }
        for label, source in active_constructs.items():
            with (
                self.subTest(indirection=label),
                self.assertRaisesRegex(
                    WorkflowContractError,
                    rf"YAML {expected_construct[label]} syntax is forbidden",
                ),
            ):
                _reject_yaml_indirection(_yaml_structural_lines(source))

    def test_retained_review_records_do_not_require_external_model_credentials(self) -> None:
        forbidden_prerequisites = (
            "provision ANTHROPIC_API_KEY",
            "provision CLAUDE_CODE_OAUTH_TOKEN",
            "Configure one valid CI credential",
        )
        paths = sorted((ROOT / "Wiki/knowledge").rglob("*.md"))
        paths += sorted((ROOT / ".github/fixtures").glob("*.json"))
        self.assertTrue(paths)
        for path in paths:
            if path.suffix not in {".md", ".json"}:
                continue
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                for phrase in forbidden_prerequisites:
                    self.assertNotIn(phrase, text)

    def test_maintenance_guidance_records_experimental_processing_boundary(self) -> None:
        guidance = (ROOT / "Wiki/features/pkstack-upstream-maintenance.md").read_text()
        self.assertIn("high-risk scheduled semantic-maintenance", guidance)
        self.assertIn("Kiro currently marks Sol experimental", guidance)
        self.assertIn("US-served regardless of profile geography", guidance)
        self.assertIn("commercial AWS Regions worldwide", guidance)
        self.assertIn("makes no claim about storage location", guidance)

    def test_workflow_contracts_are_statically_bound(self) -> None:
        kiro = (ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml").read_text()
        candidate = (ROOT / ".github/workflows/pk-stack-upstream-candidate.yml").read_text()
        smoke = (ROOT / ".github/workflows/pk-stack-kiro-credential-smoke.yml").read_text()
        permission_smoke = (
            ROOT / ".github/workflows/pk-stack-kiro-permission-smoke.yml"
        ).read_text()
        verifier = (ROOT / ".github/scripts/verify_pkstack_attempt.sh").read_text()
        kiro_runner = (ROOT / ".github/scripts/run_kiro_maintenance_attempt.sh").read_text()
        kiro_setup = (ROOT / ".github/scripts/prepare_kiro_maintenance_runtime.sh").read_text()
        self.assertIn("classifyOpenCandidate", kiro)
        self.assertIn("loadSourceRun:", kiro)
        self.assertIn("loadCandidateRuns:", kiro)
        self.assertIn("candidate_lifecycle.workflow_path", kiro)
        self.assertIn("nowMs: Date.now()", kiro)
        self.assertIn(".github/workflows \\", kiro)
        self.assertIn(".github/workflows \\", candidate)
        self.assertNotIn('decision.action === "close"', kiro)
        self.assertIn(".goal.attempt_count == 1", kiro)
        self.assertNotIn(".goal.attempt == 1", kiro)
        self.assertIn("pkstack_update_controller.py", kiro)
        self.assertIn("control_plan_sha256", kiro)
        self.assertIn("goal_kind=$(jq -er '.goal.kind'", kiro)
        self.assertIn('test "$goal_kind" = "command"', kiro)
        self.assertIn('test "$action" = "reconcile-source"', kiro)
        self.assertIn('cron: "17 13 * * *"', kiro)
        self.assertNotIn('cron: "17 13 * * 1"', kiro)
        self.assertIn(
            "preserving the canonical <!-- pk-stack-upstream-genesis: "
            "{canonical JSON} --> marker byte-for-byte",
            kiro_runner,
        )
        self.assertIn("preserving every prior marker unchanged and in order", kiro_runner)
        self.assertIn("review-ledger transition count plus one", kiro_runner)
        self.assertIn(
            "use the exact selected_source_id from the immutable control plan",
            kiro_runner,
        )
        self.assertIn("the proposal must name that source_id", kiro_runner)
        self.assertIn(
            "leave every other drifting source unchanged for a later cadence",
            kiro_runner,
        )
        self.assertIn(
            "The immutable control plan action reconcile-source requires exactly one proposal",
            kiro_runner,
        )
        self.assertNotIn("drift_count", kiro_runner)
        self.assertIn("--trust-tools=fs_read,fs_write,grep", kiro_runner)
        self.assertNotIn("--trust-tools=read,grep", kiro_runner)
        self.assertIn("env -u KIRO_API_KEY python3", kiro_runner)
        self.assertIn("validate-git-state", kiro_runner)
        self.assertLess(
            kiro_runner.index("validate-git-state"),
            kiro_runner.index('cat "$result_path"'),
        )
        self.assertIn(
            "printf 'GIT_BOUNDARY_STATE=%s\\n' \"$RUNNER_TEMP/pkstack-git-boundary-state\"",
            kiro,
        )
        self.assertEqual(kiro.count('--git-state "$GIT_BOUNDARY_STATE"'), 3)
        self.assertEqual(verifier.count('--git-state "$GIT_BOUNDARY_STATE"'), 2)
        self.assertLess(verifier.index("close-attempt"), verifier.index("pkstack_python_static.py"))
        hardened_settings = (
            "GIT_CONFIG_NOSYSTEM=1",
            "GIT_CONFIG_GLOBAL=/dev/null",
            "GIT_CONFIG_SYSTEM=/dev/null",
            "GIT_EXTERNAL_DIFF=",
            "GIT_NO_REPLACE_OBJECTS=1",
            "core.hooksPath=/dev/null",
            "core.fsmonitor=false",
            "diff.external=",
        )
        for hardened_setting in hardened_settings:
            self.assertIn(hardened_setting, verifier)
        self.assertIn("diff --no-ext-diff --no-textconv --name-only", verifier)
        for variable in (
            "GIT_DIR",
            "GIT_COMMON_DIR",
            "GIT_WORK_TREE",
            "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        ):
            self.assertIn(f"export {variable}=", verifier)
            self.assertIn(f"export {variable}=", kiro)
        self.assertIn("finalize-git-state", verifier)
        self.assertIn("finalize-git-state", kiro)
        for hardened_setting in (
            "GIT_CONFIG_NOSYSTEM",
            "GIT_CONFIG_GLOBAL",
            "GIT_CONFIG_SYSTEM",
            "GIT_EXTERNAL_DIFF",
            "GIT_NO_REPLACE_OBJECTS",
            "core.hooksPath",
            "core.fsmonitor",
            "diff.external",
        ):
            self.assertIn(hardened_setting, kiro)
        env_i_blocks = re.findall(
            r'(?ms)^env -i \\\n(?P<body>.*?)(?=^  (?:timeout |python3 -B "\$supervisor" ))',
            kiro_runner,
        )
        self.assertEqual(len(env_i_blocks), 2)
        for block in env_i_blocks:
            for setting in (
                "GIT_DIR=/dev/null",
                "GIT_CONFIG_NOSYSTEM=1",
                "GIT_CONFIG_SYSTEM=/dev/null",
                "GIT_CONFIG_GLOBAL=/dev/null",
                "GIT_EXTERNAL_DIFF=",
                "GIT_NO_REPLACE_OBJECTS=1",
            ):
                self.assertIn(setting, block)
        self.assertIn(': "${TRUSTED_ROOT:?TRUSTED_ROOT is required}"', kiro_setup)
        self.assertIn(
            'trusted_agent="$TRUSTED_ROOT/.kiro/agents/${agent_name}.json"',
            kiro_setup,
        )
        self.assertNotIn("install -m 0600 .kiro/agents/pkstack-maintainer.json", kiro_setup)
        self.assertEqual(
            self.policy["ci_authority"]["runtime_trust_tools"],
            ["fs_read", "fs_write", "grep"],
        )
        for attempt in range(1, 3):
            preparation = re.search(
                rf"(?ms)^      - name: Prepare repair {attempt} without workspace hooks\n"
                r".*?(?=^      - name: |\Z)",
                kiro,
            )
            preparation = require_match(preparation)
            preparation_step = preparation.group(0)
            self.assertLess(
                preparation_step.index("prepare-attempt"),
                preparation_step.index('bash "$KIRO_SETUP_PATH"'),
            )
            verification = re.search(
                rf"(?ms)^      - name: Secretless verification {attempt} of 2\n"
                r".*?(?=^      - name: |\Z)",
                kiro,
            )
            verification = require_match(verification)
            self.assertIn(
                "READONLY_GITHUB_TOKEN: ${{ github.token }}",
                verification.group(0),
            )
            repair = re.search(
                rf"(?ms)^      - name: Kiro repair {attempt} of 2\n"
                r".*?(?=^      - name: |\Z)",
                kiro,
            )
            repair = require_match(repair)
            repair_step = repair.group(0)
            self.assertIn("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}", repair_step)
            self.assertNotIn("READONLY_GITHUB_TOKEN", repair_step)
        self.assertIn("needs.base_ci.result == 'success'", candidate)
        self.assertIn("needs.kiro_peer_review.result == 'success'", candidate)
        self.assertIn(
            "run-name: PKStack candidate gate for source run ${{ github.event.workflow_run.id }}",
            candidate,
        )
        self.assertIn("cleanup_failed_candidate:", candidate)
        self.assertIn("authorizeTerminalCandidateClose", candidate)
        self.assertIn("needs.merge.result != 'success'", candidate)
        self.assertIn("future scheduled maintenance may retry", candidate)
        self.assertIn("REVIEW_MODEL: claude-opus-5", candidate)
        self.assertIn("REVIEW_EFFORT: xhigh", candidate)
        self.assertIn("--agent pkstack-ci-reviewer", candidate)
        self.assertIn("--trust-tools=", candidate)
        self.assertIn("validate_kiro_review_stream.py", candidate)
        self.assertIn("REVIEWED_CONTENT_SHA256", candidate)
        self.assertIn("REVIEWED_CHANGED_FILES", candidate)
        self.assertIn("REVIEWED_PATHS_SHA256", candidate)
        self.assertIn("REVIEWED_AGENT", candidate)
        self.assertIn("REVIEWED_MODEL", candidate)
        self.assertIn("REVIEWED_EFFORT", candidate)
        self.assertIn("EXPECTED_REVIEW_AGENT: pkstack-ci-reviewer", candidate)
        self.assertIn("EXPECTED_REVIEW_MODEL: claude-opus-5", candidate)
        self.assertIn("EXPECTED_REVIEW_EFFORT: xhigh", candidate)
        self.assertIn("execution_evidence_sha256", candidate)
        self.assertIn("REVIEW_ATTESTATION_SHA256", candidate)
        self.assertNotRegex(
            candidate,
            r"ANTHROPIC_API_KEY|CLAUDE_CODE_OAUTH_TOKEN|OPENAI_API_KEY|XAI_API_KEY|copilot",
        )
        self.assertIn("powers/pkstack/skills/", json.dumps(self.policy))
        self.assertIn("TESTED_BASE_SHA", candidate)
        self.assertLess(
            verifier.index("unset READONLY_GITHUB_TOKEN"),
            verifier.index("pkstack_python_static.py"),
        )
        self.assertIn("validate-proposal", verifier)
        self.assertIn("validate-serialized-acceptance", verifier)
        self.assertIn("(( drift_count > 0 ))", verifier)
        self.assertNotIn(
            "trusted_projectctl feature verify pkstack-upstream-maintenance",
            verifier,
        )
        self.assertLess(
            verifier.index("validate-proposal"),
            verifier.index('trusted_accept_with_feedback "$RUNNER_TEMP/pkstack-accept-preview-'),
        )
        self.assertIn("test ! -e .pkstack-maintenance", verifier)
        self.assertNotIn("test ! -e .pkstack/state/upstream-accept.lock", verifier)
        self.assertIn("workflow_dispatch:", smoke)
        self.assertNotIn("schedule:", smoke)
        self.assertGreaterEqual(smoke.count("permissions: {}"), 2)
        self.assertNotIn("actions/checkout", smoke)
        self.assertNotIn("actions/upload-artifact", smoke)
        self.assertEqual(smoke.count("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}"), 1)
        self.assertIn("--agent pkstack-credential-smoke", smoke)
        self.assertNotIn("--agent pkstack-maintainer", smoke)
        self.assertIn("--model gpt-5.6-sol", smoke)
        self.assertIn("--effort max", smoke)
        self.assertIn("--trust-tools=", smoke)
        self.assertIn("chmod -R a-w", smoke)
        self.assertIn("if: always()", smoke)
        credential_prepare = re.search(
            r"(?ms)^      - name: Prepare checksum-pinned isolated Kiro runtime\n"
            r".*?(?=^      - name: Invoke one bounded no-tool Sol credential smoke)",
            smoke,
        )
        credential_invoke = re.search(
            r"(?ms)^      - name: Invoke one bounded no-tool Sol credential smoke\n"
            r".*?(?=^      - name: Remove every credential-smoke runtime and log)",
            smoke,
        )
        credential_prepare = require_match(credential_prepare)
        credential_invoke = require_match(credential_invoke)
        self.assertNotIn(
            "agent validate",
            credential_prepare.group(0),
        )
        self.assertIn(
            "agent validate",
            credential_invoke.group(0),
        )
        self.assertIn(
            'KIRO_API_KEY="$KIRO_API_KEY"',
            credential_invoke.group(0),
        )
        self.assertIn(
            "prompt='PK-STACK-KIRO-AUTH-OK'",
            credential_invoke.group(0),
        )
        self.assertNotIn(
            "Authentication smoke only. Invoke no tools",
            credential_invoke.group(0),
        )
        embedded_agent = re.search(
            r"(?ms)^          CI_AGENT_BASE64: \|-\n"
            r"(?P<body>(?:^            [A-Za-z0-9+/=]+\n)+)"
            r"^        run:",
            smoke,
        )
        embedded_agent = require_match(embedded_agent)
        encoded = "".join(line.strip() for line in embedded_agent.group("body").splitlines())
        credential_agent_raw = base64.b64decode(encoded, validate=True)
        credential_agent = json.loads(credential_agent_raw)
        self.assertEqual(
            credential_agent,
            {
                "name": "pkstack-credential-smoke",
                "description": ("Immutable CI-only tool-free PKStack Kiro credential smoke."),
                "prompt": (
                    "This is an authentication-only smoke. You have no tools or "
                    "resources. Reply exactly PK-STACK-KIRO-AUTH-OK and do nothing else."
                ),
                "tools": [],
                "includeMcpJson": False,
                "includePowers": False,
                "resources": [],
                "permissions": {"rules": []},
                "toolsSettings": {},
                "welcomeMessage": "Tool-free credential smoke fixture loaded.",
            },
        )
        self.assertNotEqual(
            credential_agent_raw,
            (ROOT / ".kiro/agents/pkstack-maintainer.json").read_bytes(),
        )
        embedded_agent_sha = re.search(r"(?m)^          CI_AGENT_SHA256: ([0-9a-f]{64})$", smoke)
        embedded_agent_sha = require_match(embedded_agent_sha)
        self.assertEqual(
            embedded_agent_sha.group(1),
            hashlib.sha256(credential_agent_raw).hexdigest(),
        )
        self.assertIn(
            "$SMOKE_ROOT/workspace/.kiro/agents/pkstack-credential-smoke.json",
            smoke,
        )
        self.assertEqual(
            smoke.count("$SMOKE_ROOT/workspace/.kiro/agents/pkstack-credential-smoke.json"),
            3,
        )
        self.assertNotIn(
            "$SMOKE_ROOT/kiro-home/agents/pkstack-credential-smoke.json",
            smoke,
        )
        self.assertNotIn(
            "$SMOKE_ROOT/user-home/.kiro/agents/pkstack-credential-smoke.json",
            smoke,
        )
        self.assertLess(
            credential_prepare.group(0).index(
                "$SMOKE_ROOT/workspace/.kiro/agents/pkstack-credential-smoke.json"
            ),
            credential_prepare.group(0).index('find "$SMOKE_ROOT/workspace" -type f -print0'),
        )
        self.assertLess(
            credential_prepare.group(0).index('find "$SMOKE_ROOT/workspace" -type f -print0'),
            credential_prepare.group(0).index('chmod -R a-w "$SMOKE_ROOT/workspace"'),
        )
        self.assertIn(
            'grep -Fq \'not found, using "default"\' "$stderr"',
            credential_invoke.group(0),
        )
        self.assertLess(
            credential_invoke.group(0).index("grep -Fq 'not found, using \"default\"'"),
            credential_invoke.group(0).index("actual_workspace_sha256="),
        )
        embedded_validator = re.search(
            r"(?ms)^          STREAM_VALIDATOR_BASE64: \|-\n"
            r"(?P<body>(?:^            [A-Za-z0-9+/=]+\n)+)"
            r"^          CI_AGENT_BASE64:",
            smoke,
        )
        embedded_validator = require_match(embedded_validator)
        encoded_validator = "".join(
            line.strip() for line in embedded_validator.group("body").splitlines()
        )
        embedded_validator_raw = base64.b64decode(encoded_validator, validate=True)
        self.assertEqual(embedded_validator_raw, STREAM_GUARD_PATH.read_bytes())
        embedded_validator_sha = re.search(
            r"(?m)^          STREAM_VALIDATOR_SHA256: ([0-9a-f]{64})$", smoke
        )
        embedded_validator_sha = require_match(embedded_validator_sha)
        self.assertEqual(
            embedded_validator_sha.group(1),
            hashlib.sha256(embedded_validator_raw).hexdigest(),
        )
        self.assertIn("workflow_dispatch:", permission_smoke)
        self.assertNotIn("schedule:", permission_smoke)
        self.assertIn("permissions: {}", permission_smoke)
        self.assertIn("timeout-minutes: 20", permission_smoke)
        self.assertIn("--trust-tools=fs_read,fs_write,grep", permission_smoke)
        self.assertIn("pkstack-permission-fixture", permission_smoke)
        self.assertIn("validate_kiro_permission_stream.py", permission_smoke)
        self.assertIn(
            "$workspace_template/.kiro/agents/pkstack-permission-fixture.json",
            permission_smoke,
        )
        self.assertIn(
            "$workspace/.kiro/agents/pkstack-permission-fixture.json",
            permission_smoke,
        )
        self.assertNotIn(
            "$SMOKE_ROOT/kiro-home/agents/pkstack-permission-fixture.json",
            permission_smoke,
        )
        self.assertNotIn(
            "$SMOKE_ROOT/user-home/.kiro/agents/pkstack-permission-fixture.json",
            permission_smoke,
        )
        self.assertIn(
            hashlib.sha256(
                (ROOT / ".github/fixtures/kiro-permission-agent.json").read_bytes()
            ).hexdigest(),
            permission_smoke,
        )
        self.assertIn(
            hashlib.sha256(PERMISSION_STREAM_GUARD_PATH.read_bytes()).hexdigest(),
            permission_smoke,
        )
        self.assertIn(
            'fixture_permissions["rules"] != expected',
            permission_smoke,
        )
        self.assertIn(
            "production_permissions != fixture_permissions",
            permission_smoke,
        )
        self.assertIn(
            'fixture.get("toolsSettings") != authority["tools_settings"]',
            permission_smoke,
        )
        self.assertIn("agent list", permission_smoke)
        self.assertIn(
            "pkstack-permission-fixture([[:space:]]|$)",
            permission_smoke,
        )
        self.assertIn("--kind allowed", permission_smoke)
        self.assertIn("--kind denied", permission_smoke)
        self.assertIn('run_case allowed 180 allowed "$allowed_prompt"', permission_smoke)
        self.assertIn(
            "path exactly fixture-input.txt, offset exactly 0, and limit exactly 2000",
            permission_smoke,
        )
        self.assertIn(
            "include pattern exactly fixture-input.txt, query exactly ALPHA_TOKEN",
            permission_smoke,
        )
        self.assertIn(
            'run_case "$case_id" 120 denied "$denied_prompt" "$resource"',
            permission_smoke,
        )
        self.assertEqual(permission_smoke.count('"$SMOKE_ROOT/bin/kiro-cli" chat'), 1)
        self.assertIn('test ! -e "$case_root"', permission_smoke)
        self.assertIn('"$case_root/user-home"', permission_smoke)
        self.assertIn('"$case_root/kiro-home/settings"', permission_smoke)
        self.assertIn('"$case_root/runtime"', permission_smoke)
        self.assertIn('"$case_root/logs"', permission_smoke)
        self.assertIn('test ! -e "$case_root/user-home/.kiro"', permission_smoke)
        self.assertIn('find "$case_root" ! -type d ! -type f -print -quit', permission_smoke)
        self.assertGreaterEqual(
            permission_smoke.count("find . ! -type d ! -type f -print -quit"), 3
        )
        for path, _ in permission_stream_guard.ALLOWED_WRITES:
            self.assertIn(path, permission_smoke)
        denied_block = re.search(
            r"(?ms)^          denied_resources=\(\n(?P<body>.*?)^          \)\n",
            permission_smoke,
        )
        denied_block = require_match(denied_block)
        denied_resources = tuple(
            line.strip() for line in denied_block.group("body").splitlines() if line.strip()
        )
        self.assertEqual(denied_resources, permission_stream_guard.DENIED_RESOURCES)
        for path in permission_stream_guard.DENIED_RESOURCES:
            self.assertIn(path, permission_smoke)
        self.assertIn("b'not found, using \"default\"'", permission_smoke)
        self.assertIn(
            'sha256sum --check "$SMOKE_ROOT/template-baseline.sha256"',
            permission_smoke,
        )
        self.assertIn('cmp "$SMOKE_ROOT/template-files.txt"', permission_smoke)
        self.assertIn('cmp "$SMOKE_ROOT/allowed-files.txt"', permission_smoke)
        self.assertGreaterEqual(permission_smoke.count('"$SMOKE_ROOT/template-directories.txt"'), 3)
        self.assertIn("actual-directories.txt", permission_smoke)
        self.assertIn('chmod -R a-w "$GITHUB_WORKSPACE"', permission_smoke)
        self.assertNotIn("git status --porcelain=v1 --untracked-files=all", permission_smoke)
        self.assertNotIn('test -z "$(git status', permission_smoke)
        self.assertNotIn("protected/blocked.txt", permission_smoke)
        self.assertEqual(permission_smoke.count("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}"), 1)
        self.assertNotIn("actions/upload-artifact", permission_smoke)
        self.assertIn('test ! -L "$SMOKE_ROOT"', permission_smoke)
        self.assertIn('test -O "$SMOKE_ROOT"', permission_smoke)
        self.assertEqual(permission_smoke.count('rm -rf -- "$SMOKE_ROOT"'), 1)

    def test_credential_smoke_cleanup_is_exact_and_restores_owner_write(self) -> None:
        smoke = (ROOT / ".github/workflows/pk-stack-kiro-credential-smoke.yml").read_text()
        cleanup_marker = "      - name: Remove every credential-smoke runtime and log\n"
        self.assertEqual(smoke.count(cleanup_marker), 1)
        cleanup_step = smoke.split(cleanup_marker, maxsplit=1)[1]
        run_marker = "        run: |\n"
        self.assertEqual(cleanup_step.count(run_marker), 1)
        indented_script = cleanup_step.split(run_marker, maxsplit=1)[1]
        script_lines = indented_script.splitlines(keepends=True)
        self.assertTrue(
            all(not line.strip() or line.startswith("          ") for line in script_lines)
        )
        cleanup_script = "".join(line[10:] if line.strip() else line for line in script_lines)

        self.assertIn('"$RUNNER_TEMP"/pkstack-kiro-credential-smoke) ;;', cleanup_script)
        self.assertIn('test ! -L "$SMOKE_ROOT"', cleanup_script)
        self.assertIn('test -O "$SMOKE_ROOT"', cleanup_script)
        self.assertEqual(cleanup_script.count('rm -rf -- "$SMOKE_ROOT"'), 1)
        self.assertLess(
            cleanup_script.index('chmod -R u+rwX "$SMOKE_ROOT"'),
            cleanup_script.index('rm -rf -- "$SMOKE_ROOT"'),
        )
        self.assertNotIn('rm -rf -- "$RUNNER_TEMP"', cleanup_script)
        self.assertNotIn('rm -rf -- "$RUNNER_TEMP"/', cleanup_script)
        self.assertNotIn("*pkstack-kiro-credential-smoke*", cleanup_script)

        with tempfile.TemporaryDirectory() as temporary:
            runner_temp = Path(temporary) / "runner-temp"
            runner_temp.mkdir()
            smoke_root = runner_temp / "pkstack-kiro-credential-smoke"
            workspace = smoke_root / "workspace"
            workspace.mkdir(parents=True)
            readonly = workspace / "sentinel.txt"
            readonly.write_text("immutable\n", encoding="utf-8")
            readonly.chmod(0o400)
            workspace.chmod(0o500)
            foreign = runner_temp / "foreign"
            foreign.mkdir()
            foreign_sentinel = foreign / "keep.txt"
            foreign_sentinel.write_text("preserve\n", encoding="utf-8")

            cleanup_env = os.environ.copy()
            cleanup_env.update(
                {
                    "RUNNER_TEMP": str(runner_temp),
                    "SMOKE_ROOT": str(smoke_root),
                }
            )
            completed = subprocess.run(
                ["bash", "-c", cleanup_script],
                env=cleanup_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse(smoke_root.exists())
            self.assertEqual(foreign_sentinel.read_text(encoding="utf-8"), "preserve\n")

            os.symlink(foreign, smoke_root, target_is_directory=True)
            symlink_attempt = subprocess.run(
                ["bash", "-c", cleanup_script],
                env=cleanup_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(symlink_attempt.returncode, 0)
            self.assertTrue(smoke_root.is_symlink())
            self.assertEqual(foreign_sentinel.read_text(encoding="utf-8"), "preserve\n")
            smoke_root.unlink()

            wrong_root = runner_temp / "wrong-root"
            wrong_root.mkdir()
            wrong_sentinel = wrong_root / "keep.txt"
            wrong_sentinel.write_text("preserve\n", encoding="utf-8")
            wrong_env = cleanup_env | {"SMOKE_ROOT": str(wrong_root)}
            wrong_attempt = subprocess.run(
                ["bash", "-c", cleanup_script],
                env=wrong_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(wrong_attempt.returncode, 0)
            self.assertEqual(wrong_sentinel.read_text(encoding="utf-8"), "preserve\n")

    def test_prepare_retry_removes_only_eof_marker_separator_and_keeps_whitespace_guard(
        self,
    ) -> None:
        for trailing_space in (False, True):
            with (
                self.subTest(trailing_space=trailing_space),
                tempfile.TemporaryDirectory() as temporary,
            ):
                sandbox = Path(temporary)
                root = sandbox / "repo"
                manifest = root / "maintenance/upstreams.json"
                ledger = root / "maintenance/upstream-reviews.json"
                provenance = root / "powers/pkstack/provenance/provenance.md"
                manifest.parent.mkdir(parents=True)
                provenance.parent.mkdir(parents=True)
                drift = drift_detector_fixture(transition_count=1)
                accepted = accepted_marker_lines(drift)
                self.assertEqual(len(accepted), 1)
                base_ledger = json.dumps(review_ledger_fixture(drift)) + "\n"
                base_provenance = (
                    f"# Provenance\n\n{accepted[0]}\n\n"
                    "Accepted review detail remains byte-for-byte intact.\n"
                )
                manifest.write_text('{"pin":"base"}\n', encoding="utf-8")
                ledger.write_text(base_ledger, encoding="utf-8")
                provenance.write_text(base_provenance, encoding="utf-8")
                root, base_sha = GitControlBoundaryTests.make_repo(sandbox)

                # A post-accept failure leaves authored prose, then the pending
                # marker at EOF. Its separator is valid until cleanup removes it.
                authored = "Attempt one authored review remains useful after rollback."
                if trailing_space:
                    authored += " "
                expected_provenance = base_provenance + f"\n{authored}\n"
                pending = pending_marker_line(drift)
                provenance.write_text(expected_provenance + f"\n{pending}\n", encoding="utf-8")
                manifest.write_text('{"pin":"accepted"}\n', encoding="utf-8")
                ledger.write_text('{"ledger":"accepted"}\n', encoding="utf-8")
                subprocess.run(["git", "add", "-A"], cwd=root, check=True)
                before = subprocess.run(
                    ["git", "diff", "--cached", "--check", base_sha],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if trailing_space:
                    self.assertNotEqual(before.returncode, 0)
                    self.assertIn("trailing whitespace", before.stdout)
                else:
                    self.assertEqual(before.returncode, 0, before.stdout + before.stderr)

                detector = root / ".git/pkstack-test-detector.json"
                detector.write_text(json.dumps(drift), encoding="utf-8")
                feedback = root / ".git/pkstack-test-feedback.txt"
                feedback.write_text("post-accept gate failed\n", encoding="utf-8")
                git_state = sandbox / "git-boundary-state"
                try:
                    if trailing_space:
                        with self.assertRaisesRegex(guard.GuardError, "trailing whitespace"):
                            guard.prepare_attempt(
                                root, base_sha, self.policy, detector, feedback, git_state
                            )
                        self.assertIn(f"{authored}\n", provenance.read_text(encoding="utf-8"))
                        self.assertFalse(git_state.exists())
                    else:
                        guard.prepare_attempt(
                            root, base_sha, self.policy, detector, feedback, git_state
                        )
                        self.assertEqual(
                            provenance.read_text(encoding="utf-8"), expected_provenance
                        )
                        self.assertTrue((root / ".pkstack-maintenance").is_dir())
                        self.assertTrue((root / ".pkstack-ci/upstream-delta.json").is_file())
                        self.assertTrue(git_state.is_dir())
                    cleaned = provenance.read_text(encoding="utf-8")
                    self.assertTrue(cleaned.startswith(base_provenance))
                    self.assertNotIn(pending, cleaned)
                    self.assertEqual(cleaned.count("pk-stack-upstream-review:"), 1)
                    self.assertEqual(manifest.read_text(encoding="utf-8"), '{"pin":"base"}\n')
                    self.assertEqual(ledger.read_text(encoding="utf-8"), base_ledger)
                finally:
                    if git_state.exists():
                        guard._remove_git_state(root, git_state)

    def test_post_accept_failure_restores_pin_and_ledger_for_attempt_two(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            root = sandbox / "repo"
            root.mkdir()
            (root / "maintenance").mkdir()
            (root / "powers/pkstack/provenance").mkdir(parents=True)
            (root / ".kiro/agents").mkdir(parents=True)
            manifest = root / "maintenance/upstreams.json"
            ledger = root / "maintenance/upstream-reviews.json"
            provenance = root / "powers/pkstack/provenance/provenance.md"
            drift = drift_detector_fixture()
            base_ledger = (
                json.dumps(
                    review_ledger_fixture(drift),
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
            manifest.write_text('{"pin":"base"}\n', encoding="utf-8")
            ledger.write_text(base_ledger, encoding="utf-8")
            provenance.write_text("# Provenance\n\n", encoding="utf-8")
            (root / ".kiro/agents/pkstack.json").write_text("{}\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=PKStack Test",
                    "-c",
                    "user.email=pkstack@example.invalid",
                    "commit",
                    "-qm",
                    "base",
                ],
                cwd=root,
                check=True,
            )
            base_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()

            # Attempt 1 accepted the transition, then a later gate failed.
            manifest.write_text('{"pin":"accepted"}\n', encoding="utf-8")
            ledger.write_text('{"ledger":"accepted"}\n', encoding="utf-8")
            provenance.write_text(
                "# Provenance\n\n"
                f"{pending_marker_line(drift)}\n\n"
                "Attempt one authored review remains useful after rollback.\n",
                encoding="utf-8",
            )
            detector = root / ".git/pkstack-test-detector.json"
            detector.write_text(json.dumps(drift), encoding="utf-8")
            feedback = root / ".git/pkstack-test-feedback.txt"
            feedback.write_text("post-accept gate failed\n", encoding="utf-8")
            control_plan = root / ".git/pkstack-test-control-plan.json"
            control_plan.write_text('{"action":"reconcile-source"}\n', encoding="utf-8")
            memory = root / ".git/pkstack-test-loop-memory.md"
            memory.write_text("# Durable loop feedback\n", encoding="utf-8")
            git_state = sandbox / "git-boundary-state"

            guard.prepare_attempt(
                root,
                base_sha,
                self.policy,
                detector,
                feedback,
                git_state,
                control_plan,
                memory,
            )

            self.assertFalse((root / ".kiro").exists())
            self.assertEqual(
                (root / ".pkstack-ci/control-plan.json").read_text(encoding="utf-8"),
                '{"action":"reconcile-source"}\n',
            )
            self.assertEqual(
                (root / ".pkstack-ci/loop-memory.md").read_text(encoding="utf-8"),
                "# Durable loop feedback\n",
            )
            self.assertEqual(manifest.read_text(encoding="utf-8"), '{"pin":"base"}\n')
            self.assertEqual(ledger.read_text(encoding="utf-8"), base_ledger)
            rolled_back_provenance = provenance.read_text(encoding="utf-8")
            self.assertNotIn("pk-stack-upstream-review:", rolled_back_provenance)
            self.assertIn("Attempt one authored review remains useful", rolled_back_provenance)
            proposal_root = root / ".pkstack-maintenance"
            self.assertTrue(proposal_root.is_dir())
            proposal = proposal_root / "proposal.json"
            proposal.write_text(json.dumps(proposal_fixture(drift)), encoding="utf-8")
            with provenance.open("a", encoding="utf-8") as provenance_stream:
                provenance_stream.write(f"\n{pending_marker_line(drift)}\n")

            validated = guard.validate_proposal(root, detector, proposal)

            self.assertEqual(validated["source_id"], "cursor-pstack")
            self.assertEqual(validated["expected_head"], "c" * 40)
            self.assertEqual(
                provenance.read_text(encoding="utf-8").count("pk-stack-upstream-review:"), 1
            )
            guard._remove_git_state(root, git_state)


@unittest.skipUnless(shutil.which("bash") and shutil.which("jq"), "requires bash and jq")
class ProposalCliContractTests(unittest.TestCase):
    SENTINEL = "UNTRUSTED_PROPOSAL_SECRET_LIKE_VALUE_123"

    def run_proposal_contract(
        self, case: str = "valid", *, expected_head: str = "c" * 40
    ) -> tuple[subprocess.CompletedProcess[str], str]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        detector = drift_detector_fixture(transition_count=1)
        proposal = json.loads(json.dumps(proposal_fixture(detector)))
        selected_source_id = proposal["source_id"]
        detector_path = root / "detector.json"
        detector_path.write_text(json.dumps(detector), encoding="utf-8")
        proposal_path = root / ".pkstack-maintenance/proposal.json"
        proposal_path.parent.mkdir()
        ledger_path = root / "maintenance/upstream-reviews.json"
        ledger_path.parent.mkdir()
        ledger_path.write_text(json.dumps(review_ledger_fixture(detector)), encoding="utf-8")

        for source in detector["sources"]:
            provenance = root / source["provenance_path"]
            provenance.parent.mkdir(parents=True, exist_ok=True)
            markers = accepted_marker_lines(detector, source_id=source["id"])
            if source["id"] == selected_source_id and case != "missing_marker":
                pending = pending_marker_line(detector, source_id=source["id"])
                if case == "noncanonical_marker":
                    pending = pending.replace('":', '": ', 1)
                elif case == "nested_marker_json":
                    pending = (
                        '<!-- pk-stack-upstream-review: {"source_id":'
                        + "[" * 1500
                        + json.dumps(self.SENTINEL)
                        + "]" * 1500
                        + "} -->"
                    )
                    self.assertLessEqual(len(pending), 4096)
                elif case == "wrong_marker_binding":
                    prefix = "<!-- pk-stack-upstream-review: "
                    marker = json.loads(pending[len(prefix) : -len(" -->")])
                    marker["source_id"] = self.SENTINEL
                    pending = review_marker_line(marker)
                markers.append(pending)
            provenance.write_text("# Provenance\n\n" + "\n".join(markers) + "\n", encoding="utf-8")

        if case == "wrong_source":
            proposal["source_id"] = self.SENTINEL
        elif case == "wrong_prior":
            proposal["prior"]["commit"] = "9" * 40
        elif case == "wrong_new":
            proposal["new"]["commit"] = "9" * 40
        elif case == "wrong_digest":
            proposal["inventory_sha256"] = "9" * 64
        elif case == "missing_disposition":
            proposal["dispositions"] = []
        elif case == "invalid_disposition":
            proposal["dispositions"][0]["disposition"] = self.SENTINEL
        elif case == "invalid_rationale":
            proposal["dispositions"][0]["rationale"] = self.SENTINEL + "\n"
        elif case == "invalid_schema":
            proposal["unexpected"] = self.SENTINEL
        raw_proposal = json.dumps(proposal)
        if case == "malformed":
            raw_proposal = '{"source_id":'
        elif case == "nested_proposal_json":
            raw_proposal = (
                '{"source_id":' + "[" * 1500 + json.dumps(self.SENTINEL) + "]" * 1500 + "}"
            )
        elif case == "oversized_integer_json":
            raw_proposal = "{" + json.dumps(self.SENTINEL) + ":" + "9" * 5000 + "}"
        elif case == "duplicate_key":
            raw_proposal = (
                raw_proposal[:-1]
                + ", "
                + json.dumps(self.SENTINEL)
                + ": 0, "
                + json.dumps(self.SENTINEL)
                + ": 1}"
            )
        if case != "missing_file":
            proposal_path.write_text(raw_proposal, encoding="utf-8")

        output_path = root / "guard-output.json"
        result = subprocess.run(
            [
                "bash",
                "-o",
                "pipefail",
                "-c",
                textwrap.dedent("""\
                set -euo pipefail
                "$1" -B "$2" --root "$3" --policy "$4" validate-proposal \\
                  --detector "$5" --proposal "$6" --selected-source-id "$7" \\
                  | tee "$9" \\
                  | jq -e --arg source_id "$7" --arg expected_head "$8" \\
                    '.ok == true and .source_id == $source_id and .expected_head == $expected_head'
                """),
                "proposal-cli-contract",
                sys.executable,
                str(GUARD_PATH),
                str(root),
                str(ROOT / ".github/pkstack-maintenance-policy.json"),
                str(detector_path),
                str(proposal_path),
                selected_source_id,
                expected_head,
                str(output_path),
            ],
            cwd=root,
            env={**os.environ, "PYTHONINTMAXSTRDIGITS": "4300"},
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result, output_path.read_text(encoding="utf-8")

    def test_valid_proposal_and_canonical_marker_pass_real_cli_and_jq(self) -> None:
        result, raw = self.run_proposal_contract()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "true\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            json.loads(raw),
            {
                "ok": True,
                "source_id": "cursor-pstack",
                "expected_head": "c" * 40,
                "disposition_count": 1,
            },
        )

    def test_proposal_failures_emit_only_fixed_reason_codes(self) -> None:
        cases = {
            "missing_file": "proposal-missing",
            "malformed": "proposal-invalid",
            "nested_proposal_json": "proposal-invalid",
            "oversized_integer_json": "proposal-invalid",
            "invalid_schema": "proposal-invalid",
            "duplicate_key": "proposal-invalid",
            "wrong_source": "proposal-binding-mismatch",
            "wrong_prior": "proposal-binding-mismatch",
            "wrong_new": "proposal-binding-mismatch",
            "wrong_digest": "proposal-binding-mismatch",
            "missing_disposition": "proposal-dispositions-invalid",
            "invalid_disposition": "proposal-dispositions-invalid",
            "invalid_rationale": "proposal-dispositions-invalid",
            "missing_marker": "proposal-marker-missing",
            "noncanonical_marker": "proposal-marker-invalid",
            "nested_marker_json": "proposal-marker-invalid",
            "wrong_marker_binding": "proposal-marker-invalid",
        }
        for case, reason in cases.items():
            with self.subTest(case=case):
                result, raw = self.run_proposal_contract(case)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")
                self.assertEqual(result.stdout, "false\n")
                self.assertNotIn(self.SENTINEL, raw + result.stdout + result.stderr)
                self.assertNotIn("Traceback", raw + result.stdout + result.stderr)
                self.assertEqual(json.loads(raw), {"ok": False, "reason": reason})

    def test_jq_rejects_control_plan_expected_head_mismatch(self) -> None:
        result, raw = self.run_proposal_contract(expected_head="f" * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "false\n")
        self.assertEqual(result.stderr, "")
        self.assertTrue(json.loads(raw)["ok"])
        self.assertEqual(json.loads(raw)["expected_head"], "c" * 40)


if __name__ == "__main__":
    unittest.main()
