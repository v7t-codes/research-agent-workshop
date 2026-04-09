#!/bin/bash
# Step 2: Skill (SKILL.md)
# What changes: Claude now has a research methodology — decompose first, structured output format.
# What doesn't change: still no real-time sources, still from training data.

set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
Q="$(cat "$REPO/demo/QUESTION.txt")"

echo "━━━ STEP 2: Skill (SKILL.md) ━━━"
echo "Files in this folder:"
ls "$(dirname "$0")"
echo ""
echo "Running..."

echo "$Q" | claude -p --bare --model sonnet \
  --system-prompt "$(cat CLAUDE.md)

---
SKILL INSTRUCTIONS (follow this methodology):
$(cat SKILL.md)" \
  --disallowed-tools "WebSearch,WebFetch,Agent" \
  --dangerously-skip-permissions \
  | tee output.md

echo ""
echo "━━━ SCORE ━━━"
python3 "$REPO/benchmark/evaluate.py" --input output.md --quick --question "$Q"
