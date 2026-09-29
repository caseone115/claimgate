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
BODY_SNIPPET_CHARS = 240
SEL = '(BODY.PEEK[HEADER.FIELDS (FROM TO CC REPLY-TO SUBJECT DATE MESSAGE-ID ' \
      'IN-REPLY-TO REFERENCES RETURN-PATH AUTO-SUBMITTED PRECEDENCE ' \
      'X-AUTO-RESPONSE-SUPPRESS LIST-ID)])'

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
        typ, _ = conn.select(folder, readonly=True)   # readonly: no side effects
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
                "folder": folder,
                "from": from_addr,
                "from_name": _decode(email_utils.parseaddr(from_raw or "")[0]),
                "domain": _domain(from_addr),
                "subject": subject,
                "received": received,
                "reply_to_outreach": looks_reply,
                "machine": machine,
                "message_id": (msg.get("Message-ID") or "").strip(),
            }
            if not machine:
                # The snippet needs the body, which the header fetch above does
                # not carry; fetch it only for messages we would report.
                row["snippet"] = _sanitise_snippet(_body_text(conn, uid))
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


def _pending_rows(days: int, folder: str) -> list[dict]:
    """Everything a person wrote that nobody has answered yet, newest last."""
    rows = [r for r in scan(days=days, folder=folder) if not r["machine"]]
    sent = _load_sent_recipients()
    return [r for r in rows if _unanswered(r, sent)]


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
    args = ap.parse_args(argv)

    if args.pending:
        try:
            pend = _pending_rows(days=args.days, folder=args.folder)
        except Exception as exc:
            print(f"error: mailbox not checked — {type(exc).__name__}: {exc}")
            return 1
        if not pend:
            print("quiet")
            return 0
        for row in pend:
            print(_line(row))
        print(f'total: {len(pend)} person-mail awaiting an answer in last '
              f'{args.days}d')
        return 4

    try:
        found = scan(days=args.days, folder=args.folder)
    except Exception as exc:
        # Never claim quiet when the mailbox was not actually read.
        print(f"error: mailbox not checked — {type(exc).__name__}: {exc}")
        return 1

    seen = _seen_keys()
    new = [r for r in found if r["key"] not in seen]
    shown = found if args.show_seen else new

    if not args.no_write and new:
        _append(new)

    if not shown:
        print("quiet")
        return 0

    for row in shown:
        print(_line(row))
    human = [r for r in new if not r["machine"]]
    replies = [r for r in new if r["reply_to_outreach"]]
    print(f'total: {len(new)} new of {len(found)} person-mail in last '
          f'{args.days}d — human={len(human)} reply_to_outreach={len(replies)} '
          f'logged={0 if args.no_write else len(new)}')

    if args.strict_exit and human:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
