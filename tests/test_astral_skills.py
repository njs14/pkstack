from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from pkstack.bootstrap import _validate_curated_registry, bootstrap_project
from pkstack.upstreams import load_upstream_manifest, load_upstream_review_ledger

POWER = Path(__file__).resolve().parents[1] / "powers" / "pkstack"
ROOT = POWER.parents[1]
NAMES = {"uv", "ruff", "ty"}
PIN = "f3ce88a7ba830f53afd6d944c1d0278ed318e142"
TREE = "8cc1cb9f539f90fd98efa4be3857c6d74fd8d839"


def _tree_sha(files: list[dict[str, Any]], revision: str) -> str:
    tree: dict[str, Any] = {}
    for entry in files:
        node = tree
        *dirs, name = entry["path"].split("/")
        for directory in dirs:
            node = node.setdefault(directory, {})
        node[name] = (entry[revision]["mode"], entry[revision]["object_sha"])

    def encode(node: dict[str, Any]) -> str:
        objects = []
        for name, value in node.items():
            mode, sha = ("40000", encode(value)) if isinstance(value, dict) else value
            key = name + ("/" if isinstance(value, dict) else "")
            objects.append((key, mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(sha)))
        raw = b"".join(raw for _, raw in sorted(objects))
        return hashlib.sha1(b"tree " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

    return encode(tree)


def test_astral_source_inventory_binds_actual_upstream_tree() -> None:
    manifest = load_upstream_manifest(ROOT)
    load_upstream_review_ledger(ROOT, manifest)
    source = next(item for item in manifest.sources if item.source_id == "astral-python")
    assert (source.commit, source.subtree_sha) == (PIN, TREE)
    inventory = json.loads((POWER / "docs/astral-python-source-parity.json").read_text())
    for revision in ("pinned", "current"):
        assert inventory["source"][revision] == {"commit": PIN, "subtree_sha": TREE}
        assert _tree_sha(inventory["files"], revision) == TREE
    accepted = {entry["path"] for entry in inventory["files"] if entry["disposition"] == "A"}
    assert accepted == {f"skills/{name}/SKILL.md" for name in NAMES}
    excluded = {entry["path"] for entry in inventory["files"] if entry["disposition"] == "C"}
    assert excluded == {".claude-plugin/plugin.json"}
    assert set(_validate_curated_registry(POWER, forbidden=set())) >= NAMES


def test_astral_installation_is_complete_and_idempotent(tmp_path: Path) -> None:
    result = bootstrap_project(tmp_path, power_root=POWER)
    assert result.ok, result.to_dict()
    for name in NAMES:
        target = tmp_path / ".kiro/skills" / name / "SKILL.md"
        assert target.read_bytes() == (POWER / "skills" / name / "SKILL.md").read_bytes()
        metadata = yaml.safe_load(target.read_text().split("---", 2)[1])
        assert metadata["name"] == name
    assert (tmp_path / ".kiro/steering/pkstack-python.md").is_file()
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / "CLAUDE.md").exists()
    second = bootstrap_project(tmp_path, power_root=POWER)
    assert second.ok, second.to_dict()
    assert not second.created and not second.updated


def test_python_routing_cases_are_bounded_and_reference_installed_skills() -> None:
    path = ROOT / "tests/fixtures/astral-routing.json"
    assert path.stat().st_size < 8 * 1024
    data = json.loads(path.read_text())
    assert data["schema_version"] == 1
    cases = data["cases"]
    assert 1 <= len(cases) <= 12
    assert len({case["id"] for case in cases}) == len(cases)
    for case in cases:
        for name in [case["primary"], *case["helpers"]]:
            assert (POWER / "skills" / name / "SKILL.md").is_file()
        assert case["expected_output"] and case["forbidden_effects"]


def test_repository_claude_instructions_are_the_same_file() -> None:
    link = ROOT / "CLAUDE.md"
    assert link.is_symlink()
    assert link.readlink() == Path("AGENTS.md")
    assert link.resolve() == ROOT / "AGENTS.md"


@pytest.mark.parametrize(
    ("selected", "resolved", "label"),
    [
        ("auto", None, "Auto (Kiro-managed routing)"),
        ("explicit-model", "explicit-model", "explicit-model"),
    ],
)
def test_model_selection_text_preserves_receipt_identity(
    selected: str,
    resolved: str | None,
    label: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from pkstack import cli

    payload = {
        "ok": True,
        "schemaVersion": "2",
        "context": {"answer": "Known fact.", "sources": [], "uncertainties": []},
        "execution": {"model": selected, "resolved_model": resolved},
        "estimatedTokens": 10,
        "budget": 1200,
    }
    monkeypatch.setattr(cli, "search_knowledge", lambda *args, **kwargs: payload)
    cli.knowledge_search_command("question", model=selected)
    rendered = capsys.readouterr().out
    assert f"Selected model: {label}" in rendered
    assert f"Underlying model: {resolved or 'not disclosed'}" in rendered
    cli.knowledge_search_command("question", model=selected, output="json")
    assert json.loads(capsys.readouterr().out) == payload
