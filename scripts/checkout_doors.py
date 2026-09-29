#!/usr/bin/env python3
"""Does the shop still take money the way we advertise?

Added 2026-09-30 (sixth tick) after shopping in our own shop logged-out found two
things that no page we publish could ever show:

  1. the launch discount was scoped to *all products*, so the same link that
     takes the US$149 product to US$39 took the US$14 product to A$0;
  2. the checkout offered no discount-code field at all, so the launch price was
     reachable only by arriving through one exact link.

Both were fixed that tick. This script is what notices if either comes back. It
lives outside the test suite on purpose: it needs a browser and the live shop, so
it checks the shop rather than the code.

Exit 0 = the doors work. Exit 1 = something regressed, with the detail printed.

Assertion style: prices are compared as RATIOS, never as hard-coded cents. The
shop renders in the visitor's currency, so the same US$39 checkout shows a
different AUD figure whenever FX moves. The first version of this script
hard-coded A$55.89 and raised a false regression on 2026-09-30 when the list
price moved A$213.51 -> A$213.81 and the launch price to A$55.96: the discount
was correct, the assertion was not. A false alarm on a standing check is
expensive — it teaches the reader to ignore the check.

Browser handling: all launches go through `state/browser.py`, which reaps
this project's orphaned headless Chrome (matched by the exact
--user-data-dir, never the user's own browser) and clears stale profile
locks first. On 2026-09-30 this probe worked exactly once and then every
later browser run failed, because agent-browser leaves Chrome running and
the orphan holds the profile; the cause was invisible to the probe's own
exit code, which reported only the price regression below.

Note on parsing: agent-browser returns its eval result as an already-quoted JSON
string, so the payload is escaped twice and substring-matching on it produced two
false alarms on the first run of this script. It now asks for plain
delimiter-separated text and parses that.
"""
from __future__ import annotations

import subprocess
import sys
import time

ROOT = "/home/john-douglas"
AB = ROOT + "/.npm/_npx/ad6c181e5b604bdb/node_modules/agent-browser/bin/agent-browser.js"
BUYER_PROFILE = ROOT + "/claimgate/state/buyer-profile"
ADMIN_PROFILE = ROOT + "/claimgate/state/gumroad-profile"
FLAGS = "--no-sandbox,--disable-dev-shm-usage"

FAILURES: list[str] = []
NOTES: list[str] = []

URL_CG_LAUNCH = "https://teeterbot.gumroad.com/l/claimgate/LAUNCH39"
URL_CG_PLAIN = "https://teeterbot.gumroad.com/l/claimgate"
URL_SS_LAUNCH = "https://teeterbot.gumroad.com/l/simscan/LAUNCH39"
URL_SS_PLAIN = "https://teeterbot.gumroad.com/l/simscan"
URL_KIT = "https://teeterbot.gumroad.com/l/claimgate-starter-kit"


def _unquote(raw: str) -> str:
    """agent-browser quotes its eval payload; strip that one layer only."""
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"') and len(raw) > 1:
        raw = raw[1:-1]
    return raw.replace("\\n", "\n")


def ab(*args, profile: str, session: str, timeout: int = 300) -> str:
    """Delegate to the shared driver: it reaps our orphaned Chrome and clears
    stale profile locks before every launch. The first version of this script
    cleared locks only, which did not help — the surviving Chrome processes were
    what held the profile, and they made every run after the first one die."""
    import sys as _sys
    _sys.path.insert(0, "/home/john-douglas/claimgate/scripts")
    import browser as _b
    return _b.ab(*args, profile=profile, session=session, timeout=timeout)


# Plain text out, no nested JSON: <struck prices> || <every A$ amount in the body>
# The discounted figure is not a leaf node, so amounts come from the whole body.
PRICE_JS = (
    r"""(function(){"""
    r"""var st=[];"""
    r"""document.querySelectorAll('s,del,[style*="line-through"]').forEach(function(e){"""
    r"""var s=(e.innerText||'').trim(); if(s) st.push(s);});"""
    r"""var t=(document.body.innerText||'');"""
    r"""var m=t.match(/A\$\s?\d[\d,]*\.?\d{0,2}/g)||[];"""
    r"""return st.join(';')+'||'+m.join(';');})()"""
)


def probe(url: str) -> tuple[list[str], list[str]]:
    ab("open", url, profile=BUYER_PROFILE, session="buyer2")
    time.sleep(9)
    raw = _unquote(ab("eval", PRICE_JS, profile=BUYER_PROFILE, session="buyer2"))
    left, _, right = raw.partition("||")
    struck = [s for s in left.split(";") if s.strip()]
    leaves = [s for s in right.split(";") if s.strip()]
    return struck, leaves


def main() -> int:
    # ---- door 1: the launch link still discounts the flagship product
    struck, leaves = probe(URL_CG_LAUNCH)
    NOTES.append(f"claimgate+code: struck={struck} prices={leaves}")
    if not struck:
        FAILURES.append("claimgate/LAUNCH39 no longer shows a struck-through list price "
                        f"— the launch link is not discounting — prices seen {leaves}")
    else:
        # Assert the RATIO, not the cents. The price renders in the visitor's
        # currency, so FX drift moves the AUD figure without anything being
        # wrong — hard-coded cents produced a false "regression" on 2026-09-30
        # when the list went A$213.51 -> A$213.81. US$39 of US$149 is 39/149.
        def _amt(s: str) -> float:
            return float(s.replace("A$", "").replace(",", "").replace(" ", ""))
        try:
            list_price = _amt(struck[0])
            target = list_price * 39.0 / 149.0
            tol = max(0.75, target * 0.02)
            ok = any(abs(_amt(l) - target) <= tol for l in leaves)
            detail = (f"list {list_price:.2f} -> expected ~{target:.2f} "
                      f"(39/149, tol +/-{tol:.2f}); prices seen {leaves}")
        except Exception as e:
            ok = False
            detail = f"could not parse prices ({e}); struck={struck} prices={leaves}"
        if not ok:
            FAILURES.append("claimgate/LAUNCH39 shows a struck price but not the 39/149 "
                            f"launch price — {detail}")

    # ---- door 2: the discount must NOT reach the second product (this was the giveaway)
    ss_struck, ss_leaves = probe(URL_SS_LAUNCH)
    ss_plain_struck, ss_plain_leaves = probe(URL_SS_PLAIN)
    NOTES.append(f"simscan+code: struck={ss_struck} prices={ss_leaves}")
    NOTES.append(f"simscan plain: struck={ss_plain_struck} prices={ss_plain_leaves}")
    if ss_struck:
        FAILURES.append("simscan/LAUNCH39 shows a struck-through price again — the discount "
                        f"is reaching the second product — struck={ss_struck}")
    if ss_leaves and ss_plain_leaves and ss_leaves[0] != ss_plain_leaves[0]:
        FAILURES.append(f"simscan with the code attached prices differently from simscan plain: "
                        f"{ss_leaves[0]} vs {ss_plain_leaves[0]} — the code is reaching it")

    # ---- door 3: checkout still offers the discount-code field
    ab("open", "https://gumroad.com/checkout/form", profile=ADMIN_PROFILE, session="gumroad")
    time.sleep(9)
    radios = _unquote(ab("eval",
                r"""Array.from(document.querySelectorAll('input[type=radio]')).slice(0,2)"""
                r""".map(function(e){return e.checked;}).join(',')""",
                profile=ADMIN_PROFILE, session="gumroad"))
    NOTES.append(f"checkout form radios (first two, checked): {radios}")
    if not radios.startswith("true"):
        FAILURES.append("the discount-code field at checkout is switched off again — it must be "
                        f"'Only if a discount is available' — raw: {radios}")

    # ---- door 4: the discount still names the exclusion
    ab("open", "https://gumroad.com/checkout/discounts", profile=ADMIN_PROFILE, session="gumroad")
    time.sleep(8)
    row = ab("eval",
             r"""Array.from(document.querySelectorAll('tr')).map(function(t){"""
             r"""return t.innerText.replace(/\s+/g,' ');}).join(' ')""",
             profile=ADMIN_PROFILE, session="gumroad").strip()
    NOTES.append(f"discount row: {row[:220]}")
    if "except SimScan" not in row:
        FAILURES.append("the launch discount no longer excludes the second product — it is "
                        f"scoped to all products again — raw: {row[:220]}")

    # ---- door 5: neither live listing tells a reader to install the wrong
    # package. The bare name claimgate on PyPI belongs to a different,
    # unrelated project which has no claimgate check command at all. A
    # listing that recommends it sends a buyer nowhere. Found 2026-09-30 in
    # the kit README; this is the door that notices if it comes back.
    import urllib.request
    for label, page_url in (("paid listing", URL_CG_PLAIN),
                           ("kit listing", URL_KIT)):
        try:
            html = urllib.request.urlopen(page_url, timeout=30).read().decode()
        except Exception as exc:
            FAILURES.append(label + " could not be fetched: " + str(exc))
            continue
        if "pip install claimgate" in html and "git+" not in html:
            FAILURES.append(
                label + " tells a reader to run the bare pip install claimgate,"
                " which installs a different project")
        NOTES.append(label + " checked for the wrong install command")

    print("checkout doors probe")
    for n in NOTES:
        print("  ·", n)
    if FAILURES:
        print("\nREGRESSED:")
        for f in FAILURES:
            print("  ✗", f)
        return 1
    print("\nOK: the launch link discounts the flagship to 39/149 of its list price "
          "(US$39 of US$149), does not reach the second product, and the checkout "
          "offers the code field.")
    return 0


def _cleanup() -> None:
    """Kill our own Chrome so nothing is left holding the profile between ticks."""
    try:
        import sys as _sys
        _sys.path.insert(0, "/home/john-douglas/claimgate/scripts")
        import browser as _b
        for prof in (_b.GUMROAD_PROFILE, _b.BUYER_PROFILE):
            killed = _b.reap_orphans(prof)
            if killed:
                print(f"  · cleaned up {len(killed)} browser process(es) for {prof.rsplit('/', 1)[-1]}")
    except Exception:
        pass


if __name__ == "__main__":
    _rc = main()
    _cleanup()
    sys.exit(_rc)
