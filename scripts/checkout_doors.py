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


def _unquote(raw: str) -> str:
    """agent-browser quotes its eval payload; strip that one layer only."""
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"') and len(raw) > 1:
        raw = raw[1:-1]
    return raw.replace("\\n", "\n")


def ab(*args, profile: str, session: str, timeout: int = 300) -> str:
    cmd = ["node", AB, "--profile", profile, "--session", session, "--args", FLAGS]
    cmd += [str(a) for a in args]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    out = (p.stdout or "") + (p.stderr or "")
    return "\n".join(ln for ln in out.splitlines() if not ln.startswith("⚠"))


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
    elif not any(l.endswith("55.89") or l.endswith("55.83") for l in leaves):
        FAILURES.append("claimgate/LAUNCH39 shows a struck price but not the ~A$55.9 launch "
                        f"price — prices seen {leaves}")

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

    print("checkout doors probe")
    for n in NOTES:
        print("  ·", n)
    if FAILURES:
        print("\nREGRESSED:")
        for f in FAILURES:
            print("  ✗", f)
        return 1
    print("\nOK: the launch link discounts the flagship to ~A$55.9, does not reach the "
          "second product, and the checkout offers the code field.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
