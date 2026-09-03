# Final immutable OKF/OKN campaign

**Verdict:** pass.

This campaign executed PK-Stack commit `8806fa607b991d8e3ca9d004f2724412596f715d`
(tree `bd0488dc2b184c39c0a6c538d5f2d2ebf73375cf`) from an isolated `git archive`, not
from the live worktree. The tar's embedded commit matched the requested commit and its SHA-256 was
`998708506c9e1eb951848c2df205ab439a238699312aa3866e4dcca65076517f`.

Canonical `openknowledge-sh/openknowledge` `v0.13.0` supplied the KNOW runtime. Both the release
archive and executable matched their pinned SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| Darwin arm64 release archive | `d1350fd0e434d5231d49263981b35a1d0219d333ec167cadf605f7800d0f7b78` |
| `openknowledge` / `okn` executable | `f331ba6ea6c1cf7ea4f8903059c46647ff5118ce93440015a219006500aec4e2` |

The binary was exposed as `okn` from a temporary directory outside the candidate root. The
directory and binary were owner-only (`0700`), both `okn` and its resolved name `openknowledge`
were discoverable on PATH, and no candidate policy was relaxed. This shape matters: PK-Stack
rejects workspace-local canonical tooling and rejects unresolved external executable aliases.

## Commands and results

Private temporary locations are replaced below by stable placeholders; arguments, ordering, and
flags are otherwise exact. All commands ran with working directory
`<isolated-git-archive>/worktree`.

```text
env PATH=<verified-okn-bin>:$PATH UV_PROJECT_ENVIRONMENT=<isolated-venv> UV_CACHE_DIR=<isolated-uv-cache> PYTHONDONTWRITEBYTECODE=1 uv run --project powers/pk-stack --locked --no-config projectctl knowledge status --output json
exit 0: canonical-okn, workspace safe, Wiki present, okn 0.13.0 available as command name okn

env PATH=<verified-okn-bin>:$PATH UV_PROJECT_ENVIRONMENT=<isolated-venv> UV_CACHE_DIR=<isolated-uv-cache> PYTHONDONTWRITEBYTECODE=1 uv run --project powers/pk-stack --locked --no-config projectctl feature validate --output json
exit 0: 2 features, 0 errors, 0 warnings

env PATH=<verified-okn-bin>:$PATH UV_PROJECT_ENVIRONMENT=<isolated-venv> UV_CACHE_DIR=<isolated-uv-cache> PYTHONDONTWRITEBYTECODE=1 uv run --project powers/pk-stack --locked --no-config projectctl knowledge validate --require-okn --output json
exit 0: OKF 0.2, 7 files, 6 concepts, 1 index, 10 passing checks, 0 errors, 0 warnings, 0 issues; feature map also passed 2/2

env PATH=<verified-okn-bin>:$PATH UV_PROJECT_ENVIRONMENT=<isolated-venv> UV_CACHE_DIR=<isolated-uv-cache> PYTHONDONTWRITEBYTECODE=1 uv run --project powers/pk-stack --locked --no-config projectctl knowledge search "why native Kiro planning remains authoritative" --budget 900 --output json
exit 0: 6 passages, 879 estimated tokens of 900, 0 issues, output neither timed out nor truncated
```

The bounded search used `bm25`, `vector`, `rerank`, and `link_expansion`. Its index revision was
`485cfcd7b5893ee9b55cad4b8dbf0136b453427c809256575a207e0138c2f284`. It returned grounded
sections from `architecture/native-kiro-composition.md`, `decisions/native-spec-and-okn.md`,
`operations/context-depth.md`, and `features/document-export.md`. Every source carried a safe
relative path, exact line range, content SHA-256, and an `okf+sha256` locator whose revision matched
the index and whose content component matched the passage hash. The complete bounded locator list
is retained in `final-okf-campaign.json`.

## Limits

This is local Darwin arm64 evidence for one immutable commit. It validates the committed feature
map and seven-file Wiki through `projectctl` and canonical `okn`; it does not exercise OKN registry,
MCP, publishing, remote knowledge, Kiro UI/session behavior, Crew, Web, Floci, or application
business paths. Raw command payloads and private temporary paths are intentionally not retained.
