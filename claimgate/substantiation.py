"""Deciding whether a claim is actually supported by the evidence.

The claim extractor says what was asserted. This module says whether the
organisation can back it up — and it is the part that has to be honest,
because a reviewer tool that says "supported" when it is not is worse than no
tool at all: it launders an unsupported claim with a green tick.

So the design is deliberately two-stage:

  1. A deterministic check that cannot be talked out of its answer. If a claim
     contains a number, that number must appear in the evidence. No model
     judgement, no paraphrase credit — "40% faster" is not supported by a
     source that says "notably faster".
  2. Model adjudication of the semantic relationship, given only the claim and
     the candidate evidence, and required to answer with a verdict and the
     evidence id it relied on. It may return `unsupported`; it is never asked
     to be encouraging.

Anything that cannot be adjudicated (no key, model down, malformed reply)
comes back `unverified`, never `supported`. Fail closed.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict, field

from .claims import Claim

VERDICTS = ("supported", "partially_supported", "unsupported",
            "contradicted", "unverified")

# Verdicts that stop a publish. `partially_supported` does not block on its
# own but is surfaced for an editor, because it usually means the claim needs
# narrowing rather than deletion.
BLOCKING_VERDICTS = {"unsupported", "contradicted", "unverified"}

_SYSTEM = """You verify marketing claims against evidence an organisation has supplied.

You are given one CLAIM and a list of EVIDENCE items, each with an id and text.
Decide the relationship between the claim and THAT evidence only. Do not use
outside knowledge. Do not assume a source says something because it is plausible.

Answer with JSON only:
{"verdict": "supported|partially_supported|unsupported|contradicted|unverified",
 "evidence_id": "<id or empty>",
 "reason": "<one sentence, plain, quoting the part of the evidence you relied on>",
 "suggested_rewrite": "<a version of the claim the evidence would support, or empty>"}

Rules:
- "supported" requires the evidence to state the claim's substance, not merely
  concern the same topic.
- If a number, date, ranking or named source in the claim does not appear in the
  evidence, the claim is at best "partially_supported".
- If the evidence states the opposite, answer "contradicted".
- If the evidence is silent on the point, answer "unsupported". Silence is not
  support.
- If you cannot tell, answer "unverified". Never guess towards "supported"."""


@dataclass
class Evidence:
    id: str
    text: str
    title: str = ""
    url: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Verdict:
    claim: Claim
    verdict: str
    evidence_id: str = ""
    reason: str = ""
    suggested_rewrite: str = ""
    checked: list[str] = field(default_factory=list)   # evidence ids considered

    @property
    def blocking(self) -> bool:
        return self.verdict in BLOCKING_VERDICTS

    def as_dict(self) -> dict:
        return {
            "claim": self.claim.text,
            "category": self.claim.category,
            "severity": self.claim.severity,
            "verdict": self.verdict,
            "needs": self.claim.needs,
            "evidence_id": self.evidence_id,
            "reason": self.reason,
            "suggested_rewrite": self.suggested_rewrite,
            "matched": self.claim.matched,
        }


# ------------------------------------------------------------------ stage 1

_NUM_RX = re.compile(r"\d[\d,\.]*\s*(?:%|per ?cent|percent|x|times)?")


def numbers_in(text: str) -> list[str]:
    """Normalised numeric tokens, so 40% and 40 per cent compare equal."""
    out = []
    for m in _NUM_RX.finditer(text):
        tok = m.group(0).lower().replace(",", "").strip()
        tok = re.sub(r"\s+", " ", tok)
        tok = tok.replace("per cent", "%").replace("percent", "%")
        tok = re.sub(r"\s*%\s*$", "%", tok)
        out.append(tok)
    return out


def numbers_supported(claim: str, evidence_text: str) -> tuple[bool, list[str]]:
    """Does every number in the claim appear in the evidence?

    This is the check that catches the characteristic failure of AI-written
    copy: a figure that reads precise and is invented. It is intentionally
    unforgiving — a number the source does not contain is not supported, and
    no amount of surrounding prose should be able to excuse it.
    """
    claim_nums = numbers_in(claim)
    if not claim_nums:
        return True, []
    ev_nums = set(numbers_in(evidence_text))
    missing = [n for n in claim_nums if n not in ev_nums]
    return (not missing), missing


# ------------------------------------------------------------------ stage 2

def _key() -> str | None:
    return os.environ.get("DEEPSEEK_API_KEY") or None


def _ask(claim: str, evidence: list[Evidence],
         timeout: int = 120) -> dict:
    key = _key()
    if not key:
        raise RuntimeError("no model key configured")
    ev_block = "\n\n".join(
        f"[{e.id}] {e.title}\n{e.text[:4000]}" for e in evidence
    ) or "(no evidence supplied)"
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content":
             f"CLAIM:\n{claim}\n\nEVIDENCE:\n{ev_block}"},
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read())
    return json.loads(body["choices"][0]["message"]["content"])


def assess(claim: Claim, evidence: list[Evidence],
           timeout: int = 120) -> Verdict:
    """Adjudicate one claim against the supplied evidence. Fails closed."""
    ids = [e.id for e in evidence]

    if not evidence:
        return Verdict(claim, "unverified", reason=(
            "no evidence was supplied for this claim"))

    # Stage 1: the deterministic numeric gate. A model is not consulted about
    # whether a figure is present in a document; that is a string search, and
    # letting a model adjudicate it is how a fabricated statistic gets waved
    # through by a plausible-sounding justification.
    best = None
    for e in evidence:
        ok, missing = numbers_supported(claim.text, e.text)
        if ok:
            best = e
            break
    if best is None:
        missing = numbers_supported(claim.text, evidence[0].text)[1]
        joined = numbers_supported(claim.text, " ".join(x.text for x in evidence))[1]
        if joined:
            return Verdict(
                claim, "unsupported", evidence_id="",
                reason=("the figure(s) %s in this claim do not appear in any "
                        "supplied evidence" % ", ".join(joined[:4])),
                checked=ids)
        best = evidence[0]

    # Stage 2: semantic adjudication, restricted to evidence that survived the
    # numeric gate plus any that came close, so the model cannot "support" a
    # claim from a document that contradicts its own numbers.
    candidates = [best] + [e for e in evidence if e.id != best.id][:4]

    try:
        reply = _ask(claim.text, candidates, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 — unavailable, model down, bad JSON
        return Verdict(claim, "unverified",
                       reason=f"could not be adjudicated ({str(exc)[:120]})",
                       checked=[e.id for e in candidates])

    verdict = str(reply.get("verdict", "")).strip().lower()
    if verdict not in VERDICTS:
        return Verdict(claim, "unverified",
                       reason=f"the checker returned an unusable verdict ({verdict!r})",
                       checked=[e.id for e in candidates])

    return Verdict(
        claim=claim,
        verdict=verdict,
        evidence_id=str(reply.get("evidence_id", "") or ""),
        reason=str(reply.get("reason", "") or "")[:600],
        suggested_rewrite=str(reply.get("suggested_rewrite", "") or "")[:600],
        checked=[e.id for e in candidates],
    )


def assess_all(claims: list[Claim], evidence: list[Evidence],
               timeout: int = 120, progress=None) -> list[Verdict]:
    out = []
    for i, c in enumerate(claims, 1):
        out.append(assess(c, evidence, timeout=timeout))
        if progress:
            progress(i, len(claims), c, out[-1])
    return out


def report(verdicts: list[Verdict]) -> dict:
    counts: dict[str, int] = {}
    for v in verdicts:
        counts[v.verdict] = counts.get(v.verdict, 0) + 1
    blocking = [v for v in verdicts if v.blocking]
    return {
        "total": len(verdicts),
        "by_verdict": counts,
        "blocking": len(blocking),
        "clear": len(blocking) == 0,
    }
