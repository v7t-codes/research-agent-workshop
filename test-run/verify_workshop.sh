#!/bin/bash
#
# Workshop Verification Script
# Run this after all tasks are complete. Every check must PASS.
#
# Usage: ./test-run/verify_workshop.sh
#

set -e

WORKSHOP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0
TOTAL=0

check() {
    TOTAL=$((TOTAL + 1))
    local description="$1"
    local condition="$2"

    if eval "$condition" 2>/dev/null; then
        echo "  ✓ $description"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $description"
        FAIL=$((FAIL + 1))
    fi
}

file_exists() { [ -f "$1" ]; }
dir_exists() { [ -d "$1" ]; }
file_min_bytes() { [ -f "$1" ] && [ "$(wc -c < "$1" | tr -d ' ')" -ge "$2" ]; }
file_contains() { [ -f "$1" ] && grep -q "$2" "$1"; }
valid_json() { [ -f "$1" ] && python3 -m json.tool "$1" > /dev/null 2>&1; }
score_in_range() {
    local file="$1" min="$2" max="$3"
    [ -f "$file" ] || return 1
    local score
    score=$(grep "TOTAL SCORE" "$file" | grep -o '[0-9.]*' | head -1)
    [ -n "$score" ] && python3 -c "exit(0 if $min <= $score <= $max else 1)"
}
score_greater_than() {
    local file_a="$1" file_b="$2"
    [ -f "$file_a" ] && [ -f "$file_b" ] || return 1
    local score_a score_b
    score_a=$(grep "TOTAL SCORE" "$file_a" | grep -o '[0-9.]*' | head -1)
    score_b=$(grep "TOTAL SCORE" "$file_b" | grep -o '[0-9.]*' | head -1)
    [ -n "$score_a" ] && [ -n "$score_b" ] && python3 -c "exit(0 if $score_a > $score_b else 1)"
}
score_greater_or_equal() {
    local file_a="$1" file_b="$2"
    [ -f "$file_a" ] && [ -f "$file_b" ] || return 1
    local score_a score_b
    score_a=$(grep "TOTAL SCORE" "$file_a" | grep -o '[0-9.]*' | head -1)
    score_b=$(grep "TOTAL SCORE" "$file_b" | grep -o '[0-9.]*' | head -1)
    [ -n "$score_a" ] && [ -n "$score_b" ] && python3 -c "exit(0 if $score_a >= $score_b else 1)"
}

echo ""
echo "========================================"
echo "  WORKSHOP VERIFICATION"
echo "  $(date '+%Y-%m-%d %H:%M')"
echo "========================================"

# ─────────────────────────────────────────
echo ""
echo "── 1. Reference Reports ──"
# ─────────────────────────────────────────

check "test-1-quantum.md exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/reference/test-1-quantum.md'"

check "test-2-a2a-mcp.md exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/reference/test-2-a2a-mcp.md'"

check "test-3-metal-ions.md exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/reference/test-3-metal-ions.md'"

check "test-1-quantum.md is substantial (>50KB)" \
    "file_min_bytes '$WORKSHOP_DIR/benchmark/reference/test-1-quantum.md' 50000"

check "test-2-a2a-mcp.md is substantial (>50KB)" \
    "file_min_bytes '$WORKSHOP_DIR/benchmark/reference/test-2-a2a-mcp.md' 50000"

check "test-3-metal-ions.md is substantial (>50KB)" \
    "file_min_bytes '$WORKSHOP_DIR/benchmark/reference/test-3-metal-ions.md' 50000"

# ─────────────────────────────────────────
echo ""
echo "── 2. Evaluator (RACE-aligned) ──"
# ─────────────────────────────────────────

check "evaluate.py exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/evaluate.py'"

check "evaluate.py uses RACE dimensions (comprehensiveness)" \
    "file_contains '$WORKSHOP_DIR/benchmark/evaluate.py' 'comprehensiveness'"

check "evaluate.py uses RACE dimensions (insight)" \
    "file_contains '$WORKSHOP_DIR/benchmark/evaluate.py' '\"insight\"'"

check "evaluate.py uses RACE dimensions (instruction_following)" \
    "file_contains '$WORKSHOP_DIR/benchmark/evaluate.py' 'instruction_following'"

check "evaluate.py uses RACE dimensions (readability)" \
    "file_contains '$WORKSHOP_DIR/benchmark/evaluate.py' 'readability'"

check "evaluate.py has citation bonus" \
    "file_contains '$WORKSHOP_DIR/benchmark/evaluate.py' 'citation_bonus'"

check "evaluate.py has --question flag" \
    "grep -q 'question' '$WORKSHOP_DIR/benchmark/evaluate.py' 2>/dev/null"

check "evaluate.py runs without error (--help)" \
    "python3 '$WORKSHOP_DIR/benchmark/evaluate.py' --help > /dev/null 2>&1"

# ─────────────────────────────────────────
echo ""
echo "── 3. Score Staircase (all 7 steps) ──"
# ─────────────────────────────────────────

check "step-0 output exists and is non-empty" \
    "file_min_bytes '$WORKSHOP_DIR/test-run/outputs/step-0.md' 500"

check "step-1 output exists and is non-empty" \
    "file_min_bytes '$WORKSHOP_DIR/test-run/outputs/step-1.md' 500"

check "step-2 output exists and is non-empty" \
    "file_min_bytes '$WORKSHOP_DIR/test-run/outputs/step-2.md' 500"

check "step-3 output exists and is non-empty" \
    "file_min_bytes '$WORKSHOP_DIR/test-run/outputs/step-3.md' 500"

check "step-4 output exists and is non-empty" \
    "file_min_bytes '$WORKSHOP_DIR/test-run/outputs/step-4.md' 500"

check "step-5 output exists and is non-empty" \
    "file_min_bytes '$WORKSHOP_DIR/test-run/outputs/step-5.md' 500"

check "step-6 output exists and is non-empty" \
    "file_min_bytes '$WORKSHOP_DIR/test-run/outputs/step-6.md' 500"

check "step-0 score exists" \
    "file_exists '$WORKSHOP_DIR/test-run/scores/step-0.txt'"

check "step-1 score exists" \
    "file_exists '$WORKSHOP_DIR/test-run/scores/step-1.txt'"

check "step-2 score exists" \
    "file_exists '$WORKSHOP_DIR/test-run/scores/step-2.txt'"

check "step-3 score exists" \
    "file_exists '$WORKSHOP_DIR/test-run/scores/step-3.txt'"

check "step-4 score exists" \
    "file_exists '$WORKSHOP_DIR/test-run/scores/step-4.txt'"

check "step-5 score exists" \
    "file_exists '$WORKSHOP_DIR/test-run/scores/step-5.txt'"

check "step-6 score exists" \
    "file_exists '$WORKSHOP_DIR/test-run/scores/step-6.txt'"

# Score ranges — wider ranges to accommodate topic variance
# The A2A vs MCP question is partially in training data, so step 0 can score higher
check "step-0 score in range 5-65 (raw baseline)" \
    "score_in_range '$WORKSHOP_DIR/test-run/scores/step-0.txt' 5 65"

check "step-1 score in range 10-70 (context)" \
    "score_in_range '$WORKSHOP_DIR/test-run/scores/step-1.txt' 10 70"

check "step-2 score in range 20-80 (skill)" \
    "score_in_range '$WORKSHOP_DIR/test-run/scores/step-2.txt' 20 80"

check "step-3 score in range 35-85 (tool)" \
    "score_in_range '$WORKSHOP_DIR/test-run/scores/step-3.txt' 35 85"

check "step-4 score in range 50-90 (iterative)" \
    "score_in_range '$WORKSHOP_DIR/test-run/scores/step-4.txt' 50 90"

check "step-5 score in range 55-95 (verification)" \
    "score_in_range '$WORKSHOP_DIR/test-run/scores/step-5.txt' 55 95"

check "step-6 score in range 60-100 (team)" \
    "score_in_range '$WORKSHOP_DIR/test-run/scores/step-6.txt' 60 100"

# Monotonic improvement (each step beats previous)
check "step-1 >= step-0 (context at least matches raw)" \
    "score_greater_or_equal '$WORKSHOP_DIR/test-run/scores/step-1.txt' '$WORKSHOP_DIR/test-run/scores/step-0.txt'"

check "step-2 > step-1 (skill improves on context)" \
    "score_greater_than '$WORKSHOP_DIR/test-run/scores/step-2.txt' '$WORKSHOP_DIR/test-run/scores/step-1.txt'"

check "step-3 > step-2 (tool improves on skill)" \
    "score_greater_than '$WORKSHOP_DIR/test-run/scores/step-3.txt' '$WORKSHOP_DIR/test-run/scores/step-2.txt'"

check "step-4 > step-3 (iteration improves on tool)" \
    "score_greater_than '$WORKSHOP_DIR/test-run/scores/step-4.txt' '$WORKSHOP_DIR/test-run/scores/step-3.txt'"

check "step-5 > step-4 (verification improves on iteration)" \
    "score_greater_than '$WORKSHOP_DIR/test-run/scores/step-5.txt' '$WORKSHOP_DIR/test-run/scores/step-4.txt'"

check "step-6 > step-5 (team improves on verification)" \
    "score_greater_than '$WORKSHOP_DIR/test-run/scores/step-6.txt' '$WORKSHOP_DIR/test-run/scores/step-5.txt'"

# ─────────────────────────────────────────
echo ""
echo "── 4. Teaching Content ──"
# ─────────────────────────────────────────

STEP_DIRS=("step-1-context" "step-2-skill" "step-3-tool" "step-4-iterative" "step-5-verification" "step-6-team")
for i in "${!STEP_DIRS[@]}"; do
    step=$((i + 1))
    dir="${STEP_DIRS[$i]}"
    check "step-$step TEACHING.md exists" \
        "file_exists '$WORKSHOP_DIR/$dir/TEACHING.md'"

    check "step-$step TEACHING.md has design principle section" \
        "grep -qiE 'design principle|WHY|Why this' '$WORKSHOP_DIR/$dir/TEACHING.md' 2>/dev/null"

    check "step-$step TEACHING.md has score impact section" \
        "grep -qiE 'Score impact|Before.*After|What changes' '$WORKSHOP_DIR/$dir/TEACHING.md' 2>/dev/null"
done

# ─────────────────────────────────────────
echo ""
echo "── 5. Demo Script ──"
# ─────────────────────────────────────────

check "DEMO.md exists" \
    "file_exists '$WORKSHOP_DIR/DEMO.md'"

check "DEMO.md has all 6 steps" \
    "file_contains '$WORKSHOP_DIR/DEMO.md' 'Step 6\|step 6\|Team'"

check "DEMO.md has terminal commands" \
    "file_contains '$WORKSHOP_DIR/DEMO.md' 'claude\|python3.*evaluate'"

check "DEMO.md has score expectations" \
    "file_contains '$WORKSHOP_DIR/DEMO.md' 'Score\|score\|→'"

# ─────────────────────────────────────────
echo ""
echo "── 6. Student Build Materials ──"
# ─────────────────────────────────────────

check "BUILD.md exists" \
    "file_exists '$WORKSHOP_DIR/BUILD.md'"

check "BUILD.md has scoring instructions" \
    "file_contains '$WORKSHOP_DIR/BUILD.md' 'evaluate.py\|scoring\|Scoring'"

check "BUILD.md has group/team instructions" \
    "file_contains '$WORKSHOP_DIR/BUILD.md' 'group\|team\|Group\|Team'"

check "BUILD.md has presentation guide" \
    "file_contains '$WORKSHOP_DIR/BUILD.md' 'present\|Present'"

# ─────────────────────────────────────────
echo ""
echo "── 7. Codespace Config ──"
# ─────────────────────────────────────────

check "devcontainer.json exists" \
    "file_exists '$WORKSHOP_DIR/.devcontainer/devcontainer.json'"

check "devcontainer.json is valid JSON" \
    "valid_json '$WORKSHOP_DIR/.devcontainer/devcontainer.json'"

check "devcontainer.json installs Claude Code" \
    "file_contains '$WORKSHOP_DIR/.devcontainer/devcontainer.json' 'claude-code'"

check "devcontainer.json installs Python deps" \
    "file_contains '$WORKSHOP_DIR/.devcontainer/devcontainer.json' 'anthropic\|fastmcp\|pip'"

# ─────────────────────────────────────────
echo ""
echo "── 8. Bench Criteria ──"
# ─────────────────────────────────────────

check "test-1-quantum criteria exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/criteria/test-1-quantum.json'"

check "test-2-a2a-mcp criteria exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/criteria/test-2-a2a-mcp.json'"

check "test-3-metal-ions criteria exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/criteria/test-3-metal-ions.json'"

check "test-1 criteria is valid JSON" \
    "valid_json '$WORKSHOP_DIR/benchmark/criteria/test-1-quantum.json'"

check "test-2 criteria is valid JSON" \
    "valid_json '$WORKSHOP_DIR/benchmark/criteria/test-2-a2a-mcp.json'"

check "test-3 criteria is valid JSON" \
    "valid_json '$WORKSHOP_DIR/benchmark/criteria/test-3-metal-ions.json'"

check "criteria files have RACE dimensions" \
    "file_contains '$WORKSHOP_DIR/benchmark/criteria/test-1-quantum.json' 'comprehensiveness'"

# ─────────────────────────────────────────
echo ""
echo "── 9. Existing Assets (sanity) ──"
# ─────────────────────────────────────────

check "verify.sh exists and is executable" \
    "[ -x '$WORKSHOP_DIR/verify.sh' ]"

check "step-1 README exists" \
    "file_exists '$WORKSHOP_DIR/step-1-context/README.md'"

check "step-1 CLAUDE.md exists" \
    "file_exists '$WORKSHOP_DIR/step-1-context/CLAUDE.md'"

check "step-2 SKILL.md exists" \
    "file_exists '$WORKSHOP_DIR/step-2-skill/.claude/skills/deep-research/SKILL.md'"

check "step-3 arxiv_server.py exists" \
    "file_exists '$WORKSHOP_DIR/step-3-tool/mcp-servers/arxiv_server.py'"

check "step-4 iterative SKILL.md exists" \
    "file_exists '$WORKSHOP_DIR/step-4-iterative/.claude/skills/deep-research/SKILL.md'"

check "step-5 verify SKILL.md exists" \
    "file_exists '$WORKSHOP_DIR/step-5-verification/.claude/skills/verify-research/SKILL.md'"

check "step-6 orchestrator SKILL.md exists" \
    "file_exists '$WORKSHOP_DIR/step-6-team/.claude/skills/orchestrator/SKILL.md'"

check "step-6 searcher SKILL.md exists" \
    "file_exists '$WORKSHOP_DIR/step-6-team/.claude/skills/searcher/SKILL.md'"

check "step-6 critic SKILL.md exists" \
    "file_exists '$WORKSHOP_DIR/step-6-team/.claude/skills/critic/SKILL.md'"

check "step-6 synthesizer SKILL.md exists" \
    "file_exists '$WORKSHOP_DIR/step-6-team/.claude/skills/synthesizer/SKILL.md'"

check "practice-1 problem exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/practice/practice-1.md'"

check "practice-2 problem exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/practice/practice-2.md'"

check "practice-3 problem exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/practice/practice-3.md'"

check "test-1 problem exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/test/test-1.md'"

check "test-2 problem exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/test/test-2.md'"

check "test-3 problem exists" \
    "file_exists '$WORKSHOP_DIR/benchmark/test/test-3.md'"

# ─────────────────────────────────────────
echo ""
echo "========================================"
echo "  RESULTS: $PASS passed, $FAIL failed, $TOTAL total"
echo "========================================"

if [ "$FAIL" -eq 0 ]; then
    echo "  ★ ALL CHECKS PASSED — workshop is ready"
else
    echo "  ✗ $FAIL checks failed — fix before workshop"
fi
echo ""

exit $FAIL
