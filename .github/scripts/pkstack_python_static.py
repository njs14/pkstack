#!/usr/bin/env python3
"""One reusable static gate for every maintained first-party Python surface.

Shared by the CI policy lane and both upstream-candidate static sections so a
surface cannot be covered in one place and omitted in another. Python embedded
in maintained shell scripts and workflow `run:` steps is materialized into a
temporary directory for static analysis only; the extracted text is never
imported, executed, or evaluated, and the trusted runtime staging of those
heredocs is left exactly as it is.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[2]
POWER = "powers/pkstack"
POWER_PATHS = (
    "src",
    "tests",
    "benchmarks",
    "examples",
    "skills/pkstack-setup/scripts/setup_pkstack.py",
)
LOCKED = ("uv", "run", "--frozen", "--project", POWER)
# Embedded bodies target the same minimum interpreter as the rest of the repository.
EMBEDDED_PYTHON_VERSION = "3.11"
# `<<<` is a here-string, not a here-document; a here-document delimiter is a word.
HEREDOC = re.compile(
    r"(?<!<)<<(?!<)(-?)\s*(?P<quote>['\"]?)(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?P=quote)"
)
PYTHON_COMMAND = re.compile(r"(?:^|[\s|&;(])(?:[\w./-]*/)?python(?:3(?:\.\d+)?)?(?=\s|$)")
# Delimiters that announce Python even when the command line is not recognized.
PYTHON_DELIMITERS = frozenset({"PY", "PYTHON", "PYCODE"})
RUN_BLOCK = re.compile(r"^(?P<indent>\s*)run:\s*(?P<style>\|-?|>-?)?\s*$")


class StaticCheckError(RuntimeError):
    """A maintained Python surface could not be checked, or did not pass."""


class EmbeddedBody(NamedTuple):
    """One quoted Python here-document found in a maintained shell surface."""

    origin: str
    line: int
    text: str

    @property
    def name(self) -> str:
        """A deterministic staged filename that encodes the exact origin."""
        slug = re.sub(r"[^A-Za-z0-9]+", "_", self.origin).strip("_")
        return f"{slug}__L{self.line}.py"


def _fail(origin: str, line: int, reason: str) -> StaticCheckError:
    return StaticCheckError(f"{origin}:{line}: {reason}")


def _command_lines(lines: list[str], index: int) -> str:
    """Join a command that may be split across backslash continuation lines."""
    start = index
    while start > 0 and lines[start - 1].rstrip().endswith("\\"):
        start -= 1
    return " ".join(line.rstrip().removesuffix("\\") for line in lines[start : index + 1])


def _run_block_ranges(lines: list[str], origin: str) -> list[tuple[int, int]]:
    """Line ranges of workflow `run:` step scripts, which are literal block scalars."""
    ranges: list[tuple[int, int]] = []
    index = 0
    while index < len(lines):
        match = RUN_BLOCK.match(lines[index])
        if match is None:
            index += 1
            continue
        indent = len(match.group("indent"))
        end = index + 1
        while end < len(lines) and (
            not lines[end].strip() or len(lines[end]) - len(lines[end].lstrip()) > indent
        ):
            end += 1
        style = match.group("style")
        if style not in {"|", "|-"}:
            for offset in range(index, end):
                if HEREDOC.search(lines[offset]):
                    raise _fail(origin, offset + 1, "here-document in a non-literal run block")
        else:
            ranges.append((index + 1, end))
        index = end
    return ranges


def _extract_from_lines(
    lines: list[str], origin: str, allowed: list[tuple[int, int]] | None
) -> list[EmbeddedBody]:
    bodies: list[EmbeddedBody] = []
    for index, line in enumerate(lines):
        match = HEREDOC.search(line)
        if match is None:
            continue
        inside = allowed is None or any(start <= index < end for start, end in allowed)
        delimiter = match.group("name")
        command = _command_lines(lines, index)
        is_python = PYTHON_COMMAND.search(command) is not None
        if not is_python and delimiter not in PYTHON_DELIMITERS:
            continue
        if len(list(HEREDOC.finditer(command))) != 1:
            raise _fail(origin, index + 1, "ambiguous multiple here-documents on a Python command")
        if not inside:
            raise _fail(origin, index + 1, "Python here-document outside a run step script")
        if not is_python:
            raise _fail(
                origin,
                index + 1,
                f"ambiguous Python here-document: delimiter {delimiter!r} with"
                f" unrecognized command {command.strip()!r}",
            )
        if match.group(1) == "-":
            raise _fail(origin, index + 1, "unsupported tab-stripping (<<-) Python here-document")
        if not match.group("quote"):
            raise _fail(
                origin, index + 1, "unsupported unquoted Python here-document; the shell expands it"
            )
        bodies.append(_body(lines, index, origin, delimiter))
    return bodies


def _body(lines: list[str], index: int, origin: str, delimiter: str) -> EmbeddedBody:
    """Read one here-document body, removing the literal block indentation."""
    terminator = re.compile(rf"^(?P<indent>[ ]*){re.escape(delimiter)}$")
    for end in range(index + 1, len(lines)):
        found = terminator.match(lines[end])
        if found is None:
            continue
        indent = found.group("indent")
        if not lines[index].startswith(indent):
            raise _fail(origin, index + 1, "here-document indentation differs from its command")
        body = []
        for offset in range(index + 1, end):
            raw = lines[offset]
            if raw.strip() and not raw.startswith(indent):
                raise _fail(origin, offset + 1, "here-document line is outside the block indent")
            body.append(raw[len(indent) :] if raw.strip() else "")
        return EmbeddedBody(origin, index + 1, "".join(f"{item}\n" for item in body))
    raise _fail(origin, index + 1, f"unterminated Python here-document ({delimiter})")


def embedded_bodies(root: Path) -> list[EmbeddedBody]:
    """Every maintained embedded Python body, in a deterministic order."""
    root = Path(root)
    bodies: list[EmbeddedBody] = []
    for path in sorted((root / ".github/scripts").glob("*.sh")):
        origin = path.relative_to(root).as_posix()
        bodies += _extract_from_lines(path.read_text(encoding="utf-8").splitlines(), origin, None)
    workflows = root / ".github/workflows"
    for path in sorted([*workflows.glob("*.yml"), *workflows.glob("*.yaml")]):
        origin = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        bodies += _extract_from_lines(lines, origin, _run_block_ranges(lines, origin))
    return bodies


def run(command: list[str], cwd: Path) -> None:
    print("+", " ".join(command), flush=True)
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise StaticCheckError(f"static check failed: {' '.join(command)}")


def check_bodies(root: Path, bodies: list[EmbeddedBody]) -> None:
    """Lint, format-check, and type-check staged copies without ever running them."""
    root = Path(root)
    if not bodies:
        raise StaticCheckError("no embedded Python was found in the maintained shell surfaces")
    with tempfile.TemporaryDirectory(prefix="pkstack-embedded-python-") as raw:
        stage = Path(raw)
        for body in bodies:
            print(f"  staged {body.name} <- {body.origin}:{body.line}", flush=True)
            (stage / body.name).write_text(body.text, encoding="utf-8")
        config = str(root / "ruff.toml")
        # The staged directory carries no configuration of its own, so the repository
        # rule set is passed explicitly and ty is pinned to the supported version.
        locked = ["uv", "run", "--frozen", "--project", str(root / POWER)]
        run([*locked, "ruff", "check", "--config", config, "--no-cache", str(stage)], root)
        run(
            [*locked, "ruff", "format", "--check", "--config", config, "--no-cache", str(stage)],
            root,
        )
        run([*locked, "ty", "check", "--python-version", EMBEDDED_PYTHON_VERSION, "."], stage)


def static_commands(root: Path) -> list[tuple[Path, list[str]]]:
    """Every locked lint, format and type command for checked-in Python files."""
    power = Path(root) / POWER
    return [
        (power, ["uv", "lock", "--check"]),
        (power, ["uv", "run", "--frozen", "ruff", "check", *POWER_PATHS]),
        (power, ["uv", "run", "--frozen", "ruff", "format", "--check", *POWER_PATHS]),
        (power, ["uv", "run", "--frozen", "ty", "check"]),
        # Workflow scripts live outside the Power project, so they are checked from
        # the repository root against `ruff.toml`/`ty.toml` while still running the
        # locked analyzers from the Power environment.
        (Path(root), [*LOCKED, "ruff", "check", ".github"]),
        (Path(root), [*LOCKED, "ruff", "format", "--check", ".github"]),
        (Path(root), [*LOCKED, "ty", "check"]),
    ]


def run_static_checks(root: Path) -> None:
    root = Path(root)
    for cwd, command in static_commands(root):
        run(command, cwd)
    check_bodies(root, embedded_bodies(root))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument(
        "--embedded-only",
        action="store_true",
        help="check only Python embedded in shell scripts and workflow run steps",
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if args.embedded_only:
        check_bodies(root, embedded_bodies(root))
    else:
        run_static_checks(root)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (StaticCheckError, OSError) as error:
        print(f"PKStack Python static gate failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
