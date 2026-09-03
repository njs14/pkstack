# PK-Stack release ledger

This ledger tracks the current product release. Historical Floci findings and campaigns live in `njs14/pk-stack-floci-lab`; earlier source-only review history remains under `powers/pk-stack/reviews/`.

## Product contract

- Kiro CLI v3 and the Kiro IDE agent panel are the primary surfaces.
- Kiro Crew is optional. Kiro Web is supported by committed assets and remains untested end to end.
- Native Spec, Quick Spec, and Bug Fix workflows own planning.
- `/verified-goal` is a PK-Stack current-session skill backed by deterministic `projectctl` state. It is not Kiro's native `/goal` and does not make ACP the normal entrypoint.
- The feature map is the PROVE layer. Source-controlled OKF plus optional canonical `okn` is the KNOW layer.
- `powers/pk-stack/` is the only Power source and upgrade authority.
- The private Floci lab is a separate consumer repository.
- GitHub Actions uses `KIRO_API_KEY` only. No Anthropic, OpenAI, xAI, or GitHub Copilot credential is accepted.

## Current release gates

| Gate | Required evidence | Status |
| --- | --- | --- |
| Power package | lock, Ruff, format, type check, and complete pytest suite | passed locally: 787 tests |
| Generated controller | clean setup dry-run and managed-byte parity | passed locally: no changes or conflicts |
| Feature and knowledge contracts | `feature validate`, `knowledge status`, and `knowledge validate` | passed locally; optional `okn` unavailable |
| GitHub workflows | guard tests, policy tests, Actionlint, and ShellCheck | passed locally: 74 guard, 25 canary, 16 policy, 9 inventory, and 6 review-stream tests |
| Hosted Kiro | exact-candidate credential smoke and advertised Claude Opus 5 `xhigh` review capability | pending final candidate |
| Fable peer review | Fable 5.1 `xhigh`, exact candidate, zero material unresolved findings | pending remediation re-review |
| Grok sweep | official Grok 4.6 CLI at `xhigh`, or recorded user-owned authentication blocker | pending |
| Publication | private PR head equals reviewed candidate and required checks pass | pending |

## Fable remediation in progress

The last candidate review rejected commit `855a03ba9825b22394a6cc58514c7911ff9ba6a1` with six material findings. The final candidate must prove all six closed:

1. authenticate and validate the hosted model inventory before requesting Claude Opus 5;
2. remove the test reference to the deleted maintenance-workflow Markdown file;
3. bind reviewer approval to the exact agent, model, effort, bundle, changed-file count, and path digest;
4. cover the real Kiro v3 model and mode event shape with a sanitized fixture;
5. run review-stream and model-inventory validator tests in the candidate gate;
6. keep isolated Kiro state writable while the review workspace stays read-only.

Any material code or workflow change after approval requires another Fable review.

## Release report

The final release report will record the tested commit, exact commands, hosted run URLs, reviewer verdicts, known limits, and rollback procedure. Until that report exists, this branch is a candidate rather than a release.
