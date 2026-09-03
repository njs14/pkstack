"use strict";

const ACTIVE_RUN_STATUSES = new Set([
  "in_progress",
  "pending",
  "queued",
  "requested",
  "waiting",
]);

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function exactTitlePull(pulls, policy) {
  assert(Array.isArray(pulls), "open pull-request inventory must be an array");
  const matches = pulls.filter((pull) => pull.title === policy.pull_request.title);
  assert(matches.length <= 1, "multiple exact-title maintenance pull requests are open");
  return matches[0] || null;
}

function sourceBindingFromBranch(headRef, policy) {
  const prefix = policy.pull_request.branch_prefix;
  assert(typeof headRef === "string" && headRef.startsWith(prefix),
    "maintenance candidate branch is outside the configured prefix");
  const suffix = headRef.slice(prefix.length);
  const match = /^(kiro)-([1-9][0-9]*)$/.exec(suffix);
  assert(match, "maintenance candidate branch does not bind one provider and source run id");
  const runId = Number(match[2]);
  assert(Number.isSafeInteger(runId), "maintenance source run id exceeds JavaScript precision");
  return { provider: match[1], runId, runIdText: match[2] };
}

function sourceAuthorityFromRun({
  sourceRun,
  policy,
  baseSha,
  defaultBranch,
  repositoryFullName,
  expectedProvider = null,
}) {
  assert(Array.isArray(policy.source_workflows),
    "maintenance source workflow policy must be an array");
  const configuredMatches = policy.source_workflows.filter(
    (item) => item.name === sourceRun?.name,
  );
  assert(configuredMatches.length === 1,
    "maintenance source run does not name exactly one configured workflow");
  const configured = configuredMatches[0];
  const runId = Number(sourceRun?.id);
  // GitHub's workflow-run REST resource reports `path` as the repository
  // relative workflow filename.  The `@branch` suffix belongs to a few
  // repository-content URLs, not to this resource's identity field.
  const expectedWorkflowRunPath = workflowPathAtDefaultBranch(configured.path);
  assert(Number.isSafeInteger(runId)
      && runId > 0
      && (expectedProvider === null || configured.provider === expectedProvider)
      && sourceRun.name === configured.name
      && sourceRun.path === expectedWorkflowRunPath
      && ["schedule", "workflow_dispatch"].includes(sourceRun.event)
      && sourceRun.status === "completed"
      && sourceRun.conclusion === "success"
      && sourceRun.head_branch === defaultBranch
      && sourceRun.head_sha === baseSha
      && sourceRun.repository?.full_name === repositoryFullName
      && (sourceRun.head_repository === undefined
        || sourceRun.head_repository?.full_name === repositoryFullName),
  "maintenance source run is not the exact successful default-branch authority");
  const runIdText = String(runId);
  return {
    provider: configured.provider,
    runId,
    runIdText,
    workflowName: configured.name,
    workflowPath: configured.path,
    workflowRunPath: expectedWorkflowRunPath,
    expectedHeadRef: `${policy.pull_request.branch_prefix}${configured.provider}-${runIdText}`,
  };
}

function validateOwnedCandidate({ pull, policy, defaultBranch, repositoryFullName }) {
  assert(pull.user?.login === policy.pull_request.author_login
      && pull.user?.id === policy.pull_request.author_id
      && pull.draft === false
      && pull.base?.ref === defaultBranch
      && pull.head?.repo?.full_name === repositoryFullName
      && Array.isArray(pull.labels)
      && pull.labels.length === 0,
  "the exact-title open PR is not an unmodified owned maintenance candidate");
  assert(/^[0-9a-f]{40}$/.test(pull.head?.sha || ""),
    "maintenance candidate head SHA is invalid");
  assert(/^[0-9a-f]{40}$/.test(pull.base?.sha || ""),
    "maintenance candidate base SHA is invalid");
  return sourceBindingFromBranch(pull.head.ref, policy);
}

function validateSourceRun({ sourceRun, binding, policy, baseSha, defaultBranch,
  repositoryFullName }) {
  const authority = sourceAuthorityFromRun({
    sourceRun,
    policy,
    baseSha,
    defaultBranch,
    repositoryFullName,
    expectedProvider: binding.provider,
  });
  assert(authority.runId === binding.runId,
    "maintenance candidate source run is not the exact successful default-branch authority");
}

function candidateRunTitle(policy, sourceRunId) {
  return `${policy.candidate_lifecycle.run_title_prefix}${sourceRunId}`;
}

function workflowPathAtDefaultBranch(path) {
  return path;
}

/**
 * Resolve the sole bot-owned candidate authorized by one exact source run.
 *
 * The source workflow name selects a single immutable policy entry. Its
 * provider and path, the source run id, and the resulting exact branch name
 * are then checked together. A source run can therefore never adopt a
 * candidate created by a different provider or run, even when both runs share
 * the same default-branch SHA.
 */
function resolveCandidateForSource({
  pulls,
  sourceRun,
  policy,
  baseSha,
  defaultBranch,
  repositoryFullName,
  expectedProvider = null,
}) {
  const source = sourceAuthorityFromRun({
    sourceRun,
    policy,
    baseSha,
    defaultBranch,
    repositoryFullName,
    expectedProvider,
  });
  const pull = exactTitlePull(pulls, policy);
  if (pull === null) {
    return { source, pull: null };
  }
  const branchBinding = validateOwnedCandidate({
    pull,
    policy,
    defaultBranch,
    repositoryFullName,
  });
  assert(branchBinding.provider === source.provider
      && branchBinding.runId === source.runId
      && pull.head.ref === source.expectedHeadRef
      && pull.base.sha === baseSha,
  "maintenance candidate is not bound to this exact base, provider, and source run");
  return { source, pull };
}

function validateCandidateRun({ run, policy, sourceRunId, baseSha, defaultBranch,
  repositoryFullName }) {
  const expectedRunTitle = candidateRunTitle(policy, sourceRunId);
  assert(Number.isSafeInteger(run?.id)
      && run.id > 0
      // For a workflow_run resource GitHub populates both `name` and
      // `display_title` from the configured run-name.  Bind both fields to
      // the source run id so a same-workflow run cannot be adopted by a
      // different candidate.
      && run.name === expectedRunTitle
      && run.path === workflowPathAtDefaultBranch(
        policy.candidate_lifecycle.workflow_path,
      )
      && run.display_title === expectedRunTitle
      && run.event === "workflow_run"
      && run.head_branch === defaultBranch
      && run.head_sha === baseSha
      && run.repository?.full_name === repositoryFullName,
  "candidate gate run is not bound to the exact source/base/workflow identity");
}

function lifecycleDecision({ run, policy, nowMs }) {
  assert(Number.isSafeInteger(nowMs) && nowMs >= 0, "lifecycle clock is invalid");
  const updatedMs = Date.parse(run.updated_at);
  assert(Number.isFinite(updatedMs) && updatedMs <= nowMs + 300_000,
    "candidate gate run timestamp is invalid or materially in the future");
  const ageSeconds = Math.floor((nowMs - updatedMs) / 1000);
  if (ACTIVE_RUN_STATUSES.has(run.status)) {
    if (ageSeconds <= policy.candidate_lifecycle.freshness_seconds) {
      return { action: "skip", reason: "fresh-active-candidate", ageSeconds };
    }
    return { action: "close", reason: "stale-active-candidate", ageSeconds };
  }
  assert(run.status === "completed", "candidate gate run has an unknown lifecycle status");
  assert(typeof run.conclusion === "string" && run.conclusion.length > 0,
    "completed candidate gate run is missing its conclusion");
  return {
    action: "close",
    reason: run.conclusion === "success"
      ? "successful-candidate-left-open-pr"
      : `terminal-candidate-${run.conclusion}`,
    ageSeconds,
  };
}

/**
 * Classify one exact-title open PR without mutating GitHub state.
 *
 * A current-base candidate suppresses maintenance credits only while the exact
 * candidate-gate run for its source run is fresh and active. Every terminal,
 * missing, duplicated, or stale lifecycle closes only the fully authenticated
 * bot candidate so a future source run can make progress. Human or malformed
 * PR identities throw and are never selected for mutation.
 */
async function classifyOpenCandidate({
  pulls,
  policy,
  baseSha,
  defaultBranch,
  repositoryFullName,
  loadCommit,
  loadSourceRun,
  loadCandidateRuns,
  nowMs,
}) {
  const pull = exactTitlePull(pulls, policy);
  if (pull === null) {
    return { action: "run" };
  }
  const binding = validateOwnedCandidate({ pull, policy, defaultBranch, repositoryFullName });

  const commit = await loadCommit(pull.head.sha);
  assert(Array.isArray(commit.parents) && commit.parents.length === 1,
    "maintenance candidate head must have exactly one parent");
  const parentSha = commit.parents[0]?.sha;
  assert(/^[0-9a-f]{40}$/.test(parentSha || ""),
    "maintenance candidate parent is missing or invalid");

  const close = (reason, extra = {}) => ({
    action: "close",
    prNumber: pull.number,
    headRef: pull.head.ref,
    reason,
    ...extra,
  });
  if (parentSha !== baseSha || pull.base.sha !== baseSha) {
    return close("stale-base", { staleParentSha: parentSha });
  }

  const sourceRun = await loadSourceRun(binding.runId);
  validateSourceRun({
    sourceRun,
    binding,
    policy,
    baseSha,
    defaultBranch,
    repositoryFullName,
  });
  const candidateRuns = await loadCandidateRuns(binding.runId);
  assert(Array.isArray(candidateRuns), "candidate gate run inventory must be an array");
  const exactTitle = candidateRunTitle(policy, binding.runId);
  const matchingRuns = candidateRuns.filter((run) => run.display_title === exactTitle);
  if (matchingRuns.length === 0) {
    return close("missing-candidate-run", { sourceRunId: binding.runId });
  }
  if (matchingRuns.length !== 1) {
    return close("duplicate-candidate-runs", { sourceRunId: binding.runId });
  }
  const run = matchingRuns[0];
  validateCandidateRun({
    run,
    policy,
    sourceRunId: binding.runId,
    baseSha,
    defaultBranch,
    repositoryFullName,
  });
  const lifecycle = lifecycleDecision({ run, policy, nowMs });
  if (lifecycle.action === "skip") {
    return {
      ...lifecycle,
      prNumber: pull.number,
      headRef: pull.head.ref,
      sourceRunId: binding.runId,
      candidateRunId: run.id,
      candidateRunStatus: run.status,
    };
  }
  return close(lifecycle.reason, {
    sourceRunId: binding.runId,
    candidateRunId: run.id,
    candidateRunStatus: run.status,
    candidateRunConclusion: run.conclusion,
    ageSeconds: lifecycle.ageSeconds,
  });
}

/** Authenticate the sole PR that a terminal candidate workflow may close. */
async function authorizeTerminalCandidateClose({
  pulls,
  policy,
  baseSha,
  defaultBranch,
  repositoryFullName,
  sourceRun,
  candidateRun,
  loadCommit,
}) {
  const pull = exactTitlePull(pulls, policy);
  if (pull === null) {
    return { action: "none", reason: "no-open-candidate" };
  }
  const binding = validateOwnedCandidate({ pull, policy, defaultBranch, repositoryFullName });
  assert(binding.runId === sourceRun.id,
    "open maintenance candidate does not belong to this source run");
  validateSourceRun({
    sourceRun,
    binding,
    policy,
    baseSha,
    defaultBranch,
    repositoryFullName,
  });
  validateCandidateRun({
    run: candidateRun,
    policy,
    sourceRunId: binding.runId,
    baseSha,
    defaultBranch,
    repositoryFullName,
  });
  assert(ACTIVE_RUN_STATUSES.has(candidateRun.status),
    "terminal cleanup must execute inside its still-active candidate gate run");
  const commit = await loadCommit(pull.head.sha);
  assert(Array.isArray(commit.parents) && commit.parents.length === 1
      && commit.parents[0]?.sha === baseSha
      && pull.base.sha === baseSha,
  "terminal cleanup candidate is no longer exactly one commit atop the source base");
  return {
    action: "close",
    prNumber: pull.number,
    headRef: pull.head.ref,
    headSha: pull.head.sha,
    sourceRunId: binding.runId,
    candidateRunId: candidateRun.id,
  };
}

module.exports = {
  authorizeTerminalCandidateClose,
  candidateRunTitle,
  classifyOpenCandidate,
  lifecycleDecision,
  resolveCandidateForSource,
};
