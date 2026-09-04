# Upstream skill parity

This is the human-readable view of [the bounded machine inventory](upstream-skill-parity.json).
It accounts for the complete package beneath every top-level `pstack/skills/*/SKILL.md` in the
immutable pinned and current `cursor/plugins` trees retrieved on 2026-09-03. The inventory contains
122 files at each revision, including referenced playbooks, templates, data, and helpers. Per-package
tree hashes and every resource path, blob identity, size, and handling decision live in the JSON
file. The matrix records semantic adaptation, not copied upstream implementation.

| Disposition | Count |
|---|---:|
| Direct Kiro-native port | 17 |
| Discoverable alias or consolidation | 23 |
| Native Kiro replacement | 4 |
| Explicit exclusion | 1 |
| **Upstream total** | **45** |

Forty-four upstream names remain individually discoverable. Relative to the Cursor source,
PK-Stack also ships the aggregate `principles` skill and four PK-only workflows—`maintain-pk-stack`,
`model-council`, `okf`, and `verified-goal`—for 49 skill directories in total. The separate
OKF-skills provenance inventory records `okf`'s independently adapted methodology.

## Nested resource handling

| Handling | Files at the current revision | PK-Stack treatment |
|---|---:|---|
| Semantic source | 101 | Preserve load-bearing workflow decisions in concise Kiro skill bodies or shared references. |
| Helper semantics only | 3 | Preserve the contract of Poteto plan validation, worktree audit, and decision logging without copying or executing the upstream scripts. |
| Runtime-specific exclusion | 18 | Do not ship the Cursor orchestration, PR watcher, Bun/package, bootstrap, or test/runtime implementation. |

The three helper-semantics decisions are
`poteto-mode/scripts/check-plan.mjs`, `poteto-mode/scripts/worktree-audit.sh`, and
`show-me-your-work/scripts/log.sh`. PK-Stack preserves their plan-validation,
worktree-audit, and bounded append/audit outcomes through Kiro guidance and
projectctl contracts; it does not copy or execute those files. The 18 runtime
exclusions are the remaining `poteto-mode/scripts/**` bootstrap, Bun package,
orchestrator, and watcher implementation files listed individually in the JSON
inventory. They remain hash-accounted even though they are not shipped.

The multi-file packages are `architect`, `create-verification-skill`, `how`, `interrogate`,
`poteto-mode`, `reflect`, `show-me-your-work`, `typescript-best-practices`, and `why`. In
particular, [`poteto-mode/references/workflows.md`](../skills/poteto-mode/references/workflows.md)
preserves the package's workflow sequences while replacing Cursor `/goal`, `/loop`, Task/cloud-agent
metadata, fixed model slugs, Graphite, watcher/orchestrator programs, automatic pull-request actions,
and destructive cleanup with current-session Kiro skills, native sub-agents, `verified-goal`, and
explicit authorization gates. Its shipping path keeps GitHub CLI as the default forge, permits
Origin CLI only after resolving the same repository, binds freshness to stable patch IDs after
rebases, and treats both early ready-PR creation and landing as separately authorized actions.

The authoritative upstream route is `create-verification-skill`; there is no separate
`install-verification-skill` package in either bounded catalog. Requests phrased as "install a
verification skill" route to `create-verification-skill` rather than inventing a second skill name.
Likewise, the `setup-pk-stack` replacement preserves the source package's post-setup offer of that
workflow while deliberately replacing its Cursor-wide per-role model rule with repository-local,
idempotent Kiro bootstrap and the current session's selected model and effort.

## Complete mapping

| Upstream skill | Disposition | Runnable route | Rationale |
|---|---|---|---|
| `architect` | Direct port | [`architect`](../skills/architect/SKILL.md) | Grounded architecture alternatives and verification are portable; execution uses native Kiro context and optional projectctl evidence. |
| `arena` | Direct port | [`arena`](../skills/arena/SKILL.md) | Competing implementation sketches and evidence-based selection map directly to native Kiro sub-agents. |
| `automate-me` | Native Kiro replacement | [`automate-me`](../skills/automate-me/SKILL.md) | Captures repeatable behavior from the current Kiro session and explicit project evidence; it does not mine private editor transcripts or auto-publish. |
| `blast-radius` | Direct port | [`blast-radius`](../skills/blast-radius/SKILL.md) | Portable impact tracing follows callers, state, boundaries, and executable behavior instead of treating text search as proof. |
| `bro` | Direct port | [`bro`](../skills/bro/SKILL.md) | Plain-language restatement is surface-neutral and preserves material facts and caveats. |
| `create-verification-skill` | Direct port | [`create-verification-skill`](../skills/create-verification-skill/SKILL.md) | The repository interview and live proof lifecycle maps to projectctl feature contracts and project-local Kiro skills. |
| `figure-it-out` | Direct port | [`figure-it-out`](../skills/figure-it-out/SKILL.md) | Hypothesis-driven unfamiliar work is portable and stays in the current Kiro session with bounded native delegation. |
| `how` | Direct port | [`how`](../skills/how/SKILL.md) | Evidence-grounded runtime explanation is portable; fixed reviewer models and editor-specific transcript mechanisms are removed. |
| `interrogate` | Alias / consolidation | [`interrogate`](../skills/interrogate/SKILL.md) | A discoverable compatibility route into model-council preserves adversarial review while one canonical council owns advisory policy. |
| `maintain-verification-skill` | Direct port | [`maintain-verification-skill`](../skills/maintain-verification-skill/SKILL.md) | The live feature-by-feature audit is portable and updates only verifier assets unless product repair is separately requested. |
| `make-bot-ui` | Excluded | [Safe manual architecture path](#make-bot-ui-safety-exclusion) | No runnable skill ships: the source is a Cursor/Grok Bot routine coupled to secret-card APIs, a cursor.sh webhook endpoint, and automatic sudo/Tailscale installation. Use architect to design a reviewed, least-privilege manual bot UI for the target environment. |
| `no-comments` | Direct port | [`no-comments`](../skills/no-comments/SKILL.md) | Portable cleanup distinguishes redundant narration from external contracts, safety rationale, and narrow suppressions. |
| `poteto-mode` | Alias / consolidation | [`poteto-mode`](../skills/poteto-mode/SKILL.md) | A discoverable compatibility router selects PK-Stack skills and the DO/PROVE/KNOW interfaces without recreating Cursor task orchestration. |
| `principle-boundary-discipline` | Alias / consolidation | [`principle-boundary-discipline`](../skills/principle-boundary-discipline/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-build-the-lever` | Alias / consolidation | [`principle-build-the-lever`](../skills/principle-build-the-lever/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-encode-lessons-in-structure` | Alias / consolidation | [`principle-encode-lessons-in-structure`](../skills/principle-encode-lessons-in-structure/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-exhaust-the-design-space` | Alias / consolidation | [`principle-exhaust-the-design-space`](../skills/principle-exhaust-the-design-space/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-experience-first` | Alias / consolidation | [`principle-experience-first`](../skills/principle-experience-first/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-fix-root-causes` | Alias / consolidation | [`principle-fix-root-causes`](../skills/principle-fix-root-causes/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-foundational-thinking` | Alias / consolidation | [`principle-foundational-thinking`](../skills/principle-foundational-thinking/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-guard-the-context-window` | Alias / consolidation | [`principle-guard-the-context-window`](../skills/principle-guard-the-context-window/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-laziness-protocol` | Alias / consolidation | [`principle-laziness-protocol`](../skills/principle-laziness-protocol/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-make-operations-idempotent` | Alias / consolidation | [`principle-make-operations-idempotent`](../skills/principle-make-operations-idempotent/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-migrate-callers-then-delete-legacy-apis` | Alias / consolidation | [`principle-migrate-callers-then-delete-legacy-apis`](../skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-minimize-reader-load` | Alias / consolidation | [`principle-minimize-reader-load`](../skills/principle-minimize-reader-load/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-model-the-domain` | Alias / consolidation | [`principle-model-the-domain`](../skills/principle-model-the-domain/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-never-block-on-the-human` | Alias / consolidation | [`principle-never-block-on-the-human`](../skills/principle-never-block-on-the-human/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-outcome-oriented-execution` | Alias / consolidation | [`principle-outcome-oriented-execution`](../skills/principle-outcome-oriented-execution/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-prove-it-works` | Alias / consolidation | [`principle-prove-it-works`](../skills/principle-prove-it-works/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-redesign-from-first-principles` | Alias / consolidation | [`principle-redesign-from-first-principles`](../skills/principle-redesign-from-first-principles/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-separate-before-serializing-shared-state` | Alias / consolidation | [`principle-separate-before-serializing-shared-state`](../skills/principle-separate-before-serializing-shared-state/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-sequence-verifiable-units` | Alias / consolidation | [`principle-sequence-verifiable-units`](../skills/principle-sequence-verifiable-units/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-subtract-before-you-add` | Alias / consolidation | [`principle-subtract-before-you-add`](../skills/principle-subtract-before-you-add/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `principle-type-system-discipline` | Alias / consolidation | [`principle-type-system-discipline`](../skills/principle-type-system-discipline/SKILL.md) | Individually discoverable alias with a focused action; canonical detailed semantics live in the shared principles catalog. |
| `recall` | Native Kiro replacement | [`recall`](../skills/recall/SKILL.md) | Uses current-session context, Kiro steering, projectctl knowledge, git, and explicitly authorized task history instead of private Cursor transcript stores. |
| `reflect` | Native Kiro replacement | [`reflect`](../skills/reflect/SKILL.md) | Reflects on current Kiro work and proposes structural learning; broad durable instruction changes require explicit approval. |
| `setup-pstack` | Native Kiro replacement | [`setup-pk-stack`](../skills/setup-pk-stack/SKILL.md) | Routes the upstream setup skill to the consistent `/setup-pk-stack` Kiro command while preserving the setup outcome and optional verification-workflow offer; replaces its Cursor global role-model rule with idempotent Kiro Power bootstrap, ownership receipts, a pinned local controller, and inheritance of the user's selected Kiro model and effort. |
| `show-me-your-work` | Direct port | [`show-me-your-work`](../skills/show-me-your-work/SKILL.md) | A bounded decision-and-evidence trail is portable; it excludes hidden reasoning and unsafe raw transcript export. |
| `swarm` | Direct port | [`swarm`](../skills/swarm/SKILL.md) | Independent bounded work maps to native Kiro sub-agents with explicit ownership and current-session synthesis. |
| `tdd` | Direct port | [`tdd`](../skills/tdd/SKILL.md) | Failing-behavior-first implementation and layered proof are runtime-neutral. |
| `teach` | Direct port | [`teach`](../skills/teach/SKILL.md) | Layered how-and-why teaching is portable and grounded in inspected project evidence when repository-specific. |
| `technical-writing` | Direct port | [`technical-writing`](../skills/technical-writing/SKILL.md) | Reader- and task-oriented documentation is portable; examples and volatile claims require direct verification. |
| `typescript-best-practices` | Direct port | [`typescript-best-practices`](../skills/typescript-best-practices/SKILL.md) | TypeScript boundary schemas, constructive types, exhaustive variants, and runtime tests are portable. The full skill remains on demand, while Kiro-native `fileMatch` steering preserves the `.ts`/`.tsx` trigger without unsupported Cursor frontmatter. |
| `unslop` | Direct port | [`unslop`](../skills/unslop/SKILL.md) | Specific, human prose editing is portable and preserves facts, voice, and uncertainty. The full skill remains on demand, while concise always-included Kiro steering preserves the source's must-always-apply contract. |
| `why` | Direct port | [`why`](../skills/why/SKILL.md) | Evidence-first rationale recovery is portable; fixed model roles and editor-private transcript assumptions are removed. |

## make-bot-ui safety exclusion

`make-bot-ui` is deliberately discoverable here but has no runnable PK-Stack skill. The upstream
workflow is not merely presentation guidance: it assumes Cursor/Grok Bot routines, secret-card APIs,
a `cursor.sh` webhook endpoint, and automatic privileged Tailscale installation. Porting those
steps would introduce account, secret, network, and host side effects that a reusable on-demand
skill must not authorize.

For a real bot UI request, activate `architect` and design the target environment explicitly:
identify the caller, authentication and secret owner, inbound endpoint, network boundary, deployment
approval, rollback, and a local verifier. Implement only after those choices and permissions are
reviewed. This preserves the useful architecture outcome without importing the unsafe automation.

## Adaptation boundaries

Feature records use PK-Stack's schema-2 executable contract. The bounded initial-map batch accepts
one to five records: upstream's advice to aim for three to five features remains guidance, not a
minimum that requires inventing features. Generation proves one representative's full lifecycle;
maintenance covers every feature and repeats a live path after a repair. Port-added mandatory
duplicate proof runs have been removed. New development may start with a reviewed failing command
bound to a native Kiro spec, then publish a reusable feature record after the implementation passes.
This uses the existing verification loop without changing upstream's launch, doctor, drive,
evidence-survival, or cleanup requirements.

The shipped skills keep execution inside the current Kiro agent session. Kiro IDE 1.x and Kiro CLI
v3 are primary; Kiro Crew is compatible; Kiro Web is supported by design but remains untested. The
port uses native skills and sub-agents where helpful, and projectctl for deterministic project state
and proof. It does not vendor or execute upstream scripts, assume editor-private transcripts, add an
alternate agent runtime, hard-code model identifiers, auto-publish, install networking software,
delete worktrees, or introduce Graphite and watcher workflows.
