from __future__ import annotations

import base64
import copy
import hashlib
import json
import multiprocessing
import shutil
from pathlib import Path
from typing import Any

import pytest

from pkstack import cli, upstreams
from pkstack.bootstrap import SKILL_ROUTE_ALIASES, bootstrap_project
from pkstack.runner import CommandRejected, enforce_verification_policy
from pkstack.upstreams import UpstreamError, check_upstreams, load_upstream_manifest

POWER_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = POWER_ROOT.parents[1]
PIN = "b9ddc83c32972210b8a94d389130713e8eed346e"
PIN_TREE = "950b90234c17babd00c43e32b19ae50abb4720f5"
HEAD = "efa2a531985e0a8084d36ff3cf87233be8a9f34b"
HEAD_TREE = "1c625329e71538629f087374daa71293a498089f"
PIN_ROOT_TREE = "1" * 40
HEAD_ROOT_TREE = "2" * 40
FUTURE = "d" * 40
FUTURE_ROOT_TREE = "3" * 40
FUTURE_TREE = "4" * 40
CHANGED_PATHS = (
    ".cursor-plugin/plugin.json",
    "README.md",
    "assets/logo.png",
    "docs/guide/06-verify-and-ship.md",
    "docs/guide/07-overnight.md",
    "skills/architect/SKILL.md",
    "skills/arena/SKILL.md",
    "skills/how/SKILL.md",
    "skills/interrogate/SKILL.md",
    "skills/make-bot-ui/SKILL.md",
    "skills/pkstack/SKILL.md",
    "skills/pkstack/playbooks/autopilot-full.md",
    "skills/pkstack/playbooks/autopilot-stack.md",
    "skills/pkstack/playbooks/babysit.md",
    "skills/pkstack/playbooks/bug-fix.md",
    "skills/pkstack/playbooks/hillclimb.md",
    "skills/pkstack/playbooks/multi-phase-plan.md",
    "skills/pkstack/playbooks/opening-a-pr.md",
    "skills/pkstack/playbooks/perf-issue.md",
    "skills/pkstack/playbooks/shipping.md",
    "skills/pkstack/references/bugbot-triage.md",
    "skills/reflect/SKILL.md",
    "skills/setup-pstack/SKILL.md",
    "skills/typescript-best-practices/SKILL.md",
    "skills/typescript-best-practices/references/patterns.md",
    "skills/unslop/SKILL.md",
    "skills/why/SKILL.md",
)


def test_committed_maintenance_campaign_matches_recorded_transition_and_manifest_tip() -> None:
    campaign = json.loads(
        (REPOSITORY_ROOT / "reviews" / "pk-stack-maintenance-campaign.json").read_text(
            encoding="utf-8"
        )
    )
    ledger = json.loads(
        (REPOSITORY_ROOT / "maintenance" / "upstream-reviews.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (REPOSITORY_ROOT / "maintenance" / "upstreams.json").read_text(encoding="utf-8")
    )

    evidence = campaign["accepted_transition"]
    source_id = evidence["source_id"]
    ledger_source = next(source for source in ledger["sources"] if source["id"] == source_id)
    manifest_source = next(source for source in manifest["sources"] if source["id"] == source_id)
    transition_index = evidence["ledger_transition_index"]
    assert type(transition_index) is int and 0 <= transition_index < len(
        ledger_source["transitions"]
    )
    recorded_transition = ledger_source["transitions"][transition_index]
    latest_transition = ledger_source["transitions"][-1]
    projected_dispositions = [
        {"path": item["path"], "disposition": item["disposition"]}
        for item in recorded_transition["dispositions"]
    ]
    disposition_counts = {
        disposition: sum(
            item["disposition"] == disposition for item in recorded_transition["dispositions"]
        )
        for disposition in ("A", "B", "C")
    }

    assert campaign["decision"] == "passed"
    assert evidence["ledger_path"] == manifest["review_ledger_path"]
    assert evidence["repository"] == ledger_source["repository"]
    assert evidence["path"] == ledger_source["path"]
    # The frozen campaign predates the local Power directory rename, not a source change.
    historical_provenance = Path(evidence["provenance_path"])
    assert (
        Path("powers/pkstack") / historical_provenance.relative_to("powers/pk-stack")
    ).as_posix() == ledger_source["provenance_path"]
    assert evidence["prior"] == recorded_transition["prior"]
    assert evidence["new"] == recorded_transition["new"]
    assert evidence["inventory_sha256"] == recorded_transition["inventory_sha256"]
    assert evidence["path_count"] == len(recorded_transition["dispositions"])
    assert evidence["disposition_counts"] == disposition_counts
    assert evidence["dispositions"] == projected_dispositions
    assert {
        "commit": manifest_source["commit"],
        "subtree_sha": manifest_source["subtree_sha"],
    } == latest_transition["new"]
    assert (
        campaign["final_check"]["review_reproof"]["latest_inventory_sha256"]
        == evidence["inventory_sha256"]
    )
    assert campaign["final_check"]["review_reproof"]["latest_path_count"] == evidence["path_count"]
    assert (
        campaign["final_check"]["review_reproof"]["latest_disposition_counts"]
        == evidence["disposition_counts"]
    )

    prior = campaign["prior_campaign"]
    prior_transition = ledger_source["transitions"][prior["accepted_transition_index"]]
    prior_projection = [
        {"path": item["path"], "disposition": item["disposition"]}
        for item in prior_transition["dispositions"]
    ]
    prior_counts = {
        disposition: sum(
            item["disposition"] == disposition for item in prior_transition["dispositions"]
        )
        for disposition in ("A", "B", "C")
    }
    encoded_projection = json.dumps(prior_projection, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    assert prior["prior"] == prior_transition["prior"]
    assert prior["new"] == prior_transition["new"]
    assert prior["inventory_sha256"] == prior_transition["inventory_sha256"]
    assert prior["path_count"] == len(prior_transition["dispositions"])
    assert prior["disposition_counts"] == prior_counts
    assert prior["dispositions_sha256"] == hashlib.sha256(encoded_projection).hexdigest()
    assert prior["attempt_evidence"]["retained"] is False
    assert prior["attempt_evidence"]["attempts"] is None
    assert prior["attempt_evidence"]["bootstrap_preview"] is None


def test_committed_source_inventories_use_canonical_casefold_path_order() -> None:
    manifest = load_upstream_manifest(REPOSITORY_ROOT)
    checked_sources = set()
    for source in manifest.sources:
        parity = json.loads((REPOSITORY_ROOT / source.parity_path).read_text(encoding="utf-8"))
        if parity.get("artifact_type") != "source-inventory":
            continue
        paths = [entry["path"] for entry in parity["files"]]
        assert paths == sorted(set(paths), key=str.casefold), source.parity_path
        checked_sources.add(source.source_id)
    assert "mattpocock-writing-for-agents" in checked_sources


def test_committed_openknowledge_cli_contract_source_is_exhaustive_and_safely_scoped() -> None:
    manifest = json.loads(
        (REPOSITORY_ROOT / "maintenance" / "upstreams.json").read_text(encoding="utf-8")
    )
    ledger = json.loads(
        (REPOSITORY_ROOT / "maintenance" / "upstream-reviews.json").read_text(encoding="utf-8")
    )
    parity = json.loads(
        (REPOSITORY_ROOT / "powers/pkstack/docs/openknowledge-cli-contract-parity.json").read_text(
            encoding="utf-8"
        )
    )
    provenance = (
        REPOSITORY_ROOT / "powers/pkstack/docs/openknowledge-cli-contract-provenance.md"
    ).read_text(encoding="utf-8")
    source_id = "openknowledge-cli-contract"
    manifest_source = next(source for source in manifest["sources"] if source["id"] == source_id)
    ledger_source = next(source for source in ledger["sources"] if source["id"] == source_id)
    _assert_openknowledge_contract_scope(manifest_source, ledger_source, parity, provenance)


def _assert_openknowledge_contract_scope(
    manifest_source: dict[str, Any],
    ledger_source: dict[str, Any],
    parity: dict[str, Any],
    provenance: str,
) -> None:
    """Check local scope, not remote authenticity (the acceptance verifier proves that)."""
    source_id = "openknowledge-cli-contract"
    active = {key: manifest_source[key] for key in ("commit", "subtree_sha")}

    assert manifest_source == {
        **active,
        "id": source_id,
        "parity_path": "powers/pkstack/docs/openknowledge-cli-contract-parity.json",
        "path": "packages/cli/schemas/v1",
        "provenance_path": "powers/pkstack/docs/openknowledge-cli-contract-provenance.md",
        "ref": "main",
        "repository": "openknowledge-sh/openknowledge",
    }
    assert ledger_source == {
        "genesis": ledger_source["genesis"],
        "id": source_id,
        "parity_path": manifest_source["parity_path"],
        "path": manifest_source["path"],
        "provenance_path": manifest_source["provenance_path"],
        "repository": manifest_source["repository"],
        "transitions": ledger_source["transitions"],
    }
    transitions = ledger_source["transitions"]
    assert active == (transitions[-1]["new"] if transitions else ledger_source["genesis"])
    prior = transitions[-1]["prior"] if transitions else ledger_source["genesis"]
    assert parity["schema_version"] == 1
    assert parity["artifact_type"] == "source-inventory"
    assert parity["allowed_dispositions"] == ["A", "B", "C"]
    for key in ("id", "repository", "path"):
        assert parity["source"][key] == manifest_source[key]
    pinned = upstreams._source_parity_identity(parity["source"]["pinned"], "pinned")
    current = upstreams._source_parity_identity(parity["source"]["current"], "current")
    # Before accept, the matrix describes active -> candidate. After accept it
    # retains that same reviewed transition while the manifest advances.
    assert (pinned == active and current["subtree_sha"] != active["subtree_sha"]) or (
        current == active and pinned == prior
    )
    paths = {entry["path"] for entry in parity["files"]}
    assert paths
    assert [entry["path"] for entry in parity["files"]] == sorted(paths, key=str.casefold)
    assert all(
        entry["pinned"] is not None or entry["current"] is not None for entry in parity["files"]
    )
    assert all(entry["rationale"].strip() for entry in parity["files"])
    by_disposition = {
        disposition: {
            entry["path"] for entry in parity["files"] if entry["disposition"] == disposition
        }
        for disposition in ("A", "B", "C")
    }
    assert by_disposition["A"] == paths & {
        "cli-error.schema.json",
        "common.schema.json",
        "search-context.schema.json",
        "validation.schema.json",
    }
    assert by_disposition["B"] == {
        entry["path"]
        for entry in parity["files"]
        if entry["path"].startswith(("deploy-", "job-", "runtime-"))
    }
    assert parity["summary"] == {
        **{disposition: len(paths) for disposition, paths in by_disposition.items()},
        "pinned_files": sum(entry["pinned"] is not None for entry in parity["files"]),
        "current_files": sum(entry["current"] is not None for entry in parity["files"]),
    }
    assert sum(len(paths) for paths in by_disposition.values()) == len(parity["files"])
    assert (
        _marker_line(
            "genesis",
            {
                "source_id": source_id,
                "repository": manifest_source["repository"],
                "path": manifest_source["path"],
                **ledger_source["genesis"],
            },
        )
        in provenance
    )


@pytest.mark.parametrize("accepted", [False, True], ids=["pending", "accepted"])
def test_openknowledge_contract_scope_allows_revision_and_inventory_changes(accepted: bool) -> None:
    source = {
        "id": "openknowledge-cli-contract",
        "repository": "openknowledge-sh/openknowledge",
        "path": "packages/cli/schemas/v1",
        "ref": "main",
        "commit": PIN,
        "subtree_sha": PIN_TREE,
        "parity_path": "powers/pkstack/docs/openknowledge-cli-contract-parity.json",
        "provenance_path": "powers/pkstack/docs/openknowledge-cli-contract-provenance.md",
    }
    prior = {"commit": PIN, "subtree_sha": PIN_TREE}
    new = {"commit": HEAD, "subtree_sha": HEAD_TREE}
    review = {
        **{
            key: value
            for key, value in source.items()
            if key not in {"commit", "subtree_sha", "ref"}
        },
        "genesis": prior,
        "transitions": [],
    }
    old_file = {"type": "blob", "mode": "100644", "object_sha": "a" * 40, "size": 10}
    new_file = {**old_file, "object_sha": "b" * 40, "size": 20}
    parity = {
        "schema_version": 1,
        "artifact_type": "source-inventory",
        "allowed_dispositions": ["A", "B", "C"],
        "source": {
            **{key: source[key] for key in ("id", "repository", "path")},
            "pinned": prior,
            "current": new,
        },
        "files": [
            {
                "path": path,
                "pinned": pinned,
                "current": current,
                "disposition": disposition,
                "rationale": "Reviewed scope.",
            }
            for path, pinned, current, disposition in (
                ("new-metadata.schema.json", None, new_file, "C"),
                ("runtime-old.schema.json", old_file, None, "B"),
                ("search-context.schema.json", old_file, new_file, "A"),
            )
        ],
        "summary": {"A": 1, "B": 1, "C": 1, "pinned_files": 2, "current_files": 2},
    }
    if accepted:
        source.update(new)
        review["transitions"] = [{"prior": prior, "new": new}]
    provenance = _marker_line(
        "genesis",
        {
            "source_id": source["id"],
            "repository": source["repository"],
            "path": source["path"],
            **prior,
        },
    )
    _assert_openknowledge_contract_scope(source, review, parity, provenance)

    parity["files"][1]["disposition"] = "A"
    with pytest.raises(AssertionError):
        _assert_openknowledge_contract_scope(source, review, parity, provenance)


def _manifest() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "review_ledger_path": "maintenance/upstream-reviews.json",
        "sources": [
            {
                "id": "cursor-pstack",
                "repository": "cursor/plugins",
                "path": "pstack",
                "ref": "main",
                "commit": PIN,
                "subtree_sha": PIN_TREE,
                "provenance_path": "powers/pkstack/docs/provenance.md",
                "parity_path": "powers/pkstack/docs/upstream-skill-parity.json",
            }
        ],
    }


def _ledger() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "sources": [
            {
                "id": "cursor-pstack",
                "repository": "cursor/plugins",
                "path": "pstack",
                "provenance_path": "powers/pkstack/docs/provenance.md",
                "parity_path": "powers/pkstack/docs/upstream-skill-parity.json",
                "genesis": {"commit": PIN, "subtree_sha": PIN_TREE},
                "transitions": [],
            }
        ],
    }


def _write_ledger(root: Path, document: Any | None = None) -> None:
    path = root / "maintenance" / "upstream-reviews.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_ledger() if document is None else document), encoding="utf-8")


def _write_manifest(root: Path, document: Any | None = None) -> None:
    manifest = _manifest() if document is None else document
    provenance = root / "powers" / "pkstack" / "docs" / "provenance.md"
    provenance.parent.mkdir(parents=True, exist_ok=True)
    sources = manifest.get("sources") if isinstance(manifest, dict) else None
    source = sources[0] if isinstance(sources, list) and sources else _manifest()["sources"][0]
    genesis = _genesis_marker(
        commit=source["commit"],
        subtree_sha=source["subtree_sha"],
    )
    provenance.write_text(
        "# Provenance\n" + _marker_line("genesis", genesis) + "\n",
        encoding="utf-8",
    )
    path = root / "maintenance" / "upstreams.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    _write_skill_parity(root)
    if not (root / "maintenance" / "upstream-reviews.json").exists():
        _write_ledger(root)


def _transition(inventory_sha256: str) -> dict[str, Any]:
    dispositions = []
    for index, path in enumerate(CHANGED_PATHS):
        if path == "assets/logo.png":
            disposition = "B"
        else:
            disposition = "A" if index <= 11 else "B" if index < 24 else "C"
        dispositions.append(
            {
                "path": path,
                "disposition": disposition,
                "rationale": f"Reviewed semantic disposition {disposition} for {path}.",
            }
        )
    return {
        "prior": {"commit": PIN, "subtree_sha": PIN_TREE},
        "new": {"commit": HEAD, "subtree_sha": HEAD_TREE},
        "inventory_sha256": inventory_sha256,
        "dispositions": dispositions,
    }


def _future_transition(inventory_sha256: str) -> dict[str, Any]:
    return {
        "prior": {"commit": HEAD, "subtree_sha": HEAD_TREE},
        "new": {"commit": FUTURE, "subtree_sha": FUTURE_TREE},
        "inventory_sha256": inventory_sha256,
        "dispositions": [
            {
                "path": "README.md",
                "disposition": "C",
                "rationale": "Reviewed documentation-only update.",
            }
        ],
    }


def _advance_review(root: Path, inventory_sha256: str) -> None:
    manifest = _manifest()
    manifest["sources"][0].update(commit=HEAD, subtree_sha=HEAD_TREE)
    ledger = _ledger()
    ledger["sources"][0]["transitions"].append(_transition(inventory_sha256))
    _write_manifest(root, manifest)
    _write_ledger(root, ledger)
    _rewrite_provenance_markers(
        root,
        ledger["sources"][0]["transitions"],
        genesis=ledger["sources"][0]["genesis"],
    )


def _genesis_marker(
    *,
    commit: str = PIN,
    subtree_sha: str = PIN_TREE,
) -> dict[str, Any]:
    return {
        "source_id": "cursor-pstack",
        "repository": "cursor/plugins",
        "path": "pstack",
        "commit": commit,
        "subtree_sha": subtree_sha,
    }


def _provenance_marker(transition: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": "cursor-pstack",
        "repository": "cursor/plugins",
        "path": "pstack",
        "prior": transition["prior"],
        "new": transition["new"],
        "inventory_sha256": transition["inventory_sha256"],
    }


def _marker_line(kind: str, marker: dict[str, Any]) -> str:
    serialized = json.dumps(marker, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"<!-- pk-stack-upstream-{kind}: {serialized} -->"


def _write_provenance_marker(root: Path, transition: dict[str, Any]) -> None:
    provenance = root / "powers" / "pkstack" / "docs" / "provenance.md"
    with provenance.open("a", encoding="utf-8") as handle:
        handle.write(_marker_line("review", _provenance_marker(transition)) + "\n")


def _rewrite_provenance_markers(
    root: Path,
    transitions: list[dict[str, Any]],
    *,
    genesis: dict[str, Any] | None = None,
) -> None:
    provenance = root / "powers" / "pkstack" / "docs" / "provenance.md"
    identity = {"commit": PIN, "subtree_sha": PIN_TREE} if genesis is None else genesis
    lines = [
        "# Provenance",
        _marker_line(
            "genesis",
            _genesis_marker(
                commit=identity["commit"],
                subtree_sha=identity["subtree_sha"],
            ),
        ),
    ]
    for transition in transitions:
        lines.append(_marker_line("review", _provenance_marker(transition)))
    provenance.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_proposal(root: Path, document: Any, *, bind_provenance: bool = True) -> Path:
    path = root / ".pkstack-maintenance" / "proposal.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    proposal = (
        {"source_id": "cursor-pstack", **document}
        if isinstance(document, dict) and "source_id" not in document
        else document
    )
    path.write_text(json.dumps(proposal), encoding="utf-8")
    if bind_provenance:
        _write_provenance_marker(root, document)
    return path


def _provenance_marker_lines(root: Path) -> list[str]:
    provenance = root / "powers" / "pkstack" / "docs" / "provenance.md"
    return [
        line
        for line in provenance.read_text(encoding="utf-8").splitlines()
        if line.startswith("<!-- pk-stack-upstream-")
    ]


def _prepare_accept_root(root: Path) -> Path:
    canonical = root / "powers" / "pkstack"
    shutil.copytree(
        POWER_ROOT,
        canonical,
        ignore=shutil.ignore_patterns(
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "__pycache__",
            "build",
            "dist",
        ),
    )
    bootstrap_project(root, power_root=canonical)
    _write_manifest(root)
    return canonical


def _tree(sha: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {"sha": sha, "truncated": False, "tree": entries}


def _git_blob_sha(content: bytes) -> str:
    header = b"blob " + str(len(content)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def _fake_package_tree_sha(revision: str, name: str) -> str:
    return hashlib.sha1(f"{revision}:{name}".encode(), usedforsecurity=False).hexdigest()


def _fake_skill_contents(revision: str) -> dict[str, bytes]:
    contents: dict[str, bytes] = {}
    for path in CHANGED_PATHS:
        parts = Path(path).parts
        if len(parts) < 3 or parts[0] != "skills":
            continue
        contents[path] = _old_content(path) if revision == "pinned" else _new_content(path)
    return contents


def _fake_skill_package(revision: str, name: str) -> dict[str, Any]:
    prefix = f"skills/{name}/"
    resources = []
    for path, content in _fake_skill_contents(revision).items():
        if not path.startswith(prefix):
            continue
        resources.append(
            {
                "path": path.removeprefix(prefix),
                "blob_sha": _git_blob_sha(content),
                "size": len(content),
                "handling": "semantic-source",
                "mode": "100644",
            }
        )
    resources.sort(key=lambda value: str(value["path"]).casefold())
    return {
        "package_tree_sha": _fake_package_tree_sha(revision, name),
        "files": resources,
    }


def _skill_parity_document() -> dict[str, Any]:
    names = sorted(
        {
            Path(path).parts[1]
            for path in CHANGED_PATHS
            if len(Path(path).parts) >= 3
            and Path(path).parts[0] == "skills"
            and Path(path).parts[-1] == "SKILL.md"
        }
    )
    skills = []
    for name in names:
        excluded = name == "make-bot-ui"
        entry: dict[str, Any] = {
            "name": name,
            "pinned": _fake_skill_package("pinned", name),
            "current": _fake_skill_package("current", name),
            "disposition": "excluded" if excluded else "direct-port",
            "target": (
                None if excluded else f"skills/{SKILL_ROUTE_ALIASES.get(name, name)}/SKILL.md"
            ),
            "rationale": f"Bounded synthetic test disposition for {name}.",
        }
        if excluded:
            entry["safe_alternative"] = "Use a reviewed manual architecture path."
        skills.append(entry)
    routed = sum(entry["target"] is not None for entry in skills)
    return {
        "schema_version": 1,
        "source": {
            "id": "cursor-pstack",
            "repository": "cursor/plugins",
            "path": "pstack",
            "catalog_path": "skills",
            "pinned": {"commit": PIN, "pstack_subtree_sha": PIN_TREE},
            "current": {"commit": HEAD, "pstack_subtree_sha": HEAD_TREE},
            "retrieved_on": "2026-09-02",
        },
        "allowed_dispositions": [
            "direct-port",
            "alias-consolidation",
            "native-kiro-replacement",
            "excluded",
        ],
        "pk_only_skills": [],
        "summary": {
            "direct-port": routed,
            "alias-consolidation": 0,
            "native-kiro-replacement": 0,
            "excluded": len(skills) - routed,
            "upstream_total": len(skills),
            "routed_upstream_names": routed,
            "shipped_skill_directories": routed,
            "pinned_package_files": sum(len(entry["pinned"]["files"]) for entry in skills),
            "current_package_files": sum(len(entry["current"]["files"]) for entry in skills),
            "semantic_source_files": sum(len(entry["current"]["files"]) for entry in skills),
            "helper_semantics_only_files": 0,
            "runtime_specific_exclusion_files": 0,
        },
        "skills": skills,
        "allowed_resource_handling": [
            "semantic-source",
            "helper-semantics-only",
            "runtime-specific-exclusion",
        ],
    }


def _write_skill_parity(root: Path, document: Any | None = None) -> Path:
    path = root / "powers" / "pkstack" / "docs" / "upstream-skill-parity.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _skill_parity_document() if document is None else document
    if document is None:
        local_skill_root = root / "powers" / "pkstack" / "skills"
        local_names = (
            {
                child.name
                for child in local_skill_root.iterdir()
                if child.is_dir() and (child / "SKILL.md").is_file()
            }
            if local_skill_root.is_dir()
            else set()
        )
        # Parity names preserve upstream provenance, while the target directory
        # is the Kiro-facing route (and may use an explicit alias).
        upstream_names = {
            Path(entry["target"]).parent.name
            for entry in payload["skills"]
            if entry["target"] is not None
        }
        curated_path = root / "powers" / "pkstack" / "docs" / "curated-skills.json"
        curated_names: set[str] = set()
        if curated_path.is_file():
            curated = json.loads(curated_path.read_text(encoding="utf-8"))
            curated_names = {entry["name"] for entry in curated["skills"]}
        payload["pk_only_skills"] = sorted(local_names - upstream_names - curated_names)
        payload["summary"]["shipped_skill_directories"] = payload["summary"][
            "routed_upstream_names"
        ] + len(payload["pk_only_skills"])
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    return path


def _expected_skill_packages(document: dict[str, Any], revision: str) -> dict[str, dict[str, Any]]:
    expected: dict[str, dict[str, Any]] = {}
    for entry in document["skills"]:
        package = entry[revision]
        if package is None:
            continue
        expected[entry["name"]] = {
            "package_tree_sha": package["package_tree_sha"],
            "files": {
                resource["path"]: (
                    "blob",
                    resource["mode"],
                    resource["blob_sha"],
                    resource["size"],
                )
                for resource in package["files"]
            },
        }
    return expected


def _blob(path: str, sha: str, *, size: int = 10, mode: str = "100644") -> dict[str, Any]:
    return {"path": path, "mode": mode, "type": "blob", "sha": sha, "size": size}


def _old_content(path: str) -> bytes:
    return f"old {path}\n".encode()


def _new_content(path: str) -> bytes:
    return f"new {path}\n".encode()


def _blob_response(content: bytes) -> dict[str, Any]:
    return {
        "sha": _git_blob_sha(content),
        "encoding": "base64",
        "size": len(content),
        "content": base64.b64encode(content).decode(),
    }


def _fake_responses() -> dict[str, Any]:
    pin_contents = {path: _old_content(path) for path in CHANGED_PATHS if path != "assets/logo.png"}
    head_contents = {
        path: (b"\x89PNG\r\n\x1a\n" if path == "assets/logo.png" else _new_content(path))
        for path in CHANGED_PATHS
    }
    pin_entries = [
        _blob(path, _git_blob_sha(content), size=len(content))
        for path, content in pin_contents.items()
    ]
    head_entries = [
        _blob(path, _git_blob_sha(content), size=len(content))
        for path, content in head_contents.items()
    ]
    skill_names = sorted(
        {
            Path(path).parts[1]
            for path in CHANGED_PATHS
            if len(Path(path).parts) >= 3
            and Path(path).parts[0] == "skills"
            and Path(path).parts[-1] == "SKILL.md"
        }
    )
    pin_entries.extend(
        {
            "path": f"skills/{name}",
            "mode": "040000",
            "type": "tree",
            "sha": _fake_package_tree_sha("pinned", name),
        }
        for name in skill_names
    )
    head_entries.extend(
        {
            "path": f"skills/{name}",
            "mode": "040000",
            "type": "tree",
            "sha": _fake_package_tree_sha("current", name),
        }
        for name in skill_names
    )
    commits = [{"sha": f"{index + 300:040x}"} for index in range(6)] + [{"sha": HEAD}]
    files = []
    for path in CHANGED_PATHS:
        item: dict[str, Any] = {
            "filename": f"pstack/{path}",
            "status": "added" if path == "assets/logo.png" else "modified",
            "sha": _git_blob_sha(head_contents[path]),
            "additions": 0 if path == "assets/logo.png" else 1,
            "deletions": 0 if path == "assets/logo.png" else 1,
            "changes": 0 if path == "assets/logo.png" else 2,
        }
        if path != "assets/logo.png":
            item["patch"] = f"@@ -1 +1 @@ {path}\n-old {path}\n+new {path}"
        files.append(item)
    responses = {
        upstreams._api_url("cursor/plugins", "commits", PIN): {
            "sha": PIN,
            "commit": {"tree": {"sha": PIN_ROOT_TREE}},
        },
        upstreams._api_url("cursor/plugins", "commits", "main"): {
            "sha": HEAD,
            "commit": {"tree": {"sha": HEAD_ROOT_TREE}},
        },
        upstreams._api_url("cursor/plugins", "commits", HEAD): {
            "sha": HEAD,
            "commit": {"tree": {"sha": HEAD_ROOT_TREE}},
        },
        upstreams._api_url("cursor/plugins", "git", "trees", PIN_ROOT_TREE): _tree(
            PIN_ROOT_TREE,
            [{"path": "pstack", "mode": "040000", "type": "tree", "sha": PIN_TREE}],
        ),
        upstreams._api_url("cursor/plugins", "git", "trees", HEAD_ROOT_TREE): _tree(
            HEAD_ROOT_TREE,
            [{"path": "pstack", "mode": "040000", "type": "tree", "sha": HEAD_TREE}],
        ),
        upstreams._api_url(
            "cursor/plugins", "git", "trees", PIN_TREE, query=(("recursive", "1"),)
        ): _tree(PIN_TREE, pin_entries),
        upstreams._api_url(
            "cursor/plugins", "git", "trees", HEAD_TREE, query=(("recursive", "1"),)
        ): _tree(HEAD_TREE, head_entries),
        upstreams._api_url(
            "cursor/plugins",
            "compare",
            f"{PIN}...{HEAD}",
            query=(("per_page", "100"), ("page", "1")),
        ): {
            "status": "ahead",
            "ahead_by": 7,
            "behind_by": 0,
            "total_commits": 7,
            "base_commit": {"sha": PIN},
            "merge_base_commit": {"sha": PIN},
            "commits": commits,
            "files": files,
        },
    }
    for content in pin_contents.values():
        sha = _git_blob_sha(content)
        responses[upstreams._api_url("cursor/plugins", "git", "blobs", sha)] = _blob_response(
            content
        )
    return responses


def _future_ref_responses(*, content_change: bool = False) -> dict[str, Any]:
    responses = _fake_responses()
    responses[upstreams._api_url("cursor/plugins", "commits", "main")] = {
        "sha": FUTURE,
        "commit": {"tree": {"sha": FUTURE_ROOT_TREE}},
    }
    responses[upstreams._api_url("cursor/plugins", "commits", FUTURE)] = {
        "sha": FUTURE,
        "commit": {"tree": {"sha": FUTURE_ROOT_TREE}},
    }
    responses[upstreams._api_url("cursor/plugins", "git", "trees", FUTURE_ROOT_TREE)] = _tree(
        FUTURE_ROOT_TREE,
        [
            {
                "path": "pstack",
                "mode": "040000",
                "type": "tree",
                "sha": FUTURE_TREE if content_change else HEAD_TREE,
            }
        ],
    )
    responses[
        upstreams._api_url(
            "cursor/plugins",
            "compare",
            f"{HEAD}...{FUTURE}",
            query=(("per_page", "100"), ("page", "1")),
        )
    ] = {
        "status": "ahead",
        "ahead_by": 1,
        "behind_by": 0,
        "total_commits": 1,
        "base_commit": {"sha": HEAD},
        "merge_base_commit": {"sha": HEAD},
        "commits": [{"sha": FUTURE}],
        "files": [],
    }
    if content_change:
        old = _new_content("README.md")
        new = b"future README.md\n"
        tree = copy.deepcopy(
            responses[
                upstreams._api_url(
                    "cursor/plugins", "git", "trees", HEAD_TREE, query=(("recursive", "1"),)
                )
            ]
        )
        tree["sha"] = FUTURE_TREE
        for entry in tree["tree"]:
            if entry["path"] == "README.md":
                entry.update(sha=_git_blob_sha(new), size=len(new))
        responses[
            upstreams._api_url(
                "cursor/plugins", "git", "trees", FUTURE_TREE, query=(("recursive", "1"),)
            )
        ] = tree
        responses[upstreams._api_url("cursor/plugins", "git", "blobs", _git_blob_sha(old))] = (
            _blob_response(old)
        )
        responses[
            upstreams._api_url(
                "cursor/plugins",
                "compare",
                f"{HEAD}...{FUTURE}",
                query=(("per_page", "100"), ("page", "1")),
            )
        ]["files"] = [
            {
                "filename": "pstack/README.md",
                "status": "modified",
                "sha": _git_blob_sha(new),
                "additions": 1,
                "deletions": 1,
                "changes": 2,
                "patch": "@@ -1 +1 @@\n-new README.md\n+future README.md",
            }
        ]
    return responses


class FakeFetch:
    def __init__(self, responses: dict[str, Any] | None = None) -> None:
        self.responses = _fake_responses() if responses is None else responses
        self.calls: list[tuple[str, str | None, float]] = []

    def __call__(self, url: str, token: str | None, timeout: float) -> Any:
        self.calls.append((url, token, timeout))
        return self.responses[url]


def _compare_source() -> upstreams.UpstreamSource:
    return upstreams.UpstreamSource(
        source_id="cursor-pstack",
        repository="cursor/plugins",
        path="pstack",
        ref="main",
        commit=PIN,
        subtree_sha=PIN_TREE,
        provenance_path="powers/pkstack/docs/provenance.md",
        parity_path="powers/pkstack/docs/upstream-skill-parity.json",
    )


def _external_comparison_files(count: int) -> list[dict[str, Any]]:
    return [
        {
            "filename": f"outside/generated-{index:03}.md",
            "status": "modified",
            "sha": f"{10_000 + index:040x}",
            "additions": 1,
            "deletions": 1,
            "changes": 2,
            "patch": "@@ -1 +1 @@\n-old\n+new",
        }
        for index in range(count)
    ]


def _single_tracked_change_responses() -> tuple[dict[str, Any], str]:
    responses = _fake_responses()
    compare_url = next(url for url in responses if "/compare/" in url)
    pin_tree_url = next(url for url in responses if PIN_TREE in url and "recursive" in url)
    head_tree_url = next(url for url in responses if HEAD_TREE in url and "recursive" in url)
    tracked_filename = "pstack/README.md"
    tracked_file = next(
        item for item in responses[compare_url]["files"] if item["filename"] == tracked_filename
    )
    responses[pin_tree_url]["tree"] = [
        item for item in responses[pin_tree_url]["tree"] if item["path"] == "README.md"
    ]
    responses[head_tree_url]["tree"] = [
        item for item in responses[head_tree_url]["tree"] if item["path"] == "README.md"
    ]
    responses[compare_url]["files"] = [tracked_file]
    return responses, compare_url


def _add_parallel_source(root: Path, *, source_id: str = "alpha-source") -> dict[str, Path]:
    manifest_path = root / "maintenance" / "upstreams.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = copy.deepcopy(manifest["sources"][0])
    source.update(
        id=source_id,
        provenance_path=f"powers/pkstack/docs/{source_id}-provenance.md",
        parity_path=f"powers/pkstack/docs/{source_id}-parity.json",
    )
    manifest["sources"].append(source)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    ledger_path = root / "maintenance" / "upstream-reviews.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    review = copy.deepcopy(ledger["sources"][0])
    review.update(
        id=source_id,
        provenance_path=source["provenance_path"],
        parity_path=source["parity_path"],
    )
    ledger["sources"].append(review)
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

    default_parity = root / manifest["sources"][0]["parity_path"]
    parity = json.loads(default_parity.read_text(encoding="utf-8"))
    parity["source"]["id"] = source_id
    parity_path = root / source["parity_path"]
    parity_path.write_text(json.dumps(parity), encoding="utf-8")

    genesis = {
        "source_id": source_id,
        "repository": source["repository"],
        "path": source["path"],
        "commit": source["commit"],
        "subtree_sha": source["subtree_sha"],
    }
    provenance_path = root / source["provenance_path"]
    provenance_path.write_text(
        "# Parallel source provenance\n" + _marker_line("genesis", genesis) + "\n",
        encoding="utf-8",
    )
    return {"parity": parity_path, "provenance": provenance_path}


def _append_source_review_marker(
    path: Path,
    *,
    source_id: str,
    transition: dict[str, Any],
) -> None:
    payload = {
        "source_id": source_id,
        "repository": "cursor/plugins",
        "path": "pstack",
        "prior": transition["prior"],
        "new": transition["new"],
        "inventory_sha256": transition["inventory_sha256"],
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_marker_line("review", payload) + "\n")


def test_source_inventory_parity_is_exact_and_fully_classified() -> None:
    pinned: dict[str, tuple[str, str, str, int | None]] = {
        "SPEC.md": ("blob", "100644", "a" * 40, 11)
    }
    current: dict[str, tuple[str, str, str, int | None]] = {
        "docs/guide.md": ("blob", "100644", "b" * 40, 19),
        "SPEC.md": ("blob", "100644", "c" * 40, 13),
    }
    document: dict[str, Any] = {
        "schema_version": 1,
        "artifact_type": "source-inventory",
        "source": {},
        "allowed_dispositions": ["A", "B", "C"],
        "summary": {"A": 1, "B": 1, "C": 0, "pinned_files": 1, "current_files": 2},
        "files": [
            {
                "path": "docs/guide.md",
                "pinned": None,
                "current": {
                    "type": "blob",
                    "mode": "100644",
                    "object_sha": "b" * 40,
                    "size": 19,
                },
                "disposition": "B",
                "rationale": "Methodology reference retained without redistributing its source.",
            },
            {
                "path": "SPEC.md",
                "pinned": {
                    "type": "blob",
                    "mode": "100644",
                    "object_sha": "a" * 40,
                    "size": 11,
                },
                "current": {
                    "type": "blob",
                    "mode": "100644",
                    "object_sha": "c" * 40,
                    "size": 13,
                },
                "disposition": "A",
                "rationale": "Normative specification semantics are incorporated by reference.",
            },
        ],
    }

    assert upstreams._validate_source_inventory_document(
        document,
        expected_pinned=pinned,
        expected_current=current,
    ) == {
        "pinned_resource_count": 1,
        "current_resource_count": 2,
        "classified_resource_count": 2,
    }

    tampered: dict[str, Any] = copy.deepcopy(document)
    tampered["files"][1]["current"]["object_sha"] = "d" * 40
    with pytest.raises(UpstreamError, match="identity does not match upstream"):
        upstreams._validate_source_inventory_document(
            tampered,
            expected_pinned=pinned,
            expected_current=current,
        )


def test_source_scoped_check_uses_the_selected_sources_own_parity(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    paths = _add_parallel_source(tmp_path)
    payload = check_upstreams(
        tmp_path,
        source_id="alpha-source",
        fetch_json=FakeFetch(),
        environ={},
    )

    assert payload["selected_source_id"] == "alpha-source"
    assert [source["id"] for source in payload["sources"]] == ["alpha-source"]
    source = payload["sources"][0]
    assert source["parity_path"] == paths["parity"].relative_to(tmp_path).as_posix()
    assert source["source_parity"]["ok"] is True
    assert source["source_parity"]["candidate_ready"] is True

    with pytest.raises(UpstreamError, match="not present in the manifest"):
        check_upstreams(
            tmp_path,
            source_id="missing-source",
            fetch_json=FakeFetch(),
            environ={},
        )


def test_skill_parity_blocks_remote_catalog_drift_and_accepts_exact_repair() -> None:
    baseline = _skill_parity_document()
    pinned = _expected_skill_packages(baseline, "pinned")
    current = _expected_skill_packages(baseline, "current")
    assert upstreams._validate_skill_parity_document(
        baseline,
        expected_pinned=pinned,
        expected_current=current,
    )["upstream_skill_count"] == len(baseline["skills"])

    added_current = copy.deepcopy(current)
    added_current["z-new-workflow"] = {
        "package_tree_sha": "e" * 40,
        "files": {"SKILL.md": ("blob", "100644", "f" * 40, 17)},
    }
    with pytest.raises(UpstreamError, match="top-level catalog"):
        upstreams._validate_skill_parity_document(
            baseline,
            expected_pinned=pinned,
            expected_current=added_current,
        )
    added_repair = copy.deepcopy(baseline)
    added_repair["skills"].append(
        {
            "name": "z-new-workflow",
            "pinned": None,
            "current": {
                "package_tree_sha": "e" * 40,
                "files": [
                    {
                        "path": "SKILL.md",
                        "blob_sha": "f" * 40,
                        "size": 17,
                        "handling": "semantic-source",
                        "mode": "100644",
                    }
                ],
            },
            "disposition": "direct-port",
            "target": "skills/z-new-workflow/SKILL.md",
            "rationale": "A future portable workflow with a reviewed Kiro-native route.",
        }
    )
    added_repair["summary"].update(
        {
            "direct-port": added_repair["summary"]["direct-port"] + 1,
            "upstream_total": added_repair["summary"]["upstream_total"] + 1,
            "routed_upstream_names": added_repair["summary"]["routed_upstream_names"] + 1,
            "shipped_skill_directories": (added_repair["summary"]["shipped_skill_directories"] + 1),
            "current_package_files": added_repair["summary"]["current_package_files"] + 1,
            "semantic_source_files": added_repair["summary"]["semantic_source_files"] + 1,
        }
    )
    assert (
        upstreams._validate_skill_parity_document(
            added_repair,
            expected_pinned=pinned,
            expected_current=added_current,
        )["upstream_skill_count"]
        == len(baseline["skills"]) + 1
    )

    removed_name = next(name for name in current if name != "make-bot-ui")
    removed_current = copy.deepcopy(current)
    removed_package = removed_current.pop(removed_name)
    with pytest.raises(UpstreamError, match="package must be null"):
        upstreams._validate_skill_parity_document(
            baseline,
            expected_pinned=pinned,
            expected_current=removed_current,
        )
    removed_repair = copy.deepcopy(baseline)
    removed_entry = next(
        entry for entry in removed_repair["skills"] if entry["name"] == removed_name
    )
    removed_entry["current"] = None
    removed_count = len(removed_package["files"])
    removed_repair["summary"]["current_package_files"] -= removed_count
    removed_repair["summary"]["semantic_source_files"] -= removed_count
    upstreams._validate_skill_parity_document(
        removed_repair,
        expected_pinned=pinned,
        expected_current=removed_current,
    )

    changed_current = copy.deepcopy(current)
    changed_name = next(iter(changed_current))
    changed_path = next(iter(changed_current[changed_name]["files"]))
    old_identity = changed_current[changed_name]["files"][changed_path]
    changed_current[changed_name]["files"][changed_path] = (
        old_identity[0],
        old_identity[1],
        "9" * 40,
        old_identity[3] + 1,
    )
    with pytest.raises(UpstreamError, match="identity does not match"):
        upstreams._validate_skill_parity_document(
            baseline,
            expected_pinned=pinned,
            expected_current=changed_current,
        )
    changed_repair = copy.deepcopy(baseline)
    changed_entry = next(
        entry for entry in changed_repair["skills"] if entry["name"] == changed_name
    )
    changed_resource = next(
        resource
        for resource in changed_entry["current"]["files"]
        if resource["path"] == changed_path
    )
    changed_resource.update(blob_sha="9" * 40, size=old_identity[3] + 1)
    upstreams._validate_skill_parity_document(
        changed_repair,
        expected_pinned=pinned,
        expected_current=changed_current,
    )


def _hold_accept_lock(root: str, entered: Any, release: Any) -> None:
    with upstreams._accept_locked(Path(root)):
        entered.set()
        release.wait(5)


def test_check_reports_exact_bounded_27_path_drift_inventory(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    fetch = FakeFetch()

    payload = check_upstreams(
        tmp_path,
        fetch_json=fetch,
        environ={"GITHUB_TOKEN": "secret"},
        timeout_seconds=3,
    )

    assert payload["ok"] is False
    assert payload["network_boundary"] == "https://api.github.com"
    source = payload["sources"][0]
    assert source["pinned_reproof"] == {
        "ok": True,
        "commit": PIN,
        "subtree_sha": PIN_TREE,
    }
    assert source["current"] == {"commit": HEAD, "subtree_sha": HEAD_TREE}
    assert source["drift"] is True
    comparison = source["comparison"]
    assert comparison["untrusted"] is True
    assert comparison["complete"] is True
    assert comparison["fast_forward"] is True
    assert comparison["base_commit"] == comparison["merge_base_commit"] == PIN
    assert comparison["head_commit"] == HEAD
    assert comparison["commit_count"] == comparison["ahead_by"] == 7
    assert comparison["behind_by"] == 0
    assert comparison["path_count"] == len(CHANGED_PATHS) == 27
    assert comparison["paths"] == list(CHANGED_PATHS)
    assert len(comparison["inventory_sha256"]) == 64
    assert set(comparison["inventory_sha256"]) <= set("0123456789abcdef")
    assert [item["path"] for item in comparison["files"]] == list(CHANGED_PATHS)
    assert comparison["no_patch_count"] == 1
    assert [item["path"] for item in comparison["files"] if item["no_patch"]] == ["assets/logo.png"]
    assert comparison["review_constraints"] == {
        "unified_patch_counts": upstreams.PATCH_COUNT_CONSTRAINT,
        "exact_blob_binding": upstreams.BLOB_BINDING_CONSTRAINT,
        "supported_tree_entries": upstreams.TREE_ENTRY_CONSTRAINT,
        "no_patch": upstreams.NO_PATCH_CONSTRAINT,
        "unavailable_binary_paths": ["assets/logo.png"],
    }
    logo = next(item for item in comparison["files"] if item["path"] == "assets/logo.png")
    assert logo["reviewability"] == "unavailable-nonsemantic-image"
    assert all(
        item["reviewability"] == "exact-blob-unified-patch"
        for item in comparison["files"]
        if item is not logo
    )
    assert all(
        item["old_identity"]["type"] == item["new_identity"]["type"] == "blob"
        and item["old_identity"]["mode"] == item["new_identity"]["mode"] == "100644"
        for item in comparison["files"]
        if item is not logo
    )
    assert comparison["patch_bytes"] <= upstreams.MAX_COMPARE_PATCH_BYTES
    assert all(
        call[0].startswith("https://api.github.com/repos/cursor/plugins/") for call in fetch.calls
    )
    assert all(call[1] == "secret" and 0 < call[2] <= 3.0 for call in fetch.calls)
    assert all("secret" not in call[0] for call in fetch.calls)
    assert len(fetch.calls) == 33

    reordered = _fake_responses()
    compare_url = next(url for url in reordered if "/compare/" in url)
    reordered[compare_url]["files"].reverse()
    reordered_payload = check_upstreams(
        tmp_path,
        fetch_json=FakeFetch(reordered),
        environ={},
    )
    reordered_comparison = reordered_payload["sources"][0]["comparison"]
    assert reordered_comparison["files"] == comparison["files"]
    assert reordered_comparison["inventory_sha256"] == comparison["inventory_sha256"]


def test_compare_bounds_tracked_subtree_not_unrelated_repository_files() -> None:
    responses = _fake_responses()
    compare_url = next(url for url in responses if "/compare/" in url)
    responses[compare_url]["files"] = _external_comparison_files(101)
    fetch = FakeFetch(responses)

    comparison = upstreams._compare_inventory(
        _compare_source(),
        base_commit=PIN,
        base_subtree=PIN_TREE,
        head_commit=HEAD,
        head_subtree=PIN_TREE,
        token=None,
        timeout_seconds=3,
        fetch_json=fetch,
        blob_cache={},
    )

    assert comparison["complete"] is True
    assert comparison["status"] == "ahead"
    assert comparison["path_count"] == comparison["file_count"] == 0
    assert comparison["paths"] == comparison["files"] == []


def test_compare_keeps_source_delta_among_297_unrelated_files() -> None:
    responses, compare_url = _single_tracked_change_responses()
    responses[compare_url]["files"] = [
        *_external_comparison_files(297),
        *responses[compare_url]["files"],
    ]

    comparison = upstreams._compare_inventory(
        _compare_source(),
        base_commit=PIN,
        base_subtree=PIN_TREE,
        head_commit=HEAD,
        head_subtree=HEAD_TREE,
        token=None,
        timeout_seconds=3,
        fetch_json=FakeFetch(responses),
        blob_cache={},
    )

    assert comparison["paths"] == ["README.md"]
    assert comparison["path_count"] == comparison["file_count"] == 1
    assert comparison["files"][0]["reviewability"] == "exact-blob-unified-patch"


def test_compare_fails_when_large_repository_page_omits_source_delta() -> None:
    responses, compare_url = _single_tracked_change_responses()
    responses[compare_url]["files"] = _external_comparison_files(101)

    with pytest.raises(UpstreamError, match="incomplete or disagrees"):
        upstreams._compare_inventory(
            _compare_source(),
            base_commit=PIN,
            base_subtree=PIN_TREE,
            head_commit=HEAD,
            head_subtree=HEAD_TREE,
            token=None,
            timeout_seconds=3,
            fetch_json=FakeFetch(responses),
            blob_cache={},
        )


def test_compare_fails_when_large_repository_page_omits_source_patch() -> None:
    responses, compare_url = _single_tracked_change_responses()
    tracked_file = responses[compare_url]["files"][0]
    tracked_file.pop("patch")
    responses[compare_url]["files"] = [
        *_external_comparison_files(101),
        tracked_file,
    ]

    with pytest.raises(UpstreamError, match="without a patch"):
        upstreams._compare_inventory(
            _compare_source(),
            base_commit=PIN,
            base_subtree=PIN_TREE,
            head_commit=HEAD,
            head_subtree=HEAD_TREE,
            token=None,
            timeout_seconds=3,
            fetch_json=FakeFetch(responses),
            blob_cache={},
        )


def test_compare_reconstructs_one_skill_change_at_github_file_response_cap() -> None:
    responses, compare_url = _single_tracked_change_responses()
    path = "README.md"
    new_content = _new_content(path)
    responses[upstreams._api_url("cursor/plugins", "git", "blobs", _git_blob_sha(new_content))] = (
        _blob_response(new_content)
    )
    responses[compare_url]["files"] = _external_comparison_files(upstreams.GITHUB_COMPARE_FILE_CAP)

    comparison = upstreams._compare_inventory(
        _compare_source(),
        base_commit=PIN,
        base_subtree=PIN_TREE,
        head_commit=HEAD,
        head_subtree=HEAD_TREE,
        token=None,
        timeout_seconds=3,
        fetch_json=FakeFetch(responses),
        blob_cache={},
    )

    assert comparison["complete"] is True
    assert comparison["paths"] == [path]
    assert comparison["path_count"] == comparison["file_count"] == 1
    file = comparison["files"][0]
    assert file["path"] == path
    assert file["status"] == "modified"
    assert file["reviewability"] == "exact-blob-unified-patch"
    assert file["old_identity"]["sha"] == _git_blob_sha(_old_content(path))
    assert file["new_identity"]["sha"] == _git_blob_sha(new_content)
    assert file["patch"].startswith("@@ -1 +1 @@ source-tree-exact\n")


@pytest.mark.parametrize(
    ("old_content", "new_content"),
    [
        (b"", b"new\n"),
        (b"old\n", b""),
        (b"old\n", b"new\n"),
        (b"old", b"new"),
        (b"same", b"same\n"),
        (b"same\n", b"same"),
        (b"first\nlast", b"changed\nlast"),
    ],
)
def test_source_tree_diff_round_trips_newline_boundaries(
    old_content: bytes,
    new_content: bytes,
) -> None:
    patch, additions, deletions = upstreams._complete_unified_patch(
        old_content,
        new_content,
    )

    assert (
        upstreams._apply_patch_to_exact_blob(
            old_content.decode(),
            patch,
            additions=additions,
            deletions=deletions,
        )
        == new_content
    )


def test_capped_compare_uses_compact_patch_for_tiny_change_in_large_blob() -> None:
    responses = _fake_responses()
    compare_url = next(url for url in responses if "/compare/" in url)
    pin_tree_url = next(url for url in responses if PIN_TREE in url and "recursive" in url)
    head_tree_url = next(url for url in responses if HEAD_TREE in url and "recursive" in url)
    path = "skills/large/SKILL.md"
    old_lines = [f"stable line {index:05}\n" for index in range(5_000)]
    new_lines = list(old_lines)
    new_lines[2_500] = "one reviewed change\n"
    old_content = "".join(old_lines).encode()
    new_content = "".join(new_lines).encode()
    old_sha = _git_blob_sha(old_content)
    new_sha = _git_blob_sha(new_content)
    responses[pin_tree_url] = _tree(PIN_TREE, [_blob(path, old_sha, size=len(old_content))])
    responses[head_tree_url] = _tree(HEAD_TREE, [_blob(path, new_sha, size=len(new_content))])
    responses[upstreams._api_url("cursor/plugins", "git", "blobs", old_sha)] = _blob_response(
        old_content
    )
    responses[upstreams._api_url("cursor/plugins", "git", "blobs", new_sha)] = _blob_response(
        new_content
    )
    responses[compare_url]["files"] = _external_comparison_files(upstreams.GITHUB_COMPARE_FILE_CAP)

    comparison = upstreams._compare_inventory(
        _compare_source(),
        base_commit=PIN,
        base_subtree=PIN_TREE,
        head_commit=HEAD,
        head_subtree=HEAD_TREE,
        token=None,
        timeout_seconds=3,
        fetch_json=FakeFetch(responses),
        blob_cache={},
    )

    assert len(old_content) > upstreams.MAX_FILE_PATCH_BYTES
    assert comparison["path_count"] == comparison["file_count"] == 1
    assert comparison["patch_bytes"] < 1024
    assert comparison["files"][0]["reviewability"] == "exact-blob-unified-patch"


def test_capped_compare_rejects_adversarial_text_above_line_budget() -> None:
    responses = _fake_responses()
    compare_url = next(url for url in responses if "/compare/" in url)
    pin_tree_url = next(url for url in responses if PIN_TREE in url and "recursive" in url)
    head_tree_url = next(url for url in responses if HEAD_TREE in url and "recursive" in url)
    path = "skills/adversarial/SKILL.md"
    old_content = b"alpha\nbeta\n" * ((upstreams.MAX_DIFF_LINES // 2) + 1)
    new_content = b"beta\nalpha\n" * ((upstreams.MAX_DIFF_LINES // 2) + 1)
    old_sha = _git_blob_sha(old_content)
    new_sha = _git_blob_sha(new_content)
    responses[pin_tree_url] = _tree(PIN_TREE, [_blob(path, old_sha, size=len(old_content))])
    responses[head_tree_url] = _tree(HEAD_TREE, [_blob(path, new_sha, size=len(new_content))])
    responses[upstreams._api_url("cursor/plugins", "git", "blobs", old_sha)] = _blob_response(
        old_content
    )
    responses[upstreams._api_url("cursor/plugins", "git", "blobs", new_sha)] = _blob_response(
        new_content
    )
    responses[compare_url]["files"] = _external_comparison_files(upstreams.GITHUB_COMPARE_FILE_CAP)

    with pytest.raises(UpstreamError, match=r"exceeds the 5000-line limit"):
        upstreams._compare_inventory(
            _compare_source(),
            base_commit=PIN,
            base_subtree=PIN_TREE,
            head_commit=HEAD,
            head_subtree=HEAD_TREE,
            token=None,
            timeout_seconds=3,
            fetch_json=FakeFetch(responses),
            blob_cache={},
        )


def test_source_tree_diff_enforces_aggregate_comparison_work_budget() -> None:
    line_count = 4_000
    old_lines = [f"stable-{index}\n" for index in range(line_count)]
    new_lines = list(old_lines)
    new_lines[line_count // 2] = "changed\n"
    old_content = "".join(old_lines).encode()
    new_content = "".join(new_lines).encode()
    diff_work_cells = [0]

    upstreams._complete_unified_patch(
        old_content,
        new_content,
        diff_work_cells=diff_work_cells,
    )

    assert diff_work_cells == [line_count * line_count]
    with pytest.raises(UpstreamError, match=r"25000000-cell comparison limit"):
        upstreams._complete_unified_patch(
            old_content,
            new_content,
            diff_work_cells=diff_work_cells,
        )


def test_compare_ignores_a_capped_repository_file_page_when_subtree_is_identical() -> None:
    responses = _fake_responses()
    compare_url = next(url for url in responses if "/compare/" in url)
    responses[compare_url]["files"] = _external_comparison_files(upstreams.GITHUB_COMPARE_FILE_CAP)

    comparison = upstreams._compare_inventory(
        _compare_source(),
        base_commit=PIN,
        base_subtree=PIN_TREE,
        head_commit=HEAD,
        head_subtree=PIN_TREE,
        token=None,
        timeout_seconds=3,
        fetch_json=FakeFetch(responses),
        blob_cache={},
    )

    assert comparison["paths"] == comparison["files"] == []
    assert comparison["path_count"] == comparison["file_count"] == 0


def test_compare_rejects_more_files_than_github_can_return() -> None:
    responses = _fake_responses()
    compare_url = next(url for url in responses if "/compare/" in url)
    responses[compare_url]["files"] = _external_comparison_files(
        upstreams.GITHUB_COMPARE_FILE_CAP + 1
    )

    with pytest.raises(UpstreamError, match=r"exceeds the documented 300-file response cap"):
        upstreams._compare_inventory(
            _compare_source(),
            base_commit=PIN,
            base_subtree=PIN_TREE,
            head_commit=HEAD,
            head_subtree=PIN_TREE,
            token=None,
            timeout_seconds=3,
            fetch_json=FakeFetch(responses),
            blob_cache={},
        )


def test_capped_compare_detects_unique_exact_source_rename() -> None:
    responses = _fake_responses()
    compare_url = next(url for url in responses if "/compare/" in url)
    pin_tree_url = next(url for url in responses if PIN_TREE in url and "recursive" in url)
    head_tree_url = next(url for url in responses if HEAD_TREE in url and "recursive" in url)
    old_path = "skills/old-name/SKILL.md"
    new_path = "skills/new-name/SKILL.md"
    content = b"# Exact rename\n"
    blob_sha = _git_blob_sha(content)
    responses[pin_tree_url] = _tree(PIN_TREE, [_blob(old_path, blob_sha, size=len(content))])
    responses[head_tree_url] = _tree(HEAD_TREE, [_blob(new_path, blob_sha, size=len(content))])
    responses[upstreams._api_url("cursor/plugins", "git", "blobs", blob_sha)] = _blob_response(
        content
    )
    responses[compare_url]["files"] = _external_comparison_files(upstreams.GITHUB_COMPARE_FILE_CAP)

    comparison = upstreams._compare_inventory(
        _compare_source(),
        base_commit=PIN,
        base_subtree=PIN_TREE,
        head_commit=HEAD,
        head_subtree=HEAD_TREE,
        token=None,
        timeout_seconds=3,
        fetch_json=FakeFetch(responses),
        blob_cache={},
    )

    assert comparison["paths"] == sorted([old_path, new_path])
    assert comparison["path_count"] == 2
    assert comparison["file_count"] == 1
    assert comparison["files"][0]["status"] == "renamed"
    assert comparison["files"][0]["previous_path"] == old_path
    assert comparison["files"][0]["path"] == new_path
    assert comparison["files"][0]["reviewability"] == "exact-blob-pure-rename"


def test_capped_compare_does_not_infer_rename_with_unchanged_duplicate_identity() -> None:
    responses = _fake_responses()
    compare_url = next(url for url in responses if "/compare/" in url)
    pin_tree_url = next(url for url in responses if PIN_TREE in url and "recursive" in url)
    head_tree_url = next(url for url in responses if HEAD_TREE in url and "recursive" in url)
    unchanged_path = "skills/shared/SKILL.md"
    removed_path = "skills/old-copy/SKILL.md"
    added_path = "skills/new-copy/SKILL.md"
    content = b"# Shared exact content\n"
    blob_sha = _git_blob_sha(content)
    unchanged = _blob(unchanged_path, blob_sha, size=len(content))
    responses[pin_tree_url] = _tree(
        PIN_TREE,
        [unchanged, _blob(removed_path, blob_sha, size=len(content))],
    )
    responses[head_tree_url] = _tree(
        HEAD_TREE,
        [unchanged, _blob(added_path, blob_sha, size=len(content))],
    )
    responses[upstreams._api_url("cursor/plugins", "git", "blobs", blob_sha)] = _blob_response(
        content
    )
    responses[compare_url]["files"] = _external_comparison_files(upstreams.GITHUB_COMPARE_FILE_CAP)

    comparison = upstreams._compare_inventory(
        _compare_source(),
        base_commit=PIN,
        base_subtree=PIN_TREE,
        head_commit=HEAD,
        head_subtree=HEAD_TREE,
        token=None,
        timeout_seconds=3,
        fetch_json=FakeFetch(responses),
        blob_cache={},
    )

    assert comparison["paths"] == sorted([removed_path, added_path])
    assert comparison["path_count"] == comparison["file_count"] == 2
    assert {item["status"] for item in comparison["files"]} == {"added", "removed"}
    assert all(item["previous_path"] is None for item in comparison["files"])
    assert all(item["reviewability"] == "exact-blob-unified-patch" for item in comparison["files"])


@pytest.mark.parametrize("direction", ["out", "in"])
def test_capped_compare_projects_cross_scope_rename_as_scoped_operation(direction: str) -> None:
    responses = _fake_responses()
    compare_url = next(url for url in responses if "/compare/" in url)
    pin_tree_url = next(url for url in responses if PIN_TREE in url and "recursive" in url)
    head_tree_url = next(url for url in responses if HEAD_TREE in url and "recursive" in url)
    path = "skills/renamed/SKILL.md"
    content = b"# Cross-boundary rename\n"
    blob_sha = _git_blob_sha(content)
    entry = _blob(path, blob_sha, size=len(content))
    if direction == "out":
        responses[pin_tree_url] = _tree(PIN_TREE, [entry])
        responses[head_tree_url] = _tree(HEAD_TREE, [])
        rename = _comparison_value(
            "outside/SKILL.md",
            "renamed",
            blob_sha,
            previous_filename=f"pstack/{path}",
        )
        expected_status = "removed"
    else:
        responses[pin_tree_url] = _tree(PIN_TREE, [])
        responses[head_tree_url] = _tree(HEAD_TREE, [entry])
        rename = _comparison_value(
            f"pstack/{path}",
            "renamed",
            blob_sha,
            previous_filename="outside/SKILL.md",
        )
        expected_status = "added"
    responses[upstreams._api_url("cursor/plugins", "git", "blobs", blob_sha)] = _blob_response(
        content
    )
    responses[compare_url]["files"] = [
        *_external_comparison_files(upstreams.GITHUB_COMPARE_FILE_CAP - 1),
        rename,
    ]

    comparison = upstreams._compare_inventory(
        _compare_source(),
        base_commit=PIN,
        base_subtree=PIN_TREE,
        head_commit=HEAD,
        head_subtree=HEAD_TREE,
        token=None,
        timeout_seconds=3,
        fetch_json=FakeFetch(responses),
        blob_cache={},
    )

    assert comparison["paths"] == [path]
    assert comparison["path_count"] == comparison["file_count"] == 1
    assert comparison["files"][0]["status"] == expected_status
    assert comparison["files"][0]["previous_path"] is None
    assert comparison["files"][0]["reviewability"] == "exact-blob-unified-patch"


@pytest.mark.parametrize("failure", ["truncated", "wrong-sha"])
def test_capped_compare_rejects_incomplete_or_unverifiable_exact_subtree(failure: str) -> None:
    responses, compare_url = _single_tracked_change_responses()
    head_tree_url = next(url for url in responses if HEAD_TREE in url and "recursive" in url)
    responses[compare_url]["files"] = _external_comparison_files(upstreams.GITHUB_COMPARE_FILE_CAP)
    if failure == "truncated":
        responses[head_tree_url]["truncated"] = True
        message = "truncated or malformed"
    else:
        responses[head_tree_url]["sha"] = "f" * 40
        message = "does not match the requested SHA"

    with pytest.raises(UpstreamError, match=message):
        upstreams._compare_inventory(
            _compare_source(),
            base_commit=PIN,
            base_subtree=PIN_TREE,
            head_commit=HEAD,
            head_subtree=HEAD_TREE,
            token=None,
            timeout_seconds=3,
            fetch_json=FakeFetch(responses),
            blob_cache={},
        )


def test_compare_rejects_more_than_100_tracked_subtree_paths_before_fetching_patches() -> None:
    pin_url = upstreams._api_url(
        "cursor/plugins", "git", "trees", PIN_TREE, query=(("recursive", "1"),)
    )
    head_url = upstreams._api_url(
        "cursor/plugins", "git", "trees", HEAD_TREE, query=(("recursive", "1"),)
    )
    responses = {
        pin_url: _tree(PIN_TREE, []),
        head_url: _tree(
            HEAD_TREE,
            [
                _blob(f"changed-{index:03}.md", f"{20_000 + index:040x}")
                for index in range(upstreams.MAX_COMPARE_FILES + 1)
            ],
        ),
    }
    fetch = FakeFetch(responses)

    with pytest.raises(UpstreamError, match="exceeds the 100-file limit"):
        upstreams._compare_inventory(
            _compare_source(),
            base_commit=PIN,
            base_subtree=PIN_TREE,
            head_commit=HEAD,
            head_subtree=HEAD_TREE,
            token=None,
            timeout_seconds=3,
            fetch_json=fetch,
            blob_cache={},
        )
    assert [call[0] for call in fetch.calls] == [pin_url, head_url]


def test_check_fails_closed_on_non_fast_forward_or_incomplete_compare(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    non_ff = _fake_responses()
    compare_url = next(url for url in non_ff if "/compare/" in url)
    non_ff[compare_url] = {**non_ff[compare_url], "status": "diverged", "behind_by": 1}
    with pytest.raises(UpstreamError, match="fast-forward"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(non_ff), environ={})

    incomplete = _fake_responses()
    incomplete[compare_url] = {
        **incomplete[compare_url],
        "files": incomplete[compare_url]["files"][:-1],
    }
    with pytest.raises(UpstreamError, match="incomplete or disagrees"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(incomplete), environ={})

    missing_page = _fake_responses()
    missing_page[compare_url] = {**missing_page[compare_url], "commits": []}
    with pytest.raises(UpstreamError, match="commit page is missing"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(missing_page), environ={})

    wrong_blob = _fake_responses()
    wrong_blob[compare_url]["files"][0]["sha"] = "f" * 40
    with pytest.raises(UpstreamError, match="SHA disagrees"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(wrong_blob), environ={})


def test_check_rejects_fabricated_same_count_patch_against_exact_blob(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    responses = _fake_responses()
    compare_url = next(url for url in responses if "/compare/" in url)
    responses[compare_url]["files"][0]["patch"] = "@@ -1 +1 @@\n-fabricated\n+also-fake"

    with pytest.raises(UpstreamError, match="does not match pinned blob"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})


def test_blob_response_content_must_recompute_to_requested_git_oid(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    responses = _fake_responses()
    path = next(path for path in CHANGED_PATHS if path != "assets/logo.png")
    expected_content = _old_content(path)
    sha = _git_blob_sha(expected_content)
    fabricated = b"x" * len(expected_content)
    responses[upstreams._api_url("cursor/plugins", "git", "blobs", sha)] = {
        "sha": sha,
        "encoding": "base64",
        "size": len(fabricated),
        "content": base64.b64encode(fabricated).decode(),
    }

    with pytest.raises(UpstreamError, match="does not match the exact Git blob SHA"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})


def test_check_fails_closed_on_truncated_tree_or_patch_bound(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    truncated = _fake_responses()
    tree_url = next(url for url in truncated if PIN_TREE in url and "recursive" in url)
    truncated[tree_url] = {**truncated[tree_url], "truncated": True}
    with pytest.raises(UpstreamError, match="truncated or malformed"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(truncated), environ={})

    too_large = _fake_responses()
    compare_url = next(url for url in too_large if "/compare/" in url)
    too_large[compare_url]["files"][0]["patch"] = "x" * (upstreams.MAX_FILE_PATCH_BYTES + 1)
    with pytest.raises(UpstreamError, match="file patch exceeds"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(too_large), environ={})

    aggregate = _fake_responses()
    pin_tree_url = next(url for url in aggregate if PIN_TREE in url and "recursive" in url)
    head_tree_url = next(url for url in aggregate if HEAD_TREE in url and "recursive" in url)
    pin_entries = {item["path"]: item for item in aggregate[pin_tree_url]["tree"]}
    head_entries = {item["path"]: item for item in aggregate[head_tree_url]["tree"]}
    for item in aggregate[compare_url]["files"]:
        if "patch" not in item:
            continue
        path = item["filename"].removeprefix("pstack/")
        old_content = ("old " + path + "x" * 6000 + "\n").encode()
        new_content = ("new " + path + "y" * 6000 + "\n").encode()
        old_sha = _git_blob_sha(old_content)
        new_sha = _git_blob_sha(new_content)
        item["patch"] = (
            f"@@ -1 +1 @@ {path}\n-{old_content.decode().rstrip()}\n"
            f"+{new_content.decode().rstrip()}"
        )
        item["sha"] = new_sha
        pin_entries[path].update(sha=old_sha, size=len(old_content))
        head_entries[path].update(sha=new_sha, size=len(new_content))
        aggregate[upstreams._api_url("cursor/plugins", "git", "blobs", old_sha)] = _blob_response(
            old_content
        )
    with pytest.raises(UpstreamError, match="patches exceed"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(aggregate), environ={})


def test_semantic_skill_requires_complete_count_reconciled_patch() -> None:
    semantic_path = "pstack/skills/pkstack/SKILL.md"
    missing = _comparison_value(semantic_path, "modified", "a" * 40)
    missing["patch"] = None
    with pytest.raises(UpstreamError, match="without a patch must report zero"):
        upstreams._comparison_file(missing, source_path="pstack", index=0)

    unavailable = _comparison_value(semantic_path, "modified", "a" * 40)
    unavailable.update(patch=None, additions=0, deletions=0, changes=0)
    parsed = upstreams._comparison_file(unavailable, source_path="pstack", index=1)
    assert parsed is not None
    with pytest.raises(UpstreamError, match="exact subtree trees"):
        upstreams._validate_comparison_file_tree_identity(
            parsed,
            pinned_files={"skills/pkstack/SKILL.md": ("blob", "100644", "b" * 40, 10)},
            current_files={"skills/pkstack/SKILL.md": ("blob", "100644", "a" * 40, 10)},
        )

    truncated = _comparison_value(semantic_path, "modified", "a" * 40)
    truncated["patch"] = "@@ -1 +1 @@\n-old"
    with pytest.raises(UpstreamError, match="truncated or malformed"):
        upstreams._comparison_file(truncated, source_path="pstack", index=2)

    mismatched = _comparison_value(semantic_path, "modified", "a" * 40)
    mismatched.update(additions=2, deletions=0, changes=2)
    with pytest.raises(UpstreamError, match="body counts do not match"):
        upstreams._comparison_file(mismatched, source_path="pstack", index=3)


@pytest.mark.parametrize(
    "path",
    [
        "pstack/skills/pkstack/logo.png",
        "pstack/assets/config.md",
        "pstack/assets/SKILL.md.png",
        "pstack/assets/logo.svg",
        "pstack/assets/nested/logo.png",
    ],
)
def test_no_patch_image_exception_rejects_malicious_extensions_and_paths(path: str) -> None:
    value = _comparison_value(path, "added", "a" * 40)
    value.update(patch=None, additions=0, deletions=0, changes=0)

    with pytest.raises(UpstreamError, match="semantic or unclassified"):
        upstreams._comparison_file(value, source_path="pstack", index=0)


def test_no_patch_logo_is_explicitly_unavailable_and_tree_bound() -> None:
    sha = "a" * 40
    value = _comparison_value("pstack/assets/logo.png", "added", sha)
    value.update(patch=None, additions=0, deletions=0, changes=0)

    parsed = upstreams._comparison_file(value, source_path="pstack", index=0)

    assert parsed is not None
    assert parsed["reviewability"] == "unavailable-nonsemantic-image"
    assert parsed["content_class"] == "binary-or-patch-unavailable"
    upstreams._validate_comparison_file_tree_identity(
        parsed,
        pinned_files={},
        current_files={"assets/logo.png": ("blob", "100644", sha, 10)},
    )
    assert parsed["tree_sha_verified"] is True


def test_zero_change_semantic_rename_requires_equal_in_subtree_blob_identity() -> None:
    content = b"same semantic content\n"
    sha = _git_blob_sha(content)
    value = _comparison_value(
        "pstack/skills/new.md",
        "renamed",
        sha,
        previous_filename="pstack/skills/old.md",
    )
    value.update(patch=None, additions=0, deletions=0, changes=0)
    parsed = upstreams._comparison_file(value, source_path="pstack", index=0)

    assert parsed is not None
    assert parsed["reviewability"] == "pending-exact-blob-pure-rename"
    identity = ("blob", "100644", sha, len(content))
    upstreams._validate_comparison_file_tree_identity(
        parsed,
        pinned_files={"skills/old.md": identity},
        current_files={"skills/new.md": identity},
    )
    assert parsed["tree_sha_verified"] is True
    upstreams._bind_comparison_file_to_blobs(
        parsed,
        repository="cursor/plugins",
        token=None,
        timeout_seconds=10,
        fetch_json=FakeFetch(
            {upstreams._api_url("cursor/plugins", "git", "blobs", sha): _blob_response(content)}
        ),
        blob_cache={},
    )
    assert parsed["reviewability"] == "exact-blob-pure-rename"
    assert parsed["content_class"] == "exact-blob-identity"

    tampered = dict(parsed)
    with pytest.raises(UpstreamError, match="exact subtree trees"):
        upstreams._validate_comparison_file_tree_identity(
            tampered,
            pinned_files={"skills/old.md": identity},
            current_files={"skills/new.md": ("blob", "100644", "b" * 40, 10)},
        )


def test_content_and_executable_mode_change_are_both_inventory_bound() -> None:
    path = "skills/tool.md"
    old_content = b"old\n"
    new_content = b"new\n"
    old_sha = _git_blob_sha(old_content)
    new_sha = _git_blob_sha(new_content)
    value = _comparison_value(f"pstack/{path}", "modified", new_sha)
    parsed = upstreams._comparison_file(value, source_path="pstack", index=0)

    assert parsed is not None
    upstreams._validate_comparison_file_tree_identity(
        parsed,
        pinned_files={path: ("blob", "100644", old_sha, len(old_content))},
        current_files={path: ("blob", "100755", new_sha, len(new_content))},
    )
    upstreams._bind_comparison_file_to_blobs(
        parsed,
        repository="cursor/plugins",
        token=None,
        timeout_seconds=10,
        fetch_json=FakeFetch(
            {
                upstreams._api_url("cursor/plugins", "git", "blobs", old_sha): _blob_response(
                    old_content
                )
            }
        ),
        blob_cache={},
    )

    assert parsed["old_identity"]["mode"] == "100644"
    assert parsed["new_identity"]["mode"] == "100755"
    assert parsed["reviewability"] == "exact-blob-unified-patch"
    altered = json.loads(json.dumps(parsed))
    altered["new_identity"]["mode"] = "100644"
    assert upstreams._inventory_sha256(
        repository="cursor/plugins",
        source_path="pstack",
        base_commit=PIN,
        head_commit=HEAD,
        files=[parsed],
    ) != upstreams._inventory_sha256(
        repository="cursor/plugins",
        source_path="pstack",
        base_commit=PIN,
        head_commit=HEAD,
        files=[altered],
    )


def test_same_blob_mode_only_change_is_exactly_bound() -> None:
    path = "skills/tool.md"
    content = b"same\n"
    sha = _git_blob_sha(content)
    value = _comparison_value(f"pstack/{path}", "modified", sha)
    value.update(patch=None, additions=0, deletions=0, changes=0)
    parsed = upstreams._comparison_file(value, source_path="pstack", index=0)

    assert parsed is not None
    assert parsed["reviewability"] == "pending-exact-blob-mode-change"
    upstreams._validate_comparison_file_tree_identity(
        parsed,
        pinned_files={path: ("blob", "100644", sha, len(content))},
        current_files={path: ("blob", "100755", sha, len(content))},
    )
    upstreams._bind_comparison_file_to_blobs(
        parsed,
        repository="cursor/plugins",
        token=None,
        timeout_seconds=10,
        fetch_json=FakeFetch(
            {upstreams._api_url("cursor/plugins", "git", "blobs", sha): _blob_response(content)}
        ),
        blob_cache={},
    )

    assert parsed["reviewability"] == "exact-blob-mode-change"
    assert parsed["content_class"] == "exact-blob-identity"


@pytest.mark.parametrize(
    ("entry_type", "mode"),
    [("blob", "120000"), ("commit", "160000")],
)
def test_changed_symlink_or_submodule_tree_entry_fails_closed(
    entry_type: str,
    mode: str,
) -> None:
    path = "skills/tool.md"
    new_sha = "b" * 40
    parsed = upstreams._comparison_file(
        _comparison_value(f"pstack/{path}", "modified", new_sha),
        source_path="pstack",
        index=0,
    )

    assert parsed is not None
    with pytest.raises(UpstreamError, match="regular blob"):
        upstreams._validate_comparison_file_tree_identity(
            parsed,
            pinned_files={path: ("blob", "100644", "a" * 40, 10)},
            current_files={path: (entry_type, mode, new_sha, 10)},
        )


def _comparison_value(
    filename: str,
    status: str,
    sha: str,
    *,
    previous_filename: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "filename": filename,
        "status": status,
        "sha": sha,
        "additions": 1,
        "deletions": 1,
        "changes": 2,
        "patch": "@@ -1 +1 @@\n-old\n+new",
    }
    if previous_filename is not None:
        value["previous_filename"] = previous_filename
    return value


def test_ref_only_movement_preserves_accepted_parity_without_a_transition(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    parity = _skill_parity_document()
    parity["source"]["current"] = copy.deepcopy(parity["source"]["pinned"])
    for skill in parity["skills"]:
        skill["current"] = copy.deepcopy(skill["pinned"])
    count = parity["summary"]["pinned_package_files"]
    parity["summary"]["current_package_files"] = count
    parity["summary"]["semantic_source_files"] = count
    _write_skill_parity(tmp_path, parity)
    manifest_before = (tmp_path / "maintenance/upstreams.json").read_bytes()
    ledger_before = (tmp_path / "maintenance/upstream-reviews.json").read_bytes()
    responses = _fake_responses()
    root_url = upstreams._api_url("cursor/plugins", "git", "trees", HEAD_ROOT_TREE)
    responses[root_url]["tree"][0]["sha"] = PIN_TREE
    compare_url = next(url for url in responses if "/compare/" in url)
    responses[compare_url]["files"] = _external_comparison_files(1)

    result = check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})

    assert result["ok"] is True
    source = result["sources"][0]
    assert source["drift"] is False
    assert source["current"]["commit"] == HEAD
    assert source["current"]["subtree_sha"] == PIN_TREE
    assert source["source_parity"]["status"] == "accepted-baseline"
    assert source["source_parity"]["candidate_ready"] is False
    assert source["comparison"]["paths"] == []
    assert (tmp_path / "maintenance/upstreams.json").read_bytes() == manifest_before
    assert (tmp_path / "maintenance/upstream-reviews.json").read_bytes() == ledger_before


def test_compare_ignores_changes_wholly_outside_subtree() -> None:
    sha = "a" * 40
    assert (
        upstreams._comparison_file(
            _comparison_value(
                "other/new.md",
                "renamed",
                sha,
                previous_filename="other/old.md",
            ),
            source_path="pstack",
            index=0,
        )
        is None
    )
    assert (
        upstreams._comparison_file(
            _comparison_value("other/removed.md", "removed", sha),
            source_path="pstack",
            index=1,
        )
        is None
    )
    assert (
        upstreams._comparison_file(
            _comparison_value(
                "other/copied.md",
                "copied",
                sha,
                previous_filename="pstack/source.md",
            ),
            source_path="pstack",
            index=2,
        )
        is None
    )


def test_compare_accounts_cross_boundary_renames_and_copies_exactly() -> None:
    old_sha = "a" * 40
    new_sha = "b" * 40
    old_identity = ("blob", "100644", old_sha, 10)
    new_identity = ("blob", "100644", new_sha, 10)

    moved_out = upstreams._comparison_file(
        _comparison_value(
            "other/new.md",
            "renamed",
            new_sha,
            previous_filename="pstack/old.md",
        ),
        source_path="pstack",
        index=0,
    )
    assert moved_out is not None
    assert moved_out["_identities"] == ["old.md"]
    upstreams._validate_comparison_file_tree_identity(
        moved_out,
        pinned_files={"old.md": old_identity},
        current_files={},
    )
    assert moved_out["tree_sha_verified"] is False

    moved_in = upstreams._comparison_file(
        _comparison_value(
            "pstack/new.md",
            "renamed",
            new_sha,
            previous_filename="other/old.md",
        ),
        source_path="pstack",
        index=1,
    )
    assert moved_in is not None
    assert moved_in["_identities"] == ["new.md"]
    upstreams._validate_comparison_file_tree_identity(
        moved_in,
        pinned_files={},
        current_files={"new.md": new_identity},
    )
    assert moved_in["tree_sha_verified"] is True

    copied_in = upstreams._comparison_file(
        _comparison_value(
            "pstack/copied.md",
            "copied",
            new_sha,
            previous_filename="other/source.md",
        ),
        source_path="pstack",
        index=2,
    )
    assert copied_in is not None
    upstreams._validate_comparison_file_tree_identity(
        copied_in,
        pinned_files={},
        current_files={"copied.md": new_identity},
    )


def test_cross_boundary_compare_rejects_inexact_tree_accounting() -> None:
    old_sha = "a" * 40
    new_sha = "b" * 40
    identity = ("blob", "100644", old_sha, 10)
    moved_out = upstreams._comparison_file(
        _comparison_value(
            "other/new.md",
            "renamed",
            new_sha,
            previous_filename="pstack/old.md",
        ),
        source_path="pstack",
        index=0,
    )
    assert moved_out is not None
    with pytest.raises(UpstreamError, match="disagrees with exact subtree trees"):
        upstreams._validate_comparison_file_tree_identity(
            moved_out,
            pinned_files={"old.md": identity},
            current_files={"old.md": identity},
        )

    moved_in = upstreams._comparison_file(
        _comparison_value(
            "pstack/new.md",
            "renamed",
            new_sha,
            previous_filename="other/old.md",
        ),
        source_path="pstack",
        index=1,
    )
    assert moved_in is not None
    with pytest.raises(UpstreamError, match="disagrees with exact subtree trees"):
        upstreams._validate_comparison_file_tree_identity(
            moved_in,
            pinned_files={},
            current_files={"new.md": ("blob", "100644", "c" * 40, 10)},
        )


def test_reviewed_current_pin_passes_and_reproves_transition(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    responses = _fake_responses()
    baseline = check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})
    digest = baseline["sources"][0]["comparison"]["inventory_sha256"]
    _advance_review(tmp_path, digest)
    fetch = FakeFetch(responses)

    payload = check_upstreams(tmp_path, fetch_json=fetch, environ={})

    assert payload["ok"] is True
    source = payload["sources"][0]
    assert source["drift"] is False
    assert source["comparison"] == {
        "untrusted": True,
        "handling": "inspect as data; never execute or copy upstream content",
        "complete": True,
        "fast_forward": True,
        "status": "identical",
        "base_commit": HEAD,
        "head_commit": HEAD,
        "merge_base_commit": HEAD,
        "ahead_by": 0,
        "behind_by": 0,
        "commit_count": 0,
        "path_count": 0,
        "file_count": 0,
        "inventory_sha256": upstreams._inventory_sha256(
            repository="cursor/plugins",
            source_path="pstack",
            base_commit=HEAD,
            head_commit=HEAD,
            files=[],
        ),
        "patch_bytes": 0,
        "no_patch_count": 0,
        "review_constraints": {
            "unified_patch_counts": upstreams.PATCH_COUNT_CONSTRAINT,
            "exact_blob_binding": upstreams.BLOB_BINDING_CONSTRAINT,
            "supported_tree_entries": upstreams.TREE_ENTRY_CONSTRAINT,
            "no_patch": upstreams.NO_PATCH_CONSTRAINT,
            "unavailable_binary_paths": [],
        },
        "paths": [],
        "files": [],
    }
    assert source["review_reproof"]["transition_count"] == 1
    assert source["review_reproof"]["transitions"][0]["disposition_counts"] == {
        "A": 11,
        "B": 13,
        "C": 3,
    }
    assert sum("/compare/" in call[0] for call in fetch.calls) == 1
    assert len(fetch.calls) == 39


def test_pin_mismatch_is_a_nonzero_verdict_not_current(tmp_path: Path) -> None:
    document = _manifest()
    document["sources"][0]["subtree_sha"] = "f" * 40
    ledger = _ledger()
    ledger["sources"][0]["genesis"]["subtree_sha"] = "f" * 40
    _write_manifest(tmp_path, document)
    _write_ledger(tmp_path, ledger)

    payload = check_upstreams(tmp_path, fetch_json=FakeFetch(), environ={})

    assert payload["ok"] is False
    assert payload["sources"][0]["pinned_reproof"]["ok"] is False
    assert payload["sources"][0]["drift"] is True


def test_manifest_pin_only_advance_is_rejected_before_network(tmp_path: Path) -> None:
    document = _manifest()
    document["sources"][0].update(commit=HEAD, subtree_sha=HEAD_TREE)
    _write_manifest(tmp_path, document)
    fetch = FakeFetch()

    with pytest.raises(UpstreamError, match="pin-only advances are rejected"):
        check_upstreams(tmp_path, fetch_json=fetch, environ={})

    assert fetch.calls == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda transition: transition["dispositions"].pop(), "exactly match"),
        (
            lambda transition: transition["dispositions"].append(
                {
                    "path": "unexpected.md",
                    "disposition": "C",
                    "rationale": "Reviewed and excluded as unrelated.",
                }
            ),
            "exactly match",
        ),
        (
            lambda transition: transition["dispositions"].__setitem__(
                -1, dict(transition["dispositions"][0])
            ),
            "duplicate paths",
        ),
        (lambda transition: transition.update(inventory_sha256="f" * 64), "digest"),
        (
            lambda transition: transition["dispositions"][0].update(rationale=" "),
            "rationale",
        ),
        (
            lambda transition: transition["dispositions"][0].update(disposition="D"),
            "A, B, or C",
        ),
    ],
)
def test_review_ledger_rejects_missing_duplicate_extra_or_tampered_dispositions(
    tmp_path: Path,
    mutation: Any,
    message: str,
) -> None:
    _write_manifest(tmp_path)
    responses = _fake_responses()
    baseline = check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})
    digest = baseline["sources"][0]["comparison"]["inventory_sha256"]
    _advance_review(tmp_path, digest)
    ledger = json.loads(
        (tmp_path / "maintenance" / "upstream-reviews.json").read_text(encoding="utf-8")
    )
    mutation(ledger["sources"][0]["transitions"][0])
    _write_ledger(tmp_path, ledger)
    _rewrite_provenance_markers(
        tmp_path,
        ledger["sources"][0]["transitions"],
        genesis=ledger["sources"][0]["genesis"],
    )

    with pytest.raises(UpstreamError, match=message):
        check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})


def test_review_ledger_rejects_wrong_source_identity_and_stale_chain(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    ledger = _ledger()
    ledger["sources"][0]["repository"] = "other/project"
    _write_ledger(tmp_path, ledger)
    with pytest.raises(UpstreamError, match="does not match the manifest"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(), environ={})

    ledger = _ledger()
    ledger["sources"][0]["transitions"] = [
        {
            **_transition("f" * 64),
            "prior": {"commit": "a" * 40, "subtree_sha": PIN_TREE},
        }
    ]
    _write_ledger(tmp_path, ledger)
    with pytest.raises(UpstreamError, match="stale or non-contiguous"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(), environ={})


def test_review_transition_reproof_rejects_remote_identity_and_non_fast_forward(
    tmp_path: Path,
) -> None:
    _write_manifest(tmp_path)
    responses = _fake_responses()
    baseline = check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})
    _advance_review(tmp_path, baseline["sources"][0]["comparison"]["inventory_sha256"])

    wrong_identity = _fake_responses()
    pin_url = upstreams._api_url("cursor/plugins", "commits", PIN)
    wrong_identity[pin_url] = {**wrong_identity[pin_url], "sha": "f" * 40}
    with pytest.raises(UpstreamError, match="remote identities"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(wrong_identity), environ={})

    non_ff = _fake_responses()
    compare_url = next(url for url in non_ff if "/compare/" in url)
    non_ff[compare_url] = {**non_ff[compare_url], "status": "diverged", "behind_by": 1}
    with pytest.raises(UpstreamError, match="fast-forward"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(non_ff), environ={})


def test_check_rejects_tampered_provenance_after_review_acceptance(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    responses = _fake_responses()
    baseline = check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})
    _advance_review(tmp_path, baseline["sources"][0]["comparison"]["inventory_sha256"])
    provenance = tmp_path / "powers" / "pkstack" / "docs" / "provenance.md"
    provenance.write_text("# Stale provenance\n", encoding="utf-8")

    with pytest.raises(UpstreamError, match="provenance review markers"):
        check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})


def test_zero_transition_provenance_requires_one_exact_genesis_marker(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    parsed = load_upstream_manifest(tmp_path)
    source = parsed.sources[0]
    provenance = tmp_path / source.provenance_path

    def validate() -> None:
        upstreams._require_provenance_review_markers(
            tmp_path,
            source,
            (),
            genesis_commit=PIN,
            genesis_subtree_sha=PIN_TREE,
        )

    validate()
    expected = _genesis_marker()
    changed_values = {
        "source_id": "other-source",
        "repository": "other/project",
        "path": "other-path",
        "commit": "f" * 40,
        "subtree_sha": "e" * 40,
    }
    invalid_documents = ["# Provenance\n"]
    invalid_documents.extend(
        "# Provenance\n" + _marker_line("genesis", {**expected, key: changed}) + "\n"
        for key, changed in changed_values.items()
    )
    invalid_documents += [
        "# Provenance\n"
        + _marker_line("genesis", expected)
        + "\n"
        + _marker_line("genesis", expected)
        + "\n",
        "# Provenance\n"
        + _marker_line("genesis", expected)
        + "\n"
        + _marker_line("review", _provenance_marker(_transition("a" * 64)))
        + "\n",
    ]
    for document in invalid_documents:
        provenance.write_text(document, encoding="utf-8")
        with pytest.raises(UpstreamError, match="required genesis marker"):
            validate()

    noncanonical = json.dumps(expected, sort_keys=True)
    provenance.write_text(
        f"# Provenance\n<!-- pk-stack-upstream-genesis: {noncanonical} -->\n",
        encoding="utf-8",
    )
    with pytest.raises(UpstreamError, match="genesis marker is not canonical"):
        validate()

    provenance.write_text(
        "# Provenance\n<!-- pk-stack-upstream-genesis: not-json -->\n",
        encoding="utf-8",
    )
    with pytest.raises(UpstreamError, match="genesis marker is not valid JSON"):
        validate()


def test_genesis_ledger_rejects_unaccepted_provenance_marker(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    _write_provenance_marker(tmp_path, _transition("a" * 64))
    fetch = FakeFetch(_fake_responses())

    with pytest.raises(UpstreamError, match="provenance review markers"):
        check_upstreams(tmp_path, fetch_json=fetch, environ={})
    assert fetch.calls == []


def test_genesis_ledger_rejects_malformed_provenance_marker(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    provenance = tmp_path / "powers" / "pkstack" / "docs" / "provenance.md"
    provenance.write_text(
        "# Provenance\n<!-- pk-stack-upstream-review: not-json -->\n",
        encoding="utf-8",
    )
    fetch = FakeFetch(_fake_responses())

    with pytest.raises(UpstreamError, match="provenance review marker"):
        check_upstreams(tmp_path, fetch_json=fetch, environ={})
    assert fetch.calls == []


def test_provenance_markers_bind_full_ordered_transition_history(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    first_document = _transition("a" * 64)
    second_document = {
        "prior": {"commit": HEAD, "subtree_sha": HEAD_TREE},
        "new": {"commit": "c" * 40, "subtree_sha": "d" * 40},
        "inventory_sha256": "b" * 64,
        "dispositions": [],
    }
    transitions = (
        upstreams._parse_review_transition(first_document, context="test first"),
        upstreams._parse_review_transition(second_document, context="test second"),
    )
    source = upstreams.UpstreamSource(
        source_id="cursor-pstack",
        repository="cursor/plugins",
        path="pstack",
        ref="main",
        commit="c" * 40,
        subtree_sha="d" * 40,
        provenance_path="powers/pkstack/docs/provenance.md",
        parity_path="powers/pkstack/docs/upstream-skill-parity.json",
    )
    provenance = tmp_path / source.provenance_path

    def write_markers(
        markers: list[dict[str, Any]],
        *,
        genesis: dict[str, Any] | None = None,
    ) -> None:
        lines = [_marker_line("genesis", _genesis_marker() if genesis is None else genesis)]
        lines.extend(_marker_line("review", marker) for marker in markers)
        provenance.write_text("# Provenance\n" + "\n".join(lines) + "\n", encoding="utf-8")

    expected = [_provenance_marker(first_document), _provenance_marker(second_document)]
    write_markers(expected)
    upstreams._require_provenance_review_markers(
        tmp_path,
        source,
        transitions,
        genesis_commit=PIN,
        genesis_subtree_sha=PIN_TREE,
    )

    for mutate in (
        lambda markers: markers[0]["prior"].update(commit="f" * 40),
        lambda markers: markers[0]["new"].update(subtree_sha="f" * 40),
        lambda markers: markers[0].update(inventory_sha256="f" * 64),
        lambda markers: markers[0].update(source_id="other"),
    ):
        tampered = json.loads(json.dumps(expected))
        mutate(tampered)
        write_markers(tampered)
        with pytest.raises(UpstreamError, match="ordered review ledger"):
            upstreams._require_provenance_review_markers(
                tmp_path,
                source,
                transitions,
                genesis_commit=PIN,
                genesis_subtree_sha=PIN_TREE,
            )

    for tampered in ([expected[0], expected[0], expected[1]], list(reversed(expected))):
        write_markers(json.loads(json.dumps(tampered)))
        with pytest.raises(UpstreamError, match="ordered review ledger"):
            upstreams._require_provenance_review_markers(
                tmp_path,
                source,
                transitions,
                genesis_commit=PIN,
                genesis_subtree_sha=PIN_TREE,
            )

    changed_genesis = _genesis_marker()
    changed_genesis["repository"] = "other/project"
    for lines in (
        [
            _marker_line("review", expected[0]),
            _marker_line("genesis", _genesis_marker()),
            _marker_line("review", expected[1]),
        ],
        [
            _marker_line("genesis", _genesis_marker()),
            _marker_line("genesis", _genesis_marker()),
            *[_marker_line("review", marker) for marker in expected],
        ],
        [
            _marker_line("genesis", changed_genesis),
            *[_marker_line("review", marker) for marker in expected],
        ],
    ):
        provenance.write_text("# Provenance\n" + "\n".join(lines) + "\n", encoding="utf-8")
        with pytest.raises(UpstreamError, match="required genesis marker"):
            upstreams._require_provenance_review_markers(
                tmp_path,
                source,
                transitions,
                genesis_commit=PIN,
                genesis_subtree_sha=PIN_TREE,
            )

    provenance.write_text(
        "# Provenance\n<!-- pk-stack-upstream-review: {bad json} -->\n",
        encoding="utf-8",
    )
    with pytest.raises(UpstreamError, match="valid JSON"):
        upstreams._require_provenance_review_markers(
            tmp_path,
            source,
            transitions,
            genesis_commit=PIN,
            genesis_subtree_sha=PIN_TREE,
        )

    provenance.write_bytes(b"x" * (upstreams.MAX_PROVENANCE_BYTES + 1))
    with pytest.raises(UpstreamError, match="provenance exceeds"):
        upstreams._require_provenance_review_markers(
            tmp_path,
            source,
            transitions,
            genesis_commit=PIN,
            genesis_subtree_sha=PIN_TREE,
        )


def test_remote_review_reproof_cost_is_constant_at_maximum_history() -> None:
    def run(count: int) -> tuple[dict[str, Any], int]:
        commits = [f"{10_000 + index:040x}" for index in range(count + 1)]
        subtrees = [f"{20_000 + index:040x}" for index in range(count + 1)]
        transitions = tuple(
            upstreams.ReviewTransition(
                prior_commit=commits[index],
                prior_subtree_sha=subtrees[index],
                new_commit=commits[index + 1],
                new_subtree_sha=subtrees[index + 1],
                inventory_sha256=upstreams._inventory_sha256(
                    repository="cursor/plugins",
                    source_path="pstack",
                    base_commit=commits[index],
                    head_commit=commits[index + 1],
                    files=[],
                ),
                dispositions=(),
            )
            for index in range(count)
        )
        source = upstreams.UpstreamSource(
            source_id="cursor-pstack",
            repository="cursor/plugins",
            path="pstack",
            ref="main",
            commit=commits[-1],
            subtree_sha=subtrees[-1],
            provenance_path="powers/pkstack/docs/provenance.md",
            parity_path="powers/pkstack/docs/upstream-skill-parity.json",
        )
        review = upstreams.UpstreamReview(
            source_id=source.source_id,
            repository=source.repository,
            path=source.path,
            provenance_path=source.provenance_path,
            parity_path=source.parity_path,
            genesis_commit=commits[0],
            genesis_subtree_sha=subtrees[0],
            transitions=transitions,
        )
        base = commits[-2]
        head = commits[-1]
        base_subtree = subtrees[-2]
        head_subtree = subtrees[-1]
        base_root = "a" * 40
        head_root = "b" * 40
        responses = {
            upstreams._api_url("cursor/plugins", "commits", base): {
                "sha": base,
                "commit": {"tree": {"sha": base_root}},
            },
            upstreams._api_url("cursor/plugins", "commits", head): {
                "sha": head,
                "commit": {"tree": {"sha": head_root}},
            },
            upstreams._api_url("cursor/plugins", "git", "trees", base_root): _tree(
                base_root,
                [{"path": "pstack", "mode": "040000", "type": "tree", "sha": base_subtree}],
            ),
            upstreams._api_url("cursor/plugins", "git", "trees", head_root): _tree(
                head_root,
                [{"path": "pstack", "mode": "040000", "type": "tree", "sha": head_subtree}],
            ),
            upstreams._api_url(
                "cursor/plugins", "git", "trees", base_subtree, query=(("recursive", "1"),)
            ): _tree(base_subtree, []),
            upstreams._api_url(
                "cursor/plugins", "git", "trees", head_subtree, query=(("recursive", "1"),)
            ): _tree(head_subtree, []),
            upstreams._api_url(
                "cursor/plugins",
                "compare",
                f"{base}...{head}",
                query=(("per_page", "100"), ("page", "1")),
            ): {
                "status": "ahead",
                "ahead_by": 1,
                "behind_by": 0,
                "total_commits": 1,
                "base_commit": {"sha": base},
                "merge_base_commit": {"sha": base},
                "commits": [{"sha": head}],
                "files": [],
            },
        }
        fetch = FakeFetch(responses)
        result = upstreams._reprove_review_transitions(
            source,
            review,
            token=None,
            timeout_seconds=10,
            fetch_json=fetch,
            blob_cache={},
        )
        return result, len(fetch.calls)

    _, one_calls = run(1)
    maximum, maximum_calls = run(upstreams.MAX_REVIEW_TRANSITIONS)
    assert one_calls == maximum_calls == 7
    assert maximum["transition_count"] == upstreams.MAX_REVIEW_TRANSITIONS
    assert maximum["remote_transition_indices"] == [upstreams.MAX_REVIEW_TRANSITIONS - 1]
    assert "repository history" in maximum["history_validation"]


def test_review_ledger_accepts_32_to_33_chain_growth_under_byte_bound(tmp_path: Path) -> None:
    commits = [f"{30_000 + index:040x}" for index in range(34)]
    subtrees = [f"{40_000 + index:040x}" for index in range(34)]
    manifest = _manifest()
    manifest["sources"][0].update(commit=commits[-1], subtree_sha=subtrees[-1])
    ledger = _ledger()
    ledger["sources"][0]["genesis"] = {
        "commit": commits[0],
        "subtree_sha": subtrees[0],
    }
    ledger["sources"][0]["transitions"] = [
        {
            "prior": {"commit": commits[index], "subtree_sha": subtrees[index]},
            "new": {
                "commit": commits[index + 1],
                "subtree_sha": subtrees[index + 1],
            },
            "inventory_sha256": f"{50_000 + index:064x}",
            "dispositions": [],
        }
        for index in range(33)
    ]
    _write_manifest(tmp_path, manifest)
    _write_ledger(tmp_path, ledger)

    parsed_manifest = load_upstream_manifest(tmp_path)
    parsed_ledger = upstreams.load_upstream_review_ledger(tmp_path, parsed_manifest)

    assert len(parsed_ledger.sources[0].transitions) == 33
    assert upstreams.MAX_REVIEW_TRANSITIONS == 512
    assert (
        len((tmp_path / "maintenance" / "upstream-reviews.json").read_bytes())
        < upstreams.MAX_REVIEW_LEDGER_BYTES
    )


def test_review_bounds_truthfully_cover_representative_weekly_horizon() -> None:
    empty = _ledger()
    empty_bytes = len(upstreams._canonical_json_bytes(empty))

    def transition_bytes(rationale: str) -> int:
        one = json.loads(json.dumps(empty))
        transition = _transition("f" * 64)
        for disposition in transition["dispositions"]:
            disposition["rationale"] = rationale
        one["sources"][0]["transitions"].append(transition)
        return len(upstreams._canonical_json_bytes(one)) - empty_bytes

    representative_bytes = transition_bytes("r" * 400)
    maximum_rationale_bytes = transition_bytes("r" * upstreams.MAX_RATIONALE_BYTES)
    representative_capacity = (
        upstreams.MAX_REVIEW_LEDGER_BYTES - empty_bytes
    ) // representative_bytes
    maximum_rationale_capacity = (
        upstreams.MAX_REVIEW_LEDGER_BYTES - empty_bytes
    ) // maximum_rationale_bytes

    assert upstreams.MAX_REVIEW_TRANSITIONS == 512
    assert representative_capacity >= upstreams.MAX_REVIEW_TRANSITIONS
    assert 9 * 52 <= upstreams.MAX_REVIEW_TRANSITIONS < 10 * 52
    assert 2 * 52 <= maximum_rationale_capacity < upstreams.MAX_REVIEW_TRANSITIONS
    assert upstreams.MAX_PROVENANCE_BYTES == 8 * 1024 * 1024
    assert upstreams.MAX_ACCEPT_TRANSACTION_BYTES >= (
        2 * upstreams.MAX_REVIEW_LEDGER_BYTES + 2 * upstreams.MAX_MANIFEST_BYTES
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update(extra=True),
        lambda value: value.update(schema_version=True),
        lambda value: value.update(sources=[]),
        lambda value: value["sources"][0].update(extra=True),
        lambda value: value["sources"][0].update(repository="https://github.com/cursor/plugins"),
        lambda value: value["sources"][0].update(path="../pstack"),
        lambda value: value["sources"][0].update(ref="main..evil"),
        lambda value: value["sources"][0].update(commit=PIN.upper()),
        lambda value: value["sources"][0].update(provenance_path="README.txt"),
    ],
)
def test_manifest_schema_is_strict(tmp_path: Path, mutate: Any) -> None:
    document = _manifest()
    mutate(document)
    _write_manifest(tmp_path, document)

    with pytest.raises(UpstreamError):
        load_upstream_manifest(tmp_path)


def test_manifest_rejects_duplicate_keys_ids_and_symlinked_provenance(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    path = tmp_path / "maintenance" / "upstreams.json"
    path.write_text('{"schema_version":1,"schema_version":1,"sources":[]}', encoding="utf-8")
    with pytest.raises(UpstreamError, match="duplicate key"):
        load_upstream_manifest(tmp_path)

    document = _manifest()
    document["sources"].append(dict(document["sources"][0]))
    _write_manifest(tmp_path, document)
    with pytest.raises(UpstreamError, match="ids must be unique"):
        load_upstream_manifest(tmp_path)

    outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    provenance = tmp_path / "powers" / "pkstack" / "docs" / "provenance.md"
    provenance.unlink()
    provenance.symlink_to(outside)
    _write_manifest(tmp_path)
    provenance.unlink()
    provenance.symlink_to(outside)
    with pytest.raises(UpstreamError):
        load_upstream_manifest(tmp_path)


@pytest.mark.parametrize("timeout", [0, -1, 31, float("inf"), float("nan"), True, "1"])
def test_timeout_is_finite_numeric_and_bounded(tmp_path: Path, timeout: Any) -> None:
    _write_manifest(tmp_path)
    with pytest.raises(UpstreamError, match="timeout"):
        check_upstreams(tmp_path, timeout_seconds=timeout, fetch_json=FakeFetch(), environ={})


def test_timeout_is_one_aggregate_network_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_manifest(tmp_path)
    ticks = iter((0.0, 2.0))
    monkeypatch.setattr(upstreams.time, "monotonic", lambda: next(ticks))

    with pytest.raises(UpstreamError, match="budget was exhausted"):
        check_upstreams(tmp_path, timeout_seconds=1, fetch_json=FakeFetch(), environ={})


def test_explicit_power_root_runs_ownership_aware_dry_run_without_writes(tmp_path: Path) -> None:
    bootstrap_project(tmp_path, power_root=POWER_ROOT)
    _write_manifest(tmp_path)
    before = {
        path.relative_to(tmp_path).as_posix(): (path.read_bytes(), path.stat().st_mode)
        for path in tmp_path.rglob("*")
        if path.is_file() and not path.is_symlink()
    }

    payload = check_upstreams(
        tmp_path,
        power_root=POWER_ROOT,
        fetch_json=FakeFetch(),
        environ={},
    )

    after = {
        path.relative_to(tmp_path).as_posix(): (path.read_bytes(), path.stat().st_mode)
        for path in tmp_path.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    assert before == after
    assert payload["bootstrap_preview"]["dry_run"] is True
    assert payload["bootstrap_preview"]["update_managed"] is True
    assert payload["generated_parity"] == {
        "ok": True,
        "dry_run": True,
        "update_managed": True,
        "differences": {},
    }


def test_accept_dry_run_then_atomic_accept_leaves_no_ephemeral_residue(tmp_path: Path) -> None:
    canonical_power = _prepare_accept_root(tmp_path)
    responses = _fake_responses()
    baseline = check_upstreams(
        tmp_path,
        power_root=canonical_power,
        fetch_json=FakeFetch(responses),
        environ={},
    )
    transition = _transition(baseline["sources"][0]["comparison"]["inventory_sha256"])
    proposal_path = _write_proposal(tmp_path, transition)
    manifest_before = (tmp_path / "maintenance" / "upstreams.json").read_bytes()
    ledger_before = (tmp_path / "maintenance" / "upstream-reviews.json").read_bytes()

    preview = upstreams.accept_upstream(
        tmp_path,
        expected_head=HEAD,
        power_root=Path("powers/pkstack"),
        dry_run=True,
        fetch_json=FakeFetch(responses),
        environ={},
    )

    assert preview["ok"] is True
    assert preview["accepted"] is False
    assert proposal_path.is_file()
    assert (tmp_path / "maintenance" / "upstreams.json").read_bytes() == manifest_before
    assert (tmp_path / "maintenance" / "upstream-reviews.json").read_bytes() == ledger_before

    accepted = upstreams.accept_upstream(
        tmp_path,
        expected_head=HEAD,
        power_root=canonical_power,
        fetch_json=FakeFetch(responses),
        environ={},
    )
    assert accepted["ok"] is accepted["accepted"] is True
    assert not (tmp_path / ".pkstack-maintenance").exists()
    manifest = json.loads((tmp_path / "maintenance" / "upstreams.json").read_text(encoding="utf-8"))
    ledger = json.loads(
        (tmp_path / "maintenance" / "upstream-reviews.json").read_text(encoding="utf-8")
    )
    assert manifest["sources"][0]["commit"] == HEAD
    assert manifest["sources"][0]["subtree_sha"] == HEAD_TREE
    assert ledger["sources"][0]["transitions"] == [transition]
    assert _provenance_marker_lines(tmp_path) == [
        _marker_line("genesis", _genesis_marker()),
        _marker_line("review", _provenance_marker(transition)),
    ]

    final = check_upstreams(
        tmp_path,
        power_root=canonical_power,
        fetch_json=FakeFetch(responses),
        environ={},
    )
    assert final["ok"] is True
    assert len(json.dumps(final, sort_keys=True).encode("utf-8")) <= 32 * 1024

    parity_path = tmp_path / "powers" / "pkstack" / "docs" / "upstream-skill-parity.json"
    parity_before = parity_path.read_bytes()
    parity = json.loads(parity_before)
    parity["source"]["pinned"] = {"commit": HEAD, "pstack_subtree_sha": HEAD_TREE}
    for entry in parity["skills"]:
        entry["pinned"] = copy.deepcopy(entry["current"])
    parity_path.write_text(json.dumps(parity), encoding="utf-8")
    collapsed_history = check_upstreams(
        tmp_path,
        power_root=canonical_power,
        fetch_json=FakeFetch(responses),
        environ={},
    )
    source_parity = collapsed_history["sources"][0]["source_parity"]
    assert source_parity["ok"] is False
    assert source_parity["candidate_ready"] is False
    assert "does not match review history" in source_parity["errors"][0]
    parity_path.write_bytes(parity_before)

    _write_proposal(tmp_path, transition, bind_provenance=False)
    with pytest.raises(UpstreamError, match="stale or already applied"):
        upstreams.accept_upstream(
            tmp_path,
            expected_head=HEAD,
            power_root=Path("powers/pkstack"),
            fetch_json=FakeFetch(responses),
            environ={},
        )


@pytest.mark.parametrize("artifact_type", ["skill-catalog", "source-inventory"])
def test_multisource_accept_serializes_one_source_without_mutating_the_other(
    tmp_path: Path,
    artifact_type: str,
) -> None:
    canonical_power = _prepare_accept_root(tmp_path)
    paths = _add_parallel_source(tmp_path)
    responses = _fake_responses()
    parity: dict[str, Any] = json.loads(paths["parity"].read_text(encoding="utf-8"))
    if artifact_type == "source-inventory":
        identities = {}
        for revision, tree in (("pinned", PIN_TREE), ("current", HEAD_TREE)):
            entries = responses[
                upstreams._api_url(
                    "cursor/plugins", "git", "trees", tree, query=(("recursive", "1"),)
                )
            ]["tree"]
            identities[revision] = {
                item["path"]: {
                    "type": item["type"],
                    "mode": item["mode"],
                    "object_sha": item["sha"],
                    "size": item["size"],
                }
                for item in entries
                if item["type"] == "blob"
            }
        source = parity["source"]
        del source["catalog_path"]
        for revision in ("pinned", "current"):
            source[revision]["subtree_sha"] = source[revision].pop("pstack_subtree_sha")
        parity = {
            "schema_version": 1,
            "artifact_type": artifact_type,
            "source": source,
            "allowed_dispositions": ["A", "B", "C"],
            "summary": {
                "A": 0,
                "B": len(CHANGED_PATHS),
                "C": 0,
                "pinned_files": len(identities["pinned"]),
                "current_files": len(identities["current"]),
            },
            "files": [
                {
                    "path": path,
                    "pinned": identities["pinned"].get(path),
                    "current": identities["current"].get(path),
                    "disposition": "B",
                    "rationale": "Preserve the bounded synthetic exclusion.",
                }
                for path in sorted(CHANGED_PATHS, key=str.casefold)
            ],
        }
        paths["parity"].write_text(json.dumps(parity), encoding="utf-8")
    baseline = check_upstreams(
        tmp_path,
        power_root=canonical_power,
        fetch_json=FakeFetch(responses),
        environ={},
    )
    assert sorted(source["id"] for source in baseline["sources"] if source["drift"]) == [
        "alpha-source",
        "cursor-pstack",
    ]
    selected = next(source for source in baseline["sources"] if source["id"] == "alpha-source")
    assert parity["source"]["retrieved_on"] == "2026-09-02"
    parity["source"]["retrieved_on"] = "2026-09-05"
    paths["parity"].write_text(json.dumps(parity), encoding="utf-8")
    transition = _transition(selected["comparison"]["inventory_sha256"])
    proposal = {"source_id": "alpha-source", **transition}
    proposal_path = tmp_path / ".pkstack-maintenance" / "proposal.json"
    proposal_path.parent.mkdir(parents=True)
    proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
    _append_source_review_marker(
        paths["provenance"],
        source_id="alpha-source",
        transition=transition,
    )

    manifest_path = tmp_path / "maintenance" / "upstreams.json"
    ledger_path = tmp_path / "maintenance" / "upstream-reviews.json"
    before_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    before_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    other_manifest = copy.deepcopy(before_manifest["sources"][0])
    other_review = copy.deepcopy(before_ledger["sources"][0])
    other_provenance = (tmp_path / other_manifest["provenance_path"]).read_bytes()
    other_parity = (tmp_path / other_manifest["parity_path"]).read_bytes()

    accepted = upstreams.accept_upstream(
        tmp_path,
        expected_head=HEAD,
        power_root=canonical_power,
        fetch_json=FakeFetch(responses),
        environ={},
    )

    assert accepted["ok"] is accepted["accepted"] is True
    assert accepted["source_id"] == "alpha-source"
    after_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    after_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert after_manifest["sources"][0] == other_manifest
    assert after_ledger["sources"][0] == other_review
    assert (tmp_path / other_manifest["provenance_path"]).read_bytes() == other_provenance
    assert (tmp_path / other_manifest["parity_path"]).read_bytes() == other_parity
    assert json.loads(paths["parity"].read_text())["source"]["retrieved_on"] == "2026-09-05"
    advanced = next(
        source for source in after_manifest["sources"] if source["id"] == "alpha-source"
    )
    assert {"commit": advanced["commit"], "subtree_sha": advanced["subtree_sha"]} == {
        "commit": HEAD,
        "subtree_sha": HEAD_TREE,
    }
    advanced_review = next(
        source for source in after_ledger["sources"] if source["id"] == "alpha-source"
    )
    assert advanced_review["transitions"] == [transition]

    selected_final = check_upstreams(
        tmp_path,
        power_root=canonical_power,
        source_id="alpha-source",
        fetch_json=FakeFetch(responses),
        environ={},
    )
    assert selected_final["ok"] is True
    full_final = check_upstreams(
        tmp_path,
        power_root=canonical_power,
        fetch_json=FakeFetch(responses),
        environ={},
    )
    assert full_final["ok"] is False
    remaining = next(source for source in full_final["sources"] if source["id"] == "cursor-pstack")
    assert remaining["drift"] is True


def test_second_transition_accepts_one_proposal_bound_marker_tail(tmp_path: Path) -> None:
    canonical_power = _prepare_accept_root(tmp_path)
    first_responses = _fake_responses()
    first_proof = check_upstreams(
        tmp_path,
        power_root=canonical_power,
        fetch_json=FakeFetch(first_responses),
        environ={},
    )
    first = _transition(first_proof["sources"][0]["comparison"]["inventory_sha256"])
    _write_proposal(tmp_path, first)
    upstreams.accept_upstream(
        tmp_path,
        expected_head=HEAD,
        power_root=Path("powers/pkstack"),
        fetch_json=FakeFetch(first_responses),
        environ={},
    )

    future_responses = _future_ref_responses(content_change=True)
    second_proof = check_upstreams(
        tmp_path,
        power_root=canonical_power,
        fetch_json=FakeFetch(future_responses),
        environ={},
    )
    assert second_proof["sources"][0]["source_parity"]["candidate_ready"] is False
    second = _future_transition(second_proof["sources"][0]["comparison"]["inventory_sha256"])
    proposal = _write_proposal(tmp_path, second)
    ledger_path = tmp_path / "maintenance" / "upstream-reviews.json"
    ledger_before = ledger_path.read_bytes()

    with pytest.raises(UpstreamError, match="provenance review markers"):
        check_upstreams(
            tmp_path,
            power_root=canonical_power,
            fetch_json=FakeFetch(future_responses),
            environ={},
        )

    parity_path = tmp_path / "powers" / "pkstack" / "docs" / "upstream-skill-parity.json"
    parity = json.loads(parity_path.read_text(encoding="utf-8"))
    parity["source"]["pinned"] = {"commit": HEAD, "pstack_subtree_sha": HEAD_TREE}
    parity["source"]["current"] = {"commit": FUTURE, "pstack_subtree_sha": FUTURE_TREE}
    for entry in parity["skills"]:
        entry["pinned"] = copy.deepcopy(entry["current"])
    parity_path.write_text(json.dumps(parity), encoding="utf-8")

    preview = upstreams.accept_upstream(
        tmp_path,
        expected_head=FUTURE,
        power_root=Path("powers/pkstack"),
        dry_run=True,
        fetch_json=FakeFetch(future_responses),
        environ={},
    )
    assert preview["ok"] is True
    assert preview["accepted"] is False
    assert proposal.is_file()
    assert ledger_path.read_bytes() == ledger_before

    accepted = upstreams.accept_upstream(
        tmp_path,
        expected_head=FUTURE,
        power_root=Path("powers/pkstack"),
        fetch_json=FakeFetch(future_responses),
        environ={},
    )
    assert accepted["ok"] is accepted["accepted"] is True
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["sources"][0]["transitions"] == [first, second]
    assert not (tmp_path / ".pkstack-maintenance").exists()
    assert _provenance_marker_lines(tmp_path) == [
        _marker_line("genesis", _genesis_marker()),
        _marker_line("review", _provenance_marker(first)),
        _marker_line("review", _provenance_marker(second)),
    ]

    final = check_upstreams(
        tmp_path,
        power_root=canonical_power,
        fetch_json=FakeFetch(future_responses),
        environ={},
    )
    assert final["ok"] is True
    assert final["sources"][0]["review_reproof"]["transition_count"] == 2


@pytest.mark.parametrize("marker_shape", ["extra", "replaced", "reordered"])
def test_second_transition_accept_rejects_any_noncanonical_marker_tail(
    tmp_path: Path,
    marker_shape: str,
) -> None:
    canonical_power = _prepare_accept_root(tmp_path)
    first_responses = _fake_responses()
    first_proof = check_upstreams(
        tmp_path,
        fetch_json=FakeFetch(first_responses),
        environ={},
    )
    first = _transition(first_proof["sources"][0]["comparison"]["inventory_sha256"])
    _advance_review(tmp_path, first["inventory_sha256"])
    future_responses = _future_ref_responses(content_change=True)
    second_proof = check_upstreams(
        tmp_path,
        fetch_json=FakeFetch(future_responses),
        environ={},
    )
    second = _future_transition(second_proof["sources"][0]["comparison"]["inventory_sha256"])
    _write_proposal(tmp_path, second, bind_provenance=False)
    shapes = {
        "extra": [first, second, second],
        "replaced": [second],
        "reordered": [second, first],
    }
    _rewrite_provenance_markers(tmp_path, shapes[marker_shape])

    with pytest.raises(UpstreamError, match="provenance review markers"):
        upstreams.accept_upstream(
            tmp_path,
            expected_head=FUTURE,
            power_root=canonical_power,
            dry_run=True,
            fetch_json=FakeFetch(future_responses),
            environ={},
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value["prior"].update(commit="a" * 40), "prior identity is stale"),
        (lambda value: value["new"].update(commit="c" * 40), "expected head"),
        (lambda value: value["new"].update(subtree_sha="c" * 40), "current subtree"),
        (lambda value: value.update(inventory_sha256="c" * 64), "digest"),
        (lambda value: value["dispositions"].pop(), "exactly match"),
    ],
)
def test_accept_rejects_stale_future_or_tampered_proposal(
    tmp_path: Path,
    mutate: Any,
    message: str,
) -> None:
    _prepare_accept_root(tmp_path)
    responses = _fake_responses()
    baseline = check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})
    transition = _transition(baseline["sources"][0]["comparison"]["inventory_sha256"])
    mutate(transition)
    _write_proposal(tmp_path, transition)

    with pytest.raises(UpstreamError, match=message):
        upstreams.accept_upstream(
            tmp_path,
            expected_head=HEAD,
            power_root=Path("powers/pkstack"),
            fetch_json=FakeFetch(responses),
            environ={},
        )

    assert _manifest() == json.loads(
        (tmp_path / "maintenance" / "upstreams.json").read_text(encoding="utf-8")
    )
    assert _ledger() == json.loads(
        (tmp_path / "maintenance" / "upstream-reviews.json").read_text(encoding="utf-8")
    )


def test_accept_rejects_otherwise_valid_proposal_with_stale_provenance(tmp_path: Path) -> None:
    _prepare_accept_root(tmp_path)
    responses = _fake_responses()
    baseline = check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})
    transition = _transition(baseline["sources"][0]["comparison"]["inventory_sha256"])
    _write_proposal(tmp_path, transition, bind_provenance=False)

    with pytest.raises(UpstreamError, match="provenance review markers"):
        upstreams.accept_upstream(
            tmp_path,
            expected_head=HEAD,
            power_root=Path("powers/pkstack"),
            fetch_json=FakeFetch(responses),
            environ={},
        )

    assert _manifest() == json.loads(
        (tmp_path / "maintenance" / "upstreams.json").read_text(encoding="utf-8")
    )
    assert _ledger() == json.loads(
        (tmp_path / "maintenance" / "upstream-reviews.json").read_text(encoding="utf-8")
    )


def test_accept_requires_disposition_b_for_unavailable_logo_patch(tmp_path: Path) -> None:
    _prepare_accept_root(tmp_path)
    responses = _fake_responses()
    baseline = check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})
    transition = _transition(baseline["sources"][0]["comparison"]["inventory_sha256"])
    logo = next(item for item in transition["dispositions"] if item["path"] == "assets/logo.png")
    assert logo["disposition"] == "B"
    logo["disposition"] = "A"
    _write_proposal(tmp_path, transition)

    with pytest.raises(UpstreamError, match=r"disposition B.*assets/logo\.png"):
        upstreams.accept_upstream(
            tmp_path,
            expected_head=HEAD,
            power_root=Path("powers/pkstack"),
            fetch_json=FakeFetch(responses),
            environ={},
        )


def test_accept_rejects_wrong_expected_head_and_unsafe_proposal_path(tmp_path: Path) -> None:
    _prepare_accept_root(tmp_path)
    _write_proposal(tmp_path, _transition("f" * 64))

    with pytest.raises(UpstreamError, match="expected_head"):
        upstreams.accept_upstream(
            tmp_path,
            expected_head="not-a-sha",
            power_root=Path("powers/pkstack"),
            fetch_json=FakeFetch(),
            environ={},
        )
    with pytest.raises(UpstreamError, match="current upstream head"):
        upstreams.accept_upstream(
            tmp_path,
            expected_head=PIN,
            power_root=Path("powers/pkstack"),
            fetch_json=FakeFetch(),
            environ={},
        )
    with pytest.raises(UpstreamError, match="requires --proposal"):
        upstreams.accept_upstream(
            tmp_path,
            expected_head=HEAD,
            power_root=Path("powers/pkstack"),
            proposal=Path("other.json"),
            fetch_json=FakeFetch(),
            environ={},
        )
    for unsafe_power in (
        Path("powers/other"),
        Path("powers/../powers/pkstack"),
        Path("../outside-power"),
    ):
        with pytest.raises(UpstreamError):
            upstreams.accept_upstream(
                tmp_path,
                expected_head=HEAD,
                power_root=unsafe_power,
                fetch_json=FakeFetch(),
                environ={},
            )

    proposal = tmp_path / ".pkstack-maintenance" / "proposal.json"
    extra = proposal.parent / "unexpected.txt"
    extra.write_text("not trusted", encoding="utf-8")
    with pytest.raises(UpstreamError, match="may contain only"):
        upstreams.accept_upstream(
            tmp_path,
            expected_head=HEAD,
            power_root=Path("powers/pkstack"),
            fetch_json=FakeFetch(),
            environ={},
        )
    extra.unlink()
    proposal.unlink()
    outside = tmp_path.parent / f"{tmp_path.name}-proposal.json"
    outside.write_text("{}", encoding="utf-8")
    proposal.symlink_to(outside)
    with pytest.raises(UpstreamError, match="symlink"):
        upstreams.accept_upstream(
            tmp_path,
            expected_head=HEAD,
            power_root=Path("powers/pkstack"),
            fetch_json=FakeFetch(),
            environ={},
        )


def test_accept_rejects_symlinked_canonical_power_root(tmp_path: Path) -> None:
    _prepare_accept_root(tmp_path)
    baseline = check_upstreams(tmp_path, fetch_json=FakeFetch(), environ={})
    _write_proposal(
        tmp_path,
        _transition(baseline["sources"][0]["comparison"]["inventory_sha256"]),
    )
    canonical = tmp_path / "powers" / "pkstack"
    actual = tmp_path / "powers" / "reviewed-power"
    canonical.rename(actual)
    canonical.symlink_to(actual, target_is_directory=True)

    with pytest.raises(UpstreamError, match="symlink"):
        upstreams.accept_upstream(
            tmp_path,
            expected_head=HEAD,
            power_root=Path("powers/pkstack"),
            fetch_json=FakeFetch(),
            environ={},
        )


def test_upstream_accept_lock_serializes_two_processes(tmp_path: Path) -> None:
    context = multiprocessing.get_context("fork")
    first_entered = context.Event()
    first_release = context.Event()
    second_entered = context.Event()
    second_release = context.Event()
    first = context.Process(
        target=_hold_accept_lock,
        args=(str(tmp_path), first_entered, first_release),
    )
    second = context.Process(
        target=_hold_accept_lock,
        args=(str(tmp_path), second_entered, second_release),
    )
    first.start()
    assert first_entered.wait(2)
    second.start()
    assert not second_entered.wait(0.2)
    first_release.set()
    assert second_entered.wait(2)
    second_release.set()
    first.join(2)
    second.join(2)
    assert first.exitcode == second.exitcode == 0
    assert (tmp_path / ".pkstack" / "state" / "upstream-accept.lock").is_file()
    assert not (tmp_path / ".pkstack-maintenance").exists()


def test_upstream_accept_lock_rejects_symlink_swapped_after_path_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "outside-lock-target"
    target.write_text("unchanged", encoding="utf-8")
    lock_path = tmp_path / ".pkstack" / "state" / "upstream-accept.lock"
    original_open = upstreams.os.open
    raced = False

    def racing_open(
        path: str | bytes | Path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal raced
        if path == "upstream-accept.lock" and dir_fd is not None and not raced:
            raced = True
            lock_path.symlink_to(target)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(upstreams.os, "open", racing_open)
    with (
        pytest.raises(UpstreamError, match="safe upstream acceptance lock"),
        upstreams._accept_locked(tmp_path),
    ):
        raise AssertionError("raced symlink must not be locked")

    assert raced is True
    assert lock_path.is_symlink()
    assert target.read_text(encoding="utf-8") == "unchanged"


def test_accept_recovers_completed_journal_without_remaining_proposal(tmp_path: Path) -> None:
    _prepare_accept_root(tmp_path)
    responses = _fake_responses()
    baseline = check_upstreams(tmp_path, fetch_json=FakeFetch(responses), environ={})
    transition = _transition(baseline["sources"][0]["comparison"]["inventory_sha256"])
    _write_provenance_marker(tmp_path, transition)
    manifest_path = tmp_path / "maintenance" / "upstreams.json"
    ledger_path = tmp_path / "maintenance" / "upstream-reviews.json"
    before_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    before_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    after_manifest = json.loads(json.dumps(before_manifest))
    after_manifest["sources"][0].update(commit=HEAD, subtree_sha=HEAD_TREE)
    after_ledger = json.loads(json.dumps(before_ledger))
    after_ledger["sources"][0]["transitions"].append(transition)
    (tmp_path / ".pkstack-maintenance").mkdir()
    upstreams._write_accept_transaction(
        tmp_path,
        manifest_path=manifest_path,
        ledger_path=ledger_path,
        before_manifest=before_manifest,
        before_ledger=before_ledger,
        after_manifest=after_manifest,
        after_ledger=after_ledger,
        source_id="cursor-pstack",
        expected_head=HEAD,
    )
    assert (tmp_path / ".pkstack-maintenance" / "accept-transaction.json").is_file()

    result = upstreams.accept_upstream(
        tmp_path,
        expected_head=HEAD,
        power_root=Path("powers/pkstack"),
        fetch_json=FakeFetch(responses),
        environ={},
    )

    assert result["ok"] is result["accepted"] is result["recovered"] is True
    assert not (tmp_path / ".pkstack-maintenance").exists()
    assert _provenance_marker_lines(tmp_path) == [
        _marker_line("genesis", _genesis_marker()),
        _marker_line("review", _provenance_marker(transition)),
    ]


def test_near_limit_ledgers_fit_bounded_accept_journal_and_recover(tmp_path: Path) -> None:
    commits = [f"{70_000 + index:040x}" for index in range(upstreams.MAX_REVIEW_TRANSITIONS + 1)]
    subtrees = [f"{80_000 + index:040x}" for index in range(upstreams.MAX_REVIEW_TRANSITIONS + 1)]
    transitions: list[dict[str, Any]] = []
    for index in range(upstreams.MAX_REVIEW_TRANSITIONS):
        rationale = f"Reviewed path {index}: " + "r" * 1880
        transition = {
            "prior": {"commit": commits[index], "subtree_sha": subtrees[index]},
            "new": {"commit": commits[index + 1], "subtree_sha": subtrees[index + 1]},
            "inventory_sha256": f"{90_000 + index:064x}",
            "dispositions": [
                {
                    "path": path,
                    "disposition": "B" if path == "assets/logo.png" else "A",
                    "rationale": rationale,
                }
                for path in CHANGED_PATHS
            ],
        }
        candidate = _ledger()
        candidate["sources"][0]["genesis"] = {
            "commit": commits[0],
            "subtree_sha": subtrees[0],
        }
        candidate["sources"][0]["transitions"] = [*transitions, transition]
        if len(upstreams._canonical_json_bytes(candidate)) >= (
            upstreams.MAX_REVIEW_LEDGER_BYTES - 64 * 1024
        ):
            break
        transitions.append(transition)

    assert 100 < len(transitions) < upstreams.MAX_REVIEW_TRANSITIONS
    after_ledger = _ledger()
    after_ledger["sources"][0]["genesis"] = {
        "commit": commits[0],
        "subtree_sha": subtrees[0],
    }
    after_ledger["sources"][0]["transitions"] = transitions
    before_ledger = json.loads(json.dumps(after_ledger))
    before_ledger["sources"][0]["transitions"].pop()
    before_manifest = _manifest()
    before_manifest["sources"][0].update(
        commit=transitions[-1]["prior"]["commit"],
        subtree_sha=transitions[-1]["prior"]["subtree_sha"],
    )
    after_manifest = json.loads(json.dumps(before_manifest))
    after_manifest["sources"][0].update(
        commit=transitions[-1]["new"]["commit"],
        subtree_sha=transitions[-1]["new"]["subtree_sha"],
    )
    _write_manifest(tmp_path, before_manifest)
    _write_ledger(tmp_path, before_ledger)
    (tmp_path / ".pkstack-maintenance").mkdir()
    manifest_path = tmp_path / "maintenance" / "upstreams.json"
    ledger_path = tmp_path / "maintenance" / "upstream-reviews.json"

    upstreams._write_accept_transaction(
        tmp_path,
        manifest_path=manifest_path,
        ledger_path=ledger_path,
        before_manifest=before_manifest,
        before_ledger=before_ledger,
        after_manifest=after_manifest,
        after_ledger=after_ledger,
        source_id="cursor-pstack",
        expected_head=after_manifest["sources"][0]["commit"],
    )

    journal = tmp_path / ".pkstack-maintenance" / "accept-transaction.json"
    assert len(upstreams._canonical_json_bytes(after_ledger)) > 7 * 1024 * 1024
    assert journal.stat().st_size <= upstreams.MAX_ACCEPT_TRANSACTION_BYTES
    assert upstreams._recover_accept_transaction(
        tmp_path,
        expected_head=after_manifest["sources"][0]["commit"],
    )
    assert json.loads(ledger_path.read_text(encoding="utf-8")) == after_ledger


def test_accept_recovery_preserves_committed_transition_when_ref_advances(tmp_path: Path) -> None:
    _prepare_accept_root(tmp_path)
    baseline = check_upstreams(tmp_path, fetch_json=FakeFetch(), environ={})
    transition = _transition(baseline["sources"][0]["comparison"]["inventory_sha256"])
    _write_provenance_marker(tmp_path, transition)
    manifest_path = tmp_path / "maintenance" / "upstreams.json"
    ledger_path = tmp_path / "maintenance" / "upstream-reviews.json"
    before_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    before_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    after_manifest = json.loads(json.dumps(before_manifest))
    after_manifest["sources"][0].update(commit=HEAD, subtree_sha=HEAD_TREE)
    after_ledger = json.loads(json.dumps(before_ledger))
    after_ledger["sources"][0]["transitions"].append(transition)
    (tmp_path / ".pkstack-maintenance").mkdir()
    upstreams._write_accept_transaction(
        tmp_path,
        manifest_path=manifest_path,
        ledger_path=ledger_path,
        before_manifest=before_manifest,
        before_ledger=before_ledger,
        after_manifest=after_manifest,
        after_ledger=after_ledger,
        source_id="cursor-pstack",
        expected_head=HEAD,
    )

    result = upstreams.accept_upstream(
        tmp_path,
        expected_head=HEAD,
        power_root=Path("powers/pkstack"),
        fetch_json=FakeFetch(_future_ref_responses()),
        environ={},
    )

    assert result["ok"] is result["accepted"] is result["recovered"] is True
    assert result["final"]["ok"] is True
    source = result["final"]["sources"][0]
    assert source["pinned"] == {"commit": HEAD, "subtree_sha": HEAD_TREE}
    assert source["pinned_reproof"]["ok"] is True
    assert source["review_reproof"]["ok"] is True
    assert source["drift"] is False
    assert source["current"] == {"commit": FUTURE, "subtree_sha": HEAD_TREE}
    assert source["comparison"]["fast_forward"] is True
    assert source["comparison"]["base_commit"] == HEAD
    assert source["comparison"]["head_commit"] == FUTURE
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == after_manifest
    assert json.loads(ledger_path.read_text(encoding="utf-8")) == after_ledger
    assert not (tmp_path / ".pkstack-maintenance").exists()


def test_direct_cli_maps_drift_and_errors_to_structured_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli, "check_upstreams", lambda *args, **kwargs: {"ok": False, "drift": True}
    )
    with pytest.raises(SystemExit, match="1"):
        cli.upstream_check_command(output="json")
    assert json.loads(capsys.readouterr().out) == {"drift": True, "ok": False}

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise UpstreamError("bad boundary")

    monkeypatch.setattr(cli, "check_upstreams", fail)
    with pytest.raises(SystemExit, match="2"):
        cli.upstream_check_command(output="json")
    error = json.loads(capsys.readouterr().out)
    assert error["ok"] is False
    assert error["error_type"] == "UpstreamError"


def test_cyclopts_routes_upstream_check_with_explicit_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, Any] = {}

    def check(*args: Any, **kwargs: Any) -> dict[str, Any]:
        captured.update(args=args, kwargs=kwargs)
        return {"ok": True, "source_count": 1}

    monkeypatch.setattr(cli, "check_upstreams", check)
    with pytest.raises(SystemExit, match="0"):
        cli.main(
            [
                "upstream",
                "check",
                "--manifest",
                "maintenance/custom.json",
                "--power-root",
                "powers/pkstack",
                "--source-id",
                "okf-skills",
                "--root",
                ".",
                "--timeout-seconds",
                "4",
                "--output",
                "json",
            ]
        )

    assert json.loads(capsys.readouterr().out) == {"ok": True, "source_count": 1}
    assert captured["kwargs"] == {
        "manifest": Path("maintenance/custom.json"),
        "power_root": Path("powers/pkstack"),
        "source_id": "okf-skills",
        "timeout_seconds": 4.0,
    }


def test_cyclopts_routes_expected_head_bound_upstream_accept(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, Any] = {}

    def accept(*args: Any, **kwargs: Any) -> dict[str, Any]:
        captured.update(args=args, kwargs=kwargs)
        return {"ok": True, "accepted": False, "dry_run": True}

    monkeypatch.setattr(cli, "accept_upstream", accept)
    with pytest.raises(SystemExit, match="0"):
        cli.main(
            [
                "upstream",
                "accept",
                "--manifest",
                "maintenance/upstreams.json",
                "--power-root",
                "powers/pkstack",
                "--proposal",
                ".pkstack-maintenance/proposal.json",
                "--expected-head",
                HEAD,
                "--dry-run",
                "--root",
                ".",
                "--timeout-seconds",
                "4",
                "--output",
                "json",
            ]
        )

    assert json.loads(capsys.readouterr().out) == {
        "accepted": False,
        "dry_run": True,
        "ok": True,
    }
    assert captured["kwargs"] == {
        "expected_head": HEAD,
        "manifest": Path("maintenance/upstreams.json"),
        "power_root": Path("powers/pkstack"),
        "proposal": Path(".pkstack-maintenance/proposal.json"),
        "dry_run": True,
        "timeout_seconds": 4.0,
    }


def _managed_command(root: Path) -> list[str]:
    return [
        ".pkstack/bin/projectctl",
        "upstream",
        "check",
        "--manifest",
        "maintenance/upstreams.json",
        "--power-root",
        "powers/pkstack",
        "--output",
        "json",
    ]


def test_runner_allows_only_the_exact_managed_upstream_predicate(tmp_path: Path) -> None:
    executable = tmp_path / ".pkstack" / "bin" / "projectctl"
    executable.parent.mkdir(parents=True)
    executable.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    executable.chmod(0o755)
    command = _managed_command(tmp_path)

    enforce_verification_policy(command, root=tmp_path)
    enforce_verification_policy(
        [*command, "--source-id", "google-okf-spec"],
        root=tmp_path,
    )

    rejected = [
        command[:-2],
        [*command[:-2], "--timeout-seconds", "10"],
        [*command[:-1], "text"],
        [*command, "--manifest", "maintenance/upstreams.json"],
        [*command, "--unknown", "x"],
        [*command[:4], "../outside.json", *command[5:]],
        [*command[:4], "maintenance/other.json", *command[5:]],
        [*command[:6], "powers/other", *command[7:]],
        [*command, "--timeout-seconds", "31"],
        [*command, "--source-id", "Google-OKF"],
        [*command, "--source-id", "google--okf"],
        [*command, "--source-id", "google-okf", "--source-id", "okf-skills"],
        ["projectctl", *command[1:]],
        [command[0], "version"],
    ]
    for unsafe in rejected:
        with pytest.raises(CommandRejected):
            enforce_verification_policy(unsafe, root=tmp_path)

    executable.unlink()
    executable.symlink_to("/bin/false")
    with pytest.raises(CommandRejected, match="missing or unsafe"):
        enforce_verification_policy(command, root=tmp_path)


class _Response:
    status = 200

    def __init__(self, raw: bytes, final_url: str) -> None:
        self.raw = raw
        self.final_url = final_url

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def geturl(self) -> str:
        return self.final_url

    def read(self, limit: int) -> bytes:
        del limit
        return self.raw


class _Opener:
    def __init__(self, response: _Response) -> None:
        self.response = response
        self.request: Any = None
        self.timeout: float | None = None

    def open(self, request: Any, timeout: float) -> _Response:
        self.request = request
        self.timeout = timeout
        return self.response


def test_http_boundary_uses_token_only_as_authorization_and_bounds_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = upstreams._api_url("cursor/plugins", "commits", PIN)
    opener = _Opener(_Response(b'{"sha":"value"}', url))
    monkeypatch.setattr(upstreams, "_build_opener", lambda: opener)

    assert upstreams._fetch_json(url, "secret", 4) == {"sha": "value"}
    assert opener.request.full_url == url
    assert opener.request.method == "GET"
    assert opener.request.get_header("Authorization") == "Bearer secret"
    assert "secret" not in opener.request.full_url
    assert opener.timeout == 4

    monkeypatch.setattr(
        upstreams,
        "_build_opener",
        lambda: _Opener(_Response(b"x" * (upstreams.MAX_RESPONSE_BYTES + 1), url)),
    )
    with pytest.raises(UpstreamError, match="exceeds"):
        upstreams._fetch_json(url, None, 4)

    monkeypatch.setattr(
        upstreams,
        "_build_opener",
        lambda: _Opener(_Response(b"{}", "https://example.com/escape")),
    )
    with pytest.raises(UpstreamError, match="restricted"):
        upstreams._fetch_json(url, None, 4)


@pytest.mark.parametrize(
    "raw",
    [b"\xff", b"{", b'{"x":1,"x":2}', b"NaN", b"Infinity"],
)
def test_json_boundary_rejects_invalid_utf8_json_and_duplicate_keys(raw: bytes) -> None:
    with pytest.raises(UpstreamError):
        upstreams._decode_json(raw, context="test response")
