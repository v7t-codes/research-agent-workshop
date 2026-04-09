#!/bin/bash
# Step 3: Custom Tool (arxiv_server.py)
# What changes: Claude can now call search_arxiv() and search_semantic_scholar().
#   Real paper titles, abstracts, dates, URLs from live APIs.
#   The source grounding factor unlocks: reports with real URLs score ~2x higher.
# What doesn't change: still one pass, no iteration, no verification.

set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
Q="$(cat "$REPO/demo/QUESTION.txt")"

echo "━━━ STEP 3: Custom Tool (MCP server) ━━━"
echo "Files in this folder:"
ls "$(dirname "$0")"
echo ""
echo "Running... (this makes real API calls — watch Claude call search_arxiv)"

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
echo "━━━ SCORE ━━━"
python3 "$REPO/benchmark/evaluate.py" --input output.md --quick --question "$Q"
