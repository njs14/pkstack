"""Narrow, executable feature-map contracts backed by OKF-compatible Markdown."""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import yaml

from pstack_kiro.models import FeatureSpec
from pstack_kiro.paths import WorkspacePathError, workspace_path
from pstack_kiro.runner import (
    CommandRejected,
    display_command,
    enforce_verification_policy,
    parse_command,
)

FEATURES_DIRECTORY = Path("Wiki/features")
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_RESERVED_SLUGS = {"readme"}


class FeatureMapError(ValueError):
    """Raised when a feature contract is missing or malformed."""


def _valid_slug(value: str) -> bool:
    return bool(_SLUG.fullmatch(value)) and value not in _RESERVED_SLUGS


def feature_directory(root: Path) -> Path:
    try:
        return workspace_path(root, FEATURES_DIRECTORY)
    except WorkspacePathError as exc:
        raise FeatureMapError(str(exc)) from exc


def _frontmatter(text: str, *, path: Path) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FeatureMapError(f"{path}: expected YAML frontmatter")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise FeatureMapError(f"{path}: unterminated YAML frontmatter") from exc
    try:
        raw = yaml.safe_load("\n".join(lines[1:end])) or {}
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

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise FeatureMapError(f"{path}: feature file is not valid UTF-8: {exc}") from exc

    return _parse_feature_text(text, path=path, project_root=project_root)


def _parse_feature_text(text: str, *, path: Path, project_root: Path) -> FeatureSpec:
    """Parse one feature document, including a not-yet-written candidate."""

    metadata, body = _frontmatter(text, path=path)
    if metadata.get("type") != "feature":
        raise FeatureMapError(f"{path}: frontmatter type must be 'feature'")

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

    return FeatureSpec(
        slug=slug,
        title=title.strip(),
        path=str(path.relative_to(project_root)),
        behavior=behavior,
        expected_path=expected_path,
        command=command,
        related=tuple(raw_related),
        draft=raw_draft,
    )


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
    path = feature_directory(root) / f"{slug}.md"
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
    )
    _atomic_write(path, text, overwrite=overwrite)
    return path


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
) -> tuple[Path, str]:
    """Build and validate the exact feature document without writing it."""

    project_root = root.resolve()
    path = feature_output_path(project_root, slug, overwrite=overwrite)
    if not title.strip() or not behavior.strip() or not expected_path.strip():
        raise FeatureMapError("title, behavior, and expected path must be non-empty")
    if not draft and command is None:
        raise FeatureMapError("a ready contract requires an executable verification command")

    argv = parse_command(command) if command is not None else None
    if argv:
        enforce_verification_policy(argv, root=root.resolve())
    metadata: dict[str, Any] = {
        "type": "feature",
        "slug": slug,
        "title": title.strip(),
        "draft": draft,
    }
    if argv:
        metadata["verification"] = {"command": list(argv)}
    related_list = list(related)
    if not all(type(item) is str for item in related_list):
        raise FeatureMapError("related paths must be strings")
    if related_list:
        metadata["related"] = related_list

    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).strip()
    command_text = display_command(argv) if argv else "Not established yet. Keep `draft: true`."
    text = (
        f"---\n{frontmatter}\n---\n\n"
        f"# {title.strip()}\n\n"
        f"## User behavior\n\n{behavior.strip()}\n\n"
        f"## Expected path\n\n{expected_path.strip()}\n\n"
        f"## Verification\n\n`{command_text}`\n\n"
        "A passing command proves the behavior described above, not merely that files exist.\n"
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
    )
    if parsed != expected:
        raise FeatureMapError(
            "feature content does not round-trip through the generated Markdown structure; "
            "do not place level-2 headings in the title, user behavior, or expected path"
        )
    related_errors = _related_path_errors(project_root, parsed, require_exists=not draft)
    if related_errors:
        raise FeatureMapError(related_errors[0])
    return path, text


def _atomic_write(path: Path, text: str, *, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
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
