#!/usr/bin/env python3
"""Turn validated PK-Stack sensor output into one bounded maintenance decision."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pk_stack_maintenance_guard as guard
import pk_stack_review_feedback as feedback


def decide(
    detector_path: Path,
    feedback_path: Path = Path(__file__).resolve().parents[2]
    / "maintenance/upstream-feedback.json",
    retry_source: str = "",
) -> dict[str, object]:
    before_sha256 = hashlib.sha256(detector_path.read_bytes()).hexdigest()
    detector = guard.validate_detector(detector_path)
    sensor_sha256 = hashlib.sha256(detector_path.read_bytes()).hexdigest()
    if sensor_sha256 != before_sha256:
        raise guard.GuardError(
            "upstream detector changed while the controller was deciding"
        )
    drifts = detector["validated_drift_sources"]
    ledger = feedback.load_ledger(feedback_path)
    sources = {source["id"]: source for source in detector.get("sources", [])}
    eligible = []
    exhausted = []
    retry_id = None
    if retry_source:
        retry_id, separator, retry_tree = retry_source.partition("@")
        source = sources.get(retry_id)
        if (
            not separator
            or not source
            or source["current"]["subtree_sha"] != retry_tree
            or not source["drift"]
            or feedback.source_feedback(ledger, retry_id, retry_tree)[0]
            != feedback.MAX_REJECTIONS
        ):
            raise ValueError(
                "retry_source must name an exhausted drifting source@exact-subtree-sha"
            )
    for drift in drifts:
        source_id = drift["source_id"]
        source = sources.get(source_id)
        tree = source["current"]["subtree_sha"] if source else ""
        count, _ = feedback.source_feedback(ledger, source_id, tree)
        if count >= feedback.MAX_REJECTIONS and source_id != retry_id:
            exhausted.append(source_id)
        else:
            eligible.append(drift)
    selected = next((item for item in eligible if item["source_id"] == retry_id), None)
    if selected is None and eligible:
        selected = eligible[0]
    if selected:
        source_id = selected["source_id"]
        action = "reconcile-source"
        objective = f"Reconcile PK-Stack with selected upstream source {source_id}"
        goal = {
            "kind": "command",
            "value": (
                ".pk-stack/bin/projectctl upstream check "
                "--manifest maintenance/upstreams.json --power-root powers/pk-stack "
                f"--source-id {source_id} --output json"
            ),
        }
    elif drifts:
        source_id = None
        action = "exhausted"
        objective = "Upstream sources require an explicit source-bound retry after three rejections"
        goal = None
    elif detector["ok"] is True:
        source_id = None
        action = "current"
        objective = "PK-Stack upstream and generated parity are current"
        goal = None
    else:
        source_id = None
        action = "manual-parity"
        objective = "Generated/source parity needs a reviewed deterministic setup run"
        goal = None
    source = sources.get(source_id) if source_id else None
    tree = source["current"]["subtree_sha"] if source else None
    count, report = (
        feedback.source_feedback(ledger, source_id, tree) if source else (0, None)
    )
    return {
        "schema_version": 1,
        "action": action,
        "selected_source_id": source_id,
        "expected_head": selected["expected_head"] if selected else None,
        "source_subtree_sha": tree,
        "prior_rejections": count,
        "review_feedback": report,
        "retry_override": source_id is not None and source_id == retry_id,
        "exhausted_sources": exhausted,
        "drift_count": len(drifts),
        "sensor_sha256": sensor_sha256,
        "objective": objective,
        "goal": goal,
        "max_attempts": 5,
        "max_open_candidates": 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--detector", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--feedback", type=Path, required=True)
    parser.add_argument("--retry-source", default="")
    args = parser.parse_args()
    decision = decide(args.detector, args.feedback, args.retry_source)
    args.output.write_text(
        json.dumps(decision, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
