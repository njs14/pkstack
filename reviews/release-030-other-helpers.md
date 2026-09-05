# PKStack 0.3.0: remaining curated helper acceptance

Date: 2026-09-05. Scope: `show-me`, `writing-for-agents`, and
`narrow-react-prop-types` through a fresh installed consumer using Kiro CLI 2.21.1,
native v3, `pkstack` agent, `gpt-5.6-luna`, low effort. No helper source changes
were required. These are bounded fixture results, not general release acceptance.

## Result

| Helper | Observed behavior | Verdict |
| --- | --- | --- |
| `show-me` | Inspected the requested request-path files and returned an inline Mermaid sequence diagram with the missing queue-to-worker connection explicitly labeled as an inference. No project edits. | Pass for read-only explanation; diagram browser rendering not tested. |
| `writing-for-agents` | Removed promotional text and the unconditional read-all-references rule from the requested document. Preserved all four required operational clauses and the reference target. | Output passes. Its first turn omitted the mandatory unslop and reference-resolution checks; one bounded follow-up completed them. This is assisted method compliance. |
| `narrow-react-prop-types` | Found the live caller and support story, required the two props supplied by the live caller, simplified fallback behavior, and updated the support story. Ran the existing strict TypeScript check successfully. | Pass in the local fixture. |

## Fixture and retained evidence

- Consumer: `/var/folders/ns/6ms4sgcd3jbc071v7_b2j2640000gp/T/pkstack-release-other-helpers.3snrkssj`.
- Evidence: `/var/folders/ns/6ms4sgcd3jbc071v7_b2j2640000gp/T/pkstack-other-helpers-evidence.llsa72qk`.
- Native session: `sess_d22a4ea8-50f5-448a-b705-b167fde28fd0`, exited normally with `/quit`.
- Evidence files: `baseline.json`, `setup.json`, `show-me-readonly.json`,
  `writing-checks.json`, and `final-checks.json`.

The fixture began with 13 files: a small account-normalization request path and
its test, a noisy agent guide and release-reference document, and a React live
caller, permissive component, support story, JSX declarations, and existing
TypeScript compiler harness. It contacts no services. Both the account test and
TypeScript check passed before the session. Current Power setup completed without
conflicts, pending updates, or stale managed files. Each installed helper was
byte-equal to its source after the session.

Invocation used the existing Kiro authentication, without changing trust or
settings:

```sh
env PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin UV_OFFLINE=1 \
  /Users/noahsutter/.local/bin/kiro-cli chat --v3 --agent pkstack \
  --model gpt-5.6-luna --effort low
```

Native disclosure events loaded `show-me` (1,970 characters),
`writing-for-agents` (3,955), and `narrow-react-prop-types` (1,882). The writing
follow-up also loaded `unslop` (2,727). Tool actions were individually approved
only after inspecting the requested operation; no trust-all setting was used.

## Requests and observations

The show-me request was:

> /show-me explain the account request path in this fixture with a small inline diagram. Inspect api.mjs, account.mjs, and worker.mjs. Keep this read-only: no new artifact, evidence log, implementation, or verification workflow. Use the selected skill's actual method and preserve any uncertainty.

Kiro read all three files. The diagram followed caller → API → normalizer →
injected queue, followed by the queued API response. It correctly described the
normalizer's string validation, space/hyphen removal, uppercasing, and 4–12
alphanumeric constraint. The final response explicitly said the inspected files
did not wire the queue to the worker and used a dashed external-dispatch arrow.
After this turn all 13 original hashes and all 169 managed hashes were unchanged,
with no unexpected files.

The writing request was:

> /writing-for-agents Rewrite only docs/agent-guide.md to remove the always-read-all-references rule and promotional prose, while preserving the normalization command, completion condition, release-publication boundary, and reference target. Use the selected skill's actual method. Preserve every other file; do not install dependencies, create a workflow, or publish anything.

The first turn made the correct four-line deletion, but omitted two required
method steps. It also tried `git diff` in this intentionally non-Git fixture,
received exit 129, and reported that limitation. A single follow-up requested the
omitted unslop pass and pointer check, restricted to the same file scope. Kiro
then loaded unslop, reread the guide and linked release document, resolved the
reference, checked the four required clauses, and made no additional edits.

Independent checks verified that only the guide had changed at that point; the
normalization command, completion condition, separate publication-request rule,
and relative reference were preserved exactly; the target resolved and retained
its original hash; and both unwanted passages were removed.

The React request was:

> /narrow-react-prop-types Narrow ui/SaveButton.tsx to the prop states used by the wired live caller ui/App.tsx, and adapt ui/SaveButton.stories.tsx as support code. Inspect all imports and usages, follow the selected skill's actual method, and run the existing local TypeScript check. Edit only the component and support story; preserve the live caller, compiler harness, and every other file. Do not install dependencies or change workflows.

Kiro read the component, live caller, and story, searched all `SaveButton` and
`SaveButtonProps` occurrences, and read the existing compiler harness. The final
props are `title: string` and `onSave: () => void`, replacing optional nullable
title and optional callback. Rendering now uses `{title}` and
`onClick={onSave}`. The support story supplies the same valid shape as the live
caller. Kiro ran `node typecheck.mjs`, then repeated the usage search and read the
changed files. The live caller was unchanged.

## Independent final checks and limits

After the native session exited, the coordinator reran:

```sh
node typecheck.mjs
node --test tests/account.test.mjs
```

Both exited zero: TypeScript 5.9.3 reported `Typecheck passed`, and the account
suite passed its one request-path test. The existing harness uses strict mode,
no emit, preserved JSX, and checks the live caller plus support story through
their component import. No dependencies were installed.

The final 13-file audit found exactly three requested changes:
`docs/agent-guide.md`, `ui/SaveButton.tsx`, and `ui/SaveButton.stories.tsx`.
All 169 receipt-managed hashes remained unchanged. No unexpected files were
created; `.gitignore` is the setup-created runtime block recorded under the
`.gitignore:pkstack-runtime-block` setup inventory key. The compiler harness,
request-path test, live caller, and release reference retained their baseline
hashes. `final-checks.json` retains all final hashes and command output.

This session does not prove unassisted writing-method compliance, visual Mermaid
rendering, browser behavior of React, broad application compatibility, concurrent
execution, or hosted release behavior. No publication, workflow, schedule, or
external service operation occurred.
