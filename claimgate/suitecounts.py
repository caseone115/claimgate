"""The one place the test-suite counts are known — measured, never written down.

Why this exists (2026-09-30, ninth tick): the product's own published numbers
were wrong on two live surfaces, found the same way the install-command fault
was found the tick before — by reading what we publish against what we ship.

  * `README.md` — which also ships *inside the paid download*, so it was a
    paying customer's copy — told the buyer `tests/test_kit.py` is "34 checks".
    It is 44. Wrong since the kit contract grew.
  * the live landing page advertised a "112-check test suite". The suites are
    55 + 21 + 44 = 120.

Both are the exact fault this product exists to catch: a published figure the
supplier's own evidence does not support. The previous guard could not catch it
because it hard-coded one stale literal string ("45-check"), which is a check
that can only ever find the mistake it was written for.

So: the counts are *measured*, by running the suites and reading each one's own
verdict line, and every surface that quotes a count is asserted against the
measurement. This module is deliberately NOT called from inside a suite — a
suite that measures all three suites would have to measure itself, which is
circular and would produce a check that lies. It is called by the archive
builders (which refuse to ship a wrong number) and by the standing probe (which
reports a live surface that has drifted).

    python -m claimgate.suitecounts
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SUITES = {
    "engine": "tests/test_claimgate.py",
    "outreach": "tests/test_outreach.py",
    "kit": "tests/test_kit.py",
}

_VERDICT = re.compile(r"(\d+)\s*/\s*(\d+)\s+checks? behaved as intended")

# (label, relative path, regex with one capture group, suite it must equal,
#  required?) — `required=False` for a surface that ships only in the
# repository, so the check still works from inside the extracted archive.
SURFACES = [
    ("public README — engine count", "README.md",
     r"python tests/test_claimgate\.py\s*#\s*(\d+) checks", "engine", True),
    ("public README — outreach count", "README.md",
     r"python tests/test_outreach\.py\s*#\s*(\d+) checks", "outreach", True),
    ("public README — kit count", "README.md",
     r"python tests/test_kit\.py\s*#\s*(\d+) checks", "kit", True),
    ("starter kit text — engine count", "claimgate/kit.py",
     r"the (\d+)-check engine test suite", "engine", True),
    ("landing page — total suite count", "docs/index.html",
     r"(\d+)-check test suite", "total", False),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def measure(root: Path | None = None) -> dict[str, int]:
    """Run each suite and read the total it reports about itself."""
    root = root or repo_root()
    counts: dict[str, int] = {}
    for name, rel in SUITES.items():
        r = subprocess.run([sys.executable, str(root / rel)], cwd=root,
                           capture_output=True, text=True, timeout=900)
        out = (r.stdout or "") + (r.stderr or "")
        m = None
        for m in _VERDICT.finditer(out):
            pass
        if m is None:
            raise SystemExit(
                f"cannot measure {rel}: no verdict line\n{out[-2000:]}")
        passed, total = int(m.group(1)), int(m.group(2))
        if passed != total or r.returncode != 0:
            raise SystemExit(f"refusing — {rel} is failing ({passed}/{total})")
        counts[name] = total
    counts["total"] = counts["engine"] + counts["outreach"] + counts["kit"]
    return counts


def problems(root: Path | None = None, counts: dict[str, int] | None = None) -> list[str]:
    """Everything wrong with what the shipped surfaces state. Empty is good."""
    root = root or repo_root()
    counts = counts or measure(root)
    found: list[str] = []
    for label, rel, pattern, suite, required in SURFACES:
        path = root / rel
        if not path.exists():
            if required:
                found.append(f"{label}: {rel} is missing")
            continue
        m = re.search(pattern, path.read_text())
        if m is None:
            found.append(f"{label}: no count found in {rel} — the claim was "
                         f"dropped, which is not the same as keeping it true")
            continue
        stated, real = int(m.group(1)), counts[suite]
        if stated != real:
            found.append(f"{label}: {rel} says {stated}; the {suite} suite "
                         f"is {real}")
    return found


def main() -> int:
    counts = measure()
    print("measured straight from the suites:")
    for k in ("engine", "outreach", "kit"):
        print(f"  {k:9s} {counts[k]:4d}  ({SUITES[k]})")
    print(f"  {'total':9s} {counts['total']:4d}")
    found = problems(counts=counts)
    if found:
        print("\nMISMATCH — a shipped surface states a number the suites do not "
              "support:")
        for p in found:
            print("  x", p)
        return 1
    print("\nOK: every shipped surface states the counts the suites report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
