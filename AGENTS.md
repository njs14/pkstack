# PK-Stack lab agreements

- Keep all emulator clients on the explicit endpoints in `src/pk_stack_lab/config.py`.
- The Docker socket is mounted only into the outer Floci Compose service. It must never
  appear in an application task definition, Dockerfile, or task environment.
- `.lab-state/` is disposable, ignored, repository-local runtime state. Do not place
  credentials, image archives, or user data there.
- `labctl down` is the sole destructive lifecycle command. It validates exact run tags
  before deletion; do not replace those checks with prefix scans.
- `Wiki/features/` is the narrow proof contract. Its verifier may only use `./labctl
  verify --output json` after deployment.
