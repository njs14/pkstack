from __future__ import annotations

import json
import re
import struct
import tomllib
from pathlib import Path

from pkstack.bootstrap import (
    GITIGNORE_BLOCK,
    GITIGNORE_RESULT_KEY,
    REQUIRED_SOURCE_MODULES,
    TARGET_README,
)
from pkstack.branding import (
    DISPLAY_NAME,
    DISTRIBUTION_NAME,
    EXPANDED_NAME,
    POWER_ID,
    RECEIPT_MANAGER,
    identity_payload,
)

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parents[1]
EXPECTED_IDENTITY = {
    "name": "pkstack",
    "display_name": "PKStack",
    "expanded_name": "Poteto Kiro",
    "power_id": "pkstack",
}


def _png_dimensions(payload: bytes) -> tuple[int, int]:
    assert payload.startswith(b"\x89PNG\r\n\x1a\n")
    assert payload[12:16] == b"IHDR"
    width, height = struct.unpack(">II", payload[16:24])
    assert width > 0 and height > 0
    return width, height


def test_runtime_identity_uses_one_brand() -> None:
    assert identity_payload() == EXPECTED_IDENTITY
    assert EXPECTED_IDENTITY["name"] == DISTRIBUTION_NAME == RECEIPT_MANAGER
    assert EXPECTED_IDENTITY["display_name"] == DISPLAY_NAME
    assert EXPECTED_IDENTITY["expanded_name"] == EXPANDED_NAME
    assert EXPECTED_IDENTITY["power_id"] == POWER_ID


def test_manifest_and_distribution_share_the_pkstack_identity() -> None:
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
    assert DISPLAY_NAME in manifest["description"] and EXPANDED_NAME in manifest["description"]
    assert {DISPLAY_NAME, EXPANDED_NAME, "pkstack"} <= set(manifest["keywords"])
    assert project["name"] == DISTRIBUTION_NAME
    assert DISPLAY_NAME in project["description"]
    assert manifest["author"]["name"] == project["authors"][0]["name"]
    assert manifest["author"]["name"] == f"{DISPLAY_NAME} contributors"
    copyright_line = f"Copyright 2026 {DISPLAY_NAME} contributors"
    assert copyright_line in (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert copyright_line in (ROOT / "LICENSE").read_text(encoding="utf-8")


def test_generated_surfaces_use_the_pkstack_paths() -> None:
    assert "branding.py" in REQUIRED_SOURCE_MODULES
    assert GITIGNORE_BLOCK.startswith(f"# {DISPLAY_NAME} runtime state")
    assert GITIGNORE_RESULT_KEY == ".gitignore:pkstack-runtime-block"
    assert ".pkstack/bin/projectctl" in TARGET_README


def test_human_facing_surfaces_use_the_pkstack_brand() -> None:
    paths = (
        ROOT / "README.md",
        ROOT / "docs/architecture.md",
        ROOT / "docs/kiro-v3-compatibility.md",
        ROOT / "docs/usage.md",
        *(ROOT / "dev.kiro/steering").glob("*.md"),
        ROOT / "skills/pkstack-setup/SKILL.md",
    )
    for path in paths:
        assert DISPLAY_NAME in path.read_text(encoding="utf-8"), path


def test_repository_logo_is_a_png_asset() -> None:
    _png_dimensions((ROOT / "assets/logo.png").read_bytes())


def test_readmes_reference_the_bundled_logo() -> None:
    _png_dimensions((ROOT / "assets/logo.png").read_bytes())
    for readme, source in (
        (REPOSITORY_ROOT / "README.md", "powers/pkstack/assets/logo.png"),
        (ROOT / "README.md", "assets/logo.png"),
    ):
        image = re.search(rf'<img\b[^>]*src="{re.escape(source)}"[^>]*>', readme.read_text())
        assert image is not None, readme
        assert (readme.parent / source).is_file()
        alt = re.search(r'\balt="([^"]+)"', image.group())
        assert alt is not None and DISPLAY_NAME in alt.group(1)


def test_usage_does_not_present_the_distribution_as_a_checkout() -> None:
    usage = (ROOT / "docs" / "usage.md").read_text(encoding="utf-8")

    assert "/absolute/path/to/pkstack/" not in usage


def test_readmes_link_to_documentation_and_public_entrypoints() -> None:
    for path in (REPOSITORY_ROOT / "README.md", ROOT / "README.md"):
        content = path.read_text(encoding="utf-8")
        assert DISPLAY_NAME in content.splitlines()[0]
        for detail in ("curated-skills.md", "first-task.md", "usage.md", "release-status.md"):
            assert detail in content
        assert "/pkstack-setup" in content and "/pkstack <task>" in content
        for target in re.findall(r"!?\[[^]]*\]\(([^)#]+)(?:#[^)]*)?\)", content):
            if not target.startswith(("https://", "http://")):
                assert (path.parent / target).is_file(), f"broken README link: {target}"


def test_documentation_diagrams_keep_sources_and_resolving_previews() -> None:
    artifacts = ROOT / "docs" / "artifacts"
    for name in ("pkstack-architecture", "pkstack-task-workflow", "pkstack-updater-workflow"):
        spec = json.loads((artifacts / f"{name}.json").read_text(encoding="utf-8"))
        assert spec["meta"]["quality_profile"] == "showcase"
        assert (artifacts / f"{name}.html").is_file()
        png = (artifacts / f"{name}.png").read_bytes()
        _png_dimensions(png)
    references = {
        REPOSITORY_ROOT / "README.md": "powers/pkstack/docs/artifacts/pkstack-architecture.png",
        ROOT / "docs" / "architecture.md": "artifacts/pkstack-architecture.png",
        ROOT / "docs" / "usage.md": "artifacts/pkstack-task-workflow.png",
        ROOT / "docs" / "upstream-control-loop.md": "artifacts/pkstack-updater-workflow.png",
    }
    for path, target in references.items():
        assert target in path.read_text(encoding="utf-8")
        assert (path.parent / target).is_file()


def test_agent_ids_use_the_pkstack_name() -> None:
    agent_root = ROOT / "templates" / "project" / ".kiro" / "agents"
    profiles = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in agent_root.glob("*.json")
    }
    primary = profiles["pkstack"]

    assert primary["name"] == "pkstack"
    assert DISPLAY_NAME in primary["prompt"]
    assert DISPLAY_NAME in primary["welcomeMessage"]
    assert set(profiles) == {
        "pkstack",
        "pkstack-architect",
        "pkstack-reviewer",
        "pkstack-verifier",
    }
    for name, profile in profiles.items():
        assert profile["name"] == name
        assert DISPLAY_NAME in profile["description"]


def test_hook_payloads_use_pkstack_key_and_expose_display_brand() -> None:
    hook_root = ROOT / "templates" / "project" / ".kiro" / "hooks"
    for path in hook_root.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        command = payload["hooks"][0]["action"]["command"]
        match = re.search(r"'(\{.*\})'", command)
        assert match is not None
        fallback = json.loads(match.group(1))
        assert fallback["pkstack"]
        assert {key: fallback[key] for key in identity_payload() if key != "name"} == {
            key: value for key, value in identity_payload().items() if key != "name"
        }


def test_active_user_guidance_does_not_use_legacy_pkstack_names() -> None:
    paths = {
        *(
            REPOSITORY_ROOT / name
            for name in ("README.md", "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md")
        ),
        ROOT / "README.md",
        ROOT / "docs" / "artifacts" / "pkstack-architecture.html",
        ROOT / "docs" / "artifacts" / "pkstack-architecture.json",
        *(ROOT / "docs").rglob("*.md"),
        *(ROOT / "dev.kiro").rglob("*.md"),
        *(REPOSITORY_ROOT / "Wiki").rglob("*.md"),
        *(
            path
            for path in (ROOT / "skills").rglob("*.md")
            if "upstream" not in path.relative_to(ROOT / "skills").parts
        ),
    }
    # Historical reviews and bundled upstream bytes are outside this scan. These exact
    # live references identify an external lab, durable provenance markers, stable
    # GitHub workflow IDs, a retained historical report, or the old files users must
    # inspect before a clean install. Historical report links retain original names.
    exceptions = (
        "pk-stack-floci-lab",
        "pk-stack-upstream-genesis",
        "pk-stack-upstream-review",
        "reviews/pk-stack-maintenance-campaign.md",
        ".pk-stack/bootstrap.json",
        "`pk-stack`-named agent files",
        *(path.name for path in (REPOSITORY_ROOT / ".github" / "workflows").glob("pk-stack-*.yml")),
    )
    legacy_phrases = (
        "--agent pstack",
        "/agent swap pstack",
        "skills + pstack agent",
        "setup_pstack.py",
        ".pstack/",
        "pstack_kiro",
        "pstack-kiro",
        "PK-Stack",
        "PK-STACK",
        "pk-stack",
        "pk_stack",
        "PK_STACK",
    )

    legacy_route = re.compile(
        r"(?<![\w/])/(?:poteto-mode|setup-pstack|setup-pk-stack|maintain-pk-stack|"
        r"verified-goal|model-council|principles)(?![\w/-])"
    )
    for path in sorted(paths):
        content = path.read_text(encoding="utf-8")
        if path.suffix in {".html", ".json"}:
            # The diagram's source anchors refer to a frozen pre-rename commit.
            content = re.sub(
                r"https://github\.com/njs14/pkstack/blob/[0-9a-f]{40}/powers/pk-stack/",
                "historical-source/",
                content,
            )
            content = re.sub(
                r'"path":\s*"powers/pk-stack/docs/architecture\.md"',
                '"path":"historical-source"',
                content,
            )
        for exception in exceptions:
            content = content.replace(exception, "")
        for phrase in legacy_phrases:
            assert phrase not in content, f"{path} still contains {phrase!r}"
        assert not legacy_route.search(content), f"{path} still advertises a retired slash command"
