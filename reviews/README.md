# Release evidence

This directory holds bounded evidence for the PK-Stack Power and its self-maintenance pipeline. Historical Floci application campaigns moved to the private [`njs14/pk-stack-floci-lab`](https://github.com/njs14/pk-stack-floci-lab) repository.

Documentation and old reports never substitute for a current gate. A release candidate needs:

1. the deterministic Power, controller, workflow, and policy suites;
2. a successful Kiro credential smoke on the exact candidate;
3. an independent Fable 5.1 review at `xhigh` with no material unresolved finding;
4. a Grok 4.6 `xhigh` sweep when the user's official CLI session is authenticated, or an explicit external blocker;
5. a clean private pull request bound to the reviewed commit.

Fable is the peer acceptance reviewer. Grok is a final sweeper. Neither reviewer output is trusted as executable code, and neither may replace deterministic checks.

The most useful retained records are:

- `kiro-model-guidance-evidence.json` for model-inventory shape and versioned guidance;
- `kiro-runtime-canary-campaign.md` and `.json` for the hosted read-only runtime canary;
- `kiro-v3-agent-discovery-probe.json` and `kiro-v3-native-goal-probe.json` for bounded CLI observations;
- `kirocrew-nightly-smoke-campaign.md` and `.json` for the non-gating Nightly command-surface check;
- `pk-stack-maintenance-campaign.md` and `.json` for the maintenance feature contract;
- `okf-integration-evidence.md` and `.json` for the OKF and `okn` boundary.

Each record states the commit or runtime it observed. Evidence from an older commit stays historical.
