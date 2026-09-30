#!/usr/bin/env python3
"""Print the fileSha256 a registry entry pins, or the artifact it names.

Used by the release workflow to prove the bundle it just built is the bundle
the registry entry will serve. Kept as a file rather than an inline one-liner
in YAML so it can be read and tested like anything else.

    python3 scripts/pinned_hash.py mcp/server.json
    python3 scripts/pinned_hash.py mcp/server.json --url
"""
from __future__ import annotations

import json
import pathlib
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    path = pathlib.Path(sys.argv[1])
    data = json.loads(path.read_text())
    packages = data.get("packages") or []
    if not packages:
        print(f"{path}: no packages[] - nothing for the registry to serve",
              file=sys.stderr)
        return 1
    pkg = packages[0]
    if "--url" in sys.argv:
        print(str(pkg.get("identifier", "")))
    else:
        print(str(pkg.get("fileSha256", "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
