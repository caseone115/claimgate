"""Regenerate the buyer-facing download from the current source.

The archive is what a customer actually receives, so it is built here rather
than by hand, and the test suite is run *from inside the extracted copy* before
the archive is accepted. Tests that pass in the working checkout prove nothing
about what is in the zip: a missing module or an excluded package is invisible
until a buyer hits it.

    python scripts/build_dist.py
"""
from __future__ import annotations

import hashlib
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

# Fixed timestamp for every entry, so two builds of the same source produce the
# same bytes. Without this neither the seller nor anyone auditing the listing can
# tell whether the file attached to a product is the build it claims to be —
# every rebuild changes the hash even when nothing changed.
EPOCH = (2026, 1, 1, 0, 0, 0)


def build() -> Path:
    missing = [p for p in INCLUDE if not (ROOT / p).exists()]
    if missing:
        raise SystemExit(f"refusing to build — missing: {missing}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in INCLUDE:
            info = zipfile.ZipInfo(f"{NAME}/{rel}", date_time=EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (ROOT / rel).read_bytes())
    return OUT


def digest(archive: Path) -> str:
    return hashlib.sha256(archive.read_bytes()).hexdigest()


def record(archive: Path, sha: str) -> Path:
    """Publish the hash next to the archive so a buyer can verify the download."""
    sums = archive.parent / "SHA256SUMS"
    line = f"{sha}  {archive.name}\n"
    if not sums.exists() or sums.read_text() != line:
        sums.write_text(line)
    return sums



def verify(archive: Path) -> None:
    """Extract and run the suite from inside the extracted copy."""
    # found 2026-09-30: the shipped README told buyers to run a bare
    # pip install claimgate. That name on PyPI is a different, unrelated
    # project with no claimgate check command at all, so the first
    # instruction the product gave a buyer installed a different tool.
    # A gate against untrue published claims cannot ship an untrue
    # instruction.
    with zipfile.ZipFile(archive) as _z:
        _readme = _z.read(NAME + "/README.md").decode()
    _bad = []
    for _line in _readme.splitlines():
        _s = _line.strip()
        if _s.startswith("pip install claimgate") and "git+" not in _s:
            _bad.append(_s)
    if _bad:
        raise SystemExit("REFUSING TO SHIP - the archive README tells a buyer to install the PyPI namesake: " + str(_bad))
    if "git+https://github.com/caseone115/claimgate" not in _readme:
        raise SystemExit("REFUSING TO SHIP - the archive README lost the correct install command")
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
    first = digest(a)
    # prove reproducibility rather than claiming it: build twice, compare
    b = build()
    second = digest(b)
    if first != second:
        raise SystemExit("REFUSING TO SHIP — the archive is not reproducible")
    print(f"built {a} ({a.stat().st_size} bytes)")
    print(f"sha256 {first}  (reproducible across two builds)")
    record(a, first)
    print("verifying from inside the archive:")
    verify(a)
    print(f"OK — {a}")
