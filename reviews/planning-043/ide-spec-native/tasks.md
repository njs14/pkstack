# Tasks: normalize_reference

## Overview

Implement `reference.normalize_reference` as a local canonicalizer for six-character ASCII reference identifiers. Preserve the public function signature, README contract, and `tests/test_reference.py`; do not add dependencies, persistence, network calls, or external services.

## Tasks

- [ ] 1. Implement input trimming and ASCII reference validation in `reference.py`
  - [ ] 1.1 Update `normalize_reference(value: str) -> str` to remove surrounding whitespace, require exactly six characters, and reject any character outside ASCII letters and digits with `ValueError("invalid reference")`.
    - Keep validation ASCII-specific rather than using broad Unicode alphanumeric predicates.
    - Apply the stable error message to short, long, punctuated, and non-ASCII trimmed inputs.
    - _Requirements: 1.1, 1.3, 2.1, 2.2, 2.3, 2.4_
  - [ ] 1.2 Complete canonicalization after validation by uppercasing ASCII lowercase letters and returning the normalized six-character value.
    - Preserve digits and already-uppercase ASCII letters.
    - _Requirements: 1.2, 1.3_
  - [ ]* 1.3 Add property-based coverage for Property 1: any six-character ASCII-alphanumeric core with surrounding whitespace normalizes to its uppercase canonical form and remains exactly six ASCII alphanumeric characters.
    - **Property 1: Valid references normalize to one canonical form**
    - **Validates: Requirements 1.1, 1.2, 1.3**

- [ ] 2. Add invalid-input regression coverage without changing authoritative tests
  - [ ] 2.1 Add focused automated tests for exact-length boundaries, non-ASCII letters/digits, surrounding whitespace, and the exact `ValueError("invalid reference")` diagnostic while preserving all existing assertions in `tests/test_reference.py`.
    - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4_
  - [ ]* 2.2 Add property-based coverage for Property 2: any input whose trimmed value is not exactly six ASCII letters or digits raises `ValueError` with exactly `invalid reference`.
    - **Property 2: Invalid references fail with the stable diagnostic**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [ ] 3. Checkpoint - Ensure implementation and focused tests pass before final verification.
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Run the complete authoritative verification command
  - [ ] 4.1 Run `python3 -B -m unittest discover -s tests -v` and confirm the unchanged authoritative tests plus any added focused tests pass.
    - Do not edit `tests/test_reference.py` as part of verification.
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4_

## Notes

- Tasks marked with `*` are optional and may be skipped for a faster MVP.
- Implementation tasks are ordered before tests that exercise them; the property tests are optional complements to the authoritative examples and focused boundary tests.
- No implementation, test, README, Wiki, or configuration files are changed by this planning phase.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["1.3", "2.1"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["4.1"] }
  ]
}
```
