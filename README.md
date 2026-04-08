# Build Your Research Agent — IISc Workshop

> Presenters: Rachitt Shah + Vishwajit | Wednesday 4–7 PM | ~50 students

Build a compound research agent step by step. Watch your benchmark score climb with each concept you add. Same model. Six engineering concepts. **20 → 93.**

## The Thesis

Same model, different harness, dramatically different results. Opus 4.5 raw: 30.5% on OSWorld. With a harness: 66.3%. **The system around the model matters more than the model itself.**

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

## The Six Concepts

| Step | Concept | What it physically is | Key property |
|------|---------|----------------------|-------------|
| 0 | Baseline | Raw Claude, no files | — |
| 1 | Context | `CLAUDE.md` file on disk | Identity — who Claude works for |
| 2 | Skill | `SKILL.md` file on disk | Methodology — HOW to do the work, one pass |
| 3 | Custom Tool | Python MCP server (separate process) | Capability — new actions Claude can take |
| 4 | Iterative Skill | `SKILL.md` with loop logic | Autonomy — Claude decides when to loop |
| 5 | Verification Agent | Separate Claude subprocess (Agent tool) | Independence — own context window, fresh eyes |
| 6 | Team of Agents | Multiple Agent calls + orchestrator | Specialization — each does one thing well |

## Key Boundaries

- **Skill vs Iterative Skill:** Both run in your session. The iterative skill has decision logic ("if coverage insufficient, search again").
- **Iterative Skill vs Agent:** The hard boundary. An agent is a **separate Claude instance** with its own context window. A different process.
- **Agent vs Team:** One agent is one subprocess. A team is multiple subprocesses, each specialized.

## Setup

```bash
# 1. Install Claude Code
npm install -g @anthropic-ai/claude-code

# 2. Set API key
export ANTHROPIC_API_KEY="your-key-here"

# 3. Install Python deps
pip install -r requirements.txt

# 4. Verify
./verify.sh
```

## Workshop Structure

### First half: Demo + teach (see [DEMO.md](DEMO.md))
Watch each step demonstrated live. Learn the design principles behind each concept.

### Second half: Build + compete (see [BUILD.md](BUILD.md))
Break into groups. Build your own research agent. Score against the benchmark. Top teams present.

## Each Step

Each step folder contains:
- **README.md** — what it is, what to do, what changes
- **TEACHING.md** — design principles (WHY), how to build it (HOW), score impact
- **The actual files** — CLAUDE.md, SKILL.md, MCP server, etc.

## Evaluation

```bash
# Quick score (heuristic, instant, no API call)
python3 benchmark/evaluate.py --input output.md --quick --question "your research question"

# Full score (LLM-as-judge, RACE framework)
python3 benchmark/evaluate.py --input output.md --question "your research question"

# With reference report (calibrated)
python3 benchmark/evaluate.py --input output.md --reference benchmark/reference/test-2-a2a-mcp.md

# Verify scoring staircase
python3 benchmark/verify_staircase.py
```

## Benchmark

Evaluation uses the **RACE framework** from Deep Research Bench:
- Comprehensiveness (30%) — coverage breadth, data support, multiple perspectives
- Insight (35%) — analysis depth, causal reasoning, source conflicts
- Instruction Following (20%) — addresses all parts of the question
- Readability (15%) — structure, clarity, logical flow
- Citation Bonus (+10%) — verifiable sources with real URLs/papers

For advanced teams: run against the full [DeepResearch-Bench](https://github.com/Ayanamo0730/deep_research_bench) (100 PhD-level tasks) using the adapter in `benchmark/deepresearch-bench/`.

## Documentation

Detailed KT docs in [`docs/`](docs/):

| Doc | What It Covers |
|-----|---------------|
| [Architecture](docs/architecture.md) | How the 6-step system works — abstraction hierarchy, data flow, MCP, agent dispatch, team orchestration, building your own MCP server |
| [Demo Guide](docs/demo-guide.md) | Presenter script — exact commands, talking points, scores, fallbacks |
| [Benchmarking](docs/benchmarking.md) | RACE framework, heuristic vs LLM scoring, DeepResearch-Bench integration |
| [Self-Improvement](docs/self-improvement.md) | Optimization loop, eval-driven development, self-improving loops, competition strategy |
| [Troubleshooting](docs/troubleshooting.md) | Setup issues, demo failures, common mistakes |

## References

- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [rachittshah/deep-research](https://github.com/rachittshah/deep-research) — Production research plugin (4.56/5.00 on DeepResearch-Bench)
- [Anthropic Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)
