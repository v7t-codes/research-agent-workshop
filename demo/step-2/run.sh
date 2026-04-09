#!/bin/bash
# Step 2: Skill (SKILL.md)
# What changes: Claude now has a research methodology — decompose first, structured output format.
# What doesn't change: still no real-time sources, still from training data.

set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/common.sh"

echo "━━━ STEP 2: Skill (SKILL.md) ━━━"
echo "Files in this folder:"
ls "$(dirname "$0")"
echo ""
echo "Running..."

echo "$Q" | claude $CLAUDE_FLAGS \
  --system-prompt "$(cat CLAUDE.md)

---
SKILL INSTRUCTIONS (follow this methodology):
$(cat SKILL.md)" \
  --disallowed-tools "WebSearch,WebFetch,Agent" \
  | tee output.md

score_output output.md "$Q"
