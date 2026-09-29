# Replace this file with the copy you are about to publish.

Paste a real draft in here — the one with the claims in it. Then run:

    claimgate check DRAFT-template.md --evidence evidence/ --policy policy.json --no-model

You will get back every figure, percentage, superlative and guarantee in the
draft, and a verdict on each. Anything that appears in the draft but not in the
evidence folder is reported as unsupported, and the run exits 1.
