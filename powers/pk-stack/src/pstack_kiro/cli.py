"""Thin Cyclopts command surface over PK-Stack's typed service modules."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Literal

from cyclopts import App, CycloptsError

from pstack_kiro import __version__
from pstack_kiro.bootstrap import bootstrap_project
from pstack_kiro.branding import identity_payload
from pstack_kiro.doctor import run_doctor
from pstack_kiro.evidence import EvidenceError, append_evidence, audit_evidence
from pstack_kiro.features import (
    FEATURE_SCHEMA_VERSION,
    FeatureMapError,
    find_feature,
    find_verifiable_feature,
    list_features,
    prepare_feature,
    prepare_initial_feature_map,
    prepare_published_feature_bytes,
    snapshot_existing_feature,
    snapshot_feature_target,
    snapshot_prepared_feature_map,
    validate_feature_map,
    write_prepared_feature_if_unchanged,
    write_prepared_feature_map,
)
from pstack_kiro.goal import (
    GoalError,
    bind_spec_contract,
    clear_goal,
    get_goal,
    resume_goal,
    start_goal,
    state_payload,
    tripwire,
    verify_goal,
)
from pstack_kiro.knowledge import KnowledgeError
from pstack_kiro.knowledge import search as search_knowledge
from pstack_kiro.knowledge import status as knowledge_status
from pstack_kiro.knowledge import validate as validate_knowledge
from pstack_kiro.models import CommandSpec, EvidenceVerdict, FeatureEntrypoint, FeatureSubFeature
from pstack_kiro.runner import CommandRejected, display_command, parse_command, run_command
from pstack_kiro.upstreams import (
    DEFAULT_MANIFEST,
    DEFAULT_PROPOSAL,
    DEFAULT_TIMEOUT_SECONDS,
    UpstreamError,
    accept_upstream,
    check_upstreams,
)

Output = Literal["text", "json"]

app = App(name="projectctl", help="Operate and prove this project through stable semantics.")
feature_app = App(help="Manage narrow executable feature-map contracts.")
goal_app = App(help="Persist and verify a bounded current-session goal.")
knowledge_app = App(help="Use canonical OKF tooling when broader project knowledge is needed.")
evidence_app = App(help="Append and audit bounded public decision/evidence trails.")
upstream_app = App(help="Reprove and accept reviewed hash-pinned upstream transitions safely.")
app.command(feature_app, name="feature")
app.command(goal_app, name="goal")
app.command(knowledge_app, name="knowledge")
app.command(evidence_app, name="evidence")
app.command(upstream_app, name="upstream")


def _emit(payload: Any, output: Output) -> None:
    if output == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                print(f"{key}: {json.dumps(value, sort_keys=True)}")
            else:
                print(f"{key}: {value}")
    elif isinstance(payload, list):
        for value in payload:
            print(value)
    else:
        print(payload)


def _fail(exc: Exception, output: Output, *, code: int = 2) -> None:
    payload = {"ok": False, "error": str(exc), "error_type": type(exc).__name__}
    if output == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"error: {exc}", file=sys.stderr)
    raise SystemExit(code)


@app.command(name="version")
def version_command(*, output: Output = "text") -> None:
    """Show the installed projectctl version."""

    payload = {**identity_payload(), "version": __version__}
    _emit(payload, output)


@app.command(name="setup")
def setup_command(
    *,
    root: Path = Path("."),
    power_root: Path | None = None,
    dry_run: bool = False,
    update_managed: bool = False,
    output: Output = "text",
) -> None:
    """Bootstrap from an explicit Power; managed upgrades require reviewed opt-in."""

    try:
        if power_root is None:
            raise ValueError(
                "projectctl setup requires --power-root; use the Power-local "
                "/setup-pk-stack skill for setup or refresh, or pass a reviewed "
                "Power root explicitly"
            )
        result = bootstrap_project(
            root,
            power_root=power_root,
            dry_run=dry_run,
            update_managed=update_managed,
        )
    except (OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(result.to_dict(), output)
    if not result.ok:
        raise SystemExit(2)


@app.command(name="doctor")
def doctor_command(*, root: Path = Path("."), output: Output = "text") -> None:
    """Check Kiro, projectctl, feature-map, and goal-state integration."""

    try:
        result = run_doctor(root)
    except (OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(result, output)
    if not result["ok"]:
        raise SystemExit(1)


@feature_app.command(name="list")
def feature_list(*, root: Path = Path("."), output: Output = "text") -> None:
    """List feature contracts."""

    try:
        features = [feature.to_dict() for feature in list_features(root)]
    except (FeatureMapError, OSError) as exc:
        _fail(exc, output)
    _emit({"ok": True, "count": len(features), "features": features}, output)


@feature_app.command(name="show")
def feature_show(slug: str, *, root: Path = Path("."), output: Output = "text") -> None:
    """Show one feature contract."""

    try:
        feature = find_feature(root, slug)
    except (FeatureMapError, OSError) as exc:
        _fail(exc, output)
    _emit({"ok": True, "feature": feature.to_dict()}, output)


@feature_app.command(name="validate")
def feature_validate(*, root: Path = Path("."), output: Output = "text") -> None:
    """Validate feature syntax, commands, and related links."""

    try:
        result = validate_feature_map(root)
    except (FeatureMapError, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(result, output)
    if not result["ok"]:
        raise SystemExit(1)


def _keyed_values(values: list[str] | None, *, label: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise FeatureMapError(f"{label} values must use identifier=text")
        identifier, text = value.split("=", 1)
        identifier = identifier.strip()
        text = text.strip()
        if not identifier or not text:
            raise FeatureMapError(f"{label} values must use non-empty identifier=text")
        if identifier in parsed:
            raise FeatureMapError(f"duplicate {label} identifier {identifier!r}")
        parsed[identifier] = text
    return parsed


def _structured_feature_values(
    *,
    sub_feature: list[str] | None,
    entrypoint: list[str] | None,
    drive: list[str] | None,
    entrypoint_proof: list[str] | None,
    gotcha: list[str] | None,
    evidence_boundary: str | None,
    cleanup_boundary: str | None,
) -> dict[str, Any]:
    supplied = any(
        value is not None
        for value in (
            sub_feature,
            entrypoint,
            drive,
            entrypoint_proof,
            gotcha,
            evidence_boundary,
            cleanup_boundary,
        )
    )
    if not supplied:
        return {
            "schema_version": None,
            "sub_features": None,
            "entrypoints": None,
            "gotchas": None,
            "evidence_boundary": None,
            "cleanup_boundary": None,
        }
    sub_features = _keyed_values(sub_feature, label="sub-feature")
    user_paths = _keyed_values(entrypoint, label="entrypoint")
    drives = _keyed_values(drive, label="drive")
    proofs = _keyed_values(entrypoint_proof, label="entrypoint-proof")
    if not sub_features:
        raise FeatureMapError("structured generation requires at least one --sub-feature")
    if not user_paths or list(user_paths) != list(drives) or list(user_paths) != list(proofs):
        raise FeatureMapError(
            "every --entrypoint must have one same-order --drive and --entrypoint-proof"
        )
    if not gotcha:
        raise FeatureMapError("structured generation requires at least one --gotcha")
    return {
        "schema_version": FEATURE_SCHEMA_VERSION,
        "sub_features": [
            FeatureSubFeature(identifier=identifier, behavior=behavior)
            for identifier, behavior in sub_features.items()
        ],
        "entrypoints": [
            FeatureEntrypoint(
                identifier=identifier,
                user_path=user_path,
                drive=drives[identifier],
                observable=proofs[identifier],
            )
            for identifier, user_path in user_paths.items()
        ],
        "gotchas": gotcha,
        "evidence_boundary": evidence_boundary,
        "cleanup_boundary": cleanup_boundary,
    }


@feature_app.command(name="generate")
def feature_generate(
    slug: str,
    *,
    title: str,
    behavior: str,
    expected_path: str,
    command: str | None = None,
    related: list[str] | None = None,
    sub_feature: list[str] | None = None,
    entrypoint: list[str] | None = None,
    drive: list[str] | None = None,
    entrypoint_proof: list[str] | None = None,
    gotcha: list[str] | None = None,
    evidence_boundary: str | None = None,
    cleanup_boundary: str | None = None,
    ready: bool = False,
    overwrite: bool = False,
    root: Path = Path("."),
    timeout_seconds: float = 300.0,
    output: Output = "text",
) -> None:
    """Generate a draft contract, or prove its command before marking it ready."""

    try:
        structured = _structured_feature_values(
            sub_feature=sub_feature,
            entrypoint=entrypoint,
            drive=drive,
            entrypoint_proof=entrypoint_proof,
            gotcha=gotcha,
            evidence_boundary=evidence_boundary,
            cleanup_boundary=cleanup_boundary,
        )
        path, text = prepare_feature(
            root,
            slug,
            title=title,
            behavior=behavior,
            expected_path=expected_path,
            command=command,
            related=related or (),
            draft=not ready,
            overwrite=overwrite,
            **structured,
        )
        before = snapshot_feature_target(root.resolve(), path, overwrite=overwrite)
        proof = None
        if ready:
            assert command is not None  # validated by prepare_feature
            argv = parse_command(command)
            contract = CommandSpec(
                argv=argv,
                display=display_command(argv),
                source="feature-map",
                feature=slug,
            )
            proof = run_command(contract, root=root.resolve(), timeout_seconds=timeout_seconds)
            if not proof.passed:
                payload = {
                    "ok": False,
                    "created": False,
                    "draft": True,
                    "contract": contract.to_dict(),
                    "result": proof.to_dict(),
                }
                _emit(payload, output)
                raise SystemExit(1)
        revalidated_path, revalidated_text = prepare_feature(
            root,
            slug,
            title=title,
            behavior=behavior,
            expected_path=expected_path,
            command=command,
            related=related or (),
            draft=not ready,
            overwrite=overwrite,
            **structured,
        )
        if revalidated_path != path or revalidated_text != text:
            raise FeatureMapError(
                "feature candidate changed during verification; it was not written"
            )
        path = write_prepared_feature_if_unchanged(
            root,
            path,
            text.encode("utf-8"),
            expected=before,
        )
    except (FeatureMapError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    payload = {
        "ok": True,
        "path": str(path),
        "draft": not ready,
        "schema_version": structured["schema_version"] or 1,
        "migration_required": structured["schema_version"] is None,
    }
    if proof is not None:
        payload["initial_verification"] = proof.to_dict()
    _emit(payload, output)


@feature_app.command(name="generate-map")
def feature_generate_map(
    definition: Path,
    *,
    representative: str,
    overwrite: bool = False,
    root: Path = Path("."),
    timeout_seconds: float = 300.0,
    output: Output = "text",
) -> None:
    """Create 3-5 records and initially prove exactly one representative feature."""

    try:
        project_root = root.resolve()
        prepared = prepare_initial_feature_map(
            project_root,
            definition,
            representative=representative,
            overwrite=overwrite,
        )
        snapshots = snapshot_prepared_feature_map(
            project_root,
            prepared,
            overwrite=overwrite,
        )
        selected = next(feature for _, _, feature in prepared if feature.slug == representative)
        assert selected.command is not None  # every feature-plan record requires a command
        contract = CommandSpec(
            argv=selected.command,
            display=display_command(selected.command),
            source="feature-map",
            feature=representative,
        )
        proof = run_command(contract, root=project_root, timeout_seconds=timeout_seconds)
        if not proof.passed:
            _emit(
                {
                    "ok": False,
                    "created": False,
                    "representative": representative,
                    "contract": contract.to_dict(),
                    "result": proof.to_dict(),
                },
                output,
            )
            raise SystemExit(1)
        revalidated = prepare_initial_feature_map(
            project_root,
            definition,
            representative=representative,
            overwrite=overwrite,
        )
        if revalidated != prepared:
            raise FeatureMapError(
                "feature plan changed during representative verification; no map was written"
            )
        prepared = revalidated
        paths = write_prepared_feature_map(
            project_root,
            prepared,
            overwrite=overwrite,
            expected=snapshots,
        )
    except (FeatureMapError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(
        {
            "ok": True,
            "schema_version": FEATURE_SCHEMA_VERSION,
            "representative": representative,
            "initial_verification": proof.to_dict(),
            "features": [
                {
                    "slug": feature.slug,
                    "path": str(path),
                    "draft": feature.draft,
                    "initially_verified": feature.slug == representative,
                }
                for path, (_, _, feature) in zip(paths, prepared, strict=True)
            ],
        },
        output,
    )


@feature_app.command(name="migrate")
def feature_migrate(
    slug: str,
    *,
    sub_feature: list[str],
    entrypoint: list[str],
    drive: list[str],
    entrypoint_proof: list[str],
    gotcha: list[str],
    evidence_boundary: str,
    cleanup_boundary: str,
    root: Path = Path("."),
    timeout_seconds: float = 300.0,
    output: Output = "text",
) -> None:
    """Migrate one legacy record without changing its behavior or verifier contract."""

    try:
        project_root = root.resolve()
        existing, existing_path, before = snapshot_existing_feature(project_root, slug)
        if existing.schema_version >= FEATURE_SCHEMA_VERSION:
            raise FeatureMapError(f"feature {slug!r} already uses schema_version 2")
        if existing.legacy_extensions:
            raise FeatureMapError(
                f"feature {slug!r} has unmodeled legacy extensions; migrate it manually "
                "without discarding operator-authored bytes or structure"
            )
        structured = _structured_feature_values(
            sub_feature=sub_feature,
            entrypoint=entrypoint,
            drive=drive,
            entrypoint_proof=entrypoint_proof,
            gotcha=gotcha,
            evidence_boundary=evidence_boundary,
            cleanup_boundary=cleanup_boundary,
        )
        path, text = prepare_feature(
            project_root,
            slug,
            title=existing.title,
            behavior=existing.behavior,
            expected_path=existing.expected_path,
            command=existing.command,
            related=existing.related,
            draft=existing.draft,
            overwrite=True,
            **structured,
        )
        proof = None
        if not existing.draft:
            if existing.command is None:
                raise FeatureMapError(
                    "a ready legacy contract requires a verifier before migration"
                )
            contract = CommandSpec(
                argv=existing.command,
                display=display_command(existing.command),
                source="feature-map",
                feature=slug,
            )
            proof = run_command(contract, root=project_root, timeout_seconds=timeout_seconds)
            if not proof.passed:
                _emit(
                    {
                        "ok": False,
                        "migrated": False,
                        "contract": contract.to_dict(),
                        "result": proof.to_dict(),
                    },
                    output,
                )
                raise SystemExit(1)
        if path != existing_path:
            raise FeatureMapError(f"feature {slug!r} resolved to an inconsistent migration path")
        path = write_prepared_feature_if_unchanged(
            project_root,
            path,
            text.encode("utf-8"),
            expected=before,
        )
    except (FeatureMapError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    payload: dict[str, Any] = {
        "ok": True,
        "migrated": True,
        "path": str(path),
        "schema_version": FEATURE_SCHEMA_VERSION,
        "draft": existing.draft,
    }
    if proof is not None:
        payload["migration_verification"] = proof.to_dict()
    _emit(payload, output)


@feature_app.command(name="publish")
def feature_publish(
    slug: str,
    *,
    root: Path = Path("."),
    timeout_seconds: float = 300.0,
    output: Output = "text",
) -> None:
    """Prove one structured draft and publish it without re-entering its contract."""

    try:
        project_root = root.resolve()
        feature, path, before = snapshot_existing_feature(project_root, slug)
        if feature.schema_version < FEATURE_SCHEMA_VERSION:
            raise FeatureMapError(
                f"feature {slug!r} must be migrated to schema_version 2 before publication"
            )
        if not feature.draft:
            raise FeatureMapError(f"feature {slug!r} is already published")
        if feature.command is None:
            raise FeatureMapError(f"feature {slug!r} has no executable verification command")
        published_data = prepare_published_feature_bytes(project_root, path, before, feature)
        contract = CommandSpec(
            argv=feature.command,
            display=display_command(feature.command),
            source="feature-map",
            feature=slug,
        )
        proof = run_command(contract, root=project_root, timeout_seconds=timeout_seconds)
        if not proof.passed:
            _emit(
                {
                    "ok": False,
                    "published": False,
                    "contract": contract.to_dict(),
                    "result": proof.to_dict(),
                },
                output,
            )
            raise SystemExit(1)
        path = write_prepared_feature_if_unchanged(
            project_root,
            path,
            published_data,
            expected=before,
        )
        published = find_feature(project_root, slug)
    except (FeatureMapError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(
        {
            "ok": True,
            "published": True,
            "path": str(path),
            "feature": published.to_dict(),
            "initial_verification": proof.to_dict(),
        },
        output,
    )


def _verify_feature(slug: str, *, root: Path, timeout_seconds: float) -> dict[str, Any]:
    feature = find_verifiable_feature(root, slug)
    assert feature.command is not None  # guaranteed by find_verifiable_feature
    contract = CommandSpec(
        argv=feature.command,
        display=display_command(feature.command),
        source="feature-map",
        feature=slug,
    )
    result = run_command(contract, root=root, timeout_seconds=timeout_seconds)
    return {
        "ok": result.passed,
        "feature": feature.to_dict(),
        "contract": contract.to_dict(),
        "result": result.to_dict(),
    }


@feature_app.command(name="verify")
def feature_verify(
    slug: str,
    *,
    root: Path = Path("."),
    timeout_seconds: float = 300.0,
    output: Output = "text",
) -> None:
    """Run one feature's reviewed executable verifier."""

    try:
        payload = _verify_feature(slug, root=root.resolve(), timeout_seconds=timeout_seconds)
    except (FeatureMapError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(payload, output)
    if not payload["ok"]:
        raise SystemExit(1)


@app.command(name="verify")
def verify_alias(
    slug: str,
    *,
    root: Path = Path("."),
    timeout_seconds: float = 300.0,
    output: Output = "text",
) -> None:
    """Alias for ``projectctl feature verify``."""

    feature_verify(slug, root=root, timeout_seconds=timeout_seconds, output=output)


@evidence_app.command(name="append")
def evidence_append_command(
    slug: str,
    *,
    requirement: str,
    evidence: str,
    decision: str,
    verification: str,
    verdict: EvidenceVerdict,
    artifact: Path | None = None,
    artifact_sha256: str | None = None,
    committed: bool = False,
    target: Path | None = None,
    root: Path = Path("."),
    output: Output = "text",
) -> None:
    """Durably append one bounded, redacted, public evidence checkpoint."""

    try:
        payload = append_evidence(
            root,
            slug,
            requirement=requirement,
            evidence=evidence,
            decision=decision,
            verification=verification,
            verdict=verdict,
            artifact=artifact,
            artifact_sha256=artifact_sha256,
            committed=committed,
            target=target,
        )
    except (EvidenceError, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(payload, output)


@evidence_app.command(name="audit")
def evidence_audit_command(
    slug: str,
    *,
    committed: bool = False,
    target: Path | None = None,
    root: Path = Path("."),
    output: Output = "text",
) -> None:
    """Audit schema, ordering, bounds, references, hashes, and secret safety."""

    try:
        payload = audit_evidence(
            root,
            slug,
            committed=committed,
            target=target,
        )
    except (EvidenceError, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(payload, output)


@goal_app.command(name="start")
def goal_start(
    objective: str,
    *,
    command: str | None = None,
    feature: str | None = None,
    spec: str | None = None,
    max_attempts: int = 4,
    root: Path = Path("."),
    output: Output = "text",
) -> None:
    """Start a bounded goal with an executable acceptance contract."""

    try:
        state = start_goal(
            root,
            objective,
            command=command,
            feature=feature,
            spec=spec,
            max_attempts=max_attempts,
        )
    except (GoalError, FeatureMapError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit({"ok": True, "goal": state_payload(state)}, output)


@goal_app.command(name="bind-spec")
def goal_bind_spec(
    spec: str,
    *,
    feature: str | None = None,
    command: str | None = None,
    overwrite: bool = False,
    root: Path = Path("."),
    output: Output = "text",
) -> None:
    """Bind completed native Kiro Spec artifacts to one executable verifier."""

    try:
        payload = bind_spec_contract(
            root,
            spec,
            feature=feature,
            command=command,
            overwrite=overwrite,
        )
    except (GoalError, FeatureMapError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(payload, output)


@goal_app.command(name="status")
def goal_status(*, root: Path = Path("."), output: Output = "text") -> None:
    """Read the current goal state without changing it."""

    try:
        state = get_goal(root)
    except (GoalError, OSError) as exc:
        _fail(exc, output)
    _emit({"ok": True, "goal": state_payload(state)}, output)


@goal_app.command(name="verify")
def goal_verify(
    *,
    root: Path = Path("."),
    timeout_seconds: float = 300.0,
    output_limit: int = 64_000,
    output: Output = "text",
) -> None:
    """Run the active verifier once and persist PASS/active/exhausted evidence."""

    try:
        state = verify_goal(root, timeout_seconds=timeout_seconds, output_limit=output_limit)
    except (GoalError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    payload = {"ok": state.status == "passed", "goal": state_payload(state)}
    _emit(payload, output)
    if state.status != "passed":
        raise SystemExit(1)


@goal_app.command(name="resume")
def goal_resume(
    *,
    add_attempts: int = 0,
    max_attempts: int | None = None,
    root: Path = Path("."),
    output: Output = "text",
) -> None:
    """Resume an active goal or add budget to an exhausted goal."""

    try:
        state = resume_goal(root, add_attempts=add_attempts, max_attempts=max_attempts)
    except (GoalError, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit({"ok": True, "goal": state_payload(state)}, output)


@goal_app.command(name="clear")
def goal_clear(
    *,
    force: bool = False,
    root: Path = Path("."),
    output: Output = "text",
) -> None:
    """Remove terminal goal state; active state requires --force."""

    try:
        payload = clear_goal(root, force=force)
    except (GoalError, OSError) as exc:
        _fail(exc, output)
    _emit({"ok": True, **payload}, output)


@goal_app.command(name="tripwire")
def goal_tripwire(*, root: Path = Path("."), output: Output = "text") -> None:
    """Emit advisory Stop-hook status without blocking control flow."""

    try:
        payload = tripwire(root)
    except (GoalError, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit({"ok": True, **payload}, output)


@knowledge_app.command(name="status")
def knowledge_status_command(*, root: Path = Path("."), output: Output = "text") -> None:
    """Report whether broad canonical OKF tooling is available."""

    _emit({"ok": True, **knowledge_status(root)}, output)


@knowledge_app.command(name="validate")
def knowledge_validate_command(
    *,
    require_okn: bool = False,
    root: Path = Path("."),
    output: Output = "text",
) -> None:
    """Delegate broad validation to okn, or validate only the feature map."""

    try:
        payload = validate_knowledge(root, require_okn=require_okn)
    except (KnowledgeError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(payload, output)
    if not payload["ok"]:
        raise SystemExit(1)


@knowledge_app.command(name="search")
def knowledge_search_command(
    query: str,
    *,
    budget: int = 1_200,
    root: Path = Path("."),
    output: Output = "text",
) -> None:
    """Delegate broad project-knowledge search to okn."""

    try:
        payload = search_knowledge(root, query, budget=budget)
    except (KnowledgeError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(payload, output)
    if not payload["ok"]:
        raise SystemExit(1)


@upstream_app.command(name="check")
def upstream_check_command(
    *,
    manifest: Path = DEFAULT_MANIFEST,
    power_root: Path | None = None,
    source_id: str | None = None,
    root: Path = Path("."),
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    output: Output = "text",
) -> None:
    """Reprove pinned GitHub trees and report current drift and generated parity."""

    try:
        payload = check_upstreams(
            root,
            manifest=manifest,
            power_root=power_root,
            source_id=source_id,
            timeout_seconds=timeout_seconds,
        )
    except (OSError, UpstreamError, ValueError) as exc:
        _fail(exc, output)
    _emit(payload, output)
    if not payload["ok"]:
        raise SystemExit(1)


@upstream_app.command(name="accept")
def upstream_accept_command(
    *,
    expected_head: str,
    manifest: Path = DEFAULT_MANIFEST,
    power_root: Path,
    proposal: Path = DEFAULT_PROPOSAL,
    root: Path = Path("."),
    dry_run: bool = False,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    output: Output = "text",
) -> None:
    """Freshly reprove and atomically accept one reviewed upstream transition."""

    try:
        payload = accept_upstream(
            root,
            expected_head=expected_head,
            manifest=manifest,
            power_root=power_root,
            proposal=proposal,
            dry_run=dry_run,
            timeout_seconds=timeout_seconds,
        )
    except (OSError, UpstreamError, ValueError) as exc:
        _fail(exc, output)
    _emit(payload, output)


def main(argv: list[str] | None = None) -> None:
    """Dispatch projectctl, accepting explicit tokens for deterministic embedding and tests."""

    tokens = list(sys.argv[1:] if argv is None else argv)
    if not _requests_json(tokens):
        app(tokens)
        return
    try:
        app(tokens, print_error=False, exit_on_error=False)
    except CycloptsError as exc:
        _fail(exc, "json")


def _requests_json(tokens: list[str]) -> bool:
    return any(
        token == "--output=json"
        or (token == "--output" and index + 1 < len(tokens) and tokens[index + 1] == "json")
        for index, token in enumerate(tokens)
    )


if __name__ == "__main__":
    main()
