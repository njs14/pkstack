# Codex pre-Fable round-4 audit

- Date: 2026-09-02
- Audited base: `1e9352b944e242a4249f943b642f7db1ed03aac3`
- Role: independent read-only precheck; not a Fable verdict

## Material findings and disposition

### PREFLIGHT-010 — HIGH — Combined release lacked an installable Power package

The base snapshot described PK-Stack as the product and the Floci application as its fixture, but
contained neither `plugin.json` nor `POWER.md`. Its `.pstack/projectctl/` tree was correctly marked
as generated cache and could not honestly serve as setup authority.

Acceptance required one canonical package root with a valid Agent Plugins manifest, source,
skills, templates, and lock; a fresh Power-local setup plus idempotent rerun and doctor; and
byte-for-byte parity between canonical assets and generated fixture output. The original accepted
source checkout had to remain unchanged.

Disposition: closed. The accepted source snapshot was imported without its Git metadata at
`powers/pk-stack/`, patched only for PREFLIGHT-011, and used by its own setup shim to regenerate
the root fixture. `tests/test_power_distribution.py` pins the package manifest, fresh bootstrap,
idempotence, doctor, and complete relevant asset parity. The external original checkout remained
clean at `191997501c41ae078b6548b9d6c898aadf2907ae`.

### PREFLIGHT-011 — MEDIUM — Draft contracts could execute or become goal evidence

The base controller accepted a draft feature whenever it already contained a command. Both
`projectctl feature verify` and `goal start --feature` bypassed the documented publication boundary.

Acceptance required both routes to fail nonzero before command execution or goal-state creation,
while a published ready contract remained executable. The rule had to be shared by source and
generated code, with canonical-source and fixture regressions.

Disposition: closed. `find_verifiable_feature` is the single ready-and-command resolver used by
both routes. The canonical suite proves a draft command is not run and no goal state appears;
ready feature verification and goal evidence continue to pass. Bootstrap regenerated the three
changed controller modules and updated the ownership receipt.

## Gate results before immutable Fable review

```text
canonical Power: 509 passed in 37.58s
combined lab:     290 passed in 9.26s
canonical Ruff:  passed
canonical format: 27 files already formatted
canonical ty:    passed
canonical lock:  20 packages resolved
combined Ruff:   passed
combined lock:   15 packages resolved
manifest schema: official Agent Plugins 1.0.0 validation passed
Kiro agents:     all four canonical profiles accepted by kiro-cli 2.21.0
fixture doctor:  39 pass, 0 fail, 1 optional okn warning
lab doctor:      passed
```
