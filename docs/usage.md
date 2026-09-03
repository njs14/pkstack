# Usage

## PK-Stack in a Kiro agent session

The installable Agent Plugins package is `powers/pk-stack/`; import that local directory through
Kiro's Powers panel after cloning the private repository. Do not import `.pstack/projectctl/`: it
is generated acceptance-fixture output and the controller rejects a target-local cache as setup
authority. This repository root is already bootstrapped for the Floci campaign.

Initial bootstrap in another project is performed by the installed PK-Stack Power's
`/setup-pstack` skill. It first
runs the Power-local setup shim as a dry run, reports conflicts and managed updates, and then
creates repository-local `.kiro/` and `.pstack/` assets without overwriting user-owned files.
Managed upgrades require explicit approval. After setup, select the generated Poteto Kiro agent in
the same chat. In Kiro IDE 1.x, choose the workspace `pstack` agent from the chat/Agent Focus agent
picker. In Kiro CLI v3, run:

```text
/agent swap pstack
```

Agent selection applies to the next message. If Kiro IDE has not discovered the new agent or
skill, open one fresh pre-goal chat/Agent Focus session in the same workspace and choose `pstack`.
If Kiro CLI has not discovered it, exit normally and restart from the same repository:

```sh
kiro-cli chat --v3 --agent pstack
```

Do not start a nested Kiro process. For a later managed refresh, the `pstack` profile deliberately
has no Powers: swap in the same chat to the Power-enabled setup agent, run `/setup-pstack`, then
swap back to `pstack` before the next workflow message.

Kiro Crew is a compatible optional orchestrator. It reads committed `.kiro` configuration and
drives Kiro CLI through ACP internally; that transport does not make `kiro-cli acp` the default
PK-Stack entrypoint. Kiro Web is supported by design only from a repository that already commits
the bootstrapped `.kiro` and `.pstack` assets. Web cannot select the project `pstack` agent as its
primary agent or reproduce the local permission profile, and this release has not exercised the
Web workflow end to end. Do not treat Configuration Sync as a complete custom-Power install: its
custom Powers are text-only and limited to 50 files, while PK-Stack exceeds that shape. The exact
surface/evidence boundary is in the [compatibility matrix](../powers/pk-stack/docs/kiro-v3-compatibility.md).

PK-Stack's custom agents inherit the user's active model and effort. Normal commands intentionally
omit both flags: Kiro recommends Auto for general development, while Sol/max is a high-cost choice
reserved here for the recorded hard acceptance campaign. Kiro persists a CLI `/effort` or
`--effort` selection for that model, so users who opt into max should deliberately choose their
desired normal level afterwards. The canonical compatibility guide records the Sol/Terra/Luna
trade-offs, experimental lifecycle and AWS processing-geography boundary, and the optional IDE-only
property-based testing methodology.

### Exact before/after interaction

Without PK-Stack, a user can ask Kiro to make a change and separately mention a check, but Kiro has
no PK-Stack goal record tying attempts to that immutable predicate:

```sh
kiro-cli chat --v3
```

```text
Repair the document-export tenant-key partition-separation regression, then run
./labctl verify --output json.
```

With PK-Stack, the ordinary CLI process is still interactive Kiro v3; only the agent profile and
workspace skill are added. The IDE uses the equivalent agent picker and skill invocation:

```sh
kiro-cli chat --v3 --agent pstack
```

```text
/verified-goal Repair the document-export tenant-key partition-separation regression.
```

The skill stays in that session, displays the exact stored feature contract and its provenance,
and uses `.pstack/bin/projectctl goal verify --output json` for every attempt. A failing verifier
keeps the goal `active` until its budget is exhausted; a passing invocation records `passed`.
`/verified-goal` is separate from documented native `/goal`. A sterile interactive Kiro CLI 2.21.0
V3 probe treated `/goal clear` as ordinary prompt text, so the tested runtime does not expose that
slash command. PK-Stack does not invoke or depend on it, and no external ACP host is involved.

The deterministic surface is also usable directly:

```sh
.pstack/bin/projectctl doctor --output json
.pstack/bin/projectctl feature list --output json
.pstack/bin/projectctl feature show document-export --output json
.pstack/bin/projectctl feature validate --output json
.pstack/bin/projectctl knowledge validate --output json
.pstack/bin/projectctl goal start \
  "Repair tenant-key partition separation" \
  --feature document-export \
  --max-attempts 4 \
  --output json
.pstack/bin/projectctl goal verify --output json
.pstack/bin/projectctl goal status --output json
```

Feature generation is a two-level safety boundary. Without `--ready`, it creates a draft that
cannot be run by `feature verify` or serve as goal evidence. With `--ready`, it runs the proposed
verifier successfully before publishing the ready contract:

```sh
.pstack/bin/projectctl feature generate ready-check \
  --title "Ready check" \
  --behavior "The project passes its focused readiness check." \
  --expected-path "The focused test exits successfully." \
  --command "python3 tests/ready_check.py" \
  --ready \
  --output json
```

Replace the illustrative command with an existing project-specific verifier. Generation refuses
unsafe command shapes and existing slugs unless an overwrite is explicitly requested.

Use the canonical `.pstack/bin/projectctl`, not an ambient root `./projectctl` or
`uv run projectctl`. Do not hand-edit `.pstack/state/goal.json`, weaken its verifier, automatically
add attempts, or force-clear active evidence. `goal resume --add-attempts N` is reserved for an
explicit user extension after exhaustion. Broader `knowledge search` and strict OKF validation
require the canonical `okn` command; feature-map validation remains available without it.

## Floci lab lifecycle

Run the public interface in order:

```sh
./labctl doctor --output json
./labctl up --run-id ci-001 --acknowledge-docker-socket --output json
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
./labctl down --output json
```

Only lowercase letters, digits, and interior hyphens are accepted in a 1-32 character run ID. If
`--run-id` is omitted, `up` generates one. `doctor` checks `uv`, Docker daemon readiness, active
context/socket identity, the Compose-resolved pinned Floci digest, and both allowed endpoint
forms. `up` requires the explicit socket acknowledgement and performs a complete exact-name
collision inventory before provisioning any AWS-shaped resource.

`deploy` builds and journals a candidate, registers task definitions, creates or updates the two
services, and publishes active identity only after both stabilize. It is safe to run again after a
source change:

```sh
./labctl deploy --output json
./labctl verify --output json
```

All earlier and failed-candidate images/task-definition revisions remain in the artifact ledger so
the eventual frozen teardown plan covers them. `status`, `verify`, and `evidence` first rebind the
current state to the exact outer container, Docker daemon, and active generation.

`verify` creates and reads the happy-path export only through the deployed API; it never
manufactures a passing DynamoDB row. It then uses controlled SQS deliveries to prove worker
duplicate handling and redrive. Together the checks cover API acceptance, duplicate request
identity, worker completion, S3 result contents, terminal DynamoDB state, tenant-key partition
separation, a real duplicate SQS delivery as a worker no-op, and a fresh invalid-message DLQ
redrive. Before and after that business flow it reproves both ECS tasks and their exact Docker
containers. When Floci lacks a host port, a separately owned bounded verifier container reaches
the API over `pk-stack-lab-net`; it never runs `docker exec` in an application task.

`evidence` reports the active immutable resource and deployment identities plus requested and
effective task security. `verify` deliberately projects resource evidence to a fixed bounded
schema for the external judge; the unbounded schema-v2 ledger and teardown journal stay internal
to the recovery manifest.

## State and normal recovery

Mutable lab data stays under ignored `.lab-state/`. A valid existing manifest is never overwritten:
resume with the appropriate lifecycle command, normally `./labctl down --output json`. Corrupt,
tampered, linked, nonregular, incorrectly owned, or noncanonical state fails closed. An empty state
directory can be reused, but an unexplained entry must be resolved rather than erased by `up`.

Normal `down` freezes its first complete inventory before mutation. It removes exact task
containers before AWS data, drains every unversioned S3 object page, removes all recorded
task-definition revisions and image references, checkpoints each phase, reproves the outer/local
boundary between phases, and unlinks `run.json` last. Re-run the same command after interruption;
it uses the persisted plan and ordered journal rather than rediscovering a different target set.

If Floci is demonstrably unreachable and its ephemeral AWS-shaped state cannot be queried, an
operator may explicitly choose local control-plane discard:

```sh
./labctl down --teardown-unreachable-emulator --output json
```

This mode is authorized only when the health probe fails with a typed transport error such as a
connection refusal, timeout, DNS failure, or unreachable socket. Any HTTP response, including
4xx/5xx, malformed response JSON, or ambiguous probe failure is evidence that the endpoint
responded or that unreachability was not proved; PK-Stack fails closed without freezing a discard
plan. The discard path does not construct AWS clients and removes only exactly claimed
Docker/local/image targets. Treat it as intentional loss of the unreachable emulator's ephemeral
state, not proof that AWS-shaped resources were individually deleted.

The same flag is also the explicit recovery path if normal `down` already froze a reachable plan
but Floci became unreachable before cleanup finished. PK-Stack atomically records a one-way
reachable-to-discard transition before the next mutation. The transition keeps the original
plan's claim, ledger and Compose hashes, AWS inventory, Docker objects, and exact image targets;
it also records the prior plan hash and completed phase prefix. Any already-checkpointed local
phases map onto the canonical discard prefix, and retry resumes only its remaining local phases.
Once that transition is recorded, a later retry follows the persisted discard plan even without
repeating the flag and never falls back to AWS discovery. Successful JSON output reports both
`control_plane: "discarded"` and a bounded `control_plane_transition` summary. Unless the health
probe proves transport unreachability under the same strict rule, the transition is refused
without changing the frozen reachable plan.

If an interrupted normal teardown removed the manifest but left one or both immutable application
image tags from one exact generation, stale-image recovery is dry-run first and requires the
recorded full identity tuple:

```sh
./labctl down --recover-stale \
  --run-id ci-001 \
  --claim-id "$RECORDED_PK_CLAIM_ID" \
  --source-digest "$RECORDED_PK_SOURCE_DIGEST" \
  --image-id "$RECORDED_PK_IMAGE_ID" \
  --output json

./labctl down --recover-stale --apply-stale-recovery \
  --run-id ci-001 \
  --claim-id "$RECORDED_PK_CLAIM_ID" \
  --source-digest "$RECORDED_PK_SOURCE_DIGEST" \
  --image-id "$RECORDED_PK_IMAGE_ID" \
  --output json
```

Recovery refuses if `.lab-state`, the outer container/network, or any Floci ECS task container is
present. It requires at least one of the two tags to remain and matches every remaining tag by exact
image ID and provenance labels before deletion; this lets a retry finish after a hard exit removed
the first tag.

## JSON behavior

Once the Python CLI starts, ordinary JSON-mode success or failure is emitted as one bounded JSON
object and failures use a nonzero status. The `labctl` shell launcher intentionally does not wrap
failures that occur before Python starts. A missing or broken `uv`, for example, is a shell-level
diagnostic and is outside that JSON guarantee. Stored verifier stdout/stderr is bounded by
`projectctl` (64,000 characters by default) and records whether truncation occurred.
