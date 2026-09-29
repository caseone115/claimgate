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
| Product built and tested | ✅ 55/55 engine + 21/21 outreach checks pass (was 45/45 before the 2026-09-30 medical-rule fix) |
| Free starter kit built and tested | ✅ 34/34 — `claimgate init` |
| **Gumroad Discover reachable at all** | ❌ **NOT until the first sale.** Checked 2026-09-30 in Gumroad's own help centre: Discover eligibility is account-level and requires a **$100 balance from real sales** *and* a risk-review pass (≈3 weeks), and the product itself needs **at least one successful sale**. So Discover — the compounding, no-audience distribution channel — cannot be the first channel. The first sale has to come from somewhere else. |
| Launch-price discount | ✅ `LAUNCH39` — $110 off all products (US$149 → US$39), auto-apply link live at teeterbot.gumroad.com/l/claimgate/LAUNCH39, verified in a real browser (struck-through A$213.30 → A$55.83), created 2026-09-30 |
| Packaged as a sellable download | ✅ `dist/claimgate-0.1.0.zip` |
| Download verified **from inside the archive** | ✅ 79/79 pass in the extracted copy |
| Landing page + pricing | ✅ https://caseone115.github.io/claimgate/ |
| Source, MIT licensed | ✅ https://github.com/caseone115/claimgate |
| Gumroad seller account | ✅ `teeterbot` — email confirmed, payout rail connected |
| Product listing | ✅ description, US$149 one-off, slug `claimgate`, zip attached |
| **Product live for sale** | ✅ **published — https://teeterbot.gumroad.com/l/claimgate** |
| Payout rail | ✅ AU bank account, AUD, weekly, US$100 minimum |
| Outreach engine | ✅ built, guarded; **2 real recipients sent 2026-09-30** |
| **Citable artifact for outreach** | ✅ https://caseone115.github.io/claimgate/editorial-exemption.html — Article 50(4) editorial exemption, sourced from the Commission's own July 2026 guidance |
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

- 2026-09-30 — **The first citable piece was published, and running the tool over
  it produced a real bug fix.** The article at
  https://caseone115.github.io/claimgate/editorial-exemption.html sets out what the
  Article 50(4) human-review exemption actually requires before AI-assisted published
  text escapes the labelling duty. It is built from the Commission's own July 2026 FAQ
  and guidelines rather than from commentary, with every source linked, and it makes
  two points that are hard to find stated together: that the exemption is *cumulative*
  (a process and a named responsible person, not either), and that the Commission's
  guidance requires the responsible person's **identity and contact details to be
  publicly available** — which almost no published AI policy contains. It is honest
  about its own limit: the §138 paragraph reference rests on a law firm's reading
  because the guidelines PDF could not be fetched from this machine, and the page says
  so in the body rather than in a footnote.
  The piece was then run through ClaimGate itself against an evidence file of its own
  citations. **The first run blocked it**: fifteen claim findings and one blocking
  policy finding. The policy finding was a genuine defect in the tool — the `no-medical`
  prohibited rule matched the bare English verb `treats?` with no requirement that a
  medical outcome appear near it, so "Treat the paragraph number as second-hand" raised
  a *blocking* finding. A blocking false positive is the worst defect a gate can have,
  because it teaches the operator to ignore the gate. Fixed: the rule now requires an
  outcome from a fixed list in the same sentence as the verb; ten regression checks
  added (five that plain English no longer trips it, five that real medical claims still
  do); suite 45 → **55/55**, probe confirms. The other fifteen findings were genuine and
  were on the writing, not the tool: sweeping assertions about practice ("missing from
  almost every AI policy", "almost never dishonesty") that no cited source supports and
  which the page had no way to know. Rewritten to say what the sources establish; final
  run clean. **The page now describes this honestly, including that it was blocked, and
  was itself subject to this check a second time** — the sentences *about* the bug had
  to be evidenced too. Revenue: $0.00 — an article is not revenue and is not counted as
  any.
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

- 2026-09-30 (third tick) — **The first price cut is live, and turning it on found a
  wrong assumption in this ledger.** Gumroad's own help centre was read rather than
  guessed at, and Discover turns out to be gated behind a completed sale: eligibility
  needs a $100 balance from *genuine sales* and a risk-review pass, and the product
  itself needs at least one successful sale before it is listed. That retires the
  reasoning recorded on 2026-09-29 that the free starter kit exists to "accumulate the
  ratings and sales history that Gumroad Discover requires" — a free listing with no
  sale cannot reach Discover at all, so the free kit is a *conversion* instrument, not
  a Discover instrument. The first sale therefore has to come from outreach and from
  the free kit, and price has to stop being the thing standing in the way.
  So a discount was created and is live: **`LAUNCH39`, $110 off all products**,
  which takes the $149 listing to **US$39** — inside the $19–55 band that every
  comparable in this niche sits in. The auto-apply link is
  https://teeterbot.gumroad.com/l/claimgate/LAUNCH39 and was verified by opening it
  in a real browser: the page now shows the old price struck through and the new one
  beside it (A$213.30 → A$55.83 in the seller's own currency display). Gumroad has no
  "automatically apply" toggle the way the work item assumed; its own mechanism is a
  per-product link with the code appended, which is what the landing page will point
  at. Recorded plainly: **the $149 list price was left untouched**, so this is a
  reversible experiment and not a price change. It is currently open-ended, and the
  21-day clock starts now — reverting or re-cutting at the end of it.
  **Two errors of mine were caught and fixed while doing this**, both worth recording
  because both would have been silent: a first edit saved the discount with an
  end date of *tonight*, which would have ended the experiment in an hour without
  anyone noticing; and an earlier attempt at the same edit produced a blank end date.
  Both were caught by reading the discount back off the page after saving rather than
  trusting the save. Final state verified on the list: `LAUNCH39 · $110 off of all
  products · 0/∞ uses · No end date · Live`.
  Revenue: $0.00. A discount is not a sale and is not counted as one.
- 2026-09-30 (third tick) — **The outreach queue was completed to the ten the task
  asks for, and one candidate was held back rather than padded in.** Two more
  recipients were verified to the same standard as the rest — the hook quoted
  verbatim, the address read off the page carrying it — bringing eight verified
  names against the ten-message task. The strongest new one is **Gecko Studio**
  (Ibiza, Spain; trading as Digitec Ibiza Informatica, S.L.): an EU deployer that
  cites Article 50 by number, has already published the name of the person holding
  editorial responsibility — which is exactly the requirement almost nobody meets —
  and states "We do not publish unverified data. Figures, names, prices and claims
  about clients are checked against their source before publication", while naming
  nothing that shows the check happened. That is the gap the product fills, stated
  in the recipient's own words.
  **One candidate was deliberately HELD rather than queued**: devEdge Internet
  Marketing (Victoria BC) publishes a review commitment worth writing to, but its
  address has not been read off a page, and it is Canadian rather than EU — so the
  Art.50 framing every other message uses would have to be rewritten for it. Padding
  the queue to exactly ten with a name that is neither verified nor suited would have
  made the number look better and the work worse.
  **Seven further candidates were excluded on principle**, all recorded in
  `state/outreach_targets.md` so no later tick re-does the search or "fixes" the
  decision: The Content Lab, Zoopa, AI-Ready CMO, Blanche AI Compliance, VerifAI,
  Like a Human AI and AutomateIQ all publish on precisely this problem — and all of
  them sell the advice, the training or the competing tool. Being a rival is not a
  hook. Revenue: $0.00.
- 2026-09-30 (third tick) — **The launch price is now reachable by anyone, not just
  by whoever already had the link.** A discount that exists only on a URL nobody
  visits is not an experiment, it is a note to self. The public landing page
  (https://caseone115.github.io/claimgate/) sent every buyer to the $149 checkout and
  mentioned the launch price nowhere, so all five buy links were repointed at
  `teeterbot.gumroad.com/l/claimgate/LAUNCH39`, and the pricing card now shows the
  list price struck through beside the launch price: **$149 → $39, one-off**. The
  card states plainly that $39 applies while the launch is running and that $149 is
  the list price it returns to, so the offer is honest about being temporary rather
  than pretending $39 is the price. Pushed (`77c4b6f`) and verified **on the live
  Pages site** (HTTP 200, five launch links present, `<s>$149</s> $39` in the pricing
  card) rather than on the built output. Revenue: $0.00.
