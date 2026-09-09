"""Pytest hooks for complete collection, execution and failure diagnostics."""

import os
import time
from typing import Any

from pkstack_checks import (
    KIRO_SENTINEL,
    KIRO_SKIP_REASON,
    digest,
    selected_test,
    write_json,
)

# One-process session state shared with report hooks that do not carry config.
SESSION: Any = None


def pytest_configure(config):
    config._pkstack_scope = os.environ["PKSTACK_CHECK_SCOPE"]
    config._pkstack_started = time.monotonic()
    config._pkstack_collection = []
    config._pkstack_results = {}
    config._pkstack_issues = []
    config._pkstack_selected = []
    # Hook reports do not carry config, so keep this one-process session state.
    global SESSION
    SESSION = config


def pytest_collection_modifyitems(session, config, items):
    ids = [item.nodeid for item in items]
    config._pkstack_collection = ids
    if len(ids) != len(set(ids)):
        config._pkstack_issues.append("duplicate collected test IDs")
    selected = [item for item in items if selected_test(item.nodeid, config._pkstack_scope)]
    deselected = [item for item in items if not selected_test(item.nodeid, config._pkstack_scope)]
    config._pkstack_selected = [item.nodeid for item in selected]
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected


def pytest_runtest_logreport(report):
    result = SESSION._pkstack_results.setdefault(
        report.nodeid, {"nodeid": report.nodeid, "phases": {}}
    )
    if report.when in result["phases"]:
        SESSION._pkstack_issues.append(f"duplicate phase: {report.nodeid}:{report.when}")
    result["phases"][report.when] = report.outcome
    result["duration_seconds"] = result.get("duration_seconds", 0) + report.duration
    if report.skipped:
        reason = report.longrepr[2] if isinstance(report.longrepr, tuple) else str(report.longrepr)
        result["skip_reason"] = reason.removeprefix("Skipped: ")
    if hasattr(report, "wasxfail"):
        SESSION._pkstack_issues.append(f"unexpected xfail: {report.nodeid}")


def pytest_sessionfinish(session, exitstatus):
    config = session.config
    results = []
    for nodeid in config._pkstack_selected:
        result = config._pkstack_results.get(nodeid, {"nodeid": nodeid, "phases": {}})
        phases = result["phases"]
        if phases == {"setup": "passed", "call": "passed", "teardown": "passed"}:
            result["outcome"] = "passed"
        elif phases in (
            {"setup": "skipped", "teardown": "passed"},
            {"setup": "passed", "call": "skipped", "teardown": "passed"},
        ):
            result["outcome"] = "skipped"
        else:
            result["outcome"] = "failed"
        if result["outcome"] == "skipped" and (
            nodeid != KIRO_SENTINEL or result.get("skip_reason") != KIRO_SKIP_REASON
        ):
            config._pkstack_issues.append(f"unexpected skipped test: {nodeid}")
        results.append(result)
    unexpected = set(config._pkstack_results) - set(config._pkstack_selected)
    if unexpected:
        config._pkstack_issues.append("executed unselected test IDs")
    final_status = int(exitstatus)
    if final_status == 0 and (
        config._pkstack_issues or any(r["outcome"] == "failed" for r in results)
    ):
        final_status = 1
        session.exitstatus = final_status
    receipt = dict(
        collection=config._pkstack_collection,
        collection_digest=digest(config._pkstack_collection),
        results=results,
        exit_status=final_status,
        outcome="passed" if final_status == 0 else "failed",
        issues=config._pkstack_issues,
        duration_seconds=time.monotonic() - config._pkstack_started,
    )
    write_json(os.environ["PKSTACK_CHECK_EVIDENCE"], receipt)
