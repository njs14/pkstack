"""Integration diagnostics for a bootstrapped project."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pstack_kiro.bootstrap import (
    INTERNAL_WRAPPER,
    TARGET_PYPROJECT,
    audit_bootstrap_receipt,
    gitignore_has_entry,
)
from pstack_kiro.features import validate_feature_map
from pstack_kiro.goal import GoalError, GoalStore
from pstack_kiro.models import DoctorCheck
from pstack_kiro.paths import WorkspacePathError, ensure_tree_no_symlinks, workspace_path

KIRO_AGENT_TIMEOUT_SECONDS = 30
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
WORKSPACE_HEADER_RE = re.compile(r"^\s*Workspace:\s+\S.*$")
WORKSPACE_AGENT_ROW_RE = re.compile(
    r"^\s*(?:\*\s+)?(?P<name>[A-Za-z0-9][A-Za-z0-9_-]*)\s+Workspace(?:\s+.*)?$"
)
ARCHIFY_REQUIRED_RUNTIME_FILES = (
    "upstream/bin/archify.mjs",
    "upstream/bin/open-artifact.mjs",
    "upstream/bin/preview.mjs",
    "upstream/bin/visual-check.mjs",
    "upstream/assets/template.html",
    "upstream/scripts/check-render-output.mjs",
    "upstream/scripts/render-examples.mjs",
    "upstream/renderers/shared/generated-validators.mjs",
    "upstream/renderers/shared/output-path.mjs",
    "upstream/renderers/architecture/render-architecture.mjs",
    "upstream/renderers/dataflow/render-dataflow.mjs",
    "upstream/renderers/lifecycle/render-lifecycle.mjs",
    "upstream/renderers/sequence/render-sequence.mjs",
    "upstream/renderers/workflow/render-workflow.mjs",
    "upstream/schemas/architecture.schema.json",
    "upstream/schemas/dataflow.schema.json",
    "upstream/schemas/lifecycle.schema.json",
    "upstream/schemas/sequence.schema.json",
    "upstream/schemas/workflow.schema.json",
)
ARCHIFY_NODE_MIN_MAJOR = 18


def run_doctor(root: Path) -> dict[str, Any]:
    root = root.resolve()
    checks: list[DoctorCheck] = []

    checks.append(
        DoctorCheck(
            "project-root",
            "pass" if root.is_dir() else "fail",
            str(root),
            None if root.is_dir() else "Choose an existing project directory.",
        )
    )
    checks.append(_command_check("uv", required=True))
    checks.append(_command_check("kiro-cli", required=False))
    checks.append(_command_check("okn", required=False))

    # Discovery is a local, no-model loader probe. Keep it ahead of every
    # per-profile Kiro invocation so doctor never mistakes schema validity for
    # evidence that the current runtime can actually select the profiles.
    kiro_executable = shutil.which("kiro-cli")
    if kiro_executable:
        checks.append(_kiro_agent_discovery_check(kiro_executable, root))

    wrapper = root / "projectctl"
    try:
        internal = workspace_path(root, Path(".pstack/bin/projectctl"))
        internal_error = None
    except WorkspacePathError as exc:
        internal = root / ".pstack" / "bin" / "projectctl"
        internal_error = str(exc)
    if internal_error is None and internal.is_file() and os.access(internal, os.X_OK):
        checks.append(DoctorCheck("projectctl", "pass", "executable internal projectctl present"))
    else:
        checks.append(
            DoctorCheck(
                "projectctl",
                "fail",
                internal_error or "executable .pstack/bin/projectctl entrypoint is missing",
                "Run /setup-pk-stack or pk-stack-setup in this project.",
            )
        )
    checks.append(_receipt_integrity_check(root))
    checks.append(_runtime_integrity_check(root, internal))
    if wrapper.exists() and not (wrapper.is_file() and os.access(wrapper, os.X_OK)):
        checks.append(
            DoctorCheck(
                "root-projectctl",
                "warn",
                "root projectctl is not an executable file; use .pstack/bin/projectctl",
            )
        )

    required_assets = {
        "pk-stack-agent": root / ".kiro" / "agents" / "pk-stack.json",
        "architect-agent": root / ".kiro" / "agents" / "pk-stack-architect.json",
        "reviewer-agent": root / ".kiro" / "agents" / "pk-stack-reviewer.json",
        "verifier-agent": root / ".kiro" / "agents" / "pk-stack-verifier.json",
        "pk-stack-core-steering": root / ".kiro" / "steering" / "pk-stack-core.md",
        "pk-stack-safety-steering": root / ".kiro" / "steering" / "pk-stack-safety.md",
        "pk-stack-typescript-steering": root / ".kiro" / "steering" / "pk-stack-typescript.md",
        "pk-stack-unslop-steering": root / ".kiro" / "steering" / "pk-stack-unslop.md",
        "session-hook": root / ".kiro" / "hooks" / "pk-stack-session.json",
        "tripwire-hook": root / ".kiro" / "hooks" / "pk-stack-tripwire.json",
    }
    try:
        cached_skills = ensure_tree_no_symlinks(
            root,
            Path(".pstack/projectctl/skills"),
        )
        skill_names = sorted(
            path.name
            for path in cached_skills.iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        )
    except (OSError, WorkspacePathError) as exc:
        checks.append(
            DoctorCheck(
                "workspace-skill-inventory",
                "fail",
                f"unable to enumerate managed skills safely: {exc}",
                "Repair the receipt-managed projectctl skill cache.",
            )
        )
        skill_names = []
    if "archify" in skill_names:
        checks.append(_archify_runtime_check(root))
        checks.append(_archify_node_check())
    for skill in skill_names:
        if skill == "setup-pk-stack":
            continue
        required_assets[f"{skill}-skill"] = root / ".kiro" / "skills" / skill / "SKILL.md"

    for name, path in required_assets.items():
        try:
            safe_path = workspace_path(root, path)
        except WorkspacePathError as exc:
            checks.append(DoctorCheck(name, "fail", str(exc), "Replace symlinked Kiro paths."))
            continue
        checks.append(
            DoctorCheck(
                name,
                "pass" if safe_path.is_file() else "fail",
                f"{safe_path.relative_to(root)} {'present' if safe_path.is_file() else 'missing'}",
                (
                    None
                    if safe_path.is_file()
                    else "Re-run /setup-pk-stack; foreign files are preserved."
                ),
            )
        )
        if safe_path.is_file():
            checks.append(_asset_integrity_check(root, safe_path, name))
        if safe_path.suffix == ".json" and safe_path.is_file():
            try:
                document = json.loads(safe_path.read_text(encoding="utf-8"))
                _validate_kiro_json(safe_path, document)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                checks.append(DoctorCheck(f"{name}-json", "fail", f"invalid JSON: {exc}"))
                continue
            if (
                safe_path.parent.name == "agents"
                and kiro_executable
                and Path(kiro_executable).is_file()
            ):
                checks.append(_kiro_agent_check(kiro_executable, safe_path, name))

    feature_result: dict[str, Any]
    try:
        feature_result = validate_feature_map(root)
    except (OSError, ValueError) as exc:
        feature_result = {
            "ok": False,
            "feature_count": 0,
            "features": [],
            "errors": [str(exc)],
            "warnings": [],
        }
    checks.append(
        DoctorCheck(
            "feature-map",
            "pass" if feature_result["ok"] else "fail",
            (
                f"{feature_result['feature_count']} feature contract(s); "
                f"{len(feature_result['errors'])} error(s), "
                f"{len(feature_result['warnings'])} warning(s)"
            ),
            None if feature_result["ok"] else "Run projectctl feature validate for details.",
        )
    )

    ignore_check = _runtime_state_ignored(root)
    checks.append(ignore_check)
    checks.append(_goal_state_check(root))

    summary = {
        "pass": sum(check.status == "pass" for check in checks),
        "warn": sum(check.status == "warn" for check in checks),
        "fail": sum(check.status == "fail" for check in checks),
    }
    return {
        "ok": summary["fail"] == 0,
        "root": str(root),
        "summary": summary,
        "checks": [check.to_dict() for check in checks],
        "feature_map": feature_result,
    }


def _validate_kiro_json(path: Path, document: Any) -> None:
    if not isinstance(document, dict):
        raise ValueError("top level must be an object")
    if path.parent.name == "agents":
        if document.get("name") != path.stem:
            raise ValueError("agent name must match its file name")
        if not isinstance(document.get("tools"), list) or not document["tools"]:
            raise ValueError("agent tools must be a non-empty list")
        if not isinstance(document.get("permissions", {}).get("rules"), list):
            raise ValueError("agent permissions.rules must be a list")
    elif path.parent.name == "hooks":
        if document.get("version") != "v1":
            raise ValueError("hook version must be v1")
        hooks = document.get("hooks")
        if not isinstance(hooks, list) or not hooks:
            raise ValueError("hooks must be a non-empty list")
        if any(
            not isinstance(hook, dict) or "trigger" not in hook or "action" not in hook
            for hook in hooks
        ):
            raise ValueError("every hook requires trigger and action")


def _runtime_integrity_check(root: Path, internal: Path) -> DoctorCheck:
    pyproject = root / ".pstack" / "projectctl" / "pyproject.toml"
    lock = root / ".pstack" / "projectctl" / "uv.lock"
    cached_lock = root / ".pstack" / "projectctl" / "templates" / "projectctl" / "uv.lock"
    try:
        paths = [workspace_path(root, path) for path in (internal, pyproject, lock, cached_lock)]
        expected = [
            INTERNAL_WRAPPER.encode(),
            TARGET_PYPROJECT.encode(),
            paths[3].read_bytes(),
        ]
        actual = [paths[0].read_bytes(), paths[1].read_bytes(), paths[2].read_bytes()]
    except (OSError, ValueError) as exc:
        return DoctorCheck(
            "projectctl-runtime-integrity",
            "fail",
            f"unable to validate managed runtime: {exc}",
            "Re-run the Power-local setup preflight and repair managed files.",
        )
    return DoctorCheck(
        "projectctl-runtime-integrity",
        "pass" if actual == expected else "fail",
        (
            "managed wrapper, project metadata, and lock are consistent"
            if actual == expected
            else "managed wrapper, project metadata, or lock differs from the shipped runtime"
        ),
        None if actual == expected else "Review setup conflicts before --update-managed.",
    )


def _receipt_integrity_check(root: Path) -> DoctorCheck:
    try:
        audit = audit_bootstrap_receipt(root)
    except (OSError, ValueError) as exc:
        return DoctorCheck(
            "bootstrap-receipt-integrity",
            "fail",
            f"unable to validate bootstrap ownership receipt: {exc}",
            "Run the Power-local setup preflight and repair managed files.",
        )
    if audit.ok:
        return DoctorCheck(
            "bootstrap-receipt-integrity",
            "pass",
            f"all {audit.managed_count} receipt-managed files match recorded hashes",
        )

    failures: list[str] = []
    for label, paths in (
        ("missing or non-file", audit.missing),
        ("hash mismatch", audit.hash_mismatches),
        ("unsafe or unreadable", audit.unsafe_or_unreadable),
    ):
        if paths:
            displayed = ", ".join(paths[:5])
            remainder = len(paths) - 5
            if remainder > 0:
                displayed = f"{displayed}, and {remainder} more"
            failures.append(f"{label} ({len(paths)}): {displayed}")
    return DoctorCheck(
        "bootstrap-receipt-integrity",
        "fail",
        f"checked {audit.managed_count} receipt-managed files; " + "; ".join(failures),
        "Review setup conflicts and restore receipt-owned files from the reviewed Power.",
    )


def _asset_integrity_check(root: Path, live: Path, name: str) -> DoctorCheck:
    relative = live.relative_to(root)
    if relative.parts[:2] == (".kiro", "skills"):
        cached_relative = Path(".pstack/projectctl/skills").joinpath(*relative.parts[2:])
    elif relative.parts[:2] == (".kiro", "steering"):
        cached_relative = Path(".pstack/projectctl/dev.kiro/steering").joinpath(*relative.parts[2:])
    else:
        cached_relative = Path(".pstack/projectctl/templates/project") / relative
    try:
        cached = workspace_path(root, cached_relative)
        matches = cached.is_file() and live.read_bytes() == cached.read_bytes()
    except (OSError, ValueError) as exc:
        return DoctorCheck(f"{name}-managed-integrity", "fail", str(exc))
    return DoctorCheck(
        f"{name}-managed-integrity",
        "pass" if matches else "fail",
        "live asset matches managed cache" if matches else "live asset differs from managed cache",
        None if matches else "Review the setup conflict; do not overwrite user changes silently.",
    )


def _goal_state_check(root: Path) -> DoctorCheck:
    try:
        state = GoalStore(root).load()
    except (GoalError, OSError, ValueError) as exc:
        return DoctorCheck(
            "goal-state",
            "fail",
            f"invalid goal state: {exc}",
            "Inspect .pstack/state/goal.json; do not discard active evidence automatically.",
        )
    if state is None:
        return DoctorCheck("goal-state", "pass", "no persisted goal state")
    return DoctorCheck(
        "goal-state",
        "pass",
        f"valid {state.status} goal {state.goal_id} with {state.attempt_count} attempt(s)",
    )


def _kiro_agent_check(executable: str, path: Path, name: str) -> DoctorCheck:
    try:
        completed = subprocess.run(
            [executable, "agent", "validate", "--path", str(path)],
            capture_output=True,
            text=True,
            timeout=KIRO_AGENT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return DoctorCheck(f"{name}-kiro-validate", "fail", f"Kiro validation failed: {exc}")
    message = (completed.stderr or completed.stdout).strip()
    return DoctorCheck(
        f"{name}-kiro-validate",
        "pass" if completed.returncode == 0 else "fail",
        message or f"kiro-cli accepted {path.name}",
    )


def _kiro_agent_discovery_check(executable: str, root: Path) -> DoctorCheck:
    """Require every safe workspace profile to appear in Kiro's loader output."""

    root = root.resolve()
    try:
        expected = _workspace_agent_names(root)
    except (OSError, ValueError, WorkspacePathError) as exc:
        return DoctorCheck(
            "kiro-workspace-agent-discovery",
            "fail",
            f"unable to derive workspace agents safely: {exc}",
            "Repair .kiro/agents before starting an authenticated Kiro session.",
        )

    try:
        completed = subprocess.run(
            [executable, "agent", "list"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=KIRO_AGENT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return DoctorCheck(
            "kiro-workspace-agent-discovery",
            "fail",
            f"kiro-cli agent list timed out after {KIRO_AGENT_TIMEOUT_SECONDS} seconds",
            "Retry the local no-model discovery probe before authenticated use.",
        )
    except OSError as exc:
        return DoctorCheck(
            "kiro-workspace-agent-discovery",
            "fail",
            f"kiro-cli agent list could not run: {exc}",
            "Repair the local Kiro CLI installation and retry.",
        )

    if completed.returncode != 0:
        return DoctorCheck(
            "kiro-workspace-agent-discovery",
            "fail",
            f"kiro-cli agent list exited {completed.returncode}",
            "Run the same command from the project root and repair loader errors.",
        )

    # Kiro CLI 2.21 renders `agent list` to stderr when it owns a terminal-style
    # renderer. Test both captured streams as one bounded loader transcript;
    # neither stream is surfaced in the doctor payload.
    agent_list_output = "\n".join(
        stream for stream in (completed.stdout, completed.stderr) if stream
    )
    try:
        discovered = _parse_workspace_agent_rows(agent_list_output)
    except ValueError as exc:
        return DoctorCheck(
            "kiro-workspace-agent-discovery",
            "fail",
            f"malformed kiro-cli agent list output: {exc}",
            "Treat schema validation as insufficient; inspect the local loader output.",
        )

    missing = sorted(expected - discovered)
    if missing:
        return DoctorCheck(
            "kiro-workspace-agent-discovery",
            "fail",
            "workspace agents missing from kiro-cli agent list: " + ", ".join(missing),
            "Repair agent discovery before starting an authenticated Kiro session.",
        )

    extras = sorted(discovered - expected)
    message = f"discovered all {len(expected)} workspace agent profile(s): " + ", ".join(
        sorted(expected)
    )
    if extras:
        message += "; additional Workspace rows: " + ", ".join(extras)
    return DoctorCheck("kiro-workspace-agent-discovery", "pass", message)


def _workspace_agent_names(root: Path) -> set[str]:
    """Derive exact expected loader names from safe project-local JSON profiles."""

    agents = ensure_tree_no_symlinks(root, Path(".kiro/agents"))
    if not agents.is_dir():
        raise ValueError(".kiro/agents is not a directory")
    profiles = sorted(agents.glob("*.json"))
    if not profiles:
        raise ValueError(".kiro/agents contains no JSON profiles")

    names: set[str] = set()
    for profile in profiles:
        safe_profile = workspace_path(root, profile)
        if not safe_profile.is_file():
            raise ValueError(f"{safe_profile.name} is not a regular profile file")
        document = json.loads(safe_profile.read_text(encoding="utf-8"))
        if not isinstance(document, dict) or document.get("name") != safe_profile.stem:
            raise ValueError(f"{safe_profile.name} has no exact file-matching agent name")
        name = safe_profile.stem
        if name in names:
            raise ValueError(f"duplicate workspace agent name: {name}")
        names.add(name)
    return names


def _parse_workspace_agent_rows(output: str) -> set[str]:
    """Strip terminal control sequences and parse exact Workspace-scoped rows."""

    if not isinstance(output, str):
        raise ValueError("stdout was not text")
    normalized = ANSI_ESCAPE_RE.sub("", output).replace("\r", "")
    lines = normalized.splitlines()
    headers = [line for line in lines if WORKSPACE_HEADER_RE.fullmatch(line)]
    if len(headers) != 1:
        raise ValueError("expected exactly one Workspace path header")

    names: set[str] = set()
    row_count = 0
    for line in lines:
        match = WORKSPACE_AGENT_ROW_RE.fullmatch(line)
        if match is None:
            continue
        row_count += 1
        name = match.group("name")
        if name in names:
            raise ValueError(f"duplicate Workspace row for {name}")
        names.add(name)
    if row_count == 0:
        raise ValueError("no exact Workspace rows")
    return names


def _command_check(name: str, *, required: bool) -> DoctorCheck:
    executable = shutil.which(name)
    if executable:
        return DoctorCheck(name, "pass", executable)
    if required:
        return DoctorCheck(name, "fail", f"{name} is unavailable", f"Install {name} and retry.")
    return DoctorCheck(
        name,
        "warn",
        f"{name} is unavailable",
        f"Install {name} only if this project uses that optional integration.",
    )


def _archify_runtime_check(root: Path) -> DoctorCheck:
    """Check the reviewed offline Archify runtime closure without executing it."""

    runtime = Path(".pstack/projectctl/skills/archify")
    try:
        runtime_root = ensure_tree_no_symlinks(root, runtime)
        missing = [
            relative
            for relative in ARCHIFY_REQUIRED_RUNTIME_FILES
            if not (runtime_root / relative).is_file()
        ]
    except (OSError, WorkspacePathError) as exc:
        return DoctorCheck(
            "archify-runtime",
            "fail",
            f"unable to inspect the managed Archify runtime safely: {exc}",
            "Re-run /setup-pk-stack and restore the reviewed Archify bundle.",
        )
    if missing:
        return DoctorCheck(
            "archify-runtime",
            "fail",
            "managed Archify runtime is incomplete: " + ", ".join(missing),
            "Re-run /setup-pk-stack and restore the reviewed Archify bundle.",
        )
    return DoctorCheck(
        "archify-runtime",
        "pass",
        "offline Archify runtime is complete "
        f"({len(ARCHIFY_REQUIRED_RUNTIME_FILES)} required files)",
    )


def _archify_node_check() -> DoctorCheck:
    """Report Node as an optional capability because Archify is shipped offline."""

    executable = shutil.which("node")
    if not executable:
        return DoctorCheck(
            "archify-node",
            "warn",
            "Node.js is unavailable; optional Archify execution is unavailable",
            "Install Node.js 18 or newer to use Archify validate/deliver/visual-check.",
        )
    try:
        completed = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return DoctorCheck(
            "archify-node",
            "warn",
            f"Node.js version probe failed: {exc}",
            "Install or repair Node.js 18 or newer before using Archify.",
        )
    output = (completed.stdout or completed.stderr).strip()
    version = output.splitlines()[0] if output else ""
    match = re.match(r"^v(?P<major>\d+)(?:\.\d+){0,2}$", version)
    if completed.returncode != 0 or match is None:
        return DoctorCheck(
            "archify-node",
            "warn",
            f"Node.js version is unavailable or invalid: {version or 'no version output'}",
            "Install or repair Node.js 18 or newer before using Archify.",
        )
    major = int(match.group("major"))
    if major < ARCHIFY_NODE_MIN_MAJOR:
        return DoctorCheck(
            "archify-node",
            "warn",
            f"Node.js {version} is below the optional Archify requirement (>=18)",
            "Install Node.js 18 or newer before using Archify.",
        )
    return DoctorCheck(
        "archify-node",
        "pass",
        f"Node.js {version} supports optional Archify execution",
    )


def _runtime_state_ignored(root: Path) -> DoctorCheck:
    try:
        git_path = workspace_path(root, Path(".git"))
        gitignore = workspace_path(root, Path(".gitignore"))
        if not git_path.exists():
            ignored = gitignore.is_file() and gitignore_has_entry(
                gitignore.read_text(encoding="utf-8"),
                ".pstack/state/",
            )
        else:
            completed = subprocess.run(
                ["git", "check-ignore", "-q", ".pstack/state/goal.json"],
                cwd=root,
                capture_output=True,
                check=False,
            )
            ignored = completed.returncode == 0
    except (OSError, ValueError) as exc:
        return DoctorCheck("ephemeral-goal-state", "fail", str(exc), "Repair project paths.")
    return DoctorCheck(
        "ephemeral-goal-state",
        "pass" if ignored else "fail",
        ".pstack/state/ is ignored" if ignored else ".pstack/state/ is not ignored",
        None if ignored else "Add .pstack/state/ to .gitignore.",
    )
