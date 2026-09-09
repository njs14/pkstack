#!/usr/bin/env python3
"""Shared local and hosted PKStack checks with complete execution evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pkstack_python_static as static

SCHEMA = 2
FAST_FILES = {
    "test_branding.py",
    "test_release_metadata.py",
    "test_distribution.py",
    "test_archify_provenance.py",
}
KIRO_SENTINEL = (
    "tests/test_kiro_assets.py"
    "::test_installed_kiro_discovers_every_workspace_agent_with_221_sentinel"
)
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
    paths += [
        root / "powers/pkstack/pyproject.toml",
        root / "powers/pkstack/uv.lock",
        root / ".coveragerc",
        root / "pytest.ini",
        root / "maintenance/package-content.json",
        root / "ruff.toml",
        root / "ty.toml",
        root / "maintenance/knowledge-coverage.json",
    ]
    return digest(
        [(str(p.relative_to(root)), hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    )


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def report_path(path):
    reports = {"Wiki/knowledge/pkstack/release-record.md"}
    reports.update(
        f"reviews/{name}.md"
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
    expanded = event != "pull_request" or not certain or any(browser_sensitive(p) for p in paths)
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


def make_context(root, event, base=None, head=None):
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
    return {
        "schema": SCHEMA,
        "commit": commit,
        "config_digest": config_digest(root),
        "event": event,
        "profile": profile,
        "browser_profile": browser,
        "changes": changes,
        "base": base,
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
    }


def validate_context(context, root):
    if (
        context.get("schema") != SCHEMA
        or context.get("commit") != git(root, "rev-parse", "HEAD")
        or context.get("config_digest") != config_digest(root)
    ):
        raise ValueError("check identity does not match checkout/configuration")
    # A local caller (including secretless candidate verification) chooses its
    # checkout. workflow_run's GITHUB_SHA identifies the controller, not that candidate.
    hosted = context["event"] != "local"
    event = os.environ.get("GITHUB_EVENT_NAME", context["event"]) if hosted else "local"
    base = context.get("base")
    if os.environ.get("GITHUB_EVENT_PATH") and event == "pull_request":
        payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        base = payload["pull_request"]["base"]["sha"]
    actual = make_context(
        root, event, base, os.environ.get("GITHUB_SHA") if hosted else context["commit"]
    )
    if any(context.get(key) != actual.get(key) for key in ("event", "base", "changes")):
        raise ValueError("check change set does not match the workflow event and Git history")
    profile, browser = execution_profile(context["event"], context["changes"])
    if (context["profile"], context["browser_profile"]) != (profile, browser):
        raise ValueError("check profile is inconsistent")
    for key, env in (
        ("run_id", "GITHUB_RUN_ID"),
        ("run_attempt", "GITHUB_RUN_ATTEMPT"),
    ):
        if os.environ.get(env) and context[key] != os.environ[env]:
            raise ValueError("check run identity mismatch")


def selected_test(nodeid, scope):
    return scope == "full" or nodeid.split("::", 1)[0].rsplit("/", 1)[-1] in FAST_FILES


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
        # Check inline links/images and reference definitions; external links and
        # anchors need no local file.
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
            if not resolved.is_relative_to(Path(root).resolve()) or not resolved.exists():
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
    # The unittest fixtures deliberately skip without these executables when run
    # alone. Complete verification must fail instead of accepting that reduced suite.
    for tool in ("uv", "bash", "jq", "node", "actionlint", "shellcheck"):
        if shutil.which(tool) is None:
            raise FileNotFoundError(f"complete verification requires {tool}")
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
            # Workflow steps launch these scripts with the runner's interpreter, so
            # their tests run on the active one rather than the Power environment.
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
    # One entrypoint owns every maintained Python surface across local, hosted
    # and isolated candidate verification.
    static.run_static_checks(root)
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


def verify_tests(evidence, scope):
    collection = evidence.get("collection")
    if (
        not isinstance(collection, list)
        or not collection
        or len(set(collection)) != len(collection)
        or evidence.get("collection_digest") != digest(collection)
    ):
        raise ValueError("invalid product collection")
    expected = [nodeid for nodeid in collection if selected_test(nodeid, scope)]
    results = evidence.get("results", [])
    if (
        not expected
        or [r["nodeid"] for r in results] != expected
        or evidence.get("issues")
        or evidence.get("exit_status") != 0
        or evidence.get("outcome") != "passed"
    ):
        raise ValueError("missing, duplicate, unordered or incomplete test results")
    for result in results:
        phases = result.get("phases", {})
        if result["outcome"] == "passed":
            if phases != {"setup": "passed", "call": "passed", "teardown": "passed"}:
                raise ValueError("test phases are incomplete")
        elif result["outcome"] == "skipped":
            if (
                phases
                not in (
                    {"setup": "skipped", "teardown": "passed"},
                    {"setup": "passed", "call": "skipped", "teardown": "passed"},
                )
                or result["nodeid"] != KIRO_SENTINEL
                or result.get("skip_reason") != KIRO_SKIP_REASON
            ):
                raise ValueError("unexpected skipped test or incomplete skip phases")
        else:
            raise ValueError("test did not pass")
    return len(results)


def run_product(root, context, scope, output):
    evidence_path = output / "diagnostics/product.json"
    env = dict(
        os.environ,
        PKSTACK_CHECK_SCOPE=scope,
        PKSTACK_CHECK_EVIDENCE=str(evidence_path),
        PKSTACK_BROWSER_PROFILE=context["browser_profile"],
        PKSTACK_DIAGNOSTICS=str(output / "diagnostics"),
    )
    # Local pytest flags and plugin injection cannot narrow complete evidence.
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    env["PYTHONPATH"] = str(root / ".github/scripts")
    command = [
        "uv",
        "run",
        "--frozen",
        "--project",
        "powers/pkstack",
        "pytest",
        "tests",
        "-o",
        "addopts=",
        "--strict-config",
        "--strict-markers",
        "-q",
        "-p",
        "pkstack_pytest_evidence",
        "--basetemp",
        str(output / "diagnostics/tests"),
    ]
    subprocess.run(command, cwd=root, env=env, check=True)
    evidence = json.loads(evidence_path.read_text())
    verify_tests(evidence, scope)
    evidence_path.unlink()  # The successful evidence is included in the single summary.
    return evidence


def run_checks(root, context, scope, output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    summary = {**context, "scope": scope, "outcome": "incomplete", "checks": []}
    write_json(output / "summary.json", summary)
    code = 1
    try:
        validate_context(context, root)
        run_commands(
            [
                [
                    "uv",
                    "run",
                    "--frozen",
                    "--project",
                    "powers/pkstack",
                    "python",
                    "-B",
                    ".github/scripts/pkstack_knowledge_coverage.py",
                    "--repo-root",
                    ".",
                ]
            ],
            root,
        )
        summary["checks"].append("knowledge_coverage")
        if context["profile"] == "reports":
            summary["reports"] = check_reports(root, context["changes"], context["base"])
            summary["checks"].append("reports")
        else:
            summary["product"] = run_product(root, context, scope, output)
            summary["tests"] = verify_tests(summary["product"], scope)
            summary["checks"].append("product")
            if scope == "full":
                run_policy(root)
                summary["checks"].append("policy_static_metadata_knowledge")
        validate_context(context, root)
        summary["outcome"] = "passed"
        code = 0
    except (KeyboardInterrupt, InterruptedError) as error:
        summary.update(outcome="cancelled", error=str(error) or "verification interrupted")
        code = 130
    except (
        ValueError,
        KeyError,
        OSError,
        subprocess.SubprocessError,
        static.StaticCheckError,
    ) as error:
        summary.update(outcome="failed", error=str(error))
    finally:
        summary["duration_seconds"] = time.monotonic() - started
        write_json(output / "summary.json", summary)
    print(f"Checks {summary['outcome']}; evidence: {output / 'summary.json'}", flush=True)
    return code


def main():
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("classify", "hosted"):
        command = commands.add_parser(name)
        command.add_argument("--event", choices=["pull_request", "push"], required=True)
        command.add_argument("--base")
        command.add_argument("--head", required=True)
    commands.choices["hosted"].add_argument("--output", type=Path, required=True)
    local = commands.add_parser("local", help="Run focused contracts or all shared checks")
    local.add_argument("profile", choices=["fast", "full"])
    local.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    os.environ.setdefault("UV_PROJECT_ENVIRONMENT", str(root / ".venv"))
    if args.command == "local":
        context = make_context(root, "local")
        scope = args.profile
    else:
        context = make_context(root, args.event, args.base, args.head)
        scope = "full"
    if args.command == "classify":
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
                stream.write(
                    f"profile={context['profile']}\nbrowser_profile={context['browser_profile']}\n"
                )
        print(json.dumps(context))
        return 0
    output = args.output or Path(tempfile.mkdtemp(prefix="pkstack-local-checks-")) / "checks"

    def cancelled(signum, frame):
        raise InterruptedError(f"verification received signal {signum}")

    previous = signal.signal(signal.SIGTERM, cancelled)
    try:
        return run_checks(root, context, scope, output)
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as error:
        print(f"PKStack checks failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
