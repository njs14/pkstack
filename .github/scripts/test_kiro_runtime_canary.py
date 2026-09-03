#!/usr/bin/env python3
"""Unit and static-contract tests for the read-only Kiro runtime canary."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / ".github/scripts"
sys.path.insert(0, str(SCRIPT_DIR))
MODULE_PATH = SCRIPT_DIR / "kiro_runtime_canary.py"
SPEC = importlib.util.spec_from_file_location("kiro_runtime_canary", MODULE_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import contract guard
    raise RuntimeError("could not load Kiro runtime canary")
canary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(canary)


class FakeResponse(io.BytesIO):
    def __init__(self, body: bytes, url: str) -> None:
        super().__init__(body)
        self.headers = {"Content-Length": str(len(body))}
        self._url = url

    def geturl(self) -> str:
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def manifest(*, version: str = canary.PINNED_CLI_VERSION, sha256: str | None = None) -> bytes:
    package = {
        **canary.TARGET_SELECTOR,
        "download": f"{version}/{canary.CLI_ARCHIVE_NAME}",
        "sha256": sha256 or canary.PINNED_CLI_SHA256,
        "size": canary.PINNED_CLI_SIZE,
    }
    return json.dumps({"version": version, "packages": [package]}).encode()


def _one(pattern: str, text: str, label: str) -> str | tuple[str, ...]:
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    if len(matches) != 1:
        raise AssertionError(f"{label} must have exactly one match, got {len(matches)}")
    return matches[0]


def assert_pin_contract(texts: dict[str, str]) -> None:
    version = canary.PINNED_CLI_VERSION
    sha256 = canary.PINNED_CLI_SHA256
    url_pattern = (
        r"https://prod\.download\.cli\.kiro\.dev/stable/([0-9]+\.[0-9]+\.[0-9]+)/"
        r"kirocli-x86_64-linux\.tar\.xz"
    )

    maintenance = texts["maintenance"]
    maintenance_url_version = _one(url_pattern, maintenance, "maintenance URL")
    archive_versions = re.findall(r"kirocli-([0-9]+\.[0-9]+\.[0-9]+)\.tar\.xz", maintenance)
    if archive_versions != [version, version]:
        raise AssertionError("maintenance archive path/cache path versions diverged")
    cache_version, cache_sha = _one(
        r"key: kiro-cli-linux-x86-64-([0-9]+\.[0-9]+\.[0-9]+)-([0-9a-f]{64})$",
        maintenance,
        "maintenance cache identity",
    )
    checksum_sha = _one(
        r'^\s+([0-9a-f]{64}) \\\n\s+"\$KIRO_ARCHIVE" \| sha256sum --check$',
        maintenance,
        "maintenance checksum",
    )
    if (maintenance_url_version, cache_version, cache_sha, checksum_sha) != (
        version,
        version,
        sha256,
        sha256,
    ):
        raise AssertionError("maintenance URL/cache/checksum tuple diverged")

    for label in ("credential-smoke", "permission-smoke"):
        text = texts[label]
        url_version = _one(url_pattern, text, f"{label} URL")
        archive_version = _one(
            r'archive="\$SMOKE_ROOT/kirocli-([0-9]+\.[0-9]+\.[0-9]+)\.tar\.xz"$',
            text,
            f"{label} archive path",
        )
        checksum = _one(
            r'^\s+([0-9a-f]{64}) \\\n\s+"\$archive" \| sha256sum --check$',
            text,
            f"{label} checksum",
        )
        probe = _one(r'= "kiro-cli ([0-9]+\.[0-9]+\.[0-9]+)"$', text, f"{label} version probe")
        if (url_version, archive_version, checksum, probe) != (
            version,
            version,
            sha256,
            version,
        ):
            raise AssertionError(f"{label} pin tuple diverged")

    setup = texts["runtime-setup"]
    setup_sha = _one(r"^expected_sha256=([0-9a-f]{64})$", setup, "runtime setup SHA")
    setup_version = _one(r'= "kiro-cli ([0-9]+\.[0-9]+\.[0-9]+)"$', setup, "runtime setup version")
    if (setup_sha, setup_version) != (sha256, version):
        raise AssertionError("runtime setup pin tuple diverged")

    runtime_canary = texts["runtime-canary"]
    canary_version = _one(
        r'^PINNED_CLI_VERSION = "([0-9]+\.[0-9]+\.[0-9]+)"$',
        runtime_canary,
        "canary version",
    )
    canary_sha = _one(r'^PINNED_CLI_SHA256 = "([0-9a-f]{64})"$', runtime_canary, "canary SHA")
    canary_size = _one(r"^PINNED_CLI_SIZE = ([0-9_]+)$", runtime_canary, "canary size")
    if (canary_version, canary_sha, canary_size) != (
        version,
        sha256,
        f"{canary.PINNED_CLI_SIZE:_}",
    ):
        raise AssertionError("canary pin tuple diverged")
    if (
        'PINNED_CLI_URL = f"{CLI_DOWNLOAD_ORIGIN}{PINNED_CLI_VERSION}/{CLI_ARCHIVE_NAME}"'
        not in runtime_canary
        or 'and target["size"] == PINNED_CLI_SIZE' not in runtime_canary
    ):
        raise AssertionError("canary URL/size identity is not derived and enforced")


class KiroRuntimeCanaryTests(unittest.TestCase):
    def test_manifest_selects_one_exact_target_and_classifies_pin(self) -> None:
        target = canary._parse_manifest(manifest())
        self.assertEqual(target["download_url"], canary.PINNED_CLI_URL)
        self.assertEqual(canary._pin_status(target), "match")

        newer = canary._parse_manifest(manifest(version="2.22.0", sha256="a" * 64))
        self.assertEqual(canary._pin_status(newer), "newer")
        rollback = canary._parse_manifest(manifest(version="2.20.9", sha256="b" * 64))
        self.assertEqual(canary._pin_status(rollback), "rollback")
        republished = canary._parse_manifest(manifest(sha256="c" * 64))
        self.assertEqual(canary._pin_status(republished), "republished")

    def test_manifest_rejects_ambiguous_or_mutable_shape(self) -> None:
        value = json.loads(manifest())
        value["packages"].append(value["packages"][0].copy())
        with self.assertRaisesRegex(canary.CanaryError, "exactly one"):
            canary._parse_manifest(json.dumps(value).encode())

        value = json.loads(manifest())
        value["packages"][0]["download"] = "elsewhere/archive.tar.xz"
        with self.assertRaisesRegex(canary.CanaryError, "derived"):
            canary._parse_manifest(json.dumps(value).encode())

        value = json.loads(manifest())
        value["unexpected"] = True
        with self.assertRaisesRegex(canary.CanaryError, "root schema"):
            canary._parse_manifest(json.dumps(value).encode())

    def test_archive_extraction_writes_only_two_regular_executables(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "runtime.tar.xz"
            bin_dir = root / "bin"
            bin_dir.mkdir()
            with tarfile.open(archive_path, "w:xz") as archive:
                for name, body in (
                    ("kirocli/bin/kiro-cli", b"cli"),
                    ("kirocli/bin/kiro-cli-chat", b"chat"),
                    ("unrelated/file", b"ignored"),
                ):
                    info = tarfile.TarInfo(name)
                    info.size = len(body)
                    archive.addfile(info, io.BytesIO(body))
            extracted = canary._extract_binaries(
                archive_path,
                bin_dir,
                expected_sizes={
                    "kirocli/bin/kiro-cli": 3,
                    "kirocli/bin/kiro-cli-chat": 4,
                },
            )
            self.assertEqual(extracted["kiro-cli"].read_bytes(), b"cli")
            self.assertEqual(extracted["kiro-cli-chat"].read_bytes(), b"chat")
            self.assertFalse((bin_dir / "file").exists())
            self.assertEqual(extracted["kiro-cli"].stat().st_mode & 0o777, 0o500)

    def test_pinned_archive_member_sizes_are_exact_and_bounded(self) -> None:
        self.assertEqual(
            canary.PINNED_BINARY_SIZES,
            {
                "kirocli/bin/kiro-cli": 113_921_088,
                "kirocli/bin/kiro-cli-chat": 838_911_376,
            },
        )
        self.assertLessEqual(max(canary.PINNED_BINARY_SIZES.values()), canary.MAX_BINARY_BYTES)
        self.assertLessEqual(canary.MAX_BINARY_BYTES, 1024 * 1024 * 1024)
        bodies = {
            "kirocli/bin/kiro-cli": b"cli",
            "kirocli/bin/kiro-cli-chat": b"chat",
        }
        for changed_name in bodies:
            with (
                self.subTest(changed_name=changed_name),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                archive_path = root / "runtime.tar.xz"
                bin_dir = root / "bin"
                bin_dir.mkdir()
                with tarfile.open(archive_path, "w:xz") as archive:
                    for name, body in bodies.items():
                        info = tarfile.TarInfo(name)
                        info.size = len(body)
                        archive.addfile(info, io.BytesIO(body))
                expected = {name: len(body) for name, body in bodies.items()}
                expected[changed_name] += 1
                with self.assertRaisesRegex(canary.CanaryError, "member size changed"):
                    canary._extract_binaries(
                        archive_path,
                        bin_dir,
                        expected_sizes=expected,
                    )
                self.assertFalse((bin_dir / changed_name.rsplit("/", 1)[-1]).exists())

    def test_unpinned_archive_uses_only_the_generic_member_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "runtime.tar.xz"
            bin_dir = root / "bin"
            bin_dir.mkdir()
            with tarfile.open(archive_path, "w:xz") as archive:
                for name, body in (
                    ("kirocli/bin/kiro-cli", b"cli"),
                    ("kirocli/bin/kiro-cli-chat", b"chat"),
                ):
                    info = tarfile.TarInfo(name)
                    info.size = len(body)
                    archive.addfile(info, io.BytesIO(body))
            extracted = canary._extract_binaries(archive_path, bin_dir)
            self.assertEqual(set(extracted), {"kiro-cli", "kiro-cli-chat"})

    def test_archive_member_above_generic_bound_fails_before_extractfile(self) -> None:
        class OversizedMember:
            name = "kirocli/bin/kiro-cli-chat"
            size = canary.MAX_BINARY_BYTES + 1

            @staticmethod
            def isfile() -> bool:
                return True

        class FakeArchive:
            def __enter__(self):
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def __iter__(self):
                return iter([OversizedMember()])

            @staticmethod
            def extractfile(member: object) -> None:
                del member
                raise AssertionError("oversized member must fail before extraction")

        with (
            tempfile.TemporaryDirectory() as temporary,
            mock.patch.object(canary.tarfile, "open", return_value=FakeArchive()),
        ):
            bin_dir = Path(temporary) / "bin"
            bin_dir.mkdir()
            with self.assertRaisesRegex(canary.CanaryError, "member size is invalid"):
                canary._extract_binaries(Path(temporary) / "unused.tar.xz", bin_dir)
            self.assertEqual(list(bin_dir.iterdir()), [])

    def test_only_the_complete_pin_tuple_enables_exact_member_sizes(self) -> None:
        target = canary._parse_manifest(manifest())
        self.assertIs(canary._pinned_binary_sizes(target), canary.PINNED_BINARY_SIZES)
        mutations = {
            "version": "2.22.0",
            "sha256": "a" * 64,
            "download_url": canary.PINNED_CLI_URL.replace("2.21.0", "2.20.0"),
            "size": canary.PINNED_CLI_SIZE - 1,
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                self.assertIsNone(canary._pinned_binary_sizes({**target, field: value}))

    def test_archive_extraction_rejects_linked_executable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "runtime.tar.xz"
            bin_dir = root / "bin"
            bin_dir.mkdir()
            with tarfile.open(archive_path, "w:xz") as archive:
                info = tarfile.TarInfo("kirocli/bin/kiro-cli")
                info.type = tarfile.SYMTYPE
                info.linkname = "/tmp/foreign"
                archive.addfile(info)
            with self.assertRaisesRegex(canary.CanaryError, "invalid"):
                canary._extract_binaries(archive_path, bin_dir)

    def test_archive_download_enforces_manifest_size_and_digest(self) -> None:
        body = b"advertised archive bytes"
        target = {
            "download_url": canary.PINNED_CLI_URL,
            "size": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "archive.tar.xz"
            with mock.patch.object(
                canary.URL_OPENER,
                "open",
                return_value=FakeResponse(body, canary.PINNED_CLI_URL),
            ):
                canary._download_archive(target, destination)
            self.assertEqual(destination.read_bytes(), body)

            bad_destination = Path(temporary) / "bad.tar.xz"
            with (
                mock.patch.object(
                    canary.URL_OPENER,
                    "open",
                    return_value=FakeResponse(body, canary.PINNED_CLI_URL),
                ),
                self.assertRaisesRegex(canary.CanaryError, "size and SHA-256"),
            ):
                canary._download_archive({**target, "sha256": "0" * 64}, bad_destination)
            self.assertFalse(bad_destination.exists())

    def test_command_output_is_os_bounded(self) -> None:
        return_code, output, error = canary._run_bounded(
            [sys.executable, "-c", "import os; os.write(1, b'x' * 262144)"],
            cwd=ROOT,
            environment={"LANG": "C.UTF-8", "PATH": "/usr/bin:/bin"},
            timeout=10,
        )
        self.assertIn(return_code, {0, -25})
        self.assertLessEqual(len(output), canary.MAX_COMMAND_BYTES)
        self.assertLess(len(output), 262144)
        self.assertLessEqual(len(error), canary.MAX_COMMAND_BYTES)

    def test_exact_version_probe_fails_before_agent_processing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scratch = Path(temporary)
            (scratch / "bin").mkdir()
            (scratch / "workspace/.kiro/agents").mkdir(parents=True)
            with (
                mock.patch.object(
                    canary, "_run_bounded", return_value=(0, b"kiro-cli 2.22.0\n", b"")
                ) as run,
                self.assertRaisesRegex(canary.CanaryError, "version probe"),
            ):
                canary._probe_runtime(ROOT, scratch, "2.21.0")
            self.assertEqual(run.call_count, 1)

    def test_workspace_discovery_requires_exact_workspace_rows(self) -> None:
        output = "\n".join(
            ["\x1b[0mWorkspace: /repo/.kiro/agents"]
            + [f"  {name:<30} Workspace description" for name in canary.EXPECTED_AGENTS]
            + ["  global-helper                  Global description"]
        ).encode()
        self.assertEqual(canary._workspace_agents(output), tuple(sorted(canary.EXPECTED_AGENTS)))
        with self.assertRaisesRegex(canary.CanaryError, "duplicate"):
            canary._workspace_agents(output + b"\n  pstack Workspace duplicate\n")

    def test_runtime_probe_uses_only_non_chat_agent_commands(self) -> None:
        replies = [
            (0, b"kiro-cli 2.21.0\n", b""),
            *((0, b"valid\n", b"") for _ in canary.EXPECTED_AGENTS),
            (
                0,
                b"",
                "\n".join(f"  {name:<30} Workspace ok" for name in canary.EXPECTED_AGENTS).encode(),
            ),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            scratch = Path(temporary)
            (scratch / "bin").mkdir()
            (scratch / "workspace/.kiro/agents").mkdir(parents=True)
            with mock.patch.object(canary, "_run_bounded", side_effect=replies) as run:
                result = canary._probe_runtime(ROOT, scratch, "2.21.0")
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0][-1], "--version")
        self.assertEqual(
            [command[1:3] for command in commands[1:-1]],
            [["agent", "validate"]] * len(canary.EXPECTED_AGENTS),
        )
        self.assertTrue(all(Path(command[0]).name == "kiro-cli-chat" for command in commands[1:]))
        self.assertEqual(commands[-1][1:], ["agent", "list"])
        self.assertEqual(Path(commands[-1][0]).name, "kiro-cli-chat")
        self.assertFalse(any("chat" in command[1:] for command in commands))
        self.assertEqual(result["agent_schema_validated"], list(canary.EXPECTED_AGENTS))
        self.assertTrue(result["workspace_agent_discovery_validated"])
        for call in run.call_args_list:
            self.assertNotIn("KIRO_API_KEY", call.kwargs["environment"])

    def test_inventory_is_the_only_command_that_receives_the_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runner = Path(temporary)
            scratch = runner / canary.SCRATCH_PREFIX
            scratch.mkdir()
            (scratch / "bin").mkdir()
            state = {
                "schema_version": 1,
                "stable_cli": {"pin_status": "match"},
                "runtime": {"model_inventory_validated": False},
                "observations": {},
            }
            canary._replace_state(scratch / canary.STATE_NAME, state)
            inventory = {
                "default_model": "gpt-5.6-sol",
                "models": [canary.validate_inventory_bytes.__globals__["EXPECTED_MODEL"]],
            }
            output = json.dumps(inventory).encode()
            observed_environment = {}
            observed_commands = []

            def fake_run(
                command: list[str],
                *,
                cwd: Path,
                environment: dict[str, str],
                timeout: int,
            ) -> tuple[int, bytes, bytes]:
                del cwd, timeout
                observed_commands.append(command)
                observed_environment.update(environment)
                return 0, output, b""

            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}, clear=False),
                mock.patch.object(canary, "_run_bounded", side_effect=fake_run) as run,
            ):
                result = canary._inventory(ROOT, scratch, runner)
                self.assertNotIn("KIRO_API_KEY", os.environ)
            self.assertEqual(observed_environment["KIRO_API_KEY"], "sentinel-secret")
            self.assertEqual(
                observed_commands[0][1:], ["chat", "--list-models", "--format", "json"]
            )
            self.assertEqual(run.call_count, 1)
            self.assertTrue(result["runtime"]["model_inventory_validated"])
            self.assertEqual(
                result["runtime"]["model_inventory_sha256"], hashlib.sha256(output).hexdigest()
            )

    def test_inventory_refuses_unpinned_binary_before_reading_the_secret(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runner = Path(temporary)
            scratch = runner / canary.SCRATCH_PREFIX
            scratch.mkdir()
            state = {
                "schema_version": 1,
                "stable_cli": {"pin_status": "newer"},
                "runtime": {"model_inventory_validated": False},
                "observations": {},
            }
            canary._replace_state(scratch / canary.STATE_NAME, state)
            with (
                mock.patch.dict(os.environ, {"KIRO_API_KEY": "untouched-secret"}, clear=False),
                mock.patch.object(canary, "_run_bounded") as run,
            ):
                with self.assertRaisesRegex(canary.CanaryError, "unreviewed"):
                    canary._inventory(ROOT, scratch, runner)
                self.assertEqual(os.environ.get("KIRO_API_KEY"), "untouched-secret")
            run.assert_not_called()

    def test_inventory_rejects_literal_key_in_stdout_or_stderr(self) -> None:
        inventory = {
            "default_model": "gpt-5.6-sol",
            "models": [canary.validate_inventory_bytes.__globals__["EXPECTED_MODEL"]],
        }
        valid = json.dumps(inventory).encode()
        cases = (
            ("inventory-stdout", (0, valid + b"sentinel-secret", b"")),
            ("inventory-stderr", (0, valid, b"sentinel-secret")),
        )
        for label, reply in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                runner = Path(temporary)
                scratch = runner / canary.SCRATCH_PREFIX
                scratch.mkdir()
                (scratch / "bin").mkdir()
                (scratch / "workspace").mkdir()
                canary._replace_state(
                    scratch / canary.STATE_NAME,
                    {
                        "schema_version": 1,
                        "stable_cli": {"pin_status": "match"},
                        "runtime": {"model_inventory_validated": False},
                        "observations": {},
                    },
                )
                with (
                    mock.patch.dict(os.environ, {"KIRO_API_KEY": "sentinel-secret"}, clear=False),
                    mock.patch.object(canary, "_run_bounded", return_value=reply),
                    self.assertRaisesRegex(canary.CanaryError, "credential material"),
                ):
                    canary._inventory(ROOT, scratch, runner)

    def test_observation_parser_failures_are_non_gating(self) -> None:
        for error in (LookupError("unknown encoding"), TypeError("shape")):
            with (
                self.subTest(error=type(error).__name__),
                mock.patch.object(
                    canary, "_fetch_bytes", return_value=b"x" * canary.MAX_OBSERVATION_BYTES
                ),
            ):
                result = canary._safe_observation(
                    "advisory", "https://kiro.dev/llms.txt", mock.Mock(side_effect=error)
                )
            self.assertEqual(result["status"], "unavailable")
            self.assertEqual(result["bytes"], canary.MAX_OBSERVATION_BYTES)
            self.assertEqual(result["error_class"], type(error).__name__)

    def test_remote_errors_do_not_echo_untrusted_values_and_xml_entities_are_rejected(self) -> None:
        hostile = b'{"attacker-controlled":1,"attacker-controlled":2}'
        with self.assertRaises(canary.CanaryError) as duplicate:
            canary._strict_json(hostile, label="remote")
        self.assertNotIn("attacker-controlled", str(duplicate.exception))
        with self.assertRaisesRegex(canary.CanaryError, "forbidden XML"):
            canary._parse_changelog(
                b'<!DOCTYPE feed [<!ENTITY leaked SYSTEM "file:///etc/passwd">]><feed/>'
            )

    def test_observation_collection_enforces_one_aggregate_budget(self) -> None:
        observed_bytes = []

        def fake_observation(
            label: str, url: str, parser: object, *, maximum: int
        ) -> dict[str, object]:
            del parser
            size = min(maximum, 2 * 1024 * 1024)
            observed_bytes.append(size)
            return {"label": label, "url": url, "status": "unavailable", "bytes": size}

        with mock.patch.object(canary, "_safe_observation", side_effect=fake_observation):
            result = canary._collect_observations(ROOT)
        self.assertLessEqual(sum(observed_bytes), canary.MAX_AGGREGATE_OBSERVATION_BYTES)
        all_results = result["product_feeds"] + result["documentation"]
        self.assertIn("aggregate-limit-reached", {item["status"] for item in all_results})

    def test_recorded_documentation_is_bounded_and_deduplicated(self) -> None:
        records = canary._recorded_doc_hashes(ROOT)
        self.assertIn("https://kiro.dev/llms.txt", records)
        self.assertLessEqual(len(records), canary.MAX_DOC_RECORDS)
        self.assertTrue(all(canary.SHA256_RE.fullmatch(value) for value in records.values()))

    def test_cleanup_refuses_a_symlink_or_wrong_sibling(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runner = Path(temporary)
            foreign = runner / "foreign"
            foreign.mkdir()
            sentinel = foreign / "keep"
            sentinel.write_text("keep", encoding="utf-8")
            link = runner / canary.SCRATCH_PREFIX
            link.symlink_to(foreign, target_is_directory=True)
            with self.assertRaisesRegex(canary.CanaryError, "symlink"):
                canary._cleanup(link, runner)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            with self.assertRaisesRegex(canary.CanaryError, "exact runner"):
                canary._cleanup(runner / "wrong-root", runner)

    def test_workflow_is_weekly_read_only_secret_scoped_and_cleanup_bound(self) -> None:
        workflow = (ROOT / ".github/workflows/pk-stack-kiro-runtime-canary.yml").read_text()
        script = MODULE_PATH.read_text()
        self.assertIn('cron: "23 11 * * 1"', workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("permissions: {}", workflow)
        self.assertNotIn("    env:\n      CANARY_ROOT: ${{ runner.temp }}", workflow)
        self.assertEqual(
            workflow.count("CANARY_ROOT: ${{ runner.temp }}/pk-stack-kiro-runtime-canary"),
            4,
        )
        self.assertNotIn("actions/upload-artifact", workflow)
        self.assertNotIn("anthropic", workflow.lower())
        self.assertNotIn("claude", workflow.lower())
        self.assertEqual(workflow.count("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}"), 1)
        self.assertIn("if: steps.prepare.outputs.pin_match == 'true'", workflow)
        self.assertIn('chmod -R a-w -- "$GITHUB_WORKSPACE"', workflow)
        branch_guard = workflow.index("Refuse a non-default-branch dispatch")
        checkout = workflow.index("Check out immutable canary controls")
        prepare = workflow.index("Resolve and probe the advertised stable Kiro runtime")
        self.assertLess(branch_guard, checkout)
        self.assertLess(checkout, prepare)
        self.assertIn('test "$GITHUB_REF" = "refs/heads/$DEFAULT_BRANCH"', workflow)
        self.assertIn("ref: ${{ github.sha }}", workflow)
        self.assertIn("Validate live model inventory without a model turn", workflow)
        self.assertIn("if: always()", workflow)
        self.assertGreaterEqual(workflow.count("env -u KIRO_API_KEY"), 2)
        self.assertEqual(script.count('"chat", "--list-models", "--format", "json"'), 1)
        self.assertNotIn('"--model"', script)
        self.assertNotIn('"--effort"', script)
        inventory_source = script[script.index("def _inventory(") : script.index("def _finalize(")]
        self.assertEqual(inventory_source.count("_run_bounded("), 1)
        self.assertLess(
            inventory_source.index('get("pin_status") != "match"'),
            inventory_source.index('os.environ.pop("KIRO_API_KEY"'),
        )

    def test_candidate_review_uses_only_kiro_hosted_claude(self) -> None:
        maintenance = (
            ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml"
        ).read_text()
        candidate = (ROOT / ".github/workflows/pk-stack-upstream-candidate.yml").read_text()
        self.assertNotIn("reviewer_readiness:", maintenance)
        self.assertIn("needs: [plan, detect]", maintenance)
        self.assertIn("REVIEW_MODEL: claude-opus-5", candidate)
        self.assertIn("REVIEW_EFFORT: xhigh", candidate)
        self.assertIn("--agent pstack-ci-reviewer", candidate)
        self.assertEqual(candidate.count("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}"), 2)
        self.assertNotRegex(
            candidate,
            r"ANTHROPIC_API_KEY|CLAUDE_CODE_OAUTH_TOKEN|OPENAI_API_KEY|XAI_API_KEY|copilot",
        )

    def test_all_active_cli_pin_copies_are_one_derived_tuple(self) -> None:
        version = canary.PINNED_CLI_VERSION
        sha256 = canary.PINNED_CLI_SHA256
        url = canary.PINNED_CLI_URL
        sources = {
            "maintenance": ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml",
            "candidate": ROOT / ".github/workflows/pk-stack-upstream-candidate.yml",
            "credential-smoke": ROOT / ".github/workflows/pk-stack-kiro-credential-smoke.yml",
            "permission-smoke": ROOT / ".github/workflows/pk-stack-kiro-permission-smoke.yml",
            "runtime-setup": ROOT / ".github/scripts/prepare_kiro_maintenance_runtime.sh",
            "runtime-canary": MODULE_PATH,
        }
        texts = {label: path.read_text() for label, path in sources.items()}
        assert_pin_contract(texts)
        for label in ("maintenance", "candidate", "credential-smoke", "permission-smoke"):
            with self.subTest(label=label):
                self.assertEqual(
                    set(
                        re.findall(
                            r"https://prod\.download\.cli\.kiro\.dev/stable/[^/\s]+/"
                            r"kirocli-x86_64-linux\.tar\.xz",
                            texts[label],
                        )
                    ),
                    {url},
                )
                self.assertIn(sha256, texts[label])
        self.assertIn(f"kirocli-{version}.tar.xz", texts["maintenance"])
        self.assertIn(f"kiro-cli-linux-x86-64-{version}-{sha256}", texts["maintenance"])
        self.assertIn(f"expected_sha256={sha256}", texts["runtime-setup"])
        self.assertIn(f'= "{version}"', texts["runtime-canary"])
        self.assertIn(f'= "{sha256}"', texts["runtime-canary"])
        self.assertIn(f"PINNED_CLI_SIZE = {canary.PINNED_CLI_SIZE:_}", texts["runtime-canary"])
        self.assertIn(f'"kiro-cli {version}"', texts["runtime-setup"])

        active_candidates: set[Path] = set()
        for directory in (ROOT / ".github/workflows", ROOT / ".github/scripts"):
            for path in directory.iterdir():
                if (
                    path.is_file()
                    and not path.name.startswith("test_")
                    and canary.CLI_ARCHIVE_NAME in path.read_text(errors="ignore")
                ):
                    active_candidates.add(path)
        self.assertEqual(
            active_candidates,
            {sources[label] for label in sources if label != "runtime-setup"},
        )
        sha_candidates = {
            path
            for directory in (ROOT / ".github/workflows", ROOT / ".github/scripts")
            for path in directory.iterdir()
            if path.is_file()
            and not path.name.startswith("test_")
            and sha256 in path.read_text(errors="ignore")
        }
        self.assertEqual(sha_candidates, set(sources.values()))

    def test_pin_contract_detects_each_stale_copy_class(self) -> None:
        texts = {
            "maintenance": (
                ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml"
            ).read_text(),
            "credential-smoke": (
                ROOT / ".github/workflows/pk-stack-kiro-credential-smoke.yml"
            ).read_text(),
            "permission-smoke": (
                ROOT / ".github/workflows/pk-stack-kiro-permission-smoke.yml"
            ).read_text(),
            "runtime-setup": (
                ROOT / ".github/scripts/prepare_kiro_maintenance_runtime.sh"
            ).read_text(),
            "runtime-canary": MODULE_PATH.read_text(),
        }
        mutations = {
            "maintenance-cache": (
                "maintenance",
                "kiro-cli-linux-x86-64-2.21.0-",
                "kiro-cli-linux-x86-64-2.20.0-",
            ),
            "credential-probe": (
                "credential-smoke",
                '"kiro-cli 2.21.0"',
                '"kiro-cli 2.20.0"',
            ),
            "permission-sha": (
                "permission-smoke",
                canary.PINNED_CLI_SHA256,
                "a" * 64,
            ),
            "runtime-setup-version": (
                "runtime-setup",
                '"kiro-cli 2.21.0"',
                '"kiro-cli 2.20.0"',
            ),
            "canary-size": (
                "runtime-canary",
                "PINNED_CLI_SIZE = 536_335_872",
                "PINNED_CLI_SIZE = 536_335_871",
            ),
        }
        for label, (source, old, new) in mutations.items():
            with self.subTest(label=label):
                changed = texts[source].replace(old, new, 1)
                self.assertNotEqual(changed, texts[source])
                with self.assertRaises(AssertionError):
                    assert_pin_contract({**texts, source: changed})


if __name__ == "__main__":
    unittest.main()
