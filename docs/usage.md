# Usage

`doctor` fails if `uv` or Docker is absent and checks Docker daemon readiness, the Compose-
resolved exact Floci digest, both allowed endpoints, and the active context socket. `up` is
idempotence-safe: it refuses a pre-existing state manifest or a foreign same-name outer
container/network instead of guessing resource ownership. `status` has no secret values and
reports only the named run resources and the two task statuses. `verify` makes all business
requests through the deployed API; it does not directly manufacture a happy-path DynamoDB
state. It proves API acceptance, duplicate request handling, worker completion, S3 result,
terminal state, cross-tenant 404, API duplicate-request identity, real duplicate SQS delivery
as a worker no-op, current-invocation DLQ redrive, ECS tasks, and Docker task containers. When
Floci does not publish the reported host port, verification uses a separately owned, bounded
verifier container on the exact lab network; it never runs `docker exec` in an application task
or claims a host-reachable API endpoint. This verifier is only a valid proof when live task
security evidence passes; Floci 2.0.1 currently fails that mandatory condition.

`evidence` reports versions, endpoints, exact resource names, task-definition revisions,
task state, labels, network, and a hash of the ownership manifest. `down` is required after
every deployed run. If it sees missing or mismatched ownership tags, it fails closed instead
of deleting the resource.

For a deterministic run name use `./labctl up --run-id ci-001 --output json`; only lower-case
letters, digits, and interior hyphens are accepted. All mutable artifacts stay under ignored
`.lab-state/`. Before Compose starts, `up` atomically claims a canonical `run.json`, then creates
and validates only the direct `.lab-state/floci-data` directory for Floci's `/app/data` bind.
If that local creation fails, the claim remains for recovery. After external teardown and leak
checks, `down` removes only that exact validated path, unlinks the manifest last, and removes
`.lab-state/` only when it is empty.

An existing `.lab-state` is never overwritten by `up`: its manifest must be absent only when
the directory is empty, or it must be a valid canonical manifest that is first cleaned with
`down`. Corrupt, tampered, linked, or nonregular state fails closed.
