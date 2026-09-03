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

## Original-plot re-grounding criteria

The pre-ship audit returned to the original handoff conversation rather than treating accumulated
implementation as the design authority.

- `PLOT-001` — Make Kiro's native Spec, Quick Spec, and Bug Fix workflows the planning spine for
  nontrivial features and defects; reserve a direct default-agent flow for a genuinely trivial
  change with a recorded reason. Status: implemented in the primary router, workflow reference,
  steering, agent prompt, and docs; a native runtime campaign is pending.
- `PLOT-002` — Preserve Kiro ownership of requirements or bug analysis, design, tasks, dependency
  waves, task status, and parallel execution. PK-Stack must not build a second planner/task graph or
  treat a task checkbox as proof. Status: implemented in workflow contracts and structural tests.
- `PLOT-003` — Describe the integration boundary honestly across surfaces. Kiro does not document
  a supported workspace-skill or custom-agent tool for executing client slash commands or changing
  the active workflow, so CLI v3 and IDE use a visible
  same-conversation handoff; Web uses its built-in primary/native Spec picker and remains untested;
  Crew may consume a committed spec through Task Runner without a false built-in-agent/session
  claim. Status: closed locally in skills, architecture, surface docs, and static wording gates;
  Web runtime and Crew end-to-end PK-Stack behavior remain explicitly untested. A separate bounded
  [Crew Nightly smoke](kirocrew-nightly-smoke-campaign.md) passed the signed package's public
  `--version`, `--help`, and `doctor` surfaces but did not open the project or exercise a PK-Stack
  workflow. Its observed global `acp` provider remains Crew-owned transport and does not change
  PK-Stack's normal IDE/CLI v3 entrypoint.
- `PLOT-004` — Provide one thin deterministic spec-to-proof lever. It must require a complete native
  artifact package, prefer a published feature contract, preserve both `spec` and `feature`
  provenance, allow a reviewed command only when no reusable feature applies, and refuse silent
  bridge replacement. The started contract must bind immutable hashes for intent, design, and the
  bridge, reject drift on both sides of proof without consuming an attempt, and leave Kiro's native
  task progress mutable. Status: closed locally as `projectctl goal bind-spec` with focused service,
  race, CLI, immutable-artifact, and generated-controller parity regressions; the real native Spec
  campaign remains the separate `PLOT-008` gate.
- `PLOT-005` — Restore the context-depth ladder as product behavior: use the spec-linked feature map
  first, then canonical `okn` for broader architecture, decisions, concepts, and operations. Native
  `/knowledge` may index the source-controlled Wiki but does not replace it. Status: **closed on
  immutable candidate `8806fa607b991d8e3ca9d004f2724412596f715d`**. The isolated
  [`final-okf-campaign`](final-okf-campaign.md) validated the seven-file linked Wiki with canonical
  `okn` 0.13.0 and returned six provenance-bearing passages within the 900-token budget.
- `PLOT-006` — `knowledge validate` must always retain the PROVE feature-map verdict when canonical
  `okn` is installed; one validator cannot hide failure in the other. Status: implemented with
  positive and negative composition regressions and **closed on immutable candidate `8806fa6`**.
  The strict canonical campaign passed both feature records and the broader OKF 0.2 bundle with 10
  checks, zero errors, zero warnings, and zero issues; its
  [machine-readable record](final-okf-campaign.json) preserves the exact command and result bounds.
- `PLOT-007` — Evaluate `okfcli/okf` rather than silently substituting it. It may be an explicitly
  named advisory CI/SARIF oracle only over a disposable, immutable, symlink-free bundle copy; it
  must never transparently replace canonical `okn` search, query, lifecycle, or safety behavior or
  act as a normative `stale_after` gate. Status: **closed locally** by the bounded
  [comparison record](okf-integration-evidence.md), final architecture/usage guidance, and the
  immutable canonical-runtime campaign. The checksum-verified v0.5.0 re-evaluation confirmed that
  `okfcli/okf` still follows an in-bundle Markdown symlink outside the bundle and now rejects the
  authoritative explicit-offset `stale_after` form, while canonical `okn` rejects the symlink and
  accepts that form. The fresh comparison is worktree architecture evidence. The older immutable
  campaign re-proved canonical `okn`; it did not execute or promote the optional oracle.
- `PLOT-008` — Exercise the final integration through real native Kiro Spec or Quick Spec artifacts,
  return to `pstack`, bind a published feature, and complete a spec-backed verified goal without
  ACP, a nested Kiro process, `/spawn`, or a native `/goal` claim. Status: pending after the final
  executable tree is frozen.

## OKF skill-integration criteria

These criteria adapt the useful workflow concepts from `scaccogatto/okf-skills` without importing
its host-specific runtime or weakening PK-Stack's established KNOW boundary.

- `OKFS-001` — Audit and pin the exact upstream repository commit and `skills/` subtree identity;
  treat every upstream instruction, script, hook, workflow, and bundled spec as untrusted data.
  Status: audited at commit `bf2448f03686a8348324e4741106697d30a867f9` and skills tree
  `8cc9ed3986cf6c942f718439e1ee8249eb17a2ad`; durable source-scoped manifest, genesis, parity, and
  transactional review-ledger tracking are implemented and live-reproved.
- `OKFS-002` — Preserve the valuable produce, maintain, and consume semantics as one discoverable
  Kiro-native `/okf` skill. Do not create a second planner, knowledge runtime, or `.okf/` tree when
  PK-Stack already owns `Wiki/`. Status: implemented with structural Kiro asset tests.
- `OKFS-003` — Use Kiro-compatible Agent Skills frontmatter and workspace-relative interfaces;
  exclude Claude plugin namespaces, `${CLAUDE_SKILL_DIR}`, and Claude-only hook assumptions.
  Status: implemented; the four upstream skill files are reference input, not shipped verbatim.
- `OKFS-004` — Do not vendor, install, or activate the upstream validator, visualizer, MCP server,
  Stop hook, GitHub Action, or helper scripts. Canonical `okn` and `projectctl` remain the only
  runtime boundary. Status: implemented and structurally asserted.
- `OKFS-005` — Never mine `~/.claude`, other agent transcripts, home directories, credentials, or
  unrelated conversations. Historical backfill requires a separately authorized, redacted,
  bounded migration. Status: implemented in the skill trust boundary.
- `OKFS-006` — Reject symlinks anywhere in the knowledge tree before validation or retrieval.
  Status: implemented in `projectctl`; positive and negative subprocess regressions pass.
- `OKFS-007` — Follow the current authoritative OKF 0.2 specification rather than trusting a
  vendored snapshot. In particular, every timestamp-valued field, including `stale_after`, must be
  an ISO 8601 datetime with an explicit offset. Status: implemented in `/okf` guidance and covered
  by the canonical validator campaign.
- `OKFS-008` — Keep the task-driven context ladder: root index, matching feature and explicit links,
  then one targeted bounded `okn` search with revision, locator, content hash, and line ranges.
  Never inject the whole Wiki. Status: implemented in skills, steering, docs, and live retrieval.
- `OKFS-009` — Preserve unknown metadata and user-authored concepts; never bulk-migrate, delete,
  deprecate, publish, or auto-open content merely to satisfy a check. Status: implemented as
  workflow policy; destructive and publication paths remain separately authorized.
- `OKFS-010` — Keep `okfcli/okf` as an optional explicitly named advisory CI/SARIF oracle only. It
  may run only against a disposable, immutable, symlink-free copy and must never substitute for
  canonical `okn` retrieval, provenance, lifecycle, or safety. Until it accepts the authoritative
  explicit-offset OKF 0.2 `stale_after` form, it must not gate normative conformance. Status:
  implemented in architecture, usage, runtime selection, and the v0.5.0 comparison record.
- `OKFS-011` — Apply PK-Stack's self-maintenance contract to the OKF sources themselves: track the
  exact `okf-skills` skills subtree and authoritative Google OKF specification tree independently,
  with per-source pins, genesis, parity, proposals, and serialized acceptance. Status: **closed
  locally** in candidate `8806fa6` with per-source state and the retained three-source no-drift
  reproof. The separate immutable OKF/OKN campaign passed the candidate's resulting Wiki and
  canonical runtime boundary. Hosted cadence proof remains a release gate; the immutable knowledge
  campaign does not substitute for a GitHub-hosted updater run.
- `OKFS-012` — Track the canonical OpenKnowledge CLI machine contract independently of the Google
  OKF specification and third-party workflow methodology. Scope the source to the versioned
  `packages/cli/schemas/v1` tree, adapt only the bounded validation/search boundary, and exclude
  deployment, job, runtime, and release-management interfaces. Preserve compatibility with pinned
  `okn` 0.13.0 responses that omit search `status`; when a newer response emits it, require exactly
  `managed` before trusting sources. Status: implemented with a 63-file content-addressed parity
  inventory, live source reproof, and managed/unmanaged protocol regressions.
- `OKFS-013` — Do not let GitHub's repository-wide 300-file Compare response ceiling turn
  unrelated upstream churn into an unavailable or incomplete source-scoped review. At exactly the
  documented ceiling, retain the Compare response only as bounded fast-forward/commit-chain proof
  and reconstruct the configured subtree delta from the exact pinned and current recursive trees
  and content-addressed blobs. Preserve the 100-path, per-patch, aggregate-patch, tree-entry,
  blob-byte, 5,000-line-per-side, and 25,000,000-line-pair limits; fail closed above the ceiling or
  on any truncated, ambiguous,
  malformed, oversized, or identity-inconsistent input. Status: implemented with deterministic
  three-line-context unified patches, whole-subtree unique-rename handling, ambiguous-copy
  projection, generated controller parity, and focused boundary/adversarial regressions.

## Sol Advisor cap-boundary audit criteria

The first fresh Sol Advisor audit reviewed diff
`10e9d4aa1ece89821d271dd805e0bf038a92b6da8f370d5d3b455423f4e79322` with
`gpt-5.6-sol` at high effort and returned `FIX FIRST` with two material findings.

- `SOL-001` — Bound attacker-controlled tree-derived diff work before `difflib.SequenceMatcher`
  can run. Status: implemented with a 5,000-line ceiling on either blob side and one shared
  25,000,000-line-pair budget across the entire reconstructed comparison; capped adversarial input
  and aggregate exhaustion regressions fail before a second over-budget match.
- `SOL-002` — Infer a pure rename only when the exact identity occurs once in the entire pinned
  subtree and once in the entire current subtree. An unchanged same-identity path must make a
  remove/add pair ambiguous. Status: implemented with a capped duplicate-identity regression while
  retaining the unique-identity rename regression.

A fresh Sol audit and Fable peer acceptance remain required after these remediations.

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
  and the selected-profile Kiro campaign passed locally. Fable round 5 later reviewed candidate C,
  which carried the committed current-session evidence, and retained Kiro fail-repair-pass behavior
  as a proven strength. That is historical FBL-008 evidence only: `PLOT-008` remains open because the
  campaign did not exercise native Spec artifacts or the final executable tree.

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
  Fable round 5 reviewed the later candidate C carrying this evidence and retained Kiro
  current-session fail-repair-pass behavior as a proven strength. That review does not substitute
  for the still-pending `PLOT-008` native-Spec campaign on the final executable tree.
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
  into the frozen teardown plan, and refuse both first-pass and resumed deletion of the exact outer
  container/network after drift. Teardown must not use project-wide `docker compose down`; a
  foreign network attachment remains untouched and makes exact network deletion fail closed.
  Status: implemented in code and unit tests; fresh exact-tree lifecycle evidence is pending.
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
  strengthened contract. Fable round 5 later retained strengthened idempotency as a proven
  historical strength; current exact-tree live reproof remains a separate release gate.
- `FBL-029` — Bind final live evidence to the exact remediated combined commit. Run a fresh
  `doctor -> up -> deploy -> deploy -> verify -> evidence -> down` lifecycle with the
  owner-controlled external judge, two retained generations, explicit source identity, complete
  cleanup, and foreign-image noninterference. Local disposition: **closed locally** by
  `fable-r5-902` on executable commit `cb2cb0905687c3e94e539333d8945c37109f6189`, tree
  `c28e71a050185f19befb3832e865c4e54f2bcf03`; see `reviews/fable-r5-live-proof.md` for the two
  generations, frozen 14-path map, judge result, teardown, and postconditions. Fable round 5 did
  not reopen `FBL-029` and explicitly retained external-judge closure as a proven historical
  strength. `live-council-902` and `kiro-v3-accept-902` remain honest earlier-source evidence; none
  of these older campaigns substitutes for current exact-tree live reproof.

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
  Hatchling 1.32.0. The private repository has since been created and verified under `FBL-040` and
  `SELF-007`; publication of the exact final release tip remains sequenced after the remaining
  acceptance gates and is not claimed early.
- `FBL-035` — document the manual exact-digest Floci image-pull fallback while retaining the
  automatic preflight's fail-closed diagnostic match. Local disposition: **closed locally** and
  documented.
- `FBL-036` — document that externally deleting a journaled completed-generation image is outside
  same-digest recovery and requires a new source digest/deployment or teardown/new run. Local
  disposition: **closed locally** and documented.

## Fable round 5 criteria

Fable 5.1 reviewed commit `491bfdafc94832c6624ed86051955b1067245979` at `xhigh` effort and
returned `REQUEST CHANGES` with three material findings. The normalized report is
`reviews/fable-round-5.md`.

- `FBL-037` — Retain bounded evidence for the first real 27-path self-maintenance transition and
  bind it to the feature-backed goal, accepted ledger entry, complete disposition inventory, and
  final no-drift result. Local disposition: **closed locally** by
  `reviews/pk-stack-maintenance-campaign.md`, its machine-readable JSON companion, and an executable
  regression. The record distinguishes retained controller output, Codex harness attestations,
  and Git-history reconstruction; it proves the same goal passed on attempt 2 with `A=23`, `B=3`,
  and `C=1` rather than adopting the reviewer's arithmetically incomplete suggested counts.
- `FBL-038` — Prevent model-writable Git metadata from gaining code execution in the secretless
  finalizer. Local disposition: **closed locally** through a bounded owner/mode/type/hash snapshot
  of `.git/config`, `.git/config.worktree`, `.git/hooks`, and `.git/info` outside the model-visible
  checkout; pre-Git close refusal; and trusted Git configuration that disables hooks, fsmonitor,
  external diff, ambient attributes, and inherited global/system configuration. Planted hook and
  config regressions prove refusal before staging or hook execution. The exact hosted Kiro
  permission sub-gate is now **closed** by
  [run 33736820795](https://github.com/njs14/pk-stack/actions/runs/33736820795) on commit
  `8c5651927f6ab98fb7967e5ceca8a70bd85b9a9b`; successful hosted maintenance and final council
  acceptance remain separate gates.
- `FBL-039` — Correct stale executable identities, generated counts, campaign links, and acceptance
  status narrative. Local disposition: **closed locally** in the root README,
  `docs/validation-report.md`, and this ledger, with historical and current evidence roles kept
  distinct.
- `FBL-040` — Create the authorized private repository before treating its plugin URL as live.
  Disposition: **closed**. The authorized [`njs14/pk-stack`](https://github.com/njs14/pk-stack)
  repository was created and its visibility verified as private. This closes the URL/publication
  identity finding. Hosted credential, exact permission-matrix, and read-only canary evidence now
  exists; successful maintenance and final council acceptance remain separate pending gates.
- `FBL-041` — Remove the misleading null Kiro evidence-carrier field and state whether the source
  write preceded attempt 2. Local disposition: **closed locally** in the final Kiro JSON and prose
  evidence.
- `FBL-042` — Ensure teardown cannot sweep a foreign object that merely shares the Compose project
  identity. Local disposition: **closed locally** by deleting only the frozen claim-checked outer
  container and network and by a planted-foreign-member fail-closed regression. The fresh
  [`final-floci-903` campaign](final-floci-deletion-campaign.md) exercised the exact revised path on
  immutable candidate `8806fa6`: all eight teardown phases passed, the campaign objects were absent,
  and a running foreign container carrying the same Compose project label retained the same ID and
  bounded inspect hash. Its [JSON record](final-floci-deletion-campaign.json) is the bounded proof.
- `FBL-043` — Exercise representative direct, consolidated, native-replacement, and excluded skill
  routes and retain the remaining hosted/publication gates. Local route disposition:
  **closed locally** by `reviews/skill-route-campaign.md`, its JSON companion, and the bound
  executable regression. That record is intentionally non-interactive and does not substitute for
  private-repository maintenance-lifecycle evidence, which remains pending. The separate hosted
  credential and exact permission-matrix smokes have since passed.
- `FBL-044` — Accept only the canonical Fable reviewer while tolerating the one exact, versioned,
  tightly bounded first-party Haiku companion shape observed in the real pinned-client envelope.
  Local disposition: **closed locally** with positive real-shape and negative identity/usage-bound
  regressions; arbitrary companion or substantive reviewer models remain forbidden.
- `FBL-045` — Bind the root controller's draft-feature regression to the canonical implementation
  rather than a copied rule. Local disposition: **closed locally** by executing the single named
  helper AST extracted from the tracked vendored source.

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
  and canonical/generated parity tests. Two real transitions are accepted and locally passed. The
  bounded campaign record retains the first transition's 27 paths and `A=23` / `B=3` / `C=1`
  summary, then binds the latest two-path `B=2` transition and final all-source no-drift reproof to
  the accepted ledger tip.
- `SELF-002` — Keep self-maintenance inside one immutable feature-backed `projectctl` goal. Record
  exactly one failing pre-edit attempt for a new goal, retain four bounded repair attempts, and
  resume an already-attempted goal without consuming another attempt before a meaningful change.
  Status: implemented, regressed, and **passed in two real campaigns**. Goal
  `395bd46c-f889-4fbc-8933-187ab0e88441` proved the first feature-backed transition. The later
  source-scoped goal `efe929d9-9945-4c97-866b-a8f414b9ef97` retained contract digest
  `59f08f943111cf645d05dc4962912fa81c3bf20e26b879c6ef6f7c4e21f76b5a`, failed before the
  second transition, and passed on attempt 2 of 5 after acceptance.
- `SELF-003` — Run the primary updater on a cadence with checksum-pinned Kiro CLI 2.21.0, Sol at
  `max`, no ACP default, a minimal CI-only agent, and no shell/network/MCP/subagent authority in the
  model step. Expose `KIRO_API_KEY` only to the four bounded repair steps, destroy its isolated
  runtime before candidate code or secretless verification, and never fall back to another model
  automatically after a Kiro failure. Status: **closed locally, hosted lifecycle proof pending**.
  The conventional Kiro workflow and structural tests implement the contract. Hosted credential
  run [33729855987](https://github.com/njs14/pk-stack/actions/runs/33729855987) passed on commit
  `99d2784b35a255ebc70585542e8e78b78d05895e`, and exact permission-matrix run
  [33736820795](https://github.com/njs14/pk-stack/actions/runs/33736820795) passed on commit
  `8c5651927f6ab98fb7967e5ceca8a70bd85b9a9b`. Neither proves the updater's scheduled or dispatched
  repair lifecycle, including its per-attempt model preflight.
- `SELF-004` — Treat upstream patches and model output as untrusted data. Permit automatic author
  edits only on the declared bounded Power surface, keep controller/tests/CI/feature contracts
  immutable, and let a secretless base-commit finalizer alone regenerate, test, advance the pin,
  and package the candidate. Every candidate, including any operational skill or agent-definition
  change, must receive a fail-closed Fable 5.1/xhigh verdict bound to the exact base SHA, head SHA,
  content digest, patch digest, and trusted model execution metadata before merge. Status:
  **closed locally, hosted proof pending** after the trusted-Git remediation and adversarial
  workflow regressions. A repository Claude credential is an external prerequisite for hands-off
  operational updates and must never be copied from local session state.
- `SELF-005` — Publish only one exact, non-draft, bot-owned candidate commit; re-run the same
  deterministic gate on base and head, rebind mergeability and all digests immediately before
  squash merge, and safely replace an exact bot-owned stale PR after the default branch moves.
  Human or ambiguous PRs must never be closed or adopted. Status: **closed locally, hosted proof
  pending**; mocked policy regressions pass, but live private-repository behavior remains required.
- `SELF-006` — Keep the GitHub Agentic Workflows/Copilot path manual-only and independently locked,
  with the same immutable candidate contract. It may assist recovery but must never silently
  replace Kiro or weaken the Fable gate. Status: **closed locally and explicitly non-gating**. It
  remains an uninvoked, separately authorized recovery fallback; release acceptance requires the
  hosted primary Kiro lifecycle, not a fallback dispatch that could be mistaken for proof of the
  normal path.
- `SELF-007` — Create only the authorized private `njs14/pk-stack` repository, configure the Kiro
  secret without printing it, verify repository/action privacy and permissions, and run a hosted
  workflow proof. Status: **closed**. The authorized repository exists and was verified private;
  credential run [33729855987](https://github.com/njs14/pk-stack/actions/runs/33729855987) passed on
  commit `99d2784b35a255ebc70585542e8e78b78d05895e`, permission run
  [33736820795](https://github.com/njs14/pk-stack/actions/runs/33736820795) passed on commit
  `8c5651927f6ab98fb7967e5ceca8a70bd85b9a9b`, and read-only runtime canary
  [33743033801](https://github.com/njs14/pk-stack/actions/runs/33743033801) passed on commit
  `7ce09e3dc161965b0cdac01f992e7ec1c89748b0`. Successful maintenance and final council acceptance
  remain separate criteria; they are not implied by this repository-liveness proof.
- `SELF-008` — Ship a documented, decodable RGBA potato-ghost mascot with an OKF scholar's
  mortarboard, transparent outer corners, and an honest visual-reference notice. Status:
  implemented; the asset checksum and decoded alpha behavior are regressed.
- `SELF-009` — Bind the candidate gate and final merge to the exact authorized Kiro workflow name,
  provider, workflow path, source-run ID, base, repository, and branch
  `pk-stack-upstream/kiro-<source-run-id>`. A fallback run or a different Kiro run must not adopt a
  surviving candidate. Status: **closed locally, hosted proof pending** with exact resolve/merge
  revalidation and cross-run / cross-provider negative tests; the authorized private workflow must
  still exercise that binding.
- `SELF-010` — Make the hosted Kiro permission smoke exercise the exact immutable
  `pstack-maintainer` permission matrix rather than a representative surrogate. Every allowed class
  and representative overlapping protected path must be checked, with exact policy-denial events
  and unchanged protected hashes. The production and fixture agents must also carry the exact
  `toolsSettings` discovery contract, appear in a sterile V3 `agent list`, and fail on any default-
  agent fallback. Status: **closed on hosted commit
  `8c5651927f6ab98fb7967e5ceca8a70bd85b9a9b`**. After a live negative exposed the missing discovery
  field, the local guard suite and sterile no-model production/fixture discovery passed; hosted
  [run 33736820795](https://github.com/njs14/pk-stack/actions/runs/33736820795) then exercised seven
  allowed writes and six isolated denials with unchanged protected hashes and exact cleanup.
- `SELF-011` — Bind each upstream source to exactly one machine-validated canonical genesis marker
  before its ordered transition markers. Reject missing, changed, duplicate, extra, malformed, or
  reordered genesis/transition evidence before network access, and preserve genesis through accept
  and recovery. Status: implemented and **passed across both real campaigns**. Canonical genesis
  remained intact through the 27-path transition and the later two-path transition; the latest
  passing attempt re-proved the accepted tip, live ref, complete ordered chain, transition
  inventories, and disposition counts.
- `SELF-012` — Demonstrate the committed daily cadence, credential smoke, exact-authority
  permission smoke, authenticated upstream check, and one hosted no-op or drift lifecycle in the
  authorized private repository. Status: **partially closed**. The daily schedule is committed;
  credential run [33729855987](https://github.com/njs14/pk-stack/actions/runs/33729855987) and
  exact-authority permission run
  [33736820795](https://github.com/njs14/pk-stack/actions/runs/33736820795) passed. Maintenance
  [run 33743730700](https://github.com/njs14/pk-stack/actions/runs/33743730700) on commit
  `6e8d4bbe25d549faa5f07378139d92de60294410` passed immutable planning and authenticated drift
  detection, then failed safely at reviewer readiness because no credential was configured under
  either accepted Fable secret name; Kiro, publish, and merge work did not run. The resulting
  candidate-gate
  [run 33743818713](https://github.com/njs14/pk-stack/actions/runs/33743818713) was skipped. The
  bounded [preflight campaign](hosted-maintenance-preflight-campaign.md) preserves that safety proof.
  A successful drift lifecycle therefore remains required; a no-op skips reviewer readiness and
  cannot prove the reviewer-credential path.
- `SELF-013` — Keep autonomous acceptance limited to the four configured GitHub source
  repositories, and add a separate weekly/manual read-only Kiro product canary. Resolve the
  official stable CLI manifest; select, checksum, and probe exactly the advertised x86_64 Linux
  headless binary; validate and discover all five workspace agents; and strictly validate the live
  model inventory without sending a model turn. Expose `KIRO_API_KEY` only to that inventory step
  after version, SHA-256, derived URL, and size exactly match the reviewed pin; never pass it to an
  advertised unpinned binary. Invoke neither Anthropic nor any model, bound and scrub output,
  upload no artifact, and always
  clean the isolated runtime. Treat IDE metadata, Kiro Crew Nightly feeds, the changelog,
  `llms.txt`, and recorded relevant documentation hashes as non-gating observations. Any newer
  stable pin or runtime regression must fail red; promotion remains deliberately manual because
  workflow and protected controller files are trust roots. Status: **closed on hosted commit
  `7ce09e3dc161965b0cdac01f992e7ec1c89748b0`**.
  [Run 33743033801](https://github.com/njs14/pk-stack/actions/runs/33743033801)
  passed the exact pin, five-agent validation/discovery, live model inventory, all 13 documentation
  hashes, and cleanup without an uploaded artifact; the bounded
  [campaign record](kiro-runtime-canary-campaign.md) also retains the prior fail-safe extraction
  result and its exact-size remediation.

## Fable reviewer-readiness peer criterion

Fable 5.1 at `xhigh` reviewed immutable checkpoint
`dfbcfa82b37401e673b8441b25f1569a8fed51d4` and returned one material preflight finding. This was
a focused peer review of the hosted-maintenance checkpoint, not the final 24-area release verdict.

- `FBL-046` — Bind the execution semantics that prevent Kiro credential use after reviewer
  readiness fails. `maintain` must explicitly require a successful `reviewer_readiness` result;
  regression coverage must pin the exact five-job graph and dependency edges, the explicit
  success condition, and exactly four `KIRO_API_KEY` bindings confined to `maintain`. Status:
  **execution semantics peer-verified; focused Fable acceptance pending**. The focused Fable pass
  on commit `347d461a097f5d26e084f10958641fc4aa70ce07`
  found no route past failed, skipped, cancelled, or absent readiness, but opened the material
  subfinding below. The remediation also makes script extraction line-bounded, hardens the
  readiness runner's network, records the absent-credential branch and downloaded detector
  digest, and requires a hosted drift lifecycle rather than accepting a no-op as reviewer-
  credential proof.
- `FBL-046-R1` — Reject parser-level secret-scope multiplication. A YAML anchor on one repair
  `env` mapping plus an alias on another step produced five effective `KIRO_API_KEY` scopes while
  the former 64 textual guard tests still passed. Status: **remediation reached commit
  `f6e3440c6a6c6faab1030501baa3c193535207e1` with 67 passing guard tests; the three LOW
  defense-in-depth follow-ups were then implemented in an intermediate 69-test worktree state,
  and immutable Fable re-review remains pending**. The `f6e3440` candidate forbids active anchors,
  aliases, merge keys, and explicit mapping keys; requires bare exact credential environments;
  closes all five job property sets; enumerates the readiness, maintain, and publish steps;
  confines the secret to the four named repairs; and retains valid env-map and whole-step alias
  counterexamples. The intermediate state also closes the three LOW scanner-self-containment
  observations and passes 69 of 69 direct guard tests without changing the production workflow.
  The bounded [peer record](fable-fbl046-peer-review.md) preserves the finding and exact external
  evidence hashes.
- `FBL-046-R2-C1` — **HIGH**, from a Codex read-only conformance review. Two actionlint-valid YAML
  scalars were false accepts for the raw scanner: double-quoted
  `"\u0024{{ toJSON(se\u0063rets) }}"` decodes to `${{ toJSON(secrets) }}`, while single-quoted
  `'${{ ''}}'' && toJSON(secrets) }}'` decodes to `${{ '}}' && toJSON(secrets) }}`. Acceptance
  requires rejecting scalar token-changing quote escapes without a general YAML loader, retaining
  both exact actionlint-valid reproductions, and preserving inert comments, plain scalars, and
  block scalars. Status: **implemented locally on the current unnamed candidate; immutable Fable
  review pending**. A stateful non-block quote prepass rejects double-quoted backslash escapes and
  single-quoted doubled-quote escapes across lines; Codex independently replayed both exact rejects;
  the direct suite passes 70 of 70 tests; `py_compile`, Ruff, actionlint, and diff checks pass; and
  the production workflow remains unchanged. No new commit or tree is claimed yet.

Two attempted re-reviews of the immutable `f6e3440` target carry no acceptance value. Attempt 1
ended with a nominal clean report authored by Opus 4.8 after a Fable `model_refusal_fallback`, so
that report is inadmissible. Attempt 2 retained Fable identity but hit the five-hour session cap
and produced no report; its reset epoch was `1788444600`. The rejected mixed-model report supplied
no material counterexample. Its three actionable LOW scanner-hardening observations are now
implemented in the retained 69-test intermediate state, while its parent-tree-reference observation
requires only the existing disclosure. The later post-`FBL-046-R2-C1` auxiliary re-review was
classifier-blocked and produced no verdict or acceptance value; it is not approval. Focused Fable
acceptance and final release acceptance both remain pending.

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
  overstate IDE or Crew permission parity. Status: **closed for the tested CLI 2.21.0 boundary**.
  The bounded local Kiro 2.21.0 probe in `reviews/kiro-v3-agent-discovery-probe.json` records the
  field-absent failure and then exact sterile discovery of all five shipped workspace agents with
  the inert sentinel present. Hosted runtime-canary
  [run 33743033801](https://github.com/njs14/pk-stack/actions/runs/33743033801) on commit
  `7ce09e3dc161965b0cdac01f992e7ec1c89748b0` independently validated and discovered all five, and
  the hosted permission smoke exercised the production profile. IDE, Web, and Crew permission
  parity remain explicitly untested.

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
  **closed locally** by `powers/pk-stack/docs/upstream-skill-parity.json`: 45 upstream skills and
  122 package files are inventoried at both accepted and reviewed-current identities, with every
  load-bearing resource and exactly one validated disposition represented.
- `SKL-002` — Preserve an invocable Kiro skill under the familiar upstream name for every
  user-meaningful workflow, even when it is a thin DRY route to consolidated instructions. A prose
  crosswalk alone is insufficient, and the upstream workflow itself—not its title or description—is
  the semantic source of truth. Preserve its load-bearing sequence and referenced contracts before
  translating only Cursor/runtime-specific seams. Native replacement is allowed only when the named
  route clearly teaches the user how to invoke the equivalent Kiro primitive; exclusions are
  limited to non-workflow packaging or unsafe/inapplicable runtime machinery. Status:
  **closed locally** with 17 direct ports, 23 discoverable aliases to shared Kiro-native cores,
  four explicit native-Kiro replacements, and one narrowly justified exclusion; all 44 runnable
  upstream names retain invocable routes.
- `SKL-003` — Adapt every routed skill to PK-Stack's surface contract: current Kiro agent-session
  language; CLI V3 and IDE Agent Focus as first-class surfaces; Crew compatibility; Web support by
  design but untested; inherited model and effort; and no Cursor Task API, fixed model, ACP default,
  Graphite requirement, watcher daemon, destructive worktree cleanup, or unreviewed external side
  effect. Status: **closed locally** across the routed catalog and its wording regressions. This is
  packaged compatibility evidence, not a claim that Web or every IDE/Crew permission behavior was
  exercised.
- `SKL-004` — Package and generate the complete routed catalog without drift across the canonical
  Power, `.kiro`, and projectctl distribution. Tests must prove exact catalog coverage, route-target
  validity, metadata/schema validity, safe exclusion wording, and canonical/generated byte parity.
  The expected distribution is 49 canonical and projectctl-cache skill directories, with only the
  Power-local `setup-pstack` shim omitted from the 48 live `.kiro/skills` routes. Managed live skill
  paths remain write-denied while a new user-owned skill path falls through to explicit approval,
  so authoring workflows are functional without making generated PK-Stack assets mutable. Status:
  **closed locally**. Managed bootstrap materialized 48 live `.kiro` skills and all 49
  controller-cache skills; the dry-run is idempotent, and exact catalog, route, metadata, safety,
  and canonical/generated byte-parity regressions pass.
- `SKL-005` — Exercise representative direct, consolidated, native-replacement, and excluded routes
  in the final validation campaign, then include the complete catalog and disposition evidence in
  both the Fable acceptance review and Grok sweep. Status: **closed locally, pending council
  review**. `reviews/skill-route-campaign.md` and its JSON/regression exercise one route of every
  disposition class under an offline bounded harness; the campaign expressly does not claim an
  interactive model-selection transcript. Fable re-review and the Grok sweep remain required.
- `SKL-006` — Preserve pervasive upstream activation semantics through supported Kiro mechanisms,
  not unsupported Cursor frontmatter. TypeScript guidance must have a Kiro `fileMatch` steering
  route for `*.ts`/`*.tsx`, and the concise non-slop prose core must be always applied while the full
  skills remain directly invocable. Tests must prove steering frontmatter, generated parity, and
  that normal interactive operation still inherits the selected Kiro model. Status:
  **closed locally** through the Kiro steering assets, directly invocable skills, inherited-model
  agent profiles, and exact generated-parity regressions.
- `SKL-007` — Preserve the upstream verification lifecycle in executable projectctl contracts:
  launch, doctor, drive, evidence, cleanup, helpers, sub-features, every user entrypoint, per-entry
  drive recipes, and gotchas. Creation seeds three to five records and proves one representative
  feature; maintenance later drives the complete map with one coordinator, one bounded drift-repair
  retry, explicit verified-unreachable prerequisites, and zero or one separately authorized PR.
  Status: **closed locally** by the generated controller contracts, verification-skill templates,
  and full-catalog regressions; any real external PR remains separately authorization-gated.
- `SKL-008` — Restore the nested reasoning and review contracts rather than collapsing them into
  generic advice: architect's usage-first type/signature/module scaffold, rationale and red flags;
  how's independent critique rubric; interrogate/model-council correctness, code-quality, and lead
  judgment; reflect's three independent lenses plus synthesis; and why's source-category discovery,
  null/gap accounting, incident evidence, and calibrated confidence. Status: **closed locally** in
  the direct and consolidated routed skill bodies and their semantic-content assertions.
- `SKL-009` — Restore the load-bearing meta-workflows in `figure-it-out`, `no-comments`, `teach`,
  `technical-writing`, `unslop`, and `show-me-your-work`. The last must use a deterministic bounded,
  redacted, append-only evidence lever that is local/uncommitted by default; none may request hidden
  reasoning. Status: **closed locally** with the workflows and bounded evidence lever present in
  the canonical/generated catalog and protected by focused safety assertions.
- `SKL-010` — Preserve all 23 Poteto playbook routes and the reviewed live-current PR semantics:
  `gh` by default with optional Origin, early authorized ready-PR checkpoint, stable patch-ID
  freshness after rebase, and a same-scenario trunk regression lane or absolute budget when trunk
  lacks the feature. Cursor `/goal`, `/loop`, Task metadata, Graphite, watchers, and destructive
  cleanup remain translated or excluded rather than copied. Status: **closed locally** for all 23
  Poteto playbook routes, including the current reviewed PR semantics and explicit translation or
  exclusion of unsupported runtime machinery.

## Remaining acceptance sequence

1. Provision one valid Fable Actions credential under exactly one accepted secret name, then
   complete one authenticated hosted drift-maintenance lifecycle. The existing fail-fast run is
   safety evidence, not a successful lifecycle; a no-op would skip reviewer readiness.
2. Re-run the canonical OKF/OKN campaign and every deterministic static, packaging, policy, and
   regression gate on the final functional tree. Retain the older `8806fa6` OKF/OKN and Floci
   campaigns as exact historical evidence only.
3. Exercise the final native-Spec-to-verified-goal integration on its exact immutable candidate.
4. Repeat Fable 5.1 at `xhigh` on immutable candidates until it returns acceptance with zero
   material unresolved findings.
5. Run the final Grok 4.6 `xhigh` read-only sweep on the Fable-accepted commit.
6. Return any material Grok-driven tree change to Fable 5.1 `xhigh` for reacceptance.
7. Verify final private publication, default-branch identity, secret names, workflow permissions,
   hosted evidence, and exact release commit before declaring completion.
