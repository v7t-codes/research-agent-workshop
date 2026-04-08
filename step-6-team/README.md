# Step 6: Team of Agents (Multiple Specialized Processes)

## What you're adding
Three specialized agents coordinated by an orchestrator. Each agent is a separate Claude instance (via the Agent tool), each with its own skill, tools, and context window.

## The team
- **Searcher agent** — finds papers, extracts metadata and claims. Has arXiv + Semantic Scholar MCP tools.
- **Critic agent** — evaluates evidence quality, finds conflicts, flags weak methodology. Has WebSearch for verification.
- **Synthesizer agent** — produces the final report from searcher's findings and critic's assessment. Only has Read + Write.
- **Orchestrator** — your main session. Dispatches agents in sequence, passes outputs between them.

## What it is — multiple separate processes
In step 5, you had one subagent (verification). Now you have three. Each is a SEPARATE Claude instance:

```
Your session (orchestrator)
├── dispatches → Searcher agent (own context window, own tools)
│                  └── saves searcher_output.md
├── dispatches → Critic agent (own context window, own tools)  
│                  └── reads searcher_output.md, saves critic_output.md
└── dispatches → Synthesizer agent (own context window, own tools)
                   └── reads both files, saves final_report.md
```

The agents communicate through FILES, not shared memory. Searcher writes findings, critic reads them. This is intentional — each agent gets fresh eyes.

## Why specialization works
The Anthropic engineering blog found that multi-agent (Opus lead + Sonnet subagents) outperformed single-agent by 90.2%. The reason: each agent can focus deeply on one thing. The searcher doesn't waste context on critique. The critic doesn't waste context on searching. Specialization → better performance on every dimension.

## The four skills
- `orchestrator/SKILL.md` — coordinates the pipeline (runs in your session)
- `searcher/SKILL.md` — defines the searcher's behavior (runs in searcher agent)
- `critic/SKILL.md` — defines the critic's behavior (runs in critic agent)
- `synthesizer/SKILL.md` — defines the synthesizer's behavior (runs in synthesizer agent)

## What changes
- Evidence quality assessment: the critic catches weak methodology and unfair benchmark comparisons
- Conflict analysis: real disagreements surfaced, not glossed over
- No hallucinated sources in the final report: critic catches them, synthesizer excludes them
- Better structure: synthesizer focuses entirely on writing quality

## What to do
1. Copy everything from steps 1-5
2. Replace your research skill with the orchestrator skill
3. Add searcher, critic, and synthesizer skills
4. Run: `/deep-research [practice problem 3]`
5. Watch three agents spawn in sequence
6. Evaluate: `python benchmark/evaluate.py --input final_report.md`

## What you'll see
Score jumps from ~85 to ~93. Everything compounds. This is a compound AI system.

## Where your creativity matters
The team structure above is a STARTING POINT. You can:
- Add a "devil's advocate" agent that actively looks for contradictory evidence
- Add a "methodology specialist" that only evaluates study designs
- Run searcher agents in PARALLEL (one per sub-question) instead of one sequential searcher
- Add a final "editor" agent that polishes the synthesizer's output
- Change what tools each agent gets access to

The top scorers will be the ones who design the best team structure.
