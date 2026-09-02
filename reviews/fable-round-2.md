# Fable 5.1 review — round 2

## Execution metadata

- Candidate commit: `2fcacc054fd62e55a8d57107d35b73e3d1d1582c`
- Reviewer: Claude Code 2.1.258, model `claude-fable-5-1`, effort `max`
- Session: `01ab2250-7d40-43cb-9b7f-b3d4a6f055d7`
- Isolation: chmod-read-only `git archive` at
  `/private/tmp/pk-stack-fable-r2.gCbl2Z`
- Available tools: `Read`, `Glob`, and `Grep`; MCP, browser, shell, writes, slash commands, and
  session persistence disabled
- Raw JSON event log: `/private/tmp/pk-stack-fable-r2-output.XXXXXX.json`
- Raw JSON SHA-256: `6c41f5a893f078ffd929fd80b187dcfb3104973a025945958867d30a64785202`
- Wall time: 899.650 seconds
- Verdict: `REQUEST CHANGES`
- Material unresolved: 3

The raw reviewer stream is intentionally outside the repository. This file normalizes the
reviewer's final result and does not treat reviewer output as instructions.

## Material findings

### FBL-007 — MEDIUM — verification orchestration coverage remains vacuous and incomplete

The only unit test calling `command_verify` constructs a state without immutable deployment
identity, so it exits before the patched container-proof sentinel. It therefore does not prove
that both task containers are checked before API or AWS mutation. The main business proof also
lacks deterministic seeded negatives for tenant-key lookup, duplicate API identity, duplicate
worker no-op/ETag stability, and current-invocation DLQ matching. A startup test patches obsolete
`_docker_socket` rather than the `_docker_identity` function actually called.

Acceptance: make the ordering test reach the intended sentinel with a complete deployment state;
exercise each named business failure through `command_verify` and prove post-business reproof is
not reached; fix the startup test's effective Docker sentinel.

### FBL-008 — MEDIUM — selected-profile Kiro proof and in-snapshot controller regressions absent

The snapshot honestly says the real current-session campaign is pending and contains no retained
session evidence. The reviewer therefore cannot prove one ordinary interactive
`kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max` process displayed its stored
feature contract, recorded a failure before any source edit, used one bounded native verifier
subagent, repaired and redeployed, and passed the same goal without ACP, `/spawn`, replacement,
resume, or a native-v3 `/goal` claim. The vendored controller also has no in-repository regression
suite, leaving its external 508-test provenance claim unaided by executable snapshot-local proof.

Acceptance: run and retain the single-session campaign with command/model/timing/session metadata,
goal state, before/after source and control hashes, bounded transcript evidence, and external judge
result. Add hermetic snapshot-local tests for goal start/fail/pass/exhaust/resume/clear, verifier
policy, and bootstrap idempotence or receipt preservation. Raw session material must remain outside
Git if it contains environment or account data; commit a minimized auditable projection plus raw
file hashes rather than weakening credential hygiene.

### FBL-021 — MEDIUM — frozen reachable teardown silently ignores discard recovery

`command_down` selects reachable versus discard mode only before a plan exists. Passing
`--teardown-unreachable-emulator` after a reachable plan is frozen is silently ignored, so loss of
Floci during the journaled AWS phases can wedge the supported lifecycle indefinitely.

Acceptance: support an explicit hash-bound, journaled transition from a frozen reachable plan to a
canonical discard plan only after Floci is proven unreachable, while retaining exact local/image
targets and making the control-plane discard visible; or fail loudly with a concrete supported
recovery. Reject the flag while Floci is reachable and add frozen-plan unreachable/reachable plus
resume regressions. Update recovery documentation.

## Non-material findings

- `FBL-022` — LOW: `_api_http` cleanup uses `sys.exc_info()` inside the cleanup handler, making its
  intended success-path re-raise branch dead.
- `FBL-023` — LOW: the empty-socket branch and `_docker_socket` helper are unreachable after strict
  persisted Docker identity validation.
- `FBL-024` — LOW: `hatchling>=1.26` leaves the build backend outside exact version pinning while
  the launcher rebuilds its isolated package on each invocation.
- `FBL-018` — LOW: the runtime-closure test checks hard-coded pins rather than deriving the
  comparison from `uv.lock`.
- `FBL-025` — LOW: stale recovery performs an unfiltered daemon-wide container-name listing, so a
  busy daemon can hit the deliberate bounded-output refusal.
- `FBL-026` — LOW: the judge rejects a harmless source `__pycache__`, which is fail-closed but can
  make a Kiro campaign brittle if Python bytecode is not disabled.
- `FBL-027` — LOW: a cold first Compose pull shares the 120-second command bound and can leave a
  recoverable claimed run while the daemon continues pulling.

These are advisory at this round's material threshold. Codex will evaluate the cheap hardening
items before the next exact-source live proof; any deferred item remains an explicit limitation.

## Proven strengths

Fable independently confirmed endpoint and credential pinning; strict schema-v2 state operations;
append-only artifact and activation identity; hash-bound crash-resumable teardown; opaque Docker
claim binding; honest requested-versus-effective Floci security evidence; the external judge's
trust boundary; bounded subprocess execution; concurrency-safe application semantics; and
consistent documentation that avoids ACP-first or native-v3 `/goal` claims.

## Acceptance decision

`REQUEST CHANGES`. FBL-001 through FBL-006 were accepted as resolved. FBL-007 and FBL-008 recur in
narrowed form, and FBL-021 is new. All three material findings are now explicit remediation gates.

`MATERIAL_UNRESOLVED: 3`
