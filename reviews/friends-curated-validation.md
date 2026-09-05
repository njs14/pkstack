# Curated skill functional smokes

Completed on 2026-09-05: all six curated skills were loaded through native Kiro
tool events and produced useful results in a disposable consumer. Three smokes
passed their bounded tasks; the design, diagram, and loop-builder smokes retain
the limitations below. This is not a general semantic-routing or
production-automation acceptance verdict.

## Runtime and scope

- Kiro CLI 2.21.1, interactive `chat --v3`, generated `pkstack` profile,
  `gpt-5.6-luna`, `low`; existing Kiro authentication only.
- Source: `/private/tmp/pkstack-friends.a1lG4m/powers/pkstack`, candidate based on
  `f53f0931ef3a6748242d2dd569fe0cef0ddb2106` with the reviewed local friends changes.
- Disposable consumer: `/private/tmp/pkstack-curated-smoke.fyhM5s`.
- First native session: `sess_ea5984e2-e608-4328-9bec-1cdc72ceb800`, exited normally.
- Second native session: `sess_a5eff62f-5ca5-4e1b-82ab-f6987c794a42`, exited normally.
- No trust override, permission-profile edit, source edit, schedule, publication,
  external model provider, dependency installation, or product-updater run.
  Native per-action approvals use **Allow** once, never **Always allow**.
- Shared account baseline supplied by the parallel campaign: 340.44 of 1,000
  covered credits. Concurrent campaigns make account deltas unsuitable for
  attribution; the table records Kiro's rounded per-turn display.
- This campaign's rounded per-turn displays sum to **0.28 credits**, below its
  two-credit target. The final native `/usage` at 2026-09-05 12:56:52 UTC showed
  **343.88 of 1,000** covered credits. The account-wide increase of 3.44 includes
  the concurrent campaign and is not this lane's measured cost.

The coordinator created a small account-request fixture, a two-label JSON file,
an agent-document draft, and a React prop fixture. Setup copied the frozen Power
successfully with no conflicts or pending updates. Before model work, both
`node typecheck.mjs` and `node --test tests/account.test.mjs` passed. The typecheck
uses the TypeScript compiler already installed with Kiro, without a package install.

```sh
env PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  /opt/homebrew/bin/python3 \
  /private/tmp/pkstack-friends.a1lG4m/powers/pkstack/skills/pkstack-setup/scripts/setup_pkstack.py \
  --root /private/tmp/pkstack-curated-smoke.fyhM5s --output json

env PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  /Users/noahsutter/.local/bin/kiro-cli chat --v3 --agent pkstack \
  --model gpt-5.6-luna --effort low
```

The installed wrapper SHA-256 values bind the tested skill bytes:

| Skill | SHA-256 |
| --- | --- |
| `show-me` | `70655d39c58b8d4716c70a827f1d2c93600f3192bdc20c427d078dcd87ae5e81` |
| `archify` | `fe6e5d17592e83e9925b019764e856091269038f8099e41d215150d9261aa133` |
| `design-control-loop`, original | `7bd241cc39bf41a37dfd5cf98c8a9b011aa3887ee759601974328f298c7f9de7` |
| `design-control-loop`, source-owner correction | `93fa953b5db3e9e70961259bcd8347cfd8fca4a9dbd257b256e9d22c339377a0` |
| `build-iterated-agentic-loop` | `d38e8d6371f96cc60283f3d631011579d9a427e1674e1360eadd08c6837d32b9` |
| `writing-for-agents` | `e94a223e748ce4c41132a686b475d03693c25415cd04060b1b7678dc10a1ec44` |
| `narrow-react-prop-types` | `79d2b0bf60a9e1310952614dbb2f6985256e408935ae6f13596fbb4bd57532e1` |

## Observations

| Skill | Observed use and useful result | Rounded credits / time | Outcome |
| --- | --- | --- | --- |
| `show-me` | Native `disclose_context` loaded `show-me`; Kiro read `api.mjs`, `account.mjs`, and `worker.mjs`, then returned an inline Mermaid request-flow diagram and explicit queue-wiring uncertainty. | 0.01 / 28 s | Bounded read-only smoke passed. |
| `design-control-loop` | Native `disclose_context` loaded the skill; Kiro read `README.md`, `data/labels.json`, and `.kiro/skills/design-control-loop/references/taxonomy.md`, then returned a concrete two-attempt, one-label-per-step control contract. | 0.02 / 52 s; correction 0.00 / 2 s | Useful design with an initial unsupported observation claim; corrected after feedback. |
| `design-control-loop`, fresh retest | Native context disclosure loaded the corrected wrapper; Kiro read the README and label data, returned expected transitions, and explicitly labeled all command shapes proposed and unexecuted. | 0.02 / 1 m 16 s | Evidence-labeling retest passed; required taxonomy read was not observed. |
| `archify` | Native context disclosure, local example/runtime reads, real specification and HTML creation, doctor, validation, delivery, and browser captures. | 0.10 / 4 m 21 s | Partial: delivered and structurally valid; visual containment failed. |
| `writing-for-agents` | Native disclosures loaded `writing-for-agents` and `unslop`; Kiro read the target guide and release reference, rewrote only the guide, and checked the link target. | 0.04 / 2 m 30 s | Bounded edit and pointer check passed; Git diff checking unavailable in this non-Git fixture. |
| `narrow-react-prop-types` | Native context disclosure, complete fixture usage search, component/live-app/story reads, two bounded edits, and a real local TypeScript check. | 0.02 / 2 m 16 s | Bounded prop-narrowing smoke passed. |
| `build-iterated-agentic-loop` | Native context disclosure, required control-loop reference read, two local implementation files, separate sensor/controller commands, one Kiro-actuated trim, and verifier/no-op outputs. | 0.07 / 7 m 20 s | Partial: useful one-step execution; generated attempt-bound and baseline-verifier defects remain. |

The native context disclosures are observed tool events, not the model's claim that
it used a skill. Their matching wrapper files are under `.kiro/skills/<name>/SKILL.md`
in the consumer. Read paths above came from actual tool events. The report retains
bounded commands, outputs, and artifacts; it does not copy private reasoning or a raw transcript.

### Visual explanation

The exact task was:

> /show-me explain the account request path in this fixture with a small inline diagram. Inspect api.mjs, account.mjs, and worker.mjs. Keep this read-only: no new artifact, evidence log, implementation, or verification workflow. Use the selected skill's actual method and preserve any uncertainty.

The answer connected `submitAccount` to `normalizeAccountId`, the injected queue,
and `processAccount`, and included the invalid-input branch. It accurately stated
that the files do not show queue delivery or consumer registration. No verifier
was run by Kiro and no workspace file was created or changed for this turn.
The separate CLI campaign owns the ambiguous "show me what you did" case.

### Control-loop design and reporting limitation

The task requested a read-only design to trim at most one padded nonempty value
in `data/labels.json` per iteration, preserve keys, and stop after at most two attempts.
The initial response supplied a sensor, controller, actuator, dampener, flow bounds,
and proposed local commands. It correctly called the proposed script a placeholder.

It also used the heading **Observed run** for a predicted transition from padded
`alpha` to trimmed `alpha`, even though it had executed no loop. This was an
unsupported evidence claim. The initial control contract also left the relation
between invalid input and an empty eligible list insufficiently explicit.

One bounded correction request produced:

> Expected behavior, not observed run ... No loop was executed.

It then made malformed input, empty labels, and changed keys terminal failures;
an empty eligible list counts as success only with a valid, fully compliant input.
The corrected response does not erase the original failure.

The original frozen `design-control-loop/SKILL.md` gated implementation and asked for proof
and failure states, but neither it nor `references/taxonomy.md` explicitly requires
proposed commands and hypothetical transitions to be labeled as unexecuted.
This is a source wording gap observed during the smoke. The first taxonomy read used the wrong relative location,
returned `ENOENT`, and was recovered by finding and reading the installed reference.

The source owner then added an explicit unexecuted-label rule, refreshed the
bundle manifest, and authorized a new-conversation retest with the same original
prompt. After the first conversation ended, reviewed setup with `--update-managed`
updated only `.kiro/skills/design-control-loop/SKILL.md` in the consumer. The
fresh retest used the original prompt unchanged, without an added prompt warning.
It stated **Expected state from the inspected data** and **All commands below
are proposed and unexecuted**, with no observed-run claim. Its terminal states
explicitly distinguished invalid input from completion. The new native context
disclosure reported 2,325 characters, matching the updated wrapper.

No separate taxonomy-reference read was observed in the fresh conversation,
although the selected skill requires it. This is a remaining method-compliance
limitation; the retest demonstrates the evidence-labeling improvement in this
one run, not universal skill obedience. The original failure and feedback
correction remain above.

After the two read-only smokes, all 14 original fixture-file SHA-256 values matched
the coordinator's baseline. A nonmanaged-file inventory showed no new artifact,
decision log, automation, or implementation file.

### Archify artifact and containment failure

Kiro loaded `archify` through native context disclosure, inspected its installed
runtime tree, and read
`.kiro/skills/archify/upstream/examples/async-job-roundtrip.sequence.json`.
It reused the earlier account-flow evidence and wrote only beneath `artifacts/`.

Actual commands, with repeated validation after specification edits:

```sh
node .kiro/skills/archify/upstream/bin/archify.mjs doctor
node .kiro/skills/archify/upstream/bin/archify.mjs validate sequence \
  artifacts/account-request-path.sequence.json --quality showcase --json
node .kiro/skills/archify/upstream/bin/archify.mjs deliver sequence \
  artifacts/account-request-path.sequence.json \
  artifacts/account-request-path.html --quality showcase --json
node .kiro/skills/archify/upstream/bin/archify.mjs visual-check \
  artifacts/account-request-path.html --json
```

The first validation failed layout constraints. Kiro shortened participant
labels and removed a zero-span self-message, then passed all nine structural
checks without warnings. Delivery succeeded. The browser visual check failed
vertical containment; removing optional cards and redelivering did not resolve
that failure. Kiro stopped and accurately reported the remaining failure.
No renderer upgrade or vendor-runtime edit was attempted. A recursive comparison
of the installed Archify upstream directory against the source matched exactly;
the source upstream directory also has no diff from the candidate's base commit.

Final retained outputs in the disposable workspace:

| Output | SHA-256 |
| --- | --- |
| `artifacts/account-request-path.sequence.json` | `f9cdda4d0fcac50a840ab56d682698a8cdf415dbe3459fd1ca671df0d28452f1` |
| `artifacts/account-request-path.html` | `6708e0ca53deba7f93f426059e1414bc7b06d9306923c215dbd43554e29e436f` |
| `artifacts/account-request-path.visual-check.json` | `6f98a07cf4974125bfc13cda36533c72da3ddac4b7a6429e4856b18fddca77e1` |

The receipt records `ok: false`, `status: fail`,
`evidenceKind: automated-browser`, and `visualReview: pending`. Its
`viewer/viewport-overflow` diagnostics report no horizontal overflow and these
vertical dimensions in both light and dark themes:

| Viewport | Document scroll height |
| --- | --- |
| 1440 x 900 | 1291 |
| 1600 x 1000 | 1425 |
| 1920 x 1080 | 1425 |
| 2048 x 1320 | 1443 |

The coordinator separately inspected
`artifacts/account-request-path.visual-check.1440x900.light.png`: the lower
delivery/worker region extends below the viewport. This is visible clipping,
not just a conservative threshold. That single-capture inspection is not a full
perceptual review of every state. The artifact still marks queue delivery as
unimplemented; it does not prove real queue behavior.

### Agent-facing writing

The request selected `/writing-for-agents` to remove an always-read-all-references
rule and promotional prose from `docs/agent-guide.md`, while preserving its
normalization command, completion condition, release-publication boundary, and
reference target. The write scope was that one document.

Observed native tool events loaded `writing-for-agents` (3,955 characters) and
Poteto `unslop` (2,727 characters), read `docs/agent-guide.md` and
`docs/references/release.md`, and performed one approved replacement. The result
starts with **Load only the instructions relevant to the task** and keeps:

- `node --test tests/account.test.mjs`;
- completion only when that command passes and the path queues normalized IDs;
- the relative `references/release.md` pointer for release preparation; and
- a separate explicit request for publication.

`test -f docs/references/release.md` succeeded. An attempted `git diff --check`
returned 129 because the disposable consumer has no Git repository. Kiro then
reran the direct link check and reported the Git limitation accurately. The
coordinator inspected the final text and confirmed the reference file was
unchanged. The edited guide's SHA-256 is
`542d4845d688cea193f11f440cb6b32bf4c7af233d71df336491293edea30268`;
the reference retains
`c8b262c84e3ddc4d8b1407472dd6ecee0239630f2c80052a8dd959f0bcf176ac`.

### React prop narrowing

The request selected `/narrow-react-prop-types` for `ui/SaveButton.tsx` and
`ui/SaveButton.stories.tsx`, with `ui/App.tsx` as the wired fixture caller.
Kiro loaded the skill through native context disclosure (1,882 characters),
searched `SaveButton` uses under `ui/**/*`, and read all three files plus the
existing compiler harness and JSX declarations. The search found the component,
one wired caller, and one support story.

Only the component and story changed. `title?: string | null` became
`title: string`, `onSave?: () => void` became `onSave: () => void`, and the
component now uses its required props directly. The story supplies the same
valid prop shape as the wired caller. Kiro ran `node typecheck.mjs` successfully;
the coordinator independently reran it and inspected both final files.

| File | Final SHA-256 | Change |
| --- | --- | --- |
| `ui/SaveButton.tsx` | `4cc3f357d2e58d61bfbfd49c1a98ee96d5fec63310f410500a66fe64debf8094` | Narrowed |
| `ui/SaveButton.stories.tsx` | `ccd3c07361fde3eb5cf120e149418f665eaca6edf8eaf7d07f70debfdc54b70a` | Adapted |
| `ui/App.tsx` | `7b7e7e53ed5dd7e984586993e2e5991f42e9f9a08d5fdfef165395df40844406` | Unchanged |
| `ui/jsx.d.ts` | `047d80c6bb1ed9297167922b6c7a05f1444dc9d85938311b46ad3f22614631e2` | Unchanged |
| `typecheck.mjs` | `b27c326966740c026dad0d28cdc74ca60914b9e72d069c3587c6f6100b8ec3a7` | Unchanged |

This proves the method on the small fixture and installed compiler. It does not
claim a browser-driven React application test or coverage of a real product's
call graph. No formatter or linter was installed to extend the fixture.

### Reusable local loop

The request selected `/build-iterated-agentic-loop` to implement the already
designed label loop. It authorized only `labels-loop.mjs`,
`.kiro/skills/trim-label/SKILL.md`, and one trim in `data/labels.json`. It selected
no GitHub Actions profile and prohibited workflows, schedules, extra model
sessions, installs, network calls, commits, and publication.

Kiro loaded the builder through native context disclosure (4,583 characters),
read `.kiro/skills/build-iterated-agentic-loop/references/control-loop.md`,
`AGENTS.md`, and `data/labels.json`, then searched the fixture for existing
automation. It created the two requested files. The script contains read-only
sensor, controller, and verifier commands; Kiro remained the actuator.

The actual commands were:

```sh
node labels-loop.mjs sensor --file data/labels.json
node labels-loop.mjs controller --file data/labels.json
# Kiro then replaced exactly one value in data/labels.json.
node labels-loop.mjs verify --file data/labels.json
node labels-loop.mjs controller --file data/labels.json
node --check labels-loop.mjs
```

Before the edit, the sensor reported `eligible: ["alpha"]`, `invalid: []`, and
`setPoint: false`; the controller returned `next: "alpha"`,
`terminal: "candidate"`, and `maxAttempts: 2`. An approved file replacement
changed `alpha` from `"  Alpha "` to `"Alpha"`. The keys and `beta: "Beta"`
were preserved. The verifier then returned `eligible: []`, `setPoint: true`,
and `terminal: "no-op"`; the controller also returned `next: null` and `no-op`.
The syntax check printed success. Its combined shell command suppressed a Git
status error because the fixture is not a Git repository; that is not Git proof.

The useful path does not establish a complete reusable control loop:

- `MAX_ATTEMPTS = 2` is emitted as metadata. No attempt counter or rejection
  after two attempts is implemented. The skill states the bound in prose, but
  the generated script does not enforce it.
- The ordinary verifier checks the current set point, not preservation against
  the pre-edit data. Its optional `--baseline` branch chooses the permitted
  changed key from the post-edit eligible list. After a successful trim that
  list is empty, so the valid change is rejected.
- Kiro's final answer named malformed JSON, invalid labels, write failures, and
  baseline key/value rejection as untested. It did not identify the defects
  above. No model repair round followed.

The coordinator reproduced the baseline defect without changing any file:

```sh
node --input-type=module -e 'import {spawnSync} from "node:child_process"; const r=spawnSync(process.execPath,["labels-loop.mjs","verify","--file","data/labels.json","--baseline","/dev/stdin"],{input:JSON.stringify({alpha:"  Alpha ",beta:"Beta"}),encoding:"utf8"}); console.log(JSON.stringify({status:r.status,stdout:r.stdout,stderr:r.stderr}));'
```

It returned `status: 1`, empty stdout, and
`unchanged value changed: alpha`. This is a defect in the generated disposable
output, not a change to the bundled skill or product runtime. Failure-path and
restart-safe automation acceptance remain unproven.

| File | Final SHA-256 |
| --- | --- |
| `labels-loop.mjs` | `67855b3f620f819f3ad053cc666b4f2a4ee5bf359f794986608e5d2a511d144e` |
| `.kiro/skills/trim-label/SKILL.md` | `514ca511c3f8e78ebac61f654afb8c76b57433ff804b5bed64d6f32a4f49dd08` |
| `data/labels.json` | `aaf8c94c420cccc494381e765b2d5ce14e3c49cae134e9142fa6c24c2a6942e5` |

## Final readbacks and limits

The coordinator reran `node typecheck.mjs` and
`node --test tests/account.test.mjs`: the compiler passed and the one account
test passed. Final SHA-256 comparisons of the 14 original fixture files show
only the four authorized changes: the agent guide, component, support story,
and label data. The account implementation, account test, wired React caller,
compiler harness, JSX declarations, release reference, README, and AGENTS file
are unchanged. Inventory shows only the requested diagram artifacts and local
loop files added during model work, with no workflow or schedule.

The final reviewed setup dry run used the initial setup command with
`--dry-run --output json`. It returned `ok: true`, no conflicts, no pending
updates, and no stale managed files. All managed assets matched the source;
only the generated discovery receipt would refresh to include the new
user-owned `trim-label` skill. The dry run did not perform that write.

This smoke lane changed only this report in the shared worktree. The source
owner's separately authorized design-skill correction is documented above.
No model session remains running. The retained disposable files support the
observations, including failures; none is presented as a release gate or a
production-ready automation. The bundled `unslop` pass kept this report's
claims, caveats, and failure evidence intact while removing filler.
