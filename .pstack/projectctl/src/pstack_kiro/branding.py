"""Canonical PK-Stack identity and compatibility names."""

from __future__ import annotations

DISPLAY_NAME = "PK-Stack"
EXPANDED_NAME = "Poteto Kiro"
POWER_ID = "pk-stack"

# These names predate the display brand and are part of the installed interface.
# Keep them stable unless an explicit migration is designed and tested.
DISTRIBUTION_NAME = "pstack-kiro"
RECEIPT_MANAGER = DISTRIBUTION_NAME


def identity_payload() -> dict[str, str]:
    """Return the public identity without hiding compatibility identifiers."""

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
