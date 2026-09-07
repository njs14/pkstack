**APPROVE**

Frozen candidate `9e9f327` against base `2fe0bab`. Independent read-only review of the 22-file delta. No material contract defects.

## Scope

Reviewed launcher parsing, receipt/wrapper checks, PATH sanitation, JSON/text errors, `execve`/signal boundary, version split, bootstrap interaction, verifier self-evidence (`pkstack` / `uv run` / `uvx`), real-wheel tests, docs, and CI. Did not execute or import candidate code. Targeted check counts below are coordinator-provided, not re-run here.

## Contract mapping

**Launcher vs controller.** `pkstack` is a new console script (`powers/pkstack/pyproject.toml` line 22). `setup`/`upgrade` call packaged `bootstrap_main` with `--root` and, for upgrade, `--update-managed` (`launcher.py` 167–188). Other commands `os.execve` the project wrapper with `[wrapper, command, *arguments]` (`launcher.py` 238–243). `--version` prints package `__version__`; `version` is forwarded (`launcher.py` 118–124, 141–151). `projectctl` and `pkstack-setup` remain.

**Project selection.** Default is `Path.cwd()` with no ancestor walk (`launcher.py` 142). `--project` is consumed only before the command; missing/empty values fail (`154–164`). Forwarded `--root` and post-command `--project` are rejected until `--` (`246–266`). Option *values* containing `--root` stay intact (`test_launcher.py` 191–200). Missing project directories are not created (`161–171`).

**Receipt is local ownership.** Wrapper must be a non-symlink executable whose bytes equal `INTERNAL_WRAPPER` (`269–305`). Receipt load uses existing schema/manager/hash checks; required runtime keys and `.pkstack/bin/` + `.pkstack/projectctl/` audit failures block; unrelated managed edits do not (`308–341`). Help states the receipt is not a signature (`73–75`). `INTERNAL_WRAPPER` is unchanged from the base, so a PR #53 controller can still be exec’d. Committed compatibility JSON records doctor/version against that controller with managed files unchanged and `launcher.py` absent from the old runtime.

**PATH and environment.** Only the leading PATH entry is dropped when it is this process’s venv `bin` (`344–365`). A second identical entry is kept (`410–417`). Missing PATH stays missing; `sys.prefix == sys.base_prefix` does not strip (`382–397`). `VIRTUAL_ENV`, `PYTHONPATH`, and caller `UV_*` are passed through (`210–226`). After `execve`, exit status and signals are the wrapper/controller’s; goal verify still SIGKILLs the verifier session on unwind (`runner.py` 1219–1282).

**Errors.** Launcher failures are exit 2: JSON `{ok, error, error_type}` when `--output json`/`--output=json` is present, otherwise stderr text (`93–107`). Bootstrap `SystemExit` is not remapped (`83–90`), so setup conflicts keep bootstrap JSON and exit 2.

**Verifier self-evidence.** `_CONTROL_PLANE_EXECUTABLES` now includes `pkstack` (`runner.py` 52). Tests cover `pkstack`, `uv run pkstack`, and `uvx ... pkstack` (`test_runner.py` 118–120). `uvx` was already denied; `python -m pkstack` remains denied.

**Docs and Python.** User docs use `uvx --python '>=3.11' --from "$PKSTACK_PACKAGE"` and warn against bare `uvx pkstack` (`usage.md` 15–20, 102–123, 204–225). Walkthrough tests execute those blocks; acceptance tests pin `sys.executable` so the harness does not pick macOS 3.9.

**CI.** `pull_request:` no longer limits to `main` (`pk-stack-ci.yml` 3–7). Artifact build/upload still `push && refs/heads/main` (236–250). Only that workflow changed under `.github/workflows/`; `pk-stack-release.yml` is untouched. `test_uvx_launcher_acceptance.py` is in the package lane (`pkstack_checks.py` 238–239).

**Real-wheel tests (source review).** Three tests: application setup/idempotency/conflict, launcher vs controller versions, explicit upgrade, fail-repair-pass, env isolation; SIGTERM process-group cancel with child reaping and no recorded attempt; application venv-only import (`test_uvx_launcher_acceptance.py` 167–535). Harness uses isolated `UV_TOOL_DIR`/`UV_CACHE_DIR` and `uv tool run --from` a local wheel.

Power and cached copies of `launcher.py`/`bootstrap.py`/`runner.py` are byte-identical. Receipt SHA-256 values match those files.

## Coordinator evidence (not re-run)

Recorded in `reviews/uvx-entrypoint/README.md` and logs under `/private/tmp/pkstack-uvx-evidence/`: 39 docs/launcher, 313 runner, 3 real-wheel, 11 packaging/distribution/release-metadata, static gate. `full-gate-v1.log` was still in the policy lane when inspected (pytest shards and script unittests had completed in that log; knowledge/doctor aggregation had not). Hosted CI on the stacked PR head was not inspected.

## Residuals (not blocking)

`powers/pkstack/docs/architecture.md` line 108 still calls `setup_pkstack.py` the only setup/upgrade authority. That describes Power-packaged bootstrap vs cached `projectctl setup` (which still requires `--power-root`). User-facing docs and the launcher use the packaged bootstrap through uvx. Changelog is still 0.4.3; this is not a release commit.

No requested changes.
