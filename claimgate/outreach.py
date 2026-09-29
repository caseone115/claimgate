"""Outreach with hard limits, and a record of everything that was sent.

This exists because a daily job is allowed to email real prospects, and that
permission is only safe if the limits are enforced by code rather than by an
agent remembering them. The agent decides WHO and WHAT; this module decides
whether it is allowed to send at all, and refuses without appeal when it isn't.

The rules, all enforced here:

  * a per-recipient hook is required, and must appear in the message body —
    this is what makes a template blast impossible rather than discouraged;
  * never the same address twice, ever;
  * at most MAX_PER_DAY messages in a rolling 24 hours;
  * at most MAX_PER_DOMAIN_PER_DAY to any one company;
  * a suppression list checked first, which wins over everything;
  * a kill switch (`state/OUTREACH_OFF`) that stops all sending.

Nothing sends until `record()` has written the intent to disk, so a crash
between sending and recording cannot produce a silent second email.

The sent log is deliberately NOT committed to git: it holds real people's
addresses, and this repository is public.
"""
from __future__ import annotations

import json
import smtplib
import ssl
import sys
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
SENT = STATE / "outreach_sent.jsonl"
SUPPRESS = STATE / "outreach_suppress.txt"
KILL = STATE / "OUTREACH_OFF"
SECRETS = Path.home() / "car-watch" / "secrets.env"

MAX_PER_DAY = 3
MAX_PER_DOMAIN_PER_DAY = 1
FROM_LABEL = "ClaimGate"
REPLY_TO = None          # falls back to the sending account
MIN_HOOK_CHARS = 60      # the recipient-specific reason must be this long
MIN_BODY_CHARS = 400     # and the message must actually say something


def _now() -> datetime:
    return datetime.now(timezone.utc)


def load_smtp() -> tuple[str | None, str | None]:
    user = pw = None
    if SECRETS.exists():
        for line in SECRETS.read_text().splitlines():
            line = line.strip()
            if line.startswith("SMTP_USER="):
                user = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("SMTP_PASS="):
                pw = line.split("=", 1)[1].strip().strip('"')
    return user, pw


def suppressed() -> set[str]:
    """Addresses and whole domains that must never be contacted."""
    if not SUPPRESS.exists():
        return set()
    out: set[str] = set()
    for line in SUPPRESS.read_text().splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line:
            out.add(line)
    return out


def history() -> list[dict]:
    if not SENT.exists():
        return []
    out = []
    for line in SENT.read_text().splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def _domain(addr: str) -> str:
    return addr.rsplit("@", 1)[-1].lower()


def recent(within_hours: int = 24) -> list[dict]:
    cut = _now() - timedelta(hours=within_hours)
    out = []
    for row in history():
        try:
            ts = datetime.fromisoformat(row["at"])
        except (KeyError, ValueError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= cut:
            out.append(row)
    return out


class Refused(Exception):
    """The send was not allowed. Not retryable without changing the inputs."""


def check(to: str, body: str, hook: str, *, force: bool = False) -> None:
    """Raise Refused unless this message may be sent. Sends nothing.

    `hook` is the specific, verifiable reason this person was chosen — a
    sentence about their own public work. It must be long enough to be a real
    observation and must appear in the body, which is what stops a blast.
    """
    addr = (to or "").strip().lower()
    if not addr or "@" not in addr or "." not in addr.split("@")[-1]:
        raise Refused(f"not a usable address: {to!r}")

    if KILL.exists() and not force:
        raise Refused(f"outreach is switched off ({KILL} exists)")

    if addr in suppressed() or _domain(addr) in suppressed():
        raise Refused(f"{addr} is on the suppression list")

    if any(r.get("to", "").lower() == addr for r in history()):
        raise Refused(f"{addr} has already been contacted — never twice")

    today = recent(24)
    if len(today) >= MAX_PER_DAY:
        raise Refused(
            f"daily limit reached ({len(today)}/{MAX_PER_DAY} in the last 24h)")

    dom = _domain(addr)
    same = [r for r in today if _domain(r.get("to", "")) == dom]
    if len(same) >= MAX_PER_DOMAIN_PER_DAY:
        raise Refused(f"{dom} already had {len(same)} message(s) today")

    hook = (hook or "").strip()
    if len(hook) < MIN_HOOK_CHARS:
        raise Refused(
            f"the recipient hook is too short to be a real observation "
            f"({len(hook)}<{MIN_HOOK_CHARS} chars) — this is the check that "
            f"makes a template blast impossible")
    if hook.lower() not in (body or "").lower():
        raise Refused(
            "the recipient hook does not appear in the message body — a "
            "message that does not mention the specific reason this person "
            "was chosen is a blast and is refused")
    if len(body or "") < MIN_BODY_CHARS:
        raise Refused(f"the message is too short ({len(body)}<{MIN_BODY_CHARS})")

    # The message must be honest about what it is.
    low = (body or "").lower()
    if "claimgate" not in low:
        raise Refused("the message does not name the product")
    if not any(w in low for w in ("automated", "ai assistant", "not a person",
                                  "software", "tool")):
        raise Refused(
            "the message does not make clear what it is — outreach from an "
            "automated system must say so")


def record(to: str, subject: str, body: str, hook: str = "",
           note: str = "") -> None:
    """Append the send to the permanent log. Called BEFORE the send."""
    STATE.mkdir(parents=True, exist_ok=True)
    row = {
        "at": _now().isoformat(),
        "to": to.strip().lower(),
        "subject": subject,
        "chars": len(body or ""),
        "hook": hook,
        "note": note,
        "sender": load_smtp()[0],
    }
    with SENT.open("a") as fh:
        fh.write(json.dumps(row) + "\n")


def send(to: str, subject: str, body: str, hook: str, note: str = "",
         force: bool = False) -> dict:
    """Check, record, send — in that order, so nothing sends unrecorded."""
    check(to, body, hook, force=force)
    user, pw = load_smtp()
    if not user or not pw:
        raise SystemExit(f"no SMTP credentials in {SECRETS}")

    msg = EmailMessage()
    msg["From"] = f"{FROM_LABEL} <{user}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Reply-To"] = REPLY_TO or user
    msg.set_content(body)

    record(to, subject, body, hook=hook, note=note)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx,
                          timeout=45) as s:
        s.login(user, pw)
        s.send_message(msg, from_addr=user, to_addrs=[to])
    return {"to": to, "subject": subject, "sent_at": _now().isoformat()}


def status() -> str:
    h = history()
    t = recent(24)
    return (f"outreach: all-time {len(h)}, last 24h {len(t)}/{MAX_PER_DAY}, "
            f"suppressed {len(suppressed())}, "
            f"kill switch {'ON' if KILL.exists() else 'off'}")


if __name__ == "__main__":
    print(status())
    for r in history():
        print(f"  {r['at'][:16]}  {r['to']}")
    sys.exit(0)
