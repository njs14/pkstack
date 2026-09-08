# Grok advisory council review

Conclusion: ADVISORY_CONCERNS

The ownership split is visible in the Python services, Power-local setup shim, and skill text: Kiro is not reimplemented, native `/goal` is not claimed, ACP/`/spawn` are not hidden defaults, and OKF stays optional. Round-1 wrapper isolation, feature-map JSON errors, operand screening, and post-setup `/agent swap pstack` are present in source. They are not enough. The stored-verifier policy still exempts an absolute argv[0], so an outside binary can become the only completion contract; the “read-only” subagent profiles still have general `shell`; and the recommended post-setup `pstack` session has no working Power-local upgrade path.

## Scope matrix

| Area | Status |
| --- | --- |
| 1. Architecture | finding |
| 2. Kiro CLI v3 / current session | clear |
| 3. `projectctl` / Cyclopts | finding |
| 4. Optional OKF | clear |
| 5. Feature maps | finding |
| 6. Verified-goal loop | finding |
| 7. Bootstrap / idempotence | finding |
| 8. Permissions / hooks / safety | finding |
| 9. Tests / docs / provenance | finding |
| 10. Fake capabilities | clear |

## Material findings

### GRK-011 — HIGH — Absolute argv[0] is exempt, so an outside binary can be stored as the completion contract

**Citations:** `src/pstack_kiro/runner.py:31-47`, `src/pstack_kiro/runner.py:195-196`, `src/pstack_kiro/goal.py:193-217`, `src/pstack_kiro/features.py:211-215`, `docs/architecture.md:254-259`, `tests/test_runner.py:32-36`, `tests/test_hardening.py:484-508`

**Observed:** `_reject_path_escape` claims to cover “direct executables, interpreter scripts, nested tool operands, and `--option=../path` forms”. For every token it then does:

```python
if executable and path.is_absolute():
    return
```

`executable` is true only for argv[0]. Relative argv[0] (`../outside/verifier`) and non-zero operands (`python /tmp/outside.py`, `uv run python ../outside.py`) are rejected. An absolute argv[0] is not. `enforce_verification_policy` is the same screen used by `feature validate`, `--ready` generation, `goal start`, and every `run_command`. `start_goal` persists the contract after that screen and does not execute it first. Tests cover `[sys.executable, "/tmp/outside.py"]` and `f"{sys.executable} ../outside.py"`, not `["/tmp/outside"]`.

**Violated contract:** Architecture says the policy rejects “path operands that resolve outside the project root” at ready proof, map validation, goal start, and every run. The closed GRK-003 criterion required rejection of outside path operands, including interpreter scripts, before persistence. A stored verifier is the only completion gate.

**Failure scenario:** In a bootstrapped project:

```bash
.pstack/bin/projectctl goal start "prove it" --command /tmp/pstack-outside-verifier --output json
```

Policy allows it; `.pstack/state/goal.json` is created with that argv. A later `goal verify` executes `/tmp/pstack-outside-verifier` with `cwd` at the project root. The same argv in `Wiki/features/*.md` passes `feature validate` and can be selected by `/verified-goal` via `--feature`. `/usr/bin/python3` as argv[0] is a legitimate system interpreter; `/tmp/pstack-outside-verifier` is the same exemption.

**Fix task:** Screen argv[0] the same way as other path-shaped tokens when the token contains a path separator or is an absolute path that is not the PATH-resolved image of a bare basename (`shutil.which(Path(argv[0]).name) == argv[0]`). Keep bare names (`python3`, `uv`, `pytest`) and real PATH interpreters; reject `/tmp/...` and other non-PATH absolute executables before feature write or goal persistence. Extend the existing escape tests accordingly.

**Acceptance test:** In an isolated bootstrapped project, create `/tmp/pstack-outside-verifier` as `#!/bin/sh` / `exit 0`, then run `.pstack/bin/projectctl goal start "x" --command /tmp/pstack-outside-verifier --output json`. Repeat with a ready feature whose `verification.command` is that path and with `feature validate --output json`. **Expected after fix:** exit 2 (start) / validate `ok: false`; `error_type` `CommandRejected` or path-qualified `FeatureMapError` / `GoalError`; no `.pstack/state/goal.json`. **Current expected failure:** start `ok: true`, status `active`, contract argv `["/tmp/pstack-outside-verifier"]`; validate `ok: true`.

---

### GRK-012 — MEDIUM — “Read-only” architect/reviewer profiles still grant general `shell`

**Citations:** `templates/project/.kiro/agents/pstack-architect.json:3-9`, `templates/project/.kiro/agents/pstack-architect.json:36-56`, `templates/project/.kiro/agents/pstack-reviewer.json:3-9`, `templates/project/.kiro/agents/pstack-reviewer.json:36-56`, `templates/project/.kiro/agents/pstack.json:105-109`, `docs/usage.md:264-271`, `tests/test_kiro_assets.py:234-241`

**Observed:** Both profiles describe themselves as “Read-only”, omit `write`, and deny `fs_write` on `./**`. They still include `shell`. Allowed shell is read-only Git. Denied shell is a short list (`rm *`, `git reset *`, `git clean *`, `sudo *`, terraform apply/destroy, aws delete/terminate). There is no catch-all shell deny and no default shell effect. The primary profile marks these agents `trustedAgents`. Asset tests only assert that `write` is absent and that allow-listed shell patterns do not mention `projectctl`.

**Violated contract:** Least privilege for architecture/review subagents is the documented reason they exist. `fs_write` deny does not bind `python`, `cp`, `mv`, `tee`, `sed -i`, or `chmod` delivered through `shell`. “Read-only” is a profile claim, not a tool/permission fact.

**Failure scenario:** Primary agent, after `/agent swap pstack`, spawns `pstack-architect` or `pstack-reviewer` (trusted, so spawn may not be confirmed). That subagent runs `python3 -c 'open("src/app.py","w").write("broken")'` or `tee`. The call does not match `fs_write` or the small shell deny list. Workspace mutation happens on a profile the user was told cannot edit.

**Fix task:** Either omit `shell` from architect/reviewer, or add a default/`*` shell deny and keep only the Git allow list. Remove “Read-only” from the JSON descriptions unless shell mutation is actually denied. Assert the catch-all deny (or omitted `shell`) in `tests/test_kiro_assets.py`.

**Acceptance test:** Load both JSON profiles in the unit test and fail if `shell` is present unless a deny rule matches a documented catch-all (for example `*` or an explicit default shell deny) that would apply to `python3 *`, `cp *`, and `tee *`. **Expected after fix:** test passes only with omitted `shell` or catch-all deny. **Current expected failure:** both profiles include `shell` and deny only the listed destructive patterns.

---

### GRK-013 — MEDIUM — Post-setup `pstack` session cannot upgrade from the loaded Power; `projectctl setup` re-sources the cache

**Citations:** `src/pstack_kiro/bootstrap.py:199-210`, `src/pstack_kiro/bootstrap.py:245-252`, `src/pstack_kiro/cli.py:84-100`, `skills/setup-pstack/SKILL.md:13-32`, `skills/setup-pstack/SKILL.md:55-73`, `templates/project/.kiro/agents/pstack.json:12-13`, `tests/test_bootstrap.py:52-55`, `docs/usage.md:179-194`

**Observed:** The setup skill is Power-local and is deliberately not copied to `.kiro/skills/` (tested). After setup the user must `/agent swap pstack`. That profile sets `includePowers: false`, so `/setup-pstack` is not a workspace skill and is not loaded from the Power. The remaining public setup command is `.pstack/bin/projectctl setup`. With `power_root=None`, `bootstrap_project` uses `Path(__file__).parents[2]`. Under the wrapper that is `.pstack/projectctl`, whose `src/pstack_kiro` directory exists, so the cached snapshot is treated as the Power. Doctor compares live Kiro assets to that same cache, not to the loaded Power. The documented `--update-managed` path is the python3 shim in usage; no workspace skill remaining after swap names that shim.

**Violated contract:** “The Power-local `skills/setup-pstack/scripts/setup_pstack.py` is the setup and upgrade authority.” After the required agent handoff, that authority is not on the session’s skill surface, and the repo-local CLI that skills are told to use is not that authority.

**Failure scenario:** Power v2 changes `.kiro/agents/pstack.json` deny/ask rules. The user is in the recommended `pstack` session. `/setup-pstack` is missing. The agent runs `.pstack/bin/projectctl setup --dry-run --output json` (Cyclopts help advertises `setup`). Result is `ok: true` with no `pending_updates`, because cache matches live. Doctor also passes. The new permission profile never installs.

**Fix task:** Make wrapper `projectctl setup` fail closed unless `--power-root` points at a real Power (or remove the command from the repo-local CLI). Keep a post-swap upgrade seam: copy setup into workspace skills, or allow that one Power skill on the `pstack` profile, or put the Power-local shim invocation in always-on steering. Add a test that a bootstrapped wrapper dry-run does not treat `.pstack/projectctl` as an upgradable Power.

**Acceptance test:** Bootstrap project A from Power v1. Change only Power v1’s `templates/project/.kiro/agents/pstack.json`. From A, run `.pstack/bin/projectctl setup --dry-run --output json` with no `--power-root`. **Expected after fix:** exit 2, structured error that setup must use the Power-local shim / explicit `--power-root`; no claim of a clean managed upgrade. **Current expected failure:** `ok: true`, empty `pending_updates`.

## Low findings and notes

### GRK-014 — LOW — Older-Python setup fallback runs `uv run --locked --project` against the Power tree

`skills/setup-pstack/scripts/setup_pstack.py:17-42` execs `uv run --quiet --locked --project $POWER_ROOT python -m pstack_kiro.bootstrap` when `sys.version_info < (3, 11)`. First-time Power-local setup therefore syncs a venv into the Power checkout (and fails if that tree is not writable). The 3.11+ path only inserts `sys.path`. Docs present this as “ask uv for a compatible Python,” not as a Power-side install.

### GRK-015 — LOW — Gitignore membership is a substring test

`src/pstack_kiro/bootstrap.py:514-516` treats `.pstack/state/`, `.pstack/tmp/`, and `.pstack/projectctl/.venv/` as already ignored if those fragments appear anywhere in `.gitignore`, including comments. A comment-only match skips the ignore block. Doctor with a real `.git` uses `git check-ignore` and can still fail closed; doctor without git uses the same substring (`src/pstack_kiro/doctor.py:291-293`).

### GRK-016 — LOW — `readme.md` is invisible to list/validate

`src/pstack_kiro/features.py:157-159` and `191-192` skip any `*.md` whose name lowercases to `readme.md`. Slug `readme` is otherwise legal. On a case-insensitive volume, `feature generate readme` collides with the managed `Wiki/features/README.md` (overwrite-protected unless `--overwrite`). On a case-sensitive volume, `readme.md` can exist as an unlisted, unvalidated contract that `find_feature` / `goal start --feature readme` will still load.

### GRK-017 — LOW — Inline `-c`/`-e` detection requires a standalone token

`src/pstack_kiro/runner.py:128-134` rejects `python -c …` and `node -e …` only when `-c` / `-e` / `--eval` appear as their own argv words. `python3 -cimport os;os._exit(0)` does not match. This is denylist incompleteness on an acknowledged non-sandbox; it is listed because architecture names “inline interpreter evaluation” as rejected. Tests only use a separate `-c` token (`tests/test_runner.py:29`).

### GRK-018 — NOTE — Current-session and Stop-hook limits are instructional

`/verified-goal` tells the model to stay in the current `kiro-cli --v3` session and not use ACP, `/spawn`, nested Kiro, or native `/goal`. Nothing in `src/pstack_kiro` can enforce that. The Stop hook is disabled (`templates/project/.kiro/hooks/pstack-tripwire.json:13`) and `goal tripwire` is advisory (`src/pstack_kiro/goal.py:324-347`). That matches the docs; it is not a hidden scheduler and not a fake `/goal`.

### GRK-019 — NOTE — Round-1 material items look addressed in this tree

Statically: the wrapper now `uv sync`s then execs `.venv/bin/python` and the runner restores caller `PYTHONPATH` / strips `PSTACK_KIRO_CALLER_*` (`src/pstack_kiro/bootstrap.py:81-98`, `src/pstack_kiro/runner.py:245-257`); `load_feature` maps decode/parse failures to `FeatureMapError` (`src/pstack_kiro/features.py:78-81`, `115-117`); non-argv[0] path operands are screened (`src/pstack_kiro/runner.py:195-196`); setup/README/usage require `/agent swap pstack` or `kiro-cli chat --v3 --agent pstack`. This review did not execute those tests.

### GRK-020 — NOTE — Repository-reported Kiro/pytest campaigns are not evidence in this snapshot

`docs/validation-report.md` claims 148 passing tests, a live `kiro-cli` session, and coverage via `--cov-config=/Users/noahsutter/git-projects/codex/pyproject.toml`. Those are untrusted process claims, including a host path outside this repository. The example under `examples/verified-goal-demo/` is still intentionally red.

## Advisory remediation ledger

| ID | Fix task | Acceptance test | Status |
| --- | --- | --- | --- |
| GRK-011 | Treat absolute argv[0] as a path operand unless it is the PATH-resolved image of a bare interpreter name; reject `/tmp/...` before feature/goal persistence. | Isolated project: `goal start --command /tmp/pstack-outside-verifier --output json` and a feature contract with that command must exit nonzero, emit one JSON error object, and leave `goal.json` absent. | open |
| GRK-012 | Omit `shell` from architect/reviewer, or default-deny shell except the Git allow list; stop calling the profiles read-only unless that is true. | Asset test fails unless those profiles omit `shell` or have a catch-all shell deny covering `python3 *` / `cp *` / `tee *`. | open |
| GRK-013 | Fail wrapper `projectctl setup` without an explicit Power root; keep a post-swap upgrade seam (workspace setup skill, Power exception, or steering that names the shim). | After bootstrap, change only the Power’s `pstack.json`; `.pstack/bin/projectctl setup --dry-run --output json` must not report a clean no-op upgrade from the cache. | open |

## Design dissent and attack scenarios

1. **Deny-by-default shell.** The shipped primary profile allows Git, asks for a subset of `projectctl`, and denies a few destructive globs; architect/reviewer are the same shape with a “read-only” label (GRK-012). Unmatched `python`, `dd`, `sed`, `goal clear --force`, and `feature generate` are outside that table. This review cannot observe Kiro’s unmatched default. A default shell deny, plus ask only for exact `.pstack/bin/projectctl …` argv, would change whether GRK-012 and the residual compound-glob question are acceptance-blocking. Do not treat `trustedAgents` as a substitute for that default until Kiro’s spawn-vs-tool approval split is evidenced on 2.20.2.

2. **One setup authority.** After the required `pstack` swap, `/setup-pstack` is gone (`includePowers: false`, skill not materialized) and `.pstack/bin/projectctl setup` reads `.pstack/projectctl` (GRK-013). Collapsing setup to the Power-local shim only — and making wrapper `setup` refuse — removes a false upgrade path that can leave stale ask/deny profiles in place. That is the difference between “usage.md tells a human about python3” and “the current-session agent can actually refresh permissions.”

3. **Stored-verifier plant.** Write `Wiki/features/ok.md` with `draft: false` and `verification.command: /tmp/pstack-outside-verifier` (GRK-011), or start a goal with that argv. `feature validate` and `goal start` currently accept it. `/verified-goal` then treats that binary as the only pass condition: exit 0 marks `passed` without touching project tests. Relative `../outside.py` is already tested; this path is not.

## Evidence assessed and residual limitations

**Inspected source (this review):** `src/pstack_kiro/*.py`, `skills/**`, `templates/project/.kiro/agents/*.json`, `templates/project/.kiro/hooks/*.json`, `dev.kiro/steering/*.md`, `plugin.json`, `pyproject.toml`, `templates/projectctl/uv.lock` (header and `pstack-kiro` / `cyclopts` / `pyyaml` entries), `tests/*.py`, `docs/*.md`, `README.md`, `LICENSE` (header), `NOTICE`, `THIRD_PARTY_NOTICES.md`, `examples/verified-goal-demo/*`, `reviews/*` (process text, not findings).

**Inspected tests (static only):** bootstrap idempotence, conflicts, upgrades, stale paths, concurrency, symlinks, incomplete Power; feature schema, proof-before-write, overwrite-before-proof; goal transitions, digest, spec-bridge names, discard-on-change, fcntl fail-closed; runner hazards, PATH/PYTHONPATH restoration, descendant kill; CLI JSON for malformed features and Cyclopts coercion; packaging wheel + wrapper env probe; knowledge hyphen-query rejection; asset string contracts including `/agent swap pstack`. No test covers absolute argv[0] escape, catch-all shell deny on read-only profiles, or wrapper `setup` refusing to act as Power authority.

**Not executed (by contract):** no pytest, ruff, ty, uv, bootstrap, `kiro-cli`, or demo campaign. Live Kiro permission-matcher semantics (including whether compounds are split, what unmatched shell defaults to, and whether `trustedAgents` skip tool prompts), hook `enabled: false` handling, `/agent swap` discovery timing, and canonical `okn` behavior were not observed.

**Fake-capability search:** no `src/` invocation of ACP, `/spawn`, nested `kiro-cli`, or native `/goal`. Skills and docs disclaim those. OKF is optional and does not become proof. Workspace skills do not claim guaranteed Power discovery. The material issues above are control-plane / permission / upgrade defects, not invented Kiro features.
