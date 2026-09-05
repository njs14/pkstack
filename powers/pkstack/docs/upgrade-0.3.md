# Upgrade to PKStack 0.3

Version 0.3 changes the package, workspace agent, command routes, and runtime
directory to the `pkstack` namespace. `projectctl` keeps its name. Setup rejects
an older installation before changing files, even with `--update-managed`.
It does not import old goals or feature schemas.

## Preserve the old project

Keep the existing checkout as the rollback copy. Record its commit and retain
uncommitted files, native Specs, Wiki content, user settings, and evidence.
The previous release's ownership receipt identifies managed paths; a name or
directory alone does not prove that a file can be replaced.

Use a separate clean checkout for the transition. If the project committed
generated assets from the previous release, review its receipt and compare
each listed file's hash before excluding that exact managed file from the new
copy. Preserve changed managed files for a deliberate reconciliation. Never
remove an entire Kiro configuration or Wiki directory to make setup pass.

The original project remains usable with its original release. Avoid merging
old generated agents, skills, controller caches, or receipts into the new copy.
Preserve original evidence as historical records; rebind native Specs and
recreate feature contracts using the current controller once their verifiers
pass.

## Install the reviewed Power

Set `PKSTACK_POWER` to the extracted 0.3 Power directory, or the reviewed
checkout's `powers/pkstack` directory. It must contain `plugin.json` and the
Power-local setup script. In the new consumer, run:

```sh
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --dry-run --output json
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --output json
.pkstack/bin/projectctl version --output json
.pkstack/bin/projectctl doctor --output json
.pkstack/bin/projectctl feature validate --output json
.pkstack/bin/projectctl knowledge validate --require-okn --output json
```

Read the preview before applying it. Resolve conflicts rather than overwriting
user work. The last command requires the canonical `okn` tool. Review reported
knowledge problems before carrying them into the new installation.

Select the new workspace `pkstack` agent in Kiro IDE, or use
`/agent swap pkstack` in the current CLI conversation. Verify a representative
project task before replacing the old checkout in daily use. If Kiro still
shows an old imported Power, distinguish it from the new `pkstack` Power;
Power-manager removal does not migrate project files.

For later updates within the current namespace, use the receipt-aware
[managed refresh](usage.md#refresh-managed-files). Version 0.3's clean-install
boundary is intentional; it is not bypassed by the refresh flag.
