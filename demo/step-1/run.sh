#!/bin/bash
# Step 1: Context (CLAUDE.md)
# What changes: Claude gets an identity — domain, sources, citation format, constraints.
# What doesn't change: no methodology, no tools, still from training data only.

set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
Q="$(cat "$REPO/demo/QUESTION.txt")"

echo "━━━ STEP 1: Context (CLAUDE.md) ━━━"
echo "Files in this folder:"
ls "$(dirname "$0")"
echo ""
echo "Running..."

echo "$Q" | claude -p --bare --model sonnet \
  --system-prompt "$(cat CLAUDE.md)" \
  --disallowed-tools "WebSearch,WebFetch,Agent" \
  --dangerously-skip-permissions \
  | tee output.md

echo ""
echo "━━━ SCORE ━━━"
python3 "$REPO/benchmark/evaluate.py" --input output.md --quick --question "$Q"
