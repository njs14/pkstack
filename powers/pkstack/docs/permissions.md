# Global permission defaults

PKStack's consumer agents inherit your Kiro permission policy. The primary agent
exposes all built-in tools; architect, reviewer, and verifier expose only `read`
and `knowledge`. Tool selection defines their roles. None of these four profiles
contains permission rules, legacy tool grants, or subagent trust grants.

The optional [permissions preset](../examples/permissions.yaml) allows built-in
tools and adds targeted shell denies for direct root/home deletion, filesystem
formatting, disk erasure, and raw-device overwrites. It is intended for a trusted
personal development environment. It allows reads, writes, shell, web tools, and
subagent invocation, including future tools in Kiro's built-in category.

Ordinary cleanup, Git restoration, force pushes, publishing, infrastructure
commands, lockfile edits, and secret-file access receive no extra prompts from
this preset. An allowed tool still acts within the task you authorize; it does
not authorize unrelated work or changes to an agreed verifier.

## Install manually

1. Review the YAML and your existing `~/.kiro/settings/permissions.yaml`. Save a
   separate, dated backup of the existing file before editing it.
2. In an editor or terminal outside the Kiro agent, install the preset at that
   user-level path. If a policy already exists, merge deliberately: retain its
   MCP rules and any other restrictions you still want. Remove obsolete non-MCP
   `ask` and `deny` rules only when you intend the new defaults to replace them.
3. Check workspace policies under
   `~/.kiro/workspace-roots/<hash>/permissions.yaml` for additional restrictions.
   Do not put an active permission policy inside the cloned repository.
4. Start a fresh Kiro CLI v3 session, or a fresh IDE chat using Autopilot, and
   verify a harmless read, edit, and shell command in a disposable workspace.
   In the IDE, Supervised autonomy can still require approvals.

For a new user policy only, from the repository root:

```sh
mkdir -p "$HOME/.kiro/settings"
cp -n powers/pkstack/examples/permissions.yaml "$HOME/.kiro/settings/permissions.yaml"
```

`cp -n` leaves an existing policy untouched. For an imported Power, use the
reviewed Power folder's `examples/permissions.yaml` as the source instead.
PKStack setup never installs this example, edits global settings, or changes
your default agent. To undo the adoption, restore your saved policy or remove
only the rules you added. Existing projects and native workflows need no policy
copy in their agent configurations.

## How rules combine

Kiro evaluates `deny > ask > allow` across its own rules, enterprise policy,
user, workspace, agent, and session scopes. A broader allow cannot override an
existing ask or deny. The `builtin` capability excludes MCP, so this preset
neither grants MCP access nor changes your MCP configuration. PKStack also
retains `includeMcpJson: false` and `includePowers: false` in its consumer profiles.
Its CI maintenance and review profiles use their separate, restricted policy.

Kiro's permission files apply across local CLI v3 and IDE agents. Native Plan
and Spec retain their own workflow approvals and tool selections. A global
allow does not add write tools to a read-only planning agent or helper. Kiro Web
uses its cloud execution model and does not load this local YAML policy.

## Matching limits and remaining prompts

The preset uses native glob rules, not a command parser or an OS sandbox.
Kiro checks parsed shell subcommands independently. Shell `*` spans characters;
filesystem glob semantics are different. An allowed script can perform actions
that its invocation does not reveal. Do not treat this preset as containment
for untrusted code, and never test destructive examples by executing them.

Deletion patterns cover direct `/`, quoted `/`, `~`, `~/`, and the listed home
variable forms with common flag positions, absolute `rm` paths, and plain
`sudo` wrappers. Expanded home paths, root wildcards, aliases, unusual quoting,
wrapper options, and indirect scripts require separate review; they are not
claimed to be comprehensively matched. Add your exact home-directory spelling
if you want to deny its literal use. Recursive deletion of a specific build or
temporary directory remains allowed.

Kiro also enforces restrictions outside user YAML. Its public reference lists
protected settings writes and protected-path approvals. Inspection of the
installed CLI 2.21.2 v3 bundle on September 10, 2026 additionally found symlink
escape checks and a direct `.kiroignore` write deny; some configuration-path
asks depend on workspace trust and broad user write allowances. Those are
version-specific source observations, not a guarantee of every client surface.
Policy parse errors or an unsupported shell form can still require approval.

The preset intentionally adds no hooks, fork-bomb detector, or resource limits.
When diagnosing a prompt, identify its matched rule and scope before changing
the policy. Keep Kiro-owned protections effective.

## References

- [Kiro permissions](https://kiro.dev/docs/permissions/)
- [Configuration scopes](https://kiro.dev/docs/configuration/)
- [Built-in tools](https://kiro.dev/docs/tools/)
- [Agent configuration](https://kiro.dev/docs/custom-agents/configuration-reference/)
- [Subagent configuration](https://kiro.dev/docs/custom-agents/subagents/)

The reference pages and installed v3 policy code were inspected on September 10,
2026. Runtime observations for a candidate must record the tested client version,
selected agent, effective policy, and actual tool result separately.
