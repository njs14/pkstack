#!/usr/bin/env python3
"""Deterministic regressions for the immutable PK-Stack maintenance boundary."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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


def inventory_sha256(
    *,
    base_commit: str,
    head_commit: str,
    files: list[dict[str, object]],
) -> str:
    document = {
        "repository": "cursor/plugins",
        "source_path": "pstack",
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
        "schema_version": 1,
        "manifest": "maintenance/upstreams.json",
        "review_ledger": "maintenance/upstream-reviews.json",
        "network_boundary": "https://api.github.com",
        "sources": [
            {
                "ok": True,
                "id": "cursor-pstack",
                "repository": "cursor/plugins",
                "path": "pstack",
                "ref": "main",
                "provenance_path": "powers/pk-stack/docs/provenance.md",
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


def proposal_fixture(payload: dict[str, object]) -> dict[str, object]:
    source = payload["sources"][0]  # type: ignore[index]
    comparison = source["comparison"]  # type: ignore[index]
    unavailable = comparison["review_constraints"]["unavailable_binary_paths"]  # type: ignore[index]
    return {
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
    source = payload["sources"][0]  # type: ignore[index]
    reproof = source["review_reproof"]  # type: ignore[index]
    transition_count = reproof["transition_count"]  # type: ignore[index]
    if transition_count not in {0, 1}:
        raise AssertionError("test ledger helper supports zero or one accepted transition")
    transitions = []
    if transition_count == 1:
        summary = reproof["transitions"][0]  # type: ignore[index]
        transitions = [
            {
                "prior": summary["prior"],
                "new": summary["new"],
                "inventory_sha256": summary["inventory_sha256"],
                "dispositions": [
                    {
                        "path": "accepted-a.md",
                        "disposition": "A",
                        "rationale": "Accepted in the prior exact review.",
                    },
                    {
                        "path": "accepted-c.md",
                        "disposition": "C",
                        "rationale": "Excluded in the prior exact review.",
                    },
                ],
            }
        ]
    return {
        "schema_version": 1,
        "sources": [
            {
                "id": source["id"],  # type: ignore[index]
                "repository": source["repository"],  # type: ignore[index]
                "path": source["path"],  # type: ignore[index]
                "provenance_path": source["provenance_path"],  # type: ignore[index]
                "genesis": reproof["genesis"],  # type: ignore[index]
                "transitions": transitions,
            }
        ],
    }


def review_marker_line(marker: dict[str, object]) -> str:
    canonical = json.dumps(marker, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"<!-- pk-stack-upstream-review: {canonical} -->"


def pending_marker_line(payload: dict[str, object]) -> str:
    source = payload["sources"][0]  # type: ignore[index]
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


def accepted_marker_lines(payload: dict[str, object]) -> list[str]:
    ledger_source = review_ledger_fixture(payload)["sources"][0]  # type: ignore[index]
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
    @staticmethod
    def stream(*events: dict[str, object]) -> bytes:
        return b"".join(
            json.dumps(event, separators=(",", ":")).encode() + b"\n" for event in events
        )

    @staticmethod
    def update(kind: str, text: str = "") -> dict[str, object]:
        return {
            "sessionUpdate": {
                "sessionId": "session",
                "update": {
                    "sessionUpdate": kind,
                    "content": {"type": "text", "text": text},
                },
            }
        }

    def validate(self, raw: bytes) -> dict[str, int | bool]:
        return stream_guard.validate_stream_bytes(
            raw,
            b"",
            return_code=0,
            api_key="not-present-in-stream",
        )

    def test_accepts_exact_agent_message_marker(self) -> None:
        raw = self.stream(
            {"runStarted": {"payloadSchema": 1}},
            self.update("agent_message_chunk", stream_guard.MARKER),
            {"runFinished": {"status": "completed"}},
        )
        self.assertEqual(self.validate(raw), {"ok": True, "events": 3})

    def test_rejects_marker_echoed_only_in_user_message(self) -> None:
        raw = self.stream(self.update("user_message_chunk", stream_guard.MARKER))
        with self.assertRaises(stream_guard.StreamError):
            self.validate(raw)

    def test_rejects_nested_tool_call_and_update_events(self) -> None:
        for tool_event in (
            self.update("tool_call"),
            {
                "method": "session/update",
                "params": {
                    "update": {
                        "sessionUpdate": "tool_call_update",
                        "toolCallId": "tool-1",
                    }
                },
            },
        ):
            raw = self.stream(
                self.update("agent_message_chunk", stream_guard.MARKER),
                tool_event,
            )
            with self.assertRaises(stream_guard.StreamError):
                self.validate(raw)

    def test_rejects_malformed_duplicate_and_non_finite_json(self) -> None:
        for raw in (
            b'{"broken":\n',
            b'{"type":"x","type":"y"}\n',
            b'{"value":NaN}\n',
        ):
            with self.assertRaises(stream_guard.StreamError):
                self.validate(raw)


class KiroPermissionStreamTests(unittest.TestCase):
    def test_exact_agent_profile_denial_and_used_tools_are_required(self) -> None:
        events = [
            {
                "type": "toolResult",
                "policyDenial": {
                    "capability": "fs_write",
                    "resource": "protected/blocked.txt",
                    "effect": "deny",
                    "scope": "workspace",
                    "source": "agent-profile",
                },
            },
            {
                "runFinished": {
                    "status": "success",
                    "usedTools": ["read_file", "grep_search", "fs_write", "fs_write"],
                }
            },
        ]
        with tempfile.TemporaryDirectory() as temporary:
            stream = Path(temporary) / "stream.jsonl"
            stderr = Path(temporary) / "stderr.log"
            stream.write_text(
                "".join(f"{json.dumps(event)}\n" for event in events),
                encoding="utf-8",
            )
            stderr.write_text("", encoding="utf-8")
            self.assertEqual(
                permission_stream_guard.validate(stream, stderr, 0, "test-secret"),
                {"ok": True, "events": 2},
            )

            events[0]["policyDenial"]["resource"] = "protected/other.txt"  # type: ignore[index]
            stream.write_text(
                "".join(f"{json.dumps(event)}\n" for event in events),
                encoding="utf-8",
            )
            with self.assertRaises(permission_stream_guard.StreamError):
                permission_stream_guard.validate(stream, stderr, 0, "test-secret")


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
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            detector_path = root / "detector.json"
            proposal_path = root / "proposal.json"
            ledger_path = root / "maintenance/upstream-reviews.json"
            provenance_path = root / "powers/pk-stack/docs/provenance.md"
            ledger_path.parent.mkdir(parents=True)
            provenance_path.parent.mkdir(parents=True)
            detector_path.write_text(json.dumps(detector), encoding="utf-8")
            proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
            ledger_path.write_text(
                json.dumps(review_ledger_fixture(detector)),
                encoding="utf-8",
            )
            provenance_path.write_text(
                f"# Provenance\n\n{pending_marker_line(detector)}\n",
                encoding="utf-8",
            )
            return guard.validate_proposal(root, detector_path, proposal_path)

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
        allowed_representatives = {
            ".pk-stack-maintenance/proposal.json",
            "powers/pk-stack/README.md",
            "powers/pk-stack/dev.kiro/steering/permission-smoke.md",
            "powers/pk-stack/docs/upstream-skill-parity.json",
            "powers/pk-stack/docs/smoke/permission.md",
            "powers/pk-stack/skills/permission-smoke/SKILL.md",
            "powers/pk-stack/templates/project/.kiro/agents/permission-smoke.json",
        }
        protected_representatives = {
            ".github/protected.txt",
            ".kiro/protected.txt",
            "powers/pk-stack/src/pstack_kiro/protected.py",
            "powers/pk-stack/tests/protected.py",
            "maintenance/upstream-reviews.json",
            "powers/pk-stack/docs/validation-report.md",
        }
        for path in allowed_representatives | protected_representatives:
            self.assertIn(path, prompt)
        self.assertIn("continue after each expected denial", prompt)
        self.assertIn("Finish normally only after attempting all thirteen writes", prompt)

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
        self.assertIn(
            "preserving the canonical <!-- pk-stack-upstream-genesis: "
            "{canonical JSON} --> marker byte-for-byte",
            kiro_runner,
        )
        self.assertIn("preserving every prior marker unchanged and in order", kiro_runner)
        self.assertIn("review-ledger transition count plus one", kiro_runner)
        self.assertIn("--trust-tools=fs_read,fs_write,grep", kiro_runner)
        self.assertNotIn("--trust-tools=read,grep", kiro_runner)
        self.assertEqual(
            self.policy["ci_authority"]["runtime_trust_tools"],
            ["fs_read", "fs_write", "grep"],
        )
        for attempt in range(1, 5):
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
        self.assertIn("--agent pstack-maintainer", smoke)
        self.assertIn("--model gpt-5.6-sol", smoke)
        self.assertIn("--effort max", smoke)
        self.assertIn("--trust-tools=", smoke)
        self.assertIn("chmod -R a-w", smoke)
        self.assertIn("if: always()", smoke)
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
        self.assertEqual(
            base64.b64decode(encoded, validate=True),
            (ROOT / ".kiro/agents/pstack-maintainer.json").read_bytes(),
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
        self.assertEqual(
            base64.b64decode(encoded_validator, validate=True),
            STREAM_GUARD_PATH.read_bytes(),
        )
        self.assertIn("workflow_dispatch:", permission_smoke)
        self.assertNotIn("schedule:", permission_smoke)
        self.assertIn("permissions: {}", permission_smoke)
        self.assertIn("--trust-tools=fs_read,fs_write,grep", permission_smoke)
        self.assertIn("pk-stack-permission-fixture", permission_smoke)
        self.assertIn("validate_kiro_permission_stream.py", permission_smoke)
        self.assertIn(
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
        for path in (
            ".pk-stack-maintenance/proposal.json",
            "powers/pk-stack/README.md",
            "powers/pk-stack/dev.kiro/steering/permission-smoke.md",
            "powers/pk-stack/docs/smoke/permission.md",
            "powers/pk-stack/skills/permission-smoke/SKILL.md",
            "powers/pk-stack/templates/project/.kiro/agents/permission-smoke.json",
            ".github/protected.txt",
            ".kiro/protected.txt",
            "powers/pk-stack/src/pstack_kiro/protected.py",
            "powers/pk-stack/tests/protected.py",
            "maintenance/upstream-reviews.json",
            "powers/pk-stack/docs/validation-report.md",
        ):
            self.assertIn(path, permission_smoke)
        self.assertIn('"source": "agent-profile"', permission_smoke)
        self.assertIn("b'not found, using \"default\"'", permission_smoke)
        self.assertIn(
            '{"execute_bash", "kiro_powers", "remote_web_search"}',
            permission_smoke,
        )
        self.assertIn(
            'sha256sum --check "$SMOKE_ROOT/protected-baseline.sha256"',
            permission_smoke,
        )
        self.assertIn('cmp "$SMOKE_ROOT/expected-files.txt"', permission_smoke)
        self.assertIn('chmod -R a-w "$GITHUB_WORKSPACE"', permission_smoke)
        self.assertNotIn("git status --porcelain=v1 --untracked-files=all", permission_smoke)
        self.assertNotIn('test -z "$(git status', permission_smoke)
        self.assertNotIn("protected/blocked.txt", permission_smoke)
        self.assertEqual(permission_smoke.count("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}"), 1)
        self.assertNotIn("actions/upload-artifact", permission_smoke)

    def test_stale_pr_classification_uses_mocked_api_data(self) -> None:
        subprocess.run(
            ["node", "--test", ".github/scripts/test_pk_stack_pr_policy.js"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_post_accept_failure_restores_pin_and_ledger_for_attempt_two(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
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

            guard.prepare_attempt(root, base_sha, self.policy, detector, feedback)

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


if __name__ == "__main__":
    unittest.main()
