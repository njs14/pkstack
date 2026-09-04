from __future__ import annotations

import json
import os
import re
import runpy
import shutil
import subprocess
import sys
from collections import Counter
from fnmatch import fnmatchcase
from pathlib import Path

import pytest
import yaml

from pstack_kiro.branding import DISPLAY_NAME, EXPANDED_NAME, POWER_ID

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
AGENTS = ROOT / "templates" / "project" / ".kiro" / "agents"
HOOKS = ROOT / "templates" / "project" / ".kiro" / "hooks"
STEERING = ROOT / "dev.kiro" / "steering"
PARITY_PATH = ROOT / "docs" / "upstream-skill-parity.json"
PARITY = json.loads(PARITY_PATH.read_text(encoding="utf-8"))
PARITY_SKILLS = PARITY["skills"]
PK_ONLY_SKILLS = set(PARITY["pk_only_skills"])
CURATED_REGISTRY_PATH = ROOT / "docs" / "curated-skills.json"
CURATED_REGISTRY = json.loads(CURATED_REGISTRY_PATH.read_text(encoding="utf-8"))
CURATED_SKILLS = {entry["name"] for entry in CURATED_REGISTRY["skills"]}
EXPECTED_SKILLS = (
    {Path(entry["target"]).parent.name for entry in PARITY_SKILLS if entry["target"] is not None}
    | PK_ONLY_SKILLS
    | CURATED_SKILLS
)
REPO_ROOT = ROOT.parents[1]
ALLOWED_SKILL_FRONTMATTER = {"name", "description", "compatibility"}
ALLOWED_TOOLS = {"read", "write", "shell", "subagent", "knowledge"}
ALLOWED_HOOK_TRIGGERS = {
    "PostFileSave",
    "PostFileCreate",
    "PostFileDelete",
    "PreToolUse",
    "PostToolUse",
    "UserPromptSubmit",
    "SessionStart",
    "Stop",
    "PreTaskExec",
    "PostTaskExec",
}


def _frontmatter(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter"
    _, raw, body = text.split("---", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed, body.strip()


def _all_asset_text() -> str:
    paths = [
        *SKILLS.rglob("*.md"),
        *STEERING.glob("*.md"),
        *AGENTS.glob("*.json"),
        *HOOKS.glob("*.json"),
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_power_manifest_uses_agent_plugins_format() -> None:
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert manifest["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert manifest["name"] == POWER_ID
    assert manifest["description"].startswith(f"{DISPLAY_NAME} ({EXPANDED_NAME}):")
    assert manifest["version"]
    assert manifest["description"]
    assert isinstance(manifest["keywords"], list) and manifest["keywords"]
    assert {"Kiro CLI", "Kiro IDE", "Kiro Crew", "Kiro Web"} <= set(manifest["keywords"])


@pytest.mark.parametrize("skill_name", sorted(EXPECTED_SKILLS))
def test_skill_frontmatter_matches_agent_skills_standard(skill_name: str) -> None:
    path = SKILLS / skill_name / "SKILL.md"
    metadata, body = _frontmatter(path)

    assert metadata["name"] == skill_name
    assert set(metadata) <= ALLOWED_SKILL_FRONTMATTER
    assert isinstance(metadata["description"], str)
    assert 20 <= len(metadata["description"]) <= 1024
    compatibility = metadata["compatibility"]
    assert isinstance(compatibility, str)
    for surface in ("Kiro IDE 1.x", "Kiro CLI v3", "Kiro Crew", "Kiro Web"):
        assert surface in compatibility
    if skill_name == "setup-pk-stack":
        assert "committed post-bootstrap assets" in compatibility
        assert "rather than invoking this setup skill" in compatibility
    else:
        assert "supported by design but untested" in compatibility
    assert body


def test_only_expected_skill_directories_are_present() -> None:
    actual = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert actual == EXPECTED_SKILLS


def test_compatibility_document_inventory_counts_match_assets() -> None:
    text = (ROOT / "docs" / "kiro-v3-compatibility.md").read_text(encoding="utf-8")
    upstreams = json.loads(
        (REPO_ROOT / "maintenance" / "upstreams.json").read_text(encoding="utf-8")
    )["sources"]
    workspace_agents = list((REPO_ROOT / ".kiro" / "agents").glob("*.json"))
    shipped_agents = list(AGENTS.glob("*.json"))
    materialized_skills = EXPECTED_SKILLS - {"setup-pk-stack"}

    assert f"The {len(upstreams)} source entries in `maintenance/upstreams.json`" in text
    assert f"validates all {len(workspace_agents)} workspace-agent files" in text
    assert f"The other {len(materialized_skills)} workflow skills" in text
    assert f"all {len(shipped_agents)} shipped Power profiles" in text
    assert "`pstack-maintainer` and `pstack-ci-reviewer` CI profiles" in text


def test_upstream_skill_parity_inventory_is_complete_and_rendered() -> None:
    raw_parity = PARITY_PATH.read_text(encoding="utf-8")
    decoded, end = json.JSONDecoder().raw_decode(raw_parity)
    assert isinstance(decoded, dict)
    assert raw_parity[end:].strip() == ""
    assert set(PARITY) == {
        "schema_version",
        "source",
        "allowed_dispositions",
        "allowed_resource_handling",
        "pk_only_skills",
        "summary",
        "skills",
    }
    assert PARITY["schema_version"] == 1
    assert PARITY["source"]["id"] == "cursor-pstack"
    assert PARITY["source"]["repository"] == "cursor/plugins"
    assert PARITY["source"]["path"] == "pstack"
    assert PARITY["source"]["catalog_path"] == "skills"
    for revision in ("pinned", "current"):
        identity = PARITY["source"][revision]
        assert set(identity) == {"commit", "pstack_subtree_sha"}
        assert re.fullmatch(r"[0-9a-f]{40}", identity["commit"])
        assert re.fullmatch(r"[0-9a-f]{40}", identity["pstack_subtree_sha"])

    names = [entry["name"] for entry in PARITY_SKILLS]
    assert names == sorted(names)
    assert len(names) == len(set(names)) == PARITY["summary"]["upstream_total"]
    assert set(PARITY["allowed_dispositions"]) == {
        "direct-port",
        "alias-consolidation",
        "native-kiro-replacement",
        "excluded",
    }
    assert set(PARITY["allowed_resource_handling"]) == {
        "semantic-source",
        "helper-semantics-only",
        "runtime-specific-exclusion",
    }
    assert list(PARITY["pk_only_skills"]) == sorted(PK_ONLY_SKILLS)
    assert not PK_ONLY_SKILLS & set(names)
    counts = Counter(entry["disposition"] for entry in PARITY_SKILLS)
    for disposition in PARITY["allowed_dispositions"]:
        assert counts[disposition] == PARITY["summary"][disposition]

    excluded = [entry for entry in PARITY_SKILLS if entry["disposition"] == "excluded"]
    assert len(excluded) == 1
    assert excluded[0]["name"] == "make-bot-ui"
    assert excluded[0]["target"] is None
    exclusion = " ".join((excluded[0]["rationale"], excluded[0]["safe_alternative"]))
    for phrase in ("Cursor/Grok Bot", "secret-card APIs", "cursor.sh", "sudo/Tailscale"):
        assert phrase in exclusion

    routed = [entry for entry in PARITY_SKILLS if entry["target"] is not None]
    assert len(routed) == PARITY["summary"]["routed_upstream_names"]
    resource_counts: Counter[str] = Counter()
    package_file_counts: dict[str, int] = {"pinned": 0, "current": 0}
    for entry in PARITY_SKILLS:
        if entry["target"] is not None:
            target = ROOT / entry["target"]
            route_name = {"setup-pstack": "setup-pk-stack"}.get(entry["name"], entry["name"])
            assert target == SKILLS / route_name / "SKILL.md"
            assert target.is_file()
        for revision in ("pinned", "current"):
            package = entry[revision]
            assert set(package) == {"package_tree_sha", "files"}
            assert re.fullmatch(r"[0-9a-f]{40}", package["package_tree_sha"])
            files = package["files"]
            paths = [resource["path"] for resource in files]
            assert paths == sorted(set(paths), key=str.casefold)
            assert paths.count("SKILL.md") == 1
            for resource in files:
                assert set(resource) == {"path", "blob_sha", "size", "mode", "handling"}
                resource_path = Path(resource["path"])
                assert not resource_path.is_absolute()
                assert resource_path.as_posix() == resource["path"]
                assert ".." not in resource_path.parts
                assert re.fullmatch(r"[0-9a-f]{40}", resource["blob_sha"])
                assert type(resource["size"]) is int and resource["size"] >= 0
                assert resource["mode"] in {"100644", "100755"}
                assert resource["handling"] in PARITY["allowed_resource_handling"]
                if revision == "current":
                    resource_counts[resource["handling"]] += 1
            package_file_counts[revision] += len(files)
    assert package_file_counts == {
        "pinned": PARITY["summary"]["pinned_package_files"],
        "current": PARITY["summary"]["current_package_files"],
    }
    assert resource_counts == Counter(
        {
            "semantic-source": PARITY["summary"]["semantic_source_files"],
            "helper-semantics-only": PARITY["summary"]["helper_semantics_only_files"],
            "runtime-specific-exclusion": PARITY["summary"]["runtime_specific_exclusion_files"],
        }
    )
    assert len(EXPECTED_SKILLS - CURATED_SKILLS) == PARITY["summary"]["shipped_skill_directories"]

    rendered = (ROOT / "docs" / "upstream-skill-parity.md").read_text(encoding="utf-8")
    assert r"\n|" not in rendered
    rows = [line for line in rendered.splitlines() if line.startswith("| `")]
    assert len(rows) == len(PARITY_SKILLS)
    for name in names:
        assert sum(line.startswith(f"| `{name}` |") for line in rows) == 1


def test_load_bearing_upstream_skill_packages_are_routed_by_their_real_names() -> None:
    by_name = {entry["name"]: entry for entry in PARITY_SKILLS}

    assert "create-verification-skill" in by_name
    assert "install-verification-skill" not in by_name
    create = by_name["create-verification-skill"]
    assert create["disposition"] == "direct-port"
    assert create["target"] == "skills/create-verification-skill/SKILL.md"
    assert {resource["path"]: resource["handling"] for resource in create["current"]["files"]} == {
        "references/feature-map-example/create-note.md": "semantic-source",
        "references/feature-map-example/README.md": "semantic-source",
        "references/feature-map-example/search.md": "semantic-source",
        "SKILL.md": "semantic-source",
    }

    setup = by_name["setup-pstack"]
    assert setup["disposition"] == "native-kiro-replacement"
    assert setup["target"] == "skills/setup-pk-stack/SKILL.md"
    assert [(resource["path"], resource["handling"]) for resource in setup["current"]["files"]] == [
        ("SKILL.md", "semantic-source")
    ]
    assert "role-model rule" in setup["rationale"]
    assert "inheritance of the user's selected Kiro model and effort" in setup["rationale"]

    poteto = by_name["poteto-mode"]
    assert poteto["disposition"] == "alias-consolidation"
    assert poteto["target"] == "skills/poteto-mode/SKILL.md"
    poteto_resources = {
        resource["path"]: resource["handling"] for resource in poteto["current"]["files"]
    }
    assert {
        "playbooks/authoring-a-skill.md",
        "playbooks/autonomous-run.md",
        "playbooks/autopilot-full.md",
        "playbooks/autopilot-stack.md",
        "playbooks/babysit.md",
        "playbooks/bug-fix.md",
        "playbooks/eval.md",
        "playbooks/feature.md",
        "playbooks/hillclimb.md",
        "playbooks/investigation.md",
        "playbooks/multi-phase-plan.md",
        "playbooks/opening-a-pr.md",
        "playbooks/orchestrate.md",
        "playbooks/pause-safely.md",
        "playbooks/perf-issue.md",
        "playbooks/prototype.md",
        "playbooks/refactoring.md",
        "playbooks/runtime-forensics.md",
        "playbooks/session-pickup.md",
        "playbooks/shipping.md",
        "playbooks/trace-forensics.md",
        "playbooks/visual-parity.md",
        "playbooks/worktree-cleanup.md",
        "references/bugbot-triage.md",
        "SKILL.md",
    } == {path for path, handling in poteto_resources.items() if handling == "semantic-source"}
    assert {
        path for path, handling in poteto_resources.items() if handling == "helper-semantics-only"
    } == {"scripts/check-plan.mjs", "scripts/worktree-audit.sh"}
    assert (
        sum(handling == "runtime-specific-exclusion" for handling in poteto_resources.values())
        == 18
    )


def test_ported_skill_bodies_keep_high_value_upstream_contracts() -> None:
    create = (SKILLS / "create-verification-skill" / "SKILL.md").read_text()
    normalized_create = " ".join(create.split())
    for phrase in (
        "**launch**",
        "**doctor**",
        "**drive**",
        "**evidence**",
        "**isolation and cleanup**",
        "**helpers**",
        "three to five user-meaningful features",
        "every sub-feature",
        "every user entrypoint",
        "`sub_features`",
        "`entrypoints`",
        "`gotchas`",
        "`evidence_boundary`",
        "`cleanup_boundary`",
        "feature generate-map <plan.json>",
        "--representative <slug> --output json",
        "executes exactly the representative's stored verifier",
        "leaves every other record draft",
        "feature publish",
    ):
        assert phrase in normalized_create

    work_log = (SKILLS / "show-me-your-work" / "SKILL.md").read_text()
    normalized_work_log = " ".join(work_log.split())
    for phrase in (
        "projectctl evidence append <slug>",
        "--verdict VERIFIED|NOT VERIFIED|INCONCLUSIVE",
        ".pstack/state/evidence/<slug>/decision-log.jsonl",
        "uncommitted by default",
        "only when the user explicitly requests",
        "--committed",
        "--target Wiki/evidence/<slug>/decision-log.jsonl",
        "`schema_version`",
        "`sequence`",
        "`timestamp`",
        "`verdict`",
        "preserves the prior byte prefix",
        "workflow convention with deterministic validation, not a signed or tamper-proof log",
        "projectctl evidence audit <slug> --output json",
        "not private transcripts",
    ):
        assert phrase in normalized_work_log
    figure = (SKILLS / "figure-it-out" / "SKILL.md").read_text()
    assert "show-me-your-work" in figure and "append" in figure

    maintain = (SKILLS / "maintain-verification-skill" / "SKILL.md").read_text()
    normalized_maintain = " ".join(maintain.split())
    for phrase in (
        "feature migrate <slug> --output json",
        "exactly one recovery retry",
        "verified-unreachable",
        "single coordinator",
        "feature publish <slug> --output json",
        "changes draft state only after it passes",
        "Treat that as the first proof",
        "feature verify <slug> --output json` once more",
        "Never hand-edit `draft: false`",
        "one reviewed pull request rather than one per feature",
    ):
        assert phrase in normalized_maintain

    how = (SKILLS / "how" / "SKILL.md").read_text()
    assert "## Critique mode" in how
    comments = (SKILLS / "no-comments" / "SKILL.md").read_text()
    assert "fresh native Kiro sub-agent" in comments
    normalized_comments = " ".join(comments.split())
    for phrase in (
        "current diff against the base branch",
        "defaulting to `main`",
        "index and working tree",
        "use `how` or `why` on the symbol",
        "run exactly one fresh review again",
        "stop this workflow as failed",
        "Wait for explicit approval",
        "exact deletion count",
        "every restored comment with evidence",
    ):
        assert phrase in normalized_comments
    teach = (SKILLS / "teach" / "SKILL.md").read_text()
    normalized_teach = " ".join(teach.split())
    assert "Do not quiz the user" in normalized_teach
    for phrase in (
        "apply the `how` skill",
        "the `why` skill",
        "real skill applications",
        "coverage gaps and confidence words unchanged",
        "progressive series",
        "redraw it and add exactly one part",
        "Do not replace teaching with one crowded final diagram",
    ):
        assert phrase in normalized_teach
    teach_metadata, _ = _frontmatter(SKILLS / "teach" / "SKILL.md")
    assert "check for understanding" not in str(teach_metadata["description"]).lower()
    why = (SKILLS / "why" / "SKILL.md").read_text()
    assert "coverage ledger" in why and "source categories" in why
    normalized_why = " ".join(why.split())
    assert "includeMcpJson: false" in normalized_why
    assert "external evidence is passed to them" in normalized_why
    assert "they do not fetch it through MCP or connector calls" in normalized_why
    unslop = (SKILLS / "unslop" / "SKILL.md").read_text()
    normalized_unslop = " ".join(unslop.split())
    for phrase in (
        "**Scan.**",
        "**Rewrite.**",
        "**Add human voice.**",
        "**Self-audit.**",
        "## Pattern catalog",
        "vague attribution",
        "forced groups of three",
        "synonym cycling",
        "chatbot greetings",
        "sycophantic agreement",
        "passive voice",
        "observable result",
    ):
        assert phrase in normalized_unslop
    reflect = (SKILLS / "reflect" / "SKILL.md").read_text()
    assert "independent native Kiro sub-agent" in reflect
    assert "explicit approval before making any durable edit" in reflect

    router = (SKILLS / "poteto-mode" / "SKILL.md").read_text()
    for routed_name in (
        "automate-me",
        "bro",
        "create-verification-skill",
        "maintain-verification-skill",
        "recall",
        "reflect",
        "show-me-your-work",
        "swarm",
        "teach",
    ):
        assert f"`{routed_name}`" in router


def test_poteto_router_preserves_package_wide_triggers_and_playbook_routes() -> None:
    workflows = " ".join(
        (SKILLS / "poteto-mode" / "references" / "workflows.md").read_text(encoding="utf-8").split()
    )
    for heading in (
        "Investigation",
        "Bug fix",
        "Performance issue",
        "Hillclimb",
        "Runtime forensics",
        "Trace forensics",
        "Feature",
        "Refactoring",
        "Prototype",
        "Visual parity",
        "Author or modify a skill",
        "Evaluation",
        "Autonomous run",
        "Babysit or get merge-ready",
        "Shipping",
        "Multi-phase plan",
        "Program orchestration",
        "Full autopilot and stack autopilot",
        "Open a pull request",
        "Pause safely",
        "Session pickup",
        "Worktree and host cleanup",
        "Bugbot and automated-review triage",
    ):
        assert f"## {heading}" in workflows
    for phrase in (
        "read the complete `principles` catalog before executing",
        "full leaf skill for each principle that actually applies",
        "concrete choice it changed",
        "retain an inapplicable checkpoint with a specific skip reason",
        "reversible observation, probe, or prototype",
        "name the domain data shape first",
        "Apply `unslop` to every prose surface",
        "`no-comments` before review",
        "GitHub CLI by default",
        "stable patch-id after every rebase",
        "ready (not draft) pull request within roughly 15 minutes",
        "same load-bearing scenario on current trunk",
        "explicit absolute behavior budget",
        "PK-Stack preserves the upstream check-plan helper's semantics",
        "upstream cleanup helper is semantics-only",
        "## Native workflow spine",
        "standard Spec for unfamiliar, cross-boundary, high-risk",
        "Quick Spec for bounded, well-understood work",
        "Kiro does not document a supported Agent Skill or custom-agent tool",
        "/spec new <name>",
        "/spec run <name>",
        "/agent swap pstack",
        "PK-Stack does not recreate that task graph",
        "projectctl goal bind-spec",
        "Use the feature record first",
        "Crew may run a committed spec through its Task Runner",
    ):
        assert phrase in workflows


def test_poteto_primary_router_uses_native_specs_as_the_planning_spine() -> None:
    router = " ".join((SKILLS / "poteto-mode" / "SKILL.md").read_text(encoding="utf-8").split())
    for phrase in (
        "## Use Kiro's native planning spine",
        "standard **Spec**",
        "**Quick Spec**",
        "**Bug Fix**",
        "native **Plan**",
        "Kiro does not document a supported Agent Skill or custom-agent tool",
        "/spec new <name>",
        "/agent swap pstack",
        "Kiro owns `requirements.md` or `bugfix.md`, `design.md`, `tasks.md`",
        "never creates a second task graph",
        "through canonical `okn`",
    ):
        assert phrase in router


def test_okf_skill_is_kiro_native_bounded_and_uses_canonical_runtime() -> None:
    text = (SKILLS / "okf" / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    for phrase in (
        "**produce**, **maintain**, or **consume**",
        "Store project knowledge in `Wiki/`",
        "projectctl knowledge search",
        "--budget 1200",
        "content-addressed locators",
        "projectctl knowledge validate",
        "mode: canonical-okn",
        "explicit UTC offset",
        "Attested Computation",
        "Do not crawl editor or agent transcripts",
        "substitute `okfcli/okf`",
    ):
        assert phrase in normalized
    for residue in (
        "${CLAUDE_SKILL_DIR}",
        "${CLAUDE_PLUGIN_ROOT}",
        "/okf:",
        "user-invocable:",
        "argument-hint:",
        "~/.claude",
    ):
        assert residue not in text


def test_nested_workflow_ports_preserve_semantics_without_cursor_runtime_seams() -> None:
    def normalized(*relative_paths: str) -> str:
        return " ".join(
            " ".join((SKILLS / relative_path).read_text(encoding="utf-8").split())
            for relative_path in relative_paths
        )

    architect = normalized(
        "architect/SKILL.md",
        "architect/references/design-contract.md",
    )
    for phrase in (
        "caller's usage",
        "types and data structures",
        "signatures and scaffold",
        "module map",
        "not implemented",
        "rationale",
        "shallow module",
        "information leakage",
        "temporal decomposition",
        "pass-through method",
        "interface depth",
    ):
        assert phrase in architect.lower()

    how = normalized(
        "how/SKILL.md",
        "how/references/roles-and-critique.md",
    )
    for phrase in (
        "explorer role",
        "explainer role",
        "critique mode",
        "critic",
        "abstraction fit",
        "data model",
        "boundary discipline",
        "evolution readiness",
        "complexity versus value",
        "consistency",
        "act on",
        "dismissed",
    ):
        assert phrase in how.lower()

    interrogate = normalized(
        "interrogate/SKILL.md",
        "interrogate/references/review-contract.md",
    )
    for phrase in (
        "correctness reviewer",
        "code-quality reviewer",
        "same intent and evidence packet",
        "lead judgment",
        "actually occur",
        "premature",
        "agreement raises confidence but is not proof",
        "act on",
        "consider",
        "noted",
        "dismissed",
    ):
        assert phrase in interrogate.lower()

    reflect = normalized(
        "reflect/SKILL.md",
        "reflect/references/lenses-and-synthesis.md",
    )
    for phrase in (
        "judgment",
        "tooling",
        "divergent",
        "no other reviewer's conclusion",
        "accepted",
        "rejected",
        "backlog",
        "explicit approval before making any durable edit",
        "never search private transcript stores",
    ):
        assert phrase in reflect.lower()

    why = normalized(
        "why/SKILL.md",
        "why/references/evidence-contract.md",
    )
    for phrase in (
        "project history and code",
        "project team chat",
        "infrastructure observability",
        "error tracking",
        "product analytics",
        "incident and postmortem evidence",
        "coverage ledger",
        "checked-empty",
        "unavailable",
        "direct",
        "supported",
        "inferred",
        "speculative",
        "unknown",
        "gaps",
        "in parallel",
    ):
        assert phrase in why.lower()

    figure = normalized("figure-it-out/SKILL.md")
    for phrase in (
        "first deliverable is the designed workflow, before code",
        "quantified scope",
        "rigor level",
        "risk-first phases",
        "independently landable units",
        "baseline",
        "pre-change state",
        "multi-hour",
        "verified",
        "not verified",
        "inconclusive",
        "return the designed playbook, selected rigor",
    ):
        assert phrase in figure.lower()

    writing = normalized("technical-writing/SKILL.md")
    for phrase in (
        "diataxis",
        "google developer sentence style",
        "simplified technical english",
        "one load at a time",
        "global english ambiguity",
        "condition before the command",
        "review checklist",
        "paths, symbols, flags, defaults, counts, and error text",
    ):
        assert phrase in writing.lower()

    scoped_files = [
        path
        for skill_name in (
            "architect",
            "how",
            "interrogate",
            "reflect",
            "why",
            "figure-it-out",
            "technical-writing",
        )
        for path in (SKILLS / skill_name).rglob("*.md")
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in scoped_files)
    for forbidden in (
        "$ARGUMENTS",
        "subagent_type",
        "generalPurpose",
        "agent-transcripts",
        ".cursor/",
        "kiro-cli acp",
    ):
        assert forbidden not in combined
    assert re.search(r"\b(?:claude|gpt|grok)-[a-z0-9.-]+", combined, re.IGNORECASE) is None


def test_setup_skill_uses_idempotent_json_contract() -> None:
    text = (SKILLS / "setup-pk-stack" / "SKILL.md").read_text(encoding="utf-8")

    assert "scripts/setup_pstack.py" in text
    assert ".pstack/bin/projectctl" in text
    assert "--dry-run --output json" in text
    assert "--update-managed" in text
    assert "repository-supplied `./projectctl`" in text
    assert "doctor --output json" in text
    assert "idempotent" in text
    assert "silently install" in text
    assert "/agent swap pstack" in text
    assert "kiro-cli chat --v3 --agent pstack" in text
    assert "Agent Focus" in text
    assert "Kiro Crew" in text and "optional orchestrator" in text
    assert "Kiro Web" in text and "Configuration Sync" in text
    assert "global default" in text
    assert "does not enumerate or write Cursor-style per-role model slugs" in text
    assert "inherit the current session's selected Kiro model and effort" in text
    assert "never edits the user's global model, effort, or role settings" in text


def test_maintenance_skill_preserves_current_session_and_clean_room_contract() -> None:
    text = (SKILLS / "maintain-pk-stack" / "SKILL.md").read_text(encoding="utf-8")

    assert "current Kiro agent session" in text
    assert "Crew may use ACP internally" in text
    assert "never execute" in text
    assert "A adapt" in text
    assert "B explicitly exclude" in text
    assert "C provenance" in text
    assert "--source-id <source-id>" in text
    assert "exactly one source for this transaction" in text
    assert "Never combine transitions from different sources" in text
    assert "passing that exact scoped command to `goal start --command`" in text
    assert "Google OKF wins" in text
    assert "Claude transcript mining" in text
    assert "--max-attempts 5" in text
    assert "mandatory first attempt" in text
    assert "four bounded" in text
    assert "repair-and-secretless-verification pairs" in text
    assert "`attempt_count: 0`" in text
    assert "`attempt_count >= 1`" in text
    assert "without repeating the baseline" in text
    assert "only after a meaningful repair" in text
    assert "known receipt-managed outputs" in text
    assert "do not restart or spend an attempt" in text
    assert "parity remains mandatory" in text
    assert "re-review the full" in text
    assert "bind the proposal to the newly proved digest" in text
    assert "proposal-bound tail marker" in text
    assert "--dry-run --update-managed --output json" in text
    assert "without `--dry-run`" in text
    assert "maintenance/upstream-reviews.json` by hand" in text
    assert "upstream accept --manifest maintenance/upstreams.json" in text
    assert "--expected-head <exact-head-commit> --dry-run" in text
    assert "current no-op" in text
    assert "unrelated goal" in text
    assert "Git history is the tamper-evident authority" in text
    assert "Only report all upstreams current" in text

    agent = json.loads((AGENTS / "pstack.json").read_text(encoding="utf-8"))
    assert "/maintain-pk-stack" in agent["prompt"]
    assert "immutable feature goal" in agent["prompt"]


def test_post_setup_workflow_attaches_the_pstack_agent() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    usage = (ROOT / "docs" / "usage.md").read_text(encoding="utf-8")

    for document in (readme, usage):
        assert "/agent swap pstack" in document
        assert "kiro-cli chat --v3 --agent pstack" in document


def test_setup_shim_uses_locked_source_module_fallback_for_older_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_execve(path: str, argv: list[str], environment: dict[str, str]) -> None:
        captured.update(path=path, argv=argv, environment=environment)
        raise RuntimeError("execve captured")

    monkeypatch.setattr(sys, "version_info", (3, 10, 0))
    monkeypatch.setattr(
        shutil,
        "which",
        lambda name: "/opt/homebrew/bin/uv" if name == "uv" else None,
    )
    monkeypatch.setattr(os, "execve", fake_execve)
    monkeypatch.setattr(sys, "argv", ["setup_pstack.py", "--root", "/tmp/example"])
    monkeypatch.setenv("PYTHONPATH", "/existing/pythonpath")

    with pytest.raises(RuntimeError, match="execve captured"):
        runpy.run_path(
            str(SKILLS / "setup-pk-stack" / "scripts" / "setup_pstack.py"),
            run_name="__main__",
        )

    assert captured["path"] == "/opt/homebrew/bin/uv"
    assert captured["argv"] == [
        "/opt/homebrew/bin/uv",
        "run",
        "--quiet",
        "--isolated",
        "--locked",
        "--project",
        str(ROOT),
        "python",
        "-m",
        "pstack_kiro.bootstrap",
        "--root",
        "/tmp/example",
    ]
    environment = captured["environment"]
    assert isinstance(environment, dict)
    assert environment["PYTHONPATH"] == os.pathsep.join((str(ROOT / "src"), "/existing/pythonpath"))


def test_setup_shim_legacy_location_finds_the_project_controller(tmp_path: Path) -> None:
    shim = tmp_path / ".kiro" / "skills" / "setup-pk-stack" / "scripts" / "setup_pstack.py"
    shim.parent.mkdir(parents=True)
    shutil.copy2(SKILLS / "setup-pk-stack" / "scripts" / "setup_pstack.py", shim)
    cached_controller = tmp_path / ".pstack" / "projectctl"
    cached_controller.mkdir(parents=True)

    namespace = runpy.run_path(str(shim), run_name="pstack_setup_probe")

    assert namespace["POWER_ROOT"] == cached_controller


def test_verified_goal_is_current_session_and_deterministically_verified() -> None:
    text = (SKILLS / "verified-goal" / "SKILL.md").read_text(encoding="utf-8")

    assert "Use `.pstack/bin/projectctl` for the entire loop" in text
    assert "Do not use ambient `uv run projectctl`" in text
    for command in (
        "goal start",
        "goal status --output json",
        "goal verify --output json",
        "goal resume --add-attempts",
        "goal clear --force",
        "goal tripwire --output json",
    ):
        assert command in text
    assert "$ARGUMENTS" not in text
    assert "current Kiro agent session" in text
    assert "Kiro Crew may own the session" in text
    assert "executable verifier" in text
    assert "goal bind-spec <spec-name> --feature <slug>" in text
    assert 'goal start "<objective>" --spec <spec-name>' in text
    assert "requirements.md" in text and "bugfix.md" in text
    assert "completed task checkboxes" in text
    assert "If a native spec exists but has no executable bridge" in text
    assert "Do not automatically run `goal resume`" in text
    assert "/spawn" not in text
    assert "kiro-cli" not in text.lower()


def test_skills_do_not_depend_on_cli_only_argument_substitution() -> None:
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        assert "$ARGUMENTS" not in text, path
        assert "request text that activated this skill" in text, path


def test_surface_support_matrix_separates_targets_from_evidence() -> None:
    compatibility = (ROOT / "docs" / "kiro-v3-compatibility.md").read_text(encoding="utf-8")
    normalized_compatibility = " ".join(compatibility.split())
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    normalized_compatibility = " ".join(compatibility.split())

    for text in (compatibility, readme):
        normalized = " ".join(text.split())
        assert "Kiro CLI v3" in normalized
        assert "Kiro IDE 1.x" in normalized
        assert "Kiro Crew" in normalized
        assert "Kiro Web" in normalized
        assert "optional orchestrator" in normalized
    assert "## Support and evidence matrix" in compatibility
    assert "First-class and exercised" in normalized_compatibility
    assert "First-class and structurally validated" in normalized_compatibility
    assert "Agent Focus Mode as experimental" in normalized_compatibility
    assert "Compatibility required; orchestration optional" in normalized_compatibility
    assert "Supported by design, explicitly untested" in normalized_compatibility
    crew_nightly_versions = re.findall(
        r"\b[0-9]+\.[0-9]+\.[0-9]+-nightly\.[0-9]{8}t[0-9]{6}\b",
        normalized_compatibility,
    )
    assert len(crew_nightly_versions) == 1
    assert "project custom agent as primary" in normalized_compatibility
    assert "keep `/setup-pk-stack` Power-local as an IDE/CLI bootstrap exception" in (
        normalized_compatibility
    )
    assert "text files only" in normalized_compatibility
    assert "at most 50 files" in normalized_compatibility
    assert "does not merge into or overwrite local `.kiro`" in normalized_compatibility
    assert "Kiro Crew [PR #5129]" in normalized_compatibility
    assert "does not promote source history" in normalized_compatibility
    assert "native `/goal`" in normalized_compatibility
    assert "five iterations by default" in normalized_compatibility
    assert "treated `/goal clear` as ordinary prompt text" in normalized_compatibility
    assert "native `/goal` is not exposed by this tested runtime" in normalized_compatibility
    for model in ("Sol", "Terra", "Luna"):
        assert model in normalized_compatibility
    for multiplier in ("2.4x", "1.0x", "0.1x"):
        assert multiplier in normalized_compatibility
    assert "all three GPT-5.6 tiers as experimental" in normalized_compatibility
    assert "`none`, `low`, `medium`, `high`, `xhigh`, and `max`" in normalized_compatibility
    assert "effort selection in IDE and CLI, not Web or Mobile" in normalized_compatibility
    assert "not a primary or default pk-stack path" in normalized_compatibility.lower()

    combined_root = ROOT.parents[1]
    goal_probe = json.loads(
        (combined_root / "reviews" / "kiro-v3-native-goal-probe.json").read_text(encoding="utf-8")
    )
    assert goal_probe["scope"]["client_version"] == "2.21.0"
    assert goal_probe["scope"]["engine"] == "v3"
    assert goal_probe["probe"]["terminal_input"] == "/goal clear"
    assert goal_probe["probe"]["persisted_user_content"] == "goal clear"
    assert goal_probe["probe"]["follow_up_terminal_input"] == "/quit"
    assert goal_probe["probe"]["process_exit_code"] == 0
    assert len(goal_probe["raw_evidence"]["messages_jsonl_sha256"]) == 64
    assert len(goal_probe["raw_evidence"]["kiro_log_sha256"]) == 64


def test_model_guidance_is_kiro_native_and_evidence_bounded() -> None:
    compatibility = (ROOT / "docs" / "kiro-v3-compatibility.md").read_text(encoding="utf-8")
    normalized_compatibility = " ".join(compatibility.split())
    usage = (ROOT / "docs" / "usage.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    normalized_usage = " ".join(usage.split())
    normalized_readme = " ".join(readme.split())
    combined_root = ROOT.parents[1]
    evidence = json.loads(
        (combined_root / "reviews" / "kiro-model-guidance-evidence.json").read_text(
            encoding="utf-8"
        )
    )

    for phrase in (
        "General development | Auto",
        "Hardest long-horizon or security-sensitive work | GPT-5.6 Sol",
        "Routine multi-step implementation | GPT-5.6 Terra",
        "High-frequency bounded work | GPT-5.6 Luna",
        "automatically persists a `/effort` or `--effort` choice",
        "Higher effort uses more credits",
        "served from the US regardless of the profile's geography",
        "commercial AWS Regions worldwide",
        "global cross-region inference does not change the region where data is stored",
        "only classifier-flagged traffic may be retained for up to 30 days",
        "not a claim that any PK-Stack traffic was flagged or retained",
        "optional, IDE-only, and evidence rather than formal verification",
        "does not claim it was run here",
        "same stored projectctl verifier remains the portable completion predicate",
    ):
        assert phrase in normalized_compatibility

    assert "PK-Stack inherits the model and effort" in normalized_readme
    assert "does not hard-code Sol/max" in normalized_readme
    assert "evidence, not the interactive default" in normalized_usage
    assert "select the desired normal effort afterwards" in normalized_usage

    assert evidence["live_account_inventory"]["default_model"] == "auto"
    models = evidence["live_account_inventory"]["models"]
    assert [model["model_id"] for model in models] == [
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.6-luna",
    ]
    assert [model["rate_multiplier"] for model in models] == [2.4, 1.0, 0.1]
    assert all(model["lifecycle_description"] == "Experimental preview" for model in models)
    pages = {page["url"]: page for page in evidence["documentation"]["pages"]}
    data_protection_url = "https://kiro.dev/docs/privacy-and-security/data-protection.md"
    assert pages[data_protection_url]["sha256"] == (
        "697dfa699d8a5a6ce6e241e60b00f1c85cd792f4ba16007e1e92303fd16b1404"
    )
    boundaries = " ".join(evidence["data_processing_boundaries"])
    assert "classifier-flagged traffic" in boundaries
    assert "up to 30 days" in boundaries
    assert "region where Kiro stores data" in boundaries

    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8").lower()
        assert "gpt-5.6-" not in text, path
        assert "--model" not in text, path


def test_primary_agent_copy_is_surface_neutral_and_keeps_cli_and_crew_boundaries() -> None:
    primary = json.loads((AGENTS / "pstack.json").read_text(encoding="utf-8"))

    assert "current Kiro agent session" in primary["description"]
    assert "current Kiro CLI v3 session" not in primary["description"]
    assert "Kiro IDE 1.x and Kiro CLI v3 are the primary surfaces" in primary["prompt"]
    assert "Kiro Crew is optional and may use ACP internally" in primary["prompt"]
    assert "do not make ACP the default PK-Stack path" in primary["prompt"]
    assert "native Spec, Quick Spec, or Bug Fix workflow" in primary["prompt"]
    assert "bind the spec to a feature verifier" in primary["prompt"]
    assert "Do not recreate Kiro's task graph" in primary["prompt"]
    assert "use canonical okn only for deeper" in primary["prompt"]
    assert "On Kiro Web this profile is delegation-only" in primary["prompt"]
    assert (
        "do not claim it is the primary agent or that IDE/CLI permissions apply"
        in primary["prompt"]
    )


def test_parallel_skills_use_native_subagents_not_separate_sessions() -> None:
    for skill_name in ("arena", "swarm"):
        text = (SKILLS / skill_name / "SKILL.md").read_text(encoding="utf-8")
        assert "Native Kiro sub-agents" in text or "native Kiro sub-agents" in text
        assert "shipped delegated profiles are read-only" in text
        assert "`/spawn`" in text
        assert "not" in text[text.index("`/spawn`") : text.index("`/spawn`") + 120]


def test_model_council_is_optional_advisory_and_not_a_runtime_claim() -> None:
    text = (SKILLS / "model-council" / "SKILL.md").read_text(encoding="utf-8")
    lowered = text.lower()

    assert "optional and advisory" in lowered
    assert "not a kiro-native model runtime" in lowered
    assert "never auto-apply" in lowered
    assert "fable" in lowered and "grok" in lowered
    assert "designated peer advisor" in lowered
    assert "designated sweeper" in lowered
    assert "cannot accept" in lowered
    for label in ("Act on", "Consider", "Noted", "Dismissed"):
        assert f"`{label}`" in text


def test_prospective_fable_harness_uses_xhigh_without_rewriting_history() -> None:
    text = (ROOT / "reviews" / "README.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    prospective = text[text.index("Prospective council runs use this policy:") :]
    command = prospective[prospective.index("## Run Fable 5.1 acceptance") :]

    assert "Fable 5.1 at `max` returned `ACCEPT`" in text
    assert "Its Fable `max` value records the actual completed acceptance run" in normalized
    assert "| Fable | `claude-fable-5-1` | `xhigh` |" in prospective
    assert "--model claude-fable-5-1" in command
    assert "--effort xhigh" in command
    assert "--effort max" not in command
    assert "| Grok | `grok-4.6` | `xhigh` |" in prospective


def test_agent_templates_are_json_least_privilege_profiles() -> None:
    paths = sorted(AGENTS.glob("*.json"))
    assert {path.name for path in paths} == {
        "pstack-architect.json",
        "pstack-reviewer.json",
        "pstack-verifier.json",
        "pstack.json",
    }

    for path in paths:
        agent = json.loads(path.read_text(encoding="utf-8"))
        assert agent["name"] == path.stem
        assert set(agent["tools"]) <= ALLOWED_TOOLS
        assert "*" not in agent["tools"]
        assert "@builtin" not in agent["tools"]
        assert "@mcp" not in agent["tools"]
        assert agent["includeMcpJson"] is False
        assert agent["includePowers"] is False
        assert "model" not in agent, "templates must inherit the user's current model"
        assert "skill://.kiro/skills/*/SKILL.md" in agent["resources"]
        assert "file://.kiro/steering/**/*.md" in agent["resources"]

        rules = agent["permissions"]["rules"]
        assert rules
        for rule in rules:
            assert rule["capability"] != "all"
            assert rule["effect"] in {"allow", "ask", "deny"}
            assert "*" not in rule.get("match", [])
            assert "**" not in rule.get("match", [])
            if rule["capability"] == "shell" and rule["effect"] == "allow":
                matches = "\n".join(rule.get("match", []))
                assert "projectctl" not in matches
                assert "uv run" not in matches

    assert "write" in json.loads((AGENTS / "pstack.json").read_text())["tools"]
    primary_rules = json.loads((AGENTS / "pstack.json").read_text())["permissions"]["rules"]
    assert any(
        rule["capability"] == "fs_read" and rule["effect"] == "allow" for rule in primary_rules
    )
    for read_only in (
        "pstack-architect.json",
        "pstack-reviewer.json",
        "pstack-verifier.json",
    ):
        profile = json.loads((AGENTS / read_only).read_text())
        assert profile["tools"] == ["read", "knowledge"]
        assert profile["toolsSettings"] == {}
        assert not {"shell", "write", "fs_write"} & set(profile["toolsSettings"])
        assert not any(rule["capability"] == "shell" for rule in profile["permissions"]["rules"])


def test_primary_profile_asks_for_every_canonical_controller_route() -> None:
    primary = json.loads((AGENTS / "pstack.json").read_text(encoding="utf-8"))
    ask_patterns = [
        pattern
        for rule in primary["permissions"]["rules"]
        if rule["capability"] == "shell" and rule["effect"] == "ask"
        for pattern in rule["match"]
    ]
    commands = (
        ".pstack/bin/projectctl",
        ".pstack/bin/projectctl version --output json",
        ".pstack/bin/projectctl setup --power-root /reviewed --update-managed",
        ".pstack/bin/projectctl doctor --output json",
        ".pstack/bin/projectctl feature list --output json",
        ".pstack/bin/projectctl feature show sample --output json",
        ".pstack/bin/projectctl feature validate --output json",
        ".pstack/bin/projectctl feature generate sample --ready",
        ".pstack/bin/projectctl feature verify sample --output json",
        ".pstack/bin/projectctl verify sample --output json",
        ".pstack/bin/projectctl goal start objective --command verifier",
        ".pstack/bin/projectctl goal bind-spec sample --feature sample --output json",
        ".pstack/bin/projectctl goal status --output json",
        ".pstack/bin/projectctl goal verify --output json",
        ".pstack/bin/projectctl goal resume --add-attempts 1",
        ".pstack/bin/projectctl goal clear --force",
        ".pstack/bin/projectctl goal tripwire --output json",
        ".pstack/bin/projectctl knowledge status --output json",
        ".pstack/bin/projectctl knowledge validate --output json",
        ".pstack/bin/projectctl knowledge search sample --output json",
        ".pstack/bin/projectctl future-command --future-option",
    )

    assert set(ask_patterns) >= {
        ".pstack/bin/projectctl",
        ".pstack/bin/projectctl *",
    }
    for command in commands:
        assert any(fnmatchcase(command, pattern) for pattern in ask_patterns), command


def test_primary_profile_denies_direct_control_plane_writes_and_common_clobbers() -> None:
    primary = json.loads((AGENTS / "pstack.json").read_text(encoding="utf-8"))
    rules = primary["permissions"]["rules"]
    denied_writes = {
        pattern
        for rule in rules
        if rule["capability"] == "fs_write" and rule["effect"] == "deny"
        for pattern in rule["match"]
    }
    denied_shell = {
        pattern
        for rule in rules
        if rule["capability"] == "shell" and rule["effect"] == "deny"
        for pattern in rule["match"]
    }

    assert denied_writes >= {
        ".pstack/**",
        ".kiro/agents/**",
        ".kiro/hooks/**",
        ".kiro/steering/**",
    }
    assert ".kiro/skills/**" not in denied_writes
    managed_live_skills = EXPECTED_SKILLS - {"setup-pk-stack"}
    managed_skill_denies = {
        pattern for pattern in denied_writes if pattern.startswith(".kiro/skills/")
    }
    assert managed_skill_denies == {f".kiro/skills/{name}/**" for name in managed_live_skills}
    ask_writes = {
        pattern
        for rule in rules
        if rule["capability"] == "fs_write" and rule["effect"] == "ask"
        for pattern in rule["match"]
    }
    foreign_skill = "./.kiro/skills/user-verifier/SKILL.md"
    assert any(fnmatchcase(foreign_skill, pattern) for pattern in ask_writes)
    assert not any(fnmatchcase(foreign_skill, pattern) for pattern in denied_writes)
    assert denied_shell >= {
        "rm -r*",
        "rm -R*",
        "git checkout *",
        "git checkout -- *",
        "git restore *",
        "git branch -d *",
        "git branch -D *",
        "git branch --delete *",
        "git push --force*",
        "git push -f*",
    }

    destructive_commands = (
        "git checkout src/app.py",
        "git checkout HEAD -- src/app.py",
        "git -C nested checkout -- src/app.py",
        "git branch -d topic",
        "git branch -D topic",
        "git branch --delete topic",
        "git -C nested branch --delete --force topic",
        "git push origin main --force",
        "git push origin main --force-with-lease",
        "git push origin +main",
        "git push --mirror origin",
        "git -C nested push origin main --force",
        "git -C nested push origin +main",
        "git -C nested push --mirror origin",
    )
    for command in destructive_commands:
        assert any(fnmatchcase(command, pattern) for pattern in denied_shell), command


def test_skill_authoring_respects_bootstrap_owned_routes() -> None:
    for name in ("automate-me", "create-verification-skill", "reflect"):
        text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        assert ".pstack/bootstrap.json" in text
        assert "receipt-managed" in text


def test_primary_profile_never_allows_git_forms_that_execute_read_or_write() -> None:
    primary = json.loads((AGENTS / "pstack.json").read_text(encoding="utf-8"))
    shell_allow = [
        pattern
        for rule in primary["permissions"]["rules"]
        if rule["capability"] == "shell" and rule["effect"] == "allow"
        for pattern in rule["match"]
    ]
    shell_ask = [
        pattern
        for rule in primary["permissions"]["rules"]
        if rule["capability"] == "shell" and rule["effect"] == "ask"
        for pattern in rule["match"]
    ]
    commands = (
        "git difftool -y --extcmd=sh HEAD~1 HEAD",
        "git difftool -y -x sh",
        "git diff --ext-diff",
        "git diff --output=.kiro/hooks/evil.json",
        "git log -1 --format=%B --output=.pstack/state/goal.json",
        "git show --output=/tmp/escape HEAD",
        "git log --output=../outside.txt",
        "git diff --no-index /etc/hosts /dev/null",
        "git status --short",
    )

    for command in commands:
        assert not any(fnmatchcase(command, pattern) for pattern in shell_allow), command
        assert any(fnmatchcase(command, pattern) for pattern in shell_ask), command


def test_post_swap_setup_refresh_uses_power_local_authority() -> None:
    steering = (ROOT / "dev.kiro" / "steering" / "pstack-core.md").read_text(encoding="utf-8")
    normalized = " ".join(steering.split())

    assert "IDE users stay in chat and use the agent picker" in normalized
    assert "CLI users stay in chat" in normalized
    assert "/agent swap kiro_default" in normalized
    assert "/setup-pk-stack" in normalized
    assert "/agent swap pstack" in normalized
    assert "Crew opens the trusted project only after local bootstrap" in normalized
    assert "Web uses a locally refreshed, reviewed, committed asset tree" in normalized
    assert "Configuration Sync is not a complete PK-Stack installer" in normalized
    assert "--power-root" in normalized


def test_verified_goal_surfaces_stored_predicate_before_first_attempt() -> None:
    text = (SKILLS / "verified-goal" / "SKILL.md").read_text(encoding="utf-8")

    assert "Before the first verification attempt" in text
    assert "in every skill invocation" in text
    assert "already active" in text
    assert "goal.contract.display" in text
    assert "shell approval UI" in text


def test_subagent_trust_is_explicit_and_bounded_to_shipped_profiles() -> None:
    primary = json.loads((AGENTS / "pstack.json").read_text(encoding="utf-8"))
    settings = primary["toolsSettings"]["subagent"]

    assert settings["availableAgents"] == [
        "pstack-architect",
        "pstack-reviewer",
        "pstack-verifier",
    ]
    assert settings["trustedAgents"] == settings["availableAgents"]


def test_installed_kiro_discovers_every_workspace_agent_with_221_sentinel(
    tmp_path: Path,
) -> None:
    kiro = shutil.which("kiro-cli")
    if kiro is None:
        pytest.skip("kiro-cli is not installed")  # ty: ignore[too-many-positional-arguments]
    workspace_agents = tmp_path / ".kiro" / "agents"
    shutil.copytree(AGENTS, workspace_agents)

    for path in sorted(workspace_agents.glob("*.json")):
        completed = subprocess.run(
            [kiro, "agent", "validate", "--path", str(path)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr or completed.stdout

    completed = subprocess.run(
        [kiro, "agent", "list"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    output = re.sub(
        r"\x1b\[[0-?]*[ -/]*[@-~]",
        "",
        completed.stdout + completed.stderr,
    )
    discovered = {
        match.group(1)
        for match in re.finditer(r"^\s*(pstack(?:-[a-z]+)?)\s+Workspace\b", output, re.MULTILINE)
    }
    assert discovered == {"pstack", "pstack-architect", "pstack-reviewer", "pstack-verifier"}


def test_hook_templates_use_standalone_v3_schema() -> None:
    paths = sorted(HOOKS.glob("*.json"))
    assert paths

    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document["version"] == "v1"
        assert isinstance(document["hooks"], list) and document["hooks"]
        for hook in document["hooks"]:
            assert hook["trigger"] in ALLOWED_HOOK_TRIGGERS
            assert hook["trigger"][0].isupper()
            assert hook["action"]["type"] in {"command", "agent"}
            if hook["action"]["type"] == "command":
                assert hook["action"]["command"]
                assert "uv run" not in hook["action"]["command"]
                if hook.get("enabled", True):
                    command = hook["action"]["command"].lstrip()
                    assert not command.startswith(("./projectctl", ".pstack/bin/projectctl"))
                    assert "; .pstack/bin/projectctl" not in command
                    assert "&& .pstack/bin/projectctl" not in command


def test_stop_tripwire_is_disabled_and_advisory() -> None:
    tripwire = json.loads((HOOKS / "pstack-tripwire.json").read_text(encoding="utf-8"))
    hooks = tripwire["hooks"]

    assert len(hooks) == 1
    hook = hooks[0]
    assert hook["trigger"] == "Stop"
    assert hook["enabled"] is False
    assert "advisory" in hook["description"].lower()
    assert "blocking" in hook["description"].lower()
    assert "goal tripwire --output json" in hook["action"]["command"]


def test_steering_uses_native_always_and_file_match_inclusion() -> None:
    paths = sorted(STEERING.glob("*.md"))
    assert {path.name for path in paths} == {
        "pstack-core.md",
        "pstack-safety.md",
        "pstack-typescript.md",
        "pstack-unslop.md",
    }

    for path in paths:
        metadata, body = _frontmatter(path)
        if path.name == "pstack-typescript.md":
            assert metadata == {
                "inclusion": "fileMatch",
                "fileMatchPattern": ["**/*.ts", "**/*.tsx"],
            }
            normalized = " ".join(body.split())
            assert "reading or editing TypeScript" in normalized
            assert "typescript-best-practices" in normalized
        else:
            assert metadata == {"inclusion": "always"}
        assert len(body) < 2_000

    unslop = (STEERING / "pstack-unslop.md").read_text(encoding="utf-8")
    normalized_unslop = " ".join(unslop.split())
    assert "preserve facts, commitments, caveats" in normalized_unslop
    assert "Do not manufacture certainty, opinions, quotations, or evidence" in normalized_unslop

    parity_by_name = {entry["name"]: entry for entry in PARITY_SKILLS}
    typescript_rationale = parity_by_name["typescript-best-practices"]["rationale"]
    unslop_rationale = parity_by_name["unslop"]["rationale"]
    assert "fileMatch" in typescript_rationale
    assert ".ts/.tsx trigger" in typescript_rationale
    assert "always-included Kiro steering" in unslop_rationale
    assert "must-always-apply" in unslop_rationale


def test_assets_do_not_carry_cursor_or_legacy_runtime_contracts() -> None:
    text = _all_asset_text().lower()

    for forbidden in (
        ".cursor/",
        "/goal",
        "kiro-cli --v2",
        "kiro-cli --classic",
        "agent client protocol",
    ):
        assert forbidden not in text
