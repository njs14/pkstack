# Grok advisory council review

Conclusion: ADVISORY_CONCERNS

The ownership split (Kiro executes, pstack defines workflow, `projectctl` owns operability) is visible in the Python services, Power-local setup shim, and skill text. It is not enough. The managed `.pstack/bin/projectctl` wrapper is the required controller, yet verifier subprocesses inherit that wrapper’s `uv run` / `PYTHONPATH` environment, so a stored proof is not the same command a user would run in a clean project shell. Feature-map loading also lets a single malformed `verification.command` blow up `feature list --output json`, which `/verified-goal` uses before it can even start. Least-privilege agent profiles exist, but the documented default `kiro-cli chat --v3` path never selects them.

## Scope matrix

| Area | Status |
| --- | --- |
| 1. Architecture | finding |
| 2. Kiro CLI v3 / current session | clear |
| 3. `projectctl` / Cyclopts | finding |
| 4. Optional OKF | clear |
| 5. Feature maps | finding |
| 6. Verified-goal loop | finding |
| 7. Bootstrap / idempotence | clear |
| 8. Permissions / hooks / safety | finding |
| 9. Tests / docs / provenance | finding |
| 10. Fake capabilities | clear |

## Material findings

### GRK-001 — HIGH — Stored verifiers inherit the projectctl `uv run` environment

**Citations:** `src/pstack_kiro/bootstrap.py:81-88`, `src/pstack_kiro/runner.py:237-249`, `docs/architecture.md:119-130`, `README.md:55-61`, `tests/test_packaging.py:71-79`, `tests/test_cli.py:11-18`

**Observed:** The managed wrapper is:

```sh
PYTHONPATH="$PROJECTCTL_ROOT/src" exec uv run --quiet --locked \
  --project "$PROJECTCTL_ROOT" python -m pstack_kiro "$@"
```

`run_command` then does `process_env = os.environ.copy()` and `Popen(..., env=process_env)` with no scrub of `PYTHONPATH`, `VIRTUAL_ENV`, `PATH`, or `UV_*`. Architecture claims this runtime “isolates pstack from the host project's Python environment.” Isolation is one-way: pstack is isolated from the host, but host proofs are not isolated from pstack. The README’s ready-feature example is `uv run pytest ...`. Library and CLI tests invoke `python -m pstack_kiro`; the only wrapper execution in tests is `version` / `doctor`, which never spawn a user verifier.

**Violated contract:** A passing stored verifier is supposed to be the project’s executable predicate, not a child of the control-plane venv. Completion evidence from `.pstack/bin/projectctl goal verify` / `feature verify` / `feature generate --ready` can disagree with the same argv run in a clean project shell.

**Failure scenario:** After bootstrap, a host project whose tests need *its* venv records `--command "uv run pytest tests/test_foo.py -q"`. Outer `uv run --project .pstack/projectctl` leaves `PYTHONPATH=.pstack/projectctl/src` and typically `VIRTUAL_ENV` / `PATH` / `UV_PROJECT` pointing at the pstack runtime (no pytest; `package = false`). Inner `uv run pytest` then fails, uses the wrong interpreter, or imports from pstack’s `src`. Conversely, a stdlib-only script can pass through the wrapper and still be the wrong Python. The validation-report campaign used `python3 -m unittest`, which can hide this.

**Fix task:** Run user verifiers with a cleaned environment (restore the pre-wrapper `PATH` / `PYTHONPATH` / `VIRTUAL_ENV` / `UV_*`, or spawn via `env -u ...` / an explicit user env). Do not let `.pstack/projectctl/.venv` or `PYTHONPATH=.../projectctl/src` leak into proof processes. Add a wrapper-level test; do not treat `python -m pstack_kiro` as equivalent to `.pstack/bin/projectctl`.

**Acceptance test:** In an isolated bootstrapped project, write `envprobe.py` that prints `PYTHONPATH`, `VIRTUAL_ENV`, and `sys.executable`. Compare `python3 envprobe.py` in a clean shell with `.pstack/bin/projectctl feature generate env-probe --title T --behavior B --expected-path P --command "python3 envprobe.py" --ready --output json`. **Expected after fix:** JSON `ok: true` and probe output with no `.pstack/projectctl/src` on `PYTHONPATH` and no `VIRTUAL_ENV` under `.pstack/projectctl/.venv`. **Current expected failure:** wrapper-backed stdout includes `.pstack/projectctl/src` and/or a projectctl venv prefix.

---

### GRK-002 — HIGH — Malformed feature commands break JSON `feature list` on the verified-goal path

**Citations:** `src/pstack_kiro/features.py:97-110`, `src/pstack_kiro/features.py:141-148`, `src/pstack_kiro/cli.py:122-129`, `src/pstack_kiro/cli.py:133-140`, `src/pstack_kiro/runner.py:25-26`, `skills/verified-goal/SKILL.md:30`

**Observed:** `load_feature` calls `parse_command(raw_command)` without translating `CommandRejected`. `CommandRejected` is a `ValueError`. `list_features` loads every `Wiki/features/*.md` except README and lets the exception escape. `feature list` / `feature show` catch only `(FeatureMapError, OSError)`. JSON `main()` catches only `CycloptsError`. `/verified-goal` inspects `<runner> feature list --output json` before start. `feature validate` happens to catch `ValueError` and can still emit structured JSON; list/show do not.

**Violated contract:** Agent-facing `--output json` must be one object with `ok` / `error` / `error_type` on domain failure. Feature maps are untrusted repo files. The verified-goal skill depends on list/show JSON, not a Python traceback.

**Failure scenario:** Any hand-edited contract with `verification.command: ""` or `command: "echo 'unterminated"` makes `/verified-goal`’s first `feature list --output json` print a traceback, empty/non-JSON stdout, and a non-structured exit. One bad draft blocks discovery of valid features. `UnicodeDecodeError` on a non-UTF-8 `*.md` has the same hole.

**Fix task:** Wrap `parse_command` / decode failures in `load_feature` as `FeatureMapError`. Catch `CommandRejected` and `ValueError` on list/show (or make `list_features` per-file like `validate_feature_map`). Keep JSON `ok: false` with no traceback.

**Acceptance test:** Write `Wiki/features/broken.md` with valid sections and `verification.command: "echo 'unterminated"`. Run `.pstack/bin/projectctl feature list --output json`. **Expected after fix:** exit 2, stdout one JSON object, `"ok": false`, `error_type` in `{"FeatureMapError","CommandRejected"}`, stderr without `Traceback`. **Current expected failure:** `Traceback` and non-JSON stdout.

---

### GRK-003 — MEDIUM — Relative workspace-escape check only inspects argv[0]

**Citations:** `src/pstack_kiro/runner.py:164-171`, `src/pstack_kiro/runner.py:246-252`, `docs/architecture.md:246-252`, `tests/test_runner.py:31-38`

**Observed:** After denying named executables, the only containment check is: if argv[0] contains `/` and is not absolute, resolve it under `root` and reject escape. Tests cover `["../outside/verifier"]`. `Popen` uses `cwd=root`, so `python ../outside.py`, `python3 /tmp/evil.py`, `uv run ../outside.py`, and `bash ../outside.sh` never hit that check. The docs still list “relative executables that escape the project root” as part of the same policy applied at ready proof, validate, goal start, and every run.

**Violated contract:** The implemented escape rule is advertised as a verifier policy, not as “argv[0] only.” A ready feature or goal can persist and execute a file outside the workspace while `../outside/verifier` is rejected.

**Failure scenario:** `projectctl goal start "x" --command "python ../escape.py"` from a project whose parent contains `escape.py`. Policy allows it; the process reads and runs the outside file with `cwd` still inside the project. Same for `--ready` generation.

**Fix task:** Apply the same lexical/resolved containment rule to script-like arguments (and `uv run` operands), or stop claiming relative escape is policed. Keep the documented “not a sandbox” language for in-repo programs.

**Acceptance test:** Place `outside.py` in the parent of a tmp project. From the project, `run_command([sys.executable, "../outside.py"], root=project)` (or CLI `goal start --command "<exe> ../outside.py"`). **Expected after fix:** `CommandRejected`, no `goal.json`. **Current expected failure:** process runs (or start persists the contract).

---

### GRK-004 — MEDIUM — Default documented V3 path never attaches the shipped permission profiles

**Citations:** `README.md:29-37`, `docs/usage.md:76-81`, `docs/architecture.md:260-265`, `templates/project/.kiro/agents/pstack.json:18-85`, `dev.kiro/steering/pstack-core.md:9`

**Observed:** Architecture says Kiro permissions are the authorization boundary because the runner is not a sandbox, and that shipped primary/verifier profiles mark `projectctl` patterns `ask` and deny destructive shell. Those rules live only in `.kiro/agents/pstack.json` (and the three subagent profiles). Quick start is `kiro-cli chat --v3` then `/setup-pstack` then `/verified-goal`. `--agent pstack` is documented as optional after assets exist. Steering does not require that agent. There is no workspace default-agent file in the templates.

**Violated contract:** The least-privilege deny/ask table is not on the primary workflow. Default-agent Kiro policy (including still-exposed `--trust-all-tools`) is what actually gates `projectctl` and `rm`. Subagent allow/trust lists never apply unless the user opts in.

**Failure scenario:** User follows README. Session uses the ambient agent. `pstack.json` deny entries (`rm -rf *`, `git reset --hard*`, `terraform apply*`, …) are inert. A model that runs shell under a broad-trust default is not constrained by the port’s permission design, while docs tell the user to expect those prompts/denies.

**Fix task:** Make `--agent pstack` the post-setup default in README, usage, and `/setup-pstack` handoff, and/or install a Kiro workspace default-agent mechanism if one exists. Until then, state that shipped deny/ask rules do not apply to `kiro-cli chat --v3` without `--agent pstack`.

**Acceptance test:** Fail the build if README / `skills/setup-pstack/SKILL.md` / `docs/usage.md` document a first-run chat that is not `--agent pstack` (or if bootstrap does not write a workspace default-agent config that selects `pstack`). **Expected after fix:** those files (or the generated workspace config) attach `pstack` before `/verified-goal`. **Current expected failure:** README launch remains `kiro-cli chat --v3` with `--agent pstack` only as an optional later command.

## Low findings and notes

### GRK-005 — LOW — Goal locks skip `fcntl` instead of failing closed

`src/pstack_kiro/goal.py:79-85` flocks only `if fcntl is not None`. `src/pstack_kiro/bootstrap.py:370-371` raises if `fcntl` is missing. `docs/architecture.md:386-387` says bootstrap *and* goal-state locking require POSIX `fcntl` and that setup fails rather than running unlocked. A copied `.pstack/` tree on a non-flock platform would still mutate `goal.json` without serialization.

### GRK-006 — LOW — Omitted `draft` is treated as ready

`docs/architecture.md:217` requires an exact boolean `draft`. `src/pstack_kiro/features.py:125-127` uses `metadata.get("draft", False)`, so a missing key is ready. A hand-written contract with a command and no `draft` field skips the draft warning and is treated as proved at generation time even though it was never `--ready`.

### GRK-007 — LOW — `trustedAgents` test does not test read-only trust

`tests/test_kiro_assets.py:231-240` is named `test_subagent_trust_is_limited_to_read_only_profiles` but only asserts `trustedAgents == availableAgents`, which includes `pstack-verifier` (`templates/project/.kiro/agents/pstack.json:98-109`). The verifier is not read-only; it may run `goal verify` / `feature verify`.

### GRK-008 — LOW — `okn search` passes the raw query as the next argv

`src/pstack_kiro/knowledge.py:92` builds `(executable, "search", "Wiki", query.strip())` with no `--` separator. A query such as `--help` or `-v` can become okn flags. Absence of okn is still honest (`feature-map-only` / search fails).

### GRK-009 — NOTE — Current-session and Stop-hook limits are instructional, not runtime

`/verified-goal` and parallel skills tell the model to stay in the current `kiro-cli --v3` session and not use ACP, `/spawn`, nested Kiro, or native `/goal`. Nothing in `src/pstack_kiro` can enforce that. The Stop hook is disabled (`templates/project/.kiro/hooks/pstack-tripwire.json:13`). That matches the docs; it is not a hidden scheduler and not a fake `/goal`.

### GRK-010 — NOTE — Bootstrap apply is not rollback-atomic after a green preflight

Preflight blockers write nothing (`src/pstack_kiro/bootstrap.py:311-314`, tested). If apply then hits a post-preflight conflict or hash mismatch (`src/pstack_kiro/bootstrap.py:349-353`, `382-392`), already-replaced files remain and the receipt may be withheld. Recovery is possible on a later matching run; it is not a transaction.

## Advisory remediation ledger

| ID | Fix task | Acceptance test | Status |
| --- | --- | --- | --- |
| GRK-001 | Scrub or replace the verifier environment so proofs do not inherit `.pstack/projectctl` `PYTHONPATH` / venv / `UV_*`; test through `.pstack/bin/projectctl`, not only `python -m pstack_kiro`. | Isolated bootstrap; compare clean-shell `python3 envprobe.py` with `--ready` / `feature verify` via the wrapper. Expect no `.pstack/projectctl/src` on `PYTHONPATH` and no projectctl `VIRTUAL_ENV`. | open |
| GRK-002 | Map `parse_command` / decode failures in `load_feature` to `FeatureMapError`; catch them on `feature list` / `show`; keep JSON `ok: false` without traceback. | `Wiki/features/broken.md` with unterminated `verification.command`; `feature list --output json` must be one JSON error object, no `Traceback`. | open |
| GRK-003 | Extend containment to interpreter/script arguments (and `uv run` operands), or remove the “relative executables cannot escape” claim. | `run_command([sys.executable, "../outside.py"], root=project)` must raise `CommandRejected` and must not persist goal state. | open |
| GRK-004 | Attach `pstack` as the post-setup default agent in docs/skill/handoff and/or generated workspace config; until then, stop stating shipped ask/deny rules as the default authorization boundary. | README / setup skill / usage (or generated default-agent config) must select `--agent pstack` before `/verified-goal`. | open |

## Design dissent and attack scenarios

1. **Verifier isolation shape.** Keep `uv run --locked --project .pstack/projectctl` for *projectctl only*, then spawn proofs with a recorded user env (or `os.execve` a venv Python that is not the parent of `Popen`). As long as proofs are children of the wrapper, GRK-001 remains even if individual `UV_*` names are denylisted one by one. This is the acceptance-changing alternative.

2. **Permission matcher / default agent.** `pstack.json` allows `git status*` and asks for `.pstack/bin/projectctl goal verify*`. If Kiro matches the raw command string, `git status; rm -rf .` or `.../projectctl goal verify; ...` can ride those globs. Combined with GRK-004 (ambient agent, optional `--trust-all-tools`), the deny list is theater. Deny-by-default shell plus an actually selected `pstack` agent is the tighter boundary.

3. **Feature-map tripwire against `/verified-goal`.** Plant `Wiki/features/x.md` with a legal slug and `verification.command: "echo '"` (GRK-002) to crash list JSON before start. Or plant a ready contract `python ../outside.py` (GRK-003) so a later `goal start --feature` persists an outside script. Neither is covered by current tests, which use well-formed in-repo argv and `python -m pstack_kiro`.

## Evidence assessed and residual limitations

**Inspected source (this review):** `src/pstack_kiro/*.py`, `skills/**`, `templates/project/.kiro/{agents,hooks}/*`, `dev.kiro/steering/*`, `plugin.json`, `pyproject.toml`, `templates/projectctl/uv.lock` (header/metadata), `tests/*.py`, `docs/*.md`, `README.md`, `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`, `examples/verified-goal-demo/*`, `reviews/*` (treated as untrusted process text, not findings).

**Inspected tests (static only):** bootstrap idempotence/conflicts/upgrades/stale/concurrency/symlinks; goal transitions, digest, spec-bridge names, discard-on-change; runner hazards and descendant kill; CLI JSON coercion errors; packaging wheel + wrapper `version`/`doctor`; asset string contracts. Parametrized `def test_*` count is 130, which matches `docs/validation-report.md:51` as a *count*, not as an executed result.

**Not executed (by contract):** no pytest, ruff, ty, uv, bootstrap, `kiro-cli`, or demo campaign. Repository-reported command results in `docs/validation-report.md` and `docs/kiro-v3-compatibility.md` (Kiro `2.20.2`, 130 passed, 87.44% coverage, session `sess_4612653a-...`, goal `df0561d4-...`) are untrusted claims. Live Kiro permission-matcher semantics, `trustedAgents` prompt skipping, hook trigger behavior, and skill discovery timing were not observed.

**Fake-capability search:** no `src/` invocation of ACP, `/spawn`, nested `kiro-cli`, or native `/goal`. Skills and docs explicitly disclaim those. OKF is optional and does not become proof. The material issues above are real control-plane / contract bugs, not invented Kiro features.
