from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

TESTS = Path(__file__).parent
RUNTIME = TESTS.parent / "skills/archify/upstream"


def _node() -> str:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Archify requires optional Node.js 18+")  # ty: ignore[too-many-positional-arguments]
    return node


@pytest.mark.parametrize(
    "arguments,diagnostic",
    [
        (["--json", "out.html"], "Unknown render option"),
        (["out.html", "extra.html"], "Usage:"),
    ],
)
def test_archify_render_rejects_arguments_before_writing(
    tmp_path: Path, arguments: list[str], diagnostic: str
) -> None:
    source = tmp_path / "spec.json"
    shutil.copyfile(RUNTIME / "examples/web-app.architecture.json", source)
    result = subprocess.run(
        [
            _node(),
            str(RUNTIME / "bin/archify.mjs"),
            "render",
            "architecture",
            str(source),
            *arguments,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert diagnostic in result.stderr
    assert sorted(path.name for path in tmp_path.iterdir()) == ["spec.json"]


@pytest.mark.parametrize("length,expected_code", [(135, 0), (136, 1)])
def test_archify_segment_label_respects_frame_width(
    tmp_path: Path, length: int, expected_code: int
) -> None:
    spec = json.loads((TESTS / "fixtures/archify-native-account-request.sequence.json").read_text())
    spec["segments"][0]["label"] = "A" * length
    source = tmp_path / "width.json"
    source.write_text(json.dumps(spec))
    result = subprocess.run(
        [
            _node(),
            str(RUNTIME / "bin/archify.mjs"),
            "validate",
            "sequence",
            str(source),
            "--quality",
            "showcase",
            "--json",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == expected_code, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["ok"] == (expected_code == 0)
    if expected_code:
        assert "exceeds the segment frame's available width (716px)" in receipt["error"]
        assert "increase meta.viewBox[0] to at least 826" in receipt["error"]


def test_archify_preview_recovers_after_async_watcher_error(tmp_path: Path) -> None:
    result = subprocess.run(
        [_node(), str(TESTS / "test_archify_preview_recovery.mjs"), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["initialRevision"] == 1
    assert receipt["recoveredRevision"] == 2
    assert receipt["watcherCloseCount"] == 1
    assert receipt["initialArtifact"] != receipt["recoveredArtifact"]
