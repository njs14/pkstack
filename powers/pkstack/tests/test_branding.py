from __future__ import annotations

import json
import re
import struct
import tomllib
import zlib
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


def _decode_rgba_png(payload: bytes) -> tuple[int, int, bytes]:
    """Decode the deliberately simple, non-interlaced RGBA logo with the stdlib."""

    assert payload.startswith(b"\x89PNG\r\n\x1a\n")
    offset = 8
    idat = bytearray()
    width = height = 0
    saw_iend = False

    while offset < len(payload):
        assert offset + 12 <= len(payload), "truncated PNG chunk"
        length = struct.unpack(">I", payload[offset : offset + 4])[0]
        chunk_type = payload[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        assert data_end + 4 <= len(payload), "truncated PNG chunk payload"
        data = payload[data_start:data_end]
        expected_crc = struct.unpack(">I", payload[data_end : data_end + 4])[0]
        assert zlib.crc32(chunk_type + data) & 0xFFFFFFFF == expected_crc

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", data
            )
            assert (bit_depth, color_type, compression, filtering, interlace) == (8, 6, 0, 0, 0)
        elif chunk_type == b"IDAT":
            idat.extend(data)
        elif chunk_type == b"IEND":
            saw_iend = True
            assert data == b""
            assert data_end + 4 == len(payload), "bytes follow IEND"
            break
        offset = data_end + 4

    assert width > 0 and height > 0 and idat and saw_iend
    packed = zlib.decompress(bytes(idat))
    stride = width * 4
    assert len(packed) == height * (stride + 1)
    decoded = bytearray(height * stride)
    prior = bytearray(stride)

    for row_index in range(height):
        packed_offset = row_index * (stride + 1)
        filter_type = packed[packed_offset]
        filtered = packed[packed_offset + 1 : packed_offset + 1 + stride]
        row = bytearray(stride)
        for index, value in enumerate(filtered):
            left = row[index - 4] if index >= 4 else 0
            above = prior[index]
            upper_left = prior[index - 4] if index >= 4 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                estimate = left + above - upper_left
                distances = (
                    abs(estimate - left),
                    abs(estimate - above),
                    abs(estimate - upper_left),
                )
                predictor = (left, above, upper_left)[distances.index(min(distances))]
            else:
                raise AssertionError(f"unsupported PNG filter {filter_type}")
            row[index] = (value + predictor) & 0xFF
        decoded[row_index * stride : (row_index + 1) * stride] = row
        prior = row

    return width, height, bytes(decoded)


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
    assert manifest["description"].startswith(f"{DISPLAY_NAME} ({EXPANDED_NAME}):")
    assert {DISPLAY_NAME, EXPANDED_NAME, "pkstack"} <= set(manifest["keywords"])
    assert project["name"] == DISTRIBUTION_NAME
    assert project["description"].startswith(DISPLAY_NAME)
    assert manifest["author"]["name"] == project["authors"][0]["name"]
    assert manifest["author"]["name"] == f"{DISPLAY_NAME} contributors"
    copyright_line = f"Copyright 2026 {DISPLAY_NAME} contributors"
    assert copyright_line in (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert copyright_line in (ROOT / "LICENSE").read_text(encoding="utf-8")


def test_generated_surfaces_use_the_pkstack_paths() -> None:
    assert "branding.py" in REQUIRED_SOURCE_MODULES
    assert GITIGNORE_BLOCK.startswith(f"# {DISPLAY_NAME} runtime state")
    assert GITIGNORE_RESULT_KEY == ".gitignore:pkstack-runtime-block"
    assert f"managed by the {DISPLAY_NAME} bootstrap" in TARGET_README
    assert ".pkstack/bin/projectctl" in TARGET_README


def test_human_facing_surfaces_use_the_pkstack_brand() -> None:
    expected = {
        ROOT / "README.md": (f"# {DISPLAY_NAME}",),
        ROOT / "docs" / "architecture.md": (f"{DISPLAY_NAME} owns workflow semantics",),
        ROOT / "docs" / "kiro-v3-compatibility.md": (f"{DISPLAY_NAME} use",),
        ROOT / "docs" / "usage.md": (f"{DISPLAY_NAME} keeps implementation",),
        ROOT / "dev.kiro" / "steering" / "pkstack-core.md": (f"# {DISPLAY_NAME} operating model",),
        ROOT / "dev.kiro" / "steering" / "pkstack-safety.md": (
            f"# {DISPLAY_NAME} safety boundary",
        ),
        ROOT / "dev.kiro" / "steering" / "pkstack-typescript.md": (
            f"# {DISPLAY_NAME} TypeScript discipline",
        ),
        ROOT / "dev.kiro" / "steering" / "pkstack-unslop.md": (
            f"# {DISPLAY_NAME} prose discipline",
        ),
        ROOT / "skills" / "pkstack-setup" / "SKILL.md": (f"# Set up {DISPLAY_NAME}",),
    }
    for path, markers in expected.items():
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            assert marker in content, f"{path.relative_to(ROOT)} is missing {marker!r}"


def test_repository_artwork_is_square_rgba_without_extending_the_manifest() -> None:
    logo = ROOT / "assets" / "logo.png"
    payload = logo.read_bytes()

    width, height, rgba = _decode_rgba_png(payload)
    assert width == height
    assert width >= 512
    alpha = rgba[3::4]
    corner_indices = (0, width - 1, (height - 1) * width, height * width - 1)
    assert all(alpha[index] == 0 for index in corner_indices)
    assert max(alpha) == 255
    assert "logo" not in json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))


def test_readmes_use_the_compact_wide_banner_and_preserve_the_square_logo() -> None:
    banner = (ROOT / "assets" / "banner.png").read_bytes()
    assert banner.startswith(b"\x89PNG\r\n\x1a\n")
    assert banner[12:16] == b"IHDR"
    width, height = struct.unpack(">II", banner[16:24])
    assert width >= 600 and height > 0
    assert width / height >= 2.4
    assert banner != (ROOT / "assets" / "logo.png").read_bytes()
    for readme, source in (
        (REPOSITORY_ROOT / "README.md", "powers/pkstack/assets/banner.png"),
        (ROOT / "README.md", "assets/banner.png"),
    ):
        image = re.search(rf'<img\b[^>]*src="{re.escape(source)}"[^>]*>', readme.read_text())
        assert image is not None, readme
        assert 'width="600"' in image.group()
        assert 'alt="PKStack:' in image.group()
        assert "height=" not in image.group(), "keep the banner's natural aspect ratio"


def test_usage_does_not_present_the_distribution_as_a_checkout() -> None:
    usage = (ROOT / "docs" / "usage.md").read_text(encoding="utf-8")

    assert "/absolute/path/to/pkstack/" not in usage


def test_readmes_stay_short_and_link_to_the_details() -> None:
    for path, limit in ((REPOSITORY_ROOT / "README.md", 300), (ROOT / "README.md", 200)):
        content = path.read_text(encoding="utf-8")
        assert content.startswith("# PKStack & friends\n")
        prose = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        prose = re.sub(r"!\[[^]]*\]\([^)]*\)", "", prose)
        prose = re.sub(r"\[([^]]*)\]\([^)]*\)", r"\1", prose)
        prose = re.sub(r"<[^>]*>", "", prose)
        words = re.findall(r"\S+", prose)
        assert len(words) <= limit, f"{path}: {len(words)} words exceeds {limit}"
        for detail in ("curated-skills.md", "first-task.md", "usage.md", "release-status.md"):
            assert detail in content
        assert "## Install" in content
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
        assert png.startswith(b"\x89PNG\r\n\x1a\n") and png[12:16] == b"IHDR"
        width, height = struct.unpack(">II", png[16:24])
        assert width >= 1200 and 0 < height < width
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
    assert primary["welcomeMessage"].startswith(EXPANDED_NAME)
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
    # GitHub workflow IDs, or the old files users must inspect before a clean install.
    exceptions = (
        "pk-stack-floci-lab",
        "pk-stack-upstream-genesis",
        "pk-stack-upstream-review",
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
