"""Private launcher for the verified Kiro 2.21.1 / KAS 0.58.7 combination.

Executed as a standalone script, with no project imports. Kiro's CLI retains
native authentication; only its embedded server receives the isolated home.
This uses a version-specific Kiro runtime seam, not a public stable ACP option.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

KAS_VERSION = "0.58.7"


def resolve_node(arguments: list[str]) -> Path:
    servers = [Path(arg) for arg in arguments if arg.endswith("/acp-server.js")]
    if len(servers) != 1 or not servers[0].is_absolute():
        raise ValueError("Kiro did not supply its expected embedded ACP server")
    server = servers[0].resolve(strict=True)
    package = server.parent.parent.parent / "package.json"
    metadata = json.loads(package.read_text(encoding="utf-8"))
    if metadata.get("name") != "@kiro/agent" or metadata.get("version") != KAS_VERSION:
        raise ValueError("unverified Kiro embedded server version; isolation must be revalidated")
    cache = next((path for path in server.parents if path.name == "kas"), None)
    if cache is None:
        raise ValueError("Kiro embedded runtime cache layout is not recognized")
    node = (cache.parent / "node").resolve(strict=True)
    if not node.is_file() or not os.access(node, os.X_OK):
        raise ValueError("Kiro bundled Node runtime is unavailable")
    if set(arg for arg in arguments if arg.startswith("--")) != {
        "--experimental-wasm-modules",
        "--transport=stdio",
        "--auth=acp-callback",
    }:
        raise ValueError("Kiro embedded launch options changed; isolation must be revalidated")
    return node


def main() -> None:
    try:
        home = Path(sys.argv[1]).resolve(strict=True)
        arguments = sys.argv[2:]
        node = resolve_node(arguments)
        environment = dict(os.environ)
        environment.update(
            HOME=str(home),
            KIRO_HOME=str(home / ".kiro"),
            KIRO_CONTENT_COLLECTION_ENABLED="false",
        )
        # The isolated worker must not import personal remote sessions or cloud
        # configuration. Authentication still belongs to the parent native CLI.
        for key in ("CLOUD_CONFIG_ENDPOINT", "KIRO_REMOTE_SESSIONS_ENDPOINT"):
            environment.pop(key, None)
        os.execve(node, [str(node), *arguments, f"--home-dir={home}"], environment)
    except (OSError, ValueError, IndexError) as exc:
        print(f"PKStack knowledge isolation unavailable: {exc}", file=sys.stderr)
        raise SystemExit(78) from exc


if __name__ == "__main__":
    main()
