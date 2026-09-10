"""Read-only accounting for every entrypoint in the pinned Pocock skill repository."""

from __future__ import annotations

import hashlib
import os
import re
import time
from collections import Counter
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from pkstack.bootstrap import _validate_curated_bundle_manifest
from pkstack.paths import workspace_path
from pkstack.upstreams import (
    _SOURCE_INVENTORY_PARITY_KEYS,
    _SOURCE_INVENTORY_PARITY_SOURCE_KEYS,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_RESPONSE_BYTES,
    MAX_TREE_ENTRIES,
    FetchJSON,
    UpstreamError,
    _commit_identity,
    _fetch_json,
    _github_token,
    _inventory_file_identities,
    _read_json_path,
    _require_exact_keys,
    _response_sha,
    _source_parity_identity,
    _tree_files,
    _validate_retrieved_on,
    _validate_source_inventory_document,
    _validated_timeout,
)

CATALOG_PATH = Path("metadata/mattpocock-skill-catalog.json")
REPOSITORY = "mattpocock/skills"
DISPOSITIONS = {"imported", "consolidated", "covered", "deferred", "excluded"}
MAX_CATALOG_BYTES = 128 * 1024
MAX_CATALOG_SKILLS = 256
ENTRY_KEYS = {
    "name",
    "path",
    "disposition",
    "destination",
    "rationale",
    "source_id",
    "bundle_manifest",
}


def _json(root: Path, relative: str | Path, limit: int = MAX_CATALOG_BYTES) -> Any:
    path = workspace_path(root, Path(relative))
    if path.is_symlink() or not path.is_file():
        raise UpstreamError("catalog asset must be a regular local file")
    return _read_json_path(path, context="Pocock catalog asset", max_bytes=limit)


def _tree_identities(
    files: dict[str, tuple[str, str, str, int | None]],
) -> tuple[str, dict[str, str]]:
    nodes: dict[str, Any] = {}
    for path, (kind, mode, sha, _) in files.items():
        if (kind, mode) not in {
            ("blob", "100644"),
            ("blob", "100755"),
            ("blob", "120000"),
            ("commit", "160000"),
        }:
            raise UpstreamError("catalog tree has an unsupported entry mode")
        here = nodes
        *parents, name = path.split("/")
        for parent in parents:
            value = here.setdefault(parent, {})
            if not isinstance(value, dict):
                raise UpstreamError("catalog tree contains a file/directory collision")
            here = value
        if name in here:
            raise UpstreamError("catalog tree contains a duplicate or conflicting path")
        here[name] = (mode, sha)
    identities: dict[str, str] = {}

    def encode(node: dict[str, Any], path: str) -> str:
        entries = []
        for name, value in node.items():
            directory = isinstance(value, dict)
            child = f"{path}/{name}" if path else name
            mode, sha = ("40000", encode(value, child)) if directory else value
            entries.append(
                (
                    (name + ("/" if directory else "")).encode(),
                    mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(sha),
                )
            )
        content = b"".join(raw for _, raw in sorted(entries))
        sha = hashlib.sha1(b"tree " + str(len(content)).encode() + b"\0" + content).hexdigest()
        identities[path] = sha
        return sha

    return encode(nodes, ""), identities


def _entrypoints(files: dict[str, tuple[str, str, str, int | None]]) -> set[str]:
    found = set()
    for path, (kind, mode, _, _) in files.items():
        if path.startswith("skills/") and path.endswith("/SKILL.md"):
            if kind != "blob" or mode not in {"100644", "100755"}:
                raise UpstreamError("catalog entrypoint must be a regular source blob")
            found.add(path)
    if not 1 <= len(found) <= MAX_CATALOG_SKILLS:
        raise UpstreamError("catalog entrypoint count is outside its bounded range")
    return found


def validate_catalog(power_root: Path) -> dict[str, Any]:
    """Validate offline completeness, original tree identities, destinations, and bundles."""
    root = power_root.resolve()
    catalog = _json(root, CATALOG_PATH)
    if (
        not isinstance(catalog, dict)
        or set(catalog)
        != {"schema_version", "repository", "ref", "pinned", "tree_snapshot", "skills"}
        or type(catalog["schema_version"]) is not int
        or catalog["schema_version"] != 1
        or catalog["repository"] != REPOSITORY
        or catalog["ref"] != "main"
        or catalog["tree_snapshot"] != "metadata/mattpocock-catalog-tree.json"
    ):
        raise UpstreamError("invalid Pocock catalog schema or source")
    pin = catalog["pinned"]
    if not isinstance(pin, dict) or set(pin) != {"commit", "tree_sha"}:
        raise UpstreamError("invalid Pocock catalog pin")
    _response_sha(pin["commit"], "catalog commit")
    _response_sha(pin["tree_sha"], "catalog tree")
    snapshot = _json(root, catalog["tree_snapshot"], MAX_RESPONSE_BYTES)
    directory_shas: dict[str, str] = {}
    files = _tree_files(
        REPOSITORY,
        pin["tree_sha"],
        token=None,
        timeout_seconds=1,
        fetch_json=lambda *_: snapshot,
        tree_shas=directory_shas,
    )
    tree_sha, reconstructed = _tree_identities(files)
    if tree_sha != pin["tree_sha"] or directory_shas != {
        k: v for k, v in reconstructed.items() if k
    }:
        raise UpstreamError("catalog snapshot does not reconstruct its pinned Git tree")
    expected = _entrypoints(files)
    entries = catalog["skills"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_CATALOG_SKILLS:
        raise UpstreamError("invalid Pocock catalog entries")
    paths = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            raise UpstreamError("invalid Pocock catalog entry fields")
        path, name = entry["path"], entry["name"]
        if (
            not isinstance(path, str)
            or path not in expected
            or not isinstance(name, str)
            or name != PurePosixPath(path).parent.name
            or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is None
        ):
            raise UpstreamError("catalog entry does not identify a pinned skill")
        if not isinstance(entry["disposition"], str) or entry["disposition"] not in DISPOSITIONS:
            raise UpstreamError("catalog entry is missing an allowed disposition")
        rationale = entry["rationale"]
        if (
            not isinstance(rationale, str)
            or not rationale.strip()
            or len(rationale.encode()) > 2048
        ):
            raise UpstreamError("catalog entry needs a bounded rationale")
        destination = entry["destination"]
        if not isinstance(destination, str) or not destination:
            raise UpstreamError("catalog entry needs a destination")
        disposition = entry["disposition"]
        if disposition in {"deferred", "excluded"}:
            if destination != "not-installed":
                raise UpstreamError("uninstalled catalog entry has an active destination")
        elif destination.startswith("native:"):
            if disposition != "covered" or destination != "native:Specs":
                raise UpstreamError("catalog native destination is unsupported")
        elif not workspace_path(root, Path(destination)).is_file():
            raise UpstreamError("catalog destination is missing")
        if disposition in {"imported", "consolidated"}:
            _validate_source_bundle(root, entry)
        elif entry["source_id"] is not None or entry["bundle_manifest"] is not None:
            raise UpstreamError("unimported catalog entry cannot claim a source bundle")
        paths.append(path)
    if paths != sorted(expected):
        raise UpstreamError("catalog needs exactly one disposition for every pinned entrypoint")
    return catalog


def _validate_source_bundle(
    root: Path,
    entry: dict[str, Any],
) -> None:
    name = entry["name"]
    source_id = f"mattpocock-{name}"
    if (
        entry["source_id"] != source_id
        or entry["bundle_manifest"] != f"metadata/{source_id}-bundle-manifest.json"
    ):
        raise UpstreamError("catalog bundle identity disagrees with its source")
    source_path = str(PurePosixPath(entry["path"]).parent)
    inventory = _json(root, f"metadata/{source_id}-source-parity.json")
    if not isinstance(inventory, dict) or not isinstance(inventory.get("source"), dict):
        raise UpstreamError("catalog source inventory must be an object with a source")
    _require_exact_keys(inventory, _SOURCE_INVENTORY_PARITY_KEYS, "catalog source inventory")
    if type(inventory["schema_version"]) is not int or inventory["schema_version"] != 1:
        raise UpstreamError("catalog source inventory has an unsupported schema")
    if inventory["artifact_type"] != "source-inventory":
        raise UpstreamError("catalog source inventory has an unsupported artifact type")
    source = inventory["source"]
    _require_exact_keys(source, _SOURCE_INVENTORY_PARITY_SOURCE_KEYS, "catalog source")
    _validate_retrieved_on(source["retrieved_on"], context="catalog source")
    if (
        source.get("id") != source_id
        or source.get("repository") != REPOSITORY
        or source.get("path") != source_path
    ):
        raise UpstreamError("catalog source inventory does not match its source")
    prefix = source_path + "/"
    inventory_files = inventory.get("files")
    if not isinstance(inventory_files, list) or len(inventory_files) > MAX_TREE_ENTRIES:
        raise UpstreamError("catalog source inventory has no files")
    seen = set()
    shipped = set()
    revisions: dict[str, dict[str, tuple[str, str, str, int | None]]] = {
        "pinned": {},
        "current": {},
    }
    for resource in inventory_files:
        if not isinstance(resource, dict) or not isinstance(resource.get("path"), str):
            raise UpstreamError("catalog source resource must have a path")
        path = resource["path"]
        if path in seen:
            raise UpstreamError("catalog source resource is missing or duplicated")
        seen.add(path)
        for revision, identities in revisions.items():
            identity = resource.get(revision)
            if identity is None:
                continue
            if not isinstance(identity, dict):
                raise UpstreamError("catalog source resource needs a Git identity")
            size = identity.get("size")
            if size is not None and (type(size) is not int or size < 0):
                raise UpstreamError("catalog source resource size is invalid")
            identities[path] = (
                identity.get("type"),
                identity.get("mode"),
                identity.get("object_sha"),
                size,
            )
        disposition = resource.get("disposition")
        if not isinstance(disposition, str) or disposition not in {"A", "B", "C"}:
            raise UpstreamError("catalog source resource needs a disposition")
        if disposition == "A" and resource.get("current") is not None:
            shipped.add(prefix + path)
    # The catalog freezes entrypoint accounting, not each independently maintained
    # source revision. Source-bound acceptance authenticates transitions separately.
    for revision, identities in revisions.items():
        source_identity = _source_parity_identity(source[revision], revision)
        validated = _inventory_file_identities({f"{revision}_files": identities}, revision=revision)
        if _tree_identities(validated)[0] != source_identity["subtree_sha"]:
            raise UpstreamError("catalog source inventory does not reconstruct original Git bytes")
    _validate_source_inventory_document(
        inventory, expected_pinned=revisions["pinned"], expected_current=revisions["current"]
    )
    bundle = _json(root, entry["bundle_manifest"])
    if not isinstance(bundle, dict):
        raise UpstreamError("catalog bundle must be an object")
    bundle_root = bundle.get("bundle_root")
    if not isinstance(bundle_root, str) or not entry["destination"].startswith(bundle_root + "/"):
        raise UpstreamError("catalog destination is outside its source bundle")
    _validate_curated_bundle_manifest(
        root,
        {"name": name, "bundle_root": bundle_root, "bundle_manifest": entry["bundle_manifest"]},
    )
    if {item["source_path"] for item in bundle["files"]} != shipped:
        raise UpstreamError("catalog bundle must account for every adapted source resource")


def check_catalog(
    power_root: Path,
    *,
    offline: bool = False,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    fetch_json: FetchJSON | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Report additions/removals without installing skills or accepting a new revision."""
    catalog = validate_catalog(power_root)
    pinned_paths = {entry["path"] for entry in catalog["skills"]}
    current = catalog["pinned"]
    current_paths = pinned_paths
    if not offline:
        deadline = time.monotonic() + _validated_timeout(timeout_seconds)
        raw_fetch = _fetch_json if fetch_json is None else fetch_json
        token = _github_token(os.environ if environ is None else environ)

        def fetch(url: str, request_token: str | None, _: float) -> Any:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise UpstreamError("catalog network time budget was exhausted")
            return raw_fetch(url, request_token, remaining)

        pin_commit, pin_tree = _commit_identity(
            REPOSITORY,
            catalog["pinned"]["commit"],
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch,
        )
        if {"commit": pin_commit, "tree_sha": pin_tree} != catalog["pinned"]:
            raise UpstreamError("catalog pin does not match the remote commit tree")
        commit, tree_sha = _commit_identity(
            REPOSITORY,
            catalog["ref"],
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch,
        )
        current = {"commit": commit, "tree_sha": tree_sha}
        files = _tree_files(
            REPOSITORY,
            tree_sha,
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch,
        )
        if _tree_identities(files)[0] != tree_sha:
            raise UpstreamError("current catalog tree identity is incomplete")
        current_paths = _entrypoints(files)
    added, removed = sorted(current_paths - pinned_paths), sorted(pinned_paths - current_paths)
    return {
        "schema_version": 1,
        "ok": not added and not removed,
        "mode": "offline" if offline else "live",
        "repository": REPOSITORY,
        "pinned": catalog["pinned"],
        "current": current,
        "pinned_count": len(pinned_paths),
        "current_count": len(current_paths),
        "dispositions": dict(
            sorted(Counter(entry["disposition"] for entry in catalog["skills"]).items())
        ),
        "added": added,
        "removed": removed,
        "missing_dispositions": added,
        "acceptance": "manual disposition and source review required; no automatic installation",
    }
