"""The inbound half of the outreach: an answer to a message we sent.

Why this file exists (found 2026-10-01, by driving the guard rather than reading
it)
---------------------------------------------------------------------------
`claimgate/trials.py` answers mail whose subject carries the trial marker, which
is what the site's own button writes. Every one of the hand-written outreach
messages ends with the same call to action - *"reply with one draft ... and I will
run it and send back the report"* - and those replies carry none of that marker.
There is no subject marker an outreach reply could carry: it is whatever the
recipient's mail client produces from our subject ("Re: A free claim-accuracy
check on one piece of <company> copy (EU AI Act Art. 50)").

So the only channel in this business that can produce a sale was, in code,
write-only. `inbox.py` marks such a message `reply_to_outreach: true` and prints
it - it REPORTS, it never answers - and nothing else on the box looked at it.
Measured, not argued: driving `trials.is_trial()` with a real reply to a real
message we really sent returns False.

What this module answers
------------------------
Mail from an address this project has really written to (read out of
`state/outreach_sent.jsonl`, never a guessed pattern), inside the window that
message is still plausible as a reply, that is not us, not a bounce, not an
automated responder, and not mail this module or the trial module already
answered. Everything else is left alone and stays in the reported backlog, which
is the status quo: a false negative leaves a person in a list somebody reads,
while a false positive mails a stranger about a message they never sent.

The safety here is not in this file. It is in the rules above, which fail closed;
in the same three brakes the trial module already uses (`CLAIMGATE_REPLY_SEND=1`
in the environment, the kill switch `state/REPLY_OFF`, and the owner list - with
no owner list this refuses to send at all); and in the caps, which are the same
shape as the trial module's and deliberately separate from the outreach cap so an
inbound answer can never consume an outbound slot.

What it never does: it never runs a model, never invents a verdict, never logs
the copy, never impersonates a person, and never writes to anyone who did not
write to us first.

    python -m claimgate.replies --scan            # read the mailbox, change nothing
    python -m claimgate.replies --scan --send     # answer what is unanswered
    python -m claimgate.replies --fixtures        # the rules, over the real faults
"""
from __future__ import annotations

import argparse
import email
import email.utils
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import inbox, outreach
from . import trials

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
SENT_LOG = STATE / "outreach_sent.jsonl"
LOG = STATE / "reply_replies.jsonl"
KILL = STATE / "REPLY_OFF"

# Same shape as the trial module's caps, and separate on purpose: a reply to a
# person is not outreach, and an inbound answer must never eat an outbound slot.
MAX_PER_DAY = 5

# The window in which an outreach message can still plausibly produce a reply.
# An answer 90 days later to a message that said "one message, once" reads as
# pestering, not as service.
DAYS = 60

# A reply must be dated after the message it answers, minus a small allowance for
# clock skew between mail servers. Anything older is about something else.
SKEW = timedelta(hours=12)


def sent_targets() -> dict:
    """{address: earliest ISO send time}, read out of the real sent log.

    A recipient list rebuilt from an assumption ("anyone who replied") would be a
    rule that mails strangers. This is the record of who was actually written to.
    The oldest send wins, because that is the message a late reply is answering.
    """
    out = {}
    if not SENT_LOG.exists():
        return out
    for line in SENT_LOG.read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        to = (row.get("to") or "").strip().lower()
        at = (row.get("at") or "").strip()
        if not to or not at:
            continue
        if to not in out or at < out[to]:
            out[to] = at
    return out


def _parse(ts):
    try:
        d = datetime.fromisoformat(ts)
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def like_our_outreach(subject):
    """True when the subject is one of our own messages coming back.

    Kept as a pure rule so it can be driven over the real subjects in the fixtures
    rather than described. It is a *hint* only: the decision is the sent log, which
    cannot be guessed.
    """
    s = (subject or "").lower()
    return ("claim-accuracy check" in s
            or "re: a free claim" in s
            or "claimgate trial" in s)


def _already_answered_reply(message_id, to):
    if not LOG.exists():
        return False
    for line in LOG.read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if message_id and row.get("message_id") == message_id:
            return True
        if not message_id and row.get("to") == (to or "").strip().lower():
            return True
    return False


def is_reply(msg, from_addr, subject, targets=None):
    """True only for a reply from somebody this project really wrote to.

    Fails closed in the cheap direction at every step: everything this refuses
    stays in the inbox backlog and in `inbox.py --pending`, which is where a
    person already looks. See the module docstring.
    """
    from_addr = (from_addr or "").strip().lower()
    when = None
    try:
        when = email.utils.parsedate_to_datetime(msg.get("Date"))
        if when is not None and when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        when = None

    if not from_addr:
        return False
    if from_addr in trials._self():
        return False
    if inbox.is_bounce(msg, subject):
        return False
    if trials._is_auto(msg):
        return False
    if trials._already_answered((msg.get("Message-ID") or "").strip(), from_addr):
        return False
    if _already_answered_reply((msg.get("Message-ID") or "").strip(), from_addr):
        return False
    if when is not None:
        if when < datetime.now(timezone.utc) - timedelta(days=DAYS):
            return False
        sent_at = (targets if targets is not None else sent_targets()).get(from_addr)
        if sent_at:
            sent = _parse(sent_at)
            if sent is not None and when < sent - SKEW:
                return False
    return from_addr in (targets if targets is not None else sent_targets())


def _sent_today():
    if not LOG.exists():
        return 0
    cut = datetime.now(timezone.utc) - timedelta(hours=24)
    n = 0
    for line in LOG.read_text().splitlines():
        try:
            row = json.loads(line)
            ts = datetime.fromisoformat(row["at"])
        except (ValueError, KeyError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= cut:
            n += 1
    return n


def quoted_history(body):
    """What the recipient quoted back beneath their reply - the thread.

    The outreach message itself is long and full of marketing copy, so running the
    whole thread through the gate would report *our own* claims as findings about
    the sender's copy. Only the part above the first quoted line is their text.
    """
    return re.split(r"(?m)^\s*>", body or "", maxsplit=1)[0]


def compose(draft, reason, result=None, from_name=""):
    """The reply to an outreach message. One subject, one body, no invention.

    The trial module's own replies are reused verbatim where the situation is
    identical: a message with no copy in it, and a message whose copy the gate
    found nothing to block in. There is one wording for a person, and it was
    already written and already tested.
    """
    reason = reason or "ok"
    who = ((from_name or "").strip().split(" ")[0]
           if (from_name or "").strip() else "there")
    if reason != "ok":
        # The trial module's own no-copy reply explains "the button on the site",
        # which is true of a trial submission and FALSE of a reply to an email we
        # sent: there is no button here, the person answered our message. A reply
        # that names the wrong cause is a small lie, found by printing this body
        # rather than assuming the reuse was safe. So this case gets its own
        # wording and the same two disclosures as everything else.
        got = ("the reply arrived with no text in it at all" if reason == "nothing"
               else "only the message you were answering came back, with no text "
                    "of your own added above it")
        return ("Re: your reply - the piece did not come through", f"""Hello {who},

Thanks for writing back. Your reply reached us, but there is no copy in it to
check: {got}.

That is easy to do - many mail programs put a reply above the whole quoted
thread, and the piece to check has to be typed above that line. Nothing is wrong
on your side, and nothing was published anywhere.

To get the free check, just reply again with your copy as the plain text of the
message. Anything will do: a landing page, an ad, an email, a case study.

You will get back a report naming every claim in it that cannot be substantiated
against evidence you point at, plus any policy problem (an unsupported statistic,
a superlative, a missing EU AI Act disclosure). Free, no account. You keep it,
and nothing is published.

Two things you should know about this reply:

  * It is software. ClaimGate is a tool this project runs; nobody read your
    message by hand before this answer was written, and no human is impersonated
    here. This is the only time this address writes to you unless you reply.
  * Nothing you sent is stored. It was read once to decide what to reply, and it
    is not kept, logged or published.

{trials.SIGNATURE}""")
    subject, body = trials.compose(draft, reason, result, from_name)
    return subject.replace("ClaimGate trial", "claim-accuracy check"), body


def submissions(days=None):
    """Every reply from an outreach recipient in the mailbox, answered or not."""
    days = DAYS if days is None else days
    conn = inbox._connect()
    out = []
    targets = sent_targets()
    try:
        folder = "[Gmail]/All Mail"
        if conn.select(inbox._quote_mailbox(folder), readonly=True)[0] != "OK":
            raise RuntimeError("could not select " + folder)
        # Ask the server for the messages FROM the addresses we wrote to, instead
        # of fetching every message in the account and filtering here. Measured on
        # 2026-10-01: a full scan of `ALL` fetched 282 messages and took **2m10s**,
        # because the cost is one round trip per message and it grows with the
        # mailbox rather than with the window this module cares about. On a tick
        # that runs every 30 minutes that is the wrong shape. Searching by sender
        # is also *more robust*, not less: a subject-based filter misses a reply
        # whose subject a mail client mangled, while the sender is the one field
        # the reply must carry if it is to be a reply at all.
        #
        # Our own addresses are skipped: searching the sending account returns
        # every message we ever sent (257 of them), which is exactly the set this
        # module must not look at. An address the server refuses to search is
        # reported, never silently treated as an address with no mail.
        # `SINCE` is IMAP's own date syntax (dd-Mon-yyyy); Gmail's web syntax
        # `newer_than:60d` is rejected with `BAD Could not parse command` - tried
        # and recorded so it is not tried again.
        import datetime as _dt
        since = (_dt.date.today() - _dt.timedelta(days=days)).strftime("%d-%b-%Y")
        mine = trials._self()
        candidates = set()
        for addr in sorted(a for a in targets if a not in mine):
            typ, data = conn.search(None, "SINCE", since, "FROM", '"%s"' % addr)
            if typ != "OK" or data is None or data[0] is None:
                raise RuntimeError("the server would not search for mail from "
                                   + addr)
            candidates.update((data[0] or b"").split())
        # A second route, unioned rather than substituted. Searching by sender is
        # the cheap and robust primary, but a reply could in principle evade it -
        # a filter that renames the sender, a client that rewrites the address -
        # and this detector guards the only channel that has ever produced a human
        # contact. So the subjects of the messages we actually sent are searched as
        # well and the two sets are pooled; the real decision is still made at fetch
        # time by `is_reply` against the sent log, and this route can only ever add
        # candidates to that, never bypass it.
        for phrase in ("claim-accuracy check", "a free claim-accuracy"):
            typ, data = conn.search(None, "SINCE", since, "SUBJECT", '"%s"' % phrase)
            if typ == "OK" and data and data[0]:
                candidates.update((data[0] or b"").split())
        for uid in sorted(candidates):
            typ, parts = conn.fetch(uid, "(BODY.PEEK[])")
            raw = b"".join(p[1] for p in parts if isinstance(p, tuple))
            if not raw:
                continue
            msg = email.message_from_bytes(raw)
            from_addr = inbox._addr(msg.get("From"))
            if (from_addr or "").strip().lower() not in targets:
                continue                      # the fast, safe filter
            subject = inbox._decode(msg.get("Subject"))
            if not trials._within(msg, days):
                continue
            if not is_reply(msg, from_addr, subject, targets):
                continue
            body = quoted_history(inbox._plain_body(msg))
            draft, reason = trials.draft_from(body)
            out.append({
                "uid": uid.decode(),
                "folder": folder,
                "from": from_addr,
                "from_name": inbox._decode(
                    email.utils.parseaddr(msg.get("From") or "")[0]),
                "subject": subject,
                "date": msg.get("Date", ""),
                "message_id": (msg.get("Message-ID") or "").strip(),
                "reason": reason,
                "draft": draft,
                "answered": _already_answered_reply(
                    (msg.get("Message-ID") or "").strip(), from_addr),
            })
    finally:
        try:
            conn.logout()
        except Exception:
            pass
    return out


def _record(row, subject, body_chars):
    STATE.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write(json.dumps({
            "at": datetime.now(timezone.utc).isoformat(),
            "to": row["from"],
            "message_id": row.get("message_id", ""),
            "reply_subject": subject,
            "no_copy_reason": row.get("reason", ""),
            "reply_chars": body_chars,
            "note": "inbound reply to our outreach - the draft is never logged",
        }) + "\n")


def _send(to, subject, body):
    user, pw = outreach.load_smtp()
    if not user or not pw:
        raise SystemExit("no SMTP credentials")
    import smtplib
    import ssl
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["From"] = "ClaimGate <%s>" % user
    msg["To"] = to
    msg["Subject"] = subject
    msg["Reply-To"] = user
    msg["Auto-Submitted"] = "auto-replied"
    msg.set_content(body)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx, timeout=45) as s:
        s.login(user, pw)
        s.send_message(msg, from_addr=user, to_addrs=[to])


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="claimgate.replies",
        description="Answer replies to our outreach (read-only unless --send).")
    ap.add_argument("--scan", action="store_true", help="read the mailbox")
    ap.add_argument("--send", action="store_true", help="answer what is unanswered")
    ap.add_argument("--days", type=int, default=DAYS)
    ap.add_argument("--fixtures", action="store_true")
    args = ap.parse_args(argv)

    if args.fixtures:
        return fixtures()

    targets = sent_targets()
    subs = submissions(args.days)
    todo = [s for s in subs if not s["answered"]]
    print("outreach recipients written to: %d" % len(targets))
    print("replies from them: %d in %dd, %d unanswered"
          % (len(subs), args.days, len(todo)))
    for s in subs:
        state = "answered" if s["answered"] else "UNANSWERED"
        kind = ("carries a copy to check" if s["reason"] == "ok"
                else "no copy in it (%s)" % s["reason"])
        print("  [%s] %s %s - %s" % (state, s["from"], s["date"], kind))

    if not args.send:
        print("DRY - nothing sent (--send to answer)")
        return 0
    if os.environ.get("CLAIMGATE_REPLY_SEND") != "1":
        print("refused: CLAIMGATE_REPLY_SEND is not 1")
        return 0
    if KILL.exists():
        print("refused: kill switch present at %s" % KILL)
        return 0
    if not trials.self_list_present():
        print("refused: no owner list at %s, so us cannot be told from them - "
              "create it before arming this" % trials.OWNER_FILE)
        return 1

    sent = 0
    for s in todo:
        if _sent_today() >= MAX_PER_DAY:
            print("refused: daily reply limit reached")
            break
        if len(s["draft"]) > trials.MAX_DRAFT_CHARS:
            print("refused: draft from %s exceeds %d chars"
                  % (s["from"], trials.MAX_DRAFT_CHARS))
            continue
        subject, body = compose(
            s["draft"], s["reason"],
            None if s["reason"] != "ok" else trials.gate(s["draft"]),
            s.get("from_name", ""))
        _send(s["from"], subject, body)
        _record(s, subject, len(body))
        sent += 1
        print("replied to %s (%s)" % (s["from"], s["reason"]))
    print("outreach replies sent: %d" % sent)
    return 0



def _real_subject_for(addr):
    """The subject we really wrote to `addr`, read out of the sent log.

    Kept out of this file on purpose. This repository is public and the recipients
    in that log are real companies; the project's own standard is that a real
    prospect's details live in `state/` (gitignored), never here. A fresh clone has
    no log, so there is a synthetic fallback that still exercises the rule.
    """
    fallback = ("Re: A free claim-accuracy check on one piece of your copy "
                "(EU AI Act Art. 50)")
    if not SENT_LOG.exists():
        return fallback
    for line in SENT_LOG.read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if (row.get("to") or "").strip().lower() == (addr or "").lower():
            subj = (row.get("subject") or "").strip()
            if subj:
                return subj if subj.lower().startswith("re:") else "Re: " + subj
    return fallback


def _mail(subject, frm, body, date="", mid=None):
    m = email.message.EmailMessage()
    m["Subject"] = subject
    m["From"] = frm
    if date:
        m["Date"] = date
    m["Message-ID"] = mid or ("<probe-%d@example>"
                              % (abs(hash((subject, frm, body))) % 10 ** 9))
    m.set_content(body)
    return m


def fixtures():
    """The rules, driven over replies to messages this project really sent."""
    fails = 0

    def check(name, ok, detail=""):
        nonlocal fails
        print("  %s  %s%s" % ("PASS" if ok else "FAIL", name,
                              "" if ok else "  <- %s" % (detail,)))
        if not ok:
            fails += 1

    # The recipient is read out of the REAL sent log, not written here. This
    # module is in a PUBLIC repository: a real prospect's address committed to it
    # is the exact leak `scripts/check_public_addresses.py` exists to catch, and
    # this project has shipped it three times. Driving the fixture off the record
    # is also the stronger test - it is the recipient we really wrote to, at the
    # time we really wrote to them. The reserved fallback keeps the fixtures
    # meaningful in a fresh clone with no state/ directory.
    log = sent_targets()
    WHO = next(iter(sorted(log)), "recipient@example.org")
    REAL_SUBJECT = _real_subject_for(WHO)
    REAL_BODY = ("Here is a campaign page we are least confident about. We cut "
                 "onboarding time by 40% for three clients.\n\n"
                 "On Tue, ClaimGate wrote:\n> Hello from ClaimGate. This message "
                 "is sent by software, not by a person...")
    # Real messages carry RFC 5322 dates. The first version of these fixtures used
    # ISO strings, which `email.utils.parsedate_to_datetime` returns None for - so
    # the date rules were skipped entirely and the "too old" case passed as a
    # failure. The shape matters as much as the value.
    # The reply date is DERIVED from the real send time, not typed. It was typed
    # ("Fri, 02 Oct 2026 09:00:00 +0000") and that rotted the moment this
    # project's own sends made a recipient written to TODAY the alphabetically
    # first row of the log. WHO is read out of the live sent log on purpose (the
    # stronger test), so a typed "later" became a date BEFORE our own message,
    # and the rule under test was refused by the date check it was not testing.
    # Measured 2026-10-03, not reasoned about: after three real sends at
    # 16:14-16:15 AEST the whole suite went red on
    #   "a reply to a message we really sent is recognised" (16 passed, 1 failed)
    # against a guard that answers replies correctly. A fixture that rots is how a
    # rule gets ignored, so the date is computed from the log it already reads.
    _sent_when = _parse(log.get(WHO, "")) or datetime(2026, 10, 2, 9, 0, tzinfo=timezone.utc)
    later = email.utils.format_datetime(_sent_when + timedelta(hours=1))
    check("the fixture subject is the subject we really sent, not a typed one",
          REAL_SUBJECT.startswith("Re: "), REAL_SUBJECT)
    earlier = "2026-09-30T06:03:31+00:00"     # replaced below by the real send time
    earlier = log.get(WHO, earlier)        # the real send time, if we have it
    targets = {WHO: earlier}

    m = _mail(REAL_SUBJECT, WHO, REAL_BODY, later)
    check("a reply to a message we really sent is recognised",
          is_reply(m, WHO, REAL_SUBJECT, targets) is True)
    check("and the trial module refuses it - the gap, replayed",
          trials.is_trial(m, WHO, REAL_SUBJECT) is False)

    check("a stranger is never answered",
          is_reply(_mail("Re: hello", "someone@elsewhere.example", "hi", later),
                   "someone@elsewhere.example", "Re: hello", targets) is False)

    mine = (outreach.load_smtp()[0] or "us@example.com").strip().lower()
    check("us is never answered, whatever the subject says",
          is_reply(_mail(REAL_SUBJECT, mine, REAL_BODY, later), mine,
                   REAL_SUBJECT, dict(targets, **{mine: earlier})) is False)

    auto = _mail(REAL_SUBJECT, WHO, "Out of office until Monday.", later)
    auto["Auto-Submitted"] = "auto-replied"
    check("an automatic responder is never answered",
          is_reply(auto, WHO, REAL_SUBJECT, targets) is False)

    bounce = _mail(REAL_SUBJECT, WHO,
                   "Delivery Status Notification (Failure)", later)
    bounce["X-Failed-Recipients"] = WHO
    check("a bounce is not a reply",
          is_reply(bounce, WHO, REAL_SUBJECT, targets) is False)

    old = _mail(REAL_SUBJECT, WHO, REAL_BODY, "Tue, 01 Sep 2026 00:00:00 +0000")
    check("mail dated before our own message is not a reply to it",
          is_reply(old, WHO, REAL_SUBJECT, targets) is False)

    # An undateable message from a real recipient is answered, deliberately: the
    # documented direction of wrong here is "do not silently drop a person", and
    # every other gate (bounce, auto, us, already-answered, the sent log) has
    # already held by the time the date is consulted.
    nodate = _mail(REAL_SUBJECT, WHO, REAL_BODY)
    del nodate["Date"]
    check("an undateable message from a real recipient is still answered",
          is_reply(nodate, WHO, REAL_SUBJECT, targets) is True)

    # ...and the same undateable message from a stranger is not.
    ns = _mail(REAL_SUBJECT, "someone@elsewhere.example", REAL_BODY)
    del ns["Date"]
    check("an undateable message from a stranger is not answered",
          is_reply(ns, "someone@elsewhere.example", REAL_SUBJECT, targets) is False)

    had = LOG.read_text() if LOG.exists() else None
    try:
        STATE.mkdir(parents=True, exist_ok=True)
        LOG.write_text(json.dumps({"at": later, "to": WHO,
                                   "message_id": "<probe-x@example>"}) + "\n")
        m2 = _mail(REAL_SUBJECT, WHO, REAL_BODY, later, mid="<probe-x@example>")
        check("a reply already answered is not answered twice",
              is_reply(m2, WHO, REAL_SUBJECT, targets) is False)
        check("and one with no Message-ID is deduped by address",
              _already_answered_reply("", WHO) is True)
    finally:
        if had is None:
            LOG.unlink(missing_ok=True)
        else:
            LOG.write_text(had)

    quoted = quoted_history(REAL_BODY)
    check("our own quoted message is stripped before the gate sees it",
          "sent by software" not in quoted and "40%" in quoted, quoted[:60])

    draft, reason = trials.draft_from(quoted_history(""))
    check("an empty reply is reported as no copy, not gated",
          draft == "" and reason in ("nothing", "placeholder"), (draft, reason))

    # Both no-copy replies must actually COMPOSE. This path had no fixture, so a
    # NameError in it survived until the body was printed by hand - a person would
    # have got no answer at all, on the branch that answers the most likely first
    # mistake a recipient can make.
    for r in ("nothing", "placeholder"):
        try:
            subj, bod = compose("", r, None, "Ana")
            good = bool(subj) and bool(bod) and "software" in bod
            detail = ""
        except Exception as exc:
            good, detail = False, "%s: %s" % (type(exc).__name__, exc)
        check("the %s reply composes and says it is software" % r, good, detail)

    # And it must not explain a button that is not in this conversation.
    _, bod = compose("", "placeholder", None, "Ana")
    check("the no-copy reply does not name a site button the sender never pressed",
          "button on the site" not in bod, bod[:80])

    subj3, bod3 = compose("We cut onboarding time by 40%.", "ok", None, "Ana")
    check("a reply with copy composes a report and does not offer a trial",
          bool(bod3) and "ClaimGate trial" not in subj3, subj3)

    check("the real subject we sent carries no trial marker, which is the fault",
          trials.SUBJECT_MARKER not in REAL_SUBJECT.lower())

    print("\n  %d passed, %d failed" % (17 - fails, fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
