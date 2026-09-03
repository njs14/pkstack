from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
POWER_ROOT = REPOSITORY_ROOT / "powers" / "pk-stack"
CATALOG_PATH = POWER_ROOT / "docs" / "upstream-skill-parity.json"
EVIDENCE_PATH = REPOSITORY_ROOT / "reviews" / "skill-route-campaign.json"
LIVE_SKILLS = REPOSITORY_ROOT / ".kiro" / "skills"
CACHED_SKILLS = REPOSITORY_ROOT / ".pstack" / "projectctl" / "skills"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _skill_names(root: Path) -> set[str]:
    return {
        path.name
        for path in root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }


def _routes_by_name(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    routes = catalog["skills"]
    assert isinstance(routes, list)
    return {route["name"]: route for route in routes}


def _route_projection(route: dict[str, Any]) -> dict[str, Any]:
    projection = {
        "name": route["name"],
        "disposition": route["disposition"],
        "target": route["target"],
        "rationale": route["rationale"],
        "pinned_package_tree_sha": route["pinned"]["package_tree_sha"],
        "pinned_file_count": len(route["pinned"]["files"]),
        "current_package_tree_sha": route["current"]["package_tree_sha"],
        "current_file_count": len(route["current"]["files"]),
    }
    for optional in ("consolidates_to", "safe_alternative"):
        if optional in route:
            projection[optional] = route[optional]
    return projection


def _run(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )


def _run_json(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = _run(command, cwd=cwd, environment=environment)
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    payload = json.loads(completed.stdout)
    assert isinstance(payload, dict)
    return completed, payload


def _assert_generated_route(
    *,
    name: str,
    canonical_relative: str,
    expected_sha256: str,
    include_live: bool = True,
) -> None:
    canonical = POWER_ROOT / canonical_relative
    cached = CACHED_SKILLS / name / "SKILL.md"
    assert _sha256(canonical) == expected_sha256
    assert _sha256(cached) == expected_sha256
    live = LIVE_SKILLS / name / "SKILL.md"
    if include_live:
        assert _sha256(live) == expected_sha256
    else:
        assert not live.exists()


def test_skill_route_campaign_is_bound_to_live_catalog_and_generated_assets() -> None:
    evidence = _load_json(EVIDENCE_PATH)
    catalog = _load_json(CATALOG_PATH)
    routes = _routes_by_name(catalog)

    assert evidence["schema_version"] == 1
    assert evidence["decision"] == "pass"
    assert evidence["catalog"]["sha256"] == _sha256(CATALOG_PATH)
    assert evidence["catalog"]["source"] == catalog["source"]
    assert evidence["catalog"]["summary"] == catalog["summary"]
    assert evidence["catalog"]["pk_only_skills"] == catalog["pk_only_skills"]
    assert evidence["campaign"]["network_access"] is False
    assert evidence["campaign"]["secret_access"] is False
    assert evidence["campaign"]["interactive_kiro_invocation"] is False

    canonical_names = _skill_names(POWER_ROOT / "skills")
    live_names = _skill_names(LIVE_SKILLS)
    cached_names = _skill_names(CACHED_SKILLS)
    assert len(canonical_names) == 49
    assert len(live_names) == 48
    assert len(cached_names) == 49
    assert live_names == canonical_names - {"setup-pstack"}
    assert cached_names == canonical_names

    selected = evidence["routes"]
    expected_routes = {
        "direct": ("create-verification-skill", "direct-port"),
        "alias": ("principle-prove-it-works", "alias-consolidation"),
        "native_replacement": ("setup-pstack", "native-kiro-replacement"),
        "exclusion": ("make-bot-ui", "excluded"),
    }
    for route_class, (name, disposition) in expected_routes.items():
        recorded = selected[route_class]
        assert recorded["name"] == name
        assert recorded["disposition"] == disposition
        assert recorded["catalog_entry"] == _route_projection(routes[name])

    direct = selected["direct"]
    _assert_generated_route(
        name=direct["name"],
        canonical_relative=direct["catalog_entry"]["target"],
        expected_sha256=direct["asset_sha256"],
    )

    alias = selected["alias"]
    _assert_generated_route(
        name=alias["name"],
        canonical_relative=alias["catalog_entry"]["target"],
        expected_sha256=alias["asset_sha256"],
    )
    alias_core = POWER_ROOT / alias["catalog_entry"]["consolidates_to"]
    assert _sha256(alias_core) == alias["consolidation_sha256"]
    assert (
        _sha256(LIVE_SKILLS / "principles" / "references" / "catalog.md")
        == alias["consolidation_sha256"]
    )
    assert (
        _sha256(CACHED_SKILLS / "principles" / "references" / "catalog.md")
        == alias["consolidation_sha256"]
    )

    native = selected["native_replacement"]
    _assert_generated_route(
        name=native["name"],
        canonical_relative=native["catalog_entry"]["target"],
        expected_sha256=native["asset_sha256"],
        include_live=False,
    )
    setup_shim = POWER_ROOT / "skills" / native["name"] / "scripts" / "setup_pstack.py"
    assert _sha256(setup_shim) == native["setup_shim_sha256"]
    assert (
        _sha256(CACHED_SKILLS / native["name"] / "scripts" / "setup_pstack.py")
        == native["setup_shim_sha256"]
    )

    excluded = selected["exclusion"]
    assert excluded["catalog_entry"]["target"] is None
    assert excluded["exercise"]["resolution"] == "refused-excluded"
    for root in (POWER_ROOT / "skills", LIVE_SKILLS, CACHED_SKILLS):
        assert not (root / excluded["name"]).exists()
    alternative = excluded["safe_alternative"]
    assert alternative["name"] == "architect"
    _assert_generated_route(
        name=alternative["name"],
        canonical_relative=routes[alternative["name"]]["target"],
        expected_sha256=alternative["asset_sha256"],
    )


def test_skill_route_campaign_replays_all_four_route_classes_offline(tmp_path: Path) -> None:
    evidence = _load_json(EVIDENCE_PATH)
    catalog = _load_json(CATALOG_PATH)
    routes = _routes_by_name(catalog)
    selected = evidence["routes"]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["UV_OFFLINE"] = "1"
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Native replacement: run the Power-local setup entrypoint exactly as the skill directs.
    native = selected["native_replacement"]
    assert routes[native["name"]]["disposition"] == "native-kiro-replacement"
    setup_shim = POWER_ROOT / "skills" / native["name"] / "scripts" / "setup_pstack.py"
    _, preflight = _run_json(
        [
            sys.executable,
            str(setup_shim),
            "--root",
            str(workspace),
            "--dry-run",
            "--output",
            "json",
        ],
        cwd=REPOSITORY_ROOT,
        environment=environment,
    )
    _, applied = _run_json(
        [sys.executable, str(setup_shim), "--root", str(workspace), "--output", "json"],
        cwd=REPOSITORY_ROOT,
        environment=environment,
    )
    first_receipt = (workspace / ".pstack" / "bootstrap.json").read_bytes()
    _, repeated = _run_json(
        [sys.executable, str(setup_shim), "--root", str(workspace), "--output", "json"],
        cwd=REPOSITORY_ROOT,
        environment=environment,
    )
    second_receipt = (workspace / ".pstack" / "bootstrap.json").read_bytes()
    controller = workspace / ".pstack" / "bin" / "projectctl"
    _, doctor = _run_json(
        [str(controller), "doctor", "--output", "json"],
        cwd=workspace,
        environment=environment,
    )
    assert preflight["ok"] is native["exercise"]["preflight_ok"]
    assert preflight["dry_run"] is True
    assert applied["ok"] is native["exercise"]["apply_ok"]
    assert repeated["created"] == native["exercise"]["repeat_created"]
    assert repeated["updated"] == native["exercise"]["repeat_updated"]
    assert first_receipt == second_receipt
    assert doctor["ok"] is native["exercise"]["doctor_ok"]
    assert doctor["summary"]["fail"] == native["exercise"]["doctor_failures"]

    # Direct port: enact create-verification-skill's schema-2 generate/validate/verify lifecycle.
    direct = selected["direct"]
    assert routes[direct["name"]]["disposition"] == "direct-port"
    probe = workspace / "route_probe.py"
    probe.write_text(
        "import json, sys\n"
        "from pathlib import Path\n"
        "log = Path('route-probe-log.json')\n"
        "calls = json.loads(log.read_text()) if log.exists() else []\n"
        "calls.append(sys.argv[1])\n"
        "log.write_text(json.dumps(calls))\n"
        "print(json.dumps({'ok': True, 'route': sys.argv[1]}))\n",
        encoding="utf-8",
    )
    features: list[dict[str, object]] = []
    for index, slug in enumerate(("route-contract", "setup-contract", "safety-contract"), 1):
        features.append(
            {
                "slug": slug,
                "title": f"Route campaign surface {index}",
                "behavior": f"A caller observes deterministic route surface {index}.",
                "expected_path": "Public Python CLI -> bounded observable JSON result",
                "command": [sys.executable, "route_probe.py", slug],
                "related": [],
                "sub_features": [
                    {
                        "identifier": "deterministic-result",
                        "behavior": "The public fixture exits zero with a bounded result.",
                    }
                ],
                "entrypoints": [
                    {
                        "identifier": "cli",
                        "user_path": f"Run the {slug} fixture command.",
                        "drive": f"Run {sys.executable} route_probe.py {slug}.",
                        "observable": "The command exits zero and records only its route slug.",
                    }
                ],
                "gotchas": ["Do not substitute static inspection for the stored verifier."],
                "evidence_boundary": "Retain bounded command output and the owned call log.",
                "cleanup_boundary": "The pytest temporary workspace owns every created path.",
            }
        )
    feature_plan = workspace / "skill-route-feature-plan.json"
    feature_plan.write_text(json.dumps({"features": features}), encoding="utf-8")
    _, generated = _run_json(
        [
            str(controller),
            "feature",
            "generate-map",
            str(feature_plan),
            "--representative",
            "route-contract",
            "--output",
            "json",
        ],
        cwd=workspace,
        environment=environment,
    )
    _, validated = _run_json(
        [str(controller), "feature", "validate", "--output", "json"],
        cwd=workspace,
        environment=environment,
    )
    _, verified = _run_json(
        [
            str(controller),
            "feature",
            "verify",
            "route-contract",
            "--output",
            "json",
        ],
        cwd=workspace,
        environment=environment,
    )
    call_log = json.loads((workspace / "route-probe-log.json").read_text(encoding="utf-8"))
    assert generated["representative"] == direct["exercise"]["representative"]
    assert [feature["initially_verified"] for feature in generated["features"]] == direct[
        "exercise"
    ]["initially_verified"]
    assert validated["ok"] is direct["exercise"]["feature_validate_ok"]
    assert validated["feature_count"] == direct["exercise"]["feature_count"]
    assert verified["ok"] is direct["exercise"]["feature_verify_ok"]
    assert call_log == direct["exercise"]["representative_call_log"]

    # Alias/consolidation: apply the focused leaf and shared Prove it works predicate red then green.
    alias = selected["alias"]
    assert routes[alias["name"]]["disposition"] == "alias-consolidation"
    claim_probe = workspace / "claim_probe.py"
    claim_probe.write_text(
        "import json\n"
        "from pathlib import Path\n"
        "ok = Path('claim.txt').is_file() and Path('claim.txt').read_text() == 'proved\\n'\n"
        "print(json.dumps({'ok': ok, 'predicate': 'claim.txt contains proved newline'}))\n"
        "raise SystemExit(0 if ok else 9)\n",
        encoding="utf-8",
    )
    red = _run([sys.executable, claim_probe.name], cwd=workspace, environment=environment)
    (workspace / "claim.txt").write_text("proved\n", encoding="utf-8")
    green = _run([sys.executable, claim_probe.name], cwd=workspace, environment=environment)
    assert red.returncode == alias["exercise"]["red_exit"]
    assert json.loads(red.stdout)["ok"] is False
    assert green.returncode == alias["exercise"]["green_exit"]
    assert json.loads(green.stdout)["ok"] is True

    # Exclusion: resolve the named request through the catalog and prove it cannot become runnable.
    excluded = selected["exclusion"]
    excluded_route = routes[excluded["name"]]
    resolution = (
        "refused-excluded"
        if excluded_route["disposition"] == "excluded" and excluded_route["target"] is None
        else "runnable"
    )
    assert resolution == excluded["exercise"]["resolution"]
    assert excluded_route["safe_alternative"] == excluded["catalog_entry"]["safe_alternative"]
    assert all(
        not (root / excluded["name"]).exists()
        for root in (POWER_ROOT / "skills", LIVE_SKILLS, CACHED_SKILLS)
    )
