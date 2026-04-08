#!/bin/bash
#
# Research Agent Workshop — Step-by-Step Test Runner
#
# Runs each step (0-6) using Claude Code CLI on a benchmark question,
# saves the output, and scores it. Proves the staircase works.
#
# Usage:
#   ./test-run/run_steps.sh              # Run all steps
#   ./test-run/run_steps.sh 0            # Run only step 0
#   ./test-run/run_steps.sh 2 4          # Run steps 2 and 4
#
# Each step takes 1-5 minutes depending on depth.

set -euo pipefail

WORKSHOP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_DIR="$WORKSHOP_DIR/test-run"
OUTPUTS_DIR="$TEST_DIR/outputs"
SCORES_DIR="$TEST_DIR/scores"

mkdir -p "$OUTPUTS_DIR" "$SCORES_DIR"

# ── Staircase question ──
# Uses bench #69 (A2A vs MCP). Requires current data — training data can't fully answer.
# This makes the staircase clear: steps 0-2 score low, step 3+ jumps.
QUESTION="Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."

# Common flags
MODEL="sonnet"
COMMON_FLAGS="-p --output-format text --model $MODEL --dangerously-skip-permissions --no-session-persistence"

# MCP config for steps 3+
MCP_CONFIG="$TEST_DIR/mcp-config.json"

echo "========================================"
echo "  RESEARCH AGENT WORKSHOP — TEST RUN"
echo "========================================"
echo "Workshop dir: $WORKSHOP_DIR"
echo "Model: $MODEL"
echo "Question: A2A vs MCP (bench #69)"
echo ""

# Determine which steps to run
if [ $# -eq 0 ]; then
    STEPS="0 1 2 3 4 5 6"
else
    STEPS="$@"
fi

# Create MCP config (needed for steps 3+)
setup_mcp() {
    cat > "$MCP_CONFIG" << MCPEOF
{
    "mcpServers": {
        "research-tools": {
            "command": "python3",
            "args": ["$WORKSHOP_DIR/step-3-tool/mcp-servers/arxiv_server.py"]
        }
    }
}
MCPEOF
}

score_output() {
    local step="$1"
    local output_file="$OUTPUTS_DIR/step-$step.md"
    local score_file="$SCORES_DIR/step-$step.txt"

    if [ ! -s "$output_file" ]; then
        echo "  WARNING: Output is empty, skipping scoring"
        echo "EMPTY OUTPUT" > "$score_file"
        return 1
    fi

    python3 "$WORKSHOP_DIR/benchmark/evaluate.py" \
        --input "$output_file" \
        --quick \
        --question "$QUESTION" \
        | tee "$score_file"
}

# ── Step 0: Raw Claude ──
run_step_0() {
    echo ""
    echo "━━━ STEP 0: Raw Claude (no context, no skill) ━━━"

    echo "$QUESTION" | claude $COMMON_FLAGS \
        --system-prompt "You are a helpful assistant." \
        --disallowedTools "WebSearch,WebFetch,Agent" \
        > "$OUTPUTS_DIR/step-0.md" 2>/dev/null || true

    echo "Output saved to $OUTPUTS_DIR/step-0.md ($(wc -c < "$OUTPUTS_DIR/step-0.md" | tr -d ' ') bytes)"
    score_output 0
}

# ── Step 1: Context (CLAUDE.md) ──
run_step_1() {
    echo ""
    echo "━━━ STEP 1: Context (CLAUDE.md) ━━━"

    CONTEXT=$(cat "$WORKSHOP_DIR/step-1-context/CLAUDE.md")

    echo "$QUESTION" | claude $COMMON_FLAGS \
        --system-prompt "$CONTEXT" \
        --disallowedTools "WebSearch,WebFetch,Agent" \
        > "$OUTPUTS_DIR/step-1.md" 2>/dev/null || true

    echo "Output saved to $OUTPUTS_DIR/step-1.md ($(wc -c < "$OUTPUTS_DIR/step-1.md" | tr -d ' ') bytes)"
    score_output 1
}

# ── Step 2: Skill (SKILL.md) ──
run_step_2() {
    echo ""
    echo "━━━ STEP 2: Skill (one-pass research methodology) ━━━"

    CONTEXT=$(cat "$WORKSHOP_DIR/step-1-context/CLAUDE.md")
    SKILL=$(cat "$WORKSHOP_DIR/step-2-skill/.claude/skills/deep-research/SKILL.md")

    echo "$QUESTION" | claude $COMMON_FLAGS \
        --system-prompt "$CONTEXT

---
SKILL INSTRUCTIONS (follow this methodology):
$SKILL" \
        --disallowedTools "WebSearch,WebFetch,Agent" \
        > "$OUTPUTS_DIR/step-2.md" 2>/dev/null || true

    echo "Output saved to $OUTPUTS_DIR/step-2.md ($(wc -c < "$OUTPUTS_DIR/step-2.md" | tr -d ' ') bytes)"
    score_output 2
}

# ── Step 3: Custom Tool (MCP + WebSearch) ──
run_step_3() {
    echo ""
    echo "━━━ STEP 3: Custom Tool (MCP server + WebSearch) ━━━"

    setup_mcp

    CONTEXT=$(cat "$WORKSHOP_DIR/step-1-context/CLAUDE.md")
    SKILL=$(cat "$WORKSHOP_DIR/step-3-tool/.claude/skills/deep-research/SKILL.md")

    echo "$QUESTION" | claude $COMMON_FLAGS \
        --system-prompt "$CONTEXT

---
SKILL INSTRUCTIONS (follow this methodology):
$SKILL" \
        --allowedTools "WebSearch,WebFetch,Read,Write,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" \
        --mcp-config "$MCP_CONFIG" \
        > "$OUTPUTS_DIR/step-3.md" 2>/dev/null || true

    echo "Output saved to $OUTPUTS_DIR/step-3.md ($(wc -c < "$OUTPUTS_DIR/step-3.md" | tr -d ' ') bytes)"
    score_output 3
}

# ── Step 4: Iterative Skill ──
run_step_4() {
    echo ""
    echo "━━━ STEP 4: Iterative Skill (search → evaluate → refine → repeat) ━━━"

    setup_mcp

    CONTEXT=$(cat "$WORKSHOP_DIR/step-1-context/CLAUDE.md")
    SKILL=$(cat "$WORKSHOP_DIR/step-4-iterative/.claude/skills/deep-research/SKILL.md")

    echo "$QUESTION" | claude $COMMON_FLAGS \
        --system-prompt "$CONTEXT

---
SKILL INSTRUCTIONS (follow this methodology):
$SKILL" \
        --allowedTools "WebSearch,WebFetch,Read,Write,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" \
        --mcp-config "$MCP_CONFIG" \
        > "$OUTPUTS_DIR/step-4.md" 2>/dev/null || true

    echo "Output saved to $OUTPUTS_DIR/step-4.md ($(wc -c < "$OUTPUTS_DIR/step-4.md" | tr -d ' ') bytes)"
    score_output 4
}

# ── Step 5: Verification Agent ──
run_step_5() {
    echo ""
    echo "━━━ STEP 5: Verification Agent (separate Claude process) ━━━"

    setup_mcp

    CONTEXT=$(cat "$WORKSHOP_DIR/step-1-context/CLAUDE.md")
    SKILL=$(cat "$WORKSHOP_DIR/step-5-verification/.claude/skills/deep-research/SKILL.md")
    VERIFY_SKILL=$(cat "$WORKSHOP_DIR/step-5-verification/.claude/skills/verify-research/SKILL.md")

    echo "$QUESTION" | claude $COMMON_FLAGS \
        --system-prompt "$CONTEXT

---
RESEARCH SKILL (follow this methodology):
$SKILL

---
VERIFICATION AGENT SKILL (give this to the verification agent when dispatching):
$VERIFY_SKILL" \
        --allowedTools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" \
        --mcp-config "$MCP_CONFIG" \
        > "$OUTPUTS_DIR/step-5.md" 2>/dev/null || true

    echo "Output saved to $OUTPUTS_DIR/step-5.md ($(wc -c < "$OUTPUTS_DIR/step-5.md" | tr -d ' ') bytes)"
    score_output 5
}

# ── Step 6: Team of Agents ──
run_step_6() {
    echo ""
    echo "━━━ STEP 6: Team of Agents (searcher + critic + synthesizer) ━━━"

    setup_mcp

    CONTEXT=$(cat "$WORKSHOP_DIR/step-1-context/CLAUDE.md")
    ORCH=$(cat "$WORKSHOP_DIR/step-6-team/.claude/skills/orchestrator/SKILL.md")
    SEARCHER=$(cat "$WORKSHOP_DIR/step-6-team/.claude/skills/searcher/SKILL.md")
    CRITIC=$(cat "$WORKSHOP_DIR/step-6-team/.claude/skills/critic/SKILL.md")
    SYNTHESIZER=$(cat "$WORKSHOP_DIR/step-6-team/.claude/skills/synthesizer/SKILL.md")

    echo "$QUESTION" | claude $COMMON_FLAGS \
        --system-prompt "$CONTEXT

---
ORCHESTRATOR SKILL (follow this):
$ORCH

---
SEARCHER AGENT SKILL (give this to the searcher agent):
$SEARCHER

---
CRITIC AGENT SKILL (give this to the critic agent):
$CRITIC

---
SYNTHESIZER AGENT SKILL (give this to the synthesizer agent):
$SYNTHESIZER" \
        --allowedTools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" \
        --mcp-config "$MCP_CONFIG" \
        > "$OUTPUTS_DIR/step-6.md" 2>/dev/null || true

    echo "Output saved to $OUTPUTS_DIR/step-6.md ($(wc -c < "$OUTPUTS_DIR/step-6.md" | tr -d ' ') bytes)"
    score_output 6
}

# ── Run requested steps ──
for step in $STEPS; do
    case $step in
        0) run_step_0 ;;
        1) run_step_1 ;;
        2) run_step_2 ;;
        3) run_step_3 ;;
        4) run_step_4 ;;
        5) run_step_5 ;;
        6) run_step_6 ;;
        *) echo "Unknown step: $step" ;;
    esac
done

# ── Show summary ──
echo ""
echo "========================================"
echo "  SCORE STAIRCASE"
echo "========================================"
for step in $STEPS; do
    if [ -f "$SCORES_DIR/step-$step.txt" ]; then
        score=$(grep "TOTAL SCORE" "$SCORES_DIR/step-$step.txt" 2>/dev/null | grep -o '[0-9.]*' | head -1)
        if [ -n "$score" ]; then
            printf "  Step %s: %6s/100\n" "$step" "$score"
        else
            printf "  Step %s: FAILED\n" "$step"
        fi
    fi
done
echo "========================================"
