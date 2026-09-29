# ClaimGate starter kit

A publish gate for AI-assisted marketing copy, in a form you can adopt today.

    draft.md            the copy you are about to publish
    evidence/           what you can actually point at
    policy.json         the claims your organisation may not make
    CHECKLIST.md        the six questions, on one page
    .github/workflows/  the same gate running on every pull request

## Try it in one minute

    pip install "claimgate @ git+https://github.com/caseone115/claimgate"
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

Install it from that repository, not by the bare name: `pip install claimgate`
on PyPI is a different, unrelated project (an AI-agent test harness) and it
has no `claimgate check` command at all.
and if it does not do what this page says, do not buy it.
