# OKF skills methodology provenance

PKStack tracks the `skills/` tree from
[`scaccogatto/okf-skills`](https://github.com/scaccogatto/okf-skills) as an untrusted
methodology input. The accepted baseline is commit
`bf2448f03686a8348324e4741106697d30a867f9`, whose `skills/` tree is
`8cc9ed3986cf6c942f718439e1ee8249eb17a2ad`.

<!-- pk-stack-upstream-genesis: {"commit":"bf2448f03686a8348324e4741106697d30a867f9","path":"skills","repository":"scaccogatto/okf-skills","source_id":"okf-skills","subtree_sha":"8cc9ed3986cf6c942f718439e1ee8249eb17a2ad"} -->

The [machine-readable source parity](okf-skills-parity.json) binds every file in that tree to its
Git object identity and one A/B/C disposition. The readable companion explains the package-level
decision. PKStack adapts only the durable knowledge-working methodology into native Kiro workflow
semantics. It does not vendor or execute the upstream validator, backfill, visualizer, MCP server,
hooks, agents, or dependency declarations.

The tracked subtree is not a complete runnable dependency closure: the excluded backfill skill
references Claude-specific agents outside `skills/`. Those agents are deliberately not tracked or
activated. If backfill ever becomes a runnable PKStack capability, its dependency boundary must
be reviewed and pinned separately first.

The upstream tree includes an older vendored copy of Google's OKF specification. It is historical
input only. The separately tracked `google-okf-spec` source is authoritative for format semantics,
and canonical `okn` remains PKStack's deterministic validation and retrieval runtime.


Review of the transition to `85db7fd0a8a66d07d984ac6c5f4fbb5063d00357` found one bounded change: `backfill/SKILL.md` updates two internal backfill-agent version examples from `0.9.2` to `0.9.3`. PKStack continues to exclude that transcript-oriented historical migration workflow from the default product, so the version-reference change adds no Kiro-native workflow semantics and requires no authored skill or runtime change.

<!-- pk-stack-upstream-review: {"inventory_sha256":"625b339711cc4cdcfaac516f986d895e79ebff074a2da856981c93bcdc4558b9","new":{"commit":"85db7fd0a8a66d07d984ac6c5f4fbb5063d00357","subtree_sha":"2f9170d6937027c2b1c487ef698f0c000bb47745"},"path":"skills","prior":{"commit":"bf2448f03686a8348324e4741106697d30a867f9","subtree_sha":"8cc9ed3986cf6c942f718439e1ee8249eb17a2ad"},"repository":"scaccogatto/okf-skills","source_id":"okf-skills"} -->