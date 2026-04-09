#!/bin/bash
# Step 5: Verification Agent
# What changes: after research, a SECOND Claude process is spawned via the Agent tool.
#   It runs in its own context window — no memory of the research session.
#   It searches for each cited paper by exact title and flags anything it can't find.
# This is the boundary: step 4 is one process. Step 5 is two processes.

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/common.sh"

echo "━━━ STEP 5: Verification Agent ━━━"
echo "Files in this folder:"
ls "$(dirname "$0")"
echo ""
echo "SKILL.md         = research methodology (calls Agent tool at the end)"
echo "SKILL-verify.md  = verification agent's instructions (runs in own context)"
echo ""
echo "Running... (watch it research, then spawn a verification agent)"

echo "$Q" | claude $CLAUDE_FLAGS \
  --system-prompt "$(cat CLAUDE.md)

---
RESEARCH SKILL:
$(cat SKILL.md)

---
VERIFICATION AGENT SKILL (dispatch this as a subagent):
$(cat SKILL-verify.md)" \
  --allowed-tools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" \
  --mcp-config mcp.json \
  | tee output.md

score_output output.md "$Q"
