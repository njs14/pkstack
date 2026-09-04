from __future__ import annotations

import json
import re
import struct
import tomllib
import zlib
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
REPOSITORY_ROOT = ROOT.parents[1]
EXPECTED_IDENTITY = {
    "name": "pstack-kiro",
    "display_name": "PK-Stack",
    "expanded_name": "Poteto Kiro",
    "power_id": "pk-stack",
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
    assert {DISPLAY_NAME, EXPANDED_NAME, "pk-stack"} <= set(manifest["keywords"])
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
        ROOT / "dev.kiro" / "steering" / "pk-stack-core.md": (f"# {DISPLAY_NAME} operating model",),
        ROOT / "dev.kiro" / "steering" / "pk-stack-safety.md": (
            f"# {DISPLAY_NAME} safety boundary",
        ),
        ROOT / "dev.kiro" / "steering" / "pk-stack-typescript.md": (
            f"# {DISPLAY_NAME} TypeScript discipline",
        ),
        ROOT / "dev.kiro" / "steering" / "pk-stack-unslop.md": (
            f"# {DISPLAY_NAME} prose discipline",
        ),
        ROOT / "skills" / "setup-pk-stack" / "SKILL.md": (f"# Set up {DISPLAY_NAME}",),
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
    assert "assets/logo.png" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "logo" not in json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))


def test_usage_does_not_present_the_compatibility_distribution_as_a_checkout() -> None:
    usage = (ROOT / "docs" / "usage.md").read_text(encoding="utf-8")

    assert "/absolute/path/to/pstack-kiro/" not in usage


def test_agent_ids_use_the_pk_stack_name() -> None:
    agent_root = ROOT / "templates" / "project" / ".kiro" / "agents"
    profiles = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in agent_root.glob("*.json")
    }
    primary = profiles["pk-stack"]

    assert primary["name"] == "pk-stack"
    assert DISPLAY_NAME in primary["prompt"]
    assert primary["welcomeMessage"].startswith(EXPANDED_NAME)
    assert DISPLAY_NAME in primary["welcomeMessage"]
    assert set(profiles) == {
        "pk-stack",
        "pk-stack-architect",
        "pk-stack-reviewer",
        "pk-stack-verifier",
    }
    for name, profile in profiles.items():
        assert profile["name"] == name
        assert DISPLAY_NAME in profile["description"]


def test_hook_payloads_use_pk_stack_key_and_expose_display_brand() -> None:
    hook_root = ROOT / "templates" / "project" / ".kiro" / "hooks"
    for path in hook_root.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        command = payload["hooks"][0]["action"]["command"]
        match = re.search(r"'(\{.*\})'", command)
        assert match is not None
        fallback = json.loads(match.group(1))
        assert fallback["pk_stack"]
        assert {key: fallback[key] for key in identity_payload() if key != "name"} == {
            key: value for key, value in identity_payload().items() if key != "name"
        }


def test_active_user_guidance_does_not_use_legacy_agent_or_setup_names() -> None:
    paths = (
        REPOSITORY_ROOT / "README.md",
        ROOT / "README.md",
        ROOT / "docs" / "usage.md",
        ROOT / "docs" / "kiro-v3-compatibility.md",
        ROOT / "docs" / "artifacts" / "pk-stack-architecture.json",
        ROOT / "docs" / "artifacts" / "pk-stack-architecture.html",
    )
    legacy_phrases = (
        "--agent pstack",
        "/agent swap pstack",
        "skills + pstack agent",
        "setup_pstack.py",
    )

    for path in paths:
        content = path.read_text(encoding="utf-8")
        for phrase in legacy_phrases:
            assert phrase not in content, f"{path} still contains {phrase!r}"
