from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
from contextlib import suppress
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
    profile = os.environ.get("PKSTACK_BROWSER_PROFILE", "full")
    assert profile in {"smoke", "full"}, f"Unknown PKSTACK_BROWSER_PROFILE: {profile}"
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
    receipt = json.loads(result.stdout)
    assert receipt["profile"] == profile
    if profile == "smoke":
        assert receipt["viewports"] == 3
        assert receipt["exports"] == ["svg", "png"]
    else:
        assert receipt["exports"] == ["svg", "png", "jpeg", "webp", "share-card", "webm"]


def test_archify_reader_closes_browser_after_startup_rejection(tmp_path: Path) -> None:
    """A failed CDP attachment must still terminate the child and remove its profile."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("Archify requires optional Node.js 18+")  # ty: ignore[too-many-positional-arguments]
    record_path = tmp_path / "browser.json"
    terminated_path = tmp_path / "terminated"
    chrome = tmp_path / "chrome"
    chrome.write_text(
        "#!/usr/bin/env node\n"
        "const fs = require('node:fs');\n"
        "const record = process.env.ARCHIFY_STARTUP_TEST_RECORD;\n"
        "const profile = process.argv.find(arg => arg.startsWith('--user-data-dir='))\n"
        "  .slice('--user-data-dir='.length);\n"
        "fs.writeFileSync(record, JSON.stringify({ pid: process.pid, profile }));\n"
        "process.on('SIGTERM', () => {\n"
        "  fs.writeFileSync(process.env.ARCHIFY_STARTUP_TEST_TERMINATED, 'SIGTERM');\n"
        "  process.exit(0);\n"
        "});\n"
        "fs.writeSync(4, 'invalid CDP JSON\\0');\n"
        "setInterval(() => {}, 1000);\n"
    )
    chrome.chmod(0o755)
    try:
        result = subprocess.run(
            [node, str(Path(__file__).with_suffix(".mjs")), str(tmp_path / "output")],
            env={
                **os.environ,
                "ARCHIFY_CHROME": str(chrome),
                "ARCHIFY_STARTUP_TEST_RECORD": str(record_path),
                "ARCHIFY_STARTUP_TEST_TERMINATED": str(terminated_path),
            },
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        assert result.returncode != 0, result.stdout + result.stderr
        assert "Chrome DevTools returned invalid JSON" in result.stderr
        record = json.loads(record_path.read_text())
        assert terminated_path.exists(), "Startup rejection left the browser child running"
        with pytest.raises(ProcessLookupError):
            os.kill(record["pid"], 0)
        assert not Path(record["profile"]).exists(), "Startup rejection leaked its browser profile"
    finally:
        # Keep the injected child and profile contained even when this regression fails.
        if record_path.exists():
            record = json.loads(record_path.read_text())
            with suppress(ProcessLookupError):
                os.kill(record["pid"], signal.SIGTERM)
            shutil.rmtree(record["profile"], ignore_errors=True)
