# Google Open Knowledge Format provenance

PKStack tracks the complete `okf/` tree from
[`GoogleCloudPlatform/knowledge-catalog`](https://github.com/GoogleCloudPlatform/knowledge-catalog)
so changes to the normative specification cannot be hidden by a file-only pin. The accepted
baseline is commit `fbbc7975388288244dfc62aea0066600b25b7c47`, whose `okf/` tree is
`a8cc7ed0f4ec6bb6019da9b8ace51e3e6dafd06f`.

<!-- pk-stack-upstream-genesis: {"commit":"fbbc7975388288244dfc62aea0066600b25b7c47","path":"okf","repository":"GoogleCloudPlatform/knowledge-catalog","source_id":"google-okf-spec","subtree_sha":"a8cc7ed0f4ec6bb6019da9b8ace51e3e6dafd06f"} -->

The [machine-readable source parity](okf-spec-source-parity.json) accounts for every file in the
tree. Only `SPEC.md` is classified as the normative semantic source. `README.md` and `LICENSE.md`
are retained as provenance, while implementations, fixtures, generated results, and examples are
explicitly excluded from PKStack's runtime. Nothing from the tracked tree is executed or vendored.

The source is licensed under Apache License 2.0. PKStack links to it and records Git identities; it
does not copy the specification or implementation, so this provenance record does not add a
redistributed third-party work.
