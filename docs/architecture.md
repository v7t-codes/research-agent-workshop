# Architecture: How the Research Agent System Works

A complete knowledge-transfer document for the IISc Research Agent Workshop. This covers every file, every abstraction, every design decision. After reading this, you should be able to understand, modify, and extend the system without opening the repo.

---

## 1. The Thesis

**Same model, different harness, dramatically different results.**

Opus 4.5 raw scores 30.5% on OSWorld. With a proper harness: 66.3%. That is a 2.2x improvement from the system around the model, not from a better model. The model is the constant. The architecture is the variable.

This workshop proves the thesis by building a research agent through six incremental steps, each adding one compound-AI concept, and measuring improvement at every step against the RACE benchmark (from Deep Research Bench). The scoring staircase:

| Step | Concept | Heuristic Score | LLM Score |
|------|---------|:---------:|:---------:|
| 0 | Raw Claude (no files) | ~20 | ~18 |
| 1 | Context (CLAUDE.md) | ~21 | ~25 |
| 2 | Skill (SKILL.md) | ~37 | ~38 |
| 3 | Custom Tool (MCP server) | ~58 | ~55 |
| 4 | Iterative Skill (loop logic) | ~53 | ~72 |
| 5 | Verification Agent (subprocess) | ~90 | ~85 |
| 6 | Team of Agents (multi-agent) | ~93 | ~93 |

Step 0 to step 6 is a ~5x improvement on heuristic scoring, all from the same underlying model. The heuristic applies a source-grounding factor: outputs without real URLs (steps 0-2) are penalized; outputs with evidence quality ratings (step 6) are boosted.

---

## 2. The Abstraction Hierarchy

### The Six Concepts as Physical Artifacts

| # | Concept | Physical Form | File Path (relative) | Where It Runs | Key Property |
|---|---------|--------------|---------------------|---------------|-------------|
| 0 | Baseline | Nothing | n/a | Claude's context | No guidance |
| 1 | Context | Markdown file | `step-1-context/CLAUDE.md` | Read into Claude's context at session start | **Identity** -- WHO Claude works for |
| 2 | Skill | Markdown file with YAML frontmatter | `step-2-skill/.claude/skills/deep-research/SKILL.md` | Read into Claude's context when triggered | **Methodology** -- HOW to do the work |
| 3 | Tool | Python process (FastMCP) | `step-3-tool/mcp-servers/arxiv_server.py` | Separate OS process, communicates via MCP | **Capability** -- new actions Claude can take |
| 4 | Iterative Skill | Markdown file with loop logic | `step-4-iterative/.claude/skills/deep-research/SKILL.md` | Same session, same context window | **Autonomy** -- Claude decides when to loop |
| 5 | Agent | Separate Claude subprocess | Via `Agent` tool in SKILL.md | Separate process, separate context window | **Independence** -- fresh eyes, no shared bias |
| 6 | Team | Multiple Agent subprocesses | `step-6-team/.claude/skills/{orchestrator,searcher,critic,synthesizer}/SKILL.md` | Multiple separate processes, file-based IPC | **Specialization** -- each does one thing well |

### The Three Critical Boundaries

**Boundary 1: Skill vs. Agent.** A skill runs in YOUR session, YOUR context window. It shares memory with everything else in your conversation. An agent is a SEPARATE Claude process spawned via the `Agent` tool, with its own context window. A skill is a recipe the chef follows. An agent is hiring a second chef.

**Boundary 2: Iterative Skill vs. Agent.** Both involve decision-making. The iterative skill (step 4) makes decisions within one context window -- "do I have enough sources? search again." The agent (step 5) is a different process. The iterative skill is a chef tasting and adjusting. The agent is a food critic who never saw the cooking.

**Boundary 3: Agent vs. Team.** One agent is one subprocess. A team is multiple subprocesses, each specialized, communicating through files. One agent is hiring a second chef. A team is running a kitchen with a sous chef, a saucier, and a pastry chef.

---

## 3. Step-by-Step Deep Dive

### Step 0: Baseline (Raw Claude)

**What it IS:** Nothing. No files. Raw Claude with no context, no skill, no tools.

**What it DOES:** Claude answers from training data in generic assistant voice. No structure, no citations, wrong terminology for the domain, no awareness of the user's field.

**Score:** Heuristic ~20, LLM ~18. This is the floor.

---

### Step 1: Context (CLAUDE.md)

**What it IS:** A single markdown file at the project root.

**File path:** `step-1-context/CLAUDE.md`

**What it DOES:** Claude Code reads `CLAUDE.md` automatically at the start of every session. It injects identity: who the user is, what field they work in, what sources they trust, what citation format they prefer.

**The exact content:**

```markdown
# Research Context

You are assisting a researcher in computer science and artificial intelligence.

## Domain
- Primary fields: machine learning, deep learning, AI systems, agent architectures
- I read papers from: NeurIPS, ICML, ICLR, ACL, EMNLP, CVPR, arXiv cs.AI/cs.CL/cs.LG
- I value: empirical results with specific numbers, reproducibility, clear methodology

## Preferences
- Citation format: Author (Year) inline, full reference list at end
- Prioritize: peer-reviewed papers > preprints > technical blogs > news articles
- When numbers conflict between sources, show both with methodology notes
- Flag anything older than 12 months as potentially outdated

## Constraints
- Never state claims without attribution
- Distinguish between "the paper claims X" and "X is established consensus"
- If you're uncertain, say so explicitly
```

**Design principles (from TEACHING.md):**

1. **Identity before methodology.** Context answers WHO, not HOW. The same question asked by a physicist vs. a policy analyst should produce different outputs.
2. **Five things that belong in CLAUDE.md:** Field/sub-field, preferred sources, citation format, constraints, definition of "good."
3. **What does NOT belong:** Methodology (that's a skill), tool configuration (step 3), iteration logic (step 4), verification (step 5). Mixing these makes the file fragile.
4. **The 5-sentence test:** "If you could only give Claude 5 sentences before it started researching for you, what would those 5 sentences be?" Those are your CLAUDE.md.

**What changes from step 0:** Generic assistant voice becomes domain-appropriate framing. Right terminology, right source priority, right citation format.

**What does NOT change:** Still no structure, still from training data, still one pass, still shallow.

**Score impact:** Heuristic ~20 to ~21, LLM ~18 to ~25. Small but foundational. Every subsequent step builds on this identity.

---

### Step 2: Skill (SKILL.md)

**What it IS:** A markdown file with YAML frontmatter, placed in the `.claude/skills/` directory.

**File path:** `step-2-skill/.claude/skills/deep-research/SKILL.md`

**What it DOES:** Gives Claude a structured methodology -- a recipe to follow top to bottom. One pass. Decompose the question, search, extract claims, cross-reference, synthesize.

**The exact content (key sections):**

YAML frontmatter:
```yaml
---
name: deep-research
description: >-
  Researches any topic using structured methodology with source verification.
  Use when user says "research", "investigate", "deep dive", or "what do we know about".
---
```

The body defines a 5-step methodology:

1. **Decompose** -- break the question into 3-5 specific, searchable sub-questions. State what a strong answer would look like BEFORE searching.
2. **Search** -- for each sub-question, search. Prioritize: papers > official docs > data > news > blogs. Flag self-reported metrics as unverified.
3. **Extract Claims** -- from each source: specific claims WITH numbers, methodology behind the numbers, date of data, who is making the claim and their credibility.
4. **Cross-Reference** -- where do sources agree (consensus), where do they conflict (present both with methodology notes), what is nobody saying (gaps).
5. **Synthesize** -- write the report in a mandatory format:

```
# [Topic]: [One-sentence thesis]

## Key Findings
- [Finding with specific numbers + source]

## Detailed Analysis
[Group by theme, not by source. Cross-reference across sources.]

## Source Conflicts
| Claim | Source A says | Source B says | Assessment |

## Open Questions
- [What we don't know yet]

## Sources
- [Full reference for each source cited]
```

Quality rules: every claim needs a number or explicit "qualitative assessment." Never list sources sequentially -- synthesize ACROSS them. Label inferences explicitly: "this suggests..." not "this proves..."

**Design principles (from TEACHING.md):**

1. **A skill is a recipe, not a chef.** One pass, top to bottom. It does not loop, does not evaluate its own output, does not dispatch other processes.
2. **Decompose before you search.** This prevents the "search for the obvious thing and stop" failure mode. Forces Claude to think about coverage before executing.
3. **The output format IS part of the methodology.** If you don't specify format, Claude writes a generic essay. Specifying thesis-first, conflicts table, and reference list directly improves RACE scores.
4. **What a skill is NOT:** Not a prompt (prompts die with the chat; skills persist on disk). Not an agent (agents are separate processes). Not a tool (tools give new capabilities; skills dictate HOW to use capabilities).

**What changes from step 1:** Unstructured essay becomes structured report with thesis, numbered findings, conflicts table, and citations.

**What does NOT change:** Still from training data only. Still one pass. No real-time sources.

**Score impact:** Heuristic ~21 to ~37, LLM ~25 to ~38. Significant jump because structure and specificity are exactly what RACE measures.

---

### Step 3: Custom Tool (MCP Server)

**What it IS:** A Python process built with FastMCP that runs as a separate OS process and communicates with Claude via the Model Context Protocol.

**File path:** `step-3-tool/mcp-servers/arxiv_server.py`

**What it DOES:** Gives Claude structured access to arXiv and Semantic Scholar APIs. Instead of Google results (HTML snippets, SEO-optimized blogs, mixed quality), Claude gets structured paper metadata: titles, abstracts, authors, citation counts, publication dates, URLs.

**The exact server code:**

```python
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
            "authors": authors[:5],
            "abstract": summary[:500],
            "published": published,
            "url": link
        })

    if not papers:
        return f"No papers found for query: {query}"

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
```

**Two tools exposed:**

| Tool | API | Returns | Max Results | Best For |
|------|-----|---------|:-----------:|----------|
| `search_arxiv` | arXiv Atom API | title, authors, abstract, published date, URL | 50 | Recent papers, preprints, CS/AI/physics |
| `search_semantic_scholar` | Semantic Scholar Graph API | title, authors, year, venue, citation count, abstract, URL | 20 | Citation analysis, impact assessment, highly-cited work |

**How it connects to Claude Code:**

Add to `.claude/settings.json` (or `mcp-config.json`):
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

Then update the SKILL.md `allowed-tools` frontmatter:
```yaml
allowed-tools: WebSearch WebFetch Read Write mcp__research-tools__search_arxiv mcp__research-tools__search_semantic_scholar
```

The naming convention for MCP tools in `allowed-tools` is: `mcp__<server-name>__<function-name>`.

**Design principles (from TEACHING.md):**

1. **Structured data beats unstructured search.** WebSearch gives Google results -- HTML snippets, SEO blogs. The MCP server gives structured metadata. The research report goes from "summarizing blog posts" to "citing primary sources."
2. **Three things that matter in a tool:** The `@mcp.tool` decorator (registers the function), type hints (Claude uses them for parameters), and the docstring (Claude reads it to decide WHEN and HOW to use the tool). A good docstring is the difference between Claude using your tool well and ignoring it.
3. **Separation of skill and tool.** The skill says WHAT to do ("search arXiv for each sub-question"). The tool provides HOW to do it (`search_arxiv(query)` returns structured data). You can swap tools without changing methodology, or swap methodology without changing tools.

**What changes from step 2:** Claims from training data only become real papers from 2024-2026 with actual benchmark numbers and verifiable URLs.

**What does NOT change:** Still one pass. May miss papers. No verification.

**Score impact:** Heuristic ~37 to ~58, LLM ~38 to ~55. Often the biggest single jump in the staircase. For questions about recent topics, going from training data to real API data is the difference between a hallucinated report and a useful one.

---

### Step 4: Iterative Skill (Loop Logic)

**What it IS:** The same SKILL.md file format, but now with decision logic. After the initial search, the skill tells Claude: "evaluate your coverage. If any sub-question has fewer than 3 sources, refine your queries and search again."

**File path:** `step-4-iterative/.claude/skills/deep-research/SKILL.md`

**What it DOES:** Adds an evaluate-then-decide loop to the research methodology. Still one process, one context window, one session. The difference is Claude makes decisions within the methodology instead of following it linearly.

**What changed from step 2/3 (the diff):**

The step 2 SKILL.md had:
```markdown
### Step 2: Search
For each sub-question, search for relevant sources.
```

The step 4 SKILL.md replaces this with a multi-round loop:

```markdown
### Step 2: Search -- Round 1 (breadth-first)
For each sub-question:
- search_arxiv and/or search_semantic_scholar for papers
- WebSearch for broader context
- Record what you found AND what you're still missing

### Step 3: Evaluate Coverage
After round 1, assess:
- Which sub-questions have strong coverage (3+ quality sources)?
- Which have gaps (fewer than 3 sources, or only superficial coverage)?
- Are there NEW sub-questions that emerged from what you found?

### Step 4: Search -- Round 2 (depth-first, targeted)
For each gap identified:
- Refine your search queries based on what you learned in round 1
- Search for specific papers, specific authors, specific benchmarks
- Follow citation chains: if paper A cites paper B and B seems important, fetch B
- Add any new sub-questions that emerged

### Step 5: Evaluate Again
- Do you have 3+ quality sources for each sub-question?
- Have you found conflicting claims that need investigation?
- If still gaps: do ONE more targeted round (max 3 rounds total)
- If sufficient: proceed to synthesis
```

**The three loop-design choices (from TEACHING.md):**

1. **What triggers another round?** Concrete threshold: "If any sub-question has fewer than 3 sources, search again with refined queries." Avoids both stopping too early and searching forever.
2. **How do you refine queries?** Specific strategies: (a) different terminology, (b) broader scope, (c) specific author names from found papers' references.
3. **When do you stop?** Maximum 3 rounds. Always set a maximum. LLM loops without bounds burn tokens and time.

**The loop structure visualized:**

```
Search (breadth-first, all sub-questions)
   |
   v
Evaluate coverage (3+ sources per sub-question?)
   |
   +--[gaps exist]--> Refine queries --> Search again (depth-first, targeted)
   |                                          |
   |                                          v
   |                                    Evaluate again
   |                                          |
   |                                          +--[still gaps, round < 3]--> Search round 3
   |                                          |
   |                                          +--[sufficient or round = 3]-+
   |                                                                       |
   +--[sufficient]------------------------------------------------------>  v
                                                                     Extract claims
                                                                           |
                                                                           v
                                                                     Cross-reference
                                                                           |
                                                                           v
                                                                       Synthesize
```

**Design principles (from TEACHING.md):**

1. **Evaluate then decide, don't just execute.** A one-pass skill is a recipe: A, B, C, done. An iterative skill is a recipe with taste-testing: A, check, adjust, B, check, adjust, C.
2. **Why this is NOT an agent.** Most common confusion. The iterative skill runs in YOUR session, YOUR context window. It shares memory. An agent is a SEPARATE process with its OWN context window. Iteration = chef tasting and adjusting. Agent = hiring a second chef.
3. **Iteration catches what one pass misses:** papers using different terminology, papers from adjacent fields, very recent papers not yet indexed by the first query.

**What changes from step 3:** Found some papers but missed several. Now: multiple search rounds fill gaps using alternative terminology, author names, citation chains.

**What does NOT change:** May still cite hallucinated papers. No independent verification. Iteration improves coverage, not accuracy.

**Score impact:** Heuristic ~58 to ~53 (heuristic penalizes the extra tokens without seeing the quality improvement), LLM ~55 to ~72. The LLM scorer sees the improved depth and coverage that the heuristic misses.

---

### Step 5: Verification Agent (Subprocess)

**What it IS:** A separate Claude instance, spawned using the `Agent` tool. It has its own context window, its own tools, its own task.

**File paths:**
- Research skill: `step-5-verification/.claude/skills/deep-research/SKILL.md`
- Verification skill: `step-5-verification/.claude/skills/verify-research/SKILL.md`

**What it DOES:** After the research is complete (Phase 1, same as step 4), a second Claude process is spawned to independently audit the report. The verifier reads the output cold -- no access to the reasoning that produced it. It checks every citation and every numerical claim.

**The two-phase architecture:**

**Phase 1: Research** (same as step 4) -- decompose, iterative search, extract, cross-reference, synthesize. Save draft to `research_draft.md`.

**Phase 2: Verification** (new) -- dispatch via Agent tool:

```
You are a research verification agent. Your job is to independently
audit a research report for accuracy and citation validity.

Read the file research_draft.md.

For EACH cited source in the report:
1. Search for the paper by its exact title using WebSearch
2. Check: does this paper actually exist?
3. If it exists: does the claim attributed to it match what the paper says?
4. If it doesn't exist: flag it as UNVERIFIED

For EACH numerical claim:
1. Can you find this specific number in the cited source?
2. If yes: mark as VERIFIED
3. If no: mark as UNVERIFIED with a note

Output a verification report:
## Verified Claims
- [Claim]: [Source] -- VERIFIED

## Unverified Claims
- [Claim]: [Source] -- UNVERIFIED -- [reason]

## Hallucinated Sources
- [Source title] -- could not confirm this paper exists

## Summary
- Total claims checked: X
- Verified: Y
- Unverified: Z
- Hallucinated sources: W
```

**Phase 3: Correct and finalize** -- remove hallucinated sources, qualify unverified claims, add verification summary section.

**The verification skill (verify-research/SKILL.md):**

```yaml
---
name: verify-research
description: >-
  Verification agent that audits a research report for citation validity and
  claim accuracy. Spawned as a subagent -- runs in its own context window.
allowed-tools: WebSearch WebFetch Read
---
```

Key sections of the verification process:
1. **Read the report** -- extract every cited source, numerical claim, and factual assertion.
2. **Verify sources** -- search for each paper by EXACT title. Try to access URLs. Classify: EXISTS / DOES NOT EXIST / CANNOT VERIFY.
3. **Verify claims** -- does the cited source actually say this? Classify: VERIFIED / UNVERIFIED / CONTRADICTED.
4. **Produce verification report** with structured summary.

Rules: check EVERY source (not a sample), be honest (CANNOT VERIFY, not VERIFIED), be specific (explain what you searched for), do NOT add new information (auditor, not researcher).

**What the verification agent catches:**
- **Hallucinated papers** -- titles that look plausible but don't exist
- **Misattributed numbers** -- paper exists but the number is from a different paper
- **Outdated claims** -- cited result has been superseded
- **Author/year mismatches** -- wrong year, wrong first author

**Design principles (from TEACHING.md):**

1. **Verification must be independent.** If verification runs in the same context as research, it's biased. Claude has just spent its context window reasoning about why these claims are correct. Asking it to verify in the same context is like asking a student to grade their own exam.
2. **Why not just "verify your work" in the skill?** Three reasons: context pollution (Claude has already committed to its claims), tool competition (tool calls compete for context space), lack of specialization (verification agent's ONLY job is to check).
3. **Independence produces objectivity.** This is the fundamental argument for agents.

**What changes from step 4:** 2-3 hallucinated papers that passed through are now caught and removed. Misattributed numbers corrected or flagged.

**What does NOT change:** Coverage and depth are the same. The research methodology didn't change.

**Score impact:** Heuristic ~53 to ~90, LLM ~72 to ~85. The RACE "insight" dimension rewards identifying where sources conflict. The verification agent surfaces real conflicts rather than letting Claude gloss over them.

---

### Step 6: Team of Agents (Multi-Agent Pipeline)

**What it IS:** Multiple agents (each a separate Claude subprocess), each with their own SKILL.md, tools, and context window, coordinated by an orchestrator skill running in the user's session.

**File paths:**
- Orchestrator: `step-6-team/.claude/skills/orchestrator/SKILL.md`
- Searcher: `step-6-team/.claude/skills/searcher/SKILL.md`
- Critic: `step-6-team/.claude/skills/critic/SKILL.md`
- Synthesizer: `step-6-team/.claude/skills/synthesizer/SKILL.md`

**The architecture:**

```
Your session (orchestrator skill)
|
+-- Phase 1: dispatches --> Searcher agent (own context, own tools)
|                             Tools: search_arxiv, search_semantic_scholar, WebSearch, WebFetch, Read, Write
|                             Output: searcher_output.md
|
+-- Phase 2: dispatches --> Critic agent (own context, own tools)
|                             Tools: WebSearch, WebFetch, Read, Write
|                             Input: searcher_output.md
|                             Output: critic_output.md
|
+-- Phase 3: dispatches --> Synthesizer agent (own context, own tools)
|                             Tools: Read, Write
|                             Input: searcher_output.md + critic_output.md
|                             Output: final_report.md
|
+-- Phase 4: Review final_report.md, fix minor issues, present to user
```

**The four SKILL.md files:**

**Orchestrator** (`orchestrator/SKILL.md`):
```yaml
---
name: deep-research
description: >-
  Orchestrates a team of specialized agents to research any topic.
  Dispatches searcher, critic, and synthesizer agents in sequence.
  Use when user says "research", "investigate", "deep dive", or "what do we know about".
allowed-tools: Agent Read Write
---
```
The orchestrator does NOT do research itself. It dispatches three agents in sequence, passing each one the research question and its role-specific instructions. It has `Agent`, `Read`, and `Write` -- nothing else. Its job is coordination.

**Searcher** (`searcher/SKILL.md`):
```yaml
---
name: research-searcher
description: >-
  Searcher agent -- finds papers and extracts structured metadata and claims.
  Spawned as a subagent by the orchestrator. Runs in its own context window.
allowed-tools: WebSearch WebFetch Read Write mcp__research-tools__search_arxiv mcp__research-tools__search_semantic_scholar
---
```
Process: decompose into sub-questions, search round 1 (breadth), evaluate gaps, search round 2 (depth), extract structured metadata for EVERY source (title, authors, venue, year, URL, key claims with numbers, methodology, date, discovery method), save to `searcher_output.md`. The searcher does NOT evaluate quality. It finds and records.

**Critic** (`critic/SKILL.md`):
```yaml
---
name: research-critic
description: >-
  Critic agent -- evaluates evidence quality, finds conflicts, flags weak methodology.
  Spawned as a subagent by the orchestrator. Runs in its own context window.
allowed-tools: WebSearch WebFetch Read Write
---
```
Process: read `searcher_output.md`, evaluate each source (methodology sound? sample size adequate? benchmark comparisons fair?), rate each STRONG / MODERATE / WEAK with specific reason, find conflicts between sources (what each side claims, methodological differences), check for hallucinations (search for paper titles, try URLs), identify gaps (missing sub-topics, missing perspectives, missing data), save to `critic_output.md`. The critic does NOT search for new papers. It audits.

**Synthesizer** (`synthesizer/SKILL.md`):
```yaml
---
name: research-synthesizer
description: >-
  Synthesizer agent -- produces the final research report from searcher findings
  and critic assessment. Spawned as a subagent by the orchestrator.
allowed-tools: Read Write
---
```
Process: read both `searcher_output.md` and `critic_output.md`, remove hallucinated sources entirely, include WEAK sources only if corroborated, group findings by THEME (not by source), integrate evidence quality ratings, present conflicts with both sides and methodology differences, write "Gaps and Limitations" section from critic's analysis, include verification summary, save to `final_report.md`. The synthesizer does NOT search and does NOT critique. It weaves.

Output format specified in the synthesizer skill:
```
# [Topic]: [One-sentence thesis]

## Key Findings
- [Finding with numbers + source] -- evidence quality: [STRONG/MODERATE]

## Detailed Analysis
[Thematic grouping. Cross-referenced. Critic's quality ratings integrated.]

## Where Experts Disagree
| Claim | Position A | Position B | Evidence Strength | Assessment |

## Gaps and Limitations
[From critic's gap analysis]

## Verification Summary
- Sources included: [N] of [total found]
- Sources excluded: [N] (hallucinated or unverifiable)
- Claims verified: [N] of [total]

## Sources
[Full references -- only verified sources]
```

**Design principles (from TEACHING.md):**

1. **Specialization beats generalization.** Anthropic's engineering blog found multi-agent (Opus lead + Sonnet subagents) outperformed single-agent by 90.2%. When a single agent does everything, it distributes attention. When agents specialize, each uses its full context window for ONE task.
2. **File-based communication prevents context pollution.** The critic doesn't see the searcher's reasoning -- only its output. Each agent gets a clean context with only the information it needs.
3. **Sequential, not parallel, for this use case.** The critic needs the searcher's output. The synthesizer needs both. Sequential is the right pattern here.

**What changes from step 5:** Deep evidence quality assessment. Real methodology critique. Genuine conflict analysis. Better writing quality because the synthesizer's ONLY job is writing.

**What does NOT change:** The underlying data sources are the same tools and APIs. But each is used by a specialized agent who does that one task better.

**Score impact:** Heuristic ~90 to ~93, LLM ~85 to ~93. Everything compounds: searcher finds more papers (search is its ONLY job), critic catches more issues (evaluation is its ONLY job), synthesizer writes better (it focuses entirely on structure and clarity).

---

## 4. Data Flow

### How a Research Query Flows Through Each Step

**Step 0-1:** User question --> Claude answers from training data --> unstructured response.

**Step 2:** User question --> decompose into sub-questions --> search (one pass) --> extract claims --> cross-reference --> synthesize --> structured report.

**Step 3:** Same as step 2, but search calls `search_arxiv()` and `search_semantic_scholar()` via MCP, returning structured paper metadata instead of web snippets.

**Step 4:** Same as step 3, but after initial search: evaluate coverage --> if gaps, refine queries and search again --> up to 3 rounds --> then extract, cross-reference, synthesize.

**Step 5:**
```
Phase 1 (same process):  question --> iterative search --> draft report --> save to research_draft.md
Phase 2 (new process):   Agent tool spawns verifier --> reads research_draft.md --> checks each citation --> verification report
Phase 3 (same process):  read verification report --> remove hallucinations --> finalize report
```

**Step 6:**
```
Orchestrator (your session):
  |
  +--> Spawns Searcher agent
  |      Input:  research question (passed in Agent prompt)
  |      Work:   decompose, iterative search via arXiv/Semantic Scholar/WebSearch
  |      Output: searcher_output.md (written to disk)
  |
  +--> Spawns Critic agent
  |      Input:  searcher_output.md (read from disk)
  |      Work:   evaluate each source, find conflicts, check for hallucinations, identify gaps
  |      Output: critic_output.md (written to disk)
  |
  +--> Spawns Synthesizer agent
  |      Input:  searcher_output.md + critic_output.md (read from disk)
  |      Work:   remove bad evidence, synthesize by theme, integrate quality ratings
  |      Output: final_report.md (written to disk)
  |
  +--> Orchestrator reads final_report.md, does quality check, presents to user
```

### File-Based Communication in Step 6

| File | Written By | Read By | Contents |
|------|-----------|---------|----------|
| `searcher_output.md` | Searcher agent | Critic agent, Synthesizer agent | One section per sub-question, all sources with structured metadata, all claims with numbers |
| `critic_output.md` | Critic agent | Synthesizer agent | Per-source quality ratings (STRONG/MODERATE/WEAK), conflicts with both sides, hallucination flags, gap analysis |
| `final_report.md` | Synthesizer agent | Orchestrator (for review), user (final output) | Thesis, key findings with evidence quality, thematic analysis, conflict table, gaps section, verification summary, references |

### Context Window Boundaries

| Step | Number of Context Windows | What Shares Memory |
|------|:------------------------:|--------------------|
| 0-4 | 1 | Everything -- all search results, reasoning, and synthesis are in one window |
| 5 | 2 | Research session (window 1) and verification agent (window 2) are independent. Verification agent sees ONLY `research_draft.md`, not the reasoning that produced it |
| 6 | 4 | Orchestrator (window 1), searcher (window 2), critic (window 3), synthesizer (window 4). Each sees only its inputs (files on disk) and its own skill instructions. No cross-contamination of reasoning |

The context window boundary is what makes agents fundamentally different from iterative skills. An iterative skill (step 4) that loops 3 times has all 3 rounds of search results in the SAME context -- it can reference earlier findings but also carries earlier biases. An agent starts fresh.

---

## 5. The MCP Server

### How `arxiv_server.py` Works

The server uses the **FastMCP** library, which implements the Model Context Protocol -- a standard for giving LLMs access to external tools.

**Architecture:**

```
Claude Code session
    |
    |  (spawns at session start, based on settings.json)
    v
arxiv_server.py (separate Python process)
    |
    |  (MCP protocol over stdio)
    |
    +-- search_arxiv()  -----> arXiv Atom API (HTTP)
    +-- search_semantic_scholar() --> Semantic Scholar Graph API (HTTP)
```

**The FastMCP pattern:**

```python
from fastmcp import FastMCP

mcp = FastMCP("research-tools")  # Server name -- used in tool naming

@mcp.tool                        # Registers function as a callable tool
def search_arxiv(query: str, max_results: int = 10) -> str:
    """Docstring -- Claude reads this to decide when/how to use the tool."""
    # ... implementation ...
    return formatted_string

if __name__ == "__main__":
    mcp.run()                    # Starts the MCP server
```

Three things Claude uses from the tool definition:
1. **`@mcp.tool` decorator** -- registers the function so Claude can call it
2. **Type hints** (`query: str`, `max_results: int = 10`) -- Claude uses these to construct valid calls
3. **The docstring** -- Claude reads this to decide WHEN to use the tool and WHAT parameters to pass

### The Two Tools

**`search_arxiv(query, max_results)`**
- Calls `https://export.arxiv.org/api/query` with Atom XML response
- Parses XML using `xml.etree.ElementTree`
- Returns up to 50 results, sorted by submission date (most recent first)
- Extracts: title, first 5 authors, abstract (truncated to 500 chars), published date, HTML link
- Formats as readable markdown (one `## Paper N` block per result)

**`search_semantic_scholar(query, max_results)`**
- Calls `https://api.semanticscholar.org/graph/v1/paper/search` with JSON response
- Requests fields: title, authors, year, citationCount, abstract, url, venue
- Returns up to 20 results
- Extracts: title, first 5 authors, year, venue, citation count, abstract (truncated to 500 chars), URL
- Formats as readable markdown
- Has error handling for API failures (try/except around the HTTP call)

### How It Connects to Claude Code

**Configuration file** (`.claude/settings.json` or `mcp-config.json`):
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

Claude Code reads this at session start, spawns the Python process, and maintains the MCP connection for the duration of the session. The tools then appear to Claude as callable functions named:
- `mcp__research-tools__search_arxiv`
- `mcp__research-tools__search_semantic_scholar`

These tool names are used in SKILL.md `allowed-tools` fields to grant skills access to the MCP tools.

### Why Structured Data Beats Web Search

| Source | What You Get | Quality |
|--------|------------|---------|
| WebSearch (Google) | HTML snippets, blog posts, SEO content, mixed quality | Unstructured -- Claude has to parse noise |
| `search_arxiv` | Paper title, authors, abstract, date, URL | Structured -- every field is clean metadata |
| `search_semantic_scholar` | Same + citation count, venue | Structured + impact signal |

When Claude searches Google for "scaling laws MoE models," it gets blog summaries. When it calls `search_arxiv("scaling laws mixture of experts")`, it gets actual paper metadata with abstracts. The research report goes from "summarizing blog posts" to "citing primary sources."

---

## 6. Skill File Convention

### File Location and Discovery

Skills live at `.claude/skills/<skill-name>/SKILL.md`. Claude Code discovers them automatically. Each step directory in the workshop has its own `.claude/skills/` tree showing that step's configuration.

Directory structure example (step 6):
```
step-6-team/
  .claude/
    skills/
      orchestrator/
        SKILL.md
      searcher/
        SKILL.md
      critic/
        SKILL.md
      synthesizer/
        SKILL.md
```

### YAML Frontmatter

Every SKILL.md starts with YAML frontmatter between `---` delimiters:

```yaml
---
name: deep-research
description: >-
  Researches any topic using structured methodology with source verification.
  Use when user says "research", "investigate", "deep dive", or "what do we know about".
allowed-tools: WebSearch WebFetch Read Write mcp__research-tools__search_arxiv mcp__research-tools__search_semantic_scholar
---
```

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | How Claude identifies this skill | `deep-research`, `verify-research`, `research-searcher` |
| `description` | Claude uses this to decide when to invoke the skill. Write trigger phrases. | `"Use when user says 'research', 'investigate', 'deep dive'"` |
| `allowed-tools` | Space-separated list of tools the skill can use | `WebSearch WebFetch Read Write mcp__research-tools__search_arxiv` |

The `description` field is critical. Claude reads it to decide WHEN to activate the skill. Include trigger phrases ("Use when user says X, Y, Z") for reliable activation.

The `allowed-tools` field controls what the skill has access to. This is the tool-restriction mechanism -- an agent spawned for synthesis gets `Read Write` only, while a searcher gets the full set of search tools.

### How Skills Are Triggered

Skills are triggered via `/skillname` in Claude Code. For example, `/deep-research` activates the deep-research skill. Claude can also auto-detect when to use a skill based on the `description` field's trigger phrases.

### How Skills Compose with Context

At runtime, Claude's effective instructions are the combination of:

```
CLAUDE.md (identity -- WHO)
  +
SKILL.md (methodology -- HOW)
  =
Complete research agent behavior
```

The CLAUDE.md says "you are assisting a CS/AI researcher who values empirical results and uses Author (Year) citation format." The SKILL.md says "decompose the question, search arXiv, extract claims with numbers, cross-reference, synthesize." Together they produce a domain-appropriate structured research report.

This separation is deliberate. You can swap the CLAUDE.md to change the domain (biomedical researcher, policy analyst, investor) while keeping the same SKILL.md methodology. Or swap the SKILL.md to change the methodology (literature review vs. competitive analysis) while keeping the same identity.

---

## 7. Agent Dispatch Pattern

### How the Agent Tool Works in Claude Code

The `Agent` tool is a built-in Claude Code capability that spawns a new Claude subprocess. It is NOT a function call within the same process -- it creates a separate OS process with a separate context window.

```
Your session (parent)
    |
    | Agent tool call (with prompt + tool restrictions)
    |
    v
New Claude process (child)
    |-- Has its own context window (starts empty + the prompt you gave it)
    |-- Has access to only the tools you specified
    |-- Runs independently
    |-- Returns its output to the parent when done
```

### Prompt Construction for Spawning Agents

When a SKILL.md instructs Claude to use the Agent tool, it provides:

1. **The agent's role** -- "You are a research verification agent" / "You are a research searcher agent"
2. **The specific task** -- "Read research_draft.md and verify each citation" / "Research this question and save findings to searcher_output.md"
3. **The methodology** -- either inline in the prompt or by reference to a SKILL.md
4. **The output expectations** -- what file to write, what format to use

Example from the step 5 research skill:
```
Use the Agent tool with this prompt:

"You are a research verification agent. Your job is to independently
audit a research report for accuracy and citation validity.

Read the file research_draft.md.

For EACH cited source in the report:
1. Search for the paper by its exact title using WebSearch
2. Check: does this paper actually exist?
..."
```

Example from the step 6 orchestrator:
```
Use the Agent tool with this prompt:

"You are a research searcher agent. Your ONLY job is finding and extracting
information. You do NOT evaluate or synthesize.

Research question: [THE USER'S QUESTION]

Instructions:
1. Decompose into 3-5 sub-questions
2. For each sub-question, search using your tools
..."
```

### Tool Restriction Per Agent

Each agent gets only the tools it needs. This is specified in the dispatch and controlled by the skill's `allowed-tools` field:

| Agent | Tools Granted | Why |
|-------|--------------|-----|
| Orchestrator | `Agent`, `Read`, `Write` | Only dispatches other agents, doesn't research |
| Searcher | `WebSearch`, `WebFetch`, `Read`, `Write`, `mcp__research-tools__search_arxiv`, `mcp__research-tools__search_semantic_scholar` | Needs all search tools to find papers |
| Critic | `WebSearch`, `WebFetch`, `Read`, `Write` | Needs web access to verify citations, but not arXiv/Semantic Scholar (it evaluates, not searches) |
| Synthesizer | `Read`, `Write` | Only reads input files and writes the report. No search tools -- it works with what it's given |
| Verifier (step 5) | `WebSearch`, `WebFetch`, `Read` | Can search to verify citations but cannot write new research |

Tool restriction serves two purposes: (1) it prevents agents from doing things outside their role (synthesizer shouldn't be searching), and (2) it reduces the tool-selection surface, making the agent more focused.

### Why Separate Context Windows Matter

Three reasons agents use separate context windows:

1. **Independence** -- the verification agent hasn't seen the reasoning that produced the claims. It approaches verification with fresh eyes, not confirmation bias.
2. **Specialization** -- each agent uses its full context window for ONE task instead of splitting attention across search + evaluation + writing.
3. **Isolation** -- if the searcher makes a mistake, it doesn't propagate through shared context. The critic sees only the output and evaluates it on its merits.

This is not just architectural preference. Self-verification in the same context is measurably weaker than independent verification. Claude has already "committed" to its claims in the context window. A new context window has no such commitment.

---

## 8. Team Orchestration Pattern

### The Pipeline: Orchestrator --> Searcher --> Critic --> Synthesizer

```
[User's research question]
         |
         v
  +------------------+
  |   ORCHESTRATOR    |  (your session -- dispatches, doesn't research)
  +------------------+
         |
         | Phase 1: spawn searcher
         v
  +------------------+
  |    SEARCHER       |  (separate process)
  |                   |
  | - Decompose       |
  | - Search arXiv    |
  | - Search S2       |
  | - WebSearch       |
  | - 2-3 rounds      |
  | - Extract claims  |
  +------------------+
         |
         | writes searcher_output.md
         v
  +------------------+
  |     CRITIC        |  (separate process)
  |                   |
  | - Read findings   |
  | - Rate sources    |
  | - Find conflicts  |
  | - Check halluc.   |
  | - Identify gaps   |
  +------------------+
         |
         | writes critic_output.md
         v
  +------------------+
  |   SYNTHESIZER     |  (separate process)
  |                   |
  | - Read both files |
  | - Remove bad data |
  | - Theme grouping  |
  | - Quality ratings |
  | - Write report    |
  +------------------+
         |
         | writes final_report.md
         v
  +------------------+
  |   ORCHESTRATOR    |  (reads final_report.md, quality check, present)
  +------------------+
         |
         v
  [Final report to user]
```

### File-Based Communication Protocol

Agents cannot share memory. They communicate exclusively through files on disk.

**The protocol:**
1. Orchestrator spawns Searcher with the research question in its prompt.
2. Searcher writes `searcher_output.md` and exits.
3. Orchestrator spawns Critic, telling it to read `searcher_output.md`.
4. Critic writes `critic_output.md` and exits.
5. Orchestrator spawns Synthesizer, telling it to read both files.
6. Synthesizer writes `final_report.md` and exits.
7. Orchestrator reads `final_report.md`, does a final quality check, and presents to the user.

**Why files, not shared context:**
- **Clean inputs.** The critic sees the searcher's OUTPUT, not its reasoning. No access to "I searched for X because I thought Y" -- just the facts.
- **Debuggability.** Each intermediate file is inspectable. If the final report is bad, you can check: is `searcher_output.md` missing sources? Did `critic_output.md` flag the right issues? Did the synthesizer ignore the critic?
- **Replaceability.** You can rerun just the synthesizer with the same inputs. You can swap in a different critic. Each stage is independently testable.

### Why Sequential (Not Parallel) for This Use Case

The pipeline is sequential because each stage depends on the previous:
- The Critic cannot evaluate sources until the Searcher has found them.
- The Synthesizer cannot write a report until both the Searcher's findings and the Critic's assessment exist.

**When parallel makes sense:** If you have multiple independent search tasks (e.g., one sub-question per searcher), you can dispatch multiple searchers in parallel. The TEACHING.md suggests this as an advanced pattern: "Instead of one searcher, dispatch one per sub-question. They run concurrently, each specializing in one aspect."

### How to Customize the Team Structure

The three-role pattern (Searcher, Critic, Synthesizer) is the default. The TEACHING.md describes several advanced patterns for teams that want higher scores:

**Parallel Searchers:** Dispatch one searcher per sub-question. Each specializes in one aspect and writes to its own file. The critic then reads all searcher files.

**Devil's Advocate:** Add an agent whose ONLY job is to find contradictory evidence. "For each claim in the report, search for papers that disagree."

**Methodology Specialist:** An agent that evaluates study designs. "For each cited paper, assess: sample size, methodology rigor, potential biases."

**Editor:** A final agent that polishes the synthesizer's output for readability and formatting.

**Customization questions the TEACHING.md raises:**
1. Should the critic see the searcher's reasoning, or just its outputs? (File-based = outputs only. Shared context = everything.)
2. Should agents run sequentially or in parallel?
3. What happens when the critic flags a problem? (Drop the claim? Re-search? Note uncertainty?)
4. Does every question need the same team? (A comparison question might need a different structure than a survey question.)

---

## Appendix A: The RACE Benchmark

The evaluation system uses the **RACE framework** from Deep Research Bench, implemented in `benchmark/evaluate.py`.

**Dimensions and weights:**

| Dimension | Weight | What It Measures |
|-----------|:------:|-----------------|
| Comprehensiveness | 30% | Coverage breadth, data support, multiple perspectives, diverse sources, acknowledged gaps |
| Insight | 35% | Analysis depth, causal reasoning, trade-off comparison, source conflict identification, forward-looking assessment |
| Instruction Following | 20% | Addresses all parts of the question, scope adherence |
| Readability | 15% | Structure, clarity, logical flow |
| Citation Bonus | +10% | Verifiable sources with real URLs/papers |

**Two scoring modes:**
- `--quick` (heuristic): instant, no API call. Applies a source-grounding factor -- outputs without real URLs are penalized, outputs with evidence quality ratings are boosted.
- Default (LLM-as-judge): uses Claude Sonnet to score each dimension. Authoritative for final evaluation.
- With `--reference`: calibrates against a reference report.

**Usage:**
```bash
python3 benchmark/evaluate.py --input output.md --quick --question "your question"
python3 benchmark/evaluate.py --input output.md --question "your question"
python3 benchmark/evaluate.py --input output.md --reference benchmark/reference/test-2-a2a-mcp.md
```

## Appendix B: Complete File Tree

```
research-agent-workshop/
|
+-- CLAUDE.md                              # Repo-level context (describes the whole workshop)
+-- README.md                              # Workshop overview and setup
+-- BUILD.md                               # Second-half: build + compete instructions
+-- DEMO.md                                # First-half: demo + teach instructions
+-- verify.sh                              # Setup verification script
+-- requirements.txt                       # Python deps: anthropic, fastmcp
|
+-- step-1-context/
|     +-- CLAUDE.md                        # The artifact: research identity context
|     +-- TEACHING.md                      # Design principles for context
|
+-- step-2-skill/
|     +-- .claude/skills/deep-research/
|     |     +-- SKILL.md                   # The artifact: one-pass research methodology
|     +-- TEACHING.md                      # Design principles for skills
|
+-- step-3-tool/
|     +-- mcp-servers/
|     |     +-- arxiv_server.py            # The artifact: FastMCP server with arXiv + Semantic Scholar
|     +-- TEACHING.md                      # Design principles for custom tools
|
+-- step-4-iterative/
|     +-- .claude/skills/deep-research/
|     |     +-- SKILL.md                   # The artifact: iterative research with loop logic
|     +-- TEACHING.md                      # Design principles for iteration
|
+-- step-5-verification/
|     +-- .claude/skills/deep-research/
|     |     +-- SKILL.md                   # Updated: research + dispatch verifier
|     +-- .claude/skills/verify-research/
|     |     +-- SKILL.md                   # The artifact: verification agent skill
|     +-- TEACHING.md                      # Design principles for verification agents
|
+-- step-6-team/
|     +-- .claude/skills/orchestrator/
|     |     +-- SKILL.md                   # The artifact: team orchestrator
|     +-- .claude/skills/searcher/
|     |     +-- SKILL.md                   # The artifact: searcher agent
|     +-- .claude/skills/critic/
|     |     +-- SKILL.md                   # The artifact: critic agent
|     +-- .claude/skills/synthesizer/
|     |     +-- SKILL.md                   # The artifact: synthesizer agent
|     +-- TEACHING.md                      # Design principles for team orchestration
|
+-- benchmark/
|     +-- evaluate.py                      # RACE framework scorer
|     +-- verify_staircase.py              # Validates scoring progression
|     +-- practice/                        # Practice problems
|     +-- test/                            # Test problems
|     +-- reference/                       # Reference reports for calibration
|     +-- criteria/                        # Scoring rubrics
|     +-- deepresearch-bench/              # Adapter for full 100-task bench
|
+-- test-run/
|     +-- run_steps.sh                     # End-to-end step runner
|     +-- mcp-config.json                  # MCP server config for test runs
|
+-- docs/
      +-- architecture.md                  # This document
```
