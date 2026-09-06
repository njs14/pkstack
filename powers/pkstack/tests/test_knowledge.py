from __future__ import annotations

import json
from pathlib import Path

import pytest

from pkstack.knowledge import KnowledgeError, search, status, validate
from pkstack.knowledge_payload import KnowledgeRuntimeError


def corpus(root: Path) -> Path:
    directory = root / "Wiki/knowledge"
    directory.mkdir(parents=True)
    (root / "Wiki/features").mkdir()
    document = directory / "decision.md"
    document.write_text("---\ntype: Decision\ncustom: preserved\n---\n# Decision\nObserve only.\n")
    (root / "Wiki/index.md").write_text(
        '---\ntype: Index\nokf_version: "0.2"\n---\n[Decision](knowledge/decision.md#decision)\n'
    )
    return document


def test_validation_is_local_even_with_legacy_and_kiro_executables_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = corpus(tmp_path)
    before = document.read_bytes()

    def prohibited(*args: object, **kwargs: object) -> None:
        raise AssertionError("local validation must not discover or invoke a runtime")

    monkeypatch.setattr("subprocess.run", prohibited)
    monkeypatch.setattr("shutil.which", prohibited)
    monkeypatch.setattr("pkstack.knowledge_acp.search", prohibited)
    result = validate(tmp_path)
    assert result["ok"] is True
    assert result["schemaVersion"] == "2"
    assert result["mode"] == "local"
    assert result["metadata"]["documents"] == 2
    assert result["local_links"]["local_links"] == 1
    assert result["feature_map"]["ok"]
    assert result["unsupportedChecks"]
    assert document.read_bytes() == before


def test_feature_failure_cannot_be_hidden_by_valid_knowledge(tmp_path: Path) -> None:
    corpus(tmp_path)
    directory = tmp_path / "Wiki/features"
    (directory / "broken.md").write_text("---\ntype: Feature\n---\n# Missing verifier\n")
    result = validate(tmp_path)
    assert result["ok"] is False
    assert result["metadata"]["ok"] is True
    assert result["feature_map"]["ok"] is False


def test_metadata_and_link_failures_both_reach_the_local_verdict(tmp_path: Path) -> None:
    document = corpus(tmp_path)
    document.write_text("---\ntype: Decision\ntags: invalid\n---\n[Missing](missing.md)\n")
    result = validate(tmp_path)
    assert result["ok"] is False
    assert result["feature_map"]["ok"] is True
    assert result["metadata"]["issues"]
    assert result["local_links"]["issues"]


def test_working_drafts_do_not_enter_validation(tmp_path: Path) -> None:
    corpus(tmp_path)
    directory = tmp_path / "Wiki/work/task"
    directory.mkdir(parents=True)
    (directory / "draft.md").write_text("No metadata. [Broken](missing.md)\n")
    result = validate(tmp_path)
    assert result["ok"] is True
    assert result["metadata"]["documents"] == 2


@pytest.mark.parametrize("durable", [True, False])
def test_unmigrated_documents_are_not_silently_omitted(tmp_path: Path, durable: bool) -> None:
    if durable:
        corpus(tmp_path)
    old = tmp_path / "Wiki/decisions/prior.md"
    old.parent.mkdir(parents=True)
    old.write_text("Prior knowledge\n")
    with pytest.raises(KnowledgeError, match="legacy Wiki knowledge would be omitted"):
        validate(tmp_path)


def test_wiki_symlink_is_rejected_without_reading_the_target(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / "Wiki").symlink_to(outside, target_is_directory=True)
    with pytest.raises(KnowledgeError, match="symlink"):
        validate(project)


def test_status_reports_unavailable_search_without_degrading_local_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus(tmp_path)
    monkeypatch.setattr(
        "pkstack.knowledge_acp.runtime_status",
        lambda root: {"available": False, "error": "Kiro is unavailable"},
    )
    info = status(tmp_path)
    assert info["mode"] == "kiro-acp"
    assert info["validation_mode"] == "local"
    assert info["runtime"]["available"] is False
    assert "okn" not in json.dumps(info)
    assert validate(tmp_path)["ok"] is True


def test_search_preserves_options_and_normalizes_runtime_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = []

    def retrieve(root: Path, query: str, **options: object) -> dict[str, object]:
        seen.append((root, query, options))
        raise KnowledgeRuntimeError("citation rejected")

    monkeypatch.setattr("pkstack.knowledge_acp.search", retrieve)
    with pytest.raises(KnowledgeError, match="citation rejected"):
        search(tmp_path, "question", budget=900, model="auto", timeout_seconds=30)
    assert seen == [(tmp_path, "question", {"budget": 900, "model": "auto", "timeout_seconds": 30})]
