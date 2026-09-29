"""Tests for the free starter kit.

The kit is the product's front door, and its promise is specific: it is
genuinely useful on its own, it names the paid product once, and running the
gate on a kit that has been filled in actually catches the claims. These tests
hold that promise rather than the implementation.

    python tests/test_kit.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from claimgate import kit, suitecounts  # noqa: E402
from claimgate.policy import Policy  # noqa: E402
from claimgate.substantiation import Evidence, assess_all  # noqa: E402

results: list[tuple[str, bool, str]] = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")


def test_kit_contents() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "kit"
        written = kit.build(root)

        names = {p.relative_to(root).as_posix() for p in written}
        for expected in ("README.md", "CHECKLIST.md", "DRAFT-template.md",
                         "evidence/README.md", "policy.json",
                         "policy-notes.md", ".github/workflows/claimgate.yml"):
            ok(f"kit writes {expected}", expected in names, str(sorted(names)))

        for p in written:
            ok(f"{p.relative_to(root)} is non-empty", p.stat().st_size > 80,
               f"{p.stat().st_size} bytes")

        # the policy it ships must load and must actually contain rules
        policy = Policy.load(root / "policy.json")
        ok("packaged policy loads", policy is not None)
        ok("packaged policy has rules", len(policy.rules) >= 5,
           f"{len(policy.rules)} rules")
        ok("packaged policy requires disclosure", policy.disclosure_required
           is True)

        # the kit is adoptable: an empty evidence folder must be a directory
        ok("evidence/ is a directory", (root / "evidence").is_dir())

        # re-running must not silently overwrite somebody's edited policy
        try:
            kit.build(root)
            ok("second run refuses to clobber", False, "no error raised")
        except FileExistsError:
            ok("second run refuses to clobber", True)
        kit.build(root, force=True)
        ok("--force rewrites", True)


def test_kit_is_honest() -> None:
    """The free kit must not pretend to be the paid product, and must say
    plainly what the paid product is. Both directions matter: an unmentioned
    product earns nothing, and an over-claiming one is the thing this tool
    exists to catch."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "kit"
        kit.build(root)
        readme = (root / "README.md").read_text()

        ok("kit names ClaimGate", "ClaimGate" in readme)
        ok("kit links the paid product", "gumroad.com" in readme)
        # The kit's reader is the warmest traffic there is: they downloaded the
        # kit and read to the bottom of its README. Pointing them at the list
        # price while a launch price is live loses a sale for no reason, so
        # the kit must carry the launch link itself and state both prices.
        ok("kit links the launch price, not just the listing",
           "claimgate/LAUNCH39" in readme)
        ok("kit states the launch price", "$39" in readme)
        ok("kit states the list price", "149" in readme)
        ok("kit points at the public source", "github.com/caseone115/claimgate"
           in readme)
        ok("kit warns against buying unchecked",
           "do not buy" in readme.lower())

        # Self-application: our own customer-facing README is run through our
        # own shipped policy. A claim-checking product whose front page carries
        # a prohibited claim is the worst demonstration possible. The checklist
        # and policy.json legitimately *name* banned terms as rules, so the
        # contract is asserted on the customer-facing file, not on those.
        from claimgate.policy import check_policy
        findings = check_policy(readme, Policy.load(root / "policy.json"))
        blocking = [f for f in findings if f.blocking]
        ok("shipped README clears our own shipped policy", not blocking,
           str([(f.kind, f.text) for f in blocking]))

        checklist = (root / "CHECKLIST.md").read_text()
        ok("checklist cites Article 50", "Article 50" in checklist)
        ok("checklist disclaims legal advice",
           "not legal advice" in checklist.lower())


def test_kit_install_instruction_is_correct() -> None:
    # Found 2026-09-30: the kit told adopters to run a bare pip install
    # claimgate. That name on PyPI belongs to a different, unrelated
    # project (an AI-agent test harness), so an adopter following the kit
    # exactly got the other tool -- and the documented next command then
    # failed with No such command check. The first thing the product ever
    # asks a stranger to do did not work. A gate against untrue published
    # claims must not itself publish an untrue instruction.
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "kit"
        kit.build(root)
        repo = Path(__file__).resolve().parent.parent
        readme = (root / "README.md").read_text()
        checklist = (root / "CHECKLIST.md").read_text()
        workflow = (root / ".github" / "workflows" / "claimgate.yml").read_text()
        public = (repo / "README.md").read_text()
        surfaces = [("kit README", readme), ("kit CHECKLIST", checklist),
                    ("kit CI workflow", workflow), ("public README", public)]
        for name, text in surfaces:
            if "pip install" not in text:
                continue
            ok(name + " installs this product, not the PyPI namesake",
               "git+https://github.com/caseone115/claimgate" in text,
               [l.strip() for l in text.splitlines() if "pip install" in l])
        bare = []
        for name, text in surfaces:
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("pip install claimgate") and "git+" not in s:
                    bare.append(name + ": " + s)
        ok("no shipped surface gives the bare name as the thing to run",
           not bare, str(bare))
        ok("kit README warns the PyPI name is a different project",
           "unrelated project" in readme)
        ok("kit README names the command that would have failed",
           "claimgate check" in readme)
        ok("kit README shows the corrected install command",
           "git+https://github.com/caseone115/claimgate" in readme)

def test_kit_published_numbers_are_true() -> None:
    """Every number this product publishes about itself must be supported by
    its own artefact.

    Found 2026-09-30: the public README -- which ships inside the paid download,
    so it was a paying customer's copy -- said tests/test_kit.py is "34 checks"
    when it is 44, and the live landing page advertised a "112-check test suite"
    when the suites are 55+21+44=120. Both are the exact fault this product
    exists to catch, committed on our own published pages. A check that
    hard-codes the stale string it was written to find (the old guard looked for
    "45-check") can only ever find that one mistake, which is why this one is
    measured: the counts are read by RUNNING the suites, and each surface is
    asserted against what they report.
    """
    repo = Path(__file__).resolve().parent.parent
    counts = suitecounts.measure(repo)
    ok("the suite sizes are measured, not guessed", counts["kit"] > 0, str(counts))
    ok("the measured total is the sum of the three suites",
       counts["total"] == counts["engine"] + counts["outreach"] + counts["kit"],
       str(counts))
    found = suitecounts.problems(repo, counts)
    ok("no shipped surface states a count the suites do not support",
       not found, str(found))


def test_kit_gate_end_to_end() -> None:
    """The point of the kit: fill in a real draft and the gate catches what
    cannot be substantiated, with no API key and no network."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "kit"
        kit.build(root)

        draft = ("Our platform cuts processing time by 60% and is guaranteed to "
                 "pay for itself within a month. Thousands of teams already "
                 "rely on us.\n")
        (root / "DRAFT-template.md").write_text(draft)

        evidence = [Evidence(id="e1", title="spec",
                             text="Processing time was measured at 12 minutes "
                                  "per batch on the 2026-06 benchmark.")]
        policy = Policy.load(root / "policy.json")

        from claimgate.claims import extract
        from claimgate.policy import check_policy
        from claimgate.substantiation import numbers_supported

        claims = extract(draft)
        ok("kit draft yields claims", len(claims) >= 2, str(len(claims)))

        # no key, no network: force the offline path by pointing the model at
        # nothing, which is what assess() already does when the env var is unset.
        verdicts = assess_all(claims, evidence)
        blocked = [v for v in verdicts if v.verdict != "supported"]
        ok("unsubstantiated claims block without a model", len(blocked) >= 2,
           str([v.verdict for v in verdicts]))

        findings = check_policy(draft, policy)
        ok("prohibited 'guaranteed' is caught by the shipped policy",
           any("guarantee" in (f.text or "").lower() for f in findings),
           str([f.text for f in findings]))
        ok("missing AI disclosure is caught",
           any(f.kind == "disclosure" for f in findings))

        joined = "\n".join(e.text for e in evidence)
        supported, missing = numbers_supported(draft, joined)
        ok("the invented 60% is not in the evidence",
           (not supported) and any("60" in m for m in missing),
           f"supported={supported} missing={missing}")
        ok("the real 12 minutes is in the evidence",
           numbers_supported("Processing was measured at 12 minutes per batch.",
                             joined)[0])



def main() -> int:
    test_kit_contents()
    test_kit_is_honest()
    test_kit_install_instruction_is_correct()
    test_kit_published_numbers_are_true()
    test_kit_gate_end_to_end()

    passed = sum(1 for _, ok_, _ in results if ok_)
    total = len(results)
    print(f"\n{passed}/{total} checks behaved as intended")
    for name, ok_, detail in results:
        if not ok_:
            print(f"  FAILED: {name} — {detail}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
