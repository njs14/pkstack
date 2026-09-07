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
| Design or refine a frontend | Impeccable supplies design methods; agent control-loop design remains a separate job. |
| Supervise a PR | `babysit-pr` owns both standalone supervision and the router's Babysit method. |
| Create a skill | `writing-for-agents` owns general Kiro skill authoring; `create-verification-skill` owns verification workflows. |

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

Impeccable is a condensed instruction port: the brief and accessibility requirements outrank
aesthetic defaults, refinement preserves the incumbent design, and audit/critique remain
report-only unless repair is requested. Its binary, detector hooks, font index, upstream agents,
and live variant runtime are excluded. Product/design files are not created as a prerequisite
to narrow UI work. Browser inspection and projectctl supply separate kinds of evidence.

The OpenAI PR Babysitter port shares one supervision method with Poteto's Babysit route.
PKStack retains merge-ready completion and one supported fresh-build retry per head SHA;
explicit continued monitoring can wait until closure or a deadline. Retry state survives
observer restarts. Checks and published reviews must belong to the observed head; incomplete
coverage is not review-clean. No watcher script, detached scheduler, automatic merge, or
automatic review reply is installed. Writes require the user's corresponding authorization.
Codex's built-in skill creator is available in that host, not shipped as a Kiro dependency.

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


## Reusable loops need a durable transition contract

The early curated loop could trim one label correctly yet accept three independent controller
invocations under a two-attempt budget. Its preservation check also decided which value was
allowed to change from the *post-edit* eligible list, rejecting a legitimate trim. These are
separate failures: a correct single output does not establish either persistent budget enforcement
or preservation. The [original campaign](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/friends-curated-validation.md) and
[loop remediation](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-loop-helpers.md) supply the counterexamples.

For a reusable loop, retain the selected item and full pre-actuation baseline, reserve an attempt
before acting, and persist that reservation between commands. Verify the allowed delta against
that baseline, including unchanged keys and unrelated values. A verified increment must clear its
pending state so the next increment can proceed; global completion is a separate decision. If
restart support is promised, reconcile applied and unapplied reservations without refunding spent
attempts. Missing state on resume and malformed existing state must fail without creating a fresh
budget. A valid no-op consumes no attempt; invalid input is not a no-op.

The final 0.3 native run wrote five isolated tests before implementation and repaired code against
the unchanged suite. Those tests still called one exported function in one process, and a test
name claimed malformed-state coverage its body did not exercise. The independent 24-case harness
therefore launched a fresh process for each command. It checked exhausted budgets, pending work,
stale baselines, corrupt state, missing-state resume, preservation, and valid no-op behavior.
All 24 passed for the retained implementation; competing simultaneous controllers were untested.
Use this separation when assessing a generated test suite: inspect assertions and invocation
boundaries, then add independent counterexamples for the promised properties.

[Builder/goal composition](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-composition.md) bound that fixed suite to a
stored goal after deliberately reducing the implementation's attempt limit. The goal retained a
real failure and implementation-only repair, passing at attempt 2/4. A single demonstration such
as “this one trim succeeded” would have weakened the reusable-loop acceptance contract. The first
command spelling was rejected by the runner; an equivalent direct-script spelling was proved to
run the same tests and approved *before* binding. That was a command adjustment, not permission to
change a stored predicate until it passes.

## Skill use has output and method obligations

The [helper campaign](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-other-helpers.md) separates three distinct checks.
A visual explanation preserved an unwired queue-to-worker edge as an inference and changed no
files; producing Mermaid text did not test its rendering. The writing helper produced the right
edit but initially omitted its required prose-cleanup and reference checks. One follow-up completed
those steps, so the result is assisted method compliance. React prop narrowing used the wired
caller as authority, adapted its support story, and passed the existing strict compiler harness;
it did not establish browser behavior. Preserve these distinctions when deciding whether another
helper is needed or whether the requested job is finished.

The [Astral exercise](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/astral-python-auto/README.md) similarly separates diagnosis
from authorized repair. The non-interactive attempt could read skills but could not approve edits;
the same session completed the repair after one interactive write approval. Its claimed persisted
receipt was not supported by the actual command, which returned verifier output retained by the
observer. Prefer the command/result and source diff over a model's completion narrative. Auto was
the observed selector; neither an underlying model identity nor zero-intervention operation was
established.

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
| [powers/pkstack/docs/google-open-knowledge-format-provenance.md](../../../powers/pkstack/docs/google-open-knowledge-format-provenance.md) | Active canonical source starts at ad30107 with 132 regular blobs and the same normative SPEC.md blob as the frozen copy; fresh genesis preserves the retired source history without asserting a cross-repository transition. |
| [powers/pkstack/docs/okf-spec-provenance.md](../../../powers/pkstack/docs/okf-spec-provenance.md) | Historical provenance for the frozen knowledge-catalog/okf source; its accepted identities remain unchanged after retirement. |
| [powers/pkstack/docs/okf-spec-source-parity.md](../../../powers/pkstack/docs/okf-spec-source-parity.md) | Historical 129-blob accounting for the retired source; preserved specification, exclusions, and notices do not establish active tracking. |
| [powers/pkstack/docs/openknowledge-cli-contract-provenance.md](../../../powers/pkstack/docs/openknowledge-cli-contract-provenance.md) | The OpenKnowledge CLI schema inventory is a retired runtime reference; preserved accepted identities do not make okn an active dependency or fallback. |
| [reviews/friends-validation.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/friends-validation.md) | The friends integration made neighboring skill outputs and forbidden effects explicit; static routing cases and a bounded review bundle are not universal semantic routing proof. |
| [reviews/friends-curated-validation.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/friends-curated-validation.md) | Six skills loaded in native smokes, but design/diagram/builder limitations remained; a successful skill load alone does not establish the requested result. |
| [reviews/release-030-loop-helpers.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-loop-helpers.md) | Builder preservation checks required an explicit pre-edit baseline and end-to-end composition; later bounded native runs supersede only the reproduced earlier failures. |
| [reviews/release-030-other-helpers.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-other-helpers.md) | show-me, writing-for-agents and narrow-react-prop-types passed bounded native fixtures; inferred diagram links and untested browser rendering stayed disclosed. |

| [Impeccable provenance](../../../powers/pkstack/docs/pbakaus-impeccable-provenance.md) | Exact source and bundle identities; frontend design methods without the executable runtime. |
| [PR Babysitter provenance](../../../powers/pkstack/docs/openai-babysit-pr-provenance.md) | One shared PR method, explicit stop and retry reconciliation, and no automatic GitHub writes. |
