# tt-a1i/archify provenance

PKStack retains the reviewed upstream source identity separately from its local
runtime bytes. The Kiro wrapper is adapted, and the bundled runtime is
byte-exact upstream except for the two documented local layout patches below.
Tests, rendered demos, build/gallery tooling, and the network update checker
remain excluded from the bundle.

<!-- pk-stack-upstream-genesis: {"commit":"06dd052602dd9a369e4d034e24faef0917b5a60c","path":"archify","repository":"tt-a1i/archify","source_id":"tt-a1i-archify","subtree_sha":"cff24583cbdc3b7c7313580f3fa0636ade2e5279"} -->

## PKStack 0.3.0 local layout patches

The upstream pin and every pinned/current inventory blob identity are unchanged.
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
    "commit": "06dd052602dd9a369e4d034e24faef0917b5a60c",
    "subtree_sha": "cff24583cbdc3b7c7313580f3fa0636ade2e5279"
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
        "object_sha": "02d778175efc949d1cc0c8d4f6dcb0cda500d6bb",
        "size": 21146,
        "sha256": "20954ef721ff725c8693e2d87f993074dda5af0e3f6a9a1d29d7a39362efeed8"
      },
      "local": {
        "mode": "100644",
        "object_sha": "d2d302cfb06662e314e8662d6029ef13c0ed8a13",
        "size": 22641,
        "sha256": "c7bf2a7b39ec22a838f160f003391768d9539be848fe49031935f1f0bd6f3c55"
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
index 02d7781..d2d302c 100644
--- a/renderers/sequence/render-sequence.mjs
+++ b/renderers/sequence/render-sequence.mjs
@@ -113,6 +113,42 @@
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
+function segmentLabelBox(segment) {
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
+}
+
 const compositionFrames = asArray(sequence.segments).map((segment, index) => ({
   id: index,
   label: segment.label,
@@ -269,6 +305,10 @@
     }
     if (segment.from < layout.topY || segment.to > layout.lifelineBottom + 20) {
       problems.push(`Segment "${segment.label}" extends outside the canvas — keep its y range between ${layout.topY} and ${layout.lifelineBottom + 20}.`);
+    }
+    const label = segmentLabelBox(segment);
+    if (label.y < segmentLabelMinimumY(segment) || segmentLabelObstacles(segment).some((rect) => rectsOverlap(label, rect, 2))) {
+      problems.push(`Segment label "${segment.label}" has no clear position above or within its band — move the segment or adjacent messages to leave label space.`);
     }
   }

@@ -322,15 +362,7 @@
 }

 function renderSegmentLabel(segment, index) {
-  const labelW = Math.max(42, textUnits(segment.label) * 5.2 + 14);
-  const occupied = asArray(sequence.messages)
-    .flatMap((message) => [messageLabelBox(message), messageRouteBox(message)])
-    .filter(Boolean);
-  const label = { x: 56, y: segment.from - 22, width: labelW, height: 18 };
-  for (let attempt = 0; attempt < 4; attempt += 1) {
-    if (!occupied.some((rect) => rectsOverlap(label, rect, 2))) break;
-    label.y -= 22;
-  }
+  const label = segmentLabelBox(segment);
   return `        <g data-graph-role="segment-label" data-segment-id="${index}">
           <rect x="${label.x}" y="${label.y}" width="${label.width}" height="${label.height}" rx="3" class="c-mask"/>
           <text x="${label.x + 6}" y="${label.y + 13}" class="t-dim" font-size="9" font-weight="600">${esc(segment.label)}</text>
```
