# PKStack 0.3.0 Archify repair

The retained account-request diagram now passes the original showcase and
browser checks without changing its JSON. The release investigation also found
and fixed three visible defects: a sequence caption hidden by participant boxes,
a caption moved into the preceding sequence band, and toolbar buttons outside
the narrow viewport. These are local PKStack
maintenance patches to the pinned Archify runtime, not an upstream update.

This lane changed the Archify wrapper, two vendored runtime files, focused
regression tests, and Archify provenance manifests. Generated consumer assets
remain the coordinator's integration responsibility. A fresh native Kiro smoke
is documented separately below; no credential transfer, dependency install,
publication, or commit was used here.

## Reproduction and diagnosis

The release checkout started at `3d4583a16fe2caca497d8b8fe7d5c860a12c1a2f`.
The preserved consumer was `/private/tmp/pkstack-curated-smoke.fyhM5s`.
The new evidence directory is `/private/tmp/pkstack-archify-release.VuUtol`.

The original specification is retained byte-for-byte in
`powers/pkstack/tests/fixtures/archify-account-request.sequence.json`:
SHA-256 `f9cdda4d0fcac50a840ab56d682698a8cdf415dbe3459fd1ca671df0d28452f1`.
Before the patch, delivery recreated the historical artifact hash exactly:
`6708e0ca53deba7f93f426059e1414bc7b06d9306923c215dbd43554e29e436f`.
Its nine showcase checks passed, but `visual-check` exited 1. This reproduces
the recorded defect against the current release checkout rather than relying
only on the historical receipt.

| Confirmed defect | Cause | Repair |
| --- | --- | --- |
| Account timeline extends below desktop viewport | Adaptive layout accepted only viewBox ratios at least 1.55; the valid 760-by-620 sequence has ratio 1.226 and was inflated to the default desktop width. | Apply the existing adaptive layout to valid compact diagrams too. Their width floor may use authored width plus chrome, capped by the existing desktop floor. Wide diagrams retain their existing floor. |
| Request acceptance caption obscured by participant headers | The existing caption-placement routine avoided message routes and labels but excluded opaque participant boxes. | Include participant boxes and use the same computed caption rectangle for rendering and validation. Reject a caption that remains obstructed after the bounded placement attempts or leaves the canvas above. |
| Fresh native caption labels the preceding band | Upward collision avoidance could move a segment caption across the preceding band boundary, and validation did not catch the association error. | Treat preceding bands as occupied space. Prefer bounded clear positions above the current band, then inside it; use the same geometry for validation and rendering. |
| Theme control and part of the style control disappear at 390px | The relative mobile toolbar retained desktop top/right offsets and did not wrap its children. Negative-left overflow is not reflected in document scroll width. | Reset those offsets and allow toolbar wrapping below the existing 720px breakpoint. Assert every visible top-level toolbar button's bounds explicitly. |

The fixes preserve the original diagram facts, viewBox, participant/message
coordinates, font attributes, quality profile, and validation thresholds.
They add no clipping rule or desktop diagram scroller. The first caption moves into
available space above the participant row; later captions remain associated
with their own bands. Caption text remains unchanged.

## Verification

From the release checkout, the reproduction and final checks used:

```sh
node powers/pkstack/skills/archify/upstream/bin/archify.mjs doctor
node powers/pkstack/skills/archify/upstream/bin/archify.mjs deliver sequence \
  /private/tmp/pkstack-archify-release.VuUtol/account-request-path.sequence.json \
  /private/tmp/pkstack-archify-release.VuUtol/before.html --quality showcase --json
node powers/pkstack/skills/archify/upstream/bin/archify.mjs visual-check \
  /private/tmp/pkstack-archify-release.VuUtol/before.html --json
node powers/pkstack/skills/archify/upstream/bin/archify.mjs visual-check \
  /private/tmp/pkstack-archify-release.VuUtol/final-browser-v2/account.html --json
```

Doctor passed with Node.js 26.7.0. The final delivered artifact passes all nine
showcase checks with no warnings; the final CLI visual check exits 0.
The browser regression uses a fresh headless Chrome profile and local files.
The pytest run invoked the browser harness in its temporary directory;
its evidence was copied unchanged into `final-browser-v2/`. The final repeat
reproduced the identical delivered HTML hash.
It independently measures both themes at every desktop size, rather than
assuming a light-theme measurement applies to dark mode.

| Desktop viewport | Original document height | Repaired document height, both themes |
| --- | --- | --- |
| 1440 x 900 | 1291 | 900 |
| 1600 x 1000 | 1425 | 1000 |
| 1920 x 1080 | 1425 | 1080 |
| 2048 x 1320 | 1443 | 1320 |

All have zero horizontal overflow, unobstructed navigation chrome, and a
minimum measured node/context text size of 7px against the unchanged 6px
desktop threshold. Narrow containment passes at 390 x 844 and 720 x 900 in
both themes, including all top-level toolbar controls. A valid wide variant
also passes at 1440 x 900 in both themes with the existing wide-reader floor.

The regression clicks the zoom controls, dispatches a real pointer drag,
checks camera movement, and resets to scale 1 with zero offsets. It then uses
the actual export menu to download SVG, PNG, JPEG, WebP, Share Card, and WebM.
Each download's recorded byte count matches the completed file. The canonical
SVG is byte-identical before and after zoom/pan and retains its 760 x 620
viewBox, theme rules, and unimplemented-delivery caveat. PNG dimensions remain
3040 x 2480; the Share Card is 1200 x 630. Delivered HTML and input JSON hashes
are unchanged by all browser interactions.

Perceptual inspection covered the original clipped screenshot, final light and
dark 1440 x 900 and 2048 x 1320 compositions, both 390px captures, and the full
PNG and Share Card exports. The complete worker boundary and legend are visible;
the formerly obscured caption and mobile toolbar controls are visible. The
large desktop composition uses the available height. Other measured sizes have
automated evidence, without a claim of individual perceptual inspection.

All 14 bundled JSON examples also delivered successfully with nine showcase
checks and zero warnings. After the short-band guard, both sequence examples
were delivered again and matched the previously checked HTML byte-for-byte. That check verifies schema/render compatibility; it
does not claim a full browser visual review of all example diagrams.

From `powers/pkstack`, the following passed:

```sh
env PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  /opt/homebrew/bin/uv run --offline pytest tests/test_archify_reader_layout.py -q
env PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  /opt/homebrew/bin/uv run --offline ruff check tests/test_archify_reader_layout.py
env PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  /opt/homebrew/bin/uv run --offline ruff format --check tests/test_archify_reader_layout.py
```

Result: **4 passed in 17.77s**; Ruff lint and formatting passed. Node syntax
checks for the changed renderer and new browser harness, and `git diff --check`,
also passed. A renderer test rejects a deliberately crowded caption
with the new actionable layout diagnostic. Another renders the exact frozen
native specification and asserts its second caption stays inside its own band
and clear of the preceding band, including a short-band variant that would
otherwise allow upward placement to jump entirely over that band. The browser
test skips explicitly when Chrome is unavailable; optional runtime omissions
are reported as skips.

## Fresh native Kiro smoke and unchanged-input repair

A new disposable consumer at `/private/tmp/pkstack-archify-native.WznDOj` was
installed by the reviewed `setup_pkstack.py --root <consumer> --output json`
path. Setup reported no conflicts. It contains the same three fixture modules
(`api.mjs`, `account.mjs`, `worker.mjs`) and restricts task writes to `artifacts/`.
The native invocation was:

```sh
env PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  /Users/noahsutter/.local/bin/kiro-cli chat --v3 --agent pkstack \
  --model gpt-5.6-luna --effort low
```

The `/archify` request asked for a polished account-request sequence, source
inspection, explicit distinction between implemented enqueue/response code and
implied queue delivery, and doctor, showcase validation, delivery, and visual
checks on the exact HTML. Native skill disclosure loaded the 3,829-character
Archify body. The model read the three fixture modules, schema, and local
example, and used the installed runtime. Two guessed documentation/example
paths returned ENOENT before it recovered to a bundled sequence example.
No permanent trust override or broad tool approval was used.

Authoring corrections came first: the validator rejected an unsupported
self-message; later visual checks rejected the model's oversized composition.
The model repaired its own specification, including reducing the canvas from
820 x 760 to 820 x 520 and adjusting message/activation coordinates. These
are native authoring attempts, not runtime-regression failures. The retained
intermediate overflow receipt in `native-initial/` binds HTML SHA-256
`8d98d5191f1690513ef74b0155c895067c9643ded3ba88b158ae10e10ce64739`.
The task finished with doctor, nine showcase checks, delivery, and automated
visual checks passing. Kiro displayed 0.26 credits and 16m 19s. `/quit` exited
0 and reported session `sess_7454677a-5dbd-42ba-b941-0b918b8195ea`.

The completed native input is frozen byte-for-byte in
`powers/pkstack/tests/fixtures/archify-native-account-request.sequence.json`,
3,160 bytes, SHA-256
`17cc793566e993df0c952f4dd0ef463d973712828c4647d1adbf100ddd4d04c8`.
Its native HTML and passing automated receipt remain in `native-final/`:
HTML SHA-256
`eae39879b3134fd8e4ad693193cc3e04ad7a0f55aa0b0275131ced1057a65ec7`.

Perceptual inspection of that exact output found a separate renderer defect.
The JSON defines consecutive bands `[150,300]` and `[318,450]`. Message/label
avoidance relocated the second caption from its initial `y=296` to `y=274`,
inside the preceding band. This was not a coordinate change in the authored
input and was not detected by the previous automated checks. The minimal
renderer repair treats preceding bands as occupied and tries bounded clear
positions inside the current band when an outside caption cannot fit.
Replaying the **unchanged** native JSON places that caption at `y=324`, inside
its correct band, and leaves all message and participant coordinates intact.

The final runtime replay is `native-repaired.html`, 708,808 bytes, SHA-256
`f88a52624b1f63714b5f8e520fb38d7b6054affcdd5f856a04c2082073051faf`.
Delivery again passes 9/9 showcase checks, with zero errors or warnings;
`native-repaired.visual-check.json` binds the same hash and passes the original
browser criteria. Manual inspection covers final 1440 x 900 light and
2048 x 1320 dark captures: both captions are legible, correctly associated,
and clear of messages and participants. No new native authoring was performed
after this runtime patch; this final evidence is an unchanged-input replay of
the native-authored artifact, with an explicit regression for its caption bounds.

## Evidence and integration

Final evidence is in `final-browser-v2/browser-evidence.json`, with 15 observations,
geometry assertions, camera states, and export paths/hashes. The CLI receipt is
`final-browser-v2/account.visual-check.json`. Screenshots use
`final-browser-v2/account-<width>x<height>-<theme>.png`; narrow captures and exports
are alongside them. Original receipts/screenshots remain under `before.*`.
The final HTML SHA-256 is
`477a57e580badc80413fc7700fabeb855a889d92e43a4bccacfec7b74acaf750`.

The unchanged upstream pin remains
`06dd052602dd9a369e4d034e24faef0917b5a60c`, subtree
`cff24583cbdc3b7c7313580f3fa0636ade2e5279`. The bundle manifest identifies the two
runtime files as adapted; their original upstream identities remain unchanged
in the 192-file source-parity inventory. Provenance records both upstream and
local identities, exact patch diffs, and patch-specific rationale. The package
documentation and third-party notice describe these local maintenance patches.

| Changed skill-relative file | Bytes | SHA-256 |
| --- | --- | --- |
| `SKILL.md` | 4011 | `ca5934e1a8ca02f1370f76f020bc1a5b71e543ea5eea753028ec8c51482162b6` |
| `upstream/assets/template.html` | 678727 | `c22d8c5e4bf2182f42bce68a87ac1f1f19421df64966988cbcf5140552b5697a` |
| `upstream/renderers/sequence/render-sequence.mjs` | 22641 | `c7bf2a7b39ec22a838f160f003391768d9539be848fe49031935f1f0bd6f3c55` |

The new provenance regression reconstructs both declared 192-file Git trees,
verifies every unpatched runtime blob, reverse-applies each reviewed patch in
a temporary directory, and checks its original SHA-1, SHA-256, size, and mode.
It also rejects replacement of the upstream inventory with patched bytes,
unrecorded adaptations, and tampered local hashes. All four provenance tests
pass. Ruff and `ty check` pass for both new Python modules. Generated consumer
assets still require the coordinator's normal regeneration and release gates.
The new pytest modules are discovered by the existing Power test suite;
Chrome-enabled CI can run the complete browser regression without npm packages.

Narrow layouts retain upstream's containment-only contract: at 390px the diagram
text is small (minimum projected context text about 3.06px), so this is not a
mobile readability or full mobile-product acceptance claim. Oversized authored
diagrams may still require composition repair; the runtime continues to report
overflow instead of hiding it. No other-browser campaign or full
release-readiness verdict is supplied by this lane.
