# Step 6: Team of Agents — Design Principles

## What it physically is

Multiple agents (each a separate Claude subprocess via the `Agent` tool), each with their own skill and context window, coordinated by an **orchestrator** skill running in your session.

```
Your session (orchestrator skill)
├── dispatches → Searcher agent (own context, own tools)
│                  └── saves searcher_output.md
├── dispatches → Critic agent (own context, own tools)
│                  └── reads searcher_output.md → saves critic_output.md
└── dispatches → Synthesizer agent (own context, own tools)
                   └── reads both files → saves final_report.md
```

## The design principle: Specialization beats generalization

Each agent focuses deeply on one thing. The searcher doesn't worry about critique. The critic doesn't worry about finding papers. The synthesizer doesn't worry about either — it just writes.

**Why this works:** Anthropic's engineering blog found that multi-agent (Opus lead + Sonnet subagents) outperformed single-agent by 90.2%. The reason: when a single agent does everything, it distributes attention across search, evaluation, and writing. When agents specialize, each uses its full context window for ONE task.

## How to orchestrate a team

### The orchestrator pattern

The orchestrator is a SKILL.md that runs in your session. It doesn't do research — it dispatches and coordinates:

```markdown
# Orchestrator Skill

## Phase 1: Dispatch Searcher
Use the Agent tool to spawn the searcher with:
- The research question
- The searcher's skill instructions
- Access to: arXiv MCP, Semantic Scholar MCP, WebSearch
- Task: "Find papers, extract metadata, save to searcher_output.md"

## Phase 2: Dispatch Critic
Use the Agent tool to spawn the critic with:
- The searcher's output (read from searcher_output.md)
- The critic's skill instructions
- Access to: WebSearch, WebFetch
- Task: "Evaluate evidence quality, save to critic_output.md"

## Phase 3: Dispatch Synthesizer
Use the Agent tool to spawn the synthesizer with:
- Both previous outputs
- The synthesizer's skill instructions
- Access to: Write
- Task: "Produce final report, save to final_report.md"

## Phase 4: Review
Read final_report.md. Check completeness. Done.
```

### File-based communication

Agents communicate through **files**, not shared memory. This is intentional:
- Searcher writes `searcher_output.md` → critic reads it
- Critic writes `critic_output.md` → synthesizer reads it
- Each agent gets a clean context with only the information it needs

This prevents context pollution. The critic doesn't see the searcher's reasoning — only its output.

## Designing team roles

### The three-role pattern (default)

| Role | Job | Tools | Input | Output |
|------|-----|-------|-------|--------|
| **Searcher** | Find papers, extract claims | arXiv, Semantic Scholar, WebSearch | Research question | `searcher_output.md` |
| **Critic** | Evaluate evidence, find conflicts | WebSearch, WebFetch | Searcher's findings | `critic_output.md` |
| **Synthesizer** | Write the final report | Read, Write | Both files | `final_report.md` |

### Advanced patterns (for top scorers)

**Parallel searchers:** Instead of one searcher, dispatch one per sub-question. They run concurrently, each specializing in one aspect.

**Devil's advocate:** Add an agent whose ONLY job is to find contradictory evidence. "For each claim in the report, search for papers that disagree."

**Methodology specialist:** An agent that evaluates study designs. "For each cited paper, assess: sample size, methodology rigor, potential biases."

**Editor:** A final agent that polishes the synthesizer's output for readability and formatting.

## How to call multiple skills together

The orchestrator skill references the other skills by giving their content to each agent:

```markdown
## Phase 1: Dispatch Searcher
Use the Agent tool. In your prompt to the agent, include:
1. The research question
2. The full text of the SEARCHER SKILL (from step-6-team/.claude/skills/searcher/SKILL.md)
3. "Follow the searcher skill instructions. Save output to searcher_output.md."
```

Each agent receives its skill as part of the dispatch prompt. The orchestrator reads all skill files and passes the right one to each agent.

## Where creativity matters

The team structure above is a **starting point**. The top scorers in the workshop will be teams that design a better team. Questions to consider:

1. **Should the critic see the searcher's reasoning, or just its outputs?** (File-based communication = outputs only. Shared context = everything.)
2. **Should agents run sequentially or in parallel?** (Sequential: critic can only evaluate what searcher found. Parallel: faster but no cross-referencing.)
3. **What happens when the critic flags a problem?** (Drop the claim? Ask the searcher to re-search? Have the synthesizer note the uncertainty?)
4. **Does every question need the same team?** (A comparison question might need a different structure than a survey question.)

## Score impact

| | Before (step 5) | After (step 6) |
|--|--|--|
| **What changes** | Good coverage, verified citations. But critique is limited to "does this exist?" | Deep evidence quality assessment. Real methodology critique. Genuine conflict analysis. Better writing quality. |
| **What doesn't change** | The underlying data sources are the same. | Same tools, same APIs — but used by specialized agents who do each task better. |

Everything compounds. The searcher finds more papers because search is its ONLY job. The critic catches more issues because evaluation is its ONLY job. The synthesizer writes better because it can focus entirely on structure and clarity.

This is why the final score jumps — not because of one improvement, but because specialization improves EVERY dimension simultaneously.
