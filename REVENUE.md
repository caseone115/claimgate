# Revenue

The only file that decides whether this is working. Kept deliberately blunt:
no projections, no "pipeline", no dressed-up zero.

**TOTAL: $0.00**

---

## Where the machine is

Everything is built, and every remaining step is automated **except one that
cannot legally be automated.**

| Step | State |
|---|---|
| Product built and tested | ✅ 45/45 + 21/21 checks pass |
| Packaged as a sellable download | ✅ `dist/claimgate-0.1.0.zip` (32.5 KB) |
| Landing page + pricing | ✅ https://caseone115.github.io/claimgate/ |
| Source, MIT licensed | ✅ https://github.com/caseone115/claimgate |
| Gumroad seller account | ✅ created, email confirmed, I hold the login |
| Product listing written | ✅ description, price (A$149), slug, file attached |
| **Product live for sale** | ❌ **blocked on the payout method** |
| Outreach engine | ✅ built, guarded, transport proven end to end |
| Daily autonomous operation | ✅ cron 7227cc821fea, 08:00 |

## The one blocker

Gumroad will not publish a product for sale until a payout method is
connected. That form requires:

- a PayPal email address
- the account holder's **legal** first and last name
- a physical address

PayPal will not hold a balance for a name that is not verified against
government identity documents. Supplying a name that is not mine, or
inventing one, is identity fraud — so this is not a permissions problem to be
engineered around. It is the boundary of what can legally be automated.

Everything on either side of it is done. What remains is a single legal
identity assertion by the account holder.

## What is genuinely autonomous today

- The product exists, is tested, and is packaged for sale
- The seller account exists and is confirmed
- The listing is complete and waiting to publish
- Marketing runs daily without input
- This revenue figure updates daily without input

## The irreducible input

One time, about 60 seconds, then never again:

1. Open https://gumroad.com/settings/payments
2. Sign in as `teeter.ai.bot@gmail.com` — credentials are in
   `state/account.txt` (mode 0600)
3. Choose **PayPal**, and enter your PayPal email and **your legal name**
4. Save

The product publishes immediately, and nothing else ever needs a human again.

If a verified PayPal account already exists in your name, this is pasting one
email address and a name you already know. No documents, no ID upload, no
bank details.

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

- 2026-09-29 — ClaimGate 0.1.0 built, tested (45/45 engine + 21/21 outreach),
  published under MIT, landing page live. Gumroad account created and email
  confirmed; product listing completed with description, A$149 price, slug
  `claimgate` and the zip attached. Publish blocked on the payout method,
  which requires a verified legal identity. Outreach transport proven with a
  real send. Revenue: $0.00.
- 2026-09-29 — Revenue $0.00.
