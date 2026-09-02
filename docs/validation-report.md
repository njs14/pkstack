# Validation report

This report separates deterministic local checks, controller proof, the live Docker-backed Floci
campaign, Kiro-session evidence, and model-council acceptance. A pass at one boundary is not
reported as a pass at another. The current snapshot is candidate-complete through a fresh
exact-source Floci campaign and external judge. The selected-profile Kiro campaign and final
council gates are still pending. The older `live-final-902` evidence remains below as historical
context and is not substituted for the current run.

## Bootstrap and controller provenance

PK-Stack was generated from the reviewed Power/controller source and retains a 49-file ownership
receipt in `.pstack/bootstrap.json`. The maintained controller source suite passed **508 tests** at
source commit `191997501c41ae078b6548b9d6c898aadf2907ae`. The generated controller was compared
byte-for-byte with that source before the current lab-only hardening work.

The repository-local generated controller currently reports:

```sh
.pstack/bin/projectctl doctor --output json
.pstack/bin/projectctl feature validate --output json
.pstack/bin/projectctl knowledge validate --output json
```

Observed result: 39 doctor checks passed, zero failed, and one optional warning reported that
canonical `okn` is unavailable. All 49 receipt-managed files matched their recorded hashes. The
one ready `document-export` feature contract had zero errors and warnings. Knowledge validation
passed in explicit `feature-map-only` mode; strict broader OKF validation was not claimed.

An isolated temporary repository also exercised ready feature generation, validation, execution,
and a bounded stored goal. Goal `4360c683-7cc7-4bda-b0a5-c2b70b009735` recorded attempt 1 as a
real failure and attempt 2 as passed after the smallest fixture repair. That proves controller
state transitions, not a Kiro session.

## Candidate static gate

After the final pre-live safety audit, all of these commands exited zero:

```sh
env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync pytest -p no:cacheprovider -q
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --no-config --no-sync ruff check .
uv lock --check
git diff --check
sh -n labctl
./labctl doctor --output json
```

Pytest passed **285 tests** in 5.58 seconds. Ruff and diff checks were clean; the lock resolved 15
packages. Doctor proved Docker server access through context `desktop-linux`, daemon
`fabba3a8-3367-4971-9e85-efbdb563f86f`, the Unix socket at
`unix:///Users/noahsutter/.docker/run/docker.sock`, loopback endpoint
`http://127.0.0.1:4566`, task endpoint `http://floci:4566`, and the pinned Floci 2.0.1 digest.

The `labctl` launcher was also exercised through its fresh non-editable isolated uv environment,
explicit uv-managed Python 3.12 selection, and forced package reinstall. The judge source-closure
precondition saw exactly the five declared `src/pk_stack_lab/*.py` files and no bytecode or added
source.

The post-round-1 audit added regression coverage for state-directory ownership, complete
ledger-bound active identities, untagged-S3 create/tag recovery, stale-image partial cleanup,
bounded subprocess output/process-group termination, every destructive inner-phase crash, and
terminal manifest cleanup. The final audit additionally made every ECS describe/list path reject
unexpected structured failures and bound teardown's Compose input to the original run claim.

Fable round 2 then drove command-level negative verifier proofs, an in-snapshot controller suite,
a durable frozen-plan reachable-to-discard transition, exact build-backend pinning and lock-derived
runtime closure, verifier-cleanup precedence, narrower stale recovery, and pre-claim proof of the
digest-pinned Floci image. A subsequent independent audit retained compatibility with pre-transition
schema-v2 teardown journals and tightened discard authorization to typed transport failures rather
than HTTP or malformed-response failures. The 285-test result above covers those changes; it is
static evidence and is kept distinct from the live proof reported below.

## Fresh current-source live Floci campaign: `live-council-902`

The consolidated round-2 candidate used only the public control surface:

```sh
./labctl up --run-id live-council-902 --acknowledge-docker-socket --output json
# Add one controlled comment to src/pk_stack_lab/runtime.py.
./labctl deploy --output json
# Restore runtime.py byte-for-byte to the candidate.
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
```

`up` created claim `4067444c7226e55f423724a97ea19229` only after proving the exact pinned
Floci image. It recorded state schema v2 and Compose digest
`ffc0ae8024ceb2487f13efc4ee71a0c5c02f89e800e5657bb65783892bd45e38`.
Both generations stabilized one API and one worker service:

| Generation | Runtime file SHA-256 | Source digest | Docker image ID | API/worker revisions |
| --- | --- | --- | --- | --- |
| controlled marker | `b64d1c4bc8a633e55007837e461b8ec973587453244dd0f7f6e8659f11ad444b` | `fe4452a36c08d14638166f01d26524ade85e87c36d6d9dd6e175ea9b9bd14ed9` | `sha256:63e9551f47a51b88a4a45ec7700f7660b34a5a4173abb51ff0e830ac54d3f41c` | `:1` / `:1` |
| restored candidate | `83a05fcc163e8f72b418cb72834967e8d274bebfe872d4608ad393c18469cfe9` | `10e7e74db272a52be501983cb3a9254647937e89c3682042aadb7f15892ceded` | `sha256:5b717a85e8779bab02d58558d297f8578804bcbc2b8a6644a8abff7d2f57a9a3` | `:2` / `:2` |

The 16-event append-only ledger retained both operations. The restored API task was
`4eed6ec2d30a42769dfc7f7ce8abd7e5`; the worker task was
`b78f459c28ad49d592f27d669ad91a90`. Direct verification returned `ok: true` for export
`e-513072ed1a319a99` and current-invocation DLQ message
`c164f054-68a6-400e-9139-fec0a752081a`. It proved duplicate POST identity, terminal
`COMPLETE`, exact S3 JSON/content type/ETag, tenant-key partition separation, duplicate worker
delivery consumed as a no-op with attempts still 1 and unchanged S3 identity, both container
identities before business mutation, and post-business deployment reproof.

Docker 29.7.2 and Compose 5.5.0 ran both application containers as `65532:65532` without mounts
on `pk-stack-lab-net`. The task definitions requested read-only root filesystems, `CapDrop: ALL`,
and `no-new-privileges`; Floci 2.0.1 again did not propagate those three settings to Docker. The
evidence reports this emulator limitation explicitly.

### Current external judge

The judge controls were frozen before the temporary marker and the candidate bytes were restored
before invocation. The owner-controlled files are outside Git under
`/private/tmp/pk-stack-judge-live-council-902.ZsvRPv`; the judge is mode 0500 and its exact
14-path manifest is mode 0400. The invocation was:

```sh
/usr/bin/python3 -I -B \
  /private/tmp/pk-stack-judge-live-council-902.ZsvRPv/controls/verify_feature_contract.py \
  --repo /Users/noahsutter/git-projects/pk-stack-lab \
  --expected-contract-sha256 cc10d305410139155e5071bdd067dc780c2be51cbd7d404479f45e8fe3b59a04 \
  --control-manifest \
    /private/tmp/pk-stack-judge-live-council-902.ZsvRPv/controls/control-manifest.json
```

It exited zero without stderr:

```json
{
  "contract_sha256": "cc10d305410139155e5071bdd067dc780c2be51cbd7d404479f45e8fe3b59a04",
  "control_manifest_sha256": "74956851bc41617e0a051c5b70cff105d028f0c62552f234082224e884a48b6a",
  "judge_sha256": "d47418287932afbfa851593eb348d053c658fe683cd63b559cb4349c326646ab",
  "ok": true
}
```

All 14 protected hashes matched both before and after the judge, and the executable source closure
remained exactly the five declared Python files with no bytecode or import-time customization.

### Current teardown and noninterference

```sh
./labctl down --output json
```

Normal reachable teardown exited zero, accounted for four ECS tasks and four immutable image
references, and completed all eight frozen phases in order. Exact postcondition probes found no
`.lab-state`, `pk-stack-lab-floci`, `pk-stack-lab-net`, restored-generation task containers, or
any of the four current-run generation tags. A full before/after foreign-image comparison was
unchanged, including all retained `pklab-ci-003` through `pklab-ci-010` tags and:

```text
pklab-live-r2-902-api:d8f448b8302cb827d588aabe    250c0499c7c0
pklab-live-r2-902-worker:d8f448b8302cb827d588aabe 250c0499c7c0
```

## Historical exact-tree live Floci campaign: `live-final-902`

Commit `2fcacc0` used the public interface only. This remains useful lifecycle evidence, but it was
superseded as current-candidate proof when the round-2 executable remediations landed:

```sh
./labctl up --run-id live-final-902 --acknowledge-docker-socket --output json
./labctl deploy --output json
# Remove the controlled temporary build-input marker.
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
```

`up` created claim `ddfc9f0d56d0deb47c208157cd5541fa` with canonical state schema v2,
Compose digest `ffc0ae8024ceb2487f13efc4ee71a0c5c02f89e800e5657bb65783892bd45e38`,
and a cleared S3-create intent after successful tagging. Both deployment generations stabilized
one API and one worker service:

| Generation | Source digest | Docker image ID | API/worker revisions |
| --- | --- | --- | --- |
| controlled marker | `8ed57e672518fe41188f5b9ec2275eca9ad57eba65f157def997971e443dba12` | `sha256:4b5b4315c29eb040870840764d323a2ee4aeb4eaa04fc569675e9302139963c1` | `:1` / `:1` |
| restored candidate | `d36f1eabc87725beab70b474a4777637520edb118a10bcecf7c20ad905a8977e` | `sha256:4566a83166a5ddb123b72a205b08aefd3cf2da700f337a89e8c41692226e58f7` | `:2` / `:2` |

The append-only ledger retained all 16 planned and observed image/task-definition events. The
active API task was `2e147d27a9e44c57b2f8bee70102f730`; the worker task was
`07458654a12d46d5aa5034aa1b146094`.

The live verifier returned `ok: true` for export `e-387e74ba4a1222f1`. It proved API request
idempotency, terminal `COMPLETE`, exact object
`exports/tenant-a/e-387e74ba4a1222f1.json`, exact JSON body/content type/ETag, tenant-key partition
separation, duplicate worker delivery as a consumed no-op with attempts remaining at 1 and S3
identity unchanged, and current-invocation DLQ message
`ca59a186-ac07-47fb-819a-f96427a816e0`. Post-business identity reproof passed.

Both application containers ran as `65532:65532` on `pk-stack-lab-net`, with no mounts and exact
image/task/run/claim/operation/source identity. Task definitions requested read-only rootfs,
`CapDrop: ALL`, and `no-new-privileges`; Floci 2.0.1 demonstrably did not propagate those three
controls to Docker. Evidence reported them as emulator limitations rather than claiming they were
effective.

## External judge

While that generation was live, an owner-controlled read-only external copy of the judge and
an independent read-only control manifest invoked exactly the checkout's verifier:

```sh
python3 /private/tmp/pk-stack-judge-final-902.037z1V/verify_feature_contract.py \
  --repo /Users/noahsutter/git-projects/pk-stack-lab \
  --expected-contract-sha256 cc10d305410139155e5071bdd067dc780c2be51cbd7d404479f45e8fe3b59a04 \
  --control-manifest /private/tmp/pk-stack-judge-final-902.037z1V/control-manifest.json
```

It exited zero with:

```json
{
  "contract_sha256": "cc10d305410139155e5071bdd067dc780c2be51cbd7d404479f45e8fe3b59a04",
  "control_manifest_sha256": "05df1735d8b702c9c9a54e23eae0c90cc81aa49ac94e1e3aaa9d9ac30529c041",
  "judge_sha256": "d47418287932afbfa851593eb348d053c658fe683cd63b559cb4349c326646ab",
  "ok": true
}
```

The external judge and manifest were direct, single-link files with modes 0500 and 0400. The
judge bounded stdout, rejected any stderr, rehashed all protected files before and after, required
the exact executable-source closure, and parsed the fixed-size resource projection rather than the
internal artifact ledger.

## Historical exact teardown and noninterference

```sh
./labctl down --output json
```

`down` exited zero and reported four ECS tasks, four immutable image references, and every frozen
phase complete in order:

```text
aws_compute_absent
aws_data_absent
aws_definitions_cluster_absent
aws_postconditions_passed
docker_outer_absent
floci_data_absent
docker_images_absent
local_postconditions_passed
```

Independent exact-name/reference queries then found no `live-final-902` images, no Floci outer
container, no Floci ECS task container, no `pk-stack-lab-net`, and no `.lab-state`. Pre-existing
foreign image tags remained unchanged:

```text
pklab-live-r2-902-api:d8f448b8302cb827d588aabe    250c0499c7c0
pklab-live-r2-902-worker:d8f448b8302cb827d588aabe 250c0499c7c0
```

## Council and current-session status

Sol Advisor v0.6.0 supplied build-phase advice and is recorded as advisory, not acceptance.
Fable 5.1 round 1 reviewed commit `0b000d359b99f34ee5001088548ca872322e734a`; round 2 reviewed
commit `2fcacc054fd62e55a8d57107d35b73e3d1d1582c`. Both ran at max effort and returned material
findings. Round-2 remediations are locally green but have not yet received a fresh immutable-source
Fable disposition. The real one-process interactive
`kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max` fail-repair-pass campaign is
also still pending. Grok 4.6 `xhigh` runs only after clean Fable acceptance on that exact commit.
Private GitHub publication is likewise not claimed yet.
