#!/usr/bin/env python3
"""Bounded, read-only Kiro runtime and product-drift canary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, BinaryIO

from validate_kiro_model_inventory import InventoryError, validate_inventory_bytes

PINNED_CLI_VERSION = "2.21.0"
PINNED_CLI_SHA256 = "6eccb46617a84690fc892219f264f7617312761c9a3d7e38cc47a0e2ab0152b7"
PINNED_CLI_SIZE = 536_335_872
CLI_MANIFEST_URL = "https://prod.download.cli.kiro.dev/stable/latest/manifest.json"
CLI_DOWNLOAD_ORIGIN = "https://prod.download.cli.kiro.dev/stable/"
CLI_ARCHIVE_NAME = "kirocli-x86_64-linux.tar.xz"
PINNED_CLI_URL = f"{CLI_DOWNLOAD_ORIGIN}{PINNED_CLI_VERSION}/{CLI_ARCHIVE_NAME}"

IDE_METADATA_URL = "https://prod.download.desktop.kiro.dev/stable/metadata-darwin-arm64-stable.json"
CREW_CLI_FEED_URL = "https://download.crew.kiro.dev/feed/nightly/latest-cli.json"
CREW_DESKTOP_FEED_URL = "https://updates.crew.kiro.dev/feed/nightly/latest-mac.yml"
CHANGELOG_FEED_URL = "https://kiro.dev/changelog/feed.atom"
DOC_EVIDENCE_PATHS = (
    "reviews/kiro-model-guidance-evidence.json",
    "reviews/kiro-v3-agent-discovery-probe.json",
)

EXPECTED_AGENTS = (
    "pkstack",
    "pkstack-architect",
    "pkstack-ci-reviewer",
    "pkstack-maintainer",
    "pkstack-reviewer",
    "pkstack-verifier",
)
TARGET_SELECTOR = {
    "kind": "deb",
    "targetTriple": "x86_64-unknown-linux-gnu",
    "os": "linux",
    "fileType": "tarXz",
    "architecture": "x86_64",
    "variant": "headless",
    "channel": "stable",
}
TARGET_PACKAGE_KEYS = set(TARGET_SELECTOR) | {"download", "sha256", "size"}
ALLOWED_HOSTS = {
    "download.crew.kiro.dev",
    "kiro.dev",
    "prod.download.cli.kiro.dev",
    "prod.download.desktop.kiro.dev",
    "updates.crew.kiro.dev",
}

MAX_MANIFEST_BYTES = 128 * 1024
MAX_OBSERVATION_BYTES = 2 * 1024 * 1024
MAX_AGGREGATE_OBSERVATION_BYTES = 16 * 1024 * 1024
MAX_ARCHIVE_BYTES = 700 * 1024 * 1024
MAX_BINARY_BYTES = 1024 * 1024 * 1024
MAX_COMMAND_BYTES = 128 * 1024
MAX_STATE_BYTES = 256 * 1024
MAX_PACKAGES = 64
MAX_DOC_RECORDS = 24
MAX_TAR_MEMBERS = 200_000
STATE_NAME = "state.json"
SCRATCH_PREFIX = "pkstack-kiro-runtime-canary"
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
VERSION_RE = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)\Z")
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
WORKSPACE_ROW_RE = re.compile(r"^\s*(?:\*\s*)?([a-z0-9][a-z0-9_-]*)\s+Workspace(?:\s|$)")
SETTINGS = (
    b"{\n"
    b'  "app.disableAutoupdates": true,\n'
    b'  "chat.disableInheritingDefaultResources": true,\n'
    b'  "telemetry.enabled": false\n'
    b"}\n"
)
PINNED_BINARY_SIZES = {
    "kirocli/bin/kiro-cli": 113_921_088,
    "kirocli/bin/kiro-cli-chat": 838_911_376,
}


class CanaryError(ValueError):
    """Raised when a gating canary contract cannot be proved."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise CanaryError("remote JSON contract contains a duplicate key")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    del value
    raise CanaryError("remote JSON contract contains a non-finite value")


def _strict_json(raw: bytes, *, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CanaryError(f"{label} is not strict UTF-8 JSON") from exc


def _validate_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in {None, 443}
        or parsed.query
        or parsed.fragment
    ):
        raise CanaryError("remote URL is outside the bounded Kiro source allowlist")
    return url


class _AllowlistedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: BinaryIO,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        _validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


URL_OPENER = urllib.request.build_opener(_AllowlistedRedirectHandler())


def _fetch_bytes(url: str, *, maximum: int) -> bytes:
    _validate_url(url)
    requested_host = urllib.parse.urlsplit(url).hostname
    request = urllib.request.Request(url, headers={"User-Agent": "PKStack-Kiro-Canary/1"})
    try:
        with URL_OPENER.open(request, timeout=20) as response:
            final_url = _validate_url(response.geturl())
            if urllib.parse.urlsplit(final_url).hostname != requested_host:
                raise CanaryError("remote observation redirected across source origins")
            advertised = response.headers.get("Content-Length")
            if advertised is not None and int(advertised) > maximum:
                raise CanaryError("remote observation exceeds its byte limit")
            raw = response.read(maximum + 1)
    except CanaryError:
        raise
    except Exception as exc:
        raise CanaryError("remote observation is unavailable") from exc
    if not raw or len(raw) > maximum:
        raise CanaryError("remote observation is empty or exceeds its byte limit")
    return raw


def _parse_manifest(raw: bytes) -> dict[str, Any]:
    if not raw or len(raw) > MAX_MANIFEST_BYTES:
        raise CanaryError("stable CLI manifest is empty or exceeds its byte limit")
    document = _strict_json(raw, label="stable CLI manifest")
    if not isinstance(document, dict) or set(document) != {"version", "packages"}:
        raise CanaryError("stable CLI manifest root schema changed")
    version = document["version"]
    packages = document["packages"]
    if not isinstance(version, str) or VERSION_RE.fullmatch(version) is None:
        raise CanaryError("stable CLI manifest version is invalid")
    if not isinstance(packages, list) or not 1 <= len(packages) <= MAX_PACKAGES:
        raise CanaryError("stable CLI manifest package list is outside its item limit")
    matches = [
        item
        for item in packages
        if isinstance(item, dict)
        and all(item.get(key) == value for key, value in TARGET_SELECTOR.items())
    ]
    if len(matches) != 1:
        raise CanaryError(
            "stable CLI manifest must contain exactly one x86_64 Linux headless tar.xz"
        )
    package = matches[0]
    if set(package) != TARGET_PACKAGE_KEYS:
        raise CanaryError("stable CLI target package schema changed")
    expected_download = f"{version}/{CLI_ARCHIVE_NAME}"
    if package["download"] != expected_download:
        raise CanaryError("stable CLI target download is not derived from its version")
    sha256 = package["sha256"]
    size = package["size"]
    if not isinstance(sha256, str) or SHA256_RE.fullmatch(sha256) is None:
        raise CanaryError("stable CLI target SHA-256 is invalid")
    if type(size) is not int or not 1 <= size <= MAX_ARCHIVE_BYTES:
        raise CanaryError("stable CLI target size is invalid")
    return {
        "version": version,
        "download": expected_download,
        "download_url": urllib.parse.urljoin(CLI_DOWNLOAD_ORIGIN, expected_download),
        "sha256": sha256,
        "size": size,
    }


def _version_tuple(value: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(value)
    if match is None:
        raise CanaryError("CLI version is invalid")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _pin_status(target: dict[str, Any]) -> str:
    if (
        target["version"] == PINNED_CLI_VERSION
        and target["sha256"] == PINNED_CLI_SHA256
        and target["download_url"] == PINNED_CLI_URL
        and target["size"] == PINNED_CLI_SIZE
    ):
        return "match"
    advertised = _version_tuple(target["version"])
    pinned = _version_tuple(PINNED_CLI_VERSION)
    if advertised > pinned:
        return "newer"
    if advertised < pinned:
        return "rollback"
    return "republished"


def _pinned_binary_sizes(target: dict[str, Any]) -> dict[str, int] | None:
    return PINNED_BINARY_SIZES if _pin_status(target) == "match" else None


def _validate_scratch(scratch: Path, runner_temp: Path) -> tuple[Path, Path]:
    runner = runner_temp.resolve(strict=True)
    candidate = scratch.absolute()
    if candidate.name != SCRATCH_PREFIX or candidate.parent.resolve(strict=True) != runner:
        raise CanaryError("scratch path is outside the exact runner temporary boundary")
    return candidate, runner


def _write_private(path: Path, raw: bytes, *, mode: int = 0o600) -> None:
    if path.exists() or path.is_symlink():
        raise CanaryError("refusing to overwrite canary-owned output")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(raw)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _replace_state(path: Path, value: dict[str, Any]) -> None:
    raw = (json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n").encode()
    if len(raw) > MAX_STATE_BYTES:
        raise CanaryError("canary state exceeds its byte limit")
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.unlink(missing_ok=True)
    _write_private(temporary, raw)
    os.replace(temporary, path)


def _load_state(scratch: Path) -> dict[str, Any]:
    path = scratch / STATE_NAME
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CanaryError("canary state is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_STATE_BYTES:
        raise CanaryError("canary state is not a bounded regular file")
    value = _strict_json(path.read_bytes(), label="canary state")
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "stable_cli", "runtime", "observations"}
        or value.get("schema_version") != 1
        or not isinstance(value.get("stable_cli"), dict)
        or not isinstance(value.get("runtime"), dict)
        or not isinstance(value.get("observations"), dict)
    ):
        raise CanaryError("canary state schema changed")
    return value


def _download_archive(target: dict[str, Any], destination: Path) -> None:
    url = _validate_url(target["download_url"])
    request = urllib.request.Request(url, headers={"User-Agent": "PKStack-Kiro-Canary/1"})
    digest = hashlib.sha256()
    written = 0
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with (
            os.fdopen(descriptor, "wb") as output,
            URL_OPENER.open(request, timeout=60) as response,
        ):
            if _validate_url(response.geturl()) != url:
                raise CanaryError("stable CLI archive redirected away from its advertised URL")
            advertised = response.headers.get("Content-Length")
            if advertised is not None and int(advertised) != target["size"]:
                raise CanaryError("stable CLI archive Content-Length changed")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > target["size"] or written > MAX_ARCHIVE_BYTES:
                    raise CanaryError("stable CLI archive exceeds its advertised size")
                digest.update(chunk)
                output.write(chunk)
    except CanaryError:
        destination.unlink(missing_ok=True)
        raise
    except (OSError, ValueError, urllib.error.URLError) as exc:
        destination.unlink(missing_ok=True)
        raise CanaryError("stable CLI archive download failed") from exc
    if written != target["size"] or digest.hexdigest() != target["sha256"]:
        destination.unlink(missing_ok=True)
        raise CanaryError("stable CLI archive does not match its advertised size and SHA-256")


def _copy_tar_member(source: BinaryIO, destination: Path, expected_size: int) -> None:
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o500)
    written = 0
    try:
        with os.fdopen(descriptor, "wb") as output:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > expected_size:
                    raise CanaryError("CLI archive member exceeds its advertised size")
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    if written != expected_size:
        destination.unlink(missing_ok=True)
        raise CanaryError("CLI archive member size changed during extraction")


def _extract_binaries(
    archive_path: Path,
    bin_dir: Path,
    *,
    expected_sizes: dict[str, int] | None = None,
) -> dict[str, Path]:
    wanted = {
        "kirocli/bin/kiro-cli": bin_dir / "kiro-cli",
        "kirocli/bin/kiro-cli-chat": bin_dir / "kiro-cli-chat",
    }
    if expected_sizes is not None and (
        set(expected_sizes) != set(wanted)
        or any(
            type(size) is not int or not 1 <= size <= MAX_BINARY_BYTES
            for size in expected_sizes.values()
        )
    ):
        raise CanaryError("pinned CLI executable-size contract is invalid")
    found: set[str] = set()
    count = 0
    try:
        with tarfile.open(archive_path, mode="r:xz") as archive:
            for member in archive:
                count += 1
                if count > MAX_TAR_MEMBERS:
                    raise CanaryError("CLI archive exceeds its member limit")
                if member.name not in wanted:
                    continue
                if member.name in found or not member.isfile():
                    raise CanaryError("CLI archive has an invalid or duplicate executable member")
                if not 1 <= member.size <= MAX_BINARY_BYTES:
                    raise CanaryError("CLI archive executable member size is invalid")
                if expected_sizes is not None and member.size != expected_sizes[member.name]:
                    raise CanaryError("pinned CLI archive executable member size changed")
                source = archive.extractfile(member)
                if source is None:
                    raise CanaryError("CLI archive executable member cannot be read")
                with source:
                    _copy_tar_member(source, wanted[member.name], member.size)
                found.add(member.name)
    except CanaryError:
        raise
    except (OSError, tarfile.TarError) as exc:
        raise CanaryError("stable CLI archive cannot be safely extracted") from exc
    if found != set(wanted):
        raise CanaryError("stable CLI archive is missing a required executable")
    return {name.rsplit("/", 1)[-1]: path for name, path in wanted.items()}


def _run_bounded(
    command: list[str], *, cwd: Path, environment: dict[str, str], timeout: int
) -> tuple[int, bytes, bytes]:
    # bash documents this limit in 1024-byte blocks on the Linux runner. Using
    # that divisor is conservative on shells that implement POSIX 512-byte blocks.
    file_limit_blocks = (MAX_COMMAND_BYTES + 1023) // 1024
    limited_command = [
        "/bin/bash",
        "--noprofile",
        "--norc",
        "-c",
        f'ulimit -f {file_limit_blocks}; umask 077; exec "$@"',
        "pkstack-kiro-canary",
        *command,
    ]
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        try:
            process = subprocess.Popen(
                limited_command,
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise CanaryError("Kiro CLI probe timed out") from exc
        stdout.seek(0)
        stderr.seek(0)
        out = stdout.read(MAX_COMMAND_BYTES + 1)
        err = stderr.read(MAX_COMMAND_BYTES + 1)
    if len(out) > MAX_COMMAND_BYTES or len(err) > MAX_COMMAND_BYTES:
        raise CanaryError("Kiro CLI probe output exceeds its byte limit")
    return return_code, out, err


def _isolated_environment(scratch: Path, *, api_key: str | None = None) -> dict[str, str]:
    environment = {
        "CI": "true",
        "HOME": str(scratch / "user-home"),
        "KIRO_HOME": str(scratch / "kiro-home"),
        "KIRO_LOG_NO_COLOR": "1",
        "LANG": "C.UTF-8",
        "NO_COLOR": "1",
        "PATH": f"{scratch / 'bin'}:/usr/local/bin:/usr/bin:/bin",
        "SSL_CERT_DIR": "/etc/ssl/certs",
        "XDG_RUNTIME_DIR": str(scratch / "runtime"),
    }
    if api_key is not None:
        environment["KIRO_API_KEY"] = api_key
    return environment


def _workspace_agents(output: bytes) -> tuple[str, ...]:
    try:
        text = ANSI_RE.sub("", output.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise CanaryError("Kiro agent discovery output is not UTF-8") from exc
    rows = [match.group(1) for line in text.splitlines() if (match := WORKSPACE_ROW_RE.match(line))]
    if len(rows) != len(set(rows)):
        raise CanaryError("Kiro agent discovery contains duplicate Workspace rows")
    return tuple(sorted(rows))


def _probe_runtime(root: Path, scratch: Path, version: str) -> dict[str, Any]:
    binary = scratch / "bin/kiro-cli"
    chat_binary = scratch / "bin/kiro-cli-chat"
    workspace = scratch / "workspace"
    environment = _isolated_environment(scratch)
    return_code, output, _ = _run_bounded(
        [str(binary), "--version"], cwd=workspace, environment=environment, timeout=30
    )
    if (
        return_code != 0
        or output.decode("utf-8", errors="replace").strip() != f"kiro-cli {version}"
    ):
        raise CanaryError("advertised Kiro CLI failed its exact version probe")

    agent_hashes: dict[str, str] = {}
    for name in EXPECTED_AGENTS:
        source_path = root / ".kiro/agents" / f"{name}.json"
        try:
            metadata = source_path.lstat()
        except OSError as exc:
            raise CanaryError("a shipped workspace agent is unavailable") from exc
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 128 * 1024:
            raise CanaryError("a shipped workspace agent is not a bounded regular file")
        raw = source_path.read_bytes()
        payload = _strict_json(raw, label="workspace agent")
        if not isinstance(payload, dict) or payload.get("name") != name:
            raise CanaryError("a shipped workspace agent name changed")
        path = workspace / ".kiro/agents" / f"{name}.json"
        _write_private(path, raw, mode=0o400)
        return_code, _, _ = _run_bounded(
            [str(chat_binary), "agent", "validate", "--path", str(path)],
            cwd=workspace,
            environment=environment,
            timeout=30,
        )
        if return_code != 0:
            raise CanaryError("advertised Kiro CLI rejected a shipped workspace agent")
        agent_hashes[name] = hashlib.sha256(raw).hexdigest()

    return_code, output, error_output = _run_bounded(
        [str(chat_binary), "agent", "list"],
        cwd=workspace,
        environment=environment,
        timeout=30,
    )
    if return_code != 0:
        raise CanaryError("advertised Kiro CLI failed workspace-agent discovery")
    observed = _workspace_agents(output + b"\n" + error_output)
    if observed != tuple(sorted(EXPECTED_AGENTS)):
        raise CanaryError("advertised Kiro CLI did not discover exactly the six shipped agents")
    return {
        "agent_schema_validated": list(EXPECTED_AGENTS),
        "agent_sha256": agent_hashes,
        "workspace_agent_discovery_validated": True,
        "workspace_agents": list(observed),
    }


def _safe_observation(
    label: str, url: str, parser: Any, *, maximum: int = MAX_OBSERVATION_BYTES
) -> dict[str, Any]:
    result: dict[str, Any] = {"label": label, "url": url}
    fetched_bytes = 0
    try:
        raw = _fetch_bytes(url, maximum=maximum)
        fetched_bytes = len(raw)
        parsed = parser(raw)
        result.update(
            {
                "status": "observed",
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                **parsed,
            }
        )
    # Product/docs observations are advisory by contract. Contain any ordinary
    # parser or transport failure and expose only its class, never remote text.
    except Exception as exc:  # noqa: BLE001
        result.update(
            {
                "status": "unavailable",
                "bytes": fetched_bytes,
                "error_class": type(exc).__name__,
            }
        )
    return result


def _parse_ide_metadata(raw: bytes) -> dict[str, str]:
    value = _strict_json(raw, label="Kiro IDE metadata")
    if not isinstance(value, dict) or set(value) != {"currentRelease", "releases"}:
        raise CanaryError("Kiro IDE metadata schema changed")
    version = value["currentRelease"]
    if not isinstance(version, str) or VERSION_RE.fullmatch(version) is None:
        raise CanaryError("Kiro IDE release version is invalid")
    releases = value["releases"]
    if not isinstance(releases, list) or len(releases) != 1:
        raise CanaryError("Kiro IDE metadata release list changed")
    return {"version": version}


def _parse_crew_cli(raw: bytes) -> dict[str, str]:
    value = _strict_json(raw, label="Kiro Crew CLI feed")
    if not isinstance(value, dict):
        raise CanaryError("Kiro Crew CLI feed schema changed")
    version = value.get("version")
    sha256 = value.get("sha256")
    if (
        value.get("schema") != "kirocrew-cli-artifact-manifest-v1"
        or value.get("channel") != "nightly"
        or not isinstance(version, str)
        or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+\.dev[0-9]{14}", version) is None
        or not isinstance(sha256, str)
        or SHA256_RE.fullmatch(sha256) is None
    ):
        raise CanaryError("Kiro Crew CLI feed contract changed")
    return {"version": version, "artifact_sha256": sha256}


def _parse_crew_desktop(raw: bytes) -> dict[str, str]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CanaryError("Kiro Crew desktop feed is not UTF-8") from exc
    versions = re.findall(
        r"(?m)^version: ([0-9]+\.[0-9]+\.[0-9]+-nightly\.[0-9]{8}t[0-9]{6})$", text
    )
    if len(versions) != 1 or len(re.findall(r"(?m)^\s+sha512: '[A-Za-z0-9+/=]+'$", text)) != 2:
        raise CanaryError("Kiro Crew desktop feed contract changed")
    return {"version": versions[0]}


def _parse_changelog(raw: bytes) -> dict[str, str]:
    if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", raw, flags=re.IGNORECASE):
        raise CanaryError("Kiro changelog feed contains a forbidden XML declaration")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise CanaryError("Kiro changelog feed is not XML") from exc
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    updated = root.findtext("atom:updated", namespaces=namespace)
    entry = root.find("atom:entry", namespace)
    title = entry.findtext("atom:title", namespaces=namespace) if entry is not None else None
    if not updated or not title or len(updated) > 64 or len(title.encode("utf-8")) > 512:
        raise CanaryError("Kiro changelog feed contract changed")
    return {"updated": updated, "latest_title": title}


def _recorded_doc_hashes(root: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    for relative in DOC_EVIDENCE_PATHS:
        value = _strict_json((root / relative).read_bytes(), label="recorded Kiro documentation")
        documentation = value.get("documentation") if isinstance(value, dict) else None
        if not isinstance(documentation, dict):
            raise CanaryError("recorded Kiro documentation schema changed")
        candidates: list[Any] = []
        index = documentation.get("index")
        if isinstance(index, dict):
            candidates.append(index)
        pages = documentation.get("pages")
        if isinstance(pages, list):
            candidates.extend(pages)
        for item in candidates:
            if not isinstance(item, dict) or "sha256" not in item:
                continue
            url = item.get("url")
            sha256 = item.get("sha256")
            if (
                not isinstance(url, str)
                or not isinstance(sha256, str)
                or SHA256_RE.fullmatch(sha256) is None
                or urllib.parse.urlsplit(url).hostname != "kiro.dev"
            ):
                raise CanaryError("recorded Kiro documentation identity is invalid")
            _validate_url(url)
            prior = records.setdefault(url, sha256)
            if prior != sha256:
                raise CanaryError("recorded Kiro documentation hashes conflict")
    if not 1 <= len(records) <= MAX_DOC_RECORDS:
        raise CanaryError("recorded Kiro documentation set is outside its item limit")
    return records


def _collect_observations(root: Path) -> dict[str, Any]:
    remaining = MAX_AGGREGATE_OBSERVATION_BYTES

    def observe(label: str, url: str, parser: Any) -> dict[str, Any]:
        nonlocal remaining
        if remaining <= 0:
            return {"label": label, "url": url, "status": "aggregate-limit-reached"}
        result = _safe_observation(
            label,
            url,
            parser,
            maximum=min(MAX_OBSERVATION_BYTES, remaining),
        )
        charged = int(result.get("bytes", 0))
        if result.get("status") != "observed" and charged == 0:
            charged = min(MAX_OBSERVATION_BYTES, remaining)
        remaining -= charged
        return result

    product_feeds = [
        observe("kiro-ide-stable", IDE_METADATA_URL, _parse_ide_metadata),
        observe("kiro-crew-cli-nightly", CREW_CLI_FEED_URL, _parse_crew_cli),
        observe("kiro-crew-desktop-nightly", CREW_DESKTOP_FEED_URL, _parse_crew_desktop),
        observe("kiro-changelog", CHANGELOG_FEED_URL, _parse_changelog),
    ]
    documentation: list[dict[str, Any]] = []
    try:
        recorded = _recorded_doc_hashes(root)
    except (CanaryError, OSError) as exc:
        documentation.append(
            {"status": "unavailable", "error_class": type(exc).__name__, "label": "recorded-set"}
        )
    else:
        for url, expected in sorted(recorded.items()):
            observation = observe(
                "llms-index" if url.endswith("/llms.txt") else "recorded-doc",
                url,
                lambda raw, expected=expected: {
                    "recorded_sha256": expected,
                    "digest_status": (
                        "match" if hashlib.sha256(raw).hexdigest() == expected else "drift"
                    ),
                    "lines": len(raw.splitlines()),
                },
            )
            documentation.append(observation)
    return {"product_feeds": product_feeds, "documentation": documentation}


def _prepare(root: Path, scratch: Path, runner_temp: Path) -> dict[str, Any]:
    scratch, _ = _validate_scratch(scratch, runner_temp)
    if scratch.exists() or scratch.is_symlink():
        raise CanaryError("canary scratch path already exists")
    root = root.resolve(strict=True)
    scratch.mkdir(mode=0o700)
    try:
        for name in ("bin", "kiro-home", "user-home", "runtime", "workspace"):
            (scratch / name).mkdir(mode=0o700)
        (scratch / "kiro-home/settings").mkdir(mode=0o700)
        (scratch / "workspace/.kiro").mkdir(mode=0o700)
        (scratch / "workspace/.kiro/agents").mkdir(mode=0o700)
        _write_private(scratch / "kiro-home/settings/cli.json", SETTINGS)

        manifest = _fetch_bytes(CLI_MANIFEST_URL, maximum=MAX_MANIFEST_BYTES)
        target = _parse_manifest(manifest)
        target["pin_status"] = _pin_status(target)
        target["manifest_sha256"] = hashlib.sha256(manifest).hexdigest()
        archive_path = scratch / CLI_ARCHIVE_NAME
        _download_archive(target, archive_path)
        _extract_binaries(
            archive_path,
            scratch / "bin",
            expected_sizes=_pinned_binary_sizes(target),
        )
        archive_path.unlink()
        runtime = _probe_runtime(root, scratch, target["version"])
        state = {
            "schema_version": 1,
            "stable_cli": target,
            "runtime": {
                **runtime,
                "model_inventory_validated": False,
            },
            "observations": _collect_observations(root),
        }
        _replace_state(scratch / STATE_NAME, state)
        return state
    except Exception:
        shutil.rmtree(scratch, ignore_errors=True)
        raise


def _inventory(root: Path, scratch: Path, runner_temp: Path) -> dict[str, Any]:
    scratch, _ = _validate_scratch(scratch, runner_temp)
    state = _load_state(scratch)
    if state.get("stable_cli", {}).get("pin_status") != "match":
        raise CanaryError("refusing authenticated inventory for an unreviewed Kiro CLI pin")
    api_key = os.environ.pop("KIRO_API_KEY", "")
    if not api_key:
        raise CanaryError("KIRO_API_KEY is not configured for the inventory-only step")
    binary = scratch / "bin/kiro-cli"
    root.resolve(strict=True)
    environment = _isolated_environment(scratch, api_key=api_key)
    try:
        return_code, output, error_output = _run_bounded(
            [str(binary), "chat", "--list-models", "--format", "json"],
            cwd=scratch / "workspace",
            environment=environment,
            timeout=60,
        )
    finally:
        environment.pop("KIRO_API_KEY", None)
    encoded_key = api_key.encode("utf-8")
    leaked = encoded_key in output or encoded_key in error_output
    api_key = ""
    if leaked:
        raise CanaryError("Kiro model inventory output contained credential material")
    if return_code != 0:
        raise CanaryError("live Kiro model inventory command failed")
    try:
        validate_inventory_bytes(output)
    except InventoryError as exc:
        raise CanaryError("live Kiro model inventory contract changed") from exc
    state["runtime"]["model_inventory_validated"] = True
    state["runtime"]["model_inventory_sha256"] = hashlib.sha256(output).hexdigest()
    _replace_state(scratch / STATE_NAME, state)
    return state


def _finalize(scratch: Path, runner_temp: Path) -> dict[str, Any]:
    scratch, _ = _validate_scratch(scratch, runner_temp)
    state = _load_state(scratch)
    pin_status = state.get("stable_cli", {}).get("pin_status")
    inventory_validated = state.get("runtime", {}).get("model_inventory_validated") is True
    discovery_validated = (
        state.get("runtime", {}).get("workspace_agent_discovery_validated") is True
    )
    gate = (
        "pass" if pin_status == "match" and inventory_validated and discovery_validated else "fail"
    )
    report = {**state, "gate": gate}
    print(json.dumps(report, separators=(",", ":"), sort_keys=True))
    if pin_status != "match":
        raise CanaryError("official stable Kiro CLI no longer matches the reviewed runtime pin")
    if not inventory_validated:
        raise CanaryError("live Kiro model inventory was not validated")
    if not discovery_validated:
        raise CanaryError("live Kiro workspace-agent discovery was not validated")
    return report


def _cleanup(scratch: Path, runner_temp: Path) -> None:
    scratch, _ = _validate_scratch(scratch, runner_temp)
    if scratch.is_symlink():
        raise CanaryError("refusing to clean a symlinked canary scratch path")
    if scratch.exists():
        if not scratch.is_dir():
            raise CanaryError("canary scratch path is not a directory")
        shutil.rmtree(scratch)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "inventory"):
        child = subparsers.add_parser(command)
        child.add_argument("--root", type=Path, required=True)
        child.add_argument("--scratch", type=Path, required=True)
        child.add_argument("--runner-temp", type=Path, required=True)
    for command in ("pin-match", "finalize", "cleanup"):
        child = subparsers.add_parser(command)
        child.add_argument("--scratch", type=Path, required=True)
        child.add_argument("--runner-temp", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "prepare":
            state = _prepare(args.root, args.scratch, args.runner_temp)
            print(
                json.dumps(
                    {
                        "phase": "prepared",
                        "stable_cli": state["stable_cli"],
                        "runtime": state["runtime"],
                        "observations": state["observations"],
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
        elif args.command == "inventory":
            state = _inventory(args.root, args.scratch, args.runner_temp)
            print(
                json.dumps(
                    {
                        "phase": "inventory-validated",
                        "model_inventory_sha256": state["runtime"]["model_inventory_sha256"],
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
        elif args.command == "pin-match":
            scratch, _ = _validate_scratch(args.scratch, args.runner_temp)
            state = _load_state(scratch)
            print("true" if state.get("stable_cli", {}).get("pin_status") == "match" else "false")
        elif args.command == "finalize":
            _finalize(args.scratch, args.runner_temp)
        else:
            _cleanup(args.scratch, args.runner_temp)
    except CanaryError as exc:
        print(f"Kiro runtime canary failed: {exc}", file=sys.stderr)
        return 1
    except OSError:
        print("Kiro runtime canary failed: local filesystem operation failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
