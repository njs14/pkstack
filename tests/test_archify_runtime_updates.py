from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

TESTS = Path(__file__).parent
RUNTIME = TESTS.parent / "powers/pkstack/skills/archify/upstream"


def _node() -> str:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Archify requires optional Node.js 18+")
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


def _cli(arguments: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_node(), str(RUNTIME / "bin/archify.mjs"), *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize("command", ["render", "deliver", "compare"])
def test_archify_preserves_non_html_output_targets(tmp_path: Path, command: str) -> None:
    target = tmp_path / "settings.env"
    target.write_text("KEEP=original\n")
    source = str(RUNTIME / "examples/web-app.architecture.json")
    inputs = [source, source] if command == "compare" else [source]
    flags = [] if command == "render" else ["--json"]
    result = _cli([command, "architecture", *inputs, str(target), *flags], tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    if flags:
        assert json.loads(result.stdout)["diagnostics"][0]["code"] == "output/cli-extension"
    else:
        assert "output/cli-extension" in result.stderr
    assert target.read_text() == "KEEP=original\n"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["settings.env"]


def test_archify_preserves_wrong_type_symlink_and_compare_receipt(tmp_path: Path) -> None:
    target = tmp_path / "settings.env"
    target.write_text("KEEP=original\n")
    alias = tmp_path / "diagram.html"
    alias.symlink_to(target)
    source = str(RUNTIME / "examples/web-app.architecture.json")
    result = _cli(["deliver", "architecture", source, str(alias), "--json"], tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert json.loads(result.stdout)["diagnostics"][0]["code"] == "output/cli-resolved-extension"
    assert target.read_text() == "KEEP=original\n"
    assert alias.is_symlink()
    output = tmp_path / "delta.html"
    result = _cli(
        [
            "compare",
            "architecture",
            source,
            source,
            str(output),
            "--receipt",
            str(target),
            "--json",
        ],
        tmp_path,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert json.loads(result.stdout)["diagnostics"][0]["code"] == "output/cli-extension"
    assert target.read_text() == "KEEP=original\n"
    assert not output.exists()


@pytest.mark.parametrize("command", ["validate", "deliver"])
def test_archify_json_argument_failure_is_complete_and_writes_nothing(
    tmp_path: Path, command: str
) -> None:
    source = str(RUNTIME / "examples/agent-tool-call.workflow.json")
    result = _cli([command, "workflow", source, "--quality", "unknown", "--json"], tmp_path)
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stderr == ""
    receipt = json.loads(result.stdout)
    assert receipt["ok"] is False
    assert receipt["command"] == command
    assert receipt["stage"] == "arguments"
    assert receipt["diagnostics"][0]["code"] == "cli/invalid-option-value"
    assert list(tmp_path.iterdir()) == []


def test_archify_accepts_typed_outputs_and_keeps_layout_validation_read_only(
    tmp_path: Path,
) -> None:
    working = tmp_path / "working"
    working.mkdir()
    source = str(RUNTIME / "examples/agent-tool-call.workflow.json")
    output = tmp_path / "diagram.HTML"
    result = _cli(["deliver", "workflow", source, str(output), "--json"], working)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ok"] is True
    assert output.read_text().lower().startswith("<!doctype html>")
    layout = _cli(["validate", "workflow", source, "--layout-json"], working)
    assert layout.returncode == 0, layout.stdout + layout.stderr
    assert isinstance(json.loads(layout.stdout), dict)
    assert list(working.iterdir()) == []


@pytest.mark.parametrize("quality,exit_code", [("standard", 0), ("showcase", 1)])
def test_archify_flushes_large_artifact_receipts_to_pipes(
    tmp_path: Path, quality: str, exit_code: int
) -> None:
    paths = "\n".join(
        f'<path data-edge-id="edge-{index}" data-edge-from="from-{index}" '
        f'data-edge-to="to-{index}" d="M 20 40 L 220 40" class="a-default" '
        'marker-end="url(#arrowhead)"/>'
        for index in range(24)
    )
    artifact = tmp_path / "crowded.html"
    artifact.write_text(
        f'<svg viewBox="0 0 240 160" data-quality-profile="{quality}">{paths}</svg>'
    )
    command = [_node(), str(RUNTIME / "scripts/check-render-output.mjs"), str(artifact)]
    reference = tmp_path / "receipt.json"
    with reference.open("wb") as output:
        direct = subprocess.run(
            command, stdout=output, stderr=subprocess.PIPE, timeout=30, check=False
        )
    piped = subprocess.run(command, capture_output=True, timeout=30, check=False)
    assert direct.returncode == piped.returncode == exit_code
    expected = reference.read_bytes()
    assert len(expected) > 64 * 1024
    assert piped.stdout == expected
    receipt = json.loads(piped.stdout)
    assert receipt["ok"] is (quality == "standard")
    assert len(receipt["composition"]["issues"]) == 276
