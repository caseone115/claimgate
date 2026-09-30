# ClaimGate for MCP clients

An MCP server that gates marketing copy **before** it publishes. Give it a
draft and whatever evidence you already hold; it reports which claims cannot be
tied to that evidence, which of your own policy rules the draft breaks, and
whether a required AI disclosure is missing.

It is a checker, not a writer. It does not browse, does not invent facts, and
does not write your copy.

## Tools

| Tool | What it does |
|---|---|
| `check_draft` | The check, as a plain-English report a person can read. |
| `check_draft_json` | The same check as JSON, for a pipeline or CI gate. Gate on `summary.blocked`. |
| `list_claims` | What the checker will demand substantiation for, without judging it. |
| `check_policy_only` | Your policy alone — prohibited claims and AI disclosure. No evidence, no model. |
| `about` | What this is, what it does not do, and how to verify it. |

## Run it from this repository

Add to your MCP client's config (`claude_desktop_config.json`, `mcp.json`, or
equivalent). Nothing needs installing first — `uv` fetches the one dependency:

```json
{
  "mcpServers": {
    "claimgate": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/claimgate/mcp", "/path/to/claimgate/mcp/server.py"]
    }
  }
}
```

Or run it by hand to see it answer:

```bash
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"cli","version":"1"}}}' \
 | uv run --directory mcp mcp/server.py
```

## Install as a bundle

`mcp/manifest.json` is a valid MCP Bundle (MCPB) manifest, and the same server is
shipped as `claimgate-<version>.mcpb` on the
[releases page](https://github.com/caseone115/claimgate/releases). Open the
`.mcpb` file with a client that supports bundles (Claude Desktop on macOS and
Windows does) to install it in one step.

## What it will not do

* **It will not round "I cannot tell" up to "fine".** With no evidence, every
  claim comes back `unverified`; a number that appears in no evidence is
  `unsupported`; a model that is unreachable, unkeyed or malformed gives
  `unverified`. `unverified` blocks, because a gate that passes what it could
  not check is decoration.
* **It will not send your copy anywhere unless you ask it to.** With
  `use_model=false` nothing leaves the machine at all. With `use_model=true`,
  only the claim text and the evidence you passed in are sent, to a DeepSeek
  endpoint you supply a key for (`DEEPSEEK_API_KEY`), and only for the claims
  that survived the deterministic numeric check first.

## Tests

```bash
python3 scripts/test_mcp_server.py
```

This launches the real server as a subprocess and speaks MCP to it over stdio
through the official SDK's client — 19 checks, including that no evidence ever
yields `supported`, that a figure in no evidence blocks without a model
consulted, and that bad input is an error rather than a silent pass. The suite
is itself verified by injecting five real faults into the server and confirming
it catches every one.

## Disclosure

This software is written and maintained by automated software. Every ClaimGate
surface says so; so does this.
