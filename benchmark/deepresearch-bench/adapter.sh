#!/usr/bin/env bash
set -euo pipefail

# adapter.sh — Run a workshop research agent against DeepResearch-Bench tasks.
# Adapts the workshop's step-based agent system to the bench's JSONL format.
#
# Usage:
#   ./benchmark/deepresearch-bench/adapter.sh \
#     --bench-dir /tmp/deep_research_bench \
#     --step 6 \
#     --max 3

WORKSHOP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Defaults
BENCH_DIR=""
STEP=6
MODEL="sonnet"
OUTPUT_NAME=""
MAX_TASKS=0
LANG_FILTER="en"

usage() {
  cat >&2 <<EOF
Usage: $0 --bench-dir <path> [options]

Required:
  --bench-dir PATH    Path to cloned deep_research_bench repo

Options:
  --step N            Workshop step to use: 2-6 (default: 6)
  --model MODEL       Claude model (default: sonnet)
  --output NAME       Output name (default: workshop-stepN)
  --max N             Limit tasks, 0 = all (default: 0)
  --lang LANG         Language: en|zh|all (default: en)
  -h, --help          Show this help
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bench-dir)  BENCH_DIR="$2"; shift 2 ;;
    --step)       STEP="$2"; shift 2 ;;
    --model)      MODEL="$2"; shift 2 ;;
    --output)     OUTPUT_NAME="$2"; shift 2 ;;
    --max)        MAX_TASKS="$2"; shift 2 ;;
    --lang)       LANG_FILTER="$2"; shift 2 ;;
    -h|--help)    usage ;;
    *)            echo "Unknown: $1" >&2; usage ;;
  esac
done

[[ -z "$BENCH_DIR" ]] && { echo "Error: --bench-dir required" >&2; usage; }
[[ -z "$OUTPUT_NAME" ]] && OUTPUT_NAME="workshop-step${STEP}"

QUERY_FILE="$BENCH_DIR/data/test_data/query.jsonl"
[[ ! -f "$QUERY_FILE" ]] && { echo "Error: $QUERY_FILE not found" >&2; exit 1; }

OUTPUT_DIR="$BENCH_DIR/data/test_data/raw_data"
mkdir -p "$OUTPUT_DIR"
OUTPUT_FILE="$OUTPUT_DIR/${OUTPUT_NAME}.jsonl"

command -v claude &>/dev/null || { echo "Error: claude CLI not found" >&2; exit 1; }

# ── Build system prompt for the chosen step ──────────────────────────
build_system_prompt() {
  local step="$1"
  local prompt=""

  # Always include context
  prompt="$(cat "$WORKSHOP_DIR/step-1-context/CLAUDE.md")"

  case "$step" in
    2)
      prompt="$prompt
---
$(cat "$WORKSHOP_DIR/step-2-skill/.claude/skills/deep-research/SKILL.md")"
      ;;
    3)
      prompt="$prompt
---
$(cat "$WORKSHOP_DIR/step-3-tool/.claude/skills/deep-research/SKILL.md")"
      ;;
    4)
      prompt="$prompt
---
$(cat "$WORKSHOP_DIR/step-4-iterative/.claude/skills/deep-research/SKILL.md")"
      ;;
    5)
      local skill verify_skill
      skill="$(cat "$WORKSHOP_DIR/step-5-verification/.claude/skills/deep-research/SKILL.md")"
      verify_skill="$(cat "$WORKSHOP_DIR/step-5-verification/.claude/skills/verify-research/SKILL.md")"
      prompt="$prompt
---
RESEARCH SKILL:
$skill
---
VERIFICATION AGENT SKILL:
$verify_skill"
      ;;
    6)
      local orch searcher critic synth
      orch="$(cat "$WORKSHOP_DIR/step-6-team/.claude/skills/orchestrator/SKILL.md")"
      searcher="$(cat "$WORKSHOP_DIR/step-6-team/.claude/skills/searcher/SKILL.md")"
      critic="$(cat "$WORKSHOP_DIR/step-6-team/.claude/skills/critic/SKILL.md")"
      synth="$(cat "$WORKSHOP_DIR/step-6-team/.claude/skills/synthesizer/SKILL.md")"
      prompt="$prompt
---
ORCHESTRATOR SKILL:
$orch
---
SEARCHER AGENT SKILL:
$searcher
---
CRITIC AGENT SKILL:
$critic
---
SYNTHESIZER AGENT SKILL:
$synth"
      ;;
    *)
      echo "Error: step must be 2-6" >&2; exit 1
      ;;
  esac

  echo "$prompt"
}

# ── Build allowed tools for the step ─────────────────────────────────
build_tools() {
  local step="$1"
  case "$step" in
    2) echo "" ;;  # No tools
    3|4) echo "WebSearch,WebFetch,Read,Write,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" ;;
    5|6) echo "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" ;;
  esac
}

# ── MCP config ───────────────────────────────────────────────────────
MCP_CONFIG="$(mktemp)"
cat > "$MCP_CONFIG" <<MCPEOF
{
  "mcpServers": {
    "research-tools": {
      "command": "python3",
      "args": ["$WORKSHOP_DIR/step-3-tool/mcp-servers/arxiv_server.py"]
    }
  }
}
MCPEOF
trap "rm -f $MCP_CONFIG" EXIT

# ── Process one task ─────────────────────────────────────────────────
process_task() {
  local id="$1" prompt="$2" task_num="$3" total="$4"

  echo "[${task_num}/${total}] Processing task ${id}..." >&2

  local system_prompt
  system_prompt="$(build_system_prompt "$STEP")"
  local tools
  tools="$(build_tools "$STEP")"

  local flags="-p --output-format text --model $MODEL --dangerously-skip-permissions --no-session-persistence"
  [[ -n "$tools" ]] && flags="$flags --allowedTools $tools --mcp-config $MCP_CONFIG"

  local article
  article=$(echo "$prompt" | claude $flags --system-prompt "$system_prompt" 2>/dev/null) || {
    echo "[${task_num}/${total}] FAILED task ${id}" >&2
    return 1
  }

  # Output as JSONL
  local json_prompt json_article
  json_prompt=$(printf '%s' "$prompt" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
  json_article=$(printf '%s' "$article" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
  echo "{\"id\": ${id}, \"prompt\": ${json_prompt}, \"article\": ${json_article}}"

  echo "[${task_num}/${total}] Done task ${id}" >&2
}

# ── Main ─────────────────────────────────────────────────────────────
echo "=== Workshop Agent → DeepResearch-Bench ===" >&2
echo "Step:    $STEP" >&2
echo "Model:   $MODEL" >&2
echo "Output:  $OUTPUT_FILE" >&2
echo "" >&2

# Read and filter tasks
TASKS=()
while IFS= read -r line; do
  task_lang=$(echo "$line" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('language','en'))")
  [[ "$LANG_FILTER" == "all" || "$task_lang" == "$LANG_FILTER" ]] && TASKS+=("$line")
done < "$QUERY_FILE"

TOTAL=${#TASKS[@]}
echo "Found $TOTAL tasks" >&2
[[ "$MAX_TASKS" -gt 0 && "$MAX_TASKS" -lt "$TOTAL" ]] && TOTAL=$MAX_TASKS

> "$OUTPUT_FILE"

COMPLETED=0
FAILED=0

for ((i=0; i<TOTAL; i++)); do
  line="${TASKS[$i]}"
  task_id=$(echo "$line" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['id'])")
  task_prompt=$(echo "$line" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['prompt'])")

  if result=$(process_task "$task_id" "$task_prompt" "$((i+1))" "$TOTAL"); then
    echo "$result" >> "$OUTPUT_FILE"
    COMPLETED=$((COMPLETED + 1))
  else
    FAILED=$((FAILED + 1))
  fi
done

echo "" >&2
echo "=== Complete: $COMPLETED/$TOTAL succeeded, $FAILED failed ===" >&2
echo "Output: $OUTPUT_FILE" >&2
echo "" >&2
echo "Next: Score with RACE/FACT evaluation or the workshop evaluator:" >&2
echo "  python benchmark/evaluate.py --input <report.md> --quick" >&2
