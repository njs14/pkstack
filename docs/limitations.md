# Limitations

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
binding but the API container had no host-published port. `verify` therefore performs bounded
HTTP only from inside the exact real ECS API task container, derived from the ECS task ARN;
it does not claim host-loopback reachability. This is the smallest honest local workaround and
should be replaced with a loopback-only host binding if a later Floci version publishes one.

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
