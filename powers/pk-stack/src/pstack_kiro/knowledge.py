"""Optional process boundary to canonical OKF tooling.

This module deliberately does not implement OKF search, graphs, claims, or
registry semantics.  When ``okn`` is absent, only the narrow feature-map files
owned by PK-Stack are validated locally.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from pstack_kiro.features import validate_feature_map
from pstack_kiro.models import CommandSpec
from pstack_kiro.paths import WorkspacePathError, ensure_tree_no_symlinks
from pstack_kiro.runner import display_command, run_command


class KnowledgeError(RuntimeError):
    pass


def status(root: Path) -> dict[str, Any]:
    executable = shutil.which("okn")
    try:
        wiki = ensure_tree_no_symlinks(root, Path("Wiki"))
        workspace_safe = True
        path_error = None
    except WorkspacePathError as exc:
        wiki = root.resolve() / "Wiki"
        workspace_safe = False
        path_error = str(exc)
    return {
        "wiki": str(wiki),
        "wiki_present": workspace_safe and wiki.is_dir(),
        "workspace_safe": workspace_safe,
        "path_error": path_error,
        "okn_available": executable is not None,
        "okn_executable": executable,
        "mode": "canonical-okn" if executable else "feature-map-only",
    }


def validate(
    root: Path,
    *,
    require_okn: bool = False,
    timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    info = status(root)
    if not info["workspace_safe"]:
        raise KnowledgeError(str(info["path_error"]))
    if not info["okn_available"]:
        if require_okn:
            raise KnowledgeError(
                "okn is not installed; install a canonical OKF implementation or omit --require-okn"
            )
        feature_result = validate_feature_map(root)
        return {
            "ok": feature_result["ok"],
            "mode": "feature-map-only",
            "warning": "Broad OKF validation was not run because okn is unavailable.",
            "feature_map": feature_result,
        }

    argv = (str(info["okn_executable"]), "validate", "Wiki")
    command = CommandSpec(
        argv=argv,
        display=display_command(argv),
        source="explicit",
    )
    result = run_command(command, root=root, timeout_seconds=timeout_seconds)
    return {
        "ok": result.passed,
        "mode": "canonical-okn",
        "command": command.to_dict(),
        "result": result.to_dict(),
    }


def search(root: Path, query: str, *, timeout_seconds: float = 120.0) -> dict[str, Any]:
    normalized_query = query.strip()
    if not normalized_query:
        raise KnowledgeError("query must be non-empty")
    if normalized_query.startswith("-"):
        raise KnowledgeError(
            "query must not begin with '-' because okn could interpret it as an option"
        )
    try:
        ensure_tree_no_symlinks(root, Path("Wiki"))
    except WorkspacePathError as exc:
        raise KnowledgeError(str(exc)) from exc
    executable = shutil.which("okn")
    if not executable:
        raise KnowledgeError("okn is required for broad knowledge search")
    argv = (executable, "search", "Wiki", normalized_query)
    command = CommandSpec(argv=argv, display=display_command(argv), source="explicit")
    result = run_command(command, root=root, timeout_seconds=timeout_seconds)
    return {
        "ok": result.passed,
        "mode": "canonical-okn",
        "command": command.to_dict(),
        "result": result.to_dict(),
    }
