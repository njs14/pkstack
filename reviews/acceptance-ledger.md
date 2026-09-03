# Acceptance ledger

This ledger records implementation status; it is not itself acceptance evidence. Fable must
re-evaluate every material item from the immutable candidate source and tests.

## Original local pre-Fable criteria

- `LOCAL-001` — Isolate every Compose/Docker operation from ambient project, file, context, host,
  proxy, AWS, and uv configuration. Status: implemented and covered by hostile-environment tests.
- `LOCAL-002` — Inventory every deterministic AWS/Docker target before mutation and require exact
  claim ownership. Status: implemented, including structured not-found handling.
- `LOCAL-003` — Bind build inputs, image IDs, task definitions, services, tasks, containers, and
  the selected Docker daemon. Status: implemented and live-proven.
- `LOCAL-004` — Narrow DynamoDB idempotency classification and recover SQS publish failures.
  Status: implemented with deterministic regressions.
- `LOCAL-005` — Make worker claim/complete processing concurrency-safe. Status: implemented with
  lease/race/fault tests.
- `LOCAL-006` — Validate exact bounded S3 object content and metadata. Status: implemented and
  live-proven.
- `LOCAL-007` — Describe tenant behavior only as tenant-key partition separation. Status:
  implemented across source, feature contract, tests, and docs.
- `LOCAL-008` — Bound JSON failures and run through committed locks without ambient uv config.
  Status: implemented; the pre-Python launcher limitation remains documented.
- `LOCAL-009` — Minimize and lock the build context; prove non-root/no-mount task identity and
  report Floci security propagation honestly. Status: implemented and live-proven.
- `LOCAL-010` — Exercise Cyclopts feature generation/goals and distinguish optional OKF. Status:
  implemented; isolated goal passed on attempt 2 and `okn` absence remains an explicit warning.
- `LOCAL-011` — Move acceptance judging outside the mutable checkout and bind all protected
  controls/source. Status: implemented and live-proven by the external judge.
- `LOCAL-012` — Account for every current-claim artifact with recoverable exact cleanup. Status:
  implemented and live-proven across two generations.

## Fable round 1 material criteria

Fable 5.1 reviewed commit `0b000d359b99f34ee5001088548ca872322e734a` at max effort and
returned `REQUEST CHANGES` with eight material findings. The normalized report is
`reviews/fable-round-1.md`.

- `FBL-001` — Replace the impossible Floci effective-security gate with honest requested-versus-
  effective evidence while retaining non-root/no-mount/identity gates. Local disposition:
  implemented, regressed, and live-proven in `live-final-902`.
- `FBL-002` — Persist a frozen crash-resumable teardown plan and exact postconditions. Local
  disposition: implemented; hard exits inside every destructive phase and terminal unlink are
  covered, and the fresh live teardown completed all eight phases.
- `FBL-003` — Bind the singleton Floci/network to the opaque run claim and refuse foreign outer or
  task containers. Local disposition: implemented and tested.
- `FBL-004` — Replace truncatable global inventories and unbounded command capture. Local
  disposition: filtered/exact queries plus selector-driven bounded stdout/stderr handling,
  process-group termination, and regressions are present.
- `FBL-005` — Retain all repeat-deploy image/task-definition artifacts. Local disposition: schema
  v2 has a strict append-only ledger and active pointer bound to exactly one complete operation;
  the live run retained and removed both generations.
- `FBL-006` — Complete read-only collision inventory before provisioning. Local disposition:
  implemented; the S3 create/tag gap also has a durable narrowly scoped recovery intent.
- `FBL-007` — Add deterministic risky-branch tests and repair vacuous tests. Local disposition:
  the round-1 risky branches are covered, but Fable round 2 found that the orchestration-level
  verifier proof remained incomplete; see the narrowed round-2 criterion below.
- `FBL-008` — Prove controller generation/transitions and one real same-session Kiro v3
  fail-repair-pass run. Local disposition: controller source/vendored/isolated proof is complete,
  and the selected-profile Kiro campaign passed locally. Fable has not yet reviewed its committed
  evidence, so this criterion is not independently accepted.

## Fable round 2 criteria

Fable 5.1 reviewed commit `2fcacc054fd62e55a8d57107d35b73e3d1d1582c` at max effort and
returned `REQUEST CHANGES` with three material findings. The normalized report is
`reviews/fable-round-2.md`.

- `FBL-007` — Make the verifier-order regression reach both container proofs and add deterministic
  command-level negatives for tenant partition separation, duplicate API identity/count, duplicate
  ETag stability, and current-invocation DLQ identity. Local disposition: implemented in the
  snapshot-local suite; each business negative now proves that post-business identity reproof is
  not reached.
- `FBL-008` — Add in-snapshot controller transition/policy/bootstrap regressions and retain one real
  selected-profile current-session Kiro campaign. Local disposition: 11 hermetic controller tests
  cover start, same-goal fail/pass, exhaustion/resume, clear policy, exact verifier policy and six
  unsafe rejections, plus bootstrap idempotence and receipt integrity. The one-process Kiro
  campaign then passed the same feature contract on attempt 2 of 4 after one real fail, one native
  verifier subagent, one source repair, and one redeploy. See `reviews/kiro-v3-campaign.md`.
  Fable must still review that evidence commit before this criterion is accepted.
- `FBL-021` — Support an explicit durable reachable-to-discard transition when a previously frozen
  reachable teardown loses Floci. Local disposition: implemented as a canonical hash-bound one-way
  transition that preserves the prior plan, completed prefix, and all frozen targets; reachable
  refusal, every prior prefix, crash/retry, tamper, and no-reinventory/no-AWS paths are regressed.

Fable's low-severity round-2 findings were also evaluated before the next live proof:

- `FBL-022` — fixed cleanup error precedence around the temporary verifier container.
- `FBL-023` — removed the unreachable empty-socket compatibility path.
- `FBL-024` — pinned Hatchling exactly; an adversarial check showed that uv 0.12.9 ignored the
  proposed build-constraint mechanism under this `uv run --no-config` path, so no inert hash claim
  is shipped.
- `FBL-018` — derive the complete hash-bearing runtime export directly from `uv.lock`.
- `FBL-025` — filter stale-recovery container discovery server-side and reject unexpected names.
- `FBL-026` — intentionally retained the judge's fail-closed bytecode rejection and made that
  executable-input boundary explicit in tests and documentation.
- `FBL-027` — inspect or bounded-pull the exact digest-pinned Floci image before claiming a run,
  reprove its image ID, then start Compose with `--pull never`.

## Post-round-1 Codex preflight criteria

- `PREFLIGHT-001` — Require effective-owner, exact 0700 `.lab-state` before every state operation.
  Status: implemented and tested.
- `PREFLIGHT-002` — Reject malformed Docker/claim/active identities and cross-wired operations.
  Status: implemented and tested.
- `PREFLIGHT-003` — Recover a hard exit between S3 bucket creation and tagging from durable exact
  intent only. Status: implemented and tested through down retry.
- `PREFLIGHT-004` — Make state-less image cleanup converge after one tag was removed. Status:
  implemented and tested.
- `PREFLIGHT-005` — Bound child stdout/stderr during execution and terminate the full process
  group on overflow/timeout. Status: implemented and tested.
- `PREFLIGHT-006` — Never interpret an unexpected structured ECS describe/list failure as resource
  absence during collision checks, deployment, verification, or teardown. Status: implemented
  through one shared fail-closed parser and key/path regressions.
- `PREFLIGHT-007` — Bind the direct Compose definition at the original `up` claim, carry that digest
  into the frozen teardown plan, and refuse both first-pass and resumed Compose mutation after
  drift. Status: implemented and tested before external inventory/execution.
- `PREFLIGHT-008` — Preserve recovery compatibility with schema-v2 teardown journals written before
  transition metadata existed, without admitting any other nested state shape. Status: implemented
  and tested through legacy load, transition, checkpoint, reload, and extra-field rejection.
- `PREFLIGHT-009` — Authorize emulator discard only for typed transport unreachability; a responding
  HTTP endpoint, malformed response, redirect, permission failure, or ambiguous URL failure must
  refuse before plan freeze or transition. Status: implemented and tested on both entry paths.
- `PREFLIGHT-010` — Ship one canonical installable Agent Plugins Power alongside the lab rather
  than presenting generated `.pstack` cache as source authority. Status: implemented at
  `powers/pk-stack/`; manifest/package checks, fresh Power-local setup, idempotence, doctor, and
  byte-for-byte source/generated parity are executable regressions.
- `PREFLIGHT-011` — Prevent unpublished draft feature contracts from being executed by `feature
  verify` or bound into a goal. Status: one shared ready-feature resolver now fails before command
  execution or goal-state creation; the canonical source and generated controller tests cover
  draft rejection and published acceptance.

The pre-combination `live-council-902` campaign subsequently passed two deployments, the
then-current business verifier, the owner-controlled external judge, all eight normal teardown
phases, and a full foreign-image noninterference comparison. It ran on the `d9b1e0d` source line,
so it is historical evidence rather than exact-tree proof for the later combined candidate. Exact
identifiers and commands are in `docs/validation-report.md`.

## Fable round 4 criteria

Fable 5.1 reviewed commit `ced867c4814ef722441215bd4d33ac30769868ec` at max effort and
returned `REQUEST CHANGES` with two material findings. The normalized report is
`reviews/fable-round-4.md`.

- `FBL-028` — Make `api_idempotency` an observed contract rather than an asserted summary:
  require the duplicate response marker/status/original ID and bind the completed row to the exact
  idempotency key, one attempt, and confirmed enqueue. Add the named command-level negative paths,
  prove failure precedes post-business reproof, and pass both the live verifier and external judge.
  Local disposition: **closed locally** on executable commit
  `cb2cb0905687c3e94e539333d8945c37109f6189`. Implementation and named negative/consumer
  regressions pass; the fresh `fable-r5-902` verifier and frozen external judge also passed the
  strengthened contract. Fable must independently accept this disposition.
- `FBL-029` — Bind final live evidence to the exact remediated combined commit. Run a fresh
  `doctor -> up -> deploy -> deploy -> verify -> evidence -> down` lifecycle with the
  owner-controlled external judge, two retained generations, explicit source identity, complete
  cleanup, and foreign-image noninterference. Local disposition: **closed locally** by
  `fable-r5-902` on executable commit `cb2cb0905687c3e94e539333d8945c37109f6189`, tree
  `c28e71a050185f19befb3832e865c4e54f2bcf03`; see `reviews/fable-r5-live-proof.md` for the two
  generations, frozen 14-path map, judge result, teardown, and postconditions. Fable must
  independently accept this disposition. `live-council-902` and `kiro-v3-accept-902` remain honest
  earlier-source evidence and are not substituted for this gate.

Fable's low-severity round-4 findings are retained as explicit hardening work:

- `FBL-030` — add root generated-controller subprocess regressions for both draft rejection paths.
  Local disposition: **closed locally**; the real generated wrapper rejects both paths with
  structured `FeatureMapError` output before the sentinel executes or goal state exists.
- `FBL-031` — disclose the committed Kiro log's internal ACP/Autopilot labels and the absence of
  discrete write/deploy records in that bounded projection. Local disposition: **closed locally**
  through explicit documentation; no stronger committed source-log projection is claimed, so the
  raw-typescript and missing-PID limitations remain advisory evidence boundaries.
- `FBL-032` — reject any extra task-container network and emit the observed network identity.
  Local disposition: **closed locally**; the exact observed network set must equal the singleton
  lab network, the observed key is emitted, and an extra-network regression fails closed.
- `FBL-033` — pass one real successful command-verifier payload through the judge, including a
  maximum-length run ID and the 8,192-byte bound. Local disposition: **closed locally**; the
  successful command-level harness payload crosses the real judge consumer and its
  newline-terminated UTF-8 serialization remains within the judge's bound.
- `FBL-034` — correct historical/current evidence language and Docker-label ambiguity; keep the
  not-yet-created private repository explicit; align or document the nested build-backend policy.
  Local disposition: **closed locally**; documentation is clarified and the canonical Power pins
  Hatchling 1.32.0. Private publication remains intentionally sequenced after council acceptance
  and is not claimed early.
- `FBL-035` — document the manual exact-digest Floci image-pull fallback while retaining the
  automatic preflight's fail-closed diagnostic match. Local disposition: **closed locally** and
  documented.
- `FBL-036` — document that externally deleting a journaled completed-generation image is outside
  same-digest recovery and requires a new source digest/deployment or teardown/new run. Local
  disposition: **closed locally** and documented.

## Self-maintenance and release criteria

The following criteria extend the original port with the user's requirement that PK-Stack use its
own controller and workflow semantics to remain current without routine hand maintenance. They are
local implementation claims until the exact final commit passes the council and GitHub-hosted
proofs named below.

- `SELF-001` — Re-prove every configured upstream pin and current ref through a fixed-origin,
  bounded, read-only client. Bind each accepted fast-forward transition to its exact prior/new
  commit and subtree identities, exhaustive changed-path inventory digest, and one reviewed A/B/C
  disposition per path. Reject pin-only edits, malformed or incomplete GitHub responses,
  cross-boundary rename confusion, replay, and generated-copy drift. Status: implemented with a
  strict append-only ledger, full ordered provenance markers, latest-transition remote reproof,
  and canonical/generated parity tests; the first real 27-path transition remains to be accepted
  by the current goal.
- `SELF-002` — Keep self-maintenance inside one immutable feature-backed `projectctl` goal. Record
  exactly one failing pre-edit attempt for a new goal, retain four bounded repair attempts, and
  resume an already-attempted goal without consuming another attempt before a meaningful change.
  Status: implemented and regressed; the real current-upstream goal remains active after its
  required attempt-1 drift failure.
- `SELF-003` — Run the primary updater on a cadence with checksum-pinned Kiro CLI 2.21.0, Sol at
  `max`, no ACP default, a minimal CI-only agent, and no shell/network/MCP/subagent authority in the
  model step. Expose `KIRO_API_KEY` only to the four bounded repair steps, destroy its isolated
  runtime before candidate code or secretless verification, and never fall back to another model
  automatically after a Kiro failure. Status: implemented in the conventional Kiro workflow and
  structural tests; a private-runner smoke remains required.
- `SELF-004` — Treat upstream patches and model output as untrusted data. Permit automatic author
  edits only on the declared bounded Power surface, keep controller/tests/CI/feature contracts
  immutable, and let a secretless base-commit finalizer alone regenerate, test, advance the pin,
  and package the candidate. Every candidate, including any operational skill or agent-definition
  change, must receive a fail-closed Fable 5.1/xhigh verdict bound to the exact base SHA, head SHA,
  content digest, patch digest, and trusted model execution metadata before merge. Status:
  implemented and under final
  adversarial workflow review; a repository Claude credential is an external prerequisite for
  hands-off operational updates and must never be copied from local session state.
- `SELF-005` — Publish only one exact, non-draft, bot-owned candidate commit; re-run the same
  deterministic gate on base and head, rebind mergeability and all digests immediately before
  squash merge, and safely replace an exact bot-owned stale PR after the default branch moves.
  Human or ambiguous PRs must never be closed or adopted. Status: implemented with mocked policy
  regressions; live GitHub behavior remains required.
- `SELF-006` — Keep the GitHub Agentic Workflows/Copilot path manual-only and independently locked,
  with the same immutable candidate contract. It may assist recovery but must never silently
  replace Kiro or weaken the Fable gate. Status: implemented as a manually dispatched fallback;
  compile and action validation remain release gates.
- `SELF-007` — Create only the authorized private `njs14/pk-stack` repository, configure the Kiro
  secret without printing it, verify repository/action privacy and permissions, and run a hosted
  workflow proof. Status: pending council acceptance and publication.
- `SELF-008` — Ship a documented, decodable RGBA potato-ghost mascot with an OKF scholar's
  mortarboard, transparent outer corners, and an honest visual-reference notice. Status:
  implemented; the asset checksum and decoded alpha behavior are regressed.
- `SELF-009` — Bind the candidate gate and final merge to the exact authorized Kiro workflow name,
  provider, workflow path, source-run ID, base, repository, and branch
  `pk-stack-upstream/kiro-<source-run-id>`. A fallback run or a different Kiro run must not adopt a
  surviving candidate. Status: implemented with exact resolve/merge revalidation and cross-run /
  cross-provider negative tests.
- `SELF-010` — Make the hosted Kiro permission smoke exercise the exact immutable
  `pstack-maintainer` permission matrix rather than a representative surrogate. Every allowed class
  and representative overlapping protected path must be checked, with exact policy-denial events
  and unchanged protected hashes. The production and fixture agents must also carry the exact
  `toolsSettings` discovery contract, appear in a sterile V3 `agent list`, and fail on any default-
  agent fallback. Status: closed locally after a live negative exposed the missing discovery field;
  29 guard tests and sterile no-model production/fixture discovery now pass. Hosted execution
  remains a publication gate.
- `SELF-011` — Bind each upstream source to exactly one machine-validated canonical genesis marker
  before its ordered transition markers. Reject missing, changed, duplicate, extra, malformed, or
  reordered genesis/transition evidence before network access, and preserve genesis through accept
  and recovery. Status: implemented; 87 focused upstream tests, 604 canonical tests, parity, and a
  live pin re-proof passed while the real 27-path transition remained unaccepted.
- `SELF-012` — Demonstrate the committed weekly cadence, credential smoke, exact-authority
  permission smoke, authenticated upstream check, and one hosted no-op or drift lifecycle in the
  authorized private repository. Status: pending publication; local static proof cannot substitute
  for GitHub-hosted liveness.

## Kiro model and methodology criteria

These criteria come from the requested Fable 5.1 peer audit of the complete 2026-09-02 Kiro
documentation index, the OpenAI/AWS GPT-5.6 launch guidance, the installed CLI, and the current
repository. The Fable pass was substantive and model-attested; its attempted short reconciliation
hit the Claude session limit, so Codex rechecked every finding against the live worktree and retained
the material items below as release criteria.

- `KMG-001` — Remove Cursor-era fixed-model roles from normal PK-Stack operation. Canonical and
  generated custom agents must omit `model`; interactive instructions must inherit the user's Kiro
  choice and describe Auto, Sol, Terra, and Luna by task rather than pretending one model is always
  correct. Status: closed locally with static asset tests and live all-three-model inventory.
- `KMG-002` — Treat GPT-5.6 availability, experimental lifecycle, context, multiplier, and model ID
  as versioned Kiro facts. Preserve a dated documentation/index digest and sanitized live inventory;
  do not turn either into a permanent availability claim. Status: closed locally in
  `reviews/kiro-model-guidance-evidence.json` and the compatibility guide.
- `KMG-003` — State that Kiro effort selection is available in IDE/CLI, not Web; GPT-5.6 supports
  `none` through `max`; higher effort consumes more credits; CLI `/effort` and `--effort` persist;
  and Kiro has no documented `ultra` value. General quick starts must omit Sol/max, while historical
  acceptance commands remain exact. Status: closed locally with focused regressions and an explicit
  reset path.
- `KMG-004` — Incorporate the OpenAI/AWS methodology without inventing proof: native structured
  specs, checkpoint review, and applicable property-based tests may strengthen work, but Kiro's
  current property-testing feature is optional, IDE-only, and evidence rather than formal
  verification. The stored projectctl predicate remains the cross-surface completion gate. Status:
  closed locally and regressed; no property-based campaign is claimed.
- `KMG-005` — Disclose the scoped AWS processing boundary: GPT-5.6 is US-served, experimental
  requests may be processed in commercial AWS Regions worldwide, global routing does not change the
  storage Region, and only classifier-flagged OpenAI GPT traffic may be retained up to 30 days in
  the inference Region. Do not imply any PK-Stack traffic was flagged or retained. Status: closed
  locally against the hashed Kiro data-protection page and focused tests.
- `KMG-006` — Before each hosted repair attempt spends a turn, use the isolated pinned Kiro binary
  to list models and strictly fail closed unless the reviewed Sol contract is present (exact ID,
  experimental lifecycle, 272000 context, 2.4 multiplier). Do not print the key, consume a fifth
  credential scope, or silently substitute a model. Status: closed locally with a live Kiro 2.21.0
  inventory acceptance and eight validator/ordering regressions; hosted proof remains required.
- `KMG-007` — Keep current native `/goal` documentation separate from installed-runtime evidence.
  The sanitized CLI 2.21.0 V3 record must show `/goal clear` became ordinary prompt content while
  `/quit` remained recognized, scope that observation to the tested environment, and retain
  `/verified-goal` as an independent current-session projectctl seam. Status: closed locally in
  `reviews/kiro-v3-native-goal-probe.json` and focused tests.
- `KMG-008` — Treat `kiro-cli agent validate` as schema evidence, not discovery evidence. On the
  pinned Kiro 2.21.0 runtime, every shipped agent must both validate and appear by exact name in a
  sterile `agent list`. Until a version bump disproves the live loader quirk, every non-primary
  profile carries an inert empty `toolsSettings` object and the primary profile carries only its
  documented subagent settings; all filesystem/shell authorization remains in `permissions.rules`.
  Document this as a tested 2.21.0 compatibility sentinel, not a general V3 requirement, and do not
  overstate IDE or Crew permission parity. Status: remediation in progress after controlled
  field-present/field-absent probes exposed three silently undiscoverable helper agents.

## Upstream skill-parity criteria

These criteria close the catalog gap found during final acceptance. Consolidating shared behavior
is desirable, but a workflow is not considered ported merely because some of its ideas appear in a
different skill.

- `SKL-001` — Inventory every top-level upstream pstack skill at both the accepted pin and the
  reviewed current ref, including exact names and source identities, plus every directly referenced
  playbook, template, helper, or reference that is load-bearing for the routed workflow. Give every
  entry exactly one machine-readable disposition: direct Kiro port, discoverable compatibility
  route to a shared Kiro-native core, exact native-Kiro replacement, or explicit exclusion with a
  narrow rationale. Reject missing, duplicate, unknown, or stale catalog entries. Status:
  implementation in progress.
- `SKL-002` — Preserve an invocable Kiro skill under the familiar upstream name for every
  user-meaningful workflow, even when it is a thin DRY route to consolidated instructions. A prose
  crosswalk alone is insufficient, and the upstream workflow itself—not its title or description—is
  the semantic source of truth. Preserve its load-bearing sequence and referenced contracts before
  translating only Cursor/runtime-specific seams. Native replacement is allowed only when the named
  route clearly teaches the user how to invoke the equivalent Kiro primitive; exclusions are
  limited to non-workflow packaging or unsafe/inapplicable runtime machinery. Status:
  implementation in progress.
- `SKL-003` — Adapt every routed skill to PK-Stack's surface contract: current Kiro agent-session
  language; CLI V3 and IDE Agent Focus as first-class surfaces; Crew compatibility; Web support by
  design but untested; inherited model and effort; and no Cursor Task API, fixed model, ACP default,
  Graphite requirement, watcher daemon, destructive worktree cleanup, or unreviewed external side
  effect. Status: implementation in progress.
- `SKL-004` — Package and generate the complete routed catalog without drift across the canonical
  Power, `.kiro`, and projectctl distribution. Tests must prove exact catalog coverage, route-target
  validity, metadata/schema validity, safe exclusion wording, and canonical/generated byte parity.
  The expected distribution is 48 canonical and projectctl-cache skill directories, with only the
  Power-local `setup-pstack` shim omitted from the 47 live `.kiro/skills` routes. Managed live skill
  paths remain write-denied while a new user-owned skill path falls through to explicit approval,
  so authoring workflows are functional without making generated PK-Stack assets mutable. Status:
  implementation in progress.
- `SKL-005` — Exercise representative direct, consolidated, native-replacement, and excluded routes
  in the final validation campaign, then include the complete catalog and disposition evidence in
  both the Fable acceptance review and Grok sweep. Status: pending implementation and council
  review.
- `SKL-006` — Preserve pervasive upstream activation semantics through supported Kiro mechanisms,
  not unsupported Cursor frontmatter. TypeScript guidance must have a Kiro `fileMatch` steering
  route for `*.ts`/`*.tsx`, and the concise non-slop prose core must be always applied while the full
  skills remain directly invocable. Tests must prove steering frontmatter, generated parity, and
  that normal interactive operation still inherits the selected Kiro model. Status: implementation
  in progress.
- `SKL-007` — Preserve the upstream verification lifecycle in executable projectctl contracts:
  launch, doctor, drive, evidence, cleanup, helpers, sub-features, every user entrypoint, per-entry
  drive recipes, and gotchas. Creation seeds three to five records and proves one representative
  feature; maintenance later drives the complete map with one coordinator, one bounded drift-repair
  retry, explicit verified-unreachable prerequisites, and zero or one separately authorized PR.
  Status: implementation in progress.
- `SKL-008` — Restore the nested reasoning and review contracts rather than collapsing them into
  generic advice: architect's usage-first type/signature/module scaffold, rationale and red flags;
  how's independent critique rubric; interrogate/model-council correctness, code-quality, and lead
  judgment; reflect's three independent lenses plus synthesis; and why's source-category discovery,
  null/gap accounting, incident evidence, and calibrated confidence. Status: implementation in
  progress.
- `SKL-009` — Restore the load-bearing meta-workflows in `figure-it-out`, `no-comments`, `teach`,
  `technical-writing`, `unslop`, and `show-me-your-work`. The last must use a deterministic bounded,
  redacted, append-only evidence lever that is local/uncommitted by default; none may request hidden
  reasoning. Status: implementation in progress.
- `SKL-010` — Preserve all 23 Poteto playbook routes and the reviewed live-current PR semantics:
  `gh` by default with optional Origin, early authorized ready-PR checkpoint, stable patch-ID
  freshness after rebase, and a same-scenario trunk regression lane or absolute budget when trunk
  lacks the feature. Cursor `/goal`, `/loop`, Task metadata, Graphite, watchers, and destructive
  cleanup remain translated or excluded rather than copied. Status: implementation in progress.

## Remaining acceptance sequence

1. Complete the upstream skill-parity phase, self-apply the first reviewed upstream transition, and
   then run every static and packaging gate.
2. Run a fresh exact-final-tree Floci lifecycle and external judge; commit its evidence.
3. Repeat Fable on that immutable snapshot until no material finding remains.
4. Run Grok 4.6 `xhigh` on the Fable-accepted commit.
5. Return any material Grok-driven change to Fable before release.
6. Create and verify the private GitHub repository, secrets, permissions, and hosted workflow.
