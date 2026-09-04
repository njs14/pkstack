"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const {
  authorizeTerminalCandidateClose,
  classifyOpenCandidate,
  resolveCandidateForSource,
} = require("./pk_stack_pr_policy.js");

const CURRENT_BASE = "a".repeat(40);
const OLD_BASE = "b".repeat(40);
const HEAD = "c".repeat(40);
const SOURCE_RUN_ID = 123456;
const CANDIDATE_RUN_ID = 789012;
const NOW = Date.parse("2026-09-02T12:00:00Z");
const candidateWorkflow = fs.readFileSync(
  path.join(__dirname, "../workflows/pk-stack-upstream-candidate.yml"),
  "utf8",
);
const sourceRunFixture = JSON.parse(fs.readFileSync(
  path.join(__dirname, "../fixtures/github-actions-run-33761288363.json"),
  "utf8",
));
const candidateRunFixture = JSON.parse(fs.readFileSync(
  path.join(__dirname, "../fixtures/github-actions-run-33761403736.json"),
  "utf8",
));
const policy = {
  source_workflows: [
    {
      name: "PK-Stack Upstream Maintenance (Kiro)",
      provider: "kiro",
      path: ".github/workflows/pk-stack-upstream-maintenance-kiro.yml",
    },
  ],
  pull_request: {
    author_id: 41898282,
    author_login: "github-actions[bot]",
    branch_prefix: "pk-stack-upstream/",
    title: "[pk-stack upstream] Reconcile pinned upstream semantics",
  },
  candidate_lifecycle: {
    workflow_name: "PK-Stack Upstream Candidate Gate",
    workflow_path: ".github/workflows/pk-stack-upstream-candidate.yml",
    run_title_prefix: "PK-Stack candidate gate for source run ",
    freshness_seconds: 21600,
  },
};

function pull(overrides = {}) {
  return {
    number: 7,
    title: policy.pull_request.title,
    draft: false,
    user: { login: policy.pull_request.author_login, id: policy.pull_request.author_id },
    labels: [],
    base: { ref: "main", sha: CURRENT_BASE },
    head: {
      ref: `pk-stack-upstream/kiro-${SOURCE_RUN_ID}`,
      sha: HEAD,
      repo: { full_name: "owner/repo" },
    },
    ...overrides,
  };
}

function sourceRun(overrides = {}) {
  return {
    id: SOURCE_RUN_ID,
    name: "PK-Stack Upstream Maintenance (Kiro)",
    path: ".github/workflows/pk-stack-upstream-maintenance-kiro.yml",
    event: "schedule",
    status: "completed",
    conclusion: "success",
    head_branch: "main",
    head_sha: CURRENT_BASE,
    repository: { full_name: "owner/repo" },
    ...overrides,
  };
}

function candidateRun(overrides = {}) {
  return {
    id: CANDIDATE_RUN_ID,
    name: `${policy.candidate_lifecycle.run_title_prefix}${SOURCE_RUN_ID}`,
    path: policy.candidate_lifecycle.workflow_path,
    display_title: `${policy.candidate_lifecycle.run_title_prefix}${SOURCE_RUN_ID}`,
    event: "workflow_run",
    status: "in_progress",
    conclusion: null,
    head_branch: "main",
    head_sha: CURRENT_BASE,
    repository: { full_name: "owner/repo" },
    updated_at: "2026-09-02T11:30:00Z",
    ...overrides,
  };
}

async function classify(pulls, {
  parentSha = CURRENT_BASE,
  source = sourceRun(),
  runs = [candidateRun()],
  nowMs = NOW,
} = {}) {
  const loaded = { commits: [], sources: [], candidateSources: [] };
  const result = await classifyOpenCandidate({
    pulls,
    policy,
    baseSha: CURRENT_BASE,
    defaultBranch: "main",
    repositoryFullName: "owner/repo",
    loadCommit: async (sha) => {
      loaded.commits.push(sha);
      return { parents: [{ sha: parentSha }] };
    },
    loadSourceRun: async (runId) => {
      loaded.sources.push(runId);
      return source;
    },
    loadCandidateRuns: async (runId) => {
      loaded.candidateSources.push(runId);
      return runs;
    },
    nowMs,
  });
  return { result, loaded };
}

function resolveSourceCandidate(pulls, source, expectedProvider = "kiro") {
  return resolveCandidateForSource({
    pulls,
    sourceRun: source,
    policy,
    baseSha: CURRENT_BASE,
    defaultBranch: "main",
    repositoryFullName: "owner/repo",
    expectedProvider,
  });
}

test("resolves policy name, provider, workflow path, run id, and exact branch together", () => {
  const result = resolveSourceCandidate([pull()], sourceRun());
  assert.equal(result.pull?.number, 7);
  assert.deepEqual(result.source, {
    provider: "kiro",
    runId: SOURCE_RUN_ID,
    runIdText: String(SOURCE_RUN_ID),
    workflowName: "PK-Stack Upstream Maintenance (Kiro)",
    workflowPath: ".github/workflows/pk-stack-upstream-maintenance-kiro.yml",
    workflowRunPath: ".github/workflows/pk-stack-upstream-maintenance-kiro.yml",
    expectedHeadRef: `pk-stack-upstream/kiro-${SOURCE_RUN_ID}`,
  });
});

test("matches captured GitHub Actions REST run shapes exactly", () => {
  assert.equal(sourceRunFixture.id, 33761288363);
  assert.equal(
    sourceRunFixture.path,
    ".github/workflows/pk-stack-upstream-maintenance-kiro.yml",
  );
  assert.equal(sourceRunFixture.name, "PK-Stack Upstream Maintenance (Kiro)");
  assert.equal(sourceRunFixture.display_title, "PK-Stack Upstream Maintenance (Kiro)");
  assert.equal(candidateRunFixture.id, 33761403736);
  assert.equal(candidateRunFixture.path, ".github/workflows/pk-stack-upstream-candidate.yml");
  assert.equal(candidateRunFixture.name, "PK-Stack candidate gate for source run 33761288363");
  assert.equal(
    candidateRunFixture.display_title,
    "PK-Stack candidate gate for source run 33761288363",
  );
  // These are the real observed terminal records.  The source failure and
  // candidate skip must remain fail-closed rather than being treated as a
  // successful maintenance authority.
  assert.throws(
    () => resolveCandidateForSource({
      pulls: [],
      sourceRun: sourceRunFixture,
      policy,
      baseSha: sourceRunFixture.head_sha,
      defaultBranch: sourceRunFixture.head_branch,
      repositoryFullName: sourceRunFixture.repository.full_name,
    }),
    /exact successful default-branch authority/,
  );
});

test("one Kiro source run cannot adopt another Kiro run's branch", () => {
  const otherRun = sourceRun({ id: SOURCE_RUN_ID + 1 });
  assert.throws(
    () => resolveSourceCandidate([pull()], otherRun),
    /not bound to this exact base, provider, and source run/,
  );
});

test("candidate gate is triggered only by Kiro maintenance", () => {
  const trigger = candidateWorkflow.split("\npermissions:", 1)[0];
  assert.match(trigger, /- PK-Stack Upstream Maintenance \(Kiro\)/);
});

test("candidate workflow carries the resolved source authority through merge", () => {
  for (const output of [
    "source_provider",
    "source_run_id",
    "source_workflow",
    "source_workflow_path",
    "candidate_branch",
  ]) {
    assert.match(
      candidateWorkflow,
      new RegExp(`${output}: \\$\\{\\{ steps\\.resolve\\.outputs\\.${output} \\}\\}`),
    );
  }
  assert.match(candidateWorkflow, /github\.rest\.actions\.getWorkflowRun/);
  assert.match(
    candidateWorkflow,
    /pull\.head\.ref === process\.env\.CANDIDATE_BRANCH/,
  );
  assert.equal(
    candidateWorkflow.match(/resolveCandidateForSource\(\{/g)?.length,
    3,
  );
});

test("runs when no exact-title PR exists", async () => {
  const { result, loaded } = await classify([]);
  assert.deepEqual(result, { action: "run" });
  assert.deepEqual(loaded, { commits: [], sources: [], candidateSources: [] });
});

test("skips only a fresh active candidate run bound to exact bot, base, head, and source", async () => {
  const { result, loaded } = await classify([pull()]);
  assert.deepEqual(result, {
    action: "skip",
    reason: "fresh-active-candidate",
    ageSeconds: 1800,
    prNumber: 7,
    headRef: `pk-stack-upstream/kiro-${SOURCE_RUN_ID}`,
    sourceRunId: SOURCE_RUN_ID,
    candidateRunId: CANDIDATE_RUN_ID,
    candidateRunStatus: "in_progress",
  });
  assert.deepEqual(loaded, {
    commits: [HEAD],
    sources: [SOURCE_RUN_ID],
    candidateSources: [SOURCE_RUN_ID],
  });
});

for (const scenario of ["rejection report upload failure", "feedback CAS failure", "cleanup failure"]) {
  test(`${scenario} blocks cadence until durable feedback is reconciled`, async () => {
    await assert.rejects(() => classify([pull()], {
      runs: [candidateRun({ status: "completed", conclusion: "failure" })],
    }), /requires operator recovery: terminal-candidate-failure/);
  });
}

test("canceled and missing candidate runs cannot discard unknown feedback", async () => {
  await assert.rejects(() => classify([pull()], {
    runs: [candidateRun({ status: "completed", conclusion: "cancelled" })],
  }), /requires operator recovery: terminal-candidate-cancelled/);
  await assert.rejects(() => classify([pull()], { runs: [] }), /missing-candidate-run/);
});

test("stale active and successful-open states require operator recovery", async () => {
  await assert.rejects(() => classify([pull()], {
    runs: [candidateRun({ updated_at: "2026-09-02T05:59:59Z" })],
  }), /requires operator recovery: stale-active-candidate/);
  await assert.rejects(() => classify([pull()], {
    runs: [candidateRun({ status: "completed", conclusion: "success" })],
  }), /requires operator recovery: successful-candidate-left-open-pr/);
});

test("base movement cannot bypass unresolved rejection publication", async () => {
  const stale = pull({ base: { ref: "main", sha: OLD_BASE } });
  await assert.rejects(() => classify([stale], { parentSha: OLD_BASE }),
    /requires operator recovery: stale-base/);
});

test("source and candidate workflow identity mismatches fail closed", async () => {
  await assert.rejects(
    () => classify([pull()], { source: sourceRun({ head_sha: OLD_BASE }) }),
    /exact successful default-branch authority/,
  );
  await assert.rejects(
    () => classify([pull()], {
      runs: [candidateRun({ path: ".github/workflows/other.yml" })],
    }),
    /exact source\/base\/workflow identity/,
  );
  await assert.rejects(
    () => classify([pull()], {
      runs: [candidateRun({ head_sha: OLD_BASE })],
    }),
    /exact source\/base\/workflow identity/,
  );
});

test("terminal cleanup authorizes only this still-active exact candidate workflow", async () => {
  const result = await authorizeTerminalCandidateClose({
    pulls: [pull()],
    policy,
    baseSha: CURRENT_BASE,
    defaultBranch: "main",
    repositoryFullName: "owner/repo",
    sourceRun: sourceRun(),
    candidateRun: candidateRun(),
    loadCommit: async () => ({ parents: [{ sha: CURRENT_BASE }] }),
  });
  assert.deepEqual(result, {
    action: "close",
    prNumber: 7,
    headRef: `pk-stack-upstream/kiro-${SOURCE_RUN_ID}`,
    headSha: HEAD,
    sourceRunId: SOURCE_RUN_ID,
    candidateRunId: CANDIDATE_RUN_ID,
  });
});

test("human, ambiguous, labeled, and non-linear candidates are never selected for mutation", async () => {
  const human = pull({ user: { login: "human", id: 123 } });
  await assert.rejects(() => classify([human]), /not an unmodified owned maintenance candidate/);
  await assert.rejects(
    () => classify([pull(), pull({ number: 8 })]),
    /multiple exact-title/,
  );
  await assert.rejects(
    () => classify([pull({ labels: [{ name: "human-touched" }] })]),
    /not an unmodified owned maintenance candidate/,
  );
  await assert.rejects(
    () => classifyOpenCandidate({
      pulls: [pull()],
      policy,
      baseSha: CURRENT_BASE,
      defaultBranch: "main",
      repositoryFullName: "owner/repo",
      loadCommit: async () => ({ parents: [{ sha: OLD_BASE }, { sha: CURRENT_BASE }] }),
      loadSourceRun: async () => sourceRun(),
      loadCandidateRuns: async () => [candidateRun()],
      nowMs: NOW,
    }),
    /exactly one parent/,
  );
});

test("terminal cleanup leaves human and ambiguous exact-title PRs untouched", async () => {
  const common = {
    policy,
    baseSha: CURRENT_BASE,
    defaultBranch: "main",
    repositoryFullName: "owner/repo",
    sourceRun: sourceRun(),
    candidateRun: candidateRun(),
    loadCommit: async () => ({ parents: [{ sha: CURRENT_BASE }] }),
  };
  await assert.rejects(
    () => authorizeTerminalCandidateClose({
      ...common,
      pulls: [pull({ user: { login: "human", id: 123 } })],
    }),
    /not an unmodified owned maintenance candidate/,
  );
  await assert.rejects(
    () => authorizeTerminalCandidateClose({
      ...common,
      pulls: [pull(), pull({ number: 8 })],
    }),
    /multiple exact-title/,
  );
});
