---
name: ruff
description: Lint and format Python with Ruff using the project's configuration and pinned environment; review fixes against behavior and the requested scope.
---

# Python linting and formatting with Ruff

Inspect `pyproject.toml` or `ruff.toml` and the existing verification commands. In a uv project
with Ruff declared, use `uv run ruff`; for locked verification use `uv run --frozen ruff` from
the manifest directory. Read [uv](../uv/SKILL.md) for environment selection. Preserve another
chosen toolchain unless migration is within scope.

1. Run `ruff check <scope>` and `ruff format --check <scope>` to understand the baseline.
2. Preview lint changes with `ruff check --diff <scope>`. Apply appropriate fixes with
   `ruff check --fix <scope>` before formatting.
3. Preview formatting with `ruff format --diff <scope>`, then format the authorized scope.
   Broad formatting is appropriate when explicitly requested or already enforced by the project;
   otherwise keep unrelated files out of the diff.
4. Run the checks again and the behavioral tests affected by the edits. Formatting and lint
   success do not establish runtime correctness.

Keep the repository's configured rule sets and Python target. Do not blanket-disable checks
to get a green result. Unsafe fixes can change behavior: read the rule explanation and inspect
the proposed diff before applying an individual unsafe fix. Preserve import side effects and
intentional failing fixtures; treat vendored snapshots and historical evidence as immutable.

Ruff owns lint and format, [ty](../ty/SKILL.md) owns typing, and project tests plus projectctl
own behavioral verification. Reuse existing results rather than requiring duplicate check runs.
Respect native Kiro planning modes and current write permissions.

Reference: [Ruff documentation](https://docs.astral.sh/ruff/).
