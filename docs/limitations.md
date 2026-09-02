# Limitations

## Kiro workflow boundary

PK-Stack adds a current-session skill and deterministic repository state; it does not add a native
Kiro CLI v3 `/goal` command or runtime scheduler. Prompt and skill instructions guide the model,
while `projectctl` owns only the executable contract, bounded attempt count, and terminal state. A
disabled Stop hook is advisory, not a blocker. The normal workflow is ordinary interactive
`kiro-cli --v3`, not ACP.

Feature-map validation and feature-backed goals do not require OKF. Broader project-knowledge
search and `knowledge validate --require-okn` require the canonical `okn` executable. When it is
absent, `doctor` reports a warning and PK-Stack remains in feature-map-only knowledge mode.

The candidate implementation, isolated controller exercises, and Floci lab tests are not by
themselves proof of a real Kiro current-session fail-repair-pass campaign. Final acceptance must
retain that transcript and then record clean independent Fable review and the final Grok sweep.
Those results, and private-repository publication, remain unclaimed until their evidence exists.

## Floci is a Docker-backed ECS subset, not Fargate

Floci starts real Docker task containers, but it is not AWS Fargate and does not reproduce EC2
container-instance behavior or full ECS control-plane semantics. The lab does not establish real
IAM authorization, VPC/subnet/security-group behavior, ECR authentication, CloudWatch Logs,
capacity limits, load balancing, durable storage, or production rollout behavior. Application
images are built for `linux/arm64`; this fixture is intentionally Mac/ARM64-specific.

In observed Docker Desktop/Floci 2.0.1 runs, ECS metadata reported a bridge port binding while the
API container had no host-published port. Host-loopback API reachability is therefore not claimed.
The verifier uses a separately owned container on the exact lab network after proving the API task
identity. It has no socket, mounts, AWS credentials, or privilege expansion, but this remains a
local compatibility path rather than cloud-network evidence.

## Effective container security

In the fresh `live-final-902` run on 2026-09-02, API and worker definitions requested
`user: 65532:65532`, `readonlyRootFilesystem: true`, Linux `CapDrop: [ALL]`, and
`dockerSecurityOptions: [no-new-privileges]`. Floci 2.0.1 accepted those fields but launched both
Docker containers with:

```text
user=65532:65532 readonly=false capdrop=null security=null mounts=[]
```

The current evidence model enforces the non-root user and zero mounts, and reports requested and
effective values for the other fields plus a machine-readable emulator-limitations list. It does
not claim that Floci applied read-only root filesystem, capability drop, or no-new-privileges.

The active Docker-context socket is mounted into Floci. That is root-equivalent authority over the
selected daemon even though application tasks do not receive the socket. Use a disposable daemon
with no unrelated sensitive workloads.

## Network and credential scope

Port 4566 is published only on `127.0.0.1`, SDK clients reject any non-exact endpoint, and the lab
passes fixed local credentials rather than ambient AWS credentials. These are strong accidental
cloud-use guards, not an outbound firewall.

An attempted `internal: true` Docker network left the pinned Floci container healthy but made the
required host endpoint unreachable. The network is therefore intentionally not internal. Floci,
task containers, and build steps can have technical egress through Docker's normal networking;
the lab does not claim egress isolation.

The emulator endpoint is unauthenticated while a run is active. Do not expose it beyond the local
host or run untrusted workloads on the network.

## Missing propagated metadata

Observed Floci 2.0.1 behavior returns exact ownership tags for ECS services but has omitted task
tags from `DescribeTasks(include=TAGS)` and `ListTagsForResource`, even when create and update
requests use `propagateTags=SERVICE`. It has also dropped requested task-definition Docker labels.
Any returned mismatch fails closed, but absence is not treated as positive ownership evidence.

The compatibility chain instead requires exact service tags, task ARN and family, active
task-definition revision, Floci native container name and `io.floci.resource-id`, image reference
and ID, dedicated network, and the task environment's run, claim, role, operation, and source
digest. That proves the local current-claim chain; it does not prove AWS tag-propagation parity.

## Application scope

The `tenant` request field is an unauthenticated partition key, not caller identity,
authorization, or a security boundary. GET returns metadata and the deterministic object key,
never the object body. “Tenant-key partition separation” is the property under test; the lab does
not claim tenant isolation security.

The invalid-message case proves the configured SQS redrive boundary, not every AWS timing or
delivery behavior. The worker's terminal-state guard makes an already-completed delivery a no-op,
which is the application idempotency property checked here.

## Recovery limits

The schema-v2 ledger and frozen teardown journal make interrupted local cleanup resumable; they do
not make arbitrary state loss recoverable. The run claim and teardown plan bind the original
Compose-definition digest, so restore an edited `compose.yaml` before normal cleanup can invoke
Compose. Never delete or reconstruct `.lab-state/run.json` by guessing.
`--teardown-unreachable-emulator` is an explicit discard of an unreachable emulator's
ephemeral AWS-shaped state and cannot prove resource-by-resource deletion. State-less image
recovery handles only one or both remnants of one exact two-tag generation with a supplied run,
claim, source digest, and image ID. It refuses a fully absent initial target, any surviving Floci
task container, or an outer boundary. Normal schema-v2 state also carries a narrow S3-create
intent so a hard exit between bucket creation and ownership tagging can be cleaned without
treating an arbitrary untagged bucket as owned.

Floci data is a validated repository-local bind mount, not a Docker anonymous volume. Normal
`down` removes it only after the outer container stops and all prior phases are checkpointed. No
recovery mode scans or broadly deletes Docker volumes, images, containers, or networks.

Finally, the `labctl` launcher can promise a single bounded JSON response only after Python starts.
A missing/broken `uv` or other launcher failure remains a shell diagnostic.
