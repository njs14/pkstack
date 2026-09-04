#!/usr/bin/env python3
"""Turn validated PK-Stack sensor output into one bounded maintenance decision."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pk_stack_maintenance_guard as guard


def decide(detector_path: Path) -> dict[str, object]:
    before_sha256 = hashlib.sha256(detector_path.read_bytes()).hexdigest()
    detector = guard.validate_detector(detector_path)
    sensor_sha256 = hashlib.sha256(detector_path.read_bytes()).hexdigest()
    if sensor_sha256 != before_sha256:
        raise guard.GuardError("upstream detector changed while the controller was deciding")
    drifts = detector["validated_drift_sources"]
    if drifts:
        source_id = drifts[0]["source_id"]
        action = "reconcile-source"
        objective = f"Reconcile PK-Stack with selected upstream source {source_id}"
        goal = {
            "kind": "command",
            "value": (
                ".pstack/bin/projectctl upstream check "
                "--manifest maintenance/upstreams.json --power-root powers/pk-stack "
                f"--source-id {source_id} --output json"
            ),
        }
    elif detector["ok"] is True:
        source_id = None
        action = "current"
        objective = "PK-Stack upstream and generated parity are current"
        goal = None
    else:
        source_id = None
        action = "repair-parity"
        objective = "Restore PK-Stack generated and source parity"
        goal = {"kind": "feature", "value": "pk-stack-upstream-maintenance"}
    return {
        "schema_version": 1,
        "action": action,
        "selected_source_id": source_id,
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
    args = parser.parse_args()
    decision = decide(args.detector)
    args.output.write_text(
        json.dumps(decision, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
