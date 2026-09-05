"""Canonical PKStack identity."""

from __future__ import annotations

DISPLAY_NAME = "PKStack"
EXPANDED_NAME = "Poteto Kiro"
POWER_ID = "pkstack"

DISTRIBUTION_NAME = "pkstack"
RECEIPT_MANAGER = DISTRIBUTION_NAME


def identity_payload() -> dict[str, str]:
    """Return the public PKStack identity."""

    return {
        "name": DISTRIBUTION_NAME,
        "display_name": DISPLAY_NAME,
        "expanded_name": EXPANDED_NAME,
        "power_id": POWER_ID,
    }


__all__ = [
    "DISPLAY_NAME",
    "DISTRIBUTION_NAME",
    "EXPANDED_NAME",
    "POWER_ID",
    "RECEIPT_MANAGER",
    "identity_payload",
]
