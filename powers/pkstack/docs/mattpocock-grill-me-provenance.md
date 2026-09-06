# `grill-me` provenance

PKStack adapts Matt Pocock's `grill-me` method for native Kiro skills and project knowledge.

Source: [`mattpocock/skills` at `3cca18b`](https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/grill-me).
Retrieved on 2026-09-05. Copyright (c) 2026 Matt Pocock; MIT licensed. The complete
license notice is retained in [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

## Adaptation

Preserves the interview entrypoint by linking to the bundled grilling method. Replaces the upstream Skill tool call with portable Kiro skill loading; normal Kiro name/description discovery remains available.

The focused entrypoint reuses the shared method. Standalone decision interviews remain conversational; requested implementation plans follow native planning and capture reusable understanding only after approval and permitted writes.

The upstream `agents/openai.yaml` is recorded but not shipped. No upstream installer,
agent configuration, hooks, or runtime is activated. Local skills remain native assets;
only their project-specific knowledge output belongs in Wiki. The exact shipped bytes
are bound by [`mattpocock-grill-me-bundle-manifest.json`](mattpocock-grill-me-bundle-manifest.json).

## Source identities

These are the original upstream bytes, not hashes of the adapted local files. The
exhaustive subtree inventory is [`mattpocock-grill-me-source-parity.json`](mattpocock-grill-me-source-parity.json).

| Source-relative path | Git blob SHA-1 | SHA-256 | Bytes |
| --- | --- | --- | --- |
| `agents/openai.yaml` | `4d6fb0c746c5d21364dce5d0cf8c51eab9712e7b` | `c061e39c3e0f9d865fb1b97556d485704af2a8a58f4b8221a8917a5c2074a32b` | 137 |
| `SKILL.md` | `3947ff9c4ad980d14fc07fccbf659d47c114e81d` | `caaf8b8de1684f96e26b28f3c29189db5c89cce4b73e1c93d86164f66ef88637` | 157 |

The repository root `LICENSE` at the same commit has Git blob
`f1dd2c09108dde1a5f56097cee8461b3ea834499`, SHA-256
`0e7ac423bf2c6e223b7c5b156f8cf72da49d748e56a1641402c31f22ad07dbb5`, and 1068 bytes.

<!-- pk-stack-upstream-genesis: {"commit":"3cca18b368ae95cdbdebbff572ccafa662551015","path":"skills/productivity/grill-me","repository":"mattpocock/skills","source_id":"mattpocock-grill-me","subtree_sha":"3df14e2d3a89459bf300614be9247e3ce74798f8"} -->
