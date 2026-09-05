# Curated skills

PKStack keeps reviewed curated skills in a registry separate from the Cursor-specific parity catalog. Each entry binds a Kiro-native wrapper, a source-inventory parity artifact, a source-specific provenance marker, and an exact bundle manifest.

These imported skills retain their upstream names. PKStack's six entry points
use `/pkstack` or `/pkstack-<workflow>`; `/okf` is the separate knowledge-integration
exception. The [pstack mapping](upstream-skill-parity.md) covers Poteto's ports.

| Skill | Source | Runtime boundary |
| --- | --- | --- |
| [`archify`](../skills/archify/SKILL.md) | [`tt-a1i/archify`](https://github.com/tt-a1i/archify/commit/06dd052602dd9a369e4d034e24faef0917b5a60c) | [`tt-a1i-archify-bundle-manifest.json`](tt-a1i-archify-bundle-manifest.json); byte-exact runtime under `skills/archify/upstream/` |
| [`build-iterated-agentic-loop`](../skills/build-iterated-agentic-loop/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | Kiro-safe loop builder with bounded references |
| [`design-control-loop`](../skills/design-control-loop/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | Kiro-native control-system design method |
| [`narrow-react-prop-types`](../skills/narrow-react-prop-types/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | Framework-neutral live-call-site type narrowing |
| [`show-me`](../skills/show-me/SKILL.md) | [`humanlayer/skills`](https://github.com/humanlayer/skills/commit/3c2629142c5d437428269b1b722b08c0b87f574d) | [`humanlayer-show-me-bundle-manifest.json`](humanlayer-show-me-bundle-manifest.json); adapted Kiro wrapper |
| [`writing-for-agents`](../skills/writing-for-agents/SKILL.md) | [`mattpocock/skills`](https://github.com/mattpocock/skills/commit/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76) | Agent-facing writing method adapted to Kiro Skills, steering, and `AGENTS.md` |

The Archify bundle is offline-capable on Node.js 18 or newer. The Node capability is optional to the broader Power and is reported as a doctor warning when unavailable. Network access is denied by default; brand capture requires explicit user authorization and an official URL.
