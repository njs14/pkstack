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

Set `PKSTACK_POWER` to the reviewed 0.4 Power directory. Leave the restricted
workspace agent before running setup from a terminal:

```sh
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --dry-run --update-managed --output json
```

Review all reported paths. `--update-managed` updates only files that match the
previous ownership receipt. User-modified files need deliberate reconciliation.
Retired `stale_managed` files are not automatically removed; review them
individually and preserve their original content. If the preview cannot apply
cleanly, use a separate clean checkout and retain the original for rollback.

After resolving the preview, apply and check the new installation:

```sh
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --update-managed --output json
.pkstack/bin/projectctl version --output json
.pkstack/bin/projectctl doctor --output json
.pkstack/bin/projectctl feature validate --output json
.pkstack/bin/projectctl knowledge validate --output json
.pkstack/bin/projectctl knowledge status --output json
```

Keep durable project context in `Wiki/knowledge/`, feature contracts in
`Wiki/features/`, and working drafts in `Wiki/work/`. Native `.kiro/specs/`
remain Kiro-owned. Review existing prose before adding minimal knowledge
metadata; do not treat requirements or old reports as current passing evidence.
Setup does not convert arbitrary old Wiki content or goals into new evidence.

Return to the same CLI conversation with `/agent swap pkstack`, or select
`pkstack` in Kiro IDE. When context is needed, run a bounded query:

```sh
.pkstack/bin/projectctl knowledge search "project acceptance criteria" \
  --budget 1200 --model auto --output json
```

Retrieval requires the verified Kiro CLI 2.21.1 runtime and native Kiro
authentication. Live query evidence is macOS/KAS 0.58.7; Linux runtime discovery
and model inventory have separate canary coverage. Unsupported versions fail
closed while local validation remains available. Inspect returned uncertainty
and source passages; quote verification does not prove every generated inference.
See [knowledge usage](usage.md#use-project-knowledge) for the full limits.
