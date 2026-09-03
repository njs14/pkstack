# Validation report

This report separates deterministic local checks, controller proof, Docker-backed Floci evidence,
Kiro-session evidence, and model-council acceptance. A pass at one boundary is not reported as a
pass at another. In particular, evidence-carrier commits are not described as though every byte in
them was executed retrospectively.

The current candidate lineage is:

| Role | Commit and tree | Evidence boundary |
| --- | --- | --- |
| Historical round-4 remediation | commit `cb2cb0905687c3e94e539333d8945c37109f6189`, tree `c28e71a050185f19befb3832e865c4e54f2bcf03` | Closed the then-current Fable findings and powered the superseded `fable-r5-902` run. It is not the final executable candidate. |
| Final executable candidate A | commit `28b918268104cbcd19b18486dcb4134213c6351a`, tree `72fe6177d20eea67b6580899c1134d586be987c0` | Exact executable tree exercised by `final-floci-902`. |
| Floci evidence carrier / Kiro executable candidate B | commit `2a1afb8a301c952b655ffe9e8a0981adff3c324c`, tree `c0a2f4b84f169d86d2295f15dbbf9b5a37e98b4e` | Adds only the normalized final-Floci records to A; exact tree exercised by `kiro-final-902`. |
| Round-5 council-review candidate C | commit `491bfdafc94832c6624ed86051955b1067245979`, tree `e314bd4ab33e492b905a080b43c4ea8bdfba6828` | Carries the final Kiro records and review-contract documentation. Fable 5.1 reviewed this exact immutable tree at `xhigh`; no live campaign is retroactively claimed against C. |
| Historical executable candidate D | commit `8806fa607b991d8e3ca9d004f2724412596f715d`, tree `bd0488dc2b184c39c0a6c538d5f2d2ebf73375cf` | Exact detached archive independently exercised by `final-okf-campaign` and `final-floci-903`. The campaign records were produced afterward; neither their later evidence-carrier bytes nor any later tree is claimed as executed. |
| Hosted-control candidate E | commit `6e8d4bbe25d549faa5f07378139d92de60294410`, tree `c4360f55963437d70079d7566997e20b047e2a60` | Exact tree for the hosted maintenance fail-fast run. Its planning and authenticated drift-detection jobs passed, but reviewer readiness failed before Kiro because no credential was configured under either accepted Fable secret name. No native-Spec, successful maintenance, or final-council execution is claimed for E. |
| Native-Spec executable candidate F | commit `0dbc53c33b16de426af7e134b5faa7e819b25f97`, tree `8ed46899995163d3ef9693ff167d8a9d9bf489ec` | Exact detached tree exercised by `native-spec-903`: native Bug Fix Spec, spec-backed current-session verified goal, frozen external judge, and exact owned teardown. The later evidence-carrier commit is not retrospectively claimed as executed. |

The older `live-final-902`, `live-council-902`, `fable-r5-902`, and `kiro-v3-accept-902`
campaigns remain below as explicitly historical evidence. The newest retained exact-candidate
application records are
the [`final OKF/OKN campaign`](../reviews/final-okf-campaign.md) and
[`final-floci-903` exact-deletion campaign](../reviews/final-floci-deletion-campaign.md). The
[`kiro-final-902` campaign](../reviews/final-kiro-v3-campaign.md) remains historical non-Spec Kiro
evidence. The newer [`native-spec-903` campaign](../reviews/final-native-spec-campaign.md) closes
the final native Spec-to-current-session gate on candidate F and retains the exact generated Spec
package and terminal goal state.

The authorized [`njs14/pk-stack`](https://github.com/njs14/pk-stack) repository now exists and its
visibility was verified as private. Hosted Kiro evidence includes successful credential
[run 33729855987](https://github.com/njs14/pk-stack/actions/runs/33729855987) on exact commit
`99d2784b35a255ebc70585542e8e78b78d05895e`, exact permission-matrix
[run 33736820795](https://github.com/njs14/pk-stack/actions/runs/33736820795) on exact commit
`8c5651927f6ab98fb7967e5ceca8a70bd85b9a9b`, and read-only runtime-canary
[run 33743033801](https://github.com/njs14/pk-stack/actions/runs/33743033801) on exact commit
`7ce09e3dc161965b0cdac01f992e7ec1c89748b0`.

The bounded [maintenance preflight record](../reviews/hosted-maintenance-preflight-campaign.md)
covers [run 33743730700](https://github.com/njs14/pk-stack/actions/runs/33743730700) on exact commit
`6e8d4bbe25d549faa5f07378139d92de60294410`. Immutable planning and authenticated upstream drift
detection passed, then reviewer readiness failed safely because no credential was configured under
either accepted Fable secret name. No Kiro repair turn or publish step ran, and candidate-gate
[run 33743818713](https://github.com/njs14/pk-stack/actions/runs/33743818713) was skipped. This is
fail-closed safety evidence, not a successful autonomous upstream-maintenance lifecycle. Successful
maintenance, exact-tree deterministic and canonical OKF/OKN reproof, and exact-tree model-council
acceptance remain separate open gates; native-Spec proof is complete.

## Bounded KiroCrew Nightly compatibility smoke

The [KiroCrew Nightly smoke record](../reviews/kirocrew-nightly-smoke-campaign.md) and its
[machine-readable companion](../reviews/kirocrew-nightly-smoke-campaign.json) cover the Nightly
listed by the official feed at `2026-09-03T12:02:57Z`, version
`0.6.0-nightly.20260903t061110`. The feed, DMG, exact bundle ID/version, Developer ID Team
`94KV3E626L`, deep signature, and Gatekeeper notarization were verified. The following bounded
commands then passed:

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/noahsutter/.local/bin/kirocrew --version
PYTHONDONTWRITEBYTECODE=1 /Users/noahsutter/.local/bin/kirocrew --help
PYTHONDONTWRITEBYTECODE=1 /Users/noahsutter/.local/bin/kirocrew doctor
```

Doctor concluded `Kiro Crew is ready!` with Kiro CLI `2.21.0`, login/runtime, dependencies, and
MCP tools available; the gateway was not running. The global Crew provider was `acp`, which is a
Crew-owned transport choice and does not alter PK-Stack's ordinary IDE or interactive
`kiro-cli --v3` entrypoint.

The smoke also exposed a material upstream package-integrity limitation: CLI launch rewrote
bundled Python `.pyc` files and invalidated the signed seal even with bytecode writes disabled in
the environment. The mutated application was moved recoverably to Trash, and a fresh exact Sep. 3
bundle was restored and re-verified without another invocation. The repository was at commit
`f6e3440c6a6c6faab1030501baa3c193535207e1`, tree
`f8f28bc5142e6ac67c06dfe0f7a60a9b9fdb752d`, only as worktree context; no immutable PK-Stack tree
was executed. This is command-surface/doctor compatibility evidence, not a Crew GUI, project
trust, PK-Stack workflow, Spec, verified-goal, Task Runner, compaction, model-turn, or release-gate
pass.

## Bootstrap and controller provenance

The canonical installable package is committed at `powers/pk-stack/`. It was imported byte-for-byte
from the independently accepted source commit `191997501c41ae078b6548b9d6c898aadf2907ae`, after
which the pre-Fable audit added one centralized draft-publication guard and regressions. The
original source checkout remained clean and unchanged. The current canonical package suite passed
**769 tests**. Its Power-local setup shim regenerated this fixture's controller; source, skills,
steering, templates, and the runtime lock are parity-tested byte-for-byte.

The generated fixture currently retains a 156-file ownership receipt in
`.pstack/bootstrap.json`.

The repository-local generated controller currently reports:

```sh
.pstack/bin/projectctl doctor --output json
.pstack/bin/projectctl feature validate --output json
.pstack/bin/projectctl knowledge validate --output json
```

Observed result: 130 doctor checks passed, zero failed, and one optional warning reported that
canonical `okn` was unavailable on the ordinary shell `PATH`. All 156 receipt-managed files
matched their recorded hashes. The two ready feature contracts had zero errors and warnings.
Knowledge validation passed in explicit `feature-map-only` mode on that ordinary path. A separate
checksum-verified canonical `okn` 0.13.0 campaign on candidate D validated the seven-file Wiki and
composed feature map with zero issues, then returned bounded ranked context with content-addressed
provenance.

An isolated temporary repository also exercised ready feature generation, validation, execution,
and a bounded stored goal. Goal `4360c683-7cc7-4bda-b0a5-c2b70b009735` recorded attempt 1 as a
real failure and attempt 2 as passed after the smallest fixture repair. That proves controller
state transitions, not a Kiro session.

## Current deterministic static gate

The following commands were rerun on 2026-09-03 after the native-Spec evidence was added:

```sh
env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync pytest -p no:cacheprovider -q

(cd powers/pk-stack && env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync pytest -p no:cacheprovider -q)

python3 .github/scripts/test_pk_stack_maintenance_guard.py
actionlint -ignore 'SC2174:' <all active standard workflow paths>
shellcheck <all .github/scripts/*.sh paths>
.pstack/bin/projectctl doctor --output json
.pstack/bin/projectctl feature validate --output json
.pstack/bin/projectctl knowledge validate --output json
```

The root suite passed 302 tests in 25.87s; the canonical Power suite passed 787 tests in 83.23s;
and the standalone maintenance guard passed 70 tests. Root Ruff and lock checks passed. Canonical
Ruff, format, `ty`, and lock checks passed. Native `actionlint` 1.7.12 passed all active standard
workflows with the intentional `SC2174` warning suppressed, and native ShellCheck 0.11.0 passed all
three standalone workflow scripts. Generated-controller source parity, JSON parsing, receipt
integrity, feature validation, and feature-map knowledge validation passed. Doctor returned
`ok: true` with 130 pass, zero fail, and the single disclosed optional `okn` warning. These checks
supplement, rather than replace, immutable candidate-F Kiro/Floci proof or final model review.

## Retained immutable OKF/OKN campaign

The [`final-okf-campaign`](../reviews/final-okf-campaign.md) executed candidate D from an isolated
`git archive`. The tar embedded exact commit
`8806fa607b991d8e3ca9d004f2724412596f715d` and hashed to
`998708506c9e1eb951848c2df205ab439a238699312aa3866e4dcca65076517f`. Canonical
`openknowledge-sh/openknowledge` 0.13.0 ran outside the candidate root; its Darwin arm64 release
archive and executable matched their pinned SHA-256 values.

The exact command boundary was `projectctl knowledge status`, `feature validate`, strict
`knowledge validate --require-okn`, and one 900-token `knowledge search`. The two feature records
passed with zero errors and warnings. The OKF 0.2 Wiki passed 10 checks across seven files, six
concepts, and one index with zero issues. Search returned six passages using BM25, vector,
reranking, and link expansion at an estimated 879 tokens; every passage retained an exact safe
relative path, line range, content hash, and revision-bound `okf+sha256` locator. The bounded
[JSON record](../reviews/final-okf-campaign.json) preserves commands, artifact hashes, results, and
limits.

This is local Darwin arm64 evidence. It does not exercise the OKN registry, MCP, publishing,
remote knowledge, a Kiro UI/session, Crew, Web, Floci, or application business behavior. It also
does not promote `okfcli/okf` into the runtime path.

## Fresh `okfcli/okf` v0.5.0 comparison: worktree evidence only

The bounded [OKF integration comparison](../reviews/okf-integration-evidence.md) was refreshed
after `okfcli/okf` v0.5.0 shipped. Official Darwin arm64 release archives for `okf` v0.5.0 and
canonical `okn` v0.13.0 were downloaded into an owner-only temporary directory, inspected before
extraction, and matched against both GitHub asset digests and publisher checksums. Nothing was
installed globally and no credential was used.

The refresh re-ran the prior symlink fixture. Canonical `okn` rejected the linked concept with exit
2. `okf` returned exit 0 with zero errors and warnings, and both `show` and `search` returned the
outside body. It also exposed an inverse `stale_after` incompatibility: `okn` passed the
authoritative explicit-offset value `2027-01-01T00:00:00Z`, while `okf` rejected it with
`okf/lifecycle/stale-after-invalid`; `okf` instead accepted the nonconforming date-only value
without a finding. Version 0.5.0 adds useful broken-link, duplicate-source, duplicate-footnote, and
SARIF diagnostics, but it still lacks the ranked, budgeted, revision-bound provenance contract
used by PK-Stack search.

The decision therefore remains unchanged. Canonical `okn` 0.13.0 is the KNOW runtime.
`okfcli/okf` may be an explicitly named advisory CI/SARIF oracle only over a disposable,
immutable, symlink-free copy; it is never a fallback or a normative `stale_after` gate. This probe
was recorded from the clean pre-documentation worktree at commit
`347d461a097f5d26e084f10958641fc4aa70ce07`, tree
`78e5b4e3c1f934486ce2e24707c8ecbbdae7b92a`. It is architecture evidence, not a new immutable
candidate campaign, and it does not close the native-Spec, successful maintenance-lifecycle, or
final model-council gates.

## Retained immutable Floci exact-deletion campaign: `final-floci-903`

The [`final-floci-903` campaign](../reviews/final-floci-deletion-campaign.md) independently executed
the same candidate-D commit and tree from a detached archive with SHA-256
`cc14e34967b9132f985bdc99da92f4ba2b2e713b8077894a3b8b0b7db8a76cfb`. It ran `doctor`, `up`, one
`deploy`, `status`, the built-in verifier, `evidence`, the frozen external judge, and `down` on
Docker Engine 29.7.2, Compose 5.5.0, and pinned Floci 2.0.1. Both the built-in verifier and frozen
judge returned `ok: true` for tenant partition separation, stable idempotency, exact S3 content,
duplicate-worker no-op behavior, current-invocation DLQ evidence, and post-business identity.

Before `up`, the harness planted a hardened foreign sentinel carrying the same
`com.docker.compose.project=pk-stack-lab` label but no PK-Stack ownership claim. Candidate D's
claim-bound teardown completed all eight ordered phases and removed the exact campaign outer
container, network, tasks, data, definitions, and image tags. The sentinel remained running with
the same immutable container ID and bounded inspect hash. Full image, container, network, and
foreign-`pklab` projections were byte-identical after campaign cleanup; the harness then removed
only its re-resolved sentinel and re-proved the pre-sentinel host inventories. The bounded
[JSON record](../reviews/final-floci-deletion-campaign.json) contains the exact identities and
hashes.

This closes the live exact-code gap for `FBL-042`; it remains local ECS-like emulator evidence, not
Fargate, IAM, VPC, cross-account, or AWS control-plane proof. Floci still did not enforce three
requested task-hardening fields. The sentinel used Docker's `none` network, so this run does not
claim a live fail-closed foreign attachment to the dedicated network.

## Prior immutable Floci campaign: `final-floci-902`

That earlier Floci lifecycle exercised candidate A, commit
`28b918268104cbcd19b18486dcb4134213c6351a`, from a detached archive with SHA-256
`fa952d459574bd811c093af13c0771339ea49344f26f6105d6c66780b77cf90c`. Candidate B adds the
normalized record only; this report does not claim that B was the executable used for this run.

The public lifecycle sequence was:

```sh
./labctl doctor --output json
./labctl up --run-id final-floci-902 --acknowledge-docker-socket --output json
# Add one controlled comment to src/pk_stack_lab/runtime.py with apply_patch.
./labctl deploy --output json
./labctl status --output json
./labctl evidence --output json
# Restore runtime.py exactly to candidate A with apply_patch and recheck all 14 frozen hashes.
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
/usr/bin/python3 -I -B /path/to/frozen/verify_feature_contract.py \
  --repo /path/to/detached/candidate \
  --expected-contract-sha256 fc4c32e718f7e4ea2aa0369c24f0bca25d7cfc5af8f64990caf34fdd2214605a \
  --control-manifest /path/to/frozen/control-manifest.json
./labctl down --output json
```

Both services converged on two generations:

| Generation | Source digest | Image ID | API/worker revisions | Operation ID |
| --- | --- | --- | --- | --- |
| controlled marker | `bc4e31fb91605ba5b8c49d3abc5b24be647763e13a6844beb7a37868bc1d677a` | `sha256:c156b1d9e3573d43fdccfbaa87be79b544c298362c320963c17f280b48db6abf` | `:1` / `:1` | `f0c84db3f2b734f7ad576866d4be82f7` |
| restored candidate A | `5241fe8d4203672be0f5ed57ee9e2b2517919841b0632334b13a14a073727fe6` | `sha256:97d0151ea4bc6b357c6d8f5428d499997da0f06bf7d5286a350bf8a2f07186b6` | `:2` / `:2` | `ee0b785291220f882338032de8e8e423` |

The bounded verifier and frozen external judge both returned `ok: true`. The business proof
included tenant-key partition separation, the strengthened API-idempotency contract, exact S3
content, duplicate-worker no-op behavior, current-invocation DLQ evidence, and post-business
identity reproof. Normal teardown accounted for four tasks and four images, completed all eight
phases, and left the complete image, container, and network inventories byte-identical; all 18
foreign `pklab-*` image records were preserved.

This is local ECS-like evidence on pinned Floci 2.0.1, Docker Engine 29.7.2, and Compose 5.5.0. It
does not test Fargate, cloud IAM, VPCs, cross-account behavior, or the AWS production control
plane. Floci did not propagate the requested read-only-root, drop-all-capabilities, or
no-new-privileges settings, although the two task processes ran as UID/GID 65532 without mounts.
The full normalized result and 14-path frozen control map are in
[`reviews/final-floci-campaign.md`](../reviews/final-floci-campaign.md),
[`reviews/final-floci-campaign.json`](../reviews/final-floci-campaign.json), and
[`reviews/final-floci-control-manifest.json`](../reviews/final-floci-control-manifest.json).

## Prior Kiro CLI v3 current-session campaign: `kiro-final-902`

The fresh current-session campaign exercised candidate B, commit
`2a1afb8a301c952b655ffe9e8a0981adff3c324c`. An isolated clone first committed one controlled
tenant-key defect and deployed API/worker revision 1. The harness then launched exactly one
ordinary interactive Kiro CLI v3 process:

```sh
/usr/bin/script -q -F /private/tmp/pk-stack-final-kiro.qL6A0S/raw/kiro.typescript \
  /bin/zsh -c 'umask 077; print -r -- "$$" > /private/tmp/pk-stack-final-kiro.qL6A0S/raw/kiro.pid; exec /Users/noahsutter/.local/bin/kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max'
```

Within that one selected session, `/verified-goal` caused these completed shell commands, in order:

```text
.pstack/bin/projectctl goal status --output json
.pstack/bin/projectctl feature list --output json
.pstack/bin/projectctl feature show document-export --output json
.pstack/bin/projectctl goal start "Repair the deployed document-export tenant-key partition-separation regression in this isolated local Floci lab." --feature document-export --max-attempts 4 --output json
.pstack/bin/projectctl goal verify --output json
./labctl deploy --output json
.pstack/bin/projectctl goal verify --output json
.pstack/bin/projectctl goal status --output json
```

Goal `96e0d0a9-2366-42e9-8869-ca3ffc58e4ed` retained the unchanged feature-map contract
`./labctl verify --output json`. Attempt 1 ran before any source write and failed only on
`tenant-key partition separation check failed`. Kiro invoked native `pstack-verifier` exactly once
read-only, repaired the one runtime line with its file-edit tool, redeployed exactly once, and
passed attempt 2. No third verification, goal replacement/resume, `/spawn`, nested Kiro, native
`/goal` claim, or user-selected ACP path occurred. The worktree then matched candidate B exactly.

The restored deployment reached API/worker revision 2 and the strengthened full business contract
passed. A frozen external judge independently returned `ok: true` while the deployment remained
live; sequential status and evidence calls passed; then normal teardown accounted for four task
instances and four images and completed all eight phases. Kiro reported 559,068 ms (9m19s) and
3.461648 credits with `pstack`, `gpt-5.6-sol`, and `max` retained through goal completion.

The campaign was deliberately realistic rather than configuration-hermetic: the user's configured
Kiro memory hooks and steering were present and wrote ordinary memory. Exact-value scanning found
no supplied secret in the worktree or retained evidence. Docker Desktop Resource Saver also
recreated its built-in `bridge` ID during startup, so containers, images, and all 18 foreign
`pklab` image records were byte-identical while the network inventory was semantically, not
byte-for-byte, identical. Kiro's compact logs contain internal ACP/event-adapter labels, but the
user-facing launch and workflow remained the ordinary CLI v3 current session. This campaign did
not test Web or establish a native `/goal` command. Candidate C carries the normalized evidence
and was not retrospectively exercised.

See [`reviews/final-kiro-v3-campaign.md`](../reviews/final-kiro-v3-campaign.md),
[`reviews/final-kiro-v3-campaign.json`](../reviews/final-kiro-v3-campaign.json), the exact
[`input history`](../reviews/final-kiro-v3-campaign-history.txt), and the bounded
[`session projection`](../reviews/final-kiro-v3-campaign-session.jsonl). Raw terminal and complete
client records remain owner-controlled outside Git because they contain local paths, request
metadata, and opaque reasoning signatures.

## Historical pre-round-4 static gate

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

Pytest passed **285 tests** in 6.61 seconds. Ruff and diff checks were clean; the lock resolved 15
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

## Historical combined Power-package closure

After the selected-profile campaign, an independent Codex pre-Fable audit found that the combined
snapshot lacked an installable package root and that draft features with commands could still be
executed or bound into goals. Both findings are recorded and closed in
`reviews/pre-fable-round-4.md` and `reviews/acceptance-ledger.md`.

The accepted standalone Power snapshot was imported at `powers/pk-stack/` without changing its
original checkout. One shared `find_verifiable_feature` rule now rejects drafts before either
`feature verify` command execution or `goal start --feature` state creation. The canonical setup
shim then regenerated the fixture rather than relying on a hand-copied second source.

The pre-Fable combined gates produced:

```text
(cd powers/pk-stack && env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync pytest -p no:cacheprovider -q)
# 509 passed in 37.58s

env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync pytest -p no:cacheprovider -q
# 290 passed in 9.26s

uvx --from check-jsonschema check-jsonschema \
  --schemafile https://agent-plugins.org/schemas/1.0.0/plugin.schema.json \
  powers/pk-stack/plugin.json
# ok -- validation done
```

Canonical and combined Ruff checks, the canonical format and `ty` checks, both lock checks, the
then-current `kiro-cli agent validate` commands, generated-controller doctor, feature and
knowledge validation, shell syntax, JSON parsing, and `labctl doctor` also exited zero. The single
controller warning was the disclosed optional absence of canonical `okn`; current counts are
reported in the deterministic gate above.

## Historical Fable round-4 executable and static suites

The Fable round-4 remediation was committed before the historical `fable-r5-902` campaign:

```text
commit  cb2cb0905687c3e94e539333d8945c37109f6189
tree    c28e71a050185f19befb3832e865c4e54f2bcf03
```

The complete combined suite passed 298 tests, and the canonical Power suite passed 509:

```sh
env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync pytest -p no:cacheprovider -q
# 298 passed

(cd powers/pk-stack && env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync pytest -p no:cacheprovider -q)
# 509 passed
```

The executable remediation requires the duplicate API response marker and accepted status,
stable export ID, exact durable idempotency key, confirmed enqueue, and exactly one worker attempt.
It also closes the round-4 root-controller, exact-network, real-producer/judge-payload, and exact
build-backend-pin low findings with executable regressions.

## Historical Fable round-5 Floci campaign: `fable-r5-902`

The lifecycle used only the public control surface on executable commit `cb2cb09`:

```sh
./labctl doctor --output json
./labctl up --run-id fable-r5-902 --acknowledge-docker-socket --output json
# Add one controlled build-input marker to src/pk_stack_lab/runtime.py.
./labctl deploy --output json
# Restore src/pk_stack_lab/runtime.py byte-for-byte to executable commit cb2cb09.
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
```

Both API and worker services converged on two distinct generations:

| Generation | Source digest | Docker image ID | API/worker revisions | Operation ID |
| --- | --- | --- | --- | --- |
| controlled marker | `21d72b651fe61d76f14cb4c2e427755a3ffefe4704da6c8397311283b97c1d72` | `sha256:43545de6babede31a7d1eeaa5dc93b2578145338c35fbf9c9d582010c0bc5f69` | `:1` / `:1` | `3ce59f0bbf08bd17c5676b915a5f0f3a` |
| restored executable commit | `5241fe8d4203672be0f5ed57ee9e2b2517919841b0632334b13a14a073727fe6` | `sha256:8510c0cf5e34ce1c81869249a893779b8d9a9992a9ad322aec59cdf63c7d1377` | `:2` / `:2` | `d0e2fe295881efa76e36fc025c1b4f87` |

The restored runtime hash was
`83a05fcc163e8f72b418cb72834967e8d274bebfe872d4608ad393c18469cfe9`. The evidence command
reported the final source digest explicitly at the top level. Direct verification returned
`ok: true` for export `e-80e481584565639f` and current-invocation DLQ message
`df56c9f6-c725-486a-8ce3-d42ec91af49d`. The strengthened API-idempotency checks, complete business
contract, and post-business identity reproof passed.

The frozen owner-controlled judge then invoked the exact public verifier:

```sh
/usr/bin/python3 -I -B \
  /private/tmp/pk-stack-judge-fable-r5.dg6p1m/controls/verify_feature_contract.py \
  --repo /Users/noahsutter/git-projects/pk-stack-lab \
  --expected-contract-sha256 f8678410245c3f62b186a88535432f7f97d2f02687d1ea3685e30f526242fc48 \
  --control-manifest \
    /private/tmp/pk-stack-judge-fable-r5.dg6p1m/controls/control-manifest.json
```

It exited zero with `ok: true`, judge SHA-256
`73e6b16865381c0475e528d5c87458081d92f213e31811395b4e2ecfad9560d7`, manifest SHA-256
`b7b7e9176d435242738abfb9ea31b4faed4573cd68448454b5d964235629dd0d`, and contract SHA-256
`f8678410245c3f62b186a88535432f7f97d2f02687d1ea3685e30f526242fc48`. The full frozen 14-path
hash map is retained in `reviews/fable-r5-live-proof.md`.

Normal `./labctl down --output json` then accounted for four ECS tasks and four immutable image
references, completed all eight frozen phases, and left every exact local postcondition clean. The
full foreign-image inventory was unchanged. At that point these results closed `FBL-028` and
`FBL-029` locally. The later final campaigns below supersede this run as current executable
evidence.

## Historical pre-combination live Floci campaign: `live-council-902`

The consolidated round-2 `d9b1e0d` candidate used only the public control surface:

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

This run's verifier treated the repeated deterministic export ID as sufficient API-idempotency
evidence. Fable round 4 correctly found that it did not require the runtime's explicit duplicate
marker or bind the completed row to the submitted idempotency key and confirmed enqueue. The run
therefore does not close `FBL-028`, even though its other observed predicates remain historical
evidence.

Docker 29.7.2 and Compose 5.5.0 ran both application containers as `65532:65532` without mounts
on `pk-stack-lab-net`. The task definitions requested read-only root filesystems, `CapDrop: ALL`,
and `no-new-privileges`; Floci 2.0.1 again did not propagate those three settings to Docker. The
evidence reports this emulator limitation explicitly.

### Historical external judge

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

### Historical teardown and noninterference

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

## Historical Kiro v3 campaign: `kiro-v3-accept-902`

The controller seeded one deliberate GET partition-key defect in an isolated clone of candidate
`d9b1e0d`; red commit `052b64f565a2d91a67098ac416c6d53481284cb3` changed only
`src/pk_stack_lab/runtime.py`. The broken deployment reached API/worker revision 1 and the normal
static suite still passed, making the live business verifier the meaningful oracle.

One PTY launched one user-facing Kiro CLI 2.21.0 process with the ordinary interactive interface:

```sh
kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max
```

Kiro cloud configuration initially reset the launch effort to `high`; the same process was set to
`max` before the goal prompt and displayed `pstack · GPT 5.6 Sol · max` through completion. The
session loaded `/verified-goal`, then started goal
`9ecd2693-35bd-4b2f-80bb-f9486b0f5b17` with exact objective:

```text
Repair the deployed document-export tenant-key partition-separation regression in this isolated local Floci lab.
```

Its immutable contract was `./labctl verify --output json`, source `feature-map`, feature
`document-export`, digest
`bddcfd86cc62d274993a11726302cc9b4bc2033f164aef2edaa8d59fb595b4ab`, maximum 4. Attempt 1 ran
before any source write and exited 1; its exact JSON `error` value was
`tenant-key partition separation check failed`.
Kiro then used native `pstack-verifier` exactly once with no command or write, made the single
permitted `runtime.py` edit through its file tool, and ran one `./labctl deploy --output json`.

The repaired deployment reached API/worker revision 2 with candidate source digest
`10e7e74db272a52be501983cb3a9254647937e89c3682042aadb7f15892ceded`. Attempt 2 exited 0 and
proved tenant partition separation, the then-current verifier contract, and post-business identity.
Its API-idempotency predicate has the same later-discovered `FBL-028` limitation as
`live-council-902`; the Kiro campaign proves the fail-repair-pass workflow, not the strengthened
final business contract.
Final goal state was `passed`, 2 of 4. There was no third verification, contract change, goal
replacement/resume, `/spawn`, nested Kiro, native `/goal` claim, or user-selected ACP execution
path. The one source write restored runtime SHA-256
`83a05fcc163e8f72b418cb72834967e8d274bebfe872d4608ad393c18469cfe9`; all 88 tracked files then
matched the candidate byte-for-byte.

After the Kiro process exited normally, the frozen external judge passed with the same contract,
control-manifest, and judge hashes as `live-council-902`. Evidence and sequential status checks
passed. Reachable teardown removed four tasks and four run images through all eight frozen phases;
exact postcondition checks passed and the full foreign-image inventory was unchanged.

The scrubbed chronology, exact prompt, hashes, raw-evidence locations, and limitations are in
`reviews/kiro-v3-campaign.md` and `reviews/kiro-v3-campaign.json`. The owner-only terminal
typescript is outside Git at
`/Users/noahsutter/.local/share/pk-stack/evidence/kiro-v3-accept-902/kiro.typescript`, SHA-256
`b6bc01485060153eeb300abd1f79875ad6f8e7a737a126ebadf33a8252e94013`. Because BSD `script` does
not echo its own invocation, the exact launch argv and single user-launched process are harness
metadata rather than transcript bytes; the transcript independently proves the V3 UI, selected
profile/model/effort, chronological actions, and normal session end.

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

## Final naming and DRY sweep

A full tracked-and-hidden search found no stale `PStack`, `Pstack`, `P-Stack`, `PKStack`,
`PK Stack`, or `Potato Kiro` spelling. `PK-Stack` and `Poteto Kiro` are the user-facing names.
Lowercase `pstack`, `.pstack`, `pstack-*` agents, the `pstack_kiro` module, `pstack-kiro`
distribution/receipt manager, and `pk-stack-lab` fixture remain intentional compatibility or
implementation identifiers. Installed agents, hooks, steering, and skills are byte-identical to
their bootstrap-managed cached sources, so no duplicate template/live naming fix was needed.

## Council and current-session status

Sol Advisor v0.6.0 supplied build-phase advice and is recorded as advisory, not acceptance.
Fable 5.1 round 1 reviewed commit `0b000d359b99f34ee5001088548ca872322e734a`; round 2 reviewed
commit `2fcacc054fd62e55a8d57107d35b73e3d1d1582c`. Both ran at max effort and returned material
findings. Round 3 inspected immutable commit `d9b1e0d` read-only at max effort but reached the
five-hour account rate limit before returning the required report. It has **no verdict, no
acceptance value, and no finding disposition**. Round 4 reviewed immutable combined commit
`ced867c4814ef722441215bd4d33ac30769868ec` and returned `REQUEST CHANGES` with material findings
`FBL-028` and `FBL-029`; see `reviews/fable-round-4.md`.

Commit `cb2cb09` closed those findings and supported the now-historical `fable-r5-902` proof.
Candidate A `28b9182` is the executable proven by the prior immutable Floci campaign. Candidate B
`2a1afb8` carries that Floci evidence and is the executable proven by the fresh current-session
Kiro campaign. Candidate C `491bfda` carries both normalized campaign records and was the exact
immutable target for Fable round 5 at `xhigh`. Round 5 returned `REQUEST CHANGES` with material
findings `FBL-037`, `FBL-038`, and `FBL-039`; this report and the README address the documentation
portion of `FBL-039`, while the acceptance ledger and executable hardening are tracked separately.
Historical candidate D `8806fa6` contains the post-round-5 Kiro/OKF integration and other
remediation work. Its exact archive has independent canonical OKN and Floci exact-deletion proof.
Hosted-control candidate E `6e8d4bb` carries later workflow, compatibility, and evidence changes;
maintenance run 33743730700 exercised its control path only and stopped before Kiro. Neither D's
older campaigns nor E's fail-fast run proves a successful maintenance lifecycle or post-remediation
council review. Candidate F `0dbc53c` separately passed the final native Bug Fix Spec and
current-session campaign. Those boundaries are intentional: no report claims that a later evidence
carrier was the executable in an earlier campaign. Prospective Fable 5.1 peer and acceptance runs
use `xhigh`; historical `max` runs remain labeled as such. This report does not claim final Fable
acceptance until the exact post-remediation review tree receives `ACCEPT` with zero material
unresolved findings.

The optional Archify status flow, `npx skills use tt-a1i/archify@archify --agent codex`, reached its
interactive trust TUI under `TERM=dumb` and was not activated; it produced no authoritative
architecture artifact and changed no repository file. Grok 4.6 `xhigh` remains the final sweeper
after clean Fable acceptance, with another Fable pass required if the sweep drives a material tree
change. The private GitHub repository is real and verified private; hosted credential, exact
permission-matrix, and read-only canary proof now exist. A successful hosted maintenance lifecycle,
final exact-tree deterministic and canonical OKF/OKN reproof, and exact-tree Fable/Grok acceptance
remain open. The final native-Spec current-session campaign is complete.
