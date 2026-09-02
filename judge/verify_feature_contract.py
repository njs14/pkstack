#!/usr/bin/env python3
"""Independent, narrow judge for a deployed PK-Stack lab feature contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

MAX_OUTPUT = 8192


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--expected-contract-sha256", required=True)
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
    after = digest(contract)
    if after != before:
        raise SystemExit("contract hash changed during verifier execution")
    if result.returncode != 0 or payload.get("ok") is not True:
        raise SystemExit("labctl verifier did not prove the feature")
    print(json.dumps({"ok": True, "contract_sha256": before}, sort_keys=True))


if __name__ == "__main__":
    main()
