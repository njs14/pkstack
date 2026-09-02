# Acceptance ledger

Candidate baseline: `d94431eb4a48945687281aa4a584a45d88f2b54c`

The first external Fable attempt exhausted its five-hour usage window before emitting a verdict.
It therefore supplied no accepted findings or decision. Two independent read-only Codex audits did
reproduce the material issues below. They are mandatory pre-Fable remediation criteria, not a
substitute for the required completed Fable review.

## Open pre-Fable criteria

- `LOCAL-001` — Make every Compose/Docker operation immune to ambient project, file, context,
  host, proxy, and env-file injection. Bind the exact project, compose file, socket, daemon, and
  context; remove broad orphan deletion; add hostile-environment tests.
- `LOCAL-002` — Inventory and validate every deterministic AWS/Docker target before the first
  mutation or deletion. Never adopt or partially delete around a foreign resource. Use structured
  AWS error codes and exact per-run claim ownership.
- `LOCAL-003` — Bind the current build inputs to a content digest, immutable image identity, exact
  task-definition ARNs, exact running tasks, and concrete Docker image IDs. Reject source/runtime
  drift before and after business verification.
- `LOCAL-004` — Treat only DynamoDB `ConditionalCheckFailedException` as an idempotency collision;
  define bounded retriable behavior and recovery after an SQS publish failure.
- `LOCAL-005` — Make worker processing concurrency-safe with an atomic claim/complete protocol and
  deterministic race/fault-injection tests.
- `LOCAL-006` — Fetch and validate the exact bounded S3 JSON body, key, content type, tenant key,
  and export ID. Negative mutations must fail verification.
- `LOCAL-007` — Stop calling caller-controlled partition lookup authentication or tenant security.
  Use precise tenant-key/partition-separation language and state that auth is out of scope.
- `LOCAL-008` — Make JSON-mode application failures bounded or narrow the promise precisely. Run
  the lab through the committed lock without ambient uv configuration.
- `LOCAL-009` — Add a minimal Docker build context and hash-verified lock-derived runtime closure.
  Enforce/prove non-root tasks, no mounts, no task Docker socket, exact image/task identity, a
  separately hardened verifier, and the documented network/Floci Docker-socket trust boundary.
  Request and report read-only rootfs, dropped capabilities, and no-new-privileges without
  claiming Floci 2.0.1 enforces the fields it demonstrably drops.
- `LOCAL-010` — Exercise projectctl/Cyclopts feature generation and `knowledge validate` in an
  isolated workspace. Separate lab-package tests from vendored-controller evidence and state that
  full OKF integration is unavailable when `okn` is absent.
- `LOCAL-011` — Strengthen the external judge so a mutable in-workspace verifier cannot manufacture
  acceptance; retain immutable contract/oracle hashes and validate the complete evidence schema.
- `LOCAL-012` — Account for all current-claim AWS/Docker/task-definition/image/state artifacts on
  teardown, verify absence before discarding recovery state, and retain a dry-run recovery path.

A criterion closes only when its implementation, regression evidence, and later completed Fable
disposition are recorded.
