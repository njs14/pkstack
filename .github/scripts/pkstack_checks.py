#!/usr/bin/env python3
"""Shared PKStack CI profiles, deterministic partitions and fail-closed receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import tempfile
from urllib.parse import unquote, urlsplit

SCHEMA = 1
CORE_SHARDS = 6
LANES = (
    "fast",
    "browser",
    "package",
    *(f"core-{i}" for i in range(CORE_SHARDS)),
    "policy",
)
FAST_FILES = {
    "test_branding.py",
    "test_release_metadata.py",
    "test_distribution.py",
    "test_archify_provenance.py",
}
KIRO_SENTINEL = "tests/test_kiro_assets.py::test_installed_kiro_discovers_every_workspace_agent_with_221_sentinel"
KIRO_SKIP_REASON = "kiro-cli is not installed"
ROOT = Path(__file__).resolve().parents[2]


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def config_digest(root):
    root = Path(root)
    paths = sorted(
        p
        for p in (root / ".github").rglob("*")
        if p.is_file()
        and p.suffix in {".py", ".js", ".sh", ".yml", ".yaml", ".json"}
        and "__pycache__" not in p.parts
    )
    paths += [root / "powers/pkstack/pyproject.toml", root / "powers/pkstack/uv.lock"]
    return digest(
        [
            (str(p.relative_to(root)), hashlib.sha256(p.read_bytes()).hexdigest())
            for p in paths
        ]
    )


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def report_path(path):
    reports = {"reviews/release-status.md"}
    reports.update(
        f"reviews/release-030-{name}.md"
        for name in (
            "cli",
            "other-helpers",
            "acceptance",
            "core",
            "loop-helpers",
            "browser-harness",
            "permissions",
            "pipeline",
            "review",
            "archify",
            "composition",
        )
    )
    reports.update(
        f"powers/pkstack/reviews/{name}.md"
        for name in (
            "kiro-final-campaign",
            "kiro-selected-profile-campaign",
            "fable-final",
            "fable-round-1",
            "fable-round-2",
            "grok-round-1",
            "grok-round-2",
            "grok-round-3",
        )
    )
    return path in reports


def parse_changes(raw):
    fields = raw.split("\0")
    if fields[-1] == "":
        fields.pop()
    changes = []
    while fields:
        status = fields.pop(0)
        if not re.fullmatch(r"[ACDMRTUXB][0-9]*", status) or not fields:
            raise ValueError("invalid git change record")
        paths = [fields.pop(0)]
        if status.startswith(("R", "C")):
            if not fields:
                raise ValueError("incomplete rename/copy")
            paths.append(fields.pop(0))
        changes.append({"status": status, "paths": paths})
    return changes


def execution_profile(event, changes):
    certain = bool(changes) and all(c["status"][0] in "AMDRC" for c in changes)
    paths = [p for c in changes for p in c["paths"]]
    reports = event == "pull_request" and certain and all(report_path(p) for p in paths)
    if reports:
        return "reports", "none"
    expanded = (
        event != "pull_request"
        or not certain
        or any(browser_sensitive(p) for p in paths)
    )
    return "normal", "full" if expanded else "smoke"


def browser_sensitive(path):
    p = Path(path)
    return (
        "archify" in path.lower()
        or path.startswith(".github/")
        or p.name
        in {
            "pyproject.toml",
            "uv.lock",
            "pytest.ini",
            "tox.ini",
            "setup.cfg",
            "conftest.py",
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "bun.lock",
            "bun.lockb",
        }
        or p.suffix == ".lock"
    )


def make_plan(root, event, base=None, head=None):
    commit = git(root, "rev-parse", "HEAD")
    if head and head != commit:
        raise ValueError("checkout does not match expected head")
    changes = []
    if event == "pull_request" and base:
        try:
            raw = subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(root),
                    "diff",
                    "--name-status",
                    "-z",
                    "--find-renames",
                    f"{base}...{commit}",
                ],
                text=True,
            )
            changes = parse_changes(raw)
        except (subprocess.CalledProcessError, ValueError):
            changes = []  # Uncertain change sets get complete coverage.
    profile, browser = execution_profile(event, changes)
    selected = ["fast"] if profile == "reports" else list(LANES)
    return {
        "schema": SCHEMA,
        "commit": commit,
        "config_digest": config_digest(root),
        "event": event,
        "profile": profile,
        "browser_profile": browser,
        "changes": changes,
        "base": base,
        "scheduled": selected,
        "unscheduled": [x for x in LANES if x not in selected],
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
    }


def validate_plan(plan, root):
    if (
        plan.get("schema") != SCHEMA
        or plan.get("commit") != git(root, "rev-parse", "HEAD")
        or plan.get("config_digest") != config_digest(root)
    ):
        raise ValueError("plan identity does not match checkout/configuration")
    event = os.environ.get("GITHUB_EVENT_NAME", plan["event"])
    base = plan.get("base")
    if os.environ.get("GITHUB_EVENT_PATH") and event == "pull_request":
        payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        base = payload["pull_request"]["base"]["sha"]
    actual = make_plan(root, event, base, os.environ.get("GITHUB_SHA"))
    if any(plan.get(key) != actual.get(key) for key in ("event", "base", "changes")):
        raise ValueError(
            "plan change set does not match the workflow event and Git history"
        )
    profile, browser = execution_profile(plan["event"], plan["changes"])
    scheduled = ["fast"] if profile == "reports" else list(LANES)
    if (
        plan["profile"],
        plan["browser_profile"],
        plan["scheduled"],
        plan["unscheduled"],
    ) != (profile, browser, scheduled, [x for x in LANES if x not in scheduled]):
        raise ValueError("plan profile or scheduling is inconsistent")
    for key, env in (
        ("run_id", "GITHUB_RUN_ID"),
        ("run_attempt", "GITHUB_RUN_ATTEMPT"),
    ):
        if os.environ.get(env) and plan[key] != os.environ[env]:
            raise ValueError("plan run identity mismatch")


def lane_for(nodeid):
    filename = nodeid.split("::", 1)[0].rsplit("/", 1)[-1]
    if filename in FAST_FILES:
        return "fast"
    if filename == "test_archify_reader_layout.py":
        return "browser"
    if filename == "test_packaging.py":
        return "package"
    return f"core-{int(hashlib.sha256(nodeid.encode()).hexdigest(), 16) % CORE_SHARDS}"


def receipt_base(plan, lane):
    return {
        "schema": SCHEMA,
        "plan_digest": digest(plan),
        "commit": plan["commit"],
        "config_digest": plan["config_digest"],
        "run_id": plan["run_id"],
        "run_attempt": plan["run_attempt"],
        "profile": plan["profile"],
        "browser_profile": plan["browser_profile"],
        "lane": lane,
    }


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def check_reports(root, changes, base):
    if not base:
        raise ValueError("report validation requires the PR comparison base")
    subprocess.run(["git", "diff", "--check", f"{base}...HEAD"], cwd=root, check=True)
    checked = []
    for item in changes:
        if item["status"] == "D":
            continue
        path = Path(root) / item["paths"][-1]
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"report is missing or a symlink: {path}")
        text = path.read_text()
        # Check inline links/images and reference definitions; external links and anchors need no local file.
        targets = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text) + re.findall(
            r"^\s*\[[^\]]+\]:\s*(\S+)", text, re.M
        )
        for target in targets:
            target = target.strip().split(' "', 1)[0].strip("<>")
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            relative = unquote(parts.path)
            if Path(relative).is_absolute():
                continue  # Historical machine-local evidence is not a repository reference.
            resolved = (path.parent / relative).resolve()
            if (
                not resolved.is_relative_to(Path(root).resolve())
                or not resolved.exists()
            ):
                raise ValueError(
                    f"broken or outside-repository report reference in {path}: {target}"
                )
        checked.append(str(path.relative_to(root)))
    return checked


def run_commands(commands, root):
    for command in commands:
        print("+", " ".join(command), flush=True)
        subprocess.run(command, cwd=root, check=True)


def run_policy(root):
    power = root / "powers/pkstack"
    run_commands(
        [
            [
                "actionlint",
                *[
                    str(p.relative_to(root))
                    for p in sorted((root / ".github/workflows").glob("*.yml"))
                ],
            ],
            [
                "shellcheck",
                *[
                    str(p.relative_to(root))
                    for p in sorted((root / ".github/scripts").glob("*.sh"))
                ],
            ],
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                ".github/scripts",
                "-p",
                "test_*.py",
            ],
            ["node", "--test", ".github/scripts/test_pkstack_pr_policy.js"],
        ],
        root,
    )
    run_commands(
        [
            ["uv", "lock", "--check"],
            [
                "uv",
                "run",
                "--frozen",
                "ruff",
                "check",
                "src",
                "tests",
                "skills/pkstack-setup/scripts/setup_pkstack.py",
            ],
            [
                "uv",
                "run",
                "--frozen",
                "ruff",
                "format",
                "--check",
                "src",
                "tests",
                "skills/pkstack-setup/scripts/setup_pkstack.py",
            ],
            ["uv", "run", "--frozen", "ty", "check"],
        ],
        power,
    )
    knowledge = [
        "./.pkstack/bin/projectctl",
        "knowledge",
        "validate",
        "--output",
        "json",
    ]
    run_commands(
        [
            ["./.pkstack/bin/projectctl", "version", "--output", "json"],
            ["./.pkstack/bin/projectctl", "feature", "validate", "--output", "json"],
            knowledge,
        ],
        root,
    )


def run_lane(root, plan, lane, receipt):
    validate_plan(plan, root)
    if lane not in plan["scheduled"]:
        raise ValueError("lane not scheduled by this profile")
    if lane != "policy" and plan["profile"] != "reports":
        env = dict(
            os.environ,
            PKSTACK_CHECK_PLAN=json.dumps(plan),
            PKSTACK_CHECK_LANE=lane,
            PKSTACK_CHECK_RECEIPT=str(Path(receipt).resolve()),
            PKSTACK_BROWSER_PROFILE=plan["browser_profile"],
        )
        # Shared checks own collection; local selection flags or import paths
        # must not turn a narrowed run into apparently complete evidence.
        env.pop("PYTEST_ADDOPTS", None)
        env.pop("PYTEST_PLUGINS", None)
        env["PYTHONPATH"] = str(root / ".github/scripts")
        diagnostics_root = env.get("PKSTACK_DIAGNOSTICS")
        if diagnostics_root is None:
            diagnostics_root = tempfile.mkdtemp(prefix="pkstack-diagnostics-")
        diagnostics = Path(diagnostics_root) / lane
        if diagnostics.exists() or diagnostics.is_symlink():
            raise ValueError("diagnostics directory already exists; use fresh evidence")
        diagnostics.parent.mkdir(parents=True, exist_ok=True)
        return subprocess.run(
            [
                "uv",
                "run",
                "--frozen",
                "pytest",
                "tests",
                "-o",
                "addopts=",
                "--strict-config",
                "--strict-markers",
                "-q",
                "-p",
                "pkstack_pytest_partition",
                "--basetemp",
                str(diagnostics),
            ],
            cwd=root / "powers/pkstack",
            env=env,
        ).returncode
    started = time.monotonic()
    result = receipt_base(plan, lane)
    code = 0
    try:
        if plan["profile"] == "reports":
            result["reports"] = check_reports(root, plan["changes"], plan["base"])
        else:
            run_policy(root)
        result["outcome"] = "passed"
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        code = 1
        result.update(outcome="failed", error=str(error))
    result["duration_seconds"] = time.monotonic() - started
    write_json(receipt, result)
    return code


def verify_receipts(plan, receipts, needs=None):
    by_lane = {}
    for receipt in receipts:
        lane = receipt.get("lane")
        if lane not in plan["scheduled"] or lane in by_lane:
            raise ValueError("unexpected or duplicate lane receipt")
        if any(receipt.get(k) != v for k, v in receipt_base(plan, lane).items()):
            raise ValueError("receipt identity mismatch")
        if receipt.get("outcome") != "passed":
            raise ValueError(f"lane did not pass: {lane}")
        by_lane[lane] = receipt
    if set(by_lane) != set(plan["scheduled"]):
        raise ValueError("missing lane receipts")
    if needs is not None:
        expected = {"classify", "fast", "browser", "package", "core", "policy"}
        if set(needs) != expected:
            raise ValueError("incomplete workflow dependency results")
        for job, state in needs.items():
            required = job in {"classify", "fast"} or plan["profile"] == "normal"
            if state.get("result") != ("success" if required else "skipped"):
                raise ValueError(f"unexpected job result: {job}")
    if plan["profile"] == "reports":
        return {"tests": 0, "profile": "reports"}
    collection = None
    completed = []
    for lane, receipt in by_lane.items():
        if lane == "policy":
            continue
        ids = receipt.get("collection")
        if (
            not isinstance(ids, list)
            or not ids
            or len(set(ids)) != len(ids)
            or receipt.get("collection_digest") != digest(ids)
        ):
            raise ValueError("invalid collection")
        if collection is None:
            collection = ids
        elif collection != ids:
            raise ValueError("collection differs across lanes")
        expected = [n for n in ids if lane_for(n) == lane]
        results = receipt.get("results", [])
        if (
            [r["nodeid"] for r in results] != expected
            or receipt.get("issues")
            or receipt.get("exit_status") != 0
        ):
            raise ValueError("missing, duplicate, unordered or incomplete test results")
        for result in results:
            phases = result.get("phases", {})
            if result["outcome"] == "passed" and phases != {
                "setup": "passed",
                "call": "passed",
                "teardown": "passed",
            }:
                raise ValueError("test phases are incomplete")
            if result["outcome"] == "skipped":
                if phases not in (
                    {"setup": "skipped", "teardown": "passed"},
                    {"setup": "passed", "call": "skipped", "teardown": "passed"},
                ):
                    raise ValueError("skipped test phases are incomplete")
                if (
                    result["nodeid"] != KIRO_SENTINEL
                    or result.get("skip_reason") != KIRO_SKIP_REASON
                ):
                    raise ValueError("unexpected skipped test")
            elif result["outcome"] != "passed":
                raise ValueError("test did not pass")
            completed.append(result["nodeid"])
    if (
        collection is None
        or len(completed) != len(set(completed))
        or set(completed) != set(collection)
    ):
        raise ValueError("test partitions are incomplete or overlapping")
    return {
        "tests": len(completed),
        "profile": "normal",
        "collection_digest": digest(collection),
        "lane_seconds": {k: v.get("duration_seconds") for k, v in by_lane.items()},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    classify = commands.add_parser("classify")
    classify.add_argument(
        "--event", choices=["pull_request", "push", "local"], required=True
    )
    classify.add_argument("--base")
    classify.add_argument("--head")
    classify.add_argument("--output", type=Path, required=True)
    run = commands.add_parser("run")
    run.add_argument("--plan", type=Path, required=True)
    run.add_argument("--lane", choices=LANES, required=True)
    run.add_argument("--receipt", type=Path, required=True)
    aggregate = commands.add_parser("aggregate")
    aggregate.add_argument("--plan", type=Path, required=True)
    aggregate.add_argument("--receipts", type=Path, required=True)
    aggregate.add_argument("--needs", help="GitHub needs object as JSON")
    aggregate.add_argument("--output", type=Path)
    local = commands.add_parser(
        "local",
        help="Run fast contracts or the complete partitioned suite with shared CI commands",
    )
    local.add_argument("profile", choices=["fast", "full"])
    local.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if args.command == "classify":
        plan = make_plan(root, args.event, args.base, args.head)
        write_json(args.output, plan)
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
                stream.write(
                    f"profile={plan['profile']}\nbrowser_profile={plan['browser_profile']}\n"
                )
        print(json.dumps(plan))
        return 0
    if args.command == "local":
        plan = make_plan(root, "local")
        # Refuse to mix this execution with stale receipts or overwrite another run.
        if args.output is None:
            args.output = Path(tempfile.mkdtemp(prefix="pkstack-local-checks-"))
        else:
            args.output.mkdir(parents=True, exist_ok=False)
        print(f"Check evidence: {args.output}", flush=True)
        write_json(args.output / "plan.json", plan)
        os.environ["PKSTACK_DIAGNOSTICS"] = str(args.output.resolve() / "diagnostics")
        lanes = ["fast"] if args.profile == "fast" else list(LANES)
        receipt_dir = args.output / "receipts"
        code = max(
            run_lane(root, plan, lane, receipt_dir / f"{lane}.json") for lane in lanes
        )
        if code == 0 and args.profile == "full":
            receipts = [
                json.loads((receipt_dir / f"{lane}.json").read_text()) for lane in lanes
            ]
            write_json(args.output / "summary.json", verify_receipts(plan, receipts))
        return code
    plan = json.loads(args.plan.read_text())
    validate_plan(plan, root)
    if args.command == "run":
        return run_lane(root, plan, args.lane, args.receipt)
    receipts = [
        json.loads(p.read_text()) for p in sorted(args.receipts.rglob("*.json"))
    ]
    summary = verify_receipts(
        plan, receipts, json.loads(args.needs) if args.needs else None
    )
    if args.output:
        write_json(args.output, summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as error:
        print(f"PKStack checks failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
