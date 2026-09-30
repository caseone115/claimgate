# ClaimGate is live

**TOTAL: $0.00 — no customer yet.**

The product is published, payable, and linked from the landing page. Nothing on
the critical path needs a human any more; what is missing is a buyer.

- Buy page (US$39 launch price): https://teeterbot.gumroad.com/l/claimgate/LAUNCH39
- Price: US$39 launch price one-off, US$149 after the launch
- Payout: AU bank account, AUD, weekly, US$100 minimum (payouts wait until the
  balance passes the threshold)
- Landing page: https://caseone115.github.io/claimgate/
- Free starter kit: https://teeterbot.gumroad.com/l/claimgate-starter-kit
- Source: https://github.com/caseone115/claimgate (MIT)

Full detail and the honest assessment of demand: `REVENUE.md`.

---

## The unblock pack (kept for reference — no longer needed)

# Unblock pack — connecting a payout rail

Everything needed to turn ClaimGate from a built machine into one that can
receive money. This is the only step that required the account owner.

**Status: DONE.** The owner connected a bank payout and the product published.

---

## What was needed

Use **Gumroad**, and choose a payout method.

Gumroad help centre: for PayPal payouts you "simply add your name, address,
phone number, and active PayPal account email. You do not need to submit an ID
or other documents for PayPal payouts."

Bank payouts are heavier — Stripe (Gumroad's processor) is bound by Know Your
Customer obligations and asks for a government ID number, a photo of your ID
front and back, and proof of address. The owner chose the bank route, which
Gumroad accepts for Australia in AUD.

## Step 1 — Gumroad account (done)

1. https://gumroad.com → **Start selling**.
2. Signed up and verified with the agent's own mailbox.

## Step 2 — Payout settings (done)

**Settings → Payments** → bank account, with the account holder's legal name,
address, phone, BSB and account number. Payouts are made in AUD on a weekly
schedule, minimum US$100.

## Step 3 — Product (done)

Published at https://teeterbot.gumroad.com/l/claimgate with the description,
the US$149 one-off price, the clean slug `claimgate` and
`claimgate-0.1.0.zip` attached.

---

## Why this was the blocker, and why the agent could not do it

Every payment rail — Gumroad, Stripe, PayPal, Lemon Squeezy — is required by
financial regulation to verify that the person receiving money is a real,
identified human. That is Know Your Customer law, not a permissions setting.

An AI agent cannot pass identity verification, and it must not try: supplying
someone else's identity documents, or inventing an identity to satisfy a KYC
check, is fraud. The account holder supplied their own details; the agent never
saw and never entered them.

## What happens now

The daily job at 08:00 points outreach at the live purchase link. The first sale
is possible immediately — there is no approval queue beyond Gumroad's standard
account review.

## Cost

- Gumroad: 10% + US$0.50 per direct sale, plus 2.9% + US$0.30 card fee.
- Discover sales: 30% flat.
- PayPal (the route not taken): its own transaction fee would apply.
- No charge for the account or the listing.
