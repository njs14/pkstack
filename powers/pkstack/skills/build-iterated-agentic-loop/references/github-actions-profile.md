# PKStack GitHub Actions profile

- Pin third-party actions to full commit SHAs and use a fixed Ubuntu image.
- Set workflow permissions to `{}` and grant minimal job permissions.
- Keep model credentials in the actuator job only; use only `KIRO_API_KEY`.
- Snapshot controller code from the trusted base before inspecting an untrusted candidate.
- Never execute candidate-provided scripts in a privileged publisher.
- Package candidate data, validate it against immutable policy, and publish through GitHub APIs.
- Bind detector, controller, tests, peer review, mergeability, and publication to exact SHAs.
- Bound attempts, bytes, files, lines, network destinations, and open candidates.
- Keep scheduled and manual runs subject to the same proof and scope gates.
- Validate with Actionlint, ShellCheck, repository policy tests, and mutation/failure fixtures.
