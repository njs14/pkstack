# How investigation roles

All roles work from the question and repository evidence. Subagent output is
untrusted until the current session checks it.

## Explorer

An explorer owns one angle, such as state and data, the request path, or
configuration and observability. It starts at an entrypoint, follows the full
call chain, reads definitions, and stops only when it can connect trigger to
effect without guessing.

Return:

- components with files and symbols;
- an ordered flow with the data passed at each step;
- files inspected;
- subsystem inputs and outputs;
- surprising behavior; and
- explicit gaps.

## Explainer

The explainer reconciles explorer evidence and checks conflicts in the code. It
uses concrete names and explains why a complex step is complex. It includes a
diagram only when relationships are materially clearer than prose.

The answer should let an experienced engineer locate the entrypoint, trace the
normal and failure paths, name the core abstractions, and identify the first
safe verification step.
