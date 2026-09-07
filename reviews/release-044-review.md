# PKStack 0.4.4 independent release review

Model: Grok 4.6, xhigh. Candidate: `6a78b1910563854215e0b78232f9a39c74522749`.
Base: `5a905eb81d587fe0d8275594c12ba0eb9454f200`. Read-only external review.

**APPROVE**

Metadata-only `v0.4.4` prep on the stated frozen tree. It is consistent with merged PRs #53/#54 and does not claim publication.

## Versions and mirrors

Authority `powers/pkstack/plugin.json` is `0.4.4`. Matching mirrors: `powers/pkstack/pyproject.toml`, `powers/pkstack/src/pkstack/__init__.py`, `powers/pkstack/uv.lock` (`name = "pkstack"`), `powers/pkstack/templates/projectctl/uv.lock`. Generated copies match: `.pkstack/projectctl/pyproject.toml`, `.pkstack/projectctl/src/pkstack/__init__.py`, `.pkstack/projectctl/uv.lock`.

Lock diffs change only the `pkstack` package version (`0.4.3` → `0.4.4`). Other resolved packages are unchanged. `typing-inspection` `0.4.4` is a different package, not a stray pkstack pin.

## Receipt

`.pkstack/bootstrap.json` updates exactly the three generated files that changed (`pyproject.toml`, `__init__.py`, `uv.lock`). Other hashes, including `launcher.py` / `runner.py` / `bootstrap.py`, are untouched. Independent SHA-256 of those bytes was not computed (read-only file inspect only). Repeat preview `release-044-idempotent.json`: `ok: true`, `dry_run: true`, empty `updated` / `pending_updates` / `conflicts`.

## Notes and status

`CHANGELOG.md` `[0.4.4]` covers uvx local `--from` use, controller authority, preserved verifier/env/exit/cancel behavior, retained entrypoints, no registry/global install, Astral tooling (PR #53), Auto-model boundary, stacked-PR CI and walkthrough isolation (PR #54). It states CLI evidence, not a new native campaign.

`reviews/release-status.md`: `status: prepared` (not published). Names PRs #53/#54 and main `5a905eb81d587fe0d8275594c12ba0eb9454f200`, keeps 0.4.3 as previous publication, and describes remaining tag/verify/byte-compare steps. Existing `v0.4.3` is left in place.

No functional, dependency, workflow, or permission files in the 11-file delta.

## Coordinator evidence (not re-run)

`release-044-targeted.log`: 6 passed. `release-044-static.log`: lock/ruff/ty passed. Hosted exact-main package and tag-bound publish were not part of this review.

Publication still requires: metadata PR on main, exact-main artifact, lightweight `v0.4.4` matching the manifest, then archive/checksum compare. This commit is prepared, not released.
