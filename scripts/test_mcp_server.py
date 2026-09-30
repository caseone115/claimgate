#!/usr/bin/env python3
"""Drive the real ClaimGate MCP server over real stdio and assert what it does.

This is not a unit test of helper functions. It launches ``server.py`` as a
subprocess, speaks MCP to it through the official Python SDK's stdio client,
and reads the answers a real MCP client would get. A server that only works
when its functions are called directly in-process is not a server.

The suite exists to pin the FAIL-CLOSED property, because that is the only
thing about this tool that is worth anything:

  * with no evidence supplied, no claim may ever come back `supported`;
  * a figure that appears in no evidence is `unsupported`, decided without a
    model, because a fabricated number is not a judgement call;
  * with `use_model=false` nothing may be reported `supported` at all;
  * a draft that is AI-assisted and carries a proper plain-English disclosure
    must pass its disclosure rule, and one that carries none must fail it;
  * bad input must be an error the caller can see, never a silent pass.

Run:  python3 scripts/test_mcp_server.py [--python PATH]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
# Default: the server as it lives in the repository. Overridable so the caller
# can point the same suite at a server extracted from the PACKED artifact -
# testing the repository and shipping the bundle is how a release ends up
# broken while the tests are green.
SERVER = pathlib.Path(os.environ.get(
    "CLAIMGATE_TEST_SERVER", HERE.parent / "mcp" / "server.py"))

CONFORMING = (
    "The standard plan is $39 per month. A 2024 study by the Australian "
    "Institute found that 62% of small teams review copy before publishing. "
    "This copy is AI-assisted and was reviewed by a human before publishing."
)
UNDISCLOSED = (
    "The standard plan is $39 per month. A 2024 study by the Australian "
    "Institute found that 62% of small teams review copy before publishing."
)
FABRICATED = (
    "Clients save 45% of their time, which is 3 times faster than the "
    "market average, and we guarantee 100% accuracy."
)
EVIDENCE = [
    {"id": "pricing", "title": "price list",
     "text": "The standard plan is $39 per month, billed monthly."},
    {"id": "study", "title": "2024 AII abstract",
     "text": ("A 2024 study by the Australian Institute found that 62% of "
              "small teams review copy before publishing.")},
]

RESULTS: list[tuple[str, bool, str]] = []


def ok(name: str, passed: bool, detail: str = "") -> None:
    RESULTS.append((name, passed, detail))
    print(f"  {'PASS' if passed else 'FAIL'}  {name}"
          + (f"   [{detail}]" if detail and not passed else ""))


async def drive(session, name, args):
    r = await session.call_tool(name, args)
    err = getattr(r, "is_error", None)
    if err is None:
        err = getattr(r, "isError", None)
    text = "".join(getattr(c, "text", "") or "" for c in r.content)
    return bool(err), text


async def run(python_exe: str) -> int:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(command=python_exe, args=[str(SERVER)],
                                   env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            init = await s.initialize()
            si = getattr(init, "server_info", None) or init.serverInfo
            ok("server initialises and names itself",
               si.name == "claimgate" and bool(si.version),
               f"name={si.name!r} version={si.version!r}")

            tools = {t.name for t in (await s.list_tools()).tools}
            expected = {"check_draft", "check_draft_json", "list_claims",
                        "check_policy_only", "about"}
            ok("all five tools are advertised", expected <= tools,
               f"missing={sorted(expected - tools)}")

            # ---- fail-closed: no evidence at all -------------------------
            err, text = await drive(s, "check_draft_json", {
                "draft": FABRICATED, "use_model": False})
            d = json.loads(text)
            verdicts = {v["verdict"] for v in d["verdicts"]}
            ok("no evidence supplied -> nothing is ever 'supported'",
               "supported" not in verdicts and d["summary"]["blocked"] is True,
               f"verdicts={sorted(verdicts)} blocked={d['summary']['blocked']}")
            ok("no evidence supplied -> claims come back 'unverified'",
               d["verdicts"] and verdicts == {"unverified"},
               f"verdicts={sorted(verdicts)}")

            # ---- the deterministic numeric gate --------------------------
            err, text = await drive(s, "check_draft_json", {
                "draft": FABRICATED, "evidence_json": json.dumps(EVIDENCE),
                "use_model": False})
            d = json.loads(text)
            reasons = " ".join(v["reason"] for v in d["verdicts"])
            ok("a figure in no evidence is 'unsupported' without a model",
               all(v["verdict"] == "unsupported" for v in d["verdicts"])
               and "45%" in reasons and "100%" in reasons,
               f"verdicts={[v['verdict'] for v in d['verdicts']]}")
            ok("a guaranteed claim blocks the gate",
               d["summary"]["blocked"] is True)

            # ---- use_model=false never says 'supported' ------------------
            err, text = await drive(s, "check_draft_json", {
                "draft": CONFORMING, "evidence_json": json.dumps(EVIDENCE),
                "use_model": False})
            d = json.loads(text)
            ok("use_model=false never reports 'supported'",
               all(v["verdict"] != "supported" for v in d["verdicts"]),
               f"verdicts={[v['verdict'] for v in d['verdicts']]}")

            # ---- the disclosure rule, both directions --------------------
            # Assert on the *finding*, not on the word "disclosure": the
            # explanation printed when there is no finding also contains the
            # word, so a substring test passes a broken rule. (That mistake
            # was in the first version of this file and this is the fix.)
            err, text = await drive(s, "check_policy_only",
                                    {"draft": UNDISCLOSED})
            ok("AI-assisted copy with no disclosure is blocked",
               err is False and "[disclosure]" in text
               and "blocking" in text,
               text[:160])
            err, text = await drive(s, "check_policy_only",
                                    {"draft": CONFORMING})
            ok("a plain 'AI-assisted' disclosure satisfies the rule",
               "[disclosure]" not in text,
               text[:160])
            ok("the same rule fires through check_draft_json",
               (await drive(s, "check_draft_json", {
                   "draft": UNDISCLOSED, "use_model": False}))[1]
               .find('"rule_id": "ai-disclosure"') >= 0)
            ok("and is absent when the disclosure is present",
               (await drive(s, "check_draft_json", {
                   "draft": CONFORMING, "use_model": False}))[1]
               .find('"rule_id": "ai-disclosure"') < 0)

            # ---- reading a draft off disk --------------------------------
            tmp = pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / "cg_mcp_fixture.md"
            tmp.write_text(FABRICATED)
            err, text = await drive(s, "check_draft_json", {
                "draft_path": str(tmp), "evidence_json": json.dumps(EVIDENCE),
                "use_model": False})
            d = json.loads(text)
            ok("draft_path is read from disk",
               err is False and str(tmp) in d["draft"]
               and d["summary"]["blocked"] is True)

            # ---- evidence_dir -------------------------------------------
            ev = tmp.parent / "cg_mcp_evidence"
            ev.mkdir(exist_ok=True)
            (ev / "price.md").write_text("The standard plan is $39 per month.")
            err, text = await drive(s, "check_draft_json", {
                "draft": "The standard plan is $39 per month.",
                "evidence_dir": str(ev), "use_model": False})
            d = json.loads(text)
            ok("evidence_dir is read from disk",
               err is False and d["summary"]["evidence_items"] == 1,
               f"items={d['summary'].get('evidence_items')}")

            # ---- bad input is an error, never a silent pass --------------
            err, text = await drive(s, "check_draft", {})
            ok("an empty draft is an error, not a clear result",
               err is True, text[:120])
            err, text = await drive(s, "check_draft", {
                "draft": "x", "draft_path": "/etc/hostname"})
            ok("giving both draft and draft_path is an error",
               err is True, text[:120])
            # draft_path ALONE, so this cannot be satisfied by the
            # "both options given" rule firing instead. (The first version of
            # this check passed a draft as well, so it was testing the wrong
            # rule and caught nothing when the missing-path check was removed.)
            err, text = await drive(s, "check_draft", {
                "draft_path": "/nonexistent/nowhere.md"})
            ok("a missing draft_path alone is an error",
               err is True, text[:120])
            err, text = await drive(s, "check_draft_json", {
                "draft_path": "/nonexistent/nowhere.md"})
            ok("a missing draft_path is an error on the JSON tool too",
               err is True, text[:120])

            # ---- the report a human reads --------------------------------
            err, text = await drive(s, "check_draft", {
                "draft": FABRICATED, "evidence_json": json.dumps(EVIDENCE),
                "use_model": False})
            ok("the human report states a verdict in words",
               err is False and "VERDICT: BLOCKED" in text
               and "unsupported" in text)
            ok("the human report quotes the claim it is about",
               "Clients save 45%" in text)

    passed = sum(1 for _, p, _ in RESULTS if p)
    total = len(RESULTS)
    print(f"\n  claimgate-mcp: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--server", default=None,
                    help="path to a server.py to drive instead of the repo's")
    a = ap.parse_args()
    global SERVER
    if a.server:
        SERVER = pathlib.Path(a.server)
    print("=== ClaimGate MCP server, driven over real stdio ===")
    print(f"  server:  {SERVER}")
    print(f"  python:  {a.python}\n")
    return asyncio.run(run(a.python))


if __name__ == "__main__":
    sys.exit(main())
