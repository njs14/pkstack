# Canonical Google Open Knowledge Format provenance

The active source is [GoogleCloudPlatform/open-knowledge-format](https://github.com/GoogleCloudPlatform/open-knowledge-format), repository root (`.`), reviewed on September 7, 2026.
The accepted commit is `ad30107c31c06aec8a7d5636e0d1058118604e6f` and its root tree is `d8b7583265ead834e3e7a3146ff7ce9a3533ddfe`.

<!-- pk-stack-upstream-genesis: {"commit":"ad30107c31c06aec8a7d5636e0d1058118604e6f","path":".","repository":"GoogleCloudPlatform/open-knowledge-format","source_id":"google-open-knowledge-format","subtree_sha":"d8b7583265ead834e3e7a3146ff7ce9a3533ddfe"} -->

The [exact source inventory](../metadata/google-open-knowledge-format-source-parity.json) accounts for all 132 regular blobs. `SPEC.md` is the normative semantic reference (A); README, license, code of conduct, and contribution context are provenance (C). Reference-agent code, connectors, examples, generated output, tests, and development files are excluded (B). No upstream code is executed or vendored.

The [pinned specification](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/SPEC.md) describes Markdown concepts with open type values, YAML frontmatter, optional provenance/trust/lifecycle families, Markdown links, index files, and logs. PKStack uses these document conventions while enforcing its own bounded workspace, metadata, and link checks. It does not implement the reference agent, computation execution, or a general OKF consumer; OKF's tolerant-consumer guidance does not relax PKStack's project validation.

The canonical `SPEC.md` blob is `c06e3eede0c910d0ecf12524c34204156f8795ac` (37,748 bytes), identical to the accepted frozen specification. This migration changes tracking identity and scope; it introduces no normative specification delta requiring a runtime change.

The separate [retired source record](https://github.com/njs14/pkstack/blob/main/maintenance/retired-upstreams/google-okf-spec.json) preserves the former manifest entry and paired ledger unchanged. Its [historical provenance](okf-spec-provenance.md) and inventory remain evidence of the frozen `knowledge-catalog/okf` baseline. This source starts a fresh genesis: no cross-repository transition is asserted.

The source is Apache License 2.0. PKStack records identities and links to the specification without redistributing the upstream work.
