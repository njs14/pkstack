# Validation report

This report describes how to validate a PKStack release candidate. It is a
release-process document. Record candidate verdicts in a dated evidence packet
using the [gate contract below](#release-gate-record). The
[release record](../Wiki/knowledge/pkstack/release-record.md) retains publication
facts and links to evidence; its historical entries do not validate this candidate.

## Authority and evidence boundary

The version in [`plugin.json`](../powers/pkstack/plugin.json) is the release metadata
authority. `pyproject.toml`, `src/pkstack/__init__.py`, and the shipped
lockfiles are mirrors. Verify the authority first and compare every mirror
before recording any other result.

Historical runs and review reports are retained under
[`reviews/historical/pre-v0.2/`](https://github.com/njs14/pkstack/tree/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/historical/pre-v0.2) and
[`reviews/historical/pre-v0.2/`](../reviews/historical/pre-v0.2).
They preserve useful source identities and limitations, but they do not prove
the current release. The Floci application and live integration campaigns are
owned by the separate private
[pk-stack-floci-lab](https://github.com/njs14/pk-stack-floci-lab) repository.

## Deterministic local checks

Run the shared gate from the repository root on the exact candidate. Maintainer
commands use the ignored root `.venv`; pytest and Ruff caches also stay outside
the Power. Keep this environment setting for `uv sync`, lint, and test commands:

```sh
export UV_PROJECT_ENVIRONMENT="$PWD/.venv"
uv run --frozen --project . python -B .github/scripts/pkstack_checks.py local full
```

The command prints a fresh evidence directory containing one summary and failure
diagnostics. Retain that packet with the candidate commit, exit status, test counts,
and limitations. Local and hosted checks use the same execution functions; avoid
maintaining a second checklist of individual test commands here.
The full profile covers package and repository tests, metadata/lock consistency,
static checks, policy checks, and generated/distribution contracts.

For a focused edit, run the affected tests first; run the full profile on the
completed release candidate. A missing tool or failed lane is a failed or
unverified gate. Generated `.pkstack/` content is never a source authority: check
its bytes through reviewed setup and the receipt after updating the Power source.

## Workspace and Kiro checks

On a disposable project, use the Power-local setup flow from
[Usage](../powers/pkstack/docs/usage.md): first a dry run, then an explicitly approved apply. Confirm
that the receipt is complete, the internal lock is current, `doctor` reports no
managed drift, and the generated `pkstack` profile is selected before invoking
`/pkstack-verified-goal`. A fixture's passing goal proves that fixture predicate only.

Kiro CLI v3/IDE, Crew, and Web observations must identify the exact surface,
client build, model/effort when relevant, and whether the observation was
read-only. A Kiro log label or reviewer statement does not prove a capability
that was not observed. External Fable or Grok output is review evidence and
must not replace deterministic checks.

## Release gate record

The dated evidence packet for the final candidate must record a fresh verdict
and supporting command/output or artifact for each acceptance row below:

1. metadata equality and lock consistency;
2. package tests, lint, format, and type checks;
3. setup/doctor/generated-byte parity;
4. local feature, knowledge metadata, and Markdown-link validation, with Kiro
   retrieval availability reported separately;
5. repository guard, policy, Actionlint, ShellCheck, and documentation checks;
6. exact-candidate Kiro evidence where the release contract requires it;
7. independent review of the exact candidate, naming the reviewer and any
   unavailable requested reviewer; and
8. a PR and a version tag matching `plugin.json`, bound to the
   reviewed commit after merge.

Every material change after review returns the candidate to the affected
checks. A historical `ACCEPT`, a clean older worktree, or a passing fixture
does not close a new row.

## Known limits

- The runner is a bounded hazard screen, not an operating-system sandbox or a
  semantic proof checker.
- Kiro retrieval, Kiro Web end-to-end behavior, and external review CLIs may
  be unavailable in a local environment. Local knowledge validation remains
  available without Kiro or a model.
- The receipt is a SHA-256 drift detector, not a signature against a writer
  who controls both content and receipt.
- The Power has one goal slot and no automatic uninstaller or stale-file
  deletion.

Until the release-status document records the final reviewed commit and tag,
the current tree is a candidate, even when an older version has been released.
