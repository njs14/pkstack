# babysit-pr provenance

Source: [`openai/codex` at `9f70e34`](https://github.com/openai/codex/tree/9f70e348e0227980de97e361cce830236fb18317/.codex/skills/babysit-pr).
Retrieved 2026-09-07. Licensed under Apache-2.0; attribution and license locations are retained in
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## Reviewed adaptation

The port adds one Kiro-native `babysit-pr` method and routes PKStack's existing Babysit entry to
it. Published review coverage, current-SHA CI evidence, early failed-job diagnosis, branch-versus-
infrastructure classification, and owned monitoring are retained. The upstream Python watcher,
Codex profile, temporary-state implementation, and automatic write policy are excluded.

PKStack keeps merge-ready as the default stopping point; explicit continued monitoring may wait
for closed/merged state or an agreed deadline. One-shot checks remain one-shot. Retry budget is
one fresh-build cycle per head SHA, survives watcher restarts, and requires evidence plus user
rerun authorization. Unknown or incomplete evidence cannot establish readiness. Repair ordering
remains conflicts, valid review findings, then CI. Pushes and review-thread mutations retain exact
user authorization, and babysitting never authorizes a merge. This resolves the conflicting
upstream defaults of watching all open PRs indefinitely and up to three flaky retries per SHA.

GitHub CLI supplies observations through existing tooling; no scheduler or detached watcher is
installed. Readiness is tied to the observed head SHA and time, not a promise about later feedback.

## Local verification correction

A September 7 native continuation ran `git fetch --no-write-fetch-head` during a requested
read-only check. That flag does not prevent ref/object/reflog writes. The local adaptation now
requires forge API reads for remote freshness and disables optional Git locks for local
status/diff inspection. The continued-check regression scenario includes stale or absent
remote-tracking refs and preserved retry accounting. Check totals come from returned arrays.
This is a local guidance correction; the accepted upstream source identity and history below
are unchanged. Native observations and their limits are retained in the repository Wiki.

## Exact inventories

The [source inventory](openai-babysit-pr-source-parity.json) binds all 6 regular blobs to the exact
Git subtree `930db390730c900f644d054e4a322fc865437c34` and records A (adapt), B (exclude), or C (provenance) for each.
The [bundle manifest](openai-babysit-pr-bundle-manifest.json) binds every shipped local file by path, mode,
size, and SHA-256. This is a new source genesis, not a transition of an existing source.
Existing upstream pins and accepted histories remain unchanged.

Root legal-file identities at the same commit:

| Path | Git blob SHA-1 | SHA-256 | Bytes |
| --- | --- | --- | --- |
| `LICENSE` | `4606e72e042564097e8780d66c1d4dcb611869bd` | `d17f227e4df5da1600391338865ce0f3055211760a36688f816941d58232d8dc` | 10926 |
| `NOTICE` | `2805899d56d0332d175cfc613c67d45d6f006db7` | `9d71575ecfd9a843fc1677b0efb08053c6ba9fd686a0de1a6f5382fd3c220915` | 242 |

<!-- pk-stack-upstream-genesis: {"commit":"9f70e348e0227980de97e361cce830236fb18317","path":".codex/skills/babysit-pr","repository":"openai/codex","source_id":"openai-babysit-pr","subtree_sha":"930db390730c900f644d054e4a322fc865437c34"} -->
