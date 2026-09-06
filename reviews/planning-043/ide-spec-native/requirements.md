# Requirements Document

## Introduction

`reference.normalize_reference` shall canonicalize a user-facing six-character reference identifier without network access, external services, or persistence. The existing README contract and `tests/test_reference.py` are authoritative and remain unchanged.

## Glossary

- **Reference_Normalizer**: The `normalize_reference(value: str) -> str` function in `reference.py`.
- **Reference_Value**: The input value supplied to the Reference_Normalizer.
- **Normalized_Reference**: A six-character string containing only ASCII letters or digits, with ASCII letters represented in uppercase.
- **Invalid_Reference**: A Reference_Value that does not produce a Normalized_Reference after surrounding whitespace is removed.

## Requirements

### Requirement 1: Normalize valid references

**User Story:** As a caller, I want valid reference identifiers normalized consistently, so that equivalent inputs have one canonical representation.

#### Acceptance Criteria

1. WHEN the Reference_Normalizer receives a Reference_Value, THE Reference_Normalizer SHALL remove surrounding whitespace before evaluating the reference content.
2. WHEN the trimmed Reference_Value contains ASCII lowercase letters, THE Reference_Normalizer SHALL convert those letters to uppercase.
3. WHEN the trimmed Reference_Value contains exactly six ASCII letters or digits, THE Reference_Normalizer SHALL return the resulting Normalized_Reference.

### Requirement 2: Reject invalid references

**User Story:** As a caller, I want malformed reference identifiers rejected, so that downstream code receives only valid six-character identifiers.

#### Acceptance Criteria

1. IF the trimmed Reference_Value contains fewer than six characters, THEN THE Reference_Normalizer SHALL raise `ValueError`.
2. IF the trimmed Reference_Value contains more than six characters, THEN THE Reference_Normalizer SHALL raise `ValueError`.
3. IF the trimmed Reference_Value contains a character outside ASCII letters and digits, THEN THE Reference_Normalizer SHALL raise `ValueError`.
4. IF the Reference_Normalizer raises `ValueError` for an Invalid_Reference, THEN THE Reference_Normalizer SHALL use the message `invalid reference`.

## Decision Record: Error Message Stability

The recommended error message is exactly `invalid reference` for every Invalid_Reference. A uniform message provides a stable compatibility surface: callers and tests can rely on one documented diagnostic while the implementation can add or refine validation checks without creating a new message taxonomy. Distinct diagnostics would make individual failures easier to diagnose, but would expose validation categories as user-visible API and increase compatibility obligations without support from the README contract or existing tests.

## Acceptance Evidence

- The unchanged authoritative tests continue to pass for valid normalization, short input rejection, and punctuation rejection.
- Verification command: `python3 -B -m unittest discover -s tests -v`.
- The implementation and verification phases remain separate from this requirements artifact.
