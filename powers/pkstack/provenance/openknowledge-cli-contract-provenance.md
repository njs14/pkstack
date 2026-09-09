# OpenKnowledge CLI contract provenance

Historical reference: the active CLI adapter and maintenance source were retired by the
[knowledge foundation migration](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/knowledge-foundation.md). The accepted identities
and provenance markers below are preserved; this document is not a current runtime dependency.

PKStack tracks the versioned public CLI schema tree from
[`openknowledge-sh/openknowledge`](https://github.com/openknowledge-sh/openknowledge) so changes to
the machine contract at its optional `okn` process boundary are visible to autonomous maintenance.
The accepted baseline is commit `6e8bbe026448fd890ace9293bcfe89b53363cd1f`, whose
`packages/cli/schemas/v1/` tree is `965396e6c2f67b05dee739f2e1c7f989aea301cf`.

<!-- pk-stack-upstream-genesis: {"commit":"6e8bbe026448fd890ace9293bcfe89b53363cd1f","path":"packages/cli/schemas/v1","repository":"openknowledge-sh/openknowledge","source_id":"openknowledge-cli-contract","subtree_sha":"965396e6c2f67b05dee739f2e1c7f989aea301cf"} -->

The [machine-readable source parity](../metadata/openknowledge-cli-contract-parity.json) accounts for every
regular file in that schema tree. PKStack adapts only the bounded validation, search-context,
common, and CLI-error contracts used at its process boundary. Deployment, job-control, runtime,
release-action, and release-management interfaces are explicitly excluded. The remaining schemas
are provenance-only until PKStack deliberately adopts the corresponding command surface.

Nothing from this source is executed, installed, or vendored. Release-binary compatibility remains
a separate ephemeral smoke-test concern; a moving release artifact is not silently promoted into
this immutable source pin.
