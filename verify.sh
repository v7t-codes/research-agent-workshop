#!/bin/bash
# Workshop setup verification
# Run this before the session to confirm everything works.
#
# PRESENTERS: You need ANTHROPIC_API_KEY (for demo commands + final scoring)
# STUDENTS:   You need a claude.ai account (run `claude auth login`)

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

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
# Detect auth mode and write to .workshop_env so all run.sh scripts inherit it.
# --bare requires ANTHROPIC_API_KEY; plain -p works with OAuth.
WORKSHOP_ENV="$REPO_ROOT/.workshop_env"
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo "✓ ANTHROPIC_API_KEY is set  (API key mode — demo commands + LLM scoring work)"
    echo 'CLAUDE_AUTH_MODE=apikey' > "$WORKSHOP_ENV"
    PASS=$((PASS + 1))
elif claude auth status &>/dev/null 2>&1; then
    echo "✓ Claude Code logged in via claude.ai  (OAuth mode — all commands work)"
    echo 'CLAUDE_AUTH_MODE=oauth' > "$WORKSHOP_ENV"
    PASS=$((PASS + 1))
else
    echo "✗ Not authenticated"
    echo "  Option 1: claude auth login  (recommended)"
    echo "  Option 2: export ANTHROPIC_API_KEY=sk-ant-..."
    rm -f "$WORKSHOP_ENV"
    FAIL=$((FAIL + 1))
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
# Find the arxiv_server.py (could be in demo/step-3/ or step-3-tool/)
ARXIV_SERVER=""
for candidate in demo/step-3/arxiv_server.py step-3-tool/mcp-servers/arxiv_server.py; do
    [ -f "$candidate" ] && ARXIV_SERVER="$candidate" && break
done
if [ -n "$ARXIV_SERVER" ] && python3 -c "import fastmcp" 2>/dev/null; then
    # MCP servers use stdio transport — they start, print banner, then wait for
    # a JSON-RPC client. Without a client they exit immediately. We verify the
    # server imports and initializes without errors by checking stderr for the
    # FastMCP startup banner or "Starting MCP server".
    MCP_OUT=$(python3 "$ARXIV_SERVER" 2>&1 &
    MCP_PID=$!; sleep 2; kill $MCP_PID 2>/dev/null; wait $MCP_PID 2>/dev/null)
    if echo "$MCP_OUT" | grep -qi "MCP server\|FastMCP\|research-tools"; then
        echo "✓ arXiv MCP server starts cleanly ($ARXIV_SERVER)"
        PASS=$((PASS + 1))
    else
        echo "✗ arXiv MCP server failed to start ($ARXIV_SERVER)"
        FAIL=$((FAIL + 1))
    fi
elif [ -z "$ARXIV_SERVER" ]; then
    echo "⚠ arXiv MCP server not found (expected demo/step-3/arxiv_server.py)"
    WARN=$((WARN + 1))
fi

# ── Evaluator works ──
# evaluate.py lives in presenter/ (gitignored) for presenters,
# or benchmark/ if running from the dev branch
EVALUATOR=""
for candidate in presenter/evaluate.py benchmark/evaluate.py; do
    [ -f "$candidate" ] && EVALUATOR="$candidate" && break
done
if [ -n "$EVALUATOR" ] && python3 "$EVALUATOR" --help &>/dev/null; then
    echo "✓ evaluate.py runs ($EVALUATOR)"
    PASS=$((PASS + 1))
else
    echo "⚠ evaluate.py not found (presenters: place in presenter/evaluate.py)"
    echo "  Students: this is expected — presenters score your submissions"
    WARN=$((WARN + 1))
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
