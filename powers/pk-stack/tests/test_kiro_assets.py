from __future__ import annotations

import json
import os
import runpy
import shutil
import sys
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

EXPECTED_SKILLS = {
    "architect",
    "arena",
    "model-council",
    "setup-pstack",
    "swarm",
    "verified-goal",
}
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
        *SKILLS.glob("*/SKILL.md"),
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


@pytest.mark.parametrize("skill_name", sorted(EXPECTED_SKILLS))
def test_skill_frontmatter_matches_agent_skills_standard(skill_name: str) -> None:
    path = SKILLS / skill_name / "SKILL.md"
    metadata, body = _frontmatter(path)

    assert metadata["name"] == skill_name
    assert set(metadata) <= ALLOWED_SKILL_FRONTMATTER
    assert isinstance(metadata["description"], str)
    assert 20 <= len(metadata["description"]) <= 1024
    assert body


def test_only_expected_skill_directories_are_present() -> None:
    actual = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert actual == EXPECTED_SKILLS


def test_setup_skill_uses_idempotent_json_contract() -> None:
    text = (SKILLS / "setup-pstack" / "SKILL.md").read_text(encoding="utf-8")

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
    assert "global default" in text


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
            str(SKILLS / "setup-pstack" / "scripts" / "setup_pstack.py"),
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
    shim = tmp_path / ".kiro" / "skills" / "setup-pstack" / "scripts" / "setup_pstack.py"
    shim.parent.mkdir(parents=True)
    shutil.copy2(SKILLS / "setup-pstack" / "scripts" / "setup_pstack.py", shim)
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
    assert "$ARGUMENTS" in text
    assert "current interactive Kiro session" in text
    assert "executable verifier" in text
    assert "Do not automatically run `goal resume`" in text
    assert "/spawn" not in text
    assert "kiro-cli" not in text.lower()


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
        ".kiro/skills/**",
        ".kiro/steering/**",
    }
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

    assert "/agent swap kiro_default" in steering
    assert "/setup-pstack" in steering
    assert "/agent swap pstack" in steering
    assert "--power-root" in steering


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


def test_steering_is_small_always_on_context() -> None:
    paths = sorted(STEERING.glob("*.md"))
    assert {path.name for path in paths} == {"pstack-core.md", "pstack-safety.md"}

    for path in paths:
        metadata, body = _frontmatter(path)
        assert metadata == {"inclusion": "always"}
        assert len(body) < 2_000


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
