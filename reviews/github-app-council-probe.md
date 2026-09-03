# GitHub App review-council probe result

This private pull request probed whether account-backed Claude, Grok, and Codex GitHub Apps could
provide deterministic exact-candidate review evidence without putting provider API keys in GitHub
Actions. The result was not reliable enough to make those Apps release authorities: Claude
acknowledged the request, while Codex and Grok produced no review evidence during the bounded
observation window.

The shipped design therefore uses Kiro as the only model provider inside GitHub Actions. Kiro runs
an isolated, no-tool Claude Opus 5 reviewer at `xhigh`, bound to the exact candidate patch and
digests. Local subscription-backed Fable 5.1 and Grok 4.6 remain release-council checks. GitHub App
reviews are welcome as advisory signals, but their absence never creates an ambiguous success.

Constraints:

- GitHub Copilot is not used.
- GitHub Actions receives no Anthropic, OpenAI, or xAI model credential.
- Kiro remains the only model provider permitted to receive a pipeline API key.
- The mandatory hosted peer review is performed through Kiro with `KIRO_API_KEY`.
- A missing, stale, failed, or materially adverse mandatory Kiro review fails closed.
- GitHub App comments and reactions are not accepted as merge-gate evidence.
