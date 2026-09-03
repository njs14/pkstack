# Limitations

## Kiro workflow boundary

Kiro 2.21.0 exposes custom-Power installation through the Powers UI rather than a `kiro-cli
powers` command. The combined repository structurally validates the Agent Plugins manifest and
executes the Power-local setup/idempotence/doctor path in a fresh project, but the automated
campaign did not drive the graphical import click path. The selected-profile workflow itself was
then exercised in a real Kiro v3 terminal session. Until Kiro exposes a corresponding CLI command,
an end user must still complete and confirm the graphical Power import manually.

Kiro IDE 1.x chat/Agent Focus is a first-class target and the installed 1.0.437 build plus shared
workspace assets are structurally validated, but this snapshot has no separate GUI end-to-end
repair campaign. Kiro Crew compatibility is required while Crew itself remains optional. A
checksum- and signature-verified `0.6.0-nightly.20260903t061110` installation passed only the
public `--version`, `--help`, and `doctor` surfaces; no Crew end-to-end verified-goal campaign is
claimed. Crew's internal Kiro CLI/ACP transport is not PK-Stack's normal launcher.

That bounded Crew smoke exposed an upstream packaging limitation. Invoking the Nightly CLI
rewrote bundled Python `.pyc` files and invalidated the signed application seal even with
`PYTHONDONTWRITEBYTECODE=1`. The mutated copy was moved recoverably to Trash and a fresh exact
bundle was restored and re-verified without another invocation. A later CLI invocation may
reproduce the mutation until upstream packaging moves runtime caches outside the signed bundle.
This does not indicate a PK-Stack source mutation, but it prevents treating one pre-launch
signature check as durable post-launch integrity evidence.

Kiro Web is supported by design and explicitly untested. Its honest path is an already
bootstrapped repository with committed `.kiro` and `.pstack` assets. Web cannot select a project
custom agent as primary or apply the local IDE/CLI permission surface, and its sandbox still needs
the controller's Python 3.11+/`uv` prerequisites. Configuration Sync cannot upload the complete
PK-Stack custom Power because custom cloud Powers are text-only, limited to 50 files, and do not
write back to local `.kiro`.

PK-Stack adds a current-session skill and deterministic repository state; it neither supplies nor
depends on Kiro's documented native `/goal` loop. A sterile interactive Kiro CLI 2.21.0 V3 probe
treated `/goal clear` as ordinary prompt text, so this tested runtime does not expose the
documented slash command. Prompt and skill instructions guide the model, while `projectctl` owns
only the executable contract, bounded attempt count, and terminal state. A disabled Stop hook is
advisory, not a blocker. The normal workflow is ordinary interactive Kiro IDE chat/Agent Focus or
`kiro-cli --v3`, not a user-launched external ACP host.

The weekly and manually dispatchable Kiro runtime/documentation canary reduces product-drift
blindness; it is not an autonomous Kiro upgrade mechanism. It resolves the official stable CLI
manifest, verifies and probes the advertised x86_64 Linux headless binary, validates exact
five-agent schema/discovery, and requests the live model inventory without sending a model turn.
`KIRO_API_KEY` exists only in that inventory step after the advertised version, SHA-256, derived
URL, and size exactly match the reviewed pin; an unpinned binary never receives the credential.
The canary does not invoke Anthropic.
IDE metadata, Kiro Crew Nightly feeds, the changelog, `llms.txt`, and relevant documentation hashes
are bounded non-gating observations. The separate Crew command-surface/doctor smoke still does not
prove an IDE, Crew PK-Stack workflow, or Web campaign. A new stable CLI or regression fails red,
but promoting the checksum/version tuple remains manual because the workflows and protected
controller files that carry it are trust roots. The four configured GitHub source repositories
are the only autonomous update sources.

Feature-map validation and feature-backed goals do not require OKF. Broader project-knowledge
search and `knowledge validate --require-okn` require the canonical `okn` executable. When it is
absent, `doctor` reports a warning and PK-Stack remains in feature-map-only knowledge mode.
The `/okf` skill is workflow guidance, not a bundled validator or search engine. PK-Stack does not
install or activate `scaccogatto/okf-skills` scripts, hooks, transcript backfill, MCP server,
visualizer, or GitHub Action. A checksum-verified comparison found that `okfcli/okf` 0.5.0 still
followed a Markdown symlink outside its bundle where canonical `okn` 0.13.0 rejected it. Version
0.5.0 also accepts date-only `stale_after` values while rejecting the authoritative OKF 0.2
explicit-offset datetime form. It is therefore limited to an explicitly named advisory check over
a disposable, immutable, symlink-free copy. It is never a runtime fallback or a normative
`stale_after` gate.

The real selected-profile Kiro campaign is retained as a bounded committed chronology plus an
owner-only externally hashed raw transcript. Its 12-line client-log projection contains Kiro's
internal `ACP session/new`, `ACP session/prompt`, `ACPEventAdapter`, and
`autonomyMode: "Autopilot"` labels. Those are internal protocol/controller terms, not evidence that
the user launched an ACP-first workflow; the custom `pstack` profile still applied its tool policy
and ask-gated permissions. The projection does not contain discrete source-write or deploy-command
records, so those claims rely on the hashed raw transcript, stored goal, and byte-level source
audit. BSD `script` did not echo its own launch argv, so the exact command and single user-launched
process remain harness metadata; the transcript proves the V3 UI, selected
profile/model/effort, actions, and normal session end. This local evidence does not replace clean
independent Fable review or the final Grok sweep. Those council results and private publication
remain unclaimed until their evidence exists.

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

In the historical `live-final-902` run on 2026-09-02, API and worker definitions requested
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
requests use `propagateTags=SERVICE`. Registration requests also include PK-Stack Docker labels,
but Floci's later `DescribeTaskDefinition` projection has omitted those requested fields. That is
distinct from the live Docker containers' Floci-native labels, which are inspected directly. Any
returned mismatch fails closed, but an absent API-projected field is not invented as positive
ownership evidence.

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
Compose-definition digest, so restore an edited `compose.yaml` before normal cleanup can delete the
exact claim-owned outer container and network. Teardown does not run project-wide `docker compose
down`; a foreign attachment to the lab network is preserved and makes the exact network deletion
fail closed. Never delete or reconstruct `.lab-state/run.json` by guessing.

Before creating that claim, `up` inspects the exact content-addressed Floci dependency and, only if
needed, performs a quiet ten-minute-bounded pull of that same digest. Compose then runs with
`--pull never`. An interrupted preflight can leave shared immutable Docker cache layers, but it
cannot leave a claimed Compose container or network. After the claim, any failed startup remains
normal manifest-backed recovery work. The automatic missing-image branch intentionally recognizes
one exact Docker daemon diagnostic and otherwise fails closed. If a Docker version or locale emits
a different missing-image message, pull the same pinned reference manually and rerun `up`:

```sh
docker image pull \
  floci/floci:2.0.1@sha256:4e451c39c7bb88e3cd4f87e8fc0c25d5b47695a51185d521e2241fa00486e8eb
```

Do not replace the digest with a mutable tag.

A completed deployment generation binds its source digest and observed Docker image ID in the
append-only journal. If that image is deleted outside `labctl`, rebuilding identical source may
produce a different image ID and the same-digest generation correctly refuses adoption. External
image deletion is outside the recovery guarantee. Use a genuine new source digest and deployment
when the live state is otherwise sound; if deployment cannot safely continue, complete the
supported teardown and start a new run. Do not edit the journal to accept a replacement image.

`--teardown-unreachable-emulator` is an explicit discard of an unreachable emulator's
ephemeral AWS-shaped state and cannot prove resource-by-resource deletion. It requires a typed
connection, timeout, DNS, or socket failure; HTTP 4xx/5xx responses, malformed response JSON, and
ambiguous probe errors fail closed. If a reachable plan was already frozen, the flag first requires
the same proof of transport unreachability and durably records a
one-way transition whose prior-plan hash and completed prefix remain validated. All frozen
Docker, image, claim, ledger, Compose, and AWS-inventory targets are preserved; only the canonical
AWS-free phase sequence changes. A persisted transition remains authoritative on retry, even if
the flag is omitted. State-less image
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

The external judge also intentionally rejects any `src/**/__pycache__`: existing `.pyc` files can be
loaded as executable input. Validation commands and the Kiro campaign must prevent bytecode writes;
loosening that source-closure rule would weaken the independent evidence boundary.
