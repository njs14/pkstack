"""Bounded source snapshots and independently checked knowledge answers.

There is no index or ranking algorithm here. The Kiro worker selects passages;
this module owns which documents it can see and which results can be returned.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any

from pkstack.features import FeatureMapError, _read_bounded_bytes
from pkstack.knowledge_layout import out_of_layout_documents
from pkstack.paths import WorkspacePathError, ensure_tree_no_symlinks

SOURCE_ROOTS = ("Wiki/knowledge", "Wiki/features", ".kiro/specs")
MAX_DOCUMENT_BYTES = 512 * 1024
MAX_CORPUS_BYTES = 4 * 1024 * 1024
MAX_DOCUMENTS = 256
MAX_RESPONSE_BYTES = 64 * 1024


class KnowledgeRuntimeError(RuntimeError):
    """The bounded knowledge task could not produce usable evidence."""


def snapshot_sources(root: Path) -> dict[str, bytes]:
    """Read only retained knowledge, feature records, and native Markdown specs."""

    root = root.resolve()
    documents: dict[str, bytes] = {}
    total = 0
    try:
        legacy = out_of_layout_documents(root)
        if legacy:
            raise KnowledgeRuntimeError(
                "legacy Wiki knowledge would be omitted; migrate it into Wiki/knowledge first: "
                + ", ".join(legacy[:10])
            )
        for name in SOURCE_ROOTS:
            directory = ensure_tree_no_symlinks(root, Path(name))
            if not directory.exists():
                continue
            for path in sorted(directory.rglob("*")):
                if path.suffix.lower() != ".md":
                    continue
                if len(documents) >= MAX_DOCUMENTS:
                    raise KnowledgeRuntimeError(
                        f"corpus exceeds {MAX_DOCUMENTS} documents; retrieval is incomplete"
                    )
                value = _read_bounded_bytes(
                    path, limit=MAX_DOCUMENT_BYTES, label="knowledge source"
                )
                value.decode("utf-8", errors="strict")
                total += len(value)
                if total > MAX_CORPUS_BYTES:
                    raise KnowledgeRuntimeError(
                        "knowledge corpus exceeds 4 MiB; retrieval is incomplete"
                    )
                documents[path.relative_to(root).as_posix()] = value
    except (WorkspacePathError, FeatureMapError, UnicodeError, OSError) as exc:
        raise KnowledgeRuntimeError(str(exc)) from exc
    if not documents:
        raise KnowledgeRuntimeError("no retained knowledge, feature records, or native specs found")
    return documents


def write_snapshot(destination: Path, documents: dict[str, bytes]) -> None:
    for name, content in documents.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        path.chmod(0o400)


def confirm_sources_unchanged(root: Path, documents: dict[str, bytes]) -> None:
    """Reject a result if the source set or any source changed during the task."""

    if snapshot_sources(root) != documents:
        raise KnowledgeRuntimeError(
            "knowledge sources changed during retrieval; run the task again"
        )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KnowledgeRuntimeError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise KnowledgeRuntimeError(f"non-JSON number: {value}")


def estimate_context_tokens(context: dict[str, Any]) -> int:
    """Estimate returned context only; this does not measure internal model use."""

    encoded = json.dumps(context, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return math.ceil(len(encoded) / 4)


def verify_answer(raw: str, documents: dict[str, bytes], *, budget: int) -> dict[str, Any]:
    if len(raw.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise KnowledgeRuntimeError("knowledge response exceeded the bounded capture limit")
    body = raw.strip()
    # ACP streams may contain a whole fenced final document. Extra prose, multiple
    # documents, and partial JSON remain errors; never fish a plausible object out.
    if body.startswith("```json\n") and body.endswith("\n```"):
        body = body[8:-4]
    try:
        result = json.loads(
            body, object_pairs_hook=_unique_object, parse_constant=_invalid_constant
        )
    except (ValueError, RecursionError) as exc:
        raise KnowledgeRuntimeError("knowledge worker did not return a single JSON answer") from exc
    if not isinstance(result, dict) or set(result) != {
        "answer",
        "sources",
        "uncertainties",
        "incomplete",
    }:
        raise KnowledgeRuntimeError("knowledge answer has an unsupported shape")
    if not isinstance(result["answer"], str) or len(result["answer"]) > 16_000:
        raise KnowledgeRuntimeError("knowledge answer must be a bounded string")
    if type(result["incomplete"]) is not bool:
        raise KnowledgeRuntimeError("knowledge incomplete flag must be a boolean")
    if result["incomplete"]:
        raise KnowledgeRuntimeError("knowledge worker reported incomplete execution")
    uncertainties = result["uncertainties"]
    if (
        not isinstance(uncertainties, list)
        or len(uncertainties) > 16
        or any(not isinstance(item, str) or not item.strip() for item in uncertainties)
    ):
        raise KnowledgeRuntimeError("knowledge uncertainties must be bounded nonempty strings")
    sources = result["sources"]
    if not isinstance(sources, list) or len(sources) > 16:
        raise KnowledgeRuntimeError("knowledge sources must be a bounded collection")
    if result["answer"].strip() and not sources:
        raise KnowledgeRuntimeError("a substantive knowledge answer requires source passages")
    if not result["answer"].strip() and not uncertainties:
        raise KnowledgeRuntimeError("an unanswered question must state what remains unknown")
    verified: list[dict[str, Any]] = []
    identities: set[tuple[str, str]] = set()
    for source in sources:
        if not isinstance(source, dict) or set(source) != {"path", "quote"}:
            raise KnowledgeRuntimeError("each source must contain only a path and an exact quote")
        name, quote = source["path"], source["quote"]
        if not isinstance(name, str) or name not in documents:
            raise KnowledgeRuntimeError("knowledge worker cited an excluded or unknown source")
        # Exact membership also rejects absolute paths, traversal, and URI aliases.
        if PurePosixPath(name).as_posix() != name:
            raise KnowledgeRuntimeError("knowledge worker cited a noncanonical source path")
        if not isinstance(quote, str) or not quote.strip() or len(quote) > 8_000:
            raise KnowledgeRuntimeError("knowledge source quote must be a bounded nonempty string")
        identity = (name, quote)
        if identity in identities:
            raise KnowledgeRuntimeError("knowledge worker repeated a source passage")
        identities.add(identity)
        text = documents[name].decode("utf-8")
        offset = text.find(quote)
        if offset < 0 and "\\n" in quote and quote.replace("\\n", "\n") in text:
            raise KnowledgeRuntimeError(
                f"quote in {name} contains literal backslash-n characters; "
                "encode real newlines correctly in JSON or use a single source line substring"
            )
        if offset < 0 or text.find(quote, offset + 1) >= 0:
            raise KnowledgeRuntimeError(
                f"source quote is missing or ambiguous in {name}; "
                "use a unique exact substring, preserving all original whitespace"
            )
        verified.append(
            {
                "path": name,
                "quote": quote,
                "lineStart": text.count("\n", 0, offset) + 1,
                "lineEnd": text.count("\n", 0, offset + len(quote) - 1) + 1,
                "contentSha256": hashlib.sha256(documents[name]).hexdigest(),
            }
        )
    result["sources"] = verified
    if estimate_context_tokens(result) > budget:
        raise KnowledgeRuntimeError("verified knowledge answer exceeds the returned-context budget")
    return result
