"""Offline installation and instruction-contract checks, not live Kiro proof."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from markdown_it import MarkdownIt

from pkstack import knowledge
from pkstack.bootstrap import bootstrap_project
from pkstack.features import _frontmatter
from pkstack.knowledge_links import validate_metadata
from pkstack.knowledge_payload import snapshot_sources
from pkstack.upstreams import _validate_source_inventory_document

POWER = Path(__file__).resolve().parents[1] / "powers" / "pkstack"
LOCAL_SOURCE = "skills/engineering/setup-matt-pocock-skills/issue-tracker-local.md"


def test_wayfinder_source_inventory_matches_verified_blobs_in_canonical_order() -> None:
    inventory = json.loads((POWER / "metadata/mattpocock-wayfinder-source-parity.json").read_text())
    identities: dict[str, tuple[str, str, str, int | None]] = {
        "SKILL.md": ("blob", "100644", "812805b760baf328db0ebdef6f3807e381f97016", 11908),
        "agents/openai.yaml": (
            "blob",
            "100644",
            "b37544751e0570f9df8de6c02aef238de8c3e1e0",
            144,
        ),
    }
    _validate_source_inventory_document(
        inventory, expected_pinned=identities, expected_current=identities
    )


def test_router_rename_does_not_silently_prune_an_old_installation(tmp_path: Path) -> None:
    installed = bootstrap_project(tmp_path, power_root=POWER)
    assert installed.ok
    receipt_path = tmp_path / ".pkstack/bootstrap.json"
    receipt = json.loads(receipt_path.read_text())
    retired = tmp_path / ".kiro/skills/pkstack/SKILL.md"
    retired.parent.mkdir()
    retired.write_text("User-preserved old router\n")
    receipt["files"][".kiro/skills/pkstack/SKILL.md"] = hashlib.sha256(
        retired.read_bytes()
    ).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    before = receipt_path.read_bytes()
    result = bootstrap_project(tmp_path, power_root=POWER, update_managed=True)
    assert not result.ok
    assert result.stale_managed == [".kiro/skills/pkstack/SKILL.md"]
    assert retired.read_text() == "User-preserved old router\n"
    assert receipt_path.read_bytes() == before


def test_markdown_reference_attributes_its_separate_catalog_source() -> None:
    tree = json.loads((POWER / "metadata/mattpocock-catalog-tree.json").read_text())
    source = next(entry for entry in tree["tree"] if entry["path"] == LOCAL_SOURCE)
    assert source == {
        "path": LOCAL_SOURCE,
        "sha": "0209a19af92c9c485cf3acc3d9e253171517ea17",
        "size": 1810,
        "mode": "100644",
        "type": "blob",
    }
    bundle = json.loads((POWER / "metadata/mattpocock-wayfinder-bundle-manifest.json").read_text())
    reference = next(item for item in bundle["files"] if item["path"] == "references/markdown.md")
    assert reference["source_path"] == LOCAL_SOURCE
    inventory = json.loads((POWER / "metadata/mattpocock-wayfinder-source-parity.json").read_text())
    assert {entry["path"] for entry in inventory["files"]} == {"SKILL.md", "agents/openai.yaml"}


def test_wayfinder_installs_with_new_router_and_unchanged_agent(tmp_path: Path) -> None:
    result = bootstrap_project(tmp_path, power_root=POWER)
    assert result.ok
    for relative in (
        "skills/wayfinder/SKILL.md",
        "skills/wayfinder/references/github.md",
        "skills/wayfinder/references/markdown.md",
        "skills/poteto-kiro-mode/SKILL.md",
    ):
        assert (tmp_path / ".kiro" / relative).read_bytes() == (POWER / relative).read_bytes()
    assert not (tmp_path / ".kiro/skills/pkstack").exists()
    assert (tmp_path / ".kiro/agents/pkstack.json").is_file()
    assert "/Wiki/work/" in (tmp_path / ".gitignore").read_text()
    assert not (tmp_path / "Wiki/work").exists()
    second = bootstrap_project(tmp_path, power_root=POWER, dry_run=True, update_managed=True)
    assert second.ok and not second.created and not second.updated


def test_wayfinder_retains_shared_authority_and_github_recovery_contract() -> None:
    skill = " ".join((POWER / "skills/wayfinder/SKILL.md").read_text().split())
    operations = " ".join((POWER / "skills/wayfinder/references/github.md").read_text().split())
    for requirement in (
        "Native Plan is read-only",
        "open, unclaimed children whose blockers are resolved",
        "one decision ticket per session",
        "not an atomic session lock",
        "reconcile known partial publication",
        "previously verified claim",
        "closed state is not evidence",
        "no in-scope fog remains",
        "do not create a fallback board",
        "default to local Markdown",
        "remote alone does not select a tracker",
        "unsupported tracker needs a supported choice",
        "map URL, issue number, or local path",
        "not a second ticket ledger",
        "separately from ticket resolution",
        "must not duplicate decisions",
    ):
        assert requirement in skill
    for requirement in (
        "--hostname github.com",
        "sub_issue_id",
        "dependencies/blocked_by",
        "Integer `issue_id`",
        "not an empty list",
        "do not reparent",
        "closed-but-unindexed",
        "matching login names alone",
        "creation response is lost",
    ):
        assert requirement.casefold() in operations.casefold()
    assert skill.index("reconcile known partial publication") < skill.index(
        "Select the first eligible child"
    )


def test_markdown_reference_retains_dependency_ownership_and_recovery_contract() -> None:
    """Guard the authored contract; this does not execute an agent or a tracker engine."""
    reference = " ".join((POWER / "skills/wayfinder/references/markdown.md").read_text().split())
    for requirement in (
        "resumes in place without migration or deletion",
        "reject symlinks and path traversal",
        "numeric IDs must be unique",
        "Select by numeric ID",
        "dependency cycles",
        "A retired question",
        "does not satisfy a dependency",
        "one writer for the map",
        "claimed file without owner evidence is not free",
        "explicit owner authorization",
        "not reopening or repeating work",
        "reuse it instead of appending the same answer",
        "Report map readiness and knowledge capture separately",
    ):
        assert requirement in reference


def _ticket_example() -> str:
    reference = (POWER / "skills/wayfinder/references/markdown.md").read_text()
    examples = [
        token.content
        for token in MarkdownIt("commonmark").parse(reference)
        if token.type == "fence" and token.info == "markdown"
    ]
    assert len(examples) == 1
    return examples[0]


def test_shipped_ticket_example_separates_document_metadata_from_working_state(
    tmp_path: Path,
) -> None:
    example = _ticket_example()
    path = tmp_path / "Wiki/knowledge/example.md"
    path.parent.mkdir(parents=True)
    path.write_text(example)
    metadata, body = _frontmatter(example, path=path)
    assert metadata == {"type": "wayfinder-ticket", "title": "Resolve the API retry guarantee"}
    assert "status" not in metadata  # Working state is not OKF trust/lifecycle metadata.
    assert "Status: open" in body and "Blocked by: none" in body
    assert validate_metadata(tmp_path, path.parent)["ok"]


@pytest.mark.parametrize("backend", ["markdown", "github"])
def test_curated_resolution_is_retrievable_without_its_working_map(
    tmp_path: Path, backend: str
) -> None:
    """Validate representative retained artifacts, not an automatic capture implementation."""
    assert bootstrap_project(tmp_path, power_root=POWER).ok
    work = tmp_path / "Wiki/work/import-redesign"
    (work / "issues").mkdir(parents=True)
    map_path = work / "map.md"
    map_path.write_text("---\ntype: wayfinder-map\n---\n# Working map\n[bad draft](absent.md)\n")
    ticket = work / "issues/01-retry.md"
    ticket.write_text(
        _ticket_example().replace("Status: open", "Status: resolved")
        + "\n## Answer\nRetain retries only after the API guarantee is confirmed.\n"
        + "[Retained decision](../../../knowledge/imports/decisions.md)\n"
    )
    topic = tmp_path / "Wiki/knowledge/imports"
    topic.mkdir(parents=True)
    evidence = topic / "evidence.md"
    evidence.write_text(
        "---\ntype: observation\ntitle: Retry contract fixture\n---\n"
        "# Retry contract\nThis fixture documents only the idempotent operation.\n"
    )
    decision = topic / "decisions.md"
    content = (
        "---\ntype: decision\ntitle: Retry boundary\ncustom_owner: imports\n---\n"
        "# Retry boundary\nAccepted decision: retry only the idempotent operation.\n"
        "Alternative rejected: retrying every request could duplicate a side effect.\n"
        "[Inspected evidence](evidence.md#retry-contract).\n"
        "Open question: the promotion owner is not yet decided.\n"
        "Implementation status: unverified.\n"
    )
    if backend == "github":
        content += "[Resolution](https://github.com/example/project/issues/7#issuecomment-42).\n"
    decision.write_text(content)
    before = {path: path.read_bytes() for path in (decision, evidence)}

    result = knowledge.validate(tmp_path)
    assert result["ok"], result
    documents = snapshot_sources(tmp_path)
    assert "Wiki/knowledge/imports/decisions.md" in documents
    assert not any(path.startswith("Wiki/work/") for path in documents)
    # Disposable working state can disappear without breaking retained knowledge.
    ticket.unlink()
    map_path.unlink()
    assert knowledge.validate(tmp_path)["ok"]
    assert snapshot_sources(tmp_path) == documents
    assert {path: path.read_bytes() for path in before} == before

    decision.write_text(content + "[Working map](../../work/import-redesign/map.md)\n")
    failed = knowledge.validate(tmp_path)
    assert not failed["ok"]
    assert any(
        "must not link to Wiki/work" in issue["message"]
        for issue in failed["local_links"]["issues"]
    )
