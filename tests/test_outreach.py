"""Tests for the outreach guardrails, including one real end-to-end send.

The permission to email real prospects is only safe if the limits are enforced
by code. This suite attacks its own guardrails: every rule gets a test that
tries to break it, because a limit that has never been tested is a limit that
will fail on the day it matters.

It ends with a genuine SMTP send of a marked test message, so the send path
itself is proven rather than assumed. A `--no-send` flag skips only that final
step.

    python tests/test_outreach.py            # full, includes one real send
    python tests/test_outreach.py --no-send  # guardrails only
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from claimgate import outreach  # noqa: E402

results: list[tuple[str, bool, str]] = []
HOOK = ("Your team publishes a weekly AI-written newsletter and mentioned "
        "fact-checking overhead in a recent post")
BODY = (
    "Hello — this is an automated message from ClaimGate, a tool, sent by "
    "software rather than a person, so you know what you are reading.\n\n"
    f"{HOOK}.\n\n"
    "ClaimGate checks a draft of AI-assisted marketing copy against evidence "
    "you already hold, and flags any claim you cannot substantiate, plus any "
    "policy rule of yours it breaks and the AI disclosure that EU AI Act "
    "Article 50 now requires. It exits non-zero, so it can block a publish in "
    "CI.\n\n"
    "If it would help, send back your least confident draft and I will return "
    "a gate report. No account, nothing published.\n\n"
    "Reply STOP and I will not contact you again.\n"
)


def ok(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond and detail:
        print(f"        {detail}")


def refused(name: str, fn) -> None:
    try:
        fn()
    except outreach.Refused as e:
        ok(name, True, str(e))
    except Exception as e:  # noqa: BLE001
        ok(name, False, f"wrong error type: {type(e).__name__}: {e}")
    else:
        ok(name, False, "was ALLOWED when it should have been refused")


def main() -> int:
    send_it = "--no-send" not in sys.argv

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        outreach.STATE = tmp
        outreach.SENT = tmp / "outreach_sent.jsonl"
        outreach.SUPPRESS = tmp / "outreach_suppress.txt"
        outreach.KILL = tmp / "OUTREACH_OFF"

        print("\n=== the happy path is allowed ===\n")
        try:
            outreach.check("someone@example.com", BODY, HOOK)
            ok("a well-formed, specific, honest message passes", True)
        except outreach.Refused as e:
            ok("a well-formed, specific, honest message passes", False, str(e))

        print("\n=== template blasts are impossible ===\n")
        refused("empty hook refused",
                lambda: outreach.check("a@example.com", BODY, ""))
        refused("short hook refused",
                lambda: outreach.check("a@example.com", BODY, "I saw your post"))
        refused("hook that is not in the body is refused",
                lambda: outreach.check(
                    "a@example.com", BODY,
                    "A completely different observation about their work that "
                    "was never actually written into the message"))
        short = BODY.replace(HOOK, "")
        refused("body with the hook removed is refused",
                lambda: outreach.check("a@example.com", short, HOOK))

        print("\n=== honesty requirements ===\n")
        no_name = BODY.replace("ClaimGate", "our product")
        refused("a message that does not name the product is refused",
                lambda: outreach.check("a@example.com", no_name, HOOK))
        no_disclose = ("Hello, a person here. " + HOOK + ". " + "x" * 500)
        refused("a message that does not say it is automated is refused",
                lambda: outreach.check("a@example.com", no_disclose, HOOK))

        print("\n=== addresses ===\n")
        refused("an invalid address is refused",
                lambda: outreach.check("not-an-address", BODY, HOOK))
        refused("an address with no TLD is refused",
                lambda: outreach.check("a@localhost", BODY, HOOK))

        print("\n=== suppression wins over everything ===\n")
        outreach.SUPPRESS.write_text(
            "# people who asked not to be contacted\n"
            "optout@example.com\n"
            "competitor.com\n")
        refused("a suppressed address is refused",
                lambda: outreach.check("optout@example.com", BODY, HOOK))
        refused("a suppressed domain is refused",
                lambda: outreach.check("anyone@competitor.com", BODY, HOOK))
        refused("suppression overrides force",
                lambda: outreach.check("optout@example.com", BODY, HOOK,
                                       force=True))
        outreach.SUPPRESS.write_text("")

        print("\n=== never contacted twice ===\n")
        outreach.record("sent@example.com", "hi", BODY, hook=HOOK)
        refused("an address already in the log is refused",
                lambda: outreach.check("sent@example.com", BODY, HOOK))
        refused("case differences do not bypass it",
                lambda: outreach.check("SENT@Example.com", BODY, HOOK))

        print("\n=== the daily cap ===\n")
        outreach.SENT.write_text("")
        for i in range(outreach.MAX_PER_DAY):
            outreach.record(f"u{i}@d{i}.com", "hi", BODY, hook=HOOK)
        refused(f"the {outreach.MAX_PER_DAY}/day cap is enforced",
                lambda: outreach.check("new@fresh.com", BODY, HOOK))
        ok("the log shows exactly the cap",
           len(outreach.recent(24)) == outreach.MAX_PER_DAY,
           str(len(outreach.recent(24))))

        print("\n=== one message per company per day ===\n")
        outreach.SENT.write_text("")
        outreach.record("first@bigcorp.com", "hi", BODY, hook=HOOK)
        refused("a second address at the same company is refused",
                lambda: outreach.check("second@bigcorp.com", BODY, HOOK))

        print("\n=== the kill switch ===\n")
        outreach.SENT.write_text("")
        outreach.KILL.write_text("stop")
        refused("everything is refused while the kill switch is on",
                lambda: outreach.check("someone@example.com", BODY, HOOK))
        outreach.KILL.unlink()

        print("\n=== the log is written before anything sends ===\n")
        outreach.SENT.write_text("")
        with mock.patch.object(outreach.smtplib, "SMTP_SSL") as fake:
            fake.side_effect = RuntimeError("network down")
            try:
                outreach.send("fail@example.com", "s", BODY, HOOK)
            except RuntimeError:
                pass
        logged = [r for r in outreach.history()
                  if r["to"] == "fail@example.com"]
        ok("a send that failed still left a record, so it cannot retry blindly",
           len(logged) == 1, f"log entries: {len(logged)}")

        print("\n=== status reporting ===\n")
        outreach.SENT.write_text("")
        outreach.record("a@b.com", "s", BODY, hook=HOOK)
        s = outreach.status()
        ok("status reports the real counts", "all-time 1" in s, s)

    # ---------------------------------------------------------------- real send
    if send_it:
        print("\n=== a real end-to-end send ===\n")
        real_state = Path.home() / "claimgate" / "state"
        real_state.mkdir(parents=True, exist_ok=True)
        outreach.STATE = real_state
        outreach.SENT = real_state / "outreach_sent.jsonl"
        outreach.SUPPRESS = real_state / "outreach_suppress.txt"
        outreach.KILL = real_state / "OUTREACH_OFF"

        # Send only to the account that owns the credentials. Nothing leaves
        # the organisation, so this proves the transport without contacting
        # any real prospect.
        user, _ = outreach.load_smtp()
        if not user:
            ok("SMTP credentials present", False, "no credentials found")
        else:
            subject = "[TEST] ClaimGate outreach transport check"
            body = (
                "This is an automated transport test from ClaimGate, sent by "
                "software to its own inbox rather than by a person. It proves "
                "the outreach path works end to end before any real message is "
                "ever sent to anyone outside this mailbox.\n\n"
                f"{HOOK}.\n\n"
                "ClaimGate checks a draft of AI-assisted marketing copy against "
                "evidence an organisation already holds. It flags any claim "
                "that cannot be substantiated, any policy rule the draft "
                "breaks, and the AI disclosure that EU AI Act Article 50 now "
                "requires. It exits non-zero so it can block a publish in a "
                "CI pipeline.\n\n"
                "Nothing here needs a reply. This message is a test and the "
                "only recipient is the sending account itself.\n"
            )
            if user.lower() in {r["to"].lower() for r in outreach.history()}:
                ok("transport already proven by an earlier run", True)
            else:
                try:
                    r = outreach.send(user, subject, body, HOOK,
                                      note="self-test transport check")
                    ok(f"a real message was accepted for delivery to {user}",
                       bool(r.get("sent_at")), str(r))
                except Exception as e:  # noqa: BLE001
                    ok("a real message was accepted for delivery", False,
                       f"{type(e).__name__}: {e}")

    passed = sum(1 for _, o, _ in results if o)
    total = len(results)
    print(f"\n{passed}/{total} checks behaved as intended")
    for name, o, detail in results:
        if not o:
            print(f"  FAILED: {name} — {detail}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
