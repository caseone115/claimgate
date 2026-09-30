#!/usr/bin/env python3
"""ClaimGate MCP server - substantiate marketing claims before they publish.

WHAT THIS IS
------------
A local MCP server that runs a check, not a generator. You give it a draft of
marketing copy and whatever evidence you already hold (a policy page, a study
abstract, a price list, a product spec). It answers with the claims it found,
the ones it cannot tie to any supplied evidence, the rules of your own policy
the draft breaks, and whether a required AI disclosure is missing.

WHY IT FAILS CLOSED
-------------------
The honest answer to "is this claim substantiated" is sometimes "I cannot
tell". This server is built so that answer is never rounded up to "yes":
  * no evidence supplied -> every claim comes back `unverified`, never
    `supported`;
  * a number in the claim that appears in no evidence -> `unsupported`
    from a plain string comparison, with no model consulted, because a
    fabricated figure is not a judgement call;
  * no model key configured, model unreachable, or a malformed reply ->
    `unverified`. Never `supported`.

It does not invent facts, does not browse, and does not write copy. Every
finding quotes the text it is about.

TRANSPORT
---------
stdio. All output on stdout is protocol JSON-RPC. Diagnostics go to stderr and
are never sent to the model, because a server that leaks its own errors into
the transcript is a server that ends up in someone's logs.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Works in two layouts with one line each:
#   repo:   claimgate/mcp/server.py          -> imports ../claimgate
#   bundle: <bundle>/server/server.py       -> imports ./claimgate
_HERE = Path(__file__).resolve().parent
for _cand in (_HERE, _HERE.parent):
    if (_cand / "claimgate" / "__init__.py").is_file():
        sys.path.insert(0, str(_cand))
        break
else:
    sys.stderr.write(
        "claimgate-mcp: could not find the 'claimgate' package next to this "
        f"file (looked in {_HERE} and {_HERE.parent}).\n")
    raise SystemExit(2)

from claimgate.claims import extract, summarise                      # noqa: E402
from claimgate.htmltext import to_text                               # noqa: E402
from claimgate.policy import Policy, check_policy                    # noqa: E402
from claimgate.substantiation import Evidence, assess_all, report   # noqa: E402

# The MCP Python SDK renamed its high-level server class between generations:
# 1.x exposes ``mcp.server.fastmcp.FastMCP`` and 2.x exposes
# ``mcp.server.MCPServer``. Both carry the same ``.tool()`` decorator and
# ``.run()`` entry point, so supporting both is a two-line shim rather than a
# version pin that would break a user's environment for no reason.
try:
    from mcp.server.fastmcp import FastMCP              # SDK 1.x
    SDK_FAMILY = "fastmcp (SDK 1.x)"
except Exception:                                        # noqa: BLE001
    try:
        from mcp.server import MCPServer as FastMCP      # SDK 2.x
        SDK_FAMILY = "MCPServer (SDK 2.x)"
    except Exception as exc:                             # noqa: BLE001
        sys.stderr.write(
            "claimgate-mcp: the 'mcp' Python package is required and could not "
            f"be imported ({exc}).\nInstall it with: pip install mcp\n")
        raise SystemExit(2)

VERSION = "0.1.0"
SERVER_NAME = "io.github.caseone115/claimgate"
MAX_DRAFT_CHARS = 400_000
MAX_EVIDENCE_FILE_BYTES = 2_000_000
EVIDENCE_SUFFIXES = (".txt", ".md", ".html", ".htm")

# Both SDK generations accept name; only 2.x accepts the descriptive fields,
# so they are passed best-effort rather than pinning one SDK generation.
try:
    mcp = FastMCP("claimgate", title="ClaimGate",
                  description=("Check marketing copy against the evidence you "
                               "hold, before it publishes."),
                  version=VERSION,
                  website_url="https://caseone115.github.io/claimgate/")
except TypeError:
    mcp = FastMCP("claimgate")


# --------------------------------------------------------------------- helpers

def _read_draft(draft: str, draft_path: str) -> tuple[str, str]:
    """Return (text, source label). Exactly one of the two inputs is required."""
    if draft and draft_path:
        raise ValueError("give either `draft` or `draft_path`, not both")
    if draft_path:
        p = Path(draft_path).expanduser()
        if not p.is_file():
            raise ValueError(f"draft_path does not exist or is not a file: {p}")
        raw = p.read_text(errors="replace")
        if p.suffix.lower() in (".html", ".htm"):
            raw = to_text(raw)
        return raw, str(p)
    if not draft.strip():
        raise ValueError("`draft` is empty; supply the copy to check")
    return draft, "draft (inline)"


def _load_evidence(evidence_dir: str, evidence_json: str) -> list[Evidence]:
    """Evidence from a directory of readable files, or an inline JSON array.

    A file that a reader would see as empty is skipped rather than offered as
    evidence, because an empty source silently supports nothing and a claim
    checked against it would come back unsupported for the wrong reason.
    """
    out: list[Evidence] = []
    if evidence_json.strip():
        data = json.loads(evidence_json)
        items = data if isinstance(data, list) else data.get("evidence", [])
        for i, item in enumerate(items, 1):
            if isinstance(item, str):
                out.append(Evidence(id=f"e{i}", text=item))
            else:
                out.append(Evidence(
                    id=str(item.get("id") or f"e{i}"),
                    text=str(item.get("text", "")),
                    title=str(item.get("title", "")),
                    url=str(item.get("url", ""))))
    if evidence_dir:
        root = Path(evidence_dir).expanduser()
        if not root.is_dir():
            raise ValueError(f"evidence_dir is not a directory: {root}")
        files = sorted(p for p in root.rglob("*")
                       if p.is_file() and p.suffix.lower() in EVIDENCE_SUFFIXES)
        for f in files:
            if f.stat().st_size > MAX_EVIDENCE_FILE_BYTES:
                continue
            raw = f.read_text(errors="replace")
            text = to_text(raw) if f.suffix.lower() in (".html", ".htm") else raw
            if not text.strip():
                continue
            out.append(Evidence(id=f.stem, text=text, title=f.name, url=str(f)))
    return out


def _check_text(text: str, label: str, evidence: list[Evidence],
                policy: Policy, use_model: bool) -> dict:
    claims = extract(text)
    findings = check_policy(text, policy)

    verdicts = []
    if use_model and evidence:
        verdicts = assess_all(claims, evidence)
    elif evidence:
        # Deterministic half only: the numeric gate still runs, so a figure
        # absent from every source is caught without any model call.
        from claimgate.substantiation import Verdict, numbers_supported
        for c in claims:
            missing = numbers_supported(
                c.text, " ".join(e.text for e in evidence))[1]
            if missing:
                verdicts.append(Verdict(
                    c, "unsupported", reason=(
                        "the figure(s) %s in this claim appear in no supplied "
                        "evidence" % ", ".join(missing[:4]))))
            else:
                verdicts.append(Verdict(
                    c, "unverified", reason=(
                        "model adjudication was not requested, so this claim "
                        "has been left unverified rather than assumed true")))
    else:
        from claimgate.substantiation import Verdict
        verdicts = [Verdict(c, "unverified", reason=(
            "no evidence was supplied, so this claim cannot be substantiated "
            "here at all")) for c in claims]

    sub = report(verdicts) if verdicts else {
        "total": 0, "by_verdict": {}, "blocking": 0, "clear": True}
    stats = summarise(claims)
    blocking_policy = [f for f in findings if f.blocking]
    blocked = bool(sub["blocking"]) or bool(blocking_policy)

    return {
        "draft": label,
        "policy": {"name": policy.name,
                   "disclosure_required": policy.disclosure_required},
        "claims": [c.as_dict() for c in claims],
        "verdicts": [v.as_dict() for v in verdicts],
        # as_dict() carries the raw severity, not the derived `blocking` flag;
        # the flag is what a caller gates on, so it is added rather than left
        # for every consumer to re-derive (and get wrong).
        "policy_findings": [dict(f.as_dict(), blocking=f.blocking)
                            for f in findings],
        "summary": {**stats, **sub, "blocked": blocked,
                    "evidence_items": len(evidence)},
    }


def _plain(result: dict) -> str:
    """A report written to be read, not parsed: the same facts, in sentences."""
    claims = result["claims"]
    verdicts = result["verdicts"]
    findings = result["policy_findings"]
    s = result["summary"]

    if not claims and not findings:
        return ("No claims that need substantiation were found, and no policy "
                "rule was broken. That is not a statement that the copy is "
                "true - it is a statement that nothing in it was checkable "
                "here.")

    lines = [f"Checked: {result['draft']}",
             f"Policy: {result['policy']['name']} · "
             f"AI disclosure required: {result['policy']['disclosure_required']} · "
             f"{s['evidence_items']} evidence item(s) supplied",
             "",
             f"Claims requiring substantiation: {len(claims)}"]

    by_verdict: dict[str, list] = {}
    for v in verdicts:
        by_verdict.setdefault(v["verdict"], []).append(v)
    for name in ("unsupported", "contradicted", "unverified",
                 "partially_supported", "supported"):
        group = by_verdict.get(name)
        if not group:
            continue
        lines.append("")
        lines.append(f"  {name.replace('_', ' ')} ({len(group)})")
        for v in group:
            lines.append(f"    - [{v['category']}] {v['claim'][:110]}")
            if v["reason"]:
                lines.append(f"      {v['reason'][:200]}")
            if v["suggested_rewrite"]:
                lines.append(f"      could say: {v['suggested_rewrite'][:160]}")

    if findings:
        lines += ["", f"Policy findings: {len(findings)}"]
        for f in findings:
            flag = "blocking" if f["blocking"] else "advisory"
            lines.append(f"    - [{flag}] [{f['kind']}] "
                         f"{(f['text'] or f['kind'])[:90]}")
            if f["reason"]:
                lines.append(f"      {f['reason'][:200]}")
            if f["fix"]:
                lines.append(f"      fix: {f['fix'][:160]}")

    lines += ["", "VERDICT: BLOCKED - do not publish as it stands."
              if s["blocked"] else
              "VERDICT: CLEAR - every claim found is substantiated by the "
              "supplied evidence and no policy rule was broken."]
    if not result["policy"]["disclosure_required"]:
        lines += ["", "Note: no AI-disclosure requirement was detected in "
                  "this draft. If the copy was AI-assisted and is "
                  "customer-facing, that is itself worth a second look."]
    return "\n".join(lines)


# ----------------------------------------------------------------------- tools

@mcp.tool()
def check_draft(draft: str = "", draft_path: str = "",
                evidence_dir: str = "", evidence_json: str = "",
                policy_json: str = "", use_model: bool = True) -> str:
    """Check one piece of marketing copy against the evidence you hold.

    Returns a plain-English report of which claims cannot be substantiated,
    which of your own policy rules the draft breaks, and whether an AI
    disclosure is missing. Read the summary first: it is written to be read by
    a person, and the machine-readable detail is available from check_draft_json.

    ARGUMENTS
      draft          the copy to check, inline. Give this or draft_path.
      draft_path     path to a .md/.txt/.html file to check instead.
      evidence_dir   a folder of files to treat as evidence (.txt/.md/.html).
                     Everything in it is offered to the checker; nothing is
                     uploaded anywhere.
      evidence_json  evidence as a JSON array, e.g.
                     [{"id":"pricing","text":"The plan is $39/month"}]
      policy_json    your own policy file, from `claimgate init-policy`. Omit
                     to use the built-in defaults.
      use_model      false runs only the deterministic checks - no network, no
                     API key. A claim that cannot be decided that way comes
                     back `unverified`, never `supported`.

    WHAT IT WILL NOT DO
      It does not decide that a claim is true because it sounds reasonable.
      If it cannot tell, it says so. A green tick here means an evidence file
      you supplied actually states the claim's substance.
    """
    if len(draft) > MAX_DRAFT_CHARS:
        raise ValueError(f"draft is longer than {MAX_DRAFT_CHARS} characters")
    text, label = _read_draft(draft, draft_path)
    policy = Policy.load(policy_json) if policy_json else Policy()
    evidence = _load_evidence(evidence_dir, evidence_json)
    result = _check_text(text, label, evidence, policy, use_model)
    return _plain(result)


@mcp.tool()
def check_draft_json(draft: str = "", draft_path: str = "",
                     evidence_dir: str = "", evidence_json: str = "",
                     policy_json: str = "", use_model: bool = True) -> str:
    """The same check as check_draft, returned as structured JSON.

    Use this when a pipeline, a CI job or another agent needs to gate on the
    result rather than read it. Keys: claims, verdicts, policy_findings,
    summary. `summary.blocked` is the boolean to gate on, and it is true when
    any claim is unsupported, contradicted or unverified, or any policy
    finding is blocking. Unverified counts as blocked on purpose: unknown is
    not the same as fine, and a gate that treats it as fine is decoration.
    """
    text, label = _read_draft(draft, draft_path)
    policy = Policy.load(policy_json) if policy_json else Policy()
    evidence = _load_evidence(evidence_dir, evidence_json)
    result = _check_text(text, label, evidence, policy, use_model)
    return json.dumps(result, indent=2)


@mcp.tool()
def list_claims(draft: str = "", draft_path: str = "") -> str:
    """List the claims in a draft and what each one needs, without judging them.

    Useful as a first pass: it shows what the checker will demand substantiation
    for, so you can judge whether your evidence folder is even the right shape.
    Categories include statistic, percentage, superlative, comparative,
    guarantee, efficacy, temporal, attribution, absolute and causal.
    """
    text, label = _read_draft(draft, draft_path)
    claims = extract(text)
    if not claims:
        return (f"No checkable claims were found in {label}. Claims are "
                "numbers, comparisons, guarantees, named sources, dated "
                "facts and causal statements - not opinions.")
    lines = [f"{len(claims)} claim(s) in {label}:", ""]
    for c in claims:
        lines.append(f"  [{c.severity:6}] [{c.category:12}] {c.text[:110]}")
        lines.append(f"           needs: {c.needs}")
    lines += ["", f"Summary: {summarise(claims)}"]
    return "\n".join(lines)


@mcp.tool()
def check_policy_only(draft: str = "", draft_path: str = "",
                      policy_json: str = "") -> str:
    """Check a draft against a policy alone - prohibited claims and AI disclosure.

    This is the half that needs no evidence and no model: the constitutional
    layer. It answers "would our own rules let this out of the door", which is
    a different question from "is it true".
    """
    text, label = _read_draft(draft, draft_path)
    policy = Policy.load(policy_json) if policy_json else Policy()
    findings = check_policy(text, policy)
    if not findings:
        return (f"No policy breaches found in {label} against "
                f"'{policy.name}'. That is not a clearance: policy covers "
                f"prohibited wording and disclosure, not truth.")
    blocking = sum(1 for f in findings if f.blocking)
    lines = [f"{len(findings)} policy finding(s) in {label} "
             f"({blocking} blocking):", ""]
    for f in findings:
        lines.append(f"  [{'blocking' if f.blocking else 'advisory'}] "
                     f"[{f.kind}] {(f.text or f.kind)[:100]}")
        lines.append(f"      {f.reason[:200]}")
        if f.fix:
            lines.append(f"      fix: {f.fix[:160]}")
    return "\n".join(lines)


@mcp.tool()
def about() -> str:
    """What this server is, what it does not do, and how it can be trusted.

    Read this before relying on any verdict it returns.
    """
    return (
        "ClaimGate - a publish gate for AI-assisted marketing copy.\n"
        f"Server: {SERVER_NAME} {VERSION} (MCP SDK: {SDK_FAMILY})\n"
        "\n"
        "WHAT IT IS\n"
        "  A checker, not a writer. It reads a draft and the evidence you\n"
        "  supply and reports which claims cannot be tied to that evidence,\n"
        "  which of your own policy rules the draft breaks, and whether an AI\n"
        "  disclosure the law now expects is missing. It runs on your machine\n"
        "  over stdio and keeps nothing.\n"
        "\n"
        "WHAT IT DOES NOT DO\n"
        "  It does not browse, does not invent facts, does not write your copy,\n"
        "  and does not decide a claim is true because it sounds plausible. If\n"
        "  it cannot tell, it returns `unverified` - and `unverified` blocks,\n"
        "  because a gate that passes what it could not check is decoration.\n"
        "\n"
        "IF AN AI MODEL IS USED\n"
        "  With use_model=true, claims are adjudicated by a model you supply a\n"
        "  key for (DEEPSEEK_API_KEY). Only the claim and the evidence you\n"
        "  passed in are sent, and only for the claims that survived the\n"
        "  deterministic numeric check. With use_model=false nothing leaves\n"
        "  the machine at all and every undecidable claim stays `unverified`.\n"
        "\n"
        "HOW TO TRUST IT ANYWAY\n"
        "  The source is public under the MIT licence, with its test suite:\n"
        "  https://github.com/caseone115/claimgate\n"
        "  The reasoning behind the AI-disclosure rule it enforces is public:\n"
        "  https://caseone115.github.io/claimgate/editorial-exemption.html\n"
        "\n"
        "DISCLOSURE\n"
        "  This software is written and maintained by automated software. The\n"
        "  listing says so plainly; so does this.\n"
    )


def main() -> None:
    sys.stderr.write(f"claimgate-mcp {VERSION} ready on stdio\n")
    mcp.run()


if __name__ == "__main__":
    main()
