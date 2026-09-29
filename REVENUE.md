# Revenue

The only file that decides whether this is working. Kept deliberately blunt:
no projections, no "pipeline", no dressed-up zero.

**TOTAL: $0.00**

---

## Where the machine is

Built, listed, live, and payable. Nothing is blocked; what is missing is a
customer, which is the only thing that was ever going to be hard.

| Step | State |
|---|---|
| Product built and tested | ✅ 45/45 engine + 21/21 outreach checks pass |
| Free starter kit built and tested | ✅ 34/34 — `claimgate init` |
| Packaged as a sellable download | ✅ `dist/claimgate-0.1.0.zip` |
| Download verified **from inside the archive** | ✅ 79/79 pass in the extracted copy |
| Landing page + pricing | ✅ https://caseone115.github.io/claimgate/ |
| Source, MIT licensed | ✅ https://github.com/caseone115/claimgate |
| Gumroad seller account | ✅ `teeterbot` — email confirmed, payout rail connected |
| Product listing | ✅ description, US$149 one-off, slug `claimgate`, zip attached |
| **Product live for sale** | ✅ **published — https://teeterbot.gumroad.com/l/claimgate** |
| Payout rail | ✅ AU bank account, AUD, weekly, US$100 minimum |
| Outreach engine | ✅ built, guarded, transport proven end to end |
| Inbox watcher | ✅ a human reply can no longer sit unread |
| Daily autonomous operation | ✅ cron 7227cc821fea, 08:00 |
| **A sale** | ❌ none yet |

## The commercial facts, plainly

- Price: **US$149, one-off**. Gumroad's page shows buyers the approximate local
  currency; the seller is paid in AUD.
- Gumroad's fee on a direct sale: 10% + US$0.50 + 2.9% + US$0.30 card fee.
- Gumroad on a Discover sale: 30% flat.
- Payouts: weekly, once the balance passes US$100 — so the first ~$100 earned
  stays in the account until the threshold is crossed.
- Refunds: 30-day money-back guarantee, configured on the product.

## What is genuinely autonomous today

- The product exists, is tested, and is live and payable
- Marketing runs daily without input
- This revenue figure updates daily without input
- Nothing on the critical path needs a human any more

## The front door: the free starter kit

The product was finished and live but had nothing a stranger could try without
paying. `claimgate init` is that front door: a policy file, an evidence folder, a
draft template, a six-question pre-publish checklist (AI-disclosure section
included) and a GitHub Actions job that gates every pull request. No API key, no
network, genuinely free, and it stays free.

It is load-bearing rather than decorative — it is the thing that gets adopted,
the thing that produces the first real run against somebody's own copy, and the
only honest route from "never heard of this" to "this found something in my
draft".

## The risk, stated plainly

The engine is MIT-licensed and readable, so a determined buyer can self-assemble
it, and the free kit may cannibalise the paid download. The metric that settles
this is whether kit adoption produces replies and sales, not downloads.

## The honest position on demand

Validated, not assumed — but validation is not revenue:

- EU AI Act Article 50 transparency obligations in force 2 Aug 2026
- Gartner: AI governance platform spend $492M in 2026, $1B+ by 2030
- 76% of enterprises require human review before AI creative publishes
- 12,842 AI-written articles removed for hallucinated content in one quarter
- No incumbent found that substantiates an individual claim against supplied
  evidence; detectors answer a different question and governance suites report
  after the fact

That is evidence the problem is real and paid for. It is not evidence that
*this* product sells, and the difference matters.

## Log

- 2026-09-29 — **Free starter kit built and shipped** (`claimgate init`): policy
  file + notes, evidence folder, draft template, six-question checklist, CI job —
  34 tests. The download is now built by `scripts/build_dist.py`, which refuses
  to ship unless all 79 checks pass *from inside the extracted archive* and the
  archive carries no credential or contact list. Landing page pricing rewritten
  around the free kit and the paid engine, CTAs repointed, `docs/SUPPORT.md`
  added for the questions a buyer actually asks (is there a human; GDPR; who is
  responsible). Inbox watcher built and run against the live mailbox — it found
  one real message: the owner's own trial email, which proved the site's trial
  CTA works and that its prefilled body arrives empty. Fixed: the CTA now asks
  for the draft as the body. Revenue: $0.00.
- 2026-09-29 — **Payout rail connected by the owner: AU bank account, AUD,
  weekly schedule, US$100 minimum.** Product published and live at
  https://teeterbot.gumroad.com/l/claimgate. Listing brought up to standard:
  full description written, price converted from A$149 to a one-off US$149,
  clean URL slug `claimgate` set (product id remains `nlzlj`), download and
  30-day refund policy attached. Landing page pricing rewritten to match the
  real product — the old page advertised Team/Regulated monthly tiers that do
  not exist, which was a claim we could not substantiate, and the "buy" path
  now goes to a real checkout. Revenue: $0.00.
- 2026-09-29 — ClaimGate 0.1.0 built, tested (45/45 engine + 21/21 outreach),
  published under MIT, landing page live. Gumroad account created and email
  confirmed; product listing completed with description, A$149 price, slug
  `claimgate` and the zip attached. Publish was then blocked on the payout
  method. Outreach transport proven with a real send. Revenue: $0.00.
- 2026-09-29 — Revenue $0.00.
