# Pre-publish check — AI-assisted marketing content

Six questions. If you cannot answer one, that is the finding.

## 1. Can you point at the source of every number?

Every percentage, figure, price, ranking and date in the draft should exist in a
document you can produce. Not "it came from the model" and not "a colleague said
so". If it does not exist in a file, it does not exist.

## 2. Which claims are absolute?

"Guaranteed", "100%", "always", "never", "eliminates", "risk-free". In most
jurisdictions an absolute guarantee is unenforceable and is treated as misleading
advertising — the problem is not that it might be untrue, it is that it cannot be
made true.

## 3. Do you name a competitor?

Comparative advertising is lawful in most markets but has its own rules and is a
standing invitation to a complaint. Comparing against the customer's current
situation, or against a category, carries none of that risk and reads better.

## 4. Is there a health, financial or safety outcome in the copy?

These are regulated claims almost everywhere. They usually need authorisation,
a named professional, or a mandatory risk statement — and the marketing team is
rarely the function that knows which.

## 5. Does the asset need an AI disclosure?

The EU AI Act's transparency obligations (Article 50) applied from 2 August 2026
and require disclosure in specified circumstances — including where synthetic
text is published to inform the public on matters of public interest, and where
synthetic media is used. Meta, TikTok and Google separately require an AI label
on realistic synthetic media in ads. This is a property of the asset, not of the
copy, so it is the one item on this list that no amount of good writing fixes.

    Which AI systems produced or edited this asset?
    Is any of it published to inform the public on a matter of public interest?
    Does it contain a realistic depiction of a real or seemingly real person?
    Has the platform label been applied, as well as any disclosure in the copy?

This section is a checklist, not legal advice. Your counsel decides what applies
to you.

## 6. Who has signed this off, and against what?

Name the approver and the rule they approved against. "Marketing approved it" is
not a record; "J. Smith cleared the throughput figure against the 2026-06 spec"
is.

---

## Making it mechanical

A checklist is followed until the week it is inconvenient. The free ClaimGate
starter kit turns questions 1-3 and 5 into a command that exits non-zero:

    pip install "claimgate @ git+https://github.com/caseone115/claimgate"
    claimgate check draft.md --evidence evidence/ --policy policy.json

Exit code 1 means blocked, which is what makes it work in CI, a pre-commit hook
or a publishing pipeline. Full engine and test suite:
https://teeterbot.gumroad.com/l/claimgate/LAUNCH39 (US$39 while the launch
is running, US$149 after) — the source is MIT and public at
https://github.com/caseone115/claimgate, so read it before you pay for anything.
