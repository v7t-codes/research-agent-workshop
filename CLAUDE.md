# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Educational workshop teaching compound AI research agents through 6 incremental steps. Core thesis: the system around the model matters more than the model itself (same Opus 4.5 goes from 30.5% to 66.3% on OSWorld with a proper harness).

Each step adds one concept and measures improvement via the RACE benchmark.

## Commands

```bash
# Verify workshop setup (checks CLI, API key, Python, packages)
./verify.sh

# Run benchmark evaluation
python benchmark/evaluate.py --input output.md --quick          # Heuristic (instant, no API)
python benchmark/evaluate.py --input output.md                  # LLM-as-judge (Claude Sonnet)
python benchmark/evaluate.py --input output.md --reference benchmark/reference/test-1.md  # With calibration

# Run MCP server
python step-3-tool/mcp-servers/arxiv_server.py

# Verify scoring staircase works
python benchmark/verify_staircase.py                              # Heuristic check
python benchmark/verify_staircase.py --llm                        # Include LLM scoring (2 API calls)

# Run all steps end-to-end
bash test-run/run_steps.sh
```

## Architecture

### Step Progression (each builds on previous)

| Step | Concept | What Changes | Heuristic | LLM Target |
|------|---------|-------------|-----------|------------|
| 0 | Raw Claude | No context, no skill | ~20 | ~18 |
| 1 | Context (CLAUDE.md) | Static identity — WHO Claude works for | ~21 | ~25 |
| 2 | Skill (SKILL.md) | Methodology — HOW to research, one pass | ~37 | ~38 |
| 3 | Custom Tool (MCP) | arXiv + Semantic Scholar structured search | ~58 | ~55 |
| 4 | Iterative Skill | Evaluate coverage, loop up to 3 rounds | ~53 | ~72 |
| 5 | Verification Agent | Separate Claude subprocess audits for hallucinations | ~90 | ~85 |
| 6 | Team of Agents | Searcher → Critic → Synthesizer pipeline | ~93 | ~93 |

Heuristic (`--quick`) gives instant feedback during development. LLM scoring (no flag) is authoritative for final evaluation. The heuristic applies a source grounding factor: outputs without real URLs (steps 0-2) are penalized; outputs with evidence quality ratings (step 6) are boosted.

### Critical Boundaries

- **CLAUDE.md = WHO, SKILL.md = HOW.** Never mix identity and methodology.
- **Skill vs Agent:** Skill runs in your session (same context window). Agent is a separate Claude process via the `Agent` tool with its own context.
- **Step 4 vs 5:** Step 4 loops in one session. Step 5 spawns a subprocess.

### Skill File Convention

Skills live at `.claude/skills/<name>/SKILL.md` with YAML frontmatter declaring `allowed-tools`. Each step directory has its own `.claude/skills/` tree showing that step's configuration.

### Team Architecture (Step 6)

```
Orchestrator (your session)
├── Searcher agent  → writes searcher_output.md  (tools: arXiv, Semantic Scholar)
├── Critic agent    → writes critic_output.md    (tools: WebSearch, verification)
└── Synthesizer     → writes final_report.md     (tools: Read, Write only)
```

Agents communicate through files. Each gets fresh context — no bleed between stages.

### MCP Server

`step-3-tool/mcp-servers/arxiv_server.py` — FastMCP server with two tools:
- `search_arxiv(query, max_results)` — arXiv API, returns structured paper metadata
- `search_semantic_scholar(query, max_results)` — citation-aware search

### Benchmark (RACE Framework)

`benchmark/evaluate.py` scores on weighted dimensions:
- Comprehensiveness 30% · Insight 35% · Instruction Following 20% · Readability 15% · Citation Bonus +10%

Practice problems in `benchmark/practice/`, test problems in `benchmark/test/`, reference reports in `benchmark/reference/`, rubrics in `benchmark/criteria/`.

### DeepResearch-Bench Integration

`benchmark/deepresearch-bench/` contains an adapter to run workshop agents against the [full 100-task PhD-level bench](https://github.com/Ayanamo0730/deep_research_bench). The adapter takes a workshop step (2-6), builds the appropriate system prompt and tool config, runs against bench tasks, and outputs JSONL for RACE/FACT evaluation. See `benchmark/deepresearch-bench/README.md` for usage.

## Dependencies

Python 3.11+, `anthropic`, `fastmcp`, Node.js 20+, Claude Code CLI.
