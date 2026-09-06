"""Measure local link validation without network access or timing assertions.

Run with the Power's locked development environment. The output records every
sample after one warm-up; use the same arguments and interpreter for comparisons.
"""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from pathlib import Path

from pkstack.knowledge_links import validate_local_links


def measure(root: Path, samples: int) -> dict:
    expected = validate_local_links(root, root / "Wiki/knowledge")
    assert expected["ok"], expected
    seconds = []
    for _ in range(samples):
        start = time.perf_counter()
        actual = validate_local_links(root, root / "Wiki/knowledge")
        seconds.append(time.perf_counter() - start)
        assert actual == expected, (actual, expected)
    return {"result": expected, "seconds": seconds, "median_seconds": statistics.median(seconds)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=7)
    args = parser.parse_args()
    if args.samples < 5:
        parser.error("use at least five measured samples")
    repo = Path(__file__).resolve().parents[3]
    with tempfile.TemporaryDirectory(prefix="pkstack-link-benchmark-") as temporary:
        root = Path(temporary).resolve()
        knowledge = root / "Wiki/knowledge"
        knowledge.mkdir(parents=True)
        (root / "design.md").write_text(
            "\n".join(f"## Section {i}\n\nDesign paragraph {i}." for i in range(100)),
            encoding="utf-8",
        )
        for page in range(20):
            (knowledge / f"page-{page}.md").write_text(
                "\n".join(f"[section](../../design.md#section-{i})" for i in range(80)),
                encoding="utf-8",
            )
        print(
            json.dumps(
                {
                    "samples": args.samples,
                    "repository": measure(repo, args.samples),
                    "shared_target": measure(root, args.samples),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
