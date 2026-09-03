# Bugfix Requirements Document

## Introduction

The deployed document-export retrieval path can select a partition that differs from the tenant key in the request. This regression can hide an export from its requesting tenant or return another tenant partition's metadata under the supplied tenant key. The fix restores tenant-key partition separation while preserving the published document-export contract. A tenant key remains a partition key only; it is not identity, authentication, authorization, or a security boundary. Acceptance uses the deployed public path exercised by `./labctl verify --output json`.

## Bug Analysis

### Current Behavior (Defect)

For a valid public retrieval request `X`, the defective deployment can select a partition other than the partition named by `X.tenant`.

```text
FUNCTION isBugCondition(X)
  INPUT: X containing an operation, tenant key, and export ID
  OUTPUT: boolean

  RETURN X.operation = "public GET retrieval"
    AND X.tenant is valid
    AND X.export_id is valid
    AND selected_partition(X) != X.tenant
END FUNCTION
```

1.1 WHEN `isBugCondition(X)` is true, an export with ID `X.export_id` exists in the partition named by `X.tenant`, and no export with that ID exists in `selected_partition(X)` THEN the system does not return the requesting tenant's export metadata and makes the export unavailable through the requesting tenant key
1.2 WHEN `isBugCondition(X)` is true, an export with ID `X.export_id` exists in `selected_partition(X)`, and no export with that ID exists in the partition named by `X.tenant` THEN the system returns the selected partition's metadata under the supplied `X.tenant` key, allowing a distinct tenant key to retrieve that row
1.3 WHEN the published `tenant-partition-separation` check retrieves an export through a distinct tenant key and the defective retrieval selects the partition that owns that export THEN the check observes the export as available through the distinct tenant key and reports failure

### Expected Behavior (Correct)

Every retrieval must select the partition named by the tenant key in that retrieval request.

```text
// Property: Fix Checking
FOR ALL X WHERE isBugCondition(X) DO
  result <- retrieveExport'(X)
  ASSERT selected_partition(X) = X.tenant
  IF completed_row_exists(X.tenant, X.export_id) THEN
    ASSERT result contains that row's terminal metadata and object key
    ASSERT result does not contain the object body
  ELSE
    ASSERT result contains no export metadata, object key, or object body from another tenant partition
  END IF
END FOR
```

2.1 WHEN the system processes a public retrieval request `X` containing a valid tenant key and valid export ID THEN the system SHALL select the partition named by `X.tenant` and no other tenant partition
2.2 WHEN the system processes a retrieval request `X` for a completed export that exists in the partition named by `X.tenant` THEN the system SHALL return that export's terminal metadata and S3 object key without returning the object body
2.3 WHEN an export with ID `X.export_id` is unavailable in the partition named by `X.tenant` but exists in a different tenant partition THEN the system SHALL treat the export as unavailable through `X.tenant` without returning metadata, an S3 object key, or an object body from the different tenant partition
2.4 WHEN the published `tenant-partition-separation` check retrieves an export through its original tenant key and then tries the same export ID through a distinct tenant key THEN the system SHALL make the export available only through the original tenant key and produce a passing result for that check

### Unchanged Behavior (Regression Prevention)

All behavior outside the mismatched-partition retrieval condition must remain equivalent to the behavior before the fix.

```text
// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT documentExport(X) = documentExport'(X)
END FOR
```

3.1 WHEN the API accepts a tenant-scoped export request that has not previously been accepted THEN the system SHALL CONTINUE TO durably record the export in the requesting tenant's partition, confirm one enqueue, and deliver the accepted export to one worker
3.2 WHEN the exact tenant-scoped request and idempotency input for an accepted export are submitted again THEN the system SHALL CONTINUE TO return an accepted response with an explicit duplicate marker, preserve the original export ID and durable idempotency key, avoid a second durable delivery, and produce exactly one worker attempt across both submissions
3.3 WHEN the worker completes an accepted export THEN the system SHALL CONTINUE TO record a terminal completed state and write the S3 result whose object key is retained in the completed export metadata
3.4 WHEN retrieval of a completed export succeeds through the tenant key for its partition THEN the system SHALL CONTINUE TO return terminal export metadata and the S3 object key without returning the S3 object body
3.5 WHEN a duplicate queue delivery arrives after the original export work is terminal THEN the system SHALL CONTINUE TO acknowledge the delivery as a no-op without rewriting the S3 result, changing the terminal export state, or increasing the durable worker-attempt count above one
3.6 WHEN invalid work reaches the worker THEN the system SHALL CONTINUE TO retry it only through the configured receive boundary and place it at the DLQ boundary with a bounded terminal failure record
3.7 WHEN the published document-export verifier runs after deployment THEN the system SHALL CONTINUE TO exercise the deployed public API and worker path and report success only after every non-partition submission, idempotency, completion, retrieval, S3 result, duplicate-delivery, invalid-work redrive, and cleanup predicate passes
3.8 WHEN verification cleans up its fixtures THEN the system SHALL CONTINUE TO remove only the export row, S3 object, queue delivery, and DLQ marker owned by that verification run without targeting unrelated lab or ambient state
