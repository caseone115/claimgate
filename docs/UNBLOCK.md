# Unblock pack — connecting a payout rail

Everything needed to turn ClaimGate from a built machine into one that can
receive money. This is the only step that requires the account owner.

**Time: about 10 minutes. Cost: $0.**

---

## The short version

Use **Gumroad**, and choose **PayPal** as the payout method.

Gumroad's own help centre states that for PayPal payouts you "simply add your
name, address, phone number, and active PayPal account email. You do not need
to submit an ID or other documents for PayPal payouts."

Bank payouts are heavier — Stripe (Gumroad's processor) is bound by Know Your
Customer obligations and will ask for a government ID number, a photo of your
ID front and back, and proof of address. All of that is avoidable for now by
using the PayPal route. You can switch to bank payouts later once there is
more than a test sale to move.

---

## Step 1 — Gumroad account (3 min)

1. Go to https://gumroad.com and click **Start selling**.
2. Sign up with an email address you control.
3. Verify the email when it arrives.

## Step 2 — Payout settings (4 min)

1. In Gumroad: **Settings → Payments**.
2. Under payout method, choose **PayPal**.
3. Enter:
   - your **full legal name**
   - a **physical address** (Gumroad does not accept PO boxes)
   - a **phone number**
   - the **email address of an active PayPal account**
4. Save.

If PayPal is not offered as an option in your region, the fallback is a bank
payout: Australia is supported for AUD. That route will ask for a government
ID number, a colour photo of your ID (front and back, JPEG or PNG — not a
PDF), and proof of address. Same account, heavier paperwork.

## Step 3 — Create the product (3 min)

I will send you the exact listing text, the price, and the files. You paste
them in and hit publish. Nothing to write.

---

## What I need back from you

Only this, once it exists:

- **The Gumroad product URL** (so I can point the landing page at it)

That is the whole handshake. I do not need — and must not be given — your
bank details, tax file number, ID documents or PayPal password. The account
stays entirely under your control; I never touch the payout settings.

---

## Why this is the blocker and why I cannot do it

Every payment rail — Gumroad, Stripe, PayPal, Lemon Squeezy — is required by
financial regulation to verify that the person receiving money is a real,
identified human. That is Know Your Customer law, not a permissions setting.

An AI agent cannot pass identity verification, and it must not try: supplying
someone else's identity documents, or inventing an identity to satisfy a KYC
check, is fraud. So this one step is genuinely yours, and it is the only one.

## What happens the moment it exists

1. The product goes live within minutes of you pasting the listing.
2. The daily job at 08:00 starts pointing outreach at the real purchase link.
3. The first sale is possible immediately — there is no approval queue beyond
   Gumroad's standard account review.

## Notes on cost

- Gumroad: 10% flat fee per sale. No monthly fee. Minimum payout $10.
- PayPal: its own transaction fee applies.
- There is no charge for creating the account or the product listing.

## If you would rather not use Gumroad

Any of these work equally well; the code does not care, only the link does:

| Rail | Fee | ID documents needed |
|---|---|---|
| Gumroad + PayPal | 10% + PayPal fees | **No** |
| Gumroad + bank (AU) | 10% | Yes — ID + proof of address |
| Stripe direct | ~1.7% + 30c | Yes — business/bank details |
| Lemon Squeezy | 5% + 50c | Yes, and it is merchant of record |

Gumroad with PayPal is the fastest by a wide margin.
