---
name: model-council
description: Obtain independent reviews of the same change under one rubric, synthesize consensus and disagreement, and classify advice without auto-applying it. Use for high-risk decisions or when the user explicitly requests a model council, Fable review, or Grok review.
---

# Convene a review council

Treat the request text that activated this skill as the review request.

## Prepare one evidence packet

Give every reviewer the same intent, relevant diff or artifact, constraints, verification evidence, and 3-6 item rubric. Do not assign theatrical personas or vary the facts to manufacture disagreement.

Native Kiro sub-agents can provide independent review passes, but that is a Kiro review panel, not proof of model diversity. Do not label reviews as different models unless the returned execution metadata identifies different models.

## Optional external reviewers

Fable, Grok, or another external reviewer is optional and advisory. It is not a Kiro-native model runtime. Invoke it only when the user requested it and the required local command or integration is already available.

Honor any reviewer hierarchy in the user's rubric. A designated peer advisor
participates at candidate checkpoints and owns the final advisory acceptance;
a designated sweeper runs late, searches for residual issues, and cannot accept
the candidate. Send every supported material sweeper finding back through the
peer after remediation instead of treating the council as a vote.

- Keep external access read-only by default.
- Do not install tools, sign in, transfer credentials, or reuse Kiro session state.
- Send the minimum necessary repository content and exclude secrets or personal data.
- Preserve the reviewer identity, exact input rubric, output, and any execution limitation.

If an external reviewer is unavailable, say so and continue with the available evidence; never fabricate a council member.

## Synthesize without voting

The lead agent compares claims to the code and executable evidence, then classifies each material finding:

- `Act on` - supported and should be fixed before acceptance;
- `Consider` - credible tradeoff that needs a decision;
- `Noted` - useful context with no current action;
- `Dismissed` - unsupported, out of scope, or contradicted by evidence.

Call out consensus and disagreements separately. Never auto-apply council advice. Turn accepted material findings into explicit fix tasks or acceptance criteria, implement them through the primary workflow, and re-run the executable verifier. A council cannot override a failing verifier or create a pass by consensus.
