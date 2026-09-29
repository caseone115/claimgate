"""Regenerate the free starter kit's download from the current source.

The paid engine already had a builder that verifies itself. The kit did not:
`dist/claimgate-starter-kit-0.1.0.zip` was assembled by hand, which is how its
README kept advertising the US$149 list price long after a US$39 launch price
was live. A hand-built artifact drifts from its source with nothing to catch it.

So the kit gets the same treatment as the engine: built from `claimgate.kit`,
deterministic (fixed timestamp, sorted entries), and the README is read back
*out of the finished zip* and asserted to carry the launch link before the
archive is accepted. If the kit's own text ever loses the launch price again,
this refuses to build rather than shipping it.

    python scripts/build_kit_dist.py
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from claimgate import kit as kitmod  # noqa: E402

VERSION = "0.1.0"
NAME = f"claimgate-starter-kit-{VERSION}"
TOP = "claimgate-starter-kit"
OUT = ROOT / "dist" / f"{NAME}.zip"
EPOCH = (2026, 1, 1, 0, 0, 0)


def stage(dest: Path) -> Path:
    """Write the kit into dest/claimgate-starter-kit."""
    root = dest / TOP
    root.mkdir(parents=True, exist_ok=True)
    kitmod.build(root)
    return root


def build() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        root = stage(Path(d))
        members = sorted(p for p in root.rglob("*") if p.is_file())
        if not members:
            raise SystemExit("REFUSING TO SHIP — the kit built nothing")
        with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
            for p in members:
                rel = p.relative_to(Path(d)) / ""  # keep the top-level folder
                info = zipfile.ZipInfo(str(rel).rstrip("/"), date_time=EPOCH)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, p.read_bytes())
    return OUT


def verify(archive: Path) -> None:
    """Read the shipped README back out of the zip and hold it to its promise.

    This is the check that was missing. Whatever else changes, the free kit
    that a customer actually receives must (a) carry the launch link, (b) state
    both prices, and (c) not carry the stale check count it used to.
    """
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        readme = z.read(f"{TOP}/README.md").decode()
        checklist = z.read(f"{TOP}/CHECKLIST.md").decode()

    for must in ("README.md", "CHECKLIST.md", "DRAFT-template.md",
                 "policy.json", "policy-notes.md",
                 ".github/workflows/claimgate.yml", "evidence/README.md"):
        if f"{TOP}/{must}" not in names:
            raise SystemExit(f"REFUSING TO SHIP — {must} missing from the kit")

    if "claimgate/LAUNCH39" not in readme:
        raise SystemExit("REFUSING TO SHIP — the kit README lost the launch link")
    if "$39" not in readme or "149" not in readme:
        raise SystemExit("REFUSING TO SHIP — the kit README must state both prices")
    if "45-check" in readme:
        raise SystemExit("REFUSING TO SHIP — the kit README still carries the "
                         "stale 45-check count")
    if "claimgate/LAUNCH39" not in checklist:
        raise SystemExit("REFUSING TO SHIP — the checklist lost the launch link")

    # and the kit must still run its own gate end to end from the extracted copy
    for leaked in ("state/", ".env", "account.txt", "outreach_sent.jsonl"):
        hits = [n for n in names if leaked in n]
        if hits:
            raise SystemExit(f"REFUSING TO SHIP — archive contains {hits}")


def digest(a: Path) -> str:
    return hashlib.sha256(a.read_bytes()).hexdigest()


def record(a: Path, sha: str) -> Path:
    sums = a.parent / f"{NAME}.SHA256SUMS"
    sums.write_text(f"{sha}  {a.name}\n")
    return sums


if __name__ == "__main__":
    a = build()
    first = digest(a)
    b = build()
    second = digest(b)
    if first != second:
        raise SystemExit("REFUSING TO SHIP — the archive is not reproducible")
    print(f"built {a} ({a.stat().st_size} bytes)")
    print(f"sha256 {first}  (reproducible across two builds)")
    verify(a)
    record(a, first)
    print(f"verified the shipped README out of the zip — OK")
