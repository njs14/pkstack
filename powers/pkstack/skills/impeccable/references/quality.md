# Quality checks for UI edits

Use these checks on the actual result, with the project's accessibility target and supported
platforms. The brief controls visual direction; aesthetic defaults never override function.

- Verify text contrast in actual states and themes: ordinarily at least 4.5:1 for normal text
  and 3:1 for large text. Check control boundaries and visible focus separately. These checks
  alone do not establish complete WCAG conformance.
- Use semantic controls, useful accessible names, logical headings and tab order, visible
  focus, keyboard operation, and appropriate touch targets. Do not communicate state by color
  alone. Check labels, errors, and screen-reader announcements on the relevant path.
- Test real short and long content at narrow, intermediate, and wide widths, with text zoom
  and supported themes. Fix unintended overflow, unreadable measure, clipped controls, and
  layout shifts. A screenshot with placeholder content is insufficient.
- Keep typography roles and spacing relationships coherent. Reuse tokens and native controls;
  use semantic elevation and layering rather than arbitrary z-index escalation.
- Give controls the loading, disabled, error, success, empty, hover, and focus states their
  behavior needs. Verify that the UI's state agrees with the underlying operation.
- Respect reduced-motion preferences with useful state feedback. Content stays available
  when animation fails or is disabled. Measure expensive effects; do not add permanent
  will-change hints, heavy filters, or motion to disguise a slow task.
- Keep imagery proportions and loading stable, with appropriate alternative text. Preserve
  truthful copy, permissions, and product behavior. No fabricated metrics or testimonials.

Avoid choosing identical icon-card grids, nested cards, gradient text, decorative glass,
oversized metrics, arbitrary numbered sections, or repeated entrance animations by habit.
Use a motif only when the brief and content justify it. Existing brand choices are evidence,
not defects merely because they appear on an anti-pattern list.

Batch visual inspection and repair as described by the skill entrypoint. Record missing
browser/device evidence and remaining defects. Passing lint or a visual scan does not prove
interaction behavior, accessibility, or release readiness.
