"""Consumer policy ownership cannot change CI authority or helper roles."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import pkstack_maintenance_guard as guard

ROOT = Path(__file__).resolve().parents[2]


class ConsumerPermissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="pkstack-consumer-policy-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "powers/pkstack/templates/project/.kiro", self.root / ".kiro")
        shutil.copy2(
            ROOT / ".kiro/agents/pkstack-ci-reviewer.json",
            self.root / ".kiro/agents/pkstack-ci-reviewer.json",
        )

    def test_consumer_inheritance_coexists_with_restricted_ci_reviewer(self):
        guard.validate_product_envelope(self.root)

    def test_primary_requires_empty_v3_permission_marker(self):
        path = self.root / ".kiro/agents/pkstack.json"
        document = json.loads(path.read_bytes())
        document.pop("permissions", None)
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(guard.GuardError, "empty v3 permission marker"):
            guard.validate_product_envelope(self.root)

    def test_rejects_inline_grants_denies_legacy_trust_and_helper_writes(self):
        mutations = [
            ("pkstack", "permissions", None),
            ("pkstack", "permissions", {}),
            ("pkstack", "permissions", {"rules": {}}),
            ("pkstack", "permissions", {"rules": [], "extra": True}),
            ("pkstack", "allowedTools", ["@builtin"]),
            ("pkstack", "tools", ["*"]),
            ("pkstack", "includeMcpJson", True),
            ("pkstack", "toolsSettings", {"shell": {"allowedCommands": ["*"]}}),
            ("pkstack-reviewer", "tools", ["read", "write"]),
            ("pkstack-reviewer", "permissions", {"rules": []}),
            ("pkstack-verifier", "tools", ["@builtin"]),
            ("pkstack-ci-reviewer", "permissions", {"rules": []}),
            ("pkstack-ci-reviewer", "tools", ["shell"]),
        ]
        mutations.extend(
            (
                "pkstack",
                "permissions",
                {"rules": [{"capability": "builtin", "effect": effect}]},
            )
            for effect in ("allow", "ask", "deny")
        )
        for name, field, value in mutations:
            with self.subTest(name=name, field=field):
                path = self.root / f".kiro/agents/{name}.json"
                original = path.read_bytes()
                document = json.loads(original)
                document[field] = value
                path.write_text(json.dumps(document))
                try:
                    with self.assertRaises(guard.GuardError):
                        guard.validate_product_envelope(self.root)
                finally:
                    path.write_bytes(original)

    def test_missing_consumer_profile_is_not_a_valid_envelope(self):
        (self.root / ".kiro/agents/pkstack-reviewer.json").unlink()
        with self.assertRaisesRegex(guard.GuardError, "consumer agents are missing"):
            guard.validate_product_envelope(self.root)


if __name__ == "__main__":
    unittest.main()
