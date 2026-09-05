# PKStack 0.3.0 browser-harness startup cleanup

The reader regression now closes its browser and removes its temporary profile
when CDP startup rejects. An injected startup failure proves that cleanup defect
and its repair. The initiating live CI `Target.getTargets` timeout remains
unreproduced; this change does not establish its cause or a Linux fix.

## Original live failure

The updater's base-test job in run `33977500077`, against
`3859f635e36b26d813802445cceb037cc26d0dfc`, failed on 2026-09-05 with
`Target.getTargets: timed out after 15000ms`. The failure occurred on the first
CDP startup request, before navigation, layout measurements, or exports. The
runner used Ubuntu 24.04.4 and Node.js 22.23.2. Its Power result was
`1 failed, 867 passed, 1 skipped in 91.41s`; the failure was
`test_archify_reader_layout_and_exports`.

The retained log is
`/private/tmp/pkstack-release-030-evidence/live-updater-review/base-tests.log`,
lines 648-699. It identifies the timed-out request but does not identify why
Chrome failed to answer. Local successful startup probes cannot resolve that
Linux/Node 22 failure.

## Proven defect and bounded repair

In [the JavaScript harness](../powers/pkstack/tests/test_archify_reader_layout.mjs),
`await browser.sessionPromise` ran before the existing `try/finally`. Rejection
there bypassed `browser.close()`. The patch moves that await into the existing
`try`, before any browser interaction. Helper functions receive the session
before use, and the successful command order remains the same.

[The new regression](../powers/pkstack/tests/test_archify_reader_layout.py)
launches the actual harness with a temporary executable that sends malformed
CDP JSON and stays alive until terminated. Against the unchanged harness it
failed because startup rejection left the browser child running. After the
patch it requires the expected CDP error, a SIGTERM receipt, an absent process,
and a removed profile. Its fallback cleanup also contains the injected child
and profile if an assertion fails.

Only those two test files changed. Vendored runtime and provenance are
unchanged. The 15-second CDP deadline, 120-second outer browser-test limit,
layout thresholds, required browser assertions, and existing skip behavior
remain unchanged. There is no retry or soft-pass path.

## Local evidence and review

The local runtime was macOS, Node.js 26.8.1, and Chrome 152.0.7977.77. The
unchanged full browser test passed before the repair in 17.18 seconds. Eight
sequential startup probes against the unchanged browser implementation all
passed: 1309, 885, 884, 881, 875, 881, 882, and 896 milliseconds. Each awaited
attachment, requested `Browser.getVersion`, and closed the browser.

After the repair, `uv run --offline pytest tests/test_archify_reader_layout.py -q`
passed all five focused cases in 17.79 seconds. This includes real browser
layout checks, zoom/pan/reset, and downloads through the actual export menu for
SVG, PNG, JPEG, WebP, Share Card, and WebM. A final cleanup-only rerun passed in
0.65 seconds. Ruff lint, Ruff format check, `ty check` for the Python test, and
`git diff --check` passed.

Retained local evidence under `/private/tmp/pkstack-release-030-evidence/`:

- `archify-startup-cleanup-before.log`: reproduced cleanup failure before the repair.
- `archify-startup-cleanup-after.log`: all five focused tests passed.
- `archify-startup-stress.json`: all eight startup timings and runtime identity.

An independent read-only review covered the narrow two-file diff and cleanup
ownership. It confirmed the fix and the regression's ordering and assertions;
the reviewer did not run tests. The injected executable uses POSIX shebang and
signal behavior, consistent with existing Power subprocess fixtures. Current
CI workflows use Ubuntu 24.04; no Windows validation is claimed. The reviewer
also noted that fallback cleanup on a failing regression signals the child
without waiting, while the passing path explicitly verifies process exit.

Full-suite results belong to the coordinator's release reports. This evidence
establishes local startup-rejection cleanup and preserved render/export checks.
Validation on Linux requires the next CI run against the exact patched commit;
the original timeout trigger remains unresolved in this report.
