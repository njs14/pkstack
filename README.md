# PK-Stack (Poteto Kiro)

<p align="center">
  <img src="powers/pk-stack/assets/logo.png" alt="PK-Stack: the Kiro ghost reimagined as a scholarly golden potato" width="260">
</p>

This repository ships the canonical installable PK-Stack Power under `powers/pk-stack/` and its
realistic acceptance fixture at the repository root. PK-Stack is a Kiro-native workflow layer for
doing implementation work in the user's current Kiro agent session and proving completion with
repository-owned checks. Kiro CLI v3 and Kiro IDE 1.x chat/Agent Focus are the first-class primary
surfaces; Kiro Crew is a compatible optional orchestrator; Kiro Web is supported through committed
workspace assets by design but remains untested. Kiro owns execution and orchestration; PK-Stack
owns workflow semantics; the repo-local `projectctl` owns deterministic project operations and
verification; source-controlled OKF plus canonical `okn` is the deeper project-knowledge interface.

The acceptance fixture is a two-service document-export
application running through Floci's Docker-backed ECS subset. The API writes a tenant-keyed
DynamoDB job and SQS message. The worker writes a JSON result to S3 and records terminal state;
bounded retries end at a DLQ. It uses real Docker task containers through
`floci/floci:2.0.1@sha256:4e451c39c7bb88e3cd4f87e8fc0c25d5b47695a51185d521e2241fa00486e8eb`.
It does not use Kubernetes, a mock ECS implementation, AWS Fargate, or a real AWS account.

`PK-Stack` and `Poteto Kiro` are the user-facing names. The lowercase `pstack` agent name and
`.pstack/` directory are stable compatibility identifiers used by Kiro and existing workspaces.

## Use PK-Stack in Kiro

Clone this private repository, then import the local `powers/pk-stack/` directory through Kiro's
Powers panel. That directory has the Agent Plugins `plugin.json`, source, lock, skills, and
templates. The root `.pstack/projectctl/` directory is generated fixture output and is never an
installation or upgrade authority. Keeping one canonical Power source plus parity-checked output
avoids a second hand-maintained implementation.

In Kiro IDE 1.x, open chat or Agent Focus and choose the workspace `pstack` agent from the agent
picker. In Kiro CLI, start an ordinary interactive v3 session with the same generated profile:

```sh
kiro-cli chat --v3 --agent pstack
```

PK-Stack inherits the model and effort selected by the user; it does not make Sol/max an
interactive default. Kiro recommends Auto for general development, Sol for the hardest long-horizon
work, Terra for routine multi-step work, and Luna for high-frequency work. The recorded acceptance
campaign deliberately used Sol/max, but `--effort` persists for that model and higher effort consumes
more credits, so that validation configuration is not a neutral quick-start command. See the
[versioned model and surface guidance](powers/pk-stack/docs/kiro-v3-compatibility.md#models-effort-and-verification-methodology).

For nontrivial feature or bug work, start with Kiro's native planning workflow. In CLI v3, use
`/spec new <name>` and choose Feature, Quick Spec, or Bug; in the IDE, use **Build with spec** or
the workflow picker. Standard Spec is for unfamiliar or high-risk work, while Quick Spec is for a
bounded, well-understood change. Kiro owns the resulting requirements or bug analysis, design,
tasks, and native dependency waves. When those artifacts are ready, reselect `pstack` in the same
IDE/CLI conversation and let PK-Stack bind the spec to a published feature verifier. Kiro does not
document a supported Agent Skill or custom-agent tool for changing the active workflow, so
PK-Stack neither invokes nor emulates that client action.

Then invoke the workspace skill in that same Kiro agent session:

```text
/verified-goal Repair the document-export tenant-key partition-separation regression.
```

`/verified-goal` is a PK-Stack skill with a repository-visible contract, separate from Kiro's
documented native `/goal`. It intentionally does not invoke or depend on native `/goal`. A sterile
interactive Kiro CLI 2.21.0 V3 probe treated `/goal clear` as ordinary prompt text, so this
repository does not claim that the tested runtime exposes the documented command; re-probe after
Kiro updates. The sanitized [versioned probe record](reviews/kiro-v3-native-goal-probe.json)
binds that observation to hashes of the externally retained raw evidence. `/verified-goal` keeps
the agent in the current session while
`.pstack/bin/projectctl` stores a bounded objective, its exact executable acceptance contract,
attempts, and results. ACP is not the default path. Kiro Crew may use ACP internally when it owns a
session, but Crew remains optional. Native Kiro skills, custom agents, sub-agents, permissions,
hooks, steering, native Spec/Quick Spec/Bug Fix workflows, and `/knowledge` remain available where
they fit. PK-Stack starts context at the spec-linked feature map and descends into canonical `okn`
only for broader architecture, decisions, concepts, or operations. Native `/knowledge` may index
the same source-controlled Wiki but does not replace it. The `/okf` skill supplies Kiro-native
produce, maintain, and consume workflows for that Wiki; it selectively adapts the useful method
from `scaccogatto/okf-skills` without installing its Claude-specific hooks, transcript backfill,
validator, MCP server, or visualizer.

Kiro Web's honest path is a repository that already commits its bootstrapped `.kiro` and `.pstack`
assets. Web can activate `/verified-goal`, but project custom agents are delegation-only there and
the local primary-agent permission boundary does not apply. A complete custom-Power upload through
Configuration Sync is not supported: custom cloud Powers are text-only and capped at 50 files,
while PK-Stack exceeds that shape. See the [Kiro surface compatibility and evidence
matrix](powers/pk-stack/docs/kiro-v3-compatibility.md), including the September 1-2, 2026 change
inventory and the explicitly untested Web boundary.

See [usage](docs/usage.md) for Power setup, an exact before/after comparison, direct `projectctl`
commands, and recovery procedures.

## Let PK-Stack maintain itself

The combined repository uses the same levers it ships: a ready feature contract, a bounded
`projectctl` goal, the `/maintain-pk-stack` skill, a checksum-pinned Kiro CLI, canonical-Power
regeneration, and deterministic verification. The scheduled Kiro workflow checks every hash-pinned
source daily: Cursor pstack for workflow semantics, `scaccogatto/okf-skills` for OKF workflow
methodology, and Google Knowledge Catalog for the normative OKF specification. When several sources
move together, it selects and reviews exactly one source per transaction so pins, inventories,
provenance, and acceptance never become ambiguous. Real drift must fail attempt 1, receive one
exhaustive A/B/C path review and provenance record, and pass a later attempt before the workflow can
publish one non-draft bot PR; the next daily run then picks up any remaining source. A no-drift run
stops before Kiro or Fable is invoked, so faster backlog draining does not spend model credits on a
clean repository.

The candidate workflow independently tests the unchanged base and exact candidate, then requires
Fable 5.1 at `xhigh` to approve the exact base/head/content/patch identity before an API-only squash
merge. Upstream patches and reviewer output remain untrusted data throughout. Kiro credentials
exist only inside the four bounded repair steps and are destroyed before candidate code or
secretless verification runs. The GitHub Agentic Workflows/Copilot route is manual-only recovery;
it never silently substitutes for Kiro.

Hosted maintenance requires the repository Actions secret `KIRO_API_KEY` and exactly one of
`ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN`. Missing reviewer credentials fail closed instead
of shipping an unreviewed operational change. See the [maintenance feature
contract](Wiki/features/pk-stack-upstream-maintenance.md), [architecture](docs/architecture.md),
and [review ledger](reviews/acceptance-ledger.md).

## Run the Floci acceptance fixture

Prerequisites are macOS on ARM64, `uv`, and a running Docker daemon. The lifecycle is:

```sh
./labctl doctor --output json
./labctl up --acknowledge-docker-socket --output json
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
./labctl down --output json
```

`up` creates a fresh run identifier unless `--run-id` is supplied. It starts the pinned Floci
control plane and provisions run-owned SQS, DLQ, DynamoDB, S3, and ECS cluster resources. `deploy`
builds an immutable `linux/arm64` image, registers API and worker task-definition revisions, and
activates a generation only after both services stabilize. A later `deploy` is a supported repeat
deployment; failed candidates remain in the artifact ledger while the prior stabilized generation
remains the recorded active identity. Verification then requires the checkout's build inputs to
match that active source digest.

The host endpoint is exactly `http://127.0.0.1:4566`; task endpoints are exactly
`http://floci:4566` on `pk-stack-lab-net`. SDK construction rejects every other endpoint,
including default AWS endpoints and credential-bearing URLs. Clients use fixed `us-east-1` and
dummy local credentials. No real cloud credentials are needed or printed.

## Safety boundary

The active Docker context socket is mounted only into Floci, at `/var/run/docker.sock`. `up`
requires `--acknowledge-docker-socket` because that mount grants root-equivalent control of the
selected Docker daemon. Application task definitions have no Docker socket or host mounts.

All lifecycle commands take an owner-only non-blocking lock. State schema v2 stores the exact
Docker daemon claim, the original Compose-definition digest, an append-only planned/observed
artifact ledger, the last stabilized deployment, and a hash-bound teardown plan with durable phase
checkpoints. Cleanup validates exact
AWS tags plus task, task-definition, image, container-environment, claim, network, and daemon
identity before mutation. It removes only the frozen target set and unlinks the state manifest
last.

The emulator is unauthenticated while running. Port 4566 is bound to loopback, but the Docker
network is not an egress-isolation boundary. Use a disposable Docker daemon and read the
[limitations](docs/limitations.md) before treating the lab as production evidence.

The candidate implementation, final Docker-backed lab evidence, and final local current-session
Kiro campaign are documented separately from model-council acceptance. See
[architecture](docs/architecture.md), [test strategy](docs/test-strategy.md), the
[final Floci campaign](reviews/final-floci-campaign.md)
([machine-readable record](reviews/final-floci-campaign.json)), the
[final Kiro CLI v3 campaign](reviews/final-kiro-v3-campaign.md)
([machine-readable record](reviews/final-kiro-v3-campaign.json)), and the
[validation report](docs/validation-report.md). Independent Fable acceptance, the final Grok
sweep, and private-repository publication remain gated until their own evidence exists.
