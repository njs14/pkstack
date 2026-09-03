# Implementation Plan

## Overview

This plan orders bug-condition exploration and preservation checks before implementation and validation.

## Tasks

- [ ] 1. Write the focused bug-condition exploration test
  - **Property 1: Bug Condition** - Request-Derived Retrieval Partition
  - **CRITICAL**: Write or complete this property test before changing production code. It must fail on the unfixed handler; that failure confirms the bug.
  - Use `tests/test_runtime.py::test_get_export_uses_tenant_partition_key_and_hides_other_tenants` as the regression seam. If it already expresses the complete property, extend it rather than adding a duplicate test.
  - Encode `isBugCondition(X)`: `X` is a valid `GET /exports` request and the original key builder selects a partition different from `X.tenant`. In the current implementation, scope the first deterministic counterexample to a valid non-`tenant-a` tenant requesting an export ID stored only under `TENANT#tenant-a`.
  - Add bounded, deterministic generated cases for valid non-`tenant-a` tenant strings, representative valid export IDs, owner-only rows, and the same export ID in two partitions.
  - For every generated case, capture the single DynamoDB `GetItem` request and assert the expected behavior from the design: `pk` is `TENANT#{X.tenant}`, `sk` is `X.export_id`, an owner row returns only that row's metadata and object key, and an absent owner row returns 404 without foreign metadata, object keys, or S3 object content.
  - Run the focused test on the unfixed code:

    ```sh
    env PYTHONDONTWRITEBYTECODE=1 \
      uv run --locked --no-config --no-sync \
      pytest -p no:cacheprovider -q \
      tests/test_runtime.py::test_get_export_uses_tenant_partition_key_and_hides_other_tenants
    ```

  - **EXPECTED OUTCOME**: The test fails because a non-`tenant-a` request reads `TENANT#tenant-a`. Do not repair the test or production code during this task.
  - Record the smallest counterexample, including the request tenant, issued DynamoDB key, HTTP status, and returned metadata. Mark this task complete only after the failing result is reproducible and documented in the task execution evidence.
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4_

- [ ] 2. Write preservation property tests before implementing the fix
  - **Property 2: Preservation** - Document Export Behavior Outside the Bug Condition
  - **IMPORTANT**: Follow the observation-first method on the unfixed code. Record actual status codes, JSON bodies, storage calls, enqueue behavior, worker attempts, and terminal state before encoding assertions.
  - Cover `NOT isBugCondition(X)`: existing and missing `tenant-a` rows, missing/empty/over-64-character GET values, `/healthz`, unsupported routes, all POST paths, worker claim and completion, duplicate delivery, retry/redrive behavior, and cleanup or lifecycle checks already exercised by repository tests.
  - Add bounded, deterministic generated cases for tenant-a existing/missing rows and GET query values at the validation boundaries. Assert the complete observed HTTP result and whether DynamoDB was called; rejected requests must remain rejected before storage access.
  - Reuse the current POST, worker, CLI, judge, lifecycle, and verifier-harness tests for broader preservation. Do not copy the production implementation into tests and do not add a new property-testing dependency.
  - Run the preservation baseline on the unfixed code while excluding only the expected failing bug-condition test:

    ```sh
    env PYTHONDONTWRITEBYTECODE=1 \
      uv run --locked --no-config --no-sync \
      pytest -p no:cacheprovider -q \
      tests/test_runtime.py tests/test_cli.py tests/test_judge.py \
      -k "not test_get_export_uses_tenant_partition_key_and_hides_other_tenants"
    ```

  - **EXPECTED OUTCOME**: The preservation tests pass on the unfixed code. Mark this task complete only after the observed baseline is encoded and passing.
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [ ] 3. Fix document-export GET partition selection

  - [ ] 3.1 Derive the DynamoDB GET partition key from the validated request tenant
    - In `src/pk_stack_lab/runtime.py`, change only the `ExportHandler.do_GET` `GetItem.Key.pk` value from the fixed `TENANT#tenant-a` partition to `TENANT#{tenant}` using the already validated local `tenant` value.
    - Keep the table source, export-ID sort key, one-read behavior, validation, missing-row branch, success response, status codes, and metadata-only response unchanged.
    - Do not add a scan, fallback lookup, second read, response-side tenant check, helper layer, schema change, endpoint change, dependency, or verifier exception.
    - Do not modify emulator endpoints, POST or worker key construction, application task definitions, Docker mounts, task environments, deployment ownership, or lifecycle deletion logic. In particular, do not add the Docker socket to an application definition.
    - _Bug_Condition: `isBugCondition(X)` is a valid public GET for which the original handler's selected partition differs from `X.tenant`._
    - _Expected_Behavior: `expectedBehavior(X, ddb_request, result)` requires one read at `TENANT#{X.tenant}` and `X.export_id`, owner-only metadata on success, and 404 without foreign data when that row is absent._
    - _Preservation: Preserve every behavior listed in the design's Preservation Requirements, including POST idempotency, enqueue and worker semantics, S3 output, duplicate-delivery no-op behavior, bounded redrive, deployment identity, verifier gates, and run-owned cleanup._
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

  - [ ] 3.2 Verify the bug-condition exploration test now passes
    - **Property 1: Expected Behavior** - Request-Derived Retrieval Partition
    - Re-run the same focused property test from task 1; do not replace it or write a weaker post-fix test.
    - Require every generated request to issue one exact request-derived key, return only the requested partition's row when present, and return 404 without foreign data when absent.
    - **EXPECTED OUTCOME**: The formerly failing test passes, including the recorded counterexample.
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.3 Verify the preservation properties still pass
    - **Property 2: Preservation** - Document Export Behavior Outside the Bug Condition
    - Re-run the same property and baseline tests from task 2; do not rewrite expected values after the production change.
    - Compare results with the recorded unfixed baseline and investigate any difference outside the bug condition as a regression.
    - **EXPECTED OUTCOME**: Every preservation test still passes.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

  - [ ] 3.4 Run local repository validation and inspect the change boundary
    - Run the focused suites, then the complete test suite, lint the touched production and test files, and check patch whitespace:

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

    - Review the diff. The production change must remain confined to request-derived GET key construction; test changes must cover only the bug and preservation properties.
    - Confirm no application task definition, Dockerfile, task environment, emulator endpoint, verifier, feature map, or guarded lifecycle ownership check changed.
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [ ] 4. Checkpoint - deploy current source and prove the unchanged feature contract
  - Proceed only after all local checks in task 3 pass and the repository-owned lab is already up and healthy.
  - Rebuild and activate the current source revision through the supported deployment command:

    ```sh
    ./labctl deploy --output json
    ```

  - Run the published document-export verifier unchanged after deployment:

    ```sh
    ./labctl verify --output json
    ```

  - Require exit status zero and bounded JSON with `ok: true` and `business.tenant_key_partition_separation: true`. Also require the existing submission, duplicate/idempotency, completion, metadata retrieval, exact S3 result, duplicate-delivery no-op, invalid-work redrive, deployment identity, and run-owned cleanup predicates to pass.
  - Do not weaken or replace the verifier. Do not use raw DynamoDB, SQS, S3, Docker, container, or emulator inspection as feature proof; `./labctl verify --output json` is the sole post-deployment proof surface.
  - Do not run a destructive lifecycle command as part of acceptance. If a separately authorized teardown is required after evidence is retained, use only guarded `./labctl down`; never substitute prefix scans or ambient-resource deletion.
  - Confirm all local tests and the deployed verifier pass before marking the checkpoint complete. If deployment or verification fails, retain the bounded command output and return to the first failing task rather than bypassing a gate.
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

## Notes

Task-specific commands, requirement references, expected outcomes, and safety constraints appear in the tasks above.