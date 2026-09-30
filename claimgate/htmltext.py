"""Turn an HTML page into the text a reader actually sees.

Evidence is often a web page: a client's pricing page, a published policy, a
case study.  Handing the model the raw file is worse than useless -- most of an
HTML page is markup, CSS and JavaScript, and the model ends up judging a claim
against `{color:#333}` and a cookie-consent bundle.  In a rehearsal this made a
supplied pricing page read back to the checker as "page metadata and consent
scripts", so every claim on it was reported unsupported for the wrong reason.

This is deliberately deterministic: no parser, no dependency, no model.  It
removes what a reader never sees (script, style, noscript, template, svg,
iframe, comments), turns block boundaries into newlines so two sentences do not
run together, strips the remaining tags, unescapes entities, and drops the
blank lines that markup leaves behind.
"""
from __future__ import annotations

import html as _html
import re

# Elements whose *content* is never displayed text.
_HIDDEN = ("script", "style", "noscript", "template", "svg", "iframe",
           "head", "object", "canvas")

_BLOCK = ("p", "div", "br", "li", "ul", "ol", "tr", "td", "th", "table",
          "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "header",
          "footer", "nav", "aside", "main", "figure", "figcaption", "blockquote",
          "form", "label", "option", "dt", "dd", "dl", "tbody", "thead")

_WS = re.compile(r"[ \t\u00a0]+")
_BLANKS = re.compile(r"\n{2,}")


def to_text(raw: str) -> str:
    """Visible text of an HTML document, one block per line."""
    if not raw:
        return ""
    out = raw
    # comments first, so a commented-out <script> cannot survive the sweep
    out = re.sub(r"(?s)<!--.*?-->", " ", out)
    for tag in _HIDDEN:
        out = re.sub(r"(?is)<%s\b[^>]*>.*?</%s\s*>" % (tag, tag), " ", out)
        # a self-closed or unclosed <script .../> that never gets a close tag
        out = re.sub(r"(?is)<%s\b[^>]*/?>" % tag, " ", out)
    # block boundaries become newlines so lines stay separate sentences
    for tag in _BLOCK:
        out = re.sub(r"(?is)</?%s\b[^>]*>" % tag, "\n", out)
    out = re.sub(r"(?s)<[^>]+>", " ", out)
    out = _html.unescape(out)
    lines = []
    for line in out.split("\n"):
        line = _WS.sub(" ", line).strip()
        if line:
            lines.append(line)
    return _BLANKS.sub("\n", "\n".join(lines)).strip()


def looks_like_html(text: str) -> bool:
    """Cheap sniff, for cases where only the text is available."""
    if not text:
        return False
    head = text[:2000].lower()
    return ("<html" in head or "<!doctype" in head
            or ("<body" in head and "<" in head))
