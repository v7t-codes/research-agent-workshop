#!/usr/bin/env bash
#
# Leaderboard Runner — evaluates all student submissions
#
# For each folder in students/ (excluding template/):
#   1. Start their MCP server
#   2. Run their agent against all 3 test problems
#   3. Score each output (heuristic)
#   4. Print sorted leaderboard
#
# Usage (from repo root):
#   bash benchmark/run_leaderboard.sh               # score all students
#   bash benchmark/run_leaderboard.sh alice-bob     # score one group
#
# Requirements: ANTHROPIC_API_KEY set, claude CLI installed, fastmcp installed
# Run from a plain terminal (not inside Claude Code) to avoid MCP contamination.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STUDENTS_DIR="$REPO_ROOT/students"
BENCHMARK_DIR="$REPO_ROOT/benchmark"

[[ -z "${ANTHROPIC_API_KEY:-}" ]] && { echo "Error: ANTHROPIC_API_KEY not set"; exit 1; }
command -v claude &>/dev/null || { echo "Error: claude CLI not found"; exit 1; }

# Test problems
declare -A QUESTIONS
QUESTIONS[test-1]="$(cat "$BENCHMARK_DIR/test/test-1.md" | grep -A2 "^## Question" | tail -1)"
QUESTIONS[test-2]="$(cat "$BENCHMARK_DIR/test/test-2.md" | grep -A2 "^## Question" | tail -1)"
QUESTIONS[test-3]="$(cat "$BENCHMARK_DIR/test/test-3.md" | grep -A2 "^## Question" | tail -1)"

MODEL="sonnet"
COMMON_FLAGS="-p --output-format text --model $MODEL --dangerously-skip-permissions --no-session-persistence --bare"

# Determine which students to score
if [ $# -gt 0 ]; then
    TARGETS=("$@")
else
    TARGETS=()
    for dir in "$STUDENTS_DIR"/*/; do
        name="$(basename "$dir")"
        [[ "$name" == "template" ]] && continue
        [[ "$name" == "README.md" ]] && continue
        TARGETS+=("$name")
    done
fi

if [ ${#TARGETS[@]} -eq 0 ]; then
    echo "No student submissions found in students/"
    exit 0
fi

echo "========================================"
echo "  WORKSHOP LEADERBOARD"
echo "  $(date '+%Y-%m-%d %H:%M')"
echo "  ${#TARGETS[@]} submission(s)"
echo "========================================"
echo ""

declare -A FINAL_SCORES

for group in "${TARGETS[@]}"; do
    group_dir="$STUDENTS_DIR/$group"

    if [ ! -d "$group_dir" ]; then
        echo "[$group] not found — skipping"
        continue
    fi

    # Check required files
    missing=0
    for f in CLAUDE.md .claude/skills/deep-research/SKILL.md mcp_server.py; do
        if [ ! -f "$group_dir/$f" ]; then
            echo "[$group] missing $f — skipping"
            missing=1
            break
        fi
    done
    [ $missing -eq 1 ] && continue

    echo "── $group ──────────────────────────────"

    # Read their files
    context=$(cat "$group_dir/CLAUDE.md")
    skill=$(cat "$group_dir/.claude/skills/deep-research/SKILL.md")

    # Start their MCP server (in background, scoped to this group)
    mcp_pid=""
    mcp_config_file=""
    if python3 -c "import fastmcp" 2>/dev/null && [ -f "$group_dir/mcp_server.py" ]; then
        mcp_config_file=$(mktemp /tmp/mcp-XXXXXX.json)
        cat > "$mcp_config_file" << MCPEOF
{
  "mcpServers": {
    "my-tools": {
      "command": "python3",
      "args": ["$group_dir/mcp_server.py"]
    }
  }
}
MCPEOF
    fi

    # Determine allowed tools based on what their SKILL.md requests
    allowed_tools="WebSearch,WebFetch,Read,Write"
    if grep -q "mcp__" "$group_dir/.claude/skills/deep-research/SKILL.md" 2>/dev/null; then
        # Extract tool names from allowed-tools line
        mcp_tools=$(grep "allowed-tools:" "$group_dir/.claude/skills/deep-research/SKILL.md" | sed 's/allowed-tools://g' | tr ' ' '\n' | grep "^mcp__" | tr '\n' ',' | sed 's/,$//')
        [ -n "$mcp_tools" ] && allowed_tools="$allowed_tools,$mcp_tools"
    fi
    if grep -qi "Agent" "$group_dir/.claude/skills/deep-research/SKILL.md" 2>/dev/null; then
        allowed_tools="$allowed_tools,Agent"
    fi

    # Build MCP config flag
    mcp_flag=""
    [ -n "${mcp_config_file:-}" ] && mcp_flag="--mcp-config $mcp_config_file"

    # Run against each test problem
    scores=()
    mkdir -p "$group_dir/scores"

    for problem in test-1 test-2 test-3; do
        question_file="$BENCHMARK_DIR/test/$problem.md"
        [ ! -f "$question_file" ] && continue

        question=$(grep -A100 "^## Question" "$question_file" | tail -n+2 | head -20 | tr '\n' ' ')
        output_file="$group_dir/scores/$problem-output.md"
        score_file="$group_dir/scores/$problem-score.txt"

        printf "  %-10s running... " "$problem"

        # Run their agent
        echo "$question" | claude $COMMON_FLAGS \
            --system-prompt "$context

---
SKILL INSTRUCTIONS:
$skill" \
            --allowed-tools "$allowed_tools" \
            $mcp_flag \
            > "$output_file" 2>/dev/null || true

        if [ ! -s "$output_file" ]; then
            printf "FAILED (empty output)\n"
            scores+=("0")
            continue
        fi

        # Score it
        score=$(python3 "$BENCHMARK_DIR/evaluate.py" \
            --input "$output_file" \
            --quick \
            --question "$question" 2>/dev/null | grep "TOTAL SCORE" | grep -o '[0-9.]*' | head -1)

        score="${score:-0}"
        scores+=("$score")
        echo "$score" > "$score_file"
        printf "%s/100\n" "$score"
    done

    # Cleanup MCP config temp file
    [ -n "${mcp_config_file:-}" ] && rm -f "$mcp_config_file"

    # Average score
    if [ ${#scores[@]} -gt 0 ]; then
        avg=$(python3 -c "scores=[${scores[*]}]; print(round(sum(scores)/len(scores),1))" 2>/dev/null || echo "0")
        echo "  Average: $avg/100"
        FINAL_SCORES["$group"]="$avg"
        # Write summary
        python3 -c "
scores = [${scores[*]}]
avg = round(sum(scores)/len(scores), 1)
import json, os
summary = {'group': '$group', 'scores': {'test-1': scores[0] if len(scores)>0 else 0, 'test-2': scores[1] if len(scores)>1 else 0, 'test-3': scores[2] if len(scores)>2 else 0}, 'average': avg}
with open('$group_dir/scores/summary.json', 'w') as f:
    json.dump(summary, f, indent=2)
" 2>/dev/null || true
    fi
    echo ""
done

# Print sorted leaderboard
echo "========================================"
echo "  FINAL LEADERBOARD"
echo "========================================"
echo ""

# Sort by score descending
declare -A sorted
for group in "${!FINAL_SCORES[@]}"; do
    sorted["${FINAL_SCORES[$group]}___$group"]="$group"
done

rank=1
prev_score=""
for key in $(echo "${!sorted[@]}" | tr ' ' '\n' | sort -t_ -k1 -rn); do
    group="${sorted[$key]}"
    score="${FINAL_SCORES[$group]}"
    if [ "$score" = "$prev_score" ]; then
        printf "  =%-3s %-20s %s/100\n" "$rank" "$group" "$score"
    else
        printf "  %-4s %-20s %s/100\n" "$rank." "$group" "$score"
        rank=$((rank + 1))
    fi
    prev_score="$score"
done

echo ""
echo "========================================"
echo "  Detailed scores saved to students/<group>/scores/"
echo "========================================"
