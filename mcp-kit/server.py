#!/usr/bin/env python3
"""ClaimGate starter kit, as an MCP server - the free front door, as a tool.

WHAT THIS IS
------------
The same publish gate as the paid entry, in the form the free starter kit
delivers it: it SCAFFOLDS a gated repository and it runs the checks that need
no API key and no network.

Two things it does that the engine entry does not:

  * ``init_kit`` writes a whole starter kit into a directory you name - a
    policy file, an evidence folder, a draft template, the six-question
    pre-publish checklist, and a GitHub Actions job that gates every pull
    request. That is the free product, and it stays free.
  * it is the zero-price entry on the registry, so an agent asked to "set up
    our copy gate" has something to call that costs nothing and asks for no
    account.

WHY IT FAILS CLOSED
-------------------
Identical reasoning to the engine, because it is the same five modules:
no evidence supplied is ``unverified``, never ``supported``; a figure that
appears in no supplied evidence is ``unsupported`` from a plain string
comparison with no model consulted; and with no model key configured nothing
is ever reported ``supported``. A gate that waves through what it could not
check is decoration.

It does not browse, does not invent facts, and does not write copy.

TRANSPORT
---------
stdio. Protocol JSON-RPC on stdout; diagnostics on stderr, never leaked into
the transcript.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Works in two layouts with one line each:
#   repo:   claimgate/mcp-kit/server.py       -> imports ../claimgate
#   bundle: <bundle>/server/server.py         -> imports ./claimgate
_HERE = Path(__file__).resolve().parent
for _cand in (_HERE, _HERE.parent):
    if (_cand / "claimgate" / "__init__.py").is_file():
        sys.path.insert(0, str(_cand))
        break
else:
    sys.stderr.write(
        "claimgate-kit-mcp: could not find the 'claimgate' package next to this "
        f"file (looked in {_HERE} and {_HERE.parent}).\n")
    raise SystemExit(2)

from claimgate import kit as kitmod                                   # noqa: E402
from claimgate.claims import extract, summarise                       # noqa: E402
from claimgate.htmltext import to_text                                # noqa: E402
from claimgate.policy import Policy, check_policy                     # noqa: E402
from claimgate.substantiation import (Evidence, Verdict,              # noqa: E402
                                      numbers_supported, report)

try:
    from mcp.server.fastmcp import FastMCP              # SDK 1.x
    SDK_FAMILY = "fastmcp (SDK 1.x)"
except Exception:                                        # noqa: BLE001
    try:
        from mcp.server import MCPServer as FastMCP      # SDK 2.x
        SDK_FAMILY = "MCPServer (SDK 2.x)"
    except Exception as exc:                             # noqa: BLE001
        sys.stderr.write(
            "claimgate-kit-mcp: the 'mcp' Python package is required and could "
            f"not be imported ({exc}).\nInstall it with: pip install mcp\n")
        raise SystemExit(2)

VERSION = "0.1.0"
SERVER_NAME = "io.github.caseone115/claimgate-kit"
MAX_DRAFT_CHARS = 400_000
MAX_EVIDENCE_FILE_BYTES = 2_000_000
EVIDENCE_SUFFIXES = (".txt", ".md", ".html", ".htm")

# The launch link is the one string in the kit that sells anything, and it has
# already gone stale once in this project's history (a hand-built kit shipped a
# README quoting the pre-launch US$149 against a shop charging US$39). If it is
# ever absent, this refuses rather than quietly handing out a kit that cannot
# lead anywhere.
REQUIRED_KIT_STRING = "claimgate/LAUNCH39"

try:
    mcp = FastMCP("claimgate-kit", title="ClaimGate starter kit",
                  description=("Set up a publish gate for AI-assisted marketing "
                               "copy: a policy, an evidence folder and a CI job."),
                  version=VERSION,
                  website_url="https://caseone115.github.io/claimgate/")
except TypeError:
    mcp = FastMCP("claimgate-kit")


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

    A file a reader would see as empty is skipped rather than offered as
    evidence: an empty source supports nothing, and a claim checked against it
    would come back unsupported for the wrong reason.
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


def _decide(text: str, evidence: list[Evidence]) -> list[Verdict]:
    """The half of the engine that needs no model. Same rules as the engine."""
    if not evidence:
        return [Verdict(c, "unverified", reason=(
            "no evidence was supplied, so this claim cannot be substantiated "
            "here at all")) for c in extract(text)]
    verdicts: list[Verdict] = []
    blob = " ".join(e.text for e in evidence)
    for c in extract(text):
        missing = numbers_supported(c.text, blob)[1]
        if missing:
            verdicts.append(Verdict(c, "unsupported", reason=(
                "the figure(s) %s in this claim appear in no supplied evidence"
                % ", ".join(missing[:4]))))
        else:
            verdicts.append(Verdict(c, "unverified", reason=(
                "this check does not adjudicate a claim without a model, so it "
                "is left unverified rather than assumed true")))
    return verdicts


def _kit_dir(dest: str) -> Path:
    if not dest.strip():
        raise ValueError("`dest` is empty; name the directory to write the kit into")
    root = Path(dest).expanduser()
    if root.exists() and not root.is_dir():
        raise ValueError(f"dest exists and is not a directory: {root}")
    return root


# ----------------------------------------------------------------------- tools

@mcp.tool()
def init_kit(dest: str, force: bool = False) -> str:
    """Write the free ClaimGate starter kit into a directory.

    Creates: README.md, CHECKLIST.md (the six pre-publish questions, including
    the EU AI Act Article 50 disclosure section), DRAFT-template.md,
    evidence/README.md, policy.json, policy-notes.md and
    .github/workflows/claimgate.yml - a job that gates the copy on every pull
    request. Nothing is uploaded and nothing leaves the machine.

    Refuses to overwrite existing files unless force=true, because a kit that
    silently replaced someone's policy.json would be worse than no kit.
    """
    root = _kit_dir(dest)
    try:
        written = kitmod.build(root, force=force)
    except FileExistsError as exc:
        raise ValueError(
            f"{exc}; pass force=true to overwrite, or choose an empty directory")
    readme = (root / "README.md").read_text()
    if REQUIRED_KIT_STRING not in readme:
        raise ValueError(
            "refusing to hand over a kit whose README lost the link that "
            f"makes it useful (expected {REQUIRED_KIT_STRING!r}); this is a bug "
            "in the kit, not in your input")
    rel = sorted(str(p.relative_to(root)) for p in written)
    return ("Starter kit written to %s\n\n%s\n\nNext: put a real draft in "
            "DRAFT-template.md and call check_kit on it. Anything the kit finds "
            "is found without an API key and without a network call."
            % (root, "\n".join("  " + r for r in rel)))


@mcp.tool()
def check_kit(draft: str = "", draft_path: str = "",
              evidence_dir: str = "", evidence_json: str = "",
              policy_json: str = "") -> str:
    """Run the kit's own gate on a draft: deterministic, offline, no API key.

    This is exactly what `.github/workflows/claimgate.yml` runs. It reports
    every claim that needs substantiation, the ones no supplied evidence can
    support, and a figure that appears in no evidence is caught by plain string
    comparison with no model consulted - because a fabricated number is not a
    judgement call.

    Because no model is consulted, a claim it cannot decide comes back
    `unverified`, and `unverified` blocks. Use the paid engine entry
    (io.github.caseone115/claimgate) when you want each claim adjudicated
    against the evidence.

    ARGUMENTS
      draft          the copy to check, inline. Give this or draft_path.
      draft_path     path to a .md/.txt/.html file to check instead.
      evidence_dir   a folder of files to treat as evidence (.txt/.md/.html).
      evidence_json  evidence as a JSON array, e.g.
                     [{"id":"pricing","text":"The plan is $39/month"}]
      policy_json    your own policy file from init_kit. Omit for the defaults.
    """
    if len(draft) > MAX_DRAFT_CHARS:
        raise ValueError(f"draft is longer than {MAX_DRAFT_CHARS} characters")
    text, label = _read_draft(draft, draft_path)
    policy = Policy.load(policy_json) if policy_json else Policy()
    evidence = _load_evidence(evidence_dir, evidence_json)
    claims = extract(text)
    verdicts = _decide(text, evidence)
    findings = check_policy(text, policy)
    sub = report(verdicts) if verdicts else {
        "total": 0, "by_verdict": {}, "blocking": 0, "clear": True}
    blocked = bool(sub["blocking"]) or any(f.blocking for f in findings)

    lines = [f"Checked: {label}",
             f"Policy: {policy.name} - {len(evidence)} evidence item(s) supplied",
             "",
             f"Claims requiring substantiation: {len(claims)}"]
    by: dict[str, list] = {}
    for v in verdicts:
        by.setdefault(v.verdict, []).append(v)
    for name in ("unsupported", "contradicted", "unverified", "supported"):
        group = by.get(name)
        if not group:
            continue
        lines += ["", f"  {name} ({len(group)})"]
        for v in group:
            lines.append(f"    - {v.claim.text[:110]}")
            if v.reason:
                lines.append(f"      {v.reason[:200]}")
    if findings:
        lines += ["", f"Policy findings: {len(findings)}"]
        for f in findings:
            lines.append(f"    - [{'blocking' if f.blocking else 'advisory'}] "
                         f"[{f.kind}] {(f.text or f.kind)[:90]}")
            if f.fix:
                lines.append(f"      fix: {f.fix[:160]}")
    lines += ["", "VERDICT: BLOCKED - do not publish as it stands."
              if blocked else
              "VERDICT: CLEAR - nothing checkable here is unsupported."]
    if not claims and not findings:
        lines = [f"Checked: {label}", "",
                 "No claims that need substantiation were found, and no policy "
                 "rule was broken. That is not a statement that the copy is "
                 "true - it is a statement that nothing in it was checkable here."]
    return "\n".join(lines)


@mcp.tool()
def list_claims(draft: str = "", draft_path: str = "") -> str:
    """List the claims in a draft and what each one needs, without judging them.

    Useful before you build an evidence folder: it shows what the gate will
    demand substantiation for, so you can tell whether the folder is even the
    right shape.
    """
    text, label = _read_draft(draft, draft_path)
    claims = extract(text)
    if not claims:
        return (f"No checkable claims were found in {label}. Claims are numbers, "
                "comparisons, guarantees, named sources, dated facts and causal "
                "statements - not opinions.")
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

    The half that needs no evidence and no model: "would our own rules let this
    out of the door", which is a different question from "is it true".
    """
    text, label = _read_draft(draft, draft_path)
    policy = Policy.load(policy_json) if policy_json else Policy()
    findings = check_policy(text, policy)
    if not findings:
        return (f"No policy breaches found in {label} against '{policy.name}'. "
                "That is not a clearance: policy covers prohibited wording and "
                "disclosure, not truth.")
    blocking = sum(1 for f in findings if f.blocking)
    lines = [f"{len(findings)} policy finding(s) in {label} ({blocking} blocking):",
             ""]
    for f in findings:
        lines.append(f"  [{'blocking' if f.blocking else 'advisory'}] "
                     f"[{f.kind}] {(f.text or f.kind)[:100]}")
        lines.append(f"      {f.reason[:200]}")
        if f.fix:
            lines.append(f"      fix: {f.fix[:160]}")
    return "\n".join(lines)


@mcp.tool()
def about() -> str:
    """What this server is, what it is not, and what the paid engine adds."""
    return (
        "ClaimGate starter kit - the free half of a publish gate for\n"
        f"AI-assisted marketing copy.\n"
        f"Server: {SERVER_NAME} {VERSION} (MCP SDK: {SDK_FAMILY})\n"
        "\n"
        "WHAT IT IS\n"
        "  Two things. init_kit writes a policy file, an evidence folder, a\n"
        "  draft template, a six-question pre-publish checklist and a GitHub\n"
        "  Actions job into a directory you name. check_kit then runs that\n"
        "  gate on a draft: offline, no API key, no network call.\n"
        "\n"
        "WHAT IT DOES NOT DO\n"
        "  It does not adjudicate a claim against your evidence - that needs a\n"
        "  model, and no model is consulted here. A claim it cannot decide is\n"
        "  returned `unverified`, and `unverified` blocks, because a gate that\n"
        "  passes what it could not check is decoration. A figure that appears\n"
        "  in no evidence you supplied IS caught, by plain string comparison,\n"
        "  with no model consulted.\n"
        "\n"
        "WHAT THE ENGINE ADDS\n"
        "  io.github.caseone115/claimgate adjudicates each surviving claim\n"
        "  against the evidence and returns JSON for a pipeline to gate on.\n"
        "  The paid download is at the listing; the source of both is MIT and\n"
        "  public at https://github.com/caseone115/claimgate - read it before\n"
        "  you pay for anything.\n"
        "\n"
        "DISCLOSURE\n"
        "  This software is written and maintained by automated software. Every\n"
        "  ClaimGate surface says so; so does this.\n"
    )


def main() -> None:
    sys.stderr.write(f"claimgate-kit-mcp {VERSION} ready on stdio\n")
    mcp.run()


if __name__ == "__main__":
    main()
