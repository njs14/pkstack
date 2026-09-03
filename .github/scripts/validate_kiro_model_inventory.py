"""Fail closed unless Kiro exposes the exact scheduled-maintenance Sol contract."""

from __future__ import annotations

import json
import math
import stat
import sys
from pathlib import Path
from typing import Any

MAX_INVENTORY_BYTES = 128 * 1024
MAX_MODELS = 128
MODEL_KEYS = {
    "model_name",
    "description",
    "model_id",
    "context_window_tokens",
    "rate_multiplier",
    "rate_unit",
}
EXPECTED_MODEL = {
    "model_name": "gpt-5.6-sol",
    "description": "Experimental preview of OpenAI GPT 5.6 Sol with 272k context window",
    "model_id": "gpt-5.6-sol",
    "context_window_tokens": 272000,
    "rate_multiplier": 2.4,
    "rate_unit": "Credit",
}


class InventoryError(ValueError):
    """Raised when model inventory cannot authorize the scheduled repair model."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise InventoryError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise InventoryError(f"non-finite JSON value: {value}")


def _bounded_string(value: Any, *, label: str, maximum: int) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > maximum:
        raise InventoryError(f"{label} must be a bounded non-empty string")
    return value


def validate_inventory_bytes(raw: bytes) -> None:
    if not raw or len(raw) > MAX_INVENTORY_BYTES:
        raise InventoryError("model inventory is empty or exceeds its byte limit")
    try:
        inventory = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InventoryError("model inventory is not strict UTF-8 JSON") from exc
    if not isinstance(inventory, dict) or set(inventory) != {"default_model", "models"}:
        raise InventoryError("model inventory root contract changed")
    default_model = _bounded_string(inventory["default_model"], label="default model", maximum=128)
    models = inventory["models"]
    if not isinstance(models, list) or not 1 <= len(models) <= MAX_MODELS:
        raise InventoryError("model inventory list is missing or outside its item limit")

    ids: set[str] = set()
    names: set[str] = set()
    sol_entries: list[dict[str, Any]] = []
    for index, item in enumerate(models):
        if not isinstance(item, dict) or set(item) != MODEL_KEYS:
            raise InventoryError(f"model inventory entry {index} changed schema")
        model_id = _bounded_string(item["model_id"], label="model id", maximum=128)
        model_name = _bounded_string(item["model_name"], label="model name", maximum=128)
        _bounded_string(item["description"], label="model description", maximum=4096)
        _bounded_string(item["rate_unit"], label="model rate unit", maximum=64)
        context = item["context_window_tokens"]
        multiplier = item["rate_multiplier"]
        if type(context) is not int or context <= 0:
            raise InventoryError(f"model inventory entry {index} has invalid context")
        if type(multiplier) not in {int, float} or not math.isfinite(multiplier) or multiplier < 0:
            raise InventoryError(f"model inventory entry {index} has invalid multiplier")
        if model_id in ids or model_name in names:
            raise InventoryError("model inventory contains a duplicate model id or name")
        ids.add(model_id)
        names.add(model_name)
        if model_id == EXPECTED_MODEL["model_id"]:
            sol_entries.append(item)

    if default_model not in ids:
        raise InventoryError("default model is not present in model inventory")
    if len(sol_entries) != 1:
        raise InventoryError("model inventory must contain exactly one gpt-5.6-sol entry")
    if sol_entries[0] != EXPECTED_MODEL:
        raise InventoryError(
            "gpt-5.6-sol no longer matches the approved experimental lifecycle contract"
        )


def validate_inventory_file(path: Path) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise InventoryError("model inventory file is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_INVENTORY_BYTES:
        raise InventoryError("model inventory must be a bounded regular file")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InventoryError("model inventory file could not be read") from exc
    validate_inventory_bytes(raw)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_kiro_model_inventory.py INVENTORY.json", file=sys.stderr)
        return 2
    try:
        validate_inventory_file(Path(argv[1]))
    except InventoryError as exc:
        print(f"Kiro model preflight rejected inventory: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
