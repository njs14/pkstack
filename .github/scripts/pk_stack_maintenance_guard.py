#!/usr/bin/env python3
"""Trusted boundary checks for PK-Stack's autonomous maintenance workflows.

This file is always executed from the source workflow's immutable base commit.
It never imports repository packages and treats candidate files and detector JSON
as untrusted data.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any

POLICY_KEYS = {
    "schema_version",
    "source_workflows",
    "ci_authority",
    "pull_request",
    "candidate_lifecycle",
    "candidate_review",
    "limits",
    "agent_allowed_exact",
    "agent_allowed_prefixes",
    "final_allowed_exact",
    "final_allowed_prefixes",
    "protected_basenames",
    "protected_exact",
    "protected_path_components",
    "protected_prefixes",
}
GENERATED_PREFIXES = (".kiro/", ".pstack/bin/", ".pstack/projectctl/")
GENERATED_EXACT = {
    ".pstack/bootstrap.json",
    ".pstack/discovery.json",
    "Wiki/features/README.md",
    "maintenance/upstream-reviews.json",
    "maintenance/upstreams.json",
    "projectctl",
}
EXECUTABLE_PATHS = {".pstack/bin/projectctl", "projectctl"}
ALLOWED_PRODUCT_TOOLS = {"read", "write", "shell", "subagent", "knowledge"}
ALLOWED_HOOKS = {"pstack-session.json", "pstack-tripwire.json"}
TRUSTED_SNAPSHOT_PREFIXES = (
    "Wiki/features/pk-stack-upstream-maintenance.md",
    ".github/fixtures",
    ".github/pk-stack-maintenance-policy.json",
    ".github/scripts",
    ".github/workflows",
    ".kiro/agents",
    ".pstack/projectctl",
    "reviews",
)
CANDIDATE_PACKAGE_MAX_BYTES = 33_554_432
REVIEW_LEDGER_MAX_BYTES = 8 * 1024 * 1024
REVIEW_TRANSITION_MAX = 512
UPSTREAM_SCHEMA_VERSION = 2
GIT_CONTROL_STATE_SCHEMA = 2
GIT_CONTROL_STATE_MAX_BYTES = 256 * 1024
GIT_CONTROL_ENTRY_MAX_BYTES = 1024 * 1024
GIT_CONTROL_TOTAL_MAX_BYTES = 4 * 1024 * 1024
GIT_CONTROL_MAX_ENTRIES = 512
GIT_CONTROL_MAX_DEPTH = 8
GIT_CONTROL_TARGETS = (
    "config",
    "config.worktree",
    "hooks",
    "info",
    "index",
    "HEAD",
    "refs",
    "packed-refs",
)
GIT_FINALIZER_INDEX_MAX_BYTES = 16 * 1024 * 1024
GIT_FINALIZER_OBJECT_MAX_BYTES = 64 * 1024 * 1024
GIT_FINALIZER_OBJECT_MAX_ENTRIES = 8192
GIT_FINALIZER_MARKER = b"pk-stack-trusted-git-finalizer-v1\n"
GIT_FINALIZER_CONFIG = (
    b"[core]\n"
    b"\trepositoryformatversion = 0\n"
    b"\tbare = false\n"
    b"[gc]\n"
    b"\tauto = 0\n"
    b"[maintenance]\n"
    b"\tauto = false\n"
)
FABLE_INTERNAL_COMPANION_MODEL = "claude-haiku-4-5-20251001"
_TRUSTED_GIT_CONFIG = (
    ("core.hooksPath", "/dev/null"),
    ("core.fsmonitor", "false"),
    ("diff.external", ""),
    ("core.attributesFile", "/dev/null"),
)
PATCH_COUNT_CONSTRAINT = "unified-patch-body-matches-reported-additions-and-deletions"
BLOB_BINDING_CONSTRAINT = "old-blob-plus-patch-result-matches-exact-git-blob-identities"
TREE_ENTRY_CONSTRAINT = "regular-blob-modes-100644-or-100755-only"
NO_PATCH_CONSTRAINT = "zero-count-top-level-raster-asset-or-exact-blob-rename-or-mode-change-only"
_NONSEMANTIC_IMAGE_PATH = re.compile(r"^assets/[a-z0-9][a-z0-9_-]{0,127}\.(?:png|jpe?g|gif|webp)$")
_SOURCE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_UNIFIED_HUNK = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@(?: .*)?$"
)


class GuardError(RuntimeError):
    """A candidate or workflow input crossed an immutable boundary."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise GuardError(f"JSON contains duplicate key: {key!r}")
        value[key] = item
    return value


def _reject_json_constant(value: str) -> None:
    raise GuardError(f"JSON contains a non-finite number: {value}")


def _run(
    *args: str,
    cwd: Path,
    env: dict[str, str] | None = None,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise GuardError(f"command failed ({' '.join(args)}): {stderr}")
    return completed


def _trusted_git_env(env: dict[str, str] | None = None) -> dict[str, str]:
    """Return a deterministic Git environment that cannot inherit executable config."""

    sanitized = (os.environ if env is None else env).copy()
    for key in tuple(sanitized):
        if key == "GIT_CONFIG_PARAMETERS" or key.startswith(
            ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
        ):
            sanitized.pop(key)
    sanitized.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_EXTERNAL_DIFF": "",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_COUNT": str(len(_TRUSTED_GIT_CONFIG)),
        }
    )
    for index, (key, value) in enumerate(_TRUSTED_GIT_CONFIG):
        sanitized[f"GIT_CONFIG_KEY_{index}"] = key
        sanitized[f"GIT_CONFIG_VALUE_{index}"] = value
    return sanitized


def _git_run(
    root: Path,
    *args: str,
    env: dict[str, str] | None = None,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    """Run Git with hooks, fsmonitor, and external diff execution disabled."""

    normalized = args
    if normalized and normalized[0] == "diff":
        forced_options = tuple(
            option for option in ("--no-ext-diff", "--no-textconv") if option not in normalized
        )
        normalized = (normalized[0], *forced_options, *normalized[1:])
    config_args = tuple(
        argument for key, value in _TRUSTED_GIT_CONFIG for argument in ("-c", f"{key}={value}")
    )
    return _run(
        "git",
        *config_args,
        *normalized,
        cwd=root,
        env=_trusted_git_env(env),
        input_bytes=input_bytes,
        check=check,
    )


def _git_bytes(root: Path, *args: str, env: dict[str, str] | None = None) -> bytes:
    return _git_run(root, *args, env=env).stdout


def _git_text(root: Path, *args: str, env: dict[str, str] | None = None) -> str:
    return _git_bytes(root, *args, env=env).decode("utf-8", errors="strict")


def _control_metadata(value: os.stat_result) -> dict[str, int]:
    return {
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": stat.S_IMODE(value.st_mode),
        "uid": value.st_uid,
        "gid": value.st_gid,
        "links": value.st_nlink,
        "size": value.st_size,
        "mtime_ns": value.st_mtime_ns,
        "ctime_ns": value.st_ctime_ns,
    }


def _control_directory_identity(value: os.stat_result) -> dict[str, int]:
    """Bind the .git directory without rejecting harmless index-lock churn."""

    return {
        key: item
        for key, item in _control_metadata(value).items()
        if key not in {"size", "mtime_ns", "ctime_ns", "links"}
    }


def _same_control_object(left: os.stat_result, right: os.stat_result) -> bool:
    return _control_metadata(left) == _control_metadata(right)


def _validate_control_metadata(value: os.stat_result, *, label: str) -> None:
    if value.st_uid != os.getuid():
        raise GuardError(f"Git control entry is not owned by the runner: {label}")
    if stat.S_IMODE(value.st_mode) & 0o022:
        raise GuardError(f"Git control entry is group/other writable: {label}")


def _snapshot_control_entry(
    parent_descriptor: int,
    name: str,
    *,
    label: str,
    depth: int,
    budget: dict[str, int],
    allow_absent: bool,
) -> dict[str, Any]:
    if depth > GIT_CONTROL_MAX_DEPTH:
        raise GuardError(f"Git control tree exceeds its depth limit: {label}")
    try:
        before = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        if allow_absent:
            return {"kind": "absent"}
        raise GuardError(f"Git control entry disappeared while hashing: {label}") from None
    budget["entries"] += 1
    if budget["entries"] > GIT_CONTROL_MAX_ENTRIES:
        raise GuardError("Git control tree exceeds its entry-count limit")
    if stat.S_ISLNK(before.st_mode):
        raise GuardError(f"Git control entry may not be a symlink: {label}")
    _validate_control_metadata(before, label=label)
    common = {"metadata": _control_metadata(before)}
    if stat.S_ISREG(before.st_mode):
        if before.st_nlink != 1:
            raise GuardError(f"Git control file may not be hard-linked: {label}")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or not _same_control_object(before, opened):
                raise GuardError(f"Git control file changed before hashing: {label}")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(descriptor, 65_536)
                if not chunk:
                    break
                total += len(chunk)
                if total > GIT_CONTROL_ENTRY_MAX_BYTES:
                    raise GuardError(f"Git control file exceeds its byte limit: {label}")
                chunks.append(chunk)
            after = os.fstat(descriptor)
            if not _same_control_object(opened, after) or total != opened.st_size:
                raise GuardError(f"Git control file changed while hashing: {label}")
        finally:
            os.close(descriptor)
        budget["bytes"] += total
        if budget["bytes"] > GIT_CONTROL_TOTAL_MAX_BYTES:
            raise GuardError("Git control tree exceeds its total byte limit")
        return {
            "kind": "file",
            **common,
            "sha256": hashlib.sha256(b"".join(chunks)).hexdigest(),
        }
    if stat.S_ISDIR(before.st_mode):
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_DIRECTORY", 0)
        )
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISDIR(opened.st_mode) or not _same_control_object(before, opened):
                raise GuardError(f"Git control directory changed before hashing: {label}")
            names = sorted(os.listdir(descriptor))
            entries: list[dict[str, Any]] = []
            for child in names:
                if (
                    not child
                    or child in {".", ".."}
                    or "/" in child
                    or "\0" in child
                    or any(ord(character) < 32 for character in child)
                ):
                    raise GuardError(f"Git control directory contains an unsafe name: {label}")
                entries.append(
                    {
                        "name": child,
                        "entry": _snapshot_control_entry(
                            descriptor,
                            child,
                            label=f"{label}/{child}",
                            depth=depth + 1,
                            budget=budget,
                            allow_absent=False,
                        ),
                    }
                )
            after = os.fstat(descriptor)
            if not _same_control_object(opened, after):
                raise GuardError(f"Git control directory changed while hashing: {label}")
        finally:
            os.close(descriptor)
        return {"kind": "directory", **common, "entries": entries}
    raise GuardError(f"Git control entry is not a regular file or directory: {label}")


def _snapshot_git_controls(root: Path) -> dict[str, Any]:
    git_path = root / ".git"
    try:
        before = os.lstat(git_path)
    except FileNotFoundError:
        raise GuardError("maintenance checkout has no .git directory") from None
    if not stat.S_ISDIR(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise GuardError("maintenance checkout .git must be a real directory")
    _validate_control_metadata(before, label=".git")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_DIRECTORY", 0)
    )
    descriptor = os.open(git_path, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISDIR(opened.st_mode) or not _same_control_object(before, opened):
            raise GuardError("maintenance checkout .git changed before hashing")
        budget = {"entries": 0, "bytes": 0}
        targets = {
            name: _snapshot_control_entry(
                descriptor,
                name,
                label=f".git/{name}",
                depth=0,
                budget=budget,
                allow_absent=True,
            )
            for name in GIT_CONTROL_TARGETS
        }
        after = os.fstat(descriptor)
        if not _same_control_object(opened, after):
            raise GuardError("maintenance checkout .git changed while hashing")
    finally:
        os.close(descriptor)
    return {
        "git_dir": _control_directory_identity(opened),
        "targets": targets,
        "entry_count": budget["entries"],
        "total_bytes": budget["bytes"],
    }


def _resolve_git_state_root(root: Path, state_root: Path) -> Path:
    if not state_root.is_absolute() or state_root.name in {"", ".", ".."}:
        raise GuardError("Git control state path must be an absolute dedicated directory")
    try:
        parent = state_root.parent.resolve(strict=True)
    except (FileNotFoundError, RuntimeError) as exc:
        raise GuardError("Git control state parent must be an existing directory") from exc
    candidate = parent / state_root.name
    canonical_root = root.resolve()
    if candidate == canonical_root or candidate.is_relative_to(canonical_root):
        raise GuardError("Git control state must be outside the model-visible checkout")
    return candidate


def _read_owned_file(path: Path, *, mode: int, maximum: int, label: str) -> bytes:
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise GuardError(f"{label} is missing or unsafe") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.getuid()
            or before.st_nlink != 1
            or stat.S_IMODE(before.st_mode) != mode
            or before.st_size > maximum
        ):
            raise GuardError(f"{label} is missing or unsafe")
        raw = b""
        while len(raw) <= maximum:
            chunk = os.read(descriptor, 65_536)
            if not chunk:
                break
            raw += chunk
        after = os.fstat(descriptor)
        if len(raw) > maximum or not _same_control_object(before, after):
            raise GuardError(f"{label} changed while reading")
        return raw
    finally:
        os.close(descriptor)


def _validate_owned_directory(path: Path, *, mode: int, label: str) -> None:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        raise GuardError(f"{label} is missing or unsafe") from None
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != mode
    ):
        raise GuardError(f"{label} is missing or unsafe")


def _chmod_owned_nofollow(path: Path, mode: int, *, label: str) -> None:
    metadata = os.lstat(path)
    if metadata.st_uid != os.getuid() or stat.S_ISLNK(metadata.st_mode):
        raise GuardError(f"{label} is missing or unsafe")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    if stat.S_ISDIR(metadata.st_mode):
        flags |= getattr(os, "O_DIRECTORY", 0)
    elif not stat.S_ISREG(metadata.st_mode):
        raise GuardError(f"{label} is missing or unsafe")
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if not _same_control_object(metadata, opened):
            raise GuardError(f"{label} changed before chmod")
        os.fchmod(descriptor, mode)
    finally:
        os.close(descriptor)


def _validate_finalizer_objects(path: Path, *, sealed: bool) -> None:
    _validate_owned_directory(
        path,
        mode=0o500 if sealed else 0o700,
        label="trusted Git object directory",
    )
    entry_count = 0
    total_bytes = 0
    for directory, names, files in os.walk(path, topdown=True, followlinks=False):
        directory_path = Path(directory)
        relative_depth = len(directory_path.relative_to(path).parts)
        if relative_depth > 3:
            raise GuardError("trusted Git object directory exceeds its depth limit")
        for name in [*names, *files]:
            candidate = directory_path / name
            metadata = os.lstat(candidate)
            entry_count += 1
            if entry_count > GIT_FINALIZER_OBJECT_MAX_ENTRIES:
                raise GuardError("trusted Git object directory exceeds its entry limit")
            if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o022:
                raise GuardError("trusted Git object entry has unsafe ownership or mode")
            if stat.S_ISLNK(metadata.st_mode):
                raise GuardError("trusted Git object entry may not be a symlink")
            if stat.S_ISREG(metadata.st_mode):
                if metadata.st_nlink != 1:
                    raise GuardError("trusted Git object file may not be hard-linked")
                total_bytes += metadata.st_size
                if total_bytes > GIT_FINALIZER_OBJECT_MAX_BYTES:
                    raise GuardError("trusted Git objects exceed their byte limit")
            elif not stat.S_ISDIR(metadata.st_mode):
                raise GuardError("trusted Git object entry has an unsafe type")
    if sealed and entry_count:
        raise GuardError("sealed trusted Git object directory must be empty")


def _validate_external_git_tree(
    root: Path,
    base_sha: str,
    state_root: Path,
    *,
    phase: str,
    trusted_index_sha256: str,
) -> None:
    sealed = phase == "sealed"
    expected_root_entries = {"git", "index", "objects", "state.json"}
    if not sealed:
        expected_root_entries.add("finalizer-open")
    if set(os.listdir(state_root)) != expected_root_entries:
        raise GuardError("Git control state directory contains unexpected entries")
    git_dir = state_root / "git"
    _validate_owned_directory(git_dir, mode=0o500, label="trusted Git metadata directory")
    if set(os.listdir(git_dir)) != {"HEAD", "config", "refs"}:
        raise GuardError("trusted Git metadata directory contains unexpected entries")
    refs = git_dir / "refs"
    _validate_owned_directory(refs, mode=0o500, label="trusted Git refs directory")
    if os.listdir(refs):
        raise GuardError("trusted Git refs directory must be empty")
    if _read_owned_file(
        git_dir / "HEAD",
        mode=0o400,
        maximum=128,
        label="trusted Git HEAD",
    ) != f"{base_sha}\n".encode("ascii"):
        raise GuardError("trusted Git HEAD changed")
    if (
        _read_owned_file(
            git_dir / "config",
            mode=0o400,
            maximum=4096,
            label="trusted Git config",
        )
        != GIT_FINALIZER_CONFIG
    ):
        raise GuardError("trusted Git config changed")
    index = _read_owned_file(
        state_root / "index",
        mode=0o400 if sealed else 0o600,
        maximum=GIT_FINALIZER_INDEX_MAX_BYTES,
        label="trusted Git index",
    )
    if sealed and hashlib.sha256(index).hexdigest() != trusted_index_sha256:
        raise GuardError("sealed trusted Git index changed")
    _validate_finalizer_objects(state_root / "objects", sealed=sealed)
    if (
        not sealed
        and _read_owned_file(
            state_root / "finalizer-open",
            mode=0o400,
            maximum=128,
            label="trusted Git finalizer marker",
        )
        != GIT_FINALIZER_MARKER
    ):
        raise GuardError("trusted Git finalizer marker changed")


def _read_git_state(
    root: Path,
    base_sha: str,
    state_root: Path,
    *,
    phase: str = "sealed",
) -> dict[str, Any]:
    if phase not in {"sealed", "open"}:
        raise GuardError("invalid trusted Git state phase")
    state_root = _resolve_git_state_root(root, state_root)
    _validate_owned_directory(
        state_root,
        mode=0o500 if phase == "sealed" else 0o700,
        label="Git control state directory",
    )
    raw = _read_owned_file(
        state_root / "state.json",
        mode=0o400,
        maximum=GIT_CONTROL_STATE_MAX_BYTES,
        label="Git control state file",
    )
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GuardError(f"Git control state is not strict UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "root",
        "base_sha",
        "snapshot",
        "trusted_index_sha256",
    }:
        raise GuardError("Git control state has an invalid envelope")
    trusted_index_sha256 = value["trusted_index_sha256"]
    if (
        value["schema_version"] != GIT_CONTROL_STATE_SCHEMA
        or value["root"] != root.as_posix()
        or value["base_sha"] != base_sha
        or not isinstance(value["snapshot"], dict)
        or not isinstance(trusted_index_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", trusted_index_sha256) is None
    ):
        raise GuardError("Git control state does not match this attempt")
    _validate_external_git_tree(
        root,
        base_sha,
        state_root,
        phase=phase,
        trusted_index_sha256=trusted_index_sha256,
    )
    return value


def _external_git_environment(root: Path, state_root: Path) -> dict[str, str]:
    state_root = _resolve_git_state_root(root, state_root)
    git_dir = state_root / "git"
    return {
        "GIT_DIR": git_dir.as_posix(),
        "GIT_COMMON_DIR": git_dir.as_posix(),
        "GIT_WORK_TREE": root.as_posix(),
        "GIT_INDEX_FILE": (state_root / "index").as_posix(),
        "GIT_OBJECT_DIRECTORY": (state_root / "objects").as_posix(),
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": (root / ".git/objects").as_posix(),
        "GIT_NO_REPLACE_OBJECTS": "1",
    }


@contextmanager
def _temporary_environment(updates: dict[str, str]) -> Any:
    previous = {key: os.environ.get(key) for key in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextmanager
def _temporary_umask(mode: int) -> Any:
    previous = os.umask(mode)
    try:
        yield
    finally:
        os.umask(previous)


def _write_exclusive(path: Path, raw: bytes, *, mode: int) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
        mode,
    )
    try:
        view = memoryview(raw)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise GuardError(f"failed to write trusted Git state: {path.name}")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _remove_git_state(root: Path, state_root: Path, *, phase: str = "sealed") -> None:
    state_root = _resolve_git_state_root(root, state_root)
    _read_git_state(root, _read_git_state_base(root, state_root), state_root, phase=phase)
    for directory, _, _ in os.walk(state_root, topdown=False, followlinks=False):
        _chmod_owned_nofollow(Path(directory), 0o700, label="trusted Git state directory")
    shutil.rmtree(state_root)


def _read_git_state_base(root: Path, state_root: Path) -> str:
    """Read only the bound base identity for internal state cleanup."""

    state_root = _resolve_git_state_root(root, state_root)
    raw = _read_owned_file(
        state_root / "state.json",
        mode=0o400,
        maximum=GIT_CONTROL_STATE_MAX_BYTES,
        label="Git control state file",
    )
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GuardError(f"Git control state is not strict UTF-8 JSON: {exc}") from exc
    base_sha = value.get("base_sha") if isinstance(value, dict) else None
    if not isinstance(base_sha, str) or re.fullmatch(r"[0-9a-f]{40}", base_sha) is None:
        raise GuardError("Git control state has an invalid base identity")
    return base_sha


def _record_git_state(root: Path, base_sha: str, state_root: Path) -> None:
    if re.fullmatch(r"[0-9a-f]{40}", base_sha) is None:
        raise GuardError("Git control state base must be a full SHA-1")
    state_root = _resolve_git_state_root(root, state_root)
    if state_root.exists() or state_root.is_symlink():
        prior = _read_git_state(root, base_sha, state_root)
        if prior["snapshot"] != _snapshot_git_controls(root):
            raise GuardError("Git control state changed after the prior maintenance attempt")
        _remove_git_state(root, state_root)
    snapshot = _snapshot_git_controls(root)
    state_root.mkdir(mode=0o700)
    try:
        git_dir = state_root / "git"
        refs = git_dir / "refs"
        objects = state_root / "objects"
        git_dir.mkdir(mode=0o700)
        refs.mkdir(mode=0o700)
        objects.mkdir(mode=0o700)
        _write_exclusive(git_dir / "HEAD", f"{base_sha}\n".encode("ascii"), mode=0o600)
        _write_exclusive(git_dir / "config", GIT_FINALIZER_CONFIG, mode=0o600)
        external_environment = {**os.environ, **_external_git_environment(root, state_root)}
        _git_run(root, "read-tree", "--reset", base_sha, env=external_environment)
        index_path = state_root / "index"
        _chmod_owned_nofollow(index_path, 0o600, label="trusted Git index")
        index = _read_owned_file(
            index_path,
            mode=0o600,
            maximum=GIT_FINALIZER_INDEX_MAX_BYTES,
            label="trusted Git index",
        )
        document = {
            "schema_version": GIT_CONTROL_STATE_SCHEMA,
            "root": root.as_posix(),
            "base_sha": base_sha,
            "snapshot": snapshot,
            "trusted_index_sha256": hashlib.sha256(index).hexdigest(),
        }
        raw = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if len(raw) > GIT_CONTROL_STATE_MAX_BYTES:
            raise GuardError("Git control state exceeds its byte limit")
        _write_exclusive(state_root / "state.json", raw, mode=0o400)
        for path in (git_dir / "HEAD", git_dir / "config", index_path):
            _chmod_owned_nofollow(path, 0o400, label="trusted Git state file")
        for path in (refs, git_dir, objects, state_root):
            _chmod_owned_nofollow(path, 0o500, label="trusted Git state directory")
        _read_git_state(root, base_sha, state_root)
    except Exception:
        if state_root.exists() and not state_root.is_symlink():
            for directory, _, _ in os.walk(state_root, topdown=False, followlinks=False):
                _chmod_owned_nofollow(
                    Path(directory), 0o700, label="new trusted Git state directory"
                )
            shutil.rmtree(state_root)
        raise


def _assert_git_state_unchanged(root: Path, base_sha: str, state_root: Path) -> None:
    recorded = _read_git_state(root, base_sha, state_root)
    if recorded["snapshot"] != _snapshot_git_controls(root):
        raise GuardError("Git control metadata changed during the model attempt")


def _open_git_finalizer(root: Path, base_sha: str, state_root: Path) -> dict[str, str]:
    # This is intentionally filesystem-only. The external metadata is opened
    # only after the complete model-visible Git control plane has been rebound.
    _assert_git_state_unchanged(root, base_sha, state_root)
    state_root = _resolve_git_state_root(root, state_root)
    _chmod_owned_nofollow(state_root, 0o700, label="Git control state directory")
    _chmod_owned_nofollow(state_root / "index", 0o600, label="trusted Git index")
    _chmod_owned_nofollow(state_root / "objects", 0o700, label="trusted Git object directory")
    try:
        _write_exclusive(state_root / "finalizer-open", GIT_FINALIZER_MARKER, mode=0o400)
        _read_git_state(root, base_sha, state_root, phase="open")
    except Exception:
        marker = state_root / "finalizer-open"
        if marker.exists() and not marker.is_symlink():
            _chmod_owned_nofollow(marker, 0o600, label="trusted Git finalizer marker")
            marker.unlink()
        _chmod_owned_nofollow(state_root / "index", 0o400, label="trusted Git index")
        _chmod_owned_nofollow(state_root / "objects", 0o500, label="trusted Git object directory")
        _chmod_owned_nofollow(state_root, 0o500, label="Git control state directory")
        raise
    return _external_git_environment(root, state_root)


def finalize_git_state(root: Path, base_sha: str, state_root: Path) -> None:
    # No Git command is permitted here. Deleting the dedicated external state
    # restores the checkout to its untouched repository metadata and index.
    _read_git_state(root, base_sha, state_root, phase="open")
    _remove_git_state(root, state_root, phase="open")


def _load_json(path: Path, *, maximum: int, label: str) -> tuple[bytes, dict[str, Any]]:
    if path.is_symlink() or not path.is_file():
        raise GuardError(f"{label} must be a regular file: {path}")
    raw = path.read_bytes()
    if len(raw) > maximum:
        raise GuardError(f"{label} exceeds {maximum} bytes")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GuardError(f"{label} is not strict UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise GuardError(f"{label} must be a JSON object")
    return raw, value


def _load_json_array(path: Path, *, maximum: int, label: str) -> tuple[bytes, list[Any]]:
    if path.is_symlink() or not path.is_file():
        raise GuardError(f"{label} must be a regular file: {path}")
    raw = path.read_bytes()
    if len(raw) > maximum:
        raise GuardError(f"{label} exceeds {maximum} bytes")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GuardError(f"{label} is not strict UTF-8 JSON: {exc}") from exc
    if not isinstance(value, list):
        raise GuardError(f"{label} must be a JSON array")
    return raw, value


def load_policy(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw, policy = _load_json(path, maximum=131_072, label="maintenance policy")
    if set(policy) != POLICY_KEYS:
        raise GuardError("maintenance policy has unexpected or missing top-level keys")
    if policy.get("schema_version") != 1:
        raise GuardError("maintenance policy schema_version must be 1")
    workflows = policy.get("source_workflows")
    if not isinstance(workflows, list) or not workflows:
        raise GuardError("maintenance policy requires source_workflows")
    seen_names: set[str] = set()
    seen_providers: set[str] = set()
    for item in workflows:
        if not isinstance(item, dict) or set(item) != {"name", "provider", "path"}:
            raise GuardError("source workflow entries must contain only name, provider, and path")
        name = item["name"]
        provider = item["provider"]
        workflow_path = item["path"]
        if not isinstance(name, str) or not name or name in seen_names:
            raise GuardError("source workflow names must be unique non-empty strings")
        if provider != "kiro" or provider in seen_providers:
            raise GuardError("source workflow providers must be unique and supported")
        if (
            not isinstance(workflow_path, str)
            or not workflow_path.startswith(".github/workflows/")
            or not workflow_path.endswith((".yml", ".yaml"))
        ):
            raise GuardError("source workflow paths must identify repository workflow YAML")
        seen_names.add(name)
        seen_providers.add(provider)
    for name in (
        "agent_allowed_exact",
        "final_allowed_exact",
        "protected_basenames",
        "protected_exact",
        "protected_path_components",
        "protected_prefixes",
    ):
        if not isinstance(policy.get(name), list) or not all(
            isinstance(item, str) and item for item in policy[name]
        ):
            raise GuardError(f"maintenance policy {name} must be a non-empty string list")
    if policy["protected_basenames"] != [
        "AGENTS.md",
        "CLAUDE.local.md",
        "CLAUDE.md",
        "GEMINI.md",
    ]:
        raise GuardError("maintenance policy reviewer-instruction basenames changed")
    if policy["protected_path_components"] != [
        ".claude",
        ".codex",
        ".cursor",
        ".gemini",
    ]:
        raise GuardError("maintenance policy reviewer-instruction components changed")
    for name in ("agent_allowed_prefixes", "final_allowed_prefixes"):
        mapping = policy.get(name)
        if not isinstance(mapping, dict):
            raise GuardError(f"maintenance policy {name} must be an object")
        for prefix, suffixes in mapping.items():
            if not isinstance(prefix, str) or not prefix.endswith("/"):
                raise GuardError(f"maintenance policy {name} prefixes must end in /")
            if not isinstance(suffixes, list) or not suffixes:
                raise GuardError(f"maintenance policy {name} suffix lists must be non-empty")
            if not all(isinstance(suffix, str) and suffix.startswith(".") for suffix in suffixes):
                raise GuardError(f"maintenance policy {name} has an invalid suffix")
    limits = policy.get("limits")
    if not isinstance(limits, dict) or set(limits) != {
        "max_changed_files",
        "max_patch_bytes",
        "max_changed_lines",
        "max_candidate_package_bytes",
        "max_review_ledger_bytes",
        "max_review_transitions",
    }:
        raise GuardError("maintenance policy limits are invalid")
    if not all(type(value) is int and value > 0 for value in limits.values()):
        raise GuardError("maintenance policy limits must be positive integers")
    if limits["max_candidate_package_bytes"] != CANDIDATE_PACKAGE_MAX_BYTES:
        raise GuardError("candidate package limit changed from the exact 32 MiB boundary")
    if (
        limits["max_review_ledger_bytes"] != REVIEW_LEDGER_MAX_BYTES
        or limits["max_review_transitions"] != REVIEW_TRANSITION_MAX
    ):
        raise GuardError("review ledger bounds differ from the immutable controller contract")
    authority = policy.get("ci_authority")
    if not isinstance(authority, dict) or set(authority) != {
        "path",
        "power_managed",
        "candidate_mutable",
        "tools",
        "runtime_trust_tools",
        "tools_settings",
        "resources",
        "write_patterns",
        "deny_patterns",
    }:
        raise GuardError("maintenance policy ci_authority is invalid")
    if authority["path"] != ".kiro/agents/pstack-maintainer.json":
        raise GuardError("maintenance policy CI authority path changed")
    if authority["power_managed"] is not False or authority["candidate_mutable"] is not False:
        raise GuardError("maintenance policy CI authority must be immutable and repo-only")
    if authority["tools"] != ["read", "grep", "write"]:
        raise GuardError("maintenance policy CI authority tools changed")
    if authority["runtime_trust_tools"] != ["fs_read", "fs_write", "grep"]:
        raise GuardError("maintenance policy Kiro runtime trust-tool ids changed")
    if authority["tools_settings"] != {}:
        raise GuardError("maintenance policy Kiro toolsSettings must stay empty")
    for name in ("resources", "write_patterns", "deny_patterns"):
        if not isinstance(authority[name], list) or not all(
            isinstance(item, str) and item for item in authority[name]
        ):
            raise GuardError(f"maintenance policy ci_authority {name} is invalid")

    pull_request = policy.get("pull_request")
    if not isinstance(pull_request, dict) or set(pull_request) != {
        "author_id",
        "author_login",
        "branch_prefix",
        "title",
    }:
        raise GuardError("maintenance policy pull_request is invalid")
    if (
        pull_request["author_id"] != 41_898_282
        or pull_request["author_login"] != "github-actions[bot]"
        or pull_request["branch_prefix"] != "pk-stack-upstream/"
        or pull_request["title"] != "[pk-stack upstream] Reconcile pinned upstream semantics"
    ):
        raise GuardError("maintenance pull-request identity contract changed")

    lifecycle = policy.get("candidate_lifecycle")
    if not isinstance(lifecycle, dict) or set(lifecycle) != {
        "workflow_name",
        "workflow_path",
        "run_title_prefix",
        "freshness_seconds",
    }:
        raise GuardError("maintenance policy candidate_lifecycle is invalid")
    if lifecycle != {
        "workflow_name": "PK-Stack Upstream Candidate Gate",
        "workflow_path": ".github/workflows/pk-stack-upstream-candidate.yml",
        "run_title_prefix": "PK-Stack candidate gate for source run ",
        "freshness_seconds": 21_600,
    }:
        raise GuardError("candidate lifecycle identity or freshness contract changed")

    proposal = ".pk-stack-maintenance/proposal.json"
    ledger = "maintenance/upstream-reviews.json"
    manifest = "maintenance/upstreams.json"
    agent_exact = set(policy["agent_allowed_exact"])
    final_exact = set(policy["final_allowed_exact"])
    if proposal not in agent_exact or proposal in final_exact:
        raise GuardError("review proposal must be ephemeral and agent-only")
    if not {ledger, manifest} <= final_exact or {ledger, manifest} & agent_exact:
        raise GuardError("upstream pin and review ledger must be finalizer-only")
    if not {"powers/pk-stack/src/pstack_kiro/", "powers/pk-stack/tests/"} <= set(
        policy["protected_prefixes"]
    ):
        raise GuardError("controller and canonical Power tests must be protected")
    review = policy.get("candidate_review")
    if not isinstance(review, dict) or set(review) != {
        "required",
        "provider",
        "model",
        "effort",
        "credential_secret",
        "agent",
    }:
        raise GuardError("maintenance policy candidate_review is invalid")
    if (
        review["required"] is not True
        or review["provider"] != "kiro"
        or review["model"] != "claude-opus-5"
        or review["effort"] != "xhigh"
        or review["credential_secret"] != "KIRO_API_KEY"
        or review["agent"] != "pstack-ci-reviewer"
    ):
        raise GuardError("mandatory Kiro-hosted candidate review contract changed")
    return raw, policy


def _validate_path(path: str) -> None:
    candidate = PurePosixPath(path)
    if (
        not path
        or path.startswith("/")
        or "\\" in path
        or any(ord(character) < 32 for character in path)
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        raise GuardError(f"unsafe repository path: {path!r}")


def _matches(path: str, exact: set[str], prefixes: dict[str, list[str]]) -> bool:
    if path in exact:
        return True
    return any(
        path.startswith(prefix) and any(path.endswith(suffix) for suffix in suffixes)
        for prefix, suffixes in prefixes.items()
    )


def _is_protected(path: str, policy: dict[str, Any]) -> bool:
    candidate = PurePosixPath(path)
    return (
        candidate.name in set(policy["protected_basenames"])
        or bool(set(candidate.parts) & set(policy["protected_path_components"]))
        or path in set(policy["protected_exact"])
        or any(path.startswith(prefix) for prefix in policy["protected_prefixes"])
    )


def _changed_paths(root: Path, base_sha: str) -> list[str]:
    tracked = _git_bytes(root, "diff", "--name-only", "-z", "--no-renames", base_sha)
    untracked = _git_bytes(root, "ls-files", "--others", "--exclude-standard", "-z")
    paths = {
        item.decode("utf-8", errors="strict") for item in (tracked + untracked).split(b"\0") if item
    }
    for path in paths:
        _validate_path(path)
    return sorted(paths)


def _validate_worktree_paths(
    root: Path,
    base_sha: str,
    policy: dict[str, Any],
    *,
    scope: str,
) -> list[str]:
    if _git_text(root, "rev-parse", "HEAD").strip() != base_sha:
        raise GuardError("maintenance agents may not create commits or move HEAD")
    if _git_bytes(root, "rev-list", "--merges", f"{base_sha}..HEAD"):
        raise GuardError("merge commits are outside the maintenance boundary")
    paths = _changed_paths(root, base_sha)
    if len(paths) > policy["limits"]["max_changed_files"]:
        raise GuardError("maintenance candidate exceeds the changed-file limit")
    exact = set(policy[f"{scope}_allowed_exact"])
    prefixes = policy[f"{scope}_allowed_prefixes"]
    for path in paths:
        if _is_protected(path, policy) or not _matches(path, exact, prefixes):
            raise GuardError(f"path outside the {scope} maintenance boundary: {path}")
        absolute = root / path
        if absolute.exists() or absolute.is_symlink():
            metadata = os.lstat(absolute)
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                raise GuardError(f"candidate path must be a regular file: {path}")
    return paths


def _validate_staged_diff(
    root: Path,
    base_sha: str,
    policy: dict[str, Any],
    *,
    expected_paths: list[str],
    index_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    renamed = _git_bytes(
        root,
        "diff",
        "--cached",
        "--name-only",
        "-z",
        "--diff-filter=RC",
        "--find-renames",
        "--find-copies",
        base_sha,
        env=index_env,
    )
    if renamed:
        raise GuardError("renames and copies are outside the maintenance boundary")
    raw_paths = _git_bytes(
        root,
        "diff",
        "--cached",
        "--name-only",
        "-z",
        "--no-renames",
        base_sha,
        env=index_env,
    )
    paths = sorted(item.decode("utf-8", errors="strict") for item in raw_paths.split(b"\0") if item)
    if paths != expected_paths:
        raise GuardError("staged maintenance paths changed across boundary validation")

    records: dict[str, tuple[str, str, str]] = {}
    raw_records = _git_bytes(root, "ls-files", "--stage", "-z", env=index_env)
    for record in raw_records.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode, object_sha, stage = metadata.decode("ascii").split(" ")
        records[encoded_path.decode("utf-8", errors="strict")] = (mode, object_sha, stage)
    for path in paths:
        if path not in records:
            continue
        mode, object_sha, stage = records[path]
        expected_mode = "100755" if path in EXECUTABLE_PATHS else "100644"
        if stage != "0" or mode != expected_mode:
            raise GuardError(f"unexpected git index mode for {path}: {mode} stage {stage}")
        if _git_text(root, "cat-file", "-t", object_sha).strip() != "blob":
            raise GuardError(f"unexpected git object type for {path}")

    changed_lines = 0
    numstat = _git_text(
        root,
        "diff",
        "--cached",
        "--numstat",
        "--no-renames",
        base_sha,
        env=index_env,
    )
    for line in numstat.splitlines():
        additions, deletions, _ = line.split("\t", 2)
        if additions == "-" or deletions == "-":
            raise GuardError("binary maintenance patches are not allowed")
        changed_lines += int(additions) + int(deletions)
    if changed_lines > policy["limits"]["max_changed_lines"]:
        raise GuardError("maintenance candidate exceeds the changed-line limit")
    patch = _git_bytes(
        root,
        "diff",
        "--cached",
        "--binary",
        "--no-ext-diff",
        "--no-renames",
        base_sha,
        env=index_env,
    )
    if len(patch) > policy["limits"]["max_patch_bytes"]:
        raise GuardError("maintenance candidate exceeds the patch-byte limit")
    checked = _git_run(
        root,
        "diff",
        "--cached",
        "--check",
        base_sha,
        env=index_env,
        check=False,
    )
    if checked.returncode != 0:
        raise GuardError(checked.stdout.decode("utf-8", errors="replace").strip())
    return {
        "paths": paths,
        "changed_files": len(paths),
        "changed_lines": changed_lines,
        "patch_bytes": len(patch),
        "patch_sha256": hashlib.sha256(patch).hexdigest(),
    }


def validate_boundary(
    root: Path,
    base_sha: str,
    policy: dict[str, Any],
    *,
    scope: str,
    stage: bool,
) -> dict[str, Any]:
    paths = _validate_worktree_paths(root, base_sha, policy, scope=scope)
    if not stage:
        return {"paths": paths, "changed_files": len(paths)}
    _git_run(root, "add", "-A", "--", ".")
    if _git_bytes(root, "diff", "--name-only", "-z"):
        raise GuardError("maintenance candidate contains unstaged tracked changes")
    if _git_bytes(root, "ls-files", "--others", "--exclude-standard", "-z"):
        raise GuardError("maintenance candidate contains unstaged untracked files")
    return _validate_staged_diff(
        root,
        base_sha,
        policy,
        expected_paths=paths,
    )


def _tracked_at_base(root: Path, base_sha: str, prefix: str) -> set[str]:
    raw = _git_bytes(root, "ls-tree", "-r", "--name-only", "-z", base_sha, "--", prefix)
    return {item.decode("utf-8", errors="strict") for item in raw.split(b"\0") if item}


def _remove_untracked_generated(root: Path, base_sha: str) -> None:
    tracked: set[str] = set()
    for prefix in GENERATED_PREFIXES:
        tracked.update(_tracked_at_base(root, base_sha, prefix.rstrip("/")))
    tracked.update(
        path
        for path in GENERATED_EXACT
        if _git_run(root, "cat-file", "-e", f"{base_sha}:{path}", check=False).returncode == 0
    )
    roots = [root / prefix.rstrip("/") for prefix in GENERATED_PREFIXES]
    for generated_root in roots:
        if not generated_root.exists() and not generated_root.is_symlink():
            continue
        for path in sorted(
            generated_root.rglob("*"), key=lambda item: len(item.parts), reverse=True
        ):
            relative = path.relative_to(root).as_posix()
            if relative.startswith(".pstack/state/"):
                continue
            if path.is_symlink() or path.is_file():
                if relative not in tracked:
                    path.unlink()
            elif path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
    for relative in GENERATED_EXACT:
        path = root / relative
        if relative not in tracked and (path.exists() or path.is_symlink()):
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)


def restore_generated(root: Path, base_sha: str) -> None:
    _remove_untracked_generated(root, base_sha)
    pathspecs = [prefix.rstrip("/") for prefix in GENERATED_PREFIXES]
    pathspecs.extend(sorted(GENERATED_EXACT))
    existing_at_base = [
        path
        for path in pathspecs
        if _git_run(root, "cat-file", "-e", f"{base_sha}:{path}", check=False).returncode == 0
    ]
    if existing_at_base:
        _git_run(
            root,
            "restore",
            "--source",
            base_sha,
            "--staged",
            "--worktree",
            "--",
            *existing_at_base,
        )


def validate_trusted_snapshot(root: Path, base_sha: str, trusted_root: Path) -> None:
    if trusted_root.is_symlink() or not trusted_root.is_dir():
        raise GuardError("trusted snapshot root must be a regular directory")
    expected: set[str] = set()
    for prefix in TRUSTED_SNAPSHOT_PREFIXES:
        expected.update(_tracked_at_base(root, base_sha, prefix))
    if not expected:
        raise GuardError("trusted snapshot contains no immutable controls")
    for relative in sorted(expected):
        candidate = trusted_root / relative
        if candidate.is_symlink() or not candidate.is_file():
            raise GuardError(f"trusted snapshot file is missing or unsafe: {relative}")
        if candidate.read_bytes() != _git_bytes(root, "show", f"{base_sha}:{relative}"):
            raise GuardError(f"trusted snapshot file differs from the base commit: {relative}")
    actual: set[str] = set()
    for prefix in TRUSTED_SNAPSHOT_PREFIXES:
        candidate = trusted_root / prefix
        if candidate.is_file() and not candidate.is_symlink():
            actual.add(prefix)
            continue
        if not candidate.is_dir() or candidate.is_symlink():
            continue
        for path in candidate.rglob("*"):
            relative = path.relative_to(trusted_root).as_posix()
            if ".venv" in path.relative_to(trusted_root).parts:
                continue
            if path.is_symlink() or (path.exists() and not path.is_file() and not path.is_dir()):
                raise GuardError(f"trusted snapshot contains an unsafe object: {relative}")
            if path.is_file():
                actual.add(relative)
    if actual != expected:
        raise GuardError("trusted snapshot has missing or unexpected immutable control files")


def _remove_context(root: Path) -> None:
    context = root / ".pk-stack-ci"
    if context.is_symlink():
        raise GuardError("CI context directory may not be a symlink")
    if context.exists():
        if not context.is_dir():
            raise GuardError("CI context path must be a directory")
        shutil.rmtree(context)


def _prepare_proposal_root(root: Path) -> None:
    proposal_root = root / ".pk-stack-maintenance"
    if proposal_root.is_symlink():
        raise GuardError("maintenance proposal directory may not be a symlink")
    if proposal_root.exists() and not proposal_root.is_dir():
        raise GuardError("maintenance proposal path must be a directory")
    proposal_root.mkdir(mode=0o700, exist_ok=True)


def prepare_attempt(
    root: Path,
    base_sha: str,
    policy: dict[str, Any],
    detector_path: Path,
    feedback_path: Path,
    git_state_root: Path,
) -> None:
    if git_state_root.exists() or git_state_root.is_symlink():
        _assert_git_state_unchanged(root, base_sha, git_state_root)
        _remove_git_state(root, git_state_root)
    detector = validate_detector(detector_path)
    restore_generated(root, base_sha)
    _cleanup_unaccepted_provenance_tail(root, detector)
    _remove_context(root)
    validate_boundary(root, base_sha, policy, scope="agent", stage=True)
    proposal_root = root / ".pk-stack-maintenance"
    if detector["validated_drift_heads"]:
        _prepare_proposal_root(root)
    elif proposal_root.exists() or proposal_root.is_symlink():
        if proposal_root.is_symlink() or not proposal_root.is_dir():
            raise GuardError("unexpected maintenance proposal path without upstream drift")
        try:
            proposal_root.rmdir()
        except OSError as exc:
            raise GuardError("unexpected maintenance proposal data without upstream drift") from exc
    workspace_kiro = root / ".kiro"
    if workspace_kiro.is_symlink():
        raise GuardError("workspace .kiro may not be a symlink")
    if workspace_kiro.exists():
        if not workspace_kiro.is_dir():
            raise GuardError("workspace .kiro must be a directory")
        shutil.rmtree(workspace_kiro)
    context = root / ".pk-stack-ci"
    context.mkdir(mode=0o700)
    shutil.copyfile(detector_path, context / "upstream-delta.json")
    shutil.copyfile(feedback_path, context / "verification-feedback.txt")
    _record_git_state(root, base_sha, git_state_root)


def close_attempt(
    root: Path,
    base_sha: str,
    policy: dict[str, Any],
    git_state_root: Path,
) -> None:
    # This check is deliberately the first close operation. If model-visible
    # Git controls changed, no Git subprocess is started at all.
    _assert_git_state_unchanged(root, base_sha, git_state_root)
    workspace_kiro = root / ".kiro"
    if workspace_kiro.exists() or workspace_kiro.is_symlink():
        raise GuardError("Kiro attempt recreated the removed workspace .kiro directory")
    _remove_context(root)
    finalizer_environment = _open_git_finalizer(root, base_sha, git_state_root)
    try:
        with (
            _temporary_environment(finalizer_environment),
            _temporary_umask(0o077),
        ):
            _git_run(
                root,
                "restore",
                "--source",
                base_sha,
                "--staged",
                "--worktree",
                "--",
                ".kiro",
            )
            validate_boundary(root, base_sha, policy, scope="agent", stage=True)
    except Exception:
        # The checkout's own index and config were never touched. Discarding the
        # failed external finalizer makes the next bounded attempt start clean.
        _remove_git_state(root, git_state_root, phase="open")
        raise


def validate_ci_agent(agent_path: Path, policy: dict[str, Any]) -> None:
    _, agent = _load_json(agent_path, maximum=65_536, label="CI agent authority")
    authority = policy["ci_authority"]
    if set(agent) != {
        "name",
        "description",
        "prompt",
        "tools",
        "includeMcpJson",
        "includePowers",
        "resources",
        "permissions",
        "toolsSettings",
        "welcomeMessage",
    }:
        raise GuardError("CI agent authority has unexpected or missing fields")
    if agent.get("name") != "pstack-maintainer":
        raise GuardError("CI agent name must be pstack-maintainer")
    if agent.get("tools") != authority["tools"]:
        raise GuardError("CI agent tools must be exactly read, grep, and write")
    if agent.get("resources") != authority["resources"]:
        raise GuardError("CI agent resources differ from the immutable policy")
    prompt = agent.get("prompt")
    marker_requirements = (
        "select the lexicographically smallest drifting source id",
        "proposal must name that source_id",
        "leave every other drifting source unchanged for a later cadence",
        "append exactly one new final pk-stack-upstream-review HTML comment",
        "preserve every prior review marker unchanged and in order",
        "marker count equals the existing review-ledger transition count plus one",
    )
    if not isinstance(prompt, str) or any(item not in prompt for item in marker_requirements):
        raise GuardError("CI agent lost the append-only provenance-marker contract")
    if agent.get("includeMcpJson") is not False or agent.get("includePowers") is not False:
        raise GuardError("CI agent must disable inherited MCP and Powers")
    if agent.get("toolsSettings") != authority["tools_settings"]:
        raise GuardError("CI agent toolsSettings must be the immutable empty object")
    forbidden_keys = {
        "allowedTools",
        "excludedTools",
        "hooks",
        "mcpServers",
        "model",
    }
    if forbidden_keys.intersection(agent):
        raise GuardError("CI agent contains a forbidden authority-bearing field")
    permissions = agent.get("permissions")
    if not isinstance(permissions, dict) or set(permissions) != {"rules"}:
        raise GuardError("CI agent permissions must contain only rules")
    rules = permissions["rules"]
    if not isinstance(rules, list) or not rules:
        raise GuardError("CI agent permission rules are required")
    read_patterns: set[str] = set()
    grep_patterns: set[str] = set()
    write_patterns: set[str] = set()
    deny_patterns: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"capability", "match", "effect"}:
            raise GuardError("CI agent permission rule shape is invalid")
        capability = rule["capability"]
        effect = rule["effect"]
        matches = rule["match"]
        if not isinstance(matches, list) or not all(isinstance(item, str) for item in matches):
            raise GuardError("CI agent permission matches must be strings")
        if capability == "fs_read" and effect == "allow":
            read_patterns.update(matches)
        elif capability == "grep" and effect == "allow":
            grep_patterns.update(matches)
        elif capability == "fs_write" and effect == "allow":
            write_patterns.update(matches)
        elif capability == "fs_write" and effect == "deny":
            deny_patterns.update(matches)
        else:
            raise GuardError("CI agent may only contain read/grep allow and write allow/deny rules")
    if read_patterns != {"./**"}:
        raise GuardError("CI agent read authority must be exactly ./**")
    if grep_patterns != {"./**"}:
        raise GuardError("CI agent grep authority must be exactly ./**")
    if write_patterns != set(authority["write_patterns"]):
        raise GuardError("CI agent write allowlist differs from the immutable policy")
    if deny_patterns != set(authority["deny_patterns"]):
        raise GuardError("CI agent write denylist differs from the immutable policy")


def validate_product_envelope(root: Path) -> None:
    agent_root = root / ".kiro" / "agents"
    agents = sorted(agent_root.glob("*.json"))
    product_agents = [path for path in agents if path.name != "pstack-maintainer.json"]
    if not product_agents:
        raise GuardError("generated product agents are missing")
    for path in product_agents:
        _, agent = _load_json(path, maximum=65_536, label=f"product agent {path.name}")
        tools = agent.get("tools")
        if not isinstance(tools, list) or not set(tools) <= ALLOWED_PRODUCT_TOOLS:
            raise GuardError(f"product agent has unsupported tools: {path.name}")
        if any(
            tool.startswith("@") or tool in {"web", "web_fetch", "web_search"} for tool in tools
        ):
            raise GuardError(f"product agent widens external tool authority: {path.name}")
        if agent.get("includeMcpJson") is not False or agent.get("includePowers") is not False:
            raise GuardError(f"product agent enables ambient integrations: {path.name}")
        if any(key in agent for key in ("hooks", "mcpServers", "model")):
            raise GuardError(f"product agent contains an unsafe embedded authority: {path.name}")
        rules = agent.get("permissions", {}).get("rules")
        if not isinstance(rules, list) or not rules:
            raise GuardError(f"product agent lacks explicit permissions: {path.name}")
        for rule in rules:
            if not isinstance(rule, dict):
                raise GuardError(f"product agent permission is malformed: {path.name}")
            if rule.get("capability") in {"shell", "fs_write"} and rule.get("effect") == "allow":
                raise GuardError(f"product agent silently allows execution or writes: {path.name}")

    hook_root = root / ".kiro" / "hooks"
    hooks = sorted(hook_root.glob("*.json"))
    if {path.name for path in hooks} != ALLOWED_HOOKS:
        raise GuardError("generated product hooks differ from the bounded hook set")
    for path in hooks:
        _, document = _load_json(path, maximum=65_536, label=f"product hook {path.name}")
        entries = document.get("hooks")
        if document.get("version") != "v1" or not isinstance(entries, list) or len(entries) != 1:
            raise GuardError(f"product hook schema is invalid: {path.name}")
        hook = entries[0]
        if not isinstance(hook, dict) or hook.get("action", {}).get("type") != "command":
            raise GuardError(f"product hook action is invalid: {path.name}")
        command = hook["action"].get("command")
        if not isinstance(command, str):
            raise GuardError(f"product hook command is invalid: {path.name}")
        if path.name == "pstack-session.json":
            if hook.get("trigger") != "SessionStart" or hook.get("enabled") is not True:
                raise GuardError("session hook trigger or enabled state widened")
            try:
                argv = shlex.split(command)
            except ValueError as exc:
                raise GuardError("session hook command is not safely parseable") from exc
            if len(argv) != 3 or argv[:2] != ["printf", "%s\\n"]:
                raise GuardError("enabled session hook must remain a static printf")
            try:
                hook_payload = json.loads(argv[2])
            except json.JSONDecodeError as exc:
                raise GuardError("enabled session hook payload must remain static JSON") from exc
            if not isinstance(hook_payload, dict):
                raise GuardError("enabled session hook payload must remain a static JSON object")
        else:
            if hook.get("trigger") != "Stop" or hook.get("enabled") is not False:
                raise GuardError("tripwire hook must remain disabled and advisory")
            if ".pstack/bin/projectctl goal tripwire --output json" not in command:
                raise GuardError("disabled tripwire hook lost its bounded command")


def _exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise GuardError(f"{label} has unexpected or missing fields")
    return value


def _boolean(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise GuardError(f"{label} must be a boolean")
    return value


def _count(value: Any, label: str, *, maximum: int | None = None) -> int:
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise GuardError(f"{label} must be a bounded non-negative integer")
    return value


def _sha1(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise GuardError(f"{label} must be a full lowercase SHA-1")
    return value


def _sha256(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise GuardError(f"{label} must be a lowercase SHA-256")
    return value


def _normalized_path(value: Any, label: str, *, suffix: str | None = None) -> str:
    if not isinstance(value, str) or len(value) > 1024:
        raise GuardError(f"{label} must be a bounded path string")
    _validate_path(value)
    if PurePosixPath(value).as_posix() != value or (suffix and not value.endswith(suffix)):
        raise GuardError(f"{label} is not a normalized repository path")
    return value


def _identity(value: Any, label: str, *, with_ok: bool = False) -> dict[str, Any]:
    keys = {"commit", "subtree_sha"} | ({"ok"} if with_ok else set())
    identity = _exact_keys(value, keys, label)
    _sha1(identity["commit"], f"{label} commit")
    _sha1(identity["subtree_sha"], f"{label} subtree_sha")
    if with_ok:
        _boolean(identity["ok"], f"{label} ok")
    return identity


def _tree_identity(value: Any, label: str) -> dict[str, Any] | None:
    if value is None:
        return None
    identity = _exact_keys(value, {"type", "mode", "sha", "size"}, label)
    if identity["type"] != "blob" or identity["mode"] not in {"100644", "100755"}:
        raise GuardError(f"{label} must be a regular blob in mode 100644 or 100755")
    _sha1(identity["sha"], f"{label} sha")
    if identity["size"] is not None:
        _count(identity["size"], f"{label} size")
    return identity


def _validate_unified_patch(
    patch: str,
    *,
    additions: int,
    deletions: int,
    label: str,
) -> None:
    if not patch or "\0" in patch or "\r" in patch:
        raise GuardError(f"{label} unified patch is empty or malformed")
    expected_old: int | None = None
    expected_new: int | None = None
    consumed_old = 0
    consumed_new = 0
    actual_additions = 0
    actual_deletions = 0
    hunk_count = 0

    def require_complete_hunk() -> None:
        if expected_old is None or consumed_old != expected_old or consumed_new != expected_new:
            raise GuardError(f"{label} unified patch is truncated or malformed")

    for line in patch.splitlines():
        header = _UNIFIED_HUNK.fullmatch(line)
        if header:
            if hunk_count:
                require_complete_hunk()
            hunk_count += 1
            expected_old = int(header.group("old_count") or "1")
            expected_new = int(header.group("new_count") or "1")
            consumed_old = 0
            consumed_new = 0
            continue
        if not hunk_count:
            raise GuardError(f"{label} unified patch must begin with a hunk header")
        if expected_old is None or expected_new is None:  # pragma: no cover
            raise GuardError(f"{label} unified patch has no active hunk")
        if line == "\\ No newline at end of file":
            continue
        if not line or line[0] not in {" ", "+", "-"}:
            raise GuardError(f"{label} unified patch has an invalid body line")
        if line[0] in {" ", "-"}:
            consumed_old += 1
        if line[0] in {" ", "+"}:
            consumed_new += 1
        if line[0] == "+":
            actual_additions += 1
        elif line[0] == "-":
            actual_deletions += 1
        if consumed_old > expected_old or consumed_new > expected_new:
            raise GuardError(f"{label} unified patch hunk counts are inconsistent")
    if not hunk_count:
        raise GuardError(f"{label} unified patch has no hunks")
    require_complete_hunk()
    if actual_additions != additions or actual_deletions != deletions:
        raise GuardError(f"{label} unified patch body counts disagree with metadata")


def _validate_comparison_file(value: Any, *, label: str) -> set[str]:
    file = _exact_keys(
        value,
        {
            "path",
            "previous_path",
            "status",
            "sha",
            "additions",
            "deletions",
            "changes",
            "patch",
            "patch_bytes",
            "no_patch",
            "content_class",
            "reviewability",
            "old_identity",
            "new_identity",
            "tree_sha_verified",
        },
        label,
    )
    status_value = file["status"]
    if status_value not in {"added", "removed", "modified", "renamed", "copied", "changed"}:
        raise GuardError(f"{label} status is unsupported")
    path = file["path"]
    previous = file["previous_path"]
    if path is not None:
        path = _normalized_path(path, f"{label} path")
    if previous is not None:
        previous = _normalized_path(previous, f"{label} previous_path")
    if status_value == "renamed":
        if path is None and previous is None:
            raise GuardError(f"{label} renamed entry has no path identity")
    elif path is None or previous is not None:
        raise GuardError(f"{label} path fields disagree with status")
    comparison_sha = _sha1(file["sha"], f"{label} sha")
    old_identity = _tree_identity(file["old_identity"], f"{label} old_identity")
    new_identity = _tree_identity(file["new_identity"], f"{label} new_identity")
    expected_presence = {
        "added": (False, True),
        "copied": (False, True),
        "removed": (True, False),
        "modified": (True, True),
        "changed": (True, True),
        "renamed": (previous is not None, path is not None),
    }[status_value]
    if (old_identity is not None, new_identity is not None) != expected_presence:
        raise GuardError(f"{label} old/new identities disagree with status and paths")
    expected_sha = (
        old_identity["sha"]
        if status_value == "removed" and old_identity is not None
        else new_identity["sha"]
        if new_identity is not None
        else None
    )
    if expected_sha is not None and comparison_sha != expected_sha:
        raise GuardError(f"{label} comparison SHA disagrees with exact tree identity")
    additions = _count(file["additions"], f"{label} additions")
    deletions = _count(file["deletions"], f"{label} deletions")
    changes = _count(file["changes"], f"{label} changes")
    if additions + deletions != changes:
        raise GuardError(f"{label} change counts disagree")
    patch = file["patch"]
    no_patch = _boolean(file["no_patch"], f"{label} no_patch")
    if patch is not None and not isinstance(patch, str):
        raise GuardError(f"{label} patch must be text or null")
    patch_bytes = _count(file["patch_bytes"], f"{label} patch_bytes", maximum=65_536)
    if no_patch != (patch is None) or patch_bytes != (
        0 if patch is None else len(patch.encode("utf-8"))
    ):
        raise GuardError(f"{label} patch metadata disagrees")
    identities = [item for item in (path, previous if status_value == "renamed" else None) if item]
    if patch is not None:
        _validate_unified_patch(
            patch,
            additions=additions,
            deletions=deletions,
            label=label,
        )
        expected_reviewability = "exact-blob-unified-patch"
        expected_class = "exact-blob-text-patch"
    elif additions != 0 or deletions != 0 or changes != 0:
        raise GuardError(f"{label} no-patch entry must have zero change counts")
    elif status_value == "renamed" and path is not None and previous is not None:
        if (
            old_identity is None
            or new_identity is None
            or old_identity["sha"] != new_identity["sha"]
        ):
            raise GuardError(f"{label} pure rename does not preserve exact blob identity")
        expected_reviewability = "exact-blob-pure-rename"
        expected_class = "exact-blob-identity"
    elif identities and all(_NONSEMANTIC_IMAGE_PATH.fullmatch(item) for item in identities):
        expected_reviewability = "unavailable-nonsemantic-image"
        expected_class = "binary-or-patch-unavailable"
    elif status_value in {"modified", "changed"}:
        if (
            old_identity is None
            or new_identity is None
            or old_identity["sha"] != new_identity["sha"]
            or old_identity["mode"] == new_identity["mode"]
        ):
            raise GuardError(f"{label} no-patch mode change lacks an exact blob/mode transition")
        expected_reviewability = "exact-blob-mode-change"
        expected_class = "exact-blob-identity"
    else:
        raise GuardError(f"{label} lacks a reviewable patch or bounded binary exception")
    if file["reviewability"] != expected_reviewability or file["content_class"] != expected_class:
        raise GuardError(f"{label} reviewability or content_class disagrees")
    tree_sha_verified = _boolean(file["tree_sha_verified"], f"{label} tree_sha_verified")
    rename_out = status_value == "renamed" and path is None and previous is not None
    if tree_sha_verified is rename_out:
        raise GuardError(f"{label} tree SHA verification marker disagrees with its exact shape")
    return set(identities)


def _validate_review_reproof(value: Any, *, source_id: str, pinned: dict[str, Any]) -> None:
    review = _exact_keys(
        value,
        {
            "ok",
            "source_id",
            "genesis",
            "tip",
            "transition_count",
            "remote_transition_indices",
            "history_validation",
            "transitions",
        },
        "upstream detector review_reproof",
    )
    if _boolean(review["ok"], "upstream detector review_reproof ok") is not True:
        raise GuardError("upstream review ledger was not re-proved")
    if review["source_id"] != source_id:
        raise GuardError("upstream review reproof source id changed")
    _identity(review["genesis"], "upstream review genesis")
    tip = _identity(review["tip"], "upstream review tip")
    if tip != pinned:
        raise GuardError("upstream review ledger tip does not match the pin")
    transition_count = _count(
        review["transition_count"],
        "upstream review transition_count",
        maximum=REVIEW_TRANSITION_MAX,
    )
    expected_indices = [] if transition_count == 0 else [transition_count - 1]
    if review["remote_transition_indices"] != expected_indices:
        raise GuardError("upstream review remote transition indexes are invalid")
    if review["history_validation"] != (
        "all entries form a strict local contiguous chain; repository history is the "
        "tamper-evident authority for older reviewed transitions"
    ):
        raise GuardError("upstream review history-validation contract changed")
    transitions = review["transitions"]
    if not isinstance(transitions, list) or len(transitions) != len(expected_indices):
        raise GuardError("upstream review latest-transition reproof is invalid")
    latest_new: dict[str, Any] | None = None
    for index, item in enumerate(transitions):
        expected_index = expected_indices[index]
        transition = _exact_keys(
            item,
            {
                "index",
                "prior",
                "new",
                "inventory_sha256",
                "path_count",
                "disposition_counts",
            },
            f"upstream review transition {index}",
        )
        if transition["index"] != expected_index:
            raise GuardError("upstream review latest-transition index is invalid")
        prior = _identity(
            transition["prior"],
            f"upstream review transition {expected_index} prior",
        )
        latest_new = _identity(
            transition["new"],
            f"upstream review transition {expected_index} new",
        )
        if transition_count == 1 and prior != review["genesis"]:
            raise GuardError("first upstream review transition does not begin at genesis")
        _sha256(
            transition["inventory_sha256"],
            f"upstream review transition {index} inventory_sha256",
        )
        path_count = _count(
            transition["path_count"],
            f"upstream review transition {index} path_count",
            maximum=100,
        )
        counts = _exact_keys(
            transition["disposition_counts"],
            {"A", "B", "C"},
            f"upstream review transition {index} disposition_counts",
        )
        if (
            sum(_count(counts[key], f"upstream review {key} count") for key in ("A", "B", "C"))
            != path_count
        ):
            raise GuardError("upstream review disposition counts disagree")
    if transition_count == 0:
        if review["genesis"] != pinned:
            raise GuardError("empty upstream review chain does not terminate at the pin")
    elif latest_new != pinned:
        raise GuardError("upstream review latest transition does not terminate at the pin")


def validate_detector(path: Path) -> dict[str, Any]:
    _, detector = _load_json(path, maximum=1_048_576, label="upstream detector output")
    _exact_keys(
        detector,
        {
            "ok",
            "schema_version",
            "manifest",
            "review_ledger",
            "network_boundary",
            "selected_source_id",
            "sources",
            "bootstrap_preview",
            "generated_parity",
        },
        "upstream detector output",
    )
    if (
        detector["schema_version"] != UPSTREAM_SCHEMA_VERSION
        or detector["network_boundary"] != "https://api.github.com"
    ):
        raise GuardError("upstream detector output has an invalid schema or network boundary")
    if detector["manifest"] != "maintenance/upstreams.json":
        raise GuardError("upstream detector used an unexpected manifest")
    if detector["review_ledger"] != "maintenance/upstream-reviews.json":
        raise GuardError("upstream detector used an unexpected review ledger")
    overall_ok = _boolean(detector["ok"], "upstream detector ok")
    sources = detector.get("sources")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 16:
        raise GuardError("upstream detector output must have a bounded non-empty source list")
    seen_ids: set[str] = set()
    drift_sources: list[dict[str, str]] = []
    source_results: list[bool] = []
    for source_index, source_value in enumerate(sources):
        source = _exact_keys(
            source_value,
            {
                "ok",
                "id",
                "repository",
                "path",
                "ref",
                "provenance_path",
                "parity_path",
                "pinned",
                "pinned_reproof",
                "current",
                "drift",
                "comparison",
                "review_reproof",
                "source_parity",
            },
            f"upstream detector source {source_index}",
        )
        source_id = source["id"]
        if (
            not isinstance(source_id, str)
            or not source_id
            or len(source_id) > 64
            or source_id in seen_ids
            or _SOURCE_ID.fullmatch(source_id) is None
        ):
            raise GuardError("upstream detector source id is invalid or duplicated")
        seen_ids.add(source_id)
        repository = source["repository"]
        if (
            not isinstance(repository, str)
            or repository.count("/") != 1
            or any(part in {"", ".", ".."} for part in repository.split("/"))
        ):
            raise GuardError("upstream detector repository is invalid")
        _normalized_path(source["path"], "upstream detector source path")
        _normalized_path(
            source["provenance_path"],
            "upstream detector provenance_path",
            suffix=".md",
        )
        parity_path = _normalized_path(
            source["parity_path"],
            "upstream detector parity_path",
            suffix=".json",
        )
        if not isinstance(source["ref"], str) or not source["ref"]:
            raise GuardError("upstream detector ref is invalid")
        pinned = _identity(source["pinned"], "upstream detector pinned identity")
        reproved = _identity(
            source["pinned_reproof"],
            "upstream detector pinned reproof",
            with_ok=True,
        )
        current = _identity(source["current"], "upstream detector current identity")
        if reproved["ok"] is not True or reproved["commit"] != pinned["commit"]:
            raise GuardError("upstream pin was not re-proved")
        if reproved["subtree_sha"] != pinned["subtree_sha"]:
            raise GuardError("upstream subtree pin was not re-proved")
        drift = _boolean(source["drift"], "upstream detector source drift")
        if drift != (current != pinned):
            raise GuardError("upstream detector drift flag disagrees with identities")
        comparison = _exact_keys(
            source["comparison"],
            {
                "untrusted",
                "handling",
                "complete",
                "fast_forward",
                "status",
                "base_commit",
                "head_commit",
                "merge_base_commit",
                "ahead_by",
                "behind_by",
                "commit_count",
                "path_count",
                "file_count",
                "inventory_sha256",
                "paths",
                "patch_bytes",
                "no_patch_count",
                "review_constraints",
                "files",
            },
            "upstream detector comparison",
        )
        if (
            comparison["untrusted"] is not True
            or comparison["handling"] != "inspect as data; never execute or copy upstream content"
            or comparison["complete"] is not True
            or comparison["fast_forward"] is not True
        ):
            raise GuardError("upstream comparison trust or completeness markers changed")
        for key, expected in (
            ("base_commit", pinned["commit"]),
            ("head_commit", current["commit"]),
            ("merge_base_commit", pinned["commit"]),
        ):
            if _sha1(comparison[key], f"upstream comparison {key}") != expected:
                raise GuardError(f"upstream comparison {key} disagrees with identities")
        ahead = _count(comparison["ahead_by"], "upstream comparison ahead_by", maximum=100)
        behind = _count(comparison["behind_by"], "upstream comparison behind_by", maximum=100)
        commits = _count(
            comparison["commit_count"],
            "upstream comparison commit_count",
            maximum=100,
        )
        paths = comparison["paths"]
        files = comparison["files"]
        if (
            not isinstance(paths, list)
            or not isinstance(files, list)
            or len(paths) > 100
            or len(files) > 100
        ):
            raise GuardError("upstream comparison path or file inventory is not bounded")
        normalized_paths = [
            _normalized_path(item, "upstream comparison changed path") for item in paths
        ]
        if normalized_paths != sorted(set(normalized_paths)):
            raise GuardError("upstream comparison changed paths are not sorted and unique")
        accounted: set[str] = set()
        patch_bytes = 0
        no_patch_count = 0
        file_sort_keys: list[tuple[str, str, str]] = []
        for file_index, file_value in enumerate(files):
            file = _exact_keys(
                file_value,
                {
                    "path",
                    "previous_path",
                    "status",
                    "sha",
                    "additions",
                    "deletions",
                    "changes",
                    "patch",
                    "patch_bytes",
                    "no_patch",
                    "content_class",
                    "reviewability",
                    "old_identity",
                    "new_identity",
                    "tree_sha_verified",
                },
                f"upstream comparison file {file_index}",
            )
            accounted.update(
                _validate_comparison_file(file, label=f"upstream comparison file {file_index}")
            )
            patch_bytes += file["patch_bytes"]
            no_patch_count += int(file["no_patch"])
            file_sort_keys.append(
                (
                    file["path"] or "",
                    file["previous_path"] or "",
                    file["status"],
                )
            )
        if file_sort_keys != sorted(file_sort_keys) or len(file_sort_keys) != len(
            set(file_sort_keys)
        ):
            raise GuardError("upstream comparison files are not sorted and unique")
        if sorted(accounted) != normalized_paths:
            raise GuardError("upstream comparison files do not exactly account for changed paths")
        if _count(comparison["path_count"], "upstream comparison path_count", maximum=100) != len(
            paths
        ):
            raise GuardError("upstream comparison path_count disagrees")
        if _count(comparison["file_count"], "upstream comparison file_count", maximum=100) != len(
            files
        ):
            raise GuardError("upstream comparison file_count disagrees")
        if (
            _count(comparison["patch_bytes"], "upstream comparison patch_bytes", maximum=262_144)
            != patch_bytes
        ):
            raise GuardError("upstream comparison patch_bytes disagrees")
        if (
            _count(comparison["no_patch_count"], "upstream comparison no_patch_count", maximum=100)
            != no_patch_count
        ):
            raise GuardError("upstream comparison no_patch_count disagrees")
        review_constraints = _exact_keys(
            comparison["review_constraints"],
            {
                "unified_patch_counts",
                "exact_blob_binding",
                "supported_tree_entries",
                "no_patch",
                "unavailable_binary_paths",
            },
            "upstream comparison review_constraints",
        )
        unavailable_paths = review_constraints["unavailable_binary_paths"]
        if (
            review_constraints["unified_patch_counts"] != PATCH_COUNT_CONSTRAINT
            or review_constraints["exact_blob_binding"] != BLOB_BINDING_CONSTRAINT
            or review_constraints["supported_tree_entries"] != TREE_ENTRY_CONSTRAINT
            or review_constraints["no_patch"] != NO_PATCH_CONSTRAINT
            or not isinstance(unavailable_paths, list)
        ):
            raise GuardError("upstream comparison review constraints changed")
        expected_unavailable = sorted(
            {
                identity
                for file in files
                if file["reviewability"] == "unavailable-nonsemantic-image"
                for identity in (file["path"], file["previous_path"])
                if isinstance(identity, str)
            }
        )
        if unavailable_paths != expected_unavailable:
            raise GuardError("upstream comparison unavailable binary paths disagree")
        inventory_sha256 = _sha256(
            comparison["inventory_sha256"],
            "upstream comparison inventory_sha256",
        )
        canonical_inventory = json.dumps(
            {
                "repository": repository,
                "source_path": source["path"],
                "base_commit": comparison["base_commit"],
                "head_commit": comparison["head_commit"],
                "files": files,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        if hashlib.sha256(canonical_inventory).hexdigest() != inventory_sha256:
            raise GuardError(
                "upstream comparison inventory digest is not bound to exact file metadata"
            )
        if drift:
            if comparison["status"] != "ahead" or behind != 0 or not (ahead == commits >= 1):
                raise GuardError("upstream drift is not a bounded fast-forward")
            drift_sources.append(
                {
                    "source_id": source_id,
                    "expected_head": current["commit"],
                }
            )
        elif (
            comparison["status"] != "identical"
            or ahead != 0
            or behind != 0
            or commits != 0
            or paths
            or files
        ):
            raise GuardError("identical upstream comparison contains drift metadata")
        source_ok = _boolean(source["ok"], "upstream detector source ok")
        _validate_review_reproof(source["review_reproof"], source_id=source_id, pinned=pinned)
        source_parity = _exact_keys(
            source["source_parity"],
            {
                "ok",
                "candidate_ready",
                "artifact_type",
                "status",
                "path",
                "errors",
                "pinned_resource_count",
                "current_resource_count",
                "classified_resource_count",
            },
            "upstream detector source_parity",
        )
        parity_ok = _boolean(source_parity["ok"], "upstream detector source_parity ok")
        candidate_ready = _boolean(
            source_parity["candidate_ready"],
            "upstream detector source_parity candidate_ready",
        )
        parity_status = source_parity["status"]
        artifact_type = source_parity["artifact_type"]
        if parity_status not in {"invalid", "candidate-ready", "accepted-baseline"}:
            raise GuardError("upstream detector source_parity status is invalid")
        if artifact_type not in {"skill-catalog", "source-inventory", "unknown"}:
            raise GuardError("upstream detector source_parity artifact_type is invalid")
        if artifact_type == "unknown" and parity_status != "invalid":
            raise GuardError("unknown source_parity artifact_type must be invalid")
        if source_parity["path"] != parity_path:
            raise GuardError("upstream detector source_parity path disagrees with its source")
        counts = [
            _count(
                source_parity[key],
                f"upstream detector source_parity {key}",
                maximum=100_000,
            )
            for key in (
                "pinned_resource_count",
                "current_resource_count",
                "classified_resource_count",
            )
        ]
        parity_errors = source_parity["errors"]
        if parity_status == "invalid":
            if parity_ok or candidate_ready or counts != [0, 0, 0]:
                raise GuardError("invalid upstream source_parity has contradictory status")
            if (
                not isinstance(parity_errors, list)
                or len(parity_errors) != 1
                or not isinstance(parity_errors[0], str)
                or not parity_errors[0]
                or parity_errors[0].strip() != parity_errors[0]
                or any(character in parity_errors[0] for character in ("\0", "\r", "\n"))
                or len(parity_errors[0].encode("utf-8")) > 2048
            ):
                raise GuardError("invalid upstream source_parity errors are not bounded")
        elif (
            not parity_ok
            or candidate_ready != (parity_status == "candidate-ready")
            or parity_errors != []
        ):
            raise GuardError("valid upstream source_parity has contradictory status")
        if parity_ok and not drift and parity_status != "accepted-baseline":
            raise GuardError("non-drifting upstream source lacks an accepted parity baseline")
        if source_ok != (not drift and parity_ok):
            raise GuardError("upstream detector source ok disagrees with drift or source parity")
        source_results.append(source_ok)

    requested_source_id = detector["selected_source_id"]
    if requested_source_id is not None:
        if not isinstance(requested_source_id, str) or requested_source_id not in seen_ids:
            raise GuardError("upstream detector selected_source_id is invalid")
        if len(sources) != 1 or sources[0]["id"] != requested_source_id:
            raise GuardError("source-scoped detector returned an ambiguous source inventory")

    preview = _exact_keys(
        detector["bootstrap_preview"],
        {
            "ok",
            "root",
            "dry_run",
            "update_managed",
            "created",
            "updated",
            "pending_updates",
            "stale_managed",
            "unchanged",
            "conflicts",
            "notes",
            "discovery",
        },
        "upstream detector bootstrap_preview",
    )
    for key in ("ok", "dry_run", "update_managed"):
        _boolean(preview[key], f"upstream detector bootstrap_preview {key}")
    if preview["dry_run"] is not True or preview["update_managed"] is not True:
        raise GuardError("upstream detector bootstrap preview is not a managed dry run")
    for key in (
        "created",
        "updated",
        "pending_updates",
        "stale_managed",
        "unchanged",
        "conflicts",
        "notes",
    ):
        if not isinstance(preview[key], list) or not all(
            isinstance(item, str) for item in preview[key]
        ):
            raise GuardError(f"upstream detector bootstrap_preview {key} is invalid")
    if not isinstance(preview["root"], str) or not isinstance(preview["discovery"], dict):
        raise GuardError("upstream detector bootstrap preview metadata is invalid")
    parity = _exact_keys(
        detector["generated_parity"],
        {"ok", "dry_run", "update_managed", "differences"},
        "upstream detector generated_parity",
    )
    parity_ok = _boolean(parity["ok"], "upstream detector generated_parity ok")
    if parity["dry_run"] is not True or parity["update_managed"] is not True:
        raise GuardError("upstream detector parity is not a managed dry run")
    differences = parity["differences"]
    if not isinstance(differences, dict) or not set(differences) <= {
        "created",
        "updated",
        "pending_updates",
        "stale_managed",
        "conflicts",
    }:
        raise GuardError("upstream detector generated parity differences are invalid")
    for category, values in differences.items():
        if not isinstance(values, list) or not values or values != sorted(set(values)):
            raise GuardError(f"upstream detector parity {category} paths are invalid")
        for value in values:
            _normalized_path(value, f"upstream detector parity {category} path")
    if parity_ok != (preview["ok"] is True and not differences):
        raise GuardError("upstream detector generated parity result disagrees")
    if overall_ok != (all(source_results) and parity_ok):
        raise GuardError("upstream detector overall result disagrees")
    drift_sources.sort(key=lambda item: item["source_id"])
    detector["validated_drift_sources"] = drift_sources
    detector["validated_drift_heads"] = [item["expected_head"] for item in drift_sources]
    return detector


def _accepted_review_markers(
    root: Path,
    detector: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    ledger_path = root / detector["review_ledger"]
    _, ledger = _load_json(
        ledger_path,
        maximum=REVIEW_LEDGER_MAX_BYTES,
        label="upstream review ledger",
    )
    _exact_keys(ledger, {"schema_version", "sources"}, "upstream review ledger")
    if ledger["schema_version"] != UPSTREAM_SCHEMA_VERSION:
        raise GuardError("upstream review ledger schema_version changed")
    ledger_sources = ledger["sources"]
    if not isinstance(ledger_sources, list) or len(ledger_sources) != len(detector["sources"]):
        raise GuardError("upstream review ledger source inventory disagrees with detector")
    sources_by_id: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(ledger_sources):
        source = _exact_keys(
            value,
            {
                "id",
                "repository",
                "path",
                "provenance_path",
                "parity_path",
                "genesis",
                "transitions",
            },
            f"upstream review ledger source {index}",
        )
        source_id = source["id"]
        if not isinstance(source_id, str) or not source_id or source_id in sources_by_id:
            raise GuardError("upstream review ledger source id is invalid or duplicated")
        sources_by_id[source_id] = source

    accepted: dict[str, list[dict[str, Any]]] = {}
    for detector_source in detector["sources"]:
        source_id = detector_source["id"]
        source = sources_by_id.get(source_id)
        if source is None:
            raise GuardError("upstream review ledger is missing a detector source")
        for key in ("repository", "path", "provenance_path", "parity_path"):
            if source[key] != detector_source[key]:
                raise GuardError(f"upstream review ledger source {key} disagrees with detector")
        genesis = _identity(source["genesis"], f"upstream review ledger {source_id} genesis")
        if genesis != detector_source["review_reproof"]["genesis"]:
            raise GuardError("upstream review ledger genesis disagrees with detector reproof")
        transitions = source["transitions"]
        expected_count = detector_source["review_reproof"]["transition_count"]
        if (
            not isinstance(transitions, list)
            or len(transitions) != expected_count
            or len(transitions) > REVIEW_TRANSITION_MAX
        ):
            raise GuardError("upstream review ledger transition count disagrees with detector")
        expected_prior = genesis
        markers: list[dict[str, Any]] = []
        for index, value in enumerate(transitions):
            transition = _exact_keys(
                value,
                {"prior", "new", "inventory_sha256", "dispositions"},
                f"upstream review ledger transition {index}",
            )
            prior = _identity(
                transition["prior"],
                f"upstream review ledger transition {index} prior",
            )
            new = _identity(
                transition["new"],
                f"upstream review ledger transition {index} new",
            )
            if prior != expected_prior or new == prior:
                raise GuardError("upstream review ledger transition chain is not contiguous")
            expected_prior = new
            digest = _sha256(
                transition["inventory_sha256"],
                f"upstream review ledger transition {index} inventory_sha256",
            )
            dispositions = transition["dispositions"]
            if not isinstance(dispositions, list) or len(dispositions) > 100:
                raise GuardError("upstream review ledger dispositions are not bounded")
            disposition_paths: list[str] = []
            for disposition_index, disposition_value in enumerate(dispositions):
                disposition = _exact_keys(
                    disposition_value,
                    {"path", "disposition", "rationale"},
                    f"upstream review ledger disposition {disposition_index}",
                )
                disposition_paths.append(
                    _normalized_path(
                        disposition["path"],
                        f"upstream review ledger disposition {disposition_index} path",
                    )
                )
                if disposition["disposition"] not in {"A", "B", "C"}:
                    raise GuardError("upstream review ledger disposition is invalid")
                rationale = disposition["rationale"]
                if (
                    not isinstance(rationale, str)
                    or not rationale
                    or rationale.strip() != rationale
                    or any(character in rationale for character in ("\0", "\r", "\n"))
                    or len(rationale.encode("utf-8")) > 2048
                ):
                    raise GuardError("upstream review ledger rationale is invalid")
            if disposition_paths != sorted(set(disposition_paths)):
                raise GuardError("upstream review ledger dispositions are not sorted and unique")
            markers.append(
                {
                    "source_id": source_id,
                    "repository": source["repository"],
                    "path": source["path"],
                    "prior": prior,
                    "new": new,
                    "inventory_sha256": digest,
                }
            )
        if expected_prior != detector_source["pinned"]:
            raise GuardError("upstream review ledger tip disagrees with detector pin")
        accepted[source_id] = markers
    return accepted


def _review_marker_payload(line: str, *, label: str) -> dict[str, Any]:
    prefix = "<!-- pk-stack-upstream-review: "
    suffix = " -->"
    if not line.startswith(prefix) or not line.endswith(suffix) or len(line) > 4096:
        raise GuardError(f"{label} is malformed")
    try:
        payload = json.loads(
            line[len(prefix) : -len(suffix)],
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise GuardError(f"{label} is not strict JSON: {exc}") from exc
    marker = _exact_keys(
        payload,
        {"source_id", "repository", "path", "prior", "new", "inventory_sha256"},
        label,
    )
    if not all(
        isinstance(marker[key], str) and marker[key] for key in ("source_id", "repository", "path")
    ):
        raise GuardError(f"{label} source fields are invalid")
    _identity(marker["prior"], f"{label} prior")
    _identity(marker["new"], f"{label} new")
    _sha256(marker["inventory_sha256"], f"{label} inventory_sha256")
    canonical = json.dumps(marker, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if line != f"{prefix}{canonical}{suffix}":
        raise GuardError(f"{label} is not canonical")
    return marker


def _provenance_marker_lines(path: Path) -> tuple[list[str], list[tuple[int, str]]]:
    if path.is_symlink() or not path.is_file():
        raise GuardError(f"upstream provenance must be a regular file: {path}")
    raw = path.read_bytes()
    if len(raw) > REVIEW_LEDGER_MAX_BYTES:
        raise GuardError("upstream provenance exceeds the 8 MiB limit")
    try:
        lines = raw.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError as exc:
        raise GuardError("upstream provenance is not UTF-8") from exc
    markers: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        content = line.rstrip("\r\n")
        if "pk-stack-upstream-review:" in content:
            markers.append((index, content))
    return lines, markers


def _pending_review_marker(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source["id"],
        "repository": source["repository"],
        "path": source["path"],
        "prior": source["pinned"],
        "new": source["current"],
        "inventory_sha256": source["comparison"]["inventory_sha256"],
    }


def _cleanup_unaccepted_provenance_tail(root: Path, detector: dict[str, Any]) -> None:
    accepted = _accepted_review_markers(root, detector)
    for source in detector["sources"]:
        path = root / source["provenance_path"]
        lines, marker_lines = _provenance_marker_lines(path)
        expected = accepted[source["id"]]
        if len(marker_lines) < len(expected):
            raise GuardError("upstream provenance is missing an accepted review marker")
        for index, marker in enumerate(expected):
            actual = _review_marker_payload(
                marker_lines[index][1],
                label=f"accepted upstream provenance marker {index}",
            )
            if actual != marker:
                raise GuardError("accepted upstream provenance marker was deleted or replaced")
        extras = len(marker_lines) - len(expected)
        if extras == 0:
            continue
        if extras != 1 or source["drift"] is not True:
            raise GuardError("upstream provenance has more than one unaccepted tail marker")
        del lines[marker_lines[-1][0]]
        path.write_bytes("".join(lines).encode("utf-8"))


def _require_provenance_markers(
    root: Path,
    detector: dict[str, Any],
    *,
    selected_source_id: str | None,
) -> None:
    accepted = _accepted_review_markers(root, detector)
    for source in detector["sources"]:
        _, marker_lines = _provenance_marker_lines(root / source["provenance_path"])
        expected = list(accepted[source["id"]])
        if selected_source_id is not None and source["id"] == selected_source_id:
            if source["drift"] is not True:
                raise GuardError("selected upstream source no longer has detected drift")
            expected.append(_pending_review_marker(source))
        if len(marker_lines) != len(expected):
            raise GuardError("upstream provenance marker count disagrees with review state")
        for index, marker in enumerate(expected):
            actual = _review_marker_payload(
                marker_lines[index][1],
                label=f"upstream provenance marker {index}",
            )
            if actual != marker:
                raise GuardError(
                    "upstream provenance markers do not match accepted history and proposal"
                )


def validate_proposal(root: Path, detector_path: Path, proposal_path: Path) -> dict[str, Any]:
    """Independently bind an untrusted proposal to the exact detector inventory."""

    detector = validate_detector(detector_path)
    drift_sources = sorted(
        (source for source in detector["sources"] if source["drift"] is True),
        key=lambda item: item["id"],
    )
    if not drift_sources:
        raise GuardError("an acceptance proposal requires detected upstream drift")
    _, proposal = _load_json(
        proposal_path,
        maximum=512 * 1024,
        label="upstream acceptance proposal",
    )
    _exact_keys(
        proposal,
        {"source_id", "prior", "new", "inventory_sha256", "dispositions"},
        "upstream acceptance proposal",
    )
    source_id = proposal["source_id"]
    if not isinstance(source_id, str) or not source_id:
        raise GuardError("upstream acceptance proposal source_id is invalid")
    source = drift_sources[0]
    if source_id != source["id"]:
        raise GuardError(
            "upstream acceptance proposal did not select the lexicographically first drift source"
        )
    prior = _identity(proposal["prior"], "upstream acceptance proposal prior")
    new = _identity(proposal["new"], "upstream acceptance proposal new")
    if prior != source["pinned"]:
        raise GuardError("upstream acceptance proposal prior identity is stale")
    if new != source["current"]:
        raise GuardError("upstream acceptance proposal new identity is not the current head")
    inventory_sha256 = _sha256(
        proposal["inventory_sha256"],
        "upstream acceptance proposal inventory_sha256",
    )
    comparison = source["comparison"]
    if inventory_sha256 != comparison["inventory_sha256"]:
        raise GuardError("upstream acceptance proposal inventory digest does not match reproof")

    dispositions = proposal["dispositions"]
    if not isinstance(dispositions, list) or len(dispositions) > 100:
        raise GuardError("upstream acceptance proposal dispositions are not bounded")
    by_path: dict[str, str] = {}
    for index, value in enumerate(dispositions):
        item = _exact_keys(
            value,
            {"path", "disposition", "rationale"},
            f"upstream acceptance proposal disposition {index}",
        )
        path = _normalized_path(
            item["path"],
            f"upstream acceptance proposal disposition {index} path",
        )
        if path in by_path:
            raise GuardError("upstream acceptance proposal contains a duplicate path")
        disposition = item["disposition"]
        if disposition not in {"A", "B", "C"}:
            raise GuardError("upstream acceptance proposal disposition must be A, B, or C")
        rationale = item["rationale"]
        if (
            not isinstance(rationale, str)
            or not rationale
            or rationale.strip() != rationale
            or any(character in rationale for character in ("\0", "\r", "\n"))
            or len(rationale.encode("utf-8")) > 2048
        ):
            raise GuardError("upstream acceptance proposal rationale is invalid")
        by_path[path] = disposition
    if sorted(by_path) != comparison["paths"]:
        raise GuardError(
            "upstream acceptance proposal dispositions do not exactly match comparison paths"
        )
    unavailable = comparison["review_constraints"]["unavailable_binary_paths"]
    if any(by_path.get(path) != "B" for path in unavailable):
        raise GuardError("unavailable binary paths require disposition B")
    _require_provenance_markers(
        root,
        detector,
        selected_source_id=source_id,
    )
    return {
        "source_id": source["id"],
        "expected_head": new["commit"],
        "disposition_count": len(dispositions),
    }


def validate_serialized_acceptance(
    root: Path,
    base_sha: str,
    before_path: Path,
    after_path: Path,
) -> dict[str, Any]:
    """Prove exactly the deterministically selected source advanced once."""

    _sha1(base_sha, "serialized acceptance base")
    before = validate_detector(before_path)
    after = validate_detector(after_path)
    before_drift = before["validated_drift_sources"]
    if not before_drift:
        raise GuardError("serialized acceptance requires initial upstream drift")
    if before["selected_source_id"] is not None or after["selected_source_id"] is not None:
        raise GuardError("serialized acceptance requires full-manifest detector evidence")
    selected_id = before_drift[0]["source_id"]
    selected_head = before_drift[0]["expected_head"]
    before_sources = {source["id"]: source for source in before["sources"]}
    after_sources = {source["id"]: source for source in after["sources"]}
    if set(after_sources) != set(before_sources):
        raise GuardError("serialized acceptance changed the upstream source inventory")

    stable_fields = ("repository", "path", "ref", "provenance_path", "parity_path")
    for source_id, before_source in before_sources.items():
        after_source = after_sources[source_id]
        if any(after_source[key] != before_source[key] for key in stable_fields):
            raise GuardError("serialized acceptance changed upstream source metadata")
        before_review = before_source["review_reproof"]
        after_review = after_source["review_reproof"]
        if source_id != selected_id:
            if (
                after_source["pinned"] != before_source["pinned"]
                or after_review != before_review
                or after_source["source_parity"] != before_source["source_parity"]
            ):
                raise GuardError("serialized acceptance modified a deferred upstream source")
            continue

        if after_source["pinned"] != before_source["current"]:
            raise GuardError("serialized acceptance did not advance the selected pin exactly")
        if after_source["pinned"]["commit"] != selected_head:
            raise GuardError("serialized acceptance selected head changed")
        if after_review["genesis"] != before_review["genesis"]:
            raise GuardError("serialized acceptance changed selected source genesis")
        before_count = before_review["transition_count"]
        if after_review["transition_count"] != before_count + 1:
            raise GuardError("serialized acceptance did not append exactly one review transition")
        transitions = after_review["transitions"]
        if len(transitions) != 1:
            raise GuardError("serialized acceptance is missing its latest transition reproof")
        latest = transitions[0]
        if (
            latest["index"] != before_count
            or latest["prior"] != before_source["pinned"]
            or latest["new"] != before_source["current"]
            or latest["inventory_sha256"] != before_source["comparison"]["inventory_sha256"]
            or latest["path_count"] != before_source["comparison"]["path_count"]
        ):
            raise GuardError("serialized acceptance latest transition is not detector-bound")
        selected_parity = after_source["source_parity"]
        if (
            selected_parity["ok"] is not True
            or selected_parity["candidate_ready"] is not False
            or selected_parity["status"] != "accepted-baseline"
        ):
            raise GuardError("serialized acceptance did not establish selected parity baseline")

    _require_provenance_markers(
        root,
        after,
        selected_source_id=None,
    )
    for source_id, source in before_sources.items():
        if source_id == selected_id:
            continue
        provenance_path = source["provenance_path"]
        candidate = root / provenance_path
        try:
            base_provenance = _git_bytes(root, "show", f"{base_sha}:{provenance_path}")
        except subprocess.CalledProcessError as exc:
            raise GuardError(
                "deferred upstream provenance is missing from the base commit"
            ) from exc
        if candidate.read_bytes() != base_provenance:
            raise GuardError("serialized acceptance modified deferred upstream provenance")
    return {
        "source_id": selected_id,
        "accepted_head": selected_head,
        "initial_drift_count": len(before_drift),
        "remaining_drift_count": len(after["validated_drift_sources"]),
    }


def _goal_status(path: Path) -> dict[str, Any]:
    _, status_payload = _load_json(path, maximum=131_072, label="goal status")
    goal = status_payload.get("goal")
    if status_payload.get("ok") is not True or not isinstance(goal, dict):
        raise GuardError("goal status is not successful")
    if goal.get("status") != "passed" or goal.get("attempt_count") not in {2, 3, 4, 5}:
        raise GuardError("goal did not reach passed within the five-attempt budget")
    if goal.get("max_attempts") != 5:
        raise GuardError("goal max_attempts changed from the immutable budget")
    return goal


def package_candidate(
    root: Path,
    base_sha: str,
    policy_path: Path,
    policy_raw: bytes,
    policy: dict[str, Any],
    detector_path: Path,
    goal_status_path: Path,
    output_path: Path,
    *,
    source_workflow: str,
    source_run_id: str,
    provider: str,
) -> dict[str, Any]:
    summary = validate_boundary(root, base_sha, policy, scope="final", stage=True)
    validate_product_envelope(root)
    detector = validate_detector(detector_path)
    goal = _goal_status(goal_status_path)
    configured = {item["provider"]: item["name"] for item in policy["source_workflows"]}
    if configured.get(provider) != source_workflow:
        raise GuardError("candidate provider and source workflow do not match policy")
    files: list[dict[str, Any]] = []
    for path in summary["paths"]:
        record = _git_text(root, "ls-files", "--stage", "--", path).strip()
        if not record:
            files.append({"path": path, "deleted": True})
            continue
        mode, _, stage_and_path = record.split(" ", 2)
        stage, recorded_path = stage_and_path.split("\t", 1)
        if stage != "0" or recorded_path != path:
            raise GuardError(f"unexpected staged candidate record: {path}")
        content = _git_bytes(root, "show", f":{path}")
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise GuardError(f"candidate file is not UTF-8 text: {path}") from exc
        if b"\0" in content:
            raise GuardError(f"candidate file contains NUL bytes: {path}")
        files.append(
            {
                "path": path,
                "deleted": False,
                "mode": mode,
                "sha256": hashlib.sha256(content).hexdigest(),
                "content_base64": base64.b64encode(content).decode("ascii"),
            }
        )
    upstreams = [
        {
            "id": source["id"],
            "repository": source["repository"],
            "path": source["path"],
            "ref": source["ref"],
            "previous_commit": source["pinned"]["commit"],
            "previous_subtree_sha": source["pinned"]["subtree_sha"],
            "current_commit": source["current"]["commit"],
            "current_subtree_sha": source["current"]["subtree_sha"],
        }
        for source in detector["sources"]
    ]
    payload = {
        "schema_version": 1,
        "provider": provider,
        "source_workflow": source_workflow,
        "source_run_id": source_run_id,
        "base_sha": base_sha,
        "policy_path": policy_path.relative_to(root).as_posix(),
        "policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
        "goal": {
            "goal_id": goal.get("goal_id"),
            "status": goal["status"],
            "attempt_count": goal["attempt_count"],
            "max_attempts": goal["max_attempts"],
        },
        "upstreams": upstreams,
        "diff": {key: value for key, value in summary.items() if key != "paths"},
        "files": files,
    }
    raw = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    maximum = policy["limits"]["max_candidate_package_bytes"]
    if len(raw) > maximum:
        raise GuardError("candidate package exceeds its encoded size limit")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(raw)
    package_digest = hashlib.sha256(raw).hexdigest()
    return {
        **summary,
        "package_sha256": package_digest,
        "package_bytes": len(raw),
        "has_changes": bool(files),
    }


def validate_package(
    root: Path,
    base_sha: str,
    policy_raw: bytes,
    policy: dict[str, Any],
    package_path: Path,
    *,
    expected_digest: str,
    source_workflow: str,
    source_run_id: str,
    provider: str,
) -> dict[str, Any]:
    raw, package = _load_json(
        package_path,
        maximum=policy["limits"]["max_candidate_package_bytes"],
        label="candidate package",
    )
    _exact_keys(
        package,
        {
            "schema_version",
            "provider",
            "source_workflow",
            "source_run_id",
            "base_sha",
            "policy_path",
            "policy_sha256",
            "goal",
            "upstreams",
            "diff",
            "files",
        },
        "candidate package",
    )
    _sha256(expected_digest, "candidate package expected digest")
    _sha1(base_sha, "candidate package expected base")
    if hashlib.sha256(raw).hexdigest() != expected_digest:
        raise GuardError("candidate package digest does not match the artifact output")
    expected = {
        "schema_version": 1,
        "provider": provider,
        "source_workflow": source_workflow,
        "source_run_id": source_run_id,
        "base_sha": base_sha,
        "policy_path": ".github/pk-stack-maintenance-policy.json",
        "policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
    }
    for key, value in expected.items():
        if package.get(key) != value:
            raise GuardError(f"candidate package metadata mismatch: {key}")
    goal = _exact_keys(
        package["goal"],
        {"goal_id", "status", "attempt_count", "max_attempts"},
        "candidate package goal",
    )
    if (
        not isinstance(goal["goal_id"], str)
        or not goal["goal_id"]
        or goal["status"] != "passed"
        or goal["attempt_count"] not in {2, 3, 4, 5}
        or goal["max_attempts"] != 5
    ):
        raise GuardError("candidate package goal is not a bounded verified goal")
    upstreams = package["upstreams"]
    if not isinstance(upstreams, list) or not 1 <= len(upstreams) <= 16:
        raise GuardError("candidate package upstream inventory is invalid")
    upstream_ids: set[str] = set()
    for index, upstream_value in enumerate(upstreams):
        upstream = _exact_keys(
            upstream_value,
            {
                "id",
                "repository",
                "path",
                "ref",
                "previous_commit",
                "previous_subtree_sha",
                "current_commit",
                "current_subtree_sha",
            },
            f"candidate package upstream {index}",
        )
        source_id = upstream["id"]
        if not isinstance(source_id, str) or not source_id or source_id in upstream_ids:
            raise GuardError("candidate package upstream id is invalid or duplicated")
        upstream_ids.add(source_id)
        repository = upstream["repository"]
        if not isinstance(repository, str) or repository.count("/") != 1:
            raise GuardError("candidate package upstream repository is invalid")
        _normalized_path(upstream["path"], "candidate package upstream path")
        if not isinstance(upstream["ref"], str) or not upstream["ref"]:
            raise GuardError("candidate package upstream ref is invalid")
        for field in (
            "previous_commit",
            "previous_subtree_sha",
            "current_commit",
            "current_subtree_sha",
        ):
            _sha1(upstream[field], f"candidate package upstream {field}")
    diff = _exact_keys(
        package["diff"],
        {"changed_files", "changed_lines", "patch_bytes", "patch_sha256"},
        "candidate package diff",
    )
    _count(diff["changed_files"], "candidate package changed_files")
    _count(diff["changed_lines"], "candidate package changed_lines")
    _count(diff["patch_bytes"], "candidate package patch_bytes")
    _sha256(diff["patch_sha256"], "candidate package patch_sha256")
    files = package.get("files")
    if not isinstance(files, list) or not files:
        raise GuardError("candidate package must contain at least one file")
    if len(files) > policy["limits"]["max_changed_files"]:
        raise GuardError("candidate package exceeds the changed-file limit")
    exact = set(policy["final_allowed_exact"])
    prefixes = policy["final_allowed_prefixes"]
    seen: set[str] = set()
    decoded: list[tuple[str, str | None, bytes | None]] = []
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise GuardError("candidate package file entry is malformed")
        path = entry["path"]
        _validate_path(path)
        if path in seen or _is_protected(path, policy) or not _matches(path, exact, prefixes):
            raise GuardError(f"candidate package path is outside policy: {path}")
        seen.add(path)
        if entry.get("deleted") is True:
            if set(entry) != {"path", "deleted"}:
                raise GuardError(f"deleted candidate entry has extra fields: {path}")
            decoded.append((path, None, None))
            continue
        if set(entry) != {"path", "deleted", "mode", "sha256", "content_base64"}:
            raise GuardError(f"candidate package file fields are invalid: {path}")
        if entry["deleted"] is not False:
            raise GuardError(f"candidate package deleted flag is invalid: {path}")
        mode = entry["mode"]
        expected_mode = "100755" if path in EXECUTABLE_PATHS else "100644"
        if mode != expected_mode:
            raise GuardError(f"candidate package mode is invalid: {path}")
        try:
            content = base64.b64decode(entry["content_base64"], validate=True)
            content.decode("utf-8")
        except (TypeError, ValueError, UnicodeDecodeError) as exc:
            raise GuardError(f"candidate package content is invalid: {path}") from exc
        if b"\0" in content or hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise GuardError(f"candidate package content hash is invalid: {path}")
        decoded.append((path, mode, content))
    if sorted(seen) != sorted(entry["path"] for entry in files):
        raise GuardError("candidate package paths are not unique")

    with tempfile.TemporaryDirectory(prefix="pk-stack-index-") as temporary:
        index_path = Path(temporary) / "index"
        index_env = os.environ.copy()
        index_env["GIT_INDEX_FILE"] = str(index_path)
        _git_run(root, "read-tree", base_sha, env=index_env)
        for path, mode, content in decoded:
            if content is None:
                _git_run(
                    root,
                    "update-index",
                    "--force-remove",
                    "--",
                    path,
                    env=index_env,
                )
                continue
            object_sha = (
                _git_run(
                    root,
                    "hash-object",
                    "-w",
                    "--stdin",
                    input_bytes=content,
                )
                .stdout.decode("ascii")
                .strip()
            )
            _git_run(
                root,
                "update-index",
                "--add",
                "--cacheinfo",
                f"{mode},{object_sha},{path}",
                env=index_env,
            )
        summary = _validate_staged_diff(
            root,
            base_sha,
            policy,
            expected_paths=sorted(seen),
            index_env=index_env,
        )
    if package.get("diff") != {key: value for key, value in summary.items() if key != "paths"}:
        raise GuardError("candidate package diff summary does not match reconstructed content")
    return {**summary, "package_sha256": expected_digest}


def build_candidate_review_bundle(
    root: Path,
    base_sha: str,
    head_sha: str,
    policy: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Create a deterministic, non-executable exact-commit review input."""

    _sha1(base_sha, "candidate review base")
    _sha1(head_sha, "candidate review head")
    if _git_text(root, "rev-parse", "HEAD").strip() != head_sha:
        raise GuardError("candidate review checkout is not the expected candidate head")
    parents = _git_text(root, "rev-list", "--parents", "-n", "1", head_sha).split()
    if parents != [head_sha, base_sha]:
        raise GuardError("candidate review candidate is not exactly one commit atop base")
    if _git_text(root, "rev-list", "--count", f"{base_sha}..{head_sha}").strip() != "1":
        raise GuardError("candidate review commit count changed")
    if _git_bytes(
        root,
        "diff",
        "--name-only",
        "-z",
        "--diff-filter=RC",
        "--find-renames",
        "--find-copies",
        f"{base_sha}..{head_sha}",
    ):
        raise GuardError("candidate review contains a rename or copy")
    raw_paths = _git_bytes(
        root,
        "diff",
        "--name-only",
        "-z",
        "--no-renames",
        f"{base_sha}..{head_sha}",
    )
    paths = sorted(item.decode("utf-8", errors="strict") for item in raw_paths.split(b"\0") if item)
    if not paths or len(paths) > policy["limits"]["max_changed_files"]:
        raise GuardError("candidate review file count is outside policy")
    exact = set(policy["final_allowed_exact"])
    prefixes = policy["final_allowed_prefixes"]
    for path in paths:
        _validate_path(path)
        if _is_protected(path, policy) or not _matches(path, exact, prefixes):
            raise GuardError(f"candidate review path is outside final policy: {path}")
        exists = _git_run(root, "cat-file", "-e", f"{head_sha}:{path}", check=False)
        if exists.returncode != 0:
            continue
        record = _git_bytes(root, "ls-tree", "-z", head_sha, "--", path).rstrip(b"\0")
        if not record:
            raise GuardError(f"candidate review tree entry is missing: {path}")
        metadata, encoded_path = record.split(b"\t", 1)
        mode, object_type, _ = metadata.split(b" ", 2)
        expected_mode = b"100755" if path in EXECUTABLE_PATHS else b"100644"
        if encoded_path.decode("utf-8", errors="strict") != path:
            raise GuardError(f"candidate review tree path changed: {path}")
        if object_type != b"blob" or mode != expected_mode:
            raise GuardError(f"candidate review object or mode is invalid: {path}")
        content = _git_bytes(root, "show", f"{head_sha}:{path}")
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise GuardError(f"candidate review content is not UTF-8 text: {path}") from exc
        if b"\0" in content:
            raise GuardError(f"candidate review content contains NUL bytes: {path}")

    changed_lines = 0
    for line in _git_text(
        root,
        "diff",
        "--numstat",
        "--no-renames",
        f"{base_sha}..{head_sha}",
    ).splitlines():
        additions, deletions, _ = line.split("\t", 2)
        if additions == "-" or deletions == "-":
            raise GuardError("candidate review contains a binary diff")
        changed_lines += int(additions) + int(deletions)
    if changed_lines > policy["limits"]["max_changed_lines"]:
        raise GuardError("candidate review changed-line count exceeds policy")
    patch = _git_bytes(
        root,
        "diff",
        "--binary",
        "--no-ext-diff",
        "--no-renames",
        f"{base_sha}..{head_sha}",
        "--",
    )
    if len(patch) > policy["limits"]["max_patch_bytes"]:
        raise GuardError("candidate review patch exceeds policy")
    try:
        patch_text = patch.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GuardError("candidate review patch is not UTF-8 text") from exc
    patch_sha256 = hashlib.sha256(patch).hexdigest()
    paths_sha256 = hashlib.sha256(
        json.dumps(paths, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()
    bundle = {
        "schema_version": 1,
        "review_type": "mandatory-independent-exact-candidate",
        "base_sha": base_sha,
        "head_sha": head_sha,
        "requires_review": True,
        "changed_files": len(paths),
        "changed_lines": changed_lines,
        "paths": paths,
        "paths_sha256": paths_sha256,
        "patch_sha256": patch_sha256,
        "patch": patch_text,
    }
    raw = (json.dumps(bundle, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(raw) > policy["limits"]["max_patch_bytes"] * 2 + 65_536:
        raise GuardError("candidate review bundle exceeds its encoded size limit")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(raw)
    return {
        "base_sha": base_sha,
        "head_sha": head_sha,
        "content_sha256": hashlib.sha256(raw).hexdigest(),
        "patch_sha256": patch_sha256,
        "paths_sha256": paths_sha256,
        "changed_files": len(paths),
    }


def validate_fable_verdict(
    verdict_path: Path,
    execution_path: Path,
    policy: dict[str, Any],
    *,
    base_sha: str,
    head_sha: str,
    content_sha256: str,
    patch_sha256: str,
) -> dict[str, Any]:
    raw, verdict = _load_json(verdict_path, maximum=131_072, label="Fable review verdict")
    _exact_keys(
        verdict,
        {
            "verdict",
            "reviewed_base_sha",
            "reviewed_head_sha",
            "reviewed_content_sha256",
            "reviewed_patch_sha256",
            "material_findings",
            "summary",
        },
        "Fable review verdict",
    )
    _sha1(base_sha, "Fable verdict expected base")
    _sha1(head_sha, "Fable verdict expected head")
    _sha256(content_sha256, "Fable verdict expected content digest")
    _sha256(patch_sha256, "Fable verdict expected patch digest")
    expected = {
        "reviewed_base_sha": base_sha,
        "reviewed_head_sha": head_sha,
        "reviewed_content_sha256": content_sha256,
        "reviewed_patch_sha256": patch_sha256,
    }
    for key, value in expected.items():
        if verdict[key] != value:
            raise GuardError(f"Fable verdict is not bound to exact {key}")
    findings = verdict["material_findings"]
    if (
        not isinstance(findings, list)
        or len(findings) > 32
        or not all(
            isinstance(item, str) and item == item.strip() and 1 <= len(item) <= 2000
            for item in findings
        )
    ):
        raise GuardError("Fable verdict material findings are malformed")
    summary = verdict["summary"]
    if not isinstance(summary, str) or summary != summary.strip() or not 1 <= len(summary) <= 4000:
        raise GuardError("Fable verdict summary is malformed")
    if verdict["verdict"] != "approved" or findings:
        raise GuardError("Fable did not approve the exact candidate without material findings")
    execution_raw, messages = _load_json_array(
        execution_path,
        maximum=32 * 1024 * 1024,
        label="Fable execution evidence",
    )
    if not 1 <= len(messages) <= 4096 or not all(isinstance(item, dict) for item in messages):
        raise GuardError("Fable execution evidence has an invalid message inventory")
    init_messages = [
        item for item in messages if item.get("type") == "system" and item.get("subtype") == "init"
    ]
    result_messages = [item for item in messages if item.get("type") == "result"]
    if len(init_messages) != 1 or len(result_messages) != 1:
        raise GuardError("Fable execution evidence must contain exactly one init and one result")
    expected_model = "claude-fable-5-1"
    if init_messages[0].get("model") != expected_model:
        raise GuardError("Fable execution init did not resolve the required model")
    result = result_messages[0]
    if result.get("subtype") != "success" or result.get("is_error") is not False:
        raise GuardError("Fable execution result was not successful")
    model_usage = result.get("modelUsage")
    allowed_usage_models = {expected_model, FABLE_INTERNAL_COMPANION_MODEL}
    if (
        not isinstance(model_usage, dict)
        or expected_model not in model_usage
        or not set(model_usage) <= allowed_usage_models
    ):
        raise GuardError("Fable execution modelUsage is missing, mixed, or unexpected")
    reviewer_usage = model_usage[expected_model]
    if not isinstance(reviewer_usage, dict):
        raise GuardError("Fable execution modelUsage entry is malformed")
    if reviewer_usage.get("canonicalModel", expected_model) != expected_model:
        raise GuardError("Fable reviewer usage did not resolve the required canonical model")
    companion_usage = model_usage.get(FABLE_INTERNAL_COMPANION_MODEL)
    if companion_usage is not None:
        # Claude Code 2.1.258 emits this tiny first-party routing/classification
        # companion beside the requested reviewer. Bind its exact version and
        # keep it decisively below a substantive review turn; every other model
        # key remains forbidden.
        if not isinstance(companion_usage, dict):
            raise GuardError("Fable internal companion usage entry is malformed")
        allowed_companion_fields = {
            "inputTokens",
            "outputTokens",
            "cacheReadInputTokens",
            "cacheCreationInputTokens",
            "webSearchRequests",
            "costUSD",
            "contextWindow",
            "maxOutputTokens",
            "thinkingTokens",
            "canonicalModel",
            "provider",
            "costBasis",
        }
        required_companion_fields = {
            "inputTokens",
            "outputTokens",
            "cacheReadInputTokens",
            "cacheCreationInputTokens",
            "webSearchRequests",
            "costUSD",
            "canonicalModel",
            "provider",
        }
        if (
            not required_companion_fields <= set(companion_usage) <= allowed_companion_fields
            or companion_usage.get("canonicalModel") != "claude-haiku-4-5"
            or companion_usage.get("provider") != "firstParty"
        ):
            raise GuardError("Fable internal companion identity is unexpected")
        bounded_counts = {
            "inputTokens": 2048,
            "outputTokens": 64,
            "cacheReadInputTokens": 0,
            "cacheCreationInputTokens": 0,
            "webSearchRequests": 0,
            "thinkingTokens": 0,
        }
        for field, maximum in bounded_counts.items():
            value = companion_usage.get(field, 0)
            if type(value) is not int or not 0 <= value <= maximum:
                raise GuardError("Fable internal companion usage exceeded its inert bound")
        cost = companion_usage["costUSD"]
        if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not 0 <= cost <= 0.01:
            raise GuardError("Fable internal companion cost exceeded its inert bound")
    if result.get("structured_output") != verdict:
        raise GuardError("Fable execution evidence does not contain the exact structured verdict")
    execution_sha256 = hashlib.sha256(execution_raw).hexdigest()
    verdict_sha256 = hashlib.sha256(raw).hexdigest()
    attestation = {
        "base_sha": base_sha,
        "head_sha": head_sha,
        "content_sha256": content_sha256,
        "patch_sha256": patch_sha256,
        "execution_sha256": execution_sha256,
        "verdict_sha256": verdict_sha256,
        "model": expected_model,
        # Effort has no provider-returned metadata. Its evidence is the immutable
        # workflow argument validated by static controls, not a model-authored echo.
        "configured_effort": "xhigh",
    }
    return {
        "reviewed_base_sha": base_sha,
        "reviewed_head_sha": head_sha,
        "reviewed_content_sha256": content_sha256,
        "reviewed_patch_sha256": patch_sha256,
        "execution_evidence_sha256": execution_sha256,
        "verdict_sha256": verdict_sha256,
        "attestation_sha256": hashlib.sha256(
            json.dumps(attestation, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "approved": True,
    }


def _write_outputs(path: str | None, values: dict[str, Any]) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as output:
        for key, value in values.items():
            if isinstance(value, bool):
                rendered = "true" if value else "false"
            elif isinstance(value, (str, int)):
                rendered = str(value)
            else:
                continue
            output.write(f"{key}={rendered}\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path(".github/pk-stack-maintenance-policy.json"),
    )
    parser.add_argument("--github-output")
    commands = parser.add_subparsers(dest="command", required=True)

    validate_agent = commands.add_parser("validate-ci-agent")
    validate_agent.add_argument("--agent", type=Path, required=True)

    boundary = commands.add_parser("boundary")
    boundary.add_argument("--base", required=True)
    boundary.add_argument("--scope", choices=("agent", "final"), required=True)
    boundary.add_argument("--stage", action="store_true")

    restore = commands.add_parser("restore-generated")
    restore.add_argument("--base", required=True)

    snapshot = commands.add_parser("validate-trusted-snapshot")
    snapshot.add_argument("--base", required=True)
    snapshot.add_argument("--trusted-root", type=Path, required=True)

    prepare = commands.add_parser("prepare-attempt")
    prepare.add_argument("--base", required=True)
    prepare.add_argument("--detector", type=Path, required=True)
    prepare.add_argument("--feedback", type=Path, required=True)
    prepare.add_argument("--git-state", type=Path, required=True)

    close = commands.add_parser("close-attempt")
    close.add_argument("--base", required=True)
    close.add_argument("--git-state", type=Path, required=True)

    git_state = commands.add_parser("validate-git-state")
    git_state.add_argument("--base", required=True)
    git_state.add_argument("--git-state", type=Path, required=True)

    finalize_git = commands.add_parser("finalize-git-state")
    finalize_git.add_argument("--base", required=True)
    finalize_git.add_argument("--git-state", type=Path, required=True)

    detector = commands.add_parser("validate-detector")
    detector.add_argument("--detector", type=Path, required=True)

    proposal = commands.add_parser("validate-proposal")
    proposal.add_argument("--detector", type=Path, required=True)
    proposal.add_argument("--proposal", type=Path, required=True)

    serialized = commands.add_parser("validate-serialized-acceptance")
    serialized.add_argument("--base", required=True)
    serialized.add_argument("--before-detector", type=Path, required=True)
    serialized.add_argument("--after-detector", type=Path, required=True)

    package = commands.add_parser("package")
    package.add_argument("--base", required=True)
    package.add_argument("--detector", type=Path, required=True)
    package.add_argument("--goal-status", type=Path, required=True)
    package.add_argument("--output", type=Path, required=True)
    package.add_argument("--source-workflow", required=True)
    package.add_argument("--source-run-id", required=True)
    package.add_argument("--provider", choices=("kiro",), required=True)

    check_package = commands.add_parser("validate-package")
    check_package.add_argument("--base", required=True)
    check_package.add_argument("--package", type=Path, required=True)
    check_package.add_argument("--expected-digest", required=True)
    check_package.add_argument("--source-workflow", required=True)
    check_package.add_argument("--source-run-id", required=True)
    check_package.add_argument("--provider", choices=("kiro",), required=True)

    review_bundle = commands.add_parser("build-candidate-review-bundle")
    review_bundle.add_argument("--base", required=True)
    review_bundle.add_argument("--head", required=True)
    review_bundle.add_argument("--output", type=Path, required=True)

    fable_verdict = commands.add_parser("validate-fable-verdict")
    fable_verdict.add_argument("--verdict", type=Path, required=True)
    fable_verdict.add_argument("--execution-file", type=Path, required=True)
    fable_verdict.add_argument("--base", required=True)
    fable_verdict.add_argument("--head", required=True)
    fable_verdict.add_argument("--content-sha256", required=True)
    fable_verdict.add_argument("--patch-sha256", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = args.root.resolve()
    policy_path = args.policy if args.policy.is_absolute() else root / args.policy
    policy_raw, policy = load_policy(policy_path)
    result: dict[str, Any]
    if args.command == "validate-ci-agent":
        agent_path = args.agent if args.agent.is_absolute() else root / args.agent
        validate_ci_agent(agent_path, policy)
        result = {"ok": True, "agent": agent_path.as_posix()}
    elif args.command == "boundary":
        result = validate_boundary(
            root,
            args.base,
            policy,
            scope=args.scope,
            stage=args.stage,
        )
        if args.scope == "final":
            validate_product_envelope(root)
        result["ok"] = True
    elif args.command == "restore-generated":
        restore_generated(root, args.base)
        result = {"ok": True}
    elif args.command == "validate-trusted-snapshot":
        trusted_root = (
            args.trusted_root if args.trusted_root.is_absolute() else root / args.trusted_root
        )
        validate_trusted_snapshot(root, args.base, trusted_root.resolve())
        result = {"ok": True}
    elif args.command == "prepare-attempt":
        prepare_attempt(
            root,
            args.base,
            policy,
            args.detector,
            args.feedback,
            args.git_state,
        )
        result = {"ok": True}
    elif args.command == "close-attempt":
        close_attempt(root, args.base, policy, args.git_state)
        result = {"ok": True}
    elif args.command == "validate-git-state":
        _assert_git_state_unchanged(root, args.base, args.git_state)
        result = {"ok": True}
    elif args.command == "finalize-git-state":
        finalize_git_state(root, args.base, args.git_state)
        result = {"ok": True}
    elif args.command == "validate-detector":
        detector = validate_detector(args.detector)
        drift_sources = detector.pop("validated_drift_sources")
        detector.pop("validated_drift_heads")
        selected = drift_sources[0] if drift_sources else None
        result = {
            "ok": True,
            "sources": len(detector["sources"]),
            "drift_count": len(drift_sources),
            "selected_source_id": selected["source_id"] if selected else "",
            "expected_head": selected["expected_head"] if selected else "",
        }
    elif args.command == "validate-proposal":
        result = validate_proposal(root, args.detector, args.proposal)
        result["ok"] = True
    elif args.command == "validate-serialized-acceptance":
        result = validate_serialized_acceptance(
            root,
            args.base,
            args.before_detector,
            args.after_detector,
        )
        result["ok"] = True
    elif args.command == "package":
        result = package_candidate(
            root,
            args.base,
            policy_path,
            policy_raw,
            policy,
            args.detector,
            args.goal_status,
            args.output,
            source_workflow=args.source_workflow,
            source_run_id=args.source_run_id,
            provider=args.provider,
        )
        result["ok"] = True
    elif args.command == "validate-package":
        result = validate_package(
            root,
            args.base,
            policy_raw,
            policy,
            args.package,
            expected_digest=args.expected_digest,
            source_workflow=args.source_workflow,
            source_run_id=args.source_run_id,
            provider=args.provider,
        )
        result["ok"] = True
    elif args.command == "build-candidate-review-bundle":
        output_path = args.output if args.output.is_absolute() else root / args.output
        result = build_candidate_review_bundle(root, args.base, args.head, policy, output_path)
        result["ok"] = True
    elif args.command == "validate-fable-verdict":
        verdict_path = args.verdict if args.verdict.is_absolute() else root / args.verdict
        execution_path = (
            args.execution_file if args.execution_file.is_absolute() else root / args.execution_file
        )
        result = validate_fable_verdict(
            verdict_path,
            execution_path,
            policy,
            base_sha=args.base,
            head_sha=args.head,
            content_sha256=args.content_sha256,
            patch_sha256=args.patch_sha256,
        )
        result["ok"] = True
    else:  # pragma: no cover
        raise AssertionError(args.command)
    _write_outputs(args.github_output, result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GuardError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        raise SystemExit(1) from exc
