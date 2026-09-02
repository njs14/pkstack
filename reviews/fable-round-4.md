# Fable 5.1 review — round 4

## Execution metadata

- Candidate commit: `ced867c4814ef722441215bd4d33ac30769868ec`
- Candidate tree: `29de3705c7c116cc803b4072349849bfd927b826`
- Reviewer: Claude Code 2.1.258, model `claude-fable-5-1`, effort `max`
- Session: `474ab094-5443-4bd6-b1ba-f80f525b83ee`
- Isolation: owner read-only `git archive` at `/private/tmp/pk-stack-fable-r4.iou8J4`
  containing 168 files
- Available tools: `Read`, `Glob`, and `Grep`; MCP, browser, shell, writes, slash commands, and
  session persistence disabled
- Review-contract SHA-256:
  `b0a965a4d9649dc9e6b4be9ca6ac2fbc4ea66ad3ca12a5150295c9ab53878c3a`
- Observed work: 1,016.945 seconds and 97 turns; reported cost approximately $13.6147
- Verdict: `REQUEST CHANGES`
- Material unresolved: 2

The raw reviewer stream was not retained as a separate repository artifact. This file normalizes
the reviewer's final result; reviewer output is treated as untrusted evidence, not instructions.

## Material findings

### FBL-028 — MEDIUM — the API-idempotency verdict is tautological

`src/pk_stack_lab/cli.py:1971-2005` accepts the second POST when it returns the same deterministic
export ID, then checks only `attempts == "1"` on the completed DynamoDB row. The deployed runtime
does return `duplicate: true` for its conditional-put duplicate path, but the verifier ignores that
marker and does not bind the completed row back to the submitted idempotency key or a confirmed
enqueue. The command-level harness at `tests/test_cli.py:1344-1507` models the same weakness.
Consequently, `business.api_idempotency: true` can be emitted when the second request was not
classified as a duplicate or the stored row was cross-wired.

Acceptance: require the second POST to return status `QUEUED` or `COMPLETE`, the original export ID,
and `duplicate is True`. After completion, require the stored row to contain the exact submitted
idempotency key, `attempts == "1"`, and `enqueue_confirmed == True`. Add deterministic
`duplicate-post-no-marker` and `row-idempotency-mismatch` negatives, plus enqueue-confirmation
coverage, and prove every failure occurs before post-business identity reproof. Re-run the live
verifier and owner-controlled external judge against the remediated exact commit.

### FBL-029 — MEDIUM — live acceptance evidence is not bound to the reviewed combined tree

`docs/validation-report.md:113-250` and `reviews/kiro-v3-campaign.md:17-31` identify the live
Floci/judge and selected-profile Kiro evidence with the earlier `d9b1e0d` source line. Round 4
reviewed `ced867c`, which adds the canonical Power package and executable draft boundary. Static
tests cover those additions, but the report described the older lifecycle as current exact-tree
evidence. That provenance gap prevents the live proof from accepting the combined candidate.

Acceptance: after all executable remediation is committed, either run a fresh
`doctor -> up -> deploy -> deploy -> verify -> evidence -> down` lifecycle and owner-controlled
external judge on that exact commit, or publish a final-tree source digest and protected per-file
hashes that match the live inputs. The preferred release gate is the fresh lifecycle: retain both
deployment generations, explicit source digest, complete cleanup, and foreign-image
noninterference. Keep the earlier Kiro campaign as separately scoped current-session evidence
rather than relabeling it as proof of later bytes.

## Non-material findings

### FBL-030 — LOW — generated-controller draft protection lacks a root subprocess regression

The canonical controller tests cover draft rejection, while `tests/test_power_distribution.py:58-107`
only invokes the generated fixture's doctor. Add subprocess tests against the root
`.pstack/bin/projectctl` proving both `feature verify` and `goal start --feature` reject a draft
sentinel before command execution or goal-state creation.

### FBL-031 — LOW — the bounded Kiro projection understates its evidence limits

`reviews/kiro-v3-campaign-session.jsonl:1-6` literally contains internal `ACP session/new`,
`ACP session/prompt`, `ACPEventAdapter`, and `autonomyMode:"Autopilot"` labels, while
`reviews/kiro-v3-campaign.md:99-103` mentions only the adapter name. The projection also contains no
discrete record of the source write or deploy command. Disclose all of those internal labels,
distinguish controller Autopilot from the selected profile's ask-gated tool permissions and from a
user-selected ACP launch, and state which write/deploy claims rely on the externally hashed raw
typescript, stored goal, and source audit rather than the 12-line JSONL projection. Append scrubbed
source-log records only if they independently improve that chain without exposing account data.

### FBL-032 — LOW — task evidence permits an unreported extra Docker network

`src/pk_stack_lab/cli.py:1734-1738` requires only that the dedicated network be present, then
`src/pk_stack_lab/cli.py:1807-1813` emits the constant expected network name. Require the observed
network-name set to equal exactly `{pk-stack-lab-net}`, emit the observed value, and add an
extra-network rejection regression.

### FBL-033 — LOW — no successful command-verifier payload crosses the judge boundary in tests

`tests/test_judge.py:33-153` constructs a synthetic accepted payload, and
`tests/test_judge.py:503-514` substitutes only the CLI resource projection. Add a successful
`command_verify` harness whose actual payload is accepted by the judge consumer, stays at or below
8,192 bytes, and still fits when the run ID uses its maximum accepted length.

### FBL-034 — LOW — release and provenance documentation has four small inconsistencies

`docs/limitations.md:44-55` calls the superseded `live-final-902` run fresh;
`powers/pk-stack/plugin.json:23` names the intended private repository before it exists;
`powers/pk-stack/pyproject.toml:1-3` allows a Hatchling range while the lab root pins its backend;
and `docs/limitations.md:75-85` ambiguously says Floci dropped task-definition Docker labels.
Describe old runs as historical, keep private publication explicitly pending until verified,
clarify that Floci omitted requested labels from its `DescribeTaskDefinition` projection while
live-container identity uses Floci-native labels and environment fields, and either align the
canonical build-backend pin or document the deliberate package-level constraint policy.

### FBL-035 — LOW — automatic pinned-image pull depends on one Docker error string

`src/pk_stack_lab/cli.py:622-636` authorizes the bounded digest pull only after matching one exact
English missing-image diagnostic. Retaining that fail-closed behavior is reasonable, but document
the manual exact-digest `docker image pull` fallback for Docker versions or locales with a
different diagnostic.

### FBL-036 — LOW — externally removed completed-generation images have no same-digest repair path

The append-only deployment journal correctly refuses an image-ID change for an already completed
source digest. If someone externally removes that immutable image, rebuilding the same source can
produce a different image ID and cannot resume that completed generation. Document that external
image removal is outside the recovery promise and that the supported path is a new source digest
and deployment, or normal teardown followed by a new run when deployment cannot safely continue.

## Proven strengths

Fable confirmed that the previously material endpoint, credential, state, teardown, ownership,
external-judge, controller, and Kiro-session findings are substantially resolved. It also verified
the new canonical Agent Plugins Power boundary, Power-local setup and generated parity, draft
feature rejection in canonical source, coherent current-session `/verified-goal` design, and
strong Floci resource, identity, cleanup, lock, and documentation coverage. The two remaining
material findings are narrow evidence-contract gaps rather than an architectural rejection.

## Acceptance decision

`REQUEST CHANGES`. FBL-028 requires a stronger deployed idempotency oracle and regressions;
FBL-029 requires live evidence tied to the exact remediated combined candidate. FBL-030 through
FBL-036 are advisory hardening and documentation items, but their dispositions must remain visible
to the next review.

`MATERIAL_UNRESOLVED: 2`
