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

A tenant can request a document export through the deployed API and later retrieve only its
own completed status and S3-backed result. A duplicate request is safe, while invalid work
is retried only to the configured DLQ boundary.

## Expected path

Deployed API ECS task -> DynamoDB and SQS -> deployed worker ECS task -> S3 result and terminal
DynamoDB state; a separate tenant cannot retrieve the export.

## Verification

`./labctl verify --output json`

This verifier is intentionally narrow: after deployment it uses only the repository-owned
labctl verification surface and cannot invoke raw Docker or AWS commands.
