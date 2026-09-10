"""Offline installation and instruction-contract checks, not live Kiro proof."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pkstack.bootstrap import bootstrap_project
from pkstack.upstreams import _validate_source_inventory_document

POWER = Path(__file__).resolve().parents[1] / "powers" / "pkstack"


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


def test_wayfinder_installs_with_new_router_and_unchanged_agent(tmp_path: Path) -> None:
    result = bootstrap_project(tmp_path, power_root=POWER)
    assert result.ok
    for relative in (
        "skills/wayfinder/SKILL.md",
        "skills/wayfinder/references/github.md",
        "skills/poteto-kiro-mode/SKILL.md",
    ):
        assert (tmp_path / ".kiro" / relative).read_bytes() == (POWER / relative).read_bytes()
    assert not (tmp_path / ".kiro/skills/pkstack").exists()
    assert (tmp_path / ".kiro/agents/pkstack.json").is_file()
    second = bootstrap_project(tmp_path, power_root=POWER, dry_run=True, update_managed=True)
    assert second.ok and not second.created and not second.updated


def test_wayfinder_retains_cloud_only_relationship_and_authority_contract() -> None:
    skill = (POWER / "skills/wayfinder/SKILL.md").read_text()
    operations = (POWER / "skills/wayfinder/references/github.md").read_text()
    for requirement in (
        "Native Plan is read-only",
        "no assignee and no open blocker",
        "one decision ticket per session",
        "not an atomic session lock",
        "no in-scope fog remains",
        "do not create a fallback board",
    ):
        assert requirement in skill
    for requirement in (
        "--hostname github.com",
        "sub_issue_id",
        "dependencies/blocked_by",
        "Integer `issue_id`",
        "not an empty list",
        "do not reparent",
    ):
        assert requirement.casefold() in operations.casefold()
