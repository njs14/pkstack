---
type: Guide
title: Visual artifacts, branding, and renderer evidence
description: Ownership and validation lessons for diagrams and the selected PKStack identity.
tags: [pkstack, archify, diagrams, branding, evidence]
---

# Visual artifacts, branding, and renderer evidence

## Artifact ownership

Architecture/workflow diagrams explain the system; they are not runtime or release proof.
Retain editable JSON alongside interactive HTML and static previews. Link the explanation to
the source it describes and distinguish source observations from inferred connections. Native
Kiro planning still owns its requirements, designs and tasks; a diagram is not another task graph.
The package artifact guide identifies the component, native-workflow and updater diagrams and
their source snapshot. Do not infer that every export was regenerated whenever surrounding prose
changes; the knowledge-foundation report explicitly retained older diagrams at that checkpoint.

## Lessons from reproduced renderer failures

The 0.3 Archify campaign preserved the original JSON while reproducing hidden sequence captions,
captions entering preceding bands, and controls outside narrow viewports. Placement must consider
opaque participant boxes as well as routes and labels; rendering and validation must use the same
geometry. Bounded attempts must reject unresolved collisions rather than emitting a false green.
Toolbar wrapping and viewport fit require desktop and narrow-screen checks, not only valid SVG.

The reviewed upstream follow-up separately fixed overwide segment captions, unknown CLI options,
excess positional arguments, and watcher failure/polling fallback. Preserve provenance between
upstream corrections and local patches. A local patch is not a new upstream identity.

Browser lifecycle regressions cover failed startup cleanup, process exit, pipe EOF/closure, and
bounded timeout diagnostics. These are distinct from semantic layout, visual inspection,
zoom/pan/reset, and export checks. A test that simulates startup failure does not identify the
cause of the historical Linux startup timeout. The
[quality guide](quality-and-ci.md) retains that unresolved diagnostic boundary.

## Current naming and historical artwork

Use **PKStack** as product name, `pkstack` as technical handle, and **PKStack & friends** for the
human-facing theme. Preserve native command names and imported upstream identities. Naming work
must repair links without rewriting historical source ledgers.

The September 6 branding record says the owner selected Option 2, “Knowledge crest”: four
distinct ghost figures, a book and linked knowledge tree. The TypeScript figure is an archetype,
not a portrait, and HumanLayer's layered shape is a visual interpretation. Both inspected READMEs
reference `assets/logo.png` at their respective relative paths. The older assets README describes
the previous banner as current; preserve it as artwork provenance and use the later selection
record for the decision. A design selection is not evidence of package behavior or endorsement
by the depicted projects.


## Keep input facts fixed while repairing presentation

The [renderer review](../../../reviews/release-030-archify.md) reproduced an artifact that passed
all nine showcase checks but failed viewport containment. Its compact aspect ratio fell outside
the adaptive-layout rule and was inflated to a desktop width that made it too tall. Reusing the
same frozen JSON isolated the renderer defect; shrinking the authored content, clipping it, or
relaxing the threshold would have changed the acceptance question.

Caption correctness needs more than “inside the SVG.” Opaque participant boxes can hide a label,
collision avoidance can move it into the previous semantic band, and a caption can fit the canvas
while exceeding its own frame. Render and validate the same computed rectangle, include preceding
bands and participant boxes as obstacles, and fail if bounded placement cannot preserve meaning.
The upstream follow-up used an exact-fit caption control beside a one-character-overflow case.

At narrow widths, document scroll width missed buttons overflowing to the left. Measure each
visible toolbar control's bounds, in both themes, as well as document overflow. Exercise zoom,
pointer pan and reset, then download exports through the actual menu. The retained campaign checked
that camera changes left the canonical SVG and input bytes unchanged; successful delivery of all
example JSON files remained schema/render evidence rather than visual review of every example.

The same source records two nonvisual counterexamples: an unknown render option was used as an
output filename, and an injected watcher error escaped preview. The upstream fixes rejected bad
arguments before writing and switched a failed watcher to polling, publishing the next edit and
closing the watcher once. Runtime tests and inverse-patch/source identity checks answer different
questions; retain both when reconciling local presentation patches with an upstream update.

## Source-specific retained knowledge

These summaries describe what is retained from each source. Historical observations keep their
original candidate and scope; they are not fresh verification of this checkout.

| Source | Retained guidance or bounded observation |
| --- | --- |
| [powers/pkstack/assets/README.md](../../../powers/pkstack/assets/README.md) | Retains earlier mascot/banner provenance; its current-banner wording predates the later selected four-ghost logo and should not override that selection. |
| [powers/pkstack/docs/artifacts/README.md](../../../powers/pkstack/docs/artifacts/README.md) | Editable JSON, interactive HTML and static previews explain component/planning/updater boundaries at a recorded source snapshot; diagrams are not executable proof. |
| [powers/pkstack/docs/tt-a1i-archify-provenance.md](../../../powers/pkstack/docs/tt-a1i-archify-provenance.md) | Original upstream bytes and adapted runtime bytes remain separately bound, including local caption/viewport/transport patches and reviewed upstream parser/watcher corrections. |
| [reviews/branding-ghost-options/README.md](../../../reviews/branding-ghost-options/README.md) | The owner selected Option 2 Knowledge crest on September 6; four separate ghosts and a linked book/tree explain the theme without implying portraits or endorsement. |
| [reviews/release-030-archify.md](../../../reviews/release-030-archify.md) | Unchanged-input reproductions exposed caption collisions and mobile toolbar overflow; render and validation geometry must agree and visual checks remain separate from provenance. |
