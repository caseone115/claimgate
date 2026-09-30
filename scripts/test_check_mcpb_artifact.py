#!/usr/bin/env python3
"""Drive the artifact-discovery rule over the shapes that actually went wrong.

The v0.1.1 release run failed here: the checker named "claimgate-0.1.0.mcpb"
and the workflow had just built "claimgate-0.1.1.mcpb", so it reported both
bundles missing and failed the job. Then the obvious fix - a glob on
"claimgate-*" - had a second bug of its own: it matches "claimgate-kit-*" too,
so the engine would have checked the kit's bundle. Both are fixtures here.

Run: python3 scripts/test_check_mcpb_artifact.py
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "checker", HERE / "check_mcpb_artifact.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def build(tmp: pathlib.Path, names: list[str],
          server_relative: str, server_name: str, entry_url: str) -> None:
    (tmp / "dist").mkdir(parents=True, exist_ok=True)
    (tmp / server_relative).mkdir(parents=True, exist_ok=True)
    for n in names:
        (tmp / "dist" / n).write_text(n)
    (tmp / server_relative / "server.json").write_text(
        '{"name": "%s", "packages": [{"identifier": "%s"}]}'
        % (server_name, entry_url))


CASES = []


def case(label: str, expect: str | None, names: list[str], server_name: str,
         entry_url: str) -> None:
    CASES.append((label, expect, names, server_name, entry_url))


case("the version the entry names is the one that is found",
     "claimgate-0.1.1.mcpb", ["claimgate-0.1.1.mcpb"],
     "io.github.caseone115/claimgate",
     "https://github.com/x/y/releases/download/v0.1.1/claimgate-0.1.1.mcpb")
case("a newer version on disk does not displace the pinned one",
     "claimgate-0.1.0.mcpb",
     ["claimgate-0.1.0.mcpb", "claimgate-0.1.1.mcpb"],
     "io.github.caseone115/claimgate",
     "https://github.com/x/y/releases/download/v0.1.0/claimgate-0.1.0.mcpb")
case("the kit's bundle is never returned for the engine's entry",
     "claimgate-kit-0.1.1.mcpb",
     ["claimgate-kit-0.1.1.mcpb", "claimgate-0.1.0.mcpb"],
     "io.github.caseone115/claimgate-kit",
     "https://github.com/x/y/releases/download/v0.1.1/claimgate-kit-0.1.1.mcpb")
case("an entry naming a file that is not on disk is not silently substituted",
     None, ["claimgate-0.1.1.mcpb"],
     "io.github.caseone115/claimgate",
     "https://github.com/x/y/releases/download/v0.9.9/claimgate-0.9.9.mcpb")


def main() -> int:
    print("=== the artifact-discovery rule, over the shapes that went wrong ===")
    passed = failed = 0
    for label, expect, names, sname, url in CASES:
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td)
            src = "mcp" if "kit" not in sname.split("/")[-1] else "mcp-kit"
            build(tmp, names, src, sname, url)
            stem = sname.split("/")[-1]
            checker.ROOT = tmp
            got = checker.find_artifact(stem, tmp / src)
            got_name = got.name if got else None
            good = got_name == expect
            print(f"  {'PASS' if good else 'FAIL'}  {label}")
            if not good:
                print(f"        expected {expect!r}, got {got_name!r}")
                failed += 1
            else:
                passed += 1
    print(f"\n  {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
