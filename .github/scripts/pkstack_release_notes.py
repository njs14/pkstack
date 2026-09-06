#!/usr/bin/env python3
"""Extract the exact version's reviewed changelog body for a release."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit


def release_notes(changelog: str, tag: str) -> str:
    if not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag):
        raise ValueError("release tag must be vMAJOR.MINOR.PATCH")
    version = re.escape(tag[1:])
    headings = list(re.finditer(rf"(?m)^## \[{version}\](?:[^\n]*)$", changelog))
    if len(headings) != 1:
        raise ValueError("changelog must contain exactly one entry for the release version")
    remainder = changelog[headings[0].end() :]
    next_entry = re.search(r"(?m)^## ", remainder)
    body = remainder[: next_entry.start()] if next_entry else remainder
    body = body.strip()
    if not body:
        raise ValueError("release changelog entry is empty")
    return body + "\n"


def bind_repository_links(notes: str, repository: str, commit: str) -> str:
    """Keep changelog-relative links usable and immutable on the release page."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be owner/name")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("release commit must be a full Git SHA")
    base = f"https://github.com/{repository}/blob/{commit}/"

    def replace(match: re.Match[str]) -> str:
        target = match.group(1)
        if target.startswith(("#", "/")) or urlsplit(target).scheme:
            return match.group(0)
        return "](" + urljoin(base, target) + ")"

    return re.sub(r"\]\(([^)\s]+)\)", replace, notes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    try:
        notes = release_notes(args.changelog.read_text(encoding="utf-8"), args.tag)
        notes = bind_repository_links(notes, args.repository, args.commit)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(1, f"release notes: {exc}\n")
    print(notes, end="")


if __name__ == "__main__":
    main()
