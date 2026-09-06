# `grill-with-docs` provenance

PKStack adapts Matt Pocock's `grill-with-docs` method for native Kiro skills and project knowledge.

Source: [`mattpocock/skills` at `3cca18b`](https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/grill-with-docs).
Retrieved on 2026-09-05. Copyright (c) 2026 Matt Pocock; MIT licensed. The complete
license notice is retained in [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

## Adaptation

Preserves composition of interviewing and domain modeling as a first-class entrypoint. Replaces the upstream Skill API with local bundled references, adds bounded OKF retrieval and validation, records decisions as they settle, and hands linked context to native Kiro specs without a duplicate task graph.

Interview questions have one owner in grilling. Explicit interview-time capture uses domain-modeling and OKF only within active write permissions; native Plan retains pending knowledge in conversation. Repeated approval reconciles already captured entries without duplication.

The upstream `agents/openai.yaml` is recorded but not shipped. No upstream installer,
agent configuration, hooks, or runtime is activated. Local skills remain native assets;
only their project-specific knowledge output belongs in Wiki. The exact shipped bytes
are bound by [`mattpocock-grill-with-docs-bundle-manifest.json`](mattpocock-grill-with-docs-bundle-manifest.json).

## Source identities

These are the original upstream bytes, not hashes of the adapted local files. The
exhaustive subtree inventory is [`mattpocock-grill-with-docs-source-parity.json`](mattpocock-grill-with-docs-source-parity.json).

| Source-relative path | Git blob SHA-1 | SHA-256 | Bytes |
| --- | --- | --- | --- |
| `agents/openai.yaml` | `5dbe2780a51be3e9b118bd7758a73e54a9384e11` | `94cd0ab161fb468a836349f5ed482ba58ce8e709a05c57ce533d739dbd35cca9` | 145 |
| `SKILL.md` | `62b9efb6f991d1b229adee7506962f13ced0c499` | `7de372c13488f1ee96cc11cd8907b56b6809cc93eef776eeddd37de6b6cbe3fe` | 247 |

The repository root `LICENSE` at the same commit has Git blob
`f1dd2c09108dde1a5f56097cee8461b3ea834499`, SHA-256
`0e7ac423bf2c6e223b7c5b156f8cf72da49d748e56a1641402c31f22ad07dbb5`, and 1068 bytes.

<!-- pk-stack-upstream-genesis: {"commit":"3cca18b368ae95cdbdebbff572ccafa662551015","path":"skills/engineering/grill-with-docs","repository":"mattpocock/skills","source_id":"mattpocock-grill-with-docs","subtree_sha":"eedaf2562c83155115e9c649fa3ecaac2e10e81d"} -->
