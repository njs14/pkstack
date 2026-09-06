#!/usr/bin/env python3
"""Bounded durable reviewer feedback: one report and rejection count per source."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any

SOURCE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SHA1 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
MAX_REJECTIONS = 3
MAX_BYTES = 1024 * 1024


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate feedback key")
        result[key] = value
    return result


def read_document(path: Path) -> dict[str, Any]:
    metadata = path.lstat()  # Missing history is an error, never a fresh budget.
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_BYTES:
        raise ValueError("feedback must be a bounded regular file")
    result = json.loads(path.read_bytes(), object_pairs_hook=_object)
    if not isinstance(result, dict):
        raise ValueError("feedback must be an object")
    return result


def _text(value: Any, maximum: int) -> bool:
    return (
        isinstance(value, str)
        and value == value.strip()
        and 0 < len(value.encode()) <= maximum
        and all(ord(char) >= 32 for char in value)
    )


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "schema_version",
        "source_id",
        "source_commit",
        "source_subtree_sha",
        "source_run_id",
        "candidate_run_id",
        "base_sha",
        "head_sha",
        "content_sha256",
        "patch_sha256",
        "verdict",
        "material_findings",
        "summary",
    }
    if set(report) != expected or report["schema_version"] != 1:
        raise ValueError("review report schema changed")
    if (
        not isinstance(report["source_id"], str)
        or len(report["source_id"]) > 64
        or not SOURCE.fullmatch(report["source_id"])
    ):
        raise ValueError("review report source is invalid")
    for key in ("source_commit", "source_subtree_sha", "base_sha", "head_sha"):
        if not isinstance(report[key], str) or not SHA1.fullmatch(report[key]):
            raise ValueError(f"review report {key} is invalid")
    for key in ("content_sha256", "patch_sha256"):
        if not isinstance(report[key], str) or not SHA256.fullmatch(report[key]):
            raise ValueError(f"review report {key} is invalid")
    for key in ("source_run_id", "candidate_run_id"):
        if type(report[key]) is not int or not 0 < report[key] < 2**53:
            raise ValueError(f"review report {key} is invalid")
    findings = report["material_findings"]
    if (
        not isinstance(findings, list)
        or len(findings) > 32
        or not all(_text(item, 2000) for item in findings)
        or not _text(report["summary"], 4000)
    ):
        raise ValueError("review report prose is not bounded plain text")
    if report["verdict"] not in {"approved", "rejected"}:
        raise ValueError("review report verdict is invalid")
    if (report["verdict"] == "approved") != (not findings):
        raise ValueError("review report verdict contradicts its findings")
    return report


def load_ledger(path: Path) -> dict[str, Any]:
    ledger = read_document(path)
    if set(ledger) != {"schema_version", "sources"} or ledger["schema_version"] != 1:
        raise ValueError("feedback ledger schema changed")
    records = ledger["sources"]
    if not isinstance(records, dict) or len(records) > 16:
        raise ValueError("feedback source inventory is unbounded")
    for source_id, entry in records.items():
        if not isinstance(entry, dict) or set(entry) != {"rejection_count", "report"}:
            raise ValueError("feedback record schema changed")
        report = validate_report(entry["report"])
        if source_id != report["source_id"] or report["verdict"] != "rejected":
            raise ValueError("feedback record is not a source-bound rejection")
        if (
            type(entry["rejection_count"]) is not int
            or not 1 <= entry["rejection_count"] <= MAX_REJECTIONS
        ):
            raise ValueError("feedback rejection count is outside its budget")
    return ledger


def source_feedback(ledger: dict[str, Any], source_id: str, subtree_sha: str) -> tuple[int, Any]:
    entry = ledger["sources"].get(source_id)
    if entry is None or entry["report"]["source_subtree_sha"] != subtree_sha:
        return 0, None
    return entry["rejection_count"], entry["report"]


def record_rejection(
    ledger: dict[str, Any], report: dict[str, Any], *, retry_override: bool
) -> dict[str, Any]:
    validate_report(report)
    if report["verdict"] != "rejected":
        raise ValueError("only substantive validated rejections consume the budget")
    count, previous = source_feedback(ledger, report["source_id"], report["source_subtree_sha"])
    # Ordering belongs to the source, not just its current subtree: a delayed
    # publisher must not overwrite newer content with an old fresh budget.
    latest = ledger["sources"].get(report["source_id"])
    previous = latest["report"] if latest else None
    if previous and previous["candidate_run_id"] == report["candidate_run_id"]:
        if previous != report:
            raise ValueError("same candidate run produced conflicting feedback")
        return ledger  # Idempotent workflow reruns cannot double-count.
    if previous and report["candidate_run_id"] < previous["candidate_run_id"]:
        raise ValueError("older candidate cannot replace newer feedback")
    if retry_override:
        if count != MAX_REJECTIONS:
            raise ValueError("retry override requires an exhausted exact source content")
        count = 0
    if count >= MAX_REJECTIONS:
        raise ValueError("review budget is exhausted")
    records = {
        **ledger["sources"],
        report["source_id"]: {"rejection_count": count + 1, "report": report},
    }
    return {"schema_version": 1, "sources": records}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--source-run-id", type=int, required=True)
    parser.add_argument("--candidate-run-id", type=int, required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--retry-override", choices=("true", "false"), default="false")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ledger = load_ledger(args.ledger)
    report = validate_report(read_document(args.report))
    if hashlib.sha256(args.report.read_bytes()).hexdigest() != args.expected_sha256:
        raise ValueError("review report artifact digest changed")
    for key, value in (
        ("source_run_id", args.source_run_id),
        ("candidate_run_id", args.candidate_run_id),
        ("base_sha", args.base),
        ("head_sha", args.head),
    ):
        if report[key] != value:
            raise ValueError(f"review report is not bound to authenticated {key}")
    result = record_rejection(ledger, report, retry_override=args.retry_override == "true")
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if len(encoded.encode()) > MAX_BYTES:
        raise ValueError("feedback ledger byte budget exceeded")
    args.output.write_text(encoded, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
