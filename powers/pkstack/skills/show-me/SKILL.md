---
name: show-me
description: Explain a topic visually with concise diagrams, code-shape sketches, or focused offline-capable HTML. Use for visual understanding rather than a decision-and-evidence log.
---

# Show me

Treat the request text that activated this skill as the task input; do not
depend on CLI-only argument substitution.

Help the user understand the current topic visually. Skip the preamble and
keep prose brief. Pick the smallest view that makes the key point clear.

- Show logic or an algorithm as pseudocode.
- Show runtime control flow as a call tree.
- Show UI structure as a component tree, including only state and module
  boundaries that matter.
- Show file responsibility or a broad refactor as a shallow file tree.
- Show component interaction, control flow, or data flow with Mermaid.
- Use a focused `diff` when the surrounding shape already exists and the point
  is what changes.

Use one or several of these forms only when they clarify the user's question.
Keep calls, files, props, states, and boundaries to the minimum useful set.
Do not expose hidden chain-of-thought or raw private transcripts.

If the topic needs a polished interactive architecture, workflow, sequence,
data-flow, or lifecycle diagram, use [`archify`](../archify/SKILL.md). Use
[`show-me-your-work`](../show-me-your-work/SKILL.md) when the requested output
is an auditable decision-and-evidence trail. An ambiguous "show me what you did"
asks for a concise summary of existing evidence; it does not create a new log.

For mechanics or rationale, use the findings from [`how`](../how/SKILL.md) or
[`why`](../why/SKILL.md); [`teach`](../teach/SKILL.md) may compose those findings
into a lesson. This skill supplies the presentation. Reuse their inspected
sources and preserve their uncertainty instead of repeating the investigation.

For a visual UI, layout, state comparison, or concept too dense for Mermaid,
write one focused HTML artifact using the local tools and open it for the user.
Use real labels and data, support desktop and mobile, and report whether the
artifact was actually opened or checked. Do not claim perceptual visual review
without performing it.
