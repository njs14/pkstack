---
name: principle-attack-the-premise
description: Question the shared assumption when two or more attempted fixes fail the same check; measure which actors hold the imbalance before proposing another fix.
---

# Question the shared premise

Treat the request text that activated this skill as the repeated failure to investigate.

Apply [attack the premise](../pkstack-principles/references/catalog.md#attack-the-premise).
Write down the assumption shared by the failed fixes. Before another attempt, use a rerunnable
measurement to count the imbalance by actor, such as a worker, process, tenant, or partition.

If the same actors repeatedly hold the imbalance, trace what assigns them that role. Compare
removing that asymmetry with adding a return path, shared pool, handoff, or periodic rebalance.
Choose the smallest change supported by the measurements. An even distribution is evidence
against that explanation, so investigate another cause rather than forcing this one.

Reuse [build the lever](../principle-build-the-lever/SKILL.md) for the measurement and
[fix root causes](../principle-fix-root-causes/SKILL.md) for the causal trace. Report the premise,
the distribution, the changed decision, and the original check's result. Keep redesign and
side effects within the user's authorized scope.
