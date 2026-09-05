from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_archify_rejects_a_segment_caption_without_clearance(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Archify requires optional Node.js 18+")  # ty: ignore[too-many-positional-arguments]
    tests = Path(__file__).parent
    fixture = json.loads((tests / "fixtures/archify-account-request.sequence.json").read_text())
    fixture["segments"][0].update(
        {
            "from": 245,
            "to": 253,
            "label": "A long segment label over the request acceptance region",
        }
    )
    source = tmp_path / "crowded.json"
    source.write_text(json.dumps(fixture))
    result = subprocess.run(
        [
            node,
            str(tests.parent / "skills/archify/upstream/bin/archify.mjs"),
            "validate",
            "sequence",
            str(source),
            "--quality",
            "showcase",
            "--json",
        ],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["ok"] is False
    assert "has no clear position above or within its band" in receipt["error"]


@pytest.mark.parametrize("previous_band", [(150, 300), (276, 294)])
def test_archify_keeps_a_native_authored_caption_with_its_band(
    tmp_path: Path, previous_band: tuple[int, int]
) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Archify requires optional Node.js 18+")  # ty: ignore[too-many-positional-arguments]
    tests = Path(__file__).parent
    source = tests / "fixtures/archify-native-account-request.sequence.json"
    if previous_band != (150, 300):
        # A short preceding band must not let upward placement jump over it.
        variant = json.loads(source.read_text())
        variant["segments"][0].update(zip(("from", "to"), previous_band, strict=True))
        source = tmp_path / "short-band.json"
        source.write_text(json.dumps(variant))
    output = tmp_path / "native.html"
    result = subprocess.run(
        [
            node,
            str(tests.parent / "skills/archify/upstream/bin/archify.mjs"),
            "deliver",
            "sequence",
            str(source),
            str(output),
            "--quality",
            "showcase",
            "--json",
        ],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    match = re.search(
        r'<g data-graph-role="segment-label" data-segment-id="1">\s*'
        r'<rect x="[\d.]+" y="([\d.]+)" width="[\d.]+" height="([\d.]+)"',
        output.read_text(),
    )
    assert match is not None
    y, height = map(float, match.groups())
    bands = json.loads(source.read_text())["segments"]
    assert y >= bands[0]["to"] + 2
    assert bands[1]["from"] <= y and y + height <= bands[1]["to"]


def test_archify_reader_layout_and_exports(tmp_path: Path) -> None:
    """Exercise the vendored viewer in a fresh browser against the release repro."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("Archify requires optional Node.js 18+")  # ty: ignore[too-many-positional-arguments]
    result = subprocess.run(
        [node, str(Path(__file__).with_suffix(".mjs")), str(tmp_path)],
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if result.returncode == 77:
        pytest.skip(result.stdout.strip())  # ty: ignore[too-many-positional-arguments]
    assert result.returncode == 0, result.stdout + result.stderr
