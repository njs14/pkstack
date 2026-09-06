---
name: ty
description: Check Python types with ty, repair type errors at their source, and configure coverage for maintained modules and scripts without suppressing failures.
---

# Python type checking with ty

Inspect `[tool.ty]` or `ty.toml`, supported Python versions, dependencies, and existing check
coverage. In a project with ty declared, run `uv run ty check`; use `uv run --frozen ty check`
for locked verification from the manifest directory. Read [uv](../uv/SKILL.md) for environment
selection. Preserve another chosen checker unless migration is within scope.

- Check the maintained application, tests, scripts, and templates that can execute as Python.
  Confirm configured include/exclude paths actually cover the changed files. Treat generated
  snapshots, vendored code, and deliberate negative fixtures according to their existing contract.
- Set the target to the project's supported Python minimum. Do not raise it merely to remove
  diagnostics. Resolve imports through the real project environment rather than a broad ignore.
- Repair type errors by validating external data and using truthful, narrow types. Do not add
  casts, `Any`, or ignore comments just to hide errors. Add an ignore only when the user explicitly
  requests it; use a rule-specific `ty: ignore[...]` and retain a concrete reason.
- Check targeted files during repair, then run the full configured type check. Verify runtime
  behavior with the affected tests; static success alone does not establish correctness.

Use [ruff](../ruff/SKILL.md) for lint and format. Preserve existing planning, permission, and
projectctl verification ownership. This Kiro skill does not configure a language server or
install the upstream Claude plugin; an LSP setup is a separate requested task.

Reference: [ty documentation](https://docs.astral.sh/ty/).
