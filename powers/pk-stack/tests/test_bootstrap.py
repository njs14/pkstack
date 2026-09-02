from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from pstack_kiro.bootstrap import bootstrap_project

POWER_ROOT = Path(__file__).parents[1]


def _concurrent_bootstrap_worker(
    root: str,
    power_root: str,
    start: Any,
    results: Any,
) -> None:
    start.wait(timeout=10)
    try:
        result = bootstrap_project(Path(root), power_root=Path(power_root))
    except BaseException as exc:
        results.put({"exception": f"{type(exc).__name__}: {exc}"})
    else:
        results.put(result.to_dict())


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_bootstrap_is_idempotent_and_records_owned_files(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    first = bootstrap_project(tmp_path, power_root=POWER_ROOT)
    first_hashes = _tree_hashes(tmp_path)
    second = bootstrap_project(tmp_path, power_root=POWER_ROOT)
    second_hashes = _tree_hashes(tmp_path)

    assert first.ok is True
    assert second.ok is True
    assert second.created == []
    assert second.updated == []
    assert first_hashes == second_hashes
    assert (tmp_path / "projectctl").stat().st_mode & 0o111
    wrapper = (tmp_path / ".pstack" / "bin" / "projectctl").read_text(encoding="utf-8")
    assert 'uv sync --quiet --locked --no-config --project "$PROJECTCTL_ROOT"' in wrapper
    assert 'exec "$PROJECTCTL_ROOT/.venv/bin/python" -B -X pycache_prefix=/dev/null' in wrapper
    assert '-m pstack_kiro "$@"' in wrapper
    assert (tmp_path / ".kiro" / "skills" / "verified-goal" / "SKILL.md").is_file()
    assert not (tmp_path / ".kiro" / "skills" / "setup-pstack").exists()
    cached_setup = tmp_path / ".pstack" / "projectctl" / "skills" / "setup-pstack"
    assert (cached_setup / "SKILL.md").is_file()
    assert (cached_setup / "scripts" / "setup_pstack.py").is_file()
    assert (tmp_path / ".kiro" / "steering" / "pstack-core.md").is_file()
    assert (tmp_path / ".kiro" / "agents" / "pstack-verifier.json").is_file()
    receipt = json.loads((tmp_path / ".pstack" / "bootstrap.json").read_text())
    assert receipt["manager"] == "pstack-kiro"
    assert ".pstack/projectctl/src/pstack_kiro/goal.py" in receipt["files"]


def test_cached_setup_entrypoints_cannot_authorize_their_own_snapshot(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    assert bootstrap_project(target, power_root=POWER_ROOT).ok is True
    receipt = target / ".pstack" / "bootstrap.json"
    profile = target / ".kiro" / "agents" / "pstack.json"
    before = (receipt.read_bytes(), profile.read_bytes())
    clean_env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COV_CORE_", "COVERAGE_"))
    }

    cached_shim = (
        target
        / ".pstack"
        / "projectctl"
        / "skills"
        / "setup-pstack"
        / "scripts"
        / "setup_pstack.py"
    )
    shim_result = subprocess.run(
        [
            sys.executable,
            str(cached_shim),
            "--root",
            ".",
            "--dry-run",
            "--output",
            "json",
        ],
        cwd=target,
        env=clean_env,
        capture_output=True,
        text=True,
        check=False,
    )

    module_env = dict(clean_env)
    module_env["PYTHONPATH"] = str(target / ".pstack" / "projectctl" / "src")
    module_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pstack_kiro.bootstrap",
            "--root",
            ".",
            "--dry-run",
            "--output",
            "json",
        ],
        cwd=target,
        env=module_env,
        capture_output=True,
        text=True,
        check=False,
    )

    for completed in (shim_result, module_result):
        assert completed.returncode == 2
        assert completed.stderr == ""
        payload = json.loads(completed.stdout)
        assert payload["error_type"] == "ValueError"
        assert "project-local .pstack cache" in payload["error"]
    assert (receipt.read_bytes(), profile.read_bytes()) == before


def test_cached_setup_rejects_case_alias_on_case_folding_filesystem(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    assert bootstrap_project(target, power_root=POWER_ROOT).ok is True
    alternate_cache = target / ".PSTACK"
    canonical_cache = target / ".pstack"
    if not alternate_cache.exists() or not alternate_cache.samefile(canonical_cache):
        return

    clean_env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COV_CORE_", "COVERAGE_"))
    }
    cached_shim = (
        alternate_cache / "projectctl" / "skills" / "setup-pstack" / "scripts" / "setup_pstack.py"
    )
    shim_result = subprocess.run(
        [
            sys.executable,
            str(cached_shim),
            "--root",
            ".",
            "--dry-run",
            "--output",
            "json",
        ],
        cwd=target,
        env=clean_env,
        capture_output=True,
        text=True,
        check=False,
    )
    module_env = dict(clean_env)
    module_env["PYTHONPATH"] = str(alternate_cache / "projectctl" / "src")
    module_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pstack_kiro.bootstrap",
            "--root",
            ".",
            "--dry-run",
            "--output",
            "json",
        ],
        cwd=target,
        env=module_env,
        capture_output=True,
        text=True,
        check=False,
    )

    for completed in (shim_result, module_result):
        assert completed.returncode == 2
        assert completed.stderr == ""
        payload = json.loads(completed.stdout)
        assert payload["error_type"] == "ValueError"
        assert "project-local .pstack cache" in payload["error"]


def test_shipped_workflows_select_only_the_managed_internal_controller() -> None:
    root_selector = re.compile(r"^(?:\./)?projectctl(?:\s|$)")
    bare_command = re.compile(
        r"(?<![./\w-])projectctl\s+(?:doctor|feature|goal|knowledge|verify)(?:\s|$)"
    )

    for path in sorted((POWER_ROOT / "templates" / "project" / ".kiro" / "agents").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        shell_matches = [
            pattern
            for rule in payload["permissions"]["rules"]
            if rule["capability"] == "shell"
            for pattern in rule["match"]
        ]
        assert not any(root_selector.match(pattern) for pattern in shell_matches), path

    for path in sorted((POWER_ROOT / "templates" / "project" / ".kiro" / "hooks").glob("*.json")):
        text = path.read_text(encoding="utf-8")
        assert bare_command.search(text) is None, path

    for path in sorted((POWER_ROOT / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        fenced_blocks = text.split("```")[1::2]
        assert not any(bare_command.search(block) for block in fenced_blocks), path


def test_bootstrap_preserves_foreign_projectctl(tmp_path: Path) -> None:
    (tmp_path / "projectctl").write_text("foreign\n", encoding="utf-8")

    result = bootstrap_project(tmp_path, power_root=POWER_ROOT)

    assert result.ok is True
    assert (tmp_path / "projectctl").read_text(encoding="utf-8") == "foreign\n"
    assert (tmp_path / ".pstack" / "bin" / "projectctl").is_file()
    assert any("existing root projectctl" in note for note in result.notes)


def test_gitignore_comments_and_substrings_do_not_impersonate_runtime_patterns(
    tmp_path: Path,
) -> None:
    ignored_paths = (".pstack/state/", ".pstack/tmp/", ".pstack/projectctl/.venv/")
    impostors = (
        "".join(f"# {entry}\n" for entry in ignored_paths),
        "backup/.pstack/state/\n.pstack/tmp/cache\n.pstack/projectctl/.venv/backup\n",
    )
    for index, existing in enumerate(impostors):
        project = tmp_path / f"project-{index}"
        project.mkdir()
        gitignore = project / ".gitignore"
        gitignore.write_text(existing, encoding="utf-8")

        result = bootstrap_project(project, power_root=POWER_ROOT)
        text = gitignore.read_text(encoding="utf-8")

        assert result.ok is True
        for entry in ignored_paths:
            assert entry in text.splitlines()


def test_idempotent_bootstrap_normalizes_managed_file_modes_after_dry_run(
    tmp_path: Path,
) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok is True
    executable = tmp_path / ".pstack" / "bin" / "projectctl"
    text = tmp_path / ".kiro" / "steering" / "pstack-core.md"
    receipt = tmp_path / ".pstack" / "bootstrap.json"
    for path in (executable, text, receipt):
        path.chmod(0o777)

    preview = bootstrap_project(tmp_path, power_root=POWER_ROOT, dry_run=True)

    assert preview.ok is True
    assert all(path.stat().st_mode & 0o777 == 0o777 for path in (executable, text, receipt))

    applied = bootstrap_project(tmp_path, power_root=POWER_ROOT)

    assert applied.ok is True
    assert executable.stat().st_mode & 0o777 == 0o755
    assert text.stat().st_mode & 0o777 == 0o644
    assert receipt.stat().st_mode & 0o777 == 0o644


def test_dry_run_uses_directory_lock_without_creating_artifacts(tmp_path: Path) -> None:
    result = bootstrap_project(tmp_path, power_root=POWER_ROOT, dry_run=True)

    assert result.ok is True
    assert list(tmp_path.iterdir()) == []


def test_concurrent_fresh_bootstraps_serialize_and_commit_one_consistent_receipt(
    tmp_path: Path,
) -> None:
    powers: list[Path] = []
    expected_sources: set[bytes] = set()
    for label in ("alpha", "beta"):
        power = tmp_path / f"power-{label}"
        for relative in ("src/pstack_kiro", "skills", "dev.kiro", "templates"):
            source = POWER_ROOT / relative
            shutil.copytree(source, power / relative)
        managed_source = power / "src" / "pstack_kiro" / "__init__.py"
        managed_source.write_bytes(managed_source.read_bytes() + f"\n# {label}\n".encode())
        expected_sources.add(managed_source.read_bytes())
        powers.append(power)

    target = tmp_path / "target"
    target.mkdir()
    context = get_context("spawn")
    start = context.Event()
    results = context.Queue()
    processes = [
        context.Process(
            target=_concurrent_bootstrap_worker,
            args=(str(target), str(power), start, results),
        )
        for power in powers
    ]
    for process in processes:
        process.start()
    start.set()
    for process in processes:
        process.join(timeout=30)
        assert process.exitcode == 0

    outcomes = [results.get(timeout=5) for _ in processes]
    assert not any("exception" in outcome for outcome in outcomes)
    assert sum(outcome["ok"] is True for outcome in outcomes) == 1
    assert sum(bool(outcome["pending_updates"]) for outcome in outcomes) == 1

    receipt = json.loads((target / ".pstack" / "bootstrap.json").read_text(encoding="utf-8"))
    for relative, expected_hash in receipt["files"].items():
        managed = target / relative
        assert managed.is_file()
        assert hashlib.sha256(managed.read_bytes()).hexdigest() == expected_hash
    installed_source = target / ".pstack" / "projectctl" / "src" / "pstack_kiro" / "__init__.py"
    assert installed_source.read_bytes() in expected_sources


def test_bootstrap_refuses_to_overwrite_modified_managed_file(tmp_path: Path) -> None:
    bootstrap_project(tmp_path, power_root=POWER_ROOT)
    agent = tmp_path / ".kiro" / "agents" / "pstack.json"
    if not agent.exists():
        # The Kiro assets are added independently; use a guaranteed managed file meanwhile.
        agent = tmp_path / ".pstack" / "projectctl" / "README.md"
    agent.write_text("user customization\n", encoding="utf-8")

    result = bootstrap_project(tmp_path, power_root=POWER_ROOT)

    assert str(agent.relative_to(tmp_path)) in result.conflicts
    assert agent.read_text(encoding="utf-8") == "user customization\n"


def test_power_local_upgrade_detects_and_applies_newer_managed_assets(
    tmp_path: Path,
) -> None:
    powers: list[Path] = []
    for version in ("v1", "v2"):
        power = tmp_path / f"power-{version}"
        for relative in ("src/pstack_kiro", "skills", "dev.kiro", "templates"):
            shutil.copytree(POWER_ROOT / relative, power / relative)
        powers.append(power)
    power_v1, power_v2 = powers
    v2_profile = power_v2 / "templates" / "project" / ".kiro" / "agents" / "pstack.json"
    v2_payload = json.loads(v2_profile.read_text(encoding="utf-8"))
    marker = " managed-v2-marker"
    v2_payload["description"] += marker
    v2_profile.write_text(json.dumps(v2_payload, indent=2) + "\n", encoding="utf-8")

    target = tmp_path / "target"
    target.mkdir()
    assert bootstrap_project(target, power_root=power_v1).ok is True
    clean_env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COV_CORE_", "COVERAGE_"))
    }
    expected_pending = {
        ".kiro/agents/pstack.json",
        ".pstack/projectctl/templates/project/.kiro/agents/pstack.json",
    }

    controller_preview = subprocess.run(
        [
            str(target / ".pstack" / "bin" / "projectctl"),
            "setup",
            "--power-root",
            str(power_v2),
            "--dry-run",
            "--output",
            "json",
        ],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
        env=clean_env,
    )
    assert controller_preview.returncode == 2
    assert controller_preview.stderr == ""
    assert set(json.loads(controller_preview.stdout)["pending_updates"]) == expected_pending

    shim = power_v2 / "skills" / "setup-pstack" / "scripts" / "setup_pstack.py"
    shim_preview = subprocess.run(
        [
            sys.executable,
            str(shim),
            "--root",
            str(target),
            "--dry-run",
            "--output",
            "json",
        ],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
        env=clean_env,
    )
    assert shim_preview.returncode == 2
    assert shim_preview.stderr == ""
    assert set(json.loads(shim_preview.stdout)["pending_updates"]) == expected_pending

    applied = subprocess.run(
        [
            sys.executable,
            str(shim),
            "--root",
            str(target),
            "--update-managed",
            "--output",
            "json",
        ],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
        env=clean_env,
    )
    assert applied.returncode == 0, applied.stderr or applied.stdout
    assert applied.stderr == ""
    applied_payload = json.loads(applied.stdout)
    assert set(applied_payload["updated"]) >= expected_pending

    live = target / ".kiro" / "agents" / "pstack.json"
    cached = (
        target
        / ".pstack"
        / "projectctl"
        / "templates"
        / "project"
        / ".kiro"
        / "agents"
        / "pstack.json"
    )
    assert marker in live.read_text(encoding="utf-8")
    assert live.read_bytes() == cached.read_bytes() == v2_profile.read_bytes()
    receipt = json.loads((target / ".pstack" / "bootstrap.json").read_text(encoding="utf-8"))
    for path in (live, cached):
        key = path.relative_to(target).as_posix()
        assert receipt["files"][key] == hashlib.sha256(path.read_bytes()).hexdigest()
