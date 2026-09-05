from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
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

    def test_rejects_insufficient_context_or_higher_cost(self) -> None:
        cases = {
            "context": {"context_window_tokens": 271999},
            "multiplier": {"rate_multiplier": 2.5},
            "unit": {"rate_unit": "Credits"},
        }
        for label, replacement in cases.items():
            with self.subTest(label=label):
                inventory = valid_inventory()
                inventory["models"][0].update(replacement)  # type: ignore[index,union-attr]
                with self.assertRaisesRegex(
                    validator.InventoryError, "context and cost contract"
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
        inventory["models"][1]["rate_multiplier"] = 2.3  # type: ignore[index,union-attr]
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
        self.assertNotIn("--model auto", runner)
        self.assertNotIn("--model gpt-5.6-terra", runner)
        self.assertNotIn("--model gpt-5.6-luna", runner)
        self.assertEqual(workflow.count("KIRO_API_KEY: ${{ secrets.KIRO_API_KEY }}"), 4)
        self.assertEqual(workflow.count('run: bash "$KIRO_RUNNER_PATH"'), 4)
        self.assertIn(
            'python3 -B "$TRUSTED_ROOT/.github/scripts/test_validate_kiro_model_inventory.py"',
            workflow,
        )

    def test_description_changes_and_better_context_or_cost_are_informational(self) -> None:
        inventory = valid_inventory()
        inventory["models"][0].update(description="Generally available Sol",  # type: ignore[index,union-attr]
                                     context_window_tokens=300000, rate_multiplier=2.0)
        validator.validate_inventory_bytes(encoded(inventory))

    def test_real_shell_success_paths_reach_repair_and_clean_inventory(self) -> None:
        """Execute the shell glue with a local fake Kiro; never call a model."""
        inventory = valid_inventory()
        inventory["models"].append(copy.deepcopy(validator.EXPECTED_REVIEW_MODEL))  # type: ignore[union-attr]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "bin"
            binary.mkdir()
            for name in ("kiro-home", "kiro-user", "private"):
                (root / name).mkdir()
            fake = binary / "kiro-cli"
            fake.write_text(f"#!{sys.executable}\n" + textwrap.dedent(f'''\
                import json, os, pathlib, sys
                if "--list-models" in sys.argv:
                    print({json.dumps(inventory)!r})
                else:
                    pathlib.Path(os.environ["KIRO_HOME"], "repair-invoked").touch()
                    print("{{}}")
                '''))
            fake.chmod(0o755)
            timeout = binary / "timeout"
            timeout.write_text(f"#!{sys.executable}\n" + textwrap.dedent('''\
                import os, sys
                args = sys.argv[1:]
                while args[0].startswith("-"):
                    args.pop(0)
                args.pop(0)
                os.execv(args[0], args)
                '''))
            timeout.chmod(0o755)
            guard = root / "guard.py"
            guard.write_text("import os\nassert 'KIRO_API_KEY' not in os.environ\n")
            env = {**os.environ, "KIRO_API_KEY": "test-only-noncredential",
                   "KIRO_BIN_DIR": str(binary), "KIRO_HOME": str(root / "kiro-home"),
                   "KIRO_USER_HOME": str(root / "kiro-user"), "RUNNER_TEMP": str(root),
                   "BASE_SHA": "a" * 40, "GUARD_PATH": str(guard), "ATTEMPT_NUMBER": "1",
                   "GIT_BOUNDARY_STATE": str(root / "git-boundary")}
            result = subprocess.run(["bash", str(ROOT / ".github/scripts/run_kiro_maintenance_attempt.sh")],
                                    cwd=root, env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "kiro-home/repair-invoked").is_file())
            self.assertFalse((root / "pkstack-kiro-private-1").exists())

            workflow = (ROOT / ".github/workflows/pk-stack-upstream-candidate.yml").read_text()
            invoke = workflow.split("      - name: Independent Kiro-hosted Claude Opus 5 review\n", 1)[1]
            script = textwrap.dedent(invoke.split("        run: |\n", 1)[1].split("          printf -v prompt", 1)[0])
            env.update(REVIEW_PRIVATE=str(root / "private"), TRUSTED_REVIEW_ROOT=str(ROOT))
            result = subprocess.run(["bash", "-c", script], cwd=root, env=env,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "private/model-inventory.json").exists())
            self.assertFalse((root / "private/model-inventory.stderr").exists())

if __name__ == "__main__":
    unittest.main()
