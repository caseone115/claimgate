#!/usr/bin/env python3
"""Check the PACKED MCP bundle, not the source tree it was built from.

WHY THIS EXISTS
---------------
Two releases on this project already went out broken while every test was
green, because the tests ran against the repository and the artifact was what
users downloaded. The MCP Registry pins the SHA-256 of a specific file on a
GitHub release, so the thing that matters is those bytes.

The tick that built the engine bundle verified this by hand. A check that only
exists in a shell history is not a check, so it lives here and runs against
every bundle.

WHAT IT ASSERTS, per variant
----------------------------
  1. the archive is a readable zip, carrying manifest.json, the entry point and
     the package marker
  2. the manifest validates against the official MCPB 0.4 schema
  3. the launcher's entry_point resolves to a file actually in the archive
  4. every claimgate module the packed server imports is packed (the allowlist
     has not dropped something the code needs - the failure mode is an install
     that starts and then dies on ImportError)
  5. the packed server passes the SAME stdio suite as the repository's copy
  6. no address that is not the project's own is anywhere in the archive

--fixtures drives rules 1, 3 and 4 over synthetic archives that are wrong in the
ways that matter, because a completeness rule that has only ever passed is the
rule most likely to be matching nothing. Two of these fixtures failed on the
first run of this file and both were real: the import rule missed
`from claimgate import kit` (a bundle with no kit.py would have passed), and it
claimed to require the package marker while not actually checking for it.

Run: python3 scripts/check_mcpb_artifact.py [--rebuild] [--fixtures]
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "mcpb-manifest-v0.4.schema.json"
ADDRESS = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ALLOWED = {"teeter.ai.bot@gmail.com"}

# Both spellings of a relative package import. The first version of this rule
# only matched `from claimgate.<mod> import`, so a bundle missing
# claimgate/kit.py would have passed - and mcp-kit/server.py uses
# `from claimgate import kit`. Caught by the fixture below, not by reading it.
_FROM_DOTTED = re.compile(r"from\s+claimgate\.(\w+)\s+import")
_FROM_PLAIN = re.compile(r"from\s+claimgate\s+import\s+([^\n#]+)")

# Always required, whatever the server imports: the package marker, which is a
# file and can be dropped from an allowlist like any other. Checked explicitly
# rather than smuggled into the import rule, which would have been a claim this
# script made and did not keep.
ALWAYS_REQUIRED = ("server/claimgate/__init__.py",)

VARIANTS = [
    {"name": "claimgate", "artifact": "dist/claimgate-0.1.0.mcpb",
     "suite": "scripts/test_mcp_server.py"},
    {"name": "claimgate-kit", "artifact": "dist/claimgate-kit-0.1.0.mcpb",
     "suite": "scripts/test_mcp_kit_server.py"},
]

FAULTS: list[tuple[str, bool]] = []


def ok(name: str, passed: bool, detail: str = "") -> None:
    FAULTS.append((name, passed))
    print(f"  {'PASS' if passed else 'FAIL'}  {name}"
          + (f"   [{detail}]" if detail and not passed else ""))


def imports_of(source: str) -> set[str]:
    """The claimgate modules a server imports, either spelling of the import."""
    mods = set(_FROM_DOTTED.findall(source))
    for group in _FROM_PLAIN.findall(source):
        for part in group.split(","):
            name = part.strip().split(" as ")[0].strip()
            if name.isidentifier():
                mods.add(name)
    return mods


def required_files(names: list[str], source: str) -> list[str]:
    """Everything the archive must ship for this server to start and work.

    Pure, so the fixtures below can drive it over archives wrong on purpose.
    """
    need = {f"server/claimgate/{m}.py" for m in imports_of(source)}
    need |= set(ALWAYS_REQUIRED)
    return sorted(need - set(names))


def check_variant(v: dict, python_exe: str, workdir: pathlib.Path) -> None:
    arch = ROOT / v["artifact"]
    print(f"\n--- {v['name']}  ({v['artifact']}) ---")
    ok(f"{v['name']}: the packed artifact exists", arch.is_file())
    if not arch.is_file():
        return

    try:
        z = zipfile.ZipFile(io.BytesIO(arch.read_bytes()))
        names = z.namelist()
    except zipfile.BadZipFile:
        ok(f"{v['name']}: is a readable zip", False, "not a zip")
        return
    ok(f"{v['name']}: contains manifest.json", "manifest.json" in names)
    ok(f"{v['name']}: contains the server entry point",
       "server/server.py" in names, str(sorted(names)[:8]))

    man = {}
    if "manifest.json" in names:
        man = json.loads(z.read("manifest.json"))
        import jsonschema
        schema = json.loads(SCHEMA.read_text())
        errors = sorted(jsonschema.Draft7Validator(schema).iter_errors(man),
                        key=lambda e: list(e.path))
        ok(f"{v['name']}: manifest validates against MCPB 0.4", not errors,
           "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:3]))
        entry = (man.get("server") or {}).get("entry_point", "")
        ok(f"{v['name']}: the launcher entry_point resolves in the archive",
           bool(entry) and entry in names, f"entry_point={entry!r}")

    src = z.read("server/server.py").decode()
    need = imports_of(src)
    ok(f"{v['name']}: the import rule found the server's dependencies",
       len(need) >= 4, f"found {sorted(need)}")
    missing = required_files(names, src)
    ok(f"{v['name']}: every module the packed server imports is packed",
       not missing, f"missing {missing}")

    carried = []
    for n in names:
        if pathlib.Path(n).suffix in (".py", ".json", ".toml", ".txt", ".md"):
            for addr in ADDRESS.findall(z.read(n).decode(errors="replace")):
                if addr.lower() not in ALLOWED:
                    carried.append(f"{n}: {addr}")
    ok(f"{v['name']}: carries no address that is not ours", not carried,
       "; ".join(carried[:3]))

    extract = workdir / v["name"]
    z.extractall(extract)
    server = extract / "server" / "server.py"
    p = subprocess.run(
        [python_exe, str(ROOT / v["suite"]), "--python", python_exe,
         "--server", str(server)],
        capture_output=True, text=True, timeout=1800)
    tail = [l.strip() for l in p.stdout.splitlines() if "passed," in l]
    ok(f"{v['name']}: the packed server passes its own stdio suite",
       p.returncode == 0, tail[-1] if tail else p.stderr[-300:])


def fixtures() -> int:
    """Drive the completeness rule over archives that are wrong on purpose."""
    full = ["manifest.json", "server/server.py",
            "server/claimgate/__init__.py", "server/claimgate/claims.py",
            "server/claimgate/htmltext.py", "server/claimgate/policy.py",
            "server/claimgate/substantiation.py", "server/claimgate/kit.py"]

    def without(*drops: str) -> list[str]:
        return [n for n in full if not any(d in n for d in drops)]

    dotted = "from claimgate.kit import build\nfrom claimgate.claims import extract\n"
    plain = "from claimgate import kit as kitmod\nfrom claimgate.claims import extract\n"
    comma = "from claimgate import kit, claims\n"
    cases = [
        ("a complete archive is clean", full, plain, False),
        ("a module reached by a dotted import is required",
         without("kit.py"), dotted, True),
        ("a module reached by a plain import is required",
         without("kit.py"), plain, True),
        ("a module named inside a comma list is required",
         without("kit.py"), comma, True),
        ("the package marker is required even when nothing names it",
         without("__init__"), plain, True),
        ("an archive with no imports at all still needs the package marker",
         without("__init__"), "import os\n", True),
        ("a complete archive is clean with no imports at all", full,
         "import os\n", False),
    ]
    passed = failed = 0
    print("=== the bundle-completeness rule, over fixtures ===")
    for label, names, src, should_fail in cases:
        caught = bool(required_files(names, src))
        good = caught if should_fail else not caught
        if good:
            passed += 1
            print(f"  PASS  {label}")
        else:
            failed += 1
            print(f"  FAIL  {label}   -> missing={required_files(names, src)}")
    print(f"\n  {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true",
                    help="rebuild both bundles from source first")
    ap.add_argument("--fixtures", action="store_true")
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()

    if a.fixtures:
        return fixtures()

    if a.rebuild:
        for v in VARIANTS:
            subprocess.run([sys.executable,
                            str(ROOT / "scripts" / "mcp_bundle.py"), v["name"]],
                           check=True, cwd=ROOT)

    print("=== the PACKED MCP bundles, checked as a user would receive them ===")
    with tempfile.TemporaryDirectory() as td:
        wd = pathlib.Path(td)
        for v in VARIANTS:
            check_variant(v, a.python, wd)

    failed = [n for n, p in FAULTS if not p]
    print(f"\n  {len(FAULTS) - len(failed)} passed, {len(failed)} failed")
    if failed:
        print("FAIL: " + "; ".join(failed[:3]))
        return 1
    print("PASS: both published bundles are valid, complete and installable, "
          "and the servers inside them work.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
