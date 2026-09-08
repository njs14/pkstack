#!/usr/bin/env python3
"""Build an exact-commit CI package, or verify it for promotion without publishing."""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    raise SystemExit("pkstack CI package requires Python 3.11 or newer")

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pkstack_package_content import ContentError as PackageError
from pkstack_package_content import load_contract, validate_paths, validate_source
from pkstack_release_notes import bind_repository_links, release_notes

CI_WORKFLOW = ".github/workflows/pk-stack-ci.yml"
REQUIRED_JOBS = [
    "classify",
    "fast",
    "browser",
    "package",
    "policy",
    "deterministic",
    *[f"core ({index})" for index in range(6)],
]
FILES = {"package.tar.gz", "package.tar.gz.sha256", "notes.md", "manifest.json"}
LIMITS = {
    "package.tar.gz": 16 * 1024 * 1024,
    "package.tar.gz.sha256": 256,
    "notes.md": 128 * 1024,
    "manifest.json": 64 * 1024,
}
MAX_ZIP = 20 * 1024 * 1024
SMOKE_FLAGS = {
    "setup",
    "idempotent",
    "doctor",
    "feature_validate",
    "knowledge_validate",
    "goal_fail_pass",
    "verifier_unchanged",
}
TAG_RE = r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


class ResourceNotFound(PackageError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PackageError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def positive(value: Any, label: str) -> int:
    require(type(value) is int and 0 < value < 2**53, f"invalid {label}")
    return value


def digest(value: Any, label: str, length: int = 64) -> str:
    require(
        isinstance(value, str) and re.fullmatch(f"[0-9a-f]{{{length}}}", value) is not None,
        f"invalid {label}",
    )
    return value


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def parse_json(raw: bytes, label: str) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, f"duplicate key in {label}")
            result[key] = value
        return result

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except (ValueError, UnicodeError) as exc:
        raise PackageError(f"invalid JSON in {label}") from exc


def git(root: Path, *args: str) -> bytes:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_SYSTEM=os.devnull,
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_ATTR_NOSYSTEM="1",
        GIT_NO_REPLACE_OBJECTS="1",
        GIT_TERMINAL_PROMPT="0",
    )
    result = subprocess.run(
        ["git", "--no-pager", "-c", f"core.hooksPath={os.devnull}", *args],
        cwd=root,
        env=environment,
        capture_output=True,
        timeout=60,
        check=False,
    )
    require(result.returncode == 0, f"Git identity/package operation failed: {args[0]}")
    return result.stdout


def config_digest(root: Path) -> str:
    path = root / ".github/scripts/pkstack_checks.py"
    require(path.is_file() and not path.is_symlink(), "CI check configuration helper is missing")
    spec = importlib.util.spec_from_file_location("pkstack_ci_package_checks", path)
    if spec is None or spec.loader is None:
        raise PackageError("cannot load CI check configuration")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return digest(module.config_digest(root), "CI check configuration digest")


def identity(root: Path, repository: str, repository_id: int, commit: str) -> dict[str, Any]:
    require(
        re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is not None,
        "repository must be owner/name",
    )
    positive(repository_id, "repository ID")
    digest(commit, "release commit", 40)
    require(
        git(root, "rev-parse", "HEAD").decode().strip() == commit,
        "checkout is not the exact release commit",
    )
    git(root, "diff", "--exit-code", commit, "--")
    power_tree = git(root, "rev-parse", f"{commit}:powers/pkstack").decode().strip()
    digest(power_tree, "Power tree", 40)
    metadata = tomllib.loads(git(root, "show", f"{commit}:powers/pkstack/pyproject.toml").decode())
    plugin = parse_json(
        git(root, "show", f"{commit}:powers/pkstack/plugin.json"), "plugin metadata"
    )
    source = git(root, "show", f"{commit}:powers/pkstack/src/pkstack/__init__.py").decode()
    version = metadata.get("project", {}).get("version")
    require(
        isinstance(version, str) and re.fullmatch(TAG_RE, f"v{version}") is not None,
        "invalid package version",
    )
    require(
        plugin.get("version") == version
        and re.findall(r'^__version__ = "([^"]+)"$', source, re.MULTILINE) == [version],
        "package, plugin, and runtime versions disagree",
    )
    return {
        "repository": repository,
        "repository_id": repository_id,
        "commit": commit,
        "power_tree": power_tree,
        "version": version,
        "workflow_path": CI_WORKFLOW,
        "workflow_ref": f"{repository}/{CI_WORKFLOW}@refs/heads/main",
        "workflow_sha": commit,
        "check_config_digest": config_digest(root),
        "required_jobs": sorted(REQUIRED_JOBS),
    }


def notes_for(root: Path, repository: str, commit: str, version: str) -> bytes:
    changelog = git(root, "show", f"{commit}:CHANGELOG.md").decode("utf-8")
    return bind_repository_links(
        release_notes(changelog, f"v{version}"), repository, commit
    ).encode()


def archive_for(root: Path, commit: str) -> bytes:
    allowed = load_contract(root)
    validate_source(root / "powers/pkstack", allowed)
    timestamp = git(root, "show", "-s", "--format=%ct", commit).decode().strip()
    require(re.fullmatch(r"[0-9]+", timestamp) is not None, "invalid commit timestamp")
    raw = git(
        root,
        "archive",
        "--format=tar",
        "--prefix=pkstack/",
        f"--mtime=@{timestamp}",
        f"{commit}:powers/pkstack",
    )
    require(len(raw) <= 64 * 1024 * 1024, "Power archive exceeds its size bound")
    compressed = subprocess.run(
        ["gzip", "--no-name", "--stdout"], input=raw, capture_output=True, timeout=60, check=False
    )
    require(compressed.returncode == 0, "deterministic gzip failed")
    require(0 < len(compressed.stdout) <= LIMITS["package.tar.gz"], "invalid archive size")
    with tempfile.TemporaryDirectory(prefix="pkstack-content-check-") as temporary:
        extract_archive(compressed.stdout, Path(temporary) / "power", allowed=allowed)
    return compressed.stdout


def extract_archive(raw: bytes, destination: Path, *, allowed: set[str] | None = None) -> Path:
    """Extract only regular package files/directories, without trusting tar paths or links."""
    if allowed is None:
        allowed = load_contract()
    files: set[str] = set()
    directories: set[str] = set()
    destination.mkdir(mode=0o700)
    seen: set[str] = set()
    total = 0
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r|gz") as archive:
            for member in archive:
                name = member.name.rstrip("/") if member.isdir() else member.name
                pieces = name.split("/")
                require(
                    pieces[0] == "pkstack"
                    and all(part not in {"", ".", ".."} for part in pieces)
                    and "\\" not in name
                    and not name.startswith("/")
                    and name not in seen,
                    "unsafe or duplicate package archive path",
                )
                require(
                    member.isdir() or member.isfile(),
                    "package archive contains a link or special file",
                )
                require(not member.mode & 0o7000, "package archive contains privileged file modes")
                seen.add(name)
                relative = "/".join(pieces[1:])
                if relative:
                    (directories if member.isdir() else files).add(relative)
                total += member.size
                require(
                    len(seen) <= 4096 and total <= 64 * 1024 * 1024,
                    "package extraction exceeds its bounds",
                )
                target = destination.joinpath(*pieces)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    require(member.size <= 16 * 1024 * 1024, "package member is too large")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    stream = archive.extractfile(member)
                    if stream is None:
                        raise PackageError("package member is unreadable")
                    with target.open("xb") as output:
                        shutil.copyfileobj(stream, output)
                    target.chmod(member.mode & 0o777)
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise PackageError("invalid package archive") from exc
    require("pkstack/plugin.json" in seen, "package root is missing")
    validate_paths(files, directories, allowed)
    return destination / "pkstack"


def run_json(
    argv: list[str], root: Path, env: dict[str, str], expected_exit: int = 0
) -> dict[str, Any]:
    result = subprocess.run(argv, cwd=root, env=env, capture_output=True, timeout=120, check=False)
    require(
        result.returncode == expected_exit,
        f"extracted-consumer {Path(argv[0]).name} failed with exit {result.returncode}",
    )
    value = parse_json(result.stdout, "consumer result")
    require(
        isinstance(value, dict) and value.get("ok") is (expected_exit == 0),
        "consumer check did not report the expected success/failure state",
    )
    return value


def consumer_smoke(
    raw: bytes, version: str, workspace: Path, *, allowed: set[str] | None = None
) -> dict[str, Any]:
    power = extract_archive(raw, workspace / "extracted", allowed=allowed)
    consumer = workspace / "consumer"
    consumer.mkdir()
    (consumer / "user-note.txt").write_text("Preserve this consumer-owned note.\n")
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "VIRTUAL_ENV", "GH_TOKEN", "GITHUB_TOKEN", "KIRO_API_KEY"}
    }
    environment.update(UV_OFFLINE="1", UV_NO_PROGRESS="1", PYTHONDONTWRITEBYTECODE="1")
    setup = [
        sys.executable,
        str(power / "skills/pkstack-setup/scripts/setup_pkstack.py"),
        "--root",
        str(consumer),
        "--output",
        "json",
    ]
    run_json(setup, consumer, environment)
    require(
        (consumer / "user-note.txt").read_text() == "Preserve this consumer-owned note.\n",
        "extracted-consumer setup changed a consumer-owned file",
    )

    def snapshot() -> dict[str, str]:
        return {
            str(path.relative_to(consumer)): sha256(path.read_bytes())
            for path in consumer.rglob("*")
            if path.is_file()
            and not {".venv", "__pycache__"}.intersection(path.relative_to(consumer).parts)
        }

    before = snapshot()
    run_json(setup, consumer, environment)
    require(snapshot() == before, "extracted-consumer setup is not idempotent")
    runner = str(consumer / ".pkstack/bin/projectctl")

    def check(*args: str, expected_exit: int = 0) -> dict[str, Any]:
        return run_json([runner, *args, "--output", "json"], consumer, environment, expected_exit)

    # Version output intentionally has no generic `ok` field.
    result = subprocess.run(
        [runner, "version", "--output", "json"],
        cwd=consumer,
        env=environment,
        capture_output=True,
        timeout=120,
        check=False,
    )
    require(
        result.returncode == 0
        and parse_json(result.stdout, "consumer version").get("version") == version,
        "extracted-consumer version does not match the package",
    )
    doctor = check("doctor")
    check("feature", "validate")
    knowledge = check("knowledge", "validate")
    verifier = consumer / "verify.py"
    verifier.write_text(
        "from pathlib import Path\n"
        "raise SystemExit(0 if Path('value.txt').read_text() == 'repaired\\n' else 1)\n"
    )
    verifier_hash = sha256(verifier.read_bytes())
    (consumer / "value.txt").write_text("fault\n")
    check(
        "goal",
        "start",
        "Prove the extracted controller's stored failure/repair/pass loop",
        "--command",
        "python3 verify.py",
        "--max-attempts",
        "2",
    )
    failed = check("goal", "verify", expected_exit=1)["goal"]
    require(
        failed["status"] == "active"
        and failed["attempt_count"] == 1
        and failed["last_result"]["exit_code"] == 1,
        "consumer goal did not store a real failure",
    )
    (consumer / "value.txt").write_text("repaired\n")
    passed = check("goal", "verify")["goal"]
    require(
        passed["status"] == "passed"
        and passed["attempt_count"] == 2
        and passed["contract_digest"] == failed["contract_digest"]
        and passed["goal_id"] == failed["goal_id"]
        and sha256(verifier.read_bytes()) == verifier_hash,
        "consumer goal did not preserve its predicate and pass",
    )
    return {
        **dict.fromkeys(sorted(SMOKE_FLAGS), True),
        "doctor_summary": doctor["summary"],
        "knowledge_mode": knowledge["mode"],
    }


def write_files(output: Path, contents: dict[str, bytes]) -> None:
    require(not output.exists() and not output.is_symlink(), "output directory already exists")
    output.mkdir(mode=0o700, parents=True)
    for name, raw in contents.items():
        require(name in FILES and 0 < len(raw) <= LIMITS[name], "invalid package output")
        target = output / name
        with target.open("xb") as stream:
            stream.write(raw)
        target.chmod(0o600)


def build_package(
    root: Path,
    output: Path,
    repository: str,
    repository_id: int,
    commit: str,
    run_id: int,
    run_attempt: int,
) -> dict[str, Any]:
    expected = identity(root, repository, repository_id, commit)
    positive(run_id, "CI run ID")
    positive(run_attempt, "CI run attempt")
    first = archive_for(root, commit)
    require(first == archive_for(root, commit), "independent archive builds differ")
    with tempfile.TemporaryDirectory(prefix="pkstack-package-smoke-") as temporary:
        smoke = consumer_smoke(
            first, expected["version"], Path(temporary), allowed=load_contract(root)
        )
    contents = {
        "package.tar.gz": first,
        "package.tar.gz.sha256": f"{sha256(first)}  package.tar.gz\n".encode(),
        "notes.md": notes_for(root, repository, commit, expected["version"]),
    }
    manifest = {
        "schema_version": 1,
        "kind": "pkstack-main-ci-package",
        **expected,
        "event": "push",
        "ref": "refs/heads/main",
        "producer_job": "package",
        "run_id": run_id,
        "run_attempt": run_attempt,
        "reproducible": True,
        "smoke": smoke,
        "files": {
            name: {"sha256": sha256(raw), "size": len(raw)} for name, raw in contents.items()
        },
    }
    contents["manifest.json"] = json_bytes(manifest)
    write_files(output, contents)
    return {
        "ok": True,
        "mode": "build",
        "commit": commit,
        "version": expected["version"],
        "artifact_name": artifact_name(commit, run_id, run_attempt),
        "archive_sha256": sha256(first),
        "output_directory": str(output),
    }


def artifact_name(commit: str, run_id: int, run_attempt: int) -> str:
    return f"pkstack-release-{commit}-{run_id}-{run_attempt}"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


class GitHub:
    """Read-only API transport; never forward the API token to artifact storage."""

    def __init__(self, token: str):
        require(bool(token), "GH_TOKEN is required for read-only promotion verification")
        self.token = token
        self.opener = build_opener(NoRedirect())

    def request(self, path: str) -> Request:
        require(path.startswith("repos/"), "invalid GitHub API path")
        return Request(
            f"https://api.github.com/{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2026-03-10",
                "User-Agent": "pkstack-ci-package",
            },
        )

    def get(self, path: str) -> Any:
        try:
            with self.opener.open(self.request(path), timeout=30) as response:
                raw = response.read(4 * 1024 * 1024 + 1)
            require(len(raw) <= 4 * 1024 * 1024, "GitHub metadata exceeded its bound")
            return parse_json(raw, "GitHub response")
        except HTTPError as exc:
            exc.close()
            if exc.code == 404:
                raise ResourceNotFound("required GitHub resource was not found") from exc
            raise PackageError("GitHub metadata request failed") from exc
        except (URLError, TimeoutError) as exc:
            raise PackageError("GitHub metadata request failed") from exc

    def download(self, path: str) -> bytes:
        try:
            try:
                with self.opener.open(self.request(path), timeout=30):
                    raise PackageError("artifact API did not return its expected redirect")
            except HTTPError as response:
                try:
                    require(response.code == 302, "artifact download is unavailable")
                    location = response.headers.get("Location", "")
                finally:
                    response.close()
            target = urlsplit(location)
            require(
                target.scheme == "https"
                and bool(target.hostname)
                and target.username is None
                and target.password is None,
                "unsafe artifact download location",
            )
            anonymous = Request(location, headers={"User-Agent": "pkstack-ci-package"})
            with self.opener.open(anonymous, timeout=60) as response:
                raw = response.read(MAX_ZIP + 1)
            require(0 < len(raw) <= MAX_ZIP, "artifact ZIP exceeds its bound")
            return raw
        except (HTTPError, URLError, TimeoutError) as exc:
            raise PackageError("artifact download failed") from exc


def paginate(api: GitHub, path: str, key: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    separator = "&" if "?" in path else "?"
    for page in range(1, 11):
        response = api.get(f"{path}{separator}per_page=100&page={page}")
        require(
            isinstance(response, dict)
            and isinstance(response.get(key), list)
            and type(response.get("total_count")) is int,
            "invalid paginated GitHub response",
        )
        batch = response[key]
        require(all(isinstance(item, dict) for item in batch), "invalid GitHub collection item")
        records.extend(batch)
        if len(records) == response["total_count"]:
            return records
        require(
            len(batch) == 100 and len(records) < response["total_count"],
            "incomplete GitHub pagination",
        )
    raise PackageError("GitHub collection exceeds its bound")


def live_release_identity(
    api: GitHub, repository: str, repository_id: int, commit: str, tag: str, pre_tag: bool = False
) -> None:
    require(re.fullmatch(TAG_RE, tag) is not None, "release tag must be vMAJOR.MINOR.PATCH")
    prefix = f"repos/{repository}"
    repo = api.get(prefix)
    require(
        repo.get("id") == repository_id
        and repo.get("full_name", "").lower() == repository.lower()
        and repo.get("private") is True
        and repo.get("default_branch") == "main",
        "release repository is not the expected private main repository",
    )
    branch = api.get(f"{prefix}/branches/main")
    require(
        branch.get("commit", {}).get("sha") == commit, "release commit is no longer current main"
    )
    try:
        reference = api.get(f"{prefix}/git/ref/tags/{quote(tag, safe='')}")
    except ResourceNotFound:
        require(pre_tag, "the approved release tag is absent")
        return
    require(not pre_tag, "pre-tag verification requires the proposed tag to be absent")
    require(reference.get("ref") == f"refs/tags/{tag}", "release tag reference changed")
    obj = reference.get("object", {})
    for _ in range(5):
        digest(obj.get("sha"), "tag target", 40)
        if obj.get("type") == "commit":
            require(obj["sha"] == commit, "release tag does not identify the exact main commit")
            return
        require(obj.get("type") == "tag", "release tag does not resolve to a commit")
        obj = api.get(f"{prefix}/git/tags/{obj['sha']}").get("object", {})
    raise PackageError("release tag nesting exceeds its bound")


def successful_run(
    api: GitHub,
    repository: str,
    repository_id: int,
    commit: str,
    run_id: int | None = None,
    attempt: int | None = None,
) -> dict[str, Any]:
    prefix = f"repos/{repository}"
    workflow = api.get(f"{prefix}/actions/workflows/{Path(CI_WORKFLOW).name}")
    workflow_id = positive(workflow.get("id"), "workflow ID")
    require(
        workflow.get("path") == CI_WORKFLOW and workflow.get("state") == "active",
        "expected CI workflow is unavailable",
    )
    query = urlencode({"head_sha": commit, "event": "push", "branch": "main"})
    runs = paginate(api, f"{prefix}/actions/workflows/{workflow_id}/runs?{query}", "workflow_runs")
    require(bool(runs), "no exact push-main CI run is available; no fallback is permitted")
    latest_id = max(positive(item.get("id"), "CI run ID") for item in runs)
    require(run_id is None or run_id == latest_id, "selected CI run has been superseded")
    run = api.get(f"{prefix}/actions/runs/{latest_id}")
    current_attempt = positive(run.get("run_attempt"), "CI attempt")
    require(attempt is None or current_attempt == attempt, "selected CI attempt has changed")
    require(
        run.get("id") == latest_id
        and run.get("workflow_id") == workflow_id
        and run.get("path") == CI_WORKFLOW
        and run.get("head_sha") == commit
        and run.get("head_branch") == "main"
        and run.get("event") == "push"
        and run.get("repository", {}).get("id") == repository_id
        and run.get("head_repository", {}).get("id") == repository_id
        and run.get("status") == "completed"
        and run.get("conclusion") == "success",
        "exact main CI is not a completed successful trusted run",
    )
    jobs = paginate(
        api, f"{prefix}/actions/runs/{latest_id}/attempts/{current_attempt}/jobs", "jobs"
    )
    require(
        sorted(item.get("name", "") for item in jobs) == sorted(REQUIRED_JOBS),
        "mandatory CI jobs are missing, duplicated, or changed",
    )
    require(
        all(
            job.get("status") == "completed"
            and job.get("conclusion") == "success"
            and job.get("head_sha") == commit
            and job.get("run_id") == latest_id
            and job.get("run_attempt") == current_attempt
            for job in jobs
        ),
        "a mandatory current-attempt CI job is incomplete, skipped, failed, or misbound",
    )
    return run


def unpack_zip(raw: bytes) -> dict[str, bytes]:
    require(0 < len(raw) <= MAX_ZIP, "artifact ZIP exceeds its bound")
    contents: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            require(len(members) == len(FILES), "artifact must contain exactly four files")
            for member in members:
                require(
                    member.filename in FILES
                    and member.filename not in contents
                    and not member.is_dir()
                    and not member.flag_bits & 1,
                    "artifact contains unexpected, duplicate, or encrypted entries",
                )
                file_type = stat.S_IFMT(member.external_attr >> 16)
                require(file_type in {0, stat.S_IFREG}, "artifact contains a link or special file")
                require(
                    0 < member.file_size <= LIMITS[member.filename],
                    "artifact entry exceeds its bound",
                )
                with archive.open(member) as stream:
                    value = stream.read(LIMITS[member.filename] + 1)
                require(len(value) == member.file_size, "artifact entry length is invalid")
                contents[member.filename] = value
    except (zipfile.BadZipFile, RuntimeError, OSError, EOFError) as exc:
        raise PackageError("invalid artifact ZIP") from exc
    require(set(contents) == FILES, "artifact entries are incomplete")
    return contents


def verify_package(
    root: Path,
    output: Path,
    api: GitHub,
    repository: str,
    repository_id: int,
    commit: str,
    tag: str,
    run_id: int | None = None,
    attempt: int | None = None,
    artifact_id: int | None = None,
    artifact_digest: str | None = None,
    pre_tag: bool = False,
) -> dict[str, Any]:
    expected = identity(root, repository, repository_id, commit)
    require(tag == f"v{expected['version']}", "release tag and all version authorities must agree")
    live_release_identity(api, repository, repository_id, commit, tag, pre_tag)
    run = successful_run(api, repository, repository_id, commit, run_id, attempt)
    run_id, attempt = run["id"], run["run_attempt"]
    prefix = f"repos/{repository}"
    artifacts = paginate(api, f"{prefix}/actions/runs/{run_id}/artifacts", "artifacts")
    matches = [
        item for item in artifacts if item.get("name") == artifact_name(commit, run_id, attempt)
    ]
    require(len(matches) == 1, "exact current-attempt CI package artifact is absent or ambiguous")
    selected_id = positive(matches[0].get("id"), "artifact ID")
    require(artifact_id is None or artifact_id == selected_id, "selected artifact identity changed")
    artifact = api.get(f"{prefix}/actions/artifacts/{selected_id}")
    binding = artifact.get("workflow_run", {})
    require(
        artifact.get("id") == selected_id
        and artifact.get("expired") is False
        and artifact.get("name") == artifact_name(commit, run_id, attempt)
        and binding.get("id") == run_id
        and binding.get("repository_id") == repository_id
        and binding.get("head_repository_id") == repository_id
        and binding.get("head_sha") == commit
        and binding.get("head_branch") == "main",
        "artifact does not belong to the selected exact-main CI run",
    )
    remote_digest = artifact.get("digest")
    require(
        isinstance(remote_digest, str) and remote_digest.startswith("sha256:"),
        "artifact digest is absent",
    )
    remote_digest = digest(remote_digest[7:], "artifact digest")
    require(
        artifact_digest is None or artifact_digest == remote_digest,
        "artifact digest changed after verification",
    )
    raw = api.download(f"{prefix}/actions/artifacts/{selected_id}/zip")
    require(sha256(raw) == remote_digest, "artifact ZIP digest mismatch")
    contents = unpack_zip(raw)
    manifest = parse_json(contents["manifest.json"], "package manifest")
    keys = set(expected) | {
        "schema_version",
        "kind",
        "event",
        "ref",
        "producer_job",
        "run_id",
        "run_attempt",
        "reproducible",
        "smoke",
        "files",
    }
    require(isinstance(manifest, dict) and set(manifest) == keys, "package manifest schema changed")
    require(
        all(manifest.get(key) == value for key, value in expected.items())
        and manifest.get("schema_version") == 1
        and manifest.get("kind") == "pkstack-main-ci-package"
        and manifest.get("event") == "push"
        and manifest.get("ref") == "refs/heads/main"
        and manifest.get("producer_job") == "package"
        and manifest.get("run_id") == run_id
        and manifest.get("run_attempt") == attempt
        and manifest.get("reproducible") is True,
        "package manifest is not bound to the exact source and check configuration",
    )
    smoke = manifest.get("smoke", {})
    require(
        isinstance(smoke, dict)
        and all(smoke.get(key) is True for key in SMOKE_FLAGS)
        and smoke.get("knowledge_mode") == "local"
        and isinstance(smoke.get("doctor_summary"), dict)
        and smoke["doctor_summary"].get("fail") == 0,
        "package consumer smoke is incomplete",
    )
    files = manifest.get("files")
    require(
        isinstance(files, dict) and set(files) == FILES - {"manifest.json"},
        "invalid inner file manifest",
    )
    for name, entry in files.items():
        require(
            entry == {"sha256": sha256(contents[name]), "size": len(contents[name])},
            "package inner content digest mismatch",
        )
    archive_hash = sha256(contents["package.tar.gz"])
    require(
        contents["package.tar.gz.sha256"] == f"{archive_hash}  package.tar.gz\n".encode(),
        "archive checksum file is invalid",
    )
    require(
        contents["notes.md"] == notes_for(root, repository, commit, expected["version"]),
        "release notes differ from the exact commit's version entry",
    )
    # Recheck mutable authority after the download; this verifier never rebuilds
    # or executes the package.
    successful_run(api, repository, repository_id, commit, run_id, attempt)
    live_release_identity(api, repository, repository_id, commit, tag, pre_tag)
    write_files(output, contents)
    return {
        "ok": True,
        "mode": "verify-only",
        "commit": commit,
        "version": expected["version"],
        "pre_tag": pre_tag,
        "publication_eligible": not pre_tag,
        "source_run_id": run_id,
        "source_run_attempt": attempt,
        "artifact_id": selected_id,
        "artifact_digest": remote_digest,
        "archive_sha256": archive_hash,
        "output_directory": str(output),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=Path.cwd())
        command.add_argument("--output-dir", type=Path, required=True)
        command.add_argument("--repository", required=True)
        command.add_argument("--repository-id", required=True, type=int)
        command.add_argument("--sha", required=True)
        command.add_argument("--github-output", type=Path)
    commands.choices["build"].add_argument("--run-id", required=True, type=int)
    commands.choices["build"].add_argument("--run-attempt", required=True, type=int)
    verify = commands.choices["verify"]
    verify.add_argument("--tag", required=True)
    verify.add_argument("--run-id", type=int)
    verify.add_argument("--run-attempt", type=int)
    verify.add_argument("--artifact-id", type=int)
    verify.add_argument("--artifact-digest")
    verify.add_argument(
        "--pre-tag",
        action="store_true",
        help=(
            "read-only preflight: require the proposed tag to be absent; never publication eligible"
        ),
    )
    args = parser.parse_args()
    try:
        if args.command == "build":
            require(
                os.environ.get("GITHUB_EVENT_NAME") == "push"
                and os.environ.get("GITHUB_REF") == "refs/heads/main"
                and os.environ.get("GITHUB_JOB") == "package",
                "package producer requires the main push package job",
            )
            require(
                os.environ.get("GITHUB_SHA") == args.sha
                and os.environ.get("GITHUB_REPOSITORY") == args.repository
                and os.environ.get("GITHUB_REPOSITORY_ID") == str(args.repository_id)
                and os.environ.get("GITHUB_RUN_ID") == str(args.run_id)
                and os.environ.get("GITHUB_RUN_ATTEMPT") == str(args.run_attempt),
                "producer arguments do not match GitHub's main push identity",
            )
            result = build_package(
                args.repo_root.resolve(),
                args.output_dir,
                args.repository,
                args.repository_id,
                args.sha,
                args.run_id,
                args.run_attempt,
            )
        else:
            result = verify_package(
                args.repo_root.resolve(),
                args.output_dir,
                GitHub(os.environ.get("GH_TOKEN", "")),
                args.repository,
                args.repository_id,
                args.sha,
                args.tag,
                args.run_id,
                args.run_attempt,
                args.artifact_id,
                args.artifact_digest,
                args.pre_tag,
            )
        if args.github_output:
            with args.github_output.open("a") as stream:
                for key, value in result.items():
                    require(
                        "\n" not in str(value) and "\r" not in str(value), "unsafe workflow output"
                    )
                    stream.write(f"{key}={json.dumps(value) if type(value) is bool else value}\n")
        print(json.dumps(result, sort_keys=True))
    except (PackageError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"pkstack CI package: {exc}\n")


if __name__ == "__main__":
    main()
