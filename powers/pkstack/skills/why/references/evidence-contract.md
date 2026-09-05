# Why evidence contract

## Investigator contract

An investigator owns one evidence category. It receives the question, target
files and symbols, relevant commits and identifiers, and a bounded category
scope. It reads but does not modify repositories or external systems.

The shipped read-only profiles do not load project MCP configuration. The
primary session gathers any user-authorized external evidence with tools that
are actually available, redacts it to the needed scope, and passes the bounded
packet to the investigator. The investigator must not claim a direct connector
or MCP query. Missing access is an `unavailable` coverage result.

Return:

1. **What was searched:** exact queries, time ranges, paths, and items opened.
2. **Direct evidence:** what the source states, who or what stated it, date when
   available, precise citation, and relevance.
3. **Indirect evidence:** observation, source, careful inference, and credible
   alternative readings.
4. **Contradictions:** both claims and both citations.
5. **Gaps and empty results:** the exact unsuccessful search and its scope.
6. **Cross-source leads:** identifiers for the investigator that owns the other
   category; do not duplicate its work.

Do not infer motivation from mechanics. A changed constant proves a change,
not why the value was selected.

## Coverage contract

The final ledger includes project history and code, issues, long-form docs,
project chat, infrastructure observability, error tracking, and product
analytics. Apply incident and postmortem evidence as a cross-cutting lens over
the relevant categories. For each category, state the tool or source, query and
scope, status, result, and remaining gap.

Unavailable sources remain visible. An empty result is meaningful only after a
recorded search. Absence of a ticket does not prove that a decision was never
discussed.

## Confidence contract

- Direct and Supported claims carry adjacent verifiable citations.
- Inferred claims show the evidence chain and use calibrated language.
- Speculative claims name the evidence that would confirm or reject them.
- Unknown claims state where the search stopped.
- Contradictory sources remain side by side.

Before returning, check every causal word such as “because,” “the reason,” or
“was designed to.” Keep it only when direct evidence supports it. Always name
at least the most important evidence gap; an apparently gap-free historical
answer deserves another review.
