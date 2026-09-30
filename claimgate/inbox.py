#!/usr/bin/env python3
"""Reply watcher for the bot mailbox: a real person's reply is never missed.

The business is sold from teeter.ai.bot@gmail.com, so a human reply arriving in
that inbox is the single most valuable signal ClaimGate gets. This module exists
to make that signal impossible to lose, and to make it machine-readable so a
scheduled job can act on it.

Design rules, all deliberate:

  * READ-ONLY, always. The mailbox is selected read-only and every fetch uses
    BODY.PEEK, so nothing is ever marked seen, moved, or deleted. Running this
    watcher cannot change the state of any message.
  * Deterministic stdout, no timestamps. Each new message prints one line built
    only from the message itself (sender domain, subject, received date, whether
    it looks like a reply). Two runs over the same mail print the same lines, so
    a cron monitor can diff output and see real change rather than noise.
  * "quiet" means checked-and-nothing-new. The word is printed on a line by
    itself only after a successful scan of the mailbox that found nothing new.
    A connection or credential failure prints an `error:` line and exits
    NONZERO instead — a failed check must never look like a quiet inbox. That
    distinction is the whole point of the tool.
  * Never a false negative on people. Machine noise is excluded only by
    unambiguous markers (no-reply local-parts, bulk/auto-submitted headers,
    null return-path). Anything not provably machine is treated as human and
    reported, because showing a newsletter is cheap and missing a buyer is not.
  * Appends are deduplicated by Message-ID. Running it twice a minute all day
    adds one line per real message, never two.
  * Bodies are not printed. A bounded snippet may be stored in the JSONL for
    triage, with credential-looking lines redacted.
  * A DELIVERY FAILURE IS REPORTED, EVEN THOUGH IT IS MACHINE MAIL. Added
    2026-09-30 after the first outreach message bounced and the watcher called
    the mailbox quiet for fourteen hours. A bounce is provably automated, so
    the noise filter hides it by design, and it arrives in INBOX while the
    human scan only looks for mail FROM people we wrote TO. Both were wrong
    for the case that matters most: with outreach as the only channel, a
    bounce is the failure of the whole stream, not noise. Bounces are now
    detected on every scan (they carry `X-Failed-Recipients`, or In-Reply-To
    plus `mail delivery`/`failure`/`undelivered` in the subject) and printed
    on stderr so they cannot be filtered away, naming the address that failed.
    A bounce is NOT a person: it never counts as human mail and never changes
    an exit code, so the person-mail contract is untouched.

Usage:
    python3 claimgate/inbox.py                 # last 14 days, INBOX
    python3 claimgate/inbox.py --days 30
    python3 claimgate/inbox.py --show-seen      # reprint already-recorded mail
    python3 claimgate/inbox.py --no-write       # report without appending
    python3 claimgate/inbox.py --strict-exit    # exit 3 when new human mail
    python3 claimgate/inbox.py --pending        # exit 4 while anyone who wrote
                                                # us is still unanswered

Exit codes: 0 = scan succeeded (quiet or new mail), 1 = scan did not happen
(credentials, network, IMAP), 3 = --strict-exit and new human mail was found,
4 = --pending and a person is waiting for an answer.
"""
from __future__ import annotations

import argparse
import email
import hashlib
import imaplib
import json
import re
import ssl
import sys
import time
from datetime import datetime, timedelta, timezone
from email import utils as email_utils
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from pathlib import Path

# --- reuse the credential handling that is already in service ----------------
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
try:
    from outreach import load_smtp  # noqa: E402  (same package dir)
except ImportError as exc:  # pragma: no cover - only if the file is moved
    raise SystemExit(f"inbox: cannot reuse outreach.load_smtp: {exc}")

ROOT = _HERE.parent
STATE = ROOT / "state"
INBOX_LOG = STATE / "inbox.jsonl"
SECRETS = Path.home() / "car-watch" / "secrets.env"
SENT_LOG = STATE / "outreach_sent.jsonl"

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
DEFAULT_DAYS = 14
PERSON_FOLDERS = ("INBOX", "[Gmail]/All Mail")
_MAILBOX_SPECIAL = " \t\r\n\"\\()[]"
BODY_SNIPPET_CHARS = 240
SEL = '(BODY.PEEK[HEADER.FIELDS (FROM TO CC REPLY-TO SUBJECT DATE MESSAGE-ID ' \
      'IN-REPLY-TO REFERENCES RETURN-PATH AUTO-SUBMITTED PRECEDENCE ' \
      'X-AUTO-RESPONSE-SUPPRESS LIST-ID X-FAILED-RECIPIENTS)])'

# Unambiguous machine senders. The strong tokens are matched anywhere in the
# local part, because real senders embed them ("google-shopping-noreply",
# "bounce-bounces"). Deliberately narrow otherwise: `info@` or `hello@` at a
# small company can be a person, so those are NOT filtered.
NOISE_ANYWHERE = re.compile(
    r"(^|[-_.+])(no[-_.]?reply|donotreply|do[-_.]?not[-_.]?reply|mailer[-_.]?daemon"
    r"|postmaster|bounce|bounces|auto[-_.]?(confirm|reply|generated|reply)"
    r"|security[-_.]?noreply)([-_.+]|$)", re.I)
NOISE_WHOLE_LOCAL = re.compile(r"^(notification|notifications|alert|alerts|"
                               r"noreply|no[-_.]reply|donotreply)$", re.I)

# Domains that only ever send us notifications, never a buyer's reply. Kept
# short on purpose: the header and local-part rules already cover what this
# mailbox receives, and a domain blocklist is the fast way to lose a real reply.
NOISE_DOMAINS = {"accounts.google.com", "notifications.google.com"}
NOISE_DOMAIN_SUFFIXES = ("mailer-daemon.googlemail.com",)
BOUNCE_DOMAIN_LABEL = "bounces"   # ESP return-path label, e.g. *.bounces.google.com

# A delivery failure. Narrow on purpose so it cannot fire on a person: the
# standard marker, or a reply whose subject is about failure to deliver.
BOUNCE_SUBJECT = re.compile(
    r"(mail delivery|delivery status|delivery failure|returned mail|"
    r"undelivered mail|failure notice|address not found|delivery has failed)",
    re.I)
FAILED_RCPT = re.compile(
    r"<?([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})>?")

def is_bounce(msg, subject: str) -> bool:
    """True for a delivery-failure report. Never true for a person writing back.

    Being wrong here is asymmetric: a false positive reports a delivery failure
    that did not happen (embarrassing but harmless, and it prints the target
    address so it is checkable), while a false negative hides the failure of the
    only channel that is working. It still requires an explicit marker, so a
    person answering "we had a delivery problem" is not misread.
    """
    if (msg.get("X-Failed-Recipients") or "").strip():
        return True
    if not (msg.get("In-Reply-To") or "").strip():
        return False
    return bool(BOUNCE_SUBJECT.search(subject or ""))

def _failed_recipients(msg, subject: str, body: str) -> list[str]:
    """The addresses that failed. Header and subject need no body fetch.

    `body` may be "" and is only consulted for the address written in prose
    ("Your message was not delivered to x@y because ...").
    """
    out = [a.strip().lower() for a in
           FAILED_RCPT.findall(msg.get("X-Failed-Recipients") or "")]
    if not out:
        out = [a.strip().lower() for a in FAILED_RCPT.findall(subject or "")]
    if not out and body:
        for pat in (r"wasn.t delivered to\s+(\S+@\S+?)[\s,]",
                    r"delivery to\s+(\S+@\S+?)[\s,\.]",
                    r"to\s+(\S+@\S+?)\s+(?:because|failed)"):
            m = re.search(pat, body, re.I)
            if m:
                out = [m.group(1).strip().strip("<>.,;").lower()]
                break
    seen: list[str] = []
    for a in out:
        if a and a not in seen:
            seen.append(a)
    return seen

REPLY_PREFIX = re.compile(r"^\s*((re|aw|sv|fwd?|antw)\s*(\[\d+\])?\s*:\s*)+", re.I)
CRED_LINE = re.compile(
    r"(password|passwd|passcode|pass ?code|app password|one[- ]time|otp\b|"
    r"verification code|auth\w* token|secret|api[- ]?key|2fa)", re.I)


# --- small helpers -----------------------------------------------------------
def _decode(value: str | None) -> str:
    """Decode an RFC2047 header, never raising, never returning a newline."""
    if not value:
        return ""
    try:
        out = str(make_header(decode_header(value)))
    except Exception:
        out = value
    return " ".join(out.split())


def _addr(value: str | None) -> str:
    if not value:
        return ""
    try:
        return (email_utils.parseaddr(value)[1] or "").strip().lower()
    except Exception:
        return (value or "").strip().lower()


def _domain(addr: str) -> str:
    return addr.rsplit("@", 1)[-1].lower() if "@" in addr else ""


def _norm_subject(value: str) -> str:
    return " ".join(REPLY_PREFIX.sub("", value or "").lower().split())


def _received_date(msg) -> str:
    """The message's own date as YYYY-MM-DD (UTC). Never 'now'."""
    raw = msg.get("Date")
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            pass
    return "unknown"


def _sanitise_snippet(text: str) -> str:
    """A short, one-line, credential-free excerpt of the body."""
    kept = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        kept.append("[redacted]" if CRED_LINE.search(line) else line)
    return " ".join(" ".join(kept).split())[:BODY_SNIPPET_CHARS]


def _plain_body(msg) -> str:
    """First text/plain part of a parsed message, safely, or ''."""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" \
                        and "attachment" not in (part.get("Content-Disposition") or ""):
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", "replace")
            return ""
        return msg.get_payload(decode=True).decode(
            msg.get_content_charset() or "utf-8", "replace")
    except Exception:
        return ""


def _body_text(conn, uid: bytes) -> str:
    """Fetch a message body read-only (BODY.PEEK: never marks it seen) and
    return its plain text. Any failure yields '' — a missing snippet must never
    cost the report of the message itself."""
    try:
        typ, md = conn.fetch(uid, "(BODY.PEEK[])")
        if typ != "OK":
            return ""
        raw = b""
        for part in md:
            if isinstance(part, tuple):
                raw = part[1]
        if not raw:
            return ""
        return _plain_body(email.message_from_bytes(raw))
    except Exception:
        return ""


def _is_machine(msg, from_addr: str, bot: str) -> bool:
    """True only for provably automated mail. Everything else is a person.

    Fails open: any doubt means 'a person', because showing a newsletter is
    cheap and missing a buyer is not.
    """
    if not from_addr:
        return True                      # no usable sender: not actionable
    if from_addr == bot:
        return True                      # our own sends / our own test mail
    local = from_addr.split("@", 1)[0]
    if NOISE_ANYWHERE.search(local) or NOISE_WHOLE_LOCAL.match(local):
        return True
    dom = _domain(from_addr)
    if dom in NOISE_DOMAINS or dom.endswith(NOISE_DOMAIN_SUFFIXES):
        return True
    # ESP bounce return-paths look like a.b.c@<hash>.bounces.google.com
    if BOUNCE_DOMAIN_LABEL in dom.split("."):
        return True
    auto = (msg.get("Auto-Submitted") or "").strip().lower()
    if auto and not auto.startswith("no"):
        return True
    if (msg.get("Precedence") or "").strip().lower() in ("bulk", "list", "junk"):
        return True
    # A null return-path is a bounce or a forged sender, never a human typing.
    if (msg.get("Return-Path") or "").strip() == "<>":
        return True
    return False


def _load_sent() -> tuple[set[str], set[str]]:
    """Subjects we sent, and domains we sent to, from the outreach log."""
    subjects: set[str] = set()
    domains: set[str] = set()
    if not SENT_LOG.exists():
        return subjects, domains
    for line in SENT_LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("subject"):
            subjects.add(_norm_subject(row["subject"]))
        if row.get("to"):
            domains.add(_domain(_addr(row["to"]) or row["to"]))
    return subjects, domains


def _load_sent_recipients() -> list[tuple[str, str]]:
    """(recipient, ISO date) for everything we have sent, newest first.

    Used to answer the question that actually matters: has this person been
    answered yet? A reply that is logged but never answered is still a missed
    reply, and logging it must not be mistaken for handling it.
    """
    out: list[tuple[str, str]] = []
    if not SENT_LOG.exists():
        return out
    for line in SENT_LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        addr = _addr(row.get("to") or "")
        when = (row.get("at") or "")[:10]
        if addr and when:
            out.append((addr, when))
    out.sort(reverse=True)
    return out


def _unanswered(row: dict, sent: list[tuple[str, str]]) -> bool:
    """True if nobody has written back to this sender since they wrote to us."""
    return not any(addr == row["from"] and when >= row["received"]
                   for addr, when in sent)


def _key(msg, from_addr: str, subject: str, date: str,
         uid: str = "", folder: str = "") -> str:
    """A stable identity for one mailbox message.

    Message-ID alone is not enough: real senders reuse it across genuinely
    distinct messages (seen live with Google price-drop alerts sharing one
    Message-ID), which would silently drop all but the first from the log. So
    identity is Mailbox UID + Message-ID; the UID is stable for the life of the
    message and unique within the folder, which makes the key exactly as unique
    as the messages it names.
    """
    mid = (msg.get("Message-ID") or "").strip().lower()
    if folder and uid:
        base = f"{folder}:{uid}:{mid or subject}"
        return "uid:" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:20]
    if mid:
        return "mid:" + mid
    return "sha1:" + hashlib.sha1(
        f"{from_addr}|{subject}|{date}".encode("utf-8")).hexdigest()[:16]


def _seen_keys() -> set[str]:
    keys: set[str] = set()
    if not INBOX_LOG.exists():
        return keys
    for line in INBOX_LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("key"):
            keys.add(row["key"])
    return keys


# --- the watcher -------------------------------------------------------------
def scan(days: int = DEFAULT_DAYS, folder: str = "INBOX",
         verbose: bool = False) -> list[dict]:
    """Read `folder`, return every non-machine message in the last `days`.

    Read-only. Raises RuntimeError if the mailbox could not be read — the caller
    turns that into a nonzero exit, never into 'quiet'.
    """
    user, pw = load_smtp()
    if not user or not pw:
        raise RuntimeError(f"no SMTP_USER/SMTP_PASS in {SECRETS}")
    bot = user.strip().lower()

    conn = None
    last: Exception | None = None
    for attempt in range(3):
        try:
            ctx = ssl.create_default_context()
            conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=ctx,
                                     timeout=45)
            conn.login(user, pw)
            break
        except Exception as exc:                     # network / auth
            last = exc
            conn = None
            if attempt < 2:
                time.sleep(3)
    if conn is None:
        raise RuntimeError(f"IMAP login failed after 3 attempts: "
                           f"{type(last).__name__}") from last

    try:
        typ, _ = conn.select(_quote_mailbox(folder), readonly=True)   # readonly: no side effects
        if typ != "OK":
            raise RuntimeError(f"cannot select {folder!r}")

        since = (datetime.now(timezone.utc) - timedelta(days=days)
                 ).strftime("%d-%b-%Y")
        typ, data = conn.search(None, f'(SINCE "{since}")')
        if typ != "OK":
            raise RuntimeError(f"IMAP search failed for folder {folder!r}")
        uids = data[0].split()

        sent_subjects, sent_domains = _load_sent()
        found: list[dict] = []
        for uid in uids:
            typ, md = conn.fetch(uid, SEL)
            if typ != "OK":
                continue
            raw = b""
            for part in md:
                if isinstance(part, tuple):
                    raw = part[1]
            if not raw:
                continue
            msg = email.message_from_bytes(raw)
            from_raw = msg.get("From")
            from_addr = _addr(from_raw)
            subject = _decode(msg.get("Subject"))
            received = _received_date(msg)
            machine = _is_machine(msg, from_addr, bot)
            bounce = is_bounce(msg, subject)

            looks_reply = bool(
                (msg.get("In-Reply-To") or "").strip()
                or (msg.get("References") or "").strip()
                or REPLY_PREFIX.match(subject or "")
                or _norm_subject(subject) in sent_subjects
                or (sent_domains and _domain(from_addr) in sent_domains)
            )
            row = {
                "key": _key(msg, from_addr, subject, received,
                            uid=uid.decode(), folder=folder),
                "uid": uid.decode(),
                "folder": _fold(folder),
                "from": from_addr,
                "from_name": _decode(email_utils.parseaddr(from_raw or "")[0]),
                "domain": _domain(from_addr),
                "subject": subject,
                "received": received,
                "reply_to_outreach": looks_reply,
                "machine": machine,
                "bounce": bounce,
                "message_id": (msg.get("Message-ID") or "").strip(),
            }
            if machine and not bounce:
                # A bounce is kept: it is machine mail, but it is the report
                # that our own send failed, which no other check can see.
                continue
            if not machine:
                # The snippet needs the body, which the header fetch above does
                # not carry; fetch it only for messages we would report.
                row["snippet"] = _sanitise_snippet(_body_text(conn, uid))
            else:
                row["failed"] = _failed_recipients(
                    msg, subject, _body_text(conn, uid))
            found.append(row)
        found.sort(key=lambda r: (r["received"], r["domain"], r["subject"],
                                  r["key"]))
        return found
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def _line(row: dict) -> str:
    return (f'mail domain={row["domain"] or "unknown"} '
            f'subject="{row["subject"]}" received={row["received"]} '
            f'reply={"yes" if row["reply_to_outreach"] else "no"} '
            f'from={row["from"]}')


def _bounce_line(row: dict) -> str:
    failed = row.get("failed") or []
    return (f'DELIVERY FAILED to {", ".join(failed) or "an unnamed address"} "'
            f'— our message did not arrive. reported by {row["from"]} '
            f'on {row["received"]}')


def _pending_rows(days: int, folder: str | None = None) -> list[dict]:
    """Everything a person wrote that nobody has answered yet, newest last."""
    src = scan_all(days=days) if folder is None else scan(days=days, folder=folder)
    rows = [r for r in src
            if not r["machine"] or r.get("bounce")]
    sent = _load_sent_recipients()
    return [r for r in rows if _unanswered(r, sent)]


def _report_bounces(rows: list[dict]) -> None:
    """Print every delivery failure on STDERR: a failed send is an event.

    stderr so that a monitor watching stdout for "quiet" and for person-mail
    lines is not disturbed, and so a failure cannot be swallowed by any
    filtering aimed at machine noise. Never changes an exit code.
    """
    for row in rows:
        if row.get("bounce") or row.get("machine") and row.get("failed"):
            print(_bounce_line(row), file=sys.stderr)


def _append(rows: list[dict]) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    with INBOX_LOG.open("a") as fh:
        for row in rows:
            rec = dict(row)
            rec["first_seen"] = datetime.now(timezone.utc).isoformat()
            fh.write(json.dumps(rec, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Report new person-mail in the bot inbox (read-only).")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS,
                    help=f"how far back to look (default {DEFAULT_DAYS})")
    ap.add_argument("--folder", default="INBOX", help="mailbox to scan")
    ap.add_argument("--no-write", action="store_true",
                    help="report only; do not append to state/inbox.jsonl")
    ap.add_argument("--show-seen", action="store_true",
                    help="also reprint messages already recorded")
    ap.add_argument("--pending", action="store_true",
                    help="report every person who wrote and has not been "
                         "answered yet, ignoring what is already logged; this "
                         "is the mode that makes an unanswered reply visible "
                         "on every run (exit 4)")
    ap.add_argument("--strict-exit", action="store_true",
                    help="exit 3 if new human mail was found")
    ap.add_argument("--bounces", action="store_true",
                    help="report only delivery failures (exit 5 if any); the "
                         "mode the standing probe uses, because a failed send "
                         "to a real prospect is not 'quiet'")
    args = ap.parse_args(argv)

    if args.bounces:
        try:
            rows = [r for r in scan_all(days=args.days)
                    if r.get("bounce") or r.get("failed")]
        except Exception as exc:
            print(f"error: mailbox not checked — {type(exc).__name__}: {exc}")
            return 1
        for row in rows:
            print(_bounce_line(row))
        return 5 if rows else 0

    if args.pending:
        try:
            pend = _pending_rows(days=args.days)
        except Exception as exc:
            print(f"error: mailbox not checked — {type(exc).__name__}: {exc}")
            return 1
        _report_bounces(pend)
        people = [r for r in pend if not r["machine"]]
        if not people:
            print("quiet")
            return 0
        for row in people:
            print(_line(row))
        print(f'total: {len(people)} person-mail awaiting an answer in last '
              f'{args.days}d')
        return 4

    try:
        found = scan_all(days=args.days)
    except Exception as exc:
        # Never claim quiet when the mailbox was not actually read.
        print(f"error: mailbox not checked — {type(exc).__name__}: {exc}")
        return 1

    seen = _seen_keys()
    new = [r for r in found if r["key"] not in seen]
    shown = found if args.show_seen else new

    _report_bounces(shown)

    if not args.no_write and new:
        _append(new)

    people = [r for r in shown if not r["machine"]]
    if not people:
        print("quiet")
        return 0

    for row in people:
        print(_line(row))
    human = [r for r in new if not r["machine"]]
    replies = [r for r in new if r["reply_to_outreach"]]
    print(f'total: {len(new)} new of {len(found)} person-mail in last '
          f'{args.days}d — human={len(human)} reply_to_outreach={len(replies)} '
          f'logged={0 if args.no_write else len(new)}')

    if args.strict_exit and human:
        return 3
    return 0
def _quote_mailbox(name):
    # imaplib does not quote the mailbox argument of select, so a Gmail
    # folder whose name contains a space is rejected. Verified both ways
    # against the live mailbox 2026-09-30.
    Q = chr(34)
    if not name or name.startswith(Q):
        return name
    if not any(ch in _MAILBOX_SPECIAL for ch in name):
        return name
    BS = chr(92)
    return Q + name.replace(BS, BS + BS).replace(Q, BS + Q) + Q

def person_folders():
    # Every folder a person can write from and still be answered. A reply
    # the owner has read and archived is STILL a reply, and Gmail moves it
    # out of INBOX, so INBOX alone is not the mailbox.
    names = ["INBOX"]
    try:
        conn = _connect()
        try:
            typ, boxes = conn.list()
            raw = [b.decode(errors="replace") for b in (boxes or [])]
        finally:
            try:
                conn.logout()
            except Exception:
                pass
    except Exception:
        return names
    present = set()
    for line in raw:
        if chr(34) in line:
            present.add(line.split(chr(34))[-2])
    for f in PERSON_FOLDERS:
        if f != "INBOX" and f in present:
            names.append(f)
    return names

def _fold(name):
    # the folder name as a person reads it, without IMAP quoting
    return (name or "").strip(chr(34))


def _connect():
    # one authenticated connection, read-only at every call site
    user, pw = load_smtp()
    if not user or not pw:
        raise RuntimeError("no SMTP_USER/SMTP_PASS in %s" % SECRETS)
    ctx = ssl.create_default_context()
    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=ctx, timeout=45)
    conn.login(user, pw)

def scan_all(days=DEFAULT_DAYS, folder=None):
    # every folder a person can write from, read through one interface
    return _gg(days)

def _ff(days):
    # every folder a person can write from, in one list
    return _gg(days)

def _gg(days):
    return scan(days=days, folder=PERSON_FOLDERS[-1])
if __name__ == "__main__":
    sys.exit(main())
