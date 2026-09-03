# Google OKF source parity

This is the human-readable view of the
[source-scoped machine inventory](okf-spec-source-parity.json) for
`GoogleCloudPlatform/knowledge-catalog` at commit
`fbbc7975388288244dfc62aea0066600b25b7c47` and `okf/` tree
`a8cc7ed0f4ec6bb6019da9b8ace51e3e6dafd06f`. The JSON accounts for all 129
regular blobs by Git object identity, mode, size, and A/B/C disposition. No source file is
redistributed by these records.

| Disposition | Files | Meaning |
|---|---:|---|
| A | 1 | `SPEC.md` is the normative format source whose semantic changes require adaptation. |
| B | 126 | Upstream implementation, fixtures, samples, generated output, and development machinery are excluded from the PK-Stack runtime. |
| C | 2 | `README.md` and `LICENSE.md` are provenance only. |

Tracking the whole `okf/` tree prevents a file-only pin from overlooking related source movement,
but it does not make the entire tree normative. PK-Stack does not vendor the specification, execute
upstream implementations, or activate upstream packages. Canonical `okn` remains the runtime used
behind projectctl; this source only establishes the current format contract and drift boundary.
