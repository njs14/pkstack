"""Intentionally incomplete behavior used by the real Kiro retry-loop test."""


def normalize_account_id(value: str) -> str:
    """Return an account identifier suitable for lookup.

    This baseline intentionally handles only surrounding whitespace. The Kiro
    validation campaign must observe the failing contract, repair it, and then
    produce a passing verification attempt.
    """

    return value.strip()
