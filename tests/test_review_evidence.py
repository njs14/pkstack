from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_native_spec_campaign_binds_goal_spec_and_session_projection() -> None:
    reviews = ROOT / "reviews"
    campaign = json.loads((reviews / "final-native-spec-campaign.json").read_text())
    projection_path = reviews / "final-native-spec-session-projection.json"
    projection = json.loads(projection_path.read_text())

    assert campaign["goal"]["goal_state_sha256"] == _sha256(reviews / "final-native-spec-goal.json")
    assert campaign["kiro"]["session_projection_sha256"] == _sha256(projection_path)
    assert campaign["kiro"]["resume_id"] == projection["session"]["id"]
    assert projection["session"]["agent_mode"] == "pstack"
    assert projection["session"]["model"] == "gpt-5.6-sol"
    assert projection["session"]["effort"] == "max"

    spec_root = reviews / "native-spec-artifacts" / "document-export-partition-fix"
    for name, digest in campaign["spec"]["artifact_sha256"].items():
        assert _sha256(spec_root / name) == digest

    actions = projection["verified_goal_action_trace"]
    assert sum(item["action"] == "goal-verify" for item in actions) == 2
    assert sum(item["action"] == "str_replace" for item in actions) == 1
    assert sum(item["action"] == "labctl-deploy" for item in actions) == 1
    assert (
        sum(
            item["action"] == "native-subagent-start" and item.get("name") == "pstack-verifier"
            for item in actions
        )
        == 1
    )
    assert projection["bounded_counts"]["nested_kiro_shell_launches"] == 0
    assert projection["bounded_counts"]["spawn_tool_events"] == 0
    assert projection["ambient_context"]["user_memory_steering_included"] is True

    history = (reviews / "final-native-spec-campaign-history.txt").read_text().splitlines()
    assert history[0] == "/spec"
    assert any(line.startswith("/verified-goal ") for line in history)
    assert history[-1] == "/quit"
