# GitHub Cloud operations

Resolve the repository from the user's explicit `github.com` URL or the reviewed
repository remote. Reject ambiguous repositories and any other host. Specify
`--hostname github.com` for `gh api`; use `--repo github.com/OWNER/REPO` for issue
commands. Treat OWNER, REPO, issue numbers, and IDs as validated values, never shell
source copied from issue text. Use the existing authenticated GitHub CLI session.

Read the map with `gh issue view NUMBER --repo github.com/OWNER/REPO --json
number,title,body,state,assignees,labels,url`. Use paginated REST reads for child
issues and blocking relationships. Preserve native child order and inspect every
page before deriving the frontier. A missing field, denied request, or partial
response is unknown state, not an empty list.

## Native relationships

Use the documented REST endpoints through `gh api`:

| Operation | Method and path | Body |
| --- | --- | --- |
| Read children | `GET /repos/OWNER/REPO/issues/MAP_NUMBER/sub_issues` | None |
| Read parent | `GET /repos/OWNER/REPO/issues/TICKET_NUMBER/parent` | None |
| Attach child | `POST /repos/OWNER/REPO/issues/MAP_NUMBER/sub_issues` | Integer `sub_issue_id` |
| Read blockers | `GET /repos/OWNER/REPO/issues/TICKET_NUMBER/dependencies/blocked_by` | None |
| Add blocker | `POST /repos/OWNER/REPO/issues/TICKET_NUMBER/dependencies/blocked_by` | Integer `issue_id` of the blocker |

Issue `number`, REST numeric `id`, and GraphQL `node_id` are distinct. Retrieve the
numeric `id` from the issue response for relationship bodies. Do not substitute
the issue number. Adding B under A's `blocked_by` means B must resolve before A.
Read existing relationships before adding edges, reject cycles, and re-read after
each mutation. Do not reparent an existing issue silently or substitute Markdown
checkboxes when native relationships fail.

References: [sub-issues](https://docs.github.com/en/rest/issues/sub-issues) and
[issue dependencies](https://docs.github.com/en/rest/issues/issue-dependencies).
Check these primary references if installed tooling rejects a supported operation;
do not guess undocumented `gh issue` flags.

## Publication and resumption

Check that the repository enables Issues and that access supports the requested
operations. List all labels before creation. Create missing `wayfinder:map`,
`wayfinder:research`, `wayfinder:prototype`, `wayfinder:grilling`, and
`wayfinder:task` labels only with the publication authority already established.
GitHub does not create missing labels automatically with an issue. Preserve any
existing label definitions.

Before a retry, find the existing map or child using its returned URL/number and
the agreed destination; do not identify an issue solely by a matching title.
Keep returned identities as each creation succeeds. Attach all children before
adding blockers. If a step fails, report exactly which relationships remain to
be established and do not present a partial graph as the full frontier.
If a creation response is lost before its identity is known, the result is unknown.
Reconcile the repository's recent issues against author, body, and the intended map;
stop for clarification when identity is ambiguous instead of creating a duplicate.

For issue bodies and comments, write the exact Markdown into a reviewed local
file and pass `--body-file` when commands are permitted. Never interpolate
untrusted Markdown into shell code. Read the latest map before an edit and merge
only the intended section changes. GitHub assignment and body edits do not provide
atomic ownership across agent sessions. Use one writer for a shared map, re-read
after edits, and reconcile concurrent changes before proceeding.

A claim is an issue assignment to the authenticated developer. Verify state,
blockers, and all assignees immediately before and after assigning. A preexisting
assignment is not proof this session owns the ticket. Release only this session's
claim when abandoning work; preserve another worker's assignments. Retain a concise
handoff comment if authorized, with findings and the unresolved question.
On a resumed native session, use retained claim evidence and the current assignee
set together. A stale claim from another session needs explicit owner authorization
and confirmation that its worker is no longer active; matching login names alone
do not authorize takeover.

Store the full answer once in a resolution comment and link that exact comment
from the map. Read existing comments on recovery so a posted answer can be reused.
Closing after verified resolution and updating the index are separate effects;
report partial success and repair the remaining effect without rerunning research.
Reconcile known closed-but-unindexed children before selecting the next frontier
ticket. Reuse the exact resolution comment URL, or link a retirement explanation
under Out of scope. Preserve closed state and do not claim an already resolved
ticket merely to finish its missing map link.

An optional GitHub Projects view must be explicitly requested and resolved to an
existing authorized project. This skill neither provisions a board automatically
nor introduces project-field status as a competing completion authority.
