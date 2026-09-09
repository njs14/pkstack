# Sources and friends

PKStack began with Poteto’s pstack workflows. The friends add specific jobs:
HumanLayer’s visual explanations and control-loop methods, Matt Pocock’s
agent-facing writing and decision interviews, Archify’s diagram renderer, and Astral’s Python tooling. This is a selection of
reviewed skills, not a promise to install every upstream plugin.
Impeccable adds frontend design methods; OpenAI's PR Babysitter strengthens the shared PR
supervision workflow. Both are Kiro-native instruction ports with explicit runtime exclusions.

## What came from where

| Source | What PKStack uses | Why and how it was adapted |
| --- | --- | --- |
| [Poteto’s pstack in Cursor plugins](https://github.com/cursor/plugins/tree/main/pstack) | Engineering workflows, verification, reviews, and principles | Preserve the working method; use Kiro’s native planning and subagents in place of Cursor-specific orchestration. [Full mapping](../provenance/upstream-skill-parity.md). |
| [HumanLayer skills](https://github.com/humanlayer/skills) | `show-me`, `design-control-loop`, `build-iterated-agentic-loop`, `narrow-react-prop-types` | Visual explanations, bounded automation, and live-call-site type narrowing. Replace provider-specific execution and broad permissions with the Kiro boundary. |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | `writing-for-agents`, `grilling`, `grill-me`, `domain-modeling`, `grill-with-docs` | Clear agent instructions, focused decision interviews, and reusable project definitions and decisions. Native skills remain outside Wiki; only their project knowledge output belongs there. |
| [Astral](https://github.com/astral-sh/claude-code-plugins) | `uv`, `ruff`, `ty` | Project-aware Python environments, scripting, lint/format, and typing; [reviewed Kiro adaptations](../provenance/astral-python-provenance.md). |
| [Impeccable](https://github.com/pbakaus/impeccable) | `impeccable` | Frontend design, critique, audit, and refinement methods; excludes binary downloads, detector hooks, font data, and live runtime. [Adaptation](../provenance/pbakaus-impeccable-provenance.md). |
| [OpenAI Codex](https://github.com/openai/codex) | `babysit-pr` | Shared PR supervision through existing GitHub tooling; preserves PKStack's completion, retry, and authorization rules. [Adaptation](../provenance/openai-babysit-pr-provenance.md). |
| [Archify](https://github.com/tt-a1i/archify) | `archify` and its reviewed renderer | Produce validated diagrams without installing a renderer on each run. Keep the Kiro wrapper and documented PKStack runtime patches distinct from the pinned upstream source. |
| [OKF skills](https://github.com/scaccogatto/okf-skills) | Durable knowledge-working methods in `/okf` | Produce, maintain, and consume the project Wiki. Exclude transcript backfill, upstream executables, hooks, and MCP activation. |
| [Google’s OKF specification](https://github.com/GoogleCloudPlatform/open-knowledge-format) | Knowledge format semantics | Keep the format source independent from knowledge-working methods. Local validation checks minimal metadata and Markdown links; Kiro ACP supplies bounded retrieval. |

HumanLayer’s `improve-claude-md` and plugin registration are provenance-only.
`writing-for-agents` covers the cross-runtime instruction-writing job instead.
Poteto’s `make-bot-ui` is excluded because its privileged setup and service
assumptions need a separately reviewed design. The inventories retain these
decisions; absence is not an unnoticed missing port.

The former [OpenKnowledge CLI contract](../provenance/openknowledge-cli-contract-provenance.md)
is retired from active maintenance and runtime use. Its pinned provenance and
paired manifest/ledger history remain archived. Google OKF and OKF skills
remain independent active sources; PKStack ships no optional `okn` backend.

## Choose by the job

Use `/pkstack` for the overall task. A helper should contribute a distinct output:

| Job | Skill and handoff |
| --- | --- |
| Explain visually | `show-me`; use `archify` when a polished diagram is needed |
| Record or audit decisions and proof | `show-me-your-work`; keep its log separate from visual explanations |
| Write for a person | `technical-writing`, followed by `unslop` |
| Write instructions for an agent | `writing-for-agents`; preserve executable and permission contracts |
| Create or update a Kiro skill | `writing-for-agents`; use `create-verification-skill` for a project verification workflow |
| Design, audit, or refine an interface | `impeccable`; `shape`, `critique`, and `audit` preserve their non-editing scope |
| Check or supervise a pull request | `babysit-pr`; one-shot check or owned supervision, with merge-ready as the default stop |
| Plan or sharpen a decision | PKStack planning shares `grilling`; `grill-me` starts a focused standalone interview |
| Build understanding while interviewing | `grill-with-docs` composes `grilling`, `domain-modeling`, and `okf`; update existing topics when writes are permitted |
| Clarify domain language | `domain-modeling`; test meanings against scenarios and code, then retain definitions and consequential decisions |
| Understand an existing system | `how` for mechanics, `why` for rationale; `teach` composes those findings |
| Design an automation | `design-control-loop`, then `build-iterated-agentic-loop` when implementation is requested |
| Finish the current task | `pkstack-verified-goal`; it does not build a scheduler |
| Manage Python environments and scripts | `uv`; preserve project locks and standalone dependency boundaries |
| Lint, format, and type-check Python | `ruff` and `ty`; keep behavioral verification in the existing task |
| Tighten React props | `narrow-react-prop-types`, grounded in live call sites |

Approved implementation plans capture reusable definitions and decisions at the first permitted
write step, using the existing knowledge lifecycle. Native Plan keeps capture pending in the
conversation; explicit no-write scope takes precedence. See [planning and capture](usage.md#plan-and-bind-work).

Explicit skill invocations remain available. An ambiguous “show me what you
did” request should summarize existing evidence, not start an audit log.
Intentional composition is useful; duplicate mandatory investigations,
competing acceptance checks, and unrequested writes are conflicts.

Setup installs and checks the reviewed bundle. It reports optional capabilities
and suggests next steps; it does not run all these workflows as onboarding.

For example, ask `impeccable polish the settings form` to refine that target, or
`impeccable audit the checkout flow without edits` for an evidence-based report. These method
names are skill arguments, not installed shell commands. The upstream Impeccable detector and
live variant UI are absent. For PR work, `babysit-pr check PR 123` is read-only and one-shot;
`watch PR 123 until it closes, without writes` explicitly continues beyond merge-ready.
Repair, push, rerun, and review-thread actions retain their own authorization requirements.

General skill creation is already covered by `writing-for-agents` and its skill-mechanics
reference. Codex also supplies a built-in `skill-creator` in the host environment, but that
host tool is not part of this Kiro Power. No additional creator dependency is needed.

The historical [live Luna/Low smokes](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/friends-curated-validation.md) record
what each helper actually did. They include an Archify clipping failure and
control-loop design/builder limitations; installation is not proof that generated
output is correct. The [Archify release repair](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-archify.md)
records the reproduced clipping defect, runtime corrections, and fresh browser
and export checks. Keep each skill's verification and review checkpoints.

## Reviewed bundles

PKStack keeps curated skills in a registry separate from the pstack parity
catalog. Each entry binds its Kiro wrapper, source inventory, provenance, and
exact bundle manifest. The pins below describe the accepted sources, not a
claim that every upstream is at its latest release.

These imported skills retain their upstream names. PKStack's six entry points
use `/pkstack` or `/pkstack-<workflow>`; `/okf` is the separate knowledge-integration
exception. The [pstack mapping](../provenance/upstream-skill-parity.md) covers Poteto's ports.

| Skill | Source | Runtime boundary |
| --- | --- | --- |
| [`impeccable`](../skills/impeccable/SKILL.md) | [`pbakaus/impeccable`](https://github.com/pbakaus/impeccable/commit/dbdc470e70dbbda69f9b78ee38bc38ea1d3560b9) | [Exact bundle](../metadata/pbakaus-impeccable-bundle-manifest.json); condensed design methods with no upstream runtime |
| [`babysit-pr`](../skills/babysit-pr/SKILL.md) | [`openai/codex`](https://github.com/openai/codex/commit/9f70e348e0227980de97e361cce830236fb18317) | [Exact bundle](../metadata/openai-babysit-pr-bundle-manifest.json); current-session supervision with existing GitHub CLI |
| [`archify`](../skills/archify/SKILL.md) | [`tt-a1i/archify`](https://github.com/tt-a1i/archify/commit/2ead014aa8ec91f104cd052f1a6ca82de5e26c31) | [`tt-a1i-archify-bundle-manifest.json`](../metadata/tt-a1i-archify-bundle-manifest.json); digest-pinned runtime with [documented local runtime patches](../provenance/tt-a1i-archify-provenance.md) under `skills/archify/upstream/` |
| [`build-iterated-agentic-loop`](../skills/build-iterated-agentic-loop/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | Kiro-safe loop builder with bounded references |
| [`design-control-loop`](../skills/design-control-loop/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | Kiro-native control-system design method |
| [`domain-modeling`](../skills/domain-modeling/SKILL.md) | [`mattpocock/skills`](https://github.com/mattpocock/skills/commit/3cca18b368ae95cdbdebbff572ccafa662551015) | Domain language, concrete scenarios, and topic-based OKF glossary and decision references; [provenance](../provenance/mattpocock-domain-modeling-provenance.md) |
| [`grill-me`](../skills/grill-me/SKILL.md) | [`mattpocock/skills`](https://github.com/mattpocock/skills/commit/3cca18b368ae95cdbdebbff572ccafa662551015) | Focused interview entrypoint using the bundled grilling method; [provenance](../provenance/mattpocock-grill-me-provenance.md) |
| [`grill-with-docs`](../skills/grill-with-docs/SKILL.md) | [`mattpocock/skills`](https://github.com/mattpocock/skills/commit/3cca18b368ae95cdbdebbff572ccafa662551015) | Interview and capture reusable project understanding while native Kiro specs retain plan ownership; [provenance](../provenance/mattpocock-grill-with-docs-provenance.md) |
| [`grilling`](../skills/grilling/SKILL.md) | [`mattpocock/skills`](https://github.com/mattpocock/skills/commit/3cca18b368ae95cdbdebbff572ccafa662551015) | Dependency-ordered decision rounds with bounded scope and existing authorization; [provenance](../provenance/mattpocock-grilling-provenance.md) |
| [`narrow-react-prop-types`](../skills/narrow-react-prop-types/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | React prop narrowing from live call sites |
| [`show-me`](../skills/show-me/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | [`humanlayer-show-me-bundle-manifest.json`](../metadata/humanlayer-show-me-bundle-manifest.json); adapted Kiro wrapper |
| [`writing-for-agents`](../skills/writing-for-agents/SKILL.md) | [`mattpocock/skills`](https://github.com/mattpocock/skills/commit/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76) | Agent-facing writing method adapted to Kiro Skills, steering, and `AGENTS.md` |

The knowledge-interview additions are the first Pocock knowledge delivery. Debugging,
architecture survey, handoff, conflict resolution, questionnaire creation, and the remaining
recommended workflow merges follow acceptance of the knowledge lifecycle; they are not
represented as installed by this registry.

The Archify bundle is offline-capable on Node.js 18 or newer. The Node capability is optional to the broader Power and is reported as a doctor warning when unavailable. Network access is denied by default; brand capture requires explicit user authorization and an official URL.

## Astral Python tools

The `uv`, `ruff`, and `ty` skills are ported from [Astral](https://github.com/astral-sh/claude-code-plugins/tree/f3ce88a7ba830f53afd6d944c1d0278ed318e142).
Their [provenance and adaptations](../provenance/astral-python-provenance.md) retain upstream identities and
separate Kiro skill behavior from Claude plugin installation and language-server configuration.
