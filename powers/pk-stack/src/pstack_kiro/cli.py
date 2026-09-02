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
from pstack_kiro.features import (
    FeatureMapError,
    find_feature,
    find_verifiable_feature,
    generate_feature,
    list_features,
    prepare_feature,
    validate_feature_map,
)
from pstack_kiro.goal import (
    GoalError,
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
from pstack_kiro.models import CommandSpec
from pstack_kiro.runner import CommandRejected, display_command, parse_command, run_command

Output = Literal["text", "json"]

app = App(name="projectctl", help="Operate and prove this project through stable semantics.")
feature_app = App(help="Manage narrow executable feature-map contracts.")
goal_app = App(help="Persist and verify a bounded current-session goal.")
knowledge_app = App(help="Use canonical OKF tooling when broader project knowledge is needed.")
app.command(feature_app, name="feature")
app.command(goal_app, name="goal")
app.command(knowledge_app, name="knowledge")


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
                "/setup-pstack skill for setup or refresh, or pass a reviewed "
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


@feature_app.command(name="generate")
def feature_generate(
    slug: str,
    *,
    title: str,
    behavior: str,
    expected_path: str,
    command: str | None = None,
    related: list[str] | None = None,
    ready: bool = False,
    overwrite: bool = False,
    root: Path = Path("."),
    timeout_seconds: float = 300.0,
    output: Output = "text",
) -> None:
    """Generate a draft contract, or prove its command before marking it ready."""

    try:
        prepare_feature(
            root,
            slug,
            title=title,
            behavior=behavior,
            expected_path=expected_path,
            command=command,
            related=related or (),
            draft=not ready,
            overwrite=overwrite,
        )
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
        path = generate_feature(
            root,
            slug,
            title=title,
            behavior=behavior,
            expected_path=expected_path,
            command=command,
            related=related or (),
            draft=not ready,
            overwrite=overwrite,
        )
    except (FeatureMapError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    payload = {"ok": True, "path": str(path), "draft": not ready}
    if proof is not None:
        payload["initial_verification"] = proof.to_dict()
    _emit(payload, output)


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
    root: Path = Path("."),
    output: Output = "text",
) -> None:
    """Delegate broad project-knowledge search to okn."""

    try:
        payload = search_knowledge(root, query)
    except (KnowledgeError, CommandRejected, OSError, ValueError) as exc:
        _fail(exc, output)
    _emit(payload, output)
    if not payload["ok"]:
        raise SystemExit(1)


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
