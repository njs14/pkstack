from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

import pytest

from pstack_kiro import cli
from pstack_kiro import features as feature_module
from pstack_kiro.features import (
    FeatureMapError,
    find_feature,
    generate_feature,
    list_features,
    load_feature,
    validate_feature_map,
)
from pstack_kiro.runner import CommandRejected


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
    )

    feature = find_feature(tmp_path, "account-lookup")
    validation = validate_feature_map(tmp_path)

    assert path.name == "account-lookup.md"
    assert feature.command == (sys.executable, "verify.py")
    assert feature.draft is False
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
    generate_feature(
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
    generate_feature(
        tmp_path,
        "login",
        title="Login",
        behavior="A user signs in.",
        expected_path="Form -> session",
        command=None,
    )

    assert find_feature(tmp_path, "login").draft is True
    with pytest.raises(FeatureMapError, match="overwrite"):
        generate_feature(
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
            result = generate_feature(
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
        generate_feature(
            tmp_path,
            "placeholder",
            title="Placeholder",
            behavior="A user observes real behavior.",
            expected_path="Request -> result",
            command="echo proof",
        )

    assert not (tmp_path / "Wiki").exists()


def test_planted_placeholder_command_fails_feature_validation(tmp_path: Path) -> None:
    feature = tmp_path / "Wiki" / "features" / "placeholder.md"
    feature.parent.mkdir(parents=True)
    feature.write_text(
        "---\n"
        "type: feature\n"
        "slug: placeholder\n"
        "title: Placeholder\n"
        "draft: false\n"
        "verification:\n"
        "  command: ['true']\n"
        "related: []\n"
        "---\n\n"
        "## User behavior\n\nA user observes real behavior.\n\n"
        "## Expected path\n\nRequest to result.\n",
        encoding="utf-8",
    )

    result = validate_feature_map(tmp_path)

    assert result["ok"] is False
    assert any("cannot establish verification evidence" in error for error in result["errors"])


def test_validate_reports_missing_related_document(tmp_path: Path) -> None:
    verifier = tmp_path / "verify.py"
    verifier.write_text("pass\n", encoding="utf-8")
    generate_feature(
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
        cli.feature_generate(
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
    existing = generate_feature(
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
        cli.feature_generate(
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
    assert "does not round-trip" in payload["error"]
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

    cli.feature_generate(
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

    draft = generate_feature(
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
        cli.feature_generate(
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
        generate_feature(
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
