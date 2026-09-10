# Explore logic and states

A self-contained HTML file is useful when a human needs to press buttons and observe the model.
State the question visibly. Keep the model separate from presentation: a reducer, state machine,
or small operation interface selected for the domain. The page calls the model, not the reverse.

Show the full relevant state as readable domain fields after each action. Provide free-play
controls and guided walkthroughs reset to a known initial state. Include the normal path, a
consequential edge case, and an illegal or interrupted transition. Explain changed fields and
why an action is unavailable. Use the domain's language, keyboard-accessible controls, and local
assets. Do not add dependencies merely for presentation.

Observe each scenario and record which question it answered. A plausible diagram or screenshot
does not prove state transitions. The model can inform real implementation; it still needs
production tests and integration review before release. Preserve conclusions and clean up through
[the shared prototype method](README.md).
