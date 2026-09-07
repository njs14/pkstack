"""Local knowledge validation and one bounded native Kiro retrieval boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pkstack.features import validate_feature_map
from pkstack.knowledge_layout import out_of_layout_documents
from pkstack.knowledge_links import validate_local_links, validate_metadata
from pkstack.knowledge_payload import SOURCE_ROOTS, KnowledgeRuntimeError
from pkstack.paths import WorkspacePathError, ensure_tree_no_symlinks


class KnowledgeError(RuntimeError):
    pass


def _layout(root: Path) -> dict[str, Any]:
    root = root.resolve()
    try:
        wiki = ensure_tree_no_symlinks(root, Path("Wiki"))
        legacy_documents = out_of_layout_documents(root)
        workspace_safe = True
        path_error = None
    except WorkspacePathError as exc:
        wiki = root / "Wiki"
        legacy_documents = []
        workspace_safe = False
        path_error = str(exc)
    knowledge_root = wiki / "knowledge"
    layout_error = None
    if legacy_documents:
        layout_error = (
            "legacy Wiki knowledge would be omitted; classify and migrate these documents to "
            "Wiki/knowledge before validating or searching: " + ", ".join(sorted(legacy_documents))
        )
    return {
        "wiki": str(wiki),
        "wiki_present": workspace_safe and wiki.is_dir(),
        "knowledge_root": str(knowledge_root),
        "layout": "durable-directory" if knowledge_root.is_dir() else "uninitialized",
        "layout_error": layout_error,
        "legacy_documents": sorted(legacy_documents),
        "workspace_safe": workspace_safe,
        "path_error": path_error,
    }


def status(root: Path) -> dict[str, Any]:
    """Inspect layout and the installed retrieval runtime without a model turn."""
    from pkstack.knowledge_acp import runtime_status

    info = _layout(root)
    return {
        "schemaVersion": "2",
        "mode": "kiro-acp",
        "validation_mode": "local",
        "sourceRoots": list(SOURCE_ROOTS),
        **info,
        "runtime": runtime_status(root),
    }


def validate(root: Path) -> dict[str, Any]:
    """Validate the documented authoring profile, local links, and feature map.

    This path never discovers or invokes an external runtime, model, or validator.
    """
    root = root.resolve()
    info = _layout(root)
    if not info["workspace_safe"]:
        raise KnowledgeError(str(info["path_error"]))
    if info["layout_error"]:
        raise KnowledgeError(str(info["layout_error"]))
    knowledge_root = Path(str(info["knowledge_root"]))
    feature_result = validate_feature_map(root)
    metadata_result = validate_metadata(root, knowledge_root)
    link_result = validate_local_links(root, knowledge_root)
    return {
        "ok": feature_result["ok"] and metadata_result["ok"] and link_result["ok"],
        "schemaVersion": "2",
        "mode": "local",
        "feature_map": feature_result,
        "metadata": metadata_result,
        "local_links": link_result,
        "knowledge_root": info["knowledge_root"],
        "layout": info["layout"],
        "unsupportedChecks": [
            "Full OKF conformance, graph, lifecycle, trust, and attestation semantics",
            "External URL reachability and non-Markdown target fragments",
            "Raw HTML IDs, footnotes, and renderer-plugin anchors are not recognized",
        ],
    }


def search(
    root: Path,
    query: str,
    *,
    budget: int = 1_200,
    timeout_seconds: float = 120.0,
    model: str = "auto",
) -> dict[str, Any]:
    """Run a bounded native-authenticated Kiro knowledge task."""
    from pkstack.knowledge_acp import search as acp_search

    try:
        return acp_search(root, query, budget=budget, timeout_seconds=timeout_seconds, model=model)
    except KnowledgeRuntimeError as exc:
        raise KnowledgeError(str(exc)) from exc
