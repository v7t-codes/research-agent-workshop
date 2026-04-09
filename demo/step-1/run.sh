#!/bin/bash
# Step 1: Context (CLAUDE.md)
# What changes: Claude gets an identity — domain, sources, citation format, constraints.
# What doesn't change: no methodology, no tools, still from training data only.

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/common.sh"

echo "━━━ STEP 1: Context (CLAUDE.md) ━━━"
echo "Files in this folder:"
ls "$(dirname "$0")"
echo ""
echo "Running..."

echo "$Q" | claude $CLAUDE_FLAGS \
  --system-prompt "$(cat CLAUDE.md)" \
  --disallowed-tools "WebSearch,WebFetch,Agent" \
  | tee output.md

score_output output.md "$Q"
