# PK-Stack (Poteto Kiro)

This repository ships the canonical installable PK-Stack Power under `powers/pk-stack/` and its
realistic acceptance fixture at the repository root. PK-Stack is a Kiro CLI v3 workflow layer for
doing implementation work in the user's current interactive session and proving completion with
repository-owned checks. Kiro owns execution and orchestration; PK-Stack owns workflow semantics;
the repo-local `projectctl` owns deterministic project operations and verification; OKF is the
optional interface for broader project knowledge.

The acceptance fixture is a two-service document-export
application running through Floci's Docker-backed ECS subset. The API writes a tenant-keyed
DynamoDB job and SQS message. The worker writes a JSON result to S3 and records terminal state;
bounded retries end at a DLQ. It uses real Docker task containers through
`floci/floci:2.0.1@sha256:4e451c39c7bb88e3cd4f87e8fc0c25d5b47695a51185d521e2241fa00486e8eb`.
It does not use Kubernetes, a mock ECS implementation, AWS Fargate, or a real AWS account.

`PK-Stack` and `Poteto Kiro` are the user-facing names. The lowercase `pstack` agent name and
`.pstack/` directory are stable compatibility identifiers used by Kiro and existing workspaces.

## Use PK-Stack in Kiro v3

Clone this private repository, then import the local `powers/pk-stack/` directory through Kiro's
Powers panel. That directory has the Agent Plugins `plugin.json`, source, lock, skills, and
templates. The root `.pstack/projectctl/` directory is generated fixture output and is never an
installation or upgrade authority. Keeping one canonical Power source plus parity-checked output
avoids a second hand-maintained implementation.

Start an ordinary interactive v3 session with the generated Poteto Kiro profile:

```sh
kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max
```

Then invoke the workspace skill in that same session:

```text
/verified-goal Repair the document-export tenant-key partition-separation regression.
```

`/verified-goal` is a PK-Stack skill, not a native Kiro `/goal` command. It keeps the agent in the
current v3 session while `.pstack/bin/projectctl` stores a bounded objective, its exact executable
acceptance contract, attempts, and results. ACP is not the default path. Native v3 skills, custom
agents, sub-agents, permissions, hooks, steering, `/spec`, and `/knowledge` remain available where
they fit.

See [usage](docs/usage.md) for Power setup, an exact before/after comparison, direct `projectctl`
commands, and recovery procedures.

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

The candidate implementation, automated/lab evidence, and local current-session Kiro campaign are
documented. Independent Fable acceptance, the final Grok sweep, and private-repository publication
remain gated until their evidence exists. See [architecture](docs/architecture.md),
[test strategy](docs/test-strategy.md), the [Kiro campaign record](reviews/kiro-v3-campaign.md),
and the [validation report](docs/validation-report.md).
