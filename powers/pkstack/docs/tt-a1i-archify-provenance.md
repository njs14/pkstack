# tt-a1i/archify provenance

PKStack retains the reviewed upstream source identity separately from its local
runtime bytes. The Kiro wrapper is adapted, and the bundled runtime is
byte-exact upstream except for the two documented local layout patches below.
Tests, rendered demos, build/gallery tooling, and the network update checker
remain excluded from the bundle.

<!-- pk-stack-upstream-genesis: {"commit":"06dd052602dd9a369e4d034e24faef0917b5a60c","path":"archify","repository":"tt-a1i/archify","source_id":"tt-a1i-archify","subtree_sha":"cff24583cbdc3b7c7313580f3fa0636ade2e5279"} -->

## Reviewed upstream corrections

The reviewed upstream transition is from
`06dd052602dd9a369e4d034e24faef0917b5a60c` (subtree
`cff24583cbdc3b7c7313580f3fa0636ade2e5279`) to
`d8e4daf2610d512821365f41b139d874b29efe81` (subtree
`a7b9e1634b66a8e13d531cca4d18e8123c21f06a`). Its seven-path inventory digest is
`0d2a2cc66161261b4115b0f36a08cf8d0ec95cd700e84b2dcb03eb1997688871`.
The captured exact-blob patches were reviewed before application, and applying
them to verified prior bytes reconstructed the three shipped new Git blobs.

- `bin/archify.mjs` now rejects unknown render options and excess positional
  arguments before writing output.
- `bin/preview.mjs` closes a failed filesystem watcher once and keeps the
  polling fallback active after an asynchronous watcher error.
- The sequence renderer rejects captions wider than their own segment frame,
  with a suggested minimum canvas width. Exact-fit captions remain valid.

The four changed upstream test files remain excluded: `test/cli.test.mjs`,
`test/community-proof-intake.test.mjs`, `test/layout-rules.test.mjs`, and
`test/preview.test.mjs`. Focused PKStack regressions reproduce the shipped
failures and validate their corrections. Existing local layout patches remain
recorded below as diffs against the new reviewed upstream bytes. The genesis
marker and the inventory's prior pinned identities are preserved.

## PKStack 0.3.0 local layout patches

The inventory retains the prior reviewed source in its pinned column and the
new reviewed source in its current column. Upstream identities remain separate
from the locally adapted runtime bytes.
Disposition A means incorporated: for these two files it includes the explicitly
reviewed adaptation recorded here. The bundle manifest marks those files
`adapted-runtime`; all other runtime files remain `byte-exact-runtime`.

- The shared viewer adapts compact diagrams to the desktop height budget while
  preserving the existing wide-reader floor. Its narrow toolbar wraps controls
  and resets desktop offsets so buttons remain inside the viewport.
- Sequence caption placement avoids opaque participant headers and preceding
  bands. It uses clear positions above or inside its own band and rejects
  exhausted placements, preserving the same geometry for rendering and validation.

The [release repair evidence](../../../reviews/release-030-archify.md) records
unchanged-input reproduction, browser containment and visual inspection,
zoom/pan/reset, and canonical exports. A source update must review whether these
patches remain needed; it must not rewrite upstream identities to match adapted
bytes. The runtime already includes the patches; the diff below is provenance
data and is not an installation step.

The structured record binds both original and local bytes. Regression tests
reverse the recorded patch only in a disposable directory to recover and hash
the original files, and reconstruct the full upstream Git subtree from the
source inventory. No network access or historical checkout is required.

```json
{
  "schema_version": 1,
  "source_id": "tt-a1i-archify",
  "upstream": {
    "commit": "d8e4daf2610d512821365f41b139d874b29efe81",
    "subtree_sha": "a7b9e1634b66a8e13d531cca4d18e8123c21f06a"
  },
  "reviewed_on": "2026-09-05",
  "patches": [
    {
      "path": "assets/template.html",
      "reason": "Apply desktop viewport adaptation to compact diagrams without desktop-width inflation, and contain narrow toolbar controls by resetting desktop offsets and allowing wrapping.",
      "upstream": {
        "mode": "100644",
        "object_sha": "28c151c19384e86b1678a088183b914d7a5f5167",
        "size": 678398,
        "sha256": "35b2210b120c56a6c58d953ffe0cf815c2e67d0a5ff3e8b9518c45b737dd3fc3"
      },
      "local": {
        "mode": "100644",
        "object_sha": "3e6e223e60ab251358469a07f0660cd98bef8b9f",
        "size": 678727,
        "sha256": "c22d8c5e4bf2182f42bce68a87ac1f1f19421df64966988cbcf5140552b5697a"
      }
    },
    {
      "path": "renderers/sequence/render-sequence.mjs",
      "reason": "Keep segment captions clear of opaque participant headers, messages, and preceding bands; prefer bounded clear positions above or inside their own band and reject exhausted placements.",
      "upstream": {
        "mode": "100644",
        "object_sha": "1cfc032a12ed72a0d2b0bb09797d337c039218b3",
        "size": 21734,
        "sha256": "230c0fb79775badb4beb6fd74f45ed1ffbb70e932c3641a24bedcc61f912bddf"
      },
      "local": {
        "mode": "100644",
        "object_sha": "681227d9917698122491d455bce270ec72296e98",
        "size": 23132,
        "sha256": "340031217aa8cceca922ddbc243f5478555e13c04c89c240bd1affa1045721f4"
      }
    }
  ]
}
```

## Reviewed patch

```diff
diff --git a/assets/template.html b/assets/template.html
index 28c151c..3e6e223 100644
--- a/assets/template.html
+++ b/assets/template.html
@@ -601,7 +601,7 @@
       color: var(--frontend-stroke);
     }

-    /* The reader owns only the outer scale. Wide diagrams keep one authored
+    /* The reader owns only the outer scale. Diagrams keep one authored
        SVG/viewBox while the runtime chooses a desktop width from the actual
        vertical budget. This avoids device-specific files and breakpoint
        jumps between a laptop and a tall monitor. */
@@ -3581,6 +3581,9 @@
       }
       .toolbar {
         position: relative;
+        top: auto;
+        right: auto;
+        flex-wrap: wrap;
         justify-content: flex-end;
         width: max-content;
         max-width: 100%;
@@ -10775,9 +10778,9 @@
     /* ============================================================
        Adaptive Reader Shell — one diagram across laptop and monitor.
        The canonical SVG and viewBox never change. On ordinary desktop pages,
-       wide diagrams receive only enough outer width to use the available
+       diagrams receive only enough outer width to use the available
        height without pushing summary cards below the viewport. Mobile,
-       embed, presentation, print, and non-wide diagrams retain their own
+       embed, presentation, and print retain their own
        established layout contracts.
        ============================================================ */
     Archify.waitForStableLayout = function (options) {
@@ -10859,7 +10862,7 @@
       }
       function eligible() {
         return Boolean(
-          shell && diagram && svg && ratio >= WIDE_RATIO &&
+          shell && diagram && svg && ratio > 0 &&
           window.innerWidth >= MIN_DESKTOP_WIDTH &&
           html.getAttribute('data-embed') !== 'true' &&
           html.getAttribute('data-present') !== 'true' &&
@@ -10919,7 +10922,12 @@
         }
         var chrome = chromeMetrics();
         var viewportCap = Math.max(0, window.innerWidth - chrome.bodyX);
-        var minWidth = Math.min(MIN_READER_WIDTH, viewportCap);
+        // Compact diagrams need no desktop-width inflation: preserve at least
+        // their authored scale, while retaining the existing wide-reader floor.
+        var readerFloor = ratio >= WIDE_RATIO
+          ? MIN_READER_WIDTH
+          : Math.min(MIN_READER_WIDTH, viewBox.width + chrome.diagramX);
+        var minWidth = Math.min(readerFloor, viewportCap);
         var maxWidth = Math.min(MAX_READER_WIDTH, viewportCap);
         var fixedHeight = chrome.bodyY + chrome.diagramY + SAFE_BOTTOM_GAP +
           outerHeight(header) + outerHeight(guided) + outerHeight(cards);
diff --git a/renderers/sequence/render-sequence.mjs b/renderers/sequence/render-sequence.mjs
index 1cfc032..681227d 100644
--- a/renderers/sequence/render-sequence.mjs
+++ b/renderers/sequence/render-sequence.mjs
@@ -113,17 +113,40 @@
   };
 }

+function segmentLabelObstacles(segment) {
+  return [
+    ...participants.values(),
+    ...asArray(sequence.segments)
+      .filter((other) => other !== segment && other.to <= segment.from)
+      .map((other) => ({ x: 48, y: other.from, width: viewBox[0] - 96, height: other.to - other.from })),
+    ...asArray(sequence.messages)
+      .flatMap((message) => [messageLabelBox(message), messageRouteBox(message)])
+      .filter(Boolean),
+  ];
+}
+
+function segmentLabelMinimumY(segment) {
+  return Math.max(0, ...asArray(sequence.segments)
+    .filter((other) => other !== segment && other.to <= segment.from)
+    .map((other) => other.to + 2));
+}
+
 function segmentLabelBox(segment) {
-  const labelW = Math.max(42, textUnits(segment.label) * 5.2 + 14);
-  const occupied = asArray(sequence.messages)
-    .flatMap((message) => [messageLabelBox(message), messageRouteBox(message)])
-    .filter(Boolean);
-  const label = { x: 56, y: segment.from - 22, width: labelW, height: 18 };
-  for (let attempt = 0; attempt < 4; attempt += 1) {
-    if (!occupied.some((rect) => rectsOverlap(label, rect, 2))) break;
-    label.y -= 22;
-  }
-  return label;
+  const occupied = segmentLabelObstacles(segment);
+  const label = {
+    x: 56,
+    y: segment.from - 22,
+    width: Math.max(42, textUnits(segment.label) * 5.2 + 14),
+    height: 18,
+  };
+  // A caption must not escape into an earlier band while avoiding a message.
+  // Prefer the existing positions above it, then bounded positions inside its
+  // own band; the validator rejects a composition with no clear position.
+  const positions = [0, 1, 2, 3, 4].map((attempt) => ({ ...label, y: label.y - attempt * 22 }));
+  positions.push(...[0, 1, 2, 3]
+    .map((attempt) => ({ ...label, y: segment.from + 6 + attempt * 22 }))
+    .filter((candidate) => candidate.y + candidate.height <= segment.to - 2));
+  return positions.find((candidate) => candidate.y >= segmentLabelMinimumY(segment) && !occupied.some((rect) => rectsOverlap(candidate, rect, 2))) || label;
 }

 const compositionFrames = asArray(sequence.segments).map((segment, index) => ({
@@ -288,6 +311,10 @@
     if (labelBox.x + labelBox.width > viewBox[0] - 48) {
       const requiredWidth = Math.ceil(labelBox.x + labelBox.width + 48);
       problems.push(`Segment "${segment.label}" label (~${Math.round(labelBox.width)}px) exceeds the segment frame's available width (${availableWidth}px) — shorten the label or increase meta.viewBox[0] to at least ${requiredWidth}.`);
+    }
+    const label = segmentLabelBox(segment);
+    if (label.y < segmentLabelMinimumY(segment) || segmentLabelObstacles(segment).some((rect) => rectsOverlap(label, rect, 2))) {
+      problems.push(`Segment label "${segment.label}" has no clear position above or within its band — move the segment or adjacent messages to leave label space.`);
     }
   }

```

<!-- pk-stack-upstream-review: {"inventory_sha256":"0d2a2cc66161261b4115b0f36a08cf8d0ec95cd700e84b2dcb03eb1997688871","new":{"commit":"d8e4daf2610d512821365f41b139d874b29efe81","subtree_sha":"a7b9e1634b66a8e13d531cca4d18e8123c21f06a"},"path":"archify","prior":{"commit":"06dd052602dd9a369e4d034e24faef0917b5a60c","subtree_sha":"cff24583cbdc3b7c7313580f3fa0636ade2e5279"},"repository":"tt-a1i/archify","source_id":"tt-a1i-archify"} -->
