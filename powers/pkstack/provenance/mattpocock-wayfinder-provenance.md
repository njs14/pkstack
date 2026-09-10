# Wayfinder provenance

PKStack adapts [Matt Pocock's Wayfinder](https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/wayfinder)
under the Matt Pocock MIT notice in [third-party notices](../THIRD_PARTY_NOTICES.md).
The source subtree contains `SKILL.md` and `agents/openai.yaml`; both are recorded
in the complete source inventory. The OpenAI UI metadata is excluded from the
Kiro bundle. Explicit invocation is preserved in the wrapper's instructions.

<!-- pk-stack-upstream-genesis: {"commit":"3cca18b368ae95cdbdebbff572ccafa662551015","path":"skills/engineering/wayfinder","repository":"mattpocock/skills","source_id":"mattpocock-wayfinder","subtree_sha":"8ec0462658381bd1606d3f9db14ffc67df6a2a43"} -->

The adaptation retains agreed destinations, an index of named decisions, child
tickets, blockers, the unclaimed frontier, four ticket types, scope boundaries,
fog graduation, single-ticket resumption, and linked resolution evidence. It follows
the supplied or established tracker and restores upstream's local Markdown default
when none is provided. The earlier Cloud-only restriction is superseded.

Kiro's current session, skills, permissions, subagents, and native planning handoffs
replace provider-specific Skill calls and orchestration. Research branches and
automatic fan-out are not prerequisites. Human decision tickets wait for actual
answers. A map's Notes cannot override user authority or turn planning into
execution. Native Specs remain the authority for implementation task graphs.

GitHub Cloud and local Markdown are the only backends. The GitHub operations reference
is PKStack-authored guidance based on GitHub's documented Issues, sub-issues, and
dependency APIs. Other trackers, self-hosted issue services, automatic backend
switching, and board synchronization are excluded. The reference handles labels,
identity distinctions, pagination,
partial publication, concurrent claims, and recovery without duplicate effects.
Known closed-but-unindexed results are reconciled before selecting new work.
Resumed-session claim evidence is distinct from a matching account assignment;
another session's stale claim requires explicit owner authorization before takeover.

The Markdown reference adapts the separate
[local tracker document](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/setup-matt-pocock-skills/issue-tracker-local.md)
at the same pinned revision: original Git blob `0209a19af92c9c485cf3acc3d9e253171517ea17`,
1,810 bytes, mode `100644`. Its identity is recorded in the complete
[Pocock catalog tree](../metadata/mattpocock-catalog-tree.json), not in Wayfinder's
two-file source subtree. The wrapper adds a local backend reference without importing
or executing the upstream setup skill. The catalog's explicit `supporting_resources`
entry binds this reference to the reconstructed catalog pin. Bundle accounting requires
both every adapted primary resource and every declared supporting reference; supporting
entries cannot replace primary inventory, import a skill entrypoint, or admit executable
or symlink resources. This document is not a separately auto-accepted maintenance source.

PKStack places new local maps in ignored `Wiki/work/<effort>/` instead of `.scratch/`,
while resuming explicitly supplied existing maps in place. It keeps numbered files,
question/type/status/blocker markers, and linked Answer sections. Minimal Wiki
frontmatter, visible session claims, explicit retired state, dependency checks, and
partial-write recovery preserve local ownership without claiming atomic locking.

Both backends compose the shared OKF lifecycle: curate reusable understanding into
existing topic documents at charting, resolution, and handoff. Working maps and raw
discussion stay outside durable knowledge. Retained evidence must stand alone,
repeated capture must not duplicate knowledge, and capture failure remains separate
from ticket resolution. No knowledge receipt proves that a decision is implemented.

The [source inventory](../metadata/mattpocock-wayfinder-source-parity.json) binds
the exact upstream objects and dispositions; the
[bundle manifest](../metadata/mattpocock-wayfinder-bundle-manifest.json) binds the
installed wrapper and both backend references. Original source object identities
remain distinct from the adapted bundle hashes. Registration, fixture review, and
local validation do not establish live Kiro execution or GitHub mutation results.
