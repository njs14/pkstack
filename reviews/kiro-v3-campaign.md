# Kiro CLI v3 current-session campaign

## Decision

The selected-profile campaign passed locally on 2026-09-02. One ordinary interactive Kiro CLI
v3 session loaded `/verified-goal`, preserved one feature-backed contract, recorded a real failure
before any source write, used one read-only native verifier subagent, made one application repair,
redeployed the Floci fixture, and passed the same goal on attempt 2 of 4. The external judge then
passed and teardown removed the complete run-owned target set without changing foreign images.

This is local workflow evidence for `FBL-008`; it is not a Fable acceptance verdict. The committed
bundle contains the machine-readable summary in `reviews/kiro-v3-campaign.json`, an exact copy of
the persisted goal in `reviews/kiro-v3-campaign-goal.json`, and the exact four-line Kiro input
history in `reviews/kiro-v3-campaign-history.txt`. Twelve exact, non-secret client-log records are
retained in `reviews/kiro-v3-campaign-session.jsonl`.

## Candidate and isolation

- Correct candidate: `d9b1e0ded31b2289ef40b5d0133d65b38da63767`, tree
  `37198add1239a7c9053282a6dd0ad7a99c19adbe`.
- Isolated campaign clone: `/private/tmp/pk-stack-kiro-campaign.IEvqJ7/repo`.
- The clone had no remote, remote refs, alternates, or shared common Git directory.
- Red-fixture commit: `052b64f565a2d91a67098ac416c6d53481284cb3`, whose parent is the exact
  candidate and whose only change hard-coded the GET partition key to `TENANT#tenant-a`.
- The broken static suite still passed 285 tests, so the deployed behavioral verifier—not a unit
  test tailored to the defect—had to expose the regression.
- Before the Kiro prompt, the harness started run `kiro-v3-accept-902`. The broken deployment had
  claim `86f2e9e214c4703005ff60ffe54e162e`, source digest
  `c5d7b7270d817df23e942e8353bbaf332e4cc06f0f6b5c4c437dc22f9d12401d`, displayed image-ID
  prefix `sha256:079cd840`, and API/worker revision 1. The full removed broken-generation image ID
  was not retained and is not claimed.

## Launch and model selection

The controlling harness launched one user-facing Kiro CLI process under a PTY and recorded it:

```sh
/usr/bin/script -q -F \
  /private/tmp/pk-stack-kiro-campaign.IEvqJ7/raw/kiro.typescript \
  /Users/noahsutter/.local/bin/kiro-cli chat --v3 --agent pstack \
  --model gpt-5.6-sol --effort max
```

Kiro CLI reported version 2.21.0. Cloud configuration initially changed the effective effort from
the launch request to `high`; while inspecting `/effort`, the selection transiently moved to
`none` and was immediately corrected to `max` **before** `/verified-goal` was submitted. From
prompt submission through completion, the UI repeatedly reported
`pstack · GPT 5.6 Sol · max`, with no later effort change. The session ended normally with exit 0,
reported 8m57s and 2.68 credits, and supplied resume ID
`sess_ccc571e6-1451-4377-be64-e656004e4bd8`.

The exact launch argv is controlling-harness metadata: BSD `script` records child I/O but does not
echo its own invocation into the typescript. The raw transcript independently proves the Kiro V3
UI, selected `pstack` profile, Sol model/max effort status, one semantic prompt, chronological tool
events, and one normal session end. It cannot independently prove its own launch argv or
OS-process cardinality.

## Exact goal request

The Kiro history retained one semantic `/verified-goal` submission (SHA-256
`577b135bd49fa118987505f1f367fe4296c598f40ea769f2e7755ca00677ce17`):

```text
/verified-goal Repair the deployed document-export tenant-key partition-separation regression in this isolated local Floci lab. Start the stored objective exactly as "Repair the deployed document-export tenant-key partition-separation regression in this isolated local Floci lab." Use the existing ready document-export feature contract and the original maximum of 4 attempts. First inspect goal status, feature list, and feature show through .pstack/bin/projectctl. Start exactly one goal with --feature document-export --max-attempts 4. Before verification, visibly report the goal ID, contract display, contract source, feature provenance, contract digest, attempt count, and maximum attempts. Run .pstack/bin/projectctl goal verify --output json once before any source write; preserve that result as attempt 1. It must fail for the tenant-key partition-separation predicate; if it passes or fails for another reason, stop without manufacturing a failure. Only after attempt 1 fails, invoke the native pstack-verifier subagent exactly once to inspect the stored contract and failure evidence without executing commands or editing files. Then diagnose and make the smallest repair. The only permitted tracked-file write is src/pk_stack_lab/runtime.py, and it must use Kiro's file-edit tool rather than a shell write. Do not edit .kiro, .pstack, Wiki/features/document-export.md, judge, tests, docs, labctl, projectctl, compose.yaml, Dockerfile, pyproject.toml, uv.lock, requirements-runtime.txt, src/pk_stack_lab/__init__.py, src/pk_stack_lab/aws.py, src/pk_stack_lab/cli.py, or src/pk_stack_lab/config.py. Only .pstack/bin/projectctl may update managed .pstack/state goal data, and only labctl may update .lab-state or the emulator. Do not use raw Docker, Docker Compose, raw AWS commands or endpoints, curl, direct emulator mutation, Git write commands, goal clear, goal resume, extra attempts, a weaker verifier, /spawn, ACP, or another Kiro session. Redeploy only with ./labctl deploy --output json. Continue the same goal ID and unchanged contract until it passes within the original budget, then show final goal status. Do not run a third verification after a pass and do not tear down the lab. If any constraint would need to be violated, stop and report the blocker.
```

## Bounded chronological projection

Terminal redraws duplicate physical strings, so this chronology counts completed semantic tool
records and corroborates them against the stored goal, Kiro history, and repository diff:

1. Kiro loaded the workspace `verified-goal` skill.
2. It ran, in order, `.pstack/bin/projectctl goal status --output json`, `feature list --output
   json`, and `feature show document-export --output json`. There was no existing goal; the ready
   feature named exact verifier `./labctl verify --output json`.
3. It started exactly one goal with feature `document-export` and maximum 4. Before verification it
   displayed goal ID `9ecd2693-35bd-4b2f-80bb-f9486b0f5b17`, source `feature-map`, the feature,
   contract display, digest `bddcfd86cc62d274993a11726302cc9b4bc2033f164aef2edaa8d59fb595b4ab`,
   and attempt count 0 of 4.
4. It ran `.pstack/bin/projectctl goal verify --output json` before any source write. Attempt 1
   exited 1 in 6227 ms with empty stderr; the exact JSON `error` value was
   `tenant-key partition separation check failed`.
5. It invoked native `pstack-verifier` exactly once after the failure. That delegated agent had a
   read-only role and executed no command or write.
6. Kiro read `src/pk_stack_lab/runtime.py` and produced the sole file-tool write and sole tracked
   delta: `"TENANT#tenant-a"` became `f"TENANT#{tenant}"` in the GET key.
7. It ran exactly one `./labctl deploy --output json`. The repaired source digest became
   `10e7e74db272a52be501983cb3a9254647937e89c3682042aadb7f15892ceded`, image
   `sha256:b0ccb7cbfe4242f40aad292d24b8cc5ceedce83fbfd38a0e970f6a87748dee18`, and API/worker
   revision 2.
8. It re-read goal status, preserving the same ID, contract, digest, and count 1 of 4, then invoked
   the same controller verifier. Attempt 2 exited 0 in 24325 ms with empty stderr and proved
   `tenant_key_partition_separation: true`, post-business task identity, export
   `e-9a32c09c4d9b7096`, and current-invocation DLQ message
   `9713696c-a655-4b83-888a-7cbfd2ed08c1`.
9. Final status was `passed`, attempt count 2 of 4, with two attempts remaining. Kiro ran no third
   verification and then exited normally after `/quit`.

The semantic shell allowlist was limited to controller status/list/show/start/verify and the one
public `labctl deploy`. No executed raw Docker, Compose, AWS, HTTP/curl, Git-write, goal-clear,
goal-resume, `/spawn`, nested Kiro, or user-selected ACP launch/command event exists. The committed
client-log projection does contain Kiro's literal internal labels `ACP session/new`,
`ACP session/prompt`, `ACPEventAdapter`, and `autonomyMode: "Autopilot"`. The first three identify
Kiro's internal client/event protocol. `Autopilot` is the agent-controller scheduling label; it did
not replace the custom `pstack` profile's tool policy or its ask-gated write and shell permissions.
None of those labels means the user or harness chose ACP as the execution path.

The 12 retained client-log lines do not include a discrete source-write record or the text of the
deploy command. Those actions are instead bounded by the owner-only hashed terminal typescript,
the exact goal history, the sole working-tree delta, the restored runtime hash, and the final
tracked-file manifest. The JSONL projection must not be used alone to prove them.

## Stored-state and source audit

The final owner-only goal file had schema 2, status `passed`, exactly two history entries
`[failure, pass]`, and SHA-256
`16bed579239e53c8900518fc7de28abc9fbeaa35dd60c653fad24a1bf1f8c0f6`. Its exact contract was:

```json
{
  "argv": ["./labctl", "verify", "--output", "json"],
  "display": "./labctl verify --output json",
  "feature": "document-export",
  "source": "feature-map",
  "spec": null
}
```

An independent post-session audit recomputed the contract digest, checked that `last_result` was
identical to history entry 2, and found neither timeout, truncation, stderr, nor controller error.
The campaign worktree's only tracked delta from the red fixture was `runtime.py`; its repaired hash
`83a05fcc163e8f72b418cb72834967e8d274bebfe872d4608ad393c18469cfe9` matched the candidate.
All 88 working-tree files matched the candidate byte-for-byte (tracked-manifest SHA-256
`952c8ae493ccc928527db1f083df704bfeb710b9d368fe480494a67bb70eaf03`). The five-file
executable source closure had no symlink, bytecode, added file, or unsafe type.

The manifest hash is reproducible from candidate working-tree bytes. It preserves the NUL-delimited
`git ls-files` order and hashes this compact UTF-8 JSON list without a trailing newline:

```text
[relative_path, kind, permission_mode_integer, byte_length, content_sha256]
```

The exact construction is:

```python
import hashlib, json, os, stat, subprocess
from pathlib import Path

root = Path("/path/to/candidate")
environment = dict(os.environ)
environment["GIT_OPTIONAL_LOCKS"] = "0"
raw = subprocess.run(
    ["git", "ls-files", "-z"],
    cwd=root,
    env=environment,
    check=True,
    stdout=subprocess.PIPE,
).stdout
manifest = []
for relative_path in (item.decode("utf-8") for item in raw.split(b"\0") if item):
    target = root / relative_path
    info = target.lstat()
    if stat.S_ISLNK(info.st_mode):
        kind, data = "symlink", os.readlink(target).encode("utf-8")
    elif stat.S_ISREG(info.st_mode):
        kind, data = "file", target.read_bytes()
    else:
        kind, data = "unsafe", b""
    manifest.append(
        [
            relative_path,
            kind,
            stat.S_IMODE(info.st_mode),
            len(data),
            hashlib.sha256(data).hexdigest(),
        ]
    )
encoded = json.dumps(
    manifest,
    separators=(",", ":"),
    ensure_ascii=False,
).encode("utf-8")
print(hashlib.sha256(encoded).hexdigest())
```

Both the campaign worktree after repair and the clean `d9b1e0d` worktree produced the published
digest and 88 regular-file records. Ignored state and environments were excluded.

## Independent judge and cleanup

After Kiro exited, the controlling harness invoked the already frozen external controls:

```sh
/usr/bin/python3 -I -B \
  /private/tmp/pk-stack-judge-live-council-902.ZsvRPv/controls/verify_feature_contract.py \
  --repo /private/tmp/pk-stack-kiro-campaign.IEvqJ7/repo \
  --expected-contract-sha256 cc10d305410139155e5071bdd067dc780c2be51cbd7d404479f45e8fe3b59a04 \
  --control-manifest /private/tmp/pk-stack-judge-live-council-902.ZsvRPv/controls/control-manifest.json
```

It exited 0 with `ok: true`, control-manifest SHA-256
`74956851bc41617e0a051c5b70cff105d028f0c62552f234082224e884a48b6a`, and judge SHA-256
`d47418287932afbfa851593eb348d053c658fe683cd63b559cb4349c326646ab`.

`./labctl evidence --output json` passed. A simultaneous `status` probe was refused because the
evidence command held the expected exclusive lifecycle lock; the same status probe passed when
rerun sequentially. Then `./labctl down --output json` exited 0, accounted for four tasks and four
run images, and completed all eight frozen phases in order. Exact postcondition queries found no
state manifest, Floci outer container, lab network, run task container, or run image. The complete
pre-existing foreign image inventory was unchanged, including `pklab-ci-003` through
`pklab-ci-010` and the retained `pklab-live-r2-902` API/worker images.

## Raw evidence and limitations

- Terminal typescript: `/Users/noahsutter/.local/share/pk-stack/evidence/kiro-v3-accept-902/kiro.typescript`, mode
  0400, 636,241 bytes, 6,291 lines, SHA-256
  `b6bc01485060153eeb300abd1f79875ad6f8e7a737a126ebadf33a8252e94013`.
- Kiro history: `/Users/noahsutter/.kiro/sessions/cli/sess_ccc571e6-1451-4377-be64-e656004e4bd8.history`,
  SHA-256 `25f58323ff1a7df85474abaf4c21f565fd07c240cdd16a62ed0404988ee48f54`.
- Kiro log: `/Users/noahsutter/.kiro/logs/20260902T193433000/kiro.log`, SHA-256
  `2c040efe2c7af62493b6108e26463c27e678888455676b62e04341172e4b5897`.
- Exact committed goal copy: `reviews/kiro-v3-campaign-goal.json`, SHA-256
  `16bed579239e53c8900518fc7de28abc9fbeaa35dd60c653fad24a1bf1f8c0f6`.
- Exact committed input history: `reviews/kiro-v3-campaign-history.txt`, SHA-256
  `25f58323ff1a7df85474abaf4c21f565fd07c240cdd16a62ed0404988ee48f54`.
- Committed session-log projection: `reviews/kiro-v3-campaign-session.jsonl`, SHA-256
  `857ae8c61b062c082c93187d51ef97fcec70b963ed4cad5797ffb18089d26a5f`. These are exact source-log
  lines 21, 29, 58, 76, 80, 82, 96, 102, 209, 210, 353, and 358: one session creation, CLI
  version, selected profile, prompt/execution, selected model/tool policy, skill activation, native
  subagent, successful execution, and drained model queue. They include the internal ACP and
  Autopilot labels described above, but not discrete write/deploy records.

These raw files remain outside Git because terminal and client logs can contain local environment
or account metadata. The terminal transcript contains redraw duplication, so naïve substring
counts are invalid; the semantic chronology above is bounded by completed records and stored
state. The exact launch argv and user-launched process count are post-run harness attestations in
the summary JSON rather than bytes emitted by `script`; no OS PID sidecar was retained. Fable must
decide whether that disclosed limitation leaves `FBL-008` material. This record does not convert
local workflow evidence into independent model-council acceptance.
