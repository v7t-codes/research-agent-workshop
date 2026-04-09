"""
Custom MCP Server: Research Tools
Gives Claude structured access to arXiv and Semantic Scholar APIs.

This is what makes step 3 different from step 2.
Built-in WebSearch gives you Google results — unstructured, noisy.
This MCP server gives you structured paper metadata — titles, abstracts,
authors, citation counts, dates. Fundamentally different quality of data.

To run:
    pip install fastmcp
    python mcp-servers/arxiv_server.py

To connect to Claude Code, add to settings.json:
    "mcpServers": {
        "research-tools": {
            "command": "python",
            "args": ["mcp-servers/arxiv_server.py"]
        }
    }
"""

from fastmcp import FastMCP
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET

mcp = FastMCP("research-tools")


@mcp.tool
def search_arxiv(query: str, max_results: int = 10) -> str:
    """Search arXiv for papers matching a query.

    Returns structured paper metadata: title, authors, abstract,
    published date, and arXiv URL. Much more structured than web search.

    Args:
        query: Search terms (e.g., "multi-agent research systems")
        max_results: Number of papers to return (default 10, max 50)
    """
    max_results = min(max_results, 50)
    encoded_query = urllib.parse.quote(query)
    url = (
        f"https://export.arxiv.org/api/query"
        f"?search_query=all:{encoded_query}"
        f"&start=0&max_results={max_results}"
        f"&sortBy=submittedDate&sortOrder=descending"
    )

    response = urllib.request.urlopen(url, timeout=15).read().decode()
    root = ET.fromstring(response)

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    papers = []

    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        published = entry.find("atom:published", ns).text[:10]

        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.find("atom:name", ns).text
            authors.append(name)

        link = ""
        for l in entry.findall("atom:link", ns):
            if l.get("type") == "text/html":
                link = l.get("href")
                break

        papers.append({
            "title": title,
            "authors": authors[:5],  # first 5 authors
            "abstract": summary[:500],  # truncate long abstracts
            "published": published,
            "url": link
        })

    if not papers:
        return f"No papers found for query: {query}"

    # Format as readable text
    result = f"Found {len(papers)} papers for: {query}\n\n"
    for i, p in enumerate(papers, 1):
        result += f"## Paper {i}\n"
        result += f"**Title:** {p['title']}\n"
        result += f"**Authors:** {', '.join(p['authors'])}\n"
        result += f"**Published:** {p['published']}\n"
        result += f"**URL:** {p['url']}\n"
        result += f"**Abstract:** {p['abstract']}\n\n"

    return result


@mcp.tool
def search_semantic_scholar(query: str, max_results: int = 10) -> str:
    """Search Semantic Scholar for papers with citation data.

    Returns papers with citation counts and influence scores.
    Better than arXiv for understanding paper impact and finding
    highly-cited work.

    Args:
        query: Search terms (e.g., "deep research agents benchmark")
        max_results: Number of papers to return (default 10, max 20)
    """
    max_results = min(max_results, 20)
    encoded_query = urllib.parse.quote(query)
    url = (
        f"https://api.semanticscholar.org/graph/v1/paper/search"
        f"?query={encoded_query}"
        f"&limit={max_results}"
        f"&fields=title,authors,year,citationCount,abstract,url,venue"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "ResearchAgent/1.0"})

    try:
        response = urllib.request.urlopen(req, timeout=15).read().decode()
        data = json.loads(response)
    except Exception as e:
        return f"Semantic Scholar API error: {e}"

    papers = data.get("data", [])
    if not papers:
        return f"No papers found for query: {query}"

    result = f"Found {len(papers)} papers for: {query}\n\n"
    for i, p in enumerate(papers, 1):
        authors = [a.get("name", "Unknown") for a in (p.get("authors") or [])[:5]]
        abstract = (p.get("abstract") or "No abstract available")[:500]

        result += f"## Paper {i}\n"
        result += f"**Title:** {p.get('title', 'Unknown')}\n"
        result += f"**Authors:** {', '.join(authors)}\n"
        result += f"**Year:** {p.get('year', 'Unknown')}\n"
        result += f"**Venue:** {p.get('venue', 'Unknown')}\n"
        result += f"**Citations:** {p.get('citationCount', 0)}\n"
        result += f"**URL:** {p.get('url', 'N/A')}\n"
        result += f"**Abstract:** {abstract}\n\n"

    return result


if __name__ == "__main__":
    mcp.run()
