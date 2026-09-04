---
name: archify
description: Create polished, validated, offline-capable architecture, workflow, sequence, data-flow, and lifecycle diagrams with the reviewed Archify runtime.
---

# Archify

Treat the request text that activated this skill as the task input; do not
depend on CLI-only argument substitution.

Use the reviewed, byte-exact runtime in `upstream/` to turn a small typed JSON
specification into a self-contained interactive HTML diagram. The runtime is
bundled with this skill, so ordinary rendering, validation, delivery, and
visual-check work is offline-capable and does not need npm install.

Keep this Kiro wrapper separate from `upstream/`: this file is the
Kiro-native routing and safety contract, while `upstream/` is the reviewed
runtime snapshot recorded by the curated-skill manifests.

## Route and choose a mode

When a short explanation, pseudocode, call tree, shallow file tree, or Mermaid
sketch is enough, use `show-me`. When the user asks for a polished interactive
diagram, route the work here. `show-me-your-work` remains a distinct decision
and evidence-trail skill; do not substitute it for either visual route.

Choose exactly one diagram mode from the user's meaning:

| Mode | Use for |
| --- | --- |
| `architecture` | Components, services, infrastructure, cloud, and security boundaries |
| `workflow` | Processes, approvals, runbooks, CI/CD, and tool calls |
| `sequence` | API call chains, request lifecycles, async traces, and returns |
| `dataflow` | Pipelines, ETL/ELT, lineage, governance, and consumers |
| `lifecycle` | State/status transitions, retries, waiting, and terminal states |

For new workflows use schema v2. Preserve the semantic facts, identifiers,
commands, protocols, and environment names supplied by the user. Keep one
obvious main path, route meaningful labels, and let the runtime diagnose
geometry before adding explicit route controls.

## Bounded command contract

Resolve the runtime directory relative to this `SKILL.md` and run its entry
point with Node:

```text
node <resolved-skill-directory>/upstream/bin/archify.mjs doctor
node <resolved-skill-directory>/upstream/bin/archify.mjs validate <type> <input.json> --quality showcase --json
node <resolved-skill-directory>/upstream/bin/archify.mjs deliver <type> <input.json> <output.html> --quality showcase --json
node <resolved-skill-directory>/upstream/bin/archify.mjs visual-check <output.html> --json
```

Validate after each candidate edit. Use `deliver` once the specification is
ready; its deterministic receipt freezes the specification and artifact. Run
`visual-check` only against the exact delivered HTML. Keep automated browser
evidence and perceptual visual review as separate claims, and do not call a
non-zero command successful.

The runtime's `doctor` also checks its five mode renderers, schemas, examples,
validators, delivery dependencies, preview runtime, and visual-check runtime.
Node.js 18+ is optional to PK-Stack overall: if unavailable or too old, report
the Archify capability as a warning and continue with unrelated project
diagnostics.

## Network and brand boundary

Assume the network is denied. Do not fetch sources, run the update checker, or
perform a brand capture during ordinary authoring. Built-in brand marks are
local. A brand capture is allowed only when the user explicitly authorizes it
and supplies the official HTTP(S) URL; retain the digest-pinned result in the
authored specification and report the external evidence. Never infer a brand
from a vague role, and never let a badge replace semantic labels or
relationships.

Never modify the reviewed files under `upstream/`, install npm dependencies,
execute bundled tests, or regenerate the runtime during an ordinary diagram
request. Runtime refresh is a separately reviewed maintenance operation.
