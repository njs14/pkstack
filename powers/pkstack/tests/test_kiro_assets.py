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
from urllib.parse import unquote, urlsplit

import pytest
import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token

from pkstack.bootstrap import SKILL_ROUTE_ALIASES
from pkstack.branding import DISPLAY_NAME, EXPANDED_NAME, POWER_ID

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
ROUTING_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "skill-routing.json"
EXPECTED_SKILLS = (
    {Path(entry["target"]).parent.name for entry in PARITY_SKILLS if entry["target"] is not None}
    | PK_ONLY_SKILLS
    | CURATED_SKILLS
)
REPO_ROOT = ROOT.parents[1]
ALLOWED_SKILL_FRONTMATTER = {"name", "description"}
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


def test_pkstack_routes_are_namespaced_without_renaming_upstream_identities() -> None:
    assert {name for name in EXPECTED_SKILLS if name.startswith("pkstack")} == {
        "pkstack",
        "pkstack-setup",
        "pkstack-maintain",
        "pkstack-verified-goal",
        "pkstack-model-council",
        "pkstack-principles",
    }
    assert SKILL_ROUTE_ALIASES == {"poteto-mode": "pkstack", "setup-pstack": "pkstack-setup"}
    assert {
        "okf",
        "pkstack-maintain",
        "pkstack-verified-goal",
        "pkstack-model-council",
        "pkstack-principles",
    } == PK_ONLY_SKILLS
    targets = (
        [
            Path(entry["target"]).parent.name
            for entry in PARITY_SKILLS
            if entry["target"] is not None
        ]
        + list(PK_ONLY_SKILLS)
        + list(CURATED_SKILLS)
    )
    assert len(targets) == len(set(targets)), "each source or local skill needs one unique route"
    assert {"archify", "show-me", "okf", "writing-for-agents"} <= EXPECTED_SKILLS
    assert (
        not {
            "poteto-mode",
            "setup-pstack",
            "setup-pk-stack",
            "maintain-pk-stack",
            "verified-goal",
            "model-council",
            "principles",
        }
        & EXPECTED_SKILLS
    )


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
    assert DISPLAY_NAME in manifest["description"] and EXPANDED_NAME in manifest["description"]
    assert manifest["version"]
    assert manifest["description"]
    assert isinstance(manifest["keywords"], list) and manifest["keywords"]
    assert {"Kiro CLI", "Kiro IDE", "Kiro Crew", "Kiro Web"} <= set(manifest["keywords"])


@pytest.mark.parametrize("skill_name", sorted(EXPECTED_SKILLS))
def test_skill_frontmatter_matches_agent_skills_standard(skill_name: str) -> None:
    path = SKILLS / skill_name / "SKILL.md"
    metadata, body = _frontmatter(path)

    assert metadata["name"] == skill_name
    assert set(metadata) == ALLOWED_SKILL_FRONTMATTER
    assert isinstance(metadata["description"], str)
    assert 1 <= len(metadata["description"]) <= 1024
    assert body


def test_only_expected_skill_directories_are_present() -> None:
    actual = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert actual == EXPECTED_SKILLS


def test_skill_routing_review_fixture_is_strict_and_names_real_skills() -> None:
    """Validate review inputs, not a production dispatcher or semantic routing behavior."""

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            assert key not in result, f"duplicate routing fixture key: {key}"
            result[key] = value
        return result

    raw = ROUTING_FIXTURE_PATH.read_text(encoding="utf-8")
    assert raw.endswith("\n") and len(raw.encode()) <= 24 * 1024
    fixture = json.loads(raw, object_pairs_hook=unique_object)
    assert set(fixture) == {"schema_version", "cases"}
    assert type(fixture["schema_version"]) is int and fixture["schema_version"] == 1
    cases = fixture["cases"]
    assert isinstance(cases, list) and 1 <= len(cases) <= 48
    ids: set[str] = set()
    primary_routes: set[str] = set()
    for case in cases:
        assert isinstance(case, dict)
        assert set(case) == {
            "id",
            "prompt",
            "primary",
            "helpers",
            "expected_output",
            "forbidden_effects",
        }
        for field in ("id", "prompt", "primary", "expected_output"):
            assert isinstance(case[field], str) and case[field].strip() == case[field]
            assert 1 <= len(case[field]) <= 1000
        assert re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", case["id"])
        assert case["id"] not in ids
        ids.add(case["id"])
        assert case["primary"] in EXPECTED_SKILLS
        primary_routes.add(case["primary"])
        helpers = case["helpers"]
        assert isinstance(helpers, list) and len(helpers) <= 6
        assert all(isinstance(helper, str) and helper in EXPECTED_SKILLS for helper in helpers)
        assert len(helpers) == len(set(helpers)) and case["primary"] not in helpers
        forbidden = case["forbidden_effects"]
        assert isinstance(forbidden, list) and 1 <= len(forbidden) <= 8
        assert all(
            isinstance(effect, str) and effect.strip() == effect and 1 <= len(effect) <= 200
            for effect in forbidden
        )
        assert len(forbidden) == len(set(forbidden))

    assert primary_routes >= CURATED_SKILLS
    # Preserve the review's positive cases, near misses, invocation, and composition coverage.
    assert {
        "setup-only",
        "setup-requested-tour",
        "visual-request-flow",
        "visual-polished-artifact",
        "ambiguous-work-summary",
        "requested-evidence-trail",
        "explicit-visual-route",
        "explicit-evidence-summary-only",
        "human-runbook",
        "agent-instructions",
        "mixed-audience-docs",
        "prose-edit-only",
        "mechanics-question",
        "rationale-question",
        "teach-composed-lesson",
        "architecture-boundary",
        "artifact-contest",
        "loop-design-only",
        "loop-build-authorized",
        "execute-current-task",
        "verifier-drift",
        "product-defect",
        "recall-context",
        "reflect-proposals",
        "capture-approved-knowledge",
        "react-props-too-broad",
        "typescript-boundary-schema",
        "react-live-null-state",
        "explicit-loop-no-effects",
        "lesson-with-polished-visual",
        "explicit-grilling-method",
        "interview-decision-only",
        "domain-meaning-update",
        "interview-and-retain-knowledge",
        "native-plan-shared-method",
        "native-plan-capture-pending",
        "approved-plan-first-write",
        "approved-plan-repeat",
        "approved-plan-no-write",
        "approved-plan-capture-denied",
        "approved-plan-validation-failed",
        "native-spec-shared-ownership",
        "plan-handoff-without-interview",
        "settled-constraint-mechanics",
        "docs-interview-read-only",
    } <= ids


def _markdown_document_links(text: str) -> list[str]:
    targets: list[str] = []

    def collect(tokens: list[Token]) -> None:
        for token in tokens:
            if token.type in {"link_open", "image"}:
                href = token.attrGet("href" if token.type == "link_open" else "src")
                if isinstance(href, str) and href:
                    parsed = urlsplit(href)
                    path = unquote(parsed.path)
                    if not parsed.scheme and not parsed.netloc and path.endswith(".md"):
                        targets.append(path)
            if token.children:
                collect(token.children)

    collect(MarkdownIt("commonmark").parse(text))
    return targets


def test_markdown_document_links_ignore_code_and_resolve_reference_links() -> None:
    text = """[Inline](guide.md#usage) and [Reference][leaf].
![Image](diagram.md)

[leaf]: references/leaf.md

`[Inline example](missing-inline.md)`

```markdown
[Template example](../missing-template.md)
```
"""
    assert _markdown_document_links(text) == ["guide.md", "references/leaf.md", "diagram.md"]


def test_skill_routing_markdown_pointers_resolve_within_the_power() -> None:
    for source in SKILLS.rglob("*.md"):
        if "upstream" in source.relative_to(SKILLS).parts:
            continue
        text = source.read_text(encoding="utf-8")
        for target in _markdown_document_links(text):
            resolved = (source.parent / target).resolve()
            assert resolved.is_relative_to(ROOT.resolve()), f"{source}: {target} escapes Power"
            assert resolved.is_file(), f"{source}: missing {target}"
            if resolved.name == "SKILL.md":
                assert resolved.parent.name in EXPECTED_SKILLS


def test_contextual_entrypoints_link_all_curated_leaf_methods() -> None:
    for relative in ("pkstack/SKILL.md", "pkstack/references/workflows.md"):
        source = SKILLS / relative
        targets = {
            (source.parent / target).resolve()
            for target in _markdown_document_links(source.read_text())
            if Path(target).name == "SKILL.md"
        }
        assert {(SKILLS / name / "SKILL.md").resolve() for name in CURATED_SKILLS} <= targets


@pytest.mark.parametrize(
    ("skill_name", "neighbors"),
    [
        ("show-me", {"show-me-your-work", "archify", "how", "why", "teach"}),
        ("show-me-your-work", {"show-me"}),
        ("technical-writing", {"writing-for-agents", "unslop"}),
        ("writing-for-agents", {"technical-writing", "unslop"}),
        ("unslop", {"technical-writing", "writing-for-agents"}),
        ("how", {"teach", "show-me"}),
        ("why", {"teach", "show-me"}),
        ("teach", {"how", "why", "show-me", "archify"}),
        ("architect", {"arena", "design-control-loop", "grilling"}),
        ("arena", {"architect", "design-control-loop", "grilling"}),
        ("design-control-loop", {"architect", "arena", "build-iterated-agentic-loop", "grilling"}),
        (
            "build-iterated-agentic-loop",
            {"design-control-loop", "pkstack-verified-goal", "grilling"},
        ),
        ("pkstack-verified-goal", {"build-iterated-agentic-loop", "maintain-verification-skill"}),
        ("maintain-verification-skill", {"pkstack-verified-goal"}),
        ("recall", {"reflect", "okf"}),
        ("reflect", {"recall", "okf"}),
        ("okf", {"recall", "reflect", "grilling"}),
        ("grilling", {"pkstack", "okf", "domain-modeling", "grill-with-docs", "interrogate"}),
        ("grill-me", {"grilling", "grill-with-docs"}),
        ("grill-with-docs", {"grilling", "domain-modeling", "okf"}),
        ("domain-modeling", {"grilling", "okf"}),
        ("create-verification-skill", {"grilling"}),
        ("narrow-react-prop-types", {"typescript-best-practices"}),
        ("typescript-best-practices", {"narrow-react-prop-types"}),
    ],
)
def test_skill_boundary_leaves_link_their_neighbors(skill_name: str, neighbors: set[str]) -> None:
    text = (SKILLS / skill_name / "SKILL.md").read_text(encoding="utf-8")
    assert neighbors <= set(re.findall(r"\]\(\.\./([^/]+)/SKILL\.md\)", text))


def test_setup_handoff_and_explicit_invocation_keep_authority_visible() -> None:
    setup = " ".join((SKILLS / "pkstack-setup" / "SKILL.md").read_text().split())
    assert "Do not start onboarding" in setup
    for name in ("show-me", "writing-for-agents", "create-verification-skill"):
        assert f"../{name}/SKILL.md" in setup
    entry = " ".join((SKILLS / "pkstack" / "SKILL.md").read_text().split())
    assert "does not broaden the user's authority" in entry


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
            route_name = SKILL_ROUTE_ALIASES.get(entry["name"], entry["name"])
            assert target == SKILLS / route_name / "SKILL.md"
            assert target.is_file()
        consolidation = entry.get("consolidates_to", "")
        if consolidation.endswith(".md"):
            destination = Path(consolidation)
            assert destination.as_posix() == consolidation
            assert not destination.is_absolute() and ".." not in destination.parts
            assert destination.parts[0] == "skills" and destination.parts[1] in EXPECTED_SKILLS
            assert (ROOT / destination).is_file(), f"{entry['name']}: missing {consolidation}"
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
    assert setup["target"] == "skills/pkstack-setup/SKILL.md"
    assert [(resource["path"], resource["handling"]) for resource in setup["current"]["files"]] == [
        ("SKILL.md", "semantic-source")
    ]

    poteto = by_name["poteto-mode"]
    assert poteto["disposition"] == "alias-consolidation"
    assert poteto["target"] == "skills/pkstack/SKILL.md"
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


def test_evidence_skill_documents_public_commands_and_storage() -> None:
    text = " ".join((SKILLS / "show-me-your-work/SKILL.md").read_text().split())
    for contract in (
        "projectctl evidence append <slug>",
        "--verdict VERIFIED|NOT VERIFIED|INCONCLUSIVE",
        ".pkstack/state/evidence/<slug>/decision-log.jsonl",
        "--committed",
        "--target Wiki/evidence/<slug>/decision-log.jsonl",
        "`schema_version`",
        "`sequence`",
        "`timestamp`",
        "`verdict`",
        "projectctl evidence audit <slug> --output json",
    ):
        assert contract in text


def test_primary_router_documents_native_spec_entrypoints() -> None:
    text = (SKILLS / "pkstack/SKILL.md").read_text(encoding="utf-8")
    for command in ("/spec new <name>", "/agent swap pkstack"):
        assert command in text
    for document in ("requirements.md", "bugfix.md", "design.md", "tasks.md"):
        assert document in text


def test_planning_interview_belongs_to_the_mode_the_user_selects() -> None:
    router = " ".join((SKILLS / "pkstack/SKILL.md").read_text(encoding="utf-8").split())
    method = " ".join((SKILLS / "grilling/SKILL.md").read_text(encoding="utf-8").split())
    steering = " ".join((STEERING / "pkstack-core.md").read_text(encoding="utf-8").split())
    profile = json.loads((AGENTS / "pkstack.json").read_text(encoding="utf-8"))["prompt"]

    # The router packages an inactive requested mode instead of interviewing in its place.
    assert "Selecting the requested native planning mode is the user's action" in router
    assert "list every remaining open choice as a question for native Plan to ask" in router
    assert "do not offer to answer those questions here instead" in router
    # The runnable CLI line must reach the always-on surfaces, not only the on-demand router skill.
    for text in (router, steering, profile):
        assert "/plan Read .kiro/skills/grilling/SKILL.md;" in text
        assert "runnable line the user can send unchanged" in text
        assert "do not leave the user to compose the prompt" in text
        assert "paraphrase it into a request to switch modes" in text
        # Scoped to conversational Plan, so a requested Spec route is never forced onto /plan.
        assert "conversational Plan" in text or "conversational-Plan handoff" in text
        assert "Spec, Quick Spec, or Bug Fix keeps its own `/spec` route" in text or (
            "Spec, Quick Spec, or Bug Fix keeps its own /spec route" in text
        )
    # Returning to pkstack is Spec-backed; conversational Plan keeps Kiro's execution handoff.
    for text in (router, steering, profile):
        assert "approval-to-execution handoff" in text
        assert "return to `pkstack` after Plan approval" in text or (
            "return to pkstack after Plan approval" in text
        )
    assert "For Spec-backed execution, return with `/agent swap pkstack`" in router
    # Derived mechanics travel as derived choices, not as constraints the sources fix.
    for text in (router, profile):
        assert "naming the requirement each satisfies, not as constraints the sources fix" in text
    # No surface may claim the router selects the mode itself.
    for text in (router, method, steering, profile):
        assert "The mode that runs the plan runs the interview" in text
        assert "select that mode before asking planning questions" not in text
    assert "Return that handoff and stop" in method
    assert "Entering the requested planning mode is the user's action here" in method
    assert "stop for that selection instead of interviewing under pkstack" in profile
    # Scoped to the router's own selection; Kiro keeps its approval and execution handoffs.
    assert "Kiro's own approval and execution handoffs still move between its modes" in router
    assert "Kiro's own approval and execution handoffs remain Kiro's to make" in method
    assert "Kiro's own approval and execution handoffs are unaffected" in steering
    assert "Kiro's own approval and execution handoffs are unaffected" in profile


def test_shared_method_derives_settled_mechanics_instead_of_confirming_them() -> None:
    method = (SKILLS / "grilling/SKILL.md").read_text(encoding="utf-8")
    collapsed = " ".join(method.split())

    assert "## Derive mechanics instead of asking" in method
    assert "These are derived, not open." in collapsed
    # Equivalent compliant implementations are chosen, never narrowed to one required algorithm.
    assert "select a simple implementation that satisfies it and name the requirement" in collapsed
    assert "Several implementations are usually equally compliant" in collapsed
    assert "Guessing silently and asking for confirmation both fail here" in collapsed
    # A settled answer is reopened by contradicting evidence, never by a determined detail.
    assert "a detail the settled constraint already determines is not such a reason" in collapsed
    # A real unknown stays open rather than being closed by an invented constraint.
    assert "keep it an explicit open question instead of inventing a constraint" in collapsed
    assert "Ask only where the allowed outcomes differ materially" in collapsed
    assert "Equivalent ways of reaching the same allowed outcome are not that." in collapsed
    # Capture keeps its place ahead of implementation in the plan's own ordered steps.
    assert "this checkpoint is step one, ahead of the implementation and verification steps" in (
        collapsed
    )


def test_okf_skill_uses_knowledge_commands_without_foreign_runtime_paths() -> None:
    text = (SKILLS / "okf/SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    for contract in (
        "projectctl knowledge search",
        "--budget",
        "projectctl knowledge validate",
        "mode: local",
        "Do not crawl editor or agent transcripts",
    ):
        assert contract in normalized
    for residue in (
        "${CLAUDE_SKILL_DIR}",
        "${CLAUDE_PLUGIN_ROOT}",
        "/okf:",
        "user-invocable:",
        "argument-hint:",
        "~/.claude",
    ):
        assert residue not in text


def test_nested_workflow_ports_do_not_embed_foreign_runtime_commands() -> None:
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


def test_setup_skill_documents_public_commands() -> None:
    text = (SKILLS / "pkstack-setup/SKILL.md").read_text(encoding="utf-8")
    for command in (
        "scripts/setup_pkstack.py",
        ".pkstack/bin/projectctl",
        "--dry-run --output json",
        "--update-managed",
        "doctor --output json",
        "/agent swap pkstack",
        "kiro-cli chat --v3 --agent pkstack",
    ):
        assert command in text


def test_maintenance_skill_documents_acceptance_commands_and_boundaries() -> None:
    text = (SKILLS / "pkstack-maintain/SKILL.md").read_text(encoding="utf-8")
    for contract in (
        "--source-id <source-id>",
        "--max-attempts 5",
        "--dry-run --update-managed --output json",
        "upstream accept --manifest maintenance/upstreams.json",
        "--expected-head <exact-head-commit> --dry-run",
        "never execute",
        "Never combine transitions from different sources",
        "maintenance/upstream-reviews.json` by hand",
    ):
        assert contract in text
    agent = json.loads((AGENTS / "pkstack.json").read_text(encoding="utf-8"))
    assert "/pkstack-maintain" in agent["prompt"]


def test_post_setup_workflow_attaches_the_pkstack_agent() -> None:
    usage = (ROOT / "docs" / "usage.md").read_text(encoding="utf-8")

    for path in (REPO_ROOT / "README.md", ROOT / "README.md"):
        document = path.read_text(encoding="utf-8")
        assert "/pkstack-setup" in document
        targets = re.findall(r"\[[^\]]+\]\(([^)\s]*docs/usage\.md)\)", document)
        assert len(targets) == 1
        assert (path.parent / targets[0]).resolve() == (ROOT / "docs" / "usage.md").resolve()
    assert "/agent swap pkstack" in usage
    assert "kiro-cli chat --v3 --agent pkstack" in usage


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
    monkeypatch.setattr(sys, "argv", ["setup_pkstack.py", "--root", "/tmp/example"])
    monkeypatch.setenv("PYTHONPATH", "/existing/pythonpath")

    with pytest.raises(RuntimeError, match="execve captured"):
        runpy.run_path(
            str(SKILLS / "pkstack-setup" / "scripts" / "setup_pkstack.py"),
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
        "pkstack.bootstrap",
        "--root",
        "/tmp/example",
    ]
    environment = captured["environment"]
    assert isinstance(environment, dict)
    assert environment["PYTHONPATH"] == os.pathsep.join((str(ROOT / "src"), "/existing/pythonpath"))


def test_setup_shim_older_python_without_uv_fails_before_target_writes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "version_info", (3, 9, 6))
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    monkeypatch.setattr(sys, "argv", ["setup_pkstack.py", "--root", str(tmp_path)])

    with pytest.raises(SystemExit, match=r"requires Python 3\.11\+ or uv"):
        runpy.run_path(
            str(SKILLS / "pkstack-setup" / "scripts" / "setup_pkstack.py"),
            run_name="__main__",
        )

    assert list(tmp_path.iterdir()) == []


def test_setup_shim_legacy_location_finds_the_project_controller(tmp_path: Path) -> None:
    shim = tmp_path / ".kiro" / "skills" / "pkstack-setup" / "scripts" / "setup_pkstack.py"
    shim.parent.mkdir(parents=True)
    shutil.copy2(SKILLS / "pkstack-setup" / "scripts" / "setup_pkstack.py", shim)
    cached_controller = tmp_path / ".pkstack" / "projectctl"
    cached_controller.mkdir(parents=True)

    namespace = runpy.run_path(str(shim), run_name="pkstack_setup_probe")

    assert namespace["POWER_ROOT"] == cached_controller


def test_verified_goal_is_current_session_and_deterministically_verified() -> None:
    text = (SKILLS / "pkstack-verified-goal" / "SKILL.md").read_text(encoding="utf-8")

    assert "Use `.pkstack/bin/projectctl` for the entire loop" in text
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
    assert "goal bind-spec <spec-name> --feature <slug>" in text
    assert 'goal start "<objective>" --spec <spec-name>' in text
    assert "requirements.md" in text and "bugfix.md" in text
    assert "Do not automatically run `goal resume`" in text
    assert "/spawn" not in text
    assert "kiro-cli" not in text.lower()


def test_skills_do_not_depend_on_cli_only_argument_substitution() -> None:
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        assert "$ARGUMENTS" not in text, path


def test_support_documentation_links_resolve() -> None:
    readme = REPO_ROOT / "README.md"
    assert "](reviews/release-status.md)" in readme.read_text(encoding="utf-8")
    for source in (readme, ROOT / "docs/kiro-v3-compatibility.md"):
        for target in re.findall(
            r"\[[^\]]+\]\(([^)\s]+\.md)(?:#[^)]*)?\)", source.read_text(encoding="utf-8")
        ):
            if "://" not in target:
                resolved = (source.parent / target).resolve()
                assert resolved.is_relative_to(REPO_ROOT.resolve()), (source, target)
                assert resolved.is_file(), (source, target)


def test_skills_inherit_native_model_selection() -> None:
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8").lower()
        assert "--model" not in text, path


def test_model_council_is_optional_advisory_and_not_a_runtime_claim() -> None:
    text = (SKILLS / "pkstack-model-council" / "SKILL.md").read_text(encoding="utf-8")
    lowered = text.lower()

    assert "optional and advisory" in lowered
    assert "not a kiro-native model runtime" in lowered
    assert "never auto-apply" in lowered
    assert "cannot accept" in lowered


def test_agent_templates_are_json_least_privilege_profiles() -> None:
    paths = sorted(AGENTS.glob("*.json"))
    assert {path.name for path in paths} == {
        "pkstack-architect.json",
        "pkstack-reviewer.json",
        "pkstack-verifier.json",
        "pkstack.json",
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

    assert "write" in json.loads((AGENTS / "pkstack.json").read_text())["tools"]
    primary_rules = json.loads((AGENTS / "pkstack.json").read_text())["permissions"]["rules"]
    assert any(
        rule["capability"] == "fs_read" and rule["effect"] == "allow" for rule in primary_rules
    )
    for read_only in (
        "pkstack-architect.json",
        "pkstack-reviewer.json",
        "pkstack-verifier.json",
    ):
        profile = json.loads((AGENTS / read_only).read_text())
        assert profile["tools"] == ["read", "knowledge"]
        assert profile["toolsSettings"] == {}
        assert not {"shell", "write", "fs_write"} & set(profile["toolsSettings"])
        assert not any(rule["capability"] == "shell" for rule in profile["permissions"]["rules"])


def test_primary_profile_asks_for_every_canonical_controller_route() -> None:
    primary = json.loads((AGENTS / "pkstack.json").read_text(encoding="utf-8"))
    ask_patterns = [
        pattern
        for rule in primary["permissions"]["rules"]
        if rule["capability"] == "shell" and rule["effect"] == "ask"
        for pattern in rule["match"]
    ]
    commands = (
        ".pkstack/bin/projectctl",
        ".pkstack/bin/projectctl version --output json",
        ".pkstack/bin/projectctl setup --power-root /reviewed --update-managed",
        ".pkstack/bin/projectctl doctor --output json",
        ".pkstack/bin/projectctl feature list --output json",
        ".pkstack/bin/projectctl feature show sample --output json",
        ".pkstack/bin/projectctl feature validate --output json",
        ".pkstack/bin/projectctl feature generate sample --ready",
        ".pkstack/bin/projectctl feature verify sample --output json",
        ".pkstack/bin/projectctl verify sample --output json",
        ".pkstack/bin/projectctl goal start objective --command verifier",
        ".pkstack/bin/projectctl goal bind-spec sample --feature sample --output json",
        ".pkstack/bin/projectctl goal status --output json",
        ".pkstack/bin/projectctl goal verify --output json",
        ".pkstack/bin/projectctl goal resume --add-attempts 1",
        ".pkstack/bin/projectctl goal clear --force",
        ".pkstack/bin/projectctl goal tripwire --output json",
        ".pkstack/bin/projectctl knowledge status --output json",
        ".pkstack/bin/projectctl knowledge validate --output json",
        ".pkstack/bin/projectctl knowledge search sample --output json",
        ".pkstack/bin/projectctl future-command --future-option",
    )

    assert set(ask_patterns) >= {
        ".pkstack/bin/projectctl",
        ".pkstack/bin/projectctl *",
    }
    for command in commands:
        assert any(fnmatchcase(command, pattern) for pattern in ask_patterns), command


def test_primary_profile_denies_direct_control_plane_writes_and_common_clobbers() -> None:
    primary = json.loads((AGENTS / "pkstack.json").read_text(encoding="utf-8"))
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
        ".pkstack/**",
        ".kiro/agents/**",
        ".kiro/hooks/**",
        ".kiro/steering/**",
    }
    assert ".kiro/skills/**" not in denied_writes
    managed_live_skills = EXPECTED_SKILLS - {"pkstack-setup"}
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


def test_primary_profile_denies_reordered_destructive_switch_flags() -> None:
    primary = json.loads((AGENTS / "pkstack.json").read_text(encoding="utf-8"))
    shell_rules = [
        rule for rule in primary["permissions"]["rules"] if rule["capability"] == "shell"
    ]

    def effect(command: str) -> str:
        matches = {
            rule["effect"]
            for rule in shell_rules
            if any(fnmatchcase(command, pattern) for pattern in rule["match"])
        }
        return next(value for value in ("deny", "ask", "allow") if value in matches)

    destructive_options = (
        "-f main",
        "--force main",
        "--discard-changes main",
        "-C topic",
        "-Ctopic",
        "--force-create topic",
        "--force-create=topic",
        "-qf main",
        "-dqf main",
        "-qC topic",
        "-qCtopic",
    )
    for git_prefix in ("git", "git -C nested", "git --no-pager -C nested"):
        for preceding_options in ("", "--no-guess ", "-t ", "--quiet ", "--progress ", "--detach "):
            for destructive_option in destructive_options:
                command = f"{git_prefix} switch {preceding_options}{destructive_option}"
                assert effect(command) == "deny", command
        for following_flag in ("-f", "--force", "--discard-changes"):
            command = f"{git_prefix} switch main {following_flag}"
            assert effect(command) == "deny", command
        for benign_options in (
            "main",
            "-c topic",
            "--create topic",
            "--no-guess feature",
            "--quiet -c feature",
            "--track origin/feature",
            "--detach HEAD",
            "-q feature",
            "-dq feature",
            "--no-guess -q feature",
            "--no-guess -dq feature",
            "-q Case-sensitive-topic",
        ):
            command = f"{git_prefix} switch {benign_options}"
            assert effect(command) == "ask", command


def test_skill_authoring_respects_bootstrap_owned_routes() -> None:
    for name in ("automate-me", "create-verification-skill", "reflect"):
        text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        assert ".pkstack/bootstrap.json" in text
        assert "receipt-managed" in text


def test_primary_profile_never_allows_git_forms_that_execute_read_or_write() -> None:
    primary = json.loads((AGENTS / "pkstack.json").read_text(encoding="utf-8"))
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
        "git log -1 --format=%B --output=.pkstack/state/goal.json",
        "git show --output=/tmp/escape HEAD",
        "git log --output=../outside.txt",
        "git diff --no-index /etc/hosts /dev/null",
        "git status --short",
    )

    for command in commands:
        assert not any(fnmatchcase(command, pattern) for pattern in shell_allow), command
        assert any(fnmatchcase(command, pattern) for pattern in shell_ask), command


def test_post_swap_setup_refresh_uses_power_local_authority() -> None:
    steering = (ROOT / "dev.kiro" / "steering" / "pkstack-core.md").read_text(encoding="utf-8")
    normalized = " ".join(steering.split())

    assert "/agent swap default" in normalized
    assert "/pkstack-setup" in normalized
    assert "/agent swap pkstack" in normalized
    assert "--power-root" in normalized


def test_verified_goal_surfaces_stored_predicate_before_first_attempt() -> None:
    text = (SKILLS / "pkstack-verified-goal" / "SKILL.md").read_text(encoding="utf-8")

    assert "Before the first verification attempt" in text
    assert "in every skill invocation" in text
    assert "already active" in text
    assert "goal.contract.display" in text
    assert "shell approval UI" in text


def test_subagent_trust_is_explicit_and_bounded_to_shipped_profiles() -> None:
    primary = json.loads((AGENTS / "pkstack.json").read_text(encoding="utf-8"))
    settings = primary["toolsSettings"]["subagent"]

    assert settings["availableAgents"] == [
        "pkstack-architect",
        "pkstack-reviewer",
        "pkstack-verifier",
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
        for match in re.finditer(r"^\s*(pkstack(?:-[a-z]+)?)\s+Workspace\b", output, re.MULTILINE)
    }
    assert discovered == {
        "pkstack",
        "pkstack-architect",
        "pkstack-reviewer",
        "pkstack-verifier",
    }


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
                    assert not command.startswith(("./projectctl", ".pkstack/bin/projectctl"))
                    assert "; .pkstack/bin/projectctl" not in command
                    assert "&& .pkstack/bin/projectctl" not in command


def test_stop_tripwire_is_disabled_and_advisory() -> None:
    tripwire = json.loads((HOOKS / "pkstack-tripwire.json").read_text(encoding="utf-8"))
    hooks = tripwire["hooks"]

    assert len(hooks) == 1
    hook = hooks[0]
    assert hook["trigger"] == "Stop"
    assert hook["enabled"] is False
    assert "goal tripwire --output json" in hook["action"]["command"]


def test_steering_uses_native_always_and_file_match_inclusion() -> None:
    paths = sorted(STEERING.glob("*.md"))
    assert {path.name for path in paths} == {
        "pkstack-core.md",
        "pkstack-safety.md",
        "pkstack-typescript.md",
        "pkstack-unslop.md",
    }

    for path in paths:
        metadata, body = _frontmatter(path)
        if path.name == "pkstack-typescript.md":
            assert metadata == {
                "inclusion": "fileMatch",
                "fileMatchPattern": ["**/*.ts", "**/*.tsx"],
            }
            normalized = " ".join(body.split())
            assert "typescript-best-practices" in normalized
        else:
            assert metadata == {"inclusion": "always"}


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
