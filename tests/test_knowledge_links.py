from __future__ import annotations

from pathlib import Path

import pytest

from pkstack import knowledge_links
from pkstack.knowledge_links import validate_local_links, validate_metadata


def _document(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_native_reference_links_and_images_resolve_without_copying_artifacts(
    tmp_path: Path,
) -> None:
    native = _document(tmp_path, ".kiro/specs/account/design.md", "# Native design\n")
    _document(tmp_path, "evidence/proof image.svg", "<svg/>\n")
    _document(
        tmp_path,
        "Wiki/knowledge/account/decisions.md",
        "---\ntype: Decision\n---\n"
        "Read the [native design][spec].\n\n"
        "[spec]: ../../../.kiro/specs/account/design.md#native-design\n\n"
        "![proof](../../../evidence/proof%20image.svg)\n"
        "[source](https://example.com/never-fetched)\n"
        "`[code](missing.md)`\n\n```md\n[example](missing.md)\n```\n",
    )

    result = validate_local_links(tmp_path, tmp_path / "Wiki/knowledge")

    assert result == {"ok": True, "documents": 1, "local_links": 2, "issues": []}
    assert native.read_text() == "# Native design\n"
    assert not (tmp_path / "Wiki/knowledge/.kiro").exists()


@pytest.mark.parametrize(
    ("href", "message"),
    [
        ("../../.kiro/specs/missing.md", "does not exist"),
        ("../../../outside.md", "escapes the project root"),
        ("/absolute.md", "relative project paths"),
        ("../work/session.md", "must not link to Wiki/work"),
        ("../work/../work/session.md", "must not link to Wiki/work"),
    ],
)
def test_missing_unsafe_and_working_targets_fail(tmp_path: Path, href: str, message: str) -> None:
    _document(tmp_path, "Wiki/knowledge/index.md", f"[link]({href})\n")
    _document(tmp_path, "Wiki/work/session.md", "# ignored draft\n[broken](missing.md)")

    result = validate_local_links(tmp_path, tmp_path / "Wiki/knowledge")

    assert result["ok"] is False
    assert result["documents"] == 1
    assert message in result["issues"][0]["message"]


@pytest.mark.parametrize("href", ["../../redirect/native.md", "../../redirect/../native.md"])
def test_symlink_components_are_rejected_even_before_parent_traversal(
    tmp_path: Path, href: str
) -> None:
    workspace = tmp_path / "project"
    outside = tmp_path / "outside"
    outside.mkdir()
    _document(workspace, "Wiki/knowledge/index.md", f"[link]({href})\n")
    (workspace / "redirect").symlink_to(outside, target_is_directory=True)

    result = validate_local_links(workspace, workspace / "Wiki/knowledge")

    assert result["ok"] is False
    assert "symlink" in result["issues"][0]["message"]


def test_root_navigation_and_feature_documents_are_checked(tmp_path: Path) -> None:
    _document(tmp_path, "Wiki/index.md", "[knowledge](knowledge/index.md)\n")
    _document(tmp_path, "Wiki/knowledge/index.md", "---\ntype: Index\n---\n# Knowledge\n")
    _document(tmp_path, "Wiki/features/account.md", "[missing](../knowledge/missing.md)\n")

    result = validate_local_links(tmp_path, tmp_path / "Wiki/knowledge")

    assert result["ok"] is False
    assert result["documents"] == 3
    assert result["issues"][0]["path"] == "Wiki/features/account.md"


def test_same_document_and_native_heading_anchors_are_checked(tmp_path: Path) -> None:
    _document(tmp_path, ".kiro/specs/account/design.md", "# Native design\n## API\n## API\n")
    source = _document(
        tmp_path,
        "Wiki/knowledge/account.md",
        "---\ntype: Decision\n---\n# Account\n"
        "[here](#account)\n[native](../../.kiro/specs/account/design.md#api-1)\n",
    )
    assert validate_local_links(tmp_path, tmp_path / "Wiki/knowledge")["ok"]
    source.write_text(source.read_text() + "[missing](#not-a-heading)\n")
    result = validate_local_links(tmp_path, tmp_path / "Wiki/knowledge")
    assert not result["ok"]
    assert "heading anchor does not exist" in result["issues"][0]["message"]


def test_repeated_targets_reuse_heading_parsing_but_still_read_each_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _document(tmp_path, "design.md", "# Design\n## API\n## API\n")
    _document(
        tmp_path,
        "Wiki/knowledge/page.md",
        "[one](../../design.md#design)\n[two](../../design.md#api-1)\n",
    )
    parse_calls = []
    reads = []
    original_parse = knowledge_links._heading_anchors
    original_read = knowledge_links._read_bounded_bytes

    def parse(text, parser):
        parse_calls.append(text)
        return original_parse(text, parser)

    def read(path, **kwargs):
        reads.append(path)
        return original_read(path, **kwargs)

    monkeypatch.setattr(knowledge_links, "_heading_anchors", parse)
    monkeypatch.setattr(knowledge_links, "_read_bounded_bytes", read)
    result = validate_local_links(tmp_path, tmp_path / "Wiki/knowledge")

    assert result == {"ok": True, "documents": 1, "local_links": 2, "issues": []}
    assert reads.count(target) == 2
    assert len(parse_calls) == 1


def test_changed_target_is_rechecked_within_and_between_validations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _document(tmp_path, "design.md", "# Before\n")
    _document(
        tmp_path,
        "Wiki/knowledge/page.md",
        "[first](../../design.md#before)\n[second](../../design.md#after)\n",
    )
    original_read = knowledge_links._read_bounded_bytes
    target_reads = 0

    def read(path, **kwargs):
        nonlocal target_reads
        if path == target:
            target_reads += 1
            if target_reads == 2:
                target.write_text("# After\n")
        return original_read(path, **kwargs)

    monkeypatch.setattr(knowledge_links, "_read_bounded_bytes", read)
    assert validate_local_links(tmp_path, tmp_path / "Wiki/knowledge")["ok"]
    result = validate_local_links(tmp_path, tmp_path / "Wiki/knowledge")
    assert not result["ok"]
    assert len(result["issues"]) == 1
    assert result["issues"][0]["target"] == "../../design.md#before"


@pytest.mark.parametrize(
    "frontmatter",
    [
        "",
        "---\ntype: Decision\n",
        "---\ntype: ''\n---\n",
        "---\ntype: Decision\ntype: Concept\n---\n",
        "---\ntype: Decision\ntags: wrong\n---\n",
        "---\ntype: Decision\ntitle: []\n---\n",
        "---\ntype: Decision\nokf_version: '999'\n---\n",
    ],
)
def test_invalid_minimum_metadata_fails_locally(tmp_path: Path, frontmatter: str) -> None:
    _document(tmp_path, "Wiki/knowledge/page.md", frontmatter + "# Page\n")
    result = validate_metadata(tmp_path, tmp_path / "Wiki/knowledge")
    assert not result["ok"]
    assert len(result["issues"]) == 1


def test_unknown_metadata_is_preserved_and_drafts_are_excluded(tmp_path: Path) -> None:
    source = _document(
        tmp_path,
        "Wiki/knowledge/page.md",
        "---\ntype: CustomConcept\nproject_specific:\n  flags: [one, two]\n---\n# Page\n",
    )
    _document(tmp_path, "Wiki/work/draft.md", "No frontmatter required for a working draft.")
    before = source.read_bytes()
    result = validate_metadata(tmp_path, tmp_path / "Wiki/knowledge")
    assert result == {"ok": True, "documents": 1, "issues": []}
    assert source.read_bytes() == before
