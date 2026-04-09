#!/bin/bash
# Step 4: Iterative Skill
# What changes: SKILL.md now has loop logic — after round 1, Claude evaluates its own
#   coverage, identifies gaps, searches again with refined queries. Max 3 rounds.
# What doesn't change: still ONE session, ONE context window. Not an agent.

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/common.sh"

echo "━━━ STEP 4: Iterative Skill ━━━"
echo "Files in this folder:"
ls "$(dirname "$0")"
echo ""
echo "Running... (watch Claude search, evaluate coverage, then search again)"

echo "$Q" | claude $CLAUDE_FLAGS \
  --system-prompt "$(cat CLAUDE.md)

---
SKILL INSTRUCTIONS (follow this methodology):
$(cat SKILL.md)" \
  --allowed-tools "WebSearch,WebFetch,Read,Write,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" \
  --mcp-config mcp.json \
  | tee output.md

score_output output.md "$Q"
