#!/bin/bash
# Step 6: Team of Agents
# What changes: instead of one agent doing everything, three specialists run in sequence.
#   Searcher: dedicated to finding papers, writes searcher_output.md
#   Critic:   reads searcher output, evaluates methodology, writes critic_output.md
#   Synthesizer: reads both, writes the final report
# Each agent has its own context window and one job.
# They communicate through FILES — not shared memory.

set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
Q="$(cat "$REPO/demo/QUESTION.txt")"

echo "━━━ STEP 6: Team of Agents ━━━"
echo "Files in this folder:"
ls "$(dirname "$0")"
echo ""
echo "SKILL-orchestrator.md  = coordinates the pipeline"
echo "SKILL-searcher.md      = finds papers (own context window)"
echo "SKILL-critic.md        = evaluates evidence (own context window)"
echo "SKILL-synthesizer.md   = writes final report (own context window)"
echo ""
echo "Running... (watch three agents spawn in sequence)"

echo "$Q" | claude -p --bare --model sonnet \
  --system-prompt "$(cat CLAUDE.md)

---
ORCHESTRATOR SKILL:
$(cat SKILL-orchestrator.md)

---
SEARCHER AGENT SKILL (dispatch as subagent):
$(cat SKILL-searcher.md)

---
CRITIC AGENT SKILL (dispatch as subagent):
$(cat SKILL-critic.md)

---
SYNTHESIZER AGENT SKILL (dispatch as subagent):
$(cat SKILL-synthesizer.md)" \
  --allowed-tools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" \
  --mcp-config mcp.json \
  --dangerously-skip-permissions \
  | tee output.md

echo ""
echo "━━━ SCORE ━━━"
SCORER="$REPO/presenter/evaluate.py"; [ -f "$SCORER" ] && python3 "$SCORER" --input output.md --quick --question "$Q"
