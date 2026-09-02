# PK-Stack Floci ECS integration lab

This repository is a production-shaped local integration lab for a two-service document
export path. The API accepts a tenant-scoped export request and writes a DynamoDB job plus
an SQS message. The worker consumes the message, writes a JSON result to S3, and records a
terminal DynamoDB state. A redrive policy provides bounded retries and a DLQ.

It uses real Docker-backed ECS through exactly
`floci/floci:2.0.1@sha256:4e451c39c7bb88e3cd4f87e8fc0c25d5b47695a51185d521e2241fa00486e8eb`.
It does not use a mock ECS implementation or Kubernetes.

## Quick start

`uv sync --locked --no-config` is required once. Then run the full lifecycle, in order:

```sh
./labctl doctor --output json
./labctl up --acknowledge-docker-socket --output json
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
./labctl down --output json
```

Every JSON-mode failure is one bounded JSON object and has a nonzero exit status. `up`
creates a fresh run identifier unless `--run-id` is supplied. It only starts the outer
Floci Compose control plane and provisions run-owned SQS, DLQ, DynamoDB, S3, and ECS
cluster resources. `deploy` builds a `linux/arm64` image, registers task-definition
revisions, creates the API and worker ECS services, and waits for both.

The host endpoint is exactly `http://127.0.0.1:4566`; task endpoints are exactly
`http://floci:4566` on `pk-stack-lab-net`. Client construction rejects every other host
endpoint, including default AWS endpoints, credential-bearing URLs, paths, queries, and
fragments. All SDK clients have an explicit endpoint, fixed `us-east-1` region, and local
dummy credentials. No credentials are printed.

## Safety and cleanup

`labctl doctor` resolves the active Docker context socket rather than assuming
`/var/run/docker.sock`. The discovered socket is only mounted into Floci at that container
path. `up` requires an explicit acknowledgement because access to that socket is
root-equivalent control of the selected Docker daemon. API/worker ECS definitions have no
socket mount. Docker Compose owns the deterministic network; per-run infrastructure uses an
opaque claim ID plus exact ownership tags and local state stores the manifest, the selected
context/socket/daemon identity, and immutable deployment identity. `down` stops only the two
exact services, confirms their tasks exit, validates
every resource's tags before deleting it, removes the Floci Compose service, then independently
checks for task containers, the Floci container, and the named network leak.

The loopback emulator is unauthenticated for the lifetime of a run. Use a disposable Docker
daemon and do not expose port 4566 beyond the local machine.

See [architecture](docs/architecture.md), [usage](docs/usage.md),
[test strategy](docs/test-strategy.md), [limitations](docs/limitations.md), and the
[validation report](docs/validation-report.md).
