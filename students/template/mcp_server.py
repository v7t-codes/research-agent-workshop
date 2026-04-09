"""
TASK 3: Build your MCP tool.

Before you write a single line of code, answer these three questions:

  1. What does Claude need that it can't get from WebSearch?
     (Think: structured data, verified sources, a specific database, real-time info)

  2. What format should the return be in?
     (Tables and lists > paragraphs. Claude reasons about structure, not prose.)

  3. What parameters does Claude need to pass?
     (Fewer is better. Defaults are your friend. Every param needs a type hint.)

Your tool must:
  - Return structured data, not raw HTML
  - Have a docstring Claude can use to decide WHEN and HOW to call it
  - Handle errors gracefully (return a message, don't raise an exception)
  - Work without authentication (or with a key students can get in 2 min)

Free APIs with no auth (to get started):
  - Wikipedia:     https://en.wikipedia.org/api/rest_v1/
  - OpenAlex:      https://api.openalex.org/works?search=...
  - PubMed:        https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
  - CrossRef:      https://api.crossref.org/works?query=...
  - HackerNews:    https://hn.algolia.com/api/v1/search?query=...
  - arXiv:         https://export.arxiv.org/api/query (already built — use OpenAlex instead)

Run this server:
    pip install fastmcp
    python3 scaffold/mcp_skeleton.py

Connect to Claude Code — add to .claude/settings.json:
    "mcpServers": {
        "my-tools": {
            "command": "python3",
            "args": ["scaffold/mcp_skeleton.py"]
        }
    }

Then update your SKILL.md allowed-tools:
    allowed-tools: WebSearch WebFetch Read Write mcp__my-tools__YOUR_TOOL_NAME
"""

from fastmcp import FastMCP
import urllib.request
import urllib.parse
import json

mcp = FastMCP("my-tools")  # change "my-tools" to something descriptive


# ── Your tool goes here ──────────────────────────────────────────────────────
#
# Template:
#
# @mcp.tool
# def your_tool_name(param1: str, param2: int = 10) -> str:
#     """[WRITE THIS FOR CLAUDE, NOT FOR HUMANS]
#
#     Explain:
#     - What this tool does (one sentence)
#     - What it returns (field names, format)
#     - When Claude should use it vs WebSearch
#
#     Args:
#         param1: [what is this? what should Claude pass?]
#         param2: [what is this? what's a good default?]
#     """
#     # Your implementation
#     pass


@mcp.tool
def placeholder_tool(query: str) -> str:
    """[REPLACE THIS: describe what your tool actually does]

    Returns: [describe what fields you'll return]

    Args:
        query: [describe what Claude should pass here]
    """
    # DELETE THIS and write your real implementation
    return "Replace this placeholder with your actual tool implementation."


# ── Helper functions (optional) ──────────────────────────────────────────────

def fetch_json(url: str) -> dict:
    """Fetch and parse JSON from a URL. Returns empty dict on error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ResearchAgent/1.0"})
        response = urllib.request.urlopen(req, timeout=15).read().decode()
        return json.loads(response)
    except Exception as e:
        return {"error": str(e)}


def fetch_text(url: str) -> str:
    """Fetch text from a URL. Returns error message on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ResearchAgent/1.0"})
        return urllib.request.urlopen(req, timeout=15).read().decode()
    except Exception as e:
        return f"Error fetching {url}: {e}"


if __name__ == "__main__":
    mcp.run()
