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

import pytest

from pstack_kiro.bootstrap import bootstrap_project

POWER_ROOT = Path(__file__).parents[1]


def _copy_power_fixture(destination: Path) -> None:
    for relative in ("src/pstack_kiro", "skills", "dev.kiro", "templates", "docs"):
        shutil.copytree(POWER_ROOT / relative, destination / relative)


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
    assert not (tmp_path / ".kiro" / "skills" / "setup-pk-stack").exists()
    cached_setup = tmp_path / ".pstack" / "projectctl" / "skills" / "setup-pk-stack"
    assert (cached_setup / "SKILL.md").is_file()
    assert (cached_setup / "scripts" / "setup_pk_stack.py").is_file()
    parity = json.loads(
        (POWER_ROOT / "docs" / "upstream-skill-parity.json").read_text(encoding="utf-8")
    )
    curated = json.loads((POWER_ROOT / "docs" / "curated-skills.json").read_text(encoding="utf-8"))
    canonical_skills = (
        {
            Path(entry["target"]).parent.name
            for entry in parity["skills"]
            if entry["target"] is not None
        }
        | set(parity["pk_only_skills"])
        | {entry["name"] for entry in curated["skills"]}
    )
    live_skills = {path.parent.name for path in (tmp_path / ".kiro" / "skills").glob("*/SKILL.md")}
    cached_skills = {
        path.parent.name
        for path in (tmp_path / ".pstack" / "projectctl" / "skills").glob("*/SKILL.md")
    }
    assert live_skills == canonical_skills - {"setup-pk-stack"}
    assert cached_skills == canonical_skills
    assert len(canonical_skills) == (
        parity["summary"]["shipped_skill_directories"]
        + curated["summary"]["shipped_skill_directories"]
    )
    live_steering = {path.name for path in (tmp_path / ".kiro" / "steering").glob("*.md")}
    cached_steering = {
        path.name
        for path in (tmp_path / ".pstack" / "projectctl" / "dev.kiro" / "steering").glob("*.md")
    }
    assert (
        live_steering
        == cached_steering
        == {
            "pk-stack-core.md",
            "pk-stack-safety.md",
            "pk-stack-typescript.md",
            "pk-stack-unslop.md",
        }
    )
    assert (tmp_path / ".kiro" / "agents" / "pk-stack-verifier.json").is_file()
    feature_readme = (tmp_path / "Wiki" / "features" / "README.md").read_text(encoding="utf-8")
    wiki_index = (tmp_path / "Wiki" / "index.md").read_text(encoding="utf-8")
    assert "Schema-2 contracts" in feature_readme
    assert "--sub-feature" in feature_readme
    assert "--entrypoint-proof" in feature_readme
    assert "feature generate-map feature-plan.json" in feature_readme
    assert "feature publish <slug>" in feature_readme
    assert "No feature contract is published yet" in feature_readme
    assert "pk-stack-upstream-maintenance.md" not in feature_readme
    assert "../powers/pk-stack" not in wiki_index
    assert "../reviews/" not in wiki_index
    receipt = json.loads((tmp_path / ".pstack" / "bootstrap.json").read_text())
    assert receipt["manager"] == "pstack-kiro"
    assert ".pstack/projectctl/src/pstack_kiro/goal.py" in receipt["files"]


def test_cached_setup_entrypoints_cannot_authorize_their_own_snapshot(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    assert bootstrap_project(target, power_root=POWER_ROOT).ok is True
    receipt = target / ".pstack" / "bootstrap.json"
    profile = target / ".kiro" / "agents" / "pk-stack.json"
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
        / "setup-pk-stack"
        / "scripts"
        / "setup_pk_stack.py"
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
        alternate_cache
        / "projectctl"
        / "skills"
        / "setup-pk-stack"
        / "scripts"
        / "setup_pk_stack.py"
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
    ignored_paths = (
        ".pstack/state/",
        ".pstack/tmp/",
        ".pstack/projectctl/.venv/",
        ".pk-stack-maintenance/",
    )
    impostors = (
        "".join(f"# {entry}\n" for entry in ignored_paths),
        "backup/.pstack/state/\n.pstack/tmp/cache\n.pstack/projectctl/.venv/backup\n"
        ".pk-stack-maintenance/archive\n",
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


def test_bootstrap_migrates_legacy_gitignore_block_once_and_is_idempotent(
    tmp_path: Path,
) -> None:
    gitignore = tmp_path / ".gitignore"
    legacy = (
        "foreign-entry/\n\n"
        "# PK-Stack runtime state (generated by /setup-pk-stack)\n"
        ".pstack/state/\n"
        ".pstack/tmp/\n"
        ".pstack/projectctl/.venv/\n\n"
        "# PK-Stack runtime state (generated by /setup-pk-stack)\n"
        ".pstack/state/\n"
        ".pstack/tmp/\n"
        ".pstack/projectctl/.venv/\n"
        ".pk-stack-maintenance/\n"
    )
    gitignore.write_text(legacy, encoding="utf-8")

    preview = bootstrap_project(tmp_path, power_root=POWER_ROOT, dry_run=True)

    assert ".gitignore:pstack-runtime-block" in preview.updated
    assert gitignore.read_text(encoding="utf-8") == legacy

    applied = bootstrap_project(tmp_path, power_root=POWER_ROOT)
    normalized = gitignore.read_text(encoding="utf-8")
    assert applied.ok is True
    assert normalized.count("# PK-Stack runtime state (generated by /setup-pk-stack)") == 1
    assert normalized.count(".pstack/state/") == 1
    assert normalized.count(".pk-stack-maintenance/") == 1
    assert normalized.startswith("foreign-entry/\n\n")

    repeated = bootstrap_project(tmp_path, power_root=POWER_ROOT, update_managed=True)
    assert repeated.ok is True
    assert repeated.created == []
    assert repeated.updated == []
    assert repeated.pending_updates == []
    assert repeated.stale_managed == []
    assert gitignore.read_text(encoding="utf-8") == normalized


def test_idempotent_bootstrap_normalizes_managed_file_modes_after_dry_run(
    tmp_path: Path,
) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok is True
    executable = tmp_path / ".pstack" / "bin" / "projectctl"
    text = tmp_path / ".kiro" / "steering" / "pk-stack-core.md"
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
        _copy_power_fixture(power)
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
    agent = tmp_path / ".kiro" / "agents" / "pk-stack.json"
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
        _copy_power_fixture(power)
        powers.append(power)
    power_v1, power_v2 = powers
    v2_profile = power_v2 / "templates" / "project" / ".kiro" / "agents" / "pk-stack.json"
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
        ".kiro/agents/pk-stack.json",
        ".pstack/projectctl/templates/project/.kiro/agents/pk-stack.json",
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

    shim = power_v2 / "skills" / "setup-pk-stack" / "scripts" / "setup_pk_stack.py"
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

    live = target / ".kiro" / "agents" / "pk-stack.json"
    cached = (
        target
        / ".pstack"
        / "projectctl"
        / "templates"
        / "project"
        / ".kiro"
        / "agents"
        / "pk-stack.json"
    )
    assert marker in live.read_text(encoding="utf-8")
    assert live.read_bytes() == cached.read_bytes() == v2_profile.read_bytes()
    receipt = json.loads((target / ".pstack" / "bootstrap.json").read_text(encoding="utf-8"))
    for path in (live, cached):
        key = path.relative_to(target).as_posix()
        assert receipt["files"][key] == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        ("concatenated", "invalid PK-Stack skill parity catalog"),
        ("removed", "unexpected architect"),
        ("added", "missing zzzz-future"),
        ("retargeted", "must target its canonical skill file"),
        ("unknown-disposition", "has an invalid disposition"),
    ),
)
def test_bootstrap_rejects_noncanonical_skill_parity_catalogs(
    tmp_path: Path,
    case: str,
    expected: str,
) -> None:
    power = tmp_path / f"power-{case}"
    _copy_power_fixture(power)
    parity_path = power / "docs" / "upstream-skill-parity.json"
    if case == "concatenated":
        parity_path.write_bytes(parity_path.read_bytes() + b"{}\n")
    else:
        parity = json.loads(parity_path.read_text(encoding="utf-8"))
        if case == "removed":
            removed = parity["skills"].pop(0)
            assert removed["name"] == "architect"
        elif case == "added":
            future = dict(parity["skills"][-1])
            future.update(
                name="zzzz-future",
                disposition="direct-port",
                target="skills/zzzz-future/SKILL.md",
            )
            parity["skills"].append(future)
        elif case == "retargeted":
            parity["skills"][0]["target"] = "skills/wrong/SKILL.md"
        else:
            parity["skills"][0]["disposition"] = "invented"
        parity_path.write_text(json.dumps(parity, indent=2) + "\n", encoding="utf-8")

    target = tmp_path / f"target-{case}"
    target.mkdir()
    with pytest.raises(ValueError, match=re.escape(expected)):
        bootstrap_project(target, power_root=power)
