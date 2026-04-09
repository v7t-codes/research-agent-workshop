#!/bin/bash
# Step 5: Verification Agent
# What changes: after research, a SECOND Claude process is spawned via the Agent tool.
#   It runs in its own context window — no memory of the research session.
#   It searches for each cited paper by exact title and flags anything it can't find.
# What doesn't change: same research methodology as step 4.
# This is the boundary: step 4 is one process. Step 5 is two processes.

set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
Q="$(cat "$REPO/demo/QUESTION.txt")"

echo "━━━ STEP 5: Verification Agent ━━━"
echo "Files in this folder:"
ls "$(dirname "$0")"
echo ""
echo "SKILL.md      = research methodology (runs in this session)"
echo "SKILL-verify.md = verification agent (spawned as separate process)"
echo ""
echo "Running... (watch for the verification agent starting after research completes)"

echo "$Q" | claude -p --bare --model sonnet \
  --system-prompt "$(cat CLAUDE.md)

---
RESEARCH SKILL:
$(cat SKILL.md)

---
VERIFICATION AGENT SKILL (dispatch this as a subagent):
$(cat SKILL-verify.md)" \
  --allowed-tools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" \
  --mcp-config mcp.json \
  --dangerously-skip-permissions \
  | tee output.md

echo ""
echo "━━━ SCORE ━━━"
SCORER="$REPO/presenter/evaluate.py"; [ -f "$SCORER" ] && python3 "$SCORER" --input output.md --quick --question "$Q"
