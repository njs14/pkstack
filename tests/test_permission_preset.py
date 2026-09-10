"""Behavioral examples for the optional YAML; commands are data, never executed."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from pkstack.bootstrap import bootstrap_project

POWER = Path(__file__).resolve().parents[1] / "powers" / "pkstack"
PRESET = POWER / "examples" / "permissions.yaml"


def matches(command: str, pattern: str) -> bool:
    # Kiro's shell patterns use only *, not Python fnmatch's [] and ? syntax.
    if pattern.endswith(" *") and "*" not in pattern[:-2] and command == pattern[:-2]:
        return True
    return re.fullmatch(re.escape(pattern).replace(r"\*", ".*"), command, re.DOTALL) is not None


def effect(command: str) -> str:
    rules = yaml.safe_load(PRESET.read_text())["rules"]
    effects = {
        rule["effect"]
        for rule in rules
        if rule["capability"] in {"shell", "builtin"}
        and any(matches(command, pattern) for pattern in rule.get("match", ["*"]))
        and not any(matches(command, pattern) for pattern in rule.get("exclude", []))
    }
    return next((value for value in ("deny", "ask", "allow") if value in effects), "ask")


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf build",
        "rm -rf /tmp/pkstack-build",
        "rm -rf ~/project/build",
        'rm -rf "$HOME/project/build"',
        "sudo /bin/rm -rf /tmp/pkstack-build",
        "git checkout feature",
        "git restore src/app.py",
        "git reset --hard HEAD",
        "git push --force-with-lease origin topic",
        "git clean -fd build",
        "npm publish",
        "terraform apply",
        "tofu destroy",
        "gh pr merge 123",
        "aws s3 rm s3://example/build",
        "sudo install ./tool /usr/local/bin/tool",
        "uv sync --frozen",
        "npm install",
        "cat .env",
        "cat /etc/hosts",
        ".pkstack/bin/projectctl doctor --output json",
        "dd if=/dev/zero of=/dev/null count=1",
        "dd if=image of=copy.img",
        "dd if=image of=/dev/stdout",
        "diskutil list",
        "mkfs-helper --version",
    ],
)
def test_routine_commands_remain_allowed(command: str) -> None:
    assert effect(command) == "allow"


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf /",
        "rm -fr /",
        "rm --recursive --force /",
        "rm / -rf",
        "rm -r / -f",
        '/bin/rm -rf "/"',
        "sudo /bin/rm -rf /",
        "rm -rf ~",
        "rm -rf ~/",
        'rm -rf "$HOME"',
        'rm -rf "${HOME}"',
        "mkfs /dev/sda",
        "mkfs.ext4 /dev/sda",
        "/sbin/mkfs.ext4 /dev/sda",
        "sudo /sbin/mkfs.ext4 /dev/sda",
        "diskutil eraseDisk APFS Empty /dev/disk9",
        "diskutil secureErase 0 /dev/disk9",
        "sudo diskutil partitionDisk /dev/disk9 1 GPT APFS Empty 100%",
        "dd if=image of=/dev/disk9",
        "sudo /bin/dd if=/dev/zero of=/dev/rdisk9",
        "dd if=image of=/dev/null of=/dev/disk9",
    ],
)
def test_direct_catastrophic_commands_are_denied(command: str) -> None:
    assert effect(command) == "deny"


def test_preset_only_adds_builtin_allow_and_targeted_shell_denies() -> None:
    document = yaml.safe_load(PRESET.read_text())
    assert set(document) == {"rules"}
    assert document["rules"][0] == {"capability": "builtin", "effect": "allow"}
    for rule in document["rules"][1:]:
        assert rule["capability"] == "shell"
        assert rule["effect"] == "deny"
        assert rule["match"] and "*" not in rule["match"]


def test_setup_never_installs_or_edits_user_policy(tmp_path: Path, monkeypatch) -> None:
    user = tmp_path / "user"
    settings = user / ".kiro" / "settings"
    settings.mkdir(parents=True)
    policy = settings / "permissions.yaml"
    existing = b"rules:\n  - capability: mcp\n    effect: ask\n"
    policy.write_bytes(existing)
    monkeypatch.setattr(Path, "home", lambda: user)
    project = tmp_path / "project"
    project.mkdir()
    for dry_run in (True, False, True):
        bootstrap_project(project, power_root=POWER, dry_run=dry_run)
        assert policy.read_bytes() == existing
        assert not list(project.rglob("permissions.yaml"))
