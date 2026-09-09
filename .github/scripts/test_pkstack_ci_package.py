"""Promotion must bind one complete main-CI attempt and never execute its artifact."""

from __future__ import annotations

import copy
import io
import json
import os
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
import warnings
import zipfile
from email.message import Message
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import OpenerDirector

import pkstack_ci_package as package

REPOSITORY = "example/pkstack"
REPOSITORY_ID = 123
RUN = 456
ATTEMPT = 1
ARTIFACT = 789


def fixture_smoke() -> dict:
    return {
        **dict.fromkeys(package.SMOKE_FLAGS, True),
        "knowledge_mode": "local",
        "doctor_summary": {"pass": 81, "warn": 2, "fail": 0},
    }


def zipped(contents: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in contents.items():
            archive.writestr(name, raw)
    return stream.getvalue()


class ConsumerContentTests(unittest.TestCase):
    def test_repository_power_has_exactly_the_reviewed_consumer_files(self):
        root = Path(__file__).resolve().parents[2]
        package.validate_source(root / "powers/pkstack", package.load_contract(root))


class FakeGitHub:
    def __init__(self, commit: str, raw: bytes):
        self.raw = raw
        self.repo: dict[str, object] = {
            "id": REPOSITORY_ID,
            "full_name": REPOSITORY,
            "private": True,
            "visibility": "private",
            "default_branch": "main",
        }
        self.branch = {"commit": {"sha": commit}}
        self.tag: dict[str, Any] | None = {
            "ref": "refs/tags/v0.3.0",
            "object": {"type": "commit", "sha": commit},
        }
        self.workflow = {"id": 99, "path": package.CI_WORKFLOW, "state": "active"}
        self.run = {
            "id": RUN,
            "run_attempt": ATTEMPT,
            "workflow_id": 99,
            "path": package.CI_WORKFLOW,
            "head_sha": commit,
            "head_branch": "main",
            "event": "push",
            "status": "completed",
            "conclusion": "success",
            "repository": {"id": REPOSITORY_ID},
            "head_repository": {"id": REPOSITORY_ID},
        }
        self.commit = commit
        self.runs = [{"id": RUN}]
        self.jobs = [
            {
                "name": name,
                "status": "completed",
                "conclusion": "success",
                "head_sha": commit,
                "run_id": RUN,
                "run_attempt": ATTEMPT,
            }
            for name in package.REQUIRED_JOBS
        ]
        self.artifact = {
            "id": ARTIFACT,
            "name": package.artifact_name(commit, RUN, ATTEMPT),
            "expired": False,
            "digest": f"sha256:{package.sha256(raw)}",
            "workflow_run": {
                "id": RUN,
                "repository_id": REPOSITORY_ID,
                "head_repository_id": REPOSITORY_ID,
                "head_sha": commit,
                "head_branch": "main",
            },
        }
        self.artifacts = [self.artifact]
        self.downloads = 0
        self.after_download = lambda: None
        self.after_asset_download = lambda: None
        self.release = {
            "id": 321,
            "tag_name": "v0.3.0",
            "draft": False,
            "prerelease": False,
            "html_url": f"https://github.com/{REPOSITORY}/releases/tag/v0.3.0",
        }
        contents = package.unpack_zip(raw)
        archive = contents["package.tar.gz"]
        self.asset_bytes = {
            1001: archive,
            1002: f"{package.sha256(archive)}  pkstack-v0.3.0.tar.gz\n".encode(),
        }
        self.assets = [
            {
                "id": asset_id,
                "name": name,
                "state": "uploaded",
                "size": len(self.asset_bytes[asset_id]),
                "digest": f"sha256:{package.sha256(self.asset_bytes[asset_id])}",
                "download_count": 0,
            }
            for asset_id, name in [
                (1001, "pkstack-v0.3.0.tar.gz"),
                (1002, "pkstack-v0.3.0.tar.gz.sha256"),
            ]
        ]

    def present_tag(self) -> dict[str, Any]:
        """The tag fixture, for cases that mutate a tag they keep present."""
        if self.tag is None:
            raise AssertionError("tag fixture is absent")
        return self.tag

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
        elif relative == "/releases/tags/v0.3.0":
            result = self.release
        elif relative == "/releases/321/assets":
            result = self.assets
        elif relative == "/actions/workflows/pk-stack-ci.yml":
            result = self.workflow
        elif relative == f"/actions/runs/{RUN}":
            result = self.run
        elif relative == "/actions/workflows/99/runs":
            query = parse_qs(parsed.query)
            assert query["head_sha"] == [self.commit]
            assert "event" not in query and query["branch"] == ["main"]
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

    def download_asset(self, path: str, maximum: int) -> bytes:
        asset_id = int(path.rsplit("/", 1)[-1])
        value = self.asset_bytes[asset_id]
        for asset in self.assets:
            if asset["id"] == asset_id:
                asset["download_count"] = 1
        self.after_asset_download()
        return value


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
            ".github/scripts/pkstack_checks.py": 'def config_digest(root):\n    return "'
            + "c" * 64
            + '"\n',
            ".github/workflows/pk-stack-ci.yml": "name: PKStack CI\n",
            "CHANGELOG.md": (
                "# Changes\n\n## [0.3.0]\n\nCurrent [guide](guide.md).\n\n## [0.2.0]\nOld text.\n"
            ),
        }
        files["maintenance/package-content.json"] = json.dumps(
            {
                "schema_version": 1,
                "files": sorted(
                    name.removeprefix("powers/pkstack/")
                    for name in files
                    if name.startswith("powers/pkstack/")
                ),
            }
        )
        for relative, text in files.items():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        for argv in (
            ["init", "--quiet"],
            ["config", "user.email", "test@example.invalid"],
            ["config", "user.name", "Package fixture"],
            ["add", "."],
            ["commit", "--quiet", "-m", "fixture"],
        ):
            subprocess.run(["git", *argv], cwd=self.root, check=True, capture_output=True)
        self.commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True
        ).strip()
        self.output = Path(self.temporary.name) / "built"
        with patch.object(package, "consumer_smoke", return_value=fixture_smoke()):
            self.built = package.build_package(
                self.root, self.output, REPOSITORY, REPOSITORY_ID, self.commit, RUN, ATTEMPT
            )
        self.contents = {path.name: path.read_bytes() for path in self.output.iterdir()}
        self.api = FakeGitHub(self.commit, zipped(self.contents))

    def verify(self, **kwargs):
        return package.verify_package(
            self.root,
            Path(self.temporary.name) / "verified",
            # The stand-in answers the same bounded read-only API surface.
            cast(package.GitHub, self.api),
            REPOSITORY,
            REPOSITORY_ID,
            self.commit,
            "v0.3.0",
            **kwargs,
        )

    def verify_published(self):
        return package.verify_published(
            self.root,
            Path(self.temporary.name) / "published",
            cast(package.GitHub, self.api),
            REPOSITORY,
            REPOSITORY_ID,
            self.commit,
            "v0.3.0",
            RUN,
            ATTEMPT,
            ARTIFACT,
            package.sha256(self.api.raw),
        )

    def test_publication_receipt_binds_downloaded_bytes_to_exact_approved_artifact(self):
        with patch.object(package, "archive_for", side_effect=AssertionError("rebuilt")):
            receipt = self.verify_published()
        self.assertTrue(receipt["ok"])
        self.assertEqual(receipt["archive_sha256"], self.built["archive_sha256"])
        self.assertEqual(receipt["source_run_id"], RUN)
        self.assertEqual(receipt["source_run_attempt"], ATTEMPT)
        self.assertEqual(receipt["artifact_id"], ARTIFACT)
        self.assertEqual(receipt["package_manifest"], json.loads(self.contents["manifest.json"]))
        saved = json.loads(Path(receipt["receipt_path"]).read_text())
        self.assertEqual(
            saved["assets"]["pkstack-v0.3.0.tar.gz"]["sha256"], self.built["archive_sha256"]
        )
        self.assertEqual(
            (Path(self.temporary.name) / "published/downloaded/pkstack-v0.3.0.tar.gz").read_bytes(),
            self.contents["package.tar.gz"],
        )

    def test_changed_published_bytes_never_emit_a_success_receipt(self):
        for asset_id in (1001, 1002):
            with self.subTest(asset_id=asset_id):
                original = dict(self.api.asset_bytes)
                self.api.asset_bytes[asset_id] += b"altered"
                with self.assertRaisesRegex(package.PackageError, "bytes differ"):
                    self.verify_published()
                self.assertFalse((Path(self.temporary.name) / "published/receipt").exists())
                self.api.asset_bytes = original
                # Preserve the failed evidence and use a new output on the next fixture.
                (Path(self.temporary.name) / "published").rename(
                    Path(self.temporary.name) / f"failed-{asset_id}"
                )

    def test_missing_or_replaced_release_assets_and_release_changes_fail(self):
        original = copy.deepcopy((self.api.release, self.api.assets))
        for mode in (
            "missing",
            "duplicate",
            "digest",
            "draft",
            "tag",
            "replaced",
            "attempt",
            "base",
        ):
            with self.subTest(mode=mode):
                self.api.release, self.api.assets = copy.deepcopy(original)
                self.api.after_asset_download = lambda: None
                if mode == "missing":
                    self.api.assets.pop()
                elif mode == "duplicate":
                    self.api.assets.append(copy.deepcopy(self.api.assets[0]))
                elif mode == "digest":
                    self.api.assets[0]["digest"] = "sha256:" + "0" * 64
                elif mode == "draft":
                    self.api.release["draft"] = True
                elif mode == "tag":
                    self.api.release["tag_name"] = "v0.2.0"
                elif mode == "replaced":
                    self.api.after_asset_download = lambda: self.api.assets[0].update(
                        updated_at="changed"
                    )
                elif mode == "attempt":
                    self.api.after_asset_download = lambda: self.api.run.update(run_attempt=2)
                else:
                    self.api.after_asset_download = lambda: self.api.branch["commit"].update(
                        sha="0" * 40
                    )
                with self.assertRaises(package.PackageError):
                    self.verify_published()
                self.assertFalse((Path(self.temporary.name) / "published/receipt").exists())
                (Path(self.temporary.name) / "published").rename(
                    Path(self.temporary.name) / f"failed-{mode}"
                )
                self.api.run["run_attempt"] = ATTEMPT
                self.api.branch["commit"]["sha"] = self.commit

    def test_base_ci_admission_uses_same_complete_main_contract_without_downloads(self):
        # Candidate admission has never depended on repository visibility.
        self.api.repo.update(private=False, visibility="public")
        result = package.verify_base_ci(
            self.root, cast(package.GitHub, self.api), REPOSITORY, REPOSITORY_ID, self.commit
        )
        self.assertEqual(result["tested_sha"], self.commit)
        self.assertEqual(result["source_run_id"], RUN)
        self.assertEqual(self.api.downloads, 0)
        original = copy.deepcopy((self.api.branch, self.api.run, self.api.runs, self.api.jobs))
        for mode in (
            "moved",
            "missing",
            "failed",
            "superseded",
            "attempt",
            "incompatible",
            "wrong-sha",
        ):
            with self.subTest(mode=mode):
                self.api.branch, self.api.run, self.api.runs, self.api.jobs = copy.deepcopy(
                    original
                )
                if mode == "moved":
                    self.api.branch["commit"]["sha"] = "0" * 40
                elif mode == "missing":
                    self.api.runs = []
                elif mode == "failed":
                    self.api.run["conclusion"] = "failure"
                elif mode == "superseded":
                    self.api.runs.append({"id": RUN + 1})
                elif mode == "attempt":
                    self.api.run["run_attempt"] = 2
                elif mode == "wrong-sha":
                    self.api.run["head_sha"] = "0" * 40
                else:
                    self.api.jobs[0]["name"] = "old-aggregate"
                with self.assertRaises(package.PackageError):
                    package.verify_base_ci(
                        self.root,
                        cast(package.GitHub, self.api),
                        REPOSITORY,
                        REPOSITORY_ID,
                        self.commit,
                        RUN,
                        ATTEMPT,
                    )

    def test_dispatched_main_produces_admissible_base_and_promotable_package(self):
        output = Path(self.temporary.name) / "dispatched"
        with patch.object(package, "consumer_smoke", return_value=fixture_smoke()):
            package.build_package(
                self.root,
                output,
                REPOSITORY,
                REPOSITORY_ID,
                self.commit,
                RUN,
                ATTEMPT,
                event="workflow_dispatch",
            )
        self.contents = {path.name: path.read_bytes() for path in output.iterdir()}
        self.api = FakeGitHub(self.commit, zipped(self.contents))
        self.api.run["event"] = "workflow_dispatch"
        result = package.verify_base_ci(
            self.root, cast(package.GitHub, self.api), REPOSITORY, REPOSITORY_ID, self.commit
        )
        self.assertEqual(result["tested_sha"], self.commit)
        self.assertEqual(self.api.downloads, 0)
        self.assertTrue(self.verify_published()["ok"])
        # A newer run or attempt supersedes this proof regardless of trigger type.
        self.api.runs.append({"id": RUN + 1})
        with self.assertRaisesRegex(package.PackageError, "superseded"):
            package.verify_base_ci(
                self.root,
                cast(package.GitHub, self.api),
                REPOSITORY,
                REPOSITORY_ID,
                self.commit,
                RUN,
                ATTEMPT,
            )

    def test_package_manifest_event_must_match_the_actual_main_run(self):
        self.api.run["event"] = "workflow_dispatch"
        with self.assertRaisesRegex(package.PackageError, "manifest"):
            self.verify()

    def test_wrong_commit_or_tag_version_cannot_be_promoted(self):
        for commit, tag in (("0" * 40, "v0.3.0"), (self.commit, "v0.3.1")):
            with self.subTest(commit=commit, tag=tag), self.assertRaises(package.PackageError):
                package.verify_package(
                    self.root,
                    Path(self.temporary.name) / "invalid",
                    cast(package.GitHub, self.api),
                    REPOSITORY,
                    REPOSITORY_ID,
                    commit,
                    tag,
                )

    def replace_manifest(self, mutate):
        manifest = json.loads(self.contents["manifest.json"])
        mutate(manifest)
        self.contents["manifest.json"] = package.json_bytes(manifest)
        self.api.raw = zipped(self.contents)
        self.api.artifact["digest"] = f"sha256:{package.sha256(self.api.raw)}"

    def test_exact_main_success_preserves_built_bytes_without_rebuild_or_execution(self):
        with (
            patch.object(
                package, "archive_for", side_effect=AssertionError("promotion rebuilt archive")
            ),
            patch.object(
                package, "consumer_smoke", side_effect=AssertionError("promotion executed package")
            ),
        ):
            result = self.verify(
                run_id=RUN,
                attempt=ATTEMPT,
                artifact_id=ARTIFACT,
                artifact_digest=package.sha256(self.api.raw),
            )
        self.assertEqual(result["mode"], "verify-only")
        self.assertEqual(result["archive_sha256"], self.built["archive_sha256"])
        promoted = Path(result["output_directory"])
        self.assertEqual(
            {path.name: path.read_bytes() for path in promoted.iterdir()}, self.contents
        )
        self.assertIn(
            f"https://github.com/{REPOSITORY}/blob/{self.commit}/guide.md",
            self.contents["notes.md"].decode(),
        )
        self.assertNotIn("Old text", self.contents["notes.md"].decode())

    def test_archives_are_reproducible_and_preserve_exact_git_contents(self):
        self.assertEqual(
            package.archive_for(self.root, self.commit), self.contents["package.tar.gz"]
        )
        extracted = package.extract_archive(
            self.contents["package.tar.gz"],
            Path(self.temporary.name) / "extract",
            allowed=package.load_contract(self.root),
        )
        self.assertEqual(
            (extracted / "plugin.json").read_bytes(),
            (self.root / "powers/pkstack/plugin.json").read_bytes(),
        )

    def test_source_rejects_untracked_maintainer_content_and_local_clutter(self):
        for name in (
            "tests/local.py",
            "reviews/report.md",
            "benchmarks/local.py",
            "docs/artifacts/preview.html",
            ".venv/pyvenv.cfg",
            "src/pkstack/__pycache__/a.pyc",
            ".pytest_cache/state",
            ".ruff_cache/state",
            "dist/package.whl",
            "assets/banner.png",
        ):
            with self.subTest(name=name):
                target = self.root / "powers/pkstack" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("untracked clutter")
                with self.assertRaisesRegex(package.PackageError, "unexpected"):
                    package.archive_for(self.root, self.commit)
                target.unlink()
                # Empty unexpected directories must fail as well.
                with self.assertRaisesRegex(package.PackageError, "unexpected"):
                    package.archive_for(self.root, self.commit)
                parent = target.parent
                while parent != self.root / "powers/pkstack" and not list(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent

    def test_source_rejects_a_missing_required_consumer_file(self):
        path = self.root / "powers/pkstack/src/pkstack/__init__.py"
        path.unlink()
        with self.assertRaisesRegex(package.PackageError, "missing=.*src/pkstack/__init__.py"):
            package.archive_for(self.root, self.commit)

    def test_archive_rejects_maintainer_files_and_missing_required_assets(self):
        allowed = package.load_contract(self.root)
        for extra, missing in (
            ("tests/local.py", None),
            ("assets/banner.png", None),
            ("docs/artifacts", None),
            (None, "plugin.json"),
            (None, "src/pkstack/__init__.py"),
        ):
            with self.subTest(extra=extra, missing=missing), tempfile.TemporaryDirectory() as temp:
                raw = io.BytesIO()
                with tarfile.open(fileobj=raw, mode="w:gz") as archive:
                    for name in sorted(allowed):
                        if name != missing:
                            archive.add(
                                self.root / "powers/pkstack" / name,
                                arcname=f"pkstack/{name}",
                                recursive=False,
                            )
                    if extra:
                        entry = tarfile.TarInfo(f"pkstack/{extra}")
                        entry.type = (
                            tarfile.DIRTYPE if extra == "docs/artifacts" else tarfile.REGTYPE
                        )
                        archive.addfile(entry)
                with self.assertRaises(package.PackageError):
                    package.extract_archive(raw.getvalue(), Path(temp) / "extract", allowed=allowed)

    def test_changed_working_source_cannot_produce_or_promote(self):
        (self.root / "powers/pkstack/plugin.json").write_text('{"version":"9.9.9"}\n')
        with self.assertRaisesRegex(package.PackageError, "Git identity"):
            self.verify()

    def test_rejects_invalid_run_status_source_event_repository_and_attempt(self):
        mutations = [
            lambda r: r.update(status="in_progress"),
            lambda r: r.update(conclusion="failure"),
            lambda r: r.update(conclusion="cancelled"),
            lambda r: r.update(event="pull_request"),
            lambda r: r.update(event="repository_dispatch"),
            lambda r: r.update(head_branch="other"),
            lambda r: r.update(head_repository={"id": 999}),
            lambda r: r.update(repository={"id": 999}),
            lambda r: r.update(workflow_id=999),
            lambda r: r.update(path=".github/workflows/untrusted.yml"),
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
        with self.assertRaisesRegex(package.PackageError, "no exact main"):
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
        changes = [
            lambda jobs: jobs.pop(),
            lambda jobs: jobs.append(copy.deepcopy(jobs[0])),
            lambda jobs: jobs[0].update(conclusion="skipped"),
            lambda jobs: jobs[0].update(conclusion="neutral"),
            lambda jobs: jobs[0].update(status="in_progress"),
            lambda jobs: jobs[0].update(run_attempt=2),
            lambda jobs: jobs[0].update(head_sha="0" * 40),
        ]
        for mutate in changes:
            with self.subTest(mutation=mutate):
                self.api.jobs = copy.deepcopy(original)
                mutate(self.api.jobs)
                with self.assertRaisesRegex(package.PackageError, "mandatory"):
                    self.verify()

    def test_public_and_private_repositories_can_promote_and_verify_published_bytes(self):
        for private, visibility in ((False, "public"), (True, "private")):
            with self.subTest(visibility=visibility):
                self.api.repo.update(private=private, visibility=visibility)
                self.assertTrue(self.verify()["publication_eligible"])
                self.assertTrue(self.verify_published()["ok"])
                for output in ("verified", "published"):
                    (Path(self.temporary.name) / output).rename(
                        Path(self.temporary.name) / f"{output}-{visibility}"
                    )

    def test_release_repository_visibility_must_be_well_formed_and_consistent(self):
        for private, visibility in (
            (None, "private"),
            (1, "private"),
            ("false", "public"),
            (True, None),
            (True, []),
            (True, "internal"),
            (True, "public"),
            (False, "private"),
        ):
            with self.subTest(private=private, visibility=visibility):
                self.api.repo.update(private=private, visibility=visibility)
                with self.assertRaisesRegex(package.PackageError, "visibility"):
                    self.verify()
        self.api.repo.update(private=True, visibility="private")
        del self.api.repo["visibility"]
        with self.assertRaisesRegex(package.PackageError, "visibility"):
            self.verify()
        self.assertEqual(self.api.downloads, 0)

    def test_public_repository_still_requires_active_hosted_ci_evidence(self):
        self.api.repo.update(private=False, visibility="public")
        self.api.workflow["state"] = "disabled_manually"
        with self.assertRaisesRegex(package.PackageError, "CI workflow is unavailable"):
            self.verify_published()
        self.assertEqual(self.api.downloads, 0)
        self.assertFalse((Path(self.temporary.name) / "published/receipt").exists())

    def test_exact_repository_current_main_tag_and_version_are_required(self):
        original = copy.deepcopy((self.api.repo, self.api.branch, self.api.tag))
        mutations = [
            lambda: self.api.repo.update(id=999),
            lambda: self.api.repo.update(full_name="other/pkstack"),
            lambda: self.api.repo.update(default_branch="development"),
            lambda: self.api.branch["commit"].update(sha="a" * 40),
            lambda: self.api.present_tag()["object"].update(sha="b" * 40),
            lambda: self.api.present_tag().update(ref="refs/tags/v0.2.0"),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.api.repo, self.api.branch, self.api.tag = copy.deepcopy(original)
                mutate()
                with self.assertRaises(package.PackageError):
                    self.verify()

    def test_annotated_tag_is_peeled_to_exact_commit(self):
        self.api.present_tag()["object"] = {"type": "tag", "sha": "d" * 40}
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
        result = subprocess.CompletedProcess(
            ["fixture"], 1, b'{"ok":false,"goal":{"status":"active"}}', b""
        )
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
        mutations = [
            lambda a: a.update(expired=True),
            lambda a: a.update(id=999),
            lambda a: a.update(name="pkstack-release-old-attempt"),
            lambda a: a["workflow_run"].update(head_sha="0" * 40),
            lambda a: a["workflow_run"].update(repository_id=999),
            lambda a: a["workflow_run"].update(head_repository_id=999),
            lambda a: a["workflow_run"].update(head_branch="other"),
        ]
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
        mutations = [
            lambda m: m.update(commit="e" * 40),
            lambda m: m.update(check_config_digest="f" * 64),
            lambda m: m.update(run_attempt=2),
            lambda m: m.update(producer_job="untrusted"),
            lambda m: m.update(reproducible=False),
            lambda m: m["required_jobs"].pop(),
            lambda m: m["smoke"].update(goal_fail_pass=False),
        ]
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
        self.replace_manifest(
            lambda m: m["files"].update(
                {
                    "notes.md": {
                        "sha256": package.sha256(self.contents["notes.md"]),
                        "size": len(self.contents["notes.md"]),
                    }
                }
            )
        )
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
        for name, kind in [
            ("pkstack/../../escape", tarfile.REGTYPE),
            ("pkstack/link", tarfile.SYMTYPE),
            ("pkstack/device", tarfile.CHRTYPE),
        ]:
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
                    headers = Message()
                    headers["Location"] = "https://store.example/artifact?signature=fixture"
                    raise HTTPError(request.full_url, 302, "redirect", headers, None)
                return io.BytesIO(b"zip payload")

        client.opener = cast(OpenerDirector, Opener())
        self.assertEqual(
            client.download("repos/example/pkstack/actions/artifacts/1/zip"), b"zip payload"
        )
        self.assertEqual(requests[0].get_header("Authorization"), "Bearer fixture-secret")
        self.assertIsNone(requests[1].get_header("Authorization"))

    def test_release_download_supports_stream_and_redirect_without_forwarding_token(self):
        for redirect in (False, True):
            with self.subTest(redirect=redirect):
                client = package.GitHub("fixture-secret")
                requests = []

                class Opener:
                    def open(self, request, timeout, recorded=requests, redirects=redirect):
                        recorded.append(request)
                        if redirects and len(recorded) == 1:
                            headers = Message()
                            headers["Location"] = (
                                "https://release-assets.githubusercontent.com/asset"
                            )
                            raise HTTPError(request.full_url, 302, "redirect", headers, None)
                        return io.BytesIO(b"asset")

                client.opener = cast(OpenerDirector, Opener())
                self.assertEqual(
                    client.download_asset("repos/example/pkstack/releases/assets/1", 5), b"asset"
                )
                self.assertEqual(requests[0].get_header("Accept"), "application/octet-stream")
                self.assertEqual(requests[0].get_header("Authorization"), "Bearer fixture-secret")
                if redirect:
                    self.assertIsNone(requests[1].get_header("Authorization"))

    def test_only_http_404_means_absent_tag_not_denied_or_failed_api(self):
        client = package.GitHub("fixture-secret")
        for code in [403, 404, 500]:

            class Opener:
                status = code

                def open(self, request, timeout):
                    raise HTTPError(request.full_url, self.status, "fixture", Message(), None)

            client.opener = cast(OpenerDirector, Opener())
            expected = package.ResourceNotFound if code == 404 else package.PackageError
            with self.subTest(code=code), self.assertRaises(expected) as caught:
                client.get("repos/example/pkstack/git/ref/tags/v0.3.0")
            self.assertEqual(isinstance(caught.exception, package.ResourceNotFound), code == 404)

    def test_producer_cli_rejects_pr_execution(self):
        parser_env = {
            **os.environ,
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/1/merge",
            "GITHUB_JOB": "package",
        }
        result = subprocess.run(
            [
                sys.executable,
                str(Path(package.__file__)),
                "build",
                "--output-dir",
                "/unused",
                "--repository",
                REPOSITORY,
                "--repository-id",
                str(REPOSITORY_ID),
                "--sha",
                "a" * 40,
                "--run-id",
                "1",
                "--run-attempt",
                "1",
            ],
            env=parser_env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("main CI package job", result.stderr)


if __name__ == "__main__":
    unittest.main()
