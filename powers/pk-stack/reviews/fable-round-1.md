# Fable peer review, round 1

Verdict: **REJECT**

This is a Codex extraction from the Fable JSON event envelope, not a
byte-for-byte transcript. The host truncated the envelope after the reviewer
recursively inspected the repository's `.venv`; the complete material finding
ledger and the review conclusion were preserved. Later Fable passes use a clean
Git archive and return only the final report.

## Review identity

- Snapshot: `6b72a713bb9966cc6325381b91ea44e961e869e4`
- Model requested and reported by session metadata: `claude-fable-5-1`
- Effort: `max`
- Session: `f0c29166-0abc-44f1-a8c8-7df37335211c`
- Duration: 1,273,113 ms
- Harness: Claude Code read-only `Read,Glob,Grep`, strict empty MCP config,
  safe/restricted mode, no slash commands, no Chrome, no persistence

## Scope matrix

| Area | Result | Assessment |
| --- | --- | --- |
| Architecture boundary | clear | Kiro executes, pstack carries workflow semantics, projectctl persists operability/evidence, and OKF remains separate. |
| Kiro CLI V3 compatibility | finding | Primary permission coverage is incomplete even though the native V3/current-session direction is clear. |
| projectctl and Cyclopts | finding | Cached setup entrypoints can still self-authorize. |
| OKF integration | clear | Optional canonical `okn` delegation and feature-map fallback remain separated. |
| Feature-map generation | finding | Placeholder proof commands can create ready contracts; rejected draft generation also leaves directories. |
| Verified-goal loop | finding | Placeholder proof can complete a goal, and one active resume transition writes unloadable state. |
| Tests | finding | The four material cases and several low-risk boundaries lack regressions. |
| Documentation | finding | Permission and delegated-output wording overstates the implemented boundary. |
| Safety and permissions | finding | State-changing controller routes and direct control-plane writes need explicit coverage. |
| Validation evidence | not established | Final post-remediation Kiro campaign and final acceptance evidence were intentionally still pending. |

## Material findings

### FBL-001 — Medium: non-evidentiary and self-referential commands can prove completion

The central verifier policy accepts context-free successful programs such as
`true`, `echo`, and `printf`, along with the `.pstack/bin/projectctl` controller
itself. A ready feature can therefore claim an unimplemented behavior while its
stored command is `true` or `projectctl version`; a goal using the same command
can transition to `passed`.

Fix task: reject obvious non-evidentiary programs and direct projectctl
self-invocation centrally at contract validation and execution boundaries.
Document that this is only a syntactic evidence-integrity screen: an arbitrary
renamed or repository script can still be an irrelevant no-op.

Acceptance checks:

- `feature generate ... --command true --ready` exits 2 with
  `CommandRejected` and writes no feature file.
- `goal start ... --command "echo ok"` exits 2 and creates no goal state.
- Direct controller and Python-module self-reference are rejected on creation,
  validation, and execution.

### FBL-002 — Medium: the primary profile does not explicitly ask for every state-changing route

The profile asks for selected controller routes but omits `setup`,
`feature generate`, `goal resume`, and `goal clear`. This also makes the README
claim that projectctl execution remains at `ask` inaccurate under broader
permission scopes.

Fix task: cover every canonical `.pstack/bin/projectctl` invocation with an
explicit `ask` rule, without adding the potentially foreign root `./projectctl`
name. Add a route-matrix regression.

Acceptance check: every current state-changing route and an unknown future
canonical subcommand matches an agent-scoped `ask` pattern.

### FBL-003 — Medium: an active goal can resume into corrupt state

After one failed attempt of an active goal with a 4-attempt budget,
`goal resume --max-attempts 1` is accepted. It writes `status=active`,
`attempt_count=1`, and `max_attempts=1`; every subsequent state command rejects
the stored invariant, including the official clear path.

Fix task: reject any active resume ceiling that leaves no remaining attempt and
make `GoalStore.save` validate serialized schema and semantic invariants before
atomic replacement.

Acceptance check: the invalid resume exits 2, leaves the previous bytes intact,
and a following status exits 0 with active `1/4` state.

### FBL-004 — Medium: cached setup paths still treat the cache as authority

The Cyclopts setup route requires `--power-root`, but the cached
`setup_pstack.py` fallback and `python -m pstack_kiro.bootstrap` imported via
`.pstack/projectctl/src` infer the project cache as their asset root. Both can
report stale installed assets as clean.

Fix task: centrally reject any resolved setup asset root located under the
target project's `.pstack` directory while preserving a Power-local source
checkout and an installed wheel outside that cache.

Acceptance check: both cached entrypoints exit 2 with a structured `ValueError`
and leave the receipt and installed profile unchanged.

## Low findings and notes

- **FBL-005:** rejected draft feature generation creates empty `Wiki/features`
  directories before policy validation.
- **FBL-006:** wrapper programs such as `time`, `caffeinate`, `stdbuf`, `script`,
  and `busybox` make the hazard screen inconsistent; Git matching is deliberately
  conservative and can produce false positives.
- **FBL-007:** primary-profile deny patterns miss common recursive removal and
  forced-push spellings.
- **FBL-008:** generic `fs_write: ask` does not distinctly protect goal state,
  the bootstrap receipt/cache, or generated agent and hook definitions from a
  direct write tool.
- **FBL-009:** fail-closed symlink handling also rejects symlinked discovery
  markers; this limitation should be explicit.
- **FBL-010:** arena/swarm prose allows worker output files even though all
  shipped delegated profiles are now read-only.
- **FBL-011:** the verified-goal skill should surface the stored command and
  provenance before the first proof rather than relying on the shell approval
  display.
- The final selected-profile Kiro V3 campaign was pending by design and was not
  itself counted as a defect.

## Acceptance ledger

| ID | Fix task | Executable acceptance test | Status at review |
| --- | --- | --- | --- |
| FBL-001 | Add central placeholder and controller-self-reference rejection. | Direct service and freshly bootstrapped CLI reject `true`, `echo`, controller, and module forms before persistence. | open |
| FBL-002 | Put the full canonical controller prefix at agent-scoped `ask`. | Static route matrix plus installed Kiro agent validation. | open |
| FBL-003 | Guard resume equality and validate every state before save. | Invalid active resume preserves loadable `1/4` state and existing bytes. | open |
| FBL-004 | Reject target-local cache roots as bootstrap authority. | Cached shim and cached-module invocations return structured exit 2 without changes. | open |

## Residual limitations and unverified claims

The reviewer inspected source and tests but did not execute repository commands.
Reported test counts and live Kiro observations therefore remained
repository-reported evidence. No syntactic verifier screen can prove that an
arbitrary permitted script semantically covers the claimed behavior, and Kiro
permissions do not sandbox a subprocess after the user approves its shell
invocation.
