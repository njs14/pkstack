---
type: Guide
title: Skill composition and upstream provenance
description: Choose native methods by their jobs while preserving ownership, source identities, and exclusions.
tags: [pkstack, skills, provenance, composition]
---

# Skill composition and upstream provenance

## Choose by the requested job

PKStack adapts selected Poteto workflows and complementary methods into native Kiro skills.
It does not install every upstream plugin or treat discovery as execution evidence. `pkstack` is
the workflow entrypoint; setup installs and validates assets rather than launching a tour of skills.
Imported skill names remain recognizable. Native skills, references, steering, and agent prompts
stay in their package locations; only project-specific understanding belongs in the Wiki.

| Need | Method and boundary |
| --- | --- |
| Plan implementation or settle consequential choices | Shared `grilling`, through native Plan/Specs for implementation planning; `grill-me` for focused interviewing. |
| Define domain language and accepted decisions | `domain-modeling`; `grill-with-docs` composes it with interviewing when capture is authorized. |
| Explain a system visually | HumanLayer `show-me`, or Archify when a validated explorable artifact is needed. An explanation request does not request a work log. |
| Preserve an explicitly requested evidence trail | `show-me-your-work`; retain decisions and evidence, not private reasoning or raw transcripts. |
| Improve human prose or agent instructions | `unslop`/technical writing for human prose; `writing-for-agents` for instruction structure and skill mechanics. |
| Design or build reusable iterative automation | HumanLayer design/build loop methods. A design-only request remains conversational; it does not authorize schedules or implementation. |
| Repair a bounded task | The existing verification loop; do not invent a reusable automation product unless requested. |
| Work on Python | Astral `uv`, `ruff`, and `ty` compose by environment, lint/format, and type responsibilities. |

Overlapping vocabulary is acceptable when responsibilities are explicit. Contradictory outputs,
duplicated mandatory interviews, widened permissions, or weaker proof need correction. Routing
fixtures check declared contracts and forbidden effects; they do not measure every model's natural
language routing success. The [native composition](native-kiro-composition.md) owns approval and
handoff semantics. Repeated approval reconciles captured knowledge rather than creating copies.

## Keep source identities separate from shipped bytes

The inventories record original Git paths, modes, sizes, object identities, and dispositions.
Bundle manifests bind locally adapted files. Updating a wrapper does not justify replacing the
original upstream hash with the adapted hash. Upstream notices remain intact in their native
locations. Source parity is accounting, not a claim that excluded upstream packages are runnable.

Poteto's catalog distinguishes direct ports, native replacements, consolidated aliases, and safety
exclusions. `make-bot-ui` remains non-runnable because its assumptions include provider-specific
endpoints, secrets, and privileged networking installation. A real bot request requires an explicit
architecture and authorization. Feature-map authoring accepts one to five useful records; the
preference for three to five is not a reason to invent features or duplicate mandatory proof runs.

HumanLayer contributes four portable methods. Claude-specific plugin registration and
`improve-claude-md` are not activated. Pocock ports preserve interview/domain/writing methods;
OpenAI-only agent metadata is provenance only. Astral ports preserve existing Poetry/PDM or other
selected toolchains unless migration is requested, use locked project tools, and retain reviewed
pre-uv bootstrap exceptions. None of these ports installs a language server as a side effect.

## OKF format, methodology, and runtime are distinct

Google's separately tracked specification supplies format semantics. The OKF skills source
supplies produce/maintain/consume, progressive-disclosure, provenance, and lifecycle methods.
The tracked whole specification tree prevents overlooked upstream movement; it does not make
every implementation or fixture normative. The older vendored specification cannot override the
independent Google source. PKStack's local metadata/link profile is intentionally narrower than
full OKF conformance.

Upstream transcript backfill, Claude hooks/agents, MCP services, validators, and visualizers are
not implicitly activated. Backfill lacks an adopted runnable dependency closure and requires a
separately authorized bounded import design. The OpenKnowledge CLI schema source is retained as
historical provenance after retirement of the `okn` adapter; it is not a runtime fallback.

Archify is different from a prose-only method: its reviewed offline runtime includes documented
local patches. Preserve both the original and adapted byte identities and re-evaluate patches
when upstream changes. The [visual artifact topic](visual-artifacts.md) records the practical
layout and browser-process lessons.


## Source-specific retained knowledge

These summaries describe what is retained from each source. Historical observations keep their
original candidate and scope; they are not fresh verification of this checkout.

| Source | Retained guidance or bounded observation |
| --- | --- |
| [powers/pkstack/docs/provenance.md](../../../powers/pkstack/docs/provenance.md) | Selected upstream methods are adapted into native Kiro semantics; attribution, source inventories and package boundaries stay separate from runtime acceptance. |
| [powers/pkstack/docs/curated-skills.md](../../../powers/pkstack/docs/curated-skills.md) | Choose skills by their job: explanation versus evidence logging, human prose versus agent instructions, task repair versus reusable automation, with explicit composition. |
| [powers/pkstack/docs/upstream-skill-parity.md](../../../powers/pkstack/docs/upstream-skill-parity.md) | Poteto catalog distinguishes direct ports, native replacements and consolidated aliases; make-bot-ui stays excluded and feature batches need not invent a minimum of three records. |
| [powers/pkstack/docs/humanlayer-skills-provenance.md](../../../powers/pkstack/docs/humanlayer-skills-provenance.md) | Four portable HumanLayer methods retain bounded outputs and native planning; Claude-specific registration and improve-claude-md stay provenance-only. |
| [powers/pkstack/docs/mattpocock-writing-for-agents-provenance.md](../../../powers/pkstack/docs/mattpocock-writing-for-agents-provenance.md) | Agent writing method and skill mechanics are retained; OpenAI-only UI metadata is not shipped as Kiro configuration. |
| [powers/pkstack/docs/mattpocock-grilling-provenance.md](../../../powers/pkstack/docs/mattpocock-grilling-provenance.md) | One shared fact-first interview method carries settled constraints into native planning, stops within scope, and defers capture until approval and permitted execution. |
| [powers/pkstack/docs/mattpocock-grill-me-provenance.md](../../../powers/pkstack/docs/mattpocock-grill-me-provenance.md) | The focused interview entrypoint reuses grilling rather than duplicating its method; standalone conversation does not automatically authorize file capture. |
| [powers/pkstack/docs/mattpocock-domain-modeling-provenance.md](../../../powers/pkstack/docs/mattpocock-domain-modeling-provenance.md) | Domain modeling preserves precise vocabulary, scenarios and selective ADRs; project knowledge is captured idempotently without moving native assets. |
| [powers/pkstack/docs/mattpocock-grill-with-docs-provenance.md](../../../powers/pkstack/docs/mattpocock-grill-with-docs-provenance.md) | Grilling owns questions and domain-modeling owns capture within active permissions; native Plan keeps pending understanding conversational. |
| [powers/pkstack/docs/astral-python-provenance.md](../../../powers/pkstack/docs/astral-python-provenance.md) | Astral uv/Ruff/ty wrappers compose locked environments, lint/format and type checks, respecting existing toolchains and reviewed pre-uv bootstrap exceptions. |
| [powers/pkstack/docs/okf-skills-parity.md](../../../powers/pkstack/docs/okf-skills-parity.md) | OKF methodology is adapted locally; upstream backfill, validator and visualizer are excluded and Google remains the independent format authority. |
| [powers/pkstack/docs/okf-skills-provenance.md](../../../powers/pkstack/docs/okf-skills-provenance.md) | Whole-subtree inventories preserve original source identities; later backfill-only changes remain excluded and do not authorize a runnable transcript import. |
| [powers/pkstack/docs/okf-spec-provenance.md](../../../powers/pkstack/docs/okf-spec-provenance.md) | The whole Google OKF subtree is tracked for drift, with SPEC.md normative; provenance and samples do not expand local validator conformance claims. |
| [powers/pkstack/docs/okf-spec-source-parity.md](../../../powers/pkstack/docs/okf-spec-source-parity.md) | The 129-blob source accounting adopts the normative specification while excluding upstream implementations and retaining notices as provenance. |
| [powers/pkstack/docs/openknowledge-cli-contract-provenance.md](../../../powers/pkstack/docs/openknowledge-cli-contract-provenance.md) | The OpenKnowledge CLI schema inventory is a retired runtime reference; preserved accepted identities do not make okn an active dependency or fallback. |
| [reviews/friends-validation.md](../../../reviews/friends-validation.md) | The friends integration made neighboring skill outputs and forbidden effects explicit; static routing cases and a bounded review bundle are not universal semantic routing proof. |
| [reviews/friends-curated-validation.md](../../../reviews/friends-curated-validation.md) | Six skills loaded in native smokes, but design/diagram/builder limitations remained; a successful skill load alone does not establish the requested result. |
| [reviews/release-030-loop-helpers.md](../../../reviews/release-030-loop-helpers.md) | Builder preservation checks required an explicit pre-edit baseline and end-to-end composition; later bounded native runs supersede only the reproduced earlier failures. |
| [reviews/release-030-other-helpers.md](../../../reviews/release-030-other-helpers.md) | show-me, writing-for-agents and narrow-react-prop-types passed bounded native fixtures; inferred diagram links and untested browser rendering stayed disclosed. |
