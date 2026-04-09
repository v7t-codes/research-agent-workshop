# Knowledge Transfer: Research Agent Workshop

Documentation for the IISc "Build Your Research Agent" workshop. Everything you need to understand, demo, score, and improve the system.

## Documents

| Doc | What It Covers | Read When |
|-----|---------------|-----------|
| [Architecture](architecture.md) | How the 6-step system works — abstraction hierarchy, data flow, MCP server, agent dispatch, team orchestration | Understanding the system |
| [Demo Guide](demo-guide.md) | Step-by-step demo instructions — exact commands, talking points, scores, fallbacks, competition logistics | Preparing to present |
| [Benchmarking](benchmarking.md) | RACE framework, heuristic vs LLM scoring, evaluation commands, DeepResearch-Bench integration | Scoring and evaluation |
| [Self-Improvement](self-improvement.md) | Optimization loop, diagnosing low scores by dimension, optimizing each component, competition strategy | Building a better agent |
| [Troubleshooting](troubleshooting.md) | Setup issues, demo failures, student issues, scoring problems, common mistakes | When things break |

## Quick Reference

```bash
# Verify setup
./verify.sh

# Score a report (instant)
python benchmark/evaluate.py --input output.md --quick --question "..."

# Score with LLM judge (1-2 min, needs API key)
python benchmark/evaluate.py --input output.md --question "..."

# Verify staircase
python benchmark/verify_staircase.py

# Run against DeepResearch-Bench (optional, advanced)
bash benchmark/deepresearch-bench/adapter.sh --bench-dir /tmp/deep_research_bench --step 6 --max 3
```

## The Score Staircase

```
Step 0 (raw):           20/100  ─┐
Step 1 (context):       21/100   ├─ No tools (training data only)
Step 2 (skill):         37/100  ─┘
Step 3 (tool):          58/100  ─┐
Step 4 (iterative):     53/100  ─┤  Tools (real external sources)
                                 ─┘
Step 5 (verification):  90/100  ─┐
Step 6 (team):          93/100  ─┘  Verification + Team
```

Three clear tiers. +21 points when tools are added. +37 when verification/team is added.

## Workshop Timeline

| Time | Who | Phase |
|------|-----|-------|
| 4:00-4:50 | Rachitt (hook, 4-6) + Vishwajit (1-3) | Demo: teach 6 concepts |
| 4:50-5:00 | Both | Staircase reveal + BUILD.md handoff |
| 5:00-6:15 | Both circulate | Build phase (students work in teams) |
| 6:15-6:30 | Both | Scoring on test problems |
| 6:30-6:45 | Students | Top 3 present |
| 6:45-7:00 | Both | Wrap-up + Q&A |
