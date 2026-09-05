---
release: "0.3.0"
status: candidate
version_authority: powers/pkstack/plugin.json
---

# PKStack release status

The current source targets **0.3.0**. It is not released until the exact reviewed
main commit is tagged and the release workflow succeeds.
[v0.2.0](https://github.com/njs14/pkstack/releases/tag/v0.2.0) remains the
previous published release.

## Identity candidate

The current change standardizes the product name as **PKStack**, the technical
handle as `pkstack`, and the primary skill as `/pkstack`. It updates the
package, managed workspace assets, six PKStack command routes, documentation,
and banner while preserving upstream methods and immutable source identities.

The current local gates passed **827 Power tests, 134 repository-policy tests,
and 17 JavaScript tests**, plus lint, formatting, types, lockfile checks,
Actionlint, and ShellCheck. Kiro CLI 2.21.1 loaded `/pkstack` with Luna / Low.
The renamed `/pkstack-verified-goal` campaign passed in the same CLI session:
stored failure, an `account.py`-only repair, and all four unchanged tests passing
on attempt two. The renamed Power's IDE import is still in flight and is not
recorded as passed. The [identity validation report](pkstack-identity-validation.md)
records the candidate, commands, and completed results.

## Outstanding release gate

**The 0.3.0 release is withheld.** The paid upstream-maintenance workflow
remains `disabled_manually`; normal CI is enabled. Hands-off upstream updates
have not passed live acceptance.

The last instrumented updater [run 33934250700](https://github.com/njs14/pkstack/actions/runs/33934250700)
failed at proposal validation (exit 1; cleanup 0) after setup, feature
validation, and generated parity passed. It was cancelled during repair two
to avoid further spending. No candidate was published or peer-reviewed.
The exact inner failure is unproven because the retained diagnostic does not
distinguish a missing proposal, invalid proposal/provenance, or source binding.

A read-only follow-up found a prompt/input mismatch: the repair instructions
refer to a detector `drift_count` field that is absent from the supplied
detector JSON. The validated control plan contains that field and the selected
action. Correcting this mismatch and adding bounded diagnostic coverage are
next-phase repairs, not a proven explanation or fix for the historical run.
The workflow stays disabled until that work is verified.

## Release requirements

- Package metadata and both lockfiles match `plugin.json`.
- Lint, formatting, type checks, package tests, repository guards, Actionlint,
  and ShellCheck pass.
- Generated controller/assets match a reviewed Power-local setup.
- The fresh-consumer README walkthrough records failure, repair, and pass.
- Interactive Kiro CLI v3 checks retain normal current-session behavior and
  explicit permissions.
- Independent review has no material unresolved finding.
- The repaired updater passes a bounded live acceptance campaign before
  hands-off cadence resumes.
- The private PR passes its checks before merge; the release tag resolves to
  the reviewed main commit.

## Historical evidence

The [cleanup report](cleanup-validation.md) covers the preceding implementation,
including deletion of schema-1 compatibility and duplicate controller assets,
verifier cancellation fixes, and the executed README walkthrough.
[PR #13](https://github.com/njs14/pkstack/pull/13) merged that cleanup after CI
passed; [PR #15](https://github.com/njs14/pkstack/pull/15) added the updater's
fixed-stage diagnostics. Those results do not accept the current candidate.

Earlier Kiro CLI 2.21.0 sessions proved direct-command and native Quick Spec
fail → repair → pass handoffs. The September 4 Kiro IDE 1.0.437 smoke proved
native Power import, setup, generated-agent selection, and three separately
approved controller checks with Luna / Low. Its
[recorded scope](cleanup-validation.md#native-ide-smoke-test--september-4-2026)
does not include IDE goal-repair or Spec/Quick Spec execution. These historical
records preserve the names actually tested. Kiro Web remains untested, and
Crew is an optional compatibility target.

Earlier implementation and review records remain under
[historical/pre-v0.2](historical/pre-v0.2/). They retain their original scope.
The [Floci integration lab](https://github.com/njs14/pk-stack-floci-lab)
is a separate private consumer repository and is not included in the Power.
