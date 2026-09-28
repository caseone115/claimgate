"""Finding the claims in a piece of content.

The product's premise is that "no source, no claim" should be mechanical
rather than a matter of an editor's attention. That only works if the claims
can be extracted reliably first, so this module deliberately does the boring,
decidable part with patterns and sentence structure, and leaves the
judgement — is this claim actually supported? — to the layer above.

A claim is a sentence, or a fragment of one, that asserts something a reader
could check: a number, a date, a superlative, a comparison, a guarantee, a
causal statement. Marketing copy is dense with these and, crucially, the ones
that hurt are almost always the specific ones — a statistic, a percentage, a
"clinically proven", a "#1".

Design rules:
  - never invent a claim that is not in the text;
  - keep the exact source span, so an editor can see it in context;
  - classify by *why* it is risky, not just that it is, because the fix
    differs: a statistic needs a source, a superlative needs a substantiation
    file, an absolute needs rewording.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Iterable

# ---------------------------------------------------------------- taxonomy

# Categories are ordered by how often they cause real trouble in practice.
# `needs` says what a human must produce to clear the claim, which is what
# makes the finding actionable instead of just alarming.
CATEGORIES: dict[str, dict] = {
    "statistic": {
        "needs": "a primary source for the figure",
        "why": "a number with no source cannot be checked by anyone",
    },
    "percentage": {
        "needs": "the study or dataset the percentage comes from",
        "why": "percentages are the most commonly fabricated figure in marketing copy",
    },
    "superlative": {
        "needs": "evidence of the ranking, with the population and date",
        "why": "'best'/'#1' claims are regulated advertising claims in most markets",
    },
    "comparative": {
        "needs": "the comparison basis and the competitor evidence",
        "why": "comparative claims invite competitor challenge and regulator scrutiny",
    },
    "guarantee": {
        "needs": "the terms behind the guarantee, and legal sign-off",
        "why": "guarantees create enforceable expectations",
    },
    "efficacy": {
        "needs": "clinical or technical substantiation",
        "why": "health and performance claims are the most heavily regulated",
    },
    "temporal": {
        "needs": "confirmation the fact is still current",
        "why": "AI drafts assert dated facts as though they were present-tense",
    },
    "attribution": {
        "needs": "the named source's actual words",
        "why": "a fabricated quote or attribution is the highest-severity failure",
    },
    "absolute": {
        "needs": "reworded, or proof of the absolute",
        "why": "'always'/'never'/'guaranteed' claims are almost never true as written",
    },
    "causal": {
        "needs": "evidence of the causal link, not just correlation",
        "why": "AI drafts routinely state correlation as causation",
    },
}

RISK_ORDER = ["attribution", "efficacy", "guarantee", "percentage", "statistic",
              "superlative", "comparative", "absolute", "temporal", "causal"]

# A claim whose category is in here blocks publication outright.
BLOCKING = {"attribution", "efficacy", "guarantee"}


@dataclass
class Claim:
    text: str                 # the exact sentence or fragment, as written
    category: str
    start: int                # character offsets into the source document
    end: int
    matched: list[str] = field(default_factory=list)   # the trigger phrases
    severity: str = "medium"

    @property
    def needs(self) -> str:
        return CATEGORIES.get(self.category, {}).get("needs", "substantiation")

    def as_dict(self) -> dict:
        d = asdict(self)
        d["needs"] = self.needs
        return d


# ---------------------------------------------------------------- patterns

_NUM = r"\d[\d,\.]*"
_PCT = rf"{_NUM}\s*(?:%|per ?cent|percent)"

_PATTERNS: list[tuple[str, str]] = [
    # Highest-severity first: a fabricated quote is a retraction-class event.
    ("attribution", r"\b(?:according to|as (?:stated|confirmed|noted|reported) "
                    r"by|research(?:ers)? (?:at|from) [\w\s]+ (?:found|showed|"
                    r"reported)|(?:studies|a study|reports?) (?:show|shows|"
                    r"found|suggest|suggests)|experts? (?:say|agree|believe))\b"),
    ("efficacy", r"\b(?:clinically|scientifically|medically|independently)? ?"
                 r"(?:proven|tested|verified)\b|\b(?:reduces?|increases?|"
                 r"improves?|eliminates?|cures?|prevents?|boosts?|restores?)"
                 r"\b[^.]{0,60}?\b(?:by|up to|as much as)\b"),
    ("guarantee", r"\b(?:guarantee[ds]?|money[- ]back|risk[- ]free|"
                  r"we promise|no[- ]risk|assured?)\b"),
    ("percentage", _PCT),
    ("statistic", rf"\b{_NUM}\s*(?:x|times|fold|hours?|days?|weeks?|months?|"
                  rf"years?|users?|customers?|clients?|companies|businesses|"
                  rf"projects?|million|billion|thousand|k\b)\b"
                  rf"|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|"
                  rf"dozens?|hundreds?|thousands?|millions?|billions?) (?:of )?"
                  rf"(?:users?|customers?|clients?|companies|businesses|"
                  rf"people|hours?|projects?)\b"),
    ("superlative", r"\b(?:#1|number one|no\. ?1|world[- ]class|world[- ]leading|"
                    r"industry[- ]leading|market[- ]leading|best[- ]in[- ]class|"
                    r"the (?:best|fastest|cheapest|largest|leading|most "
                    r"(?:advanced|accurate|popular|trusted|secure|reliable)))\b"),
    ("comparative", r"\b(?:better than|faster than|cheaper than|more "
                    r"(?:accurate|effective|reliable|secure) than|"
                    r"outperforms?|unlike (?:our )?(?:competitors|others)|"
                    r"compared (?:to|with) (?:other|the market|competitors))\b"),
    ("absolute", r"\b(?:always|never|guaranteed|100%|every(?:one|body)?\b|"
                 r"all (?:of )?(?:our )?(?:customers|users|clients)|"
                 r"no one|nothing else|completely|totally|instantly|"
                 r"overnight)\b"),
    ("temporal", r"\b(?:recent(?:ly)?|last year|this year|currently|now|today|"
                 r"in 20\d\d|as of \d|new(?:ly)? (?:released|launched)|"
                 r"latest|upcoming|soon)\b"),
    ("causal", r"\b(?:causes?|leads? to|results? in|because of|due to|"
               r"drives?|makes? you|so you can|which means)\b"),
]

_COMPILED = [(cat, re.compile(pat, re.I)) for cat, pat in _PATTERNS]

# Sentence splitting that survives marketing punctuation: "Save 40%! No
# really." should not become one claim, and "e.g." should not split.
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def sentences(text: str) -> list[tuple[str, int]]:
    """Split into (sentence, offset) pairs, preserving the original text."""
    out: list[tuple[str, int]] = []
    pos = 0
    # Bullets and headings are claims too, and they carry no full stop.
    for raw in re.split(r"(\n+|(?<=[.!?])\s+)", text):
        if not raw or raw.isspace():
            continue
        stripped = raw.strip()
        if not stripped:
            continue
        idx = text.find(stripped, pos)
        if idx < 0:
            idx = pos
        out.append((stripped, idx))
        pos = idx + len(stripped)
    return out


def extract(text: str, include: Iterable[str] | None = None) -> list[Claim]:
    """Every claim in `text`, deduplicated, worst-first.

    `include` restricts to given categories, for callers that only care about
    one kind of risk (a legal-only pass, say).
    """
    wanted = set(include) if include else None
    claims: list[Claim] = []
    seen: set[tuple[str, str]] = set()

    for sentence, offset in sentences(text):
        # A long sentence can carry several distinct risks; each is its own
        # finding, because each needs its own substantiation.
        for cat, rx in _COMPILED:
            if wanted and cat not in wanted:
                continue
            hits = [m.group(0).strip() for m in rx.finditer(sentence)]
            if not hits:
                continue
            key = (sentence.lower(), cat)
            if key in seen:
                continue
            seen.add(key)
            claims.append(Claim(
                text=sentence,
                category=cat,
                start=offset,
                end=offset + len(sentence),
                matched=hits,
                severity=_severity(cat, hits, sentence),
            ))
    claims.sort(key=lambda c: (RISK_ORDER.index(c.category)
                               if c.category in RISK_ORDER else 99,
                               c.start))
    return claims


def _severity(cat: str, hits: list[str], sentence: str) -> str:
    """Severity is about consequence, not confidence.

    A fabricated statistic is embarrassing. A fabricated clinical claim or a
    quote attributed to a named source is a regulatory or legal event, so
    those are 'high' regardless of how hedged the sentence looks.
    """
    if cat in ("attribution", "efficacy", "guarantee"):
        return "high"
    if cat in ("percentage", "superlative") and re.search(
            r"\b(?:clinically|medically|scientifically|safety|health)\b",
            sentence, re.I):
        return "high"
    if cat in ("percentage", "statistic", "superlative", "comparative"):
        return "medium"
    return "low"


def summarise(claims: list[Claim]) -> dict:
    by_cat: dict[str, int] = {}
    for c in claims:
        by_cat[c.category] = by_cat.get(c.category, 0) + 1
    return {
        "total": len(claims),
        "by_category": by_cat,
        "blocking": sum(1 for c in claims if c.category in BLOCKING),
        "high": sum(1 for c in claims if c.severity == "high"),
    }
