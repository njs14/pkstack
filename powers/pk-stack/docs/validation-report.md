# Validation report

This report describes how to validate a PK-Stack release candidate. It is a
release-process document, not a standing pass claim. The [current release
status](../../../reviews/release-status.md) is the single place for the
candidate commit and gate verdicts.

## Authority and evidence boundary

The version in [`plugin.json`](../plugin.json) is the release metadata
authority. `pyproject.toml`, `src/pk_stack/__init__.py`, and the shipped
lockfiles are mirrors. Verify the authority first and compare every mirror
before recording any other result.

Historical runs and review reports are retained under
[`reviews/historical/pre-v0.2/`](../../../reviews/historical/pre-v0.2/) and
[`powers/pk-stack/reviews/historical/pre-v0.2/`](../reviews/historical/pre-v0.2/).
They preserve useful source identities and limitations, but they do not prove
the current release. The Floci application and live integration campaigns are
owned by the separate private
[pk-stack-floci-lab](https://github.com/njs14/pk-stack-floci-lab) repository.

## Deterministic local checks

Run these commands from the indicated directory on the exact candidate commit.
Record the exit code, test count, and any missing optional dependency in the
release-status evidence packet.

From `powers/pk-stack/`:

```sh
uv lock --check
uv run --frozen ruff check src tests skills/setup-pk-stack/scripts/setup_pk_stack.py
uv run --frozen ruff format --check src tests skills/setup-pk-stack/scripts/setup_pk_stack.py
uv run --frozen ty check
uv run --frozen pytest -q
```

From the repository root:

```sh
python3 -m pytest powers/pk-stack/tests/test_release_metadata.py -q
.pk-stack/bin/projectctl doctor --output json
.pk-stack/bin/projectctl feature validate --output json
.pk-stack/bin/projectctl knowledge validate --output json
```

The metadata regression compares `plugin.json`, `pyproject.toml`, the package
`__version__`, and the package lock. It does not make generated `.pk-stack/`
content authoritative; generated parity must be checked through setup and the
receipt after the Power's bootstrap source is updated.

Repository checks are separate from the package suite:

```sh
python3 .github/scripts/test_pk_stack_maintenance_guard.py
python3 .github/scripts/test_kiro_runtime_canary.py
node --test .github/scripts/test_pk_stack_pr_policy.js
actionlint .github/workflows/*.yml
shellcheck .github/scripts/*.sh
```

Run only the checks that are in scope for the candidate. A tool that is not
installed is a limitation, not a passing result. Do not copy host-specific
absolute paths into a report; use the command as run from the repository root
or a temporary directory name without exposing local identity.

## Workspace and Kiro checks

On a disposable project, use the Power-local setup flow from
[Usage](usage.md): first a dry run, then an explicitly approved apply. Confirm
that the receipt is complete, the internal lock is current, `doctor` reports no
managed drift, and the generated `pk-stack` profile is selected before invoking
`/verified-goal`. A fixture's passing goal proves that fixture predicate only.

Kiro CLI v3/IDE, Crew, and Web observations must identify the exact surface,
client build, model/effort when relevant, and whether the observation was
read-only. A Kiro log label or reviewer statement does not prove a capability
that was not observed. External Fable or Grok output is review evidence and
must not replace deterministic checks.

## Release gate record

The final candidate must have a fresh result for each row in
[`reviews/release-status.md`](../../../reviews/release-status.md):

1. metadata equality and lock consistency;
2. package tests, lint, format, and type checks;
3. setup/doctor/generated-byte parity;
4. feature validation and clearly labeled optional `okn` status;
5. repository guard, policy, Actionlint, ShellCheck, and documentation checks;
6. exact-candidate Kiro evidence where the release contract requires it;
7. independent review of the exact candidate, naming the reviewer and any
   unavailable requested reviewer; and
8. a private PR and a version tag matching `plugin.json`, bound to the
   reviewed commit after merge.

Every material change after review returns the candidate to the affected
checks. A historical `ACCEPT`, a clean older worktree, or a passing fixture
does not close a new row.

## Known limits

- The runner is a bounded hazard screen, not an operating-system sandbox or a
  semantic proof checker.
- Optional canonical `okn`, Kiro Web end-to-end behavior, and external review
  CLIs may be unavailable in a local environment.
- The receipt is a SHA-256 drift detector, not a signature against a writer
  who controls both content and receipt.
- The Power has one goal slot and no automatic uninstaller or stale-file
  deletion.

Until the release-status document records the final reviewed commit and tag,
the current tree is a candidate, even when an older version has been released.
