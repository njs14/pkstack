#!/usr/bin/env python3
"""Independent, narrow judge for a deployed PK-Stack lab feature contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

MAX_OUTPUT = 8192
PROTECTED_PATHS = {
    "Dockerfile",
    "compose.yaml",
    "labctl",
    "projectctl",
    "pyproject.toml",
    "uv.lock",
    "requirements-runtime.txt",
    "judge/verify_feature_contract.py",
    "Wiki/features/document-export.md",
    "src/pk_stack_lab/__init__.py",
    "src/pk_stack_lab/aws.py",
    "src/pk_stack_lab/cli.py",
    "src/pk_stack_lab/config.py",
    "src/pk_stack_lab/runtime.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--expected-contract-sha256", required=True)
    parser.add_argument("--control-manifest", type=Path, required=True)
    args = parser.parse_args()
    if len(args.expected_contract_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in args.expected_contract_sha256
    ):
        raise SystemExit("expected contract hash must be lowercase SHA-256")
    root = args.repo.resolve()
    contract = root / "Wiki" / "features" / "document-export.md"
    labctl = root / "labctl"
    if not contract.is_file() or not labctl.is_file():
        raise SystemExit("repository lacks the expected contract or labctl")
    if not args.control_manifest.is_file():
        raise SystemExit("control manifest must be an external regular file")
    try:
        manifest = json.loads(args.control_manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit("control manifest is not valid JSON") from exc
    if not isinstance(manifest, dict) or set(manifest) != PROTECTED_PATHS:
        raise SystemExit("control manifest does not cover the exact protected set")
    if any(not isinstance(value, str) or len(value) != 64 for value in manifest.values()):
        raise SystemExit("control manifest contains an invalid hash")
    before_protected = {relative: digest(root / relative) for relative in PROTECTED_PATHS}
    if before_protected != manifest:
        raise SystemExit("protected control-plane hash differs before verifier execution")
    before = digest(contract)
    if before != args.expected_contract_sha256:
        raise SystemExit("contract hash differs before verifier execution")
    result = subprocess.run(
        [str(labctl), "verify", "--output", "json"],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
        timeout=300,
    )
    if len(result.stdout) > MAX_OUTPUT or result.stderr:
        raise SystemExit("verifier output exceeded bound or wrote stderr")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit("verifier did not return JSON") from exc
    after_protected = {relative: digest(root / relative) for relative in PROTECTED_PATHS}
    if after_protected != before_protected or digest(contract) != before:
        raise SystemExit("protected control-plane hash changed during verifier execution")
    business = payload.get("business")
    task_proof = payload.get("task_proof")
    immutable = payload.get("immutable")
    resources = payload.get("resources")
    containers = task_proof.get("containers") if isinstance(task_proof, dict) else None
    if (
        result.returncode != 0
        or payload.get("ok") is not True
        or not isinstance(business, dict)
        or business.get("terminal_status") != "COMPLETE"
        or business.get("api_idempotency") is not True
        or business.get("tenant_key_partition_separation", business.get("tenant_isolation"))
        is not True
        or not isinstance(task_proof, dict)
        or not isinstance(task_proof.get("api"), str)
        or not isinstance(task_proof.get("worker"), str)
        or not isinstance(resources, dict)
        or not isinstance(immutable, dict)
        or not isinstance(immutable.get("source_digest"), str)
        or not isinstance(immutable.get("api_image_id"), str)
        or not isinstance(immutable.get("worker_image_id"), str)
        or not isinstance(immutable.get("api_task_definition_arn"), str)
        or not isinstance(immutable.get("worker_task_definition_arn"), str)
        or immutable.get("source_digest") != resources.get("source_digest")
        or immutable.get("api_image_id") != resources.get("api_image_id")
        or immutable.get("worker_image_id") != resources.get("worker_image_id")
        or immutable.get("api_task_definition_arn") != resources.get("api_task_definition_arn")
        or immutable.get("worker_task_definition_arn") != resources.get("worker_task_definition_arn")
        or not isinstance(containers, list)
        or len(containers) != 2
        or any(
            not isinstance(container, dict)
            or container.get("role") not in {"api", "worker"}
            or not isinstance(container.get("image"), str)
            or not isinstance(container.get("image_id"), str)
            or container.get("network") != "pk-stack-lab-net"
            or not isinstance(container.get("labels"), dict)
            or not isinstance(container.get("security"), dict)
            for container in containers
        )
    ):
        raise SystemExit("labctl verifier did not prove the feature")
    print(
        json.dumps(
            {
                "ok": True,
                "contract_sha256": before,
                "control_manifest_sha256": digest(args.control_manifest),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
