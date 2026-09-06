# `grilling` provenance

PKStack adapts Matt Pocock's `grilling` method for native Kiro skills and project knowledge.

Source: [`mattpocock/skills` at `3cca18b`](https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/grilling).
Retrieved on 2026-09-05. Copyright (c) 2026 Matt Pocock; MIT licensed. The complete
license notice is retained in [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

## Adaptation

Preserves dependency-ordered decision rounds, recommendations, inspection before questions, and concrete shared understanding. Replaces relentless exhaustive interviewing and a universal confirmation gate with scope-based stopping and existing authorization. Exploration may use native subagents when useful rather than requiring delegation.

The shared method now supplies all planning entered through PKStack and standalone interviews. Native Plan remains read-only and conversational; explicit native handoffs carry settled context and ask the built-in workflow to read the local method. Approved implementation plans use the shared, permission-aware and idempotent OKF capture checkpoint without creating a planning runtime.

Implementation mechanics governed by settled constraints are derived from inspected sources: a simple compliant implementation is selected from equivalent approaches and stated with the requirement it satisfies, rather than guessed or raised as a confirmation question. Questions are reserved for materially different allowed outcomes, preferences, or permissions, and a genuinely unknown requirement stays an explicit open question. Interview options must preserve settled constraints unless a requested change or contradictory evidence requires renegotiation.

Native execution handoffs carry approved-knowledge capture before implementation edits and identify the installed workspace OKF, lifecycle, and domain-modeling paths. Native approval exit and agent selection retain their own authority. The mode that runs the plan runs the interview: an inactive requested planning mode receives a handoff listing its open questions, and the user selects that mode. Kiro's own approval and execution handoffs are unaffected.

The upstream `agents/openai.yaml` is recorded but not shipped. No upstream installer,
agent configuration, hooks, or runtime is activated. Local skills remain native assets;
only their project-specific knowledge output belongs in Wiki. The exact shipped bytes
are bound by [`mattpocock-grilling-bundle-manifest.json`](mattpocock-grilling-bundle-manifest.json).

## Source identities

These are the original upstream bytes, not hashes of the adapted local files. The
exhaustive subtree inventory is [`mattpocock-grilling-source-parity.json`](mattpocock-grilling-source-parity.json).

| Source-relative path | Git blob SHA-1 | SHA-256 | Bytes |
| --- | --- | --- | --- |
| `agents/openai.yaml` | `ddbdb96139c0c1dfe6bca698f39d0465674b8a39` | `1411d7df7d99b7e621a1ff8283c8133cc2464be63d064e52d8ce169c6800ee9b` | 113 |
| `SKILL.md` | `8ca78c6d8f901aab0c5a1f896034b70e666ff2a3` | `10ff989e7498b23b5acb49d5048f11dcd906757d2f79c5cdf8a00001381296f2` | 1987 |

The repository root `LICENSE` at the same commit has Git blob
`f1dd2c09108dde1a5f56097cee8461b3ea834499`, SHA-256
`0e7ac423bf2c6e223b7c5b156f8cf72da49d748e56a1641402c31f22ad07dbb5`, and 1068 bytes.

<!-- pk-stack-upstream-genesis: {"commit":"3cca18b368ae95cdbdebbff572ccafa662551015","path":"skills/productivity/grilling","repository":"mattpocock/skills","source_id":"mattpocock-grilling","subtree_sha":"f0732035b8b1b60ae39454e4191caef32fa91903"} -->
