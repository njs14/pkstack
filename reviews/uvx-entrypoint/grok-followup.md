**APPROVE** (remediation `f218172` vs `8b46291`)

Test-only CI fix. It matches the hosted failure and does not reopen the launcher contract.

## What failed

Hosted run `34072770497` core-1/core-5: `uvx --from` a checkout could not resolve `cyclopts==4.23.2` because `_clean_environment` set `UV_OFFLINE=1` while inheriting `UV_CACHE_DIR` from `setup-uv` (`/home/runner/work/_temp/setup-uv-cache`). Locked `uv sync` does not populate the simple-index metadata `uvx` needs. Local runs hid this with a warm cache.

core-1: “network was disabled” / cyclopts not in cache (`hosted-core1-v1.log` ~426–430, 524).
core-5: uvx failed before any JSON docs (`hosted-core5-v1.log` ~373–384, `0 == 5`).

## What changed (three files)

`test_readme_walkthrough.py` 26–42: drop inherited `UV_*` and `UV_OFFLINE`; set per-`tmp_path` `UV_CACHE_DIR` / `UV_TOOL_DIR` / `UV_TOOL_BIN_DIR` (same pattern as `test_uvx_launcher_acceptance.py` 88–97).

`pkstack_checks.py` 238–243: `test_readme_walkthrough.py` → package lane (pypi.org / files.pythonhosted.org already allowed; workflow YAML unchanged).

`test_pkstack_checks.py` 175–177: partition assertion for that module.

No launcher, runtime, verifier, docs, release, artifact, or workflow-security edits. Prior approval of `9e9f327` still applies to the unchanged implementation.

## Coordinator evidence (not re-run here)

- Isolated-cache walkthrough: `3 passed in 58.01s` (`docs-isolated-cache.log`)
- 16 methods in `test_pkstack_checks.py` reported passing
- Static gate: `static-ci-fix.log` (ruff/ty/lock)

Hosted re-run of `f218172` is the remaining gate; this review did not execute tests.
