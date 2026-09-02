import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from pk_stack_lab import cli
from pk_stack_lab.config import ArtifactEvent, RunState

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = {
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


def _payload(*, mismatch: bool = False, missing: bool = False) -> dict[str, object]:
    run = "r"
    prefix = f"pklab-{run}"
    source_digest = "a" * 64
    image_id = "sha256:" + "b" * 64
    api_task_id = "c" * 32
    worker_task_id = "d" * 32
    resources = {
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
        "claim_id": "e" * 32,
        "docker_context": "desktop-linux",
        "docker_socket": "unix:///tmp/docker.sock",
        "docker_daemon_id": "daemon-id",
        "source_digest": source_digest,
        "api_image_id": image_id,
        "worker_image_id": image_id,
        "api_task_definition_arn": (
            f"arn:aws:ecs:us-east-1:000000000000:task-definition/{prefix}-api:1"
        ),
        "worker_task_definition_arn": (
            f"arn:aws:ecs:us-east-1:000000000000:task-definition/{prefix}-worker:1"
        ),
    }
    immutable = {
        key: resources[key]
        for key in (
            "source_digest",
            "api_image_id",
            "worker_image_id",
            "api_task_definition_arn",
            "worker_task_definition_arn",
        )
    }
    if mismatch:
        immutable["source_digest"] = "stale"
    export_id = "e-" + "f" * 16

    def container(role: str, task_id: str) -> dict[str, object]:
        return {
            "name": f"floci-ecs-{task_id}-{role}",
            "role": role,
            "image": f"{prefix}-{role}:{source_digest[:24]}",
            "image_id": image_id,
            "network": "pk-stack-lab-net",
            "labels": {
                "floci": "true",
                "floci_emulator": "floci-aws",
                "io.floci": "aws",
                "io.floci.service": "ecs",
                "io.floci.resource-id": task_id,
            },
            "security": {
                "user": "65532:65532",
                "non_root": True,
                "mounts": [],
                "requested": {
                    "readonly_root_filesystem": True,
                    "cap_drop_all": True,
                    "no_new_privileges": True,
                },
                "effective": {
                    "readonly_root_filesystem": False,
                    "cap_drop_all": False,
                    "no_new_privileges": False,
                },
                "emulator_limitations": [
                    "readonly_root_filesystem",
                    "cap_drop_all",
                    "no_new_privileges",
                ],
            },
        }

    result: dict[str, object] = {
        "ok": True,
        "run": run,
        "api_transport": (
            "bounded HTTP from a transient hardened verifier container "
            "to the exact real ECS API task"
        ),
        "resources": resources,
        "immutable": immutable,
        "business": {
            "export_id": export_id,
            "terminal_status": "COMPLETE",
            "s3_result": {
                "key": f"exports/tenant-a/{export_id}.json",
                "content_type": "application/json",
                "body": {"tenant": "tenant-a", "export_id": export_id},
                "etag": '"concrete-etag"',
            },
            "api_idempotency": True,
            "tenant_key_partition_separation": True,
            "worker_duplicate_delivery": {
                "attempts": 1,
                "s3_identity_unchanged": True,
                "consumed_noop": True,
            },
            "dlq": {"current_invocation": True, "message_id": "message-id"},
        },
        "task_proof": {
            "api": (f"arn:aws:ecs:us-east-1:000000000000:task/{prefix}-cluster/{api_task_id}"),
            "worker": (
                f"arn:aws:ecs:us-east-1:000000000000:task/{prefix}-cluster/{worker_task_id}"
            ),
            "containers": [container("api", api_task_id), container("worker", worker_task_id)],
            "post_business_reproof": True,
        },
    }
    if missing:
        result.pop("immutable")
    return result


def _complete_resource_projection_state() -> RunState:
    """Mirror one real, fully journaled deployment for the producer/consumer bridge."""
    base = RunState.create(
        "r",
        claim_id="e" * 32,
        docker_context="desktop-linux",
        docker_socket="unix:///tmp/docker.sock",
        docker_daemon_id="daemon-id",
    )
    digest = "a" * 64
    image_id = "sha256:" + "b" * 64
    operation_id = "f" * 32
    refs = {
        "api": f"{base.prefix}-api:{digest[:24]}",
        "worker": f"{base.prefix}-worker:{digest[:24]}",
    }
    api_arn = (
        "arn:aws:ecs:us-east-1:000000000000:task-definition/"
        f"{base.api_family}:1"
    )
    worker_arn = (
        "arn:aws:ecs:us-east-1:000000000000:task-definition/"
        f"{base.worker_family}:1"
    )
    ledger = (
        ArtifactEvent(1, "image_planned", operation_id, "api", digest, refs["api"]),
        ArtifactEvent(2, "image_planned", operation_id, "worker", digest, refs["worker"]),
        ArtifactEvent(
            3,
            "image_observed",
            operation_id,
            "api",
            digest,
            refs["api"],
            image_id=image_id,
        ),
        ArtifactEvent(
            4,
            "image_observed",
            operation_id,
            "worker",
            digest,
            refs["worker"],
            image_id=image_id,
        ),
        ArtifactEvent(
            5,
            "task_definition_planned",
            operation_id,
            "api",
            digest,
            refs["api"],
            family=base.api_family,
        ),
        ArtifactEvent(
            6,
            "task_definition_planned",
            operation_id,
            "worker",
            digest,
            refs["worker"],
            family=base.worker_family,
        ),
        ArtifactEvent(
            7,
            "task_definition_observed",
            operation_id,
            "api",
            digest,
            refs["api"],
            image_id=image_id,
            family=base.api_family,
            task_definition_arn=api_arn,
        ),
        ArtifactEvent(
            8,
            "task_definition_observed",
            operation_id,
            "worker",
            digest,
            refs["worker"],
            image_id=image_id,
            family=base.worker_family,
            task_definition_arn=worker_arn,
        ),
    )
    return RunState.create(
        "r",
        claim_id=base.claim_id,
        docker_context=base.docker_context,
        docker_socket=base.docker_socket,
        docker_daemon_id=base.docker_daemon_id,
        source_digest=digest,
        api_image_id=image_id,
        worker_image_id=image_id,
        api_task_definition_arn=api_arn,
        worker_task_definition_arn=worker_arn,
        artifact_ledger=ledger,
    )


def _repo(
    tmp_path: Path,
    output: str,
    *,
    labctl_source: str | None = None,
) -> tuple[Path, Path, Path, str]:
    repo = tmp_path / "repo"
    for relative in PROTECTED:
        source, target = ROOT / relative, repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    labctl = repo / "labctl"
    labctl.write_text(
        labctl_source or f"#!/usr/bin/env python3\nprint({output!r})\n",
        encoding="utf-8",
    )
    os.chmod(labctl, 0o700)
    manifest = {path: hashlib.sha256((repo / path).read_bytes()).hexdigest() for path in PROTECTED}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    manifest_path.chmod(0o400)
    external_judge = tmp_path / "external-judge.py"
    shutil.copy2(repo / "judge/verify_feature_contract.py", external_judge)
    external_judge.chmod(0o500)
    contract = hashlib.sha256((repo / "Wiki/features/document-export.md").read_bytes()).hexdigest()
    return repo, manifest_path, external_judge, contract


def _judge_command(
    repo: Path, manifest: Path, external_judge: Path, contract: str
) -> list[str]:
    return [
        "python3",
        str(external_judge),
        "--repo",
        str(repo),
        "--expected-contract-sha256",
        contract,
        "--control-manifest",
        str(manifest),
    ]


@pytest.mark.parametrize(
    "kind",
    [
        "valid",
        "ok",
        "stale",
        "malformed",
        "missing",
        "duplicate-role",
        "empty-labels",
        "fake-security",
        "fake-s3",
        "no-reproof",
    ],
)
def test_judge_schema_matrix(tmp_path: Path, kind: str) -> None:
    value: object = _payload(mismatch=kind == "stale", missing=kind == "missing")
    if kind == "ok":
        value = {"ok": True}
    if isinstance(value, dict) and kind == "duplicate-role":
        value["task_proof"]["containers"][1]["role"] = "api"
    if isinstance(value, dict) and kind == "empty-labels":
        value["task_proof"]["containers"][0]["labels"] = {}
    if isinstance(value, dict) and kind == "fake-security":
        value["task_proof"]["containers"][0]["security"]["non_root"] = False
    if isinstance(value, dict) and kind == "fake-s3":
        value["business"]["s3_result"]["body"] = {"tenant": "wrong"}
    if isinstance(value, dict) and kind == "no-reproof":
        value["task_proof"]["post_business_reproof"] = False
    output = "not-json" if kind == "malformed" else json.dumps(value)
    repo, manifest, external_judge, contract = _repo(tmp_path, output)
    result = subprocess.run(
        [
            "python3",
            str(external_judge),
            "--repo",
            str(repo),
            "--expected-contract-sha256",
            contract,
            "--control-manifest",
            str(manifest),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == (0 if kind == "valid" else 1)


def test_judge_rejects_protected_mutation_before_verifier(tmp_path: Path) -> None:
    repo, manifest, external_judge, contract = _repo(tmp_path, json.dumps(_payload()))
    (repo / "src/pk_stack_lab/runtime.py").write_text("changed", encoding="utf-8")
    result = subprocess.run(
        [
            "python3",
            str(external_judge),
            "--repo",
            str(repo),
            "--expected-contract-sha256",
            contract,
            "--control-manifest",
            str(manifest),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1 and "protected control-plane hash differs" in result.stderr


@pytest.mark.parametrize(
    ("stream", "expected"),
    [("stdout", "stdout exceeded bound"), ("stderr", "wrote stderr")],
)
def test_judge_kills_verifier_as_soon_as_output_violates_bound(
    tmp_path: Path, stream: str, expected: str
) -> None:
    write = (
        "sys.stdout.write('x' * 8193)"
        if stream == "stdout"
        else "sys.stderr.write('x')"
    )
    source = (
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "import time\n"
        f"{write}\n"
        f"sys.{stream}.flush()\n"
        "time.sleep(60)\n"
    )
    repo, manifest, external_judge, contract = _repo(
        tmp_path, "", labctl_source=source
    )

    result = subprocess.run(
        _judge_command(repo, manifest, external_judge, contract),
        text=True,
        capture_output=True,
        check=False,
        timeout=5,
    )

    assert result.returncode == 1
    assert expected in result.stderr


def test_bounded_verifier_kills_child_at_timeout(tmp_path: Path) -> None:
    labctl = tmp_path / "labctl"
    labctl.write_text(
        "#!/usr/bin/env python3\nimport time\ntime.sleep(60)\n",
        encoding="utf-8",
    )
    labctl.chmod(0o700)
    spec = importlib.util.spec_from_file_location(
        "pk_stack_timeout_judge", ROOT / "judge/verify_feature_contract.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with pytest.raises(SystemExit, match="verifier timed out"):
        module._run_verifier(labctl, tmp_path, timeout_seconds=0.05)


def test_judge_rejects_unmanifested_executable_source(tmp_path: Path) -> None:
    repo, manifest, external_judge, contract = _repo(tmp_path, json.dumps(_payload()))
    (repo / "src/pk_stack_lab/extra.py").write_text("raise SystemExit\n", encoding="utf-8")

    result = subprocess.run(
        [
            "python3",
            str(external_judge),
            "--repo",
            str(repo),
            "--expected-contract-sha256",
            contract,
            "--control-manifest",
            str(manifest),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "executable source closure differs" in result.stderr


@pytest.mark.parametrize("kind", ["judge-inside", "manifest-inside", "manifest-symlink"])
def test_judge_requires_direct_locked_external_controls(tmp_path: Path, kind: str) -> None:
    repo, manifest, external_judge, contract = _repo(tmp_path, json.dumps(_payload()))
    judge = external_judge
    selected_manifest = manifest
    if kind == "judge-inside":
        judge = repo / "judge/verify_feature_contract.py"
    elif kind == "manifest-inside":
        selected_manifest = repo / "manifest.json"
        selected_manifest.write_bytes(manifest.read_bytes())
        selected_manifest.chmod(0o400)
    else:
        selected_manifest = tmp_path / "manifest-link.json"
        selected_manifest.symlink_to(manifest)

    result = subprocess.run(
        [
            "python3",
            str(judge),
            "--repo",
            str(repo),
            "--expected-contract-sha256",
            contract,
            "--control-manifest",
            str(selected_manifest),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert any(
        message in result.stderr
        for message in ("must be outside the repository", "must not be a symlink")
    )


def test_cli_resource_projection_is_accepted_by_judge_consumer() -> None:
    payload = _payload()
    state = _complete_resource_projection_state()
    payload["resources"] = cli._verified_resource_evidence(state)
    spec = importlib.util.spec_from_file_location(
        "pk_stack_feature_judge", ROOT / "judge/verify_feature_contract.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module._valid_payload(payload) is True


def test_labctl_uses_fresh_noneditable_runtime_instead_of_mutable_project_venv() -> None:
    launcher = (ROOT / "labctl").read_text(encoding="utf-8")

    assert "uv run --isolated --no-editable --locked --no-config --no-dev --quiet" in launcher
    assert "--python 3.12 --managed-python" in launcher
    assert "--reinstall-package pk-stack-lab" in launcher
    assert "--no-sync" not in launcher
