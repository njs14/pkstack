from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

POWER = Path(__file__).resolve().parents[1]
RUNTIME = POWER / "skills/archify/upstream"
ADAPTED_PATHS = {
    "assets/template.html",
    "bin/visual-check.mjs",
    "renderers/sequence/render-sequence.mjs",
}


def _artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    docs = POWER / "docs"
    bundle = json.loads((docs / "tt-a1i-archify-bundle-manifest.json").read_text())
    inventory = json.loads((docs / "tt-a1i-archify-source-parity.json").read_text())
    provenance = (docs / "tt-a1i-archify-provenance.md").read_text()
    records = re.findall(r"^```json\n(.*?)^```$", provenance, re.MULTILINE | re.DOTALL)
    patches = re.findall(r"^```diff\n(.*?)^```$", provenance, re.MULTILINE | re.DOTALL)
    assert len(records) == len(patches) == 1
    return bundle, inventory, json.loads(records[0]), patches[0]


def _git_object(kind: str, raw: bytes) -> str:
    return hashlib.sha1(kind.encode() + b" " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def _tree_identity(tree: dict[str, Any]) -> str:
    entries = []
    for name, item in tree.items():
        directory = isinstance(item, dict)
        mode, sha = ("40000", _tree_identity(item)) if directory else item
        entries.append(
            (
                (name + ("/" if directory else "")).encode(),
                mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(sha),
            )
        )
    return _git_object("tree", b"".join(value for _, value in sorted(entries)))


def _assert_inventory_trees(inventory: dict[str, Any]) -> None:
    for revision in ("pinned", "current"):
        tree: dict[str, Any] = {}
        for item in inventory["files"]:
            if item[revision] is None:
                continue
            here = tree
            *directories, name = item["path"].split("/")
            for directory in directories:
                here = here.setdefault(directory, {})
            here[name] = (item[revision]["mode"], item[revision]["object_sha"])
        assert _tree_identity(tree) == inventory["source"][revision]["subtree_sha"]


def _file_identity(raw: bytes, mode: str) -> dict[str, Any]:
    return {
        "mode": mode,
        "object_sha": _git_object("blob", raw),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _assert_runtime_identity(
    bundle: dict[str, Any], inventory: dict[str, Any], record: dict[str, Any]
) -> None:
    _assert_inventory_trees(inventory)
    assert record["schema_version"] == 1
    assert record["source_id"] == inventory["source"]["id"]
    assert record["upstream"] == inventory["source"]["current"]
    patches = {item["path"]: item for item in record["patches"]}
    assert len(patches) == len(record["patches"])
    assert set(patches) == ADAPTED_PATHS
    sources = {item["path"]: item for item in inventory["files"]}
    runtime_files = {
        item["path"].removeprefix("upstream/"): item
        for item in bundle["files"]
        if item["path"].startswith("upstream/")
    }
    assert {
        name for name, item in runtime_files.items() if item["handling"] == "adapted-runtime"
    } == ADAPTED_PATHS
    assert set(runtime_files) == {
        item["path"]
        for item in inventory["files"]
        if item["disposition"] == "A" and item["path"] != "SKILL.md"
    }
    for name, item in runtime_files.items():
        target = RUNTIME / name
        actual = _file_identity(
            target.read_bytes(), "100755" if target.stat().st_mode & 0o111 else "100644"
        )
        assert item["source_path"] == f"{inventory['source']['path']}/{name}"
        for key in ("sha256", "size", "mode"):
            assert actual[key] == item[key], name
        if name in patches:
            patch = patches[name]
            assert patch["reason"].strip()
            assert actual == patch["local"], name
            assert actual["object_sha"] != sources[name]["current"]["object_sha"], name
            expected = patch["upstream"]
            assert "adaptation" in sources[name]["rationale"]
        else:
            assert item["handling"] == "byte-exact-runtime", name
            expected = actual
        assert {key: expected[key] for key in ("mode", "object_sha", "size")} == {
            key: sources[name]["current"][key] for key in ("mode", "object_sha", "size")
        }, name


def test_archify_patch_reconstructs_the_recorded_upstream_bytes(tmp_path: Path) -> None:
    bundle, inventory, record, diff = _artifacts()
    _assert_runtime_identity(bundle, inventory, record)
    git = shutil.which("git")
    if git is None:
        pytest.skip("Git is required to verify the recorded local patch")  # ty: ignore[too-many-positional-arguments]
    work = tmp_path / "reconstructed"
    for item in record["patches"]:
        target = work / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RUNTIME / item["path"], target)
    patch = tmp_path / "local.patch"
    patch.write_text(diff)
    result = subprocess.run(
        [git, "apply", "--reverse", "--", str(patch)],
        cwd=work,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for item in record["patches"]:
        original = (work / item["path"]).read_bytes()
        assert _file_identity(original, item["upstream"]["mode"]) == item["upstream"]


def test_archify_rejects_local_hashes_substituted_for_upstream_inventory() -> None:
    _, inventory, record, _ = _artifacts()
    changed = copy.deepcopy(inventory)
    entry = next(item for item in changed["files"] if item["path"] in ADAPTED_PATHS)
    local = next(item["local"] for item in record["patches"] if item["path"] == entry["path"])
    entry["current"].update({key: local[key] for key in ("mode", "object_sha", "size")})
    with pytest.raises(AssertionError):
        _assert_inventory_trees(changed)


@pytest.mark.parametrize("tamper", ["unrecorded-adaptation", "local-hash"])
def test_archify_rejects_unreviewed_runtime_provenance(tamper: str) -> None:
    bundle, inventory, record, _ = _artifacts()
    if tamper == "unrecorded-adaptation":
        item = next(item for item in bundle["files"] if item["path"] == "upstream/bin/archify.mjs")
        item["handling"] = "adapted-runtime"
    else:
        record["patches"][0]["local"]["sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        _assert_runtime_identity(bundle, inventory, record)
