---
type: feature
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
authorization, or a security boundary, and GET never returns the object body. A duplicate request is safe, while invalid work
is retried only to the configured DLQ boundary.

## Expected path

Deployed API ECS task -> DynamoDB and SQS -> deployed worker ECS task -> S3 result and terminal
DynamoDB state; a distinct tenant key cannot retrieve that row.

## Verification

`./labctl verify --output json`

This verifier is intentionally narrow: after deployment it uses only the repository-owned
labctl verification surface and cannot invoke raw Docker or AWS commands.
