# Feature map

This directory is the narrow **PROVE** interface. Each feature file describes
one user-observable behavior and binds it to one explicitly reviewed executable
verification command. Broader architecture, decisions, concepts, and
operations belong elsewhere in `Wiki/` (the **KNOW** interface).

Create a contract with:

```bash
.pstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve account status." \
  --expected-path "Runtime -> gateway -> account service -> response" \
  --command "uv run pytest tests/test_account_lookup.py" \
  --ready
```

Generated contracts default to `draft: true`. With `--ready`, projectctl runs
the command first and writes a ready contract only when that proof passes.
