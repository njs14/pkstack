"""Conservative workspace path checks for repository-owned reads and writes."""

from __future__ import annotations

import os
from pathlib import Path


class WorkspacePathError(ValueError):
    """Raised when a managed path can escape through traversal or a symlink."""


def workspace_path(root: Path, path: Path) -> Path:
    """Return a lexical path inside ``root`` after rejecting symlink components.

    The check is deliberately stricter than containment after ``resolve()``:
    even a symlink that currently points back into the workspace is rejected.
    That keeps managed-file ownership auditable and prevents a repository from
    redirecting bootstrap or runtime-state writes outside its root.

    This protects against repository content, not a concurrent process racing
    the filesystem between this check and a later operation.
    """

    workspace = root.resolve()
    candidate = path if path.is_absolute() else workspace / path
    candidate = Path(os.path.abspath(candidate))
    try:
        relative = candidate.relative_to(workspace)
    except ValueError as exc:
        raise WorkspacePathError(f"managed path escapes the project root: {candidate}") from exc

    current = workspace
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise WorkspacePathError(f"managed path contains a symlink: {current}")
    return candidate


def ensure_tree_no_symlinks(root: Path, path: Path) -> Path:
    """Validate an existing project tree without following any symlink entry."""

    directory = workspace_path(root, path)
    if not directory.exists():
        return directory
    if not directory.is_dir():
        raise WorkspacePathError(f"managed tree is not a directory: {directory}")
    pending = [directory]
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                candidate = Path(entry.path)
                if entry.is_symlink():
                    raise WorkspacePathError(f"managed tree contains a symlink: {candidate}")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(candidate)
    return directory
