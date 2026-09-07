#!/usr/bin/env python3
"""Read-only repository knowledge coverage and local Wiki validation.

Run with the locked Power environment. This repository policy is not a
consumer-project manifest, a synchronizer, or a semantic completeness test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "maintenance/knowledge-coverage.json"
MARKDOWN = {".md", ".markdown"}
CATEGORIES = {"native", "generated", "vendor", "policy", "historical-fixture", "historical"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def relative_path(value):
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or any(ord(char) < 32 for char in value)
        or PurePosixPath(value).is_absolute()
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or ":" in value
    ):
        raise ValueError(f"unsafe repository path: {value!r}")
    return value


def safe_file(root, name, *, instruction_alias=False):
    relative_path(name)
    path = root
    for part in name.split("/"):
        path /= part
        if path.is_symlink():
            # This reviewed, repository-only instruction alias predates the gate.
            # Hash the link itself; no other symlink (including a parent) is allowed.
            if (
                instruction_alias
                and name == "CLAUDE.md"
                and path == root / name
                and os.readlink(path) == "AGENTS.md"
            ):
                safe_file(root, "AGENTS.md")
                return path
            raise ValueError(f"symlink is not a safe coverage source: {name}")
    if not path.is_file():
        raise ValueError(f"missing or non-file coverage source: {name}")
    return path


def inventory(root):
    # Include nonignored new files locally so a not-yet-staged document cannot
    # produce a misleading green result. CI checkouts ordinarily have none.
    raw = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    )
    return {
        relative_path(name)
        for name in raw.decode("utf-8").split("\0")
        if name and PurePosixPath(name).suffix.lower() in MARKDOWN
    }


def canonical(name):
    return (
        name == "Wiki/index.md" or name.startswith(("Wiki/knowledge/", "Wiki/features/"))
    ) and PurePosixPath(name).suffix.lower() == ".md"


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def backlinks(root, destination):
    from markdown_it import MarkdownIt

    path = safe_file(root, destination)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
        if end is not None:
            text = "\n".join(lines[end + 1 :])
    tokens = list(MarkdownIt("commonmark").parse(text))
    targets = set()
    while tokens:
        token = tokens.pop()
        tokens.extend(token.children or [])
        if token.type != "link_open":
            continue
        href = token.attrGet("href")
        if not isinstance(href, str):
            continue
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        target = (path.parent / unquote(parsed.path)).resolve()
        if target.is_relative_to(root):
            targets.add(target.relative_to(root).as_posix())
    return targets


def updater_delta(root, base, data):
    """Limit automated coverage edits to the source change under review.

    The trusted caller supplies the base commit. No source or hash is repaired.
    Existing exclusions cannot be widened and mapped knowledge cannot be dropped.
    """
    if not re.fullmatch(r"[0-9a-f]{40}", base):
        raise ValueError("updater coverage base must be a full commit SHA")
    before = json.loads(
        subprocess.check_output(["git", "-C", str(root), "show", f"{base}:{MANIFEST}"]),
        object_pairs_hook=unique_object,
    )
    if not isinstance(before, dict) or not isinstance(before.get("entries"), list):
        raise ValueError("updater base coverage manifest is invalid")
    old = {entry["path"]: entry for entry in before["entries"]}
    new = {entry["path"]: entry for entry in data["entries"]}
    raw = subprocess.check_output(
        ["git", "-C", str(root), "diff", "--name-only", "--no-renames", "-z", base]
    ) + subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "-z"]
    )
    changed = {name for name in raw.decode("utf-8").split("\0") if name}
    linked_topics = set()
    for name in sorted(old.keys() | new.keys()):
        prior, current = old.get(name), new.get(name)
        if name in changed:
            for entry in (prior, current):
                if entry and entry["classification"] == "mapped":
                    linked_topics.update(entry["topics"])
        if prior == current:
            continue
        if name not in changed:
            raise ValueError(f"updater changed unrelated coverage entry: {name}")
        if prior is None:
            if current is None:
                raise ValueError(f"updater coverage entry is missing: {name}")
            kind = current["classification"]
            if kind == "excluded" and not name.startswith(
                ("powers/pkstack/skills/", "powers/pkstack/dev.kiro/", ".kiro/")
            ):
                raise ValueError(f"updater cannot exclude a new authored document: {name}")
        elif current is None:
            if (root / name).exists() or prior["classification"] == "canonical":
                raise ValueError(f"updater cannot remove this coverage entry: {name}")
        elif prior["classification"] != current["classification"]:
            raise ValueError(f"updater cannot reclassify a source: {name}")
        elif current["classification"] == "mapped":
            if not set(prior["topics"]) <= set(current["topics"]):
                raise ValueError(f"updater cannot drop a mapped topic: {name}")
        elif current["classification"] == "excluded":
            if {k: v for k, v in prior.items() if k != "sha256"} != {
                k: v for k, v in current.items() if k != "sha256"
            }:
                raise ValueError(f"updater cannot widen an exclusion: {name}")
    for name in changed:
        if name.startswith("Wiki/knowledge/") and name not in linked_topics:
            raise ValueError(f"updater topic lacks a changed mapped source: {name}")


def validate(root, base=None):
    root = root.resolve()
    data = json.loads(safe_file(root, MANIFEST).read_text(), object_pairs_hook=unique_object)
    if not isinstance(data, dict) or set(data) != {"schema_version", "entries"}:
        raise ValueError("coverage manifest requires only schema_version and entries")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("unsupported coverage schema_version")
    entries = data["entries"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("coverage entries must be a nonempty list")
    documents = inventory(root)
    seen = {}
    issues = []
    counts = Counter()
    for entry in entries:
        try:
            if not isinstance(entry, dict):
                raise ValueError("coverage entry must be an object")
            name = relative_path(entry.get("path"))
            if name in seen:
                raise ValueError(f"duplicate classification: {name}")
            seen[name] = entry
            if name not in documents:
                raise ValueError(f"obsolete or non-Markdown classification: {name}")
            kind = entry.get("classification")
            if kind not in ("canonical", "mapped", "excluded"):
                raise ValueError(f"invalid classification: {name}")
            if canonical(name) and kind != "canonical":
                raise ValueError(f"Wiki knowledge cannot be reclassified: {name}")
            keys = {"path", "classification"}
            if kind == "canonical":
                if not canonical(name):
                    raise ValueError(f"canonical knowledge must be Wiki .md: {name}")
            else:
                keys |= {"sha256"}
                if kind == "mapped":
                    keys |= {"topics", "summary"}
                    topics = entry.get("topics")
                    if (
                        not isinstance(topics, list)
                        or not topics
                        or any(not isinstance(t, str) for t in topics)
                        or len(set(topics)) != len(topics)
                        or not nonempty(entry.get("summary"))
                    ):
                        raise ValueError(f"mapped source needs unique topics and summary: {name}")
                    for topic in topics:
                        relative_path(topic)
                        if not topic.startswith("Wiki/knowledge/") or not canonical(topic):
                            raise ValueError(f"destination must be a durable Wiki topic: {topic}")
                else:
                    keys |= {"category", "reason"}
                    if entry.get("category") not in tuple(CATEGORIES) or not nonempty(
                        entry.get("reason")
                    ):
                        raise ValueError(f"excluded source needs a category and rationale: {name}")
                sha = entry.get("sha256")
                if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
                    raise ValueError(f"source requires a SHA-256: {name}")
            if set(entry) != keys:
                raise ValueError(f"unexpected or missing coverage fields: {name}")
            alias = kind == "excluded" and entry.get("category") == "native"
            path = safe_file(root, name, instruction_alias=alias)
            if kind != "canonical":
                content = (
                    os.readlink(path).encode("utf-8") if path.is_symlink() else path.read_bytes()
                )
                if hashlib.sha256(content).hexdigest() != entry["sha256"]:
                    actual = hashlib.sha256(content).hexdigest()
                    raise ValueError(
                        f"stale source hash; reconsider knowledge or exclusion: {name}; "
                        f"current_sha256={actual}"
                    )
            counts[kind] += 1
        except (ValueError, OSError) as error:
            issues.append(str(error))
    issues.extend(f"unclassified Markdown: {name}" for name in sorted(documents - seen.keys()))
    parsed_links = {}
    for name, entry in seen.items():
        if entry.get("classification") != "mapped":
            continue
        topics = entry.get("topics")
        if not isinstance(topics, list):
            continue
        for topic in topics:
            try:
                relative_path(topic)
                if (
                    topic not in documents
                    or seen.get(topic, {}).get("classification") != "canonical"
                ):
                    raise ValueError(f"missing canonical destination for {name}: {topic}")
                if topic not in parsed_links:
                    parsed_links[topic] = backlinks(root, topic)
                if name not in parsed_links[topic]:
                    raise ValueError(f"missing source backlink in {topic}: {name}")
            except (ValueError, OSError) as error:
                issues.append(str(error))
    # Reuse the product's minimum metadata/link profile, without invoking its
    # runtime discovery, Kiro, okn, a model, or a consumer-project setup.
    from pkstack.knowledge_links import validate_local_links, validate_metadata

    for check in (validate_metadata, validate_local_links):
        try:
            result = check(root, root / "Wiki/knowledge")
            if not result["ok"]:
                issues.append(f"{check.__name__}: {json.dumps(result['issues'], sort_keys=True)}")
        except (ValueError, OSError) as error:
            issues.append(f"{check.__name__}: {error}")
    if base is not None and not issues:
        try:
            updater_delta(root, base, data)
        except (ValueError, OSError, subprocess.CalledProcessError) as error:
            issues.append(str(error))
    return {
        "ok": not issues,
        "documents": len(documents),
        "classifications": dict(sorted(counts.items())),
        "issues": issues,
        "limitations": "Coverage, source freshness and local Wiki metadata/links only; "
        "semantic completeness requires review. No live retrieval or full OKF conformance check.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--base", help="trusted base commit for source-scoped updater checks")
    args = parser.parse_args()
    try:
        result = validate(args.repo_root, args.base)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        result = {"ok": False, "issues": [str(error)]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
