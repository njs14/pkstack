#!/usr/bin/env python3
"""Every tracked source must have exact, bounded parity-file write coverage."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import pk_stack_maintenance_guard as guard


ROOT = Path(__file__).resolve().parents[2]


class SourcePermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.policy = guard.load_policy(
            ROOT / ".github/pk-stack-maintenance-policy.json"
        )
        cls.manifest = json.loads(
            (ROOT / "maintenance/upstreams.json").read_text(encoding="utf-8")
        )
        cls.profiles = {
            path: json.loads((ROOT / path).read_text(encoding="utf-8"))
            for path in (
                cls.policy["ci_authority"]["path"],
                ".github/fixtures/kiro-permission-agent.json",
            )
        }

    def test_every_source_parity_has_exact_profile_and_policy_authority(self) -> None:
        for source in self.manifest["sources"]:
            path = source["parity_path"]
            with self.subTest(source=source["id"], boundary="policy"):
                self.assertIn(path, self.policy["ci_authority"]["write_patterns"])
            for profile_path, profile in self.profiles.items():
                allowed = {
                    pattern
                    for rule in profile["permissions"]["rules"]
                    if rule["capability"] == "fs_write" and rule["effect"] == "allow"
                    for pattern in rule["match"]
                }
                with self.subTest(source=source["id"], boundary=profile_path):
                    self.assertIn(path, allowed)

    def test_every_source_parity_crosses_agent_and_final_boundaries_without_wildcards(
        self,
    ) -> None:
        for source in self.manifest["sources"]:
            path = source["parity_path"]
            for scope in ("agent", "final"):
                exact = set(self.policy[f"{scope}_allowed_exact"])
                prefixes = self.policy[f"{scope}_allowed_prefixes"]
                with self.subTest(source=source["id"], boundary=scope):
                    self.assertIn(path, exact)
                    self.assertTrue(guard._matches(path, exact, prefixes))
                    self.assertFalse(guard._is_protected(path, self.policy))
                    sibling = str(Path(path).with_name("unlisted-source-parity.json"))
                    self.assertFalse(guard._matches(sibling, exact, prefixes))


if __name__ == "__main__":
    unittest.main()
