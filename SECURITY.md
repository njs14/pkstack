# Security policy

PKStack is a local developer tool. It can run project commands, write
workspace configuration, validate knowledge locally, and retrieve bounded context
through a Kiro ACP worker. Treat its permissions and imported content as sensitive.

## Supported versions

| Version | Support |
| --- | --- |
| Current `main` / next `0.5.0` pre-release | Security fixes and release-blocking reports |
| Earlier release lines | No backport commitment; reproduce against the maintained line |

The Power's release version is the `version` field in
[`powers/pkstack/plugin.json`](powers/pkstack/plugin.json). A matching
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
