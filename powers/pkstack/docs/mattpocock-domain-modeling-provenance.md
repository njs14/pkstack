# `domain-modeling` provenance

PKStack adapts Matt Pocock's `domain-modeling` method for native Kiro skills and project knowledge.

Source: [`mattpocock/skills` at `3cca18b`](https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/domain-modeling).
Retrieved on 2026-09-05. Copyright (c) 2026 Matt Pocock; MIT licensed. The complete
license notice is retained in [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

## Adaptation

Preserves glossary challenges, precise language, concrete scenarios, code cross-checks, immediate capture of settled terms, and selective ADRs. Moves new project knowledge to Wiki/knowledge/<topic>/ with OKF, reuses existing legacy topic documents pending migration, and distinguishes desired decisions from verified behavior. Native skills, operational instructions, and Kiro specs keep their existing ownership.

The upstream `agents/openai.yaml` is recorded but not shipped. No upstream installer,
agent configuration, hooks, or runtime is activated. Local skills remain native assets;
only their project-specific knowledge output belongs in Wiki. The exact shipped bytes
are bound by [`mattpocock-domain-modeling-bundle-manifest.json`](mattpocock-domain-modeling-bundle-manifest.json).

## Source identities

These are the original upstream bytes, not hashes of the adapted local files. The
exhaustive subtree inventory is [`mattpocock-domain-modeling-source-parity.json`](mattpocock-domain-modeling-source-parity.json).

| Source-relative path | Git blob SHA-1 | SHA-256 | Bytes |
| --- | --- | --- | --- |
| `ADR-FORMAT.md` | `d7e61f30a9fd8ca70d9ee68f019c2a9ebf2d13f7` | `944c92aa790e8fbdc9199640b170979abb8a34ba8d0fe18c2a01a63bce140ca0` | 2733 |
| `agents/openai.yaml` | `7f1522d2f11506ee205275ab7c282aa52366ecf6` | `f6bf2aa996c6e6f53fdd0708e18a0d16a56aed8322cca59fedbe3c0d2c75f06b` | 101 |
| `CONTEXT-FORMAT.md` | `79bbb32f6fda55758b377c980f72a6cb2b8c670e` | `17ab16ce783e4d2801ee52fd9acdf550cbf44de65ae76797a93943bbedf22a13` | 2290 |
| `SKILL.md` | `9b97707e19ef1f590aada356f2b3f6bb881f91be` | `327a2b50620e2fd70abc6893cd6965e76b20f8d0adb0dc2c8d5eb3845efb643e` | 3331 |

The repository root `LICENSE` at the same commit has Git blob
`f1dd2c09108dde1a5f56097cee8461b3ea834499`, SHA-256
`0e7ac423bf2c6e223b7c5b156f8cf72da49d748e56a1641402c31f22ad07dbb5`, and 1068 bytes.

<!-- pk-stack-upstream-genesis: {"commit":"3cca18b368ae95cdbdebbff572ccafa662551015","path":"skills/engineering/domain-modeling","repository":"mattpocock/skills","source_id":"mattpocock-domain-modeling","subtree_sha":"388c9822641805ca2dcd5038e68a1d5282437ee5"} -->
