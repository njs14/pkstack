---
name: diagnosing-bugs
description: Reproduce and diagnose bugs or performance regressions with a tight feedback loop, competing hypotheses, and proof of the original symptom. Use when behavior fails, flakes, or becomes slow.
---

# Diagnose the reported failure

Read relevant code, tests, project knowledge, and existing decisions. Reuse the current native
Bug Fix or Spec; keep its bug analysis, design, and tasks authoritative. This method also supplies
PKStack's performance diagnosis. Use [grilling](../grilling/SKILL.md) only for consequential
unknowns that inspection cannot answer.

Honor the user's scope and active Kiro workflow. In native Plan, use permitted reading and
search, keep the result conversational, and defer commands, MCP calls, file writes, experiments,
and validation until execution is permitted. A skill invocation does not widen authority.

1. Build a feedback loop that exercises the exact reported symptom. Prefer the closest existing
   failing test, CLI fixture, request replay, browser observation, or disposable harness. Verify
   that a command actually went red for this bug; unrelated errors and “did not crash” are not
   reproductions. Pin inputs, time, randomness, and environment where useful. For intermittent
   failures, measure a bounded repetition rate and retain the seed/trigger and observed counts.
   For performance, establish a comparable timing/profile baseline before changing behavior.
2. Minimize the reproduction one element at a time, keeping the same failure signal. Do not
   delete relevant concurrency or caller interactions just to obtain a simpler but different bug.
   If access prevents reproduction, state attempted checks and the missing observation. Read-only
   hypotheses may guide the next experiment; do not claim a verified cause or speculative fix.
3. Rank the plausible competing hypotheses and give each a falsifiable prediction. Share the
   short list without imposing an approval pause. Test the most discriminating prediction first,
   changing one variable at a time. Use targeted debugger inspection or uniquely tagged temporary
   instrumentation; capture only the signal and redact secrets before retention or display.
4. At a seam that reaches the real bug pattern, use [tdd](../tdd/SKILL.md) to preserve the failing
   behavior and apply the smallest coherent repair once implementation is authorized. If the
   architecture prevents a useful regression, document that limitation and retain the strongest
   safe executable characterization. Never weaken an existing verifier to accept the defect.
5. Rerun the original, unminimized scenario and relevant regressions. For performance, compare
   like-for-like measurements; for flakes report counts, not an unsupported guarantee. Remove
   temporary instrumentation and owned throwaway files, preserving unrelated work. Retain any
   needed fixture deliberately rather than deleting useful proof.

When a human-only surface is unavoidable, adapt [the observation loop](scripts/hitl-loop.template.sh)
with nonsecret observations only. Have the human run it in their own terminal; never collect login
values or execute production instrumentation without the required authority.
Return red evidence, discriminating experiments, the supported cause, changed behavior, original
scenario verification, cleanup status, and unresolved limits.
