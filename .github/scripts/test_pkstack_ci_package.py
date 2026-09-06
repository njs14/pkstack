"""Promotion must bind one complete main-CI attempt and never execute its artifact."""

from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import warnings
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
import zipfile

import pkstack_ci_package as package


REPOSITORY = "example/pkstack"
REPOSITORY_ID = 123
RUN = 456
ATTEMPT = 1
ARTIFACT = 789


def fixture_smoke() -> dict:
    return {**dict.fromkeys(package.SMOKE_FLAGS, True),
            "knowledge_mode": "local", "doctor_summary": {"pass": 81, "warn": 2, "fail": 0}}


def zipped(contents: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in contents.items():
            archive.writestr(name, raw)
    return stream.getvalue()


class FakeGitHub:
    def __init__(self, commit: str, raw: bytes):
        self.raw = raw
        self.repo = {"id": REPOSITORY_ID, "full_name": REPOSITORY, "private": True, "default_branch": "main"}
        self.branch = {"commit": {"sha": commit}}
        self.tag = {"ref": "refs/tags/v0.3.0", "object": {"type": "commit", "sha": commit}}
        self.workflow = {"id": 99, "path": package.CI_WORKFLOW, "state": "active"}
        self.run = {"id": RUN, "run_attempt": ATTEMPT, "workflow_id": 99, "path": package.CI_WORKFLOW,
                    "head_sha": commit, "head_branch": "main", "event": "push", "status": "completed",
                    "conclusion": "success", "repository": {"id": REPOSITORY_ID},
                    "head_repository": {"id": REPOSITORY_ID}}
        self.runs = [{"id": RUN}]
        self.jobs = [{"name": name, "status": "completed", "conclusion": "success", "head_sha": commit,
                      "run_id": RUN, "run_attempt": ATTEMPT} for name in package.REQUIRED_JOBS]
        self.artifact = {"id": ARTIFACT, "name": package.artifact_name(commit, RUN, ATTEMPT),
                         "expired": False, "digest": f"sha256:{package.sha256(raw)}",
                         "workflow_run": {"id": RUN, "repository_id": REPOSITORY_ID,
                                          "head_repository_id": REPOSITORY_ID,
                                          "head_sha": commit, "head_branch": "main"}}
        self.artifacts = [self.artifact]
        self.downloads = 0
        self.after_download = lambda: None

    def get(self, path: str):
        parsed = urlsplit(path)
        relative = parsed.path.removeprefix(f"repos/{REPOSITORY}")
        if relative == "":
            result = self.repo
        elif relative == "/branches/main":
            result = self.branch
        elif relative == "/git/ref/tags/v0.3.0":
            if self.tag is None:
                raise package.ResourceNotFound("missing fixture tag")
            result = self.tag
        elif relative.startswith("/git/tags/"):
            result = {"object": {"type": "commit", "sha": self.run["head_sha"]}}
        elif relative == "/actions/workflows/pk-stack-ci.yml":
            result = self.workflow
        elif relative == f"/actions/runs/{RUN}":
            result = self.run
        elif relative == "/actions/workflows/99/runs":
            query = parse_qs(parsed.query)
            assert query["head_sha"] == [self.run["head_sha"]]
            assert query["event"] == ["push"] and query["branch"] == ["main"]
            result = {"total_count": len(self.runs), "workflow_runs": self.runs}
        elif relative.startswith(f"/actions/runs/{RUN}/attempts/"):
            result = {"total_count": len(self.jobs), "jobs": self.jobs}
        elif relative == f"/actions/runs/{RUN}/artifacts":
            result = {"total_count": len(self.artifacts), "artifacts": self.artifacts}
        elif relative == f"/actions/artifacts/{ARTIFACT}":
            result = self.artifact
        else:
            raise AssertionError(f"unexpected API path: {path}")
        return copy.deepcopy(result)

    def download(self, path: str) -> bytes:
        assert path == f"repos/{REPOSITORY}/actions/artifacts/{ARTIFACT}/zip"
        self.downloads += 1
        self.after_download()
        return self.raw


class PackageFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="pkstack-package-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()
        files = {
            "powers/pkstack/pyproject.toml": '[project]\nname = "pkstack"\nversion = "0.3.0"\n',
            "powers/pkstack/plugin.json": '{"version":"0.3.0"}\n',
            "powers/pkstack/src/pkstack/__init__.py": '__version__ = "0.3.0"\n',
            ".github/scripts/pkstack_checks.py": 'def config_digest(root):\n    return "' + "c" * 64 + '"\n',
            ".github/workflows/pk-stack-ci.yml": "name: PKStack CI\n",
            "CHANGELOG.md": "# Changes\n\n## [0.3.0]\n\nCurrent [guide](guide.md).\n\n## [0.2.0]\nOld text.\n",
        }
        for relative, text in files.items():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        for argv in (["init", "--quiet"], ["config", "user.email", "test@example.invalid"],
                     ["config", "user.name", "Package fixture"], ["add", "."], ["commit", "--quiet", "-m", "fixture"]):
            subprocess.run(["git", *argv], cwd=self.root, check=True, capture_output=True)
        self.commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        self.output = Path(self.temporary.name) / "built"
        with patch.object(package, "consumer_smoke", return_value=fixture_smoke()):
            self.built = package.build_package(self.root, self.output, REPOSITORY, REPOSITORY_ID,
                                               self.commit, RUN, ATTEMPT)
        self.contents = {path.name: path.read_bytes() for path in self.output.iterdir()}
        self.api = FakeGitHub(self.commit, zipped(self.contents))

    def verify(self, **kwargs):
        return package.verify_package(self.root, Path(self.temporary.name) / "verified", self.api,
                                      REPOSITORY, REPOSITORY_ID, self.commit, "v0.3.0", **kwargs)

    def replace_manifest(self, mutate):
        manifest = json.loads(self.contents["manifest.json"])
        mutate(manifest)
        self.contents["manifest.json"] = package.json_bytes(manifest)
        self.api.raw = zipped(self.contents)
        self.api.artifact["digest"] = f"sha256:{package.sha256(self.api.raw)}"

    def test_exact_main_success_preserves_built_bytes_without_rebuild_or_execution(self):
        with patch.object(package, "archive_for", side_effect=AssertionError("promotion rebuilt archive")), \
                patch.object(package, "consumer_smoke", side_effect=AssertionError("promotion executed package")):
            result = self.verify(run_id=RUN, attempt=ATTEMPT, artifact_id=ARTIFACT,
                                 artifact_digest=package.sha256(self.api.raw))
        self.assertEqual(result["mode"], "verify-only")
        self.assertEqual(result["archive_sha256"], self.built["archive_sha256"])
        promoted = Path(result["output_directory"])
        self.assertEqual({path.name: path.read_bytes() for path in promoted.iterdir()}, self.contents)
        self.assertIn(f"https://github.com/{REPOSITORY}/blob/{self.commit}/guide.md",
                      self.contents["notes.md"].decode())
        self.assertNotIn("Old text", self.contents["notes.md"].decode())

    def test_archives_are_reproducible_and_preserve_exact_git_contents(self):
        self.assertEqual(package.archive_for(self.root, self.commit), self.contents["package.tar.gz"])
        extracted = package.extract_archive(self.contents["package.tar.gz"], Path(self.temporary.name) / "extract")
        self.assertEqual((extracted / "plugin.json").read_bytes(),
                         (self.root / "powers/pkstack/plugin.json").read_bytes())

    def test_changed_working_source_cannot_produce_or_promote(self):
        (self.root / "powers/pkstack/plugin.json").write_text('{"version":"9.9.9"}\n')
        with self.assertRaisesRegex(package.PackageError, "Git identity"):
            self.verify()

    def test_rejects_invalid_run_status_source_event_repository_and_attempt(self):
        mutations = [
            lambda r: r.update(status="in_progress"), lambda r: r.update(conclusion="failure"),
            lambda r: r.update(conclusion="cancelled"), lambda r: r.update(event="pull_request"),
            lambda r: r.update(event="workflow_dispatch"), lambda r: r.update(head_branch="other"),
            lambda r: r.update(head_repository={"id": 999}), lambda r: r.update(repository={"id": 999}),
            lambda r: r.update(workflow_id=999), lambda r: r.update(path=".github/workflows/untrusted.yml"),
            lambda r: r.update(run_attempt=2),
        ]
        original = copy.deepcopy(self.api.run)
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.api.run = copy.deepcopy(original)
                mutate(self.api.run)
                with self.assertRaises(package.PackageError):
                    self.verify(attempt=ATTEMPT)
        self.assertEqual(self.api.downloads, 0)

    def test_never_falls_back_to_old_success_or_absent_package(self):
        self.api.runs = []
        with self.assertRaisesRegex(package.PackageError, "no exact push-main"):
            self.verify()
        self.api.runs = [{"id": RUN}, {"id": RUN + 1}]
        with self.assertRaisesRegex(package.PackageError, "superseded"):
            self.verify(run_id=RUN)
        self.api.runs = [{"id": RUN}]
        self.api.artifacts = []
        with self.assertRaisesRegex(package.PackageError, "absent or ambiguous"):
            self.verify()

    def test_all_current_attempt_jobs_must_succeed_once(self):
        original = copy.deepcopy(self.api.jobs)
        changes = [lambda jobs: jobs.pop(), lambda jobs: jobs.append(copy.deepcopy(jobs[0])),
                   lambda jobs: jobs[0].update(conclusion="skipped"),
                   lambda jobs: jobs[0].update(conclusion="neutral"),
                   lambda jobs: jobs[0].update(status="in_progress"),
                   lambda jobs: jobs[0].update(run_attempt=2),
                   lambda jobs: jobs[0].update(head_sha="0" * 40)]
        for mutate in changes:
            with self.subTest(mutation=mutate):
                self.api.jobs = copy.deepcopy(original)
                mutate(self.api.jobs)
                with self.assertRaisesRegex(package.PackageError, "mandatory"):
                    self.verify()

    def test_private_current_main_tag_and_version_are_required(self):
        original = copy.deepcopy((self.api.repo, self.api.branch, self.api.tag))
        mutations = [lambda: self.api.repo.update(private=False),
                     lambda: self.api.repo.update(default_branch="development"),
                     lambda: self.api.branch["commit"].update(sha="a" * 40),
                     lambda: self.api.tag["object"].update(sha="b" * 40),
                     lambda: self.api.tag.update(ref="refs/tags/v0.2.0")]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.api.repo, self.api.branch, self.api.tag = copy.deepcopy(original)
                mutate()
                with self.assertRaises(package.PackageError):
                    self.verify()

    def test_annotated_tag_is_peeled_to_exact_commit(self):
        self.api.tag["object"] = {"type": "tag", "sha": "d" * 40}
        self.assertTrue(self.verify()["ok"])

    def test_pre_tag_dry_run_requires_absent_tag_and_cannot_be_publication_evidence(self):
        self.api.tag = None
        result = self.verify(pre_tag=True)
        self.assertTrue(result["pre_tag"])
        self.assertFalse(result["publication_eligible"])

    def test_pre_tag_requires_absence_and_strict_verify_requires_presence(self):
        with self.assertRaisesRegex(package.PackageError, "requires.*absent"):
            self.verify(pre_tag=True)
        self.api.tag = None
        with self.assertRaisesRegex(package.PackageError, "tag is absent"):
            self.verify()

    def test_expected_failed_consumer_goal_is_accepted_only_as_failure(self):
        result = subprocess.CompletedProcess(["fixture"], 1, b'{"ok":false,"goal":{"status":"active"}}', b"")
        with patch.object(package.subprocess, "run", return_value=result):
            self.assertFalse(package.run_json(["fixture"], self.root, {}, expected_exit=1)["ok"])
            with self.assertRaises(package.PackageError):
                package.run_json(["fixture"], self.root, {}, expected_exit=0)

    def test_download_race_rechecks_main_and_run_attempt(self):
        self.api.after_download = lambda: self.api.branch["commit"].update(sha="d" * 40)
        with self.assertRaisesRegex(package.PackageError, "current main"):
            self.verify()
        self.assertFalse((Path(self.temporary.name) / "verified").exists())
        self.api.branch["commit"]["sha"] = self.commit
        self.api.after_download = lambda: self.api.run.update(run_attempt=2)
        with self.assertRaisesRegex(package.PackageError, "attempt has changed"):
            self.verify()

    def test_artifact_must_bind_id_attempt_and_repository(self):
        original = copy.deepcopy(self.api.artifact)
        mutations = [lambda a: a.update(expired=True), lambda a: a.update(id=999),
                     lambda a: a.update(name="pkstack-release-old-attempt"),
                     lambda a: a["workflow_run"].update(head_sha="0" * 40),
                     lambda a: a["workflow_run"].update(repository_id=999),
                     lambda a: a["workflow_run"].update(head_repository_id=999),
                     lambda a: a["workflow_run"].update(head_branch="other")]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.api.artifact = copy.deepcopy(original)
                mutate(self.api.artifact)
                with self.assertRaises(package.PackageError):
                    self.verify(artifact_id=ARTIFACT)

    def test_zip_digest_mismatch_fails_instead_of_warning(self):
        self.api.raw += b"changed-after-upload"
        with self.assertRaisesRegex(package.PackageError, "ZIP digest mismatch"):
            self.verify()

    def test_manifest_cannot_substitute_source_config_attempt_or_smoke(self):
        original = self.contents["manifest.json"]
        mutations = [lambda m: m.update(commit="e" * 40), lambda m: m.update(check_config_digest="f" * 64),
                     lambda m: m.update(run_attempt=2), lambda m: m.update(producer_job="untrusted"),
                     lambda m: m.update(reproducible=False), lambda m: m["required_jobs"].pop(),
                     lambda m: m["smoke"].update(goal_fail_pass=False)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.contents["manifest.json"] = original
                self.replace_manifest(mutate)
                with self.assertRaises(package.PackageError):
                    self.verify()

    def test_inner_content_and_exact_version_notes_are_verified(self):
        self.contents["notes.md"] = b"Changed notes\n"
        self.api.raw = zipped(self.contents)
        self.api.artifact["digest"] = f"sha256:{package.sha256(self.api.raw)}"
        with self.assertRaisesRegex(package.PackageError, "inner content"):
            self.verify()
        self.replace_manifest(lambda m: m["files"].update({"notes.md": {
            "sha256": package.sha256(self.contents["notes.md"]), "size": len(self.contents["notes.md"])}}))
        with self.assertRaisesRegex(package.PackageError, "notes differ"):
            self.verify()


class ArchiveBoundaryTests(unittest.TestCase):
    def test_zip_rejects_path_escape_duplicate_extra_symlink_and_oversize(self):
        good = {name: b"valid" for name in package.FILES}
        cases = []
        changed = dict(good)
        changed["../escape"] = changed.pop("notes.md")
        cases.append(zipped(changed))
        cases.append(zipped({**good, "unexpected": b"extra"}))
        changed = dict(good)
        changed["notes.md"] = b"x" * (package.LIMITS["notes.md"] + 1)
        cases.append(zipped(changed))
        duplicate = io.BytesIO()
        with zipfile.ZipFile(duplicate, "w") as archive, warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            for name in ["package.tar.gz", "package.tar.gz.sha256", "notes.md", "notes.md"]:
                archive.writestr(name, b"duplicate")
        cases.append(duplicate.getvalue())
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            for name in package.FILES:
                entry = zipfile.ZipInfo(name)
                entry.create_system = 3
                entry.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(entry, b"/tmp/untrusted")
        cases.append(stream.getvalue())
        for raw in cases:
            with self.subTest(size=len(raw)), self.assertRaises(package.PackageError):
                package.unpack_zip(raw)

    def test_tar_rejects_escape_symlinks_and_devices(self):
        for name, kind in [("pkstack/../../escape", tarfile.REGTYPE),
                           ("pkstack/link", tarfile.SYMTYPE), ("pkstack/device", tarfile.CHRTYPE)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                raw = io.BytesIO()
                with tarfile.open(fileobj=raw, mode="w:gz") as archive:
                    entry = tarfile.TarInfo(name)
                    entry.type = kind
                    entry.linkname = "/tmp/outside"
                    archive.addfile(entry)
                with self.assertRaises(package.PackageError):
                    package.extract_archive(raw.getvalue(), Path(temporary) / "extract")

    def test_github_token_is_not_forwarded_to_artifact_storage(self):
        client = package.GitHub("fixture-secret")
        requests = []
        class Opener:
            def open(self, request, timeout):
                requests.append(request)
                if len(requests) == 1:
                    raise HTTPError(request.full_url, 302, "redirect", {"Location": "https://store.example/artifact?signature=fixture"}, None)
                return io.BytesIO(b"zip payload")
        client.opener = Opener()
        self.assertEqual(client.download("repos/example/pkstack/actions/artifacts/1/zip"), b"zip payload")
        self.assertEqual(requests[0].get_header("Authorization"), "Bearer fixture-secret")
        self.assertIsNone(requests[1].get_header("Authorization"))

    def test_only_http_404_means_absent_tag_not_denied_or_failed_api(self):
        client = package.GitHub("fixture-secret")
        for code in [403, 404, 500]:
            class Opener:
                def open(self, request, timeout):
                    raise HTTPError(request.full_url, code, "fixture", {}, None)
            client.opener = Opener()
            expected = package.ResourceNotFound if code == 404 else package.PackageError
            with self.subTest(code=code), self.assertRaises(expected) as caught:
                client.get("repos/example/pkstack/git/ref/tags/v0.3.0")
            self.assertEqual(isinstance(caught.exception, package.ResourceNotFound), code == 404)

    def test_producer_cli_rejects_pr_execution(self):
        parser_env = {**os.environ, "GITHUB_EVENT_NAME": "pull_request", "GITHUB_REF": "refs/pull/1/merge",
                      "GITHUB_JOB": "package"}
        result = subprocess.run([sys.executable, str(Path(package.__file__)), "build", "--output-dir", "/unused",
                                 "--repository", REPOSITORY, "--repository-id", str(REPOSITORY_ID),
                                 "--sha", "a" * 40, "--run-id", "1", "--run-attempt", "1"],
                                env=parser_env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("main push package job", result.stderr)


if __name__ == "__main__":
    unittest.main()
