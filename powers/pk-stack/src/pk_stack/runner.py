"""Bounded subprocess execution for executable verification contracts."""

from __future__ import annotations

import math
import os
import re
import shlex
import shutil
import signal
import subprocess
import threading
import time
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from io import BufferedReader
from itertools import pairwise
from pathlib import Path
from urllib.parse import unquote, urlsplit

from pk_stack.models import CommandSpec, VerificationResult

DEFAULT_TIMEOUT_SECONDS = 300.0
DEFAULT_OUTPUT_LIMIT = 64_000
_CALLER_PYTHONPATH_SET = "PK_STACK_CALLER_PYTHONPATH_SET"
_CALLER_PYTHONPATH = "PK_STACK_CALLER_PYTHONPATH"
_UV_CONTEXT_ENVIRONMENT = {"UV_CONFIG_FILE", "UV_ENV_FILE", "UV_PROJECT", "UV_WORKING_DIR"}
_UPSTREAM_SOURCE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

_NON_EVIDENTIARY_EXECUTABLES = {
    ":",
    "clear",
    "date",
    "echo",
    "false",
    "find",
    "hostname",
    "id",
    "locale",
    "printf",
    "printenv",
    "pwd",
    "sleep",
    "true",
    "uname",
    "whoami",
    "which",
    "yes",
}
_CONTROL_PLANE_EXECUTABLES = {"projectctl", "pk-stack-setup"}
_SHELL_EXECUTABLES = {"sh", "bash", "zsh", "fish", "dash", "ksh", "csh", "tcsh"}
_SCRIPT_INTERPRETERS = {"node", "nodejs", "ruby", "perl", "php", "osascript"}
_PYTHON_DELEGATING_MODULES = {
    "cprofile",
    "compileall",
    "coverage",
    "ensurepip",
    "pdb",
    "profile",
    "runpy",
    "timeit",
    "trace",
    "venv",
}
_PYTHON_SIMPLE_FLAGS = frozenset("bBdEIOPqRsuSvx")
_UV_GLOBAL_FLAGS = {
    "-n",
    "--no-cache",
    "--managed-python",
    "--no-managed-python",
    "--no-python-downloads",
    "-q",
    "--quiet",
    "-v",
    "--verbose",
    "--system-certs",
    "--offline",
    "--no-progress",
    "--no-config",
}
_UV_RUN_FLAGS = {
    "--active",
    "--all-extras",
    "--exact",
    "--frozen",
    "--isolated",
    "--locked",
    "--managed-python",
    "--no-cache",
    "--no-config",
    "--no-editable",
    "--no-managed-python",
    "--no-progress",
    "--no-project",
    "--no-python-downloads",
    "--no-sync",
    "--offline",
    "-q",
    "--quiet",
    "--system-certs",
    "-v",
    "--verbose",
}
_UV_RUN_VALUE_OPTIONS = {"--env-file", "--python", "--with", "--with-requirements"}
_PYTEST_ATTACHED_PATH_OPTIONS = (
    "--basetemp",
    "--confcutdir",
    "--rootdir",
    "--ignore",
    "-c",
)
_MAKE_ATTACHED_PATH_OPTIONS = (
    "--include-dir",
    "--directory",
    "--makefile",
    "--file",
    "-C",
    "-f",
    "-I",
)
_PACKAGE_MANAGER_ATTACHED_PATH_OPTIONS = ("--prefix", "--dir", "--cwd", "-C")
_GIT_ATTACHED_PATH_OPTIONS = ("--git-dir", "--work-tree", "-C")
_COMPILER_ATTACHED_PATH_OPTIONS = ("-include", "-isystem", "-I", "-L", "-B", "-o")
_ATTACHED_PATH_OPTIONS = {
    "cargo": ("--manifest-path",),
    "cc": _COMPILER_ATTACHED_PATH_OPTIONS,
    "clang": _COMPILER_ATTACHED_PATH_OPTIONS,
    "clang++": _COMPILER_ATTACHED_PATH_OPTIONS,
    "c++": _COMPILER_ATTACHED_PATH_OPTIONS,
    "gcc": _COMPILER_ATTACHED_PATH_OPTIONS,
    "g++": _COMPILER_ATTACHED_PATH_OPTIONS,
    "git": _GIT_ATTACHED_PATH_OPTIONS,
    "go": ("-C",),
    "gmake": _MAKE_ATTACHED_PATH_OPTIONS,
    "make": _MAKE_ATTACHED_PATH_OPTIONS,
    "npm": _PACKAGE_MANAGER_ATTACHED_PATH_OPTIONS,
    "pnpm": _PACKAGE_MANAGER_ATTACHED_PATH_OPTIONS,
    "py.test": _PYTEST_ATTACHED_PATH_OPTIONS,
    "pytest": _PYTEST_ATTACHED_PATH_OPTIONS,
    "ruby": ("-C", "-I"),
    "unittest": ("--top-level-directory", "--start-directory", "-s", "-t"),
    "uv": (
        "--with-requirements",
        "--env-file",
        "--python",
        "-w",
        "-p",
        "-C",
        "-f",
    ),
    "yarn": _PACKAGE_MANAGER_ATTACHED_PATH_OPTIONS,
}
_RESPONSE_FILE_EXECUTABLES = {
    "c++",
    "cc",
    "clang",
    "clang++",
    "g++",
    "gcc",
    "java",
    "javac",
    "mypy",
    "py.test",
    "pytest",
    "rustc",
    "swiftc",
}
_DENIED_EXECUTABLES = {
    "rm",
    "rmdir",
    "sudo",
    "su",
    "shutdown",
    "reboot",
    "halt",
    "diskutil",
    "dd",
    "mkfs",
    "env",
    "xargs",
    "command",
    "nice",
    "nohup",
    "timeout",
    "time",
    "caffeinate",
    "stdbuf",
    "script",
    "busybox",
    "taskpolicy",
    "sandbox-exec",
    "xcrun",
    "arch",
    "uvx",
}

_READ_ONLY_GIT_SUBCOMMANDS = {
    "annotate",
    "blame",
    "cat-file",
    "check-attr",
    "check-ignore",
    "check-mailmap",
    "check-ref-format",
    "describe",
    "diff",
    "diff-files",
    "diff-index",
    "diff-tree",
    "for-each-ref",
    "grep",
    "log",
    "ls-files",
    "ls-remote",
    "ls-tree",
    "merge-base",
    "name-rev",
    "rev-list",
    "rev-parse",
    "show",
    "show-branch",
    "status",
    "verify-commit",
    "verify-pack",
    "verify-tag",
    "whatchanged",
}
_GIT_GLOBAL_FLAGS = {
    "--bare",
    "--literal-pathspecs",
    "--no-advice",
    "--no-lazy-fetch",
    "--no-optional-locks",
    "--no-pager",
    "--no-replace-objects",
    "--paginate",
}
_GIT_GLOBAL_VALUE_OPTIONS = {*_GIT_ATTACHED_PATH_OPTIONS, "--namespace"}
_GIT_EXTERNAL_EXECUTION_OPTIONS = {
    "--ext-diff",
    "--filters",
    "--open-files-in-pager",
    "--output",
    "--textconv",
    "--upload-pack",
}
_PACKAGE_EXECUTION_WRAPPER_SUBCOMMANDS = {
    "npm": {"exec", "explore", "x"},
    "pnpm": {"dlx", "exec"},
    "yarn": {"dlx", "exec"},
}
_COMMON_INFORMATION_EXECUTABLES = {
    "cargo",
    "cc",
    "clang",
    "clang++",
    "cmake",
    "coverage",
    "coverage3",
    "c++",
    "gcc",
    "g++",
    "git",
    "go",
    "gmake",
    "gradle",
    "hatch",
    "java",
    "javac",
    "make",
    "mypy",
    "mvn",
    "npm",
    "npx",
    "pnpm",
    "pip",
    "pip3",
    "py.test",
    "pytest",
    "ruff",
    "rustc",
    "swift",
    "tox",
    "ty",
    "unittest",
    "yarn",
}
_SHORT_VERSION_EXECUTABLES = {
    "cargo",
    "cc",
    "clang",
    "clang++",
    "c++",
    "gcc",
    "g++",
    "go",
    "java",
    "javac",
    "mypy",
    "npm",
    "pnpm",
    "pip",
    "pip3",
    "rustc",
    "swift",
    "yarn",
}
_ALWAYS_SHORT_VERSION_EXECUTABLES = {
    "cargo",
    "java",
    "javac",
    "mypy",
    "npm",
    "pnpm",
    "pip",
    "pip3",
    "rustc",
    "swift",
    "yarn",
}
_ALWAYS_LOWER_SHORT_VERSION_EXECUTABLES = {"npm", "pip", "pip3", "pnpm", "yarn"}
_VERSION_SUBCOMMAND_EXECUTABLES = {
    "cargo",
    "cmake",
    "go",
    "mypy",
    "npm",
    "pnpm",
    "rustc",
    "ruff",
    "ty",
    "yarn",
}
_HELP_SUBCOMMAND_EXECUTABLES = {
    "cargo",
    "go",
    "npm",
    "pip",
    "pip3",
    "pnpm",
    "ruff",
    "ty",
    "yarn",
}


class CommandRejected(ValueError):
    """Raised when a verifier matches an obvious hazard or evidence-integrity screen."""


def _resolve_policy_path(path: Path) -> Path:
    """Resolve an untrusted operand without leaking filesystem parser errors."""

    try:
        return path.resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise CommandRejected("unable to resolve a verification path operand") from exc


def _exists_or_is_symlink(path: Path) -> bool:
    try:
        return path.exists() or path.is_symlink()
    except (OSError, RuntimeError, ValueError) as exc:
        raise CommandRejected("unable to inspect a verification path operand") from exc


def _reject_path_escape(token: str, *, root: Path, executable: bool = False) -> None:
    """Reject a path-shaped argv token that resolves outside ``root``.

    This is deliberately a lexical safety screen rather than a complete argv
    grammar. Applying it to every path-shaped token covers direct executables,
    interpreter scripts, nested tool operands, and ``--option=../path`` forms
    without pretending to sandbox arbitrary in-repository programs.
    """

    candidate = token
    if "=" in token:
        assigned = token.split("=", 1)[1]
        if assigned in {".", ".."} or assigned.startswith(("/", "./", "../", "file:", "git+file:")):
            candidate = assigned
    if candidate.startswith("@") and len(candidate) > 1:
        candidate = candidate[1:]
    if not candidate:
        return
    lowered_candidate = candidate.lower()
    markers = [
        index for marker in ("git+file:", "file:") if (index := lowered_candidate.find(marker)) >= 0
    ]
    local_url = candidate[min(markers) :] if markers else candidate
    try:
        parsed = urlsplit(local_url)
    except ValueError as exc:
        raise CommandRejected("invalid URL in verification path operand") from exc
    if parsed.scheme.lower() in {"file", "git+file"}:
        if parsed.netloc not in {"", "localhost"}:
            raise CommandRejected("verification cannot use a nonlocal file URL")
        candidate = unquote(parsed.path)
        if "\x00" in candidate:
            raise CommandRejected("verification file URLs cannot contain a NUL byte")
    elif "://" in candidate:
        return
    path = Path(candidate)
    explicit_path = path.is_absolute() or "/" in candidate or candidate in {".", ".."}
    path_shaped = explicit_path or (not executable and _exists_or_is_symlink(root / path))
    if not path_shaped:
        return
    resolved = _resolve_policy_path(path if path.is_absolute() else root / path)
    resolved_root = _resolve_policy_path(root)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        if executable and (
            path.is_absolute()
            or _is_python(path.name.lower())
            or path.name.lower() in _SCRIPT_INTERPRETERS
        ):
            selected = shutil.which(path.name)
            if selected is not None and _resolve_policy_path(Path(selected)) == resolved:
                return
        message = "verification path operands cannot escape the project root"
        raise CommandRejected(message) from exc


def _is_python(base: str) -> bool:
    return base.startswith("python") or base.startswith("pypy")


def _is_information_only_invocation(base: str, arguments: Sequence[str]) -> bool:
    """Recognize common version/help modes without reinterpreting script arguments."""

    full_tokens = tuple(arguments)
    subcommand_index = 0
    if base == "go" and subcommand_index < len(full_tokens):
        token = full_tokens[subcommand_index]
        if token == "-C" and subcommand_index + 1 < len(full_tokens):
            subcommand_index += 2
        elif token.startswith("-C") and len(token) > 2:
            subcommand_index += 1
    while subcommand_index < len(full_tokens) and full_tokens[subcommand_index] == "--":
        subcommand_index += 1
    if (
        subcommand_index < len(full_tokens)
        and full_tokens[subcommand_index] == "version"
        and base in _VERSION_SUBCOMMAND_EXECUTABLES
    ):
        return True
    if (
        subcommand_index < len(full_tokens)
        and full_tokens[subcommand_index] == "help"
        and base in _HELP_SUBCOMMAND_EXECUTABLES
    ):
        return True

    tokens = full_tokens
    if "--" in tokens:
        tokens = tokens[: tokens.index("--")]
    if base not in _COMMON_INFORMATION_EXECUTABLES:
        return False
    if any(
        token in {"--help", "--version"} or token.startswith(("--help=", "--version="))
        for token in tokens
    ):
        return True
    if "-h" in tokens:
        return True
    if base in _ALWAYS_SHORT_VERSION_EXECUTABLES and any(
        token in {"-V", "-version"}
        or (token == "-v" and base in _ALWAYS_LOWER_SHORT_VERSION_EXECUTABLES)
        or (
            token.startswith("-")
            and not token.startswith("--")
            and set(token[1:]) <= {"q", "v", "V"}
            and "V" in token
        )
        for token in tokens
    ):
        return True
    if base in {"py.test", "pytest"} and any(
        token in {"-h", "-V", "-VV"}
        or (
            token.startswith("-")
            and not token.startswith("--")
            and set(token[1:]) <= {"h", "q", "v", "V"}
            and bool(set(token[1:]) & {"h", "V"})
        )
        for token in tokens
    ):
        return True
    return (
        len(tokens) == 1
        and tokens[0] in {"-v", "-V", "-version"}
        and base in _SHORT_VERSION_EXECUTABLES
    )


def _python_target(arguments: Sequence[str]) -> tuple[str, str, int]:
    """Return (kind, target, target index) for the supported Python grammar."""

    tokens = tuple(arguments)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            if index + 1 >= len(tokens) or tokens[index + 1] == "-":
                break
            return ("script", tokens[index + 1], index + 1)
        if token == "-" or token in {"-c", "--command"} or token.startswith("-c"):
            raise CommandRejected("verification commands cannot execute inline interpreter code")
        if token == "-m":
            if index + 1 >= len(tokens) or tokens[index + 1].startswith("-"):
                break
            return ("module", tokens[index + 1], index + 1)
        if token.startswith("-m") and len(token) > 2:
            return ("module", token[2:], index)
        if token in {"-W", "-X", "--check-hash-based-pycs"}:
            index += 2
            continue
        if token.startswith(("-W", "-X")) and len(token) > 2:
            index += 1
            continue
        if token.startswith("--"):
            raise CommandRejected(f"unsupported leading Python verifier option: {token}")
        if token.startswith("-"):
            cluster = token[1:]
            if "c" in cluster:
                raise CommandRejected(
                    "verification commands cannot execute inline interpreter code"
                )
            if "m" in cluster:
                before, attached = cluster.split("m", 1)
                if not before or set(before) <= _PYTHON_SIMPLE_FLAGS:
                    if attached:
                        return ("module", attached, index)
                    if index + 1 < len(tokens) and not tokens[index + 1].startswith("-"):
                        return ("module", tokens[index + 1], index + 1)
                break
            if not cluster or not set(cluster) <= _PYTHON_SIMPLE_FLAGS:
                raise CommandRejected(f"unsupported leading Python verifier option: {token}")
            index += 1
            continue
        return ("script", token, index)
    raise CommandRejected("Python must select a project verification target")


def _script_interpreter_target(base: str, arguments: Sequence[str]) -> str:
    """Require a named script instead of stdin, eval, or ambiguous runtime options."""

    tokens = tuple(arguments)
    if tokens and tokens[0] == "--":
        tokens = tokens[1:]
    if not tokens or tokens[0] == "-" or tokens[0].startswith("-"):
        raise CommandRejected(
            f"{base} must select a project script directly; leading runtime options are unsupported"
        )
    return tokens[0]


def _resolves_to_control_plane(token: str, *, root: Path, search_path: bool) -> bool:
    """Detect direct or symlinked selection of a PK-Stack controller entrypoint."""

    path = Path(token)
    selected: Path | None = None
    if path.is_absolute():
        selected = path
    elif "/" in token:
        selected = root / path
    elif search_path:
        discovered = shutil.which(token)
        selected = Path(discovered) if discovered is not None else None
    elif _exists_or_is_symlink(root / path):
        selected = root / path
    if selected is None:
        return False
    resolved = _resolve_policy_path(selected)
    if resolved.name.lower() in _CONTROL_PLANE_EXECUTABLES:
        return True
    package_roots = {
        _resolve_policy_path(Path(__file__).parent),
        _resolve_policy_path(root / "src" / "pk_stack"),
        _resolve_policy_path(root / ".pk-stack" / "projectctl" / "src" / "pk_stack"),
    }
    for package_root in package_roots:
        try:
            resolved.relative_to(package_root)
        except ValueError:
            continue
        return True
    return False


def _git_subcommand(arguments: Sequence[str]) -> str:
    """Return an allowlistable Git builtin after a small global-option grammar."""

    tokens = tuple(arguments)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            index += 1
            break
        if token == "-c" or token.startswith("-c=") or (token.startswith("-c") and len(token) > 2):
            raise CommandRejected(
                "Git command-local configuration is not permitted in verification"
            )
        if token in {"--config-env"} or token.startswith("--config-env="):
            raise CommandRejected(
                "Git command-local configuration is not permitted in verification"
            )
        if token in _GIT_GLOBAL_VALUE_OPTIONS:
            if index + 1 >= len(tokens):
                raise CommandRejected(f"Git global option requires a value: {token}")
            index += 2
            continue
        if any(token.startswith(f"{option}=") for option in _GIT_GLOBAL_VALUE_OPTIONS):
            index += 1
            continue
        if token in _GIT_GLOBAL_FLAGS:
            index += 1
            continue
        if token.startswith("-"):
            raise CommandRejected(f"unsupported Git verifier option: {token}")
        break
    if index >= len(tokens):
        raise CommandRejected("Git must select a read-only verification subcommand")
    subcommand = tokens[index].lower()
    if subcommand not in _READ_ONLY_GIT_SUBCOMMANDS:
        raise CommandRejected(f"Git subcommand is not permitted in verification: {subcommand}")
    subcommand_arguments = tokens[index + 1 :]
    if "--" in subcommand_arguments:
        subcommand_arguments = subcommand_arguments[: subcommand_arguments.index("--")]

    def selects_external_program(token: str) -> bool:
        option_name = token.split("=", 1)[0]
        return (
            any(option.startswith(option_name) for option in _GIT_EXTERNAL_EXECUTION_OPTIONS)
            and option_name.startswith("--")
            and len(option_name) > 2
        ) or (subcommand == "grep" and token.startswith("-O"))

    if any(selects_external_program(token) for token in subcommand_arguments):
        raise CommandRejected("Git options that execute helpers or write output are not permitted")
    return subcommand


def _selects_package_execution_wrapper(base: str, arguments: Sequence[str]) -> bool:
    if base == "npx":
        return True
    denied = _PACKAGE_EXECUTION_WRAPPER_SUBCOMMANDS.get(base)
    if denied is None:
        return False
    tokens = tuple(arguments)
    if "--" in tokens:
        tokens = tokens[: tokens.index("--")]
    return any(token.lower() in denied for token in tokens)


def _reject_pytest_option_indirection(base: str, arguments: Sequence[str]) -> None:
    if base not in {"py.test", "pytest"}:
        return
    tokens = tuple(arguments)
    for index, token in enumerate(tokens):
        override: str | None = None
        if token in {"-o", "--override-ini"} and index + 1 < len(tokens):
            override = tokens[index + 1]
        elif token.startswith("--override-ini="):
            override = token.split("=", 1)[1]
        elif token.startswith("-o") and len(token) > 2:
            override = token[2:]
        if override is not None and override.lower().startswith("addopts="):
            raise CommandRejected("pytest addopts overrides are not supported in verification")


def _reject_response_files(base: str, arguments: Sequence[str]) -> None:
    """Reject argument-file indirection only for tools that implement it."""

    if base in _RESPONSE_FILE_EXECUTABLES and any(token.startswith("@") for token in arguments):
        raise CommandRejected(f"{base} response files are not supported in verification")


def _is_context_free_predicate(base: str, arguments: Sequence[str], *, root: Path) -> bool:
    """Recognize predicates whose success is guaranteed by the runner contract."""

    tokens = list(arguments)
    if base == "[":
        if not tokens or tokens[-1] != "]":
            return False
        tokens.pop()
    if base in {"test", "["}:
        unary_file_predicates = {
            "-b",
            "-c",
            "-d",
            "-e",
            "-f",
            "-g",
            "-h",
            "-k",
            "-L",
            "-p",
            "-r",
            "-S",
            "-s",
            "-u",
            "-w",
            "-x",
        }
        binary_file_predicates = {"-ef", "-nt", "-ot"}
        resolved_root = _resolve_policy_path(root)

        def uses_project_path(value: str) -> bool:
            operand = Path(value)
            resolved = _resolve_policy_path(operand if operand.is_absolute() else root / operand)
            return resolved != resolved_root

        def consume_file_atom(index: int) -> int | None:
            while index < len(tokens) and tokens[index] == "!":
                index += 1
            if index >= len(tokens):
                return None
            if tokens[index] in unary_file_predicates and index + 1 < len(tokens):
                return index + 2 if uses_project_path(tokens[index + 1]) else None
            if (
                index + 2 < len(tokens)
                and tokens[index + 1] in binary_file_predicates
                and (uses_project_path(tokens[index]) or uses_project_path(tokens[index + 2]))
            ):
                return index + 3
            return None

        index = consume_file_atom(0)
        if index is None:
            return True
        while index < len(tokens):
            if tokens[index] not in {"-a", "-o"}:
                return True
            index = consume_file_atom(index + 1)
            if index is None:
                return True
        return False
    if base in {"ls", "stat"}:
        operands = [token for token in tokens if token != "--" and not token.startswith("-")]
        if not operands:
            return True
        resolved_root = _resolve_policy_path(root)
        return all(_resolve_policy_path(root / operand) == resolved_root for operand in operands)
    return False


def _uv_run_target(arguments: Sequence[str]) -> tuple[tuple[str, ...], int]:
    """Locate the nested command using a small, fail-closed uv grammar."""

    tokens = tuple(arguments)
    index = 0
    while index < len(tokens) and tokens[index] != "run":
        token = tokens[index]
        if token == "--directory" or token.startswith("--directory="):
            raise CommandRejected(
                "uv --directory is not permitted because verifier paths must resolve "
                "from the project root"
            )
        if token not in _UV_GLOBAL_FLAGS:
            raise CommandRejected(f"unsupported uv verifier option before run: {token}")
        index += 1
    if index >= len(tokens):
        raise CommandRejected("uv must select the run subcommand for verification")

    index += 1
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            index += 1
            break
        if token == "--directory" or token.startswith("--directory="):
            raise CommandRejected(
                "uv --directory is not permitted because verifier paths must resolve "
                "from the project root"
            )
        if token in {"-m", "--module", "-s", "--script", "--gui-script"} or token.startswith(
            ("-m", "-s", "--module=", "--script=", "--gui-script=")
        ):
            raise CommandRejected(
                "uv run module/script shorthand is not supported in verification; "
                "select an explicit nested command"
            )
        if token in _UV_RUN_FLAGS:
            index += 1
            continue
        if token in _UV_RUN_VALUE_OPTIONS:
            if index + 1 >= len(tokens):
                raise CommandRejected(f"uv run option requires a value: {token}")
            index += 2
            continue
        if any(token.startswith(f"{option}=") for option in _UV_RUN_VALUE_OPTIONS):
            index += 1
            continue
        if token.startswith("-"):
            raise CommandRejected(f"unsupported leading uv run verifier option: {token}")
        break
    if index >= len(tokens):
        raise CommandRejected("uv run must select a project verification command")
    return (tokens[index:], index)


def _attached_path_operands(base: str, arguments: Sequence[str]) -> tuple[str, ...]:
    """Extract known CLI-specific attached path values for containment checks."""

    prefixes = _ATTACHED_PATH_OPTIONS.get(base, ())
    operands: list[str] = []
    for token in arguments:
        if token == "--":
            break
        for prefix in prefixes:
            if token.startswith(prefix) and len(token) > len(prefix):
                suffix = token[len(prefix) :]
                if suffix.startswith("="):
                    suffix = suffix[1:]
                if suffix:
                    operands.append(suffix)
                break
    return tuple(operands)


def parse_command(value: str | Sequence[str]) -> tuple[str, ...]:
    """Parse a command without invoking a shell.

    String contracts remain convenient in Markdown frontmatter, while the
    resulting argv boundary prevents pipes, redirects, substitutions, and
    compound shell expressions from being interpreted.
    """

    if isinstance(value, str):
        if "\x00" in value or "\n" in value or "\r" in value:
            raise CommandRejected("verification commands must be a single NUL-free line")
        try:
            argv = tuple(shlex.split(value, posix=True))
        except ValueError as exc:
            raise CommandRejected(f"invalid verification command: {exc}") from exc
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        if any(type(item) is not str for item in value):
            raise CommandRejected("verification argv must contain only strings")
        argv = tuple(value)
    else:
        raise CommandRejected("verification command must be a string or string sequence")

    if not argv or not argv[0].strip():
        raise CommandRejected("verification command cannot be empty")
    if any("\x00" in item for item in argv):
        raise CommandRejected("verification command contains a NUL byte")
    return argv


def display_command(argv: Sequence[str]) -> str:
    return shlex.join(tuple(argv))


def _is_managed_upstream_check(argv: Sequence[str], *, root: Path) -> bool:
    """Allow one meaningful self-host predicate without reopening generic self-proof."""

    if len(argv) < 3 or tuple(argv[1:3]) != ("upstream", "check"):
        return False
    resolved_root = _resolve_policy_path(root)
    executable = Path(argv[0])
    candidate = Path(
        os.path.abspath(executable if executable.is_absolute() else resolved_root / executable)
    )
    canonical = resolved_root / ".pk-stack" / "bin" / "projectctl"
    if candidate != canonical:
        return False
    if (
        not candidate.is_file()
        or candidate.is_symlink()
        or _resolve_policy_path(candidate) != candidate
    ):
        raise CommandRejected("the managed upstream verifier entrypoint is missing or unsafe")
    if not os.access(candidate, os.X_OK):
        raise CommandRejected("the managed upstream verifier entrypoint is not executable")

    allowed_options = {
        "--manifest",
        "--output",
        "--power-root",
        "--source-id",
        "--timeout-seconds",
    }
    values: dict[str, str] = {}
    index = 3
    while index < len(argv):
        token = argv[index]
        if "=" in token:
            option, value = token.split("=", 1)
            consumed = 1
        else:
            option = token
            if index + 1 >= len(argv):
                raise CommandRejected(
                    f"managed upstream verifier option requires a value: {option}"
                )
            value = argv[index + 1]
            consumed = 2
        if option not in allowed_options:
            raise CommandRejected(f"unsupported managed upstream verifier option: {option}")
        if option in values:
            raise CommandRejected(f"duplicate managed upstream verifier option: {option}")
        if not value or "\x00" in value:
            raise CommandRejected(
                f"managed upstream verifier option has an invalid value: {option}"
            )
        values[option] = value
        index += consumed

    required = {"--manifest", "--output", "--power-root"}
    if not required <= set(values):
        missing = ", ".join(sorted(required - set(values)))
        raise CommandRejected(f"managed upstream verifier is missing required options: {missing}")
    if values["--output"] != "json":
        raise CommandRejected("managed upstream verifier must use JSON output")
    if values["--manifest"] != "maintenance/upstreams.json":
        raise CommandRejected("managed upstream verifier must use maintenance/upstreams.json")
    if values["--power-root"] != "powers/pk-stack":
        raise CommandRejected("managed upstream verifier must use powers/pk-stack")
    if "--source-id" in values and (
        len(values["--source-id"]) > 64 or not _UPSTREAM_SOURCE_ID.fullmatch(values["--source-id"])
    ):
        raise CommandRejected("managed upstream verifier source id is invalid")
    for option in ("--manifest", "--power-root"):
        _reject_path_escape(values[option], root=resolved_root)
    if "--timeout-seconds" in values:
        try:
            timeout = float(values["--timeout-seconds"])
        except ValueError as exc:
            raise CommandRejected("managed upstream verifier timeout must be numeric") from exc
        if not math.isfinite(timeout) or not 0 < timeout <= 30:
            raise CommandRejected(
                "managed upstream verifier timeout must be positive, finite, and at most 30 seconds"
            )
    return True


def enforce_verification_policy(argv: Sequence[str], *, root: Path) -> None:
    """Reject operations that do not belong in a verifier.

    Kiro permissions and explicit user review remain the authorization layer.
    This screen rejects common destructive and context-free placeholder forms,
    but it is not a sandbox and cannot prove that an arbitrary project script
    is read-only or semantically relevant.
    """

    if not argv:
        raise CommandRejected("verification command cannot be empty")

    executable = argv[0]
    base = Path(executable).name.lower()
    if _is_managed_upstream_check(argv, root=root):
        return
    if base in _NON_EVIDENTIARY_EXECUTABLES:
        raise CommandRejected(f"{base!r} cannot establish verification evidence")
    if base in _CONTROL_PLANE_EXECUTABLES:
        raise CommandRejected("projectctl cannot serve as its own verification evidence")
    if _resolves_to_control_plane(executable, root=root, search_path=True):
        raise CommandRejected("projectctl cannot serve as its own verification evidence")
    if base in _DENIED_EXECUTABLES:
        raise CommandRejected(f"{base!r} is not permitted as a verification executable")
    _reject_response_files(base, argv[1:])
    if (
        base != "uv"
        and not _is_python(base)
        and base not in _SCRIPT_INTERPRETERS
        and (_is_information_only_invocation(base, argv[1:]))
    ):
        raise CommandRejected("informational output cannot establish verification evidence")
    if _is_context_free_predicate(base, argv[1:], root=root):
        raise CommandRejected(f"{base!r} cannot establish project-specific verification evidence")
    _reject_pytest_option_indirection(base, argv[1:])

    if base in {"coverage", "coverage3"} and (not argv[1:] or argv[1].lower() != "report"):
        raise CommandRejected("coverage must use the non-delegating report subcommand")
    if _selects_package_execution_wrapper(base, argv[1:]):
        raise CommandRejected(
            "package-manager execution wrappers are not permitted in verification"
        )

    if base in _SHELL_EXECUTABLES:
        raise CommandRejected(
            "shell interpreters are not supported as verifiers; execute a project script directly"
        )

    interpreter_target: str | None = None
    if _is_python(base):
        target_kind, interpreter_target, target_index = _python_target(argv[1:])
        if target_kind == "module":
            normalized_module = interpreter_target.lower()
            if normalized_module == "pk_stack" or normalized_module.startswith("pk_stack."):
                raise CommandRejected("pk_stack cannot serve as its own verification evidence")
            if normalized_module in _PYTHON_DELEGATING_MODULES:
                message = (
                    "delegating Python module is not supported in verification: "
                    f"{interpreter_target}"
                )
                raise CommandRejected(message)
            module_arguments = argv[target_index + 2 :]
            if _is_information_only_invocation(normalized_module, module_arguments):
                raise CommandRejected("informational output cannot establish verification evidence")
            _reject_response_files(normalized_module, module_arguments)
            _reject_pytest_option_indirection(normalized_module, module_arguments)
            for operand in _attached_path_operands(normalized_module, module_arguments):
                _reject_path_escape(operand, root=root)
    elif base in _SCRIPT_INTERPRETERS:
        interpreter_target = _script_interpreter_target(base, argv[1:])
    if interpreter_target is not None and _resolves_to_control_plane(
        interpreter_target,
        root=root,
        search_path=False,
    ):
        raise CommandRejected("projectctl cannot serve as its own verification evidence")

    lowered = [item.lower() for item in argv]
    if base in {"terraform", "tofu"} and any(
        token in {"apply", "destroy", "import"} for token in lowered[1:]
    ):
        raise CommandRejected(f"{base} mutation is not a verification operation")
    gh_pairs = list(pairwise(lowered[1:]))
    if base == "gh" and any(
        pair in {("repo", "delete"), ("release", "delete")} for pair in gh_pairs
    ):
        raise CommandRejected("destructive GitHub operations are not verification")
    if base == "gh" and "api" in lowered[1:]:
        destructive_method = any(token in {"-xdelete", "--method=delete"} for token in lowered)
        destructive_method = destructive_method or any(
            token in {"-x", "--method"}
            and index + 1 < len(lowered)
            and lowered[index + 1] == "delete"
            for index, token in enumerate(lowered)
        )
        if destructive_method:
            raise CommandRejected("destructive GitHub API calls are not verification")
    uv_nested_executable_index: int | None = None
    attached_path_arguments = argv[1:]
    if base == "uv":
        nested_argv, target_index = _uv_run_target(argv[1:])
        uv_nested_executable_index = target_index + 1
        attached_path_arguments = argv[1:uv_nested_executable_index]
        try:
            enforce_verification_policy(nested_argv, root=root)
        except CommandRejected as exc:
            raise CommandRejected(
                f"uv run cannot wrap a rejected verification command: {exc}"
            ) from exc
    if base == "git":
        _git_subcommand(argv[1:])
    if base == "aws" and any(
        token in {"delete", "deregister", "remove", "rm", "terminate"}
        or token.startswith(("delete-", "terminate-", "remove-", "deregister-"))
        for token in lowered[1:]
    ):
        raise CommandRejected("destructive AWS operations are not verification")
    if base in {"kubectl", "oc"} and any(
        token in {"apply", "create", "delete", "edit", "patch", "replace", "scale"}
        for token in lowered[1:]
    ):
        raise CommandRejected(f"mutating {base} operations are not verification")
    if base in {"docker", "podman"} and any(
        token in {"prune", "rm", "rmi"} for token in lowered[1:]
    ):
        raise CommandRejected(f"destructive {base} operations are not verification")

    for operand in _attached_path_operands(base, attached_path_arguments):
        _reject_path_escape(operand, root=root)
    for index, token in enumerate(argv):
        _reject_path_escape(
            token,
            root=root,
            executable=index in {0, uv_nested_executable_index},
        )


def _bounded(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    half = max(1, limit // 2)
    omitted = len(text) - (half * 2)
    marker = f"\n... <{omitted} characters omitted> ...\n"
    return f"{text[:half]}{marker}{text[-half:]}", True


@dataclass(slots=True)
class _BoundedCapture:
    limit: int
    head: bytearray = field(default_factory=bytearray)
    tail: bytearray = field(default_factory=bytearray)
    total: int = 0

    def feed(self, chunk: bytes) -> None:
        self.total += len(chunk)
        head_limit = self.limit // 2
        if len(self.head) < head_limit:
            take = min(head_limit - len(self.head), len(chunk))
            self.head.extend(chunk[:take])
            chunk = chunk[take:]
        if chunk:
            tail_limit = self.limit - head_limit
            self.tail.extend(chunk)
            if len(self.tail) > tail_limit:
                del self.tail[: len(self.tail) - tail_limit]

    def render(self) -> tuple[str, bool]:
        data = bytes(self.head + self.tail)
        if self.total <= self.limit:
            return data.decode(errors="replace"), False
        omitted = self.total - len(data)
        marker = f"\n... <{omitted} bytes omitted> ...\n".encode()
        return (bytes(self.head) + marker + bytes(self.tail)).decode(errors="replace"), True


def _drain(stream: BufferedReader, capture: _BoundedCapture) -> None:
    try:
        while chunk := stream.read(16_384):
            capture.feed(chunk)
    finally:
        stream.close()


def _verifier_environment(
    overrides: dict[str, str] | None = None,
    *,
    uv_command: bool,
) -> dict[str, str]:
    """Reconstruct the caller environment hidden by the controller wrapper."""

    process_env = os.environ.copy()
    caller_pythonpath_set = process_env.pop(_CALLER_PYTHONPATH_SET, None)
    caller_pythonpath = process_env.pop(_CALLER_PYTHONPATH, "")
    if caller_pythonpath_set == "1":
        process_env["PYTHONPATH"] = caller_pythonpath
    elif caller_pythonpath_set == "0":
        process_env.pop("PYTHONPATH", None)
    if overrides:
        process_env.update(overrides)
    if uv_command:
        # These variables are environment-level aliases for wrapper path inputs.
        # Strip them so the parsed argv and project-root cwd remain authoritative.
        for name in _UV_CONTEXT_ENVIRONMENT:
            process_env.pop(name, None)
    return process_env


def run_command(
    command: CommandSpec | str | Sequence[str],
    *,
    root: Path,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
    env: dict[str, str] | None = None,
) -> VerificationResult:
    if (
        not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0
        or timeout_seconds > threading.TIMEOUT_MAX
    ):
        raise ValueError("timeout_seconds must be positive, finite, and within the platform limit")
    if output_limit < 1_024:
        raise ValueError("output_limit must be at least 1024 characters")
    root = root.resolve()
    argv = parse_command(command.argv if isinstance(command, CommandSpec) else command)
    enforce_verification_policy(argv, root=root)

    started_at = datetime.now(UTC).isoformat()
    started = time.monotonic()
    process_env = _verifier_environment(env, uv_command=Path(argv[0]).name.lower() == "uv")

    process: subprocess.Popen[bytes] | None = None
    readers: list[threading.Thread] = []
    previous_sigterm = None
    if threading.current_thread() is threading.main_thread():
        previous_sigterm = signal.signal(signal.SIGTERM, _cancel_verification)
    timed_out = False
    try:
        process = subprocess.Popen(
            list(argv),
            cwd=root,
            env=process_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
        )
        if process.stdout is None or process.stderr is None:  # pragma: no cover - Popen contract
            raise RuntimeError("verifier output pipes were not created")
        stdout_capture = _BoundedCapture(output_limit)
        stderr_capture = _BoundedCapture(output_limit)
        readers = [
            threading.Thread(target=_drain, args=(process.stdout, stdout_capture), daemon=True),
            threading.Thread(target=_drain, args=(process.stderr, stderr_capture), daemon=True),
        ]
        for reader in readers:
            reader.start()
        deadline = started + timeout_seconds
        try:
            process.wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            timed_out = True
        for reader in readers:
            reader.join(max(0.0, deadline - time.monotonic()))
        if any(reader.is_alive() for reader in readers):
            timed_out = True
    except OSError as exc:
        duration_ms = int((time.monotonic() - started) * 1_000)
        return VerificationResult(
            passed=False,
            exit_code=127,
            stdout="",
            stderr="",
            duration_ms=duration_ms,
            error=f"unable to execute {argv[0]!r}: {exc}",
            started_at=started_at,
        )

    finally:
        try:
            if process is not None:
                # This also runs on Ctrl-C, SIGTERM, and failures while starting
                # capture threads. No verifier may outlive its proof attempt.
                _kill_process_group(process)
                with suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=5)
                for reader in readers:
                    if reader.ident is not None:
                        reader.join(timeout=5)
                for index, stream in enumerate((process.stdout, process.stderr)):
                    # Closing a BufferedReader while its read thread is blocked
                    # can itself block. The reader owns its stream until exit.
                    reader_stopped = index >= len(readers) or not readers[index].is_alive()
                    if reader_stopped and stream is not None and not stream.closed:
                        stream.close()
        finally:
            if previous_sigterm is not None:
                signal.signal(signal.SIGTERM, previous_sigterm)

    for reader in readers:
        if reader.is_alive():  # pragma: no cover - defensive OS pipe failure
            raise RuntimeError("verifier output pipe did not close after process termination")
    stdout, stdout_cut = stdout_capture.render()
    stderr, stderr_cut = stderr_capture.render()
    duration_ms = int((time.monotonic() - started) * 1_000)
    if timed_out:
        return VerificationResult(
            passed=False,
            exit_code=124,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timed_out=True,
            truncated=stdout_cut or stderr_cut,
            error=f"verification timed out after {timeout_seconds:g} seconds",
            started_at=started_at,
        )
    return VerificationResult(
        passed=process.returncode == 0,
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
        duration_ms=duration_ms,
        truncated=stdout_cut or stderr_cut,
        started_at=started_at,
    )


def _cancel_verification(signum: int, _frame: object) -> None:
    """Unwind the command lifetime and the caller's goal lock on termination."""

    raise SystemExit(128 + signum)


def _kill_process_group(process: subprocess.Popen[bytes]) -> None:
    """Terminate the verifier and descendants started in its process group."""

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (AttributeError, ProcessLookupError):
        if process.poll() is None:
            process.kill()
