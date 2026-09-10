from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from pkstack import cli
from pkstack.upstream_catalog import CATALOG_PATH, check_catalog, validate_catalog
from pkstack.upstreams import UpstreamError

POWER = Path(__file__).resolve().parents[1] / "powers/pkstack"
PIN = "3cca18b368ae95cdbdebbff572ccafa662551015"
TREE = "6e84c093fda2026396cea9fad6a924a6da0e1452"


@pytest.fixture
def power(tmp_path: Path) -> Path:
    target = tmp_path / "power"
    for name in ("metadata", "skills"):
        shutil.copytree(POWER / name, target / name, ignore=shutil.ignore_patterns("__pycache__"))
    return target


def edit_json(path: Path, mutate):
    data = json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data))


def test_catalog_accounts_for_all_pinned_entrypoints_and_methods_without_network():
    result = check_catalog(POWER, offline=True, fetch_json=lambda *_: pytest.fail("network call"))
    assert result["ok"]
    assert result["pinned"] == {"commit": PIN, "tree_sha": TREE}
    assert result["pinned_count"] == 37
    assert result["dispositions"] == {
        "imported": 14,
        "consolidated": 4,
        "covered": 6,
        "excluded": 13,
    }
    assert result["added"] == result["removed"] == result["missing_dispositions"] == []
    catalog = validate_catalog(POWER)
    entries = {entry["name"]: entry for entry in catalog["skills"]}
    assert entries["wayfinder"]["disposition"] == "imported"
    assert entries["wayfinder"]["destination"] == "skills/wayfinder/SKILL.md"
    assert entries["teach"]["destination"] == "skills/teach/SKILL.md"
    assert entries["tdd"]["destination"] == "skills/tdd/references/pocock-tdd/README.md"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data["skills"].pop(),
        lambda data: data["skills"].append(copy.deepcopy(data["skills"][0])),
        lambda data: data["skills"][0].update(disposition=None),
        lambda data: data["skills"][0].update(disposition={}),
        lambda data: data["skills"][0].update(rationale=""),
        lambda data: data["skills"][0].update(destination="/outside/file"),
    ],
)
def test_incomplete_or_malformed_dispositions_cannot_be_accepted(power: Path, mutation):
    edit_json(power / CATALOG_PATH, mutation)
    with pytest.raises(ValueError, match=r"catalog|path"):
        validate_catalog(power)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data.update(truncated=True),
        lambda data: data.update(sha="0" * 40),
        lambda data: data["tree"].pop(),
        lambda data: data["tree"].append(copy.deepcopy(data["tree"][0])),
    ],
)
def test_offline_snapshot_requires_original_complete_git_tree(power: Path, mutation):
    edit_json(power / "metadata/mattpocock-catalog-tree.json", mutation)
    with pytest.raises(UpstreamError, match=r"tree|snapshot"):
        validate_catalog(power)


@pytest.mark.parametrize("replacement", [None, [], {"source": []}, {"source": {"current": None}}])
def test_malformed_source_inventory_fails_closed(power: Path, replacement):
    (power / "metadata/mattpocock-code-review-source-parity.json").write_text(
        json.dumps(replacement)
    )
    with pytest.raises(ValueError, match="catalog"):
        validate_catalog(power)


def test_original_inventory_cannot_be_replaced_by_adapted_source_hash(power: Path):
    path = power / "metadata/mattpocock-code-review-source-parity.json"
    edit_json(path, lambda data: data["files"][0]["current"].update(object_sha="0" * 40))
    with pytest.raises(UpstreamError, match="original Git bytes"):
        validate_catalog(power)


def test_method_bytes_are_verified_even_without_a_duplicate_curated_skill(power: Path):
    target = power / "skills/architect/references/pocock-codebase-design/DEEPENING.md"
    target.write_text(target.read_text() + "\nUnreviewed guidance.\n")
    with pytest.raises(ValueError, match="hash or size mismatch"):
        validate_catalog(power)


def git_tree(tmp_path: Path, entries: list[dict[str, Any]]) -> str:
    repository = tmp_path / "tree-oracle"
    repository.mkdir()
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    records = b"".join(
        f"{item['mode']} {item['sha']}\t{item['path']}\0".encode()
        for item in entries
        if item["type"] != "tree"
    )
    subprocess.run(
        ["git", "update-index", "-z", "--index-info"], input=records, cwd=repository, check=True
    )
    return subprocess.check_output(
        ["git", "write-tree", "--missing-ok"], cwd=repository, text=True
    ).strip()


@pytest.mark.parametrize("change", ["content", "add", "remove"])
def test_source_revision_can_advance_without_rewriting_catalog(
    tmp_path: Path, power: Path, change: str
):
    parity = power / "metadata/mattpocock-codebase-design-source-parity.json"
    manifest = power / "metadata/mattpocock-codebase-design-bundle-manifest.json"
    inventory = json.loads(parity.read_text())
    bundle = json.loads(manifest.read_text())
    catalog_bytes = (power / CATALOG_PATH).read_bytes()
    snapshot_bytes = (power / "metadata/mattpocock-catalog-tree.json").read_bytes()
    source_path = inventory["source"]["path"]
    payload = b"An independently reviewed upstream source revision.\n"
    identity = {
        "type": "blob",
        "mode": "100644",
        "object_sha": hashlib.sha1(
            b"blob " + str(len(payload)).encode() + b"\0" + payload
        ).hexdigest(),
        "size": len(payload),
    }
    if change == "content":
        next(item for item in inventory["files"] if item["path"] == "SKILL.md")["current"] = (
            identity
        )
    elif change == "add":
        relative = "references/new-guide.md"
        inventory["files"].append(
            {
                "path": relative,
                "pinned": None,
                "current": identity,
                "disposition": "A",
                "rationale": "Adapt the newly added nested guide through source-bound review.",
            }
        )
        local = power / bundle["bundle_root"] / relative
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(payload)
        bundle["files"].append(
            {
                "path": relative,
                "source_path": f"{source_path}/{relative}",
                "mode": "100644",
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "handling": "adapted-kiro-wrapper",
            }
        )
    else:
        resource = next(item for item in inventory["files"] if item["path"] == "DEEPENING.md")
        resource.update(current=None, disposition="C", rationale="Remove the retired resource.")
        local = next(
            item for item in bundle["files"] if item["source_path"].endswith("/DEEPENING.md")
        )
        (power / bundle["bundle_root"] / local["path"]).unlink()
        bundle["files"].remove(local)
    inventory["files"].sort(key=lambda item: item["path"].casefold())
    current = [item for item in inventory["files"] if item["current"] is not None]
    tree = git_tree(
        tmp_path,
        [
            {
                "path": item["path"],
                "type": item["current"]["type"],
                "mode": item["current"]["mode"],
                "sha": item["current"]["object_sha"],
            }
            for item in current
        ],
    )
    inventory["source"]["current"] = {"commit": "f" * 40, "subtree_sha": tree}
    inventory["summary"] = {
        **{
            value: sum(item["disposition"] == value for item in inventory["files"])
            for value in ("A", "B", "C")
        },
        "pinned_files": sum(item["pinned"] is not None for item in inventory["files"]),
        "current_files": len(current),
    }
    bundle["files"].sort(key=lambda item: item["path"])
    bundle["summary"] = {
        "file_count": len(bundle["files"]),
        "byte_count": sum(item["size"] for item in bundle["files"]),
    }
    parity.write_text(json.dumps(inventory))
    manifest.write_text(json.dumps(bundle))
    assert check_catalog(power, offline=True)["ok"]
    assert (power / CATALOG_PATH).read_bytes() == catalog_bytes
    assert (power / "metadata/mattpocock-catalog-tree.json").read_bytes() == snapshot_bytes
    inventory["source"]["current"]["subtree_sha"] = "0" * 40
    parity.write_text(json.dumps(inventory))
    with pytest.raises(UpstreamError, match="original Git bytes"):
        validate_catalog(power)


def remote(tmp_path: Path):
    snapshot = json.loads((POWER / "metadata/mattpocock-catalog-tree.json").read_text())
    removed = "skills/engineering/research/SKILL.md"
    added = "skills/engineering/future-method/SKILL.md"
    entries = [entry for entry in snapshot["tree"] if entry["path"] != removed]
    original = next(entry for entry in snapshot["tree"] if entry["path"] == removed)
    entries.append({**original, "path": added})
    current_tree = git_tree(tmp_path, entries)
    current_commit = "f" * 40
    calls = []

    def fetch(url, token, timeout):
        calls.append((url, token, timeout))
        assert 0 < timeout <= 30
        assert token is None
        prefix = "https://api.github.com/repos/mattpocock/skills/"
        assert url.startswith(prefix)
        path = url.removeprefix(prefix)
        if path == "commits/" + PIN:
            return {"sha": PIN, "commit": {"tree": {"sha": TREE}}}
        if path == "commits/main":
            return {"sha": current_commit, "commit": {"tree": {"sha": current_tree}}}
        if path == f"git/trees/{current_tree}?recursive=1":
            return {"sha": current_tree, "truncated": False, "tree": entries}
        pytest.fail("unexpected request " + path)

    return fetch, calls, added, removed


def test_live_catalog_reports_additions_removals_and_missing_dispositions_without_mutation(
    tmp_path: Path, power: Path
):
    fetch, calls, added, removed = remote(tmp_path)
    original = (power / CATALOG_PATH).read_bytes()
    result = check_catalog(power, fetch_json=fetch, environ={})
    assert not result["ok"]
    assert result["added"] == result["missing_dispositions"] == [added]
    assert result["removed"] == [removed]
    assert result["current_count"] == 37
    assert len(calls) == 3
    assert (power / CATALOG_PATH).read_bytes() == original
    assert not (power / "skills/future-method").exists()


def test_live_snapshot_omission_fails_even_with_a_claimed_correct_sha(tmp_path: Path):
    fetch, _, _, _ = remote(tmp_path)

    def incomplete(url, token, timeout):
        data = fetch(url, token, timeout)
        if "/git/trees/" in url:
            data["tree"] = data["tree"][:-1]
        return data

    with pytest.raises(UpstreamError, match="identity is incomplete"):
        check_catalog(POWER, fetch_json=incomplete, environ={})


def test_catalog_cli_exposes_structured_read_only_report(capsys):
    with pytest.raises(SystemExit) as status:
        cli.main(
            ["upstream", "catalog", "--power-root", str(POWER), "--offline", "--output", "json"]
        )
    assert status.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] and payload["mode"] == "offline"
    assert payload["pinned_count"] == 37
