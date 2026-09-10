from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RUNTIME = Path(__file__).resolve().parents[1] / "powers/pkstack/skills/archify/upstream"


def _git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()


@pytest.mark.parametrize("link_mode", ["web", "local-only"])
def test_archify_verifies_pinned_sources_for_gitee_and_internal_forges(
    tmp_path: Path, link_mode: str
) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Archify requires optional Node.js 18+")
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.name", "PKStack Test")
    _git(tmp_path, "config", "user.email", "pkstack@example.test")
    source = tmp_path / "source.txt"
    source.write_text("first\nsecond\n")
    _git(tmp_path, "add", "source.txt")
    _git(
        tmp_path,
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-m",
        "fixture",
    )
    revision = _git(tmp_path, "rev-parse", "HEAD")
    remote = (
        "https://gitee.com/team/service"
        if link_mode == "web"
        else "http://git.internal:3000/Platform/Services/service"
    )
    _git(tmp_path, "remote", "add", "origin", remote)
    diagram = json.loads((RUNTIME / "examples/web-app.architecture.json").read_text())
    diagram["meta"]["repository"] = {
        "url": remote,
        "revision": revision,
        "link_mode": link_mode,
    }
    diagram["components"][0]["sources"] = [{"path": "source.txt", "line": 1, "end_line": 2}]
    spec = tmp_path / "diagram.json"
    spec.write_text(json.dumps(diagram))
    # The verifier must read the pinned Git blob, not this changed working copy.
    source.write_text("working tree differs\n")
    output = tmp_path / "diagram.html"
    command = [
        node,
        str(RUNTIME / "bin/archify.mjs"),
        "deliver",
        "architecture",
        str(spec),
        str(output),
        "--repo-root",
        str(tmp_path),
        "--json",
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    html = output.read_text()
    match = re.search(
        r'<script id="archify-source-evidence-data" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match is not None
    evidence = json.loads(match[1])
    assert evidence["verified"] is True
    assert evidence["repository"]["revision"] == revision
    reference = evidence["nodes"][diagram["components"][0]["id"]][0]
    if link_mode == "web":
        assert reference["href"] == f"{remote}/blob/{revision}/source.txt#L1-2"
    else:
        assert "href" not in reference
        assert "href" not in evidence["repository"]
        assert evidence["repository"]["linkMode"] == "local-only"

    # Local-only must still enforce origin identity and redact credential diagnostics.
    _git(
        tmp_path, "remote", "set-url", "origin", "https://test-user:test-secret@other.invalid/repo"
    )
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode != 0
    diagnostic = result.stdout + result.stderr
    assert "origin-mismatch" in diagnostic
    assert "test-secret" not in diagnostic
    assert "test-user" not in diagnostic


def test_archify_delivered_font_is_embedded_with_license(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Archify requires optional Node.js 18+")
    output = tmp_path / "offline.html"
    subprocess.run(
        [
            node,
            str(RUNTIME / "bin/archify.mjs"),
            "deliver",
            "architecture",
            str(RUNTIME / "examples/web-app.architecture.json"),
            str(output),
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    html = output.read_text()
    match = re.search(r'<style id="archify-fonts">(.*?)</style>', html, re.DOTALL)
    assert match is not None
    css = match[1]
    fonts = re.findall(r"url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)", css)
    assert len(fonts) == 6
    assert all(base64.b64decode(font, validate=True).startswith(b"wOF2") for font in fonts)
    assert (RUNTIME / "assets/JetBrainsMono-OFL.txt").read_text().strip() in css
    assert not re.search(r"src:\s*local\(", css)
    assert not re.search(r'<link\b[^>]*href=["\']https://fonts\.', html)
