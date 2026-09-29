"""Regenerate the buyer-facing download from the current source.

The archive is what a customer actually receives, so it is built here rather
than by hand, and the test suite is run *from inside the extracted copy* before
the archive is accepted. Tests that pass in the working checkout prove nothing
about what is in the zip: a missing module or an excluded package is invisible
until a buyer hits it.

    python scripts/build_dist.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "0.1.0"
NAME = f"claimgate-{VERSION}"
OUT = ROOT / "dist" / f"{NAME}.zip"

INCLUDE = [
    "claimgate/__init__.py",
    "claimgate/claims.py",
    "claimgate/cli.py",
    "claimgate/kit.py",
    "claimgate/policy.py",
    "claimgate/substantiation.py",
    "claimgate/outreach.py",
    "tests/test_claimgate.py",
    "tests/test_kit.py",
    "tests/test_outreach.py",
    "examples/bad-draft.md",
    "examples/evidence/acme-spec.md",
    "README.md",
    "LICENSE",
    "pyproject.toml",
    "REVENUE.md",
    "docs/SUPPORT.md",
]

TESTS = ["tests/test_claimgate.py", "tests/test_kit.py", "tests/test_outreach.py"]


def build() -> Path:
    missing = [p for p in INCLUDE if not (ROOT / p).exists()]
    if missing:
        raise SystemExit(f"refusing to build — missing: {missing}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in INCLUDE:
            z.write(ROOT / rel, f"{NAME}/{rel}")
    return OUT


def verify(archive: Path) -> None:
    """Extract and run the suite from inside the extracted copy."""
    with tempfile.TemporaryDirectory() as d:
        with zipfile.ZipFile(archive) as z:
            z.extractall(d)
        root = Path(d) / NAME
        for t in TESTS:
            r = subprocess.run([sys.executable, t], cwd=root,
                               capture_output=True, text=True, timeout=300)
            last = (r.stdout or r.stderr).strip().splitlines()[-1]
            print(f"  {t}: {last}")
            if r.returncode != 0 or "behaved as intended" not in last:
                raise SystemExit(f"REFUSING TO SHIP — {t} failed in the archive")

        # the archive must not carry a credential or a contact list
        for leaked in ("state/", ".env", "account.txt", "outreach_sent.jsonl",
                       "outreach_suppress.txt"):
            hits = [n for n in zipfile.ZipFile(archive).namelist()
                    if leaked in n]
            if hits:
                raise SystemExit(f"REFUSING TO SHIP — archive contains {hits}")


if __name__ == "__main__":
    a = build()
    print(f"built {a} ({a.stat().st_size} bytes)")
    print("verifying from inside the archive:")
    verify(a)
    print(f"OK — {a}")
