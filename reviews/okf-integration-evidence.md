# OKF integration selection evidence

This is a bounded architecture and runtime comparison finalized on 2026-09-03 from the clean
pre-documentation worktree at commit `347d461a097f5d26e084f10958641fc4aa70ce07`, tree
`78e5b4e3c1f934486ce2e24707c8ecbbdae7b92a`. It re-evaluates `okfcli/okf` v0.5.0
against canonical `openknowledge-sh/openknowledge` `okn` v0.13.0. It is not immutable release
acceptance and does not retroactively extend the older candidate-D campaign. The machine-readable
companion is `okf-integration-evidence.json`.

## Decision

`scaccogatto/okf-skills` remains valuable as a workflow-methodology source. PK-Stack adapts its
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
| Optional second opinion | `okfcli/okf` 0.5.0 | Advisory CI/SARIF only over an immutable symlink-free copy; never a runtime fallback or normative `stale_after` gate |

The workflow audit pins `okf-skills` commit
`bf2448f03686a8348324e4741106697d30a867f9` and its `skills/` tree
`8cc9ed3986cf6c942f718439e1ee8249eb17a2ad`. Its 13 blobs received a complete
`A=4/B=4/C=5` disposition. The normative source audit pins Google knowledge-catalog commit
`fbbc7975388288244dfc62aea0066600b25b7c47` and its 129-blob `okf/` tree
`a8cc7ed0f4ec6bb6019da9b8ace51e3e6dafd06f`, with `A=1/B=126/C=2`.

The [current specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/fbbc7975388288244dfc62aea0066600b25b7c47/okf/SPEC.md?plain=1)
requires every timestamp-valued key to use an ISO 8601 datetime with an explicit UTC offset and
defines `stale_after` as an absolute instant. The `okf-skills` vendored spec and `okfcli/okf`
v0.5.0 validator still use date-only values. Google therefore wins every semantic conflict, and
neither of those two validators is a PK-Stack verification path.

## Checksum-verified release identities

The two official Darwin arm64 archives were downloaded into an owner-only temporary directory.
Each archive matched both its GitHub release-asset digest and the publisher's `checksums.txt`
entry. Archive members were listed before extraction. No binary was installed globally and no
credential was read or used.

| Tool | Release commit | Archive SHA-256 | Binary SHA-256 |
| --- | --- | --- | --- |
| [`okn` 0.13.0](https://github.com/openknowledge-sh/openknowledge/releases/tag/v0.13.0) | `801b54d6da1abf69428ed7e85f7ea56b20e17552` | `d1350fd0e434d5231d49263981b35a1d0219d333ec167cadf605f7800d0f7b78` | `f331ba6ea6c1cf7ea4f8903059c46647ff5118ce93440015a219006500aec4e2` |
| [`okf` 0.5.0](https://github.com/okfcli/okf/releases/tag/v0.5.0) | `9985a55e986bf2c0ab39040fec4e4a0a24895ab0` | `fef958317c8c498374c3870d3adbe039cad6db2d6aa1ceb45c13ee1e759a0e41` | `c0afa856024bc4322f1f7c079495c47dc1ec2ccc75c5a29bf9a6a2059f9bed4c` |

The `okf` release also provides a checksum signature and per-archive SBOM. This comparison verified
the checksums, but it did not claim independent verification of the checksum signature.

The bounded preparation shape was:

```text
COMPARE_ROOT="$(mktemp -d /private/tmp/pk-stack-okf-v050-compare.XXXXXX)"
chmod 0700 "$COMPARE_ROOT"
curl --proto '=https' --tlsv1.2 --fail --location --silent --show-error -o <archive> <official-asset-url>
printf '%s  %s\n' <expected-sha256> <archive> | shasum -a 256 -c -
tar -tvzf <archive>
tar -xzf <archive> -C <owner-only-directory>
shasum -a 256 <binary>
file <binary>
```

## Fresh canonical-tool probe

The checksum-verified arm64 `okn` 0.13.0 binary validated the current seven-file Wiki together with
the two-record feature map. Both passed: six OKF concepts, one root index, zero errors, zero
warnings, and no protocol error. A 900-token search for why native Kiro planning remains
authoritative returned six sources across architecture, decisions, operations, and features at an
estimated 879 tokens. Every source retained an index revision, content-addressed locator, content
hash, and exact line range.

The bounded commands were:

```text
env PYTHONDONTWRITEBYTECODE=1 OPENKNOWLEDGE_TELEMETRY=off PATH=<verified-okn-directory>:$PATH .pstack/bin/projectctl knowledge status --output json
env PYTHONDONTWRITEBYTECODE=1 OPENKNOWLEDGE_TELEMETRY=off PATH=<verified-okn-directory>:$PATH .pstack/bin/projectctl knowledge validate --require-okn --output json
env PYTHONDONTWRITEBYTECODE=1 OPENKNOWLEDGE_TELEMETRY=off PATH=<verified-okn-directory>:$PATH .pstack/bin/projectctl knowledge search "why native Kiro planning remains authoritative" --budget 900 --output json
```

The search revision was
`ebe1021be8d891b225741268c873aab687d623a0871b0d1e3d5e320c21756b64`.

## Comparative validation and safety probes

### Symlink escape remains open upstream

In a controlled fixture, `escape.md` inside the bundle was a symlink to a regular Markdown concept
outside the bundle. The outside body contained `OUTSIDE_BODY_SENTINEL_V050`.

```text
OPENKNOWLEDGE_TELEMETRY=off openknowledge validate --profile okf --format json <bundle>
# exit 2: symbolic links are not supported inside knowledge bundles: escape.md

okf validate <bundle>
# exit 0: valid=true, errors=0, warnings=0

okf show <bundle> escape
# exit 0: returned the outside body and sentinel

okf search <bundle> --text OUTSIDE_BODY_SENTINEL_V050
# exit 0: returned the externally backed concept
```

Version 0.5.0 therefore does not close the trust-boundary defect. An optional invocation must first
create a disposable, immutable copy and reject every symlink; it must not run directly over a
sensitive working tree.

### `stale_after` remains specification-incompatible

The direct command shape for each bundle was:

```text
OPENKNOWLEDGE_TELEMETRY=off openknowledge validate --profile okf --spec 0.2 --format json <bundle>
okf validate <bundle>
okf validate --format sarif <bundle>
```

| Fixture | `okn` 0.13.0 | `okf` 0.5.0 |
| --- | --- | --- |
| `stale_after: "2027-01-01"` | Exit 0, `warn`; identifies the missing explicit offset | Exit 0, valid, no finding |
| `stale_after: "2027-01-01T00:00:00Z"` | Exit 0, `pass`, zero issues | Exit 1, invalid; `okf/lifecycle/stale-after-invalid` requires `YYYY-MM-DD` |

`okf validate --format sarif` emitted SARIF 2.1.0 with the same false-positive error for the
authoritative explicit-offset form. `--exit-zero` would mask every validation error; it would not
repair the semantic incompatibility. Consequently `okf` cannot gate normative `stale_after`
conformance.

### Useful v0.5.0 improvements

The release now treats a broken concept link as a warning, matching `okn` and the specification's
nonfatal behavior. On a duplicate-source fixture, `okn` warned about the duplicate `sources[].id`;
`okf` warned about both that duplicate and a duplicate footnote definition. Version 0.5.0 also
improves CLI argument errors and ships stable SARIF rule IDs. These are legitimate advisory-oracle
benefits, but they do not repair its runtime-boundary or timestamp incompatibilities.

On the current PK-Stack Wiki, `okn` reported zero issues. `okf` reported four nonfatal advisory
warnings for recommended description/tag metadata on two feature records. That additional opinion
is useful as review input, not as canonical acceptance.

## Search and schema boundary

The direct search commands were:

```text
okf schema search
okf search <bundle> --text "native planning"
OPENKNOWLEDGE_TELEMETRY=off openknowledge search <bundle> "native planning" --budget 300 --limit 4 --format json
```

`okf search --text "native planning"` returned one concept identity with no passage content,
ranking score, token budget, revision, locator, content hash, or line range. The equivalent
300-token `okn search` returned three ranked sources through BM25, vector search, reranking, and
link expansion, with an estimated 128 tokens and complete revision-bound provenance.

`okf schema` describes its command surface, and `validate`/`lint` can emit JSON or SARIF. It does
not replace `okn`'s strict versioned response schemas, bounded search context, read-only query,
registry, MCP, audit, claims, evidence, evaluation, or quality interfaces. PK-Stack already reduces
that broader `okn` surface to exact, bounded `validate` and `search` argv, disables telemetry,
rejects workspace-local executables, bounds output and execution time, and pre-rejects Wiki
symlinks.

## Operating boundary and remaining gates

`okfcli/okf` may be used only as an explicitly selected advisory CI/SARIF oracle over a
disposable, immutable, symlink-free copy, with bounded read-only `validate` or `lint` commands. It
must never become an automatic fallback, a fifth autonomous maintenance source, or a normative
`stale_after` gate.

The older immutable candidate-D campaign remains the exact-candidate proof for canonical `okn`.
This fresh v0.5.0 comparison is current-worktree architecture evidence only. The eventual frozen
release candidate must repeat canonical validation and retrieval and complete the still-open native
Spec and final Fable 5.1 `xhigh` council gates.
