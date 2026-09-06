# PKStack 0.4.3 routing follow-up — v5

**The previously failing CLI command-emission check passes. Independent review approved source and bounded native acceptance; all 12 CI jobs passed for source commit `e4941073adf89a130e8ee268fb122c113cf8a409`.**

The [v4 report](../planning-043-v4/README.md) preserves two failures to emit the runnable native Plan command, the reviewed implementation and capture-order results, and the IDE Quick Spec no-write evidence. This follow-up changes only routing guidance and its existing regression assertions; it does not rewrite those historical outcomes.

Claude Code Opus 5 at `xhigh` made the CLI handoff form explicit in the directly loaded agent prompt and core steering, matching the router skill. The requirement applies only to an inactive, user-requested conversational Plan. Spec, Quick Spec and Bug Fix retain their native routes. Approval-return wording in the router and workflow reference now applies to Spec-backed work; conversational Plan keeps Kiro's own execution handoff.

The coordinator caught an initially unscoped steering sentence before integration, requested its correction, and preserved the prior routing-fixture prohibition on claiming that the agent selected Plan. The repair is based on an observed source inconsistency. The absence of a visible router-skill read is not proof that Kiro did not inject that text; the model-causality explanation remains an inference.

## Native result

A fresh fixture used the same three authoritative input files, unchanged, with the frozen v5 Power. On the original request, without a command-format reminder, CLI `Auto` read the inputs, emitted `/plan Read .kiro/skills/grilling/SKILL.md;` with the context and open error-wording choice, and stopped. No fixture file changed. The coordinator did not provide the prefix or enter Plan in this test.

The [result receipt](router-result.json) retains the exact request, observed command, session identity, raw recording hash, file delta and limitations. The [terminal transcript](router-transcript.txt) is a rendering of the terminal's visible display; its line wrapping is not a clipboard export. The raw recording remains local.

**The router's proposed uppercase-before-validation ordering was still wrong for non-ASCII input.** It was not implemented in this router-only scenario. The v4 plan review had corrected that same mistake before execution. Command emission now passes; autonomous Unicode reasoning is not claimed. The generated command was not executed here, and this single passing response does not erase the two earlier v4 failures.

## Validation and scope

- [Checks](checks.json): the 22-test fast gate and two focused routing-boundary checks passed after integration; the worker reported 131 focused tests and clean lint/format checks.
- Reviewed setup refreshed four managed files; the final preview has no pending changes or conflicts.
- [Source manifest](source-files-v5.json): 293 Power files, frozen after integration and the coordinator's fixture correction.
- [Worker patch manifest](worker-patch-manifest.json): the six-path incremental repair before that small coordinator test-fixture correction.
- The full v4 gate passed 965 product tests and policy; v4 hosted CI passed all 12 jobs. Those are identified as v4 results. No full local gate was repeated for this routing-only change.

No grilling interview method, capture lifecycle, product Python, global settings, hooks or permissions changed in v5. The bounded native Plan/capture/implementation and IDE evidence remains the v4 campaign's evidence. [Independent review](independent-review.json) approved composing that evidence with this routing-only result. The [exact-source CI receipt](hosted-ci-e494107.json) satisfies its CI condition. Later report-only metadata commits may have different Git identities; the Power manifest still binds the reviewed source. Merge and release-package verification remain separate gates. No merge, tag or publication is claimed by this report.
