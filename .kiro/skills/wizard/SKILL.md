---
name: wizard
description: Generate a runnable guide for human-only setup or migration steps, with hidden secret entry and safe repeatable updates. Use when login, account UI, or human judgment prevents direct automation.
---

# Generate a human-run wizard

Honor the user's scope and active Kiro workflow. In native Plan, use permitted reading and
search, keep the result conversational, and defer commands, MCP calls, file writes, experiments,
and validation until execution is permitted. A skill invocation does not widen authority.

Inspect project setup examples, documentation, configuration names, and workflow references without
printing secret values. Identify the manual stages, dependencies, value names, where the human
gets each value, its destination, and whether it is secret. Reuse settled choices and ask only
about material gaps. Verify current UI paths and commands against authoritative documentation;
state uncertainty instead of inventing a click path.

Copy [template.sh](template.sh) to a requested or temporary working path and author the stages
below its marker. The helper library is reviewed source: preserve it in generated wizards.
Set the title, stage count, and explicit output file. Explain prerequisites and the effects of each
stage before it runs. Use `ask_secret` for secrets, `write_env` for local persistence, and explicit
confirmation in the generated flow before an irreversible action. Keep credentials in their
intended product; never copy authentication/session state between products.

The helper writes **POSIX shell assignment files**, defaulting to `.wizard.env`, and never sources
existing files. Verify the target application's parser supports this format before selecting its
`.env` path; use a separately reviewed format-specific writer otherwise. Values are single-line,
quoted literals; generated files are mode 0600 and updated atomically. Do not log values or enable
shell tracing. Do not use `eval`, interpolate values into commands, or pass secrets in arguments.
Pipe secrets to a verified destination only when the user expressly authorized that destination;
account helpers are not enabled merely by generating the script.

Validate `bash -n`, ShellCheck, and disposable behavioral tests with stubbed browser/account
commands. Exercise shell metacharacters, blank-entry reuse, repeated writes, EOF, and interruption;
verify no secret reaches output and incomplete runs do not claim success. Generating and testing
a wizard never executes its real account or infrastructure stages. Hand the human the absolute
script path, invocation, and remaining manual steps. Commit the wizard only when a repeatable
repository setup path is requested; otherwise keep it temporary.
