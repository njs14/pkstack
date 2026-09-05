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

The transition to commit `85db7fd0a8a66d07d984ac6c5f4fbb5063d00357` changes only two backfill-agent version labels in `backfill/SKILL.md`, from `okf-backfill/0.9.2` to `okf-backfill/0.9.3`. Historical transcript backfill remains excluded from PKStack; adopting this delta still requires the separately authorized, redacted, bounded migration design described above.

<!-- pk-stack-upstream-review: {"inventory_sha256":"625b339711cc4cdcfaac516f986d895e79ebff074a2da856981c93bcdc4558b9","new":{"commit":"85db7fd0a8a66d07d984ac6c5f4fbb5063d00357","subtree_sha":"2f9170d6937027c2b1c487ef698f0c000bb47745"},"path":"skills","prior":{"commit":"bf2448f03686a8348324e4741106697d30a867f9","subtree_sha":"8cc9ed3986cf6c942f718439e1ee8249eb17a2ad"},"repository":"scaccogatto/okf-skills","source_id":"okf-skills"} -->

The transition to commit `d8393f329c97836980566c1cf4e4aa4fe47dc111` expands the excluded backfill workflow with batched analyzer dispatch, bounded concurrency, count-only replies, orchestrator context-hygiene guidance, truncation reporting, model-tier guidance, and the `okf-backfill/0.9.4` trust label. It also adds an executable Git diff emitter with per-file and global caps, generated-file omission, line truncation, first-parent handling, and a new CLI mode.

Both changed resources remain excluded. PKStack does not adopt the Claude-specific orchestration, command examples, benchmark claims, model selection, or executable helper. Any future Kiro-v3-native backfill design must preserve native subagent, model, and effort ownership; keep interactive current-session semantics separate from deterministic `projectctl` proof; avoid making headless CI depend on slash commands; and receive separately authorized, redacted, bounded implementation, hostile-input testing, and independent review.

<!-- pk-stack-upstream-review: {"inventory_sha256":"5eb562b5e7f2b477f2baec268df543c5d292e1a7818a9194efe68f16c86f50ca","new":{"commit":"d8393f329c97836980566c1cf4e4aa4fe47dc111","subtree_sha":"21eb933ac68df2d2a81aedad6778970d71e99e8d"},"path":"skills","prior":{"commit":"85db7fd0a8a66d07d984ac6c5f4fbb5063d00357","subtree_sha":"2f9170d6937027c2b1c487ef698f0c000bb47745"},"repository":"scaccogatto/okf-skills","source_id":"okf-skills"} -->
