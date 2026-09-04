from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

from pk_stack import evidence as evidence_module
from pk_stack.evidence import EvidenceError, append_evidence, audit_evidence


def _append(
    root: Path,
    *,
    decision: str = "Keep the narrow contract.",
    now: datetime | None = None,
    artifact: Path | None = None,
    artifact_sha256: str | None = None,
) -> dict[str, object]:
    return append_evidence(
        root,
        "account-lookup",
        requirement="Account lookup must return the current status.",
        evidence="The public CLI returned active with exit code zero.",
        decision=decision,
        verification="uv run pytest tests/test_account_lookup.py -q passed.",
        verdict="VERIFIED",
        artifact=artifact,
        artifact_sha256=artifact_sha256,
        now=now,
    )


def test_default_append_is_bounded_canonical_monotonic_and_auditable(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "result.json"
    artifact.parent.mkdir()
    artifact.write_text('{"status":"active"}\n', encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    instant = datetime(2026, 9, 3, 12, 30, tzinfo=UTC)

    first = _append(
        tmp_path,
        now=instant,
        artifact=Path("artifacts/result.json"),
        artifact_sha256=digest,
    )
    second = _append(tmp_path, decision="Retain the verified implementation.", now=instant)
    audit = audit_evidence(tmp_path, "account-lookup")

    path = tmp_path / ".pk-stack/state/evidence/account-lookup/decision-log.jsonl"
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert first["path"] == ".pk-stack/state/evidence/account-lookup/decision-log.jsonl"
    assert first["committed"] is False
    assert second["event_count"] == 2
    assert [event["sequence"] for event in events] == [1, 2]
    assert events[0]["timestamp"] == "2026-09-03T12:30:00.000000Z"
    assert events[1]["timestamp"] == "2026-09-03T12:30:00.000001Z"
    assert events[0]["artifact"] == {
        "path": "artifacts/result.json",
        "sha256": digest,
    }
    assert path.read_bytes().endswith(b"\n")
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert audit["event_count"] == 2
    assert audit["next_sequence"] == 3
    assert audit["verdict_counts"] == {
        "INCONCLUSIVE": 0,
        "NOT VERIFIED": 0,
        "VERIFIED": 2,
    }


def test_concurrent_appends_serialize_without_duplicate_sequences(tmp_path: Path) -> None:
    barrier = threading.Barrier(8)
    errors: list[Exception] = []

    def append(index: int) -> None:
        try:
            barrier.wait(timeout=3)
            _append(tmp_path, decision=f"Record independent checkpoint {index}.")
        except Exception as exc:  # pragma: no cover - asserted empty below
            errors.append(exc)

    threads = [threading.Thread(target=append, args=(index,)) for index in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert errors == []
    assert all(not thread.is_alive() for thread in threads)
    assert audit_evidence(tmp_path, "account-lookup")["event_count"] == 8


@pytest.mark.parametrize(
    "secret",
    [
        "api_key=super-secret-value",
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz",
        "github_pat_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
        "-----BEGIN PRIVATE KEY-----",
        "https://user:password@example.test/path",
    ],
)
def test_secret_shaped_input_is_rejected_without_echo_or_file(
    tmp_path: Path,
    secret: str,
) -> None:
    with pytest.raises(EvidenceError) as error:
        _append(tmp_path, decision=secret)

    assert secret not in str(error.value)
    assert "redacted pointer" in str(error.value)
    assert not (tmp_path / ".pk-stack/state/evidence/account-lookup/decision-log.jsonl").exists()
    assert not (tmp_path / ".pk-stack").exists()


@pytest.mark.parametrize(
    ("artifact", "digest", "message"),
    [
        (Path("missing.txt"), None, "does not exist"),
        (Path("../outside.txt"), None, "canonical"),
        (Path("artifact.txt"), "0" * 64, "mismatch"),
    ],
)
def test_artifact_reference_is_contained_present_and_hash_bound(
    tmp_path: Path,
    artifact: Path,
    digest: str | None,
    message: str,
) -> None:
    (tmp_path / "artifact.txt").write_text("real evidence\n", encoding="utf-8")

    with pytest.raises(EvidenceError, match=message):
        _append(tmp_path, artifact=artifact, artifact_sha256=digest)


def test_artifact_reference_rejects_dotdot_alias_even_when_it_resolves_inside(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("real evidence\n", encoding="utf-8")
    (tmp_path / "artifacts").mkdir()

    with pytest.raises(EvidenceError, match="canonical"):
        _append(tmp_path, artifact=Path("artifacts/../artifact.txt"))

    assert not (tmp_path / ".pk-stack").exists()


@pytest.mark.parametrize("removed", [False, True])
def test_append_records_correction_after_historical_artifact_drift(
    tmp_path: Path, removed: bool
) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("first\n", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    first = _append(tmp_path, artifact=Path("artifact.txt"), artifact_sha256=digest)
    trail = tmp_path / str(first["path"])
    historical = trail.read_bytes()
    if removed:
        artifact.unlink()
    else:
        artifact.write_text("changed\n", encoding="utf-8")
    correction = _append(
        tmp_path, decision="The prior artifact changed; re-verification is required."
    )
    assert correction["event_count"] == 2
    assert trail.read_bytes().startswith(historical)
    with pytest.raises(EvidenceError, match=r"does not exist|sha256 mismatch"):
        audit_evidence(tmp_path, "account-lookup")


def test_artifact_symlink_and_digest_drift_fail_closed(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("first\n", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    alias = tmp_path / "alias.txt"
    alias.symlink_to(artifact)

    with pytest.raises(EvidenceError, match="symlink"):
        _append(tmp_path, artifact=Path("alias.txt"))

    _append(tmp_path, artifact=Path("artifact.txt"), artifact_sha256=digest)
    artifact.write_text("changed\n", encoding="utf-8")
    with pytest.raises(EvidenceError, match="sha256 mismatch"):
        audit_evidence(tmp_path, "account-lookup")


def test_committed_trail_requires_flag_and_exact_target(tmp_path: Path) -> None:
    target = Path("Wiki/evidence/account-lookup/decision-log.jsonl")

    with pytest.raises(EvidenceError, match="requires an explicit"):
        append_evidence(
            tmp_path,
            "account-lookup",
            requirement="Requirement",
            evidence="Evidence",
            decision="Decision",
            verification="Verification",
            verdict="INCONCLUSIVE",
            committed=True,
        )
    with pytest.raises(EvidenceError, match="only with"):
        append_evidence(
            tmp_path,
            "account-lookup",
            requirement="Requirement",
            evidence="Evidence",
            decision="Decision",
            verification="Verification",
            verdict="INCONCLUSIVE",
            target=target,
        )
    with pytest.raises(EvidenceError, match="exactly"):
        append_evidence(
            tmp_path,
            "account-lookup",
            requirement="Requirement",
            evidence="Evidence",
            decision="Decision",
            verification="Verification",
            verdict="INCONCLUSIVE",
            committed=True,
            target=Path("Wiki/evidence/other/decision-log.jsonl"),
        )

    result = append_evidence(
        tmp_path,
        "account-lookup",
        requirement="Requirement",
        evidence="Evidence",
        decision="Decision",
        verification="Verification",
        verdict="INCONCLUSIVE",
        committed=True,
        target=target,
    )

    assert result["committed"] is True
    assert (tmp_path / target).is_file()
    assert not (tmp_path / ".pk-stack/state/evidence/account-lookup").exists()
    assert (
        audit_evidence(
            tmp_path,
            "account-lookup",
            committed=True,
            target=target,
        )["event_count"]
        == 1
    )


@pytest.mark.parametrize("mutation", ["extra-key", "sequence", "noncanonical", "utf8"])
def test_audit_rejects_schema_order_encoding_and_canonicalization_tampering(
    tmp_path: Path,
    mutation: str,
) -> None:
    _append(tmp_path)
    path = tmp_path / ".pk-stack/state/evidence/account-lookup/decision-log.jsonl"
    event = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "extra-key":
        event["reasoning"] = "private narrative"
        path.write_text(json.dumps(event, sort_keys=True) + "\n", encoding="utf-8")
    elif mutation == "sequence":
        event["sequence"] = 2
        path.write_text(
            json.dumps(event, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
    elif mutation == "noncanonical":
        path.write_text(json.dumps(event, sort_keys=True) + "\n", encoding="utf-8")
    else:
        path.write_bytes(b"\xff\n")

    with pytest.raises(EvidenceError):
        audit_evidence(tmp_path, "account-lookup")


def test_bounds_reject_without_replacing_valid_trail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _append(tmp_path)
    path = tmp_path / ".pk-stack/state/evidence/account-lookup/decision-log.jsonl"
    original = path.read_bytes()
    monkeypatch.setattr(evidence_module, "MAX_EVIDENCE_EVENTS", 1)

    with pytest.raises(EvidenceError, match="event limit"):
        _append(tmp_path, decision="A second checkpoint must not be written.")

    assert path.read_bytes() == original
    with pytest.raises(EvidenceError, match="byte limit"):
        append_evidence(
            tmp_path,
            "another-trail",
            requirement="x" * (evidence_module.MAX_EVIDENCE_FIELD_BYTES + 1),
            evidence="Evidence",
            decision="Decision",
            verification="Verified",
            verdict="NOT VERIFIED",
        )


def test_append_rejects_invalid_verdict_or_detached_digest_before_writing(
    tmp_path: Path,
) -> None:
    with pytest.raises(EvidenceError, match="verdict"):
        append_evidence(
            tmp_path,
            "invalid-verdict",
            requirement="Requirement",
            evidence="Evidence",
            decision="Decision",
            verification="Verification",
            verdict="PASS",  # ty: ignore[invalid-argument-type]
        )
    with pytest.raises(EvidenceError, match="requires --artifact"):
        append_evidence(
            tmp_path,
            "detached-digest",
            requirement="Requirement",
            evidence="Evidence",
            decision="Decision",
            verification="Verification",
            verdict="INCONCLUSIVE",
            artifact_sha256="0" * 64,
        )

    assert not (tmp_path / ".pk-stack").exists()


def test_audit_rejects_missing_empty_and_duplicate_key_trails(tmp_path: Path) -> None:
    with pytest.raises(EvidenceError, match="does not exist"):
        audit_evidence(tmp_path, "account-lookup")

    path = tmp_path / ".pk-stack/state/evidence/account-lookup/decision-log.jsonl"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"")
    with pytest.raises(EvidenceError, match="no events"):
        audit_evidence(tmp_path, "account-lookup")

    path.unlink()
    _append(tmp_path)
    data = path.read_text(encoding="utf-8")
    path.write_text(
        data.replace('"decision":', '"decision":"first","decision":', 1),
        encoding="utf-8",
    )
    with pytest.raises(EvidenceError, match="duplicate key"):
        audit_evidence(tmp_path, "account-lookup")


def test_audit_duplicate_key_error_does_not_echo_untrusted_secret(tmp_path: Path) -> None:
    path = tmp_path / ".pk-stack/state/evidence/account-lookup/decision-log.jsonl"
    path.parent.mkdir(parents=True)
    secret = "api_key=super-secret-value"
    path.write_text(f'{{"{secret}":1,"{secret}":2}}\n', encoding="utf-8")

    with pytest.raises(EvidenceError, match="duplicate key") as error:
        audit_evidence(tmp_path, "account-lookup")

    assert secret not in str(error.value)


def test_audit_rejects_planted_secret_and_non_monotonic_timestamp(tmp_path: Path) -> None:
    _append(tmp_path)
    _append(tmp_path, decision="Second public checkpoint.")
    path = tmp_path / ".pk-stack/state/evidence/account-lookup/decision-log.jsonl"
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    second_timestamp = events[1]["timestamp"]
    events[1]["timestamp"] = events[0]["timestamp"]
    path.write_text(
        "".join(
            json.dumps(event, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
            for event in events
        ),
        encoding="utf-8",
    )
    with pytest.raises(EvidenceError, match="timestamps"):
        audit_evidence(tmp_path, "account-lookup")

    events[1]["timestamp"] = second_timestamp
    events[1]["decision"] = "password=definitely-secret"
    path.write_text(
        "".join(
            json.dumps(event, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
            for event in events
        ),
        encoding="utf-8",
    )
    with pytest.raises(EvidenceError, match="redacted pointer"):
        audit_evidence(tmp_path, "account-lookup")


@pytest.mark.parametrize("separator", ["crlf", "mixed"])
def test_audit_rejects_crlf_and_mixed_jsonl_separators(
    tmp_path: Path,
    separator: str,
) -> None:
    _append(tmp_path)
    _append(tmp_path, decision="Second public checkpoint.")
    path = tmp_path / ".pk-stack/state/evidence/account-lookup/decision-log.jsonl"
    lines = path.read_bytes().splitlines()
    if separator == "crlf":
        path.write_bytes(b"\r\n".join(lines) + b"\r\n")
    else:
        path.write_bytes(lines[0] + b"\r\n" + lines[1] + b"\n")

    with pytest.raises(EvidenceError, match="canonical JSONL"):
        audit_evidence(tmp_path, "account-lookup")
    with pytest.raises(EvidenceError, match="canonical JSONL"):
        _append(tmp_path, decision="A mixed trail must not be extended.")


def test_unicode_line_separator_inside_json_string_is_one_valid_event(tmp_path: Path) -> None:
    separator = chr(0x2028)
    _append(tmp_path, decision=f"Keep the public{separator}evidence boundary.")

    audit = audit_evidence(tmp_path, "account-lookup")
    path = tmp_path / ".pk-stack/state/evidence/account-lookup/decision-log.jsonl"
    assert audit["event_count"] == 1
    assert path.read_bytes().count(b"\n") == 1
    assert separator.encode() in path.read_bytes()


def test_event_and_file_bounds_are_enforced_on_append_and_audit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(evidence_module, "MAX_EVIDENCE_LINE_BYTES", 64)
    with pytest.raises(EvidenceError, match="event exceeds"):
        _append(tmp_path)
    path = tmp_path / ".pk-stack/state/evidence/account-lookup/decision-log.jsonl"
    assert not path.exists()

    monkeypatch.setattr(evidence_module, "MAX_EVIDENCE_LINE_BYTES", 24 * 1024)
    _append(tmp_path)
    original = path.read_bytes()
    monkeypatch.setattr(evidence_module, "MAX_EVIDENCE_FILE_BYTES", len(original) - 1)
    with pytest.raises(EvidenceError, match=r"file exceeds|trail exceeds"):
        audit_evidence(tmp_path, "account-lookup")
    with pytest.raises(EvidenceError, match=r"file exceeds|trail exceeds"):
        _append(tmp_path, decision="This append must not replace the trail.")
    assert path.read_bytes() == original


def test_timestamp_source_must_be_timezone_aware(tmp_path: Path) -> None:
    with pytest.raises(EvidenceError, match="timezone-aware"):
        _append(tmp_path, now=datetime(2026, 9, 3, 12, 30))
    assert not (tmp_path / ".pk-stack").exists()
