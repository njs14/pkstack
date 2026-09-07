"""Standard-library uvx entrypoint that delegates to a project's controller.

The launcher never becomes the controller. It selects a project, runs the
reviewed bootstrap that ships in this package for `setup`/`upgrade`, and hands
every other command to the project's own `.pkstack/bin/projectctl` wrapper so
the proof surface stays the bootstrapped runtime rather than a downloaded
package.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path

from pkstack import __version__
from pkstack.bootstrap import (
    INTERNAL_WRAPPER,
    audit_bootstrap_receipt,
    receipt_managed_hashes,
)
from pkstack.bootstrap import main as bootstrap_main
from pkstack.branding import DISPLAY_NAME, DISTRIBUTION_NAME
from pkstack.paths import WorkspacePathError, workspace_path

CONTROLLER = Path(".pkstack/bin/projectctl")
# The controller runtime the wrapper actually executes. Membership is required
# so a receipt cannot describe a project whose controller was never installed.
REQUIRED_RECEIPT_PATHS = (
    ".pkstack/bin/projectctl",
    ".pkstack/projectctl/pyproject.toml",
    ".pkstack/projectctl/uv.lock",
    ".pkstack/projectctl/src/pkstack/__main__.py",
    ".pkstack/projectctl/src/pkstack/cli.py",
)
RUNTIME_PREFIXES = (".pkstack/bin/", ".pkstack/projectctl/")
BOOTSTRAP_COMMANDS = ("setup", "upgrade")

HELP = f"""{DISPLAY_NAME} launcher for a project's own bootstrapped controller.

Usage:
  {DISTRIBUTION_NAME} [--project PATH] COMMAND [ARGS...]

Select a reviewed checkout or local wheel with PKSTACK_PACKAGE, then run:
  uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" {DISTRIBUTION_NAME} setup
  uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" {DISTRIBUTION_NAME} --project /path/to/repo doctor
No registry or permanent tool installation is required.

Launcher options (they must come before COMMAND):
  --project PATH  Select the project root. The default is exactly the current
                  directory; no parent directory is searched.
  --version       Print this launcher package version and exit.
  -h, --help      Print this help and exit.

Commands:
  setup           Create or repair managed files from the reviewed assets that
                  ship in this package. Accepts --dry-run and --output.
  upgrade         Like setup, plus --update-managed, which replaces files that
                  still match the recorded receipt. Review 'upgrade --dry-run'
                  first. Accepts --dry-run and --output.
  version         Forwarded: reports the version of the controller installed in
                  the selected project.
  everything else Forwarded unchanged to <project>/.pkstack/bin/projectctl
                  (doctor, feature, goal, knowledge, evidence, upstream, ...).

Notes:
  '{DISTRIBUTION_NAME} --version' reports this launcher package version, which
  can differ from the controller version reported by '{DISTRIBUTION_NAME} version'.
  Forwarded commands select the project with --project, not --root.
  Before forwarding, the launcher checks the wrapper bytes and the recorded
  bootstrap receipt. That receipt is a local ownership record of the last
  reviewed setup, not a signature or any other cryptographic trust anchor.
"""


class LauncherError(Exception):
    """Raised for a launcher-level argument, project, or controller problem."""


def main(argv: list[str] | None = None) -> None:
    """Dispatch the launcher, accepting explicit tokens for deterministic tests."""

    tokens = list(sys.argv[1:] if argv is None else argv)
    try:
        _run(tokens)
    except (LauncherError, OSError, ValueError) as exc:
        _fail(exc, tokens)


def _fail(exc: Exception, tokens: list[str]) -> None:
    payload = {"ok": False, "error": str(exc), "error_type": type(exc).__name__}
    if _requests_json(tokens):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"error: {exc}", file=sys.stderr)
    raise SystemExit(2)


def _requests_json(tokens: list[str]) -> bool:
    return any(
        token == "--output=json"
        or (token == "--output" and index + 1 < len(tokens) and tokens[index + 1] == "json")
        for index, token in enumerate(tokens)
    )


def _run(tokens: list[str]) -> None:
    project: Path | None = None
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {"-h", "--help"}:
            print(HELP, end="")
            return
        if token == "--version":
            print(f"{DISTRIBUTION_NAME} {__version__}")
            print(
                f"This is the {DISTRIBUTION_NAME} launcher package. Run "
                f"'{DISTRIBUTION_NAME} version' for the controller installed in a project."
            )
            return
        if token == "--project" or token.startswith("--project="):
            value, index = _project_value(tokens, index)
            if project is not None:
                raise LauncherError("--project was given more than once")
            project = Path(os.path.abspath(value))
            continue
        if token.startswith("-"):
            raise LauncherError(
                f"unknown launcher option before the command: {token}; "
                f"run '{DISTRIBUTION_NAME} --help'"
            )
        break
    else:
        print(HELP, end="")
        return

    command, rest = tokens[index], tokens[index + 1 :]
    selected = Path.cwd() if project is None else project
    if not selected.is_dir():
        raise LauncherError(
            f"no project directory at {selected}; {DISPLAY_NAME} never creates it. "
            "Create the directory, or select an existing project with --project PATH"
        )
    if command in BOOTSTRAP_COMMANDS:
        _bootstrap(command, selected, rest)
        return
    _forward(selected, command, rest)


def _project_value(tokens: list[str], index: int) -> tuple[str, int]:
    token = tokens[index]
    if token == "--project":
        if index + 1 >= len(tokens) or tokens[index + 1].startswith("--"):
            raise LauncherError("--project requires a project directory path")
        value, following = tokens[index + 1], index + 2
    else:
        value, following = token.split("=", 1)[1], index + 1
    if not value:
        raise LauncherError("--project requires a non-empty project directory path")
    return value, following


def _bootstrap(command: str, project: Path, arguments: list[str]) -> None:
    dry_run = False
    output = "text"
    index = 0
    while index < len(arguments):
        token = arguments[index]
        if token == "--dry-run":
            dry_run = True
            index += 1
            continue
        if token == "--output" or token.startswith("--output="):
            output, index = _output_value(command, arguments, index)
            continue
        _reject_bootstrap_option(command, token)
        index += 1

    forwarded = ["--root", str(project), "--output", output]
    if dry_run:
        forwarded.append("--dry-run")
    if command == "upgrade":
        forwarded.append("--update-managed")
    bootstrap_main(forwarded)


def _output_value(command: str, arguments: list[str], index: int) -> tuple[str, int]:
    token = arguments[index]
    if token == "--output":
        if index + 1 >= len(arguments):
            raise LauncherError(f"{DISTRIBUTION_NAME} {command} --output requires json or text")
        value, next_index = arguments[index + 1], index + 2
    else:
        value, next_index = token.split("=", 1)[1], index + 1
    if value not in {"json", "text"}:
        raise LauncherError(
            f"{DISTRIBUTION_NAME} {command} --output accepts json or text, not {value!r}"
        )
    return value, next_index


def _reject_bootstrap_option(command: str, token: str) -> None:
    if token == "--root" or token.startswith("--root="):
        raise LauncherError(
            f"{DISTRIBUTION_NAME} {command} does not accept --root; select the project with "
            f"'{DISTRIBUTION_NAME} --project PATH {command}'"
        )
    if token == "--power-root" or token.startswith("--power-root="):
        raise LauncherError(
            f"{DISTRIBUTION_NAME} {command} always uses the reviewed assets shipped in this "
            "package; --power-root is not accepted here. Use the Power-local /pkstack-setup "
            "skill to install from a checkout"
        )
    if token == "--update-managed" or token.startswith("--update-managed="):
        if command == "upgrade":
            raise LauncherError(
                f"{DISTRIBUTION_NAME} upgrade already replaces receipt-managed files; "
                "--update-managed is not accepted"
            )
        raise LauncherError(
            f"{DISTRIBUTION_NAME} setup does not accept --update-managed; review "
            f"'{DISTRIBUTION_NAME} setup --dry-run' and then run '{DISTRIBUTION_NAME} upgrade'"
        )
    if token.startswith("-"):
        raise LauncherError(
            f"unknown option for {DISTRIBUTION_NAME} {command}: {token}; "
            f"{command} accepts --dry-run and --output"
        )
    raise LauncherError(
        f"{DISTRIBUTION_NAME} {command} takes no positional arguments, but got {token!r}"
    )


def _forward(project: Path, command: str, arguments: list[str]) -> None:
    _reject_forwarded_options([command, *arguments])
    wrapper = _validated_controller(project)
    env = delegated_environment(os.environ)
    os.chdir(project)
    os.execve(str(wrapper), [str(wrapper), command, *arguments], env)


def _reject_forwarded_options(arguments: list[str]) -> None:
    """Reject project selection the controller must not receive from the launcher.

    Only whole option tokens are inspected, and only before a ``--`` terminator,
    so an option *value* such as a verifier command string that happens to
    contain ``--root`` is forwarded untouched.
    """

    for token in arguments:
        if token == "--":
            return
        if token == "--root" or token.startswith("--root="):
            raise LauncherError(
                f"--root is not forwarded; select the project with "
                f"'{DISTRIBUTION_NAME} --project PATH COMMAND'"
            )
        if token == "--project" or token.startswith("--project="):
            raise LauncherError(
                f"--project must come before the command: "
                f"'{DISTRIBUTION_NAME} --project PATH COMMAND'"
            )


def _validated_controller(project: Path) -> Path:
    try:
        wrapper = workspace_path(project, CONTROLLER)
    except WorkspacePathError as exc:
        raise LauncherError(
            f"the {DISPLAY_NAME} controller path is unsafe: {exc}. "
            f"Review the redirected path and restore it before running '{DISTRIBUTION_NAME} setup'"
        ) from exc
    if not wrapper.exists():
        raise LauncherError(
            f"no {DISPLAY_NAME} controller at {wrapper}; run "
            f"'{DISTRIBUTION_NAME} --project {project} setup' first"
        )
    if os.path.islink(wrapper) or not wrapper.is_file():
        raise LauncherError(
            f"the {DISPLAY_NAME} controller at {wrapper} is not a regular file; "
            "restore it from a reviewed setup run"
        )
    if not os.access(wrapper, os.X_OK):
        raise LauncherError(
            f"the {DISPLAY_NAME} controller at {wrapper} is not executable; "
            f"run '{DISTRIBUTION_NAME} --project {project} upgrade' after reviewing a dry run"
        )
    try:
        installed = wrapper.read_bytes()
    except OSError as exc:
        raise LauncherError(
            f"unable to read the {DISPLAY_NAME} controller at {wrapper}: {exc}"
        ) from exc
    expected = INTERNAL_WRAPPER.encode()
    if installed != expected:
        raise LauncherError(
            f"the {DISPLAY_NAME} controller at {wrapper} differs from the reviewed wrapper; "
            f"review the change, then run '{DISTRIBUTION_NAME} --project {project} upgrade'"
        )
    _validate_receipt(project, expected)
    return wrapper


def _validate_receipt(project: Path, wrapper_bytes: bytes) -> None:
    try:
        recorded = receipt_managed_hashes(project)
        audit = audit_bootstrap_receipt(project)
    except (OSError, ValueError) as exc:
        raise LauncherError(
            f"unusable {DISPLAY_NAME} ownership receipt: {exc}. "
            f"Run '{DISTRIBUTION_NAME} --project {project} setup' and review the result"
        ) from exc
    unrecorded = [key for key in REQUIRED_RECEIPT_PATHS if key not in recorded]
    if unrecorded:
        raise LauncherError(
            f"the {DISPLAY_NAME} ownership receipt does not record the controller runtime: "
            + ", ".join(unrecorded)
            + f". Run '{DISTRIBUTION_NAME} --project {project} setup' and review the result"
        )
    if recorded[CONTROLLER.as_posix()] != hashlib.sha256(wrapper_bytes).hexdigest():
        raise LauncherError(
            f"the {DISPLAY_NAME} ownership receipt records a different controller wrapper; "
            f"review the change, then run '{DISTRIBUTION_NAME} --project {project} upgrade'"
        )
    # Unrelated managed files, such as an intentionally edited skill, must not
    # block execution; only the controller runtime the wrapper executes does.
    failures = sorted(
        key
        for key in (*audit.missing, *audit.hash_mismatches, *audit.unsafe_or_unreadable)
        if key.startswith(RUNTIME_PREFIXES)
    )
    if failures:
        raise LauncherError(
            f"{DISPLAY_NAME} controller runtime files are missing or modified: "
            + ", ".join(failures)
            + f". Review the change, then run '{DISTRIBUTION_NAME} --project {project} upgrade'"
        )


def delegated_environment(environ: Mapping[str, str]) -> dict[str, str]:
    """Return the caller environment with this launcher's own bin entry dropped.

    ``uvx`` and ``uv run`` prepend the ephemeral launcher environment's ``bin``
    to ``PATH``. Only that leading entry is removed, so the project's verifier
    keeps the caller's remaining ``PATH``, ``VIRTUAL_ENV``, ``PYTHONPATH``, and
    ``UV_*`` configuration. A missing ``PATH`` stays missing.
    """

    env = dict(environ)
    path = env.get("PATH")
    if path is None:
        return env
    own = _launcher_bin_directories()
    if not own:
        return env
    entries = path.split(os.pathsep)
    if entries and _is_own_directory(entries[0], own):
        # Drop the one entry uv injected; preserve even an identical next entry
        # if it was already part of the caller's PATH.
        env["PATH"] = os.pathsep.join(entries[1:])
    return env


def _launcher_bin_directories() -> frozenset[str]:
    # Only an ephemeral or virtual launcher environment owns its bin directory.
    # A launcher installed into a base interpreter must not strip a system path.
    if sys.prefix == sys.base_prefix:
        return frozenset()
    candidates = [Path(sys.prefix) / "bin", Path(sys.executable).parent]
    return frozenset(
        name
        for candidate in candidates
        for name in (os.path.normpath(candidate), os.path.realpath(candidate))
    )


def _is_own_directory(entry: str, own: frozenset[str]) -> bool:
    if not entry:
        return False
    return os.path.normpath(entry) in own or os.path.realpath(entry) in own


if __name__ == "__main__":
    main()
