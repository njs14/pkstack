**APPROVE**

Reviewed **base** `4414dfaf27dee0a291a2bef36b293b132c444d7e` against **source** `d36bb88b2f10e3103060ecbad0c1053ccba5564e`. Workspace **HEAD** `1b1a229` is documented as reviews-only on top of that source; this verdict is for the source candidate, not a merge/release.

No actionable defects in accepted scope.

## Findings

None.

## What the change does

The candidate ports Astral `uv` / `ruff` / `ty` as adapted Kiro wrappers with provenance and bounded routing, adds a repository-only `CLAUDE.md` → `AGENTS.md` symlink, treats selected Auto as its own model without inventing an underlying identity, and extends first-party Python static coverage through one shared gate. The only source delta after `3738ede` is the bootstrap steering assertion at `powers/pkstack/tests/test_bootstrap.py:134` (`pkstack-python.md` in the expected set). That matches the v1 full-gate failure recorded in `reviews/astral-python-auto/full-gate-summary.json`.

## Independent inspection (this review)

**Resolved earlier with git (prior session, worktree was `3738ede`):** merge-base equals base; single parent `4414dfaf27dee0a291a2bef36b293b132c444d7e`. This continuation did not re-run git. Source identity for `d36bb88` is taken from the committed gate summary plus the bootstrap test line the parent identified.

**I did verify in source:**

- **Inventory / packaging / authority.** Provenance pins `f3ce88a7ba830f53afd6d944c1d0278ed318e142` / subtree `8cc1cb9f539f90fd98efa4be3857c6d74fd8d839`. Disposition A on the three skill files, C on `.claude-plugin/plugin.json`. Bundle manifests bind the adapted SHA-256s; those match the live Power skills and `reviews/astral-python-auto/native-summary.json` (`uv` `fa007ce6…`, `ruff` `33547376…`, `ty` `bdf505fe…`). `.kiro` copies matched Power bytes. Hatch `force-include` ships the Astral docs; skills ride the existing `skills/` include. Maintainer write allow-list can update those Markdown/JSON artifacts and cannot write `.github/**`, `CLAUDE.md`, `src`, or tests. `pkstack` denies writes to `.kiro/skills/{uv,ruff,ty}/**`. MIT notice for Astral is in `THIRD_PARTY_NOTICES.md`. Routing lives in a bounded `astral-routing.json` (plan-only stays `pkstack`; Poetry/LSP/global-pip are forbidden effects). Auto JSON keeps `model` / `resolved_model` / `sources`; text output only labels Auto. `knowledge_acp.py` still sets `resolved_model` to `None` when selected model is `auto`.
- **`CLAUDE.md`.** Git mode `120000`, target `AGENTS.md`. Installation test requires bootstrap not to create `CLAUDE.md` in a new project.
- **Shared static gate.** `pkstack_python_static.py` is the single entry used by `pkstack_checks.run_policy` and both upstream-candidate workflow static sections. It covers Power `src`/`tests`/`benchmarks`/`examples`/setup, `.github`, and seven pinned quoted heredocs via temp files that are linted, not executed. Empty surface fails closed. Unquoted, `<<-`, multiple heredocs, non-literal `run:` blocks, and `PY` with a non-python command raise `StaticCheckError`. Current identities are the seven tuples in `test_pkstack_python_static.py:14-21`. Double-quoted heredocs are accepted (shell would expand them); that is a bounded extractor, not a general shell parser, and the maintained bodies use `<<'PY'`.
- **`_focus_update_title`** (`validate_kiro_credential_stream.py:200-226`). Nested non-string titles are compared with `isinstance` / `!=` and raise `StreamError` before any `set()`/`encode` on unhashables. `test_python_focus_contract.py` covers `update` / `kiro` / `focus` with `None`, `[]`, `{}`, `False`, `1`.
- **Pinned workflow payloads.** Decoded `STREAM_VALIDATOR_BASE64` equals `.github/scripts/validate_kiro_credential_stream.py` and pin `5b8014edd144b21c3c5ffd3c538bdba8941dcddadec2024f4743311df9332de0`. `CI_AGENT` pin `9a3c8f66…` matches its payload and is unchanged. Permission fixture `ef583340…` and validator `e0e51017…` match the smoke workflow pins. That is a re-pin from final bytes, not a looser credential check.
- **AST-mapped “behavior” sites.** Import reorder, annotations, `contextlib.suppress`, explicit `zip(..., strict=False)`, and `type(usage) is int` vs `bool` subclassing are fail-closed JSON narrowing, not trust-boundary weakening. `pkstack_ci_package.config_digest` now loads `pkstack_checks.config_digest` (which includes `ruff.toml`/`ty.toml`) and only validates the hex. GHA output uses `json.dumps` for actual bools (`pkstack_ci_package.py:856`). `update_controller.decide`’s `source_id and source` split is equivalent to the previous `source = sources.get(source_id) if source_id else None` guard.

**Parent-observed, not re-executed here:** full local v2 at `d36bb88` (`reviews/astral-python-auto/full-gate-summary.json`): outcome `passed`, 10/10 lanes, **974** Power tests + **234** repository unit tests, policy receipt present. I did not rerun that gate, the cancelled unittest invocation, or ruff/ty. I do not claim those tests from this process.

## Native evidence (as bounded, not as full acceptance)

Committed README/summary match the code: Kiro CLI v3 Auto session, initial headless denials, same-session interactive `Allow` on one `greet.py` write, no persistent permission change. Skill bytes in the native summary match the final wrappers; later bootstrap inventory, tests, and root static-checker work were outside that fixture. Native prose claiming controller-persisted receipt is contradicted by the summary and retained verifier stdout (`native-host-final.json`: `ok: true`, `exit_code: 0`). That is not IDE, zero-intervention, or full-source acceptance.

## Limitations

- This continuation could not re-resolve `d36bb88` / `1b1a229` with git; HEAD docs were not byte-diffed against source.
- Full-gate pass is parent-observed evidence, not a test run I launched.
- Embedded extraction was reviewed against the implementation, the seven pinned identities, and the reject tests; it is not a claim that arbitrary shell quoting works.
- Worker `PYTHON-RESULT.md` early inventories were not used; current trees, coverage note, and gate summary were.

Stop at PR. Do not treat the green gate or this approval as merge or release authority.
