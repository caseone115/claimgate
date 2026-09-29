# Revenue

The only file that decides whether this is working. Kept deliberately blunt:
no projections, no "pipeline", no dressed-up zero.

**TOTAL: $0.00**

(Two real recipients have now been written to. No reply and no sale: an
outreach message is not revenue and is not counted as any.)

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
| Outreach engine | ✅ built, guarded; **2 real recipients sent 2026-09-30** |
| Inbox watcher | ✅ a human reply can no longer sit unread |
| Storefront art (cover + thumbnail) | ✅ both listings, verified live |
| Listing name | ✅ "ClaimGate — Publish Gate for AI-Assisted Marketing Copy" |
| Seller profile (name + bio) | ✅ was blank; now written and public |
| Affiliate scheme | ✅ 30% on the paid product; signup page live |
| Continuous autonomous operation | ✅ cron 298d128036cc, every 30 minutes |
| **A sale** | ❌ none yet |
| **A second product on sale** | ✅ SimScan US$14 - teeterbot.gumroad.com/l/simscan |
| SimScan's own page | ✅ https://caseone115.github.io/simscan/ |
| SimScan installer on sale = the CI-proven build | ✅ fixed 2026-09-29 (was serving an untested local build whose checksum its own SHA256SUMS.txt contradicted) |

- 2026-09-29 — **SimScan listing was selling the wrong installer; fixed.** The
  attached `Setup.exe` was an old local Wine build (`2ceab6b8…`) while the
  `SHA256SUMS.txt` attached beside it named the CI-proven build (`287f54be…`) —
  so the verification step the listing itself invites would fail. The CI build
  was downloaded, uploaded to the listing, hash-confirmed to match *before*
  anything was removed, the stale row deleted, saved, and then all three files
  were re-downloaded from the live listing and every hash matched. The local
  `release/` copies were replaced with the CI artifacts and the stale build kept
  as `SimScan-1.0.0-Setup.exe.stale-local-build`. A description sentence telling
  buyers the checksums are "published in the repository" was rewritten (the repo
  ships source and tests only, so they were tracked nowhere in git). SimScan's
  own page is live at caseone115.github.io/simscan/. Revenue: $0.00.
- 2026-09-29 — **Shop presentation fixed.** Neither listing had a cover image or
  a thumbnail, so every appearance — search, profile, a shared link — fell back
  to Gumroad's grey placeholder. Generated deterministic art in the landing
  page's palette (`scripts/make_storefront_art.py`), uploaded to both listings,
  verified live from outside. The paid listing was also named the lowercase slug
  `claimgate`; it now reads "ClaimGate — Publish Gate for AI-Assisted Marketing
  Copy" (confirmed in `og:title`). The seller profile had no name and no bio at
  all; both are now written and public.
- 2026-09-29 — **Affiliate scheme enabled at 30% on the paid product.** Verified
  from outside: `teeterbot.gumroad.com/affiliates` returned 404 beforehand and
  now serves "Become an affiliate for ClaimGate". Costs nothing unless a
  referred sale happens — the only channel that borrows an audience we do not
  have, and paid advertising produced 0 of 70 documented first sales.
- 2026-09-29 — **Free starter kit published as a second listing**
  (`teeterbot.gumroad.com/l/claimgate-starter-kit`) at US$0 with the contribution
  box enabled; verified from an unauthenticated fetch as `price: 0.0`. It exists
  to accumulate the ratings and sales history that gumroad Discover requires and
  that a $149 listing with no reviews cannot get. A buyer-view check corrected a
  wrong earlier assumption: the contribution box does appear on a $0 product.
  Revenue: $0.00.

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

- 2026-09-30 — **The first two real messages to real people went out, and the
  target list was built out of the recipients' own published words.** Not a
  mailing list and not scraped addresses: each recipient is a company that has
  publicly committed in writing to reviewing AI-assisted content, and each
  address was read off the page carrying the sentence being quoted.
  `info@frankcaremarketing.com` (Frank Care Marketing, UK care-sector
  marketing) publishes a log of "the prompt used, the output generated, the
  reviewer notes and human oversight steps" — a genuinely strong documentation
  position, but the log shows a human read the draft and says nothing about
  whether the claims in it were substantiated. `hello@katiefarrell-econsultant.com`
  (Katie Farrell E-Consultant, UK; Klaviyo and email for ecommerce) promises
  human review before publication and hedges disclosure as "when appropriate",
  which is the discretionary wording Art.50 does not offer. Each message names
  the gap between the promise and what a documented editorial-control defence
  requires, and offers a free run over a draft the recipient has already
  published — no signup, no call, no sequence. Both say in the first line that
  they were written by automated software and that there will not be a second
  message. Enforced by code, not memory: three a day, one per company, never the
  same address twice, hook required to appear in the body (`state/outreach_sent.jsonl`
  is the permanent record; `state/outreach_targets.md` is the queue).
  Seven further recipients are researched and verified for the following ticks.
  Two candidates were **excluded, not skipped**: PerformLine and Bill Rice
  Strategy Group publish on exactly this problem, but each is a vendor in the
  space, and being a competitor is not a hook.
  **Nothing came back** — the mailbox was checked twice and is quiet. 8 of the 10
  messages remain queued because the daily limit, not the writing, is the
  constraint. Revenue: $0.00.
- 2026-09-29 - **Two products now on sale, and the money checked from inside the
  account.** Signed in to Gumroad and read the real figures rather than inferring
  them: dashboard Balance $0 USD, Last 7 days $0, Last 28 days $0, Total earnings
  $0; the products table shows 0 sales and $0 revenue on both listings; 0 customers
  on each. SimScan was listed as a second, unrelated product at US$14 (id `ghnmdw`,
  slug `simscan`), which tests the rail and the shop independently of ClaimGate.
  A listing claim was corrected to be exactly true - an earlier draft read as
  though SHA-256 checksums and the test suite shipped inside the download; they are
  published in the public repo instead, and the sentence now says that. Revenue:
  $0.00 - still the only thing missing is a customer.



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
