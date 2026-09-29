"""Command line: gate a draft before it ships.

    claimgate check draft.md --evidence evidence/ --policy policy.json

Exit codes are the point: 0 clear, 1 blocked. That makes it usable in CI, in
a pre-commit hook, or in a publishing pipeline, which is where a gate
actually stops mistakes rather than documenting them afterwards.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .claims import extract, summarise
from .policy import Policy, check_policy
from .substantiation import Evidence, assess_all, report

BOLD, DIM, RED, YEL, GRN, RST = (
    "\033[1m", "\033[2m", "\033[31m", "\033[33m", "\033[32m", "\033[0m")


def _load_evidence(path: Path) -> list[Evidence]:
    """Evidence from a directory of .txt/.md files, or a single .json array."""
    out: list[Evidence] = []
    if path.is_file() and path.suffix == ".json":
        data = json.loads(path.read_text())
        items = data if isinstance(data, list) else data.get("evidence", [])
        for i, item in enumerate(items, 1):
            if isinstance(item, str):
                out.append(Evidence(id=f"e{i}", text=item))
            else:
                out.append(Evidence(id=str(item.get("id") or f"e{i}"),
                                    text=item.get("text", ""),
                                    title=item.get("title", ""),
                                    url=item.get("url", "")))
        return out
    files = sorted(p for p in (path.iterdir() if path.is_dir() else [path])
                   if p.suffix.lower() in (".txt", ".md", ".html"))
    for f in files:
        out.append(Evidence(id=f.stem, text=f.read_text(errors="replace"),
                            title=f.name, url=str(f)))
    return out


def cmd_check(args) -> int:
    draft = Path(args.draft).read_text(errors="replace")
    policy = Policy.load(args.policy) if args.policy else Policy()
    evidence = _load_evidence(Path(args.evidence)) if args.evidence else []

    claims = extract(draft)
    findings = check_policy(draft, policy)

    if args.no_model:
        verdicts = []
    elif evidence:
        verdicts = assess_all(claims, evidence, timeout=args.timeout)
    else:
        # A claim with no evidence behind it is unverified by definition.
        from .substantiation import Verdict
        verdicts = [Verdict(c, "unverified",
                            reason="no evidence supplied for this claim")
                    for c in claims]

    s = summarise(claims)
    r = report(verdicts) if verdicts else {"total": 0, "by_verdict": {},
                                           "blocking": 0, "clear": True}
    blocked = (r["blocking"] > 0
               or any(f.blocking for f in findings)
               or (args.strict and s["high"] > 0))

    if args.json:
        print(json.dumps({
            "draft": str(args.draft),
            "policy": policy.name,
            "claims": [c.as_dict() for c in claims],
            "verdicts": [v.as_dict() for v in verdicts],
            "policy_findings": [f.as_dict() for f in findings],
            "summary": {**s, **r, "blocked": blocked},
        }, indent=2))
        return 1 if blocked else 0

    print(f"\n{BOLD}ClaimGate — {args.draft}{RST}")
    print(f"{DIM}policy: {policy.name} · "
          f"disclosure required: {policy.disclosure_required} · "
          f"evidence: {len(evidence)} item(s){RST}\n")

    if not claims and not findings:
        print(f"{GRN}No claims and no policy breaches found.{RST}\n")
        return 0

    if claims:
        print(f"{BOLD}Claims requiring substantiation ({len(claims)}){RST}")
        for c, v in zip(claims, verdicts or [None] * len(claims)):
            mark = {"supported": f"{GRN}✓{RST}",
                    "partially_supported": f"{YEL}~{RST}"}.get(
                        getattr(v, "verdict", ""), f"{RED}✗{RST}")
            print(f"  {mark} [{c.category}] {c.text[:96]}")
            if v is not None and v.verdict != "supported":
                print(f"      {DIM}{v.verdict}: {v.reason[:150]}{RST}")
                if v.suggested_rewrite:
                    print(f"      {DIM}try: {v.suggested_rewrite[:140]}{RST}")
            elif v is None:
                print(f"      {DIM}needs {c.needs}{RST}")
        print()

    if findings:
        print(f"{BOLD}Policy findings ({len(findings)}){RST}")
        for f in findings:
            colour = RED if f.blocking else YEL
            label = f.text or f.kind
            print(f"  {colour}✗{RST} [{f.kind}] {label[:80]}")
            print(f"      {DIM}{f.reason[:170]}{RST}")
            if f.fix:
                print(f"      {DIM}fix: {f.fix[:150]}{RST}")
        print()

    if blocked:
        print(f"{RED}{BOLD}BLOCKED{RST} — "
              f"{r['blocking']} unsupported claim(s), "
              f"{sum(1 for f in findings if f.blocking)} blocking policy "
              f"finding(s).\n")
        return 1
    print(f"{GRN}{BOLD}CLEAR{RST} — every claim is substantiated and the "
          f"policy checks pass.\n")
    return 0


def cmd_claims(args) -> int:
    draft = Path(args.draft).read_text(errors="replace")
    claims = extract(draft, include=args.category)
    if args.json:
        print(json.dumps([c.as_dict() for c in claims], indent=2))
        return 0
    for c in claims:
        print(f"[{c.severity:6}] {c.category:12} {c.text[:100]}")
    print(f"\n{summarise(claims)}")
    return 0


def cmd_init_policy(args) -> int:
    p = Path(args.path)
    if p.exists() and not args.force:
        print(f"{p} already exists (use --force to overwrite)")
        return 1
    Policy().save(p)
    print(f"wrote {p} — edit it to match this organisation's rules")
    return 0


def cmd_init_kit(args) -> int:
    from .kit import build
    try:
        written = build(Path(args.path), force=args.force)
    except FileExistsError as exc:
        print(exc)
        return 1
    root = Path(args.path)
    print(f"{GRN}Starter kit written to {root}{RST}\n")
    for p in written:
        print(f"  {p.relative_to(root)}")
    print(f"\nNext:\n"
          f"  cd {root}\n"
          f'  pip install "claimgate @ git+https://github.com/caseone115/claimgate"\n'
          f"  claimgate check DRAFT-template.md --evidence evidence/ "
          f"--policy policy.json --no-model\n")
    print(f"{DIM}--no-model needs no API key and no network. The run exits 1 "
          f"when a claim in the draft cannot be substantiated.{RST}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="claimgate",
        description="Gate AI-assisted marketing content before it publishes.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="check a draft against evidence + policy")
    c.add_argument("draft")
    c.add_argument("--evidence", help="directory, file, or evidence.json")
    c.add_argument("--policy", help="policy.json (see claimgate init-policy)")
    c.add_argument("--json", action="store_true")
    c.add_argument("--no-model", action="store_true",
                   help="facts only: no model calls, no adjudication")
    c.add_argument("--strict", action="store_true",
                   help="also fail on high-severity unadjudicated claims")
    c.add_argument("--timeout", type=int, default=120)
    c.set_defaults(func=cmd_check)

    e = sub.add_parser("claims", help="list the claims in a draft")
    e.add_argument("draft")
    e.add_argument("--category")
    e.add_argument("--json", action="store_true")
    e.set_defaults(func=cmd_claims)

    i = sub.add_parser("init-policy", help="write a starter policy file")
    i.add_argument("path", nargs="?", default="policy.json")
    i.add_argument("--force", action="store_true")
    i.set_defaults(func=cmd_init_policy)

    k = sub.add_parser("init", help="write the free starter kit (policy, "
                       "evidence folder, checklist, CI job)")
    k.add_argument("path", nargs="?", default=".")
    k.add_argument("--force", action="store_true")
    k.set_defaults(func=cmd_init_kit)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
