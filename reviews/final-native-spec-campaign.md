# Final native Spec and current-session verified-goal campaign

## Decision

`PLOT-008` passed on 2026-09-03 against executable candidate commit
`0dbc53c33b16de426af7e134b5faa7e819b25f97` (tree
`8ed46899995163d3ef9693ff167d8a9d9bf489ec`). One ordinary interactive Kiro CLI v3 process used
the workspace `pstack` agent with GPT-5.6 Sol at `max`. In that same conversation it completed
Kiro's native Bug Fix Spec workflow, returned to `pstack`, bound the completed spec to the
published `document-export` feature, and completed `/verified-goal` on attempt 2 of 4.

The current-session path did not use a user-facing ACP launch, another Kiro process, `/spawn`, or
a native `/goal` command. Kiro owns the planning artifacts; PK-Stack contributes the thin,
hash-bound spec-to-proof bridge and deterministic goal state.

The exact generated Spec package is retained under
`reviews/native-spec-artifacts/document-export-partition-fix/`. The exact terminal goal state is
retained as `reviews/final-native-spec-goal.json`; the normalized machine record is
`reviews/final-native-spec-campaign.json`.

## Immutable candidate and controlled red fixture

The campaign clone was created without hard links, detached at the candidate, stripped of its
remote, and checked for Git alternates. Its archive was owner-read-only, 6,471,680 bytes, and had
SHA-256 `efa463676f81af1d5f5a51ce7fec938dba5bb8066641ab678b2c11f4d4d41d09`.

A single controlled commit then replaced the request-derived document-export GET partition with
the literal `TENANT#tenant-a`:

```diff
-            Key={"pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}},
+            Key={"pk": {"S": "TENANT#tenant-a"}, "sk": {"S": export_id}},
```

Red commit `7a59f2118bae36b228b341197f011998bd2601df` has the candidate as its exact parent, tree
`ec734e73c590c5a9c28a45b2316ca063f1f855e9`, and changes only
`src/pk_stack_lab/runtime.py`. The broken runtime SHA-256 was
`b4a0091a163077296b408b243215744a952e25985c4a28154a3d023e6b62e3f6`.

The harness deployed broken source digest
`997adc89f6bcb7ac4d8d5aad6c7616af703dd5e7e11194531eb43db3b0ee5ee8` as run
`native-spec-903`, claim `0267f48fe678f37c1e14463a2c311504`, image
`sha256:697d2bc395b5c0769df245a3024f7a0b8aaa1dc7deaa3bf8a3d29d027fdc05f1`, and API/worker
revision 1 before Kiro began.

## One native Kiro conversation

The controlling PTY launched exactly one process:

```sh
/Users/noahsutter/.local/bin/kiro-cli chat --v3 --agent pstack \
  --model gpt-5.6-sol --effort max
```

The UI showed `pstack · GPT 5.6 Sol · max`. Kiro completed the native Bug Fix Spec package
`document-export-partition-fix` using the requirements-first workflow and native subagents. At
the implementation prompt, the operator selected `Not now`; Kiro confirmed that the spec was
ready and that it made no implementation changes. This cleanly separated native planning from
the later PK-Stack execution loop.

The generated artifacts were:

| Artifact | SHA-256 |
| --- | --- |
| `.config.kiro` | `53abcf6213fff914f5f58cc214e2994ec40e48c935cc71a0b4ba7834505985e1` |
| `bugfix.md` | `8155df4cf06f34b49216521567abc6608c614965df1586642008a7933d2de868` |
| `design.md` | `94f2bd741e5b5117a87ecd754fb78be2faf75e8a1a193034af718b1a2461ef8e` |
| `tasks.md` | `c7f0f7e603b36b1702b0c4b83ca9137608522c13b7517280c9337bb1d457604c` |
| `pstack-verification.json` | `6d7452e7ca5482ab5e7af1ea1c38aa4761fda058bbd77fba7515fd3827af3cad` |

The design explicitly used the published feature and project knowledge ladder. Its targeted
canonical `okn` query was unavailable in the isolated environment and was reported as such; the
linked Wiki records and current code were sufficient. Kiro reported approximately 34 minutes and
49.16 credits for native planning.

Without leaving the process, the conversation switched back to the workspace `pstack` agent and
invoked `/verified-goal`. The verified-goal skill then used the generated bridge to bind the
completed spec to `document-export`. The terminal process exited normally through `/quit` and
returned resume ID `sess_8e7906ef-addf-489d-af87-88f6d8c85887`.

## Spec-backed goal proof

Goal `4bff9b0f-5724-4476-b0d6-28af007e858b` retained:

- objective `Repair the deployed document-export tenant-key partition-separation regression in
  this isolated local Floci lab.`;
- stored command `./labctl verify --output json`;
- provenance `source=spec`, `spec=document-export-partition-fix`, and
  `feature=document-export`;
- immutable hashes for `bugfix.md`, `design.md`, and `pstack-verification.json`;
- contract digest `dc6adf854ce0cce544b23758ff60227bc18bebba64b2e64e4675db4c640918a0`;
  and
- maximum 4 attempts.

Attempt 1 ran before any source edit. It exited 1 in 5,829 ms, with empty stderr, solely because
`tenant-key partition separation check failed`; the goal remained active. Kiro invoked the native
`pstack-verifier` exactly once with a bounded read-only prompt. It located the fixed
`TENANT#tenant-a` read key without editing or executing commands.

Kiro then changed exactly one tracked line in `src/pk_stack_lab/runtime.py`, restoring
`f"TENANT#{tenant}"`, and ran exactly one supported deployment:

```sh
./labctl deploy --output json
```

The redeploy produced source digest
`5241fe8d4203672be0f5ed57ee9e2b2517919841b0632334b13a14a073727fe6`, image
`sha256:ee4ce92b7732f93058ea09bf5189d75fd6313b0df6395c70fbaa5d7db35e8f68`, and API/worker
revision 2. Attempt 2 ran the unchanged stored contract, exited 0 in 24,010 ms, and proved tenant
partition separation, terminal `COMPLETE`, exact S3 identity, one enqueue and worker attempt,
duplicate-delivery no-op behavior, current-invocation DLQ evidence, and post-business task
identity. The goal finished `passed` at 2/4 attempts. No third **goal** verification ran.

The exact owner-only goal file has SHA-256
`17c1f93b8559c35aa27a72e0095c695b224a88ceb017fd575e97d44d9e9fe83e`. Kiro reported 7.77
credits and 74m44s wall time for the verified-goal phase; that wall time includes the deliberate
machine pause. After Kiro exited, the only tracked worktree difference from the red commit was the
runtime repair, and all tracked bytes matched candidate `0dbc53c`. The repaired runtime SHA-256
was `83a05fcc163e8f72b418cb72834967e8d274bebfe872d4608ad393c18469cfe9`.

## Frozen external judge

Before red-fixture creation, the harness froze the 14 protected paths and copied the judge outside
the repository. The external judge and control manifest were direct, owner-controlled, read-only
files. The feature contract SHA-256 was
`37203aba7f6404e0a820fcacbca770857070c77a6e161d9622d9011e85c80d80`.

An initial orchestration mistake ran the judge concurrently with `labctl status`; that invocation
returned `labctl verifier did not prove the feature`. It is retained as a failed test setup, not a
product verdict. The exact successful Kiro payload independently satisfied every frozen payload
predicate, a direct serialized verifier rerun passed, and the judge was then rerun alone:

```sh
/usr/bin/python3 -I -B \
  /private/tmp/pk-stack-native-spec.SfGw7a/controls/verify_feature_contract.py \
  --repo /private/tmp/pk-stack-native-spec.SfGw7a/repo \
  --expected-contract-sha256 37203aba7f6404e0a820fcacbca770857070c77a6e161d9622d9011e85c80d80 \
  --control-manifest /private/tmp/pk-stack-native-spec.SfGw7a/controls/control-manifest.json
```

The isolated invocation exited 0 with `ok: true`, control-manifest SHA-256
`d35c86b45b640d817f57b7bfd5bc61c36b42e7cd4d4bdcfc32c6bd64f6d48aa7`, and judge SHA-256
`73e6b16865381c0475e528d5c87458081d92f213e31811395b4e2ecfad9560d7`. These post-session
invocations are independent acceptance actions and did not consume or change the terminal Kiro
goal.

## Guarded teardown and noninterference

`./labctl status` and `./labctl evidence` showed both revision-2 services running from the repaired
source. `./labctl down` then exited 0, accounted for four task instances and four immutable image
references across both generations, and completed all eight phases:

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

Before `up`, the harness planted foreign container
`7d0d4ec752580f49086499a58d79b6553a3e80095f8fe9837db7bbb96ca6a62a` with misleading
Compose project labels but no PK-Stack ownership claim. It used Docker's `none` network, read-only
root, UID/GID 65532, all capabilities dropped, and no-new-privileges. After teardown it remained
running with the same ID and identical inspect SHA-256
`2c0ee79a3052889cf9a6aca67601bf886019ea5025d6056ccfca08a7fdd8f69d`. The harness then removed
only that exact test container.

The complete container inventory returned byte-for-byte to SHA-256
`8b5cae8a076ba4dd089c6940bfc777ea7be029599202cc5963a2d019e915222b`; the complete network
inventory returned to `c608cd484362c3d5bf0bf8bf172e6cfbe5296d9ab33e7b20c5c0b980e70faaa3`. No campaign
container, image tag, outer Floci container, or named lab network remained.

The global image-list bytes did not return to the pre-sentinel hash: baseline
`054a98575c92b451edf13f799884dbc363b94d2ca179e23f25b1ce4853f65341` versus final
`0d654254d8a2b0a8c9cbbe0cd93b71a6fb5fb3d220fc776b9a3be57a45f73668`. The diff contains
unrelated old untagged images and changing age metadata while Docker Desktop performed ambient
resource management during the multi-hour pause. PK-Stack's claim-bound teardown nevertheless
proved all four owned image references absent. This campaign therefore claims exact owned cleanup,
foreign-sentinel preservation, and exact container/network restoration, not global image-store
quiescence.

## Scope and limitations

This is real local Kiro CLI v3, native Bug Fix Spec, projectctl/Cyclopts, and Docker-backed
ECS-like Floci evidence. It does not test Kiro Web, the IDE agent panel, Kiro Crew Task Runner,
Fargate, IAM, VPCs, cross-account AWS behavior, or the AWS production control plane. Kiro's native
Spec generated a complete task plan, but implementation proceeded through the current-session
PK-Stack loop after the explicit `Not now` handoff; it does not claim that a workspace skill can
programmatically switch native client workflows. Floci still reported that read-only root,
cap-drop-all, and no-new-privileges were requested but not enforced on its generated task
containers; both application processes did run as UID/GID 65532 without mounts.

The later evidence commit containing this report and the retained Spec bytes is not retrospectively
described as the executable candidate. Final Fable and Grok review must target the later exact
immutable evidence tree.
