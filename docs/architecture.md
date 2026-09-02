# Architecture

## System boundary

PK-Stack (Poteto Kiro) adds workflow semantics to an ordinary interactive Kiro CLI v3 session. It
does not replace Kiro's runtime and does not recreate a goal scheduler.

```text
current interactive kiro-cli --v3 session
  -> Poteto Kiro custom agent and native v3 primitives
  -> PK-Stack skills and steering
  -> repo-local .pstack/bin/projectctl
       -> DO: stable project commands
       -> PROVE: feature contracts and bounded verified-goal state
       -> KNOW: feature map, with canonical OKF tooling when installed
  -> project-specific interfaces such as ./labctl
```

Kiro retains execution and orchestration: `/spec`, workspace skills, custom agents, native
sub-agents, `/spawn`, hooks, permissions, steering, and `/knowledge` are used where appropriate.
PK-Stack contributes the workflow contract around those primitives. The generated `pstack` agent
is deliberately permission-scoped and selects trusted PK-Stack sub-agents. `/spawn` creates a
separate session and is therefore not part of a current-session `/verified-goal` proof unless the
user explicitly asks for parallel session work.

`/verified-goal` is a workspace skill, not a native Kiro `/goal`. In one current session it selects
an existing feature-map verifier or one explicit project command, displays the stored contract and
provenance, and delegates attempt accounting to `projectctl goal verify`. The deterministic state
machine is thin: `active` becomes `passed` when the same stored verifier succeeds or `exhausted`
when its bounded attempt budget ends. A disabled Stop hook can report advisory state, but it is not
control-flow enforcement. ACP is not used for the normal path.

The canonical controller entrypoint is `.pstack/bin/projectctl`. The controller uses Cyclopts only
as a thin command surface over typed bootstrap, feature, goal, knowledge, doctor, and runner
modules. The bootstrap-managed runtime is locked and repository-local. A host project's
`./projectctl` is preserved rather than assumed to be PK-Stack, and a cached controller cannot
authorize its own upgrade without an explicitly reviewed Power root.

## Floci document-export fixture

The fixed Docker Compose project starts one pinned Floci control-plane container on
`pk-stack-lab-net` and publishes only `127.0.0.1:4566`. `FLOCI_HOSTNAME=floci` keeps returned AWS
URLs routable from task containers. The active Docker-context socket is mounted into Floci at
`/var/run/docker.sock`; repository-local `.lab-state/floci-data` is bound to `/app/data` so the
image does not create an anonymous volume. API and worker task containers have neither mount.

`deploy` builds one immutable `linux/arm64` application image and registers separate API and
worker ECS task-definition families with `runtimePlatform` set to `ARM64`/`LINUX`, bridge
networking, and fixed CPU and memory. The API listens on port 8080; the worker exposes no port.
Floci starts real Docker containers for these ECS services. This is a Docker-backed subset of ECS,
not Fargate, EC2-host parity, or an AWS cloud simulation with production semantics.

In observed Floci 2.0.1 behavior, ECS reports a bridge binding but does not publish the API port to
the macOS host. Verification derives the exact API task container from its ECS task ARN, proves its
identity, and reaches it using a transient hardened verifier container on the dedicated network.
It never uses `docker exec` inside an application task and never claims host-loopback API
reachability.

The task environment carries the explicit Floci URL and fixed region plus application resource
names. It also carries immutable identity fields for role, run ID, opaque claim ID, deployment
operation ID, and source digest. Cleanup and verification join those values with:

- exact owned ECS service tags;
- cluster, task ARN, task-definition family, and exact active revision;
- Floci's native Docker container name and `io.floci.resource-id` labels;
- exact application image reference and image ID; and
- the selected Docker daemon, dedicated network, non-root user, and empty mount list.

Floci 2.0.1 has omitted propagated ECS task tags and requested task-definition Docker labels in
observed runs. Returned mismatches still fail closed, but absent fields are not invented as proof;
the environment-bound identity chain above is the compatibility seam.

## State schema v2 and deployment activation

Every `labctl` command acquires the owner-only `.lab-lifecycle.lock` with a non-blocking `flock`,
so two lifecycle mutations cannot overlap. `up` then atomically creates canonical
`.lab-state/run.json` with `O_CREAT|O_EXCL`. State reads, replacements, and final unlink use
directory-relative no-follow operations and reject links, unexpected entries, wrong ownership,
permissions, or schema fields.

Schema v2 contains two different histories:

1. An append-only artifact ledger records image and task-definition `planned` events before each
   corresponding Docker or Floci mutation, then records the exact `observed` identity. Events have
   contiguous sequence numbers and bind role, operation ID, source digest, image reference/image
   ID, family, and task-definition ARN. Interrupted registration can be reconciled to that journal
   without overwriting or guessing.
2. The top-level active deployment identity is last-good state. It changes atomically only after
   both ECS services stabilize on a ledger-covered image and pair of task definitions. A failed
   repeat deployment leaves its candidate artifacts in history for cleanup but does not replace
   the prior recorded active generation. `status`, `verify`, and `evidence` additionally refuse to
   use it while the checkout's build inputs differ from its source digest.

`down` first inventories all run-owned AWS and Docker targets, including every ledgered image and
observed task-definition revision, then freezes that exact plan with the claim ID, ledger head,
ledger hash, the original run's Compose-definition digest, target identities, cleanup strategy,
ordered phases, and a plan hash. The current direct `compose.yaml` must still match that original
digest immediately before any first-pass or resumed Compose teardown mutation. Artifact and
deployment activation are forbidden after the plan is frozen. Each successfully reproved phase is
durably appended to the completed ordered prefix. After interruption, `down` resumes from the
first incomplete phase instead of rebuilding target scope. The manifest remains until AWS compute
and data, definitions and cluster, task containers, the outer Floci container, local data, images,
network, and final local postconditions are all proved according to the frozen mode.

## Security and non-goals

Task definitions request user `65532:65532`, read-only root filesystem, all capabilities dropped,
and `no-new-privileges`. Live evidence enforces the non-root user and zero mounts. It separately
reports requested and effective values because Floci 2.0.1 has not applied the other three Docker
controls in observed task containers.

The host endpoint is syntactically restricted to loopback and every AWS client receives an
explicit endpoint, fixed region, and local dummy credentials. That prevents accidental default
AWS resolution; it does not create technical egress isolation. The Docker network cannot be
`internal` while preserving the prescribed host-to-Floci path, and the socket gives Floci
root-equivalent authority over its Docker daemon.

The fixture intentionally has no real IAM authorization, VPC/subnet/security-group semantics,
ECR, ELB, CloudWatch Logs, durable storage, production capacity, or AWS rollout fidelity. These
constraints and the explicit recovery modes are detailed in [limitations](limitations.md).
