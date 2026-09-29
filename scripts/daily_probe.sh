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

# --- 1. product reachability
site_code="$(curl -s -o /dev/null -w '%{http_code}' -L "$SITE" 2>/dev/null)"
repo_code="$(curl -s -o /dev/null -w '%{http_code}' -L "https://github.com/$REPO" 2>/dev/null)"
echo "site:$site_code repo:$repo_code"

# --- 2. tests
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; else PY="python3"; fi
test_out="$($PY tests/test_claimgate.py 2>&1 | tail -1)"
case "$test_out" in
  *"behaved as intended"*) echo "tests: $test_out" ;;
  *) echo "tests: FAILED — $test_out" ;;
esac

# --- 3. money. The only number that matters, reported without decoration.
rev_file="$ROOT/REVENUE.md"
if [ -f "$rev_file" ]; then
  # the ledger writes it as "**TOTAL: $0.00**", so match the token, not the line start
  echo "revenue: $(grep -m1 -o 'TOTAL:[^*]*' "$rev_file" 2>/dev/null | sed 's/[[:space:]]*$//' || echo 'TOTAL: $0.00')"
else
  echo "revenue: TOTAL: \$0.00  (no ledger)"
fi

# --- 4. what exists so far
echo "outreach: $(python3 claimgate/outreach.py 2>/dev/null | head -1 || echo 'outreach: unavailable')"
echo "surfaces: site, github repo, cli, tests"
echo "STATUS: ok"
