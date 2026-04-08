# Step 3: Custom Tool (MCP Server)

## What you're adding
A Python MCP server that gives Claude structured access to arXiv and Semantic Scholar. This is a NEW capability Claude didn't have before.

## What it is
A custom tool is a function that Claude can call. MCP (Model Context Protocol) is the universal standard for connecting models to external systems. You write a Python function, wrap it in FastMCP, and Claude can call it.

## Why this isn't just "using WebSearch"
WebSearch gives you Google results — unstructured HTML, noisy, mixed quality. Your custom MCP server gives you:
- **Structured data**: paper titles, authors, abstracts, dates, citation counts
- **Domain-specific**: searches academic databases, not the general web
- **Reliable**: API returns consistent format every time

This is a fundamentally different quality of input to the research process.

## What changes
- Output has REAL papers from 2025-2026 (not hallucinated from training data)
- Citations are actual paper references with titles, authors, venues
- Benchmark numbers come from real sources, not memory

## What to do
1. Copy everything from step-1 and step-2 into your working directory
2. Copy `mcp-servers/arxiv_server.py` 
3. Install: `pip install fastmcp`
4. Add to your Claude Code settings (or `.claude/settings.json`):
   ```json
   {
     "mcpServers": {
       "research-tools": {
         "command": "python",
         "args": ["mcp-servers/arxiv_server.py"]
       }
     }
   }
   ```
5. Run: `/deep-research [practice problem 2]`
6. Evaluate: `python benchmark/evaluate.py --input output.md`

## What you'll see
Score jumps from ~38 to ~55. Source recency and citation quality jump hard. But still one-pass — misses depth.
