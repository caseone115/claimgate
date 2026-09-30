"""Every prepared outreach message must quote a page that was really read.

This exists because of a near-miss on 2026-09-30. Four new messages were
written whose hooks were *true observations* about the recipients' published
work - but paraphrased, with my own framing folded in. Read back, they look
exactly like verified quotes. Only folding the actual page text and searching
it showed they were not: the guard would have accepted every one of them,
because the guard checks that the hook appears in the *body*, not that the
hook came from anywhere real.

So there are two separate checks, and both are needed:

  1. the hook is a verbatim substring of a saved copy of the page it claims to
     come from (no clever matching - it has to literally be there);
  2. the recipient address appears on that same page, or on the page saved
     beside it as the address source.

Both are refused rather than warned about. `--plant` proves the test can fail
by breaking one hook on purpose.

    python3 tests/test_hook_provenance.py
    python3 tests/test_hook_provenance.py --plant
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
EV = STATE / "outreach_evidence"
sys.path.insert(0, str(STATE))
sys.path.insert(0, str(ROOT))

import outreach_extra  # noqa: E402  (the second wave, prepared 2026-09-30)

DASH = {"\u2013": "-", "\u2014": "-", "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"', "\u00a0": " ", "\u00ad": ""}

# slug -> (hook evidence file, address evidence file)
SLUGS = {
    "veronica": ("nimble__hook_page", "nimble__addr_page"),
    "weventure": ("weventure__hook_page", "weventure__addr_page"),
    "sackit": ("sackit__hook_page", "sackit__addr_page"),
    "blackhold": ("blackhold__hook_page", "blackhold__addr_page"),
}

results: list[tuple[str, bool, str]] = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond and detail:
        print(f"        {detail}")


def fold(s: str) -> str:
    """Same folding used when the evidence was saved, so a match is a match."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    for k, v in DASH.items():
        s = s.replace(k, v)
    s = s.replace("&quot;", '"').replace("&amp;", "&").replace("&#8217;", "'")
    return re.sub(r"\s+", " ", s).lower()


def main() -> int:
    plant = "--plant" in sys.argv
    print("\n=== every prepared message quotes a page that was really read ===\n")

    for slug, (hook_file, addr_file) in SLUGS.items():
        hook = outreach_extra.NEW[slug]["hook"]
        addr = outreach_extra.NEW[slug]["addr"]
        hp, ap = EV / f"{hook_file}.txt", EV / f"{addr_file}.txt"

        if not hp.exists():
            ok(f"{slug}: hook page was saved", False, f"missing {hp}")
            continue
        ok(f"{slug}: hook page was saved", True)

        page = fold(hp.read_text(errors="replace"))
        needle = fold(hook).strip()

        if plant and slug == "veronica":
            needle = needle.replace("nej, inte bara", "sant, aven om")
            print("        (planted: veronica's hook altered to prove this fails)")

        ok(f"{slug}: the hook is a verbatim quote of that page",
           needle in page,
           f"hook not found in {hp.name}: {needle[:90]!r}")

        if ap.exists():
            addr_page = fold(ap.read_text(errors="replace"))
        else:
            addr_page = ""
        ok(f"{slug}: the address is published on the page it was read off",
           addr.lower() in addr_page,
           f"{addr} not found in {ap.name if ap.exists() else ap} - an address "
           f"that is not on the page is an address that was guessed")

    print("\n=== the honest framing that makes this legitimate is also present ===\n")
    for slug, cfg in outreach_extra.NEW.items():
        low = cfg["body"].lower()
        ok(f"{slug}: the message says plainly that it is software",
           "sent by software" in low or "not by a person" in low)
        ok(f"{slug}: the message names the product", "claimgate" in low)

    passed = sum(1 for _, o, _ in results if o)
    total = len(results)
    print(f"\n{passed}/{total} checks behaved as intended")
    if passed != total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
