from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / ".github/scripts/validate_kiro_model_inventory.py"
SPEC = importlib.util.spec_from_file_location("validate_kiro_model_inventory", MODULE_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import contract guard
    raise RuntimeError("could not load model inventory validator")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def valid_inventory() -> dict[str, object]:
    return {
        "default_model": "gpt-5.6-sol",
        "models": [copy.deepcopy(validator.EXPECTED_MODEL)],
    }


def encoded(value: object) -> bytes:
    return (json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n").encode()


class ModelInventoryTests(unittest.TestCase):
    def test_accepts_exact_experimental_sol_contract(self) -> None:
        validator.validate_inventory_bytes(encoded(valid_inventory()))

    def test_rejects_missing_sol(self) -> None:
        inventory = valid_inventory()
        inventory["default_model"] = "auto"
        inventory["models"] = [
            {
                **copy.deepcopy(validator.EXPECTED_MODEL),
                "model_name": "auto",
                "model_id": "auto",
                "description": "Automatic routing",
                "context_window_tokens": 1000000,
                "rate_multiplier": 1.0,
            }
        ]
        with self.assertRaisesRegex(validator.InventoryError, "exactly one"):
            validator.validate_inventory_bytes(encoded(inventory))

    def test_rejects_wrong_sol_lifecycle_context_and_multiplier(self) -> None:
        cases = {
            "lifecycle": {"description": "OpenAI GPT 5.6 Sol with 272k context window"},
            "context": {"context_window_tokens": 271999},
            "multiplier": {"rate_multiplier": 2.3},
            "unit": {"rate_unit": "Credits"},
        }
        for label, replacement in cases.items():
            with self.subTest(label=label):
                inventory = valid_inventory()
                inventory["models"][0].update(replacement)  # type: ignore[index,union-attr]
                with self.assertRaisesRegex(
                    validator.InventoryError, "experimental lifecycle contract"
                ):
                    validator.validate_inventory_bytes(encoded(inventory))

    def test_rejects_duplicate_model_entries(self) -> None:
        inventory = valid_inventory()
        inventory["models"].append(  # type: ignore[union-attr]
            copy.deepcopy(validator.EXPECTED_MODEL)
        )
        with self.assertRaisesRegex(validator.InventoryError, "duplicate"):
            validator.validate_inventory_bytes(encoded(inventory))

    def test_review_preflight_requires_exact_opus_5_contract(self) -> None:
        inventory = valid_inventory()
        inventory["models"].append(copy.deepcopy(validator.EXPECTED_REVIEW_MODEL))  # type: ignore[union-attr]
        validator.validate_inventory_bytes(encoded(inventory), require_review_model=True)
        inventory["models"][1]["rate_multiplier"] = 2.1  # type: ignore[index,union-attr]
        with self.assertRaisesRegex(validator.InventoryError, "review contract"):
            validator.validate_inventory_bytes(encoded(inventory), require_review_model=True)

    def test_rejects_malformed_entries_and_json(self) -> None:
        inventory = valid_inventory()
        del inventory["models"][0]["context_window_tokens"]  # type: ignore[index,union-attr]
        with self.assertRaisesRegex(validator.InventoryError, "changed schema"):
            validator.validate_inventory_bytes(encoded(inventory))
        with self.assertRaisesRegex(validator.InventoryError, "strict UTF-8 JSON"):
            validator.validate_inventory_bytes(b'{"default_model":')
        with self.assertRaisesRegex(validator.InventoryError, "duplicate JSON key"):
            validator.validate_inventory_bytes(
                b'{"default_model":"gpt-5.6-sol","default_model":"auto","models":[]}'
            )

    def test_rejects_unbounded_or_schema_drifted_inventory(self) -> None:
        with self.assertRaisesRegex(validator.InventoryError, "byte limit"):
            validator.validate_inventory_bytes(b" " * (validator.MAX_INVENTORY_BYTES + 1))
        inventory = valid_inventory()
        inventory["unexpected"] = True
        with self.assertRaisesRegex(validator.InventoryError, "root contract"):
            validator.validate_inventory_bytes(encoded(inventory))

    def test_runner_preflights_before_chat_and_preserves_four_secret_steps(self) -> None:
        runner = (ROOT / ".github/scripts/run_kiro_maintenance_attempt.sh").read_text()
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-maintenance-kiro.yml").read_text()
        self.assertIn("validate_kiro_model_inventory.py", runner)
        self.assertIn("chat --list-models --format json", runner)
        self.assertLess(
            runner.index("chat --list-models --format json"),
            runner.index('"$KIRO_BIN_DIR/kiro-cli" chat \\'),
        )
        self.assertIn("trap cleanup_private_evidence EXIT", runner)
        preflight = runner[: runner.index("prompt=$(printf")]
        self.assertIn("env -i \\", preflight)
        self.assertIn('KIRO_API_KEY="$KIRO_API_KEY" \\', preflight)
        self.assertIn('python3 "$model_validator" "$inventory_path"', preflight)
        self.assertIn('unlink "$inventory_path" "$inventory_stderr_path"', preflight)
        self.assertNotIn("--model auto", runner)
        self.assertNotIn("--model gpt-5.6-terra", runner)
        self.assertNotIn("--model gpt-5.6-luna", runner)
        self.assertEqual(workflow.count("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}"), 4)
        self.assertEqual(workflow.count('run: bash "$KIRO_RUNNER_PATH"'), 4)
        self.assertIn(
            'python3 "$TRUSTED_ROOT/.github/scripts/test_validate_kiro_model_inventory.py"',
            workflow,
        )

    def test_maintenance_guidance_records_experimental_processing_boundary(self) -> None:
        guidance = (ROOT / "Wiki/features/pk-stack-upstream-maintenance.md").read_text()
        self.assertIn("high-risk scheduled semantic-maintenance", guidance)
        self.assertIn("Kiro currently marks Sol experimental", guidance)
        self.assertIn("US-served regardless of profile geography", guidance)
        self.assertIn("commercial AWS Regions worldwide", guidance)
        self.assertIn("makes no claim about storage location", guidance)


if __name__ == "__main__":
    unittest.main()
