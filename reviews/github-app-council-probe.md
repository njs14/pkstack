# GitHub App review-council probe

This branch replaces the hosted candidate's direct Anthropic API/Claude Code Action path with
account-backed GitHub App reviews. The probe is intentionally performed on a private pull request
before the workflow trusts any bot login, check name, or output shape.

Constraints:

- GitHub Copilot is not used.
- GitHub Actions receives no Anthropic, OpenAI, or xAI model credential.
- Kiro remains the only model provider permitted to receive a pipeline API key.
- Claude/Fable, Grok, and Codex review evidence is accepted only from an observed official GitHub
  App identity and must be bound to the current pull-request head.
- Missing, stale, failed, or materially adverse review evidence fails closed.

This record is completed with the observed identities and behavior after the three installed or
authorized Apps are requested on the pull request carrying the implementation.
