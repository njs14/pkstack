from __future__ import annotations

from pathlib import Path

import pytest

from pstack_kiro.knowledge import KnowledgeError, search, status, validate


def _fake_okn(
    tmp_path: Path,
    *,
    validation_status: str = "pass",
    malformed_operation: str | None = None,
    protocol_mutation: str | None = None,
) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    executable = tmp_path / "tools" / "okn"
    executable.parent.mkdir()
    if validation_status == "fail":
        issues = [
            {
                "path": "features/broken.md",
                "line": 1,
                "rule": "fixture",
                "severity": "error",
                "message": "fixture failed",
            }
        ]
    elif validation_status == "warn":
        issues = [
            {
                "path": "features/warning.md",
                "line": 1,
                "rule": "fixture",
                "severity": "warning",
                "message": "fixture warning",
            }
        ]
    else:
        issues = []
    validation = {
        "schemaVersion": "1",
        "root": str(workspace / "Wiki"),
        "specVersion": "0.2",
        "profile": "okf",
        "files": 1,
        "concepts": 0,
        "indexes": 1,
        "logs": 0,
        "summary": {
            "status": validation_status,
            "errorCount": int(validation_status == "fail"),
            "warningCount": int(validation_status == "warn"),
            "issueCount": len(issues),
        },
        "issues": issues,
    }
    search_result = {
        "schemaVersion": "1",
        "root": str(workspace / "Wiki"),
        "revision": {"specVersion": "0.2", "indexSha256": "0" * 64},
        "query": "__QUERY__",
        "budget": "__BUDGET__",
        "estimatedTokens": 12,
        "limit": 12,
        "route": ["bm25"],
        "sources": [
            {
                "id": "architecture/native-kiro-composition#ownership",
                "locator": f"okf+sha256://{'0' * 64}/"
                f"architecture%2Fnative-kiro-composition.md#{'1' * 64}",
                "contentSha256": "1" * 64,
                "path": "architecture/native-kiro-composition.md",
                "lineStart": 8,
                "lineEnd": 14,
                "relation": "direct",
                "estimatedTokens": 12,
                "markdown": "## Ownership\n\nKiro owns native planning.",
            }
        ],
        "issues": [],
    }
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "args = sys.argv[1:]\n"
        "if args == ['version']:\n"
        "    print('0.13.0')\n"
        "    raise SystemExit(0)\n"
        "if os.environ.get('DO_NOT_TRACK') != '1':\n"
        "    raise SystemExit(81)\n"
        "if os.environ.get('OPENKNOWLEDGE_TELEMETRY') != 'off':\n"
        "    raise SystemExit(82)\n"
        f"validation = {validation!r}\n"
        f"search_result = {search_result!r}\n"
        f"malformed = {malformed_operation!r}\n"
        f"protocol_mutation = {protocol_mutation!r}\n"
        "if 'validate' in args:\n"
        "    if protocol_mutation == 'validation-root':\n"
        "        validation['root'] = '/outside/Wiki'\n"
        "    print('[]' if malformed == 'validate' else json.dumps(validation))\n"
        "    raise SystemExit(9 if validation['summary']['status'] == 'fail' else 0)\n"
        "if 'search' in args:\n"
        "    search_result['query'] = args[-1]\n"
        "    search_result['budget'] = int(args[args.index('--budget') + 1])\n"
        "    if protocol_mutation == 'search-root':\n"
        "        search_result['root'] = '/outside/Wiki'\n"
        "    elif protocol_mutation == 'over-budget':\n"
        "        search_result['estimatedTokens'] = search_result['budget'] + 1\n"
        "    elif protocol_mutation == 'token-mismatch':\n"
        "        search_result['estimatedTokens'] = 11\n"
        "    elif protocol_mutation == 'duplicate-source':\n"
        "        search_result['sources'].append(dict(search_result['sources'][0]))\n"
        "        search_result['estimatedTokens'] = 24\n"
        "    elif protocol_mutation == 'bad-route':\n"
        "        search_result['route'] = ['bm25', 'bm25']\n"
        "    print('[]' if malformed == 'search' else json.dumps(search_result))\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(83)\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return workspace, executable


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


def test_canonical_okn_validation_composes_with_feature_map_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, okn = _fake_okn(tmp_path)
    monkeypatch.setattr("pstack_kiro.knowledge.shutil.which", lambda _: str(okn))

    result = validate(workspace)

    assert result["mode"] == "canonical-okn"
    assert result["okn_version"] == "0.13.0"
    assert result["result"]["passed"] is True
    assert result["feature_map"]["ok"] is False
    assert result["report"]["summary"]["status"] == "pass"
    assert result["ok"] is False


def test_canonical_okn_failure_cannot_be_hidden_by_valid_feature_map(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, okn = _fake_okn(tmp_path, validation_status="fail")
    monkeypatch.setattr("pstack_kiro.knowledge.shutil.which", lambda _: str(okn))
    (workspace / "Wiki/features").mkdir(parents=True)

    result = validate(workspace)

    assert result["feature_map"]["ok"] is True
    assert result["result"]["exit_code"] == 9
    assert result["protocol_error"] is None
    assert result["ok"] is False


def test_canonical_search_validates_versioned_provenance_and_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, okn = _fake_okn(tmp_path)
    monkeypatch.setattr("pstack_kiro.knowledge.shutil.which", lambda _: str(okn))
    (workspace / "Wiki").mkdir()

    result = search(workspace, "native planning", budget=512)

    assert result["ok"] is True
    assert result["okn_version"] == "0.13.0"
    assert result["context"]["query"] == "native planning"
    assert result["context"]["budget"] == 512
    assert result["context"]["sources"][0]["path"].startswith("architecture/")
    with pytest.raises(KnowledgeError, match="64 to 8000"):
        search(workspace, "native planning", budget=1)
    with pytest.raises(KnowledgeError, match="integer"):
        search(workspace, "native planning", budget=True)


@pytest.mark.parametrize("operation", ["validate", "search"])
def test_malformed_okn_machine_contract_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    workspace, okn = _fake_okn(tmp_path, malformed_operation=operation)
    monkeypatch.setattr("pstack_kiro.knowledge.shutil.which", lambda _: str(okn))
    (workspace / "Wiki/features").mkdir(parents=True)

    result = validate(workspace) if operation == "validate" else search(workspace, "context")

    assert result["ok"] is False
    assert "not an object" in result["protocol_error"]


def test_workspace_local_okn_is_never_executed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    okn = tmp_path / "okn"
    okn.write_text("#!/bin/sh\ntouch should-not-run\n", encoding="utf-8")
    okn.chmod(0o755)
    monkeypatch.setattr("pstack_kiro.knowledge.shutil.which", lambda _: str(okn))
    (tmp_path / "Wiki/features").mkdir(parents=True)

    info = status(tmp_path)
    result = validate(tmp_path)

    assert info["okn_available"] is False
    assert "workspace-local" in info["okn_error"]
    assert "workspace-local" in result["warning"]
    assert not (tmp_path / "should-not-run").exists()


def test_openknowledge_binary_name_is_supported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, okn = _fake_okn(tmp_path)
    openknowledge = okn.with_name("openknowledge")
    okn.rename(openknowledge)

    def which(name: str) -> str | None:
        return str(openknowledge) if name == "openknowledge" else None

    monkeypatch.setattr("pstack_kiro.knowledge.shutil.which", which)

    info = status(workspace)

    assert info["okn_available"] is True
    assert info["okn_executable_name"] == "openknowledge"
    assert info["okn_version"] == "0.13.0"


def test_validation_protocol_binds_the_requested_wiki_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace, okn = _fake_okn(tmp_path, protocol_mutation="validation-root")
    monkeypatch.setattr("pstack_kiro.knowledge.shutil.which", lambda _: str(okn))
    (workspace / "Wiki/features").mkdir(parents=True)

    result = validate(workspace)

    assert result["ok"] is False
    assert "root" in result["protocol_error"]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("search-root", "root"),
        ("over-budget", "over-budget"),
        ("token-mismatch", "does not match"),
        ("duplicate-source", "duplicate source"),
        ("bad-route", "retrieval route"),
    ],
)
def test_search_protocol_binds_root_budget_and_source_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    message: str,
) -> None:
    workspace, okn = _fake_okn(tmp_path, protocol_mutation=mutation)
    monkeypatch.setattr("pstack_kiro.knowledge.shutil.which", lambda _: str(okn))
    (workspace / "Wiki").mkdir()

    result = search(workspace, "native planning", budget=512)

    assert result["ok"] is False
    assert message in result["protocol_error"]
