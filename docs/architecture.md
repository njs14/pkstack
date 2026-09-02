# Architecture

The fixed outer Docker Compose project starts one pinned Floci control-plane container on
the deterministic `pk-stack-lab-net` network. It publishes only `127.0.0.1:4566`. Floci
receives the active Docker context socket at `/var/run/docker.sock` and is configured with
`FLOCI_HOSTNAME=floci`, so AWS URLs returned to tasks remain routable inside the task network.
Its image data directory `/app/data` is explicitly bind-mounted to ignored repository-local
`.lab-state/floci-data`; this prevents Docker from creating an anonymous volume. API and worker
tasks have neither bind mount.

`deploy` builds a local ARM64 image and registers two ECS task-definition families, each
with `runtimePlatform` `ARM64`/`LINUX`, `bridge` networking, fixed CPU/memory, and labels.
The API listens on container port 8080 and the worker exposes no port. In the observed Floci
2.0.1 Docker Desktop mode, ECS metadata advertises a bridge binding but Docker does not publish
that binding to the macOS host. Verification therefore performs bounded HTTP from inside the
exact API task container, derived from the ECS task ARN and verified against Floci ECS labels
and the dedicated network. It does not claim host-loopback API reachability. This still uses
Floci's Docker-backed ECS behavior, not an ECS mock.

The task environment contains no IAM role or Docker socket. It contains only task-network
Floci URL, fixed region, queue URL, table name, bucket name, and role. Application logs are
intentionally minimal and omit HTTP bodies and credentials. Floci is responsible for Docker
container lifecycle; the lab's ownership labels are additional evidence, not an authorization
to affect foreign containers.

Lifecycle authority is an atomically created canonical `.lab-state/run.json` claim. It is
created with `O_CREAT|O_EXCL` before any resource mutation and read, written, and removed through
a directory-relative no-follow descriptor. If any later provisioning or local data cleanup
fails, the manifest remains for recovery; it is unlinked only after external cleanup, Compose
teardown, leak inspection, and Floci-data removal succeed. Exact owned ECS service tags, the
cluster/task ARN and family, and the Docker name, `io.floci.resource-id`, image, network, and
empty mounts form the current-run chain. `deploy` explicitly requests `propagateTags=SERVICE`
on both create and update. In observed ci-011 Floci 2.0.1 results,
`DescribeTasks(include=TAGS)` still omitted task tags and `ListTagsForResource` returned `[]`,
despite exact service tags and the propagation request. The lab fails on any returned task-tag
mismatch but does not invent unavailable task tags. Floci also does not propagate requested
task-definition docker labels, so neither absent label set is claimed as ownership evidence.

The lab intentionally has no ELB, ECR, Terraform, real IAM authorization, durable disk, or
external AWS traffic. Floci is Fargate-shaped rather than AWS-parity: ECS networking,
rollouts, scheduling, Docker images, task logs, persistence, and IAM semantics should be
validated separately before treating this lab as cloud-production evidence.
