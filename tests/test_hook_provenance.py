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
import outreach_wave3   # noqa: E402  (the third wave, prepared 2026-10-01)
import outreach_wave4   # noqa: E402  (the fourth wave, prepared 2026-10-01)

DASH = {"\u2013": "-", "\u2014": "-", "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"', "\u00a0": " ", "\u00ad": ""}

# slug -> (hook evidence file, address evidence file), and which message file the
# entry lives in. Every wave in the queue is covered, not only the one that was
# being written when this test was first created: a provenance check that stops
# at wave two lets wave three and wave four be written on trust, and wave four was
# (2026-10-01) written and verified by a one-off script until this table was
# widened. The pages all live in state/outreach_evidence/.
SLUGS = {
    "veronica": ("nimble__hook_page", "nimble__addr_page"),
    "weventure": ("weventure__hook_page", "weventure__addr_page"),
    "sackit": ("sackit__hook_page", "sackit__addr_page"),
    "blackhold": ("blackhold__hook_page", "blackhold__addr_page"),
}

VERIFIED = "verified-2026-10-01"
# slug -> (wave module, hook page, address page) for the later waves, whose
# evidence lives together in one dated folder.
LATER = {
    "devedge": (outreach_wave3.NEW3, "devedge__policy.html", "devedge__contact.html"),
    "totem": (outreach_wave3.NEW3, "totem__policy.html", "totem__contact.html"),
    "mediaforta": (outreach_wave4.NEW4, "mediaforta_policy.html", "mediaforta_policy.html"),
    "righttouch": (outreach_wave4.NEW4, "righttouch_policy.html", "righttouch_policy.html"),
    "hellooperator": (outreach_wave4.NEW4, "hellooperator_policy.html",
                      "hellooperator_policy.html"),
    "goya": (outreach_wave4.NEW4, "goya_policy.html", "goya_policy.html"),
}

def address_on_page(addr: str, page_path: Path) -> tuple[bool, str]:
    """Is `addr` published on this page, including inside a mailto: link?

    Found 2026-10-01 while widening this test to wave four. The rule read the
    page after stripping every tag, which also strips attributes - and an
    address is most often published as `<a href="mailto:someone@example.com">`
    rather than as visible text. Hello Operator publishes its address in exactly
    that form, so the rule reported a real published address as one that had been
    guessed. That is the expensive direction of this particular error (it would
    have blocked a legitimate send, or, worse, taught the reader to wave the rule
    through), so the raw source is searched as well as the stripped text.
    """
    low = addr.lower()
    raw = page_path.read_text(errors="replace").lower()
    if low in raw:
        return True, "in the raw source (e.g. a mailto: link)"
    return False, "not in the page at all"


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

        found, where = address_on_page(addr, ap) if ap.exists() else (False, "no page saved")
        ok(f"{slug}: the address is published on the page it was read off",
           found,
           f"{addr} {where} ({ap.name}) - an address that is not on the page is "
           f"an address that was guessed")

    print("\n=== the later waves quote their pages too, not only the wave being written ===\n")
    for slug, (mod, hook_file, addr_file) in LATER.items():
        cfg = mod[slug]
        hook, addr = cfg["hook"], cfg["addr"]
        hp, ap = EV / VERIFIED / hook_file, EV / VERIFIED / addr_file
        if not hp.exists():
            ok(f"{slug}: hook page was saved", False, f"missing {hp}")
            continue
        ok(f"{slug}: hook page was saved", True)
        page = fold(hp.read_text(errors="replace"))
        needle = fold(hook).strip()
        if plant and slug == "goya":
            needle = needle.replace("individual text publications", "some text publications")
            print("        (planted: goya's hook altered to prove this fails)")
        ok(f"{slug}: the hook is a verbatim quote of that page",
           needle in page,
           f"hook not found in {hp.name}: {needle[:90]!r}")
        found, where = address_on_page(addr, ap) if ap.exists() else (False, "no page saved")
        ok(f"{slug}: the address is published on the page it was read off",
           found,
           f"{addr} {where} ({ap.name}) - an address that is not on the page is "
           f"an address that was guessed")

    # The address rule must be seen to fail too, or the reader has no reason to
    # believe it is doing anything. A guessed address is the one thing this rule
    # exists to catch, so it is planted here rather than argued about.
    print("\n=== a guessed address is caught (the rule is driven, not trusted) ===\n")
    # The real address is read out of the wave module rather than typed here.
    # This test file is committed to a PUBLIC repository, and a real prospect's
    # address in the source is precisely the leak this project removed from
    # REVENUE.md on 2026-10-01 - putting one back in a test would be the same
    # fault wearing a different hat.
    probe_page = EV / VERIFIED / "goya_policy.html"
    ok("a real address on a real page passes the rule",
       address_on_page(outreach_wave4.NEW4["goya"]["addr"], probe_page)[0])
    ok("an address that is on no page is refused by the rule",
       not address_on_page("guessed-address@example.com", probe_page)[0])

    print("\n=== the honest framing that makes this legitimate is also present ===\n")
    everything = dict(outreach_extra.NEW)
    for name, mod in (("w3", outreach_wave3.NEW3), ("w4", outreach_wave4.NEW4)):
        for k, v in mod.items():
            everything[f"{k}"] = v
    for slug, cfg in everything.items():
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
