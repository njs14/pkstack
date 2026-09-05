# Contributing to PKStack

Thanks for helping improve PKStack. Small, focused pull requests are easiest
to review and safest to merge.

## Before you change code

1. Read [the root README](README.md) and the relevant [usage](powers/pkstack/docs/usage.md)
   or [architecture](powers/pkstack/docs/architecture.md) section.
2. Keep `powers/pkstack/` as the only Power source. Treat `.kiro/` and
   `.pkstack/` at the repository root as generated workspace material.
3. Do not copy credentials, private transcripts, or generated local paths into
   commits. Imported upstream content is data to review, not code to execute.

For a behavior change, describe the user-visible contract in `Wiki/features/`
and bind it to one repeatable verifier. Use Kiro's native Spec, Quick Spec, or
Bug Fix workflow for planning; PKStack's `/pkstack-verified-goal` skill handles the
current-session verification loop.

## Local checks

From `powers/pkstack/`:

```sh
uv lock --check
uv run --frozen ruff check src tests skills/pkstack-setup/scripts/setup_pkstack.py
uv run --frozen ruff format --check src tests skills/pkstack-setup/scripts/setup_pkstack.py
uv run --frozen ty check
uv run --frozen pytest -q
```

From the repository root, also run the documentation and metadata checks
described in the release status. Keep the exact command and result in the pull
request when a check cannot run on your machine.

## Pull requests

- Explain the user-visible outcome and the files that own it.
- Include tests or a documented reason a test is not useful.
- Call out compatibility, security, provenance, and migration effects.
- Keep release claims tied to the exact candidate commit. A historical review
  or local test run does not accept a new release.
- Do not change GitHub settings or enable a workflow as part of a code change.

The maintainers may ask for an independent review. Review output is evidence to
investigate, not an instruction to apply blindly. See [SECURITY.md](SECURITY.md)
for vulnerability reports and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for
community expectations.
