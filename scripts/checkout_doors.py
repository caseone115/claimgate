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

import datetime
import json
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
# Checks that could not be run because a session was missing. These are
# neither passes nor failures, and must be visible as their own thing.
UNVERIFIED: list[str] = []

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


# A browser that never started is NOT a change in the business. On 2026-10-01 two
# overlapping ticks each reaped the other live Chrome off the shared profile, and
# these doors printed hard REGRESSED findings against a shop that was working: the
# discount-code field switched off again, the discount scoped to all products again.
# Both were really: Chrome exited early (exit code: 21) ... SingletonLock: File exists.
# A probe that cannot see the page must say so - unknown, not changed - because a false
# regression on the paying path is how a true one gets ignored.
BROWSER_FAILED = (
    "Chrome exited early",
    "exited before providing DevTools URL",
    "DevToolsActivePort",
)


def _browser_measured(raw: str) -> bool:
    """False when the reply is a browser launch failure, not a page."""
    return not any(marker in raw for marker in BROWSER_FAILED)


BROWSER_DID_NOT_START = "the browser itself did not start, so this door is unknown, not changed."


def probe(url: str) -> tuple[list[str], list[str]]:
    buyer_page_open(url, "buyer2")
    raw = _unquote(ab("eval", PRICE_JS, profile=BUYER_PROFILE, session="buyer2"))
    left, _, right = raw.partition("||")
    struck = [s for s in left.split(";") if s.strip()]
    leaves = [s for s in right.split(";") if s.strip()]
    return struck, leaves


# --------------------------------------------------------------------------
# Our own product-page opens are recorded here, because they are not free.
#
# Measured 2026-10-01, by experiment rather than assumption:
#   * five real-browser opens of the logged-out buyer profile at one product
#     page moved Gumroad's own 30-day "Views" figure 401 -> 407;
#   * one run of this file moved it 407 -> 411;
#   * five plain (non-browser) fetches of the same page moved it 0.
# So only the browser opens count, and the source tag says which is which.
# Every view on the shop is attributed to "Direct, email, IM", none to search,
# so a figure this job quotes as demand is largely its own health check
# walking the shop. The counter cannot be reset; the honest number is
# (counter - our recorded browser opens).
# --------------------------------------------------------------------------
OUR_VIEWS = ROOT + "/claimgate/state/our_view_hits.jsonl"


def _note_our_view(url: str, source: str) -> None:
    try:
        with open(OUR_VIEWS, "a") as fh:
            fh.write(json.dumps({
                "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                "url": url, "source": source}) + "\n")
    except Exception:
        pass


def buyer_page_open(url: str, session: str, wait: float = 9.0) -> None:
    """Open a buyer-facing product page and own up to it."""
    _note_our_view(url, "browser:checkout_doors")
    ab("open", url, profile=BUYER_PROFILE, session=session)
    time.sleep(wait)


def main() -> int:
    if "--fixtures" in sys.argv:
        bad = 0
        for name, raw, want in CASES:
            got = _browser_measured(raw)
            ok = got == want
            bad += 0 if ok else 1
            print(name, "->", "PASS" if ok else "FAIL")
        print(str(len(CASES) - bad) + " passed, " + str(bad) + " failed")
        return 1 if bad else 0
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

    # Get in before reading door 3. Nothing did until 2026-10-01.
    import sys as _sys2
    _sys2.path.insert(0, ROOT + "/claimgate/state")
    import gum_login
    if not gum_login.ensure():
        UNVERIFIED.append("the Gumroad admin session could not be restored, so both checkout doors below are unknown, not changed.")
    # ---- door 3: checkout still offers the discount-code field
    ab("open", "https://gumroad.com/checkout/form", profile=ADMIN_PROFILE, session="gumroad")
    time.sleep(9)
    where = _unquote(ab("eval", r"document.title + ' | ' + location.href",
                        profile=ADMIN_PROFILE, session="gumroad"))
    # A logged-out session does not say the setting is off. It says we cannot see
    # it. Reporting that as "switched off again" is a false regression, and it is
    # exactly what this probe did on 2026-10-01 when the admin session expired.
    if not _browser_measured(where):
        UNVERIFIED.append(BROWSER_DID_NOT_START)
    elif "/login" in where or "Log in" in where:
        UNVERIFIED.append("the checkout's discount-code field could not be read: the Gumroad "
                          "admin session on this box has expired, so the probe is logged out. "
                          "The setting is unknown, not changed. Re-auth state/gumroad-profile "
                          "to restore this door.")
    else:
        radios = _unquote(ab("eval",
                    r"""Array.from(document.querySelectorAll('input[type=radio]')).slice(0,2)"""
                    r""".map(function(e){return e.checked;}).join(',')""",
                    profile=ADMIN_PROFILE, session="gumroad"))
        NOTES.append(f"checkout form radios (first two, checked): {radios}")
        if not _browser_measured(radios):
            UNVERIFIED.append(BROWSER_DID_NOT_START)
        elif not radios.startswith("true"):
            FAILURES.append("the discount-code field at checkout is switched off again — it must be "
                            f"'Only if a discount is available' — raw: {radios}")

    # ---- door 4: the discount still names the exclusion
    ab("open", "https://gumroad.com/checkout/discounts", profile=ADMIN_PROFILE, session="gumroad")
    time.sleep(8)
    where2 = _unquote(ab("eval", r"document.title + ' | ' + location.href",
                         profile=ADMIN_PROFILE, session="gumroad"))
    if not _browser_measured(where2):
        UNVERIFIED.append(BROWSER_DID_NOT_START)
    elif "/login" in where2 or "Log in" in where2:
        UNVERIFIED.append("the launch discount's exclusions could not be read: the Gumroad admin "
                          "session has expired. Unknown, not changed.")
    else:
        row = ab("eval",
                 r"""Array.from(document.querySelectorAll('tr')).map(function(t){"""
                 r"""return t.innerText.replace(/\s+/g,' ');}).join(' ')""",
                 profile=ADMIN_PROFILE, session="gumroad").strip()
        NOTES.append(f"discount row: {row[:220]}")
        if not _browser_measured(row):
            UNVERIFIED.append(BROWSER_DID_NOT_START)
        elif "except SimScan" not in row:
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
            _note_our_view(page_url, "fetch:checkout_doors")
            html = urllib.request.urlopen(page_url, timeout=30).read().decode()
        except Exception as exc:
            FAILURES.append(label + " could not be fetched: " + str(exc))
            continue
        if "pip install claimgate" in html and "git+" not in html:
            FAILURES.append(
                label + " tells a reader to run the bare pip install claimgate,"
                " which installs a different project")
        NOTES.append(label + " checked for the wrong install command")

    # ---- door 6: every live listing is actually PUBLISHED and still priced.
    # Added 2026-09-30 after an edit accidentally unpublished the second
    # product. It was off the storefront for a few minutes and NOTHING
    # noticed: door 1 and door 2 above still read a price off its page,
    # because Gumroad renders an unpublished product's page to the seller
    # while hiding it from buyers. A store that is invisible to strangers is
    # the most expensive failure there is, so it gets its own door.
    import json as _json
    import re as _re
    for label, page_url, want_cents in (("claimgate", URL_CG_PLAIN, 14900),
                                        ("simscan", URL_SS_PLAIN, 1400),
                                        ("starter kit", URL_KIT, 0)):
        try:
            _note_our_view(page_url, "fetch:checkout_doors")
            html = urllib.request.urlopen(page_url, timeout=30).read().decode()
        except Exception as exc:
            FAILURES.append(f"{label} listing could not be fetched: {exc}")
            continue
        m = _re.search(r'data-page="([^"]+)"', html, _re.S)
        if not m:
            FAILURES.append(f"{label} listing has no product payload — cannot read "
                            f"whether it is published")
            continue
        try:
            from html import unescape as _unesc
            prod = _json.loads(_unesc(m.group(1)))["props"]["product"]
        except Exception as exc:
            FAILURES.append(f"{label} listing payload could not be parsed: {exc}")
            continue
        if not prod.get("is_published"):
            FAILURES.append(f"{label} listing is NOT PUBLISHED — it is off the "
                            f"storefront and no stranger can buy it ({page_url})")
        got = prod.get("price_cents")
        if want_cents is not None and got != want_cents:
            FAILURES.append(f"{label} listing price is {got} cents, expected "
                            f"{want_cents} — the price moved")
        NOTES.append(f"{label}: published={prod.get('is_published')} "
                     f"price_cents={got}")

    print("checkout doors probe")
    for n in NOTES:
        print("  ·", n)
    if UNVERIFIED:
        print("\nCOULD NOT BE VERIFIED (not a pass, not a regression):")
        for u in UNVERIFIED:
            print("  ?", u)
    if FAILURES:
        print("\nREGRESSED:")
        for f in FAILURES:
            print("  ✗", f)
        return 1
    if UNVERIFIED:
        print("\nPARTIAL: the doors above are green; the unverified ones are unknown, not fine.")
        return 0
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




# ---------------------------------------------------------------------------
# Fixtures: the rule above, driven over the exact text this project really got.
# The failure case is not invented - it is the reply an overlapping tick produced
# on 2026-10-01 17:34, which was printed as two hard business regressions.
# ---------------------------------------------------------------------------
REAL_BROWSER_FAILURE = (
    "Chrome exited early (exit code: 21) without writing DevToolsActivePort\\n"
    "(also tried parsing stderr) Chrome exited before providing DevTools URL\\n"
    "Chrome stderr:\\n"
    "  [691963:691963:1001/173438.462290:ERROR:chrome/browser/process_singleton_posix.cc:347] "
    "Failed to create /home/john-douglas/claimgate/state/gumroad-profile/SingletonLock: File exists (17)"
)



CASES = (
    ("a checkout form that was really read is a measurement",
     "checkout form radios (first two, checked): true,false", True),
    ("the real exit-21 launch failure is NOT a measurement",
     REAL_BROWSER_FAILURE, False),
    ("a discount row that was really read is a measurement",
     "Discount Revenue Uses Term Status LAUNCH39 Launch price $110 off of all products", True),
    ("a login redirect is a measurement - the page really loaded",
     "Log in to Gumroad | https://gumroad.com/login", True),
    ("an empty reply is a measurement of an empty page, not a dead browser",
     "", True),
    ("the older stderr-only shape of the same failure is not a measurement",
     "Chrome exited before providing DevTools URL", False),
)
if __name__ == "__main__":
    _rc = main()
    _cleanup()
    sys.exit(_rc)
