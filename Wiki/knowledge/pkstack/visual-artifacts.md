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
The repository artifact guide identifies the component, native-workflow and updater diagrams and
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

The September 9 upstream update embeds licensed JetBrains Mono subsets in the viewer and
its SVG/raster export source, removing the font stylesheet network dependency. Uncovered
characters still use system fallback fonts; this does not promise identical rasterization.
Repository evidence now supports Gitee links and a `local-only` mode for other forges. Both
modes verify the pinned local Git revision, origin identity, blobs, and line ranges. Local-only
omits hyperlinks; neither mode proves remote availability or reader access. Origin mismatch
diagnostics redact credentials. The three local viewport, caption, and browser-transport patches
remain separately bound to upstream bytes in the provenance record.

Use **PKStack** as product name, `pkstack` as technical handle, and **PKStack & friends** for the
human-facing theme. Preserve native command names and imported upstream identities. Naming work
must repair links without rewriting historical source ledgers.

The September 6 branding record says the owner selected Option 2, “Knowledge crest”: four
distinct ghost figures, a book and linked knowledge tree. The TypeScript figure is an archetype,
not a portrait, and HumanLayer's layered shape is a visual interpretation. The repository README now
references `docs/assets/logo.png`. The Power README ships no artwork. A compact
512 by 512 JPG uses the scholarly ghost, book and knowledge branches. IDE 1.0.437
reads its details-view `iconUrl` from `POWER.md`, while its content security policy
blocks arbitrary image hosts. The compatibility file therefore embeds the 49 KB
JPG as a permitted data URI. The Agent Plugins manifest stays authoritative and
does not gain an unsupported icon field. Root `docs/assets/` retains both source
images and their creation history, while root
`docs/artifacts/` holds the unchanged diagram sources and previews. A design selection is not evidence of package behavior or endorsement
by the depicted projects.

The September 10 refresh retains the Knowledge crest composition while replacing
the Pocock and HumanLayer companions with abstract teaching and layered-collaboration
motifs. The built-in image generator produced the new crest and compact scholarly
ghost icon; no specific backend model version is asserted. The refreshed 512 by
512 JPEG is 47,978 bytes and must exactly match the decoded `POWER.md` data URI.
The prompt and asset hashes are retained in the creation history below.


## Keep input facts fixed while repairing presentation

The [renderer review](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-archify.md) reproduced an artifact that passed
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
| [docs/assets/creation-history.md](../../../docs/assets/creation-history.md) | Identifies the current four-ghost Knowledge crest and retains the earlier mascot/banner provenance as history. |
| [docs/artifacts/README.md](../../../docs/artifacts/README.md) | Editable JSON, interactive HTML and static previews explain component/planning/updater boundaries at a recorded source snapshot; diagrams are not executable proof. |
| [powers/pkstack/provenance/tt-a1i-archify-provenance.md](../../../powers/pkstack/provenance/tt-a1i-archify-provenance.md) | Original upstream bytes and adapted runtime bytes remain separately bound, including local caption/viewport/transport patches and reviewed upstream parser/watcher corrections. |
| [reviews/branding-ghost-options/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/branding-ghost-options/README.md) | The owner selected Option 2 Knowledge crest on September 6; four separate ghosts and a linked book/tree explain the theme without implying portraits or endorsement. |
| [reviews/release-030-archify.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-archify.md) | Unchanged-input reproductions exposed caption collisions and mobile toolbar overflow; render and validation geometry must agree and visual checks remain separate from provenance. |

The [repository artwork guide](../../../docs/assets/README.md) distinguishes the
README crest from the compact JPG, documents the inline display compatibility
path, and requires decoded image bytes to match the source asset.
