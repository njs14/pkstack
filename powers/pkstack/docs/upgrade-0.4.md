# Upgrade to PKStack 0.4

Version 0.4 retains the `pkstack` namespace and replaces the optional `okn`
knowledge backend. `knowledge validate` now checks metadata, Markdown links,
and feature maps locally. `knowledge search` uses a bounded Kiro ACP worker;
`--require-okn` is no longer supported.

Preserve the existing project as the rollback copy, including user edits,
`.pkstack/bootstrap.json`, goals, native Specs, Wiki files, settings, and evidence.
For 0.2 or older namespaces, first follow the separate-checkout
[0.3 transition](upgrade-0.3.md). Do not remove an entire Wiki or Kiro directory.

## Preview the managed refresh

Set `PKSTACK_PACKAGE` to the reviewed 0.4 checkout directory or local wheel, following
the [package-source guide](usage.md#choose-the-power-source). Leave the restricted
workspace agent in the same CLI conversation:

```text
/agent swap default
```

In Kiro IDE, use the agent picker. Then preview setup from a terminal at the
target project root:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack upgrade --dry-run --output json
```

Review all reported paths. The explicit `upgrade` command uses `--update-managed` and updates only files that match the
previous ownership receipt. User-modified files need deliberate reconciliation.
Retired `stale_managed` files are not automatically removed; review them
individually and preserve their original content. If the preview cannot apply
cleanly, use a separate clean checkout and retain the original for rollback.

After resolving the preview, apply and check the new installation:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack upgrade --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack version --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack doctor --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack feature validate --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack knowledge validate --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack knowledge status --output json
```

Keep durable project context in `Wiki/knowledge/`, feature contracts in
`Wiki/features/`, and working drafts in `Wiki/work/`. Native `.kiro/specs/`
remain Kiro-owned. Review existing prose before adding minimal knowledge
metadata; do not treat requirements or old reports as current passing evidence.
Setup does not convert arbitrary old Wiki content or goals into new evidence.

Return to the same CLI conversation with `/agent swap pkstack`, or select
`pkstack` in Kiro IDE. In CLI, inspect `/config skills` under that agent; follow
the [discovery guide](usage.md#attach-the-generated-agent) if refreshed skills
remain absent. When context is needed, run a bounded query:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack knowledge search "project acceptance criteria" \
  --budget 1200 --model auto --output json
```

Retrieval requires the verified Kiro CLI 2.21.1 runtime and native Kiro
authentication. Live query evidence is macOS/KAS 0.58.7; Linux runtime discovery
and model inventory have separate canary coverage. Unsupported versions fail
closed while local validation remains available. Inspect returned uncertainty
and source passages; quote verification does not prove every generated inference.
See [knowledge usage](usage.md#use-project-knowledge) for the full limits.
