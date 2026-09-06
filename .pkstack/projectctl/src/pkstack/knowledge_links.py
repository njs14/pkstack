"""Deterministic local Markdown checks. No link is fetched or executed."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from markdown_it.token import Token

from pkstack.features import FeatureMapError, _frontmatter, _read_bounded_bytes
from pkstack.paths import WorkspacePathError, workspace_path

MAX_KNOWLEDGE_DOCUMENT_BYTES = 512 * 1024


def _links(tokens: list[Token]) -> list[str]:
    targets: list[str] = []
    for token in tokens:
        if token.type in {"link_open", "image"}:
            value = token.attrGet("href" if token.type == "link_open" else "src")
            if isinstance(value, str):
                targets.append(value)
        if token.children:
            targets.extend(_links(token.children))
    return targets


def _local_target(root: Path, source: Path, href: str) -> Path | None:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path:
        return source if parsed.fragment else None
    if path.startswith("/") or "\\" in path or "\x00" in path:
        raise WorkspacePathError("local knowledge links must use relative project paths")
    target = source.parent
    # Check each component before reducing '..': a symlink followed by '..'
    # must not be hidden by lexical normalization.
    for part in path.split("/"):
        if part in {"", "."}:
            continue
        target = target.parent if part == ".." else target / part
        target = workspace_path(root, target)
    work = root / "Wiki/work"
    if target == work or work in target.parents:
        raise WorkspacePathError("retained knowledge must not link to Wiki/work")
    return target


def _body(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
        if end is not None:
            return "\n".join(lines[end + 1 :])
    return text


def _heading_anchors(text: str, parser: MarkdownIt) -> set[str]:
    """CommonMark heading text, lowercase, punctuation removed, spaces as hyphens.

    Duplicate heading slugs receive numeric suffixes. Raw HTML IDs, footnotes,
    renderer plugins, and arbitrary non-Markdown fragments are outside this check.
    """

    anchors: set[str] = set()
    tokens = parser.parse(_body(text))
    for index, token in enumerate(tokens):
        if token.type != "heading_open" or index + 1 >= len(tokens):
            continue
        children = tokens[index + 1].children or []
        label = "".join(
            item.content
            if item.type in {"text", "code_inline", "image"}
            else " "
            if item.type in {"softbreak", "hardbreak"}
            else ""
            for item in children
        )
        base = re.sub(r"[^\w -]", "", label.lower()).replace(" ", "-")
        slug, suffix = base, 0
        while slug in anchors:
            suffix += 1
            slug = f"{base}-{suffix}"
        anchors.add(slug)
    return anchors


def _documents(root: Path, knowledge_root: Path) -> set[Path]:
    paths: set[Path] = set()
    for directory in (knowledge_root, root / "Wiki/features"):
        directory = workspace_path(root, directory)
        if directory.is_dir():
            paths.update(path for path in directory.rglob("*") if path.suffix.lower() == ".md")
    index = workspace_path(root, root / "Wiki/index.md")
    if index.exists():
        paths.add(index)
    return paths


def validate_metadata(root: Path, knowledge_root: Path) -> dict[str, Any]:
    """Check the documented minimum OKF authoring profile, preserving unknown keys."""

    root = root.resolve()
    issues: list[dict[str, str]] = []
    documents = 0
    for path in sorted(_documents(root, knowledge_root)):
        if root / "Wiki/work" in path.parents:
            continue
        relative = path.relative_to(root).as_posix()
        try:
            path = workspace_path(root, path)
            text = _read_bounded_bytes(
                path, limit=MAX_KNOWLEDGE_DOCUMENT_BYTES, label="knowledge document"
            ).decode("utf-8", errors="strict")
            metadata, _ = _frontmatter(text, path=Path(relative))
            if not isinstance(metadata.get("type"), str) or not metadata["type"].strip():
                raise FeatureMapError("knowledge metadata requires a nonempty descriptive type")
            for key in ("title", "description"):
                if key in metadata and (
                    not isinstance(metadata[key], str) or not metadata[key].strip()
                ):
                    raise FeatureMapError(f"optional {key} must be a nonempty string")
            if "tags" in metadata and (
                not isinstance(metadata["tags"], list)
                or any(not isinstance(tag, str) or not tag.strip() for tag in metadata["tags"])
            ):
                raise FeatureMapError("optional tags must be a list of nonempty strings")
            if "okf_version" in metadata and metadata["okf_version"] != "0.2":
                raise FeatureMapError('supported authoring profile uses okf_version: "0.2"')
            documents += 1
        except (WorkspacePathError, FeatureMapError, UnicodeError, OSError) as exc:
            issues.append({"path": relative, "message": str(exc)})
    return {"ok": not issues, "documents": documents, "issues": issues}


def validate_local_links(root: Path, knowledge_root: Path) -> dict[str, Any]:
    """Check retained Wiki and feature links, excluding working documents.

    CommonMark inline/reference links and images are checked; inline/fenced
    code and external URLs are left alone. Local Markdown heading anchors follow
    the explicit convention in ``_heading_anchors``; other renderers are not checked.
    """

    root = root.resolve()
    wiki = root / "Wiki"
    work = wiki / "work"
    paths = _documents(root, knowledge_root)
    parser = MarkdownIt("commonmark")
    issues: list[dict[str, str]] = []
    documents = 0
    links = 0
    for path in sorted(paths):
        if work in path.parents:
            continue
        relative = path.relative_to(root).as_posix()
        try:
            path = workspace_path(root, path)
            text = _read_bounded_bytes(
                path, limit=MAX_KNOWLEDGE_DOCUMENT_BYTES, label="knowledge document"
            ).decode("utf-8", errors="strict")
        except (WorkspacePathError, FeatureMapError, UnicodeError) as exc:
            issues.append({"path": relative, "message": str(exc)})
            continue
        documents += 1
        for href in _links(parser.parse(_body(text))):
            try:
                target = _local_target(root, path, href)
                if target is None:
                    continue
                links += 1
                if not (target.is_file() or target.is_dir()):
                    raise WorkspacePathError(f"local link target does not exist: {href}")
                fragment = unquote(urlsplit(href).fragment)
                if fragment and target.suffix.lower() == ".md" and target.is_file():
                    target_text = _read_bounded_bytes(
                        target, limit=MAX_KNOWLEDGE_DOCUMENT_BYTES, label="linked Markdown"
                    ).decode("utf-8", errors="strict")
                    if fragment not in _heading_anchors(target_text, parser):
                        raise WorkspacePathError(f"Markdown heading anchor does not exist: {href}")
            except (WorkspacePathError, FeatureMapError, ValueError, OSError) as exc:
                issues.append({"path": relative, "target": href, "message": str(exc)})
    return {"ok": not issues, "documents": documents, "local_links": links, "issues": issues}
