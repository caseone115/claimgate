# Revenue

The only file that decides whether this is working. It is kept deliberately
blunt: no projections, no "pipeline", no dressed-up zero.

**TOTAL: $0.00**

---

## Why it is zero

No payout rail is connected. Every platform that can move money — Gumroad,
Stripe, PayPal, Lemon Squeezy — requires a verified legal identity and a bank
account behind the payouts. That is banking regulation, not a permission gate,
and no amount of building routes around it.

So the machine is built and waiting for one five-minute identity step. Until
then this file reports zero, because zero is the truth.

## What is actually built and verified

| Asset | State | Evidence |
|---|---|---|
| ClaimGate CLI | Working, 45/45 tests pass | `python tests/test_claimgate.py` |
| Landing page + pricing | Live | https://caseone115.github.io/claimgate/ |
| Source, MIT licensed | Public | https://github.com/caseone115/claimgate |
| Demo on a real bad draft | 16 claims found, 14 blocking, exits 1 | `examples/bad-draft.md` |

## The honest position on demand

Validated, not assumed — but validation is not revenue:

- EU AI Act Article 50 transparency obligations in force 2 Aug 2026
- Gartner: AI governance platform spend $492M in 2026, $1B+ by 2030
- 76% of enterprises require human review before AI creative publishes
- 12,842 AI-written articles removed for hallucinated content in one quarter
- No incumbent found that substantiates an individual claim against supplied
  evidence; detectors answer a different question and governance suites report
  after the fact

That is evidence that the problem is real and paid for. It is not evidence
that *this* product sells, and the difference matters.

## What would move this number

1. **A payout rail.** Blocked on the identity step. Nothing else can happen
   until this exists.
2. **Design partners.** Three agencies or marketing teams who will run the
   free tool on real copy and say whether it caught anything worth catching.
   This is the actual next step, and it needs no money.
3. **A first paying customer at $149/month.**

## Log

- 2026-09-29 — ClaimGate 0.1.0 built, tested (45/45), published, landing page
  live. Revenue: $0.00.
