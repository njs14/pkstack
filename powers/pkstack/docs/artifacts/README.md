# Diagram sources and previews

| Diagram | Source | Interactive artifact | PNG preview |
| --- | --- | --- | --- |
| Components and ownership | [JSON](pkstack-architecture.json) | [HTML](pkstack-architecture.html) | [PNG](pkstack-architecture.png) |
| Native planning and verification | [JSON](pkstack-task-workflow.json) | [HTML](pkstack-task-workflow.html) | [PNG](pkstack-task-workflow.png) |
| Upstream update and review | [JSON](pkstack-updater-workflow.json) | [HTML](pkstack-updater-workflow.html) | [PNG](pkstack-updater-workflow.png) |

These are explanations, not runtime or release evidence. The component source
cites six repository files at `f53f0931ef3a6748242d2dd569fe0cef0ddb2106`.
The updater view also describes this change's bounded skill-review context.

Generated with the locally installed Archify 2.17, using its showcase profile.
The Power's bundled Archify runtime was not upgraded. Each JSON source passed
all nine deterministic checks with zero errors or warnings before delivery.
Each exact HTML artifact passed `visual-check` at 1440×900, 1600×1000,
1920×1080, and 2048×1320. The light and dark endpoint captures were inspected
for readable labels, unclipped nodes, and visible failure paths.

The PNGs contain only the compiled diagram, without viewer controls. They were
extracted statically from each HTML's SVG and rasterized with librsvg 2.62.3 at
1600 pixels wide, using the light theme and Menlo. This does not execute the
HTML's JavaScript or change the authored geometry. All three PNGs were inspected
separately after export. The HTML retains zoom, theme selection, and export.

To regenerate from the repository root, set `ARCHIFY` to a reviewed Archify
2.17 `bin/archify.mjs`, then run:

```sh
node "$ARCHIFY" deliver architecture \
  powers/pkstack/docs/artifacts/pkstack-architecture.json \
  powers/pkstack/docs/artifacts/pkstack-architecture.html \
  --repo-root . --quality showcase --json
node "$ARCHIFY" deliver workflow \
  powers/pkstack/docs/artifacts/pkstack-task-workflow.json \
  powers/pkstack/docs/artifacts/pkstack-task-workflow.html \
  --quality showcase --json
node "$ARCHIFY" deliver workflow \
  powers/pkstack/docs/artifacts/pkstack-updater-workflow.json \
  powers/pkstack/docs/artifacts/pkstack-updater-workflow.html \
  --quality showcase --json
```

Run `node "$ARCHIFY" visual-check <artifact.html> --json` for each output.
Inspect the new captures before exporting a PNG. The viewer's export menu can
produce a diagram-only PNG or SVG; an exported SVG can also be rasterized with
`rsvg-convert --width 1600 --background-color '#f8fafc' --output preview.png diagram.svg`.
A successful render alone does not establish visual quality or tested product
behavior.
