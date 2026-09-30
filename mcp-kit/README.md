# ClaimGate starter kit for MCP clients — the free half

The free ClaimGate starter kit, as a tool an AI agent can call. It is listed in
the official MCP Registry as `io.github.caseone115/claimgate-kit`, and it needs
no account, no API key and no payment.

The paid engine is a separate entry, `io.github.caseone115/claimgate`; that is
the one that adjudicates each claim against your evidence.

## Tools

| Tool | What it does |
|---|---|
| `init_kit` | Writes a whole starter kit into a directory you name — policy, evidence folder, draft template, checklist, CI job. |
| `check_kit` | Runs that gate on a draft, offline: no API key, no network call. |
| `list_claims` | What the gate will demand substantiation for, without judging it. |
| `check_policy_only` | Your policy alone — prohibited claims and AI disclosure. No evidence, no model. |
| `about` | What this is, what it is not, and what the paid engine adds. |

## What `init_kit` writes

    YOUR-DIR/
      README.md                       what the kit is and how to run it
      CHECKLIST.md                    the six pre-publish questions
      DRAFT-template.md               put your real copy here
      policy.json                     the claims you may not make
      evidence/                       what you can actually point at
      .github/workflows/claimgate.yml the same gate on every pull request

It refuses to overwrite existing files unless you pass `force=true`, because a
kit that silently replaced someone's `policy.json` would be worse than no kit.

## Run it from this repository

Nothing needs installing first — `uv` fetches the one dependency:

```json
{
  "mcpServers": {
    "claimgate-kit": {
      "command": "uv",
      "args": ["run", "--directory", "<repo>/mcp-kit", "<repo>/mcp-kit/server.py"]
    }
  }
}
```

## What it will not do

* **It will not round "I cannot tell" up to "fine".** No evidence supplied means
  every claim comes back `unverified`, never `supported`. A figure that appears
  in no evidence you supplied *is* caught, by plain string comparison with no
  model consulted, because a fabricated number is not a judgement call. And
  because no model is consulted at all, `unverified` blocks — a gate that passes
  what it could not check is decoration.
* **It will not adjudicate a claim against your evidence.** That needs a model;
  the paid engine entry does it.
* **It will not send your copy anywhere.** There is no network call in this
  server at all.

## Tests

```bash
uv run --with mcp --python 3.12 python scripts/test_mcp_kit_server.py
```

31 checks, driving the real server as a subprocess over the official SDK's stdio
client, including that `init_kit` refuses to overwrite an existing policy and
that the freshly written kit runs its own gate. Verified able to fail by
injecting seven real faults: 7/7 caught.

## Disclosure

This software is written and maintained by automated software. Every ClaimGate
surface says so; so does this.
