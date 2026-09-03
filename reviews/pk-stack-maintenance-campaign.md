# PK-Stack self-maintenance campaign evidence

The latest source-scoped maintenance campaign passed its immutable projectctl
goal after one real drift failure and one accepted-baseline pass. It advanced
the Cursor pstack source from
`efa2a531985e0a8084d36ff3cf87233be8a9f34b` / `1c625329e71538629f087374daa71293a498089f`
to `7314f723a487ec406b6369fe5865ba034cfed166` /
`ae6fff5803260f38f075feb8c3b008ed68153fa0`. Both changed paths were reviewed
as B dispositions because they are Cursor-only registration/branding changes.

The complete bounded projection is in
[pk-stack-maintenance-campaign.json](pk-stack-maintenance-campaign.json).
Canonical rationales remain in
[upstream-reviews.json](../maintenance/upstream-reviews.json); exact source
pins remain in [upstreams.json](../maintenance/upstreams.json).

## Outcome

- Goal `efe929d9-9945-4c97-866b-a8f414b9ef97` used the exact source-scoped
  upstream-check argv and contract digest
  `59f08f943111cf645d05dc4962912fa81c3bf20e26b879c6ef6f7c4e21f76b5a`.
- Attempt 1 exited 1 after detecting one upstream commit, two changed paths,
  one unavailable binary patch, and a complete inventory with SHA-256
  `cb3f7506f1af19f3cc2a06518e8524f54d414dc769b353edef30807ff1d79638`.
- The accepted transition at ledger index 1 has the same inventory digest and
  exactly two dispositions: A=0, B=2, C=0.
- Attempt 2 exited 0 with the selected source pinned to the new commit and
  subtree, no drift, an identical comparison, accepted-baseline parity, and a
  two-transition review-chain reproof.
- A separate aggregate post-check exited 0 and found all three configured
  sources clean: `cursor-pstack`, `google-okf-spec`, and `okf-skills`.

## Attempt evidence

| Attempt | Start | Duration | Exit | Result | Retained stdout |
|---|---|---:|---:|---|---|
| 1 | 2026-09-03T05:08:57.199423+00:00 | 17653 ms | 1 | drift true; one commit; two paths | 20200 bytes; SHA-256 `605f66514c392951b731cb3258df9a9f07eaa5f41a4fc2a44210ce61378366a2`; strict JSON; not truncated |
| 2 | 2026-09-03T05:13:39.444267+00:00 | 5585 ms | 0 | no drift; accepted pin; goal passed | 17857 bytes; SHA-256 `d4fe5bfad683ba72d24e6caa5b864a753d41a2bedd00c9b58a017a5793199e04`; strict JSON; not truncated |

The ignored goal file was mode 0600, 61441 bytes, and SHA-256
`3fe511da6dd3bd0f9207e248525ef6979597b7e5e7c4e80362a86bdfeee7348e`
when this bounded artifact was recorded. Attempt ordinals above are positions
in the goal history array; schema version 2 does not store an ordinal field in
each entry.

## Reviewed drift

| Path | Exact change evidence | Disposition | Reason |
|---|---|---|---|
| `.cursor-plugin/plugin.json` | Exact text blobs `07c09c…` to `469c2d…`; version 0.14.7 to 0.14.8 | B | Cursor registration metadata is excluded; PK-Stack retains its independently versioned Kiro Power manifest. |
| `assets/logo.png` | Exact binary blobs `d52edb…` to `3754e8…`; patch unavailable and classified nonsemantic image | B | Cursor branding is excluded; PK-Stack retains its independently generated potato-ghost mascot. |

The detector reported a complete fast-forward comparison. Its inventory digest
is identical to the accepted ledger digest, so this campaign does not need the
digest caveat that applied to the first campaign.

## Acceptance and parity

The canonical ledger, manifest, provenance marker, accepted-baseline parity,
and passing second attempt jointly prove the accepted transition. The temporary
proposal workspace was absent after acceptance. Raw output from the acceptance
dry-run and apply was not retained in this bounded artifact, so it does not
invent call ids, command spelling, exit codes, or output hashes for those two
steps.

The source parity document intentionally preserves the reviewed comparison
pair at its top level. Its 45 per-skill entries have equal pinned and current
resource identities because neither changed path was in the skills catalog.
It records 122 resources on each side, 44 routed upstream names, and 49 shipped
skill directories.

## Aggregate post-check

The following read-only command ran after the goal:

~~~text
.pstack/bin/projectctl upstream check --manifest maintenance/upstreams.json --power-root powers/pk-stack --output json
~~~

It exited 0 with `ok: true`, zero managed-file differences, 157 unchanged
managed entries, and no drift for all three configured sources. The 23995-byte
JSON output has SHA-256
`3e0b91991ddc162d83f9701f3fe63d57e5c26ba1143b9f0f1aa96cc269c87c6f`.
This aggregate check is separate from the source-scoped goal and does not widen
what that goal itself proved.

## Prior campaign retained

The machine artifact retains the durable identity of the first transition:
historical goal `395bd46c-f889-4fbc-8933-187ab0e88441`, transition index 0,
27 reviewed paths, and A=23/B=3/C=1. That transition advanced the genesis pin
to `efa2a531985e0a8084d36ff3cf87233be8a9f34b`. The canonical ledger remains
authoritative for its complete disposition rationales, and the campaign record binds their
canonical projection by SHA-256.

The earlier ignored goal record was overwritten before its attempt timing, exit codes, stdout
hashes, and bootstrap-preview counts were committed. Those details are therefore not claimed or
reconstructed. The later source-scoped campaign above is the retained executable fail-then-pass
goal proof; the first transition is ledger/provenance evidence only.

## Boundaries

This campaign ran through a Codex harness, not Kiro CLI v3, Kiro IDE, Kiro Web,
or ACP. It has no Kiro session id. The worktree was dirty, so HEAD
`491bfdafc94832c6624ed86051955b1067245979` is context rather than an exact
attempt-tree binding. The later native Kiro campaign remains separate evidence.
