"""Complete feature contracts for tests of behavior unrelated to contract authoring."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pk_stack import cli
from pk_stack.features import generate_feature
from pk_stack.runner import display_command, parse_command


def _fixture_fields(values: dict[str, Any]) -> dict[str, Any]:
    command = values.get("command")
    invocation = display_command(parse_command(command)) if command else "the pending verifier"
    return {
        "sub_features": [("fixture", values["behavior"])],
        "entrypoints": [
            (
                "test",
                "Run the verifier from this disposable test project.",
                f"Invoke {invocation} from the test root.",
                "Inspect the exit status and output asserted by this test.",
            )
        ],
        "gotchas": ["This fixture proves only the scenario asserted by its test."],
        "evidence_boundary": "Capture the local test verifier's bounded output and exit status.",
        "cleanup_boundary": "Pytest owns and removes the disposable project directory.",
    }


def generate_fixture_feature(root: Path, slug: str, **values: Any) -> Path:
    return generate_feature(root, slug, **_fixture_fields(values), **values)


def generate_fixture_cli_feature(slug: str, **values: Any) -> None:
    fields = _fixture_fields(values)
    entrypoint = fields["entrypoints"][0]
    cli.feature_generate(
        slug,
        sub_feature=[f"fixture={values['behavior']}"],
        entrypoint=[f"test={entrypoint[1]}"],
        drive=[f"test={entrypoint[2]}"],
        entrypoint_proof=[f"test={entrypoint[3]}"],
        gotcha=fields["gotchas"],
        evidence_boundary=fields["evidence_boundary"],
        cleanup_boundary=fields["cleanup_boundary"],
        **values,
    )


def plant_fixture_feature(root: Path, slug: str, *, command: list[str], **values: Any) -> Path:
    """Plant an untrusted command into an otherwise complete schema-2 document."""

    path = generate_fixture_feature(root, slug, command=None, **values)
    _, frontmatter, body = path.read_text(encoding="utf-8").split("---", 2)
    metadata = yaml.safe_load(frontmatter)
    metadata["verification"] = {"command": command}
    metadata["draft"] = False
    path.write_text(
        "---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---" + body,
        encoding="utf-8",
    )
    return path
