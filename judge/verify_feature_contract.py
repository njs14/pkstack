#!/usr/bin/env python3
"""Independent, narrow judge for a deployed PK-Stack lab feature contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import time
from pathlib import Path

MAX_OUTPUT = 8192
VERIFY_TIMEOUT_SECONDS = 300
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
EXECUTABLE_SOURCE_PATHS = {
    "src/pk_stack_lab/__init__.py",
    "src/pk_stack_lab/aws.py",
    "src/pk_stack_lab/cli.py",
    "src/pk_stack_lab/config.py",
    "src/pk_stack_lab/runtime.py",
}
RESOURCE_FIELDS = {
    "run_id",
    "queue",
    "dlq",
    "table",
    "bucket",
    "cluster",
    "api_service",
    "worker_service",
    "api_family",
    "worker_family",
    "claim_id",
    "docker_context",
    "docker_socket",
    "docker_daemon_id",
    "source_digest",
    "api_image_id",
    "worker_image_id",
    "api_task_definition_arn",
    "worker_task_definition_arn",
}
IMMUTABLE_FIELDS = {
    "source_digest",
    "api_image_id",
    "worker_image_id",
    "api_task_definition_arn",
    "worker_task_definition_arn",
}
SECURITY_FIELDS = {
    "readonly_root_filesystem",
    "cap_drop_all",
    "no_new_privileges",
}
FLOCI_LABELS = {
    "floci": "true",
    "floci_emulator": "floci-aws",
    "io.floci": "aws",
    "io.floci.service": "ecs",
}
RUN_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,30}[a-z0-9])?$")
HEX_32_RE = re.compile(r"^[0-9a-f]{32}$")
HEX_64_RE = re.compile(r"^[0-9a-f]{64}$")
IMAGE_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
EXPORT_RE = re.compile(r"^e-[0-9a-f]{16}$")
TASK_ID_RE = re.compile(r"^[0-9a-f]{32}$")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _kill_verifier(process: subprocess.Popen[bytes]) -> None:
    """Kill the verifier process group and reap its direct child."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass


def _run_verifier(
    labctl: Path,
    root: Path,
    *,
    timeout_seconds: float = VERIFY_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """Capture verifier output without allowing either pipe to grow unbounded."""
    process = subprocess.Popen(
        [str(labctl), "verify", "--output", "json"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    assert process.stdout is not None and process.stderr is not None
    stdout = bytearray()
    deadline = time.monotonic() + timeout_seconds
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _kill_verifier(process)
                raise SystemExit("verifier timed out")
            events = selector.select(remaining)
            if not events:
                _kill_verifier(process)
                raise SystemExit("verifier timed out")
            for key, _ in events:
                read_limit = 1 if key.data == "stderr" else MAX_OUTPUT + 1 - len(stdout)
                chunk = os.read(key.fd, max(1, min(4096, read_limit)))
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                if key.data == "stderr":
                    _kill_verifier(process)
                    raise SystemExit("verifier wrote stderr")
                stdout.extend(chunk)
                if len(stdout) > MAX_OUTPUT:
                    _kill_verifier(process)
                    raise SystemExit("verifier stdout exceeded bound")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _kill_verifier(process)
            raise SystemExit("verifier timed out")
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            _kill_verifier(process)
            raise SystemExit("verifier timed out") from exc
    finally:
        selector.close()
        process.stdout.close()
        process.stderr.close()
    try:
        output = stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SystemExit("verifier output was not UTF-8") from exc
    return subprocess.CompletedProcess(
        args=[str(labctl), "verify", "--output", "json"],
        returncode=returncode,
        stdout=output,
        stderr="",
    )


def _direct_regular(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    return stat.S_ISREG(info.st_mode) and not path.is_symlink()


def _locked_external_file(path: Path, root: Path, label: str) -> Path:
    if path.is_symlink():
        raise SystemExit(f"{label} must not be a symlink")
    try:
        resolved = path.resolve(strict=True)
        info = resolved.lstat()
    except OSError as exc:
        raise SystemExit(f"{label} must be an external regular file") from exc
    if resolved.is_relative_to(root):
        raise SystemExit(f"{label} must be outside the repository")
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.geteuid()
        or info.st_nlink != 1
        or stat.S_IMODE(info.st_mode) & 0o222
    ):
        raise SystemExit(f"{label} must be an owner-controlled, read-only direct regular file")
    return resolved


def _validate_executable_source_closure(root: Path) -> None:
    """Reject unmanifested source, bytecode, and import-time customization."""
    source = root / "src"
    if source.is_symlink() or not source.is_dir():
        raise SystemExit("repository executable source root is not a direct directory")
    files: set[str] = set()
    directories: set[str] = set()
    for path in source.rglob("*"):
        if path.is_symlink():
            raise SystemExit("repository executable source closure contains a symlink")
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            directories.add(relative)
        elif path.is_file():
            files.add(relative)
        else:
            raise SystemExit("repository executable source closure contains a special file")
    if files != EXECUTABLE_SOURCE_PATHS or directories != {"src/pk_stack_lab"}:
        raise SystemExit("repository executable source closure differs from the protected set")
    for name in ("sitecustomize.py", "usercustomize.py"):
        candidate = root / name
        if candidate.exists() or candidate.is_symlink():
            raise SystemExit("repository root contains an import-time customization module")


def _exact_dict(value: object, keys: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == keys


def _task_definition(arn: object, family: str) -> bool:
    return isinstance(arn, str) and bool(
        re.fullmatch(
            rf"arn:aws:ecs:us-east-1:000000000000:task-definition/{re.escape(family)}:[1-9][0-9]*",
            arn,
        )
    )


def _task_id(arn: object, cluster: str) -> str | None:
    if not isinstance(arn, str):
        return None
    match = re.fullmatch(
        rf"arn:aws:ecs:us-east-1:000000000000:task/{re.escape(cluster)}/([0-9a-f]{{32}})",
        arn,
    )
    return match.group(1) if match else None


def _valid_resources(value: object, run: str) -> bool:
    if not _exact_dict(value, RESOURCE_FIELDS):
        return False
    assert isinstance(value, dict)
    if any(not isinstance(item, str) for item in value.values()):
        return False
    prefix = f"pklab-{run}"
    derived = {
        "run_id": run,
        "queue": f"{prefix}-exports",
        "dlq": f"{prefix}-exports-dlq",
        "table": f"{prefix}-exports",
        "bucket": f"{prefix}-results",
        "cluster": f"{prefix}-cluster",
        "api_service": f"{prefix}-api",
        "worker_service": f"{prefix}-worker",
        "api_family": f"{prefix}-api",
        "worker_family": f"{prefix}-worker",
    }
    if any(value.get(key) != expected for key, expected in derived.items()):
        return False
    source = value["source_digest"]
    image_id = value["api_image_id"]
    return bool(
        HEX_32_RE.fullmatch(value["claim_id"])
        and value["docker_context"]
        and value["docker_socket"].startswith("unix:///")
        and "\n" not in value["docker_socket"]
        and value["docker_daemon_id"]
        and HEX_64_RE.fullmatch(source)
        and IMAGE_ID_RE.fullmatch(image_id)
        and value["worker_image_id"] == image_id
        and _task_definition(value["api_task_definition_arn"], value["api_family"])
        and _task_definition(value["worker_task_definition_arn"], value["worker_family"])
    )


def _valid_security(value: object) -> bool:
    if not _exact_dict(
        value,
        {"user", "non_root", "mounts", "requested", "effective", "emulator_limitations"},
    ):
        return False
    assert isinstance(value, dict)
    requested = value["requested"]
    effective = value["effective"]
    if (
        value["user"] != "65532:65532"
        or value["non_root"] is not True
        or value["mounts"] != []
        or not _exact_dict(requested, SECURITY_FIELDS)
        or not _exact_dict(effective, SECURITY_FIELDS)
    ):
        return False
    assert isinstance(requested, dict) and isinstance(effective, dict)
    if any(requested[field] is not True for field in SECURITY_FIELDS) or any(
        not isinstance(effective[field], bool) for field in SECURITY_FIELDS
    ):
        return False
    expected_limitations = [
        field
        for field in ("readonly_root_filesystem", "cap_drop_all", "no_new_privileges")
        if effective[field] is not True
    ]
    return value["emulator_limitations"] == expected_limitations


def _valid_container(
    value: object,
    *,
    role: str,
    task_id: str,
    run: str,
    source_digest: str,
    image_id: str,
) -> bool:
    if not _exact_dict(
        value, {"name", "role", "image", "image_id", "network", "security", "labels"}
    ):
        return False
    assert isinstance(value, dict)
    labels = value["labels"]
    expected_labels = {**FLOCI_LABELS, "io.floci.resource-id": task_id}
    return bool(
        value["name"] == f"floci-ecs-{task_id}-{role}"
        and value["role"] == role
        and value["image"] == f"pklab-{run}-{role}:{source_digest[:24]}"
        and value["image_id"] == image_id
        and value["network"] == "pk-stack-lab-net"
        and labels == expected_labels
        and _valid_security(value["security"])
    )


def _valid_payload(payload: object) -> bool:
    if not _exact_dict(
        payload,
        {"ok", "run", "api_transport", "resources", "immutable", "business", "task_proof"},
    ):
        return False
    assert isinstance(payload, dict)
    run = payload["run"]
    resources = payload["resources"]
    immutable = payload["immutable"]
    business = payload["business"]
    task_proof = payload["task_proof"]
    if (
        payload["ok"] is not True
        or not isinstance(run, str)
        or not RUN_RE.fullmatch(run)
        or payload["api_transport"]
        != "bounded HTTP from a transient hardened verifier container to the exact real ECS API task"
        or not _valid_resources(resources, run)
        or not _exact_dict(immutable, IMMUTABLE_FIELDS)
        or not _exact_dict(
            business,
            {
                "export_id",
                "terminal_status",
                "s3_result",
                "tenant_key_partition_separation",
                "api_idempotency",
                "worker_duplicate_delivery",
                "dlq",
            },
        )
        or not _exact_dict(task_proof, {"api", "worker", "containers", "post_business_reproof"})
    ):
        return False
    assert isinstance(resources, dict)
    assert isinstance(immutable, dict)
    assert isinstance(business, dict)
    assert isinstance(task_proof, dict)
    if immutable != {field: resources[field] for field in IMMUTABLE_FIELDS}:
        return False
    export_id = business["export_id"]
    s3_result = business["s3_result"]
    api_idempotency = business["api_idempotency"]
    duplicate = business["worker_duplicate_delivery"]
    dlq = business["dlq"]
    expected_body = {"tenant": "tenant-a", "export_id": export_id}
    if (
        not isinstance(export_id, str)
        or not EXPORT_RE.fullmatch(export_id)
        or business["terminal_status"] != "COMPLETE"
        or business["tenant_key_partition_separation"] is not True
        or not _exact_dict(
            api_idempotency,
            {
                "duplicate_marker",
                "duplicate_status",
                "same_export_id",
                "row_idempotency_matches",
                "enqueue_confirmed",
                "attempts",
            },
        )
        or not isinstance(api_idempotency, dict)
        or api_idempotency["duplicate_marker"] is not True
        or api_idempotency["duplicate_status"] not in ("QUEUED", "COMPLETE")
        or api_idempotency["same_export_id"] is not True
        or api_idempotency["row_idempotency_matches"] is not True
        or api_idempotency["enqueue_confirmed"] is not True
        or type(api_idempotency["attempts"]) is not int
        or api_idempotency["attempts"] != 1
        or not _exact_dict(s3_result, {"key", "content_type", "body", "etag"})
        or not isinstance(s3_result, dict)
        or s3_result["key"] != f"exports/tenant-a/{export_id}.json"
        or s3_result["content_type"] != "application/json"
        or s3_result["body"] != expected_body
        or not isinstance(s3_result["etag"], str)
        or not s3_result["etag"]
        or len(s3_result["etag"]) > 256
        or duplicate != {"attempts": 1, "s3_identity_unchanged": True, "consumed_noop": True}
        or not _exact_dict(dlq, {"current_invocation", "message_id"})
        or not isinstance(dlq, dict)
        or dlq["current_invocation"] is not True
        or not isinstance(dlq["message_id"], str)
        or not dlq["message_id"]
        or task_proof["post_business_reproof"] is not True
    ):
        return False
    cluster = resources["cluster"]
    api_id = _task_id(task_proof["api"], cluster)
    worker_id = _task_id(task_proof["worker"], cluster)
    containers = task_proof["containers"]
    if (
        api_id is None
        or worker_id is None
        or api_id == worker_id
        or not isinstance(containers, list)
        or len(containers) != 2
    ):
        return False
    by_role = {
        container.get("role"): container
        for container in containers
        if isinstance(container, dict) and container.get("role") in {"api", "worker"}
    }
    return (
        set(by_role) == {"api", "worker"}
        and _valid_container(
            by_role["api"],
            role="api",
            task_id=api_id,
            run=run,
            source_digest=resources["source_digest"],
            image_id=resources["api_image_id"],
        )
        and _valid_container(
            by_role["worker"],
            role="worker",
            task_id=worker_id,
            run=run,
            source_digest=resources["source_digest"],
            image_id=resources["worker_image_id"],
        )
    )


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
    root = args.repo.resolve(strict=True)
    judge_path = _locked_external_file(Path(__file__), root, "judge")
    manifest_path = _locked_external_file(args.control_manifest, root, "control manifest")
    _validate_executable_source_closure(root)
    contract = root / "Wiki" / "features" / "document-export.md"
    labctl = root / "labctl"
    if not _direct_regular(contract) or not _direct_regular(labctl):
        raise SystemExit("repository lacks the expected contract or labctl")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit("control manifest is not valid JSON") from exc
    if not isinstance(manifest, dict) or set(manifest) != PROTECTED_PATHS:
        raise SystemExit("control manifest does not cover the exact protected set")
    if any(not isinstance(value, str) or len(value) != 64 for value in manifest.values()):
        raise SystemExit("control manifest contains an invalid hash")
    if any(not _direct_regular(root / relative) for relative in PROTECTED_PATHS):
        raise SystemExit("protected control plane contains a missing, linked, or special file")
    if digest(judge_path) != manifest["judge/verify_feature_contract.py"]:
        raise SystemExit("external judge differs from the protected repository judge")
    manifest_sha256 = digest(manifest_path)
    before_protected = {relative: digest(root / relative) for relative in PROTECTED_PATHS}
    if before_protected != manifest:
        raise SystemExit("protected control-plane hash differs before verifier execution")
    before = digest(contract)
    if before != args.expected_contract_sha256:
        raise SystemExit("contract hash differs before verifier execution")
    result = _run_verifier(labctl, root)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit("verifier did not return JSON") from exc
    after_protected = {relative: digest(root / relative) for relative in PROTECTED_PATHS}
    if (
        after_protected != before_protected
        or digest(contract) != before
        or digest(judge_path) != manifest["judge/verify_feature_contract.py"]
        or digest(manifest_path) != manifest_sha256
    ):
        raise SystemExit("protected control-plane hash changed during verifier execution")
    if result.returncode != 0 or not _valid_payload(payload):
        raise SystemExit("labctl verifier did not prove the feature")
    print(
        json.dumps(
            {
                "ok": True,
                "contract_sha256": before,
                "control_manifest_sha256": manifest_sha256,
                "judge_sha256": digest(judge_path),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
