from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from test_astral_skills import _tree_sha

from pkstack.bootstrap import _validate_curated_registry, bootstrap_project
from pkstack.upstreams import load_upstream_manifest, load_upstream_review_ledger

POWER = Path(__file__).resolve().parents[1]
ROOT = POWER.parents[1]
SOURCES = {
    "pbakaus-impeccable": (
        "impeccable",
        "dbdc470e70dbbda69f9b78ee38bc38ea1d3560b9",
        "90d9f3c53a7fb64b44d0411bc0858a111c4aac23",
    ),
    "openai-babysit-pr": (
        "babysit-pr",
        "9f70e348e0227980de97e361cce830236fb18317",
        "930db390730c900f644d054e4a322fc865437c34",
    ),
}


@pytest.mark.parametrize("source_id", SOURCES)
def test_candidate_inventory_reconstructs_exact_pinned_source(source_id: str) -> None:
    name, commit, tree = SOURCES[source_id]
    manifest = load_upstream_manifest(ROOT)
    ledger = load_upstream_review_ledger(ROOT, manifest)
    source = next(item for item in manifest.sources if item.source_id == source_id)
    review = next(item for item in ledger.sources if item.source_id == source_id)
    assert (review.genesis_commit, review.genesis_subtree_sha) == (commit, tree)
    inventory = json.loads((ROOT / source.parity_path).read_text())
    assert inventory["source"]["current"] == {
        "commit": source.commit,
        "subtree_sha": source.subtree_sha,
    }
    for revision in ("pinned", "current"):
        present = [entry for entry in inventory["files"] if entry[revision] is not None]
        assert _tree_sha(present, revision) == inventory["source"][revision]["subtree_sha"]
    assert name in _validate_curated_registry(POWER, forbidden=set())
    assert all(
        entry["disposition"] == "B"
        for entry in inventory["files"]
        if entry["path"].startswith("scripts/")
    )


def test_design_and_pr_skills_install_complete_without_upstream_runtime(tmp_path: Path) -> None:
    result = bootstrap_project(tmp_path, power_root=POWER)
    assert result.ok, result.to_dict()
    for name, _, _ in SOURCES.values():
        canonical = POWER / "skills" / name
        installed = tmp_path / ".kiro/skills" / name
        expected = {path.relative_to(canonical) for path in canonical.rglob("*") if path.is_file()}
        actual = {path.relative_to(installed) for path in installed.rglob("*") if path.is_file()}
        assert actual == expected
        assert all(path.suffix == ".md" for path in actual)
        for path in actual:
            assert (installed / path).read_bytes() == (canonical / path).read_bytes()
    assert not (tmp_path / ".impeccable").exists()
    assert not (tmp_path / ".codex").exists()
    second = bootstrap_project(tmp_path, power_root=POWER)
    assert second.ok and not second.created and not second.updated, second.to_dict()


@pytest.mark.parametrize("source_id", SOURCES)
def test_candidate_bundle_rejects_changed_reference_before_install(
    tmp_path: Path, source_id: str
) -> None:
    name, _, _ = SOURCES[source_id]
    candidate = tmp_path / "power"
    shutil.copytree(POWER / "docs", candidate / "docs")
    shutil.copytree(POWER / "skills", candidate / "skills")
    reference = next((candidate / "skills" / name / "references").glob("*.md"))
    reference.write_text(reference.read_text() + "\nUnreviewed change.\n")
    with pytest.raises(ValueError, match="hash or size mismatch"):
        _validate_curated_registry(candidate, forbidden=set())
