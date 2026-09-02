import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = {
    "Dockerfile", "compose.yaml", "labctl", "projectctl", "pyproject.toml", "uv.lock",
    "requirements-runtime.txt", "judge/verify_feature_contract.py", "Wiki/features/document-export.md",
    "src/pk_stack_lab/__init__.py", "src/pk_stack_lab/aws.py", "src/pk_stack_lab/cli.py",
    "src/pk_stack_lab/config.py", "src/pk_stack_lab/runtime.py",
}


def _payload(*, mismatch: bool = False, missing: bool = False) -> dict[str, object]:
    resources = {"source_digest": "a", "api_image_id": "i", "worker_image_id": "i", "api_task_definition_arn": "ta", "worker_task_definition_arn": "tw"}
    immutable = dict(resources)
    if mismatch:
        immutable["source_digest"] = "stale"
    result: dict[str, object] = {"ok": True, "run": "r", "resources": resources, "immutable": immutable, "business": {"terminal_status": "COMPLETE", "api_idempotency": True, "tenant_key_partition_separation": True}, "task_proof": {"api": "a", "worker": "w", "containers": [{"role": "api", "image": "x", "image_id": "i", "network": "pk-stack-lab-net", "labels": {}, "security": {}}, {"role": "worker", "image": "x", "image_id": "i", "network": "pk-stack-lab-net", "labels": {}, "security": {}}]}}
    if missing:
        result.pop("immutable")
    return result


def _repo(tmp_path: Path, output: str) -> tuple[Path, Path, str]:
    repo = tmp_path / "repo"
    for relative in PROTECTED:
        source, target = ROOT / relative, repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    labctl = repo / "labctl"
    labctl.write_text(f"#!/usr/bin/env python3\nprint({output!r})\n", encoding="utf-8")
    os.chmod(labctl, 0o700)
    manifest = {path: hashlib.sha256((repo / path).read_bytes()).hexdigest() for path in PROTECTED}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    contract = hashlib.sha256((repo / "Wiki/features/document-export.md").read_bytes()).hexdigest()
    return repo, manifest_path, contract


@pytest.mark.parametrize("kind", ["valid", "ok", "stale", "malformed", "missing"])
def test_judge_schema_matrix(tmp_path: Path, kind: str) -> None:
    value: object = _payload(mismatch=kind == "stale", missing=kind == "missing")
    if kind == "ok": value = {"ok": True}
    output = "not-json" if kind == "malformed" else json.dumps(value)
    repo, manifest, contract = _repo(tmp_path, output)
    result = subprocess.run(["python3", str(repo / "judge/verify_feature_contract.py"), "--repo", str(repo), "--expected-contract-sha256", contract, "--control-manifest", str(manifest)], text=True, capture_output=True, check=False)
    assert result.returncode == (0 if kind == "valid" else 1)


def test_judge_rejects_protected_mutation_before_verifier(tmp_path: Path) -> None:
    repo, manifest, contract = _repo(tmp_path, json.dumps(_payload()))
    (repo / "src/pk_stack_lab/runtime.py").write_text("changed", encoding="utf-8")
    result = subprocess.run(["python3", str(repo / "judge/verify_feature_contract.py"), "--repo", str(repo), "--expected-contract-sha256", contract, "--control-manifest", str(manifest)], text=True, capture_output=True, check=False)
    assert result.returncode == 1 and "protected control-plane hash differs" in result.stderr
