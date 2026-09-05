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

## Merged identity cleanup

The [merged identity cleanup, PR #18](https://github.com/njs14/pkstack/pull/18),
standardizes the product name as **PKStack**, the technical
handle as `pkstack`, and the primary skill as `/pkstack`. It updates the
package, managed workspace assets, six PKStack command routes, documentation,
and banner while preserving upstream methods and immutable source identities.

The identity candidate's local gates passed **827 Power tests, 134 repository-policy tests,
and 17 JavaScript tests**, plus lint, formatting, types, lockfile checks,
Actionlint, and ShellCheck. Kiro CLI 2.21.1 loaded `/pkstack` with Luna / Low.
The renamed `/pkstack-verified-goal` campaign passed in the same CLI session:
stored failure, an `account.py`-only repair, and all four unchanged tests passing
on attempt two. Kiro IDE 1.0.437 imported the renamed Power and displayed all
six canonical skills; their installed files match the source. The
[identity validation report](pkstack-identity-validation.md)
records the candidate, commands, and completed results.

## Outstanding release gate

**The 0.3.0 release is withheld pending the first complete updater campaign.**
The owner approved re-enabling the autonomous updater after
[PR #19](https://github.com/njs14/pkstack/pull/19). The
[first enabled run](https://github.com/njs14/pkstack/actions/runs/33945088358)
failed all four bounded attempts: two missing proposals, then two missing
provenance markers. It published no candidate and did not reach peer review.
[PR #20](https://github.com/njs14/pkstack/pull/20) repaired agent loading after
exact-head CI passed. The updater is enabled again on the approved daily
13:17 UTC schedule. Its [corrected acceptance run](https://github.com/njs14/pkstack/actions/runs/33946810878)
passed direct global-agent attestation and secretless verification on repair
one. Its candidate gate then rejected an incomplete trusted snapshot before
Opus review. [PR #22](https://github.com/njs14/pkstack/pull/22) restored the
required snapshot path. The next candidate passed base and candidate tests,
then stopped during offline reviewer setup because the CLI launcher required
login. The repair uses the canary's existing secretless `kiro-cli-chat agent
validate` path. The updater remains enabled, but end-to-end acceptance is still
outstanding.

The last instrumented updater [run 33934250700](https://github.com/njs14/pkstack/actions/runs/33934250700)
failed at proposal validation (exit 1; cleanup 0) after setup, feature
validation, and generated parity passed. It was cancelled during repair two
to avoid further spending. No candidate was published or peer-reviewed.
The exact inner failure is unproven because the retained diagnostic does not
distinguish a missing proposal, invalid proposal/provenance, or source binding.

A follow-up found and fixed a prompt/input mismatch: the repair instructions
referred to a detector `drift_count` field absent from the supplied JSON. The
repair now follows the validated controller action and emits fixed, safe
proposal failure reasons. [PR #19](https://github.com/njs14/pkstack/pull/19)
also updates the reviewed Linux runtime pin to 2.21.1 after the canary detected
stable-version drift. The [pipeline validation report](pipeline-readiness-validation.md)
records 146 passing policy tests, 17 Node tests, independent review, archive
verification, and scoped live smoke results.

The 2.21.1 credential and final
[permission smoke](https://github.com/njs14/pkstack/actions/runs/33944622193)
passed. The validator now handles 2.21.1's omitted preview originals and null
diff originals. Seven allowed writes and all six denied paths passed, with
exact policy-denial evidence, protected-file checksums, and cleanup.

A local Kiro 2.21.1 probe exposed a separate runtime defect: `agent list`
recognized the maintainer under `KIRO_HOME`, but v3 chat ignored that location
and selected Default. The production layout likewise separated `KIRO_HOME`
from `HOME/.kiro`. Its private streams were deleted during cleanup, so the
historical production selection is not directly attested. The repair aligns
those paths and requires direct selected-agent evidence before a maintenance
result can be accepted. The corrected Linux run passed that attestation. The
candidate was [PR #21](https://github.com/njs14/pkstack/pull/21), which the
failed-candidate cleanup closed without merging. The full update and
independent-review campaign still needs to pass.

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
  hands-off updates are declared validated.
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
