# PKStack 0.4.2 onboarding acceptance

The documented first task passed through ordinary Kiro CLI v3 on macOS:
**stored failure → Kiro-authored repair → stored pass**, with all four tests
and the verifier unchanged. This is a bounded first-task result, not a general
correctness guarantee or a new IDE acceptance campaign.

## What was exercised

An actual GitHub clone of the candidate branch supplied a new Power source
path containing spaces. The source variable started unset and was captured
before changing into a separate disposable target, also under a path with
spaces. The documented preview and installation commands ran with the Mac's
Python 3.9.6 launcher; `uv` supplied the supported controller runtime.
Installation reported version 0.4.2, doctor **84 pass / 0 fail / 0 warn**, passing
local knowledge validation, and zero changes on a second setup.

The observer created the documented goal and recorded its expected first
failure: three of four tests failed. In a fresh ordinary
`kiro-cli chat --v3 --agent pkstack` session, Kiro received the complete
first-task request, loaded `pkstack-verified-goal`, displayed the stored verifier
and explicit-command source, and read the implementation and tests. Before
approving its first write, the observer confirmed the broken code and tests
still matched their baseline hashes. Kiro made both implementation edits and
invoked the stored verifier in that conversation, using one-time approvals.
It reached `passed` on attempt **2 of 4**. A subsequent direct four-test run
also passed. The observer supplied no repair and created no passing goal attempt.

The observed model label was **Auto**; effort was not displayed. Existing
account settings and caches were retained. Fresh paths therefore do not prove
fresh-account or empty-cache onboarding. No model, permission, or account
configuration was changed for the campaign.

## Evidence and candidate binding

- [Campaign receipt](campaign.json): immutable source/Power identities,
  file hashes, native observations, limits, and final documentation delta.
- [Stored goal history](goal-history.json): unchanged contract and both attempts;
  local paths in tracebacks are replaced with `<consumer>`.
- [Model-authored implementation diff](implementation.diff) and
  [independent test output](standalone-tests.txt).
- [Executed setup commands](commands.json): local paths replaced with role labels.

The native campaign used commit `83b0e944c9c359054955579481c6b31bc084687d`,
Power tree `7f0beda47b5059b884feb9158af1a2f76d00254e`.
The later saved-request explanation changes usage, architecture, and the
changelog. The receipt binds unchanged first-task, installer, runtime, skill,
fixture, template, and generated-workspace Git objects to both candidates.
The final whole Power tree differs; it is not described as byte-identical to
the tested tree. Independent reviewer `onboarding_final_review` approved the
native evidence with no blocking findings. Final-diff review and hosted release
gates are recorded separately in the [release status](../release-status.md).

## Local regressions

The final focused command passed **7 tests** with 117 deselected in 29.28 seconds:

```sh
uv run --frozen --project powers/pkstack pytest \
  powers/pkstack/tests/test_readme_walkthrough.py \
  powers/pkstack/tests/test_release_metadata.py \
  powers/pkstack/tests/test_kiro_assets.py -q \
  -k 'readme or declared_power_source or release_metadata or missing_uv or first_task'
```

Earlier setup fallback tests and the 22-test shared fast contract also passed.
The initial fast run found an obsolete documentation assertion that rejected
any absolute target placeholder. It was narrowed to check the declared Power
source on installer lines; executable walkthrough tests cover the actual
source-to-target transition. The corrected fast run passed. The final setup
preview reported zero pending changes. Hosted full-suite CI remains a separate
release gate.

## Disclosed probe limits

An earlier input-harness probe submitted only the skill name because the
terminal autocomplete was entered separately from the request body. It was
cancelled before the first implementation write. Its goal remains active with
one failed attempt and unchanged code/tests; it is excluded from pass evidence.
The successful run pasted the complete request, inspected it, and then submitted.

After the successful repair, `/prompts` opened the native selection menu,
including skills and a right-arrow details control. The general prompt guide's
`/prompts details pkstack-verified-goal` syntax instead became the ordinary
model request `/details pkstack-verified-goal`; streaming was cancelled without
tools or writes. No saved prompt files were created. Saved-file creation,
`@name` expansion, skill activation through expanded requests, and IDE local
prompt-file behavior remain unverified. The default first-task path stays a
direct skill invocation; saved requests remain an optional user-owned design
layer. See [usage](../../powers/pkstack/docs/usage.md#save-a-recurring-request-in-kiro).

Raw terminal and local observation files stay outside Git because they contain
machine/runtime metadata. Their hashes are retained in the campaign receipt.
Mechanical onboarding regressions continue to use a scripted repair and are
labelled separately from this model-driven campaign. No new knowledge-retrieval
or IDE GUI repair result is claimed.
