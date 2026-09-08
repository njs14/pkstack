from __future__ import annotations

import json
from pathlib import Path

import pytest

from pkstack.knowledge_payload import (
    KnowledgeRuntimeError,
    confirm_sources_unchanged,
    estimate_context_tokens,
    snapshot_sources,
    verify_answer,
    write_snapshot,
)


def answer(path: str = "Wiki/knowledge/decision.md", quote: str = "Observe only.") -> str:
    return json.dumps(
        {
            "answer": "The canary observes only.",
            "sources": [{"path": path, "quote": quote}],
            "uncertainties": ["The promotion owner is unknown."],
            "incomplete": False,
        }
    )


def corpus(root: Path) -> None:
    for name, text in {
        "Wiki/knowledge/decision.md": "# Decision\nObserve only.\n",
        "Wiki/features/runtime.md": "# Feature\nSee the decision.\n",
        ".kiro/specs/runtime/requirements.md": "# Requirements\nThree retries intended.\n",
        "Wiki/work/draft.md": "DO NOT RETRIEVE THIS DRAFT",
        ".kiro/hooks/untrusted.json": "DO NOT COPY THIS HOOK",
        "README.md": "DO NOT COPY ROOT INSTRUCTIONS",
    }.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def test_snapshot_contains_retained_feature_and_hidden_native_sources_only(tmp_path: Path) -> None:
    root = tmp_path / "project"
    corpus(root)
    documents = snapshot_sources(root)
    assert set(documents) == {
        "Wiki/knowledge/decision.md",
        "Wiki/features/runtime.md",
        ".kiro/specs/runtime/requirements.md",
    }
    destination = tmp_path / "copy"
    write_snapshot(destination, documents)
    assert snapshot_sources(destination) == documents
    assert not (destination / ".kiro/hooks").exists()
    confirm_sources_unchanged(root, documents)
    (root / "Wiki/knowledge/decision.md").write_text("Changed after lookup")
    with pytest.raises(KnowledgeRuntimeError, match="changed during"):
        confirm_sources_unchanged(root, documents)


@pytest.mark.parametrize("change", ["symlink-file", "symlink-root", "non-utf8", "oversized"])
def test_snapshot_rejects_unsafe_sources(tmp_path: Path, change: str) -> None:
    root = tmp_path / "project"
    corpus(root)
    path = root / "Wiki/knowledge/decision.md"
    if change == "symlink-file":
        path.unlink()
        path.symlink_to(root / "Wiki/work/draft.md")
    elif change == "symlink-root":
        path.unlink()
        path.parent.rmdir()
        path.parent.symlink_to(root / "Wiki/work", target_is_directory=True)
    elif change == "non-utf8":
        path.write_bytes(b"\xff")
    else:
        path.write_bytes(b"x" * (512 * 1024 + 1))
    with pytest.raises(KnowledgeRuntimeError):
        snapshot_sources(root)


def test_snapshot_limits_do_not_silently_omit_documents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    corpus(tmp_path)
    monkeypatch.setattr("pkstack.knowledge_payload.MAX_DOCUMENTS", 2)
    with pytest.raises(KnowledgeRuntimeError, match="incomplete"):
        snapshot_sources(tmp_path)
    monkeypatch.setattr("pkstack.knowledge_payload.MAX_DOCUMENTS", 256)
    monkeypatch.setattr("pkstack.knowledge_payload.MAX_CORPUS_BYTES", 10)
    with pytest.raises(KnowledgeRuntimeError, match="incomplete"):
        snapshot_sources(tmp_path)


def test_legacy_retained_pages_are_not_silently_hidden(tmp_path: Path) -> None:
    corpus(tmp_path)
    legacy = tmp_path / "Wiki/architecture/older-decision.md"
    legacy.parent.mkdir()
    legacy.write_text("# A retained decision in the old layout\n")
    with pytest.raises(KnowledgeRuntimeError, match="legacy Wiki knowledge would be omitted"):
        snapshot_sources(tmp_path)


def test_quotes_are_verified_and_line_numbers_derived_locally(tmp_path: Path) -> None:
    corpus(tmp_path)
    documents = snapshot_sources(tmp_path)
    result = verify_answer(answer(), documents, budget=1200)
    source = result["sources"][0]
    assert source["lineStart"] == source["lineEnd"] == 2
    assert len(source["contentSha256"]) == 64
    assert estimate_context_tokens(result) <= 1200
    assert verify_answer("```json\n" + answer() + "\n```", documents, budget=1200) == result
    with pytest.raises(KnowledgeRuntimeError, match="budget"):
        verify_answer(answer(), documents, budget=1)


@pytest.mark.parametrize(
    "name",
    [
        "Wiki/work/draft.md",
        "../outside.md",
        "/Wiki/knowledge/decision.md",
        "Wiki/knowledge/../work/draft.md",
        "Wiki/knowledge/missing.md",
    ],
)
def test_citations_must_identify_a_snapshot_member(tmp_path: Path, name: str) -> None:
    corpus(tmp_path)
    with pytest.raises(KnowledgeRuntimeError, match="excluded or unknown"):
        verify_answer(answer(name), snapshot_sources(tmp_path), budget=1200)


@pytest.mark.parametrize("quote", ["Fabricated.", "", " " * 10, "x" * 8001])
def test_fabricated_or_unbounded_quotes_are_rejected(tmp_path: Path, quote: str) -> None:
    corpus(tmp_path)
    with pytest.raises(KnowledgeRuntimeError):
        verify_answer(answer(quote=quote), snapshot_sources(tmp_path), budget=1200)


def test_repeated_quote_is_ambiguous_even_when_the_text_exists(tmp_path: Path) -> None:
    corpus(tmp_path)
    (tmp_path / "Wiki/knowledge/decision.md").write_text("Observe only.\nObserve only.\n")
    with pytest.raises(KnowledgeRuntimeError, match="ambiguous"):
        verify_answer(answer(), snapshot_sources(tmp_path), budget=1200)


@pytest.mark.parametrize(
    "mutation",
    [
        "commentary",
        "duplicate-key",
        "nan",
        "wrong-shape",
        "incomplete",
        "line-numbers",
        "duplicate-source",
        "uncited-answer",
        "empty-unknown",
        "invalid-uncertainties",
    ],
)
def test_malformed_and_incomplete_results_are_not_usable_context(
    tmp_path: Path,
    mutation: str,
) -> None:
    corpus(tmp_path)
    raw = answer()
    data = json.loads(raw)
    if mutation == "commentary":
        raw = "Here is the answer\n" + raw
    elif mutation == "duplicate-key":
        raw = raw.replace('"answer":', '"answer":"hidden", "answer":', 1)
    elif mutation == "nan":
        raw = raw.replace("false", "NaN")
    elif mutation == "wrong-shape":
        raw = "[]"
    else:
        if mutation == "incomplete":
            data["incomplete"] = True
        elif mutation == "line-numbers":
            data["sources"][0]["lineStart"] = 3
        elif mutation == "duplicate-source":
            data["sources"] *= 2
        elif mutation == "uncited-answer":
            data["sources"] = []
        elif mutation == "empty-unknown":
            data.update(answer="", sources=[], uncertainties=[])
        else:
            data["uncertainties"] = [12]
        raw = json.dumps(data)
    with pytest.raises(KnowledgeRuntimeError):
        verify_answer(raw, snapshot_sources(tmp_path), budget=1200)


def test_unknown_answer_can_be_reported_without_inventing_a_citation(tmp_path: Path) -> None:
    corpus(tmp_path)
    data = {
        "answer": "",
        "sources": [],
        "uncertainties": ["No owner is recorded."],
        "incomplete": False,
    }
    assert verify_answer(json.dumps(data), snapshot_sources(tmp_path), budget=1200) == data


def test_exact_substrings_derive_lines_without_requiring_whole_lines() -> None:
    documents = {
        "Wiki/knowledge/decision.md": b"Heading\n- A unique decision.\n  Continued here.\n"
    }
    result = verify_answer(answer(quote="unique decision.\n  Continued"), documents, budget=1200)
    assert result["sources"][0]["lineStart"] == 2
    assert result["sources"][0]["lineEnd"] == 3
    with pytest.raises(KnowledgeRuntimeError, match="missing"):
        verify_answer(answer(quote="unique decision. Continued"), documents, budget=1200)


def test_overlapping_exact_substrings_are_ambiguous() -> None:
    with pytest.raises(KnowledgeRuntimeError, match="ambiguous"):
        verify_answer(answer(quote="aa"), {"Wiki/knowledge/decision.md": b"aaa"}, budget=1200)


def test_literal_newline_escape_is_diagnosed_but_never_normalized() -> None:
    with pytest.raises(KnowledgeRuntimeError, match="literal backslash-n"):
        verify_answer(
            answer(quote="Observe\\nonly."),
            {"Wiki/knowledge/decision.md": b"Observe\nonly."},
            budget=1200,
        )
