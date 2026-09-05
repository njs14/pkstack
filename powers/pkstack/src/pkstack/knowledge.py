"""Optional process boundary to canonical OKF tooling.

This module deliberately does not implement OKF search, graphs, claims, or
registry semantics.  When ``okn`` is absent, only the narrow feature-map files
owned by PKStack are validated locally.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote

from pkstack.features import validate_feature_map
from pkstack.models import CommandSpec
from pkstack.paths import WorkspacePathError, ensure_tree_no_symlinks
from pkstack.runner import display_command, run_command


class KnowledgeError(RuntimeError):
    pass


_OKN_ENV = {
    "DO_NOT_TRACK": "1",
    "OPENKNOWLEDGE_TELEMETRY": "off",
}
_OKN_SPEC_VERSION = "0.2"
_OKN_SCHEMA_VERSION = "1"
_MIN_OKN_VERSION = (0, 13, 0)
_VERSION_PATTERN = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_LOCATOR_PATTERN = re.compile(
    r"okf\+sha256://(?P<revision>[0-9a-f]{64})/"
    r"(?P<path>[^#]+)#(?P<content>[0-9a-f]{64})"
)
MIN_SEARCH_BUDGET = 64
MAX_SEARCH_BUDGET = 8_000


def _json_result(stdout: str, *, operation: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return None, f"okn {operation} did not return valid JSON: {exc}"
    if not isinstance(value, dict):
        return None, f"okn {operation} returned JSON that is not an object"
    if value.get("schemaVersion") != _OKN_SCHEMA_VERSION:
        return None, (
            f"okn {operation} returned unsupported schemaVersion {value.get('schemaVersion')!r}"
        )
    return value, None


def _reported_root_matches(value: object, expected_root: Path) -> bool:
    if not isinstance(value, str):
        return False
    reported = Path(value)
    if not reported.is_absolute():
        return False
    try:
        return reported.resolve(strict=True) == expected_root.resolve(strict=True)
    except OSError:
        return False


def _validation_protocol_error(report: dict[str, Any], *, expected_root: Path) -> str | None:
    if not _reported_root_matches(report.get("root"), expected_root):
        return "okn validate returned a root that does not match the requested Wiki"
    if report.get("specVersion") != _OKN_SPEC_VERSION:
        return f"okn validate returned unexpected specVersion {report.get('specVersion')!r}"
    if report.get("profile") != "okf":
        return f"okn validate returned unexpected profile {report.get('profile')!r}"
    summary = report.get("summary")
    if not isinstance(summary, dict) or summary.get("status") not in {"pass", "warn", "fail"}:
        return "okn validate returned an invalid summary status"
    issues = report.get("issues")
    if not isinstance(issues, list):
        return "okn validate returned an invalid issues collection"
    for key in ("files", "concepts", "indexes", "logs"):
        if type(report.get(key)) is not int or report[key] < 0:
            return f"okn validate returned an invalid {key} count"
    for key in ("errorCount", "warningCount", "issueCount"):
        if type(summary.get(key)) is not int or summary[key] < 0:
            return f"okn validate returned an invalid summary {key}"
    if summary["issueCount"] != len(issues):
        return "okn validate returned an issue count that does not match its issues"
    severities: list[str] = []
    for issue in issues:
        error = _issue_protocol_error(issue, operation="validate")
        if error:
            return error
        severities.append(issue["severity"])
    if summary["errorCount"] != severities.count("error"):
        return "okn validate returned an error count that does not match its issues"
    if summary["warningCount"] != severities.count("warning"):
        return "okn validate returned a warning count that does not match its issues"
    expected_status = (
        "fail" if summary["errorCount"] else "warn" if summary["warningCount"] else "pass"
    )
    if summary["status"] != expected_status:
        return "okn validate returned a summary status that contradicts its issue counts"
    return None


def _search_protocol_error(
    report: dict[str, Any],
    *,
    query: str,
    budget: int,
    expected_root: Path,
) -> str | None:
    if not _reported_root_matches(report.get("root"), expected_root):
        return "okn search returned a root that does not match the requested Wiki"
    if report.get("query") != query:
        return "okn search returned a query that does not match the requested query"
    if report.get("budget") != budget:
        return "okn search returned a budget that does not match the requested budget"
    if "status" in report and report["status"] != "managed":
        return "okn search returned a status that is not managed"
    revision = report.get("revision")
    if not isinstance(revision, dict):
        return "okn search returned an invalid revision"
    if revision.get("specVersion") != _OKN_SPEC_VERSION:
        return "okn search returned a revision with an unexpected spec version"
    revision_sha = revision.get("indexSha256")
    if not isinstance(revision_sha, str) or not _SHA256_PATTERN.fullmatch(revision_sha):
        return "okn search returned a revision with an invalid index SHA-256"
    sources = report.get("sources")
    if not isinstance(sources, list):
        return "okn search returned an invalid sources collection"
    estimated_tokens = report.get("estimatedTokens")
    if type(estimated_tokens) is not int or estimated_tokens < 0 or estimated_tokens > budget:
        return "okn search returned an invalid or over-budget token estimate"
    limit = report.get("limit")
    if type(limit) is not int or limit < 1 or len(sources) > limit:
        return "okn search returned an invalid source limit"
    route = report.get("route")
    if (
        not isinstance(route, list)
        or not route
        or any(not isinstance(item, str) or not item.strip() for item in route)
        or len(set(route)) != len(route)
    ):
        return "okn search returned an invalid retrieval route"
    issues = report.get("issues")
    if not isinstance(issues, list):
        return "okn search returned an invalid issues collection"
    for issue in issues:
        error = _issue_protocol_error(issue, operation="search")
        if error:
            return error
    source_ids: set[str] = set()
    source_locators: set[str] = set()
    source_token_total = 0
    for source in sources:
        error = _source_protocol_error(source, revision_sha=revision_sha)
        if error:
            return error
        assert isinstance(source, dict)
        source_id = source["id"]
        locator = source["locator"]
        if source_id in source_ids or locator in source_locators:
            return "okn search returned duplicate source identity"
        source_ids.add(source_id)
        source_locators.add(locator)
        source_token_total += source["estimatedTokens"]
    if source_token_total != estimated_tokens:
        return "okn search returned a token estimate that does not match its sources"
    return None


def _issue_protocol_error(issue: object, *, operation: str) -> str | None:
    if not isinstance(issue, dict):
        return f"okn {operation} returned an issue that is not an object"
    path = issue.get("path")
    if not isinstance(path, str) or not _safe_relative_markdown_path(path):
        return f"okn {operation} returned an issue with an unsafe path"
    if type(issue.get("line")) is not int or issue["line"] < 1:
        return f"okn {operation} returned an issue with an invalid line"
    if issue.get("severity") not in {"error", "warning"}:
        return f"okn {operation} returned an issue with an invalid severity"
    for key in ("rule", "message"):
        if not isinstance(issue.get(key), str) or not issue[key].strip():
            return f"okn {operation} returned an issue with an invalid {key}"
    return None


def _source_protocol_error(source: object, *, revision_sha: str) -> str | None:
    if not isinstance(source, dict):
        return "okn search returned a source that is not an object"
    path = source.get("path")
    if not isinstance(path, str) or not _safe_relative_markdown_path(path):
        return "okn search returned a source with an unsafe path"
    content_sha = source.get("contentSha256")
    if not isinstance(content_sha, str) or not _SHA256_PATTERN.fullmatch(content_sha):
        return "okn search returned a source with an invalid content SHA-256"
    locator = source.get("locator")
    match = _LOCATOR_PATTERN.fullmatch(locator) if isinstance(locator, str) else None
    if (
        match is None
        or match["revision"] != revision_sha
        or match["content"] != content_sha
        or unquote(match["path"]) != path
    ):
        return "okn search returned a source with an invalid content-addressed locator"
    line_start = source.get("lineStart")
    line_end = source.get("lineEnd")
    if (
        type(line_start) is not int
        or type(line_end) is not int
        or line_start < 1
        or line_end < line_start
    ):
        return "okn search returned a source with an invalid line range"
    for key in ("id", "relation", "markdown"):
        if not isinstance(source.get(key), str) or not source[key].strip():
            return f"okn search returned a source with an invalid {key}"
    if type(source.get("estimatedTokens")) is not int or source["estimatedTokens"] < 1:
        return "okn search returned a source with an invalid token estimate"
    return None


def _safe_relative_markdown_path(value: str) -> bool:
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and path.suffix == ".md"


def _resolve_okn(root: Path) -> tuple[str | None, str | None, str | None]:
    workspace = root.resolve()
    for name in ("okn", "openknowledge"):
        discovered = shutil.which(name)
        if not discovered:
            continue
        try:
            executable = Path(discovered).resolve(strict=True)
        except OSError as exc:
            return None, name, f"unable to resolve {name}: {exc}"
        if executable == workspace or workspace in executable.parents:
            return (
                None,
                name,
                f"refusing workspace-local canonical OKF executable: {executable}",
            )
        return str(executable), name, None
    return None, None, None


def _probe_okn_version(
    root: Path,
    executable: str,
    *,
    timeout_seconds: float = 10.0,
) -> tuple[str | None, str | None]:
    argv = (executable, "version")
    result = run_command(
        CommandSpec(argv=argv, display=display_command(argv), source="explicit"),
        root=root,
        timeout_seconds=timeout_seconds,
        env=_OKN_ENV,
    )
    version = result.stdout.strip()
    match = _VERSION_PATTERN.fullmatch(version)
    if not result.passed or result.truncated or match is None:
        return None, "canonical OKF executable did not return a supported semantic version"
    parsed = tuple(int(part) for part in match.groups())
    if parsed < _MIN_OKN_VERSION:
        return version, f"canonical OKF version {version} is older than supported 0.13.0"
    return version, None


def status(root: Path) -> dict[str, Any]:
    try:
        wiki = ensure_tree_no_symlinks(root, Path("Wiki"))
        workspace_safe = True
        path_error = None
    except WorkspacePathError as exc:
        wiki = root.resolve() / "Wiki"
        workspace_safe = False
        path_error = str(exc)
    executable, executable_name, executable_error = _resolve_okn(root)
    version = None
    if executable is not None and executable_error is None:
        version, executable_error = _probe_okn_version(root, executable)
    available = executable is not None and executable_error is None
    return {
        "wiki": str(wiki),
        "wiki_present": workspace_safe and wiki.is_dir(),
        "workspace_safe": workspace_safe,
        "path_error": path_error,
        "okn_available": available,
        "okn_executable": executable,
        "okn_executable_name": executable_name,
        "okn_version": version,
        "okn_error": executable_error,
        "mode": "canonical-okn" if available else "feature-map-only",
    }


def validate(
    root: Path,
    *,
    require_okn: bool = False,
    timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    info = status(root)
    if not info["workspace_safe"]:
        raise KnowledgeError(str(info["path_error"]))
    feature_result = validate_feature_map(root)
    if not info["okn_available"]:
        if require_okn:
            detail = info["okn_error"] or "okn is not installed"
            raise KnowledgeError(f"{detail}; install a supported canonical OKF implementation")
        return {
            "ok": feature_result["ok"],
            "mode": "feature-map-only",
            "warning": (
                "Broad OKF validation was not run because canonical okn is unavailable."
                if not info["okn_error"]
                else f"Broad OKF validation was not run: {info['okn_error']}."
            ),
            "feature_map": feature_result,
        }

    argv = (
        str(info["okn_executable"]),
        "--error-format",
        "json",
        "validate",
        "--spec",
        _OKN_SPEC_VERSION,
        "--profile",
        "okf",
        "--format",
        "json",
        "Wiki",
    )
    command = CommandSpec(
        argv=argv,
        display=display_command(argv),
        source="explicit",
    )
    result = run_command(
        command,
        root=root,
        timeout_seconds=timeout_seconds,
        env=_OKN_ENV,
    )
    report, protocol_error = _json_result(result.stdout, operation="validate")
    if report is not None:
        protocol_error = _validation_protocol_error(
            report,
            expected_root=Path(str(info["wiki"])),
        )
    okn_ok = (
        result.passed
        and not result.truncated
        and protocol_error is None
        and report is not None
        and report["summary"]["status"] in {"pass", "warn"}
    )
    return {
        "ok": feature_result["ok"] and okn_ok,
        "mode": "canonical-okn",
        "okn_spec_version": _OKN_SPEC_VERSION,
        "okn_schema_version": _OKN_SCHEMA_VERSION,
        "okn_version": info["okn_version"],
        "feature_map": feature_result,
        "command": command.to_dict(),
        "result": result.to_dict(),
        "report": report,
        "protocol_error": (
            "okn validate output exceeded the bounded capture limit"
            if result.truncated
            else protocol_error
        ),
    }


def search(
    root: Path,
    query: str,
    *,
    budget: int = 1_200,
    timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    normalized_query = query.strip()
    if not normalized_query:
        raise KnowledgeError("query must be non-empty")
    if normalized_query.startswith("-"):
        raise KnowledgeError(
            "query must not begin with '-' because okn could interpret it as an option"
        )
    if type(budget) is not int or not MIN_SEARCH_BUDGET <= budget <= MAX_SEARCH_BUDGET:
        raise KnowledgeError(
            f"search budget must be an integer from {MIN_SEARCH_BUDGET} to {MAX_SEARCH_BUDGET}"
        )
    try:
        ensure_tree_no_symlinks(root, Path("Wiki"))
    except WorkspacePathError as exc:
        raise KnowledgeError(str(exc)) from exc
    info = status(root)
    executable = info["okn_executable"]
    if not info["okn_available"] or not executable:
        detail = info["okn_error"] or "okn is not installed"
        raise KnowledgeError(f"canonical okn is required for broad knowledge search: {detail}")
    argv = (
        executable,
        "--error-format",
        "json",
        "search",
        "--spec",
        _OKN_SPEC_VERSION,
        "--format",
        "json",
        "--budget",
        str(budget),
        "Wiki",
        normalized_query,
    )
    command = CommandSpec(argv=argv, display=display_command(argv), source="explicit")
    result = run_command(
        command,
        root=root,
        timeout_seconds=timeout_seconds,
        env=_OKN_ENV,
    )
    context, protocol_error = _json_result(result.stdout, operation="search")
    if context is not None:
        protocol_error = _search_protocol_error(
            context,
            query=normalized_query,
            budget=budget,
            expected_root=Path(str(info["wiki"])),
        )
    ok = result.passed and not result.truncated and protocol_error is None and context is not None
    return {
        "ok": ok,
        "mode": "canonical-okn",
        "okn_spec_version": _OKN_SPEC_VERSION,
        "okn_schema_version": _OKN_SCHEMA_VERSION,
        "okn_version": info["okn_version"],
        "command": command.to_dict(),
        "result": result.to_dict(),
        "context": context,
        "protocol_error": (
            "okn search output exceeded the bounded capture limit"
            if result.truncated
            else protocol_error
        ),
    }
