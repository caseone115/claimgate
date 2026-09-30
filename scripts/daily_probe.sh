#!/usr/bin/env bash
# Daily health + honesty check for ClaimGate.
#
# Prints a short, factual status the cron agent reads before deciding what to
# do. Deliberately deterministic (no timestamps) so the cron monitor can detect
# real change rather than noise.
#
# It answers three questions:
#   1. Is the product still reachable and self-consistent?
#   2. Does the test suite still pass?
#   3. What has actually been sold / earned — and if nothing, say so plainly.
set -uo pipefail

ROOT="$HOME/claimgate"
cd "$ROOT" 2>/dev/null || { echo "STATE: missing — $ROOT does not exist"; exit 1; }

REPO="caseone115/claimgate"
SITE="https://caseone115.github.io/claimgate/"
BUY="https://teeterbot.gumroad.com/l/claimgate"
INBOX="$ROOT/state/inbox.jsonl"

# --- 1. product reachability
site_code="$(curl -s -o /dev/null -w '%{http_code}' -L "$SITE" 2>/dev/null)"
repo_code="$(curl -s -o /dev/null -w '%{http_code}' -L "https://github.com/$REPO" 2>/dev/null)"
echo "site:$site_code repo:$repo_code"

# --- 2. tests
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; else PY="python3"; fi
tests_ok=1
for t in tests/test_claimgate.py tests/test_outreach.py tests/test_kit.py \
         tests/test_hook_provenance.py; do
  test_out="$($PY "$t" 2>&1 | tail -1)"
  case "$test_out" in
    *"behaved as intended"*) echo "tests[$(basename "$t")]: $test_out" ;;
    *) echo "tests[$(basename "$t")]: FAILED — $test_out"; tests_ok=0 ;;
  esac
done

# --- 3. money. The only number that matters, reported without decoration.
rev_file="$ROOT/REVENUE.md"
if [ -f "$rev_file" ]; then
  # the ledger writes it as "**TOTAL: $0.00**", so match the token, not the line start
  echo "revenue: $(grep -m1 -o 'TOTAL:[^*]*' "$rev_file" 2>/dev/null | sed 's/[[:space:]]*$//' || echo 'TOTAL: $0.00')"
else
  echo "revenue: TOTAL: \$0.00  (no ledger)"
fi

# --- 4. anything a human sent us. The buy page is live, so a reply is the most
# valuable signal there is and it must not sit unread.
if [ -f "$ROOT/claimgate/inbox.py" ]; then
  echo "inbox: $($PY -m claimgate.inbox --days 14 2>&1 | tail -1)"
elif [ -f "$INBOX" ]; then
  echo "inbox: $(wc -l < "$INBOX" | tr -d ' ') recorded"
else
  echo "inbox: no watcher and nothing recorded"
fi

# --- 4b. did our own outreach actually arrive? A bounce is machine mail, so the
# watcher hides it from the person-mail report by design; without this line a
# failed send read exactly like a quiet mailbox, which is how the first bounce
# (info@frankcaremarketing.com, 2026-09-29) went unseen for fourteen hours.
out_out="$($PY -m claimgate.inbox --days 14 --bounces 2>&1)"; out_rc=$?
case "$out_rc" in
  0) echo "outreach-delivery: ok - no delivery failure in 14d" ;;
  5) echo "outreach-delivery: FAILED - $(echo "$out_out" | tr '\n' ' ')" ;;
  *) echo "outreach-delivery: NOT CHECKED - $(echo "$out_out" | tr '\n' ' ')" ;;
esac

# --- 5. surfaces
echo "outreach: $(python3 claimgate/outreach.py 2>/dev/null | head -1 || echo 'outreach: unavailable')"
echo "surfaces: site, github repo, cli, tests, gumroad, free starter kit"
echo "STATUS: ok"
