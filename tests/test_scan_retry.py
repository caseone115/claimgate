"""Fixtures proving the whole-conversation retry, added 2026-10-02 (sixty-seventh tick).

Replays the REAL fault measured live that night: IMAP welcome + login succeed,
then the very next command on the same connection dies with
abort: socket error: EOF. Each case drives the patched scan() and asserts
what a reader would see.

    python3 tests/test_scan_retry.py
"""
from __future__ import annotations

import sys
import unittest.mock as mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from claimgate import inbox  # noqa: E402

CRLF = chr(13) + chr(10)
results = []


def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print("  " + ("PASS" if cond else "FAIL") + "  " + name)
    if not cond and detail:
        print("       " + str(detail))


def _payload():
    return ("From: Jane <jane@brightlabs.co>" + CRLF +
            "Subject: Re: ClaimGate" + CRLF +
            "Date: Mon, 21 Sep 2026 10:00:00 +0000" + CRLF +
            "Message-ID: <abc@x>" + CRLF + CRLF + "hello" + CRLF).encode()


class DeadOnFirstCommand:
    """Welcome and login succeed; the NEXT command kills the socket.

    This is the measured shape, not an invention: 2026-10-02 22:00/22:16/22:29.
    """

    def __init__(self):
        self.logins = 0
        self.commands = 0

    def login(self, u, p):
        self.logins += 1
        return ("OK", [b"logged in"])

    def select(self, *a, **k):
        self.commands += 1
        raise inbox.imaplib.IMAP4.abort("command: SELECT => socket error: EOF")

    def logout(self):
        return ("BYE", [b"bye"])


class RecoversOnSecondConnection(DeadOnFirstCommand):
    opened = 0

    def __init__(self):
        DeadOnFirstCommand.__init__(self)
        RecoversOnSecondConnection.opened += 1
        self.ordinal = RecoversOnSecondConnection.opened

    """First connection dies mid-command; a fresh one works. Retry must catch it."""

    def select(self, *a, **k):
        self.commands += 1
        if self.ordinal < 2:
            raise inbox.imaplib.IMAP4.abort("command: SELECT => socket error: EOF")
        return ("OK", [b"12"])

    def search(self, *a, **k):
        return ("OK", [b"1"])

    def fetch(self, uid, what):
        return ("OK", [(b"1 (BODY[] {123}", _payload()), b")"])


def factory(cls, sink):
    def f(*a, **k):
        c = cls()
        sink.append(c)
        return c
    return f


print("")
print("=== a socket dropped mid-conversation is retried on a fresh connection ===")
print("")
made = []

with mock.patch.object(inbox.imaplib, "IMAP4_SSL", factory(RecoversOnSecondConnection, made)):
    with mock.patch.object(inbox, "load_smtp", return_value=("teeter.ai.bot@gmail.com", "pw")):
        with mock.patch.object(inbox, "_load_sent", return_value=(set(), set())):
            with mock.patch.object(inbox, "_body_text", return_value="hello"):
                rows = inbox.scan(days=14, folder="INBOX")
ok("the second connection is made", len(made) >= 2, "connections=" + str(len(made)))
ok("the read succeeds instead of failing the tick", len(rows) == 1, "rows=" + str(len(rows)))
ok("the person is reported", bool(rows) and rows[0]["from"] == "jane@brightlabs.co", str(rows[:1]))

print("")
print("=== an outage that does not clear still fails loudly, and names itself ===")
print("")
made2 = []

with mock.patch.object(inbox.imaplib, "IMAP4_SSL", factory(DeadOnFirstCommand, made2)):
    with mock.patch.object(inbox, "load_smtp", return_value=("teeter.ai.bot@gmail.com", "pw")):
        with mock.patch.object(inbox.time, "sleep", lambda s: None):
            try:
                inbox.scan(days=14, folder="INBOX")
                raised = None
            except Exception as exc:
                raised = exc
ok("it still raises - an unreadable mailbox is never a quiet one", raised is not None, "no exception raised")
ok("the error names the real cause", raised is not None and "socket error: EOF" in str(raised), str(raised))
ok("it tried three times, not once", len(made2) == 3, "connections=" + str(len(made2)))

failed = [n for n, c, _ in results if not c]
print("")
print(str(len(results) - len(failed)) + "/" + str(len(results)) + " passed")
if failed:
    print("FAILED: " + str(failed))
sys.exit(1 if failed else 0)
