# Build Your Research Agent

## The Challenge

Build a research agent that scores as high as possible on the Deep Research Bench. You have 90 minutes. Work in groups of 2-3.

Your agent will be scored on 3 unseen test problems using the **RACE framework** — the same methodology used to evaluate production deep research systems like Gemini Deep Research, Perplexity, and Claude Research.

## How scoring works

**RACE dimensions:**
| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Comprehensiveness | 30% | Coverage breadth, data support, multiple perspectives |
| Insight | 35% | Analysis depth, causal reasoning, source conflicts |
| Instruction Following | 20% | Addresses every part of the question, stays in scope |
| Readability | 15% | Structure, clarity, logical flow, formatting |
| Citation Bonus | +10% | Verifiable sources with real URLs, arXiv IDs, DOIs |

**Total: 0-100.** Higher is better. Citation bonus is additive.

## Quick start

### 1. Verify setup
```bash
cd research-agent-workshop
./verify.sh
```

### 2. Start with context + skill (steps 1-2)
```bash
# Copy the starter files
cp step-1-context/CLAUDE.md ./CLAUDE.md
mkdir -p .claude/skills/deep-research
cp step-2-skill/.claude/skills/deep-research/SKILL.md .claude/skills/deep-research/

# Open Claude Code
claude

# Edit your CLAUDE.md for your group's domain expertise
# Then run on a practice problem:
# "Research: Compare the three main approaches to neural architecture search..."

# Score it:
python3 benchmark/evaluate.py --input output.md --quick --question "your question here"
```

### 3. Add tools (step 3)
```bash
# Copy the MCP server
cp -r step-3-tool/mcp-servers ./mcp-servers

# Update your SKILL.md to allow tools
cp step-3-tool/.claude/skills/deep-research/SKILL.md .claude/skills/deep-research/

# Connect the MCP server — add to .claude/settings.json:
# "mcpServers": { "research-tools": { "command": "python3", "args": ["mcp-servers/arxiv_server.py"] } }
```

### 4. Make it iterate (step 4)
```bash
# Replace SKILL.md with the iterative version
cp step-4-iterative/.claude/skills/deep-research/SKILL.md .claude/skills/deep-research/
```

### 5. Add verification (step 5)
```bash
# Add the verification agent skill
mkdir -p .claude/skills/verify-research
cp step-5-verification/.claude/skills/deep-research/SKILL.md .claude/skills/deep-research/
cp step-5-verification/.claude/skills/verify-research/SKILL.md .claude/skills/verify-research/
```

### 6. Build a team (step 6)
```bash
# Add orchestrator + specialist skills
mkdir -p .claude/skills/{orchestrator,searcher,critic,synthesizer}
cp step-6-team/.claude/skills/orchestrator/SKILL.md .claude/skills/orchestrator/
cp step-6-team/.claude/skills/searcher/SKILL.md .claude/skills/searcher/
cp step-6-team/.claude/skills/critic/SKILL.md .claude/skills/critic/
cp step-6-team/.claude/skills/synthesizer/SKILL.md .claude/skills/synthesizer/
```

### 7. Innovate (this is where you beat other teams)

The steps above are the baseline. Top teams will:
- **Design a better team structure** — add a "devil's advocate" agent, a "methodology specialist", or run searchers in parallel
- **Build a different MCP server** — PubMed, DBLP, PapersWithCode, Google Scholar
- **Write a custom verification tool** — DOI checker, abstract similarity comparison
- **Optimize iteration strategy** — breadth-first vs. depth-first, convergence detection
- **Customize for the problem domain** — different skills for different types of questions

## Scoring your agent

```bash
# Quick score (instant, no API call) — use this while iterating
python3 benchmark/evaluate.py --input output.md --quick --question "your question"

# Full score (LLM-as-judge, uses API) — use for final scoring
python3 benchmark/evaluate.py --input output.md --question "your question"

# With reference report (calibrated scoring)
python3 benchmark/evaluate.py --input output.md --reference benchmark/reference/test-2-a2a-mcp.md
```

## Practice problems

Use these to build and iterate (in `benchmark/practice/`):
1. **NAS comparison** — warmup, well-covered in training data
2. **Q1 2026 foundation models** — forces tools + iteration (training data can't answer)
3. **MoE scaling laws** — forces verification + team (conflicting results, easy to hallucinate)

## Test problems (scored for competition)

When your group is ready, run on the 3 unseen test problems (in `benchmark/test/`). Your **average score across all 3** is your competition score.

```bash
# Run on each test problem, save outputs, score them
python3 benchmark/evaluate.py --input test-1-output.md --quick --question "$(head -5 benchmark/test/test-1.md | tail -1)"
python3 benchmark/evaluate.py --input test-2-output.md --quick --question "$(head -5 benchmark/test/test-2.md | tail -1)"
python3 benchmark/evaluate.py --input test-3-output.md --quick --question "$(head -5 benchmark/test/test-3.md | tail -1)"
```

## Presenting (top 3 teams)

Top 3 teams by average test score present for 2-3 minutes each. Cover:

1. **Score progression** — show how your score climbed as you added each step. Where was the biggest jump?
2. **Design choices** — what MCP server did you build? How did you design iteration? What team structure?
3. **One surprise** — something that worked unexpectedly well, or failed unexpectedly

The audience votes for "best design" (separate from best score).
