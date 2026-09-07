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

from pkstack.bootstrap import REQUIRED_SOURCE_MODULES, bootstrap_project

POWER_ROOT = Path(__file__).parents[1]


def _copy_power_fixture(destination: Path) -> None:
    for relative in ("src/pkstack", "skills", "dev.kiro", "templates", "docs"):
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


@pytest.mark.parametrize("legacy_name", [".pk-stack", ".pstack"])
@pytest.mark.parametrize("kind", ["directory", "file", "dangling-symlink"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_legacy_installation_is_rejected_before_lock_or_workspace_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    legacy_name: str,
    kind: str,
    dry_run: bool,
) -> None:
    legacy = tmp_path / legacy_name
    if kind == "directory":
        legacy.mkdir()
        (legacy / "bootstrap.json").write_text("untrusted legacy receipt\n", encoding="utf-8")
    elif kind == "file":
        legacy.write_text("preserve this file\n", encoding="utf-8")
    else:
        legacy.symlink_to("absent-legacy-target")
    (tmp_path / "user-file.txt").write_text("preserve user work\n", encoding="utf-8")
    before_hashes = _tree_hashes(tmp_path)
    before_paths = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))

    def unexpected_lock(_root: Path) -> None:
        raise AssertionError("legacy detection must run before acquiring the setup lock")

    monkeypatch.setattr("pkstack.bootstrap._bootstrap_lock", unexpected_lock)
    with pytest.raises(ValueError, match="legacy installation paths detected") as exc:
        bootstrap_project(tmp_path, power_root=POWER_ROOT, dry_run=dry_run, update_managed=True)

    assert legacy_name in str(exc.value)
    assert "does not migrate or delete" in str(exc.value)
    assert "No workspace files were changed" in str(exc.value)
    assert _tree_hashes(tmp_path) == before_hashes
    assert sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*")) == before_paths
    assert not (tmp_path / ".pkstack").exists()
    if kind == "dangling-symlink":
        assert legacy.is_symlink() and legacy.readlink() == Path("absent-legacy-target")


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
    assert not (tmp_path / "projectctl").exists()
    wrapper = (tmp_path / ".pkstack" / "bin" / "projectctl").read_text(encoding="utf-8")
    assert 'uv sync --quiet --locked --no-config --project "$PROJECTCTL_ROOT"' in wrapper
    assert 'exec "$PROJECTCTL_ROOT/.venv/bin/python" -B -X pycache_prefix=/dev/null' in wrapper
    assert '-m pkstack "$@"' in wrapper
    assert (tmp_path / ".kiro" / "skills" / "pkstack-verified-goal" / "SKILL.md").is_file()
    assert not (tmp_path / ".kiro" / "skills" / "pkstack-setup").exists()
    assert not list(tmp_path.rglob("skill-routing.json")), "review cases are not runtime assets"
    assert not list(tmp_path.rglob("decision-log.jsonl")), "setup does not start an evidence trail"
    assert not (tmp_path / ".pkstack" / "state" / "goal.json").exists()
    for directory in ("skills", "dev.kiro", "templates"):
        assert not (tmp_path / ".pkstack" / "projectctl" / directory).exists()
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
    assert live_skills == canonical_skills - {"pkstack-setup"}
    assert len(canonical_skills) == (
        parity["summary"]["shipped_skill_directories"]
        + curated["summary"]["shipped_skill_directories"]
    )
    live_steering = {path.name for path in (tmp_path / ".kiro" / "steering").glob("*.md")}
    assert live_steering == {
        "pkstack-core.md",
        "pkstack-python.md",
        "pkstack-safety.md",
        "pkstack-typescript.md",
        "pkstack-unslop.md",
    }
    assert (tmp_path / ".kiro" / "agents" / "pkstack-verifier.json").is_file()
    feature_readme = (tmp_path / "Wiki" / "features" / "README.md").read_text(encoding="utf-8")
    wiki_index = (tmp_path / "Wiki" / "index.md").read_text(encoding="utf-8")
    assert "Schema-2 contracts" in feature_readme
    assert "--sub-feature" in feature_readme
    assert "--entrypoint-proof" in feature_readme
    assert "feature generate-map feature-plan.json" in feature_readme
    assert "feature publish <slug>" in feature_readme
    assert "No feature contract is published yet" in feature_readme
    assert "pkstack-upstream-maintenance.md" not in feature_readme
    assert "../powers/pkstack" not in wiki_index
    assert "../reviews/" not in wiki_index
    receipt = json.loads((tmp_path / ".pkstack" / "bootstrap.json").read_text())
    assert receipt["manager"] == "pkstack"
    assert ".pkstack/projectctl/src/pkstack/goal.py" in receipt["files"]


def test_project_indexes_remain_editable_after_setup(tmp_path: Path) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok
    indexes = (Path("Wiki/index.md"), Path("Wiki/knowledge/index.md"))
    for relative in indexes:
        (tmp_path / relative).write_text("---\ntype: Guide\n---\n\nUser navigation.\n")
    result = bootstrap_project(tmp_path, power_root=POWER_ROOT, update_managed=True)
    assert result.ok
    assert set(result.preserved) == {str(path) for path in indexes}
    receipt = json.loads((tmp_path / ".pkstack/bootstrap.json").read_text())
    for relative in indexes:
        assert str(relative) not in receipt["files"]
        assert "User navigation." in (tmp_path / relative).read_text()


@pytest.mark.parametrize("update_managed", [False, True])
@pytest.mark.parametrize("dry_run", [False, True])
def test_old_receipt_is_rejected_without_mutation(
    tmp_path: Path, update_managed: bool, dry_run: bool
) -> None:
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok
    index = tmp_path / "Wiki/index.md"
    receipt_path = tmp_path / ".pkstack/bootstrap.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["schema_version"] = 1
    receipt["files"]["Wiki/index.md"] = hashlib.sha256(index.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    index.write_text("Important user links.\n")
    before = _tree_hashes(tmp_path)
    with pytest.raises(ValueError, match="clean consumer copy"):
        bootstrap_project(
            tmp_path, power_root=POWER_ROOT, dry_run=dry_run, update_managed=update_managed
        )
    assert _tree_hashes(tmp_path) == before


@pytest.mark.parametrize("module", REQUIRED_SOURCE_MODULES)
def test_every_runtime_module_is_required_before_target_writes(tmp_path: Path, module: str) -> None:
    power = tmp_path / "power"
    _copy_power_fixture(power)
    (power / "src/pkstack" / module).unlink()
    target = tmp_path / "target"
    target.mkdir()
    before = _tree_hashes(target)
    with pytest.raises(ValueError, match="missing"):
        bootstrap_project(target, power_root=power)
    assert _tree_hashes(target) == before
    assert not (target / ".pkstack").exists()


@pytest.mark.parametrize("relative", ["Wiki/domain/glossary.md", "Wiki/NOTES.MD"])
def test_existing_flat_knowledge_does_not_get_hidden_by_new_root(
    tmp_path: Path, relative: str
) -> None:
    legacy = tmp_path / relative
    legacy.parent.mkdir(parents=True)
    legacy.write_text("---\ntype: Glossary\n---\n\nExisting project terms.\n")
    original = legacy.read_bytes()
    result = bootstrap_project(tmp_path, power_root=POWER_ROOT)
    assert result.ok
    assert not (tmp_path / "Wiki/knowledge").exists()
    assert legacy.read_bytes() == original
    assert "knowledge/index.md" not in (tmp_path / "Wiki/index.md").read_text()
    assert any("flat Wiki" in note for note in result.notes)


def test_working_directory_is_ignored_without_ignoring_durable_knowledge(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    assert bootstrap_project(tmp_path, power_root=POWER_ROOT).ok
    result = subprocess.run(
        ["git", "check-ignore", "Wiki/work/interview/context.md", "Wiki/knowledge/topic.md"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.splitlines() == ["Wiki/work/interview/context.md"]


def test_cached_setup_entrypoints_cannot_authorize_their_own_snapshot(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    assert bootstrap_project(target, power_root=POWER_ROOT).ok is True
    receipt = target / ".pkstack" / "bootstrap.json"
    profile = target / ".kiro" / "agents" / "pkstack.json"
    before = (receipt.read_bytes(), profile.read_bytes())
    clean_env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COV_CORE_", "COVERAGE_"))
    }

    module_env = dict(clean_env)
    module_env["PYTHONPATH"] = str(target / ".pkstack" / "projectctl" / "src")
    module_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pkstack.bootstrap",
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

    assert module_result.returncode == 2
    assert module_result.stderr == ""
    payload = json.loads(module_result.stdout)
    assert payload["error_type"] == "ValueError"
    assert "project-local .pkstack cache" in payload["error"]
    assert (receipt.read_bytes(), profile.read_bytes()) == before


def test_cached_setup_rejects_case_alias_on_case_folding_filesystem(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    assert bootstrap_project(target, power_root=POWER_ROOT).ok is True
    alternate_cache = target / ".PKSTACK"
    canonical_cache = target / ".pkstack"
    if not alternate_cache.exists() or not alternate_cache.samefile(canonical_cache):
        return

    clean_env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COV_CORE_", "COVERAGE_"))
    }
    module_env = dict(clean_env)
    module_env["PYTHONPATH"] = str(alternate_cache / "projectctl" / "src")
    module_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pkstack.bootstrap",
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

    assert module_result.returncode == 2
    assert module_result.stderr == ""
    payload = json.loads(module_result.stdout)
    assert payload["error_type"] == "ValueError"
    assert "project-local .pkstack cache" in payload["error"]


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
    assert (tmp_path / ".pkstack" / "bin" / "projectctl").is_file()


def test_gitignore_comments_and_substrings_do_not_impersonate_runtime_patterns(
    tmp_path: Path,
) -> None:
    ignored_paths = (
        ".pkstack/state/",
        ".pkstack/tmp/",
        ".pkstack/projectctl/.venv/",
        ".pkstack-maintenance/",
    )
    impostors = (
        "".join(f"# {entry}\n" for entry in ignored_paths),
        "backup/.pkstack/state/\n.pkstack/tmp/cache\n.pkstack/projectctl/.venv/backup\n"
        ".pkstack-maintenance/archive\n",
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
    executable = tmp_path / ".pkstack" / "bin" / "projectctl"
    text = tmp_path / ".kiro" / "steering" / "pkstack-core.md"
    receipt = tmp_path / ".pkstack" / "bootstrap.json"
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
        managed_source = power / "src" / "pkstack" / "__init__.py"
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

    receipt = json.loads((target / ".pkstack" / "bootstrap.json").read_text(encoding="utf-8"))
    for relative, expected_hash in receipt["files"].items():
        managed = target / relative
        assert managed.is_file()
        assert hashlib.sha256(managed.read_bytes()).hexdigest() == expected_hash
    installed_source = target / ".pkstack" / "projectctl" / "src" / "pkstack" / "__init__.py"
    assert installed_source.read_bytes() in expected_sources


def test_bootstrap_refuses_to_overwrite_modified_managed_file(tmp_path: Path) -> None:
    bootstrap_project(tmp_path, power_root=POWER_ROOT)
    agent = tmp_path / ".kiro" / "agents" / "pkstack.json"
    if not agent.exists():
        # The Kiro assets are added independently; use a guaranteed managed file meanwhile.
        agent = tmp_path / ".pkstack" / "projectctl" / "README.md"
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
    v2_profile = power_v2 / "templates" / "project" / ".kiro" / "agents" / "pkstack.json"
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
        ".kiro/agents/pkstack.json",
    }

    controller_preview = subprocess.run(
        [
            str(target / ".pkstack" / "bin" / "projectctl"),
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

    shim = power_v2 / "skills" / "pkstack-setup" / "scripts" / "setup_pkstack.py"
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

    live = target / ".kiro" / "agents" / "pkstack.json"
    assert marker in live.read_text(encoding="utf-8")
    assert live.read_bytes() == v2_profile.read_bytes()
    receipt = json.loads((target / ".pkstack" / "bootstrap.json").read_text(encoding="utf-8"))
    key = live.relative_to(target).as_posix()
    assert receipt["files"][key] == hashlib.sha256(live.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        ("concatenated", "invalid PKStack skill parity catalog"),
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


def test_runtime_copy_uses_only_the_reviewed_module_inventory(tmp_path: Path) -> None:
    power = tmp_path / "power"
    _copy_power_fixture(power)
    assert {path.name for path in (POWER_ROOT / "src/pkstack").glob("*.py")} == set(
        REQUIRED_SOURCE_MODULES
    )
    (power / "src/pkstack/unreviewed.py").write_text("raise RuntimeError('unreviewed')\n")
    target = tmp_path / "target"
    target.mkdir()
    assert bootstrap_project(target, power_root=power).ok
    installed = target / ".pkstack/projectctl/src/pkstack"
    assert {path.name for path in installed.glob("*.py")} == set(REQUIRED_SOURCE_MODULES)


def test_gitignore_repair_appends_only_missing_runtime_entries(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    gitignore = project / ".gitignore"
    from pkstack.bootstrap import GITIGNORE_BLOCK

    partial = "\n".join(line for line in GITIGNORE_BLOCK.splitlines() if line != ".pkstack/tmp/")
    gitignore.write_text(partial + "\n", encoding="utf-8")

    result = bootstrap_project(project, power_root=POWER_ROOT)
    lines = gitignore.read_text(encoding="utf-8").splitlines()

    assert result.ok is True
    assert ".pkstack/tmp/" in lines
    assert lines.count(".pkstack/state/") == 1
    assert lines.count("/Wiki/work/") == 1
    assert lines.count(GITIGNORE_BLOCK.splitlines()[0]) == 1
    assert bootstrap_project(project, power_root=POWER_ROOT).updated == []
