"""Read the prose this product ships and refuse a paragraph that is broken.

Found 2026-09-30, by extracting the free starter kit's own download and reading
it the way a stranger does. The kit's README had its PyPI-namesake warning
paragraph inserted into the middle of the sentence that warns you not to buy
unchecked, so a reader met this:

    ... Nothing is held back from it. Read it,

    Install it from that repository, not by the bare name: `pip install claimgate`
    on PyPI is a different, unrelated project ... and it has no `claimgate check`
    command at all.
    and if it does not do what this page says, do not buy it.

Every test that covered the kit was a substring assertion -- `"$39" in readme`,
`"do not buy" in readme` -- so all of them passed on text no reader could read
straight. A substring check can only find the mistake it was written for. This
one looks at structure instead: prose does not end in a comma or a semicolon,
and prose does not open on a lower-case fragment.

    python scripts/check_prose.py            # the repo's customer-facing pages
    python scripts/check_prose.py --root DIR # any tree of .md files

Exits non-zero, naming the file and the line, if any shipped prose is broken.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Customer-facing text: what a buyer, an adopter or a visitor reads. Internal
# notes and ledgers are deliberately out of scope -- they are written for the
# job, in fragments, and holding them to a prose standard would be noise.
DEFAULT_TARGETS = (
    "README.md",
    "docs/SUPPORT.md",
    "docs/UNBLOCK.md",
)
# The kit's own README and CHECKLIST are checked from a *built* kit (below),
# not from kit.py's source: what ships is the only text that matters, and the
# builder is the thing that decides what ships.

OPENERS = ("http", "`", "(", "[", "{", '"', "'", "*", "_", "|", "@", "/", "-", ">",
           "e.g.", "i.e.", "etc.")


def _indented(line: str) -> bool:
    return line.startswith("    ") or line.startswith("\t")


def markdown_blocks(text: str):
    """Prose paragraphs of a markdown document, in order.

    Blank-line delimited, minus fenced code, minus indented code. A block whose
    *second* line is indented is a label introducing an indented table
    ("severity" / "    high  ..."), not prose that opens on a fragment.
    """
    fence, blocks, cur = False, [], []
    for raw in text.splitlines():
        if raw.lstrip().startswith("```"):
            fence = not fence
            if cur:
                blocks.append(cur)
                cur = []
            continue
        if fence:
            continue
        if not raw.strip():
            if cur:
                blocks.append(cur)
                cur = []
            continue
        cur.append(raw)
    if cur:
        blocks.append(cur)
    out = []
    for b in blocks:
        if not b or _indented(b[0]):
            continue
        if len(b) > 1 and _indented(b[1]):
            continue
        out.append(b)
    return out


def evaluate(text: str, name: str = "file"):
    """Pure rules. Returns [(name, kind, line)] -- drive this over fixtures."""
    out = []
    for block in markdown_blocks(text):
        first = block[0].strip()
        last = block[-1].strip()
        if not first:
            continue
        if last.endswith((",", ";")):
            out.append((name, "paragraph ends mid-sentence (no sentence does)", last))
        if first[:1].islower() and not first.startswith(OPENERS):
            out.append((name, "paragraph opens on a lower-case fragment", first))
    return out


def _scan(path: Path, name: str | None = None):
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    return evaluate(text, name or str(path.relative_to(ROOT)))


def kit_text() -> str:
    """The kit's shipped text, read out of a built kit rather than the source."""
    sys.path.insert(0, str(ROOT))
    import tempfile

    from claimgate import kit as kitmod

    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "kit"
        kitmod.build(root)
        return (root / "README.md").read_text() + "\n\n" + \
            (root / "CHECKLIST.md").read_text()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None,
                    help="scan every .md under this directory instead")
    a = ap.parse_args(argv)

    if a.root:
        files = sorted(Path(a.root).rglob("*.md"))
        findings = []
        for f in files:
            findings += _scan(f, str(f))
    else:
        findings = []
        for rel in DEFAULT_TARGETS:
            findings += _scan(ROOT / rel, rel)
        findings += evaluate(kit_text(), "claimgate/kit.py (built kit)")

    for name, kind, line in findings:
        print(f"FAIL  {name}: {kind}\n        {line[:160]}")
    print(f"\n{len(findings)} broken paragraph(s) in shipped prose")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
