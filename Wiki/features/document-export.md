---
type: feature
schema_version: 2
slug: document-export
title: Tenant document export
draft: false
verification:
  command:
    - ./labctl
    - verify
    - --output
    - json
related:
  - ../../docs/architecture.md
  - ../../docs/test-strategy.md
---

# Tenant document export

## User behavior

A caller can request a document export with a tenant key and later retrieve its completed
metadata and S3 object key. The tenant key is partition separation only: it is not identity,
authorization, or a security boundary, and GET never returns the object body. A duplicate request
is safe only when the API marks the collision, preserves the same export ID and durable
idempotency row, and causes exactly one worker attempt. Invalid work is retried only to the
configured DLQ boundary.

## Expected path

Deployed API ECS task -> DynamoDB and SQS -> deployed worker ECS task -> S3 result and terminal
DynamoDB state; a distinct tenant key cannot retrieve that row.

## Sub-features

### `submit-and-complete`

An accepted export request is durably recorded, delivered to one worker, and reaches a terminal
completed state with an S3 result key.

### `api-idempotency`

Repeating the same tenant-scoped request returns the original export identity, marks the
collision, and does not create a second durable delivery or worker attempt.

### `retrieve-metadata`

The public retrieval route returns terminal export metadata and the object key without returning
the object body.

### `tenant-partition-separation`

The same export identifier is unavailable through a different tenant partition key; this proves
partition separation, not authentication or authorization.

### `duplicate-delivery-noop`

A duplicate queue delivery is acknowledged as a no-op after the original work is already
terminal, without rewriting the object or increasing the durable attempt count.

### `invalid-work-redrive`

Invalid work is retried only through the configured receive boundary and then appears at the DLQ
boundary with a bounded terminal failure record.

## How to get to it (user POV)

### `submit-export`

From the deployed application surface, submit one tenant-scoped export request, repeat the exact
request, and wait for the export to complete.

### `retrieve-export`

Retrieve the completed export through its public API using the original tenant key, then try the
same export identifier with a distinct tenant key.

### `maintainer-verifier`

From the repository root, run the supported lab verification lever after the Floci-backed ECS-like
environment is deployed and healthy.

## Driving it

### `submit-export`

#### Recipe

Use the endpoint and bounded fixture values emitted by `./labctl verify --output json` to exercise
the public POST route twice with the same tenant and idempotency input. Do not substitute direct
DynamoDB, SQS, or container inspection for the public path.

#### Observable proof

The duplicate response is explicitly marked, both responses preserve one export ID, the durable
idempotency key matches, enqueue is confirmed, and the worker attempt count remains exactly one.

### `retrieve-export`

#### Recipe

Use the public GET route exercised by `./labctl verify --output json` for the completed export with
the original tenant, then repeat that GET with the verifier-owned alternate tenant fixture.

#### Observable proof

The original tenant receives terminal metadata and the S3 object key but no object body; the
alternate tenant cannot retrieve the row.

### `maintainer-verifier`

#### Recipe

Run `./labctl verify --output json` from the repository root and retain its bounded JSON result.
For release evidence, retain the external judge result and hashes identified by that supported
surface rather than raw backend dumps.

#### Observable proof

The command exits zero only after submission, idempotency, completion, retrieval, partition,
duplicate-delivery, invalid-work redrive, and cleanup predicates all pass.

## Evidence boundary

Retain only bounded `labctl` JSON, external-judge verdicts, and referenced artifact hashes needed
to reproduce the business predicates. Do not retain raw Docker or AWS output, object bodies,
credentials, tenant secrets, or private agent reasoning.

## Cleanup boundary

Verification may remove only its run-owned DynamoDB row, S3 object, queue delivery, and DLQ marker
inside the local lab. `./labctl down` removes only lab resources owned by this repository and run;
it must not target ambient Docker, AWS, or unrelated Floci state.

## Gotchas

- A tenant key demonstrates partition separation only; it is not authentication or authorization.
- The Floci API port belongs to the emulated control plane and is not the application host port.
- Evidence must come from the current source and deployed revision, not a stale local container.
- Duplicate success requires the collision marker, stable ID, durable key, one enqueue, and one attempt.
- Live business-path proof does not replace crash-recovery, redrive-boundary, or cleanup tests.

## Verification

`./labctl verify --output json`

This verifier is intentionally narrow: after deployment it uses only the repository-owned
labctl verification surface and cannot invoke raw Docker or AWS commands. Its bounded evidence
includes the duplicate-response marker, accepted duplicate status, stable export identity,
matching durable idempotency key, durable enqueue confirmation, and exactly-one attempt count.
