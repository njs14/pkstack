# Fable 5.1 review — round 5

## Execution metadata

- Candidate commit: `491bfdafc94832c6624ed86051955b1067245979`
- Candidate tree: `e314bd4ab33e492b905a080b43c4ea8bdfba6828`
- Reviewer: Claude Code 2.1.258, canonical model `claude-fable-5-1`, caller-requested
  effort `xhigh`
- Session: `a92de2f4-44de-4479-bd84-1e941aba70b0`
- Isolation: chmod-read-only `git archive` at
  `/private/tmp/pk-stack-review-snapshot.DZziF6`
- Available tools: `Read`, `Glob`, and `Grep`; MCP, browser, shell, writes, slash commands,
  persistence, web search/fetch, and subagents disabled
- Review-contract SHA-256:
  `20552e694c32fbff4480f45d7fe7763918c05f97cc97d7474fde7a82f3ba8d5f`
- Raw owner-only envelope:
  `/private/tmp/pk-stack-review-controls.t5zL49/fable-envelope.json`, SHA-256
  `411896794d3070297de095b2a918f92488bbb5ca28de6d6c49bf1466d4c0c193`
- Extracted raw report SHA-256:
  `39e3dc43843da084292a6cb55d420cda0877db4d2d58ae778aee57186e5a34f0`
- Observed work: 951.501 seconds, 162 turns, 51,177 Fable thinking tokens, and reported
  cost approximately $23.7897
- Envelope validation: terminal reason `completed`, stop reason `end_turn`, zero web-search,
  zero web-fetch, and zero subagents
- Verdict: `REQUEST CHANGES`
- Material unresolved: 3

The provider envelope identifies the substantive reviewer as canonical `claude-fable-5-1`. It
also reports a small internal `claude-haiku-4-5-20251001` companion usage of 917 input and 16
output tokens; this record does not hide that auxiliary service usage or reinterpret it as the
reviewer. Effort is bound by the caller's exact `--effort xhigh` launch argument because the
result envelope does not independently expose an effort field.

The raw reviewer output is untrusted evidence. The findings below are a normalized, source-checked
record and become acceptance work only after Codex reproduces their premises.

## Material findings and acceptance tasks

### FBL-037 — MEDIUM — missing self-maintenance campaign evidence

The accepted upstream pin and transition ledger prove that one 27-path fast-forward was applied,
while stale acceptance-ledger text says it remains unaccepted. The reviewed tree lacked a bounded
campaign record tying the ignored feature-backed goal's initial drift failure, semantic path
dispositions, regeneration/accept transaction, and later passing attempt to those artifacts.

Acceptance task:

1. Commit `reviews/pk-stack-maintenance-campaign.md` and JSON bound to the exercised repository
   state, exact goal ID and contract digest, attempt results, transition identity, inventory digest,
   all 27 path dispositions, actual A/B/C counts, and final no-drift proof.
2. Label any command/output detail reconstructed from terminal effects rather than retained raw
   output; do not invent a Kiro session record.
3. Update `SELF-001`, `SELF-002`, and `SELF-011` to the resulting truth.
4. Add an executable regression binding the campaign JSON's transition/inventory/disposition
   fields to the live manifest and latest ledger entry.

The reviewer's prose suggested counts `22/3/1`, which sum to 26. The authoritative transition
contains 27 unique paths and actual counts `A=23`, `B=3`, `C=1`; remediation must follow the
machine record rather than the arithmetic typo.

### FBL-038 — MEDIUM — trusted finalizer exposed to model-writable Git metadata

The Kiro repair step operates in a writable Git checkout. Changed-path validation cannot see
`.git`, yet the first secretless finalizer action invokes Git. A model-written hook or config such
as `core.hooksPath`, `core.fsmonitor`, or `diff.external` could therefore execute in the trusted
runner context; the profile's `.git/**` write denial was the only current control and had not yet
been proven on a hosted runner.

Acceptance task:

1. Make every trusted Git invocation ignore repository/global/system hooks and execution-bearing
   config, including empty hooks, disabled fsmonitor, disabled external diff, and `--no-ext-diff`.
2. Before the model step, record a bounded, canonical integrity snapshot of `.git/config`,
   `.git/hooks`, and `.git/info`; before any closing Git command, refuse any change, unsafe file
   type, or added entry.
3. Add regressions that plant a post-index hook and config mutation and prove failure occurs before
   `git add` or any hook execution.
4. Execute the exact committed hosted Kiro permission smoke and retain a bounded record showing
   `.git/**` denial sourced from the agent profile.

### FBL-039 — MEDIUM — stale executable identities, counts, and status narrative

The primary validation report still called historical commit `cb2cb09` current, omitted the newer
final Floci/Kiro campaigns, and retained obsolete literal bootstrap/doctor counts. The acceptance
ledger likewise called the shipped agent-discovery and full-skill work in progress, and the root
README linked only the historical Kiro campaign.

Acceptance task:

1. Distinguish historical `cb2cb09`, final Floci executable `28b9182`, Floci evidence carrier and
   fresh Kiro executable `2a1afb8`, round-5 review target `491bfda`, and each later evidence carrier.
2. Replace brittle or incorrect receipt/doctor counts with values derived from the current
   artifacts, or omit literals where they do not add value.
3. Update `KMG-008` and `SKL-001` through `SKL-010` to their actual closed/pending dispositions.
4. Point the README at `final-floci-campaign.*` and `final-kiro-v3-campaign.*`.

## Non-material findings

- `FBL-040` — LOW: the plugin URL names the authorized private repository before it is created.
  Creating and verifying that exact repository resolves the sequencing concern.
- `FBL-041` — LOW: the fresh Kiro JSON included a null carrier field and omitted whether a source
  write preceded attempt 2. Remove the misleading field or populate it consistently and add the
  attempt-order key.
- `FBL-042` — LOW: whole-project `docker compose down` could theoretically include a foreign
  container carrying the same Compose project identity. Narrow removal to exact claim-bound
  objects or fail closed on every project member, and add a planted-foreign-member regression.
- `FBL-043` — LOW/external: representative skill routes, private-repository publication, and
  hosted cadence/credential/permission evidence remain release gates.
- `FBL-044` — LOW: exact equality on the Fable `modelUsage` key set could reject a legitimate
  pinned-SDK envelope containing a versioned internal companion model. Validate canonical Fable
  authority without admitting arbitrary substantive reviewer models, using a real envelope shape.
- `FBL-045` — LOW: a root-controller test copies a draft rule into a stub; bind it to the real
  vendored implementation or assert exact text equivalence so the fixture cannot drift silently.

## Proven strengths

Fable independently retained the earlier accepted conclusions for requested-versus-effective
Floci security; frozen crash-resumable teardown; claim-bound outer/task objects; bounded process
execution; append-only deployment identity; read-only collision inventory; command-level negative
verification; reachable-to-discard recovery; strengthened idempotency; external judge closure;
exact source/runtime packaging; Kiro current-session fail/repair/pass behavior; feature CAS and
evidence-ledger bounds; upstream transition validation; model guidance; full 48/47/48 skill
distribution; Kiro 2.21 agent discovery; GitHub candidate/merge identity; PK-Stack naming; and the
potato-ghost/OKF artwork.

The read-only reviewer could not itself run SHA-256. It instead checked consistency among the
committed final manifest, Kiro summary, and prior map and did not reopen FBL-029. Codex retains the
separate successful frozen-hash invocation as the executable proof.

## Acceptance decision

`REQUEST CHANGES`. FBL-037, FBL-038, and FBL-039 are explicit remediation gates. The next
candidate must receive a new Fable 5.1 `xhigh` review after all material fixes and their tests are
committed.

`MATERIAL_UNRESOLVED: 3`
