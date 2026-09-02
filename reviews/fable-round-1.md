# Fable 5.1 acceptance review — round 1

- Reviewed commit: `0b000d359b99f34ee5001088548ca872322e734a`
- Reviewer: `claude-fable-5-1`
- Effort: `max`
- Access: chmod read-only `git archive`; `Read`, `Glob`, and `Grep` only; no MCP
- Duration: 865224 ms
- Verdict: `REQUEST CHANGES`
- Material unresolved: 8

This is the normalized acceptance record from the reviewer's final result. The CLI emitted a
large JSON event stream, so this file retains the complete substantive findings and criteria
rather than intermediate read events.

# Verdict

REQUEST CHANGES

# Material findings

## FBL-001 — HIGH — The mandatory effective-security gate makes the pinned Floci lab unable to verify

`src/pk_stack_lab/cli.py:878-899` rejects the exact Floci 2.0.1 behavior the review contract treats
as an accepted emulator limitation. Consequently, the hardened verifier and current business
contract have no live proof.

Acceptance: enforce non-root, zero mounts, network, labels, and immutable image identity; report
requested versus effective read-only rootfs/capability/security-option controls without claiming
enforcement. Add regression coverage and run a fresh complete Floci lifecycle.

## FBL-002 — HIGH — Teardown preflight and partial-failure recovery cannot converge

`src/pk_stack_lab/cli.py:1327-1616` builds a transient preflight plan, then rediscovers resources.
The unreachable-emulator guard begins after the unguarded AWS preflight. A crash after Compose
teardown retains state but makes the next AWS preflight unreachable. Cluster-not-found paths and
the intended data-directory-failure test do not exercise the promised branch.

Acceptance: persist a frozen teardown plan and phase journal; make every phase idempotently
resumable; handle an explicitly acknowledged unreachable emulator before AWS inventory; verify
exact AWS and Docker postconditions before removing recovery state. Add mutation-boundary and
stuck-delete tests.

## FBL-003 — MEDIUM — The singleton Floci container and network are not bound to a run claim

`src/pk_stack_lab/cli.py:281-291` accepts an already-present lab-labeled outer container/network,
while `compose.yaml` has no opaque claim label. A second checkout can recreate or co-tenant the
singleton and later tear down another run.

Acceptance: `up` refuses any pre-existing Floci container, network, or Floci ECS task container;
interpolate the opaque claim into the Compose service/network labels and require the matching
claim on all post-up lifecycle commands. Add startup and teardown mismatch tests.

## FBL-004 — MEDIUM — Truncated global Docker listings can hide owned images and containers

`src/pk_stack_lab/cli.py:48-99` truncates command output at 8192 bytes, while cleanup consumes
unfiltered image/container listings. Owned entries beyond the truncation point can be skipped and
reported absent.

Acceptance: use exact-name/reference/claim-filtered queries with distinguished not-found handling,
or fail closed on output truncation. Add an over-8192-byte regression.

## FBL-005 — MEDIUM — Repeat deploy leaks earlier digest images and task-definition revisions

`src/pk_stack_lab/cli.py:570-626` and `src/pk_stack_lab/config.py:117-121` retain only the newest
digest/image/task-definition identities. `down` can therefore account for only the latest pair.

Acceptance: keep an append-only per-claim artifact ledger, including planned image tags before
build and every validated task definition. Reconcile the unavoidable registration/save crash
window by exact family and exact claim tags. Test two source-changing deployments and injected
hard exits after each artifact mutation.

## FBL-006 — MEDIUM — Startup mutates before a complete AWS collision inventory

`src/pk_stack_lab/cli.py:446-479` provisions directly. Idempotent S3/ECS creates can adopt a
same-name leftover and retag it to the new claim.

Acceptance: probe all deterministic queue, table, bucket, cluster, service, and task-definition
names before the first create and reject any existing or ambiguous resource. Test existing bucket
and cluster cases with zero create calls.

## FBL-007 — MEDIUM — Risky branches are untested and several tests pass vacuously

The round-1 snapshot does not drive worker concurrency/crash handling, negative S3 body cases,
successful/failed transient-verifier cleanup, deletion planning/execution, or stale recovery.
Several named tests exit before reaching their intended branch.

Acceptance: add deterministic worker race/lease tests, exact S3 mutation tests, verifier cleanup
tests, frozen-plan/deletion/postcondition tests, and sentinels proving the intended branches ran.

## FBL-008 — MEDIUM — No real verified-goal/Kiro v3 campaign is recorded

The snapshot contains controller configuration checks but no in-snapshot goal transition suite,
ready feature generation proof, or real current-session `kiro-cli chat --v3 --agent pstack`
`/verified-goal` transcript.

Acceptance: run the pinned controller suite and isolated ready-generation cases, then record one
real single-session Kiro v3 fail-repair-pass campaign. Configuration validation is not a substitute.

# Non-material findings

Fable also identified twelve low-severity cleanup items (`FBL-009` through `FBL-020`): disable
host system proxy discovery; remove a claim-matching stranded verifier; make `labctl` independent
of caller CWD; refresh stale discovery metadata; document recovery flags and current judge usage;
avoid duplicate-POST timing flake; document or derive the host architecture; pin the verifier by
image ID; remove the legacy `:0.1` cleanup fallback; derive runtime closure tests from the lock;
retain Kiro validation evidence; and make tenant-partition wording consistent.

# Proven strengths

Fable confirmed strict local endpoints and dummy AWS credentials, ambient-environment isolation,
careful no-follow/atomic state handling, narrow API idempotency classification, strong intended
worker token semantics, exact S3 verification, hardened separate verifier design, lock-derived
runtime closure, bounded JSON failures, protected-oracle hashing, coherent Kiro current-session
assets, and honest emulator limitations.

# Acceptance decision

REQUEST CHANGES. All eight material findings are repository-fixable. The Floci security-field,
task-tag, and host-port limitations are external and are not themselves counted as defects.

MATERIAL_UNRESOLVED: 8
