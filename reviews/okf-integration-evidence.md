# OKF integration selection evidence

This is a bounded architectural probe from the dirty worktree based at
`491bfdafc94832c6624ed86051955b1067245979`. It selects the integration shape; it is not immutable
release acceptance. The machine-readable companion is `okf-integration-evidence.json`.

## Decision

`scaccogatto/okf-skills` is valuable as a workflow-methodology source. PK-Stack adapts its
produce, maintain, consume, progressive-disclosure, provenance, trust, and lifecycle ideas into one
Kiro-native `/okf` skill. It does not install or execute the upstream Claude plugin, environment-
specific scripts, Stop hook, transcript backfill, validator, visualizer, MCP server, action, or
vendored specification.

The roles remain deliberately separate:

| Layer | Selected owner | Reason |
| --- | --- | --- |
| Format | Google Cloud OKF 0.2 specification | Authoritative portable data contract |
| Kiro workflow | PK-Stack `/okf` | Native produce/maintain/consume semantics and trust boundary |
| Retrieval and validation | `openknowledge-sh/openknowledge` `okn` 0.13.0 | Ranked bounded context with revision and content-addressed provenance |
| Optional second opinion | `okfcli/okf` 0.4.0 | Explicit isolated conformance/SARIF only; never a runtime fallback |

The workflow audit pins `okf-skills` commit
`bf2448f03686a8348324e4741106697d30a867f9` and its `skills/` tree
`8cc9ed3986cf6c942f718439e1ee8249eb17a2ad`. Its 13 blobs received a complete
`A=4/B=4/C=5` disposition. The normative source audit pins Google knowledge-catalog commit
`fbbc7975388288244dfc62aea0066600b25b7c47` and its 129-blob `okf/` tree
`a8cc7ed0f4ec6bb6019da9b8ace51e3e6dafd06f`, with `A=1/B=126/C=2`.

The `okf-skills` vendored spec predates Google's current explicit-offset rule for every timestamp-
valued key, and its templates/validator still admit date-only values in places. Google therefore
wins every semantic conflict, and the upstream validator is not a PK-Stack verification path.

## Live canonical-tool probe

The checksum-verified arm64 `okn` 0.13.0 binary validated the current seven-file Wiki together with
the two-record feature map. Both passed: six OKF concepts, one root index, zero errors, and zero
warnings. A 900-token search for why native Kiro planning remains authoritative returned the
architecture, decision, and operations records with an index revision, content-addressed locators,
content hashes, and exact line ranges.

The bounded commands were:

```text
env PATH=<verified-okn-directory>:$PATH uv run --project powers/pk-stack projectctl knowledge status --output json
env PATH=<verified-okn-directory>:$PATH uv run --project powers/pk-stack projectctl knowledge validate --require-okn --output json
env PATH=<verified-okn-directory>:$PATH uv run --project powers/pk-stack projectctl knowledge search "why native Kiro planning remains authoritative" --budget 900 --output json
```

## Why `okfcli/okf` does not replace `okn`

In a controlled fixture, a Markdown concept inside `Wiki/` was a symlink to a regular file outside
the bundle. Canonical `okn` rejected the bundle with exit 2. `okfcli/okf` reported it valid with no
errors and its `show` command returned the outside file body. That does not make the tool unusable,
but it rules out transparent substitution at PK-Stack's trust boundary.

The immutable candidate must repeat the `okn` validation/search campaign and this selection must be
reviewed by Fable 5.1 at `xhigh` before release.
