#!/usr/bin/env python3
"""Every tracked source must have exact, bounded parity-file write coverage."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import pkstack_maintenance_guard as guard

ROOT = Path(__file__).resolve().parents[2]


class SourcePermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.policy = guard.load_policy(ROOT / ".github/pkstack-maintenance-policy.json")
        cls.manifest = json.loads((ROOT / "maintenance/upstreams.json").read_text(encoding="utf-8"))
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

    def test_knowledge_writes_are_data_only_and_cannot_change_controls(self):
        for scope in ("agent", "final"):
            exact = set(self.policy[f"{scope}_allowed_exact"])
            prefixes = self.policy[f"{scope}_allowed_prefixes"]
            for path in ("maintenance/knowledge-coverage.json", "Wiki/knowledge/pkstack/topic.md"):
                with self.subTest(scope=scope, allowed=path):
                    self.assertTrue(guard._matches(path, exact, prefixes))
                    self.assertFalse(guard._is_protected(path, self.policy))
            for path in (
                "Wiki/knowledge/run.py",
                "Wiki/work/notes.md",
                "maintenance/other.json",
                ".github/scripts/pkstack_knowledge_coverage.py",
                "Wiki/knowledge/pkstack/corpus-migration.md",
                "Wiki/knowledge/pkstack/corpus-inventory.json",
            ):
                with self.subTest(scope=scope, denied=path):
                    self.assertTrue(
                        guard._is_protected(path, self.policy)
                        or not guard._matches(path, exact, prefixes)
                    )

    def test_candidate_gate_uses_trusted_checker_before_success_identity(self):
        workflow = (ROOT / ".github/workflows/pk-stack-upstream-candidate.yml").read_text()
        candidate = workflow.split("  candidate_tests:\n", 1)[1].split("\n  candidate_review:", 1)[
            0
        ]
        self.assertIn('"$TRUSTED_ROOT/.github/scripts/pkstack_knowledge_coverage.py"', candidate)
        self.assertIn('--base "$COVERAGE_BASE_SHA"', candidate)
        self.assertLess(
            candidate.index("pkstack_knowledge_coverage.py"),
            candidate.index("Bind successful gates to candidate SHA"),
        )


if __name__ == "__main__":
    unittest.main()
