# Sources and friends

PKStack began with Poteto’s pstack workflows. The friends add specific jobs:
HumanLayer’s visual explanations and control-loop methods, Matt Pocock’s
agent-facing writing, and Archify’s diagram renderer. This is a selection of
reviewed skills, not a promise to install every upstream plugin.

## What came from where

| Source | What PKStack uses | Why and how it was adapted |
| --- | --- | --- |
| [Poteto’s pstack in Cursor plugins](https://github.com/cursor/plugins/tree/main/pstack) | Engineering workflows, verification, reviews, and principles | Preserve the working method; use Kiro’s native planning and subagents in place of Cursor-specific orchestration. [Full mapping](upstream-skill-parity.md). |
| [HumanLayer skills](https://github.com/humanlayer/skills) | `show-me`, `design-control-loop`, `build-iterated-agentic-loop`, `narrow-react-prop-types` | Visual explanations, bounded automation, and live-call-site type narrowing. Replace provider-specific execution and broad permissions with the Kiro boundary. |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | `writing-for-agents` | Make skill descriptions, steering, `AGENTS.md`, and references easier for an agent to find and follow. It does not replace human-facing technical writing. |
| [Archify](https://github.com/tt-a1i/archify) | `archify` and its reviewed renderer | Produce validated diagrams without installing a renderer on each run. Keep the Kiro wrapper separate from the exact runtime snapshot. |
| [OKF skills](https://github.com/scaccogatto/okf-skills) | Durable knowledge-working methods in `/okf` | Produce, maintain, and consume the project Wiki. Exclude transcript backfill, upstream executables, hooks, and MCP activation. |
| [Google’s OKF specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) and [OpenKnowledge](https://github.com/openknowledge-sh/openknowledge) | Knowledge format and the external `okn` interface | Keep source-controlled knowledge and bounded retrieval without building another knowledge engine. |

HumanLayer’s `improve-claude-md` and plugin registration are provenance-only.
`writing-for-agents` covers the cross-runtime instruction-writing job instead.
Poteto’s `make-bot-ui` is excluded because its privileged setup and service
assumptions need a separately reviewed design. The inventories retain these
decisions; absence is not an unnoticed missing port.

## Choose by the job

Use `/pkstack` for the overall task. A helper should contribute a distinct output:

| Job | Skill and handoff |
| --- | --- |
| Explain visually | `show-me`; use `archify` when a polished diagram is needed |
| Record or audit decisions and proof | `show-me-your-work`; keep its log separate from visual explanations |
| Write for a person | `technical-writing`, followed by `unslop` |
| Write instructions for an agent | `writing-for-agents`; preserve executable and permission contracts |
| Understand an existing system | `how` for mechanics, `why` for rationale; `teach` composes those findings |
| Design an automation | `design-control-loop`, then `build-iterated-agentic-loop` when implementation is requested |
| Finish the current task | `pkstack-verified-goal`; it does not build a scheduler |
| Tighten React props | `narrow-react-prop-types`, grounded in live call sites |

Explicit skill invocations remain available. An ambiguous “show me what you
did” request should summarize existing evidence, not start an audit log.
Intentional composition is useful; duplicate mandatory investigations,
competing acceptance checks, and unrequested writes are conflicts.

Setup installs and checks the reviewed bundle. It reports optional capabilities
and suggests next steps; it does not run all these workflows as onboarding.

The [live Luna/Low smokes](https://github.com/njs14/pkstack/blob/main/reviews/friends-curated-validation.md) record
what each helper actually did. They include an Archify clipping failure and
control-loop design/builder limitations; installation is not proof that generated
output is correct. Keep each skill's verification and review checkpoints.

## Reviewed bundles

PKStack keeps curated skills in a registry separate from the pstack parity
catalog. Each entry binds its Kiro wrapper, source inventory, provenance, and
exact bundle manifest. The pins below describe the accepted sources, not a
claim that every upstream is at its latest release.

These imported skills retain their upstream names. PKStack's six entry points
use `/pkstack` or `/pkstack-<workflow>`; `/okf` is the separate knowledge-integration
exception. The [pstack mapping](upstream-skill-parity.md) covers Poteto's ports.

| Skill | Source | Runtime boundary |
| --- | --- | --- |
| [`archify`](../skills/archify/SKILL.md) | [`tt-a1i/archify`](https://github.com/tt-a1i/archify/commit/06dd052602dd9a369e4d034e24faef0917b5a60c) | [`tt-a1i-archify-bundle-manifest.json`](tt-a1i-archify-bundle-manifest.json); byte-exact runtime under `skills/archify/upstream/` |
| [`build-iterated-agentic-loop`](../skills/build-iterated-agentic-loop/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | Kiro-safe loop builder with bounded references |
| [`design-control-loop`](../skills/design-control-loop/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | Kiro-native control-system design method |
| [`narrow-react-prop-types`](../skills/narrow-react-prop-types/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | React prop narrowing from live call sites |
| [`show-me`](../skills/show-me/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | [`humanlayer-show-me-bundle-manifest.json`](humanlayer-show-me-bundle-manifest.json); adapted Kiro wrapper |
| [`writing-for-agents`](../skills/writing-for-agents/SKILL.md) | [`mattpocock/skills`](https://github.com/mattpocock/skills/commit/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76) | Agent-facing writing method adapted to Kiro Skills, steering, and `AGENTS.md` |

The Archify bundle is offline-capable on Node.js 18 or newer. The Node capability is optional to the broader Power and is reported as a doctor warning when unavailable. Network access is denied by default; brand capture requires explicit user authorization and an official URL.
