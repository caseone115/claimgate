"""Tests for ClaimGate.

These are written against the guarantees the product makes, not against its
implementation. The guarantees are:

  1. Every claim in a draft is found, and no claim is invented.
  2. A number in a claim that is absent from the evidence is never reported as
     supported — regardless of what any model says.
  3. Anything that cannot be checked comes back unverified, never supported.
  4. A prohibited claim, or a missing legally-required disclosure, blocks.
  5. The gate is deterministic: the same input gives the same answer.

    python -m pytest tests/ -q      (or: python tests/test_claimgate.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from claimgate import Policy, Evidence, extract, summarise  # noqa: E402
from claimgate.policy import check_policy, PolicyFinding  # noqa: E402
from claimgate.substantiation import (numbers_supported, numbers_in,  # noqa: E402
                                      assess)

results: list[tuple[str, bool, str]] = []


def check(name: str, got, want) -> None:
    ok = got == want
    results.append((name, ok, f"got {got!r}, wanted {want!r}"))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print(f"        got {got!r}, wanted {want!r}")


def ok(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond and detail:
        print(f"        {detail}")


# ------------------------------------------------------------- extraction

def test_extraction() -> None:
    print("\n=== 1. claim extraction ===\n")
    text = ("We save teams 40% of processing time. "
            "Acme is the best platform in the industry. "
            "According to a study, 92% of teams agree. "
            "The weather was pleasant.")
    claims = extract(text)
    cats = {c.category for c in claims}
    ok("finds the percentage claim", "percentage" in cats, str(cats))
    ok("finds the superlative claim", "superlative" in cats, str(cats))
    ok("finds the unsourced attribution", "attribution" in cats, str(cats))
    ok("does not invent a claim from a neutral sentence",
       not any("pleasant" in c.text for c in claims))

    ok("keeps exact source offsets",
       all(text[c.start:c.end] == c.text for c in claims),
       "offsets do not round-trip")

    ok("never returns an empty claim text",
       all(c.text.strip() for c in claims))

    # Idempotence: a claim must not appear twice for the same category.
    pairs = [(c.text, c.category) for c in claims]
    check("no duplicate (text, category) findings", len(pairs), len(set(pairs)))

    s = summarise(claims)
    ok("summary counts match", s["total"] == len(claims))
    ok("attribution is counted as blocking", s["blocking"] >= 1, str(s))


def test_extraction_categories() -> None:
    print("\n=== 2. risk taxonomy ===\n")
    cases = {
        "guarantee": "We guarantee a full refund.",
        "efficacy": "This is clinically proven to reduce pain.",
        "comparative": "We are faster than every other tool.",
        "absolute": "You will always get instant results.",
        "temporal": "Our new release shipped last year.",
        "causal": "This causes a 30% lift in conversion.",
    }
    for cat, sentence in cases.items():
        got = {c.category for c in extract(sentence)}
        ok(f"{cat!r} detected in {sentence[:40]!r}", cat in got, str(got))


# ------------------------------------------------------- numeric guarantee

def test_number_gate() -> None:
    print("\n=== 3. the numeric guarantee ===\n")
    ok("extracts 40%", numbers_in("save 40% of time") == ["40%"],
       str(numbers_in("save 40% of time")))
    ok("normalises '40 per cent'", numbers_in("save 40 per cent") == ["40%"],
       str(numbers_in("save 40 per cent")))
    ok("normalises '40 percent'", numbers_in("save 40 percent") == ["40%"])

    ok("absent number is not supported",
       numbers_supported("save 60% of time",
                         "the product saves time") == (False, ["60%"]))
    ok("present number is supported",
       numbers_supported("save 40% of time",
                         "customers save 40% of processing time") == (True, []))
    ok("a different number does not satisfy it",
       numbers_supported("save 60%", "customers save 40%") == (False, ["60%"]))

    # The central promise: an invented figure is blocked even with no model.
    claim_text = "According to research, 94% of teams waste time."
    ev = [Evidence(id="e1", text="Teams waste time on reconciliation.")]
    c = extract(claim_text)[0]
    v = assess(c, ev, timeout=5)
    check("fabricated statistic is unsupported, not unverified",
          v.verdict, "unsupported")
    ok("and it is blocking", v.blocking)


def test_fails_closed() -> None:
    print("\n=== 4. fail-closed behaviour ===\n")
    c = extract("We save teams 40% of the time.")[0]

    v = assess(c, [], timeout=5)
    check("no evidence -> unverified", v.verdict, "unverified")
    ok("unverified is blocking", v.blocking)

    # A model that cannot be reached must not produce a pass.
    import os
    saved = os.environ.pop("DEEPSEEK_API_KEY", None)
    try:
        ev = [Evidence(id="e1", text="Teams save 40% of the time on this task.")]
        v = assess(c, ev, timeout=5)
        check("model unavailable -> unverified", v.verdict, "unverified")
        ok("unavailable model is blocking", v.blocking)
    finally:
        if saved:
            os.environ["DEEPSEEK_API_KEY"] = saved


# ------------------------------------------------------------- policy

def test_policy() -> None:
    print("\n=== 5. policy enforcement ===\n")
    p = Policy()

    f = check_policy("We guarantee 100% uptime for every customer.", p)
    ids = {x.rule_id for x in f}
    ok("prohibited guarantee blocks", "no-guarantee" in ids, str(ids))
    ok("prohibited findings are blocking",
       any(x.blocking for x in f if x.rule_id == "no-guarantee"))

    f = check_policy("Our competitor is worse.", p)
    ok("naming a competitor is restricted, not prohibited",
       all(not x.blocking for x in f if x.kind == "restricted"))

    f = check_policy("This treatment cures disease.", p)
    ids = {x.rule_id for x in f}
    ok("medical claim blocks", "no-medical" in ids, str(ids))


def test_disclosure() -> None:
    print("\n=== 6. AI disclosure (EU AI Act Art. 50) ===\n")
    p = Policy(ai_assisted=True, customer_facing=True, jurisdictions=["EU"])
    ok("disclosure is required for an EU AI-assisted asset",
       p.disclosure_required)

    f = check_policy("A perfectly ordinary sentence about our product.", p)
    ok("missing disclosure is flagged",
       any(x.rule_id == "ai-disclosure" for x in f), str([x.rule_id for x in f]))
    ok("and it blocks", any(x.rule_id == "ai-disclosure" and x.blocking
                            for x in f))

    f = check_policy("This copy is AI-assisted. A sentence about our product.", p)
    ok("present disclosure clears it",
       not any(x.rule_id == "ai-disclosure" for x in f))

    p2 = Policy(ai_assisted=False, customer_facing=True, jurisdictions=["EU"])
    ok("no disclosure needed for human-written copy", not p2.disclosure_required)

    p3 = Policy(ai_assisted=True, customer_facing=False, jurisdictions=["EU"])
    ok("internal drafts are not customer-facing",
       not p3.disclosure_required)


def test_policy_roundtrip(tmp: Path) -> None:
    print("\n=== 7. a customer's own policy ===\n")
    p = Policy(name="acme", jurisdictions=["AU"], ai_assisted=False,
               required_terms=["Terms apply"])
    p.save(tmp)
    q = Policy.load(tmp)
    check("name survives", q.name, "acme")
    check("jurisdictions survive", q.jurisdictions, ["AU"])
    ok("custom rules survive", any(r.id == "no-guarantee" for r in q.rules))

    f = check_policy("Buy now.", q)
    ok("a required term is enforced",
       any(x.rule_id == "required:Terms apply" for x in f),
       str([x.rule_id for x in f]))


# ----------------------------------------------------------- determinism

def test_determinism() -> None:
    print("\n=== 8. determinism ===\n")
    text = ("We save 40% of time. According to research, 94% of teams agree. "
            "Acme is the best. We guarantee it.")
    a = [(c.text, c.category, c.severity, c.start) for c in extract(text)]
    b = [(c.text, c.category, c.severity, c.start) for c in extract(text)]
    check("same input, same findings", a, b)

    ok("findings are ordered worst-first",
       [c.category for c in extract(text)][0] in
       ("attribution", "efficacy", "guarantee"),
       str([c.category for c in extract(text)]))


def test_clean_copy_passes() -> None:
    print("\n=== 9. good copy is not blocked ===\n")
    good = ("Acme Invoicing reconciles invoices against bank statements. "
            "On an internal benchmark of 1,200 invoices it reconciled 87 per "
            "cent of line items without manual intervention. Setup takes an "
            "average of 45 minutes.")
    p = Policy(ai_assisted=False)
    claims = extract(good)
    findings = check_policy(good, p)
    ok("no prohibited policy findings",
       not [x for x in findings if x.blocking],
       str([x.rule_id for x in findings]))
    ok("claims are extracted but none are fabricated-category",
       not [c for c in claims if c.category in
            ("attribution", "efficacy", "guarantee")],
       str([c.category for c in claims]))


def main() -> int:
    import tempfile
    test_extraction()
    test_extraction_categories()
    test_number_gate()
    test_fails_closed()
    test_policy()
    test_disclosure()
    with tempfile.TemporaryDirectory() as d:
        test_policy_roundtrip(Path(d) / "policy.json")
    test_determinism()
    test_clean_copy_passes()

    passed = sum(1 for _, ok_, _ in results if ok_)
    total = len(results)
    print(f"\n{passed}/{total} checks behaved as intended")
    for name, ok_, detail in results:
        if not ok_:
            print(f"  FAILED: {name} — {detail}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
