---
name: show-me
description: Help the user understand the current topic with concise diagrams, code-shape sketches, and focused offline-capable HTML artifacts.
compatibility: Kiro IDE 1.x and Kiro CLI v3 for concise visual explanations; Kiro Crew and Kiro Web consume committed assets; supported by design but untested.
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
data-flow, or lifecycle diagram, route it to the curated `archify` skill. Keep
this lightweight explainer route distinct from `show-me-your-work`, which is
the separate decision-and-evidence trail skill.

For a visual UI, layout, state comparison, or concept too dense for Mermaid,
write one focused HTML artifact using the local tools and open it for the user.
Use real labels and data, support desktop and mobile, and report whether the
artifact was actually opened or checked. Do not claim perceptual visual review
without performing it.
