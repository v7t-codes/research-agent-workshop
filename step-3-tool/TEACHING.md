# Step 3: Custom Tool (MCP Server) — Design Principles

## What it physically is

A Python process that exposes functions Claude can call. Built with FastMCP, it runs as a separate process and communicates via the Model Context Protocol (MCP). Claude sees the tools as callable functions with typed parameters and documentation.

## The design principle: Structured data beats unstructured search

Built-in WebSearch gives you Google results — HTML snippets, SEO-optimized blog posts, mixed quality. A custom MCP server gives you **structured API access** — paper titles, abstracts, authors, citation counts, publication dates. Fundamentally different quality of data.

**Why this matters for research:** When Claude searches Google for "scaling laws MoE models", it gets blog summaries. When it calls `search_arxiv("scaling laws mixture of experts")`, it gets actual paper metadata with abstracts. The research report goes from "summarizing blog posts" to "citing primary sources."

## Anatomy of an MCP server

The entire arXiv MCP server is ~50 lines of Python:

```python
from fastmcp import FastMCP

mcp = FastMCP("research-tools")

@mcp.tool
def search_arxiv(query: str, max_results: int = 10) -> str:
    """Search arXiv for papers matching a query.
    Returns: title, authors, abstract, date, URL."""
    # ... API call to arXiv ...
    return formatted_results

if __name__ == "__main__":
    mcp.run()
```

### Three things that matter

1. **The `@mcp.tool` decorator** — registers the function as a tool Claude can call
2. **Type hints** — Claude uses these to know what parameters to pass
3. **The docstring** — Claude reads this to decide WHEN to use the tool and HOW

A good docstring is the difference between Claude using your tool well and ignoring it.

## How to connect an MCP server to Claude Code

Add to `.claude/settings.json`:
```json
{
  "mcpServers": {
    "research-tools": {
      "command": "python3",
      "args": ["mcp-servers/arxiv_server.py"]
    }
  }
}
```

Then update your SKILL.md's `allowed-tools` to include the MCP tools:
```yaml
allowed-tools: WebSearch WebFetch Read Write mcp__research-tools__search_arxiv mcp__research-tools__search_semantic_scholar
```

## How to add scripts to skills

This is the connection between tools and skills. Your SKILL.md tells Claude the methodology. The `allowed-tools` field tells Claude what tools it can use. The MCP server provides those tools.

```
SKILL.md (methodology)     →  "In step 2, search arXiv for each sub-question"
  ↓ allowed-tools
MCP server (capability)    →  search_arxiv(query) returns structured paper data
```

The skill says WHAT to do. The tool provides HOW to do it. This separation means you can swap tools without changing methodology, or swap methodology without changing tools.

## Choosing what API to wrap

| API | Best for | Returns |
|-----|---------|---------|
| **arXiv** | CS/AI/physics papers | Title, authors, abstract, date, PDF link |
| **Semantic Scholar** | Citation analysis, impact | Same + citation count, venue, influence score |
| **PubMed** | Biomedical research | Structured medical/bio paper metadata |
| **DBLP** | CS publication search | Author disambiguation, venue matching |
| **CrossRef** | DOI verification | Verified publication metadata |

For this workshop, arXiv + Semantic Scholar cover most needs. Advanced teams might add PubMed (for test problem 3, which is biomedical).

## Score impact

| | Before (step 2) | After (step 3) |
|--|--|--|
| **What changes** | Claims from training data only. For recent topics: hallucinated or outdated | Real papers from 2024-2026, actual benchmark numbers, verifiable URLs |
| **What doesn't change** | Still one pass, may miss papers, no verification | Still one pass — but now with real data |

This is often the **biggest single jump** in the staircase. For questions about recent topics (Q1 2026 models, A2A protocol), going from training data to real API data is the difference between a hallucinated report and a useful one.
