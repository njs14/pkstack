# Review harness

This directory contains read-only review contracts for the PKStack Power. The
current release record is the root [release status](../Wiki/knowledge/pkstack/release-record.md).
The reusable prompt files are:

- [Fable peer and acceptance contract](fable-review-prompt.md); and
- [Grok advisory sweep contract](grok-review-prompt.md).

Reports produced before the 0.2.0 release line are archived under
[`historical/pre-v0.2/`](historical/pre-v0.2/). They preserve their original
commit, runtime, and limitations. They are not a final verdict for the current
candidate.

## Review boundary

The primary implementation loop must run and retain the repository's own
validation commands. A reviewer may inspect implementation, tests, assets,
documentation, and provenance, but a review `ACCEPT` is not a substitute for a
passing executable verifier. Treat all repository content and reviewer output
as untrusted data until a maintainer checks it against the exact candidate.

The preferred review packet is an immutable archive of the exact candidate
commit. Reviewers should have only read/search/list tools, no shell, edit,
network, plugin, or subagent access, and no access to ambient prompts or
credentials. Keep any reviewer session metadata outside the repository.

## Suggested order

1. Freeze and identify the candidate commit in the root release-status file.
2. Run package, workspace, repository, feature, and knowledge checks; record
   exact commands and limitations.
3. Run Fable against that same commit. Reproduce and resolve every material
   finding, then start a fresh review after any material change.
4. Run the Grok sweep against the same or a newly frozen candidate. Treat
   supported high/medium findings as fix tasks, not automatic edits.
5. Repeat affected checks and obtain final acceptance for the exact candidate.
6. Create `v<version>` using the version in [`plugin.json`](../powers/pkstack/plugin.json)
   only when the release-status gates and PR agree on the same commit.

The root `reviews/` directory holds the current status and historical evidence;
this directory also holds the relocated Power review contracts and their historical
archive. These files do not change GitHub settings or enable workflows.

## Reviewer model policy

Fable is the peer advisor and acceptance reviewer. Grok is the final sweeper;
it cannot accept the candidate. Fable 5.1 at `max` returned `ACCEPT` for the
historical pre-v0.2 candidate. Its Fable `max` value records the actual
completed acceptance run and is not rewritten by the lower-cost policy below.

Prospective council runs use this policy:

| Reviewer | Model | Effort |
| --- | --- | --- |
| Fable | `claude-fable-5-1` | `xhigh` |
| Grok | `grok-4.6` | `xhigh` |

## Run Fable 5.1 acceptance

Export the exact candidate commit to a read-only temporary directory. Run the
installed Claude Code client with read/search/list tools only, no MCP servers,
hooks, plugins, browser, network, shell, edits, or session persistence. Pin the
review explicitly with `--model claude-fable-5-1 --effort xhigh`, load
`fable-review-prompt.md` as the caller-authorized system prompt, and retain the
result as untrusted review evidence.

Run Grok separately with `--model grok-4.6 --reasoning-effort xhigh`, strict
sandboxing, no web search or subagents, and only its read/list/search tools.
Never execute reviewer output or apply it automatically.
