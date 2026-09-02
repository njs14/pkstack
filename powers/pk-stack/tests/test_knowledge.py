from __future__ import annotations

from pathlib import Path

import pytest

from pstack_kiro.knowledge import KnowledgeError, search, status, validate


def test_knowledge_falls_back_only_to_narrow_feature_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("pstack_kiro.knowledge.shutil.which", lambda _: None)
    (tmp_path / "Wiki" / "features").mkdir(parents=True)

    info = status(tmp_path)
    result = validate(tmp_path)

    assert info["mode"] == "feature-map-only"
    assert result["ok"] is True
    assert "Broad OKF validation was not run" in result["warning"]
    with pytest.raises(KnowledgeError, match="okn"):
        validate(tmp_path, require_okn=True)
    with pytest.raises(KnowledgeError, match="okn"):
        search(tmp_path, "account")
