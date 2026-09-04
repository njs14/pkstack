"""Read-only repository discovery used by bootstrap and doctor."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pk_stack.paths import WorkspacePathError, ensure_tree_no_symlinks, workspace_path


def discover_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    wiki = ensure_tree_no_symlinks(root, Path("Wiki"))
    markers = {
        "python": ["pyproject.toml", "setup.py", "requirements.txt"],
        "javascript": ["package.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock"],
        "go": ["go.mod"],
        "rust": ["Cargo.toml"],
        "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "terraform": [],
    }
    languages: dict[str, list[str]] = {}
    for language, names in markers.items():
        matches = [name for name in names if _safe_exists(root, Path(name))]
        if language == "terraform":
            matches = _terraform_paths(root)
        if matches:
            languages[language] = matches

    tests = _matching_paths(
        root,
        (
            "tests",
            "test",
            "spec",
            "__tests__",
            "pytest.ini",
            "vitest.config.*",
            "playwright.config.*",
        ),
    )
    clis = _matching_paths(
        root,
        ("projectctl", "bin", "scripts", "Makefile", "justfile", "Taskfile.yml"),
    )
    verification = _matching_paths(
        root,
        ("verification", "e2e", "tests/e2e", ".github/workflows", "Wiki/features"),
    )
    kiro = {
        "present": _safe_is_dir(root, Path(".kiro")),
        "agents": _relative_files(root, root / ".kiro" / "agents"),
        "skills": _relative_files(root, root / ".kiro" / "skills"),
        "hooks": _relative_files(root, root / ".kiro" / "hooks"),
        "steering": _relative_files(root, root / ".kiro" / "steering"),
        "specs": _relative_files(root, root / ".kiro" / "specs"),
    }
    knowledge = {
        "wiki": wiki.is_dir(),
        "feature_map": _safe_is_dir(root, Path("Wiki/features")),
        "knowledge_markers": _matching_paths(root, ("okf.yaml", "okf.yml", ".okf", "Wiki")),
    }
    aws_markers = _matching_paths(
        root,
        (".bedrock_agentcore.yaml", "cdk.json", "template.yaml", "serverless.yml"),
    )

    return {
        "root": ".",
        "git": _safe_exists(root, Path(".git")),
        "languages": languages,
        "tests": tests,
        "developer_interfaces": clis,
        "verification_surfaces": verification,
        "kiro": kiro,
        "knowledge": knowledge,
        "aws": {"markers": aws_markers, "detected": bool(aws_markers)},
    }


def _matching_paths(root: Path, patterns: tuple[str, ...]) -> list[str]:
    found: set[str] = set()
    for pattern in patterns:
        if any(char in pattern for char in "*?["):
            candidates = root.glob(pattern)
        else:
            candidate = root / pattern
            candidates = [candidate] if _safe_exists(root, Path(pattern)) else []
        for path in candidates:
            workspace_path(root, path)
            found.add(str(path.relative_to(root)))
    return sorted(found)


def _relative_files(root: Path, directory: Path) -> list[str]:
    directory = workspace_path(root, directory)
    if not directory.is_dir():
        return []
    found: list[str] = []
    pending = [directory]
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                path = Path(entry.path)
                if entry.is_symlink():
                    raise WorkspacePathError(f"discovery path contains a symlink: {path}")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    found.append(str(path.relative_to(root)))
    return sorted(found)


def _safe_exists(root: Path, relative: Path) -> bool:
    return workspace_path(root, relative).exists()


def _safe_is_dir(root: Path, relative: Path) -> bool:
    return workspace_path(root, relative).is_dir()


def _terraform_paths(root: Path) -> list[str]:
    """Find a bounded set of Terraform files without following repository symlinks."""

    found: list[str] = []
    ignored = {".git", ".pk-stack", ".venv", "node_modules"}
    for directory, names, files in os.walk(root, followlinks=False):
        base = Path(directory)
        names[:] = sorted(
            name for name in names if name not in ignored and not (base / name).is_symlink()
        )
        for name in sorted(files):
            path = base / name
            if name.endswith(".tf") and not path.is_symlink():
                found.append(str(path.relative_to(root)))
                if len(found) == 50:
                    return found
    return found
