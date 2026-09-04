"""Read-only, hash-pinned upstream drift checks for self-maintaining projects."""

from __future__ import annotations

import base64
import binascii
import difflib
import hashlib
import json
import math
import os
import re
import stat
import tempfile
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    OpenerDirector,
    ProxyHandler,
    Request,
    build_opener,
)

from pk_stack.bootstrap import (
    SKILL_ROUTE_ALIASES,
    BootstrapResult,
    bootstrap_project,
)
from pk_stack.paths import WorkspacePathError, workspace_path

UPSTREAM_SCHEMA_VERSION = 2
UPSTREAM_REVIEW_SCHEMA_VERSION = 2
DEFAULT_MANIFEST = Path("maintenance/upstreams.json")
DEFAULT_PROPOSAL = Path(".pk-stack-maintenance/proposal.json")
DEFAULT_POWER_ROOT = Path("powers/pk-stack")
DEFAULT_SKILL_PARITY = DEFAULT_POWER_ROOT / "docs/upstream-skill-parity.json"
_ACCEPT_DIRECTORY = Path(".pk-stack-maintenance")
_ACCEPT_LOCK = Path(".pk-stack/state/upstream-accept.lock")
_ACCEPT_TRANSACTION = _ACCEPT_DIRECTORY / "accept-transaction.json"
GITHUB_API_ORIGIN = "https://api.github.com"
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_TIMEOUT_SECONDS = 30.0
MAX_MANIFEST_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_SOURCES = 16
MAX_COMPARE_COMMITS = 100
MAX_COMPARE_FILES = 100
GITHUB_COMPARE_FILE_CAP = 300
MAX_COMPARE_PATCH_BYTES = 256 * 1024
MAX_FILE_PATCH_BYTES = 64 * 1024
MAX_TEXT_BLOB_BYTES = 512 * 1024
MAX_COMPARE_BLOB_BYTES = 4 * 1024 * 1024
MAX_DIFF_LINES = 5_000
MAX_COMPARE_DIFF_CELLS = 25_000_000
MAX_TREE_ENTRIES = 10_000
MAX_REVIEW_LEDGER_BYTES = 8 * 1024 * 1024
MAX_REVIEW_TRANSITIONS = 512
MAX_RATIONALE_BYTES = 2048
MAX_PROPOSAL_BYTES = 512 * 1024
MAX_SOURCE_PARITY_BYTES = 512 * 1024
MAX_SKILL_PARITY_BYTES = MAX_SOURCE_PARITY_BYTES
MAX_PROVENANCE_BYTES = 8 * 1024 * 1024
MAX_ACCEPT_TRANSACTION_BYTES = 20 * 1024 * 1024
PATCH_COUNT_CONSTRAINT = "unified-patch-body-matches-reported-additions-and-deletions"
BLOB_BINDING_CONSTRAINT = "old-blob-plus-patch-result-matches-exact-git-blob-identities"
TREE_ENTRY_CONSTRAINT = "regular-blob-modes-100644-or-100755-only"
NO_PATCH_CONSTRAINT = "zero-count-top-level-raster-asset-or-exact-blob-rename-or-mode-change-only"

try:
    import fcntl
except ImportError:  # pragma: no cover - PK-Stack currently targets macOS/Linux
    fcntl = None  # type: ignore[assignment]

_SOURCE_KEYS = {
    "id",
    "repository",
    "path",
    "ref",
    "commit",
    "subtree_sha",
    "provenance_path",
    "parity_path",
}
_LEDGER_SOURCE_KEYS = {
    "id",
    "repository",
    "path",
    "provenance_path",
    "parity_path",
    "genesis",
    "transitions",
}
_IDENTITY_KEYS = {"commit", "subtree_sha"}
_SKILL_PARITY_IDENTITY_KEYS = {"commit", "pstack_subtree_sha"}
_SKILL_PARITY_KEYS = {
    "schema_version",
    "source",
    "allowed_dispositions",
    "allowed_resource_handling",
    "pk_only_skills",
    "summary",
    "skills",
}
_SKILL_PARITY_SOURCE_KEYS = {
    "id",
    "repository",
    "path",
    "catalog_path",
    "pinned",
    "current",
    "retrieved_on",
}
_SKILL_PARITY_SUMMARY_KEYS = {
    "direct-port",
    "alias-consolidation",
    "native-kiro-replacement",
    "excluded",
    "upstream_total",
    "routed_upstream_names",
    "shipped_skill_directories",
    "pinned_package_files",
    "current_package_files",
    "semantic_source_files",
    "helper_semantics_only_files",
    "runtime_specific_exclusion_files",
}
_SOURCE_INVENTORY_PARITY_KEYS = {
    "schema_version",
    "artifact_type",
    "source",
    "allowed_dispositions",
    "summary",
    "files",
}
_SOURCE_INVENTORY_PARITY_SOURCE_KEYS = {
    "id",
    "repository",
    "path",
    "pinned",
    "current",
    "retrieved_on",
}
_SOURCE_INVENTORY_PARITY_SUMMARY_KEYS = {
    "A",
    "B",
    "C",
    "pinned_files",
    "current_files",
}
_SKILL_DISPOSITIONS = {
    "direct-port",
    "alias-consolidation",
    "native-kiro-replacement",
    "excluded",
}
_SKILL_RESOURCE_HANDLING = {
    "semantic-source",
    "helper-semantics-only",
    "runtime-specific-exclusion",
}
_TRANSITION_KEYS = {"prior", "new", "inventory_sha256", "dispositions"}
_PROPOSAL_KEYS = {*_TRANSITION_KEYS, "source_id"}
_DISPOSITION_KEYS = {"path", "disposition", "rationale"}
_REPOSITORY = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9_.-]{0,98}[A-Za-z0-9])?/"
    r"[A-Za-z0-9](?:[A-Za-z0-9_.-]{0,98}[A-Za-z0-9])?$"
)
_SOURCE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_NONSEMANTIC_IMAGE_PATH = re.compile(r"^assets/[a-z0-9][a-z0-9_-]{0,127}\.(?:png|jpe?g|gif|webp)$")
_UNIFIED_HUNK = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@(?: .*)?$"
)

FetchJSON = Callable[[str, str | None, float], Any]


class UpstreamError(ValueError):
    """Raised when an upstream manifest or remote identity is unsafe or malformed."""


@dataclass(frozen=True, slots=True)
class UpstreamSource:
    """One immutable source pin and the branch/ref used to detect later work."""

    source_id: str
    repository: str
    path: str
    ref: str
    commit: str
    subtree_sha: str
    provenance_path: str
    parity_path: str


@dataclass(frozen=True, slots=True)
class UpstreamManifest:
    """Validated manifest content with its project-relative source path."""

    path: str
    review_ledger_path: str
    sources: tuple[UpstreamSource, ...]


@dataclass(frozen=True, slots=True)
class ReviewDisposition:
    """One reviewed semantic disposition for one exact changed path."""

    path: str
    disposition: str
    rationale: str


@dataclass(frozen=True, slots=True)
class _UnifiedHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReviewTransition:
    """One append-only, content-addressed reviewed upstream transition."""

    prior_commit: str
    prior_subtree_sha: str
    new_commit: str
    new_subtree_sha: str
    inventory_sha256: str
    dispositions: tuple[ReviewDisposition, ...]


@dataclass(frozen=True, slots=True)
class UpstreamReview:
    """Review chain for one manifest source."""

    source_id: str
    repository: str
    path: str
    provenance_path: str
    parity_path: str
    genesis_commit: str
    genesis_subtree_sha: str
    transitions: tuple[ReviewTransition, ...]


@dataclass(frozen=True, slots=True)
class UpstreamReviewLedger:
    """Validated review ledger and its project-relative path."""

    path: str
    sources: tuple[UpstreamReview, ...]


class _RejectRedirects(HTTPRedirectHandler):
    """Prevent Authorization from following an API redirect to another origin."""

    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        del req, fp, code, msg, headers, newurl
        raise UpstreamError("GitHub API redirects are not permitted")


def _build_opener() -> OpenerDirector:
    """Build a direct HTTPS opener without ambient proxy or redirect behavior."""

    return build_opener(ProxyHandler({}), _RejectRedirects())


def load_upstream_manifest(
    root: Path,
    manifest: Path = DEFAULT_MANIFEST,
) -> UpstreamManifest:
    """Load one strict project-contained upstream manifest without following symlinks."""

    project_root = root.resolve()
    try:
        path = workspace_path(project_root, manifest)
    except WorkspacePathError as exc:
        raise UpstreamError(str(exc)) from exc
    if not path.is_file():
        raise UpstreamError(f"upstream manifest is missing or not a file: {path}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise UpstreamError(f"unable to read upstream manifest: {path}") from exc
    if len(raw) > MAX_MANIFEST_BYTES:
        raise UpstreamError(
            f"upstream manifest exceeds the {MAX_MANIFEST_BYTES}-byte limit: {path}"
        )
    document = _decode_json(raw, context="upstream manifest")
    if not isinstance(document, dict):
        raise UpstreamError("upstream manifest must be a JSON object")
    _require_exact_keys(
        document,
        {"schema_version", "review_ledger_path", "sources"},
        "upstream manifest",
    )
    if type(document["schema_version"]) is not int:
        raise UpstreamError("upstream manifest schema_version must be an integer")
    if document["schema_version"] != UPSTREAM_SCHEMA_VERSION:
        raise UpstreamError(
            f"unsupported upstream manifest schema_version: {document['schema_version']!r}"
        )
    raw_sources = document["sources"]
    if not isinstance(raw_sources, list) or not 1 <= len(raw_sources) <= MAX_SOURCES:
        raise UpstreamError(
            f"upstream manifest sources must contain between 1 and {MAX_SOURCES} entries"
        )

    sources = tuple(
        _parse_source(project_root, value, index=index) for index, value in enumerate(raw_sources)
    )
    identifiers = [source.source_id for source in sources]
    if len(identifiers) != len(set(identifiers)):
        raise UpstreamError("upstream manifest source ids must be unique")
    review_ledger_path = _require_string(
        document,
        "review_ledger_path",
        "upstream manifest",
    )
    _validate_posix_relative(
        review_ledger_path,
        context="upstream manifest review_ledger_path",
        max_length=512,
    )
    if not review_ledger_path.endswith(".json"):
        raise UpstreamError("upstream manifest review_ledger_path must identify a JSON file")
    try:
        workspace_path(project_root, Path(review_ledger_path))
    except WorkspacePathError as exc:
        raise UpstreamError(str(exc)) from exc
    return UpstreamManifest(
        path=path.relative_to(project_root).as_posix(),
        review_ledger_path=review_ledger_path,
        sources=sources,
    )


def load_upstream_review_ledger(
    root: Path,
    manifest: UpstreamManifest,
) -> UpstreamReviewLedger:
    """Load and cross-bind the append-only reviewed-transition ledger."""

    project_root = root.resolve()
    try:
        path = workspace_path(project_root, Path(manifest.review_ledger_path))
    except WorkspacePathError as exc:
        raise UpstreamError(str(exc)) from exc
    if not path.is_file():
        raise UpstreamError(f"upstream review ledger is missing or not a file: {path}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise UpstreamError(f"unable to read upstream review ledger: {path}") from exc
    if len(raw) > MAX_REVIEW_LEDGER_BYTES:
        raise UpstreamError(
            f"upstream review ledger exceeds the {MAX_REVIEW_LEDGER_BYTES}-byte limit: {path}"
        )
    document = _decode_json(raw, context="upstream review ledger")
    if not isinstance(document, dict):
        raise UpstreamError("upstream review ledger must be a JSON object")
    _require_exact_keys(document, {"schema_version", "sources"}, "upstream review ledger")
    if type(document["schema_version"]) is not int:
        raise UpstreamError("upstream review ledger schema_version must be an integer")
    if document["schema_version"] != UPSTREAM_REVIEW_SCHEMA_VERSION:
        raise UpstreamError(
            f"unsupported upstream review ledger schema_version: {document['schema_version']!r}"
        )
    raw_sources = document["sources"]
    if not isinstance(raw_sources, list) or len(raw_sources) != len(manifest.sources):
        raise UpstreamError(
            "upstream review ledger must contain exactly one entry for every manifest source"
        )
    manifest_sources = {source.source_id: source for source in manifest.sources}
    reviews: list[UpstreamReview] = []
    for index, value in enumerate(raw_sources):
        if not isinstance(value, dict):
            raise UpstreamError(f"upstream review source {index} must be a JSON object")
        source_id = value.get("id")
        if type(source_id) is not str or source_id not in manifest_sources:
            raise UpstreamError(
                f"upstream review source {index} does not match a manifest source id"
            )
        reviews.append(
            _parse_review_source(
                value,
                manifest_source=manifest_sources[source_id],
                index=index,
            )
        )
    review_ids = [review.source_id for review in reviews]
    if len(review_ids) != len(set(review_ids)) or set(review_ids) != set(manifest_sources):
        raise UpstreamError(
            "upstream review ledger source ids must uniquely match the manifest sources"
        )
    return UpstreamReviewLedger(
        path=path.relative_to(project_root).as_posix(),
        sources=tuple(reviews),
    )


def _parse_review_source(
    value: dict[str, Any],
    *,
    manifest_source: UpstreamSource,
    index: int,
) -> UpstreamReview:
    context = f"upstream review source {index}"
    _require_exact_keys(value, _LEDGER_SOURCE_KEYS, context)
    for key, expected in (
        ("id", manifest_source.source_id),
        ("repository", manifest_source.repository),
        ("path", manifest_source.path),
        ("provenance_path", manifest_source.provenance_path),
        ("parity_path", manifest_source.parity_path),
    ):
        actual = _require_string(value, key, context)
        if actual != expected:
            raise UpstreamError(f"{context} {key} does not match the manifest source")

    genesis_commit, genesis_subtree = _parse_review_identity(
        value["genesis"],
        context=f"{context} genesis",
    )
    raw_transitions = value["transitions"]
    if not isinstance(raw_transitions, list) or len(raw_transitions) > MAX_REVIEW_TRANSITIONS:
        raise UpstreamError(
            f"{context} transitions must be a list of at most {MAX_REVIEW_TRANSITIONS} entries"
        )
    transitions: list[ReviewTransition] = []
    prior_commit = genesis_commit
    prior_subtree = genesis_subtree
    for transition_index, raw_transition in enumerate(raw_transitions):
        transition = _parse_review_transition(
            raw_transition,
            context=f"{context} transition {transition_index}",
        )
        if transition.prior_commit != prior_commit or transition.prior_subtree_sha != prior_subtree:
            raise UpstreamError(f"{context} transition chain is stale or non-contiguous")
        if (
            transition.new_commit == transition.prior_commit
            and transition.new_subtree_sha == transition.prior_subtree_sha
        ):
            raise UpstreamError(f"{context} transition must advance its identity")
        transitions.append(transition)
        prior_commit = transition.new_commit
        prior_subtree = transition.new_subtree_sha

    if prior_commit != manifest_source.commit or prior_subtree != manifest_source.subtree_sha:
        raise UpstreamError(
            f"{context} reviewed tip does not match the manifest pin; "
            "pin-only advances are rejected"
        )
    return UpstreamReview(
        source_id=manifest_source.source_id,
        repository=manifest_source.repository,
        path=manifest_source.path,
        provenance_path=manifest_source.provenance_path,
        parity_path=manifest_source.parity_path,
        genesis_commit=genesis_commit,
        genesis_subtree_sha=genesis_subtree,
        transitions=tuple(transitions),
    )


def _parse_review_identity(value: Any, *, context: str) -> tuple[str, str]:
    if not isinstance(value, dict):
        raise UpstreamError(f"{context} must be a JSON object")
    _require_exact_keys(value, _IDENTITY_KEYS, context)
    commit = _require_string(value, "commit", context)
    subtree_sha = _require_string(value, "subtree_sha", context)
    if not _FULL_SHA.fullmatch(commit) or not _FULL_SHA.fullmatch(subtree_sha):
        raise UpstreamError(f"{context} values must be full lowercase Git SHAs")
    return commit, subtree_sha


def _parse_review_transition(value: Any, *, context: str) -> ReviewTransition:
    if not isinstance(value, dict):
        raise UpstreamError(f"{context} must be a JSON object")
    _require_exact_keys(value, _TRANSITION_KEYS, context)
    prior_commit, prior_subtree = _parse_review_identity(
        value["prior"],
        context=f"{context} prior",
    )
    new_commit, new_subtree = _parse_review_identity(
        value["new"],
        context=f"{context} new",
    )
    inventory_sha256 = _require_string(value, "inventory_sha256", context)
    if not re.fullmatch(r"[0-9a-f]{64}", inventory_sha256):
        raise UpstreamError(f"{context} inventory_sha256 must be a lowercase SHA-256")
    raw_dispositions = value["dispositions"]
    if not isinstance(raw_dispositions, list) or len(raw_dispositions) > MAX_COMPARE_FILES:
        raise UpstreamError(
            f"{context} dispositions must be a list of at most {MAX_COMPARE_FILES} entries"
        )
    dispositions = tuple(
        _parse_review_disposition(item, context=f"{context} disposition {item_index}")
        for item_index, item in enumerate(raw_dispositions)
    )
    paths = [item.path for item in dispositions]
    if len(paths) != len(set(paths)):
        raise UpstreamError(f"{context} dispositions contain duplicate paths")
    return ReviewTransition(
        prior_commit=prior_commit,
        prior_subtree_sha=prior_subtree,
        new_commit=new_commit,
        new_subtree_sha=new_subtree,
        inventory_sha256=inventory_sha256,
        dispositions=dispositions,
    )


def _parse_acceptance_proposal(value: Any) -> tuple[str, ReviewTransition]:
    """Parse one source-bound proposal without adding source identity to ledger entries."""

    context = "upstream acceptance proposal"
    if not isinstance(value, dict):
        raise UpstreamError(f"{context} must be a JSON object")
    _require_exact_keys(value, _PROPOSAL_KEYS, context)
    source_id = _require_string(value, "source_id", context)
    if len(source_id) > 64 or not _SOURCE_ID.fullmatch(source_id):
        raise UpstreamError(f"{context} source_id must be a lowercase hyphenated identifier")
    transition = _parse_review_transition(
        {key: value[key] for key in _TRANSITION_KEYS},
        context=context,
    )
    return source_id, transition


def _parse_review_disposition(value: Any, *, context: str) -> ReviewDisposition:
    if not isinstance(value, dict):
        raise UpstreamError(f"{context} must be a JSON object")
    _require_exact_keys(value, _DISPOSITION_KEYS, context)
    path = _require_string(value, "path", context)
    _validate_posix_relative(path, context=f"{context} path", max_length=1024)
    disposition = _require_string(value, "disposition", context)
    if disposition not in {"A", "B", "C"}:
        raise UpstreamError(f"{context} disposition must be A, B, or C")
    rationale = _require_string(value, "rationale", context)
    if rationale.strip() != rationale or len(rationale.encode("utf-8")) > MAX_RATIONALE_BYTES:
        raise UpstreamError(
            f"{context} rationale must be trimmed and at most {MAX_RATIONALE_BYTES} bytes"
        )
    return ReviewDisposition(path=path, disposition=disposition, rationale=rationale)


def check_upstreams(
    root: Path,
    *,
    manifest: Path = DEFAULT_MANIFEST,
    power_root: Path | None = None,
    source_id: str | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    fetch_json: FetchJSON | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Reprove every pin and report current ref drift without executing upstream content."""

    return _check_upstreams(
        root,
        manifest=manifest,
        power_root=power_root,
        source_id=source_id,
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
        environ=environ,
        provenance_tail=None,
    )


def _check_upstreams(
    root: Path,
    *,
    manifest: Path,
    power_root: Path | None,
    source_id: str | None,
    timeout_seconds: float,
    fetch_json: FetchJSON | None,
    environ: Mapping[str, str] | None,
    provenance_tail: tuple[str, ReviewTransition] | None,
) -> dict[str, Any]:
    """Internal checker with a proposal-bound provenance tail for acceptance preflight."""

    project_root = root.resolve()
    if not project_root.is_dir():
        raise UpstreamError(f"project root does not exist: {project_root}")
    timeout = _validated_timeout(timeout_seconds)
    token = _github_token(os.environ if environ is None else environ)
    parsed = load_upstream_manifest(project_root, manifest)
    review_ledger = load_upstream_review_ledger(project_root, parsed)
    if source_id is not None:
        if len(source_id) > 64 or not _SOURCE_ID.fullmatch(source_id):
            raise UpstreamError("upstream source_id must be a lowercase hyphenated identifier")
        selected_sources = tuple(
            source for source in parsed.sources if source.source_id == source_id
        )
        if not selected_sources:
            raise UpstreamError(f"upstream source_id is not present in the manifest: {source_id}")
    else:
        selected_sources = parsed.sources
    if provenance_tail is not None and provenance_tail[0] not in {
        source.source_id for source in selected_sources
    }:
        raise UpstreamError("upstream acceptance preproof source is not selected")
    reviews = {review.source_id: review for review in review_ledger.sources}
    raw_fetch = _fetch_json if fetch_json is None else fetch_json
    deadline = time.monotonic() + timeout

    def fetch(url: str, request_token: str | None, _: float) -> Any:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise UpstreamError("upstream network time budget was exhausted")
        return raw_fetch(url, request_token, remaining)

    results: list[dict[str, Any]] = []
    blob_cache: dict[str, bytes] = {}
    for source in selected_sources:
        review = reviews[source.source_id]
        expected_markers = review.transitions
        if provenance_tail is not None and provenance_tail[0] == source.source_id:
            expected_markers = (*expected_markers, provenance_tail[1])
        _require_provenance_review_markers(
            project_root,
            source,
            expected_markers,
            genesis_commit=review.genesis_commit,
            genesis_subtree_sha=review.genesis_subtree_sha,
        )
        pinned_commit, pinned_root_tree = _commit_identity(
            source.repository,
            source.commit,
            token=token,
            timeout_seconds=timeout,
            fetch_json=fetch,
        )
        pinned_subtree = _subtree_identity(
            source.repository,
            pinned_root_tree,
            source.path,
            token=token,
            timeout_seconds=timeout,
            fetch_json=fetch,
        )
        current_commit, current_root_tree = _commit_identity(
            source.repository,
            source.ref,
            token=token,
            timeout_seconds=timeout,
            fetch_json=fetch,
        )
        current_subtree = _subtree_identity(
            source.repository,
            current_root_tree,
            source.path,
            token=token,
            timeout_seconds=timeout,
            fetch_json=fetch,
        )
        current_inventory: dict[str, Any] = {}
        comparison = _compare_inventory(
            source,
            base_commit=source.commit,
            base_subtree=pinned_subtree,
            head_commit=current_commit,
            head_subtree=current_subtree,
            token=token,
            timeout_seconds=timeout,
            fetch_json=fetch,
            blob_cache=blob_cache,
            inventory_capture=current_inventory,
        )
        reviewed_inventory: dict[str, Any] = {}
        review_reproof = _reprove_review_transitions(
            source,
            review,
            token=token,
            timeout_seconds=timeout,
            fetch_json=fetch,
            blob_cache=blob_cache,
            latest_inventory_capture=reviewed_inventory,
        )
        source_parity = _source_parity_status(
            project_root,
            source=source,
            review=review,
            current_commit=current_commit,
            current_subtree=current_subtree,
            current_inventory=current_inventory,
            reviewed_inventory=reviewed_inventory,
        )
        pin_reproof_ok = pinned_commit == source.commit and pinned_subtree == source.subtree_sha
        drift = current_commit != source.commit or current_subtree != source.subtree_sha
        results.append(
            {
                "ok": pin_reproof_ok and not drift and source_parity["ok"],
                "id": source.source_id,
                "repository": source.repository,
                "path": source.path,
                "ref": source.ref,
                "provenance_path": source.provenance_path,
                "parity_path": source.parity_path,
                "pinned": {
                    "commit": source.commit,
                    "subtree_sha": source.subtree_sha,
                },
                "pinned_reproof": {
                    "ok": pin_reproof_ok,
                    "commit": pinned_commit,
                    "subtree_sha": pinned_subtree,
                },
                "current": {
                    "commit": current_commit,
                    "subtree_sha": current_subtree,
                },
                "drift": drift,
                "comparison": comparison,
                "review_reproof": review_reproof,
                "source_parity": source_parity,
            }
        )

    payload: dict[str, Any] = {
        "ok": all(result["ok"] for result in results),
        "schema_version": UPSTREAM_SCHEMA_VERSION,
        "manifest": parsed.path,
        "review_ledger": review_ledger.path,
        "selected_source_id": source_id,
        "network_boundary": GITHUB_API_ORIGIN,
        "sources": results,
    }
    if power_root is not None:
        preview = bootstrap_project(
            project_root,
            power_root=power_root,
            dry_run=True,
            update_managed=True,
        )
        parity = _generated_parity(preview)
        payload["bootstrap_preview"] = preview.to_dict()
        payload["generated_parity"] = parity
        payload["ok"] = payload["ok"] and parity["ok"]
    return payload


def accept_upstream(
    root: Path,
    *,
    expected_head: str,
    manifest: Path = DEFAULT_MANIFEST,
    power_root: Path,
    proposal: Path = DEFAULT_PROPOSAL,
    dry_run: bool = False,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    fetch_json: FetchJSON | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Accept one freshly re-proved review proposal into the ledger and manifest."""

    project_root = root.resolve()
    if not project_root.is_dir():
        raise UpstreamError(f"project root does not exist: {project_root}")
    if manifest != DEFAULT_MANIFEST:
        raise UpstreamError(f"upstream accept requires --manifest {DEFAULT_MANIFEST.as_posix()}")
    if proposal != DEFAULT_PROPOSAL:
        raise UpstreamError(f"upstream accept requires --proposal {DEFAULT_PROPOSAL.as_posix()}")
    if not power_root.is_absolute():
        _validate_posix_relative(
            power_root.as_posix(),
            context="upstream accept power_root",
            max_length=512,
        )
    try:
        canonical_power_root = workspace_path(project_root, power_root)
        expected_power_root = workspace_path(project_root, DEFAULT_POWER_ROOT)
    except WorkspacePathError as exc:
        raise UpstreamError(str(exc)) from exc
    if canonical_power_root != expected_power_root:
        raise UpstreamError(
            f"upstream accept requires --power-root {DEFAULT_POWER_ROOT.as_posix()}"
        )
    if not _FULL_SHA.fullmatch(expected_head):
        raise UpstreamError("expected_head must be a full lowercase Git SHA")
    try:
        proposal_path = workspace_path(project_root, proposal)
    except WorkspacePathError as exc:
        raise UpstreamError(str(exc)) from exc
    with _accept_locked(project_root):
        _validate_accept_directory(project_root)
        recovered_source_id = _recover_accept_transaction(
            project_root,
            expected_head=expected_head,
        )
        if recovered_source_id is not None:
            try:
                final = check_upstreams(
                    project_root,
                    manifest=manifest,
                    power_root=canonical_power_root,
                    source_id=recovered_source_id,
                    timeout_seconds=timeout_seconds,
                    fetch_json=fetch_json,
                    environ=environ,
                )
                if not _recovered_acceptance_is_valid(
                    final,
                    expected_head=expected_head,
                    source_id=recovered_source_id,
                ):
                    raise UpstreamError("recovered upstream acceptance did not pass final reproof")
            except BaseException:
                _rollback_accept_transaction(project_root)
                _cleanup_acceptance_inputs(project_root, proposal_path)
                raise
            _cleanup_acceptance_inputs(project_root, proposal_path)
            return {
                "ok": True,
                "accepted": True,
                "dry_run": False,
                "recovered": True,
                "source_id": recovered_source_id,
                "expected_head": expected_head,
                "final": final,
            }

        if not proposal_path.is_file():
            raise UpstreamError(
                f"upstream acceptance proposal is missing or not a file: {proposal_path}"
            )
        raw_proposal = _read_json_path(
            proposal_path,
            context="upstream acceptance proposal",
            max_bytes=MAX_PROPOSAL_BYTES,
        )
        proposal_source_id, transition = _parse_acceptance_proposal(raw_proposal)
        preflight_manifest = load_upstream_manifest(project_root, manifest)
        preflight_sources = {source.source_id: source for source in preflight_manifest.sources}
        try:
            preflight_source = preflight_sources[proposal_source_id]
        except KeyError as exc:
            raise UpstreamError(
                "upstream acceptance proposal source_id is not present in the manifest"
            ) from exc
        if (
            transition.prior_commit != preflight_source.commit
            or transition.prior_subtree_sha != preflight_source.subtree_sha
        ):
            raise UpstreamError(
                "upstream acceptance proposal prior identity is stale or already applied"
            )

        proof = _check_upstreams(
            project_root,
            manifest=manifest,
            power_root=canonical_power_root,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
            environ=environ,
            source_id=None,
            provenance_tail=(proposal_source_id, transition),
        )
        if not proof.get("generated_parity", {}).get("ok"):
            raise UpstreamError("upstream accept requires canonical/generated Power parity")
        drift_source_ids = sorted(
            result["id"] for result in proof["sources"] if result["drift"] is True
        )
        if not drift_source_ids:
            raise UpstreamError("upstream accept proposal is stale or already applied")
        if proposal_source_id != drift_source_ids[0]:
            raise UpstreamError(
                "upstream acceptance proposal must select the lexicographically first "
                "drifting source"
            )
        source_result = next(
            result for result in proof["sources"] if result["id"] == proposal_source_id
        )
        if not source_result.get("source_parity", {}).get("candidate_ready"):
            raise UpstreamError(
                "upstream accept requires a complete source-bound candidate parity artifact"
            )
        if not source_result["pinned_reproof"]["ok"]:
            raise UpstreamError("upstream accept requires an exactly re-proved current pin")
        if not source_result["drift"]:
            raise UpstreamError("upstream accept proposal is stale or already applied")
        comparison = source_result["comparison"]
        if not comparison["complete"] or not comparison["fast_forward"]:
            raise UpstreamError("upstream accept requires a complete fast-forward comparison")
        if source_result["current"]["commit"] != expected_head:
            raise UpstreamError("current upstream head does not match --expected-head")

        _bind_proposed_transition(
            transition,
            source_result=source_result,
            expected_head=expected_head,
        )
        parsed_manifest = load_upstream_manifest(project_root, manifest)
        parsed_ledger = load_upstream_review_ledger(project_root, parsed_manifest)
        manifest_index = next(
            index
            for index, source in enumerate(parsed_manifest.sources)
            if source.source_id == proposal_source_id
        )
        ledger_index = next(
            index
            for index, review in enumerate(parsed_ledger.sources)
            if review.source_id == proposal_source_id
        )
        selected_manifest_source = parsed_manifest.sources[manifest_index]
        selected_review = parsed_ledger.sources[ledger_index]
        if len(selected_review.transitions) >= MAX_REVIEW_TRANSITIONS:
            raise UpstreamError(
                f"upstream review ledger already has the {MAX_REVIEW_TRANSITIONS}-transition limit"
            )
        _require_provenance_review_markers(
            project_root,
            selected_manifest_source,
            (*selected_review.transitions, transition),
            genesis_commit=selected_review.genesis_commit,
            genesis_subtree_sha=selected_review.genesis_subtree_sha,
        )
        normalized_transition = _transition_document(transition)
        manifest_path = workspace_path(project_root, manifest)
        ledger_path = workspace_path(project_root, Path(parsed_ledger.path))
        manifest_document = _read_json_path(
            manifest_path,
            context="upstream manifest",
            max_bytes=MAX_MANIFEST_BYTES,
        )
        ledger_document = _read_json_path(
            ledger_path,
            context="upstream review ledger",
            max_bytes=MAX_REVIEW_LEDGER_BYTES,
        )
        assert isinstance(manifest_document, dict)
        assert isinstance(ledger_document, dict)
        next_manifest = json.loads(json.dumps(manifest_document))
        next_ledger = json.loads(json.dumps(ledger_document))
        next_manifest["sources"][manifest_index]["commit"] = transition.new_commit
        next_manifest["sources"][manifest_index]["subtree_sha"] = transition.new_subtree_sha
        next_ledger["sources"][ledger_index]["transitions"].append(normalized_transition)
        if len(_canonical_json_bytes(next_manifest)) > MAX_MANIFEST_BYTES:
            raise UpstreamError("accepted upstream manifest would exceed its byte limit")
        if len(_canonical_json_bytes(next_ledger)) > MAX_REVIEW_LEDGER_BYTES:
            raise UpstreamError("accepted upstream review ledger would exceed its byte limit")

        candidate = {
            "ok": True,
            "accepted": not dry_run,
            "dry_run": dry_run,
            "recovered": False,
            "source_id": source_result["id"],
            "expected_head": expected_head,
            "inventory_sha256": transition.inventory_sha256,
            "path_count": len(transition.dispositions),
            "manifest": parsed_manifest.path,
            "review_ledger": parsed_ledger.path,
        }
        if dry_run:
            return candidate

        _write_accept_transaction(
            project_root,
            manifest_path=manifest_path,
            ledger_path=ledger_path,
            before_manifest=manifest_document,
            before_ledger=ledger_document,
            after_manifest=next_manifest,
            after_ledger=next_ledger,
            source_id=proposal_source_id,
            expected_head=expected_head,
        )
        _cleanup_acceptance_inputs(project_root, proposal_path)
        return candidate


def _recovered_acceptance_is_valid(
    payload: dict[str, Any],
    *,
    expected_head: str,
    source_id: str,
) -> bool:
    """Validate the committed transition while permitting newer fast-forward drift."""

    try:
        if (
            payload.get("schema_version") != UPSTREAM_SCHEMA_VERSION
            or payload.get("manifest") != DEFAULT_MANIFEST.as_posix()
            or payload.get("review_ledger") != "maintenance/upstream-reviews.json"
            or payload.get("generated_parity", {}).get("ok") is not True
        ):
            return False
        sources = payload["sources"]
        if not isinstance(sources, list) or len(sources) != 1:
            return False
        source = sources[0]
        if source.get("id") != source_id or source.get("source_parity", {}).get("ok") is not True:
            return False
        pinned = source["pinned"]
        pinned_reproof = source["pinned_reproof"]
        current = source["current"]
        comparison = source["comparison"]
        review_reproof = source["review_reproof"]
        drift = source["drift"]
        transition_count = review_reproof["transition_count"]
        transitions = review_reproof["transitions"]
        if type(drift) is not bool or type(transition_count) is not int or transition_count < 1:
            return False
        if (
            pinned.get("commit") != expected_head
            or pinned_reproof.get("ok") is not True
            or pinned_reproof.get("commit") != pinned.get("commit")
            or pinned_reproof.get("subtree_sha") != pinned.get("subtree_sha")
            or review_reproof.get("ok") is not True
            or review_reproof.get("tip") != pinned
            or review_reproof.get("remote_transition_indices") != [transition_count - 1]
            or not isinstance(transitions, list)
            or len(transitions) != 1
            or transitions[0].get("index") != transition_count - 1
            or transitions[0].get("new") != pinned
        ):
            return False
        if (
            comparison.get("complete") is not True
            or comparison.get("fast_forward") is not True
            or comparison.get("base_commit") != expected_head
            or comparison.get("merge_base_commit") != expected_head
            or comparison.get("head_commit") != current.get("commit")
        ):
            return False
        expected_drift = current != pinned
        return (
            drift is expected_drift
            and source.get("ok") is (not drift)
            and payload.get("ok") is (not drift)
        )
    except (AttributeError, IndexError, KeyError, TypeError):
        return False


def _bind_proposed_transition(
    transition: ReviewTransition,
    *,
    source_result: dict[str, Any],
    expected_head: str,
) -> None:
    pinned = source_result["pinned"]
    current = source_result["current"]
    comparison = source_result["comparison"]
    if (
        transition.prior_commit != pinned["commit"]
        or transition.prior_subtree_sha != pinned["subtree_sha"]
    ):
        raise UpstreamError("upstream acceptance proposal prior identity is stale")
    if transition.new_commit != expected_head or transition.new_commit != current["commit"]:
        raise UpstreamError("upstream acceptance proposal new commit is not the expected head")
    if transition.new_subtree_sha != current["subtree_sha"]:
        raise UpstreamError("upstream acceptance proposal new subtree is not the current subtree")
    if transition.inventory_sha256 != comparison["inventory_sha256"]:
        raise UpstreamError("upstream acceptance proposal inventory digest does not match reproof")
    proposed_paths = sorted(item.path for item in transition.dispositions)
    if proposed_paths != comparison["paths"]:
        raise UpstreamError(
            "upstream acceptance proposal dispositions do not exactly match comparison paths"
        )
    _require_unavailable_binary_exclusions(
        transition,
        comparison,
        context="upstream acceptance proposal",
    )


def _require_unavailable_binary_exclusions(
    transition: ReviewTransition,
    comparison: dict[str, Any],
    *,
    context: str,
) -> None:
    dispositions = {item.path: item.disposition for item in transition.dispositions}
    unavailable = comparison["review_constraints"]["unavailable_binary_paths"]
    invalid = [path for path in unavailable if dispositions.get(path) != "B"]
    if invalid:
        raise UpstreamError(
            f"{context} must assign disposition B to unavailable binary paths: "
            + ", ".join(invalid)
        )


def _transition_document(transition: ReviewTransition) -> dict[str, Any]:
    return {
        "prior": {
            "commit": transition.prior_commit,
            "subtree_sha": transition.prior_subtree_sha,
        },
        "new": {
            "commit": transition.new_commit,
            "subtree_sha": transition.new_subtree_sha,
        },
        "inventory_sha256": transition.inventory_sha256,
        "dispositions": [
            {
                "path": item.path,
                "disposition": item.disposition,
                "rationale": item.rationale,
            }
            for item in sorted(transition.dispositions, key=lambda disposition: disposition.path)
        ],
    }


def _require_provenance_review_markers(
    root: Path,
    source: UpstreamSource,
    transitions: tuple[ReviewTransition, ...],
    *,
    genesis_commit: str,
    genesis_subtree_sha: str,
) -> None:
    provenance_path = workspace_path(root, Path(source.provenance_path))
    try:
        raw = provenance_path.read_bytes()
    except OSError as exc:
        raise UpstreamError(f"unable to read upstream provenance: {provenance_path}") from exc
    if len(raw) > MAX_PROVENANCE_BYTES:
        raise UpstreamError(f"upstream provenance exceeds the {MAX_PROVENANCE_BYTES}-byte limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UpstreamError("upstream provenance is not valid UTF-8") from exc
    expected: list[tuple[str, dict[str, Any]]] = [
        (
            "genesis",
            {
                "source_id": source.source_id,
                "repository": source.repository,
                "path": source.path,
                "commit": genesis_commit,
                "subtree_sha": genesis_subtree_sha,
            },
        ),
        *[
            (
                "review",
                {
                    "source_id": source.source_id,
                    "repository": source.repository,
                    "path": source.path,
                    "prior": {
                        "commit": transition.prior_commit,
                        "subtree_sha": transition.prior_subtree_sha,
                    },
                    "new": {
                        "commit": transition.new_commit,
                        "subtree_sha": transition.new_subtree_sha,
                    },
                    "inventory_sha256": transition.inventory_sha256,
                },
            )
            for transition in transitions
        ],
    ]
    prefixes = {
        "genesis": "<!-- pk-stack-upstream-genesis: ",
        "review": "<!-- pk-stack-upstream-review: ",
    }
    suffix = " -->"
    markers: list[tuple[str, dict[str, Any]]] = []
    for line in text.splitlines():
        kinds = [kind for kind in prefixes if f"pk-stack-upstream-{kind}:" in line]
        if not kinds:
            continue
        if len(kinds) != 1:
            raise UpstreamError("upstream provenance marker is malformed")
        kind = kinds[0]
        prefix = prefixes[kind]
        if not line.startswith(prefix) or not line.endswith(suffix) or len(line) > 4096:
            raise UpstreamError(f"upstream provenance {kind} marker is malformed")
        payload = _decode_json(
            line[len(prefix) : -len(suffix)].encode("utf-8"),
            context=f"upstream provenance {kind} marker",
        )
        if not isinstance(payload, dict):
            raise UpstreamError(f"upstream provenance {kind} marker must contain a JSON object")
        context = f"upstream provenance {kind} marker"
        if kind == "genesis":
            _require_exact_keys(
                payload,
                {"source_id", "repository", "path", "commit", "subtree_sha"},
                context,
            )
            commit = _require_string(payload, "commit", context)
            subtree_sha = _require_string(payload, "subtree_sha", context)
            if not _FULL_SHA.fullmatch(commit) or not _FULL_SHA.fullmatch(subtree_sha):
                raise UpstreamError(
                    "upstream provenance genesis marker identities must be full lowercase Git SHAs"
                )
        else:
            _require_exact_keys(
                payload,
                {"source_id", "repository", "path", "prior", "new", "inventory_sha256"},
                context,
            )
            _parse_review_identity(payload["prior"], context="provenance marker prior")
            _parse_review_identity(payload["new"], context="provenance marker new")
            digest = _require_string(payload, "inventory_sha256", context)
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise UpstreamError("upstream provenance review marker inventory_sha256 is invalid")
        _require_string(payload, "source_id", context)
        _require_string(payload, "repository", context)
        _require_string(payload, "path", context)
        canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        if line != f"{prefix}{canonical}{suffix}":
            raise UpstreamError(f"upstream provenance {kind} marker is not canonical")
        markers.append((kind, payload))
    if markers != expected:
        raise UpstreamError(
            "upstream provenance review markers do not exactly match the required genesis "
            "marker followed by the ordered review ledger"
        )


def _parse_source(root: Path, value: Any, *, index: int) -> UpstreamSource:
    context = f"upstream source {index}"
    if not isinstance(value, dict):
        raise UpstreamError(f"{context} must be a JSON object")
    _require_exact_keys(value, _SOURCE_KEYS, context)
    fields = {key: _require_string(value, key, context) for key in _SOURCE_KEYS}

    source_id = fields["id"]
    if len(source_id) > 64 or not _SOURCE_ID.fullmatch(source_id):
        raise UpstreamError(f"{context} id must be a lowercase hyphenated identifier")
    repository = fields["repository"]
    if not _REPOSITORY.fullmatch(repository) or any(
        part in {".", ".."} for part in repository.split("/")
    ):
        raise UpstreamError(f"{context} repository must be a GitHub owner/name pair")
    source_path = fields["path"]
    _validate_posix_relative(source_path, context=f"{context} path", max_length=512)
    _validate_ref(fields["ref"], context=context)
    for key in ("commit", "subtree_sha"):
        if not _FULL_SHA.fullmatch(fields[key]):
            raise UpstreamError(f"{context} {key} must be a full lowercase Git SHA")

    provenance = fields["provenance_path"]
    _validate_posix_relative(provenance, context=f"{context} provenance_path", max_length=512)
    if not provenance.endswith(".md"):
        raise UpstreamError(f"{context} provenance_path must identify a Markdown file")
    try:
        provenance_file = workspace_path(root, Path(provenance))
    except WorkspacePathError as exc:
        raise UpstreamError(str(exc)) from exc
    if not provenance_file.is_file():
        raise UpstreamError(f"{context} provenance_path is missing or not a file: {provenance}")

    parity = fields["parity_path"]
    _validate_posix_relative(parity, context=f"{context} parity_path", max_length=512)
    if not parity.endswith(".json"):
        raise UpstreamError(f"{context} parity_path must identify a JSON file")
    try:
        parity_file = workspace_path(root, Path(parity))
    except WorkspacePathError as exc:
        raise UpstreamError(str(exc)) from exc
    if not parity_file.is_file():
        raise UpstreamError(f"{context} parity_path is missing or not a file: {parity}")

    return UpstreamSource(
        source_id=source_id,
        repository=repository,
        path=source_path,
        ref=fields["ref"],
        commit=fields["commit"],
        subtree_sha=fields["subtree_sha"],
        provenance_path=provenance,
        parity_path=parity,
    )


def _require_exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    actual = set(value)
    if actual == expected:
        return
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    details: list[str] = []
    if missing:
        details.append("missing " + ", ".join(missing))
    if extra:
        details.append("unexpected " + ", ".join(extra))
    raise UpstreamError(f"{context} has invalid fields: {'; '.join(details)}")


def _require_string(value: dict[str, Any], key: str, context: str) -> str:
    item = value[key]
    if type(item) is not str or not item:
        raise UpstreamError(f"{context} {key} must be a non-empty string")
    if any(character in item for character in ("\x00", "\r", "\n")):
        raise UpstreamError(f"{context} {key} contains a control character")
    return item


def _validate_posix_relative(value: str, *, context: str, max_length: int) -> None:
    path = PurePosixPath(value)
    if (
        len(value) > max_length
        or value.startswith("/")
        or "\\" in value
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise UpstreamError(f"{context} must be a normalized relative POSIX path")


def _validate_ref(value: str, *, context: str) -> None:
    forbidden = ("..", "//", "@{", "\\", "~", "^", ":", "?", "*", "[")
    if (
        len(value) > 255
        or value.startswith(("/", "."))
        or value.endswith(("/", "."))
        or any(marker in value for marker in forbidden)
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise UpstreamError(f"{context} ref is not a safe Git ref")


def _validated_timeout(value: float) -> float:
    if type(value) not in {int, float}:
        raise UpstreamError("upstream timeout must be a number")
    timeout = float(value)
    if not math.isfinite(timeout) or not 0 < timeout <= MAX_TIMEOUT_SECONDS:
        raise UpstreamError(
            "upstream timeout must be positive, finite, and at most "
            f"{MAX_TIMEOUT_SECONDS:g} seconds"
        )
    return timeout


def _source_parity_status(
    root: Path,
    *,
    source: UpstreamSource,
    review: UpstreamReview,
    current_commit: str,
    current_subtree: str,
    current_inventory: dict[str, Any],
    reviewed_inventory: dict[str, Any],
) -> dict[str, Any]:
    """Validate one source-scoped parity artifact against exact fetched Git trees."""

    result: dict[str, Any] = {
        "ok": False,
        "candidate_ready": False,
        "artifact_type": "unknown",
        "status": "invalid",
        "path": source.parity_path,
        "errors": [],
        "pinned_resource_count": 0,
        "current_resource_count": 0,
        "classified_resource_count": 0,
    }
    try:
        path = workspace_path(root, Path(source.parity_path))
        if not path.is_file():
            raise UpstreamError(f"upstream source parity artifact is missing or not a file: {path}")
        document = _read_json_path(
            path,
            context="upstream source parity artifact",
            max_bytes=MAX_SOURCE_PARITY_BYTES,
        )
        if not isinstance(document, dict):
            raise UpstreamError("upstream source parity artifact must be a JSON object")
        if set(document) == _SKILL_PARITY_KEYS:
            result["artifact_type"] = "skill-catalog"
            counts, status, candidate_ready = _validate_skill_catalog_parity(
                document,
                source=source,
                review=review,
                current_commit=current_commit,
                current_subtree=current_subtree,
                current_inventory=current_inventory,
                reviewed_inventory=reviewed_inventory,
            )
        elif document.get("artifact_type") == "source-inventory":
            result["artifact_type"] = "source-inventory"
            counts, status, candidate_ready = _validate_source_inventory_parity(
                document,
                source=source,
                review=review,
                current_commit=current_commit,
                current_subtree=current_subtree,
                current_inventory=current_inventory,
                reviewed_inventory=reviewed_inventory,
            )
        else:
            raise UpstreamError("upstream source parity artifact has an unsupported shape")
        result.update(
            {
                "ok": True,
                "candidate_ready": candidate_ready,
                "status": status,
                "errors": [],
                **counts,
            }
        )
    except (OSError, KeyError, TypeError, WorkspacePathError, UpstreamError) as exc:
        result["errors"] = [str(exc)]
    return result


def _validate_skill_catalog_parity(
    document: dict[str, Any],
    *,
    source: UpstreamSource,
    review: UpstreamReview,
    current_commit: str,
    current_subtree: str,
    current_inventory: dict[str, Any],
    reviewed_inventory: dict[str, Any],
) -> tuple[dict[str, int], str, bool]:
    """Validate the historical Cursor-style package catalog for one bound source."""

    _require_exact_keys(document, _SKILL_PARITY_KEYS, "upstream skill parity catalog")
    raw_source = document["source"]
    if not isinstance(raw_source, dict):
        raise UpstreamError("upstream skill parity source must be a JSON object")
    _require_exact_keys(raw_source, _SKILL_PARITY_SOURCE_KEYS, "upstream skill parity source")
    _bind_parity_source(raw_source, source=source, context="upstream skill parity source")
    if raw_source.get("catalog_path") != "skills":
        raise UpstreamError("upstream skill parity catalog_path must be 'skills'")
    _validate_retrieved_on(raw_source.get("retrieved_on"), context="upstream skill parity source")

    matrix_pinned = _skill_parity_identity(raw_source.get("pinned"), "pinned")
    matrix_current = _skill_parity_identity(raw_source.get("current"), "current")
    active = {"commit": source.commit, "pstack_subtree_sha": source.subtree_sha}
    remote = {"commit": current_commit, "pstack_subtree_sha": current_subtree}
    status, candidate_ready, inventory = _resolve_parity_state(
        matrix_pinned,
        matrix_current,
        active=active,
        remote=remote,
        review=review,
        subtree_key="pstack_subtree_sha",
        current_inventory=current_inventory,
        reviewed_inventory=reviewed_inventory,
        context="upstream skill parity",
    )
    expected_pinned = _skill_packages_from_inventory(inventory, revision="pinned")
    expected_current = (
        _skill_packages_from_inventory(inventory, revision="current")
        if candidate_ready or review.transitions
        else expected_pinned
    )
    counts = _validate_skill_parity_document(
        document,
        expected_pinned=expected_pinned,
        expected_current=expected_current,
    )
    return (
        {
            "pinned_resource_count": counts["pinned_resource_count"],
            "current_resource_count": counts["current_resource_count"],
            "classified_resource_count": counts["classified_resource_count"],
        },
        status,
        candidate_ready,
    )


def _bind_parity_source(
    raw_source: dict[str, Any],
    *,
    source: UpstreamSource,
    context: str,
) -> None:
    for key, expected in (
        ("id", source.source_id),
        ("repository", source.repository),
        ("path", source.path),
    ):
        if raw_source.get(key) != expected:
            raise UpstreamError(f"{context} {key} does not match the manifest")


def _validate_retrieved_on(value: Any, *, context: str) -> None:
    if type(value) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise UpstreamError(f"{context} retrieved_on must be an ISO date")


def _resolve_parity_state(
    matrix_pinned: dict[str, str],
    matrix_current: dict[str, str],
    *,
    active: dict[str, str],
    remote: dict[str, str],
    review: UpstreamReview,
    subtree_key: str,
    current_inventory: dict[str, Any],
    reviewed_inventory: dict[str, Any],
    context: str,
) -> tuple[str, bool, dict[str, Any]]:
    if matrix_pinned == active and matrix_current == remote and remote != active:
        return "candidate-ready", True, current_inventory
    if matrix_current == active:
        prior = (
            {
                "commit": review.transitions[-1].prior_commit,
                subtree_key: review.transitions[-1].prior_subtree_sha,
            }
            if review.transitions
            else {"commit": review.genesis_commit, subtree_key: review.genesis_subtree_sha}
        )
        if matrix_pinned != prior:
            raise UpstreamError(f"accepted {context} pinned identity does not match review history")
        inventory = reviewed_inventory if review.transitions else current_inventory
        return "accepted-baseline", False, inventory
    raise UpstreamError(f"{context} identities are stale or do not bind the active review")


def _validate_source_inventory_parity(
    document: dict[str, Any],
    *,
    source: UpstreamSource,
    review: UpstreamReview,
    current_commit: str,
    current_subtree: str,
    current_inventory: dict[str, Any],
    reviewed_inventory: dict[str, Any],
) -> tuple[dict[str, int], str, bool]:
    """Validate a generic file-by-file source inventory and semantic disposition."""

    context = "upstream source inventory parity"
    _require_exact_keys(document, _SOURCE_INVENTORY_PARITY_KEYS, context)
    if document.get("schema_version") != 1 or document.get("artifact_type") != "source-inventory":
        raise UpstreamError(f"{context} has an unsupported schema or artifact type")
    raw_source = document["source"]
    if not isinstance(raw_source, dict):
        raise UpstreamError(f"{context} source must be a JSON object")
    _require_exact_keys(raw_source, _SOURCE_INVENTORY_PARITY_SOURCE_KEYS, f"{context} source")
    _bind_parity_source(raw_source, source=source, context=f"{context} source")
    _validate_retrieved_on(raw_source.get("retrieved_on"), context=f"{context} source")

    matrix_pinned = _source_parity_identity(raw_source.get("pinned"), "pinned")
    matrix_current = _source_parity_identity(raw_source.get("current"), "current")
    active = {"commit": source.commit, "subtree_sha": source.subtree_sha}
    remote = {"commit": current_commit, "subtree_sha": current_subtree}
    status, candidate_ready, inventory = _resolve_parity_state(
        matrix_pinned,
        matrix_current,
        active=active,
        remote=remote,
        review=review,
        subtree_key="subtree_sha",
        current_inventory=current_inventory,
        reviewed_inventory=reviewed_inventory,
        context=context,
    )
    expected_pinned = _inventory_file_identities(inventory, revision="pinned")
    expected_current = (
        _inventory_file_identities(inventory, revision="current")
        if candidate_ready or review.transitions
        else expected_pinned
    )
    counts = _validate_source_inventory_document(
        document,
        expected_pinned=expected_pinned,
        expected_current=expected_current,
    )
    return counts, status, candidate_ready


def _source_parity_identity(value: Any, revision: str) -> dict[str, str]:
    context = f"upstream source parity {revision} identity"
    if not isinstance(value, dict):
        raise UpstreamError(f"{context} must be a JSON object")
    _require_exact_keys(value, _IDENTITY_KEYS, context)
    commit, subtree_sha = _parse_review_identity(value, context=context)
    return {"commit": commit, "subtree_sha": subtree_sha}


def _inventory_file_identities(
    inventory: dict[str, Any],
    *,
    revision: str,
) -> dict[str, tuple[str, str, str, int | None]]:
    raw_files = inventory.get(f"{revision}_files")
    if not isinstance(raw_files, dict):
        raise UpstreamError(f"upstream {revision} source inventory was not captured")
    validated: dict[str, tuple[str, str, str, int | None]] = {}
    for path, identity in raw_files.items():
        if type(path) is not str:
            raise UpstreamError(f"upstream {revision} source inventory path is invalid")
        _validate_posix_relative(
            path,
            context=f"upstream {revision} source inventory path",
            max_length=1024,
        )
        if (
            not isinstance(identity, tuple)
            or len(identity) != 4
            or identity[0] not in {"blob", "commit"}
            or type(identity[1]) is not str
            or not re.fullmatch(r"[0-7]{6}", identity[1])
            or type(identity[2]) is not str
            or not _FULL_SHA.fullmatch(identity[2])
            or (identity[3] is not None and type(identity[3]) is not int)
        ):
            raise UpstreamError(f"upstream {revision} source inventory identity is invalid")
        validated[path] = identity
    return validated


def _validate_source_inventory_document(
    document: dict[str, Any],
    *,
    expected_pinned: dict[str, tuple[str, str, str, int | None]],
    expected_current: dict[str, tuple[str, str, str, int | None]],
) -> dict[str, int]:
    context = "upstream source inventory parity"
    allowed = document.get("allowed_dispositions")
    if not isinstance(allowed, list) or allowed != ["A", "B", "C"]:
        raise UpstreamError(f"{context} dispositions must be the canonical A/B/C order")
    raw_files = document.get("files")
    if not isinstance(raw_files, list):
        raise UpstreamError(f"{context} files must be a list")
    expected_paths = sorted(expected_pinned.keys() | expected_current.keys(), key=str.casefold)
    paths = [item.get("path") for item in raw_files if isinstance(item, dict)]
    if len(paths) != len(raw_files) or paths != expected_paths:
        raise UpstreamError(f"{context} files do not exactly match the remote tree")

    disposition_counts = {value: 0 for value in allowed}
    for index, item in enumerate(raw_files):
        assert isinstance(item, dict)
        item_context = f"{context} file {index}"
        _require_exact_keys(
            item,
            {"path", "pinned", "current", "disposition", "rationale"},
            item_context,
        )
        path = item["path"]
        _validate_posix_relative(path, context=f"{item_context} path", max_length=1024)
        for revision, expected in (
            ("pinned", expected_pinned.get(path)),
            ("current", expected_current.get(path)),
        ):
            _validate_source_inventory_file_identity(
                item[revision],
                expected=expected,
                context=f"{item_context} {revision}",
            )
        disposition = item["disposition"]
        if disposition not in disposition_counts:
            raise UpstreamError(f"{item_context} disposition is invalid")
        rationale = item["rationale"]
        if (
            type(rationale) is not str
            or not rationale
            or rationale != rationale.strip()
            or len(rationale.encode("utf-8")) > MAX_RATIONALE_BYTES
        ):
            raise UpstreamError(f"{item_context} rationale must be specific and bounded")
        disposition_counts[disposition] += 1

    summary = document.get("summary")
    if not isinstance(summary, dict):
        raise UpstreamError(f"{context} summary must be a JSON object")
    _require_exact_keys(summary, _SOURCE_INVENTORY_PARITY_SUMMARY_KEYS, f"{context} summary")
    expected_summary = {
        **disposition_counts,
        "pinned_files": len(expected_pinned),
        "current_files": len(expected_current),
    }
    if summary != expected_summary:
        raise UpstreamError(f"{context} summary is not derived from its inventory")
    return {
        "pinned_resource_count": len(expected_pinned),
        "current_resource_count": len(expected_current),
        "classified_resource_count": len(expected_paths),
    }


def _validate_source_inventory_file_identity(
    value: Any,
    *,
    expected: tuple[str, str, str, int | None] | None,
    context: str,
) -> None:
    if expected is None:
        if value is not None:
            raise UpstreamError(f"{context} identity must be null")
        return
    if not isinstance(value, dict):
        raise UpstreamError(f"{context} identity must be a JSON object")
    _require_exact_keys(value, {"type", "mode", "object_sha", "size"}, f"{context} identity")
    actual = (value["type"], value["mode"], value["object_sha"], value["size"])
    if actual != expected:
        raise UpstreamError(f"{context} identity does not match upstream")


def _skill_parity_identity(value: Any, revision: str) -> dict[str, str]:
    context = f"upstream skill parity {revision} identity"
    if not isinstance(value, dict):
        raise UpstreamError(f"{context} must be a JSON object")
    _require_exact_keys(value, _SKILL_PARITY_IDENTITY_KEYS, context)
    commit = value.get("commit")
    subtree = value.get("pstack_subtree_sha")
    if type(commit) is not str or not _FULL_SHA.fullmatch(commit):
        raise UpstreamError(f"{context} commit must be a full lowercase Git SHA")
    if type(subtree) is not str or not _FULL_SHA.fullmatch(subtree):
        raise UpstreamError(f"{context} pstack_subtree_sha must be a full lowercase Git SHA")
    return {"commit": commit, "pstack_subtree_sha": subtree}


def _skill_packages_from_inventory(
    inventory: dict[str, Any],
    *,
    revision: str,
) -> dict[str, dict[str, Any]]:
    raw_files = inventory.get(f"{revision}_files")
    raw_trees = inventory.get(f"{revision}_trees")
    if not isinstance(raw_files, dict) or not isinstance(raw_trees, dict):
        raise UpstreamError(f"upstream {revision} skill inventory was not captured")
    skill_names = {
        parts[1]
        for path in raw_files
        if len(parts := PurePosixPath(path).parts) == 3
        and parts[0] == "skills"
        and parts[2] == "SKILL.md"
    }
    packages: dict[str, dict[str, Any]] = {}
    for name in sorted(skill_names):
        if not _SOURCE_ID.fullmatch(name):
            raise UpstreamError(f"upstream skill package has an invalid name: {name!r}")
        prefix = f"skills/{name}/"
        files: dict[str, tuple[str, str, str, int]] = {}
        for path, identity in raw_files.items():
            if not path.startswith(prefix):
                continue
            if (
                not isinstance(identity, tuple)
                or len(identity) != 4
                or identity[0] != "blob"
                or identity[1] not in {"100644", "100755"}
                or type(identity[3]) is not int
            ):
                raise UpstreamError(
                    f"upstream skill resource is not a bounded regular blob: {path}"
                )
            relative = path.removeprefix(prefix)
            _validate_posix_relative(
                relative,
                context="upstream skill resource path",
                max_length=1024,
            )
            files[relative] = identity  # type: ignore[assignment]
        tree_sha = raw_trees.get(f"skills/{name}")
        if type(tree_sha) is not str or not _FULL_SHA.fullmatch(tree_sha):
            raise UpstreamError(f"upstream skill package tree is missing for {name!r}")
        packages[name] = {"package_tree_sha": tree_sha, "files": files}
    return packages


def _validate_skill_parity_document(
    document: dict[str, Any],
    *,
    expected_pinned: dict[str, dict[str, Any]],
    expected_current: dict[str, dict[str, Any]],
) -> dict[str, int]:
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1:
        raise UpstreamError("unsupported upstream skill parity schema_version")
    dispositions = document.get("allowed_dispositions")
    if (
        not isinstance(dispositions, list)
        or len(dispositions) != len(set(dispositions))
        or set(dispositions) != _SKILL_DISPOSITIONS
    ):
        raise UpstreamError("upstream skill parity dispositions are not canonical")
    handling_values = document.get("allowed_resource_handling")
    if (
        not isinstance(handling_values, list)
        or len(handling_values) != len(set(handling_values))
        or set(handling_values) != _SKILL_RESOURCE_HANDLING
    ):
        raise UpstreamError("upstream skill parity resource handling values are not canonical")

    raw_pk_only = document.get("pk_only_skills")
    if not isinstance(raw_pk_only, list) or not all(
        type(name) is str and _SOURCE_ID.fullmatch(name) for name in raw_pk_only
    ):
        raise UpstreamError("upstream skill parity PK-only skills are invalid")
    if raw_pk_only != sorted(set(raw_pk_only)):
        raise UpstreamError("upstream skill parity PK-only skills must be sorted and unique")

    raw_skills = document.get("skills")
    if not isinstance(raw_skills, list):
        raise UpstreamError("upstream skill parity skills must be a list")
    names = [entry.get("name") for entry in raw_skills if isinstance(entry, dict)]
    expected_names = sorted(expected_pinned.keys() | expected_current.keys())
    if len(names) != len(raw_skills) or names != expected_names:
        raise UpstreamError(
            "upstream skill parity entries do not exactly match the remote top-level catalog"
        )

    disposition_counts = {name: 0 for name in _SKILL_DISPOSITIONS}
    resource_counts = {name: 0 for name in _SKILL_RESOURCE_HANDLING}
    routed_names: set[str] = set()
    pinned_file_count = 0
    current_file_count = 0
    classified_resources: set[tuple[str, str]] = set()
    for index, entry in enumerate(raw_skills):
        assert isinstance(entry, dict)
        context = f"upstream skill parity entry {index}"
        required = {"name", "pinned", "current", "disposition", "target", "rationale"}
        optional = {"consolidates_to", "safe_alternative"}
        actual_keys = set(entry)
        if not required <= actual_keys or actual_keys - required - optional:
            raise UpstreamError(f"{context} has invalid fields")
        name = entry["name"]
        disposition = entry["disposition"]
        if disposition not in _SKILL_DISPOSITIONS:
            raise UpstreamError(f"{context} has an invalid disposition")
        rationale = entry["rationale"]
        if (
            type(rationale) is not str
            or not rationale
            or rationale != rationale.strip()
            or len(rationale.encode("utf-8")) > MAX_RATIONALE_BYTES
        ):
            raise UpstreamError(f"{context} rationale must be specific and bounded")
        target = entry["target"]
        if disposition == "excluded":
            if target is not None or type(entry.get("safe_alternative")) is not str:
                raise UpstreamError(f"{context} exclusion must name a safe alternative")
        else:
            expected_target = f"skills/{SKILL_ROUTE_ALIASES.get(name, name)}/SKILL.md"
            if target != expected_target:
                raise UpstreamError(f"{context} target must be its canonical Kiro skill")
            # The upstream name remains the provenance identity; the target
            # directory is the Kiro-facing route and may intentionally use an
            # explicit compatibility alias.
            routed_names.add(Path(target).parent.name)
        if disposition == "alias-consolidation":
            if type(entry.get("consolidates_to")) is not str:
                raise UpstreamError(f"{context} alias must name its consolidation")
        elif "consolidates_to" in entry:
            raise UpstreamError(f"{context} unexpectedly names a consolidation")
        disposition_counts[disposition] += 1

        for revision, expected in (
            ("pinned", expected_pinned),
            ("current", expected_current),
        ):
            package = entry[revision]
            expected_package = expected.get(name)
            if expected_package is None:
                if package is not None:
                    raise UpstreamError(f"{context} {revision} package must be null")
                continue
            if not isinstance(package, dict):
                raise UpstreamError(f"{context} {revision} package must be an object")
            _require_exact_keys(
                package,
                {"package_tree_sha", "files"},
                f"{context} {revision} package",
            )
            if package["package_tree_sha"] != expected_package["package_tree_sha"]:
                raise UpstreamError(f"{context} {revision} package tree does not match upstream")
            raw_files = package["files"]
            if not isinstance(raw_files, list):
                raise UpstreamError(f"{context} {revision} files must be a list")
            resource_paths = [
                resource.get("path") for resource in raw_files if isinstance(resource, dict)
            ]
            expected_paths = sorted(expected_package["files"], key=str.casefold)
            if len(resource_paths) != len(raw_files) or resource_paths != expected_paths:
                raise UpstreamError(f"{context} {revision} resources do not exactly match upstream")
            for resource_index, resource in enumerate(raw_files):
                assert isinstance(resource, dict)
                resource_context = f"{context} {revision} resource {resource_index}"
                _require_exact_keys(
                    resource,
                    {"path", "blob_sha", "size", "mode", "handling"},
                    resource_context,
                )
                identity = expected_package["files"][resource["path"]]
                if (
                    resource["blob_sha"] != identity[2]
                    or resource["mode"] != identity[1]
                    or resource["size"] != identity[3]
                ):
                    raise UpstreamError(f"{resource_context} identity does not match upstream")
                handling = resource["handling"]
                if handling not in _SKILL_RESOURCE_HANDLING:
                    raise UpstreamError(f"{resource_context} handling is invalid")
                if revision == "current":
                    resource_counts[handling] += 1
            if revision == "pinned":
                pinned_file_count += len(raw_files)
            else:
                current_file_count += len(raw_files)
            classified_resources.update((name, path) for path in resource_paths)

    if set(raw_pk_only) & set(names):
        raise UpstreamError("PK-only skills must not shadow upstream skill names")
    expected_local_skills = routed_names | set(raw_pk_only)

    summary = document.get("summary")
    if not isinstance(summary, dict):
        raise UpstreamError("upstream skill parity summary must be an object")
    _require_exact_keys(summary, _SKILL_PARITY_SUMMARY_KEYS, "upstream skill parity summary")
    expected_summary = {
        **disposition_counts,
        "upstream_total": len(raw_skills),
        "routed_upstream_names": len(routed_names),
        "shipped_skill_directories": len(expected_local_skills),
        "pinned_package_files": pinned_file_count,
        "current_package_files": current_file_count,
        "semantic_source_files": resource_counts["semantic-source"],
        "helper_semantics_only_files": resource_counts["helper-semantics-only"],
        "runtime_specific_exclusion_files": resource_counts["runtime-specific-exclusion"],
    }
    if summary != expected_summary:
        raise UpstreamError("upstream skill parity summary is not derived from its inventory")
    return {
        "upstream_skill_count": len(raw_skills),
        "routed_skill_count": len(routed_names),
        "pinned_resource_count": pinned_file_count,
        "current_resource_count": current_file_count,
        "classified_resource_count": len(classified_resources),
    }


def _github_token(environ: Mapping[str, str]) -> str | None:
    token = environ.get("GITHUB_TOKEN")
    if token is None or token == "":
        return None
    if (
        type(token) is not str
        or len(token) > 4096
        or token.strip() != token
        or any(character in token for character in ("\x00", "\r", "\n"))
    ):
        raise UpstreamError("GITHUB_TOKEN is not a valid HTTP authorization value")
    return token


def _commit_identity(
    repository: str,
    revision: str,
    *,
    token: str | None,
    timeout_seconds: float,
    fetch_json: FetchJSON,
) -> tuple[str, str]:
    url = _api_url(repository, "commits", revision)
    document = fetch_json(url, token, timeout_seconds)
    if not isinstance(document, dict):
        raise UpstreamError("GitHub commit response must be a JSON object")
    commit_sha = _response_sha(document.get("sha"), "GitHub commit sha")
    commit = document.get("commit")
    if not isinstance(commit, dict):
        raise UpstreamError("GitHub commit response commit must be an object")
    tree = commit.get("tree")
    if not isinstance(tree, dict):
        raise UpstreamError("GitHub commit response commit.tree must be an object")
    tree_sha = _response_sha(tree.get("sha"), "GitHub commit tree sha")
    return commit_sha, tree_sha


def _subtree_identity(
    repository: str,
    root_tree_sha: str,
    source_path: str,
    *,
    token: str | None,
    timeout_seconds: float,
    fetch_json: FetchJSON,
) -> str:
    tree_sha = root_tree_sha
    for component in PurePosixPath(source_path).parts:
        document = fetch_json(
            _api_url(repository, "git", "trees", tree_sha),
            token,
            timeout_seconds,
        )
        if not isinstance(document, dict):
            raise UpstreamError("GitHub tree response must be a JSON object")
        returned_sha = _response_sha(document.get("sha"), "GitHub tree sha")
        if returned_sha != tree_sha:
            raise UpstreamError("GitHub tree response does not match the requested tree SHA")
        truncated = document.get("truncated")
        if type(truncated) is not bool:
            raise UpstreamError("GitHub tree response truncated must be a boolean")
        if truncated:
            raise UpstreamError("GitHub tree response was truncated")
        entries = document.get("tree")
        if not isinstance(entries, list):
            raise UpstreamError("GitHub tree response tree must be a list")
        matches: list[tuple[str, str]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                raise UpstreamError("GitHub tree entry must be an object")
            entry_path = entry.get("path")
            entry_type = entry.get("type")
            entry_sha = entry.get("sha")
            if type(entry_path) is not str or type(entry_type) is not str:
                raise UpstreamError("GitHub tree entry path and type must be strings")
            validated_sha = _response_sha(entry_sha, "GitHub tree entry sha")
            if entry_path == component:
                matches.append((entry_type, validated_sha))
        if len(matches) != 1:
            raise UpstreamError(
                f"GitHub tree must contain exactly one {component!r} entry for {source_path!r}"
            )
        entry_type, tree_sha = matches[0]
        if entry_type != "tree":
            raise UpstreamError(f"GitHub path component is not a tree: {component}")
    return tree_sha


def _compare_inventory(
    source: UpstreamSource,
    *,
    base_commit: str,
    base_subtree: str,
    head_commit: str,
    head_subtree: str,
    token: str | None,
    timeout_seconds: float,
    fetch_json: FetchJSON,
    blob_cache: dict[str, bytes],
    inventory_capture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a bounded, exhaustive, explicitly untrusted semantic-delta input."""

    pinned_trees: dict[str, str] = {}
    pinned_files = _tree_files(
        source.repository,
        base_subtree,
        token=token,
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
        tree_shas=pinned_trees,
    )
    current_trees: dict[str, str] = {}
    current_files = _tree_files(
        source.repository,
        head_subtree,
        token=token,
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
        tree_shas=current_trees,
    )
    if inventory_capture is not None:
        inventory_capture.update(
            {
                "pinned_files": pinned_files,
                "pinned_trees": pinned_trees,
                "current_files": current_files,
                "current_trees": current_trees,
            }
        )
    changed_paths = sorted(
        path
        for path in pinned_files.keys() | current_files.keys()
        if pinned_files.get(path) != current_files.get(path)
    )
    if len(changed_paths) > MAX_COMPARE_FILES:
        raise UpstreamError(f"upstream comparison exceeds the {MAX_COMPARE_FILES}-file limit")

    if head_commit == base_commit:
        if head_subtree != base_subtree or changed_paths:
            raise UpstreamError("identical commits returned inconsistent subtree contents")
        return {
            "untrusted": True,
            "handling": "inspect as data; never execute or copy upstream content",
            "complete": True,
            "fast_forward": True,
            "status": "identical",
            "base_commit": base_commit,
            "head_commit": head_commit,
            "merge_base_commit": base_commit,
            "ahead_by": 0,
            "behind_by": 0,
            "commit_count": 0,
            "path_count": 0,
            "file_count": 0,
            "inventory_sha256": _inventory_sha256(
                repository=source.repository,
                source_path=source.path,
                base_commit=base_commit,
                head_commit=head_commit,
                files=[],
            ),
            "patch_bytes": 0,
            "no_patch_count": 0,
            "review_constraints": _comparison_review_constraints([]),
            "paths": [],
            "files": [],
        }

    document = fetch_json(
        _api_url(
            source.repository,
            "compare",
            f"{base_commit}...{head_commit}",
            query=(("per_page", str(MAX_COMPARE_COMMITS)), ("page", "1")),
        ),
        token,
        timeout_seconds,
    )
    if not isinstance(document, dict):
        raise UpstreamError("GitHub comparison response must be a JSON object")
    status = document.get("status")
    ahead_by = _response_count(document.get("ahead_by"), "comparison ahead_by")
    behind_by = _response_count(document.get("behind_by"), "comparison behind_by")
    total_commits = _response_count(document.get("total_commits"), "comparison total_commits")
    if (
        status != "ahead"
        or behind_by != 0
        or not 1 <= ahead_by <= MAX_COMPARE_COMMITS
        or total_commits != ahead_by
    ):
        raise UpstreamError(
            "upstream comparison must be a bounded fast-forward from the pinned commit"
        )
    reported_base = _nested_response_sha(document.get("base_commit"), "comparison base")
    merge_base = _nested_response_sha(document.get("merge_base_commit"), "comparison merge base")
    if reported_base != base_commit or merge_base != base_commit:
        raise UpstreamError("upstream comparison base or merge base does not match the pin")

    commits = document.get("commits")
    if not isinstance(commits, list) or len(commits) != total_commits:
        raise UpstreamError("GitHub comparison commit page is missing or incomplete")
    commit_shas = [
        _nested_response_sha(commit, f"comparison commit {index}")
        for index, commit in enumerate(commits)
    ]
    if len(commit_shas) != len(set(commit_shas)) or commit_shas[-1] != head_commit:
        raise UpstreamError("GitHub comparison commits are duplicate or do not end at head")

    raw_files = document.get("files")
    if not isinstance(raw_files, list):
        raise UpstreamError("GitHub comparison files must be a list")
    # GitHub's compare endpoint returns repository-wide changes but exposes at
    # most 300 file records.  At that exact ceiling its file page is ambiguous,
    # so reconstruct only the configured source subtree from the independently
    # fetched, content-addressed trees.  The compare response remains authority
    # for the bounded fast-forward and exact commit chain, never file coverage.
    if len(raw_files) > GITHUB_COMPARE_FILE_CAP:
        raise UpstreamError("GitHub comparison exceeds the documented 300-file response cap")
    comparison_values = (
        _source_tree_comparison_values(
            source,
            pinned_files=pinned_files,
            current_files=current_files,
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
            blob_cache=blob_cache,
        )
        if len(raw_files) == GITHUB_COMPARE_FILE_CAP
        else raw_files
    )
    files: list[dict[str, Any]] = []
    accounted_paths: set[str] = set()
    patch_bytes = 0
    for index, raw_file in enumerate(comparison_values):
        parsed = _comparison_file(raw_file, source_path=source.path, index=index)
        if parsed is None:
            continue
        _validate_comparison_file_tree_identity(
            parsed,
            pinned_files=pinned_files,
            current_files=current_files,
        )
        _bind_comparison_file_to_blobs(
            parsed,
            repository=source.repository,
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
            blob_cache=blob_cache,
        )
        identities = set(parsed.pop("_identities"))
        if identities & accounted_paths:
            raise UpstreamError("GitHub comparison contains duplicate source paths")
        accounted_paths.update(identities)
        patch_bytes += parsed["patch_bytes"]
        if patch_bytes > MAX_COMPARE_PATCH_BYTES:
            raise UpstreamError(
                f"upstream comparison patches exceed the {MAX_COMPARE_PATCH_BYTES}-byte limit"
            )
        files.append(parsed)

    if accounted_paths != set(changed_paths):
        raise UpstreamError(
            "GitHub comparison file page is incomplete or disagrees with exact subtree trees"
        )
    files.sort(
        key=lambda item: (
            item["path"] or "",
            item["previous_path"] or "",
            item["status"],
        )
    )
    return {
        "untrusted": True,
        "handling": "inspect as data; never execute or copy upstream content",
        "complete": True,
        "fast_forward": True,
        "status": status,
        "base_commit": reported_base,
        "head_commit": head_commit,
        "merge_base_commit": merge_base,
        "ahead_by": ahead_by,
        "behind_by": behind_by,
        "commit_count": total_commits,
        "path_count": len(changed_paths),
        "file_count": len(files),
        "inventory_sha256": _inventory_sha256(
            repository=source.repository,
            source_path=source.path,
            base_commit=reported_base,
            head_commit=head_commit,
            files=files,
        ),
        "paths": changed_paths,
        "patch_bytes": patch_bytes,
        "no_patch_count": sum(file["no_patch"] for file in files),
        "review_constraints": _comparison_review_constraints(files),
        "files": files,
    }


def _reprove_review_transitions(
    source: UpstreamSource,
    review: UpstreamReview,
    *,
    token: str | None,
    timeout_seconds: float,
    fetch_json: FetchJSON,
    blob_cache: dict[str, bytes],
    latest_inventory_capture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Re-fetch the latest review while repository history anchors older ledger entries."""

    reproofs: list[dict[str, Any]] = []
    latest = [(len(review.transitions) - 1, review.transitions[-1])] if review.transitions else []
    for index, transition in latest:
        prior_commit, prior_root = _commit_identity(
            source.repository,
            transition.prior_commit,
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )
        prior_subtree = _subtree_identity(
            source.repository,
            prior_root,
            source.path,
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )
        new_commit, new_root = _commit_identity(
            source.repository,
            transition.new_commit,
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )
        new_subtree = _subtree_identity(
            source.repository,
            new_root,
            source.path,
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
        )
        if (
            prior_commit != transition.prior_commit
            or prior_subtree != transition.prior_subtree_sha
            or new_commit != transition.new_commit
            or new_subtree != transition.new_subtree_sha
        ):
            raise UpstreamError(
                f"upstream review transition {index} remote identities do not match the ledger"
            )
        comparison = _compare_inventory(
            source,
            base_commit=prior_commit,
            base_subtree=prior_subtree,
            head_commit=new_commit,
            head_subtree=new_subtree,
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
            blob_cache=blob_cache,
            inventory_capture=latest_inventory_capture,
        )
        if comparison["inventory_sha256"] != transition.inventory_sha256:
            raise UpstreamError(
                f"upstream review transition {index} inventory digest does not match reproof"
            )
        disposition_paths = sorted(item.path for item in transition.dispositions)
        if disposition_paths != comparison["paths"]:
            missing = sorted(set(comparison["paths"]) - set(disposition_paths))
            extra = sorted(set(disposition_paths) - set(comparison["paths"]))
            details: list[str] = []
            if missing:
                details.append("missing " + ", ".join(missing))
            if extra:
                details.append("unexpected " + ", ".join(extra))
            raise UpstreamError(
                f"upstream review transition {index} dispositions do not exactly match "
                f"the comparison paths: {'; '.join(details)}"
            )
        _require_unavailable_binary_exclusions(
            transition,
            comparison,
            context=f"upstream review transition {index}",
        )
        counts = {
            disposition: sum(item.disposition == disposition for item in transition.dispositions)
            for disposition in ("A", "B", "C")
        }
        reproofs.append(
            {
                "index": index,
                "prior": {
                    "commit": transition.prior_commit,
                    "subtree_sha": transition.prior_subtree_sha,
                },
                "new": {
                    "commit": transition.new_commit,
                    "subtree_sha": transition.new_subtree_sha,
                },
                "inventory_sha256": transition.inventory_sha256,
                "path_count": len(disposition_paths),
                "disposition_counts": counts,
            }
        )
    return {
        "ok": True,
        "source_id": review.source_id,
        "genesis": {
            "commit": review.genesis_commit,
            "subtree_sha": review.genesis_subtree_sha,
        },
        "tip": {
            "commit": source.commit,
            "subtree_sha": source.subtree_sha,
        },
        "transition_count": len(review.transitions),
        "remote_transition_indices": [index for index, _ in latest],
        "history_validation": (
            "all entries form a strict local contiguous chain; repository history is the "
            "tamper-evident authority for older reviewed transitions"
        ),
        "transitions": reproofs,
    }


def _tree_files(
    repository: str,
    subtree_sha: str,
    *,
    token: str | None,
    timeout_seconds: float,
    fetch_json: FetchJSON,
    tree_shas: dict[str, str] | None = None,
) -> dict[str, tuple[str, str, str, int | None]]:
    document = fetch_json(
        _api_url(
            repository,
            "git",
            "trees",
            subtree_sha,
            query=(("recursive", "1"),),
        ),
        token,
        timeout_seconds,
    )
    if not isinstance(document, dict):
        raise UpstreamError("GitHub recursive tree response must be a JSON object")
    if _response_sha(document.get("sha"), "GitHub recursive tree sha") != subtree_sha:
        raise UpstreamError("GitHub recursive tree response does not match the requested SHA")
    if document.get("truncated") is not False:
        raise UpstreamError("GitHub recursive tree response is truncated or malformed")
    entries = document.get("tree")
    if not isinstance(entries, list) or len(entries) > MAX_TREE_ENTRIES:
        raise UpstreamError(
            f"GitHub recursive tree must contain at most {MAX_TREE_ENTRIES} entries"
        )

    files: dict[str, tuple[str, str, str, int | None]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise UpstreamError(f"GitHub recursive tree entry {index} must be an object")
        path = entry.get("path")
        entry_type = entry.get("type")
        mode = entry.get("mode")
        if type(path) is not str or type(entry_type) is not str or type(mode) is not str:
            raise UpstreamError("GitHub recursive tree path, type, and mode must be strings")
        _validate_posix_relative(path, context="GitHub recursive tree path", max_length=1024)
        if entry_type not in {"blob", "tree", "commit"} or not re.fullmatch(r"[0-7]{6}", mode):
            raise UpstreamError("GitHub recursive tree entry has an invalid type or mode")
        sha = _response_sha(entry.get("sha"), "GitHub recursive tree entry sha")
        size = entry.get("size")
        if size is not None and (type(size) is not int or size < 0):
            raise UpstreamError("GitHub recursive tree entry size must be non-negative")
        if entry_type == "tree":
            if tree_shas is not None:
                if path in tree_shas:
                    raise UpstreamError("GitHub recursive tree contains duplicate tree paths")
                tree_shas[path] = sha
            continue
        if path in files:
            raise UpstreamError("GitHub recursive tree contains duplicate paths")
        files[path] = (entry_type, mode, sha, size)
    return files


def _source_tree_comparison_values(
    source: UpstreamSource,
    *,
    pinned_files: dict[str, tuple[str, str, str, int | None]],
    current_files: dict[str, tuple[str, str, str, int | None]],
    token: str | None,
    timeout_seconds: float,
    fetch_json: FetchJSON,
    blob_cache: dict[str, bytes],
) -> list[dict[str, Any]]:
    """Build a deterministic source-scoped delta when GitHub's file page is capped."""

    pinned_paths = set(pinned_files)
    current_paths = set(current_files)
    removed_paths = pinned_paths - current_paths
    added_paths = current_paths - pinned_paths

    pinned_by_identity: dict[tuple[str, str, str, int | None], list[str]] = {}
    current_by_identity: dict[tuple[str, str, str, int | None], list[str]] = {}
    pinned_identity_counts: dict[tuple[str, str, str, int | None], int] = {}
    current_identity_counts: dict[tuple[str, str, str, int | None], int] = {}
    for identity in pinned_files.values():
        pinned_identity_counts[identity] = pinned_identity_counts.get(identity, 0) + 1
    for identity in current_files.values():
        current_identity_counts[identity] = current_identity_counts.get(identity, 0) + 1
    for path in removed_paths:
        pinned_by_identity.setdefault(pinned_files[path], []).append(path)
    for path in added_paths:
        current_by_identity.setdefault(current_files[path], []).append(path)

    rename_pairs: list[tuple[str, str]] = []
    for identity in pinned_by_identity.keys() & current_by_identity.keys():
        old_candidates = sorted(pinned_by_identity[identity])
        new_candidates = sorted(current_by_identity[identity])
        # Git does not store renames.  Pair only a unique exact-identity move;
        # ambiguous duplicate blobs remain explicit removals and additions.
        if (
            len(old_candidates) == len(new_candidates) == 1
            and pinned_identity_counts[identity] == 1
            and current_identity_counts[identity] == 1
        ):
            old_path = old_candidates[0]
            new_path = new_candidates[0]
            rename_pairs.append((old_path, new_path))
            removed_paths.remove(old_path)
            added_paths.remove(new_path)

    operations: list[tuple[str, str, str | None]] = [
        ("modified", path, None)
        for path in pinned_paths & current_paths
        if pinned_files[path] != current_files[path]
    ]
    operations.extend(("renamed", new_path, old_path) for old_path, new_path in rename_pairs)
    operations.extend(("removed", path, None) for path in removed_paths)
    operations.extend(("added", path, None) for path in added_paths)
    operations.sort(key=lambda item: (item[1], item[2] or "", item[0]))

    diff_work_cells = [0]
    return [
        _source_tree_comparison_value(
            source,
            status=status,
            path=path,
            previous_path=previous_path,
            pinned_files=pinned_files,
            current_files=current_files,
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
            blob_cache=blob_cache,
            diff_work_cells=diff_work_cells,
        )
        for status, path, previous_path in operations
    ]


def _source_tree_comparison_value(
    source: UpstreamSource,
    *,
    status: str,
    path: str,
    previous_path: str | None,
    pinned_files: dict[str, tuple[str, str, str, int | None]],
    current_files: dict[str, tuple[str, str, str, int | None]],
    token: str | None,
    timeout_seconds: float,
    fetch_json: FetchJSON,
    blob_cache: dict[str, bytes],
    diff_work_cells: list[int],
) -> dict[str, Any]:
    """Render one exact-tree operation into the existing review record shape."""

    old_path = previous_path if status == "renamed" else path
    old_identity = pinned_files.get(old_path)
    new_identity = current_files.get(path)
    for label, identity in (("pinned", old_identity), ("current", new_identity)):
        if identity is not None:
            _require_reviewable_tree_identity(identity, context=label)

    identity_paths = [value for value in (path, previous_path) if value is not None]
    no_patch_image = bool(identity_paths) and all(
        _NONSEMANTIC_IMAGE_PATH.fullmatch(value) for value in identity_paths
    )
    exact_rename = (
        status == "renamed"
        and old_identity is not None
        and new_identity is not None
        and old_identity == new_identity
    )
    exact_mode_change = (
        status == "modified"
        and old_identity is not None
        and new_identity is not None
        and old_identity[2] == new_identity[2]
        and old_identity[1] != new_identity[1]
        and old_identity[3] == new_identity[3]
    )

    patch: str | None = None
    additions = 0
    deletions = 0
    if exact_rename or exact_mode_change:
        identity = old_identity
        assert identity is not None
        content = _exact_tree_blob_content(
            source.repository,
            identity,
            context="source-tree identity",
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
            blob_cache=blob_cache,
        )
        if (
            new_identity is not None
            and new_identity[3] is not None
            and len(content) != new_identity[3]
        ):
            raise UpstreamError("source-tree blob size disagrees across exact identities")
    elif not no_patch_image:
        old_content = (
            b""
            if old_identity is None
            else _exact_tree_blob_content(
                source.repository,
                old_identity,
                context=f"pinned source-tree blob {old_path}",
                token=token,
                timeout_seconds=timeout_seconds,
                fetch_json=fetch_json,
                blob_cache=blob_cache,
            )
        )
        new_content = (
            b""
            if new_identity is None
            else _exact_tree_blob_content(
                source.repository,
                new_identity,
                context=f"current source-tree blob {path}",
                token=token,
                timeout_seconds=timeout_seconds,
                fetch_json=fetch_json,
                blob_cache=blob_cache,
            )
        )
        patch, additions, deletions = _complete_unified_patch(
            old_content,
            new_content,
            diff_work_cells=diff_work_cells,
        )

    identity = old_identity if status == "removed" else new_identity
    if identity is None:  # pragma: no cover - operations are derived from the exact trees
        raise UpstreamError("source-tree comparison operation has no exact blob identity")
    value: dict[str, Any] = {
        "filename": f"{source.path}/{path}",
        "status": status,
        "sha": identity[2],
        "additions": additions,
        "deletions": deletions,
        "changes": additions + deletions,
    }
    if previous_path is not None:
        value["previous_filename"] = f"{source.path}/{previous_path}"
    if patch is not None:
        value["patch"] = patch
    return value


def _exact_tree_blob_content(
    repository: str,
    identity: tuple[str, str, str, int | None],
    *,
    context: str,
    token: str | None,
    timeout_seconds: float,
    fetch_json: FetchJSON,
    blob_cache: dict[str, bytes],
) -> bytes:
    content = _blob_content(
        repository,
        identity[2],
        token=token,
        timeout_seconds=timeout_seconds,
        fetch_json=fetch_json,
        blob_cache=blob_cache,
    )
    if identity[3] is not None and len(content) != identity[3]:
        raise UpstreamError(f"{context} size disagrees with its exact tree identity")
    return content


def _complete_unified_patch(
    old_content: bytes,
    new_content: bytes,
    *,
    diff_work_cells: list[int] | None = None,
) -> tuple[str, int, int]:
    """Return a deterministic bounded-context diff for two bounded UTF-8 Git blobs."""

    old_text = _reviewable_text(old_content, context="pinned source-tree blob")
    new_text = _reviewable_text(new_content, context="current source-tree blob")
    old_lines, old_final_newline = _text_lines(old_text)
    new_lines, new_final_newline = _text_lines(new_text)
    if len(old_lines) > MAX_DIFF_LINES or len(new_lines) > MAX_DIFF_LINES:
        raise UpstreamError(f"source-tree diff exceeds the {MAX_DIFF_LINES}-line limit")
    comparison_cells = max(1, len(old_lines)) * max(1, len(new_lines))
    work_cells = [0] if diff_work_cells is None else diff_work_cells
    if comparison_cells > MAX_COMPARE_DIFF_CELLS - work_cells[0]:
        raise UpstreamError(
            f"source-tree diff work exceeds the {MAX_COMPARE_DIFF_CELLS}-cell comparison limit"
        )
    work_cells[0] += comparison_cells
    old_tokens = [
        (line, index < len(old_lines) - 1 or old_final_newline)
        for index, line in enumerate(old_lines)
    ]
    new_tokens = [
        (line, index < len(new_lines) - 1 or new_final_newline)
        for index, line in enumerate(new_lines)
    ]
    matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens)
    groups = list(matcher.get_grouped_opcodes(n=3))
    if not groups:
        raise UpstreamError("source-tree identities changed without a textual difference")

    rendered: list[str] = []
    additions = 0
    deletions = 0

    def append_line(prefix: str, token_value: tuple[str, bool]) -> None:
        line, has_newline = token_value
        rendered.append(f"{prefix}{line}")
        if not has_newline:
            rendered.append("\\ No newline at end of file")

    for group in groups:
        _, old_start, _, new_start, _ = group[0]
        _, _, old_stop, _, new_stop = group[-1]
        rendered.append(
            "@@ -"
            f"{_unified_range(old_start, old_stop)} "
            f"+{_unified_range(new_start, new_stop)} @@ source-tree-exact"
        )
        for operation, old_first, old_last, new_first, new_last in group:
            if operation == "equal":
                for token_value in old_tokens[old_first:old_last]:
                    append_line(" ", token_value)
                continue
            if operation in {"replace", "delete"}:
                for token_value in old_tokens[old_first:old_last]:
                    append_line("-", token_value)
                    deletions += 1
            if operation in {"replace", "insert"}:
                for token_value in new_tokens[new_first:new_last]:
                    append_line("+", token_value)
                    additions += 1
    patch = "\n".join(rendered)
    return patch, additions, deletions


def _unified_range(start: int, stop: int) -> str:
    """Format one zero-based half-open range using GNU unified-diff rules."""

    beginning = start + 1
    length = stop - start
    if length == 1:
        return str(beginning)
    if length == 0:
        beginning -= 1
    return f"{beginning},{length}"


def _comparison_file(
    value: Any,
    *,
    source_path: str,
    index: int,
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        raise UpstreamError(f"GitHub comparison file {index} must be an object")
    filename = value.get("filename")
    status = value.get("status")
    if type(filename) is not str or type(status) is not str:
        raise UpstreamError("GitHub comparison filename and status must be strings")
    _validate_posix_relative(filename, context="GitHub comparison filename", max_length=1024)
    if status not in {"added", "removed", "modified", "renamed", "copied", "changed"}:
        raise UpstreamError(f"GitHub comparison file has unsupported status: {status!r}")
    previous = value.get("previous_filename")
    if previous is not None:
        if type(previous) is not str:
            raise UpstreamError("GitHub comparison previous_filename must be a string")
        _validate_posix_relative(
            previous,
            context="GitHub comparison previous_filename",
            max_length=1024,
        )
    if status == "renamed" and previous is None:
        raise UpstreamError("GitHub renamed comparison file is missing previous_filename")

    relative = _relative_source_path(filename, source_path)
    previous_relative = (
        _relative_source_path(previous, source_path) if previous is not None else None
    )
    identities: set[str] = set()
    if status == "renamed":
        if relative is not None:
            identities.add(relative)
        if previous_relative is not None:
            identities.add(previous_relative)
    elif relative is not None:
        identities.add(relative)
    else:
        return None
    if not identities:
        return None

    sha = _response_sha(value.get("sha"), "GitHub comparison file sha")
    additions = _response_count(value.get("additions"), "comparison file additions")
    deletions = _response_count(value.get("deletions"), "comparison file deletions")
    changes = _response_count(value.get("changes"), "comparison file changes")
    if additions + deletions != changes:
        raise UpstreamError("GitHub comparison file change counts are inconsistent")
    patch = value.get("patch")
    if patch is not None and type(patch) is not str:
        raise UpstreamError("GitHub comparison file patch must be a string")
    patch_size = len(patch.encode("utf-8")) if patch is not None else 0
    if patch_size > MAX_FILE_PATCH_BYTES:
        raise UpstreamError(
            f"GitHub comparison file patch exceeds the {MAX_FILE_PATCH_BYTES}-byte limit"
        )
    reviewability = _patch_reviewability(
        path=relative,
        previous_path=previous_relative,
        status=status,
        patch=patch,
        additions=additions,
        deletions=deletions,
        changes=changes,
    )
    content_class = {
        "pending-exact-blob-unified-patch": "pending-text-patch",
        "unavailable-nonsemantic-image": "binary-or-patch-unavailable",
        "pending-exact-blob-pure-rename": "pending-blob-identity",
        "pending-exact-blob-mode-change": "pending-blob-identity",
    }[reviewability]
    return {
        "_identities": sorted(identities),
        "path": relative,
        "previous_path": previous_relative if status == "renamed" else None,
        "status": status,
        "sha": sha,
        "additions": additions,
        "deletions": deletions,
        "changes": changes,
        "patch": patch,
        "patch_bytes": patch_size,
        "no_patch": patch is None,
        "content_class": content_class,
        "reviewability": reviewability,
    }


def _patch_reviewability(
    *,
    path: str | None,
    previous_path: str | None,
    status: str,
    patch: str | None,
    additions: int,
    deletions: int,
    changes: int,
) -> str:
    if patch is not None:
        _validate_unified_patch(
            patch,
            additions=additions,
            deletions=deletions,
        )
        return "pending-exact-blob-unified-patch"
    if additions != 0 or deletions != 0 or changes != 0:
        raise UpstreamError(
            "GitHub comparison file without a patch must report zero additions and deletions"
        )
    if status == "renamed" and path is not None and previous_path is not None:
        return "pending-exact-blob-pure-rename"
    identities = [item for item in (path, previous_path) if item is not None]
    if identities and all(_NONSEMANTIC_IMAGE_PATH.fullmatch(item) for item in identities):
        return "unavailable-nonsemantic-image"
    if status in {"modified", "changed"} and path is not None:
        return "pending-exact-blob-mode-change"
    raise UpstreamError(
        "GitHub comparison patch is unavailable for a semantic or unclassified path"
    )


def _validate_unified_patch(patch: str, *, additions: int, deletions: int) -> None:
    """Reject incomplete patches and reconcile body counts to GitHub metadata."""

    _parse_unified_patch(patch, additions=additions, deletions=deletions)


def _parse_unified_patch(
    patch: str,
    *,
    additions: int,
    deletions: int,
) -> tuple[_UnifiedHunk, ...]:
    if not patch or "\x00" in patch or "\r" in patch:
        raise UpstreamError("GitHub comparison unified patch is empty or malformed")
    expected_old: int | None = None
    expected_new: int | None = None
    consumed_old = 0
    consumed_new = 0
    actual_additions = 0
    actual_deletions = 0
    hunk_count = 0
    body: list[str] = []
    hunks: list[_UnifiedHunk] = []

    def require_complete_hunk() -> None:
        if expected_old is None or consumed_old != expected_old or consumed_new != expected_new:
            raise UpstreamError("GitHub comparison unified patch is truncated or malformed")

    def append_hunk() -> None:
        require_complete_hunk()
        assert expected_old is not None and expected_new is not None
        header = _UNIFIED_HUNK.fullmatch(body[0])
        assert header is not None
        hunks.append(
            _UnifiedHunk(
                old_start=int(header.group("old_start")),
                old_count=expected_old,
                new_start=int(header.group("new_start")),
                new_count=expected_new,
                lines=tuple(body[1:]),
            )
        )

    for line in patch.splitlines():
        header = _UNIFIED_HUNK.fullmatch(line)
        if header:
            if hunk_count:
                append_hunk()
            hunk_count += 1
            expected_old = int(header.group("old_count") or "1")
            expected_new = int(header.group("new_count") or "1")
            consumed_old = 0
            consumed_new = 0
            body = [line]
            continue
        if not hunk_count:
            raise UpstreamError("GitHub comparison unified patch must begin with a hunk header")
        if expected_old is None or expected_new is None:  # pragma: no cover - guarded above
            raise UpstreamError("GitHub comparison unified patch has no active hunk")
        if line == "\\ No newline at end of file":
            body.append(line)
            continue
        if not line or line[0] not in {" ", "+", "-"}:
            raise UpstreamError("GitHub comparison unified patch has an invalid body line")
        if line[0] in {" ", "-"}:
            consumed_old += 1
        if line[0] in {" ", "+"}:
            consumed_new += 1
        if line[0] == "+":
            actual_additions += 1
        elif line[0] == "-":
            actual_deletions += 1
        if consumed_old > expected_old or consumed_new > expected_new:
            raise UpstreamError("GitHub comparison unified patch hunk counts are inconsistent")
        body.append(line)

    if not hunk_count:
        raise UpstreamError("GitHub comparison unified patch has no hunks")
    append_hunk()
    if actual_additions != additions or actual_deletions != deletions:
        raise UpstreamError(
            "GitHub comparison unified patch body counts do not match additions and deletions"
        )
    return tuple(hunks)


def _bind_comparison_file_to_blobs(
    value: dict[str, Any],
    *,
    repository: str,
    token: str | None,
    timeout_seconds: float,
    fetch_json: FetchJSON,
    blob_cache: dict[str, bytes],
) -> None:
    reviewability = value["reviewability"]
    if reviewability == "unavailable-nonsemantic-image":
        return
    path = value["path"]
    previous = value["previous_path"]
    old_identity = value["old_identity"]
    new_identity = value["new_identity"]
    if reviewability in {
        "pending-exact-blob-pure-rename",
        "pending-exact-blob-mode-change",
    }:
        assert old_identity is not None and new_identity is not None
        assert old_identity["sha"] == new_identity["sha"]
        blob = _blob_content(
            repository,
            old_identity["sha"],
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
            blob_cache=blob_cache,
        )
        if reviewability == "pending-exact-blob-pure-rename":
            assert path is not None and previous is not None
            if not (
                _NONSEMANTIC_IMAGE_PATH.fullmatch(path)
                and _NONSEMANTIC_IMAGE_PATH.fullmatch(previous)
            ):
                _reviewable_text(blob, context=f"renamed blob {path}")
            value["reviewability"] = "exact-blob-pure-rename"
        else:
            value["reviewability"] = "exact-blob-mode-change"
        value["content_class"] = "exact-blob-identity"
        return

    old_blob = (
        b""
        if old_identity is None
        else _blob_content(
            repository,
            old_identity["sha"],
            token=token,
            timeout_seconds=timeout_seconds,
            fetch_json=fetch_json,
            blob_cache=blob_cache,
        )
    )
    old_text = _reviewable_text(old_blob, context=f"pinned blob {previous or path}")
    patch = value["patch"]
    assert isinstance(patch, str)
    result = _apply_patch_to_exact_blob(
        old_text,
        patch,
        additions=value["additions"],
        deletions=value["deletions"],
    )
    if new_identity is None:
        if result:
            raise UpstreamError("GitHub comparison patch result does not remove the exact blob")
    else:
        expected_size = new_identity["size"]
        if expected_size is not None and len(result) != expected_size:
            raise UpstreamError(
                "GitHub comparison patch result size does not match the current tree blob"
            )
        if _git_blob_sha(result) != new_identity["sha"]:
            raise UpstreamError(
                "GitHub comparison patch result does not match the current tree blob SHA"
            )
    value["reviewability"] = "exact-blob-unified-patch"
    value["content_class"] = "exact-blob-text-patch"


def _blob_content(
    repository: str,
    sha: str,
    *,
    token: str | None,
    timeout_seconds: float,
    fetch_json: FetchJSON,
    blob_cache: dict[str, bytes],
) -> bytes:
    if sha in blob_cache:
        return blob_cache[sha]
    document = fetch_json(
        _api_url(repository, "git", "blobs", sha),
        token,
        timeout_seconds,
    )
    if not isinstance(document, dict):
        raise UpstreamError("GitHub blob response must be a JSON object")
    if _response_sha(document.get("sha"), "GitHub blob sha") != sha:
        raise UpstreamError("GitHub blob response does not match the exact tree blob SHA")
    if document.get("encoding") != "base64":
        raise UpstreamError("GitHub blob response must use base64 encoding")
    size = document.get("size")
    content = document.get("content")
    if type(size) is not int or not 0 <= size <= MAX_TEXT_BLOB_BYTES:
        raise UpstreamError(f"GitHub text blob exceeds the {MAX_TEXT_BLOB_BYTES}-byte limit")
    if type(content) is not str:
        raise UpstreamError("GitHub blob content must be a base64 string")
    try:
        decoded = base64.b64decode(content.replace("\n", ""), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise UpstreamError("GitHub blob content is not valid base64") from exc
    if len(decoded) != size:
        raise UpstreamError("GitHub blob decoded size does not match its metadata")
    if _git_blob_sha(decoded) != sha:
        raise UpstreamError("GitHub blob content does not match the exact Git blob SHA")
    if sum(len(item) for item in blob_cache.values()) + len(decoded) > MAX_COMPARE_BLOB_BYTES:
        raise UpstreamError(
            f"upstream comparison blobs exceed the {MAX_COMPARE_BLOB_BYTES}-byte limit"
        )
    blob_cache[sha] = decoded
    return decoded


def _git_blob_sha(content: bytes) -> str:
    header = b"blob " + str(len(content)).encode("ascii") + b"\x00"
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def _reviewable_text(content: bytes, *, context: str) -> str:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UpstreamError(f"{context} is not reviewable UTF-8 text") from exc
    if "\x00" in text or "\r" in text:
        raise UpstreamError(f"{context} contains unsupported control or CRLF content")
    return text


def _text_lines(text: str) -> tuple[list[str], bool]:
    if not text:
        return [], False
    final_newline = text.endswith("\n")
    lines = text.split("\n")
    if final_newline:
        lines.pop()
    return lines, final_newline


def _apply_patch_to_exact_blob(
    old_text: str,
    patch: str,
    *,
    additions: int,
    deletions: int,
) -> bytes:
    hunks = _parse_unified_patch(patch, additions=additions, deletions=deletions)
    old_lines, old_final_newline = _text_lines(old_text)
    old_cursor = 0
    output: list[str] = []
    old_no_newline = False
    new_no_newline = False
    new_no_newline_position: int | None = None

    for hunk in hunks:
        old_index = hunk.old_start if hunk.old_count == 0 else hunk.old_start - 1
        new_index = hunk.new_start if hunk.new_count == 0 else hunk.new_start - 1
        if old_index < old_cursor or old_index > len(old_lines):
            raise UpstreamError("GitHub comparison patch old hunk position is invalid")
        output.extend(old_lines[old_cursor:old_index])
        old_cursor = old_index
        if len(output) != new_index:
            raise UpstreamError("GitHub comparison patch new hunk position is invalid")
        previous_prefix: str | None = None
        for line in hunk.lines:
            if line == "\\ No newline at end of file":
                if previous_prefix not in {" ", "+", "-"}:
                    raise UpstreamError("GitHub comparison patch has a misplaced newline marker")
                if previous_prefix in {" ", "-"}:
                    if old_cursor != len(old_lines) or old_final_newline or old_no_newline:
                        raise UpstreamError("GitHub comparison patch old newline marker is invalid")
                    old_no_newline = True
                if previous_prefix in {" ", "+"}:
                    if new_no_newline:
                        raise UpstreamError("GitHub comparison patch new newline marker is invalid")
                    new_no_newline = True
                    new_no_newline_position = len(output)
                continue
            prefix, content = line[0], line[1:]
            previous_prefix = prefix
            if prefix in {" ", "-"}:
                if old_cursor >= len(old_lines) or old_lines[old_cursor] != content:
                    raise UpstreamError(
                        "GitHub comparison patch deletion or context does not match pinned blob"
                    )
                old_cursor += 1
            if prefix in {" ", "+"}:
                output.append(content)

    trailing_old = old_cursor < len(old_lines)
    output.extend(old_lines[old_cursor:])
    if old_lines and not old_final_newline and old_cursor == len(old_lines) and not old_no_newline:
        raise UpstreamError("GitHub comparison patch omits the pinned no-newline marker")
    if new_no_newline and new_no_newline_position != len(output):
        raise UpstreamError("GitHub comparison patch new newline marker is not at end of file")
    if not output:
        result = b""
    else:
        final_newline = old_final_newline if trailing_old else not new_no_newline
        rendered = "\n".join(output) + ("\n" if final_newline else "")
        result = rendered.encode("utf-8")
    if len(result) > MAX_TEXT_BLOB_BYTES:
        raise UpstreamError(
            f"GitHub comparison patch result exceeds the {MAX_TEXT_BLOB_BYTES}-byte limit"
        )
    return result


def _comparison_review_constraints(files: list[dict[str, Any]]) -> dict[str, Any]:
    unavailable_paths = sorted(
        {
            identity
            for file in files
            if file["reviewability"] == "unavailable-nonsemantic-image"
            for identity in (file["path"], file["previous_path"])
            if identity is not None
        }
    )
    return {
        "unified_patch_counts": PATCH_COUNT_CONSTRAINT,
        "exact_blob_binding": BLOB_BINDING_CONSTRAINT,
        "supported_tree_entries": TREE_ENTRY_CONSTRAINT,
        "no_patch": NO_PATCH_CONSTRAINT,
        "unavailable_binary_paths": unavailable_paths,
    }


def _relative_source_path(filename: str, source_path: str) -> str | None:
    prefix = f"{source_path}/"
    if not filename.startswith(prefix):
        return None
    relative = filename[len(prefix) :]
    _validate_posix_relative(relative, context="upstream source-relative path", max_length=1024)
    return relative


def _validate_comparison_file_tree_identity(
    value: dict[str, Any],
    *,
    pinned_files: dict[str, tuple[str, str, str, int | None]],
    current_files: dict[str, tuple[str, str, str, int | None]],
) -> None:
    status = value["status"]
    path = value["path"]
    previous = value["previous_path"]
    old_identity: tuple[str, str, str, int | None] | None = None
    new_identity: tuple[str, str, str, int | None] | None = None
    expected_sha: str | None = None
    valid = True
    if status == "removed":
        valid = path is not None and path in pinned_files and path not in current_files
        if valid:
            old_identity = pinned_files[path]
            expected_sha = old_identity[2]
    elif status in {"added", "copied"}:
        valid = path is not None and path in current_files and path not in pinned_files
        if valid:
            new_identity = current_files[path]
            expected_sha = new_identity[2]
    elif status in {"modified", "changed"}:
        valid = path is not None and path in pinned_files and path in current_files
        if valid:
            old_identity = pinned_files[path]
            new_identity = current_files[path]
            expected_sha = new_identity[2]
    elif status == "renamed":
        valid = (path is None or (path in current_files and path not in pinned_files)) and (
            previous is None or (previous in pinned_files and previous not in current_files)
        )
        if valid:
            if previous is not None:
                old_identity = pinned_files[previous]
            if path is not None:
                new_identity = current_files[path]
                expected_sha = new_identity[2]
    if valid:
        for context, identity in (("pinned", old_identity), ("current", new_identity)):
            if identity is not None:
                _require_reviewable_tree_identity(identity, context=context)
        if value["reviewability"] in {
            "pending-exact-blob-pure-rename",
            "exact-blob-pure-rename",
        }:
            valid = (
                old_identity is not None
                and new_identity is not None
                and old_identity[2] == new_identity[2]
            )
        elif value["reviewability"] in {
            "pending-exact-blob-mode-change",
            "exact-blob-mode-change",
        }:
            valid = (
                old_identity is not None
                and new_identity is not None
                and old_identity[2] == new_identity[2]
                and old_identity[1] != new_identity[1]
            )
    if not valid or (expected_sha is not None and value["sha"] != expected_sha):
        raise UpstreamError(
            "GitHub comparison file status or SHA disagrees with exact subtree trees"
        )
    value["old_identity"] = _tree_identity_document(old_identity)
    value["new_identity"] = _tree_identity_document(new_identity)
    value["tree_sha_verified"] = expected_sha is not None


def _require_reviewable_tree_identity(
    identity: tuple[str, str, str, int | None],
    *,
    context: str,
) -> None:
    entry_type, mode, _, _ = identity
    if entry_type != "blob" or mode not in {"100644", "100755"}:
        raise UpstreamError(
            f"{context} changed tree entry must be a regular blob in mode 100644 or 100755"
        )


def _tree_identity_document(
    identity: tuple[str, str, str, int | None] | None,
) -> dict[str, Any] | None:
    if identity is None:
        return None
    entry_type, mode, sha, size = identity
    return {"type": entry_type, "mode": mode, "sha": sha, "size": size}


def _response_count(value: Any, context: str) -> int:
    if type(value) is not int or value < 0:
        raise UpstreamError(f"{context} must be a non-negative integer")
    return value


def _inventory_sha256(
    *,
    repository: str,
    source_path: str,
    base_commit: str,
    head_commit: str,
    files: list[dict[str, Any]],
) -> str:
    canonical = json.dumps(
        {
            "repository": repository,
            "source_path": source_path,
            "base_commit": base_commit,
            "head_commit": head_commit,
            "files": files,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _nested_response_sha(value: Any, context: str) -> str:
    if not isinstance(value, dict):
        raise UpstreamError(f"{context} must be an object")
    return _response_sha(value.get("sha"), f"{context} sha")


def _response_sha(value: Any, context: str) -> str:
    if type(value) is not str or not _FULL_SHA.fullmatch(value):
        raise UpstreamError(f"{context} must be a full lowercase Git SHA")
    return value


def _api_url(
    repository: str,
    *segments: str,
    query: tuple[tuple[str, str], ...] = (),
) -> str:
    owner, name = repository.split("/", 1)
    encoded = "/".join(quote(segment, safe="") for segment in (owner, name, *segments))
    url = f"{GITHUB_API_ORIGIN}/repos/{encoded}"
    if query:
        url = f"{url}?{urlencode(query)}"
    _require_api_url(url)
    return url


def _require_api_url(url: str) -> None:
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise UpstreamError(
            "upstream network access is restricted to https://api.github.com"
        ) from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != "api.github.com"
        or port not in {None, 443}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise UpstreamError("upstream network access is restricted to https://api.github.com")


def _fetch_json(url: str, token: str | None, timeout_seconds: float) -> Any:
    _require_api_url(url)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "PK-Stack/0.1 upstream-check",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers, method="GET")
    try:
        with _build_opener().open(request, timeout=timeout_seconds) as response:
            final_url = response.geturl()
            _require_api_url(final_url)
            if response.status != 200:
                raise UpstreamError(f"GitHub API returned HTTP {response.status}")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise UpstreamError(f"GitHub API returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise UpstreamError("GitHub API request failed") from exc
    except OSError as exc:
        raise UpstreamError("GitHub API response could not be read") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise UpstreamError(f"GitHub API response exceeds the {MAX_RESPONSE_BYTES}-byte limit")
    return _decode_json(raw, context="GitHub API response")


def _read_json_path(path: Path, *, context: str, max_bytes: int) -> Any:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise UpstreamError(f"unable to read {context}: {path}") from exc
    if len(raw) > max_bytes:
        raise UpstreamError(f"{context} exceeds the {max_bytes}-byte limit: {path}")
    return _decode_json(raw, context=context)


@contextmanager
def _accept_locked(root: Path) -> Iterator[None]:
    if fcntl is None:
        raise UpstreamError("upstream acceptance locking requires POSIX fcntl")
    descriptor = _open_accept_lock_descriptor(root)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _open_accept_lock_descriptor(root: Path) -> int:
    """Open the persistent lock without following a raced repository symlink."""

    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    if not nofollow or not directory_flag:
        raise UpstreamError("upstream acceptance requires safe no-follow directory locking")
    directory_flags = os.O_RDONLY | directory_flag | nofollow | getattr(os, "O_CLOEXEC", 0)
    file_flags = os.O_RDWR | os.O_CREAT | nofollow | getattr(os, "O_CLOEXEC", 0)
    descriptors: list[int] = []

    def open_directory(parent: int, name: str, *, mode: int, owner_only: bool) -> int:
        with suppress(FileExistsError):
            os.mkdir(name, mode, dir_fd=parent)
        descriptor = os.open(name, directory_flags, dir_fd=parent)
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid():
            os.close(descriptor)
            raise UpstreamError("upstream acceptance state is not a safe owner-owned directory")
        if owner_only:
            os.fchmod(descriptor, 0o700)
        return descriptor

    try:
        root_descriptor = os.open(root, directory_flags)
        descriptors.append(root_descriptor)
        pk_stack_descriptor = open_directory(
            root_descriptor,
            ".pk-stack",
            mode=0o755,
            owner_only=False,
        )
        descriptors.append(pk_stack_descriptor)
        state_descriptor = open_directory(
            pk_stack_descriptor,
            "state",
            mode=0o700,
            owner_only=True,
        )
        descriptors.append(state_descriptor)
        descriptor = os.open(_ACCEPT_LOCK.name, file_flags, 0o600, dir_fd=state_descriptor)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_nlink != 1
        ):
            os.close(descriptor)
            raise UpstreamError("upstream acceptance lock is not a safe owner-owned regular file")
        os.fchmod(descriptor, 0o600)
        return descriptor
    except UpstreamError:
        raise
    except OSError as exc:
        raise UpstreamError("unable to open a safe upstream acceptance lock") from exc
    finally:
        for directory_descriptor in reversed(descriptors):
            os.close(directory_descriptor)


def _validate_accept_directory(root: Path) -> None:
    directory = workspace_path(root, _ACCEPT_DIRECTORY)
    if not directory.exists():
        return
    if not directory.is_dir() or directory.is_symlink():
        raise UpstreamError(f"upstream acceptance input is not a safe directory: {directory}")
    allowed = {DEFAULT_PROPOSAL.name, _ACCEPT_TRANSACTION.name}
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.name not in allowed or entry.is_symlink() or not entry.is_file():
                raise UpstreamError(
                    "upstream acceptance directory may contain only the proposal and "
                    "recovery journal"
                )


def _canonical_json_bytes(document: Any) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _atomic_write_json(path: Path, document: Any, *, mode: int) -> None:
    content = _canonical_json_bytes(document)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _write_accept_transaction(
    root: Path,
    *,
    manifest_path: Path,
    ledger_path: Path,
    before_manifest: dict[str, Any],
    before_ledger: dict[str, Any],
    after_manifest: dict[str, Any],
    after_ledger: dict[str, Any],
    source_id: str,
    expected_head: str,
) -> None:
    if not _SOURCE_ID.fullmatch(source_id):
        raise UpstreamError("upstream acceptance transaction source_id is invalid")
    _validate_serialized_accept_snapshots(
        before_manifest=before_manifest,
        before_ledger=before_ledger,
        after_manifest=after_manifest,
        after_ledger=after_ledger,
        source_id=source_id,
        expected_head=expected_head,
    )
    transaction_path = workspace_path(root, _ACCEPT_TRANSACTION)
    transaction = {
        "schema_version": 2,
        "manifest_path": manifest_path.relative_to(root).as_posix(),
        "review_ledger_path": ledger_path.relative_to(root).as_posix(),
        "source_id": source_id,
        "expected_head": expected_head,
        "before": {"manifest": before_manifest, "review_ledger": before_ledger},
        "after": {"manifest": after_manifest, "review_ledger": after_ledger},
    }
    if len(_canonical_json_bytes(transaction)) > MAX_ACCEPT_TRANSACTION_BYTES:
        raise UpstreamError(
            f"upstream acceptance transaction exceeds the {MAX_ACCEPT_TRANSACTION_BYTES}-byte limit"
        )
    _atomic_write_json(transaction_path, transaction, mode=0o600)
    try:
        _atomic_write_json(
            ledger_path,
            after_ledger,
            mode=ledger_path.stat().st_mode & 0o777,
        )
        _atomic_write_json(
            manifest_path,
            after_manifest,
            mode=manifest_path.stat().st_mode & 0o777,
        )
    except BaseException as exc:
        try:
            _atomic_write_json(
                ledger_path,
                before_ledger,
                mode=ledger_path.stat().st_mode & 0o777,
            )
            _atomic_write_json(
                manifest_path,
                before_manifest,
                mode=manifest_path.stat().st_mode & 0o777,
            )
            transaction_path.unlink(missing_ok=True)
        except BaseException as rollback_exc:
            raise UpstreamError(
                "upstream acceptance was interrupted; rerun the same accept command to recover"
            ) from rollback_exc
        raise UpstreamError("upstream acceptance write failed and was rolled back") from exc
    # Keep the journal through proposal cleanup. A crash before that cleanup can
    # be completed by rerunning the same expected-head-bound accept command.


def _recover_accept_transaction(root: Path, *, expected_head: str) -> str | None:
    transaction_path = workspace_path(root, _ACCEPT_TRANSACTION)
    if not transaction_path.exists():
        return None
    if not transaction_path.is_file() or transaction_path.is_symlink():
        raise UpstreamError("upstream acceptance transaction path is unsafe")
    document = _read_json_path(
        transaction_path,
        context="upstream acceptance transaction",
        max_bytes=MAX_ACCEPT_TRANSACTION_BYTES,
    )
    if not isinstance(document, dict):
        raise UpstreamError("upstream acceptance transaction must be a JSON object")
    _require_exact_keys(
        document,
        {
            "schema_version",
            "manifest_path",
            "review_ledger_path",
            "source_id",
            "expected_head",
            "before",
            "after",
        },
        "upstream acceptance transaction",
    )
    if document["schema_version"] != 2 or document["expected_head"] != expected_head:
        raise UpstreamError("upstream acceptance transaction does not match this invocation")
    source_id = document["source_id"]
    if type(source_id) is not str or not _SOURCE_ID.fullmatch(source_id):
        raise UpstreamError("upstream acceptance transaction source_id is invalid")
    if document["manifest_path"] != DEFAULT_MANIFEST.as_posix():
        raise UpstreamError("upstream acceptance transaction manifest path is invalid")
    if document["review_ledger_path"] != "maintenance/upstream-reviews.json":
        raise UpstreamError("upstream acceptance transaction review ledger path is invalid")
    before = document["before"]
    after = document["after"]
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise UpstreamError("upstream acceptance transaction snapshots must be objects")
    _require_exact_keys(before, {"manifest", "review_ledger"}, "transaction before snapshot")
    _require_exact_keys(after, {"manifest", "review_ledger"}, "transaction after snapshot")
    _validate_serialized_accept_snapshots(
        before_manifest=before["manifest"],
        before_ledger=before["review_ledger"],
        after_manifest=after["manifest"],
        after_ledger=after["review_ledger"],
        source_id=source_id,
        expected_head=expected_head,
    )
    manifest_path = workspace_path(root, DEFAULT_MANIFEST)
    ledger_path = workspace_path(root, Path("maintenance/upstream-reviews.json"))
    current_manifest = _read_json_path(
        manifest_path,
        context="upstream manifest",
        max_bytes=MAX_MANIFEST_BYTES,
    )
    current_ledger = _read_json_path(
        ledger_path,
        context="upstream review ledger",
        max_bytes=MAX_REVIEW_LEDGER_BYTES,
    )
    if current_manifest not in (before["manifest"], after["manifest"]):
        raise UpstreamError("upstream acceptance transaction conflicts with the manifest")
    if current_ledger not in (before["review_ledger"], after["review_ledger"]):
        raise UpstreamError("upstream acceptance transaction conflicts with the review ledger")
    _atomic_write_json(
        ledger_path,
        after["review_ledger"],
        mode=ledger_path.stat().st_mode & 0o777,
    )
    _atomic_write_json(
        manifest_path,
        after["manifest"],
        mode=manifest_path.stat().st_mode & 0o777,
    )
    return source_id


def _validate_serialized_accept_snapshots(
    *,
    before_manifest: Any,
    before_ledger: Any,
    after_manifest: Any,
    after_ledger: Any,
    source_id: str,
    expected_head: str,
) -> None:
    """Prove that an acceptance journal advances exactly one named source."""

    if not _FULL_SHA.fullmatch(expected_head):
        raise UpstreamError("transaction expected_head is invalid")
    if len(source_id) > 64 or not _SOURCE_ID.fullmatch(source_id):
        raise UpstreamError("transaction source_id is invalid")

    documents = {
        "before manifest": before_manifest,
        "after manifest": after_manifest,
        "before review ledger": before_ledger,
        "after review ledger": after_ledger,
    }
    if not all(isinstance(value, dict) for value in documents.values()):
        raise UpstreamError("upstream acceptance transaction snapshots must be JSON objects")
    assert isinstance(before_manifest, dict)
    assert isinstance(after_manifest, dict)
    assert isinstance(before_ledger, dict)
    assert isinstance(after_ledger, dict)
    for label, document, expected_keys, expected_schema in (
        (
            "manifest",
            before_manifest,
            {"schema_version", "review_ledger_path", "sources"},
            UPSTREAM_SCHEMA_VERSION,
        ),
        (
            "manifest",
            after_manifest,
            {"schema_version", "review_ledger_path", "sources"},
            UPSTREAM_SCHEMA_VERSION,
        ),
        (
            "review ledger",
            before_ledger,
            {"schema_version", "sources"},
            UPSTREAM_REVIEW_SCHEMA_VERSION,
        ),
        (
            "review ledger",
            after_ledger,
            {"schema_version", "sources"},
            UPSTREAM_REVIEW_SCHEMA_VERSION,
        ),
    ):
        _require_exact_keys(document, expected_keys, f"transaction {label}")
        if document["schema_version"] != expected_schema:
            raise UpstreamError(f"transaction {label} schema_version is invalid")
    if (
        before_manifest["review_ledger_path"] != "maintenance/upstream-reviews.json"
        or after_manifest["review_ledger_path"] != "maintenance/upstream-reviews.json"
    ):
        raise UpstreamError("transaction changed the upstream review ledger path")

    before_manifest_sources = _transaction_sources(before_manifest, label="before manifest")
    after_manifest_sources = _transaction_sources(after_manifest, label="after manifest")
    before_review_sources = _transaction_sources(before_ledger, label="before review ledger")
    after_review_sources = _transaction_sources(after_ledger, label="after review ledger")
    expected_ids = set(before_manifest_sources)
    if (
        set(after_manifest_sources) != expected_ids
        or set(before_review_sources) != expected_ids
        or set(after_review_sources) != expected_ids
        or source_id not in expected_ids
    ):
        raise UpstreamError("transaction source ids do not match across snapshots")
    if list(before_manifest_sources) != list(after_manifest_sources):
        raise UpstreamError("transaction reordered manifest sources")
    if list(before_review_sources) != list(after_review_sources):
        raise UpstreamError("transaction reordered review sources")

    _validate_transaction_source_chains(
        before_manifest_sources,
        before_review_sources,
        label="before",
    )
    _validate_transaction_source_chains(
        after_manifest_sources,
        after_review_sources,
        label="after",
    )

    for other_id in expected_ids - {source_id}:
        if before_manifest_sources[other_id] != after_manifest_sources[other_id]:
            raise UpstreamError("transaction changed a nonselected manifest source")
        if before_review_sources[other_id] != after_review_sources[other_id]:
            raise UpstreamError("transaction changed a nonselected review source")

    before_source = before_manifest_sources[source_id]
    after_source = after_manifest_sources[source_id]
    _require_exact_keys(before_source, _SOURCE_KEYS, "transaction selected manifest source")
    _require_exact_keys(after_source, _SOURCE_KEYS, "transaction selected manifest source")
    immutable_source = _SOURCE_KEYS - {"commit", "subtree_sha"}
    if any(before_source[key] != after_source[key] for key in immutable_source):
        raise UpstreamError("transaction changed selected source metadata")
    if after_source["commit"] != expected_head:
        raise UpstreamError("transaction selected source does not advance to expected_head")

    before_review = before_review_sources[source_id]
    after_review = after_review_sources[source_id]
    _require_exact_keys(before_review, _LEDGER_SOURCE_KEYS, "transaction selected review source")
    _require_exact_keys(after_review, _LEDGER_SOURCE_KEYS, "transaction selected review source")
    for key in ("id", "repository", "path", "provenance_path", "parity_path"):
        if before_source[key] != before_review[key] or after_source[key] != after_review[key]:
            raise UpstreamError("transaction selected source and review metadata do not match")
    immutable_review = _LEDGER_SOURCE_KEYS - {"transitions"}
    if any(before_review[key] != after_review[key] for key in immutable_review):
        raise UpstreamError("transaction changed selected review metadata")
    before_transitions = before_review["transitions"]
    after_transitions = after_review["transitions"]
    if (
        not isinstance(before_transitions, list)
        or not isinstance(after_transitions, list)
        or after_transitions[:-1] != before_transitions
        or len(after_transitions) != len(before_transitions) + 1
    ):
        raise UpstreamError("transaction must append exactly one selected review transition")
    transition = _parse_review_transition(
        after_transitions[-1],
        context="transaction appended review transition",
    )
    if (
        transition.prior_commit != before_source["commit"]
        or transition.prior_subtree_sha != before_source["subtree_sha"]
        or transition.new_commit != after_source["commit"]
        or transition.new_subtree_sha != after_source["subtree_sha"]
    ):
        raise UpstreamError(
            "transaction appended transition does not bind the selected pin advance"
        )


def _transaction_sources(document: dict[str, Any], *, label: str) -> dict[str, dict[str, Any]]:
    raw_sources = document.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise UpstreamError(f"transaction {label} sources must be a non-empty list")
    result: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(raw_sources):
        if not isinstance(value, dict):
            raise UpstreamError(f"transaction {label} source {index} must be an object")
        value_source_id = value.get("id")
        if type(value_source_id) is not str or not _SOURCE_ID.fullmatch(value_source_id):
            raise UpstreamError(f"transaction {label} source {index} id is invalid")
        if value_source_id in result:
            raise UpstreamError(f"transaction {label} source ids are duplicated")
        result[value_source_id] = value
    return result


def _validate_transaction_source_chains(
    manifest_sources: dict[str, dict[str, Any]],
    review_sources: dict[str, dict[str, Any]],
    *,
    label: str,
) -> None:
    """Validate every journal source and its complete append-only review chain."""

    for source_id, source in manifest_sources.items():
        review = review_sources[source_id]
        _require_exact_keys(source, _SOURCE_KEYS, f"transaction {label} manifest source")
        _require_exact_keys(review, _LEDGER_SOURCE_KEYS, f"transaction {label} review source")
        for key in ("id", "repository", "path", "provenance_path", "parity_path"):
            if source.get(key) != review.get(key):
                raise UpstreamError(f"transaction {label} source and review metadata do not match")
        if source.get("id") != source_id:
            raise UpstreamError(f"transaction {label} manifest source id is invalid")
        commit = source.get("commit")
        subtree_sha = source.get("subtree_sha")
        if (
            type(commit) is not str
            or not _FULL_SHA.fullmatch(commit)
            or type(subtree_sha) is not str
            or not _FULL_SHA.fullmatch(subtree_sha)
        ):
            raise UpstreamError(f"transaction {label} manifest pin is invalid")
        prior_commit, prior_subtree = _parse_review_identity(
            review.get("genesis"),
            context=f"transaction {label} review genesis",
        )
        raw_transitions = review.get("transitions")
        if not isinstance(raw_transitions, list) or len(raw_transitions) > MAX_REVIEW_TRANSITIONS:
            raise UpstreamError(f"transaction {label} review transitions are invalid")
        for index, raw_transition in enumerate(raw_transitions):
            transition = _parse_review_transition(
                raw_transition,
                context=f"transaction {label} review transition {index}",
            )
            if (
                transition.prior_commit != prior_commit
                or transition.prior_subtree_sha != prior_subtree
            ):
                raise UpstreamError(f"transaction {label} review chain is not contiguous")
            if (
                transition.new_commit == transition.prior_commit
                and transition.new_subtree_sha == transition.prior_subtree_sha
            ):
                raise UpstreamError(f"transaction {label} review transition does not advance")
            prior_commit = transition.new_commit
            prior_subtree = transition.new_subtree_sha
        if prior_commit != commit or prior_subtree != subtree_sha:
            raise UpstreamError(f"transaction {label} review tip does not match its pin")


def _rollback_accept_transaction(root: Path) -> None:
    transaction_path = workspace_path(root, _ACCEPT_TRANSACTION)
    document = _read_json_path(
        transaction_path,
        context="upstream acceptance transaction",
        max_bytes=MAX_ACCEPT_TRANSACTION_BYTES,
    )
    if not isinstance(document, dict) or not isinstance(document.get("before"), dict):
        raise UpstreamError("upstream acceptance transaction cannot be rolled back safely")
    before = document["before"]
    if set(before) != {"manifest", "review_ledger"}:
        raise UpstreamError("upstream acceptance transaction cannot be rolled back safely")
    manifest_path = workspace_path(root, DEFAULT_MANIFEST)
    ledger_path = workspace_path(root, Path("maintenance/upstream-reviews.json"))
    _atomic_write_json(
        ledger_path,
        before["review_ledger"],
        mode=ledger_path.stat().st_mode & 0o777,
    )
    _atomic_write_json(
        manifest_path,
        before["manifest"],
        mode=manifest_path.stat().st_mode & 0o777,
    )


def _cleanup_acceptance_inputs(root: Path, proposal_path: Path) -> None:
    expected = workspace_path(root, DEFAULT_PROPOSAL)
    if proposal_path != expected or proposal_path.is_symlink():
        raise UpstreamError("upstream acceptance proposal cleanup path is unsafe")
    transaction_path = workspace_path(root, _ACCEPT_TRANSACTION)
    proposal_path.unlink(missing_ok=True)
    transaction_path.unlink(missing_ok=True)
    directory = workspace_path(root, _ACCEPT_DIRECTORY)
    try:
        directory.rmdir()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise UpstreamError(
            "upstream acceptance succeeded but ephemeral state cleanup was incomplete"
        ) from exc


def _decode_json(raw: bytes, *, context: str) -> Any:
    def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise UpstreamError(f"{context} contains duplicate key: {key}")
            result[key] = value
        return result

    def no_nonfinite_constant(value: str) -> None:
        raise UpstreamError(f"{context} contains non-standard JSON constant: {value}")

    try:
        text = raw.decode("utf-8")
        return json.loads(
            text,
            object_pairs_hook=no_duplicate_keys,
            parse_constant=no_nonfinite_constant,
        )
    except UnicodeDecodeError as exc:
        raise UpstreamError(f"{context} is not valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise UpstreamError(f"{context} is not valid JSON") from exc
    except RecursionError as exc:
        raise UpstreamError(f"{context} is nested too deeply") from exc


def _generated_parity(preview: BootstrapResult) -> dict[str, Any]:
    categories = {
        "created": preview.created,
        "updated": preview.updated,
        "pending_updates": preview.pending_updates,
        "stale_managed": preview.stale_managed,
        "conflicts": preview.conflicts,
    }
    differences = {
        category: sorted(path for path in paths if path != ".pk-stack/discovery.json")
        for category, paths in categories.items()
    }
    differences = {category: paths for category, paths in differences.items() if paths}
    return {
        "ok": preview.ok and not differences,
        "dry_run": preview.dry_run,
        "update_managed": preview.update_managed,
        "differences": differences,
    }


__all__ = [
    "BLOB_BINDING_CONSTRAINT",
    "DEFAULT_MANIFEST",
    "DEFAULT_POWER_ROOT",
    "DEFAULT_PROPOSAL",
    "DEFAULT_TIMEOUT_SECONDS",
    "GITHUB_API_ORIGIN",
    "GITHUB_COMPARE_FILE_CAP",
    "MAX_COMPARE_BLOB_BYTES",
    "MAX_COMPARE_COMMITS",
    "MAX_COMPARE_DIFF_CELLS",
    "MAX_COMPARE_FILES",
    "MAX_COMPARE_PATCH_BYTES",
    "MAX_DIFF_LINES",
    "MAX_FILE_PATCH_BYTES",
    "MAX_MANIFEST_BYTES",
    "MAX_PROVENANCE_BYTES",
    "MAX_RESPONSE_BYTES",
    "MAX_REVIEW_LEDGER_BYTES",
    "MAX_REVIEW_TRANSITIONS",
    "MAX_TEXT_BLOB_BYTES",
    "MAX_TIMEOUT_SECONDS",
    "MAX_TREE_ENTRIES",
    "NO_PATCH_CONSTRAINT",
    "PATCH_COUNT_CONSTRAINT",
    "TREE_ENTRY_CONSTRAINT",
    "UPSTREAM_SCHEMA_VERSION",
    "UpstreamError",
    "UpstreamManifest",
    "UpstreamSource",
    "accept_upstream",
    "check_upstreams",
    "load_upstream_manifest",
    "load_upstream_review_ledger",
]
