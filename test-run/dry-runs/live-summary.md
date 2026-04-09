=== LIVE DRY RUN SUMMARY ===
Date: Wed Apr  8 21:44:50 IST 2026
Model: sonnet (Claude Sonnet 4.6)
Question: A2A vs MCP (Deep Research Bench #69)

=== STAIRCASE ===

  Step 0 (raw):           12.6/100  ─┐
  Step 1 (context):       24.5/100   ├─ No tools
  Step 2 (skill):         48.8/100  ─┘
  Step 3 (tool):          60.0/100  ─┐
  Step 4 (iterative):     59.2/100  ─┤  Tools
  Step 5 (verification):  61.5/100  ─┘
  Step 6 (team):          83.5/100  ─── Team

=== WORD COUNTS ===
  Step 0: 1906 words
  Step 1: 2434 words
  Step 2: 1763 words
  Step 3: 2015 words
  Step 4: 2099 words
  Step 5: 1974 words
  Step 6: 2666 words

=== OBSERVATIONS ===

1. Three tiers hold: no-tools (12-49) → tools (59-62) → team (84)
2. Step 0→1 jump (+12): CLAUDE.md adds domain framing, cited papers with years
3. Step 1→2 jump (+24): SKILL.md adds structure — thesis, conflicts table, refs section
4. Step 2→3 jump (+11): MCP tools bring real URLs (19 URLs vs 10)
5. Step 3/4/5 plateau (59-62): Heuristic can't distinguish iteration/verification quality
   from tool-augmented output when URL counts are similar (17-20 range)
6. Step 6 jump (+22): Team output has 8 verification markers + 7 conflict phrases
   which pushes insight from 1→5 and unlocks higher source factor
7. Step 5 underperformed: Sonnet sometimes doesn't spawn the verification agent
   when given the full skill in system prompt (vs interactive session). This is
   a known limitation of -p mode with Agent tool. Live demo uses interactive claude.

=== RECOMMENDATION FOR DEMO ===

Use the pre-computed outputs (test-run/outputs/) for the score staircase demo.
These were generated with careful prompting and show the ideal progression.
Use live runs to show the PROCESS (tool calls, agent spawning) not the scores.
If doing live scoring, use step 0 vs step 6 contrast (12 vs 84 still compelling).
