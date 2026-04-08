#!/bin/bash
echo "=== Research Agent Workshop — Setup Verification ==="
echo ""

PASS=0
FAIL=0

# Check Claude Code
if command -v claude &> /dev/null; then
    echo "✓ Claude Code installed ($(claude --version 2>/dev/null || echo 'version unknown'))"
    PASS=$((PASS + 1))
else
    echo "✗ Claude Code not found. Run: npm install -g @anthropic-ai/claude-code"
    FAIL=$((FAIL + 1))
fi

# Check API key
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✓ ANTHROPIC_API_KEY is set"
    PASS=$((PASS + 1))
else
    echo "✗ ANTHROPIC_API_KEY not set. Get one at console.anthropic.com"
    FAIL=$((FAIL + 1))
fi

# Check Python
if command -v python3 &> /dev/null; then
    echo "✓ Python3 installed ($(python3 --version 2>/dev/null))"
    PASS=$((PASS + 1))
else
    echo "✗ Python3 not found"
    FAIL=$((FAIL + 1))
fi

# Check anthropic package
if python3 -c "import anthropic" 2>/dev/null; then
    echo "✓ anthropic Python package installed"
    PASS=$((PASS + 1))
else
    echo "✗ anthropic package not found. Run: pip install anthropic"
    FAIL=$((FAIL + 1))
fi

# Check fastmcp package
if python3 -c "import fastmcp" 2>/dev/null; then
    echo "✓ fastmcp Python package installed"
    PASS=$((PASS + 1))
else
    echo "✗ fastmcp package not found. Run: pip install fastmcp"
    FAIL=$((FAIL + 1))
fi

# Check git
if command -v git &> /dev/null; then
    echo "✓ Git installed"
    PASS=$((PASS + 1))
else
    echo "✗ Git not found"
    FAIL=$((FAIL + 1))
fi

# Check Node.js
if command -v node &> /dev/null; then
    echo "✓ Node.js installed ($(node --version))"
    PASS=$((PASS + 1))
else
    echo "✗ Node.js not found"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ $FAIL -eq 0 ]; then
    echo "✓ All checks passed. You're ready for the workshop!"
    exit 0
else
    echo "✗ Fix the issues above before the workshop."
    exit 1
fi
