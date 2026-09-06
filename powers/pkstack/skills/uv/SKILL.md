---
name: uv
description: Manage Python projects, dependencies, environments, and standalone scripts with uv; preserve an existing Poetry or PDM workflow unless migration is requested.
---

# Python environments and scripts with uv

Inspect the project's manifest, lockfile, supported Python versions, and existing commands first.
Use uv for uv-managed projects and new Python work without another chosen manager. Preserve
Poetry or PDM projects unless the task includes migration. Do not install global tools or change
package indexes as a side effect of ordinary Python work.

## Choose the execution environment

- In a project, run `uv run <command>` from its manifest directory, or use
  `uv run --project <directory> <command>`. Use `--frozen` for reviewed locked CI and verification;
  update dependencies intentionally with `uv add` or `uv remove` and review the lockfile diff.
- Run a dependency-free standalone script with `uv run --no-project script.py`. For an isolated
  script with dependencies, declare PEP 723 inline metadata including `requires-python` and
  `dependencies`, then run `uv run script.py`. Inline metadata isolates the script from the
  project dependencies: do not add it to scripts that import the installed project.
- Use `uv run --python 3.12 python ...` to request an interpreter. `uvx python@3.12` is not an
  interpreter-selection command. Preserve the project's supported minimum version.
- Use `uvx <known-tool>@<version>` only for a tool outside the project's dependencies; prefer
  the project's locked tools when present. Never add a new requirements.txt to a uv project.
- Preserve a reviewed dependency-free bootstrap path that must run before uv exists. Child
  processes that need the active environment may correctly use `sys.executable`.

Prefer project or script lockfiles for maintained dependency-bearing workflows. Report any
intentional unlocked one-off command. Do not replace an isolated script environment with a
manual global pip install or activate an unrelated environment.

## Compose by responsibility

This skill owns dependency and execution choices. Read [ruff](../ruff/SKILL.md) for linting and
formatting and [ty](../ty/SKILL.md) for type checking. Keep the task's existing planning,
approval, test, and projectctl verification checkpoints; successful tool execution is not
proof of the requested behavior. In read-only planning, describe commands without running
synchronization or modifying the environment.

References: [uv projects](https://docs.astral.sh/uv/guides/projects/),
[uv scripts](https://docs.astral.sh/uv/guides/scripts/), and
[uv tools](https://docs.astral.sh/uv/guides/tools/).
