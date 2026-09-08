from pathlib import Path

import pytest

from pkstack.bootstrap import _has_legacy_knowledge
from pkstack.knowledge import _layout
from pkstack.knowledge_layout import out_of_layout_documents
from pkstack.knowledge_payload import KnowledgeRuntimeError, snapshot_sources
from pkstack.paths import WorkspacePathError


def test_all_consumers_share_case_insensitive_repository_relative_inventory(tmp_path: Path) -> None:
    documents = ["Wiki/NOTES.MD", "Wiki/domain/terms.md", "Wiki/domain/DEEP.Md"]
    for relative in [*documents, "Wiki/index.md", "Wiki/knowledge/topic.md", "Wiki/work/task.MD"]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("User-owned material.\n")
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    assert out_of_layout_documents(tmp_path) == sorted(documents)
    assert _layout(tmp_path)["legacy_documents"] == sorted(documents)
    assert _has_legacy_knowledge(tmp_path)
    with pytest.raises(KnowledgeRuntimeError, match=r"Wiki/NOTES\.MD"):
        snapshot_sources(tmp_path)
    assert all(path.read_bytes() == content for path, content in before.items())


@pytest.mark.parametrize("target", ["notes.MD", "folder", "knowledge"])
def test_all_consumers_reject_wiki_symlinks(tmp_path: Path, target: str) -> None:
    root = tmp_path / "project"
    wiki = root / "Wiki"
    wiki.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("private")
    (wiki / target).symlink_to(outside, target_is_directory=True)
    with pytest.raises(WorkspacePathError, match="symlink"):
        out_of_layout_documents(root)
    with pytest.raises(WorkspacePathError, match="symlink"):
        _has_legacy_knowledge(root)
    assert _layout(root)["workspace_safe"] is False
    with pytest.raises(KnowledgeRuntimeError, match="symlink"):
        snapshot_sources(root)


def test_uppercase_index_is_not_the_canonical_navigation_seed(tmp_path: Path) -> None:
    wiki = tmp_path / "Wiki"
    wiki.mkdir()
    (wiki / "INDEX.MD").write_text("Retained document.\n")
    assert out_of_layout_documents(tmp_path) == ["Wiki/INDEX.MD"]
