# Security policy

PK-Stack is a local developer tool. It can run project commands, write
workspace configuration, and optionally call a separately installed knowledge
tool, so treat its permissions and imported content as sensitive.

## Supported versions

| Version | Support |
| --- | --- |
| `0.2.x` | Security fixes and release-blocking reports |
| `< 0.2.0` | Upgrade to the current release before reporting a known issue |

The Power's release version is the `version` field in
[`powers/pk-stack/plugin.json`](powers/pk-stack/plugin.json). A matching
`v<version>` tag is required before calling that version released.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting or Security Advisory flow
for this repository. Include the affected version or commit, a minimal
reproduction, expected and observed behavior, and any known workaround. Do not
open a public issue for an unpatched vulnerability or include credentials,
private transcripts, or personal data in the report.

If private reporting is unavailable, open an issue that contains only the words
"security report requested" and wait for maintainer guidance; do not disclose
the details publicly.

We will acknowledge a report when we can, reproduce it in an isolated project,
and coordinate disclosure after a fix or mitigation is available. This policy
does not promise a response time or a bounty.

## Scope notes

- The verifier screen is a bounded hazard check, not an operating-system
  sandbox. Review project-owned verifier code before approving it.
- The Floci integration lab is a separate private repository and has its own
  deployment and data boundary.
- Never place `KIRO_API_KEY` or another provider credential in candidate code,
  project files, evidence, or review prompts.
