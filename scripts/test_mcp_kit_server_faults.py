#!/usr/bin/env python3
"""Prove the KIT MCP server test suite can fail, by breaking the server for real.

A test suite that has only ever passed is a suite nobody can trust. This copies
the kit server into a scratch tree, injects one genuine fault at a time, runs
the real suite against the broken copy, and requires the suite to go red. A
fault that is NOT caught is a hole in the suite, so this exits non-zero.

The first five are the same ways the engine could quietly stop being safe. The
last two exist only on this entry, and they are the ways a *free front door* in
particular goes wrong: it overwrites the policy someone has been editing, and it
tells a reader the copy is clear when the gate was blocked.

  1. fail-open      - "no evidence supplied" starts answering `supported`.
  2. no numbers     - the deterministic numeric gate stops comparing figures.
  3. silent pass    - an empty or unreadable draft is reported clean.
  4. no disclosure  - the EU AI Act Article 50 disclosure rule stops firing.
  5. silent empty   - a missing draft_path becomes an empty draft.
  6. force-always   - init_kit stops refusing and overwrites somebody's policy.
  7. verdict-clear  - the human report says CLEAR whatever the gate decided.

Run: python3 scripts/test_mcp_kit_server_faults.py
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path("/home/john-douglas/claimgate")
SUITE = REPO / "scripts" / "test_mcp_kit_server.py"

FAULTS = [
    ("fail-open: 'no evidence supplied' starts answering 'supported'",
     "server.py",
     'return [Verdict(c, "unverified", reason=(',
     'return [Verdict(c, "supported", reason=('),
    ("the deterministic numeric gate is disabled",
     "server.py",
     "missing = numbers_supported(c.text, blob)[1]\n        if missing:",
     "missing = numbers_supported(c.text, blob)[1]\n        if False:"),
    ("an empty draft is quietly reported clear",
     "server.py",
     'if not draft.strip():\n        raise ValueError("`draft` is empty; supply the copy to check")',
     'if not draft.strip():\n        return "", "draft (inline)"'),
    ("the AI-disclosure rule stops firing",
     "policy.py",
     'if policy.disclosure_required:',
     'if False:'),
    ("a missing draft_path silently becomes an empty draft",
     "server.py",
     'if not p.is_file():\n            raise ValueError(f"draft_path does not exist or is not a file: {p}")',
     'if not p.is_file():\n            return "", str(p)'),
    ("init_kit stops refusing and overwrites an existing policy",
     "server.py",
     "written = kitmod.build(root, force=force)",
     "written = kitmod.build(root, force=True)"),
    ("the human report says CLEAR whatever the gate decided",
     "server.py",
     '"VERDICT: BLOCKED - do not publish as it stands."',
     '"VERDICT: CLEAR - do not publish as it stands."'),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()

    print("=== can the KIT MCP server suite fail? injected faults ===")
    all_caught = True
    for label, rel, old, new in FAULTS:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="cgkitfault-"))
        try:
            (tmp / "claimgate").mkdir()
            (tmp / "mcp-kit").mkdir()
            for f in REPO.glob("claimgate/*.py"):
                shutil.copy2(f, tmp / "claimgate" / f.name)
            shutil.copy2(REPO / "mcp-kit" / "server.py",
                         tmp / "mcp-kit" / "server.py")
            target = (tmp / "mcp-kit" / rel) if rel == "server.py" \
                else (tmp / "claimgate" / rel)
            text = target.read_text()
            if old not in text:
                print(f"  INVALID    {label}")
                print("             anchor not found - this fault was never "
                      "injected, so it proves nothing")
                all_caught = False
                continue
            target.write_text(text.replace(old, new, 1))
            p = subprocess.run(
                [a.python, str(SUITE), "--python", a.python,
                 "--server", str(tmp / "mcp-kit" / "server.py")],
                capture_output=True, text=True, timeout=1200)
            caught = p.returncode != 0
            tail = [l.strip() for l in p.stdout.splitlines()
                    if "FAIL" in l or "passed," in l]
            print(f"  {'CAUGHT' if caught else 'NOT CAUGHT':10} {label}")
            if tail:
                print(f"             {tail[-1]}")
            all_caught = all_caught and caught
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    print()
    if all_caught:
        print("  PASS: every injected fault was caught by the suite.")
        return 0
    print("  FAIL: at least one injected fault went undetected - the suite has "
          "a hole.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
