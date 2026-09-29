"""The free starter kit: everything an organisation needs to gate a draft.

This is the product's front door. It is genuinely useful on its own — a policy
file, an evidence folder, a pre-publish checklist, a CI job — and it is what a
marketing team can adopt in an afternoon without buying anything.

It names ClaimGate once, in plain terms, and links to where the full engine
lives. That is the whole commercial relationship: no dark patterns, no
artificially crippled file, no expiry. A starter kit that is secretly broken
would be the same dishonesty the product exists to catch.
"""
from __future__ import annotations

from pathlib import Path

from .policy import Policy

POLICY_NOTE = """\
# This is the policy file. ClaimGate reads it and enforces it on every draft.

Every rule below is a claim this organisation is not allowed to publish, or is
only allowed to publish with evidence attached. Edit it: delete what does not
apply to you, add what does. The rules you write are the ones that get enforced
— the tool has no opinion of its own.

categories
    prohibited  the draft is blocked. Nothing publishing on a deadline without
                someone removing it.
    restricted  flagged, and blocks unless the draft carries the evidence the
                rule asks for.
    style       reported, never blocks.

severity
    high        treated as blocking for a prohibited or restricted rule.
    medium      reported; blocks only under --strict.
"""

DRAFT_TEMPLATE = """\
# Replace this file with the copy you are about to publish.

Paste a real draft in here — the one with the claims in it. Then run:

    claimgate check DRAFT-template.md --evidence evidence/ --policy policy.json --no-model

You will get back every figure, percentage, superlative and guarantee in the
draft, and a verdict on each. Anything that appears in the draft but not in the
evidence folder is reported as unsupported, and the run exits 1.
"""

EVIDENCE_README = """\
# Evidence

Drop in whatever you can actually point at: the product spec, the case study,
the signed-off figure, the security certificate, the paper. `.md`, `.txt` and
`.html` files in this folder are all read.

The one rule that matters

Every figure in a claim must appear in an evidence file. That check is a string
comparison, not a judgement call, so a number that was invented — by a model or
by a person at 5pm — cannot be talked into a pass. Write the numbers down
exactly as they appear in your source.

You can also point at a JSON array instead of a folder:

    [{"id": "spec", "title": "Product spec", "text": "Throughput is 1,400 rows
      per minute..."},
     {"id": "case-1", "title": "Meridian case study", "url": "https://..."}]
"""

CHECKLIST = """\
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

    pip install claimgate
    claimgate check draft.md --evidence evidence/ --policy policy.json

Exit code 1 means blocked, which is what makes it work in CI, a pre-commit hook
or a publishing pipeline. Full engine and test suite:
https://teeterbot.gumroad.com/l/claimgate/LAUNCH39 (US$39 while the launch
is running, US$149 after) — the source is MIT and public at
https://github.com/caseone115/claimgate, so read it before you pay for anything.
"""

KIT_README = """\
# ClaimGate starter kit

A publish gate for AI-assisted marketing copy, in a form you can adopt today.

    draft.md            the copy you are about to publish
    evidence/           what you can actually point at
    policy.json         the claims your organisation may not make
    CHECKLIST.md        the six questions, on one page
    .github/workflows/  the same gate running on every pull request

## Try it in one minute

    pip install claimgate
    claimgate check DRAFT-template.md --evidence evidence/ --policy policy.json --no-model

`--no-model` needs no API key and no network: it runs the deterministic checks.
The run exits 1 when something in the draft cannot be substantiated.

Then put a real draft in `DRAFT-template.md` and run it again. Most teams find
something on the first file they try.

## Wiring it into CI

`.github/workflows/claimgate.yml` is ready to copy into your repository. It runs
on every pull request that touches a `.md` file and fails the build when the copy
cannot be substantiated.

## What this kit is not

It is not a fact-checker — it does not search the web or decide what is true. It
decides whether *you* can substantiate what *you* wrote, against evidence *you*
supply, which is the question a compliance review actually asks. It is not legal
advice. It is not an AI detector: it does not guess whether text was AI-written.

## Where the rest of it is

This kit is the free part and it stays free. The full engine — claim extraction
across every category, model adjudication of each claim against the evidence,
JSON output for pipelines, and the 55-check engine test suite — is a one-off
download, US$39 while the launch is running and US$149 after it, at
https://teeterbot.gumroad.com/l/claimgate/LAUNCH39

The source is MIT licensed and public at
https://github.com/caseone115/claimgate. Nothing is held back from it. Read it,
and if it does not do what this page says, do not buy it.
"""

WORKFLOW = """\
# Gate the copy on every pull request.
# Copy to .github/workflows/ in your repository.
name: claimgate

on:
  pull_request:
    paths:
      - "**/*.md"

jobs:
  substantiation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install claimgate
      # --no-model keeps this deterministic and offline; it still catches every
      # figure that does not appear in evidence/, and every absolute claim.
      - run: |
          for draft in $(git diff --name-only origin/${{ github.base_ref }}...HEAD -- '*.md'); do
            echo "gating $draft"
            claimgate check "$draft" --evidence evidence/ --policy policy.json --no-model
          done
"""


def build(out: Path, *, force: bool = False) -> list[Path]:
    """Write the starter kit into `out`. Returns the files written."""
    out = Path(out)
    (out / "evidence").mkdir(parents=True, exist_ok=True)
    (out / ".github" / "workflows").mkdir(parents=True, exist_ok=True)

    files: dict[Path, str] = {
        out / "README.md": KIT_README,
        out / "CHECKLIST.md": CHECKLIST,
        out / "DRAFT-template.md": DRAFT_TEMPLATE,
        out / "evidence" / "README.md": EVIDENCE_README,
        out / ".github" / "workflows" / "claimgate.yml": WORKFLOW,
    }

    written: list[Path] = []
    for path, _ in files.items():
        if path.exists() and not force:
            raise FileExistsError(f"{path} already exists (use --force)")

    for path, text in files.items():
        path.write_text(text)
        written.append(path)

    policy_path = out / "policy.json"
    if policy_path.exists() and not force:
        raise FileExistsError(f"{policy_path} already exists (use --force)")
    Policy().save(policy_path)
    written.append(policy_path)

    notes = out / "policy-notes.md"
    notes.write_text(POLICY_NOTE)
    written.append(notes)

    return written
