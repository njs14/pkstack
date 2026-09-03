# Document Export Partition Fix Bugfix Design

## Overview

The public document-export GET route parses and validates the request tenant but currently reads DynamoDB with the fixed partition key `TENANT#tenant-a`. A request for another tenant can therefore miss its own export or receive tenant-a metadata labeled with the supplied tenant. The repair is to build that one read key from the already validated request tenant.

The HTTP interface, DynamoDB schema, export identity, response shape, and failure statuses stay unchanged. The repair does not alter POST idempotency, SQS delivery, worker claims, S3 writes, DLQ redrive, deployment configuration, lifecycle ownership, or verifier logic. A tenant key continues to provide partition separation only; this design does not turn it into identity, authentication, authorization, or a security boundary.

This design uses bounded context: the approved `bugfix.md`, the published `Wiki/features/document-export.md` contract and its explicit related links, `ExportHandler.do_GET`/`do_POST`, the worker flow, the focused runtime tests, and `command_verify`. One targeted project knowledge query was unavailable because canonical `okn` is not installed; the linked records and current code were sufficient to locate the defect.

## Glossary

- **Bug_Condition (C)**: A valid public export retrieval for which the original GET handler selects a DynamoDB tenant partition different from the tenant in the request.
- **Property (P)**: The required result of a valid retrieval: read only the requesting tenant's partition, return that partition's export metadata and S3 object key when present, and otherwise return no export data.
- **Preservation**: Equality of externally observable behavior between the original system `F` and fixed system `F'` for inputs outside the mismatched-partition retrieval condition.
- **`F`**: The original document-export implementation containing the constant `TENANT#tenant-a` GET key.
- **`F'`**: The implementation after the GET key uses the validated request tenant.
- **Tenant_Key**: A validated string supplied to POST and GET. It determines the DynamoDB partition and is not an authorization credential.
- **Partition_Key**: The DynamoDB `pk` value encoded as `TENANT#{tenant}`.
- **Export_ID**: The DynamoDB sort key and public export identifier, encoded as `e-` followed by 16 hexadecimal characters for exports created by POST.
- **Public_Retrieval**: `GET /exports?tenant={tenant}&id={export_id}` through the deployed API task.
- **Terminal_Metadata**: The response fields `id`, `tenant`, `status`, and `object_key`; it excludes the S3 object's content.
- **Published_Verifier**: `./labctl verify --output json`, the sole deployed feature-proof surface after deployment.

## Bug Details

### Bug Condition

Let `R` be the set of public retrieval inputs. The buggy-input set is:

`C = { X ∈ R | validTenant(X.tenant) ∧ validExportId(X.export_id) ∧ selectedPartition_F(X) ≠ X.tenant }`

The current implementation makes `selectedPartition_F(X)` equal to `tenant-a` for every valid public retrieval, so `C` contains every such request whose tenant is not `tenant-a`.

**Formal Specification:**

```text
FUNCTION isBugCondition(X)
  INPUT: X containing HTTP method, route, tenant query value, and export ID query value
  OUTPUT: boolean

  IF X.method != "GET" OR X.route != "/exports" THEN
    RETURN false
  END IF

  IF NOT validTenant(X.tenant) OR NOT validExportId(X.export_id) THEN
    RETURN false
  END IF

  selected_partition <- partitionEncodedInDynamoDBKeyBuiltByOriginalGET(X)
  RETURN selected_partition != X.tenant
END FUNCTION
```

### Runtime Manifestation

`ExportHandler.do_GET` performs the following steps:

1. It accepts only `/healthz` or `/exports` and parses `tenant` and `id` from the query.
2. It rejects missing, empty, or longer-than-64-character values before storage access.
3. It calls DynamoDB `GetItem`, but its `pk` is the literal `TENANT#tenant-a`; only `sk` uses the request export ID.
4. If a row is found, it copies `status` and `object_key` from that row while echoing the request tenant in the response.

Step 3 is the first incorrect state. Step 4 makes the defect observable as cross-partition metadata labeled with the requesting tenant.

### Examples

- **Observed cross-partition result**: With `e-0123456789abcdef` stored only at `TENANT#tenant-a`, GET with `tenant-b` currently returns HTTP 200, response tenant `tenant-b`, and object key `exports/tenant-a/e-0123456789abcdef.json`. It should query `TENANT#tenant-b` and return HTTP 404.
- **Requesting tenant hidden**: With an export stored only at `TENANT#tenant-b`, GET with `tenant-b` queries `TENANT#tenant-a` and returns 404. It should return tenant-b's terminal metadata and object key.
- **Same ID in two partitions**: If both tenant-a and tenant-b contain the same export ID, GET with `tenant-b` currently returns tenant-a's row. It should return only the row keyed by `TENANT#tenant-b`.
- **Existing non-bug request**: GET with `tenant-a` already selects `TENANT#tenant-a`. Its successful metadata response must remain unchanged.
- **Validation edge**: GET with a missing, empty, or over-64-character tenant or ID returns HTTP 400 before DynamoDB access. The repair must not change that result.

## Expected Behavior

The following predicate defines the result checked by Property 1: `P(X, ddb_request, result) ≜ expectedBehavior(X, ddb_request, result)`. The numbered properties in the Correctness Properties section remain the traceability source of truth.

```text
FUNCTION expectedBehavior(X, ddb_request, result)
  INPUT: valid public retrieval X, the issued DynamoDB request, and HTTP result
  OUTPUT: boolean

  expected_key <- {
    "pk": {"S": "TENANT#" + X.tenant},
    "sk": {"S": X.export_id}
  }

  IF ddb_request.Key != expected_key THEN
    RETURN false
  END IF

  row <- rowAt(expected_key)
  IF row exists THEN
    expected_object_key <- optionalObjectKey(row)
    RETURN result.status = 200
       AND result.json = {
             "id": X.export_id,
             "tenant": X.tenant,
             "status": row.status,
             "object_key": expected_object_key
           }
       AND (row.status != "COMPLETE" OR expected_object_key is a string)
       AND result contains no S3 object content
  END IF

  RETURN result.status = 404
     AND result.json = {"error": "not found"}
     AND result contains no metadata, object key, or S3 object content from another partition
END FUNCTION
```

### Preservation Requirements

**Unchanged Behaviors:**

- A new tenant-scoped POST continues to create one durable row under `TENANT#{tenant}`, publish one logical job, and retain enqueue confirmation.
- An exact duplicate POST continues to return the original export ID with an explicit duplicate marker and durable idempotency key, without a second confirmed delivery or worker attempt.
- The worker continues to claim the tenant-derived row, write the deterministic `exports/{tenant}/{export_id}.json` object, and record terminal `COMPLETE` metadata.
- A successful GET continues to return metadata and `object_key`, never the S3 object content.
- Missing rows continue to return 404; invalid GET values continue to return 400; health and unknown-route responses remain unchanged.
- A duplicate delivery for terminal work continues to be consumed as a no-op without rewriting S3, changing terminal state, or increasing attempts above one.
- Invalid work continues through the configured receive boundary to the DLQ marker checked by the current verifier.
- Deployment identity, source-digest checks, task proof, bounded verifier output, run-owned cleanup, and `labctl down` ownership checks remain unchanged.

**Scope:**

All inputs outside `C` must preserve `F(X) = F'(X)`. This includes tenant-a retrievals that already select the matching partition; health checks; malformed or unsupported GETs; every POST path; worker retries, duplicate deliveries, and invalid messages; S3 and DLQ behavior; deployment and lifecycle commands; and verifier failure gates. The fix introduces no table scan, fallback lookup, secondary read, response-side authorization check, new schema, new endpoint, or verifier exception.

## Hypothesized Root Cause

Repository evidence confirms one causal defect rather than a broader storage or worker failure:

1. **Hard-coded read partition**: `ExportHandler.do_GET` constructs `Key.pk` as `TENANT#tenant-a` after parsing a valid request tenant. The request value is discarded only at this key-construction point.
2. **Read/write invariant split**: `do_POST` writes and updates `TENANT#{tenant}`. The worker also reads, claims, completes, and deduplicates `TENANT#{tenant}` from its message. GET is the only document-export path using a fixed tenant partition.
3. **Misleading response label**: GET echoes the supplied tenant while reading `status` and `object_key` from the selected row. A foreign row can therefore appear under the request tenant even though its object key still names the owning partition.
4. **Verifier exposure**: The verifier's original-tenant request succeeds for its `tenant-a` fixture by coincidence. Its alternate `tenant-b` request hits the same tenant-a row and triggers `tenant-key partition separation check failed` before S3, duplicate-delivery, DLQ, and post-business identity proof.

The focused unfixed test reproduced item 3 exactly. Four adjacent runtime tests covering worker lease and POST retry/idempotency behavior passed unchanged, which narrows the repair boundary to GET key construction.

## Correctness Properties

Property 1: Bug Condition - Request-Derived Retrieval Partition

_For any_ valid public retrieval where the original GET handler would select a partition different from the request tenant, the fixed handler SHALL issue exactly one DynamoDB read keyed by `TENANT#{request tenant}` and the supplied export ID; it SHALL return only that partition's current metadata, include its S3 object key when the row is complete, never return S3 object content, and return 404 without data from another tenant partition when the requested row is absent.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Document Export Behavior Outside the Bug Condition

_For any_ input where the bug condition does not hold, the fixed system SHALL produce the same externally observable result as the original system, preserving GET validation and response shape, POST idempotency and enqueue semantics, worker claim and completion behavior, deterministic S3 output, duplicate-delivery no-op behavior, bounded DLQ redrive, deployment identity checks, verifier gates, and run-owned cleanup.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**

## Fix Implementation

### Decision and Constraints

The repair must satisfy five criteria: derive the read partition from the validated request, keep the public and storage contracts unchanged, avoid touching already-correct write and worker paths, remain directly testable at the DynamoDB request boundary, and pass the unchanged deployed verifier.

Select an inline request-derived key in `ExportHandler.do_GET`. No new public function, type, module, dependency, or configuration is needed.

### Caller-Visible Usage

The existing caller interface and imports do not change. The verifier continues to use the same two public calls:

```text
owner_result <- GET /exports?tenant=tenant-a&id={export_id}
ASSERT owner_result.status = 200
ASSERT owner_result.json contains terminal metadata and object_key
ASSERT owner_result contains no S3 object content

other_result <- GET /exports?tenant=tenant-b&id={export_id}
ASSERT other_result.status = 404 when tenant-b has no row with that ID

repeat_result <- POST /exports with the original tenant and Idempotency-Key
ASSERT repeat_result preserves the original ID and marks the duplicate
```

### Data and Invariants

- The validated request tenant remains a `str` of length 1 through 64; this repair does not broaden accepted syntax.
- A retrieval key remains a DynamoDB mapping with `pk = TENANT#{tenant}` and `sk = export_id`.
- POST, GET, and worker must address the same row for the same `(tenant, export_id)` pair.
- GET performs no cross-partition fallback. Row absence in the requested partition is final and produces 404.
- The response remains metadata-only. It does not fetch S3 and does not return S3 object content.

### Changes Required

**File**: `src/pk_stack_lab/runtime.py`

**Function**: `ExportHandler.do_GET`

1. Build the `GetItem` partition component from the validated local `tenant` value instead of the `tenant-a` literal.
2. Keep the table source, export-ID sort key, number of reads, row-missing branch, success response, status handling, and endpoint selection unchanged.
3. Do not add a scan, fallback query, item-tenant guard, helper layer, or second read.

No production file outside `runtime.py` requires a source change. The existing regression test in `tests/test_runtime.py` already captures both the owner response and the exact owner/alternate DynamoDB keys. `src/pk_stack_lab/cli.py`, verifier tests, deployment definitions, environment construction, worker code, and lifecycle code remain unchanged.

### Repair Alternatives

| Candidate | Correct partition | Change surface | Preservation risk | Interface cost | Decision |
| --- | --- | --- | --- | --- | --- |
| Inline request-derived key in `do_GET` | Yes | One existing key component in the defective read | Lowest | None | Selected |
| Add a shared partition-key helper and migrate GET, POST, and worker | Yes | All read/write/worker key construction | Higher because correct paths move too | A shallow one-line helper and new call sites | Rejected |
| Keep the fixed read and reject rows whose stored tenant differs | No | GET response branch | Still hides legitimate non-tenant-a rows and retains the wrong access | Adds compensating policy | Rejected as symptom masking |

The helper candidate centralizes spelling but hides no meaningful policy and broadens the blast radius. If later work introduces multiple partition formats or validation rules, a typed key constructor may earn an interface; this one-line repair does not.

### Module Map

- **`src/pk_stack_lab/runtime.py` / `ExportHandler.do_GET`** owns public GET parsing, boundary validation, the single DynamoDB read, and metadata response. Only its read-key value changes.
- **`src/pk_stack_lab/runtime.py` / `do_POST` and `worker`** own durable creation, enqueue, claims, completion, S3 writes, duplicate delivery, and redrive behavior. They remain unchanged.
- **`tests/test_runtime.py`** observes the GET storage key and response without a deployed emulator. Its focused partition test is the direct regression seam.
- **`src/pk_stack_lab/cli.py` / `command_verify`** owns deployed public-path proof across POST, owner GET, alternate GET, S3, durable row, duplicate delivery, DLQ, and task identity. It remains unchanged.
- **Deployment and lifecycle modules** rebuild and activate source by digest and enforce exact run ownership. They remain unchanged; a new application source digest still requires redeployment before live verification.

### Deployment Effect

The source edit changes the application build input, so the active API must be rebuilt and redeployed before acceptance. The fixture builds one immutable application image for separate API and worker task definitions; the worker may receive a new image identity even though its behavior is unchanged. No task environment, endpoint, Docker mount, task-definition field, queue, table, bucket, or verifier contract changes. Running the verifier against a stale deployment is invalid because deployment identity checks bind proof to the current source digest.

## Testing Strategy

### Validation Approach

Use two phases. First, run the focused GET test against `F` and retain the counterexample. Then apply the one-key repair, rerun the focused and preservation suites, redeploy the current source, and run the unchanged public verifier. Unit checks prove the key decision directly; the deployed verifier proves that the current API/worker image still satisfies the whole feature contract.

### Exploratory Bug Condition Checking

**Goal**: Demonstrate `C(X)` before editing and confirm that the first wrong value is the DynamoDB partition key.

**Executable Check:**

```sh
env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync \
  pytest -p no:cacheprovider -q \
  tests/test_runtime.py::test_get_export_uses_tenant_partition_key_and_hides_other_tenants
```

**Observed Counterexample on Unfixed Code:**

The test failed because GET for tenant-b returned HTTP 200 with response tenant `tenant-b` and object key `exports/tenant-a/e-0123456789abcdef.json`; the expected result was 404. This confirms that the handler read tenant-a's row for a tenant-b request.

**Test Cases:**

1. **Foreign row visible**: Store the ID only under tenant-a and retrieve it as tenant-b; unfixed code returns tenant-a metadata.
2. **Owner row hidden**: Store the ID only under a non-tenant-a owner and retrieve it as that owner; unfixed code reads tenant-a and misses the row.
3. **Same ID, two partitions**: Give two tenants distinct rows with the same ID; unfixed code always chooses tenant-a's row.
4. **Validation edge**: Omit or oversize tenant/ID values; both versions must return 400 without a DynamoDB read.

A live pre-fix verifier attempt is not required to diagnose this already reproduced line-level defect. Live feature proof belongs after the source is repaired and redeployed.

### Fix Checking

**Goal**: For every input in `C`, prove that `F'` selects the requesting tenant's partition and satisfies the metadata-only result predicate.

**Pseudocode:**

```text
FOR ALL X WHERE isBugCondition(X) DO
  ddb_request, result <- retrieveExport'(X)
  ASSERT expectedBehavior(X, ddb_request, result)
END FOR
```

**Executable Checks:**

1. Rerun the focused test above and require it to pass, including the exact key sequence `TENANT#tenant-a` followed by `TENANT#tenant-b`.
2. Run the deterministic generated-input property tests described below and require every valid tenant to produce only its own `pk`.
3. With the lab already up and healthy, rebuild and activate current source, then run the published verifier:

```sh
./labctl deploy --output json
./labctl verify --output json
```

The verifier must exit zero and return bounded JSON with `ok: true` and `business.tenant_key_partition_separation: true`. The owner GET must reach `COMPLETE`; the alternate-tenant GET must return 404. Do not replace this with raw DynamoDB, SQS, S3, Docker, or container inspection.

### Preservation Checking

**Goal**: For every input outside `C`, show that the repair changes no observable behavior.

**Pseudocode:**

```text
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT documentExport_F(X) = documentExport_F'(X)
END FOR
```

**Pre-Fix Baseline:**

Before the repair, the four other tests in `tests/test_runtime.py` passed while the focused GET test failed. This records a local baseline for worker lease recovery and POST retry/idempotency behavior without copying the original implementation into a test.

**Executable Checks:**

```sh
env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync \
  pytest -p no:cacheprovider -q tests/test_runtime.py tests/test_cli.py tests/test_judge.py

env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync \
  pytest -p no:cacheprovider -q

env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync \
  ruff check src/pk_stack_lab/runtime.py tests/test_runtime.py

git diff --check
```

Review the production diff and require it to contain only the request-derived GET partition repair. The unchanged full verifier then provides preservation evidence for duplicate POST identity, durable idempotency, enqueue confirmation, exactly one worker attempt, terminal state, exact S3 result, duplicate-delivery no-op, current-invocation DLQ evidence, and post-business deployment identity. Lifecycle and cleanup remain covered by the existing repository suite and the controlled lab campaign; no raw backend command may replace the published feature verifier.

### Unit Tests

- Keep `test_get_export_uses_tenant_partition_key_and_hides_other_tenants` as the focused regression: owner retrieval is 200, alternate retrieval is 404, and each exact DynamoDB key matches its request tenant.
- Cover a row owned by a non-tenant-a tenant so owner retrieval cannot pass by coincidence.
- Cover equal export IDs in two tenant partitions and assert the requested partition wins.
- Preserve invalid query, health, unknown-route, POST retry, duplicate POST, confirmed enqueue, worker claim, expired lease, and terminal completion tests.
- Keep verifier harness mutation tests unchanged so a visible alternate tenant, idempotency drift, S3 change, missing DLQ marker, or missing identity reproof still fails closed.

### Property-Based Tests

Use deterministic generated cases in `tests/test_runtime.py`; no new runtime dependency or production abstraction is needed.

- Generate valid tenant strings at boundary lengths and representative export IDs. For each pair, capture `GetItem.Key` and assert `pk == TENANT#{tenant}` and `sk == export_id`.
- Generate distinct tenant pairs sharing an export ID. Place a row under one generated owner and assert owner retrieval returns that row while the other tenant gets 404 and never receives its metadata or object key.
- Generate missing, empty, valid, and over-limit query values and assert all non-bug validation outcomes match the recorded baseline without storage access where validation rejects the request.
- Generate existing/missing owner-row states for tenant-a, where `C` is false in the original implementation, and assert the complete HTTP status and JSON response remain unchanged.

Use a fixed seed if random generation is chosen, print the seed on failure, and keep the generated domain bounded so the command is deterministic and rerunnable.

### Integration Tests

- Run the unchanged `command_verify` harness tests to prove partition failure occurs before later business proof and that idempotency, S3 identity, duplicate delivery, DLQ, and post-business reproof gates remain active.
- Redeploy current source and run only `./labctl verify --output json` for deployed feature proof.
- Require the verifier result to retain the duplicate marker, same export ID, matching durable idempotency key, enqueue confirmation, `attempts: 1`, exact S3 key/content metadata, duplicate-delivery no-op evidence, current-invocation DLQ marker, and post-business task identity in addition to partition separation.
- If the controlled campaign performs teardown, use only `./labctl down`; its exact run-tag checks and unrelated-resource refusal must remain unchanged.

The fix is accepted only when the focused counterexample passes after repair, the preservation suites remain green, the production diff stays at the GET key boundary, the current source is redeployed, and the unchanged published verifier exits zero.