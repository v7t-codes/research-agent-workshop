# Practice Problem 2: Forces Tools + Iteration (Steps 3-4)

## Question

What new foundation models were released in Q1 2026? For each model, provide: the organization that released it, the model size and architecture, key benchmark results compared to predecessors, and any novel training techniques. Identify which release had the most significant impact and why.

## Why this problem

Claude's training data CANNOT fully answer this. Q1 2026 models are too recent. Without custom tools (arXiv, Semantic Scholar, WebSearch), you'll get hallucinated model names and made-up benchmark numbers.

A single search pass will miss models — there were many releases. You need iterative search to achieve coverage.

## Expected ceiling by step

- Step 0-2 (no tools): ~20 — will hallucinate models and numbers
- Step 3 (tools, one pass): ~50 — finds real models but misses several
- Step 4 (iterative): ~75 — multiple search rounds catch what was missed
- Step 5-6 (verification/team): ~85 — catches any remaining hallucinations

## What to focus on

This is where your MCP server and iteration loop matter. Build your arXiv/Semantic Scholar tools, make your skill iterative, and watch the score jump. The gap between step 2 and step 3 is dramatic here.
