"""Narrow, executable feature-map contracts backed by OKF-compatible Markdown."""

from __future__ import annotations

import json
import os
import re
import stat
import tempfile
import threading
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager, suppress
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode, ScalarNode
from yaml.resolver import BaseResolver

from pk_stack.models import FeatureEntrypoint, FeatureSpec, FeatureSubFeature
from pk_stack.paths import WorkspacePathError, workspace_path
from pk_stack.runner import (
    CommandRejected,
    display_command,
    enforce_verification_policy,
    parse_command,
)

try:
    import fcntl
except ImportError:  # pragma: no cover - PK-Stack currently targets macOS/Linux
    fcntl = None  # type: ignore[assignment]

FEATURES_DIRECTORY = Path("Wiki/features")
FEATURE_SCHEMA_VERSION = 2
MIN_INITIAL_FEATURES = 1
MAX_INITIAL_FEATURES = 5
MAX_FEATURE_PLAN_BYTES = 256 * 1024
MAX_FEATURE_DOCUMENT_BYTES = 512 * 1024
MAX_FEATURE_ROLLBACK_BYTES = 4 * 1024 * 1024
FEATURE_MAP_LOCK = Path(".pk-stack/state/feature-map.lock")
_FEATURE_MAP_THREAD_LOCK = threading.Lock()
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_H2 = re.compile(r"^##\s+([^\n]+?)\s*$", re.MULTILINE)
_RESERVED_SLUGS = {"readme"}
_FEATURE_PLAN_KEYS = {"features"}
_FEATURE_DEFINITION_KEYS = {
    "slug",
    "title",
    "behavior",
    "expected_path",
    "command",
    "related",
    "sub_features",
    "entrypoints",
    "gotchas",
    "evidence_boundary",
    "cleanup_boundary",
}


class FeatureMapError(ValueError):
    """Raised when a feature contract is missing or malformed."""


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that refuses mappings whose meaning depends on key order."""


def _construct_unique_mapping(
    loader: _UniqueKeySafeLoader,
    node: MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeySafeLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _valid_slug(value: str) -> bool:
    return bool(_SLUG.fullmatch(value)) and value not in _RESERVED_SLUGS


def feature_directory(root: Path) -> Path:
    try:
        return workspace_path(root, FEATURES_DIRECTORY)
    except WorkspacePathError as exc:
        raise FeatureMapError(str(exc)) from exc


def _read_bounded_bytes(path: Path, *, limit: int, label: str) -> bytes:
    """Read one regular file with pre/post identity, size, and growth checks."""

    try:
        before = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise FeatureMapError(f"cannot inspect {label}: {path}: {exc}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise FeatureMapError(f"{label} is not a regular file: {path}")
    if before.st_size > limit:
        raise FeatureMapError(f"{label} exceeds the {limit}-byte limit")
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise FeatureMapError(f"{label} is not a regular file: {path}")
            data = handle.read(limit + 1)
            after_read = os.fstat(handle.fileno())
        after_path = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise FeatureMapError(f"cannot read {label}: {path}: {exc}") from exc
    if len(data) > limit or after_read.st_size > limit:
        raise FeatureMapError(f"{label} exceeds the {limit}-byte limit")
    expected_identity = (before.st_dev, before.st_ino)
    if (
        (opened.st_dev, opened.st_ino) != expected_identity
        or (after_read.st_dev, after_read.st_ino) != expected_identity
        or (after_path.st_dev, after_path.st_ino) != expected_identity
        or before.st_size != len(data)
        or after_read.st_size != len(data)
        or after_path.st_size != len(data)
    ):
        raise FeatureMapError(f"{label} changed during its bounded read")
    return data


def _read_feature_bytes(path: Path) -> bytes:
    return _read_bounded_bytes(
        path,
        limit=MAX_FEATURE_DOCUMENT_BYTES,
        label="feature document",
    )


def _decode_feature_bytes(data: bytes, *, path: Path) -> str:
    try:
        return data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise FeatureMapError(f"{path}: feature file is not valid UTF-8: {exc}") from exc


def _frontmatter(text: str, *, path: Path) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FeatureMapError(f"{path}: expected YAML frontmatter")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise FeatureMapError(f"{path}: unterminated YAML frontmatter") from exc
    try:
        raw = yaml.load("\n".join(lines[1:end]), Loader=_UniqueKeySafeLoader) or {}
    except yaml.YAMLError as exc:
        raise FeatureMapError(f"{path}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(raw, dict):
        raise FeatureMapError(f"{path}: frontmatter must be a mapping")
    return raw, "\n".join(lines[end + 1 :]).strip()


def _section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n(?P<content>.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(body)
    return match.group("content").strip() if match else ""


def _subsections(section: str, *, level: int, label: str, path: Path) -> list[tuple[str, str]]:
    marker = "#" * level
    pattern = re.compile(
        rf"^{marker}\s+`?(?P<identifier>[a-z0-9]+(?:-[a-z0-9]+)*)`?\s*$\n"
        rf"(?P<content>.*?)(?=^{marker}\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    matches = list(pattern.finditer(section))
    headings = re.findall(rf"^{marker}\s+([^\n]+?)\s*$", section, re.MULTILINE)
    if len(headings) != len(matches):
        raise FeatureMapError(
            f"{path}: {label} contains an invalid or unstructured level-{level} heading"
        )
    if not matches or section[: matches[0].start()].strip():
        raise FeatureMapError(f"{path}: {label} must contain identifier subsections")
    parsed: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in matches:
        identifier = match.group("identifier")
        content = match.group("content").strip()
        if identifier in seen:
            raise FeatureMapError(f"{path}: duplicate {label} identifier {identifier!r}")
        if not content:
            raise FeatureMapError(f"{path}: {label} {identifier!r} must be non-empty")
        seen.add(identifier)
        parsed.append((identifier, content))
    return parsed


def _drive_parts(body: str, *, identifier: str, path: Path) -> tuple[str, str]:
    pattern = re.compile(
        r"^####\s+(?P<heading>[^\n]+?)\s*$\n(?P<content>.*?)(?=^####\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    matches = list(pattern.finditer(body))
    if (
        len(matches) != 2
        or body[: matches[0].start()].strip()
        or [match.group("heading") for match in matches] != ["Recipe", "Observable proof"]
    ):
        raise FeatureMapError(
            f"{path}: drive recipe {identifier!r} must contain exactly "
            "'#### Recipe' then '#### Observable proof'"
        )
    drive, observable = (match.group("content").strip() for match in matches)
    if not drive or not observable:
        raise FeatureMapError(
            f"{path}: drive recipe {identifier!r} requires non-empty recipe and proof"
        )
    return drive, observable


def _parse_gotchas(body: str, *, path: Path) -> tuple[str, ...]:
    section = _section(body, "Gotchas")
    if not section:
        raise FeatureMapError(f"{path}: missing non-empty '## Gotchas' section")
    lines = section.splitlines()
    if any(not line.startswith("- ") or not line[2:].strip() for line in lines):
        raise FeatureMapError(f"{path}: Gotchas must be non-empty single-line bullets")
    return tuple(line[2:].strip() for line in lines)


def _parse_structured_sections(
    body: str,
    *,
    path: Path,
) -> tuple[
    tuple[FeatureSubFeature, ...],
    tuple[FeatureEntrypoint, ...],
    tuple[str, ...],
    str,
    str,
]:
    sub_feature_section = _section(body, "Sub-features")
    if not sub_feature_section:
        raise FeatureMapError(f"{path}: missing non-empty '## Sub-features' section")
    raw_sub_features = _subsections(
        sub_feature_section,
        level=3,
        label="Sub-features",
        path=path,
    )
    sub_features = tuple(
        FeatureSubFeature(identifier=identifier, behavior=behavior)
        for identifier, behavior in raw_sub_features
    )

    user_section = _section(body, "How to get to it (user POV)")
    drive_section = _section(body, "Driving it")
    if not user_section:
        raise FeatureMapError(f"{path}: missing non-empty '## How to get to it (user POV)' section")
    if not drive_section:
        raise FeatureMapError(f"{path}: missing non-empty '## Driving it' section")
    user_paths = _subsections(user_section, level=3, label="entrypoint", path=path)
    drive_recipes = _subsections(drive_section, level=3, label="drive recipe", path=path)
    user_ids = [identifier for identifier, _ in user_paths]
    drive_ids = [identifier for identifier, _ in drive_recipes]
    if user_ids != drive_ids:
        raise FeatureMapError(
            f"{path}: every user entrypoint must have one same-order drive recipe"
        )
    entrypoints: list[FeatureEntrypoint] = []
    for (identifier, user_path), (_, recipe_body) in zip(user_paths, drive_recipes, strict=True):
        drive, observable = _drive_parts(recipe_body, identifier=identifier, path=path)
        entrypoints.append(
            FeatureEntrypoint(
                identifier=identifier,
                user_path=user_path,
                drive=drive,
                observable=observable,
            )
        )

    evidence_boundary = _section(body, "Evidence boundary")
    cleanup_boundary = _section(body, "Cleanup boundary")
    if not evidence_boundary:
        raise FeatureMapError(f"{path}: missing non-empty '## Evidence boundary' section")
    if not cleanup_boundary:
        raise FeatureMapError(f"{path}: missing non-empty '## Cleanup boundary' section")
    return (
        sub_features,
        tuple(entrypoints),
        _parse_gotchas(body, path=path),
        evidence_boundary,
        cleanup_boundary,
    )


def load_feature(path: Path, *, root: Path | None = None) -> FeatureSpec:
    project_root = root.resolve() if root else path.resolve().parents[2]
    try:
        path = workspace_path(project_root, path)
    except WorkspacePathError as exc:
        raise FeatureMapError(str(exc)) from exc
    expected_directory = feature_directory(project_root)
    try:
        path.relative_to(expected_directory)
    except ValueError as exc:
        raise FeatureMapError(f"{path}: feature must live under {expected_directory}") from exc
    if path.suffix.lower() != ".md":
        raise FeatureMapError(f"{path}: feature files must be Markdown")

    text = _decode_feature_bytes(_read_feature_bytes(path), path=path)

    return _parse_feature_text(text, path=path, project_root=project_root)


def _parse_feature_text(text: str, *, path: Path, project_root: Path) -> FeatureSpec:
    """Parse one feature document, including a not-yet-written candidate."""

    metadata, body = _frontmatter(text, path=path)
    if metadata.get("type") != "feature":
        raise FeatureMapError(f"{path}: frontmatter type must be 'feature'")

    schema_version = metadata.get("schema_version")
    if type(schema_version) is not int or schema_version != FEATURE_SCHEMA_VERSION:
        raise FeatureMapError(f"{path}: schema_version must be {FEATURE_SCHEMA_VERSION}")
    allowed_metadata = {
        "type",
        "schema_version",
        "slug",
        "title",
        "draft",
        "verification",
        "related",
    }
    unknown_metadata = set(metadata) - allowed_metadata
    if unknown_metadata:
        raise FeatureMapError(
            f"{path}: unknown frontmatter fields: "
            f"{', '.join(sorted(repr(item) for item in unknown_metadata))}"
        )

    slug = metadata.get("slug", path.stem)
    if type(slug) is not str:
        raise FeatureMapError(f"{path}: slug must be a string")
    if not _valid_slug(slug):
        raise FeatureMapError(f"{path}: invalid feature slug {slug!r}")
    if slug != path.stem:
        raise FeatureMapError(f"{path}: slug must match the file name")

    title = metadata.get("title")
    if not isinstance(title, str) or not title.strip():
        raise FeatureMapError(f"{path}: title must be a non-empty string")

    verification = metadata.get("verification", {})
    if not isinstance(verification, dict):
        raise FeatureMapError(f"{path}: verification must be a mapping")
    unknown_verification = set(verification) - {"command"}
    if unknown_verification:
        raise FeatureMapError(f"{path}: verification contains unknown fields")
    if "command" in verification:
        raw_command = verification["command"]
        if not (
            isinstance(raw_command, str)
            or (
                isinstance(raw_command, list)
                and raw_command
                and all(type(item) is str for item in raw_command)
            )
        ):
            raise FeatureMapError(
                f"{path}: verification command must be a string or non-empty list of strings"
            )
        try:
            command = parse_command(raw_command)
        except CommandRejected as exc:
            raise FeatureMapError(f"{path}: {exc}") from exc
    else:
        command = None

    raw_related = metadata.get("related", [])
    if not isinstance(raw_related, list) or not all(isinstance(item, str) for item in raw_related):
        raise FeatureMapError(f"{path}: related must be a list of relative paths")

    behavior = _section(body, "User behavior")
    expected_path = _section(body, "Expected path")
    if not behavior:
        raise FeatureMapError(f"{path}: missing non-empty '## User behavior' section")
    if not expected_path:
        raise FeatureMapError(f"{path}: missing non-empty '## Expected path' section")

    if "draft" not in metadata:
        raise FeatureMapError(f"{path}: draft must be present and must be a boolean")
    raw_draft = metadata["draft"]
    if type(raw_draft) is not bool:
        raise FeatureMapError(f"{path}: draft must be a boolean")

    expected_headings = [
        "User behavior",
        "Expected path",
        "Sub-features",
        "How to get to it (user POV)",
        "Driving it",
        "Evidence boundary",
        "Cleanup boundary",
        "Gotchas",
        "Verification",
    ]
    actual_headings = [heading.strip() for heading in _H2.findall(body)]
    if actual_headings != expected_headings:
        raise FeatureMapError(
            f"{path}: schema 2 requires exactly these ordered level-2 sections: "
            f"{', '.join(expected_headings)}"
        )
    if not _section(body, "Verification"):
        raise FeatureMapError(f"{path}: missing non-empty '## Verification' section")
    (
        sub_features,
        entrypoints,
        gotchas,
        evidence_boundary,
        cleanup_boundary,
    ) = _parse_structured_sections(body, path=path)

    feature = FeatureSpec(
        slug=slug,
        title=title.strip(),
        path=str(path.relative_to(project_root)),
        behavior=behavior,
        expected_path=expected_path,
        command=command,
        related=tuple(raw_related),
        draft=raw_draft,
        sub_features=sub_features,
        entrypoints=entrypoints,
        gotchas=gotchas,
        evidence_boundary=evidence_boundary,
        cleanup_boundary=cleanup_boundary,
    )
    return feature


def _related_path_errors(
    project_root: Path,
    feature: FeatureSpec,
    *,
    require_exists: bool = True,
) -> list[str]:
    """Return portable containment/existence errors for a feature's related paths."""

    errors: list[str] = []
    source = project_root / feature.path
    for related in feature.related:
        relative = Path(related)
        if not related.strip() or relative.is_absolute():
            errors.append(f"{feature.path}: related path must be relative and non-empty: {related}")
            continue
        try:
            target = (source.parent / relative).resolve()
            target.relative_to(project_root)
        except ValueError:
            errors.append(f"{feature.path}: related path escapes the project: {related}")
            continue
        except (OSError, RuntimeError) as exc:
            errors.append(f"{feature.path}: related path cannot be resolved: {related}: {exc}")
            continue
        try:
            present = target.exists()
        except OSError as exc:
            errors.append(f"{feature.path}: related path cannot be inspected: {related}: {exc}")
            continue
        if require_exists and not present:
            errors.append(f"{feature.path}: related path does not exist: {related}")
    return errors


def list_features(root: Path) -> list[FeatureSpec]:
    directory = feature_directory(root)
    if not directory.exists():
        return []
    return [
        load_feature(path, root=root)
        for path in sorted(directory.glob("*.md"))
        if path.name.lower() != "readme.md"
    ]


def find_feature(root: Path, slug: str) -> FeatureSpec:
    if not _valid_slug(slug):
        raise FeatureMapError(f"invalid feature slug {slug!r}")
    path = feature_directory(root) / f"{slug}.md"
    if not path.is_file():
        raise FeatureMapError(f"feature {slug!r} not found at {path}")
    return load_feature(path, root=root)


def find_verifiable_feature(root: Path, slug: str) -> FeatureSpec:
    """Return a published feature with an executable acceptance contract."""

    feature = find_feature(root, slug)
    if feature.draft:
        raise FeatureMapError(
            f"feature {slug!r} is still a draft; publish it before using it as "
            "verification evidence"
        )
    if not feature.command:
        raise FeatureMapError(f"feature {slug!r} has no executable verification command")
    return feature


def feature_output_path(root: Path, slug: str, *, overwrite: bool = False) -> Path:
    """Validate a generation target without creating directories or running proof."""

    if slug in _RESERVED_SLUGS:
        raise FeatureMapError(f"feature slug {slug!r} is reserved for managed documentation")
    if not _valid_slug(slug):
        raise FeatureMapError("slug must contain lowercase letters, numbers, and single hyphens")
    try:
        path = workspace_path(root, FEATURES_DIRECTORY / f"{slug}.md")
    except WorkspacePathError as exc:
        raise FeatureMapError(str(exc)) from exc
    if path.exists() and not overwrite:
        raise FeatureMapError(f"refusing to overwrite existing feature contract: {path}")
    return path


def validate_feature_map(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    features: list[FeatureSpec] = []
    directory = feature_directory(root)
    if not directory.is_dir():
        errors.append(f"missing feature-map directory: {directory}")
    else:
        for path in sorted(directory.glob("*.md")):
            if path.name.lower() == "readme.md":
                continue
            try:
                feature = load_feature(path, root=root)
                features.append(feature)
            except (FeatureMapError, OSError) as exc:
                errors.append(str(exc))

    seen: set[str] = set()
    project_root = root.resolve()
    for feature in features:
        if feature.slug in seen:
            errors.append(f"duplicate feature slug: {feature.slug}")
        seen.add(feature.slug)
        if feature.draft:
            warnings.append(f"{feature.path}: contract is still marked draft")
        if not feature.command and feature.draft:
            warnings.append(f"{feature.path}: no executable verification command")
        elif not feature.command:
            errors.append(f"{feature.path}: ready contract has no executable verification command")
        if feature.command:
            try:
                enforce_verification_policy(feature.command, root=project_root)
            except CommandRejected as exc:
                errors.append(f"{feature.path}: rejected verification command: {exc}")
        errors.extend(_related_path_errors(project_root, feature))

    return {
        "ok": not errors,
        "feature_count": len(features),
        "features": [feature.to_dict() for feature in features],
        "errors": errors,
        "warnings": warnings,
    }


def _normalize_sub_features(
    values: Iterable[FeatureSubFeature | tuple[str, str]] | None,
) -> tuple[FeatureSubFeature, ...]:
    if values is None:
        return ()
    normalized: list[FeatureSubFeature] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, FeatureSubFeature):
            item = value
        elif isinstance(value, tuple) and len(value) == 2:
            item = FeatureSubFeature(identifier=value[0], behavior=value[1])
        else:
            raise FeatureMapError("sub-features must be FeatureSubFeature values or string pairs")
        if type(item.identifier) is not str or not _SLUG.fullmatch(item.identifier):
            raise FeatureMapError("sub-feature identifiers must be lowercase hyphenated names")
        if item.identifier in seen:
            raise FeatureMapError(f"duplicate sub-feature identifier {item.identifier!r}")
        if type(item.behavior) is not str or not item.behavior.strip():
            raise FeatureMapError(f"sub-feature {item.identifier!r} behavior must be non-empty")
        seen.add(item.identifier)
        normalized.append(
            FeatureSubFeature(identifier=item.identifier, behavior=item.behavior.strip())
        )
    return tuple(normalized)


def _normalize_entrypoints(
    values: Iterable[FeatureEntrypoint | tuple[str, str, str, str]] | None,
) -> tuple[FeatureEntrypoint, ...]:
    if values is None:
        return ()
    normalized: list[FeatureEntrypoint] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, FeatureEntrypoint):
            item = value
        elif isinstance(value, tuple) and len(value) == 4:
            item = FeatureEntrypoint(
                identifier=value[0],
                user_path=value[1],
                drive=value[2],
                observable=value[3],
            )
        else:
            raise FeatureMapError(
                "entrypoints must be FeatureEntrypoint values or four-string tuples"
            )
        if type(item.identifier) is not str or not _SLUG.fullmatch(item.identifier):
            raise FeatureMapError("entrypoint identifiers must be lowercase hyphenated names")
        if item.identifier in seen:
            raise FeatureMapError(f"duplicate entrypoint identifier {item.identifier!r}")
        fields = {
            "user path": item.user_path,
            "drive recipe": item.drive,
            "observable proof": item.observable,
        }
        for label, field_value in fields.items():
            if type(field_value) is not str or not field_value.strip():
                raise FeatureMapError(f"entrypoint {item.identifier!r} {label} must be non-empty")
        seen.add(item.identifier)
        normalized.append(
            FeatureEntrypoint(
                identifier=item.identifier,
                user_path=item.user_path.strip(),
                drive=item.drive.strip(),
                observable=item.observable.strip(),
            )
        )
    return tuple(normalized)


def _normalize_gotchas(values: Iterable[str] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not value.strip():
            raise FeatureMapError("gotchas must be non-empty strings")
        if "\n" in value or "\r" in value:
            raise FeatureMapError("each gotcha must fit on one line")
        normalized.append(value.strip())
    return tuple(normalized)


def _render_structured_sections(
    *,
    sub_features: tuple[FeatureSubFeature, ...],
    entrypoints: tuple[FeatureEntrypoint, ...],
    gotchas: tuple[str, ...],
    evidence_boundary: str,
    cleanup_boundary: str,
) -> str:
    sub_feature_text = "\n\n".join(
        f"### `{item.identifier}`\n\n{item.behavior}" for item in sub_features
    )
    user_path_text = "\n\n".join(
        f"### `{item.identifier}`\n\n{item.user_path}" for item in entrypoints
    )
    drive_text = "\n\n".join(
        f"### `{item.identifier}`\n\n"
        f"#### Recipe\n\n{item.drive}\n\n"
        f"#### Observable proof\n\n{item.observable}"
        for item in entrypoints
    )
    gotcha_text = "\n".join(f"- {item}" for item in gotchas)
    return (
        f"## Sub-features\n\n{sub_feature_text}\n\n"
        f"## How to get to it (user POV)\n\n{user_path_text}\n\n"
        f"## Driving it\n\n{drive_text}\n\n"
        f"## Evidence boundary\n\n{evidence_boundary}\n\n"
        f"## Cleanup boundary\n\n{cleanup_boundary}\n\n"
        f"## Gotchas\n\n{gotcha_text}\n\n"
    )


def _render_feature_document(
    *,
    slug: str,
    title: str,
    behavior: str,
    expected_path: str,
    command: tuple[str, ...] | None,
    related: Sequence[str],
    draft: bool,
    sub_features: tuple[FeatureSubFeature, ...],
    entrypoints: tuple[FeatureEntrypoint, ...],
    gotchas: tuple[str, ...],
    evidence_boundary: str,
    cleanup_boundary: str,
) -> str:
    metadata: dict[str, Any] = {
        "type": "feature",
        "slug": slug,
        "title": title,
        "draft": draft,
    }
    metadata["schema_version"] = FEATURE_SCHEMA_VERSION
    if command:
        metadata["verification"] = {"command": list(command)}
    if related:
        metadata["related"] = list(related)

    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).strip()
    command_text = (
        display_command(command) if command else "Not established yet. Keep `draft: true`."
    )
    structured_text = _render_structured_sections(
        sub_features=sub_features,
        entrypoints=entrypoints,
        gotchas=gotchas,
        evidence_boundary=evidence_boundary,
        cleanup_boundary=cleanup_boundary,
    )
    return (
        f"---\n{frontmatter}\n---\n\n"
        f"# {title}\n\n"
        f"## User behavior\n\n{behavior}\n\n"
        f"## Expected path\n\n{expected_path}\n\n"
        f"{structured_text}"
        f"## Verification\n\n`{command_text}`\n\n"
        "A passing command proves the behavior described above, not merely that files exist.\n"
    )


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise FeatureMapError(f"feature plan JSON contains duplicate key {key!r}")
        value[key] = item
    return value


def _strict_string(value: object, *, field: str) -> str:
    if type(value) is not str or not value.strip():
        raise FeatureMapError(f"feature plan {field} must be a non-empty string")
    return value.strip()


def load_feature_plan(root: Path, definition: Path) -> list[dict[str, Any]]:
    """Load an exact, bounded 1-5 record initial feature-map definition."""

    project_root = root.resolve()
    try:
        path = workspace_path(project_root, definition)
    except WorkspacePathError as exc:
        raise FeatureMapError(str(exc)) from exc
    if not path.is_file():
        raise FeatureMapError(f"feature plan does not exist as a regular file: {path}")
    try:
        data = _read_bounded_bytes(
            path,
            limit=MAX_FEATURE_PLAN_BYTES,
            label="feature plan",
        )
        raw = json.loads(data.decode("utf-8"), object_pairs_hook=_object_without_duplicate_keys)
    except UnicodeDecodeError as exc:
        raise FeatureMapError("feature plan is not valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise FeatureMapError(f"feature plan is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != _FEATURE_PLAN_KEYS:
        raise FeatureMapError("feature plan must be an exact object containing only 'features'")
    definitions = raw["features"]
    if not isinstance(definitions, list) or not (
        MIN_INITIAL_FEATURES <= len(definitions) <= MAX_INITIAL_FEATURES
    ):
        raise FeatureMapError(
            f"initial feature plan must contain "
            f"{MIN_INITIAL_FEATURES}-{MAX_INITIAL_FEATURES} records"
        )

    result: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()
    for index, definition_value in enumerate(definitions, 1):
        if (
            not isinstance(definition_value, dict)
            or set(definition_value) != _FEATURE_DEFINITION_KEYS
        ):
            raise FeatureMapError(f"feature plan record {index} does not match the exact schema")
        slug = _strict_string(definition_value["slug"], field=f"record {index} slug")
        if not _valid_slug(slug):
            raise FeatureMapError(f"feature plan record {index} has invalid slug {slug!r}")
        if slug in seen_slugs:
            raise FeatureMapError(f"feature plan contains duplicate slug {slug!r}")
        seen_slugs.add(slug)

        raw_command = definition_value["command"]
        if not (
            type(raw_command) is str
            or (
                isinstance(raw_command, list)
                and raw_command
                and all(type(item) is str for item in raw_command)
            )
        ):
            raise FeatureMapError(
                f"feature plan record {slug!r} command must be a string or non-empty string list"
            )
        raw_related = definition_value["related"]
        if not isinstance(raw_related, list) or not all(type(item) is str for item in raw_related):
            raise FeatureMapError(f"feature plan record {slug!r} related must be a string list")

        raw_sub_features = definition_value["sub_features"]
        if not isinstance(raw_sub_features, list):
            raise FeatureMapError(f"feature plan record {slug!r} sub_features must be a list")
        sub_features: list[FeatureSubFeature] = []
        for item in raw_sub_features:
            if not isinstance(item, dict) or set(item) != {"identifier", "behavior"}:
                raise FeatureMapError(f"feature plan record {slug!r} has malformed sub-feature")
            sub_features.append(
                FeatureSubFeature(identifier=item["identifier"], behavior=item["behavior"])
            )

        raw_entrypoints = definition_value["entrypoints"]
        if not isinstance(raw_entrypoints, list):
            raise FeatureMapError(f"feature plan record {slug!r} entrypoints must be a list")
        entrypoints: list[FeatureEntrypoint] = []
        for item in raw_entrypoints:
            if not isinstance(item, dict) or set(item) != {
                "identifier",
                "user_path",
                "drive",
                "observable",
            }:
                raise FeatureMapError(f"feature plan record {slug!r} has malformed entrypoint")
            entrypoints.append(
                FeatureEntrypoint(
                    identifier=item["identifier"],
                    user_path=item["user_path"],
                    drive=item["drive"],
                    observable=item["observable"],
                )
            )
        raw_gotchas = definition_value["gotchas"]
        if not isinstance(raw_gotchas, list):
            raise FeatureMapError(f"feature plan record {slug!r} gotchas must be a list")
        result.append(
            {
                "slug": slug,
                "title": _strict_string(definition_value["title"], field=f"record {slug!r} title"),
                "behavior": _strict_string(
                    definition_value["behavior"], field=f"record {slug!r} behavior"
                ),
                "expected_path": _strict_string(
                    definition_value["expected_path"],
                    field=f"record {slug!r} expected_path",
                ),
                "command": raw_command,
                "related": raw_related,
                "sub_features": _normalize_sub_features(sub_features),
                "entrypoints": _normalize_entrypoints(entrypoints),
                "gotchas": _normalize_gotchas(raw_gotchas),
                "evidence_boundary": _strict_string(
                    definition_value["evidence_boundary"],
                    field=f"record {slug!r} evidence_boundary",
                ),
                "cleanup_boundary": _strict_string(
                    definition_value["cleanup_boundary"],
                    field=f"record {slug!r} cleanup_boundary",
                ),
            }
        )
    return result


def prepare_initial_feature_map(
    root: Path,
    definition: Path,
    *,
    representative: str,
    overwrite: bool = False,
) -> list[tuple[Path, str, FeatureSpec]]:
    """Prepare 1-5 records while publishing only the representative contract."""

    definitions = load_feature_plan(root, definition)
    matches = [item for item in definitions if item["slug"] == representative]
    if len(matches) != 1:
        raise FeatureMapError("--representative must name exactly one feature-plan record")
    prepared: list[tuple[Path, str, FeatureSpec]] = []
    project_root = root.resolve()
    for item in definitions:
        draft = item["slug"] != representative
        path, text = prepare_feature(
            project_root,
            item["slug"],
            title=item["title"],
            behavior=item["behavior"],
            expected_path=item["expected_path"],
            command=item["command"],
            related=item["related"],
            draft=draft,
            overwrite=overwrite,
            sub_features=item["sub_features"],
            entrypoints=item["entrypoints"],
            gotchas=item["gotchas"],
            evidence_boundary=item["evidence_boundary"],
            cleanup_boundary=item["cleanup_boundary"],
        )
        feature = _parse_feature_text(text, path=path, project_root=project_root)
        prepared.append((path, text, feature))
    return prepared


@contextmanager
def _feature_map_lock(root: Path) -> Iterator[None]:
    if fcntl is None:
        raise FeatureMapError("feature-map locking requires POSIX fcntl")
    try:
        path = workspace_path(root, FEATURE_MAP_LOCK)
    except WorkspacePathError as exc:
        raise FeatureMapError(str(exc)) from exc
    with _FEATURE_MAP_THREAD_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.parent.chmod(0o700)
        with path.open("a+", encoding="utf-8") as handle:
            path.chmod(0o600)
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _checked_feature_target(root: Path, path: Path) -> Path:
    project_root = root.resolve()
    try:
        checked = workspace_path(project_root, path)
    except WorkspacePathError as exc:
        raise FeatureMapError(str(exc)) from exc
    directory = feature_directory(project_root)
    if checked != path or checked.parent != directory or checked.suffix.lower() != ".md":
        raise FeatureMapError(f"feature target is not canonical: {path}")
    if not _valid_slug(checked.stem):
        raise FeatureMapError(f"feature target has invalid slug: {path}")
    return checked


def _current_feature_bytes(path: Path) -> bytes | None:
    if not path.exists():
        return None
    return _read_feature_bytes(path)


def snapshot_feature_target(root: Path, path: Path, *, overwrite: bool) -> bytes | None:
    """Capture the exact pre-proof bytes in the shared feature mutation domain."""

    project_root = root.resolve()
    with _feature_map_lock(project_root):
        checked = _checked_feature_target(project_root, path)
        current = _current_feature_bytes(checked)
        if current is not None and not overwrite:
            raise FeatureMapError(f"refusing to overwrite existing feature contract: {checked}")
        return current


def snapshot_existing_feature(root: Path, slug: str) -> tuple[FeatureSpec, Path, bytes]:
    """Read one existing contract and its compare-and-swap bytes under the shared lock."""

    project_root = root.resolve()
    if not _valid_slug(slug):
        raise FeatureMapError(f"invalid feature slug {slug!r}")
    path = feature_directory(project_root) / f"{slug}.md"
    with _feature_map_lock(project_root):
        checked = _checked_feature_target(project_root, path)
        data = _current_feature_bytes(checked)
        if data is None:
            raise FeatureMapError(f"feature {slug!r} not found at {checked}")
        feature = _parse_feature_text(
            _decode_feature_bytes(data, path=checked),
            path=checked,
            project_root=project_root,
        )
        return feature, checked, data


def write_prepared_feature_if_unchanged(
    root: Path,
    path: Path,
    data: bytes,
    *,
    expected: bytes | None,
) -> Path:
    """Compare exact bytes and install one candidate while holding the shared lock."""

    project_root = root.resolve()
    checked = _checked_feature_target(project_root, path)
    if len(data) > MAX_FEATURE_DOCUMENT_BYTES:
        raise FeatureMapError(
            f"feature document exceeds the {MAX_FEATURE_DOCUMENT_BYTES}-byte limit"
        )
    _parse_feature_text(
        _decode_feature_bytes(data, path=checked),
        path=checked,
        project_root=project_root,
    )
    with _feature_map_lock(project_root):
        checked = _checked_feature_target(project_root, path)
        current = _current_feature_bytes(checked)
        if current != expected:
            if expected is None and current is not None:
                raise FeatureMapError(f"refusing to overwrite existing feature contract: {checked}")
            raise FeatureMapError(
                f"feature {checked.stem!r} changed during verification; candidate was not written"
            )
        _atomic_write_bytes(checked, data, overwrite=expected is not None)
    return checked


def prepare_published_feature_bytes(
    root: Path,
    path: Path,
    data: bytes,
    feature: FeatureSpec,
) -> bytes:
    """Patch only the YAML draft scalar, preserving every other accepted byte."""

    if not feature.draft:
        raise FeatureMapError(f"feature {feature.slug!r} is already published")
    project_root = root.resolve()
    checked = _checked_feature_target(project_root, path)
    related_errors = _related_path_errors(project_root, feature)
    if related_errors:
        raise FeatureMapError(related_errors[0])
    text = _decode_feature_bytes(data, path=checked)
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise FeatureMapError(f"{checked}: expected YAML frontmatter")
    yaml_start = len(lines[0])
    yaml_end: int | None = None
    offset = yaml_start
    for line in lines[1:]:
        if line.strip() == "---":
            yaml_end = offset
            break
        offset += len(line)
    if yaml_end is None:
        raise FeatureMapError(f"{checked}: unterminated YAML frontmatter")
    yaml_text = text[yaml_start:yaml_end]
    try:
        node = yaml.compose(yaml_text, Loader=yaml.SafeLoader)
    except yaml.YAMLError as exc:
        raise FeatureMapError(f"{checked}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(node, MappingNode):
        raise FeatureMapError(f"{checked}: frontmatter must be a mapping")
    draft_values = [
        value_node
        for key_node, value_node in node.value
        if isinstance(key_node, ScalarNode) and key_node.value == "draft"
    ]
    if len(draft_values) != 1 or not isinstance(draft_values[0], ScalarNode):
        raise FeatureMapError(f"{checked}: draft must appear exactly once as a scalar")
    value_node = draft_values[0]
    start = yaml_start + value_node.start_mark.index
    end = yaml_start + value_node.end_mark.index
    published_text = text[:start] + "false" + text[end:]
    published = _parse_feature_text(published_text, path=checked, project_root=project_root)
    if published != replace(feature, draft=False):
        raise FeatureMapError(f"{checked}: surgical publication changed more than the draft state")
    return published_text.encode("utf-8")


def _stage_feature_file(path: Path, text: str) -> Path:
    descriptor, temporary = tempfile.mkstemp(prefix=".pk-stack-map-stage-", dir=path.parent)
    staged = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        staged.chmod(0o644)
        return staged
    except BaseException:
        staged.unlink(missing_ok=True)
        raise


def _install_feature_file(source: Path, target: Path, *, replace_existing: bool) -> None:
    """Install one stage, using a hard-link create when clobber is not authorized."""

    if replace_existing:
        os.replace(source, target)
    else:
        os.link(source, target)


def _restore_feature_file(path: Path, data: bytes, mode: int) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".pk-stack-map-rollback-", dir=path.parent)
    replacement = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        replacement.chmod(mode)
        os.replace(replacement, path)
    except BaseException:
        replacement.unlink(missing_ok=True)
        raise


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def snapshot_prepared_feature_map(
    root: Path,
    prepared: Sequence[tuple[Path, str, FeatureSpec]],
    *,
    overwrite: bool,
) -> dict[Path, bytes | None]:
    """Capture every pre-proof map target under the common mutation lock."""

    project_root = root.resolve()
    with _feature_map_lock(project_root):
        snapshots: dict[Path, bytes | None] = {}
        for path, _, _ in prepared:
            checked = _checked_feature_target(project_root, path)
            current = _current_feature_bytes(checked)
            if current is not None and not overwrite:
                raise FeatureMapError(f"refusing to overwrite existing feature contract: {checked}")
            snapshots[checked] = current
        return snapshots


def write_prepared_feature_map(
    root: Path,
    prepared: Sequence[tuple[Path, str, FeatureSpec]],
    *,
    overwrite: bool,
    expected: dict[Path, bytes | None],
) -> list[Path]:
    """Stage a validated map and roll back the complete batch on an I/O failure."""

    if not MIN_INITIAL_FEATURES <= len(prepared) <= MAX_INITIAL_FEATURES:
        raise FeatureMapError(
            f"initial feature map must contain "
            f"{MIN_INITIAL_FEATURES}-{MAX_INITIAL_FEATURES} records"
        )
    project_root = root.resolve()
    directory = feature_directory(project_root)
    paths = [path for path, _, _ in prepared]
    if len(set(paths)) != len(paths):
        raise FeatureMapError("initial feature map contains duplicate output paths")
    if set(expected) != set(paths):
        raise FeatureMapError("initial feature-map snapshot does not match its targets")

    for path, text, feature in prepared:
        try:
            canonical = workspace_path(
                project_root,
                FEATURES_DIRECTORY / f"{feature.slug}.md",
            )
        except WorkspacePathError as exc:
            raise FeatureMapError(str(exc)) from exc
        if path != canonical or path.parent != directory:
            raise FeatureMapError(f"initial feature target is not canonical: {path}")
        if feature.path != str(path.relative_to(project_root)):
            raise FeatureMapError(f"initial feature target disagrees with its contract: {path}")
        parsed = _parse_feature_text(text, path=path, project_root=project_root)
        if parsed != feature:
            raise FeatureMapError(f"prepared feature text disagrees with its contract: {path}")

    directory_was_missing = not directory.exists()
    with _feature_map_lock(project_root):
        try:
            directory = feature_directory(project_root)
            directory.mkdir(parents=True, exist_ok=True)
        except (OSError, WorkspacePathError) as exc:
            raise FeatureMapError(f"cannot prepare the feature-map directory: {exc}") from exc
        if not directory.is_dir():
            raise FeatureMapError(f"feature-map path is not a directory: {directory}")

        checked_paths: list[Path] = []
        for _, _, feature in prepared:
            try:
                checked = workspace_path(
                    project_root,
                    FEATURES_DIRECTORY / f"{feature.slug}.md",
                )
            except WorkspacePathError as exc:
                raise FeatureMapError(str(exc)) from exc
            checked_paths.append(checked)
        originals: dict[Path, tuple[bytes, int] | None] = {}
        staged: dict[Path, Path] = {}
        installed: list[Path] = []
        rollback_bytes = 0
        try:
            for path, (_, text, _) in zip(checked_paths, prepared, strict=True):
                current = _current_feature_bytes(path)
                if current != expected[path]:
                    raise FeatureMapError(
                        f"feature {path.stem!r} changed during representative verification; "
                        "no map was written"
                    )
                if current is not None:
                    remaining = MAX_FEATURE_ROLLBACK_BYTES - rollback_bytes
                    if remaining <= 0:
                        raise FeatureMapError(
                            "existing feature contracts exceed the bounded rollback snapshot"
                        )
                    original = _read_bounded_bytes(
                        path,
                        limit=min(MAX_FEATURE_DOCUMENT_BYTES, remaining),
                        label="feature rollback snapshot",
                    )
                    if original != current:
                        raise FeatureMapError(
                            f"feature {path.stem!r} changed while preparing rollback; "
                            "no map was written"
                        )
                    rollback_bytes += len(original)
                    originals[path] = (original, stat.S_IMODE(path.stat().st_mode))
                else:
                    originals[path] = None
                staged[path] = _stage_feature_file(path, text)

            for path in checked_paths:
                _install_feature_file(
                    staged[path],
                    path,
                    replace_existing=expected[path] is not None and overwrite,
                )
                installed.append(path)
            _fsync_directory(directory)
        except BaseException as exc:
            rollback_errors: list[str] = []
            for path in reversed(installed):
                snapshot = originals[path]
                try:
                    if snapshot is None:
                        path.unlink(missing_ok=True)
                    else:
                        _restore_feature_file(path, snapshot[0], snapshot[1])
                except OSError as rollback_exc:
                    rollback_errors.append(f"{path}: {rollback_exc}")
            try:
                _fsync_directory(directory)
            except OSError as rollback_exc:
                rollback_errors.append(f"{directory}: {rollback_exc}")
            if rollback_errors:
                raise FeatureMapError(
                    "initial feature-map write failed and rollback was incomplete: "
                    + "; ".join(rollback_errors)
                ) from exc
            if isinstance(exc, FeatureMapError):
                raise
            raise FeatureMapError(
                f"initial feature-map write failed and was rolled back: {exc}"
            ) from exc
        finally:
            for temporary in staged.values():
                temporary.unlink(missing_ok=True)
            if directory_was_missing:
                with suppress(OSError):
                    directory.rmdir()
    return paths


def generate_feature(
    root: Path,
    slug: str,
    *,
    title: str,
    behavior: str,
    expected_path: str,
    command: str | Sequence[str] | None,
    related: Iterable[str] = (),
    draft: bool = True,
    overwrite: bool = False,
    sub_features: Iterable[FeatureSubFeature | tuple[str, str]] | None = None,
    entrypoints: Iterable[FeatureEntrypoint | tuple[str, str, str, str]] | None = None,
    gotchas: Iterable[str] | None = None,
    evidence_boundary: str | None = None,
    cleanup_boundary: str | None = None,
) -> Path:
    path, text = prepare_feature(
        root,
        slug,
        title=title,
        behavior=behavior,
        expected_path=expected_path,
        command=command,
        related=related,
        draft=draft,
        overwrite=overwrite,
        sub_features=sub_features,
        entrypoints=entrypoints,
        gotchas=gotchas,
        evidence_boundary=evidence_boundary,
        cleanup_boundary=cleanup_boundary,
    )
    before = snapshot_feature_target(root, path, overwrite=overwrite)
    return write_prepared_feature_if_unchanged(
        root,
        path,
        text.encode("utf-8"),
        expected=before,
    )


def prepare_feature(
    root: Path,
    slug: str,
    *,
    title: str,
    behavior: str,
    expected_path: str,
    command: str | Sequence[str] | None,
    related: Iterable[str] = (),
    draft: bool = True,
    overwrite: bool = False,
    sub_features: Iterable[FeatureSubFeature | tuple[str, str]] | None = None,
    entrypoints: Iterable[FeatureEntrypoint | tuple[str, str, str, str]] | None = None,
    gotchas: Iterable[str] | None = None,
    evidence_boundary: str | None = None,
    cleanup_boundary: str | None = None,
) -> tuple[Path, str]:
    """Build and validate the exact feature document without writing it."""

    project_root = root.resolve()
    path = feature_output_path(project_root, slug, overwrite=overwrite)
    if not title.strip() or not behavior.strip() or not expected_path.strip():
        raise FeatureMapError("title, behavior, and expected path must be non-empty")
    if not draft and command is None:
        raise FeatureMapError("a ready contract requires an executable verification command")

    normalized_sub_features = _normalize_sub_features(sub_features)
    normalized_entrypoints = _normalize_entrypoints(entrypoints)
    normalized_gotchas = _normalize_gotchas(gotchas)
    if not normalized_sub_features:
        raise FeatureMapError("schema 2 requires at least one non-empty sub-feature")
    if not normalized_entrypoints:
        raise FeatureMapError("schema 2 requires at least one user entrypoint and drive recipe")
    if not normalized_gotchas:
        raise FeatureMapError("schema 2 requires at least one gotcha")
    if not isinstance(evidence_boundary, str) or not evidence_boundary.strip():
        raise FeatureMapError("schema 2 requires a non-empty evidence boundary")
    if not isinstance(cleanup_boundary, str) or not cleanup_boundary.strip():
        raise FeatureMapError("schema 2 requires a non-empty cleanup boundary")
    normalized_evidence_boundary = evidence_boundary.strip()
    normalized_cleanup_boundary = cleanup_boundary.strip()

    argv = parse_command(command) if command is not None else None
    if argv:
        enforce_verification_policy(argv, root=root.resolve())
    related_list = list(related)
    if not all(type(item) is str for item in related_list):
        raise FeatureMapError("related paths must be strings")
    text = _render_feature_document(
        slug=slug,
        title=title.strip(),
        behavior=behavior.strip(),
        expected_path=expected_path.strip(),
        command=argv,
        related=related_list,
        draft=draft,
        sub_features=normalized_sub_features,
        entrypoints=normalized_entrypoints,
        gotchas=normalized_gotchas,
        evidence_boundary=normalized_evidence_boundary,
        cleanup_boundary=normalized_cleanup_boundary,
    )
    if len(text.encode("utf-8")) > MAX_FEATURE_DOCUMENT_BYTES:
        raise FeatureMapError(
            f"feature document exceeds the {MAX_FEATURE_DOCUMENT_BYTES}-byte limit"
        )
    parsed = _parse_feature_text(text, path=path, project_root=project_root)
    expected = FeatureSpec(
        slug=slug,
        title=title.strip(),
        path=str(path.relative_to(project_root)),
        behavior=behavior.strip(),
        expected_path=expected_path.strip(),
        command=argv,
        related=tuple(related_list),
        draft=draft,
        sub_features=normalized_sub_features,
        entrypoints=normalized_entrypoints,
        gotchas=normalized_gotchas,
        evidence_boundary=normalized_evidence_boundary,
        cleanup_boundary=normalized_cleanup_boundary,
    )
    if parsed != expected:
        raise FeatureMapError(
            "feature content does not round-trip through the generated Markdown structure; "
            "do not inject structural headings into feature fields"
        )
    related_errors = _related_path_errors(project_root, parsed, require_exists=not draft)
    if related_errors:
        raise FeatureMapError(related_errors[0])
    return path, text


def _atomic_write_bytes(path: Path, data: bytes, *, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if overwrite:
            os.replace(temporary, path)
        else:
            try:
                os.link(temporary, path)
            except FileExistsError as exc:
                message = f"refusing to overwrite existing feature contract: {path}"
                raise FeatureMapError(message) from exc
            Path(temporary).unlink()
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
