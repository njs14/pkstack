import json
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError

from pk_stack_lab import cli
from pk_stack_lab.config import RunState, SafetyError, claim_state, load_state, save_state


def test_run_state_has_single_safe_prefix() -> None:
    state = RunState.create(
        "ci-001",
        source_digest="a" * 64,
        api_image_id="sha256:" + "b" * 64,
        worker_image_id="sha256:" + "b" * 64,
    )
    assert all(name.startswith("pklab-ci-001") for name in state.names())


def test_tampered_state_cannot_authorize_cleanup(tmp_path: Path) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    path = tmp_path / ".lab-state" / "run.json"
    path.write_text(
        path.read_text().replace("pklab-ci-001-results", "foreign-bucket"), encoding="utf-8"
    )
    with pytest.raises(SafetyError):
        load_state(tmp_path)


def test_state_manifest_requires_exact_canonical_schema(tmp_path: Path) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    path = tmp_path / ".lab-state" / "run.json"
    path.write_text(
        path.read_text(encoding="utf-8").replace("}", ',"extra":"x"}'), encoding="utf-8"
    )
    with pytest.raises(SafetyError, match="no valid lab state"):
        load_state(tmp_path)


def test_atomic_state_claim_has_one_winner(tmp_path: Path) -> None:
    claim_state(tmp_path, RunState.create("ci-001"))
    with pytest.raises(SafetyError, match="artifacts|manifest"):
        claim_state(tmp_path, RunState.create("ci-002"))


def test_concurrent_atomic_state_claim_has_exactly_one_winner(tmp_path: Path) -> None:
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def claim(run_id: str) -> None:
        barrier.wait()
        try:
            claim_state(tmp_path, RunState.create(run_id))
        except SafetyError:
            outcomes.append("rejected")
        else:
            outcomes.append("claimed")

    threads = [threading.Thread(target=claim, args=(f"ci-00{i}",)) for i in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(outcomes) == ["claimed", "rejected"]
    assert load_state(tmp_path).run_id in {"ci-001", "ci-002"}


def test_symlinked_state_directory_never_reads_or_writes_external_target(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    external_state = outside / "run.json"
    external_state.write_text('{"external":true}', encoding="utf-8")
    (tmp_path / ".lab-state").symlink_to(outside, target_is_directory=True)
    with pytest.raises(SafetyError, match="must not be a symlink"):
        load_state(tmp_path)
    with pytest.raises(SafetyError, match="must not be a symlink"):
        save_state(tmp_path, RunState.create("ci-001"))
    assert external_state.read_text(encoding="utf-8") == '{"external":true}'


def test_symlinked_run_manifest_never_reads_or_writes_external_target(tmp_path: Path) -> None:
    outside = tmp_path / "outside.json"
    outside.write_text('{"external":true}', encoding="utf-8")
    state = tmp_path / ".lab-state"
    state.mkdir()
    (state / "run.json").symlink_to(outside)
    with pytest.raises(SafetyError, match="must not be a symlink"):
        load_state(tmp_path)
    with pytest.raises(SafetyError, match="direct regular file"):
        save_state(tmp_path, RunState.create("ci-001"))
    assert outside.read_text(encoding="utf-8") == '{"external":true}'


@pytest.mark.parametrize(
    "contents",
    [
        "not-json",
        '{"run_id":"ci-001","queue":"foreign","dlq":"pklab-ci-001-exports-dlq"}',
    ],
)
def test_up_preserves_invalid_direct_manifest_without_reaching_docker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contents: str
) -> None:
    state = tmp_path / ".lab-state"
    state.mkdir()
    manifest = state / "run.json"
    manifest.write_text(contents, encoding="utf-8")
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(
        cli,
        "_docker_socket",
        lambda: (_ for _ in ()).throw(AssertionError("Docker must not be reached")),
    )
    with pytest.raises(cli.LabError, match="existing .lab-state is invalid"):
        cli.command_up(SimpleNamespace(run_id="ci-002"))
    assert manifest.read_text(encoding="utf-8") == contents


def test_task_definition_has_no_socket_or_host_mounts() -> None:
    state = RunState.create("ci-001")
    definition = cli._task_definition(
        state, role="api", image="pklab-ci-001-api:0.1", queue_url="http://floci:4566/q"
    )
    container = definition["containerDefinitions"][0]
    assert "mountPoints" not in container
    assert "volumesFrom" not in container
    assert "volumes" not in definition
    assert all("SOCKET" not in item["name"] for item in container["environment"])


def test_task_definition_requests_all_mandatory_security_fields() -> None:
    state = RunState.create("ci-001")
    definition = cli._task_definition(
        state, role="worker", image="pklab-ci-001-worker:hash", queue_url="http://floci:4566/q"
    )
    container = definition["containerDefinitions"][0]
    assert container["user"] == "65532:65532"
    assert container["readonlyRootFilesystem"] is True
    assert container["linuxParameters"]["capabilities"]["drop"] == ["ALL"]
    assert container["dockerSecurityOptions"] == ["no-new-privileges"]


def test_deploy_create_service_requests_service_tag_propagation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    calls: list[dict[str, object]] = []

    class Sqs:
        def get_queue_url(self, **kwargs):
            return {"QueueUrl": "http://floci:4566/queue"}

    class Ecs:
        def register_task_definition(self, **kwargs):
            return {
                "taskDefinition": {"taskDefinitionArn": f"arn:task-definition/{kwargs['family']}:1"}
            }

        def create_service(self, **kwargs):
            calls.append(kwargs)

        def describe_services(self, **kwargs):
            return {"services": []}

    services = [
        {"serviceName": state.api_service, "runningCount": 1},
        {"serviceName": state.worker_service, "runningCount": 1},
    ]
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(
        cli, "_docker_identity", lambda: ("test", "unix:///tmp/docker.sock", "daemon")
    )
    monkeypatch.setattr(cli, "source_digest", lambda root: "a" * 64)
    monkeypatch.setattr(
        cli,
        "_run",
        lambda args, **kwargs: (
            "sha256:test\n" if args[:3] == ["docker", "image", "inspect"] else ""
        ),
    )
    monkeypatch.setattr(cli, "_wait_services", lambda value: services)
    monkeypatch.setattr(cli, "client", lambda name: Sqs() if name == "sqs" else Ecs())
    cli.command_deploy(SimpleNamespace())
    assert len(calls) == 2
    assert all(call["propagateTags"] == "SERVICE" for call in calls)


def test_deploy_repeat_update_requests_service_tag_propagation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = RunState.create("ci-001")
    save_state(tmp_path, state)
    calls: list[dict[str, object]] = []

    class Sqs:
        def get_queue_url(self, **kwargs):
            return {"QueueUrl": "http://floci:4566/queue"}

    class Ecs:
        def register_task_definition(self, **kwargs):
            return {
                "taskDefinition": {"taskDefinitionArn": f"arn:task-definition/{kwargs['family']}:1"}
            }

        def create_service(self, **kwargs):
            raise AssertionError("existing service must be discovered before mutation")

        def describe_services(self, **kwargs):
            return {"services": [{"tags": cli._ecs_tags(state)}]}

        def update_service(self, **kwargs):
            calls.append(kwargs)

    services = [
        {"serviceName": state.api_service, "runningCount": 1},
        {"serviceName": state.worker_service, "runningCount": 1},
    ]
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_docker_socket", lambda: "unix:///tmp/docker.sock")
    monkeypatch.setattr(cli, "source_digest", lambda root: "a" * 64)
    monkeypatch.setattr(
        cli,
        "_run",
        lambda args, **kwargs: (
            "sha256:test\n" if args[:3] == ["docker", "image", "inspect"] else ""
        ),
    )
    monkeypatch.setattr(cli, "_wait_services", lambda value: services)
    monkeypatch.setattr(cli, "client", lambda name: Sqs() if name == "sqs" else Ecs())
    cli.command_deploy(SimpleNamespace())
    assert len(calls) == 2
    assert all(call["propagateTags"] == "SERVICE" for call in calls)


def test_foreign_outer_resources_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli,
        "_inspect_labels",
        lambda kind, name, missing_ok=False: (
            {"pk-stack-lab.managed": "false"} if kind == "container" else None
        ),
    )
    with pytest.raises(cli.LabError, match="foreign container"):
        cli._assert_outer_ownership()


def test_outer_inspection_does_not_turn_generic_docker_failure_into_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "_run",
        lambda *args, **kwargs: (_ for _ in ()).throw(cli.LabError("daemon unavailable")),
    )
    with pytest.raises(cli.LabError, match="daemon unavailable"):
        cli._inspect_labels("container", "pk-stack-lab-floci", missing_ok=True)


def test_outer_inspection_accepts_only_positive_exact_absence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_run", lambda *args, **kwargs: "")
    assert cli._inspect_labels("network", cli.NETWORK, missing_ok=True) is None


def test_task_container_evidence_requires_exact_resource_id_and_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "a" * 32
    task = {
        "taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/cluster/{task_id}",
        "containers": [{"image": "example:1"}],
    }
    labels = {
        "floci": "true",
        "floci_emulator": "floci-aws",
        "io.floci": "aws",
        "io.floci.service": "ecs",
        "io.floci.resource-id": task_id,
    }
    monkeypatch.setattr(cli, "_inspect_labels", lambda *args, **kwargs: labels)
    monkeypatch.setattr(
        cli,
        "_docker_json",
        lambda args, **kwargs: [] if ".Mounts" in args[4] else {cli.NETWORK: {}},
    )
    monkeypatch.setattr(
        cli,
        "_run",
        lambda args, **kwargs: (
            '65532:65532|true|["ALL"]|["no-new-privileges"]\n'
            if ".HostConfig.ReadonlyRootfs" in args[4]
            else "example:1\n"
        ),
    )
    evidence = cli._task_container_evidence(task, "api")
    assert evidence["network"] == cli.NETWORK
    labels["io.floci.resource-id"] = "b" * 32
    with pytest.raises(cli.LabError, match="exact Floci ECS task"):
        cli._task_container_evidence(task, "api")


def test_task_container_evidence_rejects_socket_mount(monkeypatch: pytest.MonkeyPatch) -> None:
    task_id = "c" * 32
    task = {
        "taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/cluster/{task_id}",
        "containers": [{"image": "example:1"}],
    }
    labels = {
        "floci": "true",
        "floci_emulator": "floci-aws",
        "io.floci": "aws",
        "io.floci.service": "ecs",
        "io.floci.resource-id": task_id,
    }
    monkeypatch.setattr(cli, "_inspect_labels", lambda *args, **kwargs: labels)
    monkeypatch.setattr(cli, "_run", lambda *args, **kwargs: "example:1\n")
    monkeypatch.setattr(
        cli,
        "_docker_json",
        lambda args, **kwargs: (
            [{"Destination": "/var/run/docker.sock"}] if ".Mounts" in args[4] else {cli.NETWORK: {}}
        ),
    )
    with pytest.raises(cli.LabError, match="no mounts"):
        cli._task_container_evidence(task, "api")


def test_task_container_evidence_fails_closed_on_unenforced_security(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "b" * 32
    task = {
        "taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/cluster/{task_id}",
        "containers": [{"image": "example:1"}],
    }
    labels = {
        "floci": "true",
        "floci_emulator": "floci-aws",
        "io.floci": "aws",
        "io.floci.service": "ecs",
        "io.floci.resource-id": task_id,
    }
    monkeypatch.setattr(cli, "_inspect_labels", lambda *args, **kwargs: labels)
    monkeypatch.setattr(
        cli,
        "_docker_json",
        lambda args, **kwargs: [] if ".Mounts" in args[4] else {cli.NETWORK: {}},
    )
    monkeypatch.setattr(
        cli,
        "_run",
        lambda args, **kwargs: (
            "65532:65532|false|null|null\n"
            if ".HostConfig.ReadonlyRootfs" in args[4]
            else "example:1\n"
        ),
    )
    with pytest.raises(cli.LabError, match="did not enforce required security fields"):
        cli._task_container_evidence(task, "api")


def test_verify_proves_both_containers_before_docker_exec_or_aws_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create("ci-001")
    task_id = "e" * 32
    api = {"taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/{state.cluster}/{task_id}"}
    worker = {"taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/{state.cluster}/" + "f" * 32}
    calls: list[str] = []
    monkeypatch.setattr(cli, "load_state", lambda root: state)
    monkeypatch.setattr(cli, "_docker_socket", lambda: "unix:///tmp/docker.sock")
    monkeypatch.setattr(cli, "_service_tasks", lambda value: (api, worker))
    monkeypatch.setattr(
        cli,
        "_task_container_evidence",
        lambda *args: (_ for _ in ()).throw(
            cli.LabError("API and worker task containers must have no mounts")
        ),
    )
    monkeypatch.setattr(cli, "_api_http", lambda *args, **kwargs: calls.append("docker-exec"))
    monkeypatch.setattr(cli, "client", lambda name: calls.append(f"aws-{name}"))
    with pytest.raises(cli.LabError, match="immutable deployment identity"):
        cli.command_verify(SimpleNamespace())
    assert calls == []


def test_api_http_rejects_unproven_container_without_docker_exec(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "e" * 32
    task = {"taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/cluster/{task_id}"}
    monkeypatch.setattr(
        cli,
        "_run",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("docker exec must not run")),
    )
    with pytest.raises(cli.LabError, match="prior exact API container proof"):
        cli._api_http(task, {"name": "wrong", "role": "api"}, method="GET", path="/healthz")


def test_remaining_current_run_task_leak_is_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    task_id = "d" * 32
    name = f"floci-ecs-{task_id}-api"
    monkeypatch.setattr(cli, "_run", lambda *args, **kwargs: f"{name}\n")
    monkeypatch.setattr(
        cli,
        "_inspect_labels",
        lambda *args, **kwargs: {"io.floci.service": "ecs", "io.floci.resource-id": task_id},
    )
    assert cli._remaining_owned_task_leaks([name]) == [name]


def test_local_image_cleanup_removes_only_exact_current_run_tags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = RunState.create(
        "ci-001",
        source_digest="a" * 64,
        api_image_id="sha256:" + "b" * 64,
        worker_image_id="sha256:" + "b" * 64,
    )
    commands: list[list[str]] = []
    listings = iter(
        [
            f"{state.prefix}-api:{state.source_digest[:24]}\n{state.prefix}-worker:{state.source_digest[:24]}\nforeign:1\n",
            "foreign:1\n",
        ]
    )

    def run(args: list[str], **kwargs: object) -> str:
        commands.append(args)
        if args[:3] == ["docker", "image", "ls"]:
            return next(listings)
        if args[:3] == ["docker", "image", "inspect"] and args[4] == "{{.Id}}":
            return state.api_image_id + "\n"
        if args[:3] == ["docker", "image", "inspect"]:
            return json.dumps(
                {
                    "pk-stack-lab.project": cli.PROJECT,
                    "pk-stack-lab.run": state.run_id,
                    "pk-stack-lab.claim": state.claim_id,
                    "pk-stack-lab.source-digest": state.source_digest,
                }
            )
        return ""

    monkeypatch.setattr(cli, "_run", run)
    cli._remove_owned_images(state)
    assert [command[-1] for command in commands if command[:3] == ["docker", "image", "rm"]] == [
        f"{state.prefix}-api:{state.source_digest[:24]}",
        f"{state.prefix}-worker:{state.source_digest[:24]}",
    ]
    assert all("foreign:1" not in command for command in commands)


@pytest.mark.parametrize("argv", [["not-a-command", "--output", "json"], ["--output=json"]])
def test_json_parser_failures_are_single_stdout_object(argv: list[str]) -> None:
    program = "from pk_stack_lab.cli import main; main(" + repr(argv) + ")"
    result = subprocess.run(
        [sys.executable, "-c", program], text=True, capture_output=True, check=False
    )
    assert result.returncode != 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False and payload["command"] is None


def test_json_mode_bounds_an_ordinary_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setitem(
        cli.COMMANDS, "doctor", lambda args: (_ for _ in ()).throw(RuntimeError("ordinary failure"))
    )
    with pytest.raises(SystemExit) as stopped:
        cli.main(["doctor", "--output", "json"])
    assert stopped.value.code == 1
    assert capsys.readouterr().err == ""


def test_service_tasks_rejects_service_tag_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    class Ecs:
        def describe_services(self, **kwargs):
            return {"services": [{"tags": []}]}

    monkeypatch.setattr(cli, "client", lambda name: Ecs())
    with pytest.raises(cli.LabError, match="service lacks"):
        cli._service_tasks(RunState.create("ci-001"))


def test_service_tasks_rejects_task_tag_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    state = RunState.create("ci-001")
    tags = cli._ecs_tags(state)
    task_id = "a" * 32

    class Ecs:
        def describe_services(self, **kwargs):
            return {"services": [{"tags": tags}]}

        def list_tasks(self, **kwargs):
            return {
                "taskArns": [f"arn:aws:ecs:us-east-1:000000000000:task/{state.cluster}/{task_id}"]
            }

        def describe_tasks(self, **kwargs):
            return {
                "tasks": [
                    {
                        "tags": [],
                        "taskArn": f"arn:aws:ecs:us-east-1:000000000000:task/{state.cluster}/{task_id}",
                        "taskDefinitionArn": f"arn:aws:ecs:us-east-1:000000000000:task-definition/{state.api_family}:1",
                    }
                ]
            }

    monkeypatch.setattr(cli, "client", lambda name: Ecs())
    with pytest.raises(cli.LabError, match="task does not"):
        cli._service_tasks(state)


@pytest.mark.parametrize(
    "task",
    [
        {
            "taskArn": "arn:aws:ecs:us-east-1:000000000000:task/foreign/" + "a" * 32,
            "taskDefinitionArn": "arn:aws:ecs:us-east-1:000000000000:task-definition/pklab-ci-001-api:1",
        },
        {
            "taskArn": "arn:aws:ecs:us-east-1:000000000000:task/pklab-ci-001-cluster/" + "a" * 32,
            "taskDefinitionArn": "arn:aws:ecs:us-east-1:000000000000:task-definition/foreign:1",
        },
    ],
)
def test_service_tasks_rejects_wrong_cluster_or_task_definition_family(
    monkeypatch: pytest.MonkeyPatch, task: dict[str, str]
) -> None:
    state = RunState.create("ci-001")
    tags = cli._ecs_tags(state)

    class Ecs:
        def describe_services(self, **kwargs):
            return {"services": [{"tags": tags}]}

        def list_tasks(self, **kwargs):
            return {"taskArns": [task["taskArn"]]}

        def describe_tasks(self, **kwargs):
            return {"tasks": [{**task, "tags": tags}]}

    monkeypatch.setattr(cli, "client", lambda name: Ecs())
    with pytest.raises(cli.LabError, match="task does not"):
        cli._service_tasks(state)


@pytest.mark.parametrize(
    ("code", "allowed", "expected"),
    [
        ("ClusterNotFoundException", {"ClusterNotFoundException"}, True),
        (
            "ServiceNotFoundException",
            {"ServiceNotFoundException", "ClusterNotFoundException"},
            True,
        ),
        ("QueueDoesNotExist", {"QueueDoesNotExist"}, True),
        ("ResourceNotFoundException", {"ResourceNotFoundException"}, True),
        ("NoSuchBucket", {"NoSuchBucket"}, True),
        ("NoSuchTagSet", {"NoSuchBucket"}, False),
        ("AccessDenied", {"NoSuchBucket"}, False),
    ],
)
def test_cleanup_missing_codes_are_operation_specific(
    code: str, allowed: set[str], expected: bool
) -> None:
    error = ClientError({"Error": {"Code": code, "Message": "x"}}, "test")
    assert cli._is_missing(error, allowed) is expected


def test_up_data_directory_failure_retains_manifest_and_returns_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(
        cli, "_docker_identity", lambda: ("test", "unix:///tmp/docker.sock", "daemon")
    )
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda: None)
    monkeypatch.setattr(cli, "_compose_image", lambda socket: cli.FLOCI_IMAGE)
    monkeypatch.setattr(
        cli, "_floci_data_path", lambda **kwargs: (_ for _ in ()).throw(OSError("disk error"))
    )
    with pytest.raises(SystemExit) as stopped:
        cli.main(["up", "--run-id", "ci-003", "--acknowledge-docker-socket", "--output", "json"])
    assert stopped.value.code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is False and result["command"] == "up"
    assert load_state(tmp_path).run_id == "ci-003"


def test_down_data_directory_failure_retains_manifest_and_returns_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    state = RunState.create("ci-003")
    claim_state(tmp_path, state)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "_docker_socket", lambda: "unix:///tmp/docker.sock")
    monkeypatch.setattr(cli, "_assert_outer_ownership", lambda: None)
    monkeypatch.setattr(cli, "_delete_owned_resources", lambda value: [])
    monkeypatch.setattr(cli, "_compose", lambda *args, **kwargs: "")
    monkeypatch.setattr(cli, "_run", lambda *args, **kwargs: "")
    monkeypatch.setattr(cli, "_remaining_owned_task_leaks", lambda names: [])
    monkeypatch.setattr(
        cli,
        "_remove_floci_data_path",
        lambda **kwargs: (_ for _ in ()).throw(OSError("permission error")),
    )
    with pytest.raises(SystemExit) as stopped:
        cli.main(["down", "--output", "json"])
    assert stopped.value.code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is False and result["command"] == "down"
    assert load_state(tmp_path) == state


def test_doctor_fails_when_required_tool_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda name: None if name == "uv" else "/bin/docker")
    with pytest.raises(cli.LabError, match="required tools"):
        cli.command_doctor(object())


def test_task_image_has_complete_locked_runtime_closure() -> None:
    dockerfile = (cli.ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "pip install --no-cache-dir --require-hashes" in dockerfile
    requirements = (cli.ROOT / "requirements-runtime.txt").read_text(encoding="utf-8")
    for pin in (
        "boto3==1.43.86",
        "botocore==1.43.86",
        "jmespath==1.1.0",
        "python-dateutil==2.9.0.post0",
        "s3transfer==0.19.2",
        "six==1.17.0",
        "urllib3==2.7.0",
    ):
        assert pin in requirements


def test_floci_data_path_is_direct_repository_local_and_cleanup_is_exact(tmp_path: Path) -> None:
    data = cli._floci_data_path(root=tmp_path, create=True)
    assert data == tmp_path / ".lab-state" / "floci-data"
    (data / "owned-state.json").write_text("{}", encoding="utf-8")
    cli._remove_floci_data_path(root=tmp_path)
    assert not data.exists()
    cli._remove_empty_state_dir(root=tmp_path)
    assert not (tmp_path / ".lab-state").exists()


def test_floci_data_path_rejects_symlink(tmp_path: Path) -> None:
    state = tmp_path / ".lab-state"
    state.mkdir()
    target = tmp_path / "outside"
    target.mkdir()
    (state / "floci-data").symlink_to(target, target_is_directory=True)
    with pytest.raises(cli.LabError, match="direct directory"):
        cli._floci_data_path(root=tmp_path, create=False)


def test_compose_binds_only_socket_and_repository_local_floci_data() -> None:
    compose = (cli.ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert "target: /var/run/docker.sock" in compose
    assert "source: ${PK_STACK_LAB_FLOCI_DATA" in compose
    assert "target: /app/data" in compose
