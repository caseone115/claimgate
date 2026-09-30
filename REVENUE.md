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
| Free starter kit built and tested | ✅ 36/36 — `claimgate init` (was 34; the two added checks fail if the kit stops carrying the launch link) |
| **Gumroad Discover reachable at all** | ❌ **NOT until the first sale.** Checked 2026-09-30 in Gumroad's own help centre: Discover eligibility is account-level and requires a **$100 balance from real sales** *and* a risk-review pass (≈3 weeks), and the product itself needs **at least one successful sale**. So Discover — the compounding, no-audience distribution channel — cannot be the first channel. The first sale has to come from somewhere else. |
| Launch-price discount | ✅ `LAUNCH39` — $110 off all products (US$149 → US$39), link live at teeterbot.gumroad.com/l/claimgate/LAUNCH39, verified in a real browser (struck-through A$213.30 → A$55.83), created 2026-09-30. Still `0/∞ uses · No end date · Live` on 2026-09-30 (fourth tick) |
| Launch price on **every warm-buyer surface** | ✅ **added 2026-09-30 (fifth tick).** The launch price was on the landing page and the two listings, and **missing from every other surface a reader arrives from**: the free kit's README *and* CHECKLIST (both shipped inside the download), the public README, `docs/SUPPORT.md`, and the footer of `editorial-exemption.html`. All five fixed and confirmed live. The live free-kit listing description was the worst of them: it read "One-off US$149 at github.com/caseone115/claimgate" — the *list* price, and a pointer to the source repo, not to the shop — shown to the reader who had just decided the free kit was worth their time. Verified from outside: `LAUNCH39` ×3 in the served HTML, the old sentence 0 times |
| Free kit has a **builder that refuses to ship a stale price** | ✅ **added 2026-09-30 (fifth tick).** `scripts/build_kit_dist.py` builds the kit from `claimgate.kit`, reproducibly (two builds, identical SHA-256 `5cdb11be…`), then reads the README back **out of the finished zip** and refuses to build unless it carries the launch link, both prices, and no stale check count. The kit had *no* builder before this, which is exactly how its README drifted |
| Both live listings serve the rebuilt archives | ✅ **2026-09-30 (fifth tick).** Free kit: only the new 6.3 KB archive (the stale 6.1 KB one had to be deleted separately — uploading *adds* rather than replaces, so both were briefly attached). Paid: only the new 49.9 KB archive (stale 40.7 KB deleted). Both confirmed by reopening the editor against the server, not by trusting the save |
| Launch price visible **on the listing itself** | ✅ **added 2026-09-30.** The product description now opens with the launch price, the list price and the launch link. Verified on the live public listing (renders as the page's `og:description`). Before this, a visitor arriving from search or a share saw a listing that never mentioned $39 |
| Gumroad **auto-apply discount** toggle | ❌ **found and does not save.** The toggle exists (product editor → Pricing → `Automatically apply discount code`) — the 2026-09-30 third-tick note that Gumroad "has no automatically apply toggle" is **wrong**. It was switched on and saved 3×; it reverts to off every time and the public page does not change. Cause probed: its `Discount code` search widget returns **no `LAUNCH39` option**, so the code is typed but never selected, and there is nothing valid for the switch to save. The listing's headline price is therefore still US$149; the discount applies through the launch link or the code at checkout |
| Packaged as a sellable download | ✅ `dist/claimgate-0.1.0.zip` |
| Download verified **from inside the archive** | ✅ 112/112 pass in the extracted copy (55 engine + 36 kit + 21 outreach) |
| **Discount scope** | ✅ **fixed 2026-09-30 (sixth tick).** `LAUNCH39` was scoped to *all products* and was giving the second product away free: `teeterbot.gumroad.com/l/simscan/LAUNCH39` rendered **A$20.06 → A$0** in a logged-out browser. SimScan is now excluded. Verified after saving, from outside: SimScan with the code attached renders plain A$20.06 with no struck-through price, while ClaimGate with the same code still renders A$213.51 struck through to A$55.89 |
| **Discount code field at checkout** | ✅ **fixed 2026-09-30 (sixth tick).** `Checkout → Checkout form → Add discount code field` was set to **Never**, so the launch price was reachable only through the exact launch link and through no other route. Switched to *Only if a discount is available*, saved, and exercised as a stranger: cart A$216.31 → code applied → **A$61.90** (US$39 + GST) on a logged-out checkout |
| **A person is waiting for an answer** | ⚠️ **raised 2026-09-30 (sixth tick), not fixed.** The inbox watcher reports 1 person-mail awaiting an answer: the owner's own 2026-09-29 "ClaimGate trial" message. Deliberately not auto-answered — replying to the owner as if they were a prospect would be worse than silence. Re-raised every run until the owner closes it |
| Landing page + pricing | ✅ https://caseone115.github.io/claimgate/ |
| Source, MIT licensed | ✅ https://github.com/caseone115/claimgate |
| Gumroad seller account | ✅ `teeterbot` — email confirmed, payout rail connected |
| Product listing | ✅ description, US$149 one-off, slug `claimgate`, zip attached |
| **Product live for sale** | ✅ **published — https://teeterbot.gumroad.com/l/claimgate** |
| Payout rail | ✅ AU bank account, AUD, weekly, US$100 minimum |
| Outreach engine | ✅ built, guarded; **3 messages sent in total, 2 of which reached a recipient** (the first bounced). **Cap re-driven 2026-09-30 15:00 AEST with the guard itself (`state/cap_now.py`): ALLOWED at 2/3** — the self-test no longer consumes a slot (`outreach.countable()`). **Two** slots clear together at **2026-10-01 00:04 AEST** (the two 14:04 UTC sends age out at once), the last two at 12:04. Hour-granular sample — treat as "first tick after". Sender: `state/outreach_queue.py` |
| **Citable artifact for outreach** | ✅ https://caseone115.github.io/claimgate/editorial-exemption.html — Article 50(4) editorial exemption, sourced from the Commission's own July 2026 guidance |
| **Standing shop probe** | ✅ **fixed 2026-09-30 (seventh tick).** It had been crying wolf: it asserted the discounted price as the exact cents seen on the day it was written (A$55.89 / A$55.83), so when FX moved the list price A$213.51 → A$213.81 the launch price read A$55.96 and a working 74% discount was reported as a regression. It now asserts the **ratio** (39/149), which is currency-blind, and was proved against the real page plus four deliberately broken cases it still catches |
| **Browser automation (was silently dead)** | ✅ **fixed 2026-09-30 (seventh tick).** Every browser run was dying with `Failed to create SingletonLock: File exists`. The cause was not the lock: **48 orphaned headless Chrome processes** from earlier runs were still alive on our two profile dirs and holding them — agent-browser leaves Chrome running on exit, so the run *after* any browser run failed. The shop was unreachable to every automated check while `daily_probe.sh` still printed `STATUS: ok`. `scripts/browser.py` now reaps our own orphans (matched by exact `--user-data-dir`; proved not to match a profile we do not own), clears stale locks, reaps once per process, and the probe cleans up after itself. Verified by two consecutive green runs — the thing that used to be impossible |
| **Traffic actually observed** | 📊 **39 views in the last 30 days, 0 sales**, read from inside the account 2026-09-30 (seventh tick) now that browsing works again. 3 views placed in the United States, the rest unplaced. Balance $0, last 7 days $0, last 28 days $0, total earnings $0 on all three listings; the dashboard's own "Make your first sale" step is unticked. This is a sample that says nobody has been given a reason to buy yet — not that the price is wrong |
| Inbox watcher | ✅ a human reply can no longer sit unread |
| Storefront art (cover + thumbnail) | ✅ both listings, verified live |
| Listing name | ✅ "ClaimGate — Publish Gate for AI-Assisted Marketing Copy" |
| Seller profile (name + bio) | ✅ was blank; now written and public |
| Affiliate scheme | ✅ 30% on the paid product; signup page live |
| Continuous autonomous operation | ✅ cron 298d128036cc, every 30 minutes |
| **Install instruction on every shipped surface** | ✅ **fixed 2026-09-30 (eighth tick), and it was wrong everywhere.** Every shipped instruction told a reader to run a bare `pip install claimgate`. That name on PyPI is **not ours** — it belongs to an unrelated project (an AI-agent test harness, v0.1.0, another owner). Proved in a clean venv: the bare name installs *that* tool, and our own next command then failed with `No such command "check"`. Fixed in all four surfaces — public `README.md`, kit README, kit CHECKLIST, the **kit's CI workflow** (which would have failed a customer's build) — plus the `claimgate init` message, each now naming `git+https://github.com/caseone115/claimgate`, with the kit README stating plainly what the bare name installs. Proved by installing the corrected line and running `claimgate check` in a clean venv |
| **Every live listing is checked for being switched off** | ✅ **added 2026-09-30 (ninth tick), because the shop went dark and nothing noticed.** An edit to the SimScan listing accidentally **unpublished** it — off the storefront, invisible to every buyer — and doors 1 and 2 of the probe kept reading a price off its page, because Gumroad renders an unpublished product to the *seller* while hiding it from buyers. Caught from the product list within minutes, republished, and verified from outside: `is_published: true`, US$14 USD. **Door 6** now reads `is_published` and `price_cents` out of all three listings' own product payload and fails if either moved. Proved able to fail: catches an unpublished listing and a repriced one, passes all three live listings. Full probe exit 0. |
| **A sale** | ❌ none yet |
| Two stale test-count claims | ✅ **fixed 2026-09-30 (fifth tick).** The kit README sold a "45-check test suite" (it is 55) and the public README quoted 45 for the engine. A claim-checking product quoting its own test count wrong is the exact failure it exists to catch |
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

- 2026-09-30 (fourth tick) — **The launch price is now on the product listing
  itself, and this ledger's own note about the auto-apply toggle was wrong.**
  Two things, one done and one not, both recorded rather than smoothed over.
  **(a) Done.** The listing description opened straight into the pitch with no
  price in it, so anyone arriving from search, a share or a bookmark saw a page
  that never mentioned US$39 — the previous tick had pointed the *landing page*
  at the launch link, but the *shop listing* is a different surface and said
  nothing. The description now begins: *"Launch price: US$39 while the launch is
  running, list price US$149. Buy through
  https://teeterbot.gumroad.com/l/claimgate/LAUNCH39 and the US$110 discount
  applies at checkout."* The old text was backed up to `state/_desc_backup.txt`
  (3979 chars) before editing, saved, and **verified on the live public listing
  from outside** — it renders as the page's `og:description`, with "Launch
  price", "LAUNCH39" and "US$39" each present nine times, and the listing is
  still `is_published: true` and still lists at US$149 from its own URL.
  **(b) Not done, and the correction matters more than the feature.** This
  ledger claimed on 2026-09-30 that Gumroad "has no 'automatically apply
  discount code' toggle". **That was false.** The toggle is right there in the
  product editor under Pricing. It was found, the `Discount code` box accepted
  `LAUNCH39`, the switch genuinely moved to on, and it was saved three times —
  **and it reverted to off every single time**, with the public page unchanged at
  A$213.30. Probing the cause: the code box is a search widget whose filtered
  option list contains **no `LAUNCH39` entry at all**, so the string is typed into
  the input but no real option is ever selected and the selection is never
  committed. That is a widget/options problem, not a missing feature — and the
  distinction is the whole point, because "Gumroad cannot do this" would have
  stopped anyone trying again. **The honest position on price reach:** the landing
  page and the listing description both state the launch price; the listing's own
  headline price remains US$149, and the discount is applied via the launch link
  or the code at checkout.
  Re-verified unchanged this tick: the suite at 55/55 + 34/34 + 21/21, the site
  and repo at HTTP 200, the mailbox quiet, and the discount still
  `$110 off of all products · 0/∞ uses · No end date · Live`.
  Revenue: $0.00. A discount is not a sale and is not counted as one.
- 2026-09-30 (fourth tick) — **The next three outreach messages could not be
  sent, and the portfolio's date for when they can be was wrong.** The guard
  returned `daily limit reached (3/3 in the last 24h)` and refused all three —
  correctly. The rolling 24h window runs from the actual send timestamps
  (2026-09-29 14:04 UTC in `state/outreach_sent.jsonl`), so the next three can go
  at the first tick after **2026-09-30 14:04 UTC / 2026-10-01 00:04 AEST**. Earlier
  prose in `PORTFOLIO.md` and `WORKLOG.md` said the window cleared at 00:04 AEST
  on 2026-09-30; it does not, and this run was still inside it. The timestamps in
  the log are the authority, not the prose. All three queued recipients (Solomon
  Advising, EMF Consultants, ZORC AB) were re-read page-by-page this tick and
  every address and quoted hook is still traceable, so nothing in the queue has
  gone stale while it waits. Nothing was sent, so nothing is claimed. Revenue:
  $0.00.

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

- 2026-09-30 (seventh tick) — **The shop's own standing check was wrong in two
  ways, and the second was hiding a total outage of every browser-based check.**
  It started with running the queue's own probe instead of trusting it, and the
  probe failed (exit 1) claiming three doors were broken.
  **(a) It was crying wolf.** The probe asserted the launch price as the exact
  cents from the day it was written (`A$55.89` / `A$55.83`). Gumroad renders in
  the visitor's currency, so when the list price moved `A$213.51 → A$213.81` the
  launch price read `A$55.96` and a working 74% discount was reported as a
  regression — for a check whose whole job is to be believed. It now asserts the
  **ratio**, `39/149`, which is the real invariant and currency-blind. Proved
  both ways: it passes every real render, including today's, and still fails four
  deliberately broken ones — discount not applying, product gone free, wrong
  coupon, no struck price at all. A check that cannot fail is not a check.
  **(b) The real fault, and it was not the one being reported.** Every browser run
  was dying with `Failed to create SingletonLock: File exists` (Chrome exit 21).
  The cause was **not** a stale lock: **48 orphaned headless Chrome processes**
  were still alive on our two profile dirs and holding them. agent-browser leaves
  Chrome running when a script exits, so **the run after any browser run failed**.
  That means the shop had become unreachable to every automated check while
  `daily_probe.sh` went on reporting `STATUS: ok`, because it never starts a
  browser — a real outage invisible from every health surface we had.
  `scripts/browser.py` is now the single self-healing driver: reaps our own
  orphans (matched by the exact `--user-data-dir`, **proved not to match a profile
  we do not own**), clears stale locks, reaps **once per process**, and the probe
  cleans up after itself so they cannot re-accumulate. Two mistakes of mine were
  caught by running it rather than reasoning about it: reaping on *every* call
  killed the browser between `open` and `eval` and produced three *false* breaks
  on a shop that was fine, and the helper was first written into gitignored
  `state/`, where the tracked probe importing it would break on a fresh clone.
  **Verified: two consecutive green runs** (`0` Chrome left running afterwards),
  `daily_probe.sh` still `55/55 + 36/36 + 21/21`, site 200, repo 200.
  **(c) With browsing repaired, the real numbers were read from inside the
  account** instead of guessed: **39 views, 0 sales** on all three listings;
  Balance $0, last 7 days $0, last 28 days $0, total earnings $0; 3 views from the
  United States, the rest unplaced; the dashboard's own "Make your first sale"
  step unticked. The inbox is quiet — the only person-mail on record is still the
  owner's own 2026-09-29 trial message, deliberately not auto-answered.
  **Revenue: $0.00 — a fixed check is not a sale, and 39 views is not demand.**
  No sale, no reply, no traffic change attributed to anything.

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
  `<addr: Frank Care Marketing>` (Frank Care Marketing, UK care-sector
  marketing) publishes a log of "the prompt used, the output generated, the
  reviewer notes and human oversight steps" — a genuinely strong documentation
  position, but the log shows a human read the draft and says nothing about
  whether the claims in it were substantiated. `<addr: Katie Farrell E-Consultant>`
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

- 2026-09-30 (fifth tick) — **Every warm-buyer surface was still quoting the
  $149 list price; all of them now carry the launch price.** The audit that
  caught it went over the surfaces the previous tick did not check, and found
  the price cut had never reached the people most likely to act on it. Five
  surfaces fixed (kit README, kit CHECKLIST, public README, `docs/SUPPORT.md`,
  the outreach article footer), plus the live free-kit listing description,
  which had named the list price and sent readers to the source repo instead of
  the shop. The cause was structural — the kit was hand-built with no builder to
  catch drift — so it was fixed structurally: `scripts/build_kit_dist.py` now
  builds the kit reproducibly and reads its own README back out of the finished
  zip, refusing to ship unless it carries the launch link and both prices; the
  kit test suite got the same contract (34 → 36). Both archives rebuilt and
  verified from inside the extracted copy (112/112), both live listings now
  serve the rebuilt files, pushed `442fbed`. Also corrected: this file's and
  `WORKLOG.md`'s claim that the outreach cap clears at 00:04 AEST tomorrow was
  pessimistic by ten hours — the guard was driven directly at future times
  (`state/cap_when.py`) and one message clears at 2026-09-30 01:44 UTC, when the
  self-test transport row (not a prospect) falls out of the 24h window.
  **Revenue: $0.00 — a corrected price is not a sale.**

- 2026-09-30 (sixth tick) — **Two ways the shop was losing money, found by
  shopping in it logged-out as a stranger, and both fixed and verified.** Every
  previous tick audited the pages *we* publish, with our own session. This tick
  walked the buyer's path instead — no login, add to cart, checkout, pay — and
  found two defects that no page we control would ever have shown.
  **(a) The launch discount was giving a paid product away.** `LAUNCH39` is $110
  off **all products**; appended to the second product's link
  (`teeterbot.gumroad.com/l/simscan/LAUNCH39`) its page rendered **A$20.06 →
  A$0** in a logged-out browser, and the discounts list displayed the giveaway in
  plain text. A $110-off coupon on a A$20.06 product was never the intent — it
  exists to take a US$149 product to US$39. SimScan is now excluded from it.
  Verified after saving, from outside: SimScan with the code attached renders
  plain **A$20.06**, no struck-through price; ClaimGate with the same code still
  renders **A$213.51 struck through to A$55.89**.
  **(b) The checkout had no discount-code field.** `Checkout → Checkout form →
  Add discount code field to purchase form` was set to **Never**, so the launch
  price was usable only by someone arriving through the exact launch link — the
  same class of mistake as a discount on a URL nobody visits, in a different
  place. Switched to *Only if a discount is available*, saved, re-read after a
  reload to confirm it persisted, and then **exercised as a stranger**: cart
  A$216.31, `LAUNCH39` typed into the new field, Apply → **A$61.90**, which is
  the US$39 launch price plus Australian GST, on a logged-out checkout.
  **Also re-verified, unchanged:** the published landing page leads with
  A$213.51 and points at the launch link; suites 55/55 + 36/36 + 21/21; site
  200; repo 200; `LAUNCH39 · $110 off of all products except SimScan … · 0/∞ ·
  No end date · Live`.
  **Raised, not fixed:** the watcher reports **1 person-mail awaiting an
  answer** — the owner's own 2026-09-29 "ClaimGate trial" message. It is not a
  prospect's reply, and replying to the owner as though it were would be worse
  than the silence, so it is surfaced rather than auto-answered.
  **Revenue: $0.00 — closing a leak is not a sale.** No sale, no reply, no
  traffic change, nothing measured.

- 2026-09-30 (ninth tick) — **The live SimScan listing never stated its own price and never mentioned the SmartScreen warning, and closing that gap briefly took the product off sale.** Walking the buyer's path as a stranger (rather than as ourselves) found the listing strong on honesty and missing the two facts that decide a download: the body said nothing about US$14, and nothing about the blue SmartScreen dialog a buyer hits because the installer is not code-signed. That warning was in the GitHub README and **absent from the page where money changes hands** — and a buyer who downloads and meets an unknown-publisher dialog without being warned bounces. Both added in the listing's first line and **verified on the live public page from outside** (`og:description` now opens with it; `product:price:amount` still `14.0` USD).
  **The expensive part was my own mistake.** My Save control matched on a substring, caught Gumroad's **`Unpublish`** button instead, and switched the product off — it sat **Unpublished** and invisible to buyers. Caught within minutes from `/products` (which showed `Unpublished` beside the other two as `Published`), republished from the Share tab, and confirmed from outside. **Nothing flagged it, and nothing would have:** the probe's own doors 1 and 2 read a price off an unpublished product's page without complaint, because Gumroad serves that page to the seller while hiding it from buyers. A closed shop was invisible to every health check we had. **Structural fix: `scripts/checkout_doors.py` door 6** now pulls `is_published` and `price_cents` from each listing's own payload and fails if either moved — proved by driving it against a deliberately unpublished copy and a repriced copy, and passing all three live listings. Pushed `5497f7d`. Full probe `exit 0`: doors 1–5 green, the 39/149 ratio still holding, the discount still excluding SimScan, and all three listings published.
  Also: **SimScan's GitHub repo had zero topics**, so it was invisible to GitHub topic search; eight added (`sims4`, `the-sims-4`, `mod-conflicts`, `dbpf`, …), verified on the repo. Competitor research recorded honestly: `Mecapixel/sims4-mod-detector` does DBPF/TGI conflict detection and is free — SimScan's difference is a signed installer rather than a Python script to set up. **Revenue: $0.00** — a listing that is visible is not a sale.

- 2026-09-30 (tenth tick) — **The outreach clock was wrong in two separate
  places, and both were costing messages.** Everything below was settled by
  running the guard, not by reasoning about it.
  **(a) The cap probe could not test the cap.** `state/cap_now.py` drove
  `outreach.check()` with a probe hook that did not appear in its own probe
  body. The guard's hook-in-body rule sits **after** the daily-cap check, so
  every run of the probe died on that rule and printed *"the recipient hook
  does not appear in the message body"* — and the queue files read that verdict
  as *"the cap is still 3/3"*. The file had therefore never actually reached the
  cap check. Rewritten so the body contains the hook; driven at ten future
  offsets it now returns a real verdict, and the real verdict from NOW was
  **ALLOWED (2/3)**. The queue had been told to wait ten hours for a slot that
  had been free since 01:44 UTC. **The one free message was sent this tick.**
  **(b) The transport self-test was eating a prospect's slot.** `recent(24)`
  counted every row in the log, including the self-test sent to our own inbox
  on 2026-09-29 — which is what actually held the count at 3/3. A test message
  must not cost a prospect their slot, so `outreach.countable()` now excludes
  rows whose note carries the self-test marker, `check()` counts against
  `countable(recent(24))`, and `status()` reports the self-test rows separately
  as *never counted*. The anti-spam limit is unchanged for real recipients:
  `tests/test_outreach.py` gained three checks — a self-test row does not
  consume a slot, the row is still in the log, and three real sends still close
  the cap — **25/25**. The rule itself stays recorded in the log either way.
  **(c) Sent: `<addr: Solomon Advising>`** (2026-09-30 02:01:52 UTC), hook
  quoted from their own AI use policy — *"All AI-generated content is reviewed
  by senior consultants"* and *"Fact-checking and verification of all
  AI-generated information"*, with no artifact named that shows a claim was
  ever checked against a source. Their page also publishes *"Accuracy
  standards: Human verification of all strategic recommendations"* and a
  documentation promise, which sharpens the same gap. 3 of 10 sent. The cap
  then closed correctly at 3/3 and refused the fourth.
  **(d) An honesty correction to this ledger and to `WORKLOG.md`:** the first
  outreach message, `<addr: Frank Care Marketing>` (sent 2026-09-29 14:04:13),
  **bounced** — the delivery-failure notification is recorded in
  `state/inbox.jsonl` at 2026-09-30T00:32:16Z with `X-Failed-Recipients`. It was
  counted here and in the queue as a prospect reached. It was not: nothing
  arrived, the address is dead, and Frank Care Marketing is struck from the
  queue. **People actually written to: 2**, not 3, until a slot opens.
  **(e) Also re-verified unchanged this tick:** `scripts/checkout_doors.py`
  exit 0 — doors 1–5 green, the launch ratio holding at 39/149
  (`A$213.86 → A$55.98`), SimScan excluded from the discount (plain `A$20.09`,
  no strike-through), all three listings `published=True` at 14900 / 1400 / 0
  cents, and the install-command check on both paid listings clean.
  **Current constraint, stated plainly: distribution.** 39 views, 0 sales,
  still no reply from the one live recipient. **Revenue: $0.00 — a sent message
  is not a sale, and a bounced one is not even a message.**

## 2026-09-30 (twelfth tick) — a "rehearsal" sent three real messages, and the log said they went tomorrow

**What happened, plainly.** A read-only rehearsal was run: import the prepared
outreach queue, patch `outreach._now` forward to a window where the cap is open,
and check every message against the real guard without sending. The queue file
had its **send loop at module level** (`for job in JOBS: _try(job)`), so the
import itself sent. Three messages left the mailbox on the real transport —
**ZORC AB (`<addr: ZORC AB>`), EMF Consultants (`<addr: EMF Consultants>`),
ON Advertising (`<addr: ON Advertising>`)** — and because `record()` stamps its
row with `_now()`, and `_now()` was patched, the log filed them at
**2026-10-01T06:00:00+00:00**: a send time a day and a half in the future.

**The harm was the timestamp, not the messages.** All three recipients were
verified, their hooks are quoted from their own published pages, each message
says plainly that it is software, the cap was not exceeded (three is the limit),
and the guard passed every content rule for each one. Nothing bounced — the
inbox is quiet and `inbox.py --days 3` reports no failure notification. They are
real, legitimate outreach that happened six hours early, and the queue had them
scheduled anyway. What was wrong is that the log — the thing the rolling 24h cap
is computed from — was wrong by a day and a half, and any figure read from it
would have been.

**Corrections, all driven rather than reasoned:**
- The three rows were rewritten to the times the mailbox itself stamped, read
  from the `Date` header in **`[Gmail]/Sent Mail`** via IMAP (read-only,
  `BODY.PEEK`): **06:03:31 / 06:03:39 / 06:03:47 UTC on 2026-09-30**. The rows
  carry `time_source: imap Sent Mail Date header`. Backup:
  `state/outreach_sent.jsonl.bak-20260930-1604`.
- **The slot arithmetic in the queue files was wrong** and is now measured:
  `state/cap_now.py` walks the guard forward in two-minute steps over 40 hours,
  and the next slot opens at **2026-10-01 16:04 UTC = 2026-10-02 02:04 AEST**,
  not 2026-10-01 00:04 AEST. That earlier figure was right for a log with four
  countable sends; there are six.
- **`WORKLOG.md` and `PORTFOLIO.md` both said "four remaining messages". There
  are eight prepared and unsent** (four in `state/outreach_queue.py`, four more
  in `state/outreach_extra.py` — Nimble & co, WEVENTURE, sackit, BlackHold).
  The second wave was never recorded in `state/outreach_targets.md`, which is
  how two files came to disagree with a third.
- **All five not-yet-sent messages pass the real guard** at a window that is
  genuinely open with the corrected log (Gecko Studio, Nimble & co, WEVENTURE,
  sackit, BlackHold) — hook 114–201 chars, body 1764–1949 chars. The three sent
  by accident are, of course, now refused as "already contacted", which is the
  guard working.

**The fix is in the product, not in this note.** A rehearsal that can only be
run by importing the file that sends, on a clock that is deliberately wrong, is
one mistake away from sending at a wrong time permanently. So:
1. `state/outreach_queue.py` — the module-level send loop is gone. There is one
   entry point and **nothing runs on import** (proved: the log's sha256 is
   unchanged across an import). Sending is now DRY by default and requires the
   explicit `CLAIMGATE_OUTREACH_SEND=1`.
2. `claimgate/outreach.py` — `send()` now **refuses to send while `_now()`
   disagrees with the wall clock** (`_clock_is_real`), because a send on a
   patched clock is logged under a fictional time forever. `check()` is
   deliberately still allowed on a faked clock: that is the rehearsal.
3. `tests/test_outreach.py` — four new checks: a send on a faked clock is
   refused, it writes nothing to the log, a *check* on a faked clock is still
   allowed, and the send path resumes when the clock is restored. **28/28**
   (was 25).

**Also re-verified unchanged:** `scripts/checkout_doors.py` **exit 0** — launch
ratio 39/149 (`A$213.58 → A$55.90`), SimScan excluded from the discount (plain
`A$20.07`), all three listings `published=True` at 14900 / 1400 / 0 cents, the
checkout offers the discount field, install-command check clean on both paid
listings. Inbox: quiet, no reply from any real recipient this tick.

**Revenue: $0.00.** Three messages that were going to be sent tomorrow were sent
today; a sent message is not a reply and a reply is not a sale.

**A correction to my own correction, added the same tick.** While re-verifying the
second wave I recorded that BlackHold's stored address was wrong (substituting
`<addr: BlackHold Group>`) and that WEVENTURE published no address at all
(setting `addr=None`). **Both calls were wrong, and the project's own evidence
settled it.** `state/outreach_evidence/blackhold__addr_page.txt` is a saved copy of
BlackHold's *contacto* page and it carries `<addr: BlackHold Group>`;
`weventure__addr_page.txt` is a saved copy of WEVENTURE's *Datenschutz* page and it
carries `<addr: WEVENTURE>` ("Kontakt zum Verantwortlichen: WEVENTURE Performance
GmbH, Bettina Wille, <addr: WEVENTURE>"). I had checked one page each — BlackHold's
IA policy page, WEVENTURE's Impressum and Kontakt — and generalised from it. Both
entries were reverted to verified, `tests/test_hook_provenance.py` — which exists
precisely to catch an address that was not read off a page — is **20/20** again, and
`state/outreach_targets.md` now records where each address actually lives. The rule
this queue runs on ("the address was read off the page that carries the hook") turns
out to need a second clause for verification itself: *absent from the page you
happened to open is not absent from the company.*

## 2026-09-30 (eleventh tick) — the four remaining messages are written, and the rehearsal caught one that would have burned a slot

**The queue had four verified names and four blank bodies.** The plan of record
was to write each message when its sending day arrived, which puts the discovery
of any fault at the exact moment the slot is open - the most expensive moment to
find one. All four are now written and prepared, and the sending is driven by
`state/outreach_queue.py`, which runs the messages through the **real guard**
(`claimgate.outreach.check`) on every tick: it prints the guard own refusal
reason while the cap is closed, and sends when it opens. Nothing about the
anti-spam limits changed.

**The rehearsal is the part that mattered.** Run as-is, every probe stopped at
the cap (3/3) before reaching the hook rule, so the messages looked fine while
their content was never actually tested. Re-run at a **simulated open window**
(2026-10-01T06:00Z, guard time monkey-patched), three passed and **ZORC failed
the hook-in-body rule**: the quoted policy line was written in US spelling
("labeled") in the hook and UK spelling ("labelled") in the body, so the
verbatim match the guard requires broke. Invisible to reading; fatal to the
send. Fixed. All four now pass the guard at the simulated open window:

| # | Recipient | Hook (chars) | Body (chars) |
|---|---|---|---|
| 5 | ZORC AB, Sweden (EU) | 114 | 1911 |
| 4 | EMF Consultants, UK | 168 | 1896 |
| 6 | ON Advertising, US | 184 | 1820 |
| 7 | Gecko Studio, Spain (EU) | 201 | 1764 |

**A timing correction.** Two sends clear **together** at 2026-10-01 00:04 AEST,
not one: both 2026-09-29 14:04 UTC sends age out of the rolling 24h at the same
instant (verified with `state/cap_now.py`, which reports ALLOWED from
2026-09-30T14:33Z); the 2026-09-29 01:44 row is the transport self-test and is
never counted. The queue file said one slot. Corrected in the queue file and in
`WORKLOG.md`.

**Also re-verified unchanged this tick:** `scripts/checkout_doors.py` **exit 0**
- launch ratio holding at 39/149 (`A$213.86 -> A$55.98`), SimScan excluded from
the discount (plain `A$20.09`, no strike-through), all three listings
`published=True` at 14900 / 1400 / 0 cents, checkout discount field offered,
install-command check on both paid listings clean. No reply in the mailbox (2
rows: the owner's own trial message, and the Frank Care bounce).

**Revenue: $0.00.** A written message is not a sent message, a sent message is
not a reply, and a reply is not a sale. Nothing here is claimed as revenue until
the Gumroad ledger shows it.

## 2026-09-30 (fourteenth tick) — the paid listing was still serving a 1.0.0
## installer, and the version fix had to reach the shop, not just the repo

The version-consistency work (single source, guard, `v1.0.2` release) is recorded
in `~/simscan/README.md` and the portfolio. This is the Shop half of it, because
that is what this ledger is for.

**What was wrong, measured by opening the live listing's Content tab:** the
SimScan listing still attached **`SimScan-1.0.0-Setup`**, **`SimScan-1.0.0-portable`**
and a stale **`SHA256SUMS`**. The published GitHub release was already `v1.0.2`.
So a buyer paying US$14 today receives an installer named 1.0.0 whose own resource
says 1.0.0 — the exact artifact the version work was done to retire. The repo was
fixed and the shop was not, which is the same class of miss as the launch price
that reached the landing page and the two listings but not the warm-buyer
surfaces, recorded on 2026-09-30 (fifth tick).

**Fixed and verified from the server, not the editor's optimistic state:**
1.02 artifacts uploaded, the three stale attachments deleted, and the list read
back after a save **and a reopen**: the listing now serves exactly
`SHA256SUMS` (185 bytes), `SimScan-1.0.2-portable` (18.4 MB) and
`SimScan-1.0.2-Setup` (13.6 MB). The buyer-facing storefront still reads A$20.09
and `is_published: true`, and `scripts/checkout_doors.py` is green on all six
doors afterwards — editing a live listing is what took SimScan off sale on
2026-09-30 (ninth tick), so it was re-checked rather than assumed.

**Four things this cost, recorded because they will happen again:**
- **Uploads ADD, and nothing saves without `Save changes`.** The first pass
  uploaded all three files, read them back as present, and reopened to find the
  old list — because the editor had never been saved. The ClaimGate ledger
  already knew uploads add rather than replace; it did not record that they do
  not persist until saved.
- **My file-list parser attributed one `Actions` button to several rows.** It
  searched backwards N lines for the nearest `Actions` ref, so the first two
  files both reported `ref e72`. The accessibility tree groups each file in its
  own `- group [ref=e..]`; parsing the group is the correct unit. A wrong ref
  here means deleting the wrong file off a live listing.
- **The row's `Actions` control only exists after hovering that row**, and the
  refs are re-issued every time the tree is re-read, so hover-then-re-read-then-
  click targeted the wrong row. Re-opening the page between the hover and the
  click is what made the ref honest.
- **Inno Setup names its uninstall key after the AppId GUID, not the app.** The
  CI assertion I wrote looked for `...\Uninstall\SimScan` and failed against an
  installer that had installed perfectly. CI now reads the Add/Remove list and
  matches `DisplayName`, and prints every entry it saw before giving up.

**TOTAL: $0.00** — an installer that finally agrees with itself is not a sale, and
the listing still reads 0 sales.

## 2026-09-30 (fifteenth tick) — the shop's installer is now installable by a
## package manager, which turned a blocked item into a business decision

The Windows Package Manager (`winget`) is the Windows default and SimScan
appears nowhere in it. Adding it was work-queue item 15, blocked only on the
installer disagreeing with itself about its own version — which v1.0.2 fixed.
This tick did the part that is mine and stopped at the one line that is not.

**Item 17 is settled with a measurement, not with an argument.** The open
question was whether the manifest should point at the free GitHub release or
the US$14 Gumroad listing. Measured: the release asset is already **public and
unauthenticated** — a plain `curl` returns HTTP 200 and the published
`SHA256SUMS.txt` downloads with no credentials at all — so a manifest pointing
there gives away **nothing that is not already free**, and winget's own policy
requires an installer URL discoverable from the publisher, which a paywalled
URL is not (`winget install SimScan` would fail for anyone who had not paid).
So the decision is the public release, and it is a decision the evidence made.

**Built, derived from one source, and asserted against the published release:**
three manifests (`version` / `locale` / `installer`, schema 1.12.0) at
`~/simscan/winget/manifests/s/SimScan/SimScan/1.0.2/`. All three validate with
**zero errors** against the official 1.12.0 JSON schemas, fetched from `aka.ms`.
`scripts/check_winget_manifest.py` asserts the version against
`simscan/__init__.py`, the URL against the release path, the scope against the
`[Setup]` section's `PrivilegesRequired=lowest`, and — with `--release` — the
hash against the release's **own published `SHA256SUMS.txt`**, which matched:
`e83189ea…46af481`. `AppsAndFeaturesEntries` asserts `DisplayVersion 1.0.2`,
the exact check the v1.0.1 drift failed.

**Proven able to fail: 8/8 real faults refused,** including a manifest that
points at the Gumroad listing, and a well-formed but wrong hash. That last case
**caught a gap in my own test first**: the initial test file ran every case
offline and reported 7/8, and the missing one was the test's fault, not the
checker's — the checker cannot compare a hash it never fetches. Recorded because
a guard reported as 8/8 when it is really 7/8 is the sort of thing this ledger
exists to prevent. Suite 50 → 53.

**Two of winget-pkgs' own pre-submission checks were run and pass:** no other
open or closed PR mentions SimScan (0), no manifest for it exists (0 code hits,
no `manifests/s/SimScan` directory), and it is listed in neither the repository
nor `search/code`.

**Stopped at the one line that is not mine: the Contributor License Agreement.**
`microsoft/winget-pkgs` requires a signed Microsoft CLA, checked by their bot at
PR time, and the PR template's first checkbox is that signature. That is a legal
agreement, not a formality, and it is the account holder's to make rather than
mine to accept for them — the same line this ledger already drew for identity
work. Everything up to it is done and pushed (`8b795b1`).

**Also this tick: the standing shop check was run, not assumed.** Exit 0 on all
three listings published at 14900 / 1400 / 0 cents, the launch link still landing
on `39/149` of list and not reaching SimScan, checkout still offering the code
field — re-run deliberately *because* editing a live listing is what took SimScan
off sale on 2026-09-30.

**TOTAL: $0.00** — a product a package manager can install is not a sale, and
the shop has still sold nothing.


## 2026-09-30 (seventeenth tick) — the pages we send buyers to were a dead end,
## and nothing had ever read them

Work-queue item 16. Item 9 checks the *shop* every tick. Nothing had ever read
the two **GitHub Pages product sites** — the pages a buyer actually arrives from
— and the same fault had already shipped twice on the channel's site next door:
a promise with no link to the thing it promised, and a page with no path back.

**Read as a stranger, page by page. Four faults, all live:**

1. **`simscan/sample-report.html` was a dead end.** The landing page's own
   section — "A real report, not a mock-up" — invites a buyer to *"Open the full
   HTML report"*. That page is the single best evidence the product works, and
   it carried **no link back to the site and no way to buy**. A stranger who
   opened it had nowhere to go. Measured, not assumed: `href` count → zero
   links to `caseone115.github.io/simscan/`, zero to the shop.
2. **`claimgate/SUPPORT.html` and `claimgate/UNBLOCK.html`** — both published
   and served by Pages from `docs/` — carried **no buy link either**.
3. **`UNBLOCK.html` quoted the wrong price.** It said "Price: US$149 one-off"
   against a shop charging US$39 through the launch link. **Corrected after
   reading the captured pages rather than trusting this note's first version,
   which said "both": `SUPPORT.html` already carried the launch price
   correctly.**
4. **The Article 50 guide's nav pointed at a section that does not exist.**
   `editorial-exemption.html` linked `./#get`; `index.html`'s ids are
   `contact`/`how`/`pricing`/`why`. It renders as a working link and scrolls
   nowhere.

**Fixed, and read back:**
- The report fix went into **the product's own `to_html()`**, not just the
  published sample — so the sample stays honestly "unedited engine output" and
  every buyer's own report carries the links. `simscan` `d463436`; suite 53 → 56
  (the suite asserted the report was *written* and had never asserted what was
  *in* it).
- `SUPPORT.md` and `UNBLOCK.md` now carry the buy link and the launch price.
  **The first attempt failed and the check caught it:** Jekyll does not linkify
  bare URLs, so the URL read fine in the source and was still not clickable
  live. Converted to markdown links. `claimgate` `38550b4`, `8aed5a1`.
- The nav link now points at `./#pricing`, a section that exists.

**The instrument, so it cannot recur:** `~/revenue-portfolio/scripts/check_sites.py`
reads both sites' published pages every tick and fails if any page has lost its
way to the shop, is a dead end, has a fragment link with no matching id, has an
internal `.html` link that is not a published page, or **advertises a price the
live listing cannot charge** (the price is read from the shop, not from a
constant). Rules are a pure `evaluate()`; `scripts/test_check_sites.py` drives
them over the real faults as fixtures — **26/26** — including a replay of the
site *as it was*, captured to `state/evidence/sites-prefix-2026-09-30/` before
the fix, which the checker fails on by name.

**Two of my own mistakes were caught by the fixtures, and are recorded because
that is the point of writing them:** (a) `./#how` was checked against the ids of
the page it was written on rather than the home page's, so a working nav link
was reported broken; (b) the home-page normaliser only understood relative
forms, so the published `SUPPORT.html` — which links home absolutely — was
reported as a dead end too. Both fixed; neither would have been seen without
fixtures. A checker that has never been seen to fail is not a checker, and one
that has never been seen to pass is not one either.

`scripts/tick_checks.sh` runs the shop check and the site check together, so a
tick cannot quietly skip one. Both green at 2026-09-30 23:12 AEST.

**TOTAL: $0.00** — a working route to the till is not a sale, and the shop has
still sold nothing.


## 2026-10-01 (eighteenth tick) — nothing we had built could be found by any
## search engine, and it had never been checked because it cannot be checked from inside

Work-queue item 2 (distribution is the binding constraint), worked on the one
surface of it that is not blocked on an account.

**Measured first, on the live web. Not assumed.**

- A `site:` query for our own host on Bing returned **none of our pages** — the
  result set was filled with unrelated sites (zhihu.com, baidu.com).
- A quoted-URL query for `"caseone115.github.io/simscan"` returned **none of our
  pages** (the results were coles.com.au).
- A product-name query returned **none of our pages**.
- All four hosts — `claimgate/`, `simscan/`, `madetoorder/`, and the root —
  answered **404 for both `robots.txt` and `sitemap.xml`**. Not one of the four
  sites had ever told a search engine it existed.
- Read from the account itself, not from the shop page: **224 views in the last
  30 days, 0 sales, 0 paid** on all three products, and every single view is
  attributed to *Direct, email, IM*. **Not one view has come from search.**

So thirteen pages were live, linked to one another, and unreachable by the one
free discovery route that exists. This is the same class of fault as the
seventeenth tick, one level out: the *site* joined up with itself and joined up
with nothing else.

**Fixed and read back.**

- `robots.txt` and `sitemap.xml` written for all four sites. **A URL is only
  written into a sitemap if it answers 200 on the live web at that moment** — a
  sitemap listing a 404 is a false statement a crawler will act on.
- An IndexNow key file published on all four hosts. Key is 32 hex characters,
  inside the protocol limit of 8–128.
- All thirteen URLs submitted via IndexNow: `api.indexnow.org` → **200**,
  `www.bing.com/indexnow` → **200**, `yandex.com/indexnow` → **202
  `{"success":true}`**. Accepted by every engine.
- Committed and pushed: `claimgate` `ff16e4b`, `simscan` `d92a9cc`,
  `madetoorder` `b910f3a`, root site `cf94858`. All nine artifacts verified
  live (HTTP 200) afterwards.

**The instrument, so it cannot recur:** `scripts/check_search_visibility.sh`
reads every robots.txt, every sitemap, every key file and **every URL inside
every sitemap** back from the live web on each tick, and fails if any of them is
missing or answers anything but 200. It is wired into `scripts/tick_checks.sh`.

**Two of my own mistakes were caught by fixtures, and are recorded because that**
**is the point of writing them:**

1. The sitemap-coverage rule first matched only bare `page.html` hrefs. On
   claimgate the href is `./editorial-exemption.html`, so the rule found **zero**
   pages and **reported a PASS** — a vacuous green, the exact failure this
   ledger keeps recording. Caught by driving the rule over that site's real
   hrefs and noticing it had found nothing. It now strips `./` and **refuses to
   pass on an empty page list**.
2. The same rule then flagged `index.html` as a missing page on madetoorder.
   `index.html` *is* the home page and is already listed as the directory URL, so
   that was a false alarm, not a fault. Excluded. (The sibling checker made this
   identical mistake once — a normaliser that understood only the relative form
   called a working link broken.)

`scripts/test_search_visibility.sh` drives both rules and the sitemap-liveness
rule over real faults as fixtures — **7/7**, including fixtures 3 and 4, which
are the vacuous-pass bug itself and the empty-page-list case, and fixture 5, the
false alarm above. Proven able to fail: fixture 5 failed on the first run
(because the *fixture* pointed at the wrong path) and passed once the fixture
was corrected, which is the right way round.

`scripts/tick_checks.sh` now runs the shop check, the site check, the search
check and both fixture suites together. **All green, exit 0, 2026-10-01 01:48
AEST.**

**TOTAL: $0.00** — being findable is not being bought, and the shop has still
sold nothing. The number that matters next is whether the 0-of-224 search
referral figure moves.
