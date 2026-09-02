from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from pstack_kiro.bootstrap import (
    GITIGNORE_BLOCK,
    GITIGNORE_RESULT_KEY,
    REQUIRED_SOURCE_MODULES,
    TARGET_README,
)
from pstack_kiro.branding import (
    DISPLAY_NAME,
    DISTRIBUTION_NAME,
    EXPANDED_NAME,
    POWER_ID,
    RECEIPT_MANAGER,
    identity_payload,
)

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDENTITY = {
    "name": "pstack-kiro",
    "display_name": "PK-Stack",
    "expanded_name": "Poteto Kiro",
    "power_id": "pk-stack",
}


def test_runtime_identity_has_one_brand_and_explicit_compatibility_name() -> None:
    assert identity_payload() == EXPECTED_IDENTITY
    assert EXPECTED_IDENTITY["name"] == DISTRIBUTION_NAME == RECEIPT_MANAGER
    assert EXPECTED_IDENTITY["display_name"] == DISPLAY_NAME
    assert EXPECTED_IDENTITY["expanded_name"] == EXPANDED_NAME
    assert EXPECTED_IDENTITY["power_id"] == POWER_ID


def test_manifest_and_distribution_separate_brand_from_compatibility_id() -> None:
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert manifest["name"] == POWER_ID
    assert re.fullmatch(r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", POWER_ID)
    assert set(manifest) <= {
        "$schema",
        "author",
        "description",
        "homepage",
        "keywords",
        "license",
        "name",
        "repository",
        "version",
    }
    assert manifest["description"].startswith(f"{DISPLAY_NAME} ({EXPANDED_NAME}):")
    assert {DISPLAY_NAME, EXPANDED_NAME, "pstack"} <= set(manifest["keywords"])
    assert project["name"] == DISTRIBUTION_NAME
    assert project["description"].startswith(DISPLAY_NAME)
    assert manifest["author"]["name"] == project["authors"][0]["name"]
    assert manifest["author"]["name"] == f"{DISPLAY_NAME} contributors"
    copyright_line = f"Copyright 2026 {DISPLAY_NAME} contributors"
    assert copyright_line in (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert copyright_line in (ROOT / "LICENSE").read_text(encoding="utf-8")


def test_generated_surfaces_use_brand_without_renaming_installed_paths() -> None:
    assert "branding.py" in REQUIRED_SOURCE_MODULES
    assert GITIGNORE_BLOCK.startswith(f"# {DISPLAY_NAME} runtime state")
    assert GITIGNORE_RESULT_KEY == ".gitignore:pstack-runtime-block"
    assert f"managed by the {DISPLAY_NAME} bootstrap" in TARGET_README
    assert ".pstack/bin/projectctl" in TARGET_README


def test_human_facing_surfaces_use_the_pk_stack_brand() -> None:
    expected = {
        ROOT / "README.md": (f"# {DISPLAY_NAME}", EXPANDED_NAME),
        ROOT / "docs" / "architecture.md": (f"{DISPLAY_NAME} owns workflow semantics",),
        ROOT / "docs" / "kiro-v3-compatibility.md": (f"{DISPLAY_NAME} use",),
        ROOT / "docs" / "usage.md": (f"{DISPLAY_NAME} keeps implementation",),
        ROOT / "dev.kiro" / "steering" / "pstack-core.md": (f"# {DISPLAY_NAME} operating model",),
        ROOT / "dev.kiro" / "steering" / "pstack-safety.md": (f"# {DISPLAY_NAME} safety boundary",),
        ROOT / "skills" / "setup-pstack" / "SKILL.md": (f"# Set up {DISPLAY_NAME}",),
    }
    for path, markers in expected.items():
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            assert marker in content, f"{path.relative_to(ROOT)} is missing {marker!r}"


def test_agent_ids_remain_compatible_while_visible_copy_is_branded() -> None:
    agent_root = ROOT / "templates" / "project" / ".kiro" / "agents"
    profiles = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in agent_root.glob("*.json")
    }
    primary = profiles["pstack"]

    assert primary["name"] == "pstack"
    assert DISPLAY_NAME in primary["prompt"]
    assert primary["welcomeMessage"].startswith(EXPANDED_NAME)
    assert DISPLAY_NAME in primary["welcomeMessage"]
    assert set(profiles) == {"pstack", "pstack-architect", "pstack-reviewer", "pstack-verifier"}
    for name, profile in profiles.items():
        assert profile["name"] == name
        assert DISPLAY_NAME in profile["description"]


def test_hook_payloads_keep_compatibility_key_and_expose_display_brand() -> None:
    hook_root = ROOT / "templates" / "project" / ".kiro" / "hooks"
    for path in hook_root.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        command = payload["hooks"][0]["action"]["command"]
        match = re.search(r"'(\{.*\})'", command)
        assert match is not None
        fallback = json.loads(match.group(1))
        assert fallback["pstack"]
        assert {key: fallback[key] for key in identity_payload() if key != "name"} == {
            key: value for key, value in identity_payload().items() if key != "name"
        }
