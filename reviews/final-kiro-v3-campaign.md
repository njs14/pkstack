# Final Kiro CLI v3 current-session campaign

## Decision

The fresh candidate-bound Kiro campaign passed locally on 2026-09-02. One ordinary interactive
Kiro CLI v3 process used the workspace `pstack` profile with GPT-5.6 Sol at `max`, loaded the
`verified-goal` skill, started one feature-backed goal, recorded a real deployed failure before
any source write, invoked the native `pstack-verifier` once read-only, repaired one line with
Kiro's file-edit tool, redeployed exactly once, and passed the unchanged stored contract on
attempt 2 of 4. No third verification ran. A frozen external judge passed against the still-live
repaired deployment, after which normal owned teardown completed all eight phases.

This campaign exercised commit `2a1afb8a301c952b655ffe9e8a0981adff3c324c` (tree
`c0a2f4b84f169d86d2295f15dbbf9b5a37e98b4e`). The later commit that carries this report is
evidence only and was not retrospectively exercised. Machine-readable normalized evidence is in
`reviews/final-kiro-v3-campaign.json`; the exact two-line Kiro input history is in
`reviews/final-kiro-v3-campaign-history.txt`. Twelve exact, non-secret Kiro log records are in
`reviews/final-kiro-v3-campaign-session.jsonl`. Raw terminal and complete client records remain
uncommitted.

## Immutable candidate and red fixture

The harness created `/private/tmp/pk-stack-final-kiro.qL6A0S/repo` with `git clone
--no-hardlinks`, detached it at candidate `2a1afb8`, removed its remote, and confirmed that it had
no Git alternates. It made and committed one controlled defect:

```diff
-            Key={"pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}},
+            Key={"pk": {"S": "TENANT#tenant-a"}, "sk": {"S": export_id}},
```

Red commit `52b6972a65f093902e161a052de513475fd4b584` has the candidate as its exact parent and changes
only `src/pk_stack_lab/runtime.py`. Its broken runtime hash was
`b4a0091a163077296b408b243215744a952e25985c4a28154a3d023e6b62e3f6`. Before Kiro started,
the harness deployed run `kiro-final-902`, claim `94b537aebe65d6ed29f028d37df9de19`, source digest
`997adc89f6bcb7ac4d8d5aad6c7616af703dd5e7e11194531eb43db3b0ee5ee8`, image
`sha256:6e5b8a02abbf5e44a9bfaaa7aafb83addcb6257e691c001c21e4ce957f2d5e33`, and API/worker task
definition revision 1.

After Kiro exited, `git diff --quiet 2a1afb8a301c952b655ffe9e8a0981adff3c324c --` exited 0.
The repaired runtime hash was
`83a05fcc163e8f72b418cb72834967e8d274bebfe872d4608ad393c18469cfe9`, exactly matching the
candidate. Relative to the red commit, the sole tracked worktree delta was the intended runtime
repair.

## One selected current session

The controlling harness launched exactly one user-facing process under a PTY and recorded its PID
before `exec` replaced the shell:

```sh
/usr/bin/script -q -F /private/tmp/pk-stack-final-kiro.qL6A0S/raw/kiro.typescript \
  /bin/zsh -c 'umask 077; print -r -- "$$" > /private/tmp/pk-stack-final-kiro.qL6A0S/raw/kiro.pid; exec /Users/noahsutter/.local/bin/kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max'
```

The sidecar recorded PID 30020. The process exited 0 and was absent afterward. The session supplied
resume ID `sess_12ca9c3f-d52e-414c-954f-cf360068d41c`; its persisted metadata records agent
`pstack`, model `gpt-5.6-sol`, and effort `max`. The UI settled on
`pstack · GPT 5.6 Sol · max` before the semantic prompt and retained it through completion.
Kiro reported 559,068 ms (9m19s) and 3.461648 credits.

The exact history contains only the one semantic `/verified-goal` prompt and `/quit`. Its SHA-256
is `e5c7e34d500e4cef02e1be658b50c1e929c5e6e19dc61a60cd8222155f1af6ae`; the first line's
SHA-256 is `0c223b03bc0b508d8d462826954c100dd38d2e0d71de5f8418a6450a848852d1`.

## Chronological action proof

The 103 persisted structured session records show the following completed actions in order:

1. Load the workspace `verified-goal` skill.
2. Run controller goal status, feature list, and `feature show document-export`.
3. Start exactly one feature-backed goal with maximum 4 attempts.
4. Run goal verification once before any source write; attempt 1 fails only with
   `tenant-key partition separation check failed`.
5. Invoke native `pstack-verifier` exactly once with a read-only prompt. Its sub-session executes
   no command and makes no write.
6. Read `src/pk_stack_lab/runtime.py` and apply the one-line repair through Kiro's `str_replace`
   file tool.
7. Run `./labctl deploy --output json` exactly once.
8. Run the unchanged goal verifier once more; attempt 2 passes.
9. Read final goal status and report `passed`, 2 of 4. Exit through `/quit`.

The completed shell commands are exactly:

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

There was no raw Docker, Compose, AWS, HTTP/curl, Git-write, goal-clear, goal-resume, `/spawn`,
user-selected ACP, another Kiro session, or nested Kiro action. The compact log projection does
contain Kiro's internal `ACP session/new`, `ACP session/prompt`, `ACPEventAdapter`, and `Autopilot`
labels. These identify its client/event protocol and controller scheduling; they are not treated
as evidence that the user selected ACP instead of the ordinary Kiro CLI v3 surface.

## Stored goal and deployed proof

Final owner-only goal state had schema 2, goal ID
`96e0d0a9-2366-42e9-8869-ca3ffc58e4ed`, status `passed`, exactly two history entries, and
SHA-256 `3f79fb370add4c581629a0ce091b3d51d5eee8e8aa26744efb43718e9cea8f18`. The immutable contract
remained:

```json
{
  "argv": ["./labctl", "verify", "--output", "json"],
  "display": "./labctl verify --output json",
  "feature": "document-export",
  "source": "feature-map",
  "spec": null
}
```

Contract digest `bddcfd86cc62d274993a11726302cc9b4bc2033f164aef2edaa8d59fb595b4ab` did not change.
Attempt 1 exited 1 in 5,632 ms with empty stderr and the precise required error. Attempt 2 exited
0 in 24,255 ms with empty stderr and proved the full business contract, including
`tenant_key_partition_separation: true`, API idempotency, terminal `COMPLETE`, exact S3 content,
worker duplicate-delivery no-op, current-invocation DLQ evidence, and post-business task identity.

The sole redeploy produced source digest
`5241fe8d4203672be0f5ed57ee9e2b2517919841b0632334b13a14a073727fe6`, image
`sha256:0adec931350990cd280731c87b08f27e14c041f187ab152ceab8e555a053248c`, and API/worker revision
2. The successful export was `e-21f6f8795ecc96d1`; the current-invocation DLQ message was
`09129ed7-235c-408a-9c48-971454a4cf4c`.

## Frozen external judge and teardown

Before introducing the red fixture, the harness copied and made read-only a 14-path control
manifest plus the external judge. After Kiro exited, while the repaired ECS deployment remained
live, it ran:

```sh
/usr/bin/python3 -I -B \
  /private/tmp/pk-stack-final-kiro.qL6A0S/controls/verify_feature_contract.py \
  --repo /private/tmp/pk-stack-final-kiro.qL6A0S/repo \
  --expected-contract-sha256 fc4c32e718f7e4ea2aa0369c24f0bca25d7cfc5af8f64990caf34fdd2214605a \
  --control-manifest /private/tmp/pk-stack-final-kiro.qL6A0S/controls/control-manifest.json
```

It exited 0 with `ok: true`. The control-manifest SHA-256 was
`94b2c45ffc7f51ec4d770c0d46cc0d335ce9900b060b1d5682ceb8864b8aba90`; the judge SHA-256 was
`73e6b16865381c0475e528d5c87458081d92f213e31811395b4e2ecfad9560d7`; the feature contract
SHA-256 was `fc4c32e718f7e4ea2aa0369c24f0bca25d7cfc5af8f64990caf34fdd2214605a`.

Sequential `./labctl status --output json` and `./labctl evidence --output json` also passed. Then
`./labctl down --output json` exited 0, accounted for four task instances and four immutable image
references across the two generations, and completed all eight frozen phases. Exact
postconditions found no state manifest, Floci outer container, named lab network, run task
container, or run image.

## Noninterference and limitations

The complete container inventory was byte-identical before and after (SHA-256
`ef13f64486d0af29888be4f45216a221097bfefaf823231b913219abe0900230`). The complete image
inventory was byte-identical (SHA-256
`51dbc634a9a43f53db11a2c70d6dbf891a522ae9a971ed657aa6919e07a58657`), including all 18
pre-existing `pklab-*` image records (SHA-256
`4d6bc3e1d5a3665280921a971e988ea6dd62e8f05b1bc86a59a3a9278bfe3460`).

The network inventory was semantically identical by name, driver, and scope, but **not**
byte-identical by object ID. Docker Desktop's five-minute Resource Saver had stopped its VM before
the baseline; its host backend served that network-list request from the stopped-engine cache. The
first live, read-only container-list request during startup resumed the VM, and Docker recreated
its built-in `bridge`. The bridge retained driver `bridge`, local scope, subnet `172.17.0.0/16`,
and gateway `172.17.0.1`, but its opaque ID changed from
`825882251a325749072379f7e2db68125e24f1d2791c8309f6062cd158f4b133` to
`f69b57cbdb8a9976f6719f9962fccc520f28b5c05428ed3ad291b31ef2be5e84`. Docker reports the new
bridge was created at `2026-09-03T02:31:29.761118125Z`: after the 02:31:22Z cached pre-snapshot
and before the first deployment. Docker Desktop's host and VM logs independently record the idle
shutdown, cached request, VM initialization, old-resource de-registration, and new-resource
registration. PK-Stack creates, validates, and removes only the exact claim-bound
`pk-stack-lab-net`; no repository command targets Docker's built-in bridge. This report therefore
does not claim byte preservation of a host-managed default-network ID across Resource Saver
transitions.

This realistic session also inherited the user's normal Kiro configuration. It invoked configured
`memory-recall` and `memory-distill` hooks, included user-level `memory-steering.md`, and wrote
ordinary user STM/LTM summaries. Thus repository, process, goal, and action isolation are proven,
but model context was not hermetically isolated from ambient Kiro memory. The supplied secret was
scanned by exact value and was absent from the worktree, goal, history, transcript, session files,
and written memory. Raw records are not committed because they contain local paths, request
metadata, and opaque reasoning signatures.

The owner-only terminal typescript is 615,475 bytes, 6,060 lines, mode 0400, and SHA-256
`97c6960ddc21c19b9d02fe29b83efa68eb2cdf420e6def7c08111aa05b671bda`. Structured messages are
157,725 bytes, 103 lines, mode 0600, and SHA-256
`bafe59584e1e09f81ddf119a49cfc3e90de2e31f33c7521c1076ea446d4240ca`. They remain outside Git
under the paths recorded in the JSON summary. This is local Kiro CLI v3 evidence; it does not test
Kiro Web, claim a native `/goal` command in installed v3, or convert itself into an independent
Fable acceptance verdict.
