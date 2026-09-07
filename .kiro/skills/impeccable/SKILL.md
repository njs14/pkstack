---
name: impeccable
description: Design, redesign, critique, audit, or refine a frontend interface, including its typography, layout, color, motion, responsive behavior, accessibility, and UX copy.
---

# Design and refine interfaces

Treat the request as the target surface and intended change. This is PKStack's Kiro-native
adaptation of Impeccable's design methods. Use the current session's permitted tools and the
project's existing build and browser workflow. The upstream detector, binary launcher, hooks,
browser extension, font downloader, and live variant runtime are not bundled.

## Establish the target

Inspect the named route or component, real content, neighboring screens, shared tokens, and
existing product/design documents. A missing PRODUCT.md or DESIGN.md does not erase the
incumbent design. Read existing documents as evidence; do not create or replace them merely
because a design task started. Reuse settled requirements and any native Kiro Spec.

Choose the surface's purpose: **Persuade** helps a visitor decide and act; **Operate** helps
someone finish a task; **Read** supports understanding; **Experience** puts the work itself
first. A product can have surfaces with different purposes. Derive visual decisions from the
audience, content, and use environment instead of applying one style across every project.

Refinement preserves identity, behavior, factual copy, and scope. Redesign may replace the
visual system within the requested target while preserving product truth and functionality.
The user's brief and accessibility requirements outrank aesthetic preferences. Do not invent
testimonials, metrics, product capabilities, or configuration to fill a layout.

## Select one method

These are arguments to this skill, not installed executables or standalone slash commands.
With no target or task, give a short context-aware choice of methods; do not start editing.

| Request | Method |
| --- | --- |
| New UI, redesign, `craft`, or `shape` | [Direction and structure](references/direction.md); `shape` returns a brief without implementation |
| `init` or `document` | [Direction and structure](references/direction.md); capture product facts or the observed design system only when requested |
| `critique` or `audit` | [Review](references/review.md); report findings without fixes unless fixes are also requested |
| `polish`, `bolder`, `quieter`, `distill`, `extract` | [Refinement](references/refinement.md) |
| `colorize`, `typeset`, `layout`, `animate`, `delight`, `overdrive` | [Refinement](references/refinement.md) |
| `clarify`, `harden`, `onboard`, `adapt`, `optimize` | [Refinement](references/refinement.md) |

For `live`, explain that the upstream runtime is absent; use available browser inspection
and scoped source edits if those satisfy the requested outcome. Do not install it silently.
Requests for upstream hooks, pin/unpin shortcuts, or runtime doctor are not supported by this
port. Report that boundary instead of issuing nonexistent commands. `teach` remains the
separate PKStack teaching skill; it is not an alias for Impeccable initialization here.

## Build and verify

Before UI edits, read [the quality checks](references/quality.md). Inspect the rendered target
at representative narrow and wide sizes together, fix the observed issues in one batch, then
confirm in one more round. Reuse screenshots and findings already current for this target.
Stop discretionary polishing after that confirmation; unresolved functional or accessibility
defects remain failures and follow the task's existing repair and verification contract.

When the application cannot run, inspect current source and available screenshot fixtures,
check their freshness, and report the missing live evidence. Never describe source inspection
as a successful browser check. Report the changed behavior, visual evidence, checks, and limits.

Kiro owns planning modes, permissions, model selection, and subagents. Read-only planning stays
conversational; this skill creates no parallel plan or mandatory interview. Use
[writing-for-agents](../writing-for-agents/SKILL.md) for skill authoring,
[show-me](../show-me/SKILL.md) for an explanation, and [archify](../archify/SKILL.md) for diagrams.
Use [design-control-loop](../design-control-loop/SKILL.md) only to design reusable agent
automation. Existing projectctl checks retain executable proof ownership; a visual review
does not replace them or authorize publication.
