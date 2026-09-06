# Design: normalize_reference

## Scope and approach

Implement the behavior locally in `reference.py`; no new modules, dependencies, persistence, network calls, or external services are needed. Keep the existing public interface:

```python
def normalize_reference(value: str) -> str:
    ...
```

The function performs three ordered steps:

1. Remove surrounding whitespace with `value.strip()`.
2. Validate that the trimmed value has exactly six characters and that every character is an ASCII letter (`A-Z` or `a-z`) or ASCII digit (`0-9`).
3. Return the validated value with ASCII lowercase letters converted to uppercase.

The validation must be ASCII-specific; broad Unicode predicates such as `str.isalnum()` are insufficient because they accept non-ASCII letters and digits.

## Components and responsibilities

- **Reference normalizer (`reference.normalize_reference`)**: owns trimming, ASCII-only validation, canonical uppercasing, and error translation.
- **Callers**: receive either a canonical six-character reference or `ValueError` and require no changes.
- **Existing tests**: remain unchanged and provide the required regression coverage for normalization, short input, and punctuation.

No additional data model is required. The input and output are Python strings; the normalized output invariant is exactly six ASCII alphanumeric characters in uppercase form.

## Error handling

Every invalid trimmed value—including values shorter than six characters, longer than six characters, containing punctuation, or containing non-ASCII characters—raises:

```python
ValueError("invalid reference")
```

Use the same message for every validation failure. Do not expose reason-specific messages or allow incidental errors from validation to escape for the documented invalid-input cases.

## Verification strategy

Preserve `tests/test_reference.py` and run:

```text
python3 -B -m unittest discover -s tests -v
```

The existing examples verify the settled behavior. The design also supports property tests, if added later, for arbitrary valid six-character ASCII-alphanumeric cores with surrounding whitespace and for arbitrary invalid trimmed values.

## Correctness Properties

*A correctness property is a behavior that must hold across all valid executions. These properties bridge the requirements to executable tests; concrete unit tests remain useful for the authoritative examples and boundary cases.*

### Property 1: Valid references normalize to one canonical form

**For any** six-character ASCII-alphanumeric core and any surrounding whitespace, normalization returns the core with ASCII lowercase letters converted to uppercase; the result is exactly six characters and every result character is an uppercase ASCII letter or digit.

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Invalid references fail with the stable diagnostic

**For any** input whose trimmed value is not exactly six ASCII letters or digits, normalization raises `ValueError` with the exact message `invalid reference`.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**
