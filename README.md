# ClaimGate

**A publish gate for AI-assisted marketing content.**

Point it at the copy you are about to publish and the evidence your
organisation actually holds. It tells you which claims you cannot
substantiate, which of your own policy rules you are breaking, and whether the
asset is missing a disclosure the law now requires.

Exit code `1` means blocked. That makes it usable in CI, a pre-commit hook, or
a publishing pipeline — which is where a gate stops mistakes instead of
documenting them afterwards.

```console
$ claimgate check campaign.md --evidence substantiation/ --policy policy.json

Claims requiring substantiation (14)
  ✗ [attribution] According to research at a leading university, 94% of finance teams waste more
      unsupported: the figure(s) 94% in this claim do not appear in any supplied evidence
  ✗ [statistic] thousands of businesses, and we are fully ISO 27001 certified.
      contradicted: evidence states "Acme Invoicing is not certified under ISO 27001"
  ~ [statistic] Meridian Freight cut their reconciliation time from 22 hours to 9 hours a week
      partially_supported: the case study confirms 22 hours and 9 hours, but not "always"
      try: Meridian Freight's finance team reduced reconciliation from 22 hours a week to 9

Policy findings (3)
  ✗ [prohibited] guaranteed
      absolute guarantees are unenforceable and are treated as misleading advertising
  ✗ [disclosure] AI disclosure missing
      required under EU AI Act Article 50 (in force 2 Aug 2026) and platform labelling rules

BLOCKED — 14 unsupported claim(s), 3 blocking policy finding(s).
```

## Why this exists

Generative AI is now how a large share of marketing copy gets written, and the
controls did not scale with it. The recurring finding across 2025–2026 is not
that models are bad at writing. It is that a reviewer cannot tell a
hallucinated statistic from a real one — there is no grammatical signal that
separates them — so hallucinated content passes a casual read. Organisations
that scaled AI content without a review gate did not reduce their content
risk, they accelerated it.

The existing tools do not close this. Detectors tell you a text *was*
AI-written, which is not the question. Generators produce more copy. Governance
platforms tell you at the end of the quarter that you had incidents.

ClaimGate answers the question that actually decides whether an asset can
ship: **can this specific claim be traced to something we can point at?**

## The three checks

**1. Substantiation.** Every checkable claim in the draft is extracted, then
adjudicated against your evidence. The important part is how:

- A number in a claim must appear in the evidence. That is a string search,
  not a judgement call, and no model gets to overrule it. A fabricated
  statistic cannot be talked into a pass.
- Semantic support is decided by a model given *only* the claim and the
  evidence, required to name the evidence it relied on, and allowed to answer
  `unsupported` or `unverified`.
- If the model is unavailable, the key is missing, or the reply is malformed,
  the verdict is `unverified` — which blocks. It never fails towards
  "supported".

**2. Policy.** Your prohibited and restricted claims, written down once and
enforced on every draft: guarantees, medical and financial claims, unsourced
superlatives, named competitors, personal data.

**3. Disclosure.** From 2 August 2026 the EU AI Act (Article 50) requires
disclosure of AI-generated content in specified circumstances, and Meta,
TikTok and Google each require an AI label on realistic synthetic media in
ads. A customer-facing AI-assisted asset with no disclosure is
non-compliant however good the copy is — so it is checked as a property of the
draft, not left to whoever uploads it.

## Install

No dependencies. Python 3.9+.

```bash
pip install claimgate        # or: pip install -e . from a checkout
```

## Use

```bash
claimgate init-policy policy.json          # a starter policy to edit
claimgate claims draft.md                  # just list the claims
claimgate check draft.md --evidence ./evidence/
claimgate check draft.md --evidence evidence.json --policy policy.json --json
claimgate check draft.md --no-model        # facts and policy only, no API calls
```

Evidence is any directory of `.txt`/`.md`/`.html` files, or a JSON array:

```json
[{"id": "spec", "title": "Product spec", "text": "..."},
 {"id": "case-1", "title": "Meridian case study", "url": "..."}]
```

Set `DEEPSEEK_API_KEY` for adjudication. Without it, `--no-model` still runs
the deterministic checks — which is where the fabricated-figure guarantee
lives.

## What this is not

- **Not a fact-checker.** It does not search the web or decide what is true.
  It decides whether *you* can substantiate what you wrote, against evidence
  *you* supply. That is the question a compliance review actually asks, and it
  is the only one answerable without pretending to authority the tool does not
  have.
- **Not a detector.** It does not guess whether a text was AI-written.
- **Not a lawyer.** It enforces the policy you write. It flags where AI
  disclosure obligations appear to apply; it does not give legal advice.

## Tests

```bash
python tests/test_claimgate.py     # 45 checks
```

The suite is written against the product's promises, not its implementation:
that no claim is invented, that a number absent from the evidence is never
reported as supported, that anything uncheckable blocks, and that the same
input always gives the same answer.

## Licence

MIT.
