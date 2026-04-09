#!/bin/bash
# Workshop setup verification
# Run this before the session to confirm everything works.
#
# PRESENTERS: You need ANTHROPIC_API_KEY (for demo commands + final scoring)
# STUDENTS:   You need a claude.ai account (run `claude auth login`)

echo "=== Research Agent Workshop — Setup Verification ==="
echo ""

PASS=0
FAIL=0
WARN=0

# ── Claude Code ──
if command -v claude &> /dev/null; then
    echo "✓ Claude Code installed ($(claude --version 2>/dev/null | head -1))"
    PASS=$((PASS + 1))
else
    echo "✗ Claude Code not found"
    echo "  Install: npm install -g @anthropic-ai/claude-code"
    FAIL=$((FAIL + 1))
fi

# ── Auth check ──
# Claude Code uses OAuth (claude.ai login) for interactive use.
# ANTHROPIC_API_KEY is needed for demo commands (claude -p) and evaluate.py LLM mode.
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo "✓ ANTHROPIC_API_KEY is set  (presenter mode — demo commands + LLM scoring work)"
    PASS=$((PASS + 1))
else
    # Check if logged in via OAuth instead
    if claude auth status &>/dev/null 2>&1; then
        echo "✓ Claude Code logged in via claude.ai  (student mode — interactive build works)"
        echo "  Note: set ANTHROPIC_API_KEY for demo commands and LLM scoring"
        PASS=$((PASS + 1))
    else
        echo "✗ Not authenticated"
        echo "  Presenters: export ANTHROPIC_API_KEY=sk-ant-..."
        echo "  Students:   claude auth login"
        FAIL=$((FAIL + 1))
    fi
fi

# ── Python ──
if command -v python3 &> /dev/null; then
    echo "✓ Python3 installed ($(python3 --version 2>/dev/null))"
    PASS=$((PASS + 1))
else
    echo "✗ Python3 not found"
    FAIL=$((FAIL + 1))
fi

# ── fastmcp (required — MCP server won't run without it) ──
if python3 -c "import fastmcp" 2>/dev/null; then
    echo "✓ fastmcp installed"
    PASS=$((PASS + 1))
else
    echo "✗ fastmcp not found"
    echo "  Install: pip install fastmcp"
    FAIL=$((FAIL + 1))
fi

# ── anthropic (required for LLM scoring, optional for heuristic) ──
if python3 -c "import anthropic" 2>/dev/null; then
    echo "✓ anthropic Python package installed"
    PASS=$((PASS + 1))
else
    echo "⚠ anthropic package not found  (--quick scoring still works; LLM scoring won't)"
    echo "  Install: pip install anthropic"
    WARN=$((WARN + 1))
fi

# ── MCP server starts ──
if python3 -c "import fastmcp" 2>/dev/null; then
    timeout 5 python3 step-3-tool/mcp-servers/arxiv_server.py &
    MCP_PID=$!
    sleep 1
    if kill -0 $MCP_PID 2>/dev/null; then
        echo "✓ arXiv MCP server starts cleanly"
        kill $MCP_PID 2>/dev/null
        PASS=$((PASS + 1))
    else
        echo "✗ arXiv MCP server failed to start"
        FAIL=$((FAIL + 1))
    fi
fi

# ── Evaluator works ──
if python3 benchmark/evaluate.py --help &>/dev/null; then
    echo "✓ evaluate.py runs"
    PASS=$((PASS + 1))
else
    echo "✗ evaluate.py failed"
    FAIL=$((FAIL + 1))
fi

# ── Pre-computed fallbacks exist ──
missing=0
for i in 0 1 2 3 4 5 6; do
    if [ ! -s "test-run/outputs/step-$i.md" ]; then
        missing=$((missing + 1))
    fi
done
if [ $missing -eq 0 ]; then
    echo "✓ Pre-computed demo fallbacks ready (test-run/outputs/)"
    PASS=$((PASS + 1))
else
    echo "⚠ $missing pre-computed fallback(s) missing in test-run/outputs/"
    WARN=$((WARN + 1))
fi

# ── Git ──
if command -v git &> /dev/null; then
    echo "✓ Git installed"
    PASS=$((PASS + 1))
else
    echo "✗ Git not found"
    FAIL=$((FAIL + 1))
fi

# ── Node.js ──
if command -v node &> /dev/null; then
    echo "✓ Node.js installed ($(node --version))"
    PASS=$((PASS + 1))
else
    echo "✗ Node.js not found"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed, $WARN warnings ==="

if [ $FAIL -eq 0 ]; then
    echo "✓ Ready for the workshop."
    exit 0
else
    echo "✗ Fix the failures above before the workshop."
    exit 1
fi
