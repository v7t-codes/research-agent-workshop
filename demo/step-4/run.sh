#!/bin/bash
# Step 4: Iterative Skill
# What changes: SKILL.md now has loop logic — after round 1, Claude evaluates its own
#   coverage, identifies gaps, searches again with refined queries. Max 3 rounds.
# What doesn't change: still ONE session, ONE context window. Not an agent.
# Note: heuristic score may dip slightly (process narration text shifts keyword ratios).
#   Use the LLM scorer (drop --quick) for an accurate reading.

set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
Q="$(cat "$REPO/demo/QUESTION.txt")"

echo "━━━ STEP 4: Iterative Skill ━━━"
echo "Files in this folder:"
ls "$(dirname "$0")"
echo ""
echo "Running... (watch Claude search, evaluate coverage, then search again)"

echo "$Q" | claude -p --bare --model sonnet \
  --system-prompt "$(cat CLAUDE.md)

---
SKILL INSTRUCTIONS (follow this methodology):
$(cat SKILL.md)" \
  --allowed-tools "WebSearch,WebFetch,Read,Write,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" \
  --mcp-config mcp.json \
  --dangerously-skip-permissions \
  | tee output.md

echo ""
echo "━━━ SCORE (heuristic) ━━━"
python3 "$REPO/benchmark/evaluate.py" --input output.md --quick --question "$Q"
echo ""
echo "Note: if heuristic dips below step 3, run without --quick for accurate LLM score."
