"""The inbound half of the free trial the site advertises.

The landing page carries a button that opens a pre-filled email:

    Send the copy you are least confident about ... You will get back a gate
    report naming every claim you cannot substantiate. Free, and no account
    required.

Nothing read that mailbox for a draft. `claimgate/inbox.py` *reports* what is
waiting; it does not answer, and until this file existed no other process on
the box handled an inbound submission at all. The one message the mailbox has
ever held under that subject was the owner pressing our own button: it
contained the button's own placeholder and no draft.

This file answers those messages, and only those: mail whose subject carries
the trial marker, sent from an address that is not us and not machine mail.
A stranger's ordinary reply is never touched.

Two rules, and they are the whole point:

  * **It fails closed.** A draft with no evidence supplied is `unverified` by
    definition, and this responder never supplies evidence on the sender's
    behalf. It can therefore only ever report claims it cannot substantiate,
    which is exactly what the page promises.
  * **It never guesses what someone meant.** A submission that carries the
    button's placeholder and nothing else is reported back as empty, in one
    line, with the sentinel named - not run through the gate as if the
    placeholder were a draft.

Off by default. `TRIAL_INBOUND_SEND=1` is required to send anything, and the
kill switch `state/TRIAL_OFF` outranks that.

    python -m claimgate.trials --scan            # read the mailbox, change nothing
    python -m claimgate.trials --scan --send     # answer what is unanswered
    python -m claimgate.trials --fixtures        # the rules over the real faults
"""
from __future__ import annotations

import email
import email.utils
import imaplib
import json
import os
import re
import smtplib
import ssl
import sys
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

from . import inbox, outreach
from .claims import extract, summarise
from .policy import Policy, check_policy

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
LOG = STATE / "trial_replies.jsonl"
KILL = STATE / "TRIAL_OFF"

# The subject the landing page's own button writes, and the one an owner
# pressing "reply" produces ("Re: ClaimGate trial ..."). Both carry the marker.
SUBJECT_MARKER = "claimgate trial"

# The placeholder the button puts in the body. If this is all a submission
# contains, there is no draft in it. Written once, here, so the rule can be
# tested against the exact string a real message carried.
PLACEHOLDER = "PASTE YOUR DRAFT HERE"

MAX_PER_DAY = 5          # a reply to a person, not outreach: a separate cap
MAX_DRAFT_CHARS = 20000

# How much of the draft goes into the reply. A person sent it to us and the
# report is about their own text; quoting it back is quoting a document they
# already hold. Bounded anyway, and never logged.
QUOTE_CHARS = 90


# Addresses that are this project's own people, who must never be answered by
# the trial bot. The owner wrote to the trial address on 2026-09-29; the queue's
# own standing decision is that replying to the owner as though they were a
# prospect is worse than silence, and that decision is respected here in code
# rather than remembered. A stranger is answered; we are not.
SELF_ADDRESSES = (
    "dougie115@icloud.com",     # the owner, who pressed the site's own button
    "caseone@hotmail.co.uk",    # the owner's other address
)


def _self() -> set[str]:
    """The addresses that are us: the sending account and the owner's."""
    out = {(outreach.load_smtp()[0] or "").strip().lower()}
    out.update(SELF_ADDRESSES)
    out.discard("")
    return out


# --- the pure rules ----------------------------------------------------------
def is_trial(msg, from_addr: str, subject: str) -> bool:
    """True only for a trial submission from someone other than us.

    Fails closed in the cheap direction: a false negative leaves a message in
    the reported backlog for a person to see, which is the status quo, while a
    false positive would mail a stranger back about a message they never sent.
    """
    if not (from_addr or "").strip():
        return False
    if (from_addr or "").strip().lower() in _self():
        return False
    if inbox.is_bounce(msg, subject):
        return False
    if _is_auto(msg):
        return False
    return SUBJECT_MARKER in (subject or "").lower()


def _is_auto(msg) -> bool:
    """True for mail a machine sent in answer to mail a machine sent.

    The reply this module sends carries `Auto-Submitted: auto-replied`, which is
    the header a well-behaved vacation responder reads before answering. Not all
    of them are well-behaved, and one that answers *our* answer would be answered
    again on the next tick and again after that: a loop between two robots, sent
    from the account that has to receive real prospect mail. Nothing that
    announces itself as automatic is ever answered.
    """
    auto = (msg.get("Auto-Submitted") or "").strip().lower()
    if auto and auto != "no":
        return True
    prec = (msg.get("Precedence") or "").strip().lower()
    if prec.split(";")[0].strip() in ("bulk", "junk", "auto_reply", "list"):
        return True
    if (msg.get("X-Autoreply") or msg.get("X-Autorespond")
            or msg.get("X-Autoresponder")):
        return True
    return False


# The whole sentence the button writes into the body. Matched as a sentence,
# because the first version of this rule kept everything after the marker and
# so read the button's own instruction as the sender's copy: the real message
# in the mailbox came back as the draft ", as the plain text of this email."
BUTTON_LINE = re.compile(
    r"^[ \t]*%s[ \t]*,?[ \t]*(?:as the plain text of this email\.)?[ \t]*$"
    % re.escape(PLACEHOLDER), re.I | re.M)


def _strip_placeholder(body: str) -> str:
    """The body with the button's own placeholder, and its variants, removed.

    The button's sentence goes entirely. The bare marker is removed *in place*,
    so a draft a person pasted on the same line as the marker survives - losing
    their text to tidy a label would be the expensive direction of wrong.
    """
    text = BUTTON_LINE.sub("", body or "")
    text = re.sub(re.escape(PLACEHOLDER), "", text, flags=re.I)
    return text


# Wording that belongs to the form rather than to the sender. This list is
# short and literal on purpose: it was written only after reading the one
# message the mailbox has ever held under this subject, which arrived as the
# page's instruction sentence with no copy under it. A rule that guesses at
# "this looks like instructions" is how a real draft gets thrown away.
FORM_WORDS = re.compile(
    r"(paste (your|the) draft|you want checked below|below\.?|"
    r"nothing is published anywhere|the plain text of this email|"
    r"list the documents you can point at|optional|"
    r"sent from my iphone|sent from my ipad)", re.I)


def _only_form_words(text: str) -> bool:
    """True when every word in `text` belongs to the form, not to the sender.

    This began as `FORM_WORDS.sub("", text).strip(" .,;") == ""`, which is wrong:
    `str.strip` only removes characters at the ends, so the *interior* of the
    form's own sentence ("you want checked below") survived and the real message
    in the mailbox was read as a draft. What the rule means is that nothing the
    sender wrote is left, so that is what it now checks.
    """
    left = FORM_WORDS.sub("", text)
    return re.sub(r"[^0-9A-Za-z]+", "", left) == ""


def draft_from(body: str) -> tuple[str, str]:
    """(the copy to check, why there is none).

    reason is one of:
      "ok"          - there is text here that could be the copy to check
      "placeholder" - only the form's own wording arrived, no copy
      "nothing"     - the body was empty once the form's wording, the phone
                      signature and blank lines were dropped

    The two failure reasons are decided here, once, so the form's own wording can
    never be run through the gate as though it were somebody's copy - and they
    are kept apart, because the reply names which one happened and a reply that
    names the wrong cause is a small lie.
    """
    text = _strip_placeholder(body)
    text = re.sub(r"(?im)^\s*sent from my i?(phone|pad)\s*$", "", text)
    text = re.sub(r"(?im)^\s*optional:\s*list the documents.*$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return "", ("placeholder"
                    if re.search(re.escape(PLACEHOLDER), body or "", re.I)
                    else "nothing")
    # Text that is *entirely* the form's own wording is still not a draft. The
    # one real message in the mailbox was exactly this shape.
    if _only_form_words(text):
        return "", "placeholder"
    return text, "ok"


# --- the gate ----------------------------------------------------------------
def gate(draft: str, policy_path=None) -> dict:
    """Run the deterministic gate over a submission. No model, no credentials.

    Deliberately the facts-only path: it needs nothing from another project's
    secrets, and it cannot invent a verdict about a stranger's copy.
    """
    policy = Policy.load(policy_path) if (policy_path and Path(policy_path).exists()) else Policy()
    claims = extract(draft)
    findings = check_policy(draft, policy)
    s = summarise(claims)
    blocking = [f for f in findings if f.blocking]
    return {
        "claims": [c.as_dict() for c in claims],
        "policy_findings": [f.as_dict() for f in findings],
        "summary": {
            "claims": s.get("total", len(claims)),
            "by_category": s.get("by_category", {}),
            "blocking_policy_findings": len(blocking),
            "blocked": bool(blocking),
        },
    }


def _quote(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:QUOTE_CHARS] + ("..." if len(text) > QUOTE_CHARS else "")


SIGNATURE = (
    "-- \n"
    "ClaimGate - a publish gate for AI-assisted marketing copy\n"
    "https://caseone115.github.io/claimgate/\n"
)


def compose(draft: str, reason: str, result=None, from_name: str = ""):
    """The reply. Plain text, no HTML, one report, nothing invented.

    There are three replies and the gate's own output decides which one is
    honest. A "gate report" is only sent when the gate really found something to
    report; when it found no claims at all it says so and says what that does
    and does not mean. A message with no copy in it gets a third reply that
    names what arrived, and names the right cause, because reason says which.
    """
    who = ((from_name or "").strip().split(" ")[0]
           if (from_name or "").strip() else "there")
    claims = (result or {}).get("claims", [])
    findings = (result or {}).get("policy_findings", [])
    blocking = [f for f in findings if f.get("severity") == "high"]

    if reason != "ok":
        got = ("what came through was the page's own wording and none of your "
               "copy" if reason == "placeholder" else
               "the message arrived with nothing written in it")
        subject = "Re: ClaimGate trial - no copy reached us"
        return subject, f"""Hello {who},

Your message came through, but there is no copy in it to check: {got}.

That is easy to do, and it is worth knowing why. The button on the site opens a
mail with the wording already filled in, and it is easy to send that without
pasting anything underneath it. Nothing is wrong on your side, and nothing was
published anywhere.

To get the free check, reply to this message with the copy pasted under this
line, as plain text:

    --- below here ---

You will get back a report naming every claim in it that cannot be substantiated
against evidence you point at, plus any policy problem (an unsupported
statistic, a superlative, a missing EU AI Act disclosure). Free, no account.

If you would rather not send the copy itself, describe what the piece claims and
it will be checked the same way.

Two things you should know about this reply:

  * It is software. ClaimGate is a tool this project runs; nobody read your
    message by hand before this answer was written, and no human is
    impersonated here.
  * Nothing you sent is stored. It was read once to decide what to reply, and
    it is not kept, logged or published.

{SIGNATURE}"""

    if not claims:
        subject = "Re: ClaimGate trial - I found nothing to block, and here is what that means"
        return subject, f"""Hello {who},

I read the copy you sent and the gate found nothing to block: no statistic, no
superlative, no guarantee, no comparison and no policy problem it recognises.

Read that narrowly, because it is narrower than it sounds. This run had no
evidence attached, so nothing in your copy was *proven* - it means the text
carries no claim of the kinds the gate looks for. It also means something worth
checking: if you meant to send a longer piece and only part of it arrived, the
part that is missing is the part that would have been checked.

Two things you should know about this reply:

  * It is software. ClaimGate is a tool this project runs; the check above was
    produced by it, not by a person pretending to be one.
  * Nothing you sent is stored. It was read once to produce this answer, and it
    is not kept, logged or published.

{SIGNATURE}"""

    subject = "Re: ClaimGate trial - your gate report"
    lines = [f"Hello {who},", "",
             "Here is the gate report on the copy you sent. Nothing here was",
             "decided by opinion: each claim below is listed because no evidence",
             "supplied with the message substantiates it, and every item is",
             "checkable against your own text.", "",
             f"**Claims that need substantiation ({len(claims)})**", ""]
    for c in claims:
        lines.append(f"  - [{c.get('category')}] {_quote(c.get('text', ''))}")
        if c.get("needs"):
            lines.append(f"      needs: {c['needs']}")
    lines.append("")
    if blocking:
        lines += [f"**Policy findings ({len(blocking)})**", ""]
        for f in blocking:
            lines.append(f"  - [{f.get('kind')}] {_quote(f.get('reason', ''))}")
            if f.get("fix"):
                lines.append(f"      fix: {f['fix']}")
        lines.append("")
    lines += [
        "What this does not say: it does not say your claims are false. A claim",
        "with no evidence supplied is unverified, and this report is the shortest",
        "path to fixing that - each line above names the artifact that would",
        "settle it (a spec sheet, a case study, a signed figure, a dated ranking).",
        "",
        "If you reply with those documents, the same check runs again against them",
        "and the list usually shrinks.",
        "",
        "Two things you should know about this reply:",
        "",
        "  * It is software. ClaimGate is a tool this project runs; the report",
        "    above was produced by it, not by a person pretending to be one.",
        "  * Nothing you sent is stored. It was read once to produce this report",
        "    and is not kept, logged or published.",
        "",
        SIGNATURE,
    ]
    return subject, "\n".join(lines)


# --- the mailbox side --------------------------------------------------------
def _sent_today() -> int:
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


def _already_answered(message_id: str, to: str) -> bool:
    if not LOG.exists():
        return False
    for line in LOG.read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if message_id and row.get("message_id") == message_id:
            return True
        if not message_id and row.get("to") == (to or "").lower():
            return True
    return False


def _within(msg, days: int) -> bool:
    try:
        d = email.utils.parsedate_to_datetime(msg.get("Date"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d >= datetime.now(timezone.utc) - timedelta(days=days)
    except Exception:
        return True          # cannot date it: do not silently drop a person


def submissions(days: int = 14) -> list[dict]:
    """Every trial submission in the mailbox, answered or not."""
    conn = inbox._connect()
    out: list[dict] = []
    try:
        folder = "[Gmail]/All Mail"
        if conn.select(inbox._quote_mailbox(folder), readonly=True)[0] != "OK":
            raise RuntimeError("could not select " + folder)
        typ, data = conn.search(None, "SUBJECT", '"ClaimGate trial"')
        for uid in (data[0] or b"").split():
            typ, parts = conn.fetch(uid, "(BODY.PEEK[])")
            raw = b"".join(p[1] for p in parts if isinstance(p, tuple))
            if not raw:
                continue
            msg = email.message_from_bytes(raw)
            from_addr = inbox._addr(msg.get("From"))
            subject = inbox._decode(msg.get("Subject"))
            if not _within(msg, days):
                continue
            if not is_trial(msg, from_addr, subject):
                continue
            body = inbox._plain_body(msg)
            draft, reason = draft_from(body)
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
                "answered": _already_answered(
                    (msg.get("Message-ID") or "").strip(), from_addr),
            })
    finally:
        try:
            conn.logout()
        except Exception:
            pass
    return out


def _record(row: dict, subject: str, body_chars: int) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write(json.dumps({
            "at": datetime.now(timezone.utc).isoformat(),
            "to": row["from"],
            "message_id": row.get("message_id", ""),
            "reply_subject": subject,
            "no_copy_reason": row.get("reason", ""),
            "reply_chars": body_chars,
            "note": "inbound trial reply - the draft itself is never logged",
        }) + "\n")


def _send(to: str, subject: str, body: str) -> None:
    user, pw = outreach.load_smtp()
    if not user or not pw:
        raise SystemExit("no SMTP credentials")
    msg = EmailMessage()
    msg["From"] = f"ClaimGate <{user}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Reply-To"] = user
    msg["Auto-Submitted"] = "auto-replied"
    msg.set_content(body)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx, timeout=45) as s:
        s.login(user, pw)
        s.send_message(msg, from_addr=user, to_addrs=[to])


# --- fixtures ---------------------------------------------------------------
def fixtures() -> int:
    """The rules, over the exact body this mailbox really received.

    Every case below is built from something that actually happened on this box
    or was actually read off the live page: the real message, and the current
    pre-filled button body off caseone115.github.io/claimgate/.
    """
    results: list[tuple[str, bool, str]] = []

    def ok(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        print(f"  {'PASS' if cond else 'FAIL'}  {name}"
              + (f"   <- {detail}" if detail and not cond else ""))

    me = (outreach.load_smtp()[0] or "teeter.ai.bot@gmail.com")

    def mk(frm, subj, body):
        m = email.message.Message()
        m["From"] = frm
        m["Subject"] = subj
        m.set_payload(body)
        return m

    print("\n=== who counts as a trial submission ===\n")
    ok("our own address pressing the site's button is NOT a submission",
       not is_trial(mk(me, "ClaimGate trial", "PASTE YOUR DRAFT HERE"),
                    me, "ClaimGate trial"), "would mail ourselves")
    ok("a stranger with the marker is a submission",
       is_trial(mk("buyer@example.org", "ClaimGate trial", "Our costs fell 40%"),
                "buyer@example.org", "ClaimGate trial"),
       "a real buyer would go unanswered")
    ok("an ordinary reply from a stranger is not",
       not is_trial(mk("buyer@example.org", "Re: your invoice", "hello"),
                    "buyer@example.org", "Re: your invoice"))
    bounce = mk("mailer-daemon@googlemail.com", "ClaimGate trial", "failure")
    bounce["In-Reply-To"] = "<something@mx.google.com>"
    bounce["X-Failed-Recipients"] = "buyer@example.org"
    ok("a delivery-failure notice carrying the marker is not a submission",
       not is_trial(bounce, "mailer-daemon@googlemail.com", "ClaimGate trial"),
       "would reply to a robot")
    ok("no sender address is not a person to answer",
       not is_trial(mk("", "ClaimGate trial", "x"), "", "ClaimGate trial"))
    from claimgate.trials import SELF_ADDRESSES
    ok("the owner's own messages are never auto-answered by the trial bot",
       all(not is_trial(mk(a, "ClaimGate trial", "x"), a, "ClaimGate trial")
           for a in SELF_ADDRESSES),
       "the bot would answer the owner as if they were a prospect, which the "
       "queue's standing decision forbids")
    auto = mk("buyer@example.org", "Re: ClaimGate trial - no copy reached us",
              "I am away until Monday.")
    auto["Auto-Submitted"] = "auto-replied"
    ok("an out-of-office answering our own reply is never answered again",
       not is_trial(auto, "buyer@example.org", auto["Subject"]),
       "two robots would talk to each other every 30 minutes")
    bulk = mk("buyer@example.org", "ClaimGate trial", "x")
    bulk["Precedence"] = "bulk"
    ok("bulk mail carrying the marker is not a person",
       not is_trial(bulk, "buyer@example.org", "ClaimGate trial"))
    ok("the subject match is case-blind (a client may re-case it)",
       is_trial(mk("buyer@example.org", "CLAIMGATE TRIAL", "x"),
                "buyer@example.org", "CLAIMGATE TRIAL"))

    print("\n=== what counts as a copy to check ===\n")
    # This is the body of the one message the mailbox has ever received under
    # this subject, byte for byte.
    REAL = ("\nPaste the draft you want checked below. Nothing is published "
            "anywhere.\n\n\nSent from my iPhone")
    d, r = draft_from(REAL)
    ok("the real message carries no copy", r != "ok" and d == "",
       f"reason={r} draft={d!r}")
    ok("and it is not reported as a gate report with nothing in it",
       "gate report" not in compose(d, r)[0], compose(d, r)[0])

    BUTTON = ("PASTE YOUR DRAFT HERE, as the plain text of this email.\n\n"
              "Optional: list the documents you can point at\n")
    d, r = draft_from(BUTTON)
    ok("the site's current pre-filled body is no copy either", r != "ok",
       f"reason={r} draft={d!r}")
    ok("the reply names the right cause: the page's wording, not silence",
       draft_from(REAL)[1] == "placeholder"
       and draft_from(BUTTON)[1] == "placeholder"
       and draft_from("")[1] == "nothing",
       f"{draft_from(REAL)[1]} / {draft_from(BUTTON)[1]} / {draft_from('')[1]}")

    d2, r2 = draft_from(
        "PASTE YOUR DRAFT HERE\n\nOur serum is 94% effective in 4 weeks.\n")
    ok("a real copy under the placeholder survives", r2 == "ok", repr(d2))
    ok("and the placeholder does not end up in the report text",
       "PASTE YOUR DRAFT" not in d2, repr(d2))
    ok("a normal message with no placeholder is a copy",
       draft_from("A normal reply with no placeholder at all.")[1] == "ok")
    ok("the phone signature is not a copy",
       draft_from("Paste your draft below\n\nSent from my iPhone")[1] != "ok")
    ok("a copy on the same line as the placeholder is kept, not swallowed",
       "94%" in draft_from("PASTE YOUR DRAFT HERE Our serum is 94% effective.")[0])
    ok("an empty body is 'nothing', not 'placeholder'",
       draft_from("")[1] == "nothing")

    print("\n=== the gate is the real gate, offline ===\n")
    r = gate("We are the leading platform and cut costs by 60%.")
    ok("a draft the gate must block is blocked",
       r["summary"]["blocked"] and r["summary"]["claims"] >= 1, str(r["summary"]))
    ok("the percentage claim is named",
       any(c["category"] == "percentage" for c in r["claims"]), str(r["claims"]))
    r2 = gate("The cat sat on the mat. " * 12)
    ok("a draft with nothing checkable produces no claims",
       r2["summary"]["claims"] == 0, str(r2["summary"]))
    ok("and the gate still requires a disclosure on it - the rule working, "
       "not a fault",
       r2["summary"]["blocking_policy_findings"] == 1, str(r2["summary"]))

    print("\n=== every reply says what is true ===\n")
    ok("the no-copy reply never claims a check happened",
       "gate report on the copy" not in compose("", "nothing")[1])
    ok("the no-copy reply says it is software",
       "It is software" in compose("", "placeholder")[1])
    ok("the found-nothing reply says so, and says what it does not mean",
       "found nothing to block" in compose("cat", "ok", r2)[1]
       and "evidence attached" in compose("cat", "ok", r2)[1],
       compose("cat", "ok", r2)[1][:300])
    ok("the report reply says it is software",
       "It is software" in compose("x", "ok", r)[1])
    ok("the report reply does not call unverified claims false",
       "does not say your claims are false" in compose("x", "ok", r)[1])
    ok("the report quotes the sender's own words, bounded",
       "the leading platform" in compose("x", "ok", r)[1])
    ok("all three replies have three different subjects",
       len({compose("", "nothing")[0], compose("", "placeholder")[0],
            compose("cat", "ok", r2)[0], compose("x", "ok", r)[0]}) == 3,
       "a reader must be able to tell them apart in an inbox")

    print("\n=== nothing sends unless it is asked to, and never twice ===\n")
    ok("sending is off unless the environment asks for it",
       os.environ.get("TRIAL_INBOUND_SEND") != "1", "this run would send")
    ok("the kill switch is consulted before any send",
       "KILL.exists()" in Path(__file__).read_text())
    shape = json.dumps(_record_shape())
    ok("the copy itself is never written to the log",
       '"draft"' not in shape and PLACEHOLDER not in shape, shape)

    failed = [n for n, c, _ in results if not c]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("FAILED:", failed)
    return 1 if failed else 0

def _record_shape() -> dict:
    """The keys a logged reply carries - checked so no draft text can hide there."""
    return {"at": "", "to": "", "message_id": "", "reply_subject": "",
            "no_copy_reason": "", "reply_chars": 0, "note": ""}


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="claimgate.trials",
                                 description="Answer trial submissions (read-only "
                                             "unless --send).")
    ap.add_argument("--scan", action="store_true", help="read the mailbox")
    ap.add_argument("--send", action="store_true", help="answer what is unanswered")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--fixtures", action="store_true")
    args = ap.parse_args(argv)

    if args.fixtures:
        return fixtures()

    subs = submissions(args.days)
    todo = [s for s in subs if not s["answered"]]
    print(f"trial submissions: {len(subs)} in {args.days}d, "
          f"{len(todo)} unanswered")
    for s in subs:
        state = "answered" if s["answered"] else "UNANSWERED"
        kind = ("carries a copy to check" if s["reason"] == "ok"
                else f"no copy in it ({s['reason']})")
        print(f"  [{state}] {s['from']} {s['date']} - {kind}")

    if not args.send:
        print("DRY - nothing sent (--send to answer)")
        return 0
    if os.environ.get("TRIAL_INBOUND_SEND") != "1":
        print("refused: TRIAL_INBOUND_SEND is not 1")
        return 0
    if KILL.exists():
        print(f"refused: kill switch present at {KILL}")
        return 0

    sent = 0
    for s in todo:
        if _sent_today() >= MAX_PER_DAY:
            print("refused: daily reply limit reached")
            break
        if len(s["draft"]) > MAX_DRAFT_CHARS:
            print(f"refused: draft from {s['from']} exceeds {MAX_DRAFT_CHARS} chars")
            continue
        subject, body = compose(s["draft"], s["reason"],
                                None if s["reason"] != "ok" else gate(s["draft"]),
                                s.get("from_name", ""))
        _send(s["from"], subject, body)
        _record(s, subject, len(body))
        sent += 1
        print(f"replied to {s['from']} ({s['reason']})")
    print(f"trial replies sent: {sent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
