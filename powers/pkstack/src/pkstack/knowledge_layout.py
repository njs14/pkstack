"""Shared, symlink-safe inventory of retained Wiki Markdown outside topic roots."""

from pathlib import Path

from pkstack.paths import ensure_tree_no_symlinks


def out_of_layout_documents(root: Path) -> list[str]:
    """Return canonical repository-relative paths without following symlinks."""
    root = root.resolve()
    wiki = ensure_tree_no_symlinks(root, Path("Wiki"))
    return sorted(
        path.relative_to(root).as_posix()
        for path in wiki.rglob("*")
        if path.is_file()
        and path.suffix.lower() == ".md"
        and path.relative_to(wiki).parts[0] not in {"knowledge", "features", "work"}
        and path.relative_to(wiki) != Path("index.md")
    )
