"""The evidence loader must hand the checker what a reader sees, not markup.

Written after a rehearsal in which a real client's pricing page, supplied as
evidence, came back to the checker as "page metadata and consent scripts" -- so
every claim on it was reported unsupported for the wrong reason.  These tests
fail on the old behaviour (raw HTML passed through).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from claimgate.htmltext import to_text, looks_like_html        # noqa: E402
from claimgate.cli import _load_evidence                       # noqa: E402

results: list[tuple[str, bool, str]] = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        print(f"        {detail}")


PAGE = """<!doctype html>
<html><head>
  <title>Pricing - Acme</title>
  <style>.x{color:#333;font-size:14px}</style>
  <script>var consent={ad_storage:"denied",ua:"G-12345"};track();</script>
  <meta name="description" content="Prices for Acme services">
</head>
<body>
  <!-- <p>We are fully certified and 100% guaranteed.</p> -->
  <nav>Home Contact</nav>
  <h1>Our pricing</h1>
  <p>Local SEO from 198&euro;/month. No minimum term.</p>
  <li>Response time under 24 hours</li>
  <noscript>Please enable JavaScript for 99% uptime.</noscript>
  <svg><text>vector noise</text></svg>
  <footer>&copy; 2026 Acme S.L.</footer>
  <script>fbq('init');</script>
</body></html>"""


def test_visible_text_only() -> None:
    t = to_text(PAGE)
    ok("keeps the real pricing sentence", "Local SEO from 198" in t, t[:200])
    ok("unescapes entities", "\u20ac/month" in t, t)
    ok("keeps a list item", "Response time under 24 hours" in t, t)
    ok("drops <script> bodies", "ad_storage" not in t and "fbq" not in t, t)
    ok("drops <style> bodies", "font-size" not in t and "#333" not in t, t)
    ok("drops the commented-out claim",
       "fully certified" not in t and "100% guaranteed" not in t, t)
    ok("drops <noscript> fallback", "enable JavaScript" not in t, t)
    ok("drops inline <svg>", "vector noise" not in t, t)
    ok("drops the head metadata", "description" not in t, t)
    ok("no markup survives", "<" not in t and ">" not in t, t)
    ok("no CSS-ish residue", "{" not in t and "}" not in t, t)
    ok("no run-together lines", "\n" in t, repr(t))


def test_plain_text_is_untouched() -> None:
    t = to_text("Acme cut reconciliation from 22 hours to 9.\n\nSecond para.")
    ok("plain text preserved", "22 hours to 9" in t and "Second para." in t, t)


def test_evidence_loader_strips_html(tmp: Path = None) -> None:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "client_pricing.html"
        p.write_text(PAGE)
        (Path(d) / "notes.md").write_text("Internal note: 42 clients.")
        ev = {e.id: e for e in _load_evidence(Path(d))}
        ok("loader returns both files", set(ev) == {"client_pricing", "notes"},
           str(sorted(ev)))
        html_ev = ev["client_pricing"].text
        ok("loader strips scripts from .html", "ad_storage" not in html_ev, html_ev[:200])
        ok("loader keeps the page's own claim",
           "Local SEO from 198" in html_ev, html_ev[:200])
        ok("loader leaves .md alone", ev["notes"].text == "Internal note: 42 clients.",
           ev["notes"].text)


def test_a_page_with_no_visible_text_is_not_evidence() -> None:
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "empty.html").write_text(
            "<html><head><style>a{b:c}</style></head><body>"
            "<script>x()</script></body></html>")
        ev = _load_evidence(Path(d))
        ok("script/style-only page yields no evidence", ev == [], str(ev))


def test_sniff() -> None:
    ok("sniffs a full document", looks_like_html(PAGE))
    ok("does not sniff prose", not looks_like_html("Local SEO from 198 per month."))
    ok("does not sniff markdown", not looks_like_html("# Heading\n\nSome text."))


if __name__ == "__main__":
    for fn in (test_visible_text_only, test_plain_text_is_untouched,
               test_evidence_loader_strips_html,
               test_a_page_with_no_visible_text_is_not_evidence, test_sniff):
        print(f"\n{fn.__name__}")
        fn()
    bad = [n for n, ok_, _ in results if not ok_]
    print(f"\n{len(results) - len(bad)}/{len(results)} passed")
    if bad:
        print("FAILED: " + ", ".join(bad))
    raise SystemExit(1 if bad else 0)
