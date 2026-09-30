#!/usr/bin/env python3
"""Drive the real ClaimGate KIT MCP server over real stdio and assert what it does.

The engine's suite (``test_mcp_server.py``) pins the fail-closed property of the
gate. This one pins the same property for the zero-price entry AND the thing
that only exists here: that ``init_kit`` actually writes a usable kit, with the
file that sells anything in it, and that it refuses rather than overwriting
somebody's policy.

Run:  python3 scripts/test_mcp_kit_server.py [--python PATH]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SERVER = pathlib.Path(os.environ.get(
    "CLAIMGATE_TEST_SERVER", HERE.parent / "mcp-kit" / "server.py"))

FABRICATED = (
    "Clients save 45% of their time, which is 3 times faster than the "
    "market average, and we guarantee 100% accuracy."
)
UNDISCLOSED = (
    "The standard plan is $39 per month. A 2024 study by the Australian "
    "Institute found that 62% of small teams review copy before publishing."
)
EVIDENCE = [
    {"id": "pricing", "title": "price list",
     "text": "The standard plan is $39 per month, billed monthly."},
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
               si.name == "claimgate-kit" and bool(si.version),
               f"name={si.name!r} version={si.version!r}")

            tools = {t.name for t in (await s.list_tools()).tools}
            expected = {"init_kit", "check_kit", "list_claims",
                        "check_policy_only", "about"}
            ok("all five tools are advertised", expected <= tools,
               f"missing={sorted(expected - tools)}")

            with tempfile.TemporaryDirectory() as td:
                tdp = pathlib.Path(td)
                # A real file that exists, used where a directory is required.
                # Deliberately NOT a system path: a test that reads a system
                # file is a test that breaks on somebody else's machine.
                notadir = tdp / "this-is-a-file.txt"
                notadir.write_text("not a directory\n")

                dest = tdp / "kit"
                err, text = await drive(s, "init_kit", {"dest": str(dest)})
                ok("init_kit writes a kit and reports where", err is False
                   and str(dest) in text, text[:160])
                for must in ("README.md", "CHECKLIST.md", "DRAFT-template.md",
                             "policy.json", "policy-notes.md",
                             "evidence/README.md",
                             ".github/workflows/claimgate.yml"):
                    ok(f"init_kit wrote {must}", (dest / must).is_file())
                readme = (dest / "README.md").read_text()
                ok("the kit README carries the link that leads anywhere",
                   "claimgate/LAUNCH39" in readme, readme[:200])
                ok("the kit README says the free part stays free",
                   "stays free" in readme)
                ok("the kit checklist carries the Article 50 disclosure section",
                   "Article 50" in (dest / "CHECKLIST.md").read_text())
                # The kit must be a working gate, not a pile of text.
                err, text = await drive(s, "check_kit", {
                    "draft_path": str(dest / "DRAFT-template.md"),
                    "evidence_dir": str(dest / "evidence"),
                    "policy_json": str(dest / "policy.json")})
                ok("the freshly written kit runs its own gate", err is False
                   and "VERDICT:" in text, text[:160])

                # ---- refusing, rather than overwriting somebody's policy --
                (dest / "policy.json").write_text('{"name": "MINE"}')
                err, text = await drive(s, "init_kit", {"dest": str(dest)})
                ok("init_kit refuses to overwrite an existing kit", err is True,
                   text[:160])
                ok("...and the file it refused to touch is untouched",
                   json.loads((dest / "policy.json").read_text())["name"]
                   == "MINE")
                err, text = await drive(s, "init_kit",
                                        {"dest": str(dest), "force": True})
                ok("force=true does overwrite it", err is False)

                # ---- fail-closed: no evidence at all ---------------------
                err, text = await drive(s, "check_kit", {"draft": FABRICATED})
                ok("no evidence supplied never says the copy is clear",
                   err is False and "VERDICT: BLOCKED" in text, text[:160])
                ok("no evidence supplied -> every claim is 'unverified'",
                   "unverified" in text and "supported (" not in text,
                   text[:200])

                # ---- the deterministic numeric gate ----------------------
                err, text = await drive(s, "check_kit", {
                    "draft": FABRICATED, "evidence_json": json.dumps(EVIDENCE)})
                ok("a figure in no evidence is 'unsupported' without a model",
                   "unsupported" in text and "45%" in text, text[:300])
                err, text = await drive(s, "check_kit", {
                    "draft": "The standard plan is $39 per month.",
                    "evidence_json": json.dumps(EVIDENCE)})
                ok("a figure that IS in the evidence is not called unsupported",
                   "unsupported" not in text, text[:300])

                # ---- the disclosure rule, both directions ----------------
                err, text = await drive(s, "check_policy_only",
                                        {"draft": UNDISCLOSED})
                ok("AI-assisted copy with no disclosure is blocked",
                   err is False and "[disclosure]" in text
                   and "blocking" in text, text[:160])
                err, text = await drive(s, "check_policy_only", {
                    "draft": UNDISCLOSED + " This copy is AI-assisted."})
                ok("a plain 'AI-assisted' note satisfies the rule",
                   "[disclosure]" not in text, text[:160])

                # ---- bad input is an error, never a silent pass ----------
                err, text = await drive(s, "check_kit", {})
                ok("an empty draft is an error, not a clear result", err is True,
                   text[:120])
                err, text = await drive(s, "check_kit", {
                    "draft": "x", "draft_path": str(notadir)})
                ok("giving both draft and draft_path is an error", err is True,
                   text[:120])
                err, text = await drive(s, "check_kit", {
                    "draft_path": str(tdp / "nowhere-at-all.md")})
                ok("a missing draft_path alone is an error", err is True,
                   text[:120])
                err, text = await drive(s, "init_kit", {"dest": ""})
                ok("an empty dest is an error, not a kit in the cwd", err is True,
                   text[:120])
                err, text = await drive(s, "init_kit", {"dest": str(notadir)})
                ok("a dest that is a file is an error", err is True, text[:120])

                # ---- the report a human reads ----------------------------
                err, text = await drive(s, "check_kit", {
                    "draft": FABRICATED, "evidence_json": json.dumps(EVIDENCE)})
                ok("the human report quotes the claim it is about",
                   "Clients save 45%" in text)
                err, text = await drive(s, "list_claims", {"draft": FABRICATED})
                ok("list_claims lists without judging", err is False
                   and "needs:" in text and "VERDICT" not in text, text[:160])
                err, text = await drive(s, "about", {})
                ok("about names the paid engine and the disclosure", err is False
                   and "io.github.caseone115/claimgate" in text
                   and "automated software" in text)

    passed = sum(1 for _, p, _ in RESULTS if p)
    total = len(RESULTS)
    print(f"\n  claimgate-kit-mcp: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--server", default=None)
    a = ap.parse_args()
    global SERVER
    if a.server:
        SERVER = pathlib.Path(a.server)
    print("=== ClaimGate KIT MCP server, driven over real stdio ===")
    print(f"  server:  {SERVER}")
    print(f"  python:  {a.python}\n")
    return asyncio.run(run(a.python))


if __name__ == "__main__":
    sys.exit(main())
