from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from pkstack.bootstrap import bootstrap_project

POWER = Path(__file__).resolve().parents[1] / "powers" / "pkstack"
GUIDE = Path(".kiro/skills/pkstack-guide")


def _files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


def test_guide_installs_exact_resources_once_and_preview_is_read_only(tmp_path: Path) -> None:
    before = _files(tmp_path)
    preview = bootstrap_project(tmp_path, power_root=POWER, dry_run=True)
    assert preview.ok
    assert _files(tmp_path) == before

    first = bootstrap_project(tmp_path, power_root=POWER)
    assert first.ok
    receipt = json.loads((tmp_path / ".pkstack/bootstrap.json").read_text())
    for relative in ("SKILL.md", "references/project-lifecycle.md"):
        installed = tmp_path / GUIDE / relative
        expected = (POWER / "skills/pkstack-guide" / relative).read_bytes()
        assert installed.read_bytes() == expected
        assert receipt["files"][str(GUIDE / relative)] == hashlib.sha256(expected).hexdigest()

    installed_files = _files(tmp_path)
    second = bootstrap_project(tmp_path, power_root=POWER)
    assert second.ok and not second.created and not second.updated
    assert _files(tmp_path) == installed_files
    assert not (tmp_path / ".pkstack/state").exists()
    assert not (tmp_path / ".kiro/specs").exists()
    assert not (tmp_path / ".kiro/skills/pkstack-setup").exists()


@pytest.mark.parametrize("managed", [False, True])
@pytest.mark.parametrize("relative", ["SKILL.md", "references/project-lifecycle.md"])
def test_guide_conflicts_preserve_user_owned_bytes(
    tmp_path: Path, managed: bool, relative: str
) -> None:
    if managed:
        assert bootstrap_project(tmp_path, power_root=POWER).ok
    target = tmp_path / GUIDE / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("User-owned project guidance.\n")
    before = _files(tmp_path)

    for preview in (True, False):
        result = bootstrap_project(tmp_path, power_root=POWER, dry_run=preview, update_managed=True)
        assert not result.ok
        assert str(GUIDE / relative) in result.conflicts
        assert _files(tmp_path) == before
