from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from typing import Any

import pytest
from feature_fixtures import (
    generate_fixture_cli_feature,
    generate_fixture_feature,
    plant_fixture_feature,
)

from pkstack import cli
from pkstack import features as feature_module
from pkstack.features import (
    FeatureMapError,
    find_feature,
    generate_feature,
    list_features,
    load_feature,
    load_feature_plan,
    validate_feature_map,
)
from pkstack.models import FeatureEntrypoint, FeatureSubFeature
from pkstack.runner import CommandRejected

POWER_ROOT = Path(__file__).resolve().parents[1] / "powers" / "pkstack"
REPOSITORY_ROOT = POWER_ROOT.parents[1]


def test_shared_okf_metadata_preserves_the_executable_feature_contract(tmp_path: Path) -> None:
    path = generate_fixture_feature(
        tmp_path,
        "metadata",
        title="Metadata",
        behavior="A maintainer reads sourced knowledge alongside executable proof.",
        expected_path="Knowledge to feature verification",
        command=[sys.executable, "verify.py"],
    )
    before = load_feature(path, root=tmp_path)
    metadata = (
        "description: Source-grounded feature context\n"
        "resource: https://example.com/spec\n"
        "tags: [accounts]\n"
        "sources: [{resource: 'https://example.com/spec', title: Specification}]\n"
        "usage_window: {from: '2026-09-01T00:00:00Z', to: '2026-09-02T00:00:00Z'}\n"
        "generated: {by: 'process:interview', at: '2026-09-02T00:00:00Z'}\n"
        "verified: {by: 'human:owner', at: '2026-09-02T00:00:00Z'}\n"
        "status: stable\n"
        "stale_after: '2026-10-01T00:00:00Z'\n"
    )
    path.write_text(path.read_text().replace("type: feature\n", "type: feature\n" + metadata))

    assert load_feature(path, root=tmp_path) == before
    # Knowledge verification metadata must not authorize an unrecognized
    # executable setting or replace the feature schema's command validation.
    path.write_text(
        path.read_text().replace("verification:\n", "verification:\n  approved: true\n")
    )
    with pytest.raises(FeatureMapError, match="verification contains unknown fields"):
        load_feature(path, root=tmp_path)


def test_okf_trust_metadata_does_not_publish_an_unverified_feature(tmp_path: Path) -> None:
    path = generate_fixture_feature(
        tmp_path,
        "unverified",
        title="Unverified",
        behavior="The maintainer distinguishes decisions from executed proof.",
        expected_path="Decision to draft feature",
        command=None,
    )
    path.write_text(
        path.read_text().replace(
            "type: feature\n",
            "type: feature\nverified: {by: 'human:owner', at: '2026-09-02T00:00:00Z'}\n",
        )
    )
    feature = load_feature(path, root=tmp_path)
    assert feature.draft is True
    assert feature.command is None
    path.write_text(path.read_text().replace("draft: true", "draft: false"))
    result = validate_feature_map(tmp_path)
    assert result["ok"] is False
    assert any(
        "ready contract has no executable verification command" in x for x in result["errors"]
    )


@pytest.mark.parametrize("schema", [None, 1, 3, "2", True])
def test_only_current_feature_schema_is_readable(tmp_path: Path, schema: object) -> None:
    path = generate_fixture_feature(
        tmp_path,
        "current",
        title="Current",
        behavior="A maintainer reads the current contract.",
        expected_path="Feature file to validated contract",
        command=None,
    )
    text = path.read_text(encoding="utf-8")
    replacement = "" if schema is None else f"schema_version: {json.dumps(schema)}\n"
    path.write_text(text.replace("schema_version: 2\n", replacement), encoding="utf-8")

    with pytest.raises(FeatureMapError, match="schema_version must be 2"):
        load_feature(path, root=tmp_path)


def test_generation_requires_structured_contract_without_fabricating_fields(tmp_path: Path) -> None:
    with pytest.raises(FeatureMapError, match="at least one non-empty sub-feature"):
        generate_feature(
            tmp_path,
            "incomplete",
            title="Incomplete",
            behavior="A user reaches the application.",
            expected_path="User request to application result",
            command=None,
        )
    assert not (tmp_path / "Wiki").exists()


def test_generate_load_list_and_validate_feature(tmp_path: Path) -> None:
    verifier = tmp_path / "verify.py"
    verifier.write_text("print('ok')\n", encoding="utf-8")
    architecture = tmp_path / "Wiki" / "architecture" / "boundary.md"
    architecture.parent.mkdir(parents=True)
    architecture.write_text("# Boundary\n", encoding="utf-8")
    path = generate_feature(
        tmp_path,
        "account-lookup",
        title="Account lookup",
        behavior="A caller retrieves an account status.",
        expected_path="Runtime -> gateway -> account service -> response",
        command=[sys.executable, "verify.py"],
        related=["../architecture/boundary.md"],
        draft=False,
        sub_features=[
            FeatureSubFeature(
                identifier="lookup-status",
                behavior="Return the current account status.",
            )
        ],
        entrypoints=[
            FeatureEntrypoint(
                identifier="cli",
                user_path="Run the account lookup command.",
                drive=f"Run {sys.executable} verify.py from the project root.",
                observable="The command exits zero and prints ok.",
            )
        ],
        gotchas=["A zero exit without the expected output is not sufficient."],
        evidence_boundary="Capture the bounded command output and exit status.",
        cleanup_boundary="The read-only check creates no feature-owned state.",
    )

    feature = find_feature(tmp_path, "account-lookup")
    validation = validate_feature_map(tmp_path)

    assert path.name == "account-lookup.md"
    assert feature.command == (sys.executable, "verify.py")
    assert feature.draft is False
    assert feature.schema_version == 2
    assert feature.sub_features[0].identifier == "lookup-status"
    assert feature.entrypoints[0].identifier == "cli"
    assert [item.slug for item in list_features(tmp_path)] == ["account-lookup"]
    assert validation["ok"] is True
    assert validation["warnings"] == []


@pytest.mark.parametrize(
    "token",
    (
        "on",
        "off",
        "yes",
        "no",
        "true",
        "false",
        "y",
        "n",
        "null",
        "none",
        "2",
        "Yes",
        "NO",
        "Null",
        "~",
    ),
)
def test_generated_yaml_ambiguous_strings_round_trip_without_coercion(
    tmp_path: Path,
    token: str,
) -> None:
    slug = token.lower() if token != "~" else "tilde"
    generate_fixture_feature(
        tmp_path,
        slug,
        title=token,
        behavior="A caller runs a tagged check.",
        expected_path="CLI -> verifier -> result",
        command=[sys.executable, "verify.py", token],
        draft=True,
    )

    feature = find_feature(tmp_path, slug)
    validation = validate_feature_map(tmp_path)

    assert feature.slug == slug
    assert feature.title == token
    assert feature.command == (sys.executable, "verify.py", token)
    assert validation["ok"] is True


def test_generate_is_draft_by_default_and_refuses_overwrite(tmp_path: Path) -> None:
    generate_fixture_feature(
        tmp_path,
        "login",
        title="Login",
        behavior="A user signs in.",
        expected_path="Form -> session",
        command=None,
    )

    assert find_feature(tmp_path, "login").draft is True
    with pytest.raises(FeatureMapError, match="overwrite"):
        generate_fixture_feature(
            tmp_path,
            "login",
            title="Login",
            behavior="A user signs in.",
            expected_path="Form -> session",
            command=None,
        )


def test_concurrent_generation_without_overwrite_has_exactly_one_winner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    barrier = threading.Barrier(2)
    original = feature_module.feature_output_path

    def synchronized_output_path(root: Path, slug: str, *, overwrite: bool = False) -> Path:
        path = original(root, slug, overwrite=overwrite)
        barrier.wait(timeout=2)
        return path

    monkeypatch.setattr(feature_module, "feature_output_path", synchronized_output_path)
    outcomes: list[Path | FeatureMapError] = []

    def generate(title: str) -> None:
        try:
            result = generate_fixture_feature(
                tmp_path,
                "raced-feature",
                title=title,
                behavior="A caller observes one stable contract.",
                expected_path="Generation -> one atomic create",
                command=None,
            )
        except FeatureMapError as exc:
            outcomes.append(exc)
        else:
            outcomes.append(result)

    threads = [threading.Thread(target=generate, args=(title,)) for title in ("First", "Second")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3)

    assert all(not thread.is_alive() for thread in threads)
    assert sum(isinstance(outcome, Path) for outcome in outcomes) == 1
    errors = [outcome for outcome in outcomes if isinstance(outcome, FeatureMapError)]
    assert len(errors) == 1
    assert "refusing to overwrite" in str(errors[0])
    assert find_feature(tmp_path, "raced-feature").title in {"First", "Second"}


def test_rejected_generation_has_no_filesystem_side_effect(tmp_path: Path) -> None:
    with pytest.raises(CommandRejected, match="verification evidence"):
        generate_fixture_feature(
            tmp_path,
            "placeholder",
            title="Placeholder",
            behavior="A user observes real behavior.",
            expected_path="Request -> result",
            command="echo proof",
        )

    assert not (tmp_path / "Wiki").exists()


def test_planted_placeholder_command_fails_feature_validation(tmp_path: Path) -> None:
    plant_fixture_feature(
        tmp_path,
        "placeholder",
        title="Placeholder",
        behavior="A user observes real behavior.",
        expected_path="Request to result.",
        command=["true"],
    )

    result = validate_feature_map(tmp_path)

    assert result["ok"] is False
    assert any("cannot establish verification evidence" in error for error in result["errors"])


def test_validate_reports_missing_related_document(tmp_path: Path) -> None:
    verifier = tmp_path / "verify.py"
    verifier.write_text("pass\n", encoding="utf-8")
    generate_fixture_feature(
        tmp_path,
        "checkout",
        title="Checkout",
        behavior="A user pays.",
        expected_path="Cart -> payment",
        command=[sys.executable, "verify.py"],
        related=["../operations/missing.md"],
    )

    result = validate_feature_map(tmp_path)

    assert result["ok"] is False
    assert "does not exist" in result["errors"][0]


@pytest.mark.parametrize(
    ("related", "message"),
    [
        ("../architecture/missing.md", "does not exist"),
        ("../../../outside.md", "escapes the project"),
    ],
)
def test_ready_generation_rejects_invalid_related_before_running_proof(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    related: str,
    message: str,
) -> None:
    proof = tmp_path / "proof.py"
    proof.write_text(
        "from pathlib import Path\nPath('proof-ran').write_text('yes')\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="2"):
        generate_fixture_cli_feature(
            "invalid-related",
            title="Invalid related path",
            behavior="A caller observes verified behavior.",
            expected_path="Input -> result",
            command=f"{sys.executable} proof.py",
            related=[related],
            ready=True,
            root=tmp_path,
            output="json",
        )

    payload = json.loads(capsys.readouterr().out)
    assert payload["error_type"] == "FeatureMapError"
    assert message in payload["error"]
    assert not (tmp_path / "proof-ran").exists()
    assert not (tmp_path / "Wiki").exists()


def test_ready_semantic_drift_is_rejected_before_proof_and_preserves_overwrite(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    existing = generate_fixture_feature(
        tmp_path,
        "stable-contract",
        title="Stable contract",
        behavior="A caller observes the original behavior.",
        expected_path="Input -> original result",
        command=None,
    )
    original = existing.read_bytes()
    proof = tmp_path / "proof.py"
    proof.write_text(
        "from pathlib import Path\nPath('proof-ran').write_text('yes')\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="2"):
        generate_fixture_cli_feature(
            "stable-contract",
            title="Stable contract",
            behavior="Intended behavior.\n\n## Expected path\n\nInjected path.",
            expected_path="Input -> legitimate result",
            command=f"{sys.executable} proof.py",
            ready=True,
            overwrite=True,
            root=tmp_path,
            output="json",
        )

    payload = json.loads(capsys.readouterr().out)
    assert payload["error_type"] == "FeatureMapError"
    assert "exactly these ordered level-2 sections" in payload["error"]
    assert not (tmp_path / "proof-ran").exists()
    assert existing.read_bytes() == original
    assert find_feature(tmp_path, "stable-contract").expected_path == "Input -> original result"


def test_related_preflight_keeps_valid_ready_and_deferred_draft_generation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    reference = tmp_path / "Wiki" / "architecture" / "boundary.md"
    reference.parent.mkdir(parents=True)
    reference.write_text("# Boundary\n", encoding="utf-8")
    proof = tmp_path / "proof.py"
    proof.write_text("raise SystemExit(0)\n", encoding="utf-8")

    generate_fixture_cli_feature(
        "ready-reference",
        title="Ready reference",
        behavior="A caller observes verified behavior.",
        expected_path="Input -> verified result",
        command=f"{sys.executable} proof.py",
        related=["../architecture/boundary.md"],
        ready=True,
        root=tmp_path,
        output="json",
    )
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert find_feature(tmp_path, "ready-reference").draft is False

    draft = generate_fixture_feature(
        tmp_path,
        "deferred-reference",
        title="Deferred reference",
        behavior="A draft records intended behavior.",
        expected_path="Input -> future result",
        command=None,
        related=["../architecture/future.md"],
    )
    assert draft.is_file()
    assert find_feature(tmp_path, "deferred-reference").draft is True
    validation = validate_feature_map(tmp_path)
    assert validation["ok"] is False
    assert any("future.md" in error and "does not exist" in error for error in validation["errors"])


@pytest.mark.parametrize("kind", ["empty", "absolute", "escape"])
def test_draft_generation_rejects_nonportable_related_paths_before_write(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    kind: str,
) -> None:
    related = {
        "empty": "",
        "absolute": str(tmp_path.parent / "outside.md"),
        "escape": "../../../outside.md",
    }[kind]

    with pytest.raises(SystemExit, match="2"):
        generate_fixture_cli_feature(
            "invalid-draft-related",
            title="Invalid draft related path",
            behavior="A draft records intended behavior.",
            expected_path="Input -> future result",
            related=[related],
            root=tmp_path,
            output="json",
        )

    payload = json.loads(capsys.readouterr().out)
    assert payload["error_type"] == "FeatureMapError"
    assert not (tmp_path / "Wiki").exists()


@pytest.mark.parametrize(
    "slug",
    ["Uppercase", "two words", "../escape", "double--dash", "readme"],
)
def test_rejects_invalid_slugs(tmp_path: Path, slug: str) -> None:
    with pytest.raises(FeatureMapError):
        generate_fixture_feature(
            tmp_path,
            slug,
            title="Title",
            behavior="Behavior",
            expected_path="Path",
            command=None,
        )


def test_planted_readme_slug_cannot_be_loaded_or_selected_as_a_feature(tmp_path: Path) -> None:
    readme = tmp_path / "Wiki" / "features" / "readme.md"
    readme.parent.mkdir(parents=True)
    readme.write_text(
        "---\n"
        "type: feature\n"
        "schema_version: 2\n"
        "slug: readme\n"
        "title: Hidden contract\n"
        "draft: true\n"
        "related: []\n"
        "---\n\n"
        "## User behavior\n\nA caller sees the hidden behavior.\n\n"
        "## Expected path\n\nInput to hidden output.\n",
        encoding="utf-8",
    )

    with pytest.raises(FeatureMapError, match="invalid feature slug 'readme'"):
        load_feature(readme, root=tmp_path)
    with pytest.raises(FeatureMapError, match="invalid feature slug 'readme'"):
        find_feature(tmp_path, "readme")


def test_structured_feature_round_trips_every_entrypoint_recipe_and_boundary(
    tmp_path: Path,
) -> None:
    path = generate_feature(
        tmp_path,
        "note-search",
        title="Note search",
        behavior="A user finds notes from either supported surface.",
        expected_path="Browser or CLI -> search service -> bounded results",
        command=[sys.executable, "verify.py"],
        sub_features=[
            ("matching", "Matching titles and bodies are returned."),
            ("empty-state", "An absent query produces a complete empty state."),
        ],
        entrypoints=[
            (
                "toolbar",
                "Choose Search in the browser toolbar.",
                "Drive the Search control by accessible name and enter the query.",
                "The result region contains only matching notes.",
            ),
            (
                "cli",
                "Run notes search from a terminal.",
                "Run notes search quarterly --format json.",
                "Exit code zero and JSON contain the matching note.",
            ),
        ],
        gotchas=[
            "Wait for the result state rather than a fixed sleep.",
            "A different entrypoint cannot stand in for a skipped one.",
        ],
        evidence_boundary="Retain bounded action and result artifacts, not raw private data.",
        cleanup_boundary="Restore seeded notes and retain proof artifacts.",
    )

    feature = load_feature(path, root=tmp_path)
    payload = feature.to_dict()

    assert feature.schema_version == 2
    assert [item.identifier for item in feature.sub_features] == ["matching", "empty-state"]
    assert [item.identifier for item in feature.entrypoints] == ["toolbar", "cli"]
    assert payload["entrypoints"][1]["drive"] == "Run notes search quarterly --format json."
    assert "## Sub-features" in path.read_text(encoding="utf-8")
    assert "## How to get to it (user POV)" in path.read_text(encoding="utf-8")
    assert "## Driving it" in path.read_text(encoding="utf-8")


def test_structured_generation_rejects_missing_entrypoint_before_write(tmp_path: Path) -> None:
    with pytest.raises(FeatureMapError, match="at least one user entrypoint"):
        generate_feature(
            tmp_path,
            "broken-map",
            title="Broken map",
            behavior="A user reaches a result.",
            expected_path="User -> result",
            command=[sys.executable, "verify.py"],
            sub_features=[("primary", "The primary behavior works.")],
            entrypoints=[],
            gotchas=["Do not skip the public surface."],
            evidence_boundary="Capture the result.",
            cleanup_boundary="Remove owned scratch state.",
        )
    assert not (tmp_path / "Wiki").exists()

    planted = tmp_path / "Wiki/features/planted.md"
    planted.parent.mkdir(parents=True)
    valid = generate_feature(
        tmp_path,
        "valid",
        title="Valid",
        behavior="A user reaches a result.",
        expected_path="User -> result",
        command=[sys.executable, "verify.py"],
        sub_features=[("primary", "The primary behavior works.")],
        entrypoints=[("cli", "Run it.", "Drive it.", "Observe it.")],
        gotchas=["Do not skip the public surface."],
        evidence_boundary="Capture the result.",
        cleanup_boundary="Remove owned scratch state.",
    )
    planted.write_text(
        valid.read_text(encoding="utf-8")
        .replace("slug: valid", "slug: planted")
        .replace("### `cli`\n\n#### Recipe", "### `other`\n\n#### Recipe"),
        encoding="utf-8",
    )
    with pytest.raises(FeatureMapError, match="same-order drive recipe"):
        load_feature(planted, root=tmp_path)


@pytest.mark.parametrize("mutation", ["duplicate-yaml", "extra-h2", "invalid-h3"])
def test_structured_feature_rejects_ambiguous_or_unstructured_markdown(
    tmp_path: Path,
    mutation: str,
) -> None:
    path = generate_feature(
        tmp_path,
        "strict-structure",
        title="Strict structure",
        behavior="A user observes one unambiguous contract.",
        expected_path="Public entrypoint -> result",
        command=[sys.executable, "verify.py"],
        sub_features=[("primary", "The main behavior completes.")],
        entrypoints=[("cli", "Run the CLI.", "Drive the CLI.", "Observe the result.")],
        gotchas=["Do not bypass the public entrypoint."],
        evidence_boundary="Retain bounded public output.",
        cleanup_boundary="Remove only verifier-owned state.",
    )
    text = path.read_text(encoding="utf-8")
    if mutation == "duplicate-yaml":
        text = text.replace("title: Strict structure", "title: First\ntitle: Strict structure")
        message = "duplicate key"
    elif mutation == "extra-h2":
        text += "\n## Operator notes\n\nUnmodeled content.\n"
        message = "exactly these ordered"
    else:
        text = text.replace("### `primary`", "### Primary behavior", 1)
        message = "invalid or unstructured"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(FeatureMapError, match=message):
        load_feature(path, root=tmp_path)


def _write_feature_plan(tmp_path: Path, *, feature_count: int = 3) -> Path:
    features: list[dict[str, object]] = []
    for index in range(feature_count):
        slug = f"surface-{index + 1}"
        script = tmp_path / f"verify-{index + 1}.py"
        script.write_text(
            f"from pathlib import Path\nPath('ran-{index + 1}').write_text('yes')\n",
            encoding="utf-8",
        )
        features.append(
            {
                "slug": slug,
                "title": f"Surface {index + 1}",
                "behavior": f"A user observes surface {index + 1}.",
                "expected_path": "Public entrypoint -> result",
                "command": [sys.executable, script.name],
                "related": [],
                "sub_features": [
                    {"identifier": "primary", "behavior": "The main behavior completes."}
                ],
                "entrypoints": [
                    {
                        "identifier": "cli",
                        "user_path": "Run the public CLI.",
                        "drive": f"Run {sys.executable} {script.name}.",
                        "observable": "The command exits zero and writes its owned marker.",
                    }
                ],
                "gotchas": ["Do not substitute a different entrypoint."],
                "evidence_boundary": "Capture the marker and bounded command result.",
                "cleanup_boundary": "Remove the owned marker after retaining evidence.",
            }
        )
    definition = tmp_path / "feature-plan.json"
    definition.write_text(json.dumps({"features": features}), encoding="utf-8")
    return definition


def test_initial_map_proves_only_representative(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    definition = _write_feature_plan(tmp_path)

    cli.feature_generate_map(
        definition,
        representative="surface-2",
        root=tmp_path,
        output="json",
    )

    result = json.loads(capsys.readouterr().out)
    assert result["representative"] == "surface-2"
    assert [item["initially_verified"] for item in result["features"]] == [False, True, False]
    assert not (tmp_path / "ran-1").exists()
    assert (tmp_path / "ran-2").read_text(encoding="utf-8") == "yes"
    assert not (tmp_path / "ran-3").exists()
    assert find_feature(tmp_path, "surface-2").draft is False
    assert find_feature(tmp_path, "surface-1").draft is True
    assert find_feature(tmp_path, "surface-3").draft is True

    cli.feature_publish("surface-1", root=tmp_path, output="json")
    first_later = json.loads(capsys.readouterr().out)
    cli.feature_publish("surface-3", root=tmp_path, output="json")
    third_later = json.loads(capsys.readouterr().out)
    assert first_later["published"] is True
    assert third_later["published"] is True
    assert (tmp_path / "ran-1").read_text(encoding="utf-8") == "yes"
    assert (tmp_path / "ran-3").read_text(encoding="utf-8") == "yes"
    assert all(not feature.draft for feature in list_features(tmp_path))


def test_initial_map_accepts_one_real_feature(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    definition = _write_feature_plan(tmp_path, feature_count=1)

    cli.feature_generate_map(
        definition,
        representative="surface-1",
        root=tmp_path,
        output="json",
    )

    result = json.loads(capsys.readouterr().out)
    assert len(result["features"]) == 1
    assert result["initial_verification"]["passed"] is True
    assert find_feature(tmp_path, "surface-1").draft is False
    assert (tmp_path / "ran-1").read_text(encoding="utf-8") == "yes"


def test_initial_map_rejects_definition_changed_by_representative_proof(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    definition = _write_feature_plan(tmp_path)
    mutator = tmp_path / "verify-2.py"
    mutator.write_text(
        "import json\n"
        "from pathlib import Path\n"
        "p = Path('feature-plan.json')\n"
        "data = json.loads(p.read_text())\n"
        "data['features'][0]['title'] = 'Changed during proof'\n"
        "p.write_text(json.dumps(data))\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="2"):
        cli.feature_generate_map(
            definition,
            representative="surface-2",
            root=tmp_path,
            output="json",
        )

    error = json.loads(capsys.readouterr().out)
    assert "changed during representative verification" in error["error"]
    assert not (tmp_path / "Wiki").exists()


def test_initial_map_failed_representative_writes_no_contracts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    definition = _write_feature_plan(tmp_path)
    (tmp_path / "verify-2.py").write_text("raise SystemExit(9)\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="1"):
        cli.feature_generate_map(
            definition,
            representative="surface-2",
            root=tmp_path,
            output="json",
        )

    result = json.loads(capsys.readouterr().out)
    assert result["created"] is False
    assert result["result"]["exit_code"] == 9
    assert not (tmp_path / "Wiki").exists()


def test_publish_failed_verifier_preserves_draft_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    definition = _write_feature_plan(tmp_path)
    cli.feature_generate_map(
        definition,
        representative="surface-2",
        root=tmp_path,
        output="json",
    )
    capsys.readouterr()
    draft = tmp_path / "Wiki/features/surface-1.md"
    original = draft.read_bytes()
    (tmp_path / "verify-1.py").write_text("raise SystemExit(7)\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="1"):
        cli.feature_publish("surface-1", root=tmp_path, output="json")

    result = json.loads(capsys.readouterr().out)
    assert result["published"] is False
    assert result["result"]["exit_code"] == 7
    assert draft.read_bytes() == original
    assert find_feature(tmp_path, "surface-1").draft is True


def test_initial_map_late_replace_failure_rolls_back_every_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    definition = _write_feature_plan(tmp_path)
    cli.feature_generate_map(
        definition,
        representative="surface-2",
        root=tmp_path,
        output="json",
    )
    capsys.readouterr()
    paths = sorted((tmp_path / "Wiki/features").glob("surface-*.md"))
    originals = {path: path.read_bytes() for path in paths}
    plan = json.loads(definition.read_text(encoding="utf-8"))
    for record in plan["features"]:
        record["title"] += " replacement"
    definition.write_text(json.dumps(plan), encoding="utf-8")

    calls = 0
    real_install = feature_module._install_feature_file

    def fail_second_replace(
        source: Path,
        target: Path,
        *,
        replace_existing: bool,
    ) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected later replacement failure")
        real_install(source, target, replace_existing=replace_existing)

    monkeypatch.setattr(feature_module, "_install_feature_file", fail_second_replace)

    with pytest.raises(SystemExit, match="2"):
        cli.feature_generate_map(
            definition,
            representative="surface-2",
            overwrite=True,
            root=tmp_path,
            output="json",
        )

    error = json.loads(capsys.readouterr().out)
    assert "was rolled back" in error["error"]
    assert {path: path.read_bytes() for path in paths} == originals
    assert not list((tmp_path / "Wiki/features").glob(".pkstack-map-*"))


def test_initial_map_no_clobber_survives_file_planted_at_install(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    definition = _write_feature_plan(tmp_path)
    real_install = feature_module._install_feature_file
    planted = tmp_path / "Wiki/features/surface-1.md"
    injected = False

    def plant_before_install(
        source: Path,
        target: Path,
        *,
        replace_existing: bool,
    ) -> None:
        nonlocal injected
        if not injected:
            injected = True
            target.write_text("planted concurrent content\n", encoding="utf-8")
        real_install(source, target, replace_existing=replace_existing)

    monkeypatch.setattr(feature_module, "_install_feature_file", plant_before_install)

    with pytest.raises(SystemExit, match="2"):
        cli.feature_generate_map(
            definition,
            representative="surface-2",
            root=tmp_path,
            output="json",
        )

    error = json.loads(capsys.readouterr().out)
    assert "rolled back" in error["error"]
    assert planted.read_text(encoding="utf-8") == "planted concurrent content\n"
    assert not (tmp_path / "Wiki/features/surface-2.md").exists()
    assert not (tmp_path / "Wiki/features/surface-3.md").exists()


def test_initial_map_overwrite_detects_target_changed_by_representative_proof(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    definition = _write_feature_plan(tmp_path)
    cli.feature_generate_map(
        definition,
        representative="surface-2",
        root=tmp_path,
        output="json",
    )
    capsys.readouterr()
    paths = sorted((tmp_path / "Wiki/features").glob("surface-*.md"))
    originals = {path: path.read_bytes() for path in paths}
    (tmp_path / "verify-2.py").write_text(
        "from pathlib import Path\n"
        "p = Path('Wiki/features/surface-1.md')\n"
        "p.write_text(p.read_text() + '\\nConcurrent batch note.\\n')\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="2"):
        cli.feature_generate_map(
            definition,
            representative="surface-2",
            overwrite=True,
            root=tmp_path,
            output="json",
        )

    error = json.loads(capsys.readouterr().out)
    assert "changed during representative verification" in error["error"]
    assert b"Concurrent batch note" in paths[0].read_bytes()
    assert paths[1].read_bytes() == originals[paths[1]]
    assert paths[2].read_bytes() == originals[paths[2]]


def test_initial_map_rejects_oversized_overwrite_target_before_proof(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    definition = _write_feature_plan(tmp_path)
    target = tmp_path / "Wiki/features/surface-1.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"x" * (feature_module.MAX_FEATURE_DOCUMENT_BYTES + 1))

    with pytest.raises(SystemExit, match="2"):
        cli.feature_generate_map(
            definition,
            representative="surface-2",
            overwrite=True,
            root=tmp_path,
            output="json",
        )

    error = json.loads(capsys.readouterr().out)
    assert "feature document exceeds" in error["error"]
    assert not (tmp_path / "ran-2").exists()
    assert target.stat().st_size == feature_module.MAX_FEATURE_DOCUMENT_BYTES + 1


def test_initial_map_rejects_symlink_target_before_representative_proof(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    definition = _write_feature_plan(tmp_path)
    target = tmp_path / "Wiki/features/surface-1.md"
    target.parent.mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("outside remains unchanged\n", encoding="utf-8")
    target.symlink_to(outside)

    with pytest.raises(SystemExit, match="2"):
        cli.feature_generate_map(
            definition,
            representative="surface-2",
            overwrite=True,
            root=tmp_path,
            output="json",
        )

    error = json.loads(capsys.readouterr().out)
    assert "symlink" in error["error"]
    assert outside.read_text(encoding="utf-8") == "outside remains unchanged\n"
    assert not any((tmp_path / f"ran-{index}").exists() for index in range(1, 4))


def test_feature_plan_rejects_duplicate_keys_and_unknown_representative(
    tmp_path: Path,
) -> None:
    definition = _write_feature_plan(tmp_path)
    raw = definition.read_text(encoding="utf-8")
    definition.write_text(raw.replace('{"features":', '{"features": [], "features":', 1))

    with pytest.raises(FeatureMapError, match="duplicate key"):
        load_feature_plan(tmp_path, definition)

    definition = _write_feature_plan(tmp_path)
    with pytest.raises(FeatureMapError, match="exactly one"):
        feature_module.prepare_initial_feature_map(
            tmp_path,
            definition,
            representative="not-in-plan",
        )


def test_publish_changes_only_draft_scalar_and_preserves_operator_prose(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    verifier = tmp_path / "verify.py"
    verifier.write_text("raise SystemExit(0)\n", encoding="utf-8")
    path = generate_feature(
        tmp_path,
        "byte-preserving",
        title="Byte preserving",
        behavior="A user observes the public result.",
        expected_path="Public entrypoint -> result",
        command=[sys.executable, verifier.name],
        sub_features=[("primary", "The main behavior completes.")],
        entrypoints=[("cli", "Run it.", "Drive it.", "Observe it.")],
        gotchas=["Do not bypass the public path."],
        evidence_boundary="Retain bounded public evidence.",
        cleanup_boundary="Remove only verifier-owned state.",
    )
    text = path.read_text(encoding="utf-8").replace(
        "# Byte preserving\n\n",
        "# Byte preserving\n\nOperator preamble: preserve this exact line.\n\n",
        1,
    )
    text = text.replace(
        "A passing command proves the behavior described above, not merely that files exist.",
        "Operator verification prose: this boundary is load-bearing.",
    )
    path.write_text(text, encoding="utf-8")
    before = path.read_bytes()
    assert validate_feature_map(tmp_path)["ok"] is True

    cli.feature_publish("byte-preserving", root=tmp_path, output="json")

    result = json.loads(capsys.readouterr().out)
    assert result["published"] is True
    assert path.read_bytes() == before.replace(b"draft: true", b"draft: false", 1)
    assert b"Operator preamble" in path.read_bytes()
    assert b"Operator verification prose" in path.read_bytes()


def test_ready_generate_detects_existing_contract_changed_by_its_verifier(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = generate_fixture_feature(
        tmp_path,
        "ready-race",
        title="Original contract",
        behavior="A user observes the original result.",
        expected_path="Original entrypoint -> result",
        command=None,
    )
    mutator = tmp_path / "mutate.py"
    mutator.write_text(
        "from pathlib import Path\n"
        "p = Path('Wiki/features/ready-race.md')\n"
        "p.write_text(p.read_text() + '\\nConcurrent operator note.\\n')\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="2"):
        generate_fixture_cli_feature(
            "ready-race",
            title="Replacement contract",
            behavior="A user observes the replacement result.",
            expected_path="Replacement entrypoint -> result",
            command=f"{sys.executable} {mutator.name}",
            ready=True,
            overwrite=True,
            root=tmp_path,
            output="json",
        )

    error = json.loads(capsys.readouterr().out)
    assert "changed during verification" in error["error"]
    assert "Concurrent operator note" in path.read_text(encoding="utf-8")
    assert find_feature(tmp_path, "ready-race").title == "Original contract"


def test_publish_detects_contract_changed_by_its_verifier(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mutator = tmp_path / "mutate.py"
    mutator.write_text(
        "from pathlib import Path\n"
        "p = Path('Wiki/features/publish-race.md')\n"
        "p.write_text(p.read_text() + '\\nConcurrent publication note.\\n')\n",
        encoding="utf-8",
    )
    path = generate_feature(
        tmp_path,
        "publish-race",
        title="Publish race",
        behavior="A user observes the draft behavior.",
        expected_path="Public entrypoint -> result",
        command=[sys.executable, mutator.name],
        sub_features=[("primary", "The behavior completes.")],
        entrypoints=[("cli", "Run it.", "Drive it.", "Observe it.")],
        gotchas=["Do not lose operator content."],
        evidence_boundary="Retain bounded output.",
        cleanup_boundary="Remove verifier-owned state.",
    )

    with pytest.raises(SystemExit, match="2"):
        cli.feature_publish("publish-race", root=tmp_path, output="json")

    error = json.loads(capsys.readouterr().out)
    assert "changed during verification" in error["error"]
    assert "Concurrent publication note" in path.read_text(encoding="utf-8")
    assert find_feature(tmp_path, "publish-race").draft is True


def test_feature_document_and_concurrently_growing_plan_are_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    feature = tmp_path / "Wiki/features/oversized.md"
    feature.parent.mkdir(parents=True)
    feature.write_bytes(b"x" * (feature_module.MAX_FEATURE_DOCUMENT_BYTES + 1))

    with pytest.raises(FeatureMapError, match="feature document exceeds"):
        load_feature(feature, root=tmp_path)
    validation = validate_feature_map(tmp_path)
    assert validation["ok"] is False
    assert any("feature document exceeds" in error for error in validation["errors"])

    definition = _write_feature_plan(tmp_path)
    original_open = Path.open
    grew = False

    def grow_before_binary_open(path: Path, mode: str = "r", *args: Any, **kwargs: Any):
        nonlocal grew
        if path == definition and mode == "rb" and not grew:
            grew = True
            with original_open(path, "ab") as handle:
                handle.write(b" " * feature_module.MAX_FEATURE_PLAN_BYTES)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", grow_before_binary_open)
    with pytest.raises(FeatureMapError, match="feature plan exceeds"):
        load_feature_plan(tmp_path, definition)


@pytest.mark.parametrize("feature_count", [0, 6])
def test_initial_map_rejects_out_of_range_count(tmp_path: Path, feature_count: int) -> None:
    definition = _write_feature_plan(tmp_path, feature_count=feature_count)

    with pytest.raises(FeatureMapError, match="1-5 records"):
        load_feature_plan(tmp_path, definition)


def test_shipped_repository_features_are_complete_schema_two_contracts() -> None:
    result = validate_feature_map(REPOSITORY_ROOT)

    assert result["ok"] is True, result["errors"]
    assert result["warnings"] == []
    assert result["feature_count"] == 4
    features = {item["slug"]: item for item in result["features"]}
    assert set(features) == {
        "pkstack-consumer-permissions",
        "pkstack-guide",
        "pkstack-upstream-maintenance",
        "pkstack-power-installation",
    }
    assert all(item["schema_version"] == 2 for item in features.values())
    assert {
        item["identifier"] for item in features["pkstack-power-installation"]["entrypoints"]
    } == {"cli"}
    assert {item["identifier"] for item in features["pkstack-guide"]["entrypoints"]} == {
        "setup",
        "discovery",
    }
    assert {
        item["identifier"] for item in features["pkstack-consumer-permissions"]["entrypoints"]
    } == {"cli"}
    assert {
        item["identifier"] for item in features["pkstack-upstream-maintenance"]["entrypoints"]
    } == {"local-check", "current-session-maintenance", "scheduled-cadence", "manual-dispatch"}

    maintenance_path = REPOSITORY_ROOT / "Wiki/features/pkstack-upstream-maintenance.md"
    maintenance = maintenance_path.read_text(encoding="utf-8")
    assert "exactly one canonical genesis marker" in maintenance
    assert "Kiro-hosted Claude Opus 5" in maintenance
    assert "`xhigh`" in maintenance
