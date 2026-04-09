#!/bin/bash
# Step 6: Team of Agents
# What changes: instead of one agent doing everything, three specialists run in sequence.
#   Searcher: dedicated to finding papers, writes searcher_output.md
#   Critic:   reads searcher output, evaluates methodology, writes critic_output.md
#   Synthesizer: reads both, writes the final report
# Each agent has its own context window and one job.
# They communicate through FILES — not shared memory.

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/common.sh"

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

echo "$Q" | claude $CLAUDE_FLAGS \
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
  | tee output.md

score_output output.md "$Q"
