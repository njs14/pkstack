# Test strategy

PK-Stack needs evidence at three different boundaries: deterministic controller behavior, the
real Docker-backed Floci fixture, and the behavior of one ordinary interactive Kiro v3 session.
Passing one boundary must not be reported as proof of another.

## Evidence matrix

| Layer | What it proves | Primary check | Current acceptance role |
| --- | --- | --- | --- |
| Static and unit | Endpoint refusal, runtime semantics, state schema, ownership, bounded output | Repository pytest, Ruff, lockfile and diff checks | Required on every candidate |
| Controller source | The maintained PK-Stack controller behaves correctly at its source | Controller checkout's locked pytest suite | Required; host-source only |
| Vendored controller | The generated `.pstack` runtime matches the reviewed controller | Byte-for-byte source comparison plus repo-local commands | Required separately from source tests |
| Isolated contracts | Feature generation and goal state transitions work outside the fixture | Temporary repository with ready feature and fail-then-pass goal | Required, but not Kiro-session proof |
| Live Floci | Docker-backed ECS service behavior, repeat deploy, business proof, exact cleanup | `doctor -> up -> deploy -> deploy -> verify -> evidence -> down` | Required on the candidate tree |
| External judge | A mutation cannot pass by changing its verifier or protected controls | Read-only external judge and control manifest | Required during live mutation campaign |
| Kiro current session | `/verified-goal` displays and preserves one contract through fail, repair, redeploy, pass | One interactive `kiro-cli chat --v3 --agent pstack` transcript | Passed locally; exact evidence awaits Fable disposition |
| Model council | Architecture/safety acceptance and final low-level sweep | Repeated Fable 5.1 peer reviews, then Grok 4.6 sweeper | Record only after completed cleanly |

Do not encode a permanent test count in this document. The suite is still evolving; each
validation report must record the exact command, observed count, exit status, candidate commit,
and timestamp for that run.

## Repository checks

Create the locked development environment once, then run the checks without syncing during the
measurement or writing bytecode:

```sh
uv sync --locked --no-config
env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync \
  pytest -p no:cacheprovider -q
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --no-config --no-sync ruff check .
uv lock --check
git diff --check
```

The tests cover exact host/task endpoint construction, absence of ambient AWS and proxy behavior,
application queue/idempotency state transitions, task security requests, resource/body identity,
and one bounded JSON error object after Python dispatch.

State/lifecycle coverage includes:

- exclusive process and state claiming, no-follow state operations, canonical schema v2, and
  atomic-transition failure retention;
- planned-before-mutation artifact events, candidate reconciliation, last-good activation, and
  repeat-deploy retention;
- complete exact-name collision inventory before provisioning and claim/daemon rebinding before
  post-`up` commands;
- frozen plan installation before deletion, hash/ledger binding, every crash boundary, ordered
  resume, and terminal reproof before manifest unlink;
- task-container removal before data cleanup, cluster-wide service/task absence, timeout without a
  false checkpoint, fail-closed ECS describe/list failures, and S3 draining beyond one page;
- original-claim Compose digest binding before both first-pass and resumed outer teardown;
- exact pinned-Floci-image preflight before the run claim, Compose `--pull never` after the claim,
  exact application-image scope, filtered stale-recovery dry-run/apply and mismatch refusal, and
  refusal of a foreign task or reappeared outer boundary; and
- a fixed-size `verify.resources` projection even when the internal artifact ledger grows.

## Source controller versus generated controller

The maintained controller checkout and the generated runtime are separate proof boundaries. Run
the source checkout's own locked test suite first:

```sh
env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync \
  pytest -p no:cacheprovider --no-cov -q
```

Then compare its `src/pstack_kiro` directory to this repository's
`.pstack/projectctl/src/pstack_kiro`, excluding only bytecode caches:

```sh
diff -qr --exclude=__pycache__ \
  /absolute/path/to/reviewed-pk-stack-power/projectctl/src/pstack_kiro \
  .pstack/projectctl/src/pstack_kiro
```

A green source suite can mask a stale generated controller if imports resolve to the source
checkout. The directory comparison and these repo-local calls guard that distinction:

```sh
.pstack/bin/projectctl doctor --output json
.pstack/bin/projectctl feature validate --output json
.pstack/bin/projectctl knowledge validate --output json
```

The knowledge command may truthfully warn that `okn` is unavailable while still validating the
feature map. Strict OKF coverage requires a separate environment with canonical `okn` installed.

In a new temporary repository, generate one ready feature with a harmless executable command,
validate and verify it, then start a two-attempt goal whose command initially fails. Record attempt
1 as `active`; make the smallest fixture change and record attempt 2 as `passed`. This proves
feature generation plus projectctl's state transition, but it must not be labeled a Kiro campaign.

## Live Floci matrix

The cold path uses only the public surface:

```sh
./labctl doctor --output json
./labctl up --run-id live-candidate-001 --acknowledge-docker-socket --output json
./labctl deploy --output json
# Make one controlled build-input change.
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
./labctl down --output json
```

Restore the intended candidate source before the second deployment so the active generation and
its verification match the candidate being accepted. Preserve both generation digests,
task-definition revisions, artifact-ledger length, task ARNs, image references, security evidence,
and the final teardown phase list. After `down`, prove that every frozen current-run task container
and image reference is absent, while explicitly seeded foreign images remain.

The business verifier must prove API acceptance, worker completion, exact S3 content and terminal
DynamoDB state, duplicate POST identity, duplicate worker no-op, current-invocation DLQ redrive,
and tenant-key partition separation. Host tests do not substitute for this live path. Conversely,
a live business pass does not substitute for crash/resume fault injection.

## Independent external judge

Before handing a mutable checkout to Kiro, copy `judge/verify_feature_contract.py` and a control
manifest outside the checkout. Both must be owner-controlled, direct, single-link, read-only
regular files. The manifest contains SHA-256 hashes for every protected control-plane and
executable source path. Also preserve the expected hash of
`Wiki/features/document-export.md` separately.

After deployment, invoke the external copy:

```sh
python3 /external/read-only/verify_feature_contract.py \
  --repo /absolute/path/to/mutable-checkout \
  --expected-contract-sha256 "$RECORDED_PK_CONTRACT_SHA256" \
  --control-manifest /external/read-only/control-manifest.json
```

The judge hashes controls before and after, rejects unmanifested executable source and import-time
customization, parses only bounded JSON, and invokes exactly the checkout's
`labctl verify --output json`. It does not use Docker or AWS directly. The CLI exposes a fixed
resource schema rather than the unbounded internal ledger so the judge's memory and output remain
bounded. A `src/**/__pycache__` directory is intentionally rejected: Python bytecode is executable
mutable input, not a harmless cache at this trust boundary. Keep bytecode disabled throughout the
campaign rather than excluding it from the source-closure check. Retain the judge JSON, both
visible control hashes, and exit status.

## Real current-session Kiro campaign

The completed workflow campaign used one process launched exactly as an ordinary interactive v3
session, without an ACP command/launch, native `/goal`, `--no-interactive`, a machine-output
transport, resume into another session, or `/spawn`:

```sh
kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max
```

The seeded defect forced this sequence in that same session:

1. Invoke `/verified-goal` for the document-export feature with a bounded attempt budget.
2. Display the stored feature contract and feature-map provenance before the first attempt.
3. Run `projectctl goal verify` before any source edit and retain its failure as attempt 1.
4. Diagnose and make the smallest permitted application-source repair.
5. Redeploy with `./labctl deploy --output json`.
6. Verify the same goal ID and unchanged contract until it records `passed` within budget.
The committed bounded chronology plus externally hashed raw transcript records that sequence in
`reviews/kiro-v3-campaign.md`; `reviews/kiro-v3-campaign.json` retains the machine-readable
projection. After the Kiro process returned, the controlling harness invoked the protected
external judge, verified its control hashes, and cleanly tore down the live lab. Those are
independent acceptance actions, not a second Kiro session or a substitute for session evidence.

Sol Advisor may advise the implementation phase, but its output is design input rather than an
acceptance verdict. Fable 5.1 is the peer reviewer throughout candidate development and must review
the final immutable candidate plus Kiro evidence. Material findings become explicit fixes and the
Fable gate repeats. Grok 4.6 at very high reasoning is the final DRY/naming and low-level sweeper;
any material Grok-driven code change returns to Fable before acceptance.
