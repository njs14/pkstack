from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from pkstack.bootstrap import _validate_curated_registry, bootstrap_project
from pkstack.upstreams import load_upstream_manifest, load_upstream_review_ledger

POWER = Path(__file__).resolve().parents[1] / "powers" / "pkstack"
ROOT = POWER.parents[1]
PIN = "3cca18b368ae95cdbdebbff572ccafa662551015"
SOURCES = {
    "domain-modeling": (
        "skills/engineering/domain-modeling",
        "388c9822641805ca2dcd5038e68a1d5282437ee5",
    ),
    "grill-me": (
        "skills/productivity/grill-me",
        "3df14e2d3a89459bf300614be9247e3ce74798f8",
    ),
    "grill-with-docs": (
        "skills/engineering/grill-with-docs",
        "eedaf2562c83155115e9c649fa3ecaac2e10e81d",
    ),
    "grilling": (
        "skills/productivity/grilling",
        "f0732035b8b1b60ae39454e4191caef32fa91903",
    ),
}


def _tree_identity(entries: list[dict[str, Any]], revision: str) -> str:
    tree: dict[str, Any] = {}
    for entry in entries:
        here = tree
        *directories, name = entry["path"].split("/")
        for directory in directories:
            here = here.setdefault(directory, {})
        here[name] = (entry[revision]["mode"], entry[revision]["object_sha"])

    def encode(node: dict[str, Any]) -> str:
        items = []
        for name, value in node.items():
            directory = isinstance(value, dict)
            mode, sha = ("40000", encode(value)) if directory else value
            sort_key = (name + ("/" if directory else "")).encode()
            raw = mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(sha)
            items.append((sort_key, raw))
        content = b"".join(raw for _, raw in sorted(items))
        return hashlib.sha1(b"tree " + str(len(content)).encode() + b"\0" + content).hexdigest()

    return encode(tree)


def test_pocock_sources_bind_original_git_trees_and_genesis() -> None:
    manifest = load_upstream_manifest(ROOT)
    # This loader checks every source's manifest, genesis, and provenance markers together.
    load_upstream_review_ledger(ROOT, manifest)
    sources = {source.source_id: source for source in manifest.sources}
    registry = json.loads((POWER / "metadata/curated-skills.json").read_text())
    curated = {entry["name"]: entry for entry in registry["skills"]}
    assert set(SOURCES) <= set(_validate_curated_registry(POWER, forbidden=set()))
    for name, (path, tree_sha) in SOURCES.items():
        entry = curated[name]
        source = sources[entry["source_id"]]
        inventory = json.loads((POWER / entry["source_parity"]).read_text())
        assert source.source_id == f"mattpocock-{name}"
        assert source.path == path
        assert source.commit == PIN
        assert source.subtree_sha == tree_sha
        assert inventory["source"]["repository"] == "mattpocock/skills"
        assert inventory["source"]["path"] == path
        for revision in ("pinned", "current"):
            assert inventory["source"][revision] == {"commit": PIN, "subtree_sha": tree_sha}
            assert _tree_identity(inventory["files"], revision) == tree_sha
        files = {item["path"]: item for item in inventory["files"]}
        assert files["agents/openai.yaml"]["disposition"] == "C"
        bundle = json.loads((POWER / entry["bundle_manifest"]).read_text())
        assert {item["path"] for item in bundle["files"]} == {
            item["path"] for item in inventory["files"] if item["disposition"] == "A"
        }
        assert all(item["source_path"] == f"{path}/{item['path']}" for item in bundle["files"])


def test_adapted_skill_hash_cannot_replace_an_upstream_inventory_identity() -> None:
    name = "grilling"
    inventory = json.loads((POWER / f"docs/mattpocock-{name}-source-parity.json").read_text())
    altered = copy.deepcopy(inventory)
    local = (POWER / f"skills/{name}/SKILL.md").read_bytes()
    local_sha = hashlib.sha1(b"blob " + str(len(local)).encode() + b"\0" + local).hexdigest()
    entry = next(item for item in altered["files"] if item["path"] == "SKILL.md")
    assert local_sha != entry["current"]["object_sha"]
    entry["current"]["object_sha"] = local_sha
    assert _tree_identity(altered["files"], "current") != SOURCES[name][1]


def test_knowledge_interview_skills_install_as_native_packages_with_resolving_references(
    tmp_path: Path,
) -> None:
    first = bootstrap_project(tmp_path, power_root=POWER)
    assert first.ok, first.to_dict()
    for name in SOURCES:
        source = POWER / "skills" / name
        installed = tmp_path / ".kiro/skills" / name
        assert not (tmp_path / "Wiki" / name).exists()
        assert not (installed / "agents/openai.yaml").exists()
        for asset in source.rglob("*"):
            if asset.is_file():
                assert (installed / asset.relative_to(source)).read_bytes() == asset.read_bytes()
        skill = installed / "SKILL.md"
        metadata = yaml.safe_load(skill.read_text().split("---", 2)[1])
        assert set(metadata) == {"name", "description"}
        assert metadata["name"] == name
        assert isinstance(metadata["description"], str) and metadata["description"].strip()
        # Entry references must resolve after installation; external UI metadata is unnecessary.
        for link in re.findall(r"\]\(([^)]+\.md)\)", skill.read_text()):
            assert (skill.parent / link).is_file(), (name, link)
    second = bootstrap_project(tmp_path, power_root=POWER)
    assert second.ok
    assert not second.created
    assert not second.updated


@pytest.mark.parametrize("name", SOURCES)
def test_curated_skill_modification_requires_updated_bundle_identity(
    tmp_path: Path, name: str
) -> None:
    import shutil

    # Build a minimal independent registry fixture and alter its actual native entrypoint.
    entry = next(
        entry
        for entry in json.loads((POWER / "metadata/curated-skills.json").read_text())["skills"]
        if entry["name"] == name
    )
    shutil.copytree(POWER / entry["bundle_root"], tmp_path / entry["bundle_root"])
    (tmp_path / "docs").mkdir()
    for field in ("bundle_manifest", "source_parity", "provenance"):
        shutil.copyfile(POWER / entry[field], tmp_path / entry[field])
    count = json.loads((POWER / entry["bundle_manifest"]).read_text())["summary"]["file_count"]
    (tmp_path / "metadata/curated-skills.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "registry_type": "curated-skills",
                "skills": [entry],
                "summary": {
                    "curated_skill_count": 1,
                    "shipped_skill_directories": 1,
                    "bundle_file_count": count,
                },
            }
        )
    )
    _validate_curated_registry(tmp_path, forbidden=set())
    target = tmp_path / entry["target"]
    target.write_text(target.read_text() + "\nUnreviewed change.\n")
    with pytest.raises(ValueError, match="hash or size mismatch"):
        _validate_curated_registry(tmp_path, forbidden=set())
