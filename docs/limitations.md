# Limitations

## Floci 2.0.1 effective-security limitation (live-r3-902)

On 2026-09-02, `live-r3-902` registered API and worker definitions requesting
`user: 65532:65532`, `readonlyRootFilesystem: true`, Linux `CapDrop: [ALL]`, and
`dockerSecurityOptions: [no-new-privileges]`. Floci 2.0.1 accepted those API fields but
launched both Docker containers with this actual inspection result:

```text
user=65532:65532 readonly=false capdrop=null security=null mounts=[]
```

`./labctl evidence --output json` therefore failed closed with `real ECS task container did
not enforce required security fields`. The missing effective fields are an accepted emulator
limitation for this local lab, but the lab must not claim read-only root filesystem, dropped
capabilities, or no-new-privileges under this Floci version. The exact run was torn down using
`./labctl down --output json`; a subsequent
read-only check found no Floci container, `pk-stack-lab-net`, `pklab-live-r3-902-*` tags, or
`.lab-state`.

The attempted `internal: true` Docker network is also incompatible with the prescribed host
endpoint. The pinned Floci container remained `healthy`, but `./labctl deploy --output json`
returned `Could not connect to the endpoint URL: "http://127.0.0.1:4566/"`. The network is
therefore intentionally not marked internal; this is documented behavior, not an isolation claim.

Floci's ECS implementation starts real Docker task containers but is not AWS Fargate. It does
not establish AWS IAM policy enforcement, VPC/subnet/security-group behavior, CloudWatch Logs,
capacity limits, image registry/ECR authentication, durable storage, production rollout
semantics, or a load balancer. Local `bridge` networking and any dynamically published loopback
port are deliberately laboratory-only. Docker Desktop availability and the pinned image pull
are external prerequisites.

Floci's data is ephemeral for this lab but is deliberately a repository-local bind mount rather
than an image-declared anonymous Docker volume. `down` removes only the validated
`.lab-state/floci-data` directory after the Floci container stops; it never scans or deletes
Docker volumes broadly.

In the observed Docker Desktop/Floci 2.0.1 run, ECS task metadata reported a bridge port
binding but the API container had no host-published port. The legacy in-task `docker exec`
transport is therefore not an acceptable proof boundary. A hardened, separately owned verifier
container is required before the complete external acceptance can be claimed; it must have no
socket, mounts, AWS credentials, or privilege expansion. Until that implementation is proven on
Floci 2.0.1, host-loopback reachability and in-network verifier isolation are external gaps.

The same emulator returns exact ownership tags for ECS services but, in ci-011, omitted task tags
from `DescribeTasks(include=TAGS)` and returned `[]` from `ListTagsForResource`, even though
both ECS `create_service` and repeat `update_service` explicitly requested
`propagateTags=SERVICE`. The lab treats a returned mismatched task tag set as a failure, but its
current-run task proof therefore relies on exact owned service tags plus task ARN/family, Docker
name, Floci `io.floci.resource-id`, image, network, role, and empty mounts. This is evidence of
the local emulator chain, not a claim of AWS task-tag parity.

The worker's invalid-message exercise proves the configured SQS redrive boundary. It does not
model every SQS timing or duplicate-delivery behavior in AWS. Its terminal-state guard makes
an already-completed message a no-op, which is the application idempotency property tested by
the verification flow.

The `tenant` request parameter is an unauthenticated partition key, not caller identity,
authorization, or a security boundary. The status GET returns metadata and the deterministic
object key, never the object body. “Tenant-key partition separation” is the accurate local
property; this lab does not claim tenant isolation security.
