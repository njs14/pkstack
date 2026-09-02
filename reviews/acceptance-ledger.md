# Acceptance ledger

This ledger records implementation status; it is not itself acceptance evidence. Fable must
re-evaluate every material item from the immutable candidate source and tests.

## Original local pre-Fable criteria

- `LOCAL-001` — Isolate every Compose/Docker operation from ambient project, file, context, host,
  proxy, AWS, and uv configuration. Status: implemented and covered by hostile-environment tests.
- `LOCAL-002` — Inventory every deterministic AWS/Docker target before mutation and require exact
  claim ownership. Status: implemented, including structured not-found handling.
- `LOCAL-003` — Bind build inputs, image IDs, task definitions, services, tasks, containers, and
  the selected Docker daemon. Status: implemented and live-proven.
- `LOCAL-004` — Narrow DynamoDB idempotency classification and recover SQS publish failures.
  Status: implemented with deterministic regressions.
- `LOCAL-005` — Make worker claim/complete processing concurrency-safe. Status: implemented with
  lease/race/fault tests.
- `LOCAL-006` — Validate exact bounded S3 object content and metadata. Status: implemented and
  live-proven.
- `LOCAL-007` — Describe tenant behavior only as tenant-key partition separation. Status:
  implemented across source, feature contract, tests, and docs.
- `LOCAL-008` — Bound JSON failures and run through committed locks without ambient uv config.
  Status: implemented; the pre-Python launcher limitation remains documented.
- `LOCAL-009` — Minimize and lock the build context; prove non-root/no-mount task identity and
  report Floci security propagation honestly. Status: implemented and live-proven.
- `LOCAL-010` — Exercise Cyclopts feature generation/goals and distinguish optional OKF. Status:
  implemented; isolated goal passed on attempt 2 and `okn` absence remains an explicit warning.
- `LOCAL-011` — Move acceptance judging outside the mutable checkout and bind all protected
  controls/source. Status: implemented and live-proven by the external judge.
- `LOCAL-012` — Account for every current-claim artifact with recoverable exact cleanup. Status:
  implemented and live-proven across two generations.

## Fable round 1 material criteria

Fable 5.1 reviewed commit `0b000d359b99f34ee5001088548ca872322e734a` at max effort and
returned `REQUEST CHANGES` with eight material findings. The normalized report is
`reviews/fable-round-1.md`.

- `FBL-001` — Replace the impossible Floci effective-security gate with honest requested-versus-
  effective evidence while retaining non-root/no-mount/identity gates. Local disposition:
  implemented, regressed, and live-proven in `live-final-902`.
- `FBL-002` — Persist a frozen crash-resumable teardown plan and exact postconditions. Local
  disposition: implemented; hard exits inside every destructive phase and terminal unlink are
  covered, and the fresh live teardown completed all eight phases.
- `FBL-003` — Bind the singleton Floci/network to the opaque run claim and refuse foreign outer or
  task containers. Local disposition: implemented and tested.
- `FBL-004` — Replace truncatable global inventories and unbounded command capture. Local
  disposition: filtered/exact queries plus selector-driven bounded stdout/stderr handling,
  process-group termination, and regressions are present.
- `FBL-005` — Retain all repeat-deploy image/task-definition artifacts. Local disposition: schema
  v2 has a strict append-only ledger and active pointer bound to exactly one complete operation;
  the live run retained and removed both generations.
- `FBL-006` — Complete read-only collision inventory before provisioning. Local disposition:
  implemented; the S3 create/tag gap also has a durable narrowly scoped recovery intent.
- `FBL-007` — Add deterministic risky-branch tests and repair vacuous tests. Local disposition:
  221 tests cover concurrency, negative object cases, judge mutation/output bounds, provisioning
  and teardown crash boundaries, image collisions, and stale recovery.
- `FBL-008` — Prove controller generation/transitions and one real same-session Kiro v3
  fail-repair-pass run. Local disposition: controller source/vendored/isolated proof is complete;
  the selected-profile Kiro campaign remains open.

## Post-round-1 Codex preflight criteria

- `PREFLIGHT-001` — Require effective-owner, exact 0700 `.lab-state` before every state operation.
  Status: implemented and tested.
- `PREFLIGHT-002` — Reject malformed Docker/claim/active identities and cross-wired operations.
  Status: implemented and tested.
- `PREFLIGHT-003` — Recover a hard exit between S3 bucket creation and tagging from durable exact
  intent only. Status: implemented and tested through down retry.
- `PREFLIGHT-004` — Make state-less image cleanup converge after one tag was removed. Status:
  implemented and tested.
- `PREFLIGHT-005` — Bound child stdout/stderr during execution and terminate the full process
  group on overflow/timeout. Status: implemented and tested.
- `PREFLIGHT-006` — Never interpret an unexpected structured ECS describe/list failure as resource
  absence during collision checks, deployment, verification, or teardown. Status: implemented
  through one shared fail-closed parser and key/path regressions.
- `PREFLIGHT-007` — Bind the direct Compose definition at the original `up` claim, carry that digest
  into the frozen teardown plan, and refuse both first-pass and resumed Compose mutation after
  drift. Status: implemented and tested before external inventory/execution.

## Remaining acceptance sequence

1. Commit the current candidate and run an immutable Fable peer review.
2. Convert every new material finding into a criterion and remediate/re-review.
3. Run the one-process interactive Kiro v3 `/verified-goal` campaign on an isolated clone.
4. Commit the selected-profile evidence and final PK-Stack naming/DRY sweep.
5. Obtain clean Fable acceptance on that exact commit.
6. Run Grok 4.6 `xhigh` as the final sweeper; return any material repair to Fable.
7. Create and verify the private GitHub repository.
