#!/usr/bin/env python3
"""Deterministic regressions for the immutable PK-Stack maintenance boundary."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
GUARD_PATH = ROOT / ".github" / "scripts" / "pk_stack_maintenance_guard.py"
SPEC = importlib.util.spec_from_file_location("pk_stack_maintenance_guard", GUARD_PATH)
assert SPEC is not None and SPEC.loader is not None
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
STREAM_GUARD_PATH = ROOT / ".github" / "scripts" / "validate_kiro_credential_stream.py"
STREAM_SPEC = importlib.util.spec_from_file_location(
    "validate_kiro_credential_stream", STREAM_GUARD_PATH
)
assert STREAM_SPEC is not None and STREAM_SPEC.loader is not None
stream_guard = importlib.util.module_from_spec(STREAM_SPEC)
STREAM_SPEC.loader.exec_module(stream_guard)
PERMISSION_STREAM_GUARD_PATH = ROOT / ".github" / "scripts" / "validate_kiro_permission_stream.py"
PERMISSION_STREAM_SPEC = importlib.util.spec_from_file_location(
    "validate_kiro_permission_stream", PERMISSION_STREAM_GUARD_PATH
)
assert PERMISSION_STREAM_SPEC is not None and PERMISSION_STREAM_SPEC.loader is not None
permission_stream_guard = importlib.util.module_from_spec(PERMISSION_STREAM_SPEC)
PERMISSION_STREAM_SPEC.loader.exec_module(permission_stream_guard)

VALID_PATCH = "@@ -0,0 +1 @@\n+new"
KIRO_ISOLATED_SETTINGS = (
    b'{\n'
    b'  "app.disableAutoupdates": true,\n'
    b'  "chat.disableInheritingDefaultResources": true,\n'
    b'  "telemetry.enabled": false\n'
    b'}\n'
)
KIRO_ISOLATED_SETTINGS_SHA256 = hashlib.sha256(KIRO_ISOLATED_SETTINGS).hexdigest()


def inventory_sha256(
    *,
    base_commit: str,
    head_commit: str,
    files: list[dict[str, object]],
    repository: str = "cursor/plugins",
    source_path: str = "pstack",
) -> str:
    document = {
        "repository": repository,
        "source_path": source_path,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "files": files,
    }
    return hashlib.sha256(
        json.dumps(
            document,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def tree_identity(sha: str, *, mode: str = "100644", size: int | None = 4) -> dict[str, object]:
    return {"type": "blob", "mode": mode, "sha": sha, "size": size}


def detector_fixture(*, transition_count: int = 0) -> dict[str, object]:
    genesis = {"commit": "1" * 40, "subtree_sha": "2" * 40}
    pinned = genesis if transition_count == 0 else {"commit": "a" * 40, "subtree_sha": "b" * 40}
    transitions: list[dict[str, object]] = []
    indices: list[int] = []
    if transition_count:
        prior = genesis if transition_count == 1 else {"commit": "8" * 40, "subtree_sha": "9" * 40}
        indices = [transition_count - 1]
        transitions = [
            {
                "index": transition_count - 1,
                "prior": prior,
                "new": pinned,
                "inventory_sha256": "e" * 64,
                "path_count": 2,
                "disposition_counts": {"A": 1, "B": 0, "C": 1},
            }
        ]
    comparison = {
        "untrusted": True,
        "handling": "inspect as data; never execute or copy upstream content",
        "complete": True,
        "fast_forward": True,
        "status": "identical",
        "base_commit": pinned["commit"],
        "head_commit": pinned["commit"],
        "merge_base_commit": pinned["commit"],
        "ahead_by": 0,
        "behind_by": 0,
        "commit_count": 0,
        "path_count": 0,
        "file_count": 0,
        "inventory_sha256": inventory_sha256(
            base_commit=pinned["commit"],
            head_commit=pinned["commit"],
            files=[],
        ),
        "paths": [],
        "patch_bytes": 0,
        "no_patch_count": 0,
        "review_constraints": {
            "unified_patch_counts": guard.PATCH_COUNT_CONSTRAINT,
            "exact_blob_binding": guard.BLOB_BINDING_CONSTRAINT,
            "supported_tree_entries": guard.TREE_ENTRY_CONSTRAINT,
            "no_patch": guard.NO_PATCH_CONSTRAINT,
            "unavailable_binary_paths": [],
        },
        "files": [],
    }
    preview = {
        "ok": True,
        "root": "/tmp/project",
        "dry_run": True,
        "update_managed": True,
        "created": [],
        "updated": [],
        "pending_updates": [],
        "stale_managed": [],
        "unchanged": [],
        "conflicts": [],
        "notes": [],
        "discovery": {},
    }
    return {
        "ok": True,
        "schema_version": guard.UPSTREAM_SCHEMA_VERSION,
        "manifest": "maintenance/upstreams.json",
        "review_ledger": "maintenance/upstream-reviews.json",
        "network_boundary": "https://api.github.com",
        "selected_source_id": None,
        "sources": [
            {
                "ok": True,
                "id": "cursor-pstack",
                "repository": "cursor/plugins",
                "path": "pstack",
                "ref": "main",
                "provenance_path": "powers/pk-stack/docs/provenance.md",
                "parity_path": "powers/pk-stack/docs/upstream-skill-parity.json",
                "pinned": pinned,
                "pinned_reproof": {"ok": True, **pinned},
                "current": pinned,
                "drift": False,
                "comparison": comparison,
                "review_reproof": {
                    "ok": True,
                    "source_id": "cursor-pstack",
                    "genesis": genesis,
                    "tip": pinned,
                    "transition_count": transition_count,
                    "remote_transition_indices": indices,
                    "history_validation": (
                        "all entries form a strict local contiguous chain; repository history is the "
                        "tamper-evident authority for older reviewed transitions"
                    ),
                    "transitions": transitions,
                },
                "source_parity": {
                    "ok": True,
                    "candidate_ready": False,
                    "artifact_type": "skill-catalog",
                    "status": "accepted-baseline",
                    "path": "powers/pk-stack/docs/upstream-skill-parity.json",
                    "errors": [],
                    "pinned_resource_count": 1,
                    "current_resource_count": 1,
                    "classified_resource_count": 1,
                },
            }
        ],
        "bootstrap_preview": preview,
        "generated_parity": {
            "ok": True,
            "dry_run": True,
            "update_managed": True,
            "differences": {},
        },
    }


def drift_detector_fixture(*, transition_count: int = 0) -> dict[str, object]:
    payload = detector_fixture(transition_count=transition_count)
    source = payload["sources"][0]  # type: ignore[index]
    comparison = source["comparison"]  # type: ignore[index]
    source["ok"] = False  # type: ignore[index]
    source["drift"] = True  # type: ignore[index]
    source["current"] = {"commit": "c" * 40, "subtree_sha": "d" * 40}  # type: ignore[index]
    comparison.update(  # type: ignore[union-attr]
        {
            "status": "ahead",
            "head_commit": "c" * 40,
            "ahead_by": 1,
            "commit_count": 1,
            "path_count": 1,
            "file_count": 1,
            "paths": ["README.md"],
            "patch_bytes": len(VALID_PATCH.encode("utf-8")),
            "files": [
                {
                    "path": "README.md",
                    "previous_path": None,
                    "status": "modified",
                    "sha": "e" * 40,
                    "additions": 1,
                    "deletions": 0,
                    "changes": 1,
                    "patch": VALID_PATCH,
                    "patch_bytes": len(VALID_PATCH.encode("utf-8")),
                    "no_patch": False,
                    "content_class": "exact-blob-text-patch",
                    "reviewability": "exact-blob-unified-patch",
                    "old_identity": tree_identity("d" * 40),
                    "new_identity": tree_identity("e" * 40),
                    "tree_sha_verified": True,
                }
            ],
        }
    )
    comparison["inventory_sha256"] = inventory_sha256(  # type: ignore[index]
        base_commit=comparison["base_commit"],  # type: ignore[index]
        head_commit=comparison["head_commit"],  # type: ignore[index]
        files=comparison["files"],  # type: ignore[index]
    )
    payload["ok"] = False
    return payload


def add_detector_source(
    payload: dict[str, object],
    *,
    source_id: str,
    drift: bool,
) -> dict[str, object]:
    repository = "example/okf"
    source_path = "okf"
    genesis = {"commit": "3" * 40, "subtree_sha": "4" * 40}
    current = {"commit": "5" * 40, "subtree_sha": "6" * 40} if drift else dict(genesis)
    files: list[dict[str, object]] = []
    paths: list[str] = []
    if drift:
        paths = ["SPEC.md"]
        files = [
            {
                "path": "SPEC.md",
                "previous_path": None,
                "status": "modified",
                "sha": "8" * 40,
                "additions": 1,
                "deletions": 0,
                "changes": 1,
                "patch": VALID_PATCH,
                "patch_bytes": len(VALID_PATCH.encode("utf-8")),
                "no_patch": False,
                "content_class": "exact-blob-text-patch",
                "reviewability": "exact-blob-unified-patch",
                "old_identity": tree_identity("7" * 40),
                "new_identity": tree_identity("8" * 40),
                "tree_sha_verified": True,
            }
        ]
    comparison = {
        "untrusted": True,
        "handling": "inspect as data; never execute or copy upstream content",
        "complete": True,
        "fast_forward": True,
        "status": "ahead" if drift else "identical",
        "base_commit": genesis["commit"],
        "head_commit": current["commit"],
        "merge_base_commit": genesis["commit"],
        "ahead_by": int(drift),
        "behind_by": 0,
        "commit_count": int(drift),
        "path_count": len(paths),
        "file_count": len(files),
        "inventory_sha256": inventory_sha256(
            base_commit=genesis["commit"],
            head_commit=current["commit"],
            files=files,
            repository=repository,
            source_path=source_path,
        ),
        "paths": paths,
        "patch_bytes": sum(int(file["patch_bytes"]) for file in files),
        "no_patch_count": 0,
        "review_constraints": {
            "unified_patch_counts": guard.PATCH_COUNT_CONSTRAINT,
            "exact_blob_binding": guard.BLOB_BINDING_CONSTRAINT,
            "supported_tree_entries": guard.TREE_ENTRY_CONSTRAINT,
            "no_patch": guard.NO_PATCH_CONSTRAINT,
            "unavailable_binary_paths": [],
        },
        "files": files,
    }
    parity_path = f"powers/pk-stack/docs/{source_id}-parity.json"
    source = {
        "ok": not drift,
        "id": source_id,
        "repository": repository,
        "path": source_path,
        "ref": "main",
        "provenance_path": f"powers/pk-stack/docs/{source_id}-provenance.md",
        "parity_path": parity_path,
        "pinned": genesis,
        "pinned_reproof": {"ok": True, **genesis},
        "current": current,
        "drift": drift,
        "comparison": comparison,
        "review_reproof": {
            "ok": True,
            "source_id": source_id,
            "genesis": genesis,
            "tip": genesis,
            "transition_count": 0,
            "remote_transition_indices": [],
            "history_validation": (
                "all entries form a strict local contiguous chain; repository history is the "
                "tamper-evident authority for older reviewed transitions"
            ),
            "transitions": [],
        },
        "source_parity": {
            "ok": True,
            "candidate_ready": False,
            "artifact_type": "source-inventory",
            "status": "accepted-baseline",
            "path": parity_path,
            "errors": [],
            "pinned_resource_count": 1,
            "current_resource_count": 1,
            "classified_resource_count": 1,
        },
    }
    payload["sources"].append(source)  # type: ignore[union-attr]
    payload["ok"] = all(item["ok"] for item in payload["sources"])  # type: ignore[index]
    return source


def accepted_detector_fixture(
    payload: dict[str, object],
    *,
    selected_source_id: str,
) -> dict[str, object]:
    accepted = json.loads(json.dumps(payload))
    source = next(item for item in accepted["sources"] if item["id"] == selected_source_id)
    prior = source["pinned"]
    new = source["current"]
    comparison = source["comparison"]
    inventory_digest = comparison["inventory_sha256"]
    path_count = comparison["path_count"]
    before_count = source["review_reproof"]["transition_count"]
    source["pinned"] = new
    source["pinned_reproof"] = {"ok": True, **new}
    source["ok"] = True
    source["drift"] = False
    source["comparison"] = {
        "untrusted": True,
        "handling": "inspect as data; never execute or copy upstream content",
        "complete": True,
        "fast_forward": True,
        "status": "identical",
        "base_commit": new["commit"],
        "head_commit": new["commit"],
        "merge_base_commit": new["commit"],
        "ahead_by": 0,
        "behind_by": 0,
        "commit_count": 0,
        "path_count": 0,
        "file_count": 0,
        "inventory_sha256": inventory_sha256(
            base_commit=new["commit"],
            head_commit=new["commit"],
            files=[],
            repository=source["repository"],
            source_path=source["path"],
        ),
        "paths": [],
        "patch_bytes": 0,
        "no_patch_count": 0,
        "review_constraints": {
            "unified_patch_counts": guard.PATCH_COUNT_CONSTRAINT,
            "exact_blob_binding": guard.BLOB_BINDING_CONSTRAINT,
            "supported_tree_entries": guard.TREE_ENTRY_CONSTRAINT,
            "no_patch": guard.NO_PATCH_CONSTRAINT,
            "unavailable_binary_paths": [],
        },
        "files": [],
    }
    source["review_reproof"].update(
        {
            "tip": new,
            "transition_count": before_count + 1,
            "remote_transition_indices": [before_count],
            "transitions": [
                {
                    "index": before_count,
                    "prior": prior,
                    "new": new,
                    "inventory_sha256": inventory_digest,
                    "path_count": path_count,
                    "disposition_counts": {"A": path_count, "B": 0, "C": 0},
                }
            ],
        }
    )
    source["source_parity"].update(
        {
            "ok": True,
            "candidate_ready": False,
            "status": "accepted-baseline",
            "errors": [],
        }
    )
    accepted["ok"] = all(item["ok"] for item in accepted["sources"])
    return accepted


def comparison_file_fixture(
    *,
    path: str | None,
    previous_path: str | None,
    status: str,
    tree_sha_verified: bool,
) -> dict[str, object]:
    old_identity = (
        tree_identity("d" * 40)
        if status in {"removed", "modified", "changed"} or (status == "renamed" and previous_path)
        else None
    )
    new_identity = (
        tree_identity("e" * 40)
        if status in {"added", "copied", "modified", "changed"} or (status == "renamed" and path)
        else None
    )
    return {
        "path": path,
        "previous_path": previous_path,
        "status": status,
        "sha": "e" * 40,
        "additions": 1,
        "deletions": 0,
        "changes": 1,
        "patch": VALID_PATCH,
        "patch_bytes": len(VALID_PATCH.encode("utf-8")),
        "no_patch": False,
        "content_class": "exact-blob-text-patch",
        "reviewability": "exact-blob-unified-patch",
        "old_identity": old_identity,
        "new_identity": new_identity,
        "tree_sha_verified": tree_sha_verified,
    }


def set_comparison_files(payload: dict[str, object], files: list[dict[str, object]]) -> None:
    comparison = payload["sources"][0]["comparison"]  # type: ignore[index]
    paths = sorted(
        {
            identity
            for file in files
            for identity in (
                file["path"],
                file["previous_path"] if file["status"] == "renamed" else None,
            )
            if isinstance(identity, str)
        }
    )
    comparison.update(  # type: ignore[union-attr]
        {
            "path_count": len(paths),
            "file_count": len(files),
            "paths": paths,
            "patch_bytes": sum(int(file["patch_bytes"]) for file in files),
            "no_patch_count": sum(bool(file["no_patch"]) for file in files),
            "review_constraints": {
                "unified_patch_counts": guard.PATCH_COUNT_CONSTRAINT,
                "exact_blob_binding": guard.BLOB_BINDING_CONSTRAINT,
                "supported_tree_entries": guard.TREE_ENTRY_CONSTRAINT,
                "no_patch": guard.NO_PATCH_CONSTRAINT,
                "unavailable_binary_paths": sorted(
                    {
                        identity
                        for file in files
                        if file["reviewability"] == "unavailable-nonsemantic-image"
                        for identity in (file["path"], file["previous_path"])
                        if isinstance(identity, str)
                    }
                ),
            },
            "files": files,
        }
    )
    comparison["inventory_sha256"] = inventory_sha256(  # type: ignore[index]
        base_commit=comparison["base_commit"],  # type: ignore[index]
        head_commit=comparison["head_commit"],  # type: ignore[index]
        files=comparison["files"],  # type: ignore[index]
    )


def proposal_fixture(
    payload: dict[str, object],
    *,
    source_id: str | None = None,
) -> dict[str, object]:
    drift_sources = sorted(
        (source for source in payload["sources"] if source["drift"]),  # type: ignore[index]
        key=lambda item: item["id"],
    )
    if source_id is None:
        source = drift_sources[0]
    else:
        source = next(item for item in payload["sources"] if item["id"] == source_id)  # type: ignore[index]
    comparison = source["comparison"]  # type: ignore[index]
    unavailable = comparison["review_constraints"]["unavailable_binary_paths"]  # type: ignore[index]
    return {
        "source_id": source["id"],  # type: ignore[index]
        "prior": source["pinned"],  # type: ignore[index]
        "new": source["current"],  # type: ignore[index]
        "inventory_sha256": comparison["inventory_sha256"],  # type: ignore[index]
        "dispositions": [
            {
                "path": path,
                "disposition": "B" if path in unavailable else "A",
                "rationale": "Reviewed against the exact detector inventory.",
            }
            for path in comparison["paths"]  # type: ignore[index]
        ],
    }


def review_ledger_fixture(payload: dict[str, object]) -> dict[str, object]:
    sources = []
    for source in payload["sources"]:  # type: ignore[union-attr]
        reproof = source["review_reproof"]
        transition_count = reproof["transition_count"]
        if transition_count not in {0, 1}:
            raise AssertionError("test ledger helper supports zero or one accepted transition")
        transitions = []
        if transition_count == 1:
            summary = reproof["transitions"][0]
            counts = summary["disposition_counts"]
            dispositions = []
            for disposition in ("A", "B", "C"):
                dispositions.extend(
                    {
                        "path": f"accepted-{disposition.lower()}-{index:03d}.md",
                        "disposition": disposition,
                        "rationale": "Accepted in the prior exact review.",
                    }
                    for index in range(counts[disposition])
                )
            dispositions.sort(key=lambda item: item["path"])
            transitions = [
                {
                    "prior": summary["prior"],
                    "new": summary["new"],
                    "inventory_sha256": summary["inventory_sha256"],
                    "dispositions": dispositions,
                }
            ]
        sources.append(
            {
                "id": source["id"],
                "repository": source["repository"],
                "path": source["path"],
                "provenance_path": source["provenance_path"],
                "parity_path": source["parity_path"],
                "genesis": reproof["genesis"],
                "transitions": transitions,
            }
        )
    return {
        "schema_version": guard.UPSTREAM_SCHEMA_VERSION,
        "sources": sources,
    }


def review_marker_line(marker: dict[str, object]) -> str:
    canonical = json.dumps(marker, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"<!-- pk-stack-upstream-review: {canonical} -->"


def pending_marker_line(payload: dict[str, object], *, source_id: str | None = None) -> str:
    if source_id is None:
        source = min(
            (item for item in payload["sources"] if item["drift"]),  # type: ignore[index]
            key=lambda item: item["id"],
        )
    else:
        source = next(item for item in payload["sources"] if item["id"] == source_id)  # type: ignore[index]
    return review_marker_line(
        {
            "source_id": source["id"],  # type: ignore[index]
            "repository": source["repository"],  # type: ignore[index]
            "path": source["path"],  # type: ignore[index]
            "prior": source["pinned"],  # type: ignore[index]
            "new": source["current"],  # type: ignore[index]
            "inventory_sha256": source["comparison"]["inventory_sha256"],  # type: ignore[index]
        }
    )


def accepted_marker_lines(
    payload: dict[str, object],
    *,
    source_id: str = "cursor-pstack",
) -> list[str]:
    ledger_source = next(
        source
        for source in review_ledger_fixture(payload)["sources"]  # type: ignore[index]
        if source["id"] == source_id
    )
    return [
        review_marker_line(
            {
                "source_id": ledger_source["id"],
                "repository": ledger_source["repository"],
                "path": ledger_source["path"],
                "prior": transition["prior"],
                "new": transition["new"],
                "inventory_sha256": transition["inventory_sha256"],
            }
        )
        for transition in ledger_source["transitions"]
    ]


class StrictJsonTests(unittest.TestCase):
    def test_duplicate_keys_and_non_finite_numbers_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.json"
            for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
                path.write_bytes(raw)
                with self.assertRaises(guard.GuardError):
                    guard._load_json(path, maximum=1024, label="test input")

    def test_fable_verdict_is_bound_to_exact_candidate_and_content(self) -> None:
        _, policy = guard.load_policy(ROOT / ".github/pk-stack-maintenance-policy.json")
        base_sha = "1" * 40
        head_sha = "2" * 40
        content_sha256 = "3" * 64
        patch_sha256 = "4" * 64
        verdict = {
            "verdict": "approved",
            "reviewed_base_sha": base_sha,
            "reviewed_head_sha": head_sha,
            "reviewed_content_sha256": content_sha256,
            "reviewed_patch_sha256": patch_sha256,
            "material_findings": [],
            "summary": "No material unresolved findings in the exact candidate.",
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "verdict.json"
            execution_path = Path(temporary) / "execution.json"

            def execution(
                structured: dict[str, object],
                *,
                init_model: str = "claude-fable-5-1",
                usage_models: tuple[str, ...] = ("claude-fable-5-1",),
                duplicate_init: bool = False,
            ) -> list[dict[str, object]]:
                messages: list[dict[str, object]] = [
                    {"type": "system", "subtype": "init", "model": init_model}
                ]
                if duplicate_init:
                    messages.append({"type": "system", "subtype": "init", "model": init_model})
                messages.append(
                    {
                        "type": "result",
                        "subtype": "success",
                        "is_error": False,
                        "modelUsage": {model: {} for model in usage_models},
                        "structured_output": structured,
                    }
                )
                return messages

            path.write_text(json.dumps(verdict), encoding="utf-8")
            execution_path.write_text(json.dumps(execution(verdict)), encoding="utf-8")
            result = guard.validate_fable_verdict(
                path,
                execution_path,
                policy,
                base_sha=base_sha,
                head_sha=head_sha,
                content_sha256=content_sha256,
                patch_sha256=patch_sha256,
            )
            self.assertTrue(result["approved"])
            real_companion_usage = {
                "inputTokens": 917,
                "outputTokens": 16,
                "cacheReadInputTokens": 0,
                "cacheCreationInputTokens": 0,
                "webSearchRequests": 0,
                "costUSD": 0.000997,
                "contextWindow": 200000,
                "maxOutputTokens": 32000,
                "thinkingTokens": 0,
                "canonicalModel": "claude-haiku-4-5",
                "provider": "firstParty",
                "costBasis": "list",
            }
            companion_execution = execution(verdict)
            companion_execution[-1]["modelUsage"] = {
                "claude-fable-5-1": {
                    "canonicalModel": "claude-fable-5-1",
                    "provider": "firstParty",
                },
                "claude-haiku-4-5-20251001": real_companion_usage,
            }
            execution_path.write_text(json.dumps(companion_execution), encoding="utf-8")
            self.assertTrue(
                guard.validate_fable_verdict(
                    path,
                    execution_path,
                    policy,
                    base_sha=base_sha,
                    head_sha=head_sha,
                    content_sha256=content_sha256,
                    patch_sha256=patch_sha256,
                )["approved"]
            )
            companion_execution[-1]["modelUsage"]["claude-haiku-4-5-20251001"][  # type: ignore[index]
                "outputTokens"
            ] = 65
            execution_path.write_text(json.dumps(companion_execution), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.validate_fable_verdict(
                    path,
                    execution_path,
                    policy,
                    base_sha=base_sha,
                    head_sha=head_sha,
                    content_sha256=content_sha256,
                    patch_sha256=patch_sha256,
                )
            execution_path.write_text(json.dumps(execution(verdict)), encoding="utf-8")
            for field, replacement in (
                ("reviewed_head_sha", "5" * 40),
                ("reviewed_content_sha256", "6" * 64),
                ("reviewed_patch_sha256", "7" * 64),
            ):
                poisoned = {**verdict, field: replacement}
                path.write_text(json.dumps(poisoned), encoding="utf-8")
                with self.assertRaises(guard.GuardError):
                    guard.validate_fable_verdict(
                        path,
                        execution_path,
                        policy,
                        base_sha=base_sha,
                        head_sha=head_sha,
                        content_sha256=content_sha256,
                        patch_sha256=patch_sha256,
                    )
            rejected = {**verdict, "verdict": "rejected", "material_findings": ["unsafe skill"]}
            path.write_text(json.dumps(rejected), encoding="utf-8")
            execution_path.write_text(json.dumps(execution(rejected)), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.validate_fable_verdict(
                    path,
                    execution_path,
                    policy,
                    base_sha=base_sha,
                    head_sha=head_sha,
                    content_sha256=content_sha256,
                    patch_sha256=patch_sha256,
                )
            path.write_text(json.dumps(verdict), encoding="utf-8")
            invalid_execution_shapes = (
                execution(verdict, init_model="claude-other-model"),
                execution(verdict, duplicate_init=True),
                execution(verdict, usage_models=()),
                execution(verdict, usage_models=("claude-fable-5-1", "claude-other-model")),
            )
            for messages in invalid_execution_shapes:
                execution_path.write_text(json.dumps(messages), encoding="utf-8")
                with self.assertRaises(guard.GuardError):
                    guard.validate_fable_verdict(
                        path,
                        execution_path,
                        policy,
                        base_sha=base_sha,
                        head_sha=head_sha,
                        content_sha256=content_sha256,
                        patch_sha256=patch_sha256,
                    )


class KiroCredentialStreamTests(unittest.TestCase):
    SESSION_ID = "sess_11111111-1111-4111-8111-111111111111"
    OTHER_SESSION_ID = "sess_22222222-2222-4222-8222-222222222222"
    CALL_ID = "12345678-1234-4123-8123-123456789abc"
    REPLAY_ID = "sanitizedReplayId_1234567890123456789012"
    FOCUS_TITLE = stream_guard.MARKER

    @staticmethod
    def stream(*events: dict[str, object]) -> bytes:
        return b"".join(
            json.dumps(event, separators=(",", ":")).encode() + b"\n" for event in events
        )

    @staticmethod
    def run_started() -> dict[str, object]:
        return {
            "type": "runStarted",
            "data": {
                "payloadSchema": "acp",
                "acpProtocolVersion": 1,
                "engine": "v3",
            },
        }

    @classmethod
    def run_finished(
        cls,
        *,
        session_id: str | None = None,
        final_text: str | None = None,
        status: str = "success",
        stop_reason: str = "end_turn",
        truncated: bool = False,
    ) -> dict[str, object]:
        return {
            "type": "runFinished",
            "data": {
                "sessionId": session_id or cls.SESSION_ID,
                "status": status,
                "stopReason": stop_reason,
                "finalText": (
                    final_text if final_text is not None else stream_guard.MARKER
                ),
                "finalTextTruncated": truncated,
            },
        }

    @classmethod
    def agent_chunk(
        cls,
        text: str,
        *,
        session_id: str | None = None,
        replay_id: str | None = None,
    ) -> dict[str, object]:
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": session_id or cls.SESSION_ID,
                "update": {
                    "_meta": {"kiro": {"replayId": replay_id or cls.REPLAY_ID}},
                    "content": {"type": "text", "text": text},
                    "sessionUpdate": "agent_message_chunk",
                },
            },
        }

    @classmethod
    def cloud_config_start(cls, *, session_id: str | None = None) -> dict[str, object]:
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": session_id or cls.SESSION_ID,
                "update": {
                    "_meta": {"kiro": {"toolId": "fetch_cloud_config"}},
                    "sessionUpdate": "tool_call",
                    "status": "in_progress",
                    "title": "Fetching your cloud config",
                    "toolCallId": cls.CALL_ID,
                },
            },
        }

    @classmethod
    def cloud_config_terminal(
        cls, *, status: str = "failed", session_id: str | None = None
    ) -> dict[str, object]:
        update: dict[str, object] = {
            "sessionUpdate": "tool_call_update",
            "status": status,
            "toolCallId": cls.CALL_ID,
        }
        if status == "failed":
            update["rawOutput"] = "sanitized isolated cloud-config lookup failure"
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": session_id or cls.SESSION_ID,
                "update": update,
            },
        }

    @classmethod
    def unrelated_update(cls) -> dict[str, object]:
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": cls.SESSION_ID,
                "update": {
                    "sessionUpdate": "session_info_update",
                    "_meta": {
                        "kiro": {
                            "kind": "context_usage",
                            "breakdown": {
                                "tools": {
                                    "builtin": {"percent": 0.6, "tokens": 6},
                                    "mcp": {"percent": 0, "tokens": 0},
                                    "percent": 0.0,
                                    "tokens": 6,
                                }
                            }
                        }
                    },
                },
            },
        }

    @classmethod
    def focus_update(cls, *, title: str | None = None) -> dict[str, object]:
        current_title = title or cls.FOCUS_TITLE
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": cls.SESSION_ID,
                "update": {
                    "sessionUpdate": "session_info_update",
                    "title": current_title,
                    "_meta": {
                        "kiro": {
                            "kind": "focus_update",
                            "title": current_title,
                            "focus": {"title": current_title},
                        }
                    },
                },
            },
        }

    def complete(self, *events: dict[str, object]) -> bytes:
        return self.stream(self.run_started(), *events, self.run_finished())

    def validate(self, raw: bytes) -> dict[str, int | bool]:
        return stream_guard.validate_stream_bytes(
            raw,
            b"",
            return_code=0,
            api_key="not-present-in-stream",
        )

    def test_accepts_sanitized_real_agent_message_wire_shape(self) -> None:
        chunks = ["PK", "-", "STACK", "-K", "IRO", "-A", "UTH", "-", "OK"]
        raw = self.complete(*(self.agent_chunk(chunk) for chunk in chunks))
        self.assertEqual(self.validate(raw), {"ok": True, "events": 11})

    def test_accepts_one_bounded_challenge_with_exact_assistant_final_equality(self) -> None:
        response = f"{stream_guard.MARKER}\nAcknowledged."
        raw = self.stream(
            self.run_started(),
            self.agent_chunk(response),
            self.run_finished(final_text=response),
        )
        self.assertEqual(self.validate(raw), {"ok": True, "events": 3})

    def test_rejects_missing_duplicate_or_overlong_challenge_response(self) -> None:
        responses = (
            "no challenge present",
            f"{stream_guard.MARKER} {stream_guard.MARKER}",
            stream_guard.MARKER
            + "x" * (
                stream_guard.MAX_ASSISTANT_RESPONSE_BYTES
                - len(stream_guard.MARKER.encode())
                + 1
            ),
        )
        for response in responses:
            with self.subTest(response_bytes=len(response.encode())), self.assertRaises(
                stream_guard.StreamError
            ):
                self.validate(
                    self.stream(
                        self.run_started(),
                        self.agent_chunk(response),
                        self.run_finished(final_text=response),
                    )
                )

    def test_accepts_exact_failed_and_completed_bootstrap_pairs(self) -> None:
        for terminal in (
            self.cloud_config_terminal(status="failed"),
            self.cloud_config_terminal(status="completed"),
        ):
            with self.subTest(status=terminal["data"]["update"]["status"]):
                raw = self.complete(
                    self.cloud_config_start(),
                    self.unrelated_update(),
                    terminal,
                    self.agent_chunk(stream_guard.MARKER),
                )
                self.assertEqual(self.validate(raw), {"ok": True, "events": 6})

    def test_rejects_nested_legacy_and_user_marker_spoofs(self) -> None:
        nested = {
            "type": "telemetry",
            "data": {
                "wrapper": {
                    "sessionUpdate": "agent_message_chunk",
                    "content": {"type": "text", "text": stream_guard.MARKER},
                }
            },
        }
        legacy = {
            "sessionUpdate": {
                "sessionId": self.SESSION_ID,
                "update": {
                    "sessionUpdate": "agent_message_chunk",
                    "content": {"type": "text", "text": stream_guard.MARKER},
                },
            }
        }
        user_echo = {
            "type": "sessionUpdate",
            "data": {
                "sessionId": self.SESSION_ID,
                "update": {
                    "sessionUpdate": "user_message_chunk",
                    "content": {"type": "text", "text": stream_guard.MARKER},
                },
            },
        }
        for spoof in (nested, legacy, user_echo):
            with self.subTest(spoof=spoof), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(spoof))

    def test_marker_rejection_reports_only_bounded_structural_provenance(self) -> None:
        echoed_prompt = {
            "type": "sessionUpdate",
            "data": {
                "sessionId": self.SESSION_ID,
                "update": {
                    "sessionUpdate": "session_info_update",
                    "_meta": {
                        "kiro": {
                            "kind": "prompt_echo",
                            "prompt": f"untrusted-prefix {stream_guard.MARKER} untrusted-suffix",
                        }
                    },
                },
            },
        }
        with self.assertRaises(stream_guard.StreamError) as caught:
            self.validate(self.complete(echoed_prompt))

        message = str(caught.exception)
        self.assertIn('"event_index_0_based":1', message)
        self.assertIn('"marker_path_count":1', message)
        self.assertIn(
            '"marker_paths":["$.data.update._meta.kiro.prompt"]', message
        )
        self.assertIn('"session_update_kind":"session_info_update"', message)
        self.assertNotIn(self.SESSION_ID, message)
        self.assertNotIn(stream_guard.MARKER, message)
        self.assertNotIn("untrusted-prefix", message)
        self.assertNotIn("untrusted-suffix", message)

        many_echoes = {
            "type": "sessionUpdate",
            "data": {
                "sessionId": self.SESSION_ID,
                "update": {
                    "sessionUpdate": "config_option_update",
                    "configOptions": [
                        {"description": stream_guard.MARKER} for _ in range(12)
                    ],
                },
            },
        }
        with self.assertRaises(stream_guard.StreamError) as many_caught:
            self.validate(self.complete(many_echoes))
        diagnostic = json.loads(
            str(many_caught.exception).split("structural_diagnostic=", 1)[1]
        )
        self.assertEqual(diagnostic["marker_path_count"], 12)
        self.assertEqual(len(diagnostic["marker_paths"]), 8)
        self.assertTrue(
            all(
                path.startswith("$.data.update.configOptions[")
                for path in diagnostic["marker_paths"]
            )
        )

        long_key = "untrusted-structural-key-" + "x" * 64
        nonstandard_key_echo = {
            "type": "sessionUpdate",
            "data": {
                "sessionId": self.SESSION_ID,
                "update": {
                    "sessionUpdate": "session_info_update",
                    "_meta": {
                        "kiro": {"kind": "prompt_echo", long_key: stream_guard.MARKER}
                    },
                },
            },
        }
        with self.assertRaises(stream_guard.StreamError) as redacted_caught:
            self.validate(self.complete(nonstandard_key_echo))
        redacted_message = str(redacted_caught.exception)
        self.assertIn("$.data.update._meta.kiro.<redacted-key>", redacted_message)
        self.assertNotIn(long_key, redacted_message)

    def test_accepts_only_exact_focus_update_title_echo_as_non_evidence(self) -> None:
        raw = self.complete(
            self.focus_update(), self.agent_chunk(stream_guard.MARKER)
        )
        self.assertEqual(self.validate(raw), {"ok": True, "events": 4})

        with self.assertRaises(stream_guard.StreamError):
            self.validate(self.complete(self.focus_update()))

    def test_rejects_focus_update_title_echo_shape_drift(self) -> None:
        def clone(event: dict[str, object]) -> dict[str, object]:
            return json.loads(json.dumps(event))

        extra_update = clone(self.focus_update())
        extra_update["data"]["update"]["unexpected"] = True
        extra_metadata = clone(self.focus_update())
        extra_metadata["data"]["update"]["_meta"]["unexpected"] = True
        extra_kiro = clone(self.focus_update())
        extra_kiro["data"]["update"]["_meta"]["kiro"]["unexpected"] = True
        extra_focus = clone(self.focus_update())
        extra_focus["data"]["update"]["_meta"]["kiro"]["focus"]["unexpected"] = True
        mismatched_title = clone(self.focus_update())
        mismatched_title["data"]["update"]["_meta"]["kiro"]["title"] += " mismatch"
        wrong_kind = clone(self.focus_update())
        wrong_kind["data"]["update"]["_meta"]["kiro"]["kind"] = "prompt_echo"
        wrong_path = clone(self.focus_update())
        wrong_path["data"]["update"]["_meta"]["kiro"]["other"] = stream_guard.MARKER
        empty_title = self.focus_update(title="placeholder")
        empty_title["data"]["update"]["title"] = ""
        overlong_title = self.focus_update(
            title="x" * (stream_guard.MAX_FOCUS_TITLE_BYTES + 1)
        )

        for event in (
            extra_update,
            extra_metadata,
            extra_kiro,
            extra_focus,
            mismatched_title,
            wrong_kind,
            wrong_path,
            empty_title,
            overlong_title,
        ):
            with self.subTest(event=event), self.assertRaises(
                stream_guard.StreamError
            ):
                self.validate(
                    self.complete(event, self.agent_chunk(stream_guard.MARKER))
                )

    def test_rejects_bootstrap_order_and_identity_failures(self) -> None:
        cases = (
            (
                self.agent_chunk(stream_guard.MARKER),
                self.cloud_config_start(),
                self.cloud_config_terminal(),
            ),
            (
                self.cloud_config_start(),
                self.agent_chunk(stream_guard.MARKER),
                self.cloud_config_terminal(),
            ),
            (
                self.cloud_config_start(session_id=self.OTHER_SESSION_ID),
                self.cloud_config_terminal(session_id=self.OTHER_SESSION_ID),
                self.agent_chunk(stream_guard.MARKER),
            ),
            (self.cloud_config_start(),),
            (self.cloud_config_terminal(), self.agent_chunk(stream_guard.MARKER)),
            (
                self.cloud_config_start(),
                self.cloud_config_start(),
                self.cloud_config_terminal(),
                self.agent_chunk(stream_guard.MARKER),
            ),
            (
                self.cloud_config_start(),
                self.cloud_config_terminal(),
                self.cloud_config_terminal(),
                self.agent_chunk(stream_guard.MARKER),
            ),
        )
        for events in cases:
            with self.subTest(events=events), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(*events))

    def test_rejects_bootstrap_extra_missing_and_status_shape_confusion(self) -> None:
        def clone(event: dict[str, object]) -> dict[str, object]:
            return json.loads(json.dumps(event))

        extra_start = clone(self.cloud_config_start())
        extra_start["data"]["update"]["unexpected"] = True
        missing_failed = clone(self.cloud_config_terminal())
        del missing_failed["data"]["update"]["rawOutput"]
        empty_failed = clone(self.cloud_config_terminal())
        empty_failed["data"]["update"]["rawOutput"] = ""
        non_string_failed = clone(self.cloud_config_terminal())
        non_string_failed["data"]["update"]["rawOutput"] = {"error": "sanitized"}
        completed_with_output = clone(self.cloud_config_terminal(status="completed"))
        completed_with_output["data"]["update"]["rawOutput"] = "unexpected"
        wrong_title = clone(self.cloud_config_start())
        wrong_title["data"]["update"]["title"] = "Fetching another config"
        wrong_tool = clone(self.cloud_config_start())
        wrong_tool["data"]["update"]["_meta"]["kiro"]["toolId"] = "read"
        mismatched_terminal = clone(self.cloud_config_terminal())
        mismatched_terminal["data"]["update"]["toolCallId"] = "abcdefab-cdef-4abc-8def-abcdefabcdef"

        cases = (
            (extra_start, self.cloud_config_terminal()),
            (self.cloud_config_start(), missing_failed),
            (self.cloud_config_start(), empty_failed),
            (self.cloud_config_start(), non_string_failed),
            (self.cloud_config_start(), completed_with_output),
            (wrong_title, self.cloud_config_terminal()),
            (wrong_tool, self.cloud_config_terminal()),
            (self.cloud_config_start(), mismatched_terminal),
        )
        for start, terminal in cases:
            with self.subTest(start=start, terminal=terminal):
                raw = self.complete(
                    start,
                    terminal,
                    self.agent_chunk(stream_guard.MARKER),
                )
                with self.assertRaises(stream_guard.StreamError):
                    self.validate(raw)

    def test_rejects_unknown_tool_prefix_discriminators_and_keys(self) -> None:
        def tool_update(kind: str) -> dict[str, object]:
            return {
                "type": "sessionUpdate",
                "data": {
                    "sessionId": self.SESSION_ID,
                    "update": {
                        "sessionUpdate": kind,
                        "toolCallId": self.CALL_ID,
                    },
                },
            }

        prefixed_key = self.unrelated_update()
        prefixed_key["data"]["update"]["toolCallStart"] = {"sanitized": True}
        arbitrary_tools_key = {
            "type": "telemetry",
            "data": {
                "tools": {
                    "builtin": {"percent": 0.0, "tokens": 0},
                    "mcp": {"percent": 0.0, "tokens": 0},
                    "percent": 0.0,
                    "tokens": 0,
                }
            },
        }
        for event in (
            tool_update("tool_call_start"),
            tool_update("tool_call_delta"),
            prefixed_key,
            {"type": "telemetry", "data": {"toolCallStart": {}}},
            arbitrary_tools_key,
        ):
            with self.subTest(event=event), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(event, self.agent_chunk(stream_guard.MARKER)))

    def test_rejects_unknown_top_level_and_session_update_kinds(self) -> None:
        def unknown_session_update(kind: str) -> dict[str, object]:
            return {
                "type": "sessionUpdate",
                "data": {
                    "sessionId": self.SESSION_ID,
                    "update": {"sessionUpdate": kind},
                },
            }

        for event in (
            {"type": "commandExecution", "data": {}},
            {"type": "function_call", "data": {}},
            unknown_session_update("commandExecution"),
            unknown_session_update("function_call"),
        ):
            with self.subTest(event=event), self.assertRaises(
                stream_guard.StreamError
            ):
                self.validate(
                    self.complete(event, self.agent_chunk(stream_guard.MARKER))
                )

    def test_rejects_malformed_metrics_and_ignored_session_updates(self) -> None:
        def clone(event: dict[str, object]) -> dict[str, object]:
            return json.loads(json.dumps(event))

        wrong_metric_keys = clone(self.unrelated_update())
        wrong_metric_keys["data"]["update"]["_meta"]["kiro"]["breakdown"]["tools"]["calls"] = 0
        wrong_metric_type = clone(self.unrelated_update())
        wrong_metric_type["data"]["update"]["_meta"]["kiro"]["breakdown"]["tools"][
            "percent"
        ] = True
        wrong_metric_kind = clone(self.unrelated_update())
        wrong_metric_kind["data"]["update"]["_meta"]["kiro"]["kind"] = "other"
        arbitrary_nested_metric = clone(self.unrelated_update())
        arbitrary_nested_metric["data"]["update"]["_meta"]["kiro"]["breakdown"][
            "tools"
        ]["builtin"]["calls"] = 0
        invalid_nested_percent = clone(self.unrelated_update())
        invalid_nested_percent["data"]["update"]["_meta"]["kiro"]["breakdown"][
            "tools"
        ]["mcp"]["percent"] = 101
        invalid_nested_tokens = clone(self.unrelated_update())
        invalid_nested_tokens["data"]["update"]["_meta"]["kiro"]["breakdown"][
            "tools"
        ]["builtin"]["tokens"] = -1
        wrong_session = clone(self.unrelated_update())
        wrong_session["data"]["sessionId"] = self.OTHER_SESSION_ID
        malformed_envelope = clone(self.unrelated_update())
        malformed_envelope["data"]["unexpected"] = True

        for event in (
            wrong_metric_keys,
            wrong_metric_type,
            wrong_metric_kind,
            arbitrary_nested_metric,
            invalid_nested_percent,
            invalid_nested_tokens,
            wrong_session,
            malformed_envelope,
        ):
            with self.subTest(event=event), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(event, self.agent_chunk(stream_guard.MARKER)))

    def test_rejects_agent_and_run_boundary_shape_or_identity_drift(self) -> None:
        def clone(event: dict[str, object]) -> dict[str, object]:
            return json.loads(json.dumps(event))

        extra_agent = clone(self.agent_chunk(stream_guard.MARKER))
        extra_agent["data"]["update"]["unexpected"] = True
        nested_content = clone(self.agent_chunk(stream_guard.MARKER))
        nested_content["data"]["update"]["content"]["unexpected"] = True
        changed_replay = self.agent_chunk(
            "-STACK-KIRO-AUTH-OK",
            replay_id="otherReplayId_12345678901234567890123456",
        )
        identity_cases = (
            (extra_agent,),
            (nested_content,),
            (
                self.agent_chunk("PK"),
                self.agent_chunk("-STACK-KIRO-AUTH-OK", session_id=self.OTHER_SESSION_ID),
            ),
            (self.agent_chunk("PK"), changed_replay),
            (self.agent_chunk(stream_guard.MARKER + " "),),
        )
        for events in identity_cases:
            with self.subTest(events=events), self.assertRaises(stream_guard.StreamError):
                self.validate(self.complete(*events))

        with self.assertRaises(stream_guard.StreamError):
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(stream_guard.MARKER),
                    self.run_finished(session_id=self.OTHER_SESSION_ID),
                )
            )
        with self.assertRaises(stream_guard.StreamError):
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(stream_guard.MARKER),
                    self.run_finished(),
                    self.unrelated_update(),
                )
            )
        malformed_start = self.run_started()
        malformed_start["data"]["unexpected"] = True
        wrong_protocol_type = self.run_started()
        wrong_protocol_type["data"]["acpProtocolVersion"] = True
        malformed_finish = self.run_finished()
        malformed_finish["data"]["unexpected"] = True
        for start, finish in (
            (malformed_start, self.run_finished()),
            (wrong_protocol_type, self.run_finished()),
            (self.run_started(), malformed_finish),
        ):
            with self.subTest(start=start, finish=finish), self.assertRaises(
                stream_guard.StreamError
            ):
                self.validate(
                    self.stream(
                        start,
                        self.agent_chunk(stream_guard.MARKER),
                        finish,
                    )
                )

    def test_run_finished_failure_reports_only_bounded_non_content_metadata(self) -> None:
        unexpected_final = f"sensitive-prefix {stream_guard.MARKER} sensitive-suffix"
        with self.assertRaises(stream_guard.StreamError) as mismatch_caught:
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(stream_guard.MARKER),
                    self.run_finished(final_text=unexpected_final),
                )
            )
        mismatch_message = str(mismatch_caught.exception)
        mismatch_diagnostic = json.loads(
            mismatch_message.split("run_finished_diagnostic=", 1)[1]
        )
        self.assertEqual(
            mismatch_diagnostic,
            {
                "assistant_final_equal": False,
                "finalTextTruncated": False,
                "final_text_utf8_bytes": len(unexpected_final.encode()),
                "marker_occurrence_count": 1,
                "status": "success",
                "stopReason": "end_turn",
            },
        )
        self.assertNotIn(unexpected_final, mismatch_message)
        self.assertNotIn(stream_guard.MARKER, mismatch_message)
        self.assertNotIn(self.SESSION_ID, mismatch_message)
        self.assertNotIn("sensitive-prefix", mismatch_message)

        equal_non_marker = "sensitive-equal-non-marker"
        with self.assertRaises(stream_guard.StreamError) as equal_caught:
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(equal_non_marker),
                    self.run_finished(final_text=equal_non_marker),
                )
            )
        equal_message = str(equal_caught.exception)
        equal_diagnostic = json.loads(
            equal_message.split("run_finished_diagnostic=", 1)[1]
        )
        self.assertTrue(equal_diagnostic["assistant_final_equal"])
        self.assertEqual(equal_diagnostic["marker_occurrence_count"], 0)
        self.assertNotIn(equal_non_marker, equal_message)

        with self.assertRaises(stream_guard.StreamError) as failed_caught:
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(stream_guard.MARKER),
                    self.run_finished(status="failed"),
                )
            )
        failed_diagnostic = json.loads(
            str(failed_caught.exception).split("run_finished_diagnostic=", 1)[1]
        )
        self.assertEqual(failed_diagnostic["status"], "failed")
        self.assertIsNone(failed_diagnostic["assistant_final_equal"])

        unsafe_status = "sensitiveRawStatus"
        with self.assertRaises(stream_guard.StreamError) as unsafe_caught:
            self.validate(
                self.stream(
                    self.run_started(),
                    self.agent_chunk(stream_guard.MARKER),
                    self.run_finished(status=unsafe_status),
                )
            )
        unsafe_message = str(unsafe_caught.exception)
        unsafe_diagnostic = json.loads(
            unsafe_message.split("run_finished_diagnostic=", 1)[1]
        )
        self.assertIsNone(unsafe_diagnostic["status"])
        self.assertNotIn(unsafe_status, unsafe_message)

    def test_rejects_malformed_duplicate_and_non_finite_json(self) -> None:
        for raw in (
            b'{"broken":\n',
            b'{"type":"x","type":"y"}\n',
            b'{"value":NaN}\n',
        ):
            with self.assertRaises(stream_guard.StreamError):
                self.validate(raw)


class KiroPermissionStreamTests(unittest.TestCase):
    @staticmethod
    def selection_event(workspace: str) -> dict[str, object]:
        return {
            "type": "sessionUpdate",
            "data": {
                "sessionId": "sanitized-session",
                "update": {
                    "sessionUpdate": "config_option_update",
                    "configOptions": [
                        {
                            "id": "mode",
                            "name": "Mode",
                            "type": "select",
                            "category": "mode",
                            "currentValue": permission_stream_guard.PERMISSION_AGENT_NAME,
                            "options": [
                                {
                                    "name": permission_stream_guard.PERMISSION_AGENT_NAME,
                                    "value": permission_stream_guard.PERMISSION_AGENT_NAME,
                                    "description": (
                                        permission_stream_guard.PERMISSION_AGENT_DESCRIPTION
                                    ),
                                    "_meta": {
                                        "kiro": {
                                            "source": "workspace",
                                            "welcomeMessage": (
                                                permission_stream_guard.PERMISSION_AGENT_WELCOME
                                            ),
                                            "resource": {
                                                "resourceType": "agent",
                                                "source": {
                                                    "origin": "workspace",
                                                    "root": workspace,
                                                },
                                            },
                                        }
                                    },
                                }
                            ],
                        }
                    ],
                },
            },
        }

    def test_requires_exact_workspace_agent_selection_attestation(self) -> None:
        workspace = "/tmp/pk-stack-permission-workspace"
        event = self.selection_event(workspace)
        initial_vibe = json.loads(json.dumps(event))
        initial_vibe["data"]["update"]["configOptions"][0]["currentValue"] = "vibe"
        permission_stream_guard.validate_workspace_agent_selection(
            [initial_vibe, event], expected_workspace=workspace
        )

        def clone() -> dict[str, object]:
            return json.loads(json.dumps(event))

        wrong_root = clone()
        wrong_root["data"]["update"]["configOptions"][0]["options"][0]["_meta"][
            "kiro"
        ]["resource"]["source"]["root"] = "/tmp/other-workspace"
        global_source = clone()
        global_source["data"]["update"]["configOptions"][0]["options"][0]["_meta"][
            "kiro"
        ]["source"] = "global"
        extra_option_key = clone()
        extra_option_key["data"]["update"]["configOptions"][0]["options"][0][
            "unexpected"
        ] = True
        duplicate_option = clone()
        duplicate_option["data"]["update"]["configOptions"][0]["options"].append(
            duplicate_option["data"]["update"]["configOptions"][0]["options"][0]
        )
        fallback = clone()
        fallback["data"]["update"]["configOptions"][0]["currentValue"] = "vibe"
        conflicting_mode = clone()
        second_mode = json.loads(
            json.dumps(conflicting_mode["data"]["update"]["configOptions"][0])
        )
        second_mode["currentValue"] = "vibe"
        conflicting_mode["data"]["update"]["configOptions"].append(second_mode)

        for malformed in (
            wrong_root,
            global_source,
            extra_option_key,
            duplicate_option,
            fallback,
        ):
            with self.subTest(malformed=malformed), self.assertRaises(
                permission_stream_guard.StreamError
            ):
                permission_stream_guard.validate_workspace_agent_selection(
                    [malformed], expected_workspace=workspace
                )

        for events in (
            [event, fallback],
            [conflicting_mode],
        ):
            with self.subTest(events=events), self.assertRaises(
                permission_stream_guard.StreamError
            ):
                permission_stream_guard.validate_workspace_agent_selection(
                    events, expected_workspace=workspace
                )

    SESSION_ID = "sess_00000000-0000-0000-0000-000000000001"

    @staticmethod
    def tool_call_id(index: int) -> str:
        return f"call_00000000-0000-0000-0000-{index:012x}"

    @classmethod
    def envelope(cls, update: dict[str, object]) -> dict[str, object]:
        return {
            "type": "sessionUpdate",
            "data": {"sessionId": cls.SESSION_ID, "update": update},
        }

    @staticmethod
    def reflected_content(raw_output: dict[str, str]) -> list[dict[str, object]]:
        return [
            {
                "type": "content",
                "content": {"type": "text", "text": json.dumps(raw_output)},
            }
        ]

    @classmethod
    def read_group(cls, workspace: Path, index: int) -> list[dict[str, object]]:
        tool_call_id = cls.tool_call_id(index)
        raw_input = {
            "limit": 2000,
            "offset": 0,
            "path": permission_stream_guard.FIXTURE_INPUT_PATH,
        }
        locations = [
            {"path": str(workspace / permission_stream_guard.FIXTURE_INPUT_PATH)}
        ]
        origin = {"kiro": {"toolOrigin": "default"}}
        raw_output = {
            "message": (
                "fixture-input.txt: "
                + permission_stream_guard.FIXTURE_INPUT_TEXT.rstrip("\n")
            )
        }
        return [
            cls.envelope(
                {
                    "sessionUpdate": "tool_call",
                    "toolCallId": tool_call_id,
                    "title": "Read File",
                    "kind": "read",
                    "rawInput": raw_input,
                    "locations": locations,
                    "_meta": origin,
                }
            ),
            cls.envelope(
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": tool_call_id,
                    "status": "in_progress",
                    "rawInput": raw_input,
                    "locations": locations,
                    "_meta": origin,
                }
            ),
            cls.envelope(
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": tool_call_id,
                    "status": "completed",
                    "title": "Read File",
                    "rawInput": raw_input,
                    "rawOutput": raw_output,
                    "content": cls.reflected_content(raw_output),
                    "locations": locations,
                    "_meta": origin,
                }
            ),
        ]

    @classmethod
    def grep_group(cls, index: int) -> list[dict[str, object]]:
        tool_call_id = cls.tool_call_id(index)
        raw_input = {
            "caseSensitive": True,
            "explanation": "Find the exact sterile token.",
            "includePattern": permission_stream_guard.FIXTURE_INPUT_PATH,
            "query": permission_stream_guard.GREP_QUERY,
        }
        origin = {"kiro": {"toolOrigin": "default"}}
        raw_output = {
            "message": (
                "fixture-input.txt: "
                + permission_stream_guard.FIXTURE_INPUT_TEXT.rstrip("\n")
            )
        }
        return [
            cls.envelope(
                {
                    "sessionUpdate": "tool_call",
                    "toolCallId": tool_call_id,
                    "title": "Grep Search",
                    "kind": "search",
                    "rawInput": raw_input,
                    "_meta": origin,
                }
            ),
            cls.envelope(
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": tool_call_id,
                    "status": "in_progress",
                    "rawInput": raw_input,
                    "_meta": origin,
                }
            ),
            cls.envelope(
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": tool_call_id,
                    "status": "completed",
                    "title": "Grep Search",
                    "rawInput": raw_input,
                    "rawOutput": raw_output,
                    "content": cls.reflected_content(raw_output),
                    "_meta": origin,
                }
            ),
        ]

    @classmethod
    def write_group(
        cls,
        workspace: Path,
        index: int,
        relative_path: str,
        text: str,
        *,
        denied: bool,
        deny_patterns: list[str] | None = None,
    ) -> list[dict[str, object]]:
        tool_call_id = cls.tool_call_id(index)
        raw_input = {"path": relative_path, "text": text}
        locations = [{"path": str(workspace / relative_path)}]
        start_preview = {"file": relative_path, "modifiedContent": text}
        if denied:
            start_preview["originalContent"] = (
                f"PROTECTED_BASELINE {relative_path}\n"
            )
        start = cls.envelope(
            {
                "sessionUpdate": "tool_call",
                "toolCallId": tool_call_id,
                "status": "in_progress",
                "title": "Write File",
                "kind": "edit",
                "rawInput": raw_input,
                "locations": locations,
                "_meta": {
                    "kiro": {"toolOrigin": "default", "preview": start_preview}
                },
            }
        )
        pending = cls.envelope(
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "status": "pending",
                "rawInput": raw_input,
                "locations": locations,
                "_meta": {
                    "kiro": {
                        "toolOrigin": "default",
                        "preview": {"file": relative_path},
                    }
                },
            }
        )
        if denied:
            assert deny_patterns is not None
            policy_denial = {
                "capability": "fs_write",
                "effect": "deny",
                "matchedRule": {
                    "capability": "fs_write",
                    "effect": "deny",
                    "match": deny_patterns,
                },
                "resource": relative_path,
                "scope": "workspace",
                "source": "agent-profile",
            }
            terminal = cls.envelope(
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": tool_call_id,
                    "status": "failed",
                    "title": "Write File",
                    "rawInput": raw_input,
                    "rawOutput": {
                        "message": "Tool call denied. Source: agent-profile."
                    },
                    "content": [
                        {
                            "type": "diff",
                            "path": relative_path,
                            "oldText": "",
                            "newText": text,
                        }
                    ],
                    "locations": locations,
                    "_meta": {
                        "kiro": {
                            "toolOrigin": "default",
                            "preview": {
                                "file": relative_path,
                                "modifiedContent": text,
                                "originalContent": "",
                            },
                            "policyDenial": policy_denial,
                        }
                    },
                }
            )
            return [start, pending, terminal]

        absolute_path = str(workspace / relative_path)
        file_uri = f"file://{absolute_path}"
        snapshot = f"kiro-snapshot-v2://{cls.SESSION_ID}/{index}"
        terminal = cls.envelope(
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "status": "completed",
                "title": "Write File",
                "rawInput": raw_input,
                "rawOutput": {"message": "File written successfully."},
                "content": [
                    {
                        "type": "diff",
                        "path": file_uri,
                        "oldText": "",
                        "newText": text,
                    }
                ],
                "locations": locations,
                "_meta": {
                    "kiro": {
                        "toolOrigin": "default",
                        "preview": {
                            "file": absolute_path,
                            "local": file_uri,
                            "modified": snapshot,
                            "modifiedContent": text,
                            "originalContent": "",
                        },
                        "checkpoint": {"local": file_uri, "modified": snapshot},
                    }
                },
            }
        )
        return [start, pending, terminal]

    @classmethod
    def complete_events(
        cls, workspace: Path, *, denied_resource: str | None = None
    ) -> list[dict[str, object]]:
        events: list[dict[str, object]] = [
            {
                "type": "runStarted",
                "data": {
                    "payloadSchema": "acp",
                    "acpProtocolVersion": 1,
                    "engine": "v3",
                },
            }
        ]
        selection = cls.selection_event(str(workspace))
        selection["data"]["sessionId"] = cls.SESSION_ID  # type: ignore[index]
        events.append(selection)
        if denied_resource is not None:
            fixture = json.loads(
                (ROOT / ".github/fixtures/kiro-permission-agent.json").read_text(
                    encoding="utf-8"
                )
            )
            deny_patterns = fixture["permissions"]["rules"][3]["match"]
            events.extend(
                cls.write_group(
                    workspace,
                    1,
                    denied_resource,
                    permission_stream_guard.DENIED_WRITE_TEXT,
                    denied=True,
                    deny_patterns=deny_patterns,
                )
            )
            used_tools = ["fs_write"]
        else:
            events.extend(cls.read_group(workspace, 1))
            events.extend(cls.grep_group(2))
            for index, (relative_path, text) in enumerate(
                permission_stream_guard.ALLOWED_WRITES, start=3
            ):
                events.extend(
                    cls.write_group(
                        workspace,
                        index,
                        relative_path,
                        text,
                        denied=False,
                    )
                )
            used_tools = [
                "read_file",
                "grep_search",
                *("fs_write" for _ in permission_stream_guard.ALLOWED_WRITES),
            ]
        request_ids = [
            f"00000000-0000-0000-0001-{index:012x}"
            for index in range(len(used_tools) + 1)
        ]
        events.append(
            cls.envelope(
                {
                    "sessionUpdate": "session_info_update",
                    "_meta": {
                        "kiro": {
                            "kind": "turn_completion",
                            "status": "success",
                            "elapsedTime": 1,
                            "requestIds": request_ids,
                            "promptTurnSummaries": [
                                {
                                    "unit": "credit",
                                    "unitPlural": "credits",
                                    "usage": 0.25,
                                    "usedTools": used_tools,
                                }
                            ],
                        }
                    },
                }
            )
        )
        events.append(
            {
                "type": "runFinished",
                "data": {
                    "sessionId": cls.SESSION_ID,
                    "status": "success",
                    "stopReason": "end_turn",
                    "finalText": "",
                    "finalTextTruncated": False,
                },
            }
        )
        return events

    @staticmethod
    def write_stream(path: Path, events: list[dict[str, object]]) -> None:
        path.write_text(
            "".join(f"{json.dumps(event, separators=(',', ':'))}\n" for event in events),
            encoding="utf-8",
        )
        path.chmod(0o600)

    @staticmethod
    def fixture_workspace(temporary: str) -> tuple[Path, Path, Path, Path]:
        root = Path(temporary)
        workspace = root / "workspace"
        agent = workspace / ".kiro/agents/pk-stack-permission-fixture.json"
        agent.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / ".github/fixtures/kiro-permission-agent.json", agent)
        stream = root / "stream.jsonl"
        stderr = root / "stderr.log"
        stderr.write_text("", encoding="utf-8")
        stderr.chmod(0o600)
        return workspace, agent, stream, stderr

    def test_real_shape_allowed_and_isolated_denied_streams_validate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, agent, stream, stderr = self.fixture_workspace(temporary)
            allowed_events = self.complete_events(workspace)
            self.write_stream(stream, allowed_events)
            allowed = permission_stream_guard.validate_allowed_invocation(
                stream,
                stderr,
                return_code=124,
                api_key="test-secret",
                workspace=workspace,
            )
            self.assertEqual(allowed["user_tool_calls"], 9)
            self.assertEqual(allowed["credit_usage"], 0.25)

            without_explanation = self.complete_events(workspace)
            for event in without_explanation[5:8]:
                event["data"]["update"]["rawInput"].pop(  # type: ignore[index]
                    "explanation", None
                )
            self.write_stream(stream, without_explanation)
            optional_explanation = permission_stream_guard.validate_allowed_invocation(
                stream,
                stderr,
                return_code=0,
                api_key="test-secret",
                workspace=workspace,
            )
            self.assertEqual(optional_explanation["user_tool_calls"], 9)

            resource = permission_stream_guard.DENIED_RESOURCES[0]
            denied_events = self.complete_events(workspace, denied_resource=resource)
            self.write_stream(stream, denied_events)
            denied = permission_stream_guard.validate_denied_invocation(
                stream,
                stderr,
                return_code=0,
                api_key="test-secret",
                workspace=workspace,
                agent_path=agent,
                resource=resource,
            )
            self.assertEqual(denied["user_tool_calls"], 1)
            self.assertEqual(denied["resource"], resource)

    @staticmethod
    def read_start_diagnostic_from_error(
        error: permission_stream_guard.StreamError,
    ) -> dict[str, object]:
        marker = "read_start_diagnostic="
        message = str(error)
        if marker not in message:
            raise AssertionError("read-start diagnostic is missing")
        return json.loads(message.split(marker, 1)[1])

    def test_read_start_diagnostic_is_bounded_and_never_echoes_values(self) -> None:
        sensitive = "SENSITIVE-RAW-VALUE-MUST-NEVER-APPEAR"
        opaque_tool_id = "call_deadbeef-dead-beef-dead-deadbeefdead"
        with tempfile.TemporaryDirectory() as temporary:
            workspace, _, stream, stderr = self.fixture_workspace(temporary)
            events = self.complete_events(workspace)
            for event in events[2:5]:
                event["data"]["update"]["toolCallId"] = opaque_tool_id  # type: ignore[index]
            read_start = events[2]["data"]["update"]  # type: ignore[index]
            read_start["title"] = sensitive
            read_start["kind"] = sensitive
            read_start["rawInput"]["path"] = sensitive  # type: ignore[index]
            read_start["rawInput"]["offset"] = 424242  # type: ignore[index]
            read_start["rawInput"][sensitive] = sensitive  # type: ignore[index]
            read_start["locations"] = [{"path": sensitive, sensitive: sensitive}]
            self.write_stream(stream, events)

            with self.assertRaises(permission_stream_guard.StreamError) as caught:
                permission_stream_guard.validate_allowed_invocation(
                    stream,
                    stderr,
                    return_code=124,
                    api_key="test-secret",
                    workspace=workspace,
                )
            message = str(caught.exception)
            for forbidden in (
                sensitive,
                "424242",
                str(workspace),
                opaque_tool_id,
                self.SESSION_ID,
            ):
                self.assertNotIn(forbidden, message)
            self.assertLessEqual(
                len(message.encode("utf-8")),
                permission_stream_guard.MAX_READ_START_DIAGNOSTIC_BYTES + 256,
            )
            diagnostic = self.read_start_diagnostic_from_error(caught.exception)
            self.assertEqual(
                diagnostic["schema"],
                "pk-stack-permission-read-start-diagnostic-v1",
            )
            start = diagnostic["start"]  # type: ignore[assignment]
            self.assertFalse(start["kind"]["matches_expected"])  # type: ignore[index]
            self.assertFalse(start["title"]["matches_expected"])  # type: ignore[index]
            self.assertEqual(
                start["raw_input"]["path"]["classification"],  # type: ignore[index]
                "other_string",
            )
            self.assertEqual(start["raw_input"]["unexpected_key_count"], 1)  # type: ignore[index]
            self.assertEqual(
                start["raw_input"]["offset"]["classification"],  # type: ignore[index]
                "other_positive_integer",
            )
            self.assertFalse(start["locations"]["matches_expected"])  # type: ignore[index]
            self.assertEqual(
                start["locations"]["first_path"]["classification"],  # type: ignore[index]
                "other_string",
            )
            expected_classes = {
                permission_stream_guard.FIXTURE_INPUT_PATH: "exact_relative",
                f"./{permission_stream_guard.FIXTURE_INPUT_PATH}": "dot_relative",
                str(workspace / permission_stream_guard.FIXTURE_INPUT_PATH): (
                    "exact_workspace_absolute"
                ),
                f"file://{workspace / permission_stream_guard.FIXTURE_INPUT_PATH}": (
                    "exact_workspace_file_uri"
                ),
            }
            for value, expected in expected_classes.items():
                self.assertEqual(
                    permission_stream_guard._diagnostic_path(
                        value, workspace=workspace
                    )["classification"],
                    expected,
                )

    def test_grep_input_diagnostic_is_bounded_and_never_echoes_values(self) -> None:
        sensitive = "SENSITIVE-GREP-VALUE-MUST-NEVER-APPEAR"
        opaque_tool_id = "call_feedface-feed-face-feed-feedfacefeed"
        with tempfile.TemporaryDirectory() as temporary:
            workspace, _, stream, stderr = self.fixture_workspace(temporary)
            events = self.complete_events(workspace)
            for event in events[5:8]:
                event["data"]["update"]["toolCallId"] = opaque_tool_id  # type: ignore[index]
            raw_input = events[5]["data"]["update"]["rawInput"]  # type: ignore[index]
            raw_input.pop("explanation")
            raw_input["caseSensitive"] = sensitive
            raw_input["includePattern"] = sensitive
            raw_input["query"] = sensitive
            raw_input[sensitive] = sensitive
            self.write_stream(stream, events)

            with self.assertRaises(permission_stream_guard.StreamError) as caught:
                permission_stream_guard.validate_allowed_invocation(
                    stream,
                    stderr,
                    return_code=124,
                    api_key="test-secret",
                    workspace=workspace,
                )
            message = str(caught.exception)
            for forbidden in (
                sensitive,
                "test-secret",
                str(workspace),
                opaque_tool_id,
                self.SESSION_ID,
            ):
                self.assertNotIn(forbidden, message)
            self.assertLessEqual(
                len(message.encode("utf-8")),
                permission_stream_guard.MAX_GREP_INPUT_DIAGNOSTIC_BYTES + 256,
            )
            diagnostic = json.loads(message.split("grep_input_diagnostic=", 1)[1])
            self.assertEqual(
                diagnostic["schema"],
                "pk-stack-permission-grep-input-diagnostic-v1",
            )
            facts = diagnostic["raw_input"]
            self.assertEqual(facts["key_count"], 4)
            self.assertFalse(facts["expected_keys_present"]["explanation"])
            self.assertEqual(facts["unexpected_key_count"], 1)
            self.assertFalse(facts["case_sensitive"]["matches_expected"])
            self.assertEqual(facts["case_sensitive"]["type"], "string")
            self.assertTrue(facts["explanation"]["matches_validator_contract"])
            self.assertEqual(facts["explanation"]["type"], "null")
            self.assertEqual(
                facts["include_pattern"]["classification"], "other_string"
            )
            self.assertFalse(facts["query"]["matches_expected"])
            self.assertEqual(facts["query"]["type"], "string")

    def test_denied_stream_rejects_policy_and_lifecycle_lookalikes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, agent, stream, stderr = self.fixture_workspace(temporary)
            resource = permission_stream_guard.DENIED_RESOURCES[0]
            baseline = self.complete_events(workspace, denied_resource=resource)

            def clone() -> list[dict[str, object]]:
                return json.loads(json.dumps(baseline))

            malformed_streams: list[list[dict[str, object]]] = []
            for mutation in ("missing", "extra", "resource", "rule"):
                events = clone()
                terminal = events[-3]["data"]["update"]  # type: ignore[index]
                denial = terminal["_meta"]["kiro"]["policyDenial"]  # type: ignore[index]
                if mutation == "missing":
                    denial.pop("matchedRule")
                elif mutation == "extra":
                    denial["unexpected"] = True
                elif mutation == "resource":
                    denial["resource"] = permission_stream_guard.DENIED_RESOURCES[1]
                else:
                    denial["matchedRule"]["match"] = [resource]
                malformed_streams.append(events)

            mismatched_id = clone()
            mismatched_id[-3]["data"]["update"]["toolCallId"] = self.tool_call_id(9)  # type: ignore[index]
            malformed_streams.append(mismatched_id)
            late_selection = clone()
            late_selection.insert(-2, late_selection[1])
            malformed_streams.append(late_selection)
            unknown_update = clone()
            unknown_update.insert(
                -1,
                self.envelope({"sessionUpdate": "command_execution", "status": "done"}),
            )
            malformed_streams.append(unknown_update)
            extra_tool = clone()
            extra_tool[-2:-2] = self.write_group(
                workspace,
                2,
                resource,
                permission_stream_guard.DENIED_WRITE_TEXT,
                denied=True,
                deny_patterns=json.loads(agent.read_text(encoding="utf-8"))["permissions"]
                ["rules"][3]["match"],
            )
            malformed_streams.append(extra_tool)

            for events in malformed_streams:
                with self.subTest(events=events), self.assertRaises(
                    permission_stream_guard.StreamError
                ):
                    self.write_stream(stream, events)
                    permission_stream_guard.validate_denied_invocation(
                        stream,
                        stderr,
                        return_code=124,
                        api_key="test-secret",
                        workspace=workspace,
                        agent_path=agent,
                        resource=resource,
                    )

    def test_allowed_stream_rejects_missing_reordered_or_denied_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, _, stream, stderr = self.fixture_workspace(temporary)
            baseline = self.complete_events(workspace)

            def clone() -> list[dict[str, object]]:
                return json.loads(json.dumps(baseline))

            missing_write = clone()
            missing_id = self.tool_call_id(9)
            missing_write[:] = [
                event
                for event in missing_write
                if event.get("data", {}).get("update", {}).get("toolCallId") != missing_id  # type: ignore[union-attr]
            ]
            wrong_order = clone()
            first_write = next(
                event
                for event in wrong_order
                if event.get("data", {}).get("update", {}).get("toolCallId")  # type: ignore[union-attr]
                == self.tool_call_id(3)
            )
            first_write["data"]["update"]["rawInput"]["path"] = "wrong.txt"  # type: ignore[index]
            wrong_used_tools = clone()
            wrong_used_tools[-2]["data"]["update"]["_meta"]["kiro"][  # type: ignore[index]
                "promptTurnSummaries"
            ][0]["usedTools"].append("execute_bash")
            hidden_denial = clone()
            hidden_denial.insert(
                -1,
                self.envelope(
                    {
                        "sessionUpdate": "session_info_update",
                        "_meta": {"kiro": {"policyDenial": {"effect": "deny"}}},
                    }
                ),
            )
            nonempty_final = clone()
            nonempty_final[-1]["data"]["finalText"] = "done"  # type: ignore[index]

            for events in (
                missing_write,
                wrong_order,
                wrong_used_tools,
                hidden_denial,
                nonempty_final,
            ):
                with self.subTest(events=events), self.assertRaises(
                    permission_stream_guard.StreamError
                ):
                    self.write_stream(stream, events)
                    permission_stream_guard.validate_allowed_invocation(
                        stream,
                        stderr,
                        return_code=124,
                        api_key="test-secret",
                        workspace=workspace,
                    )

    def test_invocation_bounds_fallback_and_secret_checks_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace, agent, stream, stderr = self.fixture_workspace(temporary)
            resource = permission_stream_guard.DENIED_RESOURCES[0]
            events = self.complete_events(workspace, denied_resource=resource)
            self.write_stream(stream, events)
            common = {
                "stream_path": stream,
                "stderr_path": stderr,
                "api_key": "test-secret",
                "workspace": workspace,
                "agent_path": agent,
                "resource": resource,
            }
            with self.assertRaises(permission_stream_guard.StreamError):
                permission_stream_guard.validate_denied_invocation(
                    return_code=1, **common
                )
            stream.chmod(0o644)
            with self.assertRaises(permission_stream_guard.StreamError):
                permission_stream_guard.validate_denied_invocation(
                    return_code=0, **common
                )
            stream.chmod(0o600)
            stderr.write_text('not found, using "default"', encoding="utf-8")
            with self.assertRaises(permission_stream_guard.StreamError):
                permission_stream_guard.validate_denied_invocation(
                    return_code=0, **common
                )
            stderr.write_text("test-secret", encoding="utf-8")
            with self.assertRaises(permission_stream_guard.StreamError):
                permission_stream_guard.validate_denied_invocation(
                    return_code=0, **common
                )
            stderr.write_text("", encoding="utf-8")
            with self.assertRaises(permission_stream_guard.StreamError):
                permission_stream_guard.validate_denied_invocation(
                    return_code=0,
                    **(common | {"resource": "unapproved/protected.txt"}),
                )


class GitControlBoundaryTests(unittest.TestCase):
    @staticmethod
    def make_repo(sandbox: Path) -> tuple[Path, str]:
        root = sandbox / "repo"
        (root / ".kiro/agents").mkdir(parents=True)
        (root / ".kiro/agents/base.json").write_text("{}\n", encoding="utf-8")
        (root / "README.md").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=PK-Stack Test",
                "-c",
                "user.email=pk-stack@example.invalid",
                "commit",
                "-qm",
                "base",
            ],
            cwd=root,
            check=True,
        )
        base_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        return root, base_sha

    @staticmethod
    def record_model_boundary(root: Path, base_sha: str, state_root: Path) -> None:
        shutil.rmtree(root / ".kiro")
        guard._record_git_state(root, base_sha, state_root)

    def test_close_refuses_all_model_visible_git_control_changes_before_git(self) -> None:
        _, policy = guard.load_policy(ROOT / ".github/pk-stack-maintenance-policy.json")

        def mutate_config(root: Path) -> None:
            with (root / ".git/config").open("a", encoding="utf-8") as stream:
                stream.write("\n[core]\n\tfsmonitor = planted\n")

        def mutate_replace_ref(root: Path) -> None:
            replacement = root / ".git/refs/replace" / ("a" * 40)
            replacement.parent.mkdir()
            replacement.write_text(f"{'b' * 40}\n", encoding="ascii")

        mutations = {
            "config": mutate_config,
            "hooks": lambda root: (root / ".git/hooks/post-index-change").write_text(
                "#!/bin/sh\nexit 0\n", encoding="utf-8"
            ),
            "info": lambda root: (root / ".git/info/planted").write_text(
                "planted\n", encoding="utf-8"
            ),
            "index": lambda root: (root / ".git/index").write_bytes(
                (root / ".git/index").read_bytes() + b"planted"
            ),
            "HEAD": lambda root: (root / ".git/HEAD").write_text(f"{'a' * 40}\n", encoding="ascii"),
            "replacement-ref": mutate_replace_ref,
            "packed-refs": lambda root: (root / ".git/packed-refs").write_text(
                f"{'a' * 40} refs/replace/{'b' * 40}\n", encoding="ascii"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                sandbox = Path(temporary)
                root, base_sha = self.make_repo(sandbox)
                state_root = sandbox / "git-state"
                self.record_model_boundary(root, base_sha, state_root)
                try:
                    mutate(root)
                    with mock.patch.object(
                        guard,
                        "_git_run",
                        side_effect=AssertionError("Git ran before control-state rejection"),
                    ) as git_run:
                        with self.assertRaisesRegex(guard.GuardError, "Git control metadata"):
                            guard.close_attempt(root, base_sha, policy, state_root)
                        git_run.assert_not_called()
                finally:
                    guard._remove_git_state(root, state_root)

    def test_close_rejects_skip_worktree_and_assume_unchanged_index_attacks(self) -> None:
        _, policy = guard.load_policy(ROOT / ".github/pk-stack-maintenance-policy.json")
        for flag in ("--skip-worktree", "--assume-unchanged"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as temporary:
                sandbox = Path(temporary)
                root, base_sha = self.make_repo(sandbox)
                state_root = sandbox / "git-state"
                self.record_model_boundary(root, base_sha, state_root)
                subprocess.run(["git", "update-index", flag, "README.md"], cwd=root, check=True)
                (root / "README.md").write_text("protected mutation\n", encoding="utf-8")
                with mock.patch.object(
                    guard,
                    "_git_run",
                    side_effect=AssertionError("Git ran before index-state rejection"),
                ) as git_run:
                    with self.assertRaisesRegex(guard.GuardError, "Git control metadata"):
                        guard.close_attempt(root, base_sha, policy, state_root)
                    git_run.assert_not_called()
                guard._remove_git_state(root, state_root)

    def test_trusted_git_disables_repo_and_ambient_executable_config(self) -> None:
        _, policy = guard.load_policy(ROOT / ".github/pk-stack-maintenance-policy.json")
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            root, base_sha = self.make_repo(sandbox)
            tripwire = root / ".git/hooks/post-index-change"
            tripwire.write_text(
                "#!/bin/sh\nprintf executed >.git/pk-stack-tripwire-executed\nexit 1\n",
                encoding="utf-8",
            )
            tripwire.chmod(0o700)
            subprocess.run(["git", "config", "core.hooksPath", "hooks"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "core.fsmonitor", ".git/hooks/post-index-change"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "diff.external", ".git/hooks/post-index-change"],
                cwd=root,
                check=True,
            )
            global_config = sandbox / "hostile-global-config"
            global_config.write_text(
                "[core]\n\thooksPath = hooks\n\tfsmonitor = .git/hooks/post-index-change\n"
                "[diff]\n\texternal = .git/hooks/post-index-change\n",
                encoding="utf-8",
            )
            state_root = sandbox / "git-state"
            self.record_model_boundary(root, base_sha, state_root)
            recorded = guard._read_git_state(root, base_sha, state_root)["snapshot"]
            self.assertEqual(
                recorded["targets"]["config"]["sha256"],
                hashlib.sha256((root / ".git/config").read_bytes()).hexdigest(),
            )
            self.assertEqual(recorded["targets"]["config.worktree"], {"kind": "absent"})
            for target in ("hooks", "info", "refs"):
                self.assertEqual(recorded["targets"][target]["kind"], "directory")
                for entry in recorded["targets"][target]["entries"]:
                    if entry["entry"]["kind"] == "file":
                        self.assertRegex(entry["entry"]["sha256"], r"^[0-9a-f]{64}$")
            hostile_environment = {
                "GIT_CONFIG_GLOBAL": str(global_config),
                "GIT_CONFIG_SYSTEM": str(global_config),
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.hooksPath",
                "GIT_CONFIG_VALUE_0": "hooks",
                "GIT_EXTERNAL_DIFF": str(tripwire),
            }
            with mock.patch.dict(os.environ, hostile_environment, clear=False):
                guard.close_attempt(root, base_sha, policy, state_root)
            self.assertFalse((root / ".git/pk-stack-tripwire-executed").exists())
            self.assertTrue(state_root.exists())
            guard._read_git_state(root, base_sha, state_root, phase="open")
            guard.finalize_git_state(root, base_sha, state_root)
            self.assertFalse(state_root.exists())
            self.assertTrue((root / ".kiro/agents/base.json").is_file())

    def test_external_finalizer_blocks_clean_filter_and_textconv_execution(self) -> None:
        _, policy = guard.load_policy(ROOT / ".github/pk-stack-maintenance-policy.json")
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            root, _ = self.make_repo(sandbox)
            target = root / "powers/pk-stack/README.md"
            target.parent.mkdir(parents=True)
            target.write_text("base\n", encoding="utf-8")
            (root / ".gitattributes").write_text(
                "powers/pk-stack/README.md filter=trip diff=trip\n", encoding="utf-8"
            )
            subprocess.run(
                ["git", "add", ".gitattributes", "powers/pk-stack/README.md"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=PK-Stack Test",
                    "-c",
                    "user.email=pk-stack@example.invalid",
                    "commit",
                    "-qm",
                    "attributes",
                ],
                cwd=root,
                check=True,
            )
            base_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            marker = sandbox / "filter-or-textconv-executed"
            tripwire = sandbox / "git-driver.sh"
            tripwire.write_text(
                "#!/bin/sh\n"
                f"printf '%s\\n' \"$1\" >>{shlex.quote(str(marker))}\n"
                'if [ "$1" = textconv ]; then cat "$2"; else cat; fi\n',
                encoding="utf-8",
            )
            tripwire.chmod(0o700)
            subprocess.run(
                ["git", "config", "filter.trip.clean", f"{tripwire} clean"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "diff.trip.textconv", f"{tripwire} textconv"],
                cwd=root,
                check=True,
            )

            # Prove that the planted local drivers are genuinely executable by
            # ordinary Git before testing the trusted finalizer isolation.
            target.write_text("raw hostile path\n", encoding="utf-8")
            subprocess.run(
                ["git", "diff", "--", "powers/pk-stack/README.md"],
                cwd=root,
                check=True,
                stdout=subprocess.DEVNULL,
            )
            subprocess.run(["git", "add", "powers/pk-stack/README.md"], cwd=root, check=True)
            self.assertIn("textconv", marker.read_text(encoding="utf-8"))
            self.assertIn("clean", marker.read_text(encoding="utf-8"))
            subprocess.run(
                ["git", "reset", "-q", "HEAD", "--", "powers/pk-stack/README.md"],
                cwd=root,
                check=True,
            )
            target.write_text("base\n", encoding="utf-8")
            marker.unlink()

            state_root = sandbox / "git-state"
            self.record_model_boundary(root, base_sha, state_root)
            original_index = hashlib.sha256((root / ".git/index").read_bytes()).hexdigest()
            target.write_text("candidate\n", encoding="utf-8")
            guard.close_attempt(root, base_sha, policy, state_root)
            self.assertFalse(marker.exists())
            self.assertEqual(
                hashlib.sha256((root / ".git/index").read_bytes()).hexdigest(),
                original_index,
            )
            self.assertNotEqual(
                hashlib.sha256((state_root / "index").read_bytes()).hexdigest(),
                guard._read_git_state(root, base_sha, state_root, phase="open")[
                    "trusted_index_sha256"
                ],
            )
            guard.finalize_git_state(root, base_sha, state_root)

    def test_trusted_git_wrapper_pins_config_and_no_ext_diff(self) -> None:
        completed = subprocess.CompletedProcess(args=(), returncode=0, stdout=b"", stderr=b"")
        with mock.patch.object(guard.subprocess, "run", return_value=completed) as run:
            guard._git_run(
                Path("/tmp"),
                "diff",
                "--name-only",
                env={
                    "PATH": os.environ.get("PATH", ""),
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "core.hooksPath",
                    "GIT_CONFIG_VALUE_0": "hooks",
                },
            )
        command = run.call_args.args[0]
        environment = run.call_args.kwargs["env"]
        self.assertIn("--no-ext-diff", command)
        self.assertIn("--no-textconv", command)
        for setting in (
            "core.hooksPath=/dev/null",
            "core.fsmonitor=false",
            "diff.external=",
        ):
            self.assertIn(setting, command)
        self.assertEqual(environment["GIT_CONFIG_GLOBAL"], "/dev/null")
        self.assertEqual(environment["GIT_CONFIG_SYSTEM"], "/dev/null")
        self.assertEqual(environment["GIT_CONFIG_NOSYSTEM"], "1")
        self.assertEqual(environment["GIT_EXTERNAL_DIFF"], "")
        self.assertEqual(environment["GIT_NO_REPLACE_OBJECTS"], "1")
        self.assertEqual(environment["GIT_CONFIG_VALUE_0"], "/dev/null")

    def test_git_control_snapshot_rejects_unsafe_and_racing_entries(self) -> None:
        unsafe_mutations = {
            "symlink": lambda root, sandbox: (root / ".git/hooks/unsafe").symlink_to(
                sandbox / "outside"
            ),
            "hardlink": lambda root, sandbox: os.link(
                root / ".git/config", root / ".git/hooks/unsafe"
            ),
            "oversized": lambda root, sandbox: (root / ".git/info/oversized").write_bytes(
                b"x" * (guard.GIT_CONTROL_ENTRY_MAX_BYTES + 1)
            ),
        }
        for label, mutate in unsafe_mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                sandbox = Path(temporary)
                root, base_sha = self.make_repo(sandbox)
                mutate(root, sandbox)
                with self.assertRaises(guard.GuardError):
                    guard._record_git_state(root, base_sha, sandbox / "git-state")

        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            root, base_sha = self.make_repo(sandbox)
            with self.assertRaisesRegex(guard.GuardError, "outside the model-visible checkout"):
                guard._record_git_state(root, base_sha, root / "git-state")

        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            root, _ = self.make_repo(sandbox)
            config = root / ".git/config"
            original_read = guard.os.read
            mutated = False

            def racing_read(descriptor: int, count: int) -> bytes:
                nonlocal mutated
                chunk = original_read(descriptor, count)
                if not mutated:
                    with config.open("ab") as stream:
                        stream.write(b"\n# raced\n")
                    mutated = True
                return chunk

            with (
                mock.patch.object(guard.os, "read", side_effect=racing_read),
                self.assertRaisesRegex(guard.GuardError, "changed while hashing"),
            ):
                guard._snapshot_git_controls(root)


class DetectorTests(unittest.TestCase):
    def validate(self, payload: dict[str, object]) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "detector.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return guard.validate_detector(path)

    def validate_proposal(
        self,
        detector: dict[str, object],
        proposal: dict[str, object],
        *,
        extra_pending_source_id: str | None = None,
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            detector_path = root / "detector.json"
            proposal_path = root / "proposal.json"
            ledger_path = root / "maintenance/upstream-reviews.json"
            ledger_path.parent.mkdir(parents=True)
            detector_path.write_text(json.dumps(detector), encoding="utf-8")
            proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
            ledger_path.write_text(
                json.dumps(review_ledger_fixture(detector)),
                encoding="utf-8",
            )
            selected_source_id = proposal["source_id"]
            for source in detector["sources"]:  # type: ignore[union-attr]
                provenance_path = root / source["provenance_path"]
                provenance_path.parent.mkdir(parents=True, exist_ok=True)
                markers = accepted_marker_lines(detector, source_id=source["id"])
                if source["id"] == selected_source_id:
                    markers.append(pending_marker_line(detector, source_id=source["id"]))
                if source["id"] == extra_pending_source_id:
                    markers.append(pending_marker_line(detector, source_id=source["id"]))
                provenance_path.write_text(
                    "# Provenance\n\n" + "\n".join(markers) + "\n",
                    encoding="utf-8",
                )
            return guard.validate_proposal(root, detector_path, proposal_path)

    def validate_serialized(
        self,
        before: dict[str, object],
        after: dict[str, object],
        *,
        mutate_deferred_provenance: bool = False,
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before_path = root / "before.json"
            after_path = root / "after.json"
            before_path.write_text(json.dumps(before), encoding="utf-8")
            after_path.write_text(json.dumps(after), encoding="utf-8")
            for source in before["sources"]:  # type: ignore[union-attr]
                provenance_path = root / source["provenance_path"]
                provenance_path.parent.mkdir(parents=True, exist_ok=True)
                provenance_path.write_text(
                    "# Provenance\n\n"
                    + "\n".join(accepted_marker_lines(before, source_id=source["id"]))
                    + "\n",
                    encoding="utf-8",
                )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=PK-Stack Test",
                    "-c",
                    "user.email=pk-stack@example.invalid",
                    "commit",
                    "-qm",
                    "before serialized acceptance",
                ],
                cwd=root,
                check=True,
            )
            base_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            ledger_path = root / "maintenance/upstream-reviews.json"
            ledger_path.parent.mkdir(parents=True)
            ledger_path.write_text(
                json.dumps(review_ledger_fixture(after)),
                encoding="utf-8",
            )
            for source in after["sources"]:  # type: ignore[union-attr]
                provenance_path = root / source["provenance_path"]
                provenance_path.parent.mkdir(parents=True, exist_ok=True)
                provenance_path.write_text(
                    "# Provenance\n\n"
                    + "\n".join(accepted_marker_lines(after, source_id=source["id"]))
                    + "\n",
                    encoding="utf-8",
                )
            if mutate_deferred_provenance:
                selected_source_id = min(
                    source["id"]
                    for source in before["sources"]  # type: ignore[union-attr]
                    if source["drift"]
                )
                deferred = next(
                    source
                    for source in after["sources"]  # type: ignore[union-attr]
                    if source["id"] != selected_source_id
                )
                with (root / deferred["provenance_path"]).open("a", encoding="utf-8") as stream:
                    stream.write("Deferred prose changed.\n")
            return guard.validate_serialized_acceptance(
                root,
                base_sha,
                before_path,
                after_path,
            )

    def test_multiple_drift_sources_are_sorted_for_serialized_selection(self) -> None:
        payload = drift_detector_fixture()
        add_detector_source(payload, source_id="alpha-okf", drift=True)

        validated = self.validate(payload)

        self.assertEqual(
            validated["validated_drift_sources"],
            [
                {"source_id": "alpha-okf", "expected_head": "5" * 40},
                {"source_id": "cursor-pstack", "expected_head": "c" * 40},
            ],
        )
        self.assertEqual(validated["validated_drift_heads"], ["5" * 40, "c" * 40])

    def test_source_ids_match_the_bounded_controller_contract(self) -> None:
        for source_id in ("-alpha", "alpha-", "alpha--okf", "Alpha", "a" * 65):
            with self.subTest(source_id=source_id):
                payload = detector_fixture()
                payload["sources"][0]["id"] = source_id  # type: ignore[index]
                with self.assertRaisesRegex(guard.GuardError, "source id is invalid"):
                    self.validate(payload)

    def test_invalid_source_parity_is_typed_and_can_trigger_parity_only_repair(self) -> None:
        payload = detector_fixture()
        source = payload["sources"][0]  # type: ignore[index]
        source["ok"] = False  # type: ignore[index]
        source["source_parity"] = {  # type: ignore[index]
            "ok": False,
            "candidate_ready": False,
            "artifact_type": "unknown",
            "status": "invalid",
            "path": source["parity_path"],  # type: ignore[index]
            "errors": ["Parity artifact is unavailable."],
            "pinned_resource_count": 0,
            "current_resource_count": 0,
            "classified_resource_count": 0,
        }
        payload["ok"] = False

        self.assertEqual(self.validate(payload)["validated_drift_sources"], [])

        source["source_parity"]["errors"] = []  # type: ignore[index]
        with self.assertRaisesRegex(guard.GuardError, "errors are not bounded"):
            self.validate(payload)

        payload = detector_fixture()
        source = payload["sources"][0]  # type: ignore[index]
        source["source_parity"]["candidate_ready"] = True  # type: ignore[index]
        source["source_parity"]["status"] = "candidate-ready"  # type: ignore[index]
        with self.assertRaisesRegex(guard.GuardError, "non-drifting upstream"):
            self.validate(payload)

    def test_proposal_must_name_lexicographically_first_drift_source(self) -> None:
        payload = drift_detector_fixture()
        add_detector_source(payload, source_id="alpha-okf", drift=True)

        selected = proposal_fixture(payload)
        self.assertEqual(selected["source_id"], "alpha-okf")
        self.assertEqual(self.validate_proposal(payload, selected)["source_id"], "alpha-okf")

        wrong = proposal_fixture(payload, source_id="cursor-pstack")
        with self.assertRaisesRegex(guard.GuardError, "lexicographically first"):
            self.validate_proposal(payload, wrong)

        with self.assertRaisesRegex(guard.GuardError, "marker count"):
            self.validate_proposal(
                payload,
                selected,
                extra_pending_source_id="cursor-pstack",
            )

    def test_serialized_acceptance_advances_only_selected_source(self) -> None:
        before = drift_detector_fixture()
        add_detector_source(before, source_id="alpha-okf", drift=True)
        after = accepted_detector_fixture(before, selected_source_id="alpha-okf")

        result = self.validate_serialized(before, after)

        self.assertEqual(result["source_id"], "alpha-okf")
        self.assertEqual(result["initial_drift_count"], 2)
        self.assertEqual(result["remaining_drift_count"], 1)

        after["sources"][0]["source_parity"]["pinned_resource_count"] = 2  # type: ignore[index]
        with self.assertRaisesRegex(guard.GuardError, "deferred upstream source"):
            self.validate_serialized(before, after)

        after = accepted_detector_fixture(before, selected_source_id="alpha-okf")
        with self.assertRaisesRegex(guard.GuardError, "modified deferred upstream provenance"):
            self.validate_serialized(
                before,
                after,
                mutate_deferred_provenance=True,
            )

    def test_serialized_acceptance_binds_latest_transition_to_selected_inventory(self) -> None:
        before = drift_detector_fixture()
        add_detector_source(before, source_id="alpha-okf", drift=True)
        after = accepted_detector_fixture(before, selected_source_id="alpha-okf")
        selected = next(
            source
            for source in after["sources"]
            if source["id"] == "alpha-okf"  # type: ignore[index]
        )
        selected["review_reproof"]["transitions"][0]["inventory_sha256"] = "f" * 64

        with self.assertRaisesRegex(guard.GuardError, "not detector-bound"):
            self.validate_serialized(before, after)

    def test_zero_one_and_multi_transition_reproof_shapes(self) -> None:
        for count in (0, 1, 7, 33, guard.REVIEW_TRANSITION_MAX):
            validated = self.validate(detector_fixture(transition_count=count))
            self.assertEqual(validated["validated_drift_heads"], [])

        with self.assertRaises(guard.GuardError):
            self.validate(detector_fixture(transition_count=guard.REVIEW_TRANSITION_MAX + 1))

    def test_arbitrary_ok_false_and_typed_boolean_are_rejected(self) -> None:
        payload = detector_fixture()
        payload.pop("sources")
        payload["ok"] = False
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

        payload = detector_fixture()
        payload["sources"][0]["drift"] = 1  # type: ignore[index]
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_inventory_counts_must_be_exact(self) -> None:
        payload = detector_fixture()
        payload["sources"][0]["comparison"]["path_count"] = 1  # type: ignore[index]
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_cross_boundary_rename_out_is_the_only_unverified_tree_sha(self) -> None:
        payload = drift_detector_fixture()
        rename_out = comparison_file_fixture(
            path=None,
            previous_path="old.md",
            status="renamed",
            tree_sha_verified=False,
        )
        set_comparison_files(payload, [rename_out])
        self.assertEqual(self.validate(payload)["validated_drift_heads"], ["c" * 40])

        rename_out["status"] = "removed"
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_rename_in_and_copy_require_verified_current_tree_sha(self) -> None:
        for file in (
            comparison_file_fixture(
                path="new.md",
                previous_path=None,
                status="renamed",
                tree_sha_verified=True,
            ),
            comparison_file_fixture(
                path="copied.md",
                previous_path=None,
                status="copied",
                tree_sha_verified=True,
            ),
        ):
            payload = drift_detector_fixture()
            set_comparison_files(payload, [file])
            self.validate(payload)
            file["tree_sha_verified"] = False
            with self.assertRaises(guard.GuardError):
                self.validate(payload)

    def test_comparison_may_omit_changes_wholly_outside_source_subtree(self) -> None:
        payload = drift_detector_fixture()
        set_comparison_files(payload, [])
        source = payload["sources"][0]  # type: ignore[index]
        source["current"]["subtree_sha"] = source["pinned"]["subtree_sha"]  # type: ignore[index]
        self.assertEqual(self.validate(payload)["validated_drift_heads"], ["c" * 40])

    def test_patch_body_and_review_constraints_are_recomputed(self) -> None:
        payload = drift_detector_fixture()
        self.validate(payload)

        file = payload["sources"][0]["comparison"]["files"][0]  # type: ignore[index]
        file["patch"] = "@@ -0,0 +1 @@\n+new\n+hidden"  # type: ignore[index]
        file["patch_bytes"] = len(file["patch"].encode("utf-8"))  # type: ignore[index,union-attr]
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_exact_blob_identities_modes_and_inventory_are_independently_bound(self) -> None:
        payload = drift_detector_fixture()
        file = payload["sources"][0]["comparison"]["files"][0]  # type: ignore[index]
        file["new_identity"]["mode"] = "100755"  # type: ignore[index]
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

        for entry_type, mode in (("commit", "160000"), ("blob", "120000")):
            payload = drift_detector_fixture()
            file = payload["sources"][0]["comparison"]["files"][0]  # type: ignore[index]
            file["new_identity"].update(type=entry_type, mode=mode)  # type: ignore[index]
            set_comparison_files(payload, [file])
            with self.assertRaises(guard.GuardError):
                self.validate(payload)

    def test_exact_blob_rename_and_mode_only_changes_are_reviewable(self) -> None:
        rename = comparison_file_fixture(
            path="new.md",
            previous_path="old.md",
            status="renamed",
            tree_sha_verified=True,
        )
        rename.update(
            additions=0,
            deletions=0,
            changes=0,
            patch=None,
            patch_bytes=0,
            no_patch=True,
            content_class="exact-blob-identity",
            reviewability="exact-blob-pure-rename",
            old_identity=tree_identity("e" * 40),
            new_identity=tree_identity("e" * 40),
        )
        payload = drift_detector_fixture()
        set_comparison_files(payload, [rename])
        self.validate(payload)

        mode_change = comparison_file_fixture(
            path="script.md",
            previous_path=None,
            status="modified",
            tree_sha_verified=True,
        )
        mode_change.update(
            additions=0,
            deletions=0,
            changes=0,
            patch=None,
            patch_bytes=0,
            no_patch=True,
            content_class="exact-blob-identity",
            reviewability="exact-blob-mode-change",
            old_identity=tree_identity("e" * 40, mode="100644"),
            new_identity=tree_identity("e" * 40, mode="100755"),
        )
        payload = drift_detector_fixture()
        set_comparison_files(payload, [mode_change])
        self.validate(payload)

        mode_change["new_identity"]["mode"] = "100644"  # type: ignore[index]
        set_comparison_files(payload, [mode_change])
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

        payload = drift_detector_fixture()
        payload["sources"][0]["comparison"]["review_constraints"][  # type: ignore[index]
            "unavailable_binary_paths"
        ] = ["README.md"]
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_unavailable_image_requires_disposition_b(self) -> None:
        payload = drift_detector_fixture()
        unavailable = {
            "path": "assets/logo.png",
            "previous_path": None,
            "status": "added",
            "sha": "e" * 40,
            "additions": 0,
            "deletions": 0,
            "changes": 0,
            "patch": None,
            "patch_bytes": 0,
            "no_patch": True,
            "content_class": "binary-or-patch-unavailable",
            "reviewability": "unavailable-nonsemantic-image",
            "old_identity": None,
            "new_identity": tree_identity("e" * 40),
            "tree_sha_verified": True,
        }
        set_comparison_files(payload, [unavailable])
        self.validate(payload)
        proposal = proposal_fixture(payload)
        self.assertEqual(self.validate_proposal(payload, proposal)["disposition_count"], 1)

        proposal["dispositions"][0]["disposition"] = "A"  # type: ignore[index]
        with self.assertRaises(guard.GuardError):
            self.validate_proposal(payload, proposal)

        unavailable["path"] = "skills/evil.png"
        set_comparison_files(payload, [unavailable])
        with self.assertRaises(guard.GuardError):
            self.validate(payload)

    def test_retry_cleanup_preserves_accepted_marker_prefix_and_authored_prose(self) -> None:
        payload = drift_detector_fixture(transition_count=1)
        accepted = accepted_marker_lines(payload)
        self.assertEqual(len(accepted), 1)
        pending = pending_marker_line(payload)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ledger = root / "maintenance/upstream-reviews.json"
            provenance = root / "powers/pk-stack/docs/provenance.md"
            detector_path = root / "detector.json"
            ledger.parent.mkdir(parents=True)
            provenance.parent.mkdir(parents=True)
            ledger.write_text(json.dumps(review_ledger_fixture(payload)), encoding="utf-8")
            detector_path.write_text(json.dumps(payload), encoding="utf-8")
            validated_detector = guard.validate_detector(detector_path)
            provenance.write_text(
                "# Provenance\n\n"
                f"{accepted[0]}\n\n"
                "Authored reconciliation detail before the retry marker.\n\n"
                f"{pending}\n\n"
                "Authored reconciliation detail after the retry marker.\n",
                encoding="utf-8",
            )

            guard._cleanup_unaccepted_provenance_tail(root, validated_detector)

            cleaned = provenance.read_text(encoding="utf-8")
            self.assertIn(accepted[0], cleaned)
            self.assertNotIn(pending, cleaned)
            self.assertIn("detail before", cleaned)
            self.assertIn("detail after", cleaned)

            provenance.write_text(
                f"# Provenance\n{accepted[0]}\n{pending}\n{pending}\n",
                encoding="utf-8",
            )
            duplicate_tail = provenance.read_bytes()
            with self.assertRaises(guard.GuardError):
                guard._cleanup_unaccepted_provenance_tail(
                    root,
                    validated_detector,
                )
            self.assertEqual(provenance.read_bytes(), duplicate_tail)

            altered_accepted = accepted[0].replace(
                f'"inventory_sha256":"{"e" * 64}"',
                f'"inventory_sha256":"{"f" * 64}"',
            )
            provenance.write_text(
                f"# Provenance\n{altered_accepted}\n{pending}\n",
                encoding="utf-8",
            )
            replaced_prefix = provenance.read_bytes()
            with self.assertRaises(guard.GuardError):
                guard._cleanup_unaccepted_provenance_tail(
                    root,
                    validated_detector,
                )
            self.assertEqual(provenance.read_bytes(), replaced_prefix)


class PolicyAndWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.policy = guard.load_policy(ROOT / ".github" / "pk-stack-maintenance-policy.json")

    def test_candidate_and_finalizer_scopes_do_not_share_oracles(self) -> None:
        agent_exact = set(self.policy["agent_allowed_exact"])
        final_exact = set(self.policy["final_allowed_exact"])
        self.assertIn(".pk-stack-maintenance/proposal.json", agent_exact)
        self.assertNotIn(".pk-stack-maintenance/proposal.json", final_exact)
        self.assertNotIn("maintenance/upstream-reviews.json", agent_exact)
        self.assertIn("maintenance/upstream-reviews.json", final_exact)
        self.assertFalse(
            guard._matches(
                "powers/pk-stack/src/pstack_kiro/upstreams.py",
                agent_exact,
                self.policy["agent_allowed_prefixes"],
            )
        )
        self.assertTrue(guard._is_protected("powers/pk-stack/tests/test_upstreams.py", self.policy))

    def test_candidate_package_has_one_exact_bounded_size_contract(self) -> None:
        self.assertEqual(
            self.policy["limits"]["max_candidate_package_bytes"],
            33_554_432,
        )
        self.assertEqual(self.policy["limits"]["max_review_ledger_bytes"], 8 * 1024 * 1024)
        self.assertEqual(self.policy["limits"]["max_review_transitions"], 512)
        source = GUARD_PATH.read_text(encoding="utf-8")
        self.assertGreaterEqual(
            source.count('policy["limits"]["max_candidate_package_bytes"]'),
            2,
        )
        self.assertNotIn('policy["limits"]["max_patch_bytes"] * 3 + 65_536', source)

    def test_ci_agent_matches_immutable_policy(self) -> None:
        guard.validate_ci_agent(
            ROOT / ".kiro" / "agents" / "pstack-maintainer.json",
            self.policy,
        )

    def test_permission_smoke_fixture_matches_production_and_policy_exactly(self) -> None:
        fixture = json.loads(
            (ROOT / ".github/fixtures/kiro-permission-agent.json").read_text(encoding="utf-8")
        )
        production = json.loads(
            (ROOT / ".kiro/agents/pstack-maintainer.json").read_text(encoding="utf-8")
        )
        authority = self.policy["ci_authority"]
        self.assertIn(".git/**", authority["deny_patterns"])
        expected_rules = [
            {"capability": "fs_read", "match": ["./**"], "effect": "allow"},
            {"capability": "grep", "match": ["./**"], "effect": "allow"},
            {
                "capability": "fs_write",
                "match": authority["write_patterns"],
                "effect": "allow",
            },
            {
                "capability": "fs_write",
                "match": authority["deny_patterns"],
                "effect": "deny",
            },
        ]
        self.assertEqual(set(fixture["permissions"]), {"rules"})
        self.assertEqual(fixture["permissions"]["rules"], expected_rules)
        self.assertEqual(fixture["permissions"], production["permissions"])
        self.assertEqual(fixture["toolsSettings"], authority["tools_settings"])
        self.assertEqual(production["toolsSettings"], fixture["toolsSettings"])

        prompt = fixture["prompt"]
        self.assertIn(
            "exactly and only the ordered filesystem operations enumerated in the current user prompt",
            prompt,
        )
        self.assertIn("Do not infer, retry, or add operations", prompt)
        self.assertIn("Emit no assistant prose before or after tool use", prompt)
        self.assertIn("including when that operation is denied", prompt)
        self.assertNotIn("continue after each expected denial", prompt)
        self.assertNotIn("all thirteen writes", prompt)
        for path in permission_stream_guard.ALLOWED_WRITES:
            self.assertNotIn(path[0], prompt)
        for path in permission_stream_guard.DENIED_RESOURCES:
            self.assertNotIn(path, prompt)

    def test_ci_agent_rejects_nonempty_v3_discovery_settings(self) -> None:
        document = json.loads(
            (ROOT / ".kiro/agents/pstack-maintainer.json").read_text(encoding="utf-8")
        )
        document["toolsSettings"] = {"shell": {"allowedCommands": ["*"]}}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "agent.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.validate_ci_agent(path, self.policy)

    def test_ci_agent_cannot_replace_prior_provenance_markers(self) -> None:
        document = json.loads(
            (ROOT / ".kiro/agents/pstack-maintainer.json").read_text(encoding="utf-8")
        )
        document["prompt"] = document["prompt"].replace(
            "preserve every prior review marker unchanged and in order",
            "replace prior review markers",
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "agent.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.validate_ci_agent(path, self.policy)

    def test_ci_agent_cannot_choose_an_ambiguous_drift_source(self) -> None:
        document = json.loads(
            (ROOT / ".kiro/agents/pstack-maintainer.json").read_text(encoding="utf-8")
        )
        required = "select the lexicographically smallest drifting source id"
        self.assertIn(required, document["prompt"])
        document["prompt"] = document["prompt"].replace(
            required,
            "select any drifting source",
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "agent.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.validate_ci_agent(path, self.policy)

    def test_operational_skill_patch_builds_mandatory_exact_fable_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "powers/pk-stack/skills/example/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("base instruction\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            commit = [
                "git",
                "-c",
                "user.name=PK-Stack Test",
                "-c",
                "user.email=pk-stack@example.invalid",
                "commit",
                "-qm",
            ]
            subprocess.run([*commit, "base"], cwd=root, check=True)
            base_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            skill.write_text("changed operational instruction\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run([*commit, "candidate"], cwd=root, check=True)
            head_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            bundle_path = root / ".git/fable-review-input.json"
            result = guard.build_fable_review_bundle(
                root,
                base_sha,
                head_sha,
                self.policy,
                bundle_path,
            )
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            self.assertEqual(bundle["paths"], ["powers/pk-stack/skills/example/SKILL.md"])
            self.assertTrue(bundle["requires_fable"])
            self.assertEqual(bundle["base_sha"], base_sha)
            self.assertEqual(bundle["head_sha"], head_sha)
            self.assertEqual(
                result["content_sha256"],
                hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
            )

    def test_goal_status_uses_attempt_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            status = Path(temporary) / "goal.json"
            status.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "goal": {
                            "goal_id": "goal",
                            "status": "passed",
                            "attempt_count": 2,
                            "max_attempts": 5,
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(guard._goal_status(status)["attempt_count"], 2)

    def test_isolated_kiro_settings_are_exact_and_never_written_via_cli(self) -> None:
        sources = {
            "maintenance setup": (
                ROOT / ".github/scripts/prepare_kiro_maintenance_runtime.sh"
            ).read_text(),
            "credential smoke": (
                ROOT / ".github/workflows/pk-stack-kiro-credential-smoke.yml"
            ).read_text(),
            "permission smoke": (
                ROOT / ".github/workflows/pk-stack-kiro-permission-smoke.yml"
            ).read_text(),
        }
        payload_pattern = re.compile(
            r"(?m)^\s*printf '%s\\n' \\\n"
            r'(?P<lines>(?:^\s*\'[^\']*\'(?: \\| >"\$settings_path")\n)+)'
        )
        for label, source in sources.items():
            with self.subTest(label=label):
                payload_match = payload_pattern.search(source)
                self.assertIsNotNone(payload_match)
                values = re.findall(
                    r'(?m)^\s*\'([^\']*)\'(?: \\| >"\$settings_path")$',
                    payload_match.group("lines"),  # type: ignore[union-attr]
                )
                payload = ("\n".join(values) + "\n").encode()
                self.assertEqual(payload, KIRO_ISOLATED_SETTINGS)
                self.assertEqual(
                    json.loads(payload),
                    {
                        "app.disableAutoupdates": True,
                        "chat.disableInheritingDefaultResources": True,
                        "telemetry.enabled": False,
                    },
                )
                self.assertIn(KIRO_ISOLATED_SETTINGS_SHA256, source)
                self.assertIn('install -m 0600 /dev/null "$settings_path"', source)
                self.assertIn("stat -c '%a'", source)
                self.assertIn("settings/mcp.json", source)
                self.assertTrue(
                    'test ! -e "$KIRO_USER_HOME/.kiro"' in source
                    or 'test ! -e "$SMOKE_ROOT/user-home/.kiro"' in source
                    or 'test ! -e "$case_root/user-home/.kiro"' in source
                )
                for key in (
                    "app.disableAutoupdates",
                    "chat.disableInheritingDefaultResources",
                    "telemetry.enabled",
                ):
                    self.assertEqual(source.count(f'"{key}"'), 1)
                    self.assertNotIn(f" settings {key} ", source)

    def test_workflow_contracts_are_statically_bound(self) -> None:
        kiro = (ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml").read_text()
        candidate = (ROOT / ".github/workflows/pk-stack-upstream-candidate.yml").read_text()
        fallback = (ROOT / ".github/workflows/pk-stack-upstream-maintenance.md").read_text()
        fallback_lock = (
            ROOT / ".github/workflows/pk-stack-upstream-maintenance.lock.yml"
        ).read_text()
        smoke = (ROOT / ".github/workflows/pk-stack-kiro-credential-smoke.yml").read_text()
        permission_smoke = (
            ROOT / ".github/workflows/pk-stack-kiro-permission-smoke.yml"
        ).read_text()
        verifier = (ROOT / ".github/scripts/verify_pk_stack_attempt.sh").read_text()
        kiro_runner = (ROOT / ".github/scripts/run_kiro_maintenance_attempt.sh").read_text()
        kiro_setup = (ROOT / ".github/scripts/prepare_kiro_maintenance_runtime.sh").read_text()
        self.assertIn("classifyOpenCandidate", kiro)
        self.assertIn("loadSourceRun:", kiro)
        self.assertIn("loadCandidateRuns:", kiro)
        self.assertIn("candidate_lifecycle.workflow_path", kiro)
        self.assertIn("nowMs: Date.now()", kiro)
        self.assertIn(".github/workflows \\", kiro)
        self.assertIn(".github/workflows \\", candidate)
        self.assertIn('decision.action === "close"', kiro)
        self.assertIn(".goal.attempt_count == 1", kiro)
        self.assertNotIn(".goal.attempt == 1", kiro)
        self.assertIn("selected_source_id=$(jq", kiro)
        self.assertIn("--source-id $selected_source_id --output json", kiro)
        self.assertIn("goal_contract=(--feature pk-stack-upstream-maintenance)", kiro)
        self.assertIn('cron: "17 13 * * *"', kiro)
        self.assertNotIn('cron: "17 13 * * 1"', kiro)
        self.assertIn(
            "preserving the canonical <!-- pk-stack-upstream-genesis: "
            "{canonical JSON} --> marker byte-for-byte",
            kiro_runner,
        )
        self.assertIn("preserving every prior marker unchanged and in order", kiro_runner)
        self.assertIn("review-ledger transition count plus one", kiro_runner)
        self.assertIn(
            "select the lexicographically smallest drifting source id",
            kiro_runner,
        )
        self.assertIn("the proposal must name that source_id", kiro_runner)
        self.assertIn(
            "leave every other drifting source unchanged for a later cadence",
            kiro_runner,
        )
        self.assertIn("When detector drift_count is zero, create no proposal", kiro_runner)
        self.assertIn("--trust-tools=fs_read,fs_write,grep", kiro_runner)
        self.assertNotIn("--trust-tools=read,grep", kiro_runner)
        self.assertIn("env -u KIRO_API_KEY python3", kiro_runner)
        self.assertIn("validate-git-state", kiro_runner)
        self.assertLess(
            kiro_runner.index("validate-git-state"),
            kiro_runner.index('validate_private_file "$stream_path" 16777216'),
        )
        self.assertIn(
            "printf 'GIT_BOUNDARY_STATE=%s\\n' \"$RUNNER_TEMP/pk-stack-git-boundary-state\"",
            kiro,
        )
        self.assertEqual(kiro.count('--git-state "$GIT_BOUNDARY_STATE"'), 5)
        self.assertEqual(verifier.count('--git-state "$GIT_BOUNDARY_STATE"'), 2)
        self.assertLess(verifier.index("close-attempt"), verifier.index("uv lock --check"))
        hardened_settings = (
            "GIT_CONFIG_NOSYSTEM=1",
            "GIT_CONFIG_GLOBAL=/dev/null",
            "GIT_CONFIG_SYSTEM=/dev/null",
            "GIT_EXTERNAL_DIFF=",
            "GIT_NO_REPLACE_OBJECTS=1",
            "core.hooksPath=/dev/null",
            "core.fsmonitor=false",
            "diff.external=",
        )
        for hardened_setting in hardened_settings:
            self.assertIn(hardened_setting, verifier)
        self.assertIn("diff --no-ext-diff --no-textconv --name-only", verifier)
        for variable in (
            "GIT_DIR",
            "GIT_COMMON_DIR",
            "GIT_WORK_TREE",
            "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        ):
            self.assertIn(f"export {variable}=", verifier)
            self.assertIn(f"export {variable}=", kiro)
        self.assertIn("finalize-git-state", verifier)
        self.assertIn("finalize-git-state", kiro)
        for hardened_setting in (
            "GIT_CONFIG_NOSYSTEM",
            "GIT_CONFIG_GLOBAL",
            "GIT_CONFIG_SYSTEM",
            "GIT_EXTERNAL_DIFF",
            "GIT_NO_REPLACE_OBJECTS",
            "core.hooksPath",
            "core.fsmonitor",
            "diff.external",
        ):
            self.assertIn(hardened_setting, kiro)
        env_i_blocks = re.findall(r"(?ms)^env -i \\\n(?P<body>.*?)(?=^  timeout )", kiro_runner)
        self.assertEqual(len(env_i_blocks), 2)
        for block in env_i_blocks:
            for setting in (
                "GIT_DIR=/dev/null",
                "GIT_CONFIG_NOSYSTEM=1",
                "GIT_CONFIG_SYSTEM=/dev/null",
                "GIT_CONFIG_GLOBAL=/dev/null",
                "GIT_EXTERNAL_DIFF=",
                "GIT_NO_REPLACE_OBJECTS=1",
            ):
                self.assertIn(setting, block)
        self.assertIn(': "${TRUSTED_ROOT:?TRUSTED_ROOT is required}"', kiro_setup)
        self.assertIn(
            'trusted_agent="$TRUSTED_ROOT/.kiro/agents/pstack-maintainer.json"',
            kiro_setup,
        )
        self.assertNotIn("install -m 0600 .kiro/agents/pstack-maintainer.json", kiro_setup)
        self.assertEqual(
            self.policy["ci_authority"]["runtime_trust_tools"],
            ["fs_read", "fs_write", "grep"],
        )
        for attempt in range(1, 5):
            preparation = re.search(
                rf"(?ms)^      - name: Prepare repair {attempt} without workspace hooks\n"
                r".*?(?=^      - name: |\Z)",
                kiro,
            )
            self.assertIsNotNone(preparation)
            preparation_step = preparation.group(0)  # type: ignore[union-attr]
            self.assertLess(
                preparation_step.index("prepare-attempt"),
                preparation_step.index('bash "$KIRO_SETUP_PATH"'),
            )
            verification = re.search(
                rf"(?ms)^      - name: Secretless verification {attempt} of 4\n"
                r".*?(?=^      - name: |\Z)",
                kiro,
            )
            self.assertIsNotNone(verification)
            self.assertIn(
                "READONLY_GITHUB_TOKEN: ${{ github.token }}",
                verification.group(0),  # type: ignore[union-attr]
            )
            repair = re.search(
                rf"(?ms)^      - name: Kiro repair {attempt} of 4\n"
                r".*?(?=^      - name: |\Z)",
                kiro,
            )
            self.assertIsNotNone(repair)
            repair_step = repair.group(0)  # type: ignore[union-attr]
            self.assertIn("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}", repair_step)
            self.assertNotIn("READONLY_GITHUB_TOKEN", repair_step)
        self.assertIn("needs.base_tests.result == 'success'", candidate)
        self.assertIn("needs.fable_review.result == 'success'", candidate)
        self.assertIn(
            "run-name: PK-Stack candidate gate for source run ${{ github.event.workflow_run.id }}",
            candidate,
        )
        self.assertIn("cleanup_failed_candidate:", candidate)
        self.assertIn("authorizeTerminalCandidateClose", candidate)
        self.assertIn("needs.merge.result != 'success'", candidate)
        self.assertIn("future scheduled maintenance may retry", candidate)
        self.assertIn(
            "anthropics/claude-code-action@8251c103ac8c1d761882c86aba1412c7f583c844",
            candidate,
        )
        self.assertIn("--model claude-fable-5-1", candidate)
        self.assertIn("--effort xhigh", candidate)
        self.assertIn(
            "https://downloads.claude.ai/claude-code-releases/2.1.258/linux-x64/claude",
            candidate,
        )
        self.assertIn(
            "704f1334ac65d3e89e1c6c1d7663293ad786a6166afdb71b5075337df630f976",
            candidate,
        )
        self.assertIn("path_to_claude_code_executable:", candidate)
        self.assertIn("downloads.claude.ai:443", candidate)
        self.assertNotIn("https://claude.ai/install.sh", candidate)
        self.assertIn("FABLE_REVIEWED_CONTENT_SHA256", candidate)
        self.assertIn("steps.fable.outputs.execution_file", candidate)
        self.assertIn("execution_evidence_sha256", candidate)
        self.assertIn("FABLE_ATTESTATION_SHA256", candidate)
        self.assertIn("powers/pk-stack/skills/", json.dumps(self.policy))
        self.assertIn("TESTED_BASE_SHA", candidate)
        self.assertLess(
            verifier.index("unset READONLY_GITHUB_TOKEN"),
            verifier.index("uv lock --check"),
        )
        self.assertIn("validate-proposal", verifier)
        self.assertIn("validate-serialized-acceptance", verifier)
        self.assertIn("(( drift_count > 0 ))", verifier)
        self.assertNotIn(
            "trusted_projectctl feature verify pk-stack-upstream-maintenance",
            verifier,
        )
        self.assertLess(
            verifier.index("validate-proposal"),
            verifier.index("trusted_projectctl_network upstream accept"),
        )
        self.assertIn("test ! -e .pk-stack-maintenance", verifier)
        self.assertNotIn("test ! -e .pstack/state/upstream-accept.lock", verifier)
        self.assertIn("workflow_dispatch:", fallback)
        self.assertNotIn("schedule:", fallback)
        self.assertIn("max-daily-ai-credits: -1", fallback)
        self.assertIn("acknowledge-diagnostic:", fallback)
        self.assertNotIn("create-pull-request:", fallback)
        self.assertIn("copilot-requests: write", fallback_lock)
        self.assertIn('"acknowledge_diagnostic"', fallback_lock)
        for permission in ("issues", "actions", "contents", "pull-requests"):
            self.assertNotRegex(fallback_lock, rf"(?m)^\s+{permission}: write$")
        self.assertIn("workflow_dispatch:", smoke)
        self.assertNotIn("schedule:", smoke)
        self.assertGreaterEqual(smoke.count("permissions: {}"), 2)
        self.assertNotIn("actions/checkout", smoke)
        self.assertNotIn("actions/upload-artifact", smoke)
        self.assertEqual(smoke.count("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}"), 1)
        self.assertIn("--agent pk-stack-credential-smoke", smoke)
        self.assertNotIn("--agent pstack-maintainer", smoke)
        self.assertIn("--model gpt-5.6-sol", smoke)
        self.assertIn("--effort max", smoke)
        self.assertIn("--trust-tools=", smoke)
        self.assertIn("chmod -R a-w", smoke)
        self.assertIn("if: always()", smoke)
        credential_prepare = re.search(
            r"(?ms)^      - name: Prepare checksum-pinned isolated Kiro runtime\n"
            r".*?(?=^      - name: Invoke one bounded no-tool Sol credential smoke)",
            smoke,
        )
        credential_invoke = re.search(
            r"(?ms)^      - name: Invoke one bounded no-tool Sol credential smoke\n"
            r".*?(?=^      - name: Remove every credential-smoke runtime and log)",
            smoke,
        )
        self.assertIsNotNone(credential_prepare)
        self.assertIsNotNone(credential_invoke)
        self.assertNotIn(
            "agent validate",
            credential_prepare.group(0),  # type: ignore[union-attr]
        )
        self.assertIn(
            "agent validate",
            credential_invoke.group(0),  # type: ignore[union-attr]
        )
        self.assertIn(
            'KIRO_API_KEY="$KIRO_API_KEY"',
            credential_invoke.group(0),  # type: ignore[union-attr]
        )
        self.assertIn(
            "prompt='PK-STACK-KIRO-AUTH-OK'",
            credential_invoke.group(0),  # type: ignore[union-attr]
        )
        self.assertNotIn(
            "Authentication smoke only. Invoke no tools",
            credential_invoke.group(0),  # type: ignore[union-attr]
        )
        embedded_agent = re.search(
            r"(?ms)^          CI_AGENT_BASE64: \|-\n"
            r"(?P<body>(?:^            [A-Za-z0-9+/=]+\n)+)"
            r"^        run:",
            smoke,
        )
        self.assertIsNotNone(embedded_agent)
        encoded = "".join(
            line.strip()
            for line in embedded_agent.group("body").splitlines()  # type: ignore[union-attr]
        )
        credential_agent_raw = base64.b64decode(encoded, validate=True)
        credential_agent = json.loads(credential_agent_raw)
        self.assertEqual(
            credential_agent,
            {
                "name": "pk-stack-credential-smoke",
                "description": ("Immutable CI-only tool-free PK-Stack Kiro credential smoke."),
                "prompt": (
                    "This is an authentication-only smoke. You have no tools or "
                    "resources. Reply exactly PK-STACK-KIRO-AUTH-OK and do nothing else."
                ),
                "tools": [],
                "includeMcpJson": False,
                "includePowers": False,
                "resources": [],
                "permissions": {"rules": []},
                "toolsSettings": {},
                "welcomeMessage": "Tool-free credential smoke fixture loaded.",
            },
        )
        self.assertNotEqual(
            credential_agent_raw,
            (ROOT / ".kiro/agents/pstack-maintainer.json").read_bytes(),
        )
        embedded_agent_sha = re.search(r"(?m)^          CI_AGENT_SHA256: ([0-9a-f]{64})$", smoke)
        self.assertIsNotNone(embedded_agent_sha)
        self.assertEqual(
            embedded_agent_sha.group(1),  # type: ignore[union-attr]
            hashlib.sha256(credential_agent_raw).hexdigest(),
        )
        self.assertIn(
            "$SMOKE_ROOT/workspace/.kiro/agents/pk-stack-credential-smoke.json",
            smoke,
        )
        self.assertEqual(
            smoke.count(
                "$SMOKE_ROOT/workspace/.kiro/agents/pk-stack-credential-smoke.json"
            ),
            3,
        )
        self.assertNotIn(
            "$SMOKE_ROOT/kiro-home/agents/pk-stack-credential-smoke.json",
            smoke,
        )
        self.assertNotIn(
            "$SMOKE_ROOT/user-home/.kiro/agents/pk-stack-credential-smoke.json",
            smoke,
        )
        self.assertLess(
            credential_prepare.group(0).index(  # type: ignore[union-attr]
                "$SMOKE_ROOT/workspace/.kiro/agents/pk-stack-credential-smoke.json"
            ),
            credential_prepare.group(0).index(  # type: ignore[union-attr]
                'find "$SMOKE_ROOT/workspace" -type f -print0'
            ),
        )
        self.assertLess(
            credential_prepare.group(0).index(  # type: ignore[union-attr]
                'find "$SMOKE_ROOT/workspace" -type f -print0'
            ),
            credential_prepare.group(0).index(  # type: ignore[union-attr]
                'chmod -R a-w "$SMOKE_ROOT/workspace"'
            ),
        )
        self.assertIn(
            "grep -Fq 'not found, using \"default\"' \"$stderr\"",
            credential_invoke.group(0),  # type: ignore[union-attr]
        )
        self.assertLess(
            credential_invoke.group(0).index(  # type: ignore[union-attr]
                "grep -Fq 'not found, using \"default\"'"
            ),
            credential_invoke.group(0).index(  # type: ignore[union-attr]
                "actual_workspace_sha256="
            ),
        )
        embedded_validator = re.search(
            r"(?ms)^          STREAM_VALIDATOR_BASE64: \|-\n"
            r"(?P<body>(?:^            [A-Za-z0-9+/=]+\n)+)"
            r"^          CI_AGENT_BASE64:",
            smoke,
        )
        self.assertIsNotNone(embedded_validator)
        encoded_validator = "".join(
            line.strip()
            for line in embedded_validator.group("body").splitlines()  # type: ignore[union-attr]
        )
        embedded_validator_raw = base64.b64decode(encoded_validator, validate=True)
        self.assertEqual(embedded_validator_raw, STREAM_GUARD_PATH.read_bytes())
        embedded_validator_sha = re.search(
            r"(?m)^          STREAM_VALIDATOR_SHA256: ([0-9a-f]{64})$", smoke
        )
        self.assertIsNotNone(embedded_validator_sha)
        self.assertEqual(
            embedded_validator_sha.group(1),  # type: ignore[union-attr]
            hashlib.sha256(embedded_validator_raw).hexdigest(),
        )
        self.assertIn("workflow_dispatch:", permission_smoke)
        self.assertNotIn("schedule:", permission_smoke)
        self.assertIn("permissions: {}", permission_smoke)
        self.assertIn("timeout-minutes: 20", permission_smoke)
        self.assertIn("--trust-tools=fs_read,fs_write,grep", permission_smoke)
        self.assertIn("pk-stack-permission-fixture", permission_smoke)
        self.assertIn("validate_kiro_permission_stream.py", permission_smoke)
        self.assertIn(
            "$workspace_template/.kiro/agents/pk-stack-permission-fixture.json",
            permission_smoke,
        )
        self.assertIn(
            '$workspace/.kiro/agents/pk-stack-permission-fixture.json',
            permission_smoke,
        )
        self.assertNotIn(
            "$SMOKE_ROOT/kiro-home/agents/pk-stack-permission-fixture.json",
            permission_smoke,
        )
        self.assertNotIn(
            "$SMOKE_ROOT/user-home/.kiro/agents/pk-stack-permission-fixture.json",
            permission_smoke,
        )
        self.assertIn(
            hashlib.sha256(
                (ROOT / ".github/fixtures/kiro-permission-agent.json").read_bytes()
            ).hexdigest(),
            permission_smoke,
        )
        self.assertIn(
            hashlib.sha256(PERMISSION_STREAM_GUARD_PATH.read_bytes()).hexdigest(),
            permission_smoke,
        )
        self.assertIn(
            'fixture_permissions["rules"] != expected',
            permission_smoke,
        )
        self.assertIn(
            "production_permissions != fixture_permissions",
            permission_smoke,
        )
        self.assertIn(
            'fixture.get("toolsSettings") != authority["tools_settings"]',
            permission_smoke,
        )
        self.assertIn("agent list", permission_smoke)
        self.assertIn(
            "pk-stack-permission-fixture([[:space:]]|$)",
            permission_smoke,
        )
        self.assertIn("--kind allowed", permission_smoke)
        self.assertIn("--kind denied", permission_smoke)
        self.assertIn('run_case allowed 180 allowed "$allowed_prompt"', permission_smoke)
        self.assertIn(
            "path exactly fixture-input.txt, offset exactly 0, and limit exactly 2000",
            permission_smoke,
        )
        self.assertIn(
            "include pattern exactly fixture-input.txt, query exactly ALPHA_TOKEN",
            permission_smoke,
        )
        self.assertIn(
            'run_case "$case_id" 120 denied "$denied_prompt" "$resource"',
            permission_smoke,
        )
        self.assertEqual(permission_smoke.count('"$SMOKE_ROOT/bin/kiro-cli" chat'), 1)
        self.assertIn('test ! -e "$case_root"', permission_smoke)
        self.assertIn('"$case_root/user-home"', permission_smoke)
        self.assertIn('"$case_root/kiro-home/settings"', permission_smoke)
        self.assertIn('"$case_root/runtime"', permission_smoke)
        self.assertIn('"$case_root/logs"', permission_smoke)
        self.assertIn('test ! -e "$case_root/user-home/.kiro"', permission_smoke)
        self.assertIn(
            'find "$case_root" ! -type d ! -type f -print -quit', permission_smoke
        )
        self.assertGreaterEqual(
            permission_smoke.count('find . ! -type d ! -type f -print -quit'), 3
        )
        for path, _ in permission_stream_guard.ALLOWED_WRITES:
            self.assertIn(path, permission_smoke)
        denied_block = re.search(
            r"(?ms)^          denied_resources=\(\n(?P<body>.*?)^          \)\n",
            permission_smoke,
        )
        self.assertIsNotNone(denied_block)
        denied_resources = tuple(
            line.strip()
            for line in denied_block.group("body").splitlines()  # type: ignore[union-attr]
            if line.strip()
        )
        self.assertEqual(denied_resources, permission_stream_guard.DENIED_RESOURCES)
        for path in permission_stream_guard.DENIED_RESOURCES:
            self.assertIn(path, permission_smoke)
        self.assertIn("b'not found, using \"default\"'", permission_smoke)
        self.assertIn(
            'sha256sum --check "$SMOKE_ROOT/template-baseline.sha256"',
            permission_smoke,
        )
        self.assertIn('cmp "$SMOKE_ROOT/template-files.txt"', permission_smoke)
        self.assertIn('cmp "$SMOKE_ROOT/allowed-files.txt"', permission_smoke)
        self.assertGreaterEqual(
            permission_smoke.count('"$SMOKE_ROOT/template-directories.txt"'), 3
        )
        self.assertIn('actual-directories.txt', permission_smoke)
        self.assertIn('chmod -R a-w "$GITHUB_WORKSPACE"', permission_smoke)
        self.assertNotIn("git status --porcelain=v1 --untracked-files=all", permission_smoke)
        self.assertNotIn('test -z "$(git status', permission_smoke)
        self.assertNotIn("protected/blocked.txt", permission_smoke)
        self.assertEqual(permission_smoke.count("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}"), 1)
        self.assertNotIn("actions/upload-artifact", permission_smoke)
        self.assertIn('test ! -L "$SMOKE_ROOT"', permission_smoke)
        self.assertIn('test -O "$SMOKE_ROOT"', permission_smoke)
        self.assertEqual(permission_smoke.count('rm -rf -- "$SMOKE_ROOT"'), 1)

    def test_credential_smoke_cleanup_is_exact_and_restores_owner_write(self) -> None:
        smoke = (ROOT / ".github/workflows/pk-stack-kiro-credential-smoke.yml").read_text()
        cleanup_marker = "      - name: Remove every credential-smoke runtime and log\n"
        self.assertEqual(smoke.count(cleanup_marker), 1)
        cleanup_step = smoke.split(cleanup_marker, maxsplit=1)[1]
        run_marker = "        run: |\n"
        self.assertEqual(cleanup_step.count(run_marker), 1)
        indented_script = cleanup_step.split(run_marker, maxsplit=1)[1]
        script_lines = indented_script.splitlines(keepends=True)
        self.assertTrue(
            all(not line.strip() or line.startswith("          ") for line in script_lines)
        )
        cleanup_script = "".join(line[10:] if line.strip() else line for line in script_lines)

        self.assertIn('"$RUNNER_TEMP"/pk-stack-kiro-credential-smoke) ;;', cleanup_script)
        self.assertIn('test ! -L "$SMOKE_ROOT"', cleanup_script)
        self.assertIn('test -O "$SMOKE_ROOT"', cleanup_script)
        self.assertEqual(cleanup_script.count('rm -rf -- "$SMOKE_ROOT"'), 1)
        self.assertLess(
            cleanup_script.index('chmod -R u+rwX "$SMOKE_ROOT"'),
            cleanup_script.index('rm -rf -- "$SMOKE_ROOT"'),
        )
        self.assertNotIn('rm -rf -- "$RUNNER_TEMP"', cleanup_script)
        self.assertNotIn('rm -rf -- "$RUNNER_TEMP"/', cleanup_script)
        self.assertNotIn("*pk-stack-kiro-credential-smoke*", cleanup_script)

        with tempfile.TemporaryDirectory() as temporary:
            runner_temp = Path(temporary) / "runner-temp"
            runner_temp.mkdir()
            smoke_root = runner_temp / "pk-stack-kiro-credential-smoke"
            workspace = smoke_root / "workspace"
            workspace.mkdir(parents=True)
            readonly = workspace / "sentinel.txt"
            readonly.write_text("immutable\n", encoding="utf-8")
            readonly.chmod(0o400)
            workspace.chmod(0o500)
            foreign = runner_temp / "foreign"
            foreign.mkdir()
            foreign_sentinel = foreign / "keep.txt"
            foreign_sentinel.write_text("preserve\n", encoding="utf-8")

            cleanup_env = os.environ.copy()
            cleanup_env.update(
                {
                    "RUNNER_TEMP": str(runner_temp),
                    "SMOKE_ROOT": str(smoke_root),
                }
            )
            completed = subprocess.run(
                ["bash", "-c", cleanup_script],
                env=cleanup_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse(smoke_root.exists())
            self.assertEqual(foreign_sentinel.read_text(encoding="utf-8"), "preserve\n")

            os.symlink(foreign, smoke_root, target_is_directory=True)
            symlink_attempt = subprocess.run(
                ["bash", "-c", cleanup_script],
                env=cleanup_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(symlink_attempt.returncode, 0)
            self.assertTrue(smoke_root.is_symlink())
            self.assertEqual(foreign_sentinel.read_text(encoding="utf-8"), "preserve\n")
            smoke_root.unlink()

            wrong_root = runner_temp / "wrong-root"
            wrong_root.mkdir()
            wrong_sentinel = wrong_root / "keep.txt"
            wrong_sentinel.write_text("preserve\n", encoding="utf-8")
            wrong_env = cleanup_env | {"SMOKE_ROOT": str(wrong_root)}
            wrong_attempt = subprocess.run(
                ["bash", "-c", cleanup_script],
                env=wrong_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(wrong_attempt.returncode, 0)
            self.assertEqual(wrong_sentinel.read_text(encoding="utf-8"), "preserve\n")

    def test_stale_pr_classification_uses_mocked_api_data(self) -> None:
        subprocess.run(
            ["node", "--test", ".github/scripts/test_pk_stack_pr_policy.js"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_kiro_runtime_canary_contract(self) -> None:
        subprocess.run(
            [sys.executable, ".github/scripts/test_kiro_runtime_canary.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_post_accept_failure_restores_pin_and_ledger_for_attempt_two(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            root = sandbox / "repo"
            root.mkdir()
            (root / "maintenance").mkdir()
            (root / "powers/pk-stack/docs").mkdir(parents=True)
            (root / ".kiro/agents").mkdir(parents=True)
            manifest = root / "maintenance/upstreams.json"
            ledger = root / "maintenance/upstream-reviews.json"
            provenance = root / "powers/pk-stack/docs/provenance.md"
            drift = drift_detector_fixture()
            base_ledger = (
                json.dumps(
                    review_ledger_fixture(drift),
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
            manifest.write_text('{"pin":"base"}\n', encoding="utf-8")
            ledger.write_text(base_ledger, encoding="utf-8")
            provenance.write_text("# Provenance\n\n", encoding="utf-8")
            (root / ".kiro/agents/pstack.json").write_text("{}\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=PK-Stack Test",
                    "-c",
                    "user.email=pk-stack@example.invalid",
                    "commit",
                    "-qm",
                    "base",
                ],
                cwd=root,
                check=True,
            )
            base_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()

            # Attempt 1 accepted the transition, then a later gate failed.
            manifest.write_text('{"pin":"accepted"}\n', encoding="utf-8")
            ledger.write_text('{"ledger":"accepted"}\n', encoding="utf-8")
            provenance.write_text(
                "# Provenance\n\n"
                f"{pending_marker_line(drift)}\n\n"
                "Attempt one authored review remains useful after rollback.\n",
                encoding="utf-8",
            )
            detector = root / ".git/pk-stack-test-detector.json"
            detector.write_text(json.dumps(drift), encoding="utf-8")
            feedback = root / ".git/pk-stack-test-feedback.txt"
            feedback.write_text("post-accept gate failed\n", encoding="utf-8")
            git_state = sandbox / "git-boundary-state"

            guard.prepare_attempt(
                root,
                base_sha,
                self.policy,
                detector,
                feedback,
                git_state,
            )

            self.assertFalse((root / ".kiro").exists())
            self.assertEqual(manifest.read_text(encoding="utf-8"), '{"pin":"base"}\n')
            self.assertEqual(ledger.read_text(encoding="utf-8"), base_ledger)
            rolled_back_provenance = provenance.read_text(encoding="utf-8")
            self.assertNotIn("pk-stack-upstream-review:", rolled_back_provenance)
            self.assertIn("Attempt one authored review remains useful", rolled_back_provenance)
            proposal_root = root / ".pk-stack-maintenance"
            self.assertTrue(proposal_root.is_dir())
            proposal = proposal_root / "proposal.json"
            proposal.write_text(json.dumps(proposal_fixture(drift)), encoding="utf-8")
            with provenance.open("a", encoding="utf-8") as provenance_stream:
                provenance_stream.write(f"\n{pending_marker_line(drift)}\n")

            validated = guard.validate_proposal(root, detector, proposal)

            self.assertEqual(validated["source_id"], "cursor-pstack")
            self.assertEqual(validated["expected_head"], "c" * 40)
            self.assertEqual(
                provenance.read_text(encoding="utf-8").count("pk-stack-upstream-review:"), 1
            )
            guard._remove_git_state(root, git_state)


if __name__ == "__main__":
    unittest.main()
