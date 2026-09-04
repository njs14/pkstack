# Verified-goal validation fixture

This fixture intentionally starts red. `normalize_account_id` must normalize
spaces and hyphens into exactly twelve decimal digits and raise `ValueError`
otherwise.

The real Kiro CLI v3 campaign copies this directory to an isolated temporary
Git repository, bootstraps PK-Stack, starts a goal against the unittest command,
and invokes:

```text
/verified-goal Repair account identifier normalization. First record the current failing verifier before editing, then repair and rerun until passed.
```

The fixture in this repository stays broken on purpose so the campaign is
repeatable. The repaired temporary copy and Kiro transcript are validation
evidence, not product source.
