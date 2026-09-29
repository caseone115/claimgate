"""Tests for the inbox watcher — the thing that must never miss a human reply.

The watcher's job is asymmetric: reporting a newsletter is cheap, missing a
buyer's reply is the most expensive failure the business has. So every test
here attacks it in the direction that matters — proving it FAILS OPEN on
anything that might be a person, and only excludes what is provably a machine.

It also pins the two properties a scheduled job depends on:
  * 'quiet' is only ever printed after a real scan found nothing new;
  * a failed scan exits non-zero and never prints 'quiet'.

    python tests/test_inbox.py            # offline, no network
"""
from __future__ import annotations

from email.message import Message
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from claimgate import inbox  # noqa: E402

BOT = "teeter.ai.bot@gmail.com"
results: list[tuple[str, bool, str]] = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    if not cond and detail:
        print(f"        {detail}")


def msg(headers: dict, body: str = "") -> Message:
    m = Message()
    for k, v in headers.items():
        m[k] = v
    if body:
        m.set_payload(body)
        m["Content-Type"] = "text/plain; charset=utf-8"
    return m


print("\n=== a person is never mistaken for a machine ===\n")

PEOPLE = [
    ({"From": "Jane Okafor <jane@brightlabs.co>", "Subject": "Re: ClaimGate"},
     "yes, send me a report"),
    ({"From": "info@smallagency.com", "Subject": "question about pricing"},
     "what does it cost?"),
    ({"From": "hello@startup.io", "Subject": "Re: your note"},
     "interesting"),
    ({"From": "billing@acme.com", "Subject": "Re: ClaimGate trial"},
     "invoice please"),
    ({"From": "d.nguyen@acme.com", "Subject": "Fwd: ClaimGate"},
     "passing this to my team"),
    ({"From": "support@vendor.com", "Subject": "Re: ClaimGate"},
     "we can help"),
]
for headers, body in PEOPLE:
    m = msg(headers, body)
    addr = inbox._addr(m.get("From"))
    ok(f"human: {headers['From']}",
       not inbox._is_machine(m, addr, BOT))

print("\n=== a machine is recognised as one ===\n")

MACHINES = [
    {"From": "no-reply@accounts.google.com", "Subject": "Security alert"},
    {"From": "noreply@github.com", "Subject": "PR merged"},
    {"From": "google-shopping-noreply@google.com", "Subject": "Price drop"},
    {"From": "google-gemini-noreply@google.com", "Subject": "Gemini"},
    {"From": "mailer-daemon@googlemail.com", "Subject": "Undelivered"},
    {"From": "notifications@github.com", "Subject": "Run failed"},
    {"From": "bounce@sendgrid.net", "Subject": "bounce"},
    {"From": "a.b@xyz.bounces.google.com", "Subject": "bounce"},
    {"From": "robot@x.co", "Subject": "auto", "Auto-Submitted": "auto-generated"},
    {"From": "list@x.co", "Subject": "news", "Precedence": "bulk"},
    {"From": "someone@x.co", "Subject": "nope", "Return-Path": "<>"},
    {"From": BOT, "Subject": "[TEST] our own outreach"},
]
for headers in MACHINES:
    m = msg(headers)
    addr = inbox._addr(m.get("From"))
    ok(f"machine: {headers.get('From')}",
       inbox._is_machine(m, addr, BOT))

print("\n=== no sender at all is not actionable, and is never 'a person' to report ===\n")
ok("empty From is machine/unactionable", inbox._is_machine(msg({}), "", BOT))

print("\n=== reply detection ===\n")

reply_cases = [
    ({"From": "j@x.co", "Subject": "Re: ClaimGate — quick question",
      "In-Reply-To": "<abc@teeter.ai.bot@gmail.com>"}, True, "In-Reply-To"),
    ({"From": "j@x.co", "Subject": "Re: ClaimGate — quick question"}, True,
     "Re: prefix"),
    ({"From": "j@x.co", "Subject": "AW: ClaimGate"}, True, "AW: prefix"),
    ({"From": "j@x.co", "Subject": "ClaimGate"}, False, "new subject"),
]
sent_subjects, sent_domains = inbox._load_sent()
for headers, _want, why in reply_cases:
    m = msg(headers)
    subj = inbox._decode(m.get("Subject"))
    looks = bool((m.get("In-Reply-To") or "").strip()
                 or (m.get("References") or "").strip()
                 or inbox.REPLY_PREFIX.match(subj)
                 or inbox._norm_subject(subj) in sent_subjects)
    ok(f"reply detection ({why}): expected {_want}", looks == _want,
       f"got {looks}")

print("\n=== the dedupe key is as unique as the messages ===\n")
reused = {"Message-ID": "<same-id@google.com>", "From": "g@google.com"}
k1 = inbox._key(msg(reused), "g@google.com", "s", "2026-09-01", uid="7", folder="INBOX")
k2 = inbox._key(msg(reused), "g@google.com", "s", "2026-09-06", uid="13", folder="INBOX")
ok("same Message-ID, different UID => different keys (no silent drop)", k1 != k2,
   f"{k1} vs {k2}")
k3 = inbox._key(msg(reused), "g@google.com", "s", "2026-09-01", uid="7", folder="INBOX")
ok("same UID => same key (idempotent re-run)", k1 == k3)

print("\n=== body snippet is credential-free ===\n")
leaky = ("Hi, my app password is hunter2 and the token is abc\n"
         "Also here is my draft to check.")
snip = inbox._sanitise_snippet(leaky)
ok("credential line redacted", "hunter2" not in snip and "abc" not in snip, snip)
ok("useful text survives", "draft to check" in snip, snip)
ok("snippet is one line", "\n" not in snip)

print("\n=== a failed scan can never look quiet ===\n")
import unittest.mock as mock  # noqa: E402

with mock.patch.object(inbox, "scan", side_effect=RuntimeError("imap down")):
    out = []
    with mock.patch("sys.stdout") as so:
        so.write = lambda s: out.append(s)
        rc = inbox.main(["--days", "7"])
ok("scan failure exits non-zero", rc == 1, f"rc={rc}")
ok("scan failure never says quiet", "quiet" not in "".join(out) and
   "error:" in "".join(out), "".join(out))

with mock.patch.object(inbox, "scan", side_effect=RuntimeError("imap down")):
    out = []
    with mock.patch("sys.stdout") as so:
        so.write = lambda s: out.append(s)
        rc = inbox.main(["--days", "7", "--pending"])
ok("--pending scan failure exits non-zero too", rc == 1, f"rc={rc}")
ok("--pending scan failure never says quiet", "quiet" not in "".join(out),
   "".join(out))

print("\n=== logging a reply is not the same as answering it ===\n")
row = {"from": "jane@brightlabs.co", "received": "2026-09-20"}
ok("unanswered when we have never written back",
   inbox._unanswered(row, []))
ok("unanswered when our last send was before their reply",
   inbox._unanswered(row, [("jane@brightlabs.co", "2026-09-01")]))
ok("answered once we have written back after their reply",
   not inbox._unanswered(row, [("jane@brightlabs.co", "2026-09-21")]))
ok("someone else's send does not close it",
   inbox._unanswered(row, [("other@x.co", "2026-09-25")]))

with mock.patch.object(inbox, "scan", return_value=[
        {"from": "jane@brightlabs.co", "domain": "brightlabs.co",
         "subject": "Re: ClaimGate", "received": "2026-09-20",
         "reply_to_outreach": True, "machine": False}]):
    with mock.patch.object(inbox, "_load_sent_recipients", return_value=[]):
        out = []
        with mock.patch("sys.stdout") as so:
            so.write = lambda s: out.append(s)
            rc = inbox.main(["--days", "7", "--pending"])
        text = "".join(out)
ok("--pending exits 4 while a person is waiting", rc == 4, f"rc={rc}")
ok("--pending names the waiting sender", "brightlabs.co" in text, text)
ok("--pending prints a total line", "awaiting an answer" in text, text)

with mock.patch.object(inbox, "scan", return_value=[
        {"from": "jane@brightlabs.co", "domain": "brightlabs.co",
         "subject": "Re: ClaimGate", "received": "2026-09-20",
         "reply_to_outreach": True, "machine": False}]):
    with mock.patch.object(inbox, "_load_sent_recipients",
                           return_value=[("jane@brightlabs.co", "2026-09-25")]):
        out = []
        with mock.patch("sys.stdout") as so:
            so.write = lambda s: out.append(s)
            rc = inbox.main(["--days", "7", "--pending"])
ok("--pending goes quiet once answered", rc == 0 and
   "".join(out).strip() == "quiet", "".join(out))

print("\n=== empty result prints the exact word a monitor looks for ===\n")
with mock.patch.object(inbox, "scan", return_value=[]):
    with mock.patch.object(inbox, "_seen_keys", return_value=set()):
        out = []
        with mock.patch("sys.stdout") as so:
            so.write = lambda s: out.append(s)
            rc = inbox.main(["--days", "7"])
ok("nothing new exits 0", rc == 0, f"rc={rc}")
ok("prints 'quiet' on a line by itself", "".join(out).strip() == "quiet",
   repr("".join(out)))

failed = [n for n, c, _ in results if not c]
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
if failed:
    print("FAILED:", failed)
sys.exit(1 if failed else 0)
