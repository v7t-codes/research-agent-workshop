# Session Plan — Build Your Research Agent

> IISc | Wed 4–7 PM | ~50 CS students
> Presenters: Rachitt (opens + closes) · Vishwajit (steps 1-3, build briefing)

---

## The arc

```
4:00  Hook (Rachitt, 5 min)
4:05  Teach: Steps 1-3 (Vishwajit, 20 min)
4:25  Teach: Steps 4-6 (Rachitt, 25 min)
4:50  Score staircase reveal (both, 5 min)
4:55  Build briefing (Vishwajit, 10 min)
5:05  ── HACK SESSION ──────────────────── (~115 min)
       Task 1: CLAUDE.md         (15 min)
       Task 2: SKILL.md          (30 min)
       Task 3: MCP server        (40 min)
       Task 4: Agent (optional)  (remaining)
7:00  Top 3 teams present (Rachitt, 15 min)
```

---

## Part 1: Hook (Rachitt, 5 min)

Show the finished product (step 6 output) live. Score it.
Then show raw Claude on the same question. Score it.

> "Same model. Same question. 20 to 93. Six engineering concepts between them.
> You're going to see each one in the next 45 minutes. Then you build your own."

---

## Part 2: Vishwajit's talk — Steps 1, 2, 3

### Step 1: Context (5 min)

**What to show:** Open `step-1-context/CLAUDE.md`.

**What to say:**

> "Before you tell Claude HOW to do the work, tell it WHO it's working for.
> This is 20 lines of markdown. It's not a prompt — it's an identity.
> Watch what it changes."

Walk through the five fields:
- **Domain** — what field, what conferences, what kind of evidence you trust
- **Preferences** — citation format, source priority, how to handle conflicting numbers
- **Constraints** — what never to do (never cite without attribution)

Run it. Show the score. Point out: terminology is tighter, citation format matches, sources are more credible.

> "Five sentences change the output. This is the cheapest line on the staircase."

**The principle to leave them with:**
> "Context answers WHO. Not HOW. Before you teach Claude your methodology, tell it who it's working for."

---

### Step 2: Skill (7 min)

**What to show:** Open `step-2-skill/.claude/skills/deep-research/SKILL.md`.

Walk through the three parts:

**Frontmatter — the interface:**
```yaml
name: deep-research
description: >-
  Use when user says "research", "investigate", "deep dive"...
allowed-tools: WebSearch WebFetch Read Write
```

Point out: `description` is what Claude reads to decide when to invoke the skill. Write trigger phrases. If the description is vague, Claude doesn't know when to use it.

**Methodology — the recipe:**

Walk through Decompose → Search → Extract → Cross-reference → Synthesize.

> "Notice: Decompose comes before Search. Claude breaks the question into sub-questions
> and states what a good answer looks like — BEFORE it searches anything.
> That forces coverage. Without this, Claude searches for the obvious thing and stops."

**Output format — the most underrated part:**

Show the output format spec block (thesis → key findings → analysis by theme → conflicts table → open questions → sources).

> "If you don't specify structure, you get an essay. An essay is not a research report.
> The output format is not decoration — it's half the methodology."

Run it. Show the score jump. Point out: structure and numbers are exactly what RACE measures.

**The principle:**
> "A skill is a recipe, not a chef. It follows instructions top to bottom, once.
> It doesn't decide to go back and search again. That's step 4.
> It doesn't dispatch another process. That's step 5.
> Know what a skill IS so you know what to put in it."

---

### Step 3: Tool design (8 min) ← most important teaching moment

**What to show:** Open `step-3-tool/mcp-servers/arxiv_server.py`. The WHOLE file.

> "This is 50 lines of Python. It gives Claude access to every paper on arXiv.
> Let me show you why that's different from WebSearch."

**The comparison:**

```
WebSearch("scaling laws MoE models")
→ Google results: blog summaries, Medium posts, tweet threads
→ Claude writes: "According to various sources, MoE models..."

search_arxiv("scaling laws mixture of experts")
→ Paper titles, abstracts, authors, dates, URLs
→ Claude writes: "Chen et al. (2024) find that..."
```

> "The quality of the data determines the quality of the report.
> WebSearch gives you what's popular. A custom tool gives you what's accurate."

**The anatomy — three things that matter:**

Point at the code as you explain:

```python
@mcp.tool                          # 1. Register it
def search_arxiv(                  # 2. The signature
    query: str,                    #    Claude uses type hints
    max_results: int = 10          #    to know what to pass
) -> str:
    """Search arXiv for papers...  # 3. The docstring
    Returns: title, authors...        Claude reads this to decide
    """                               WHEN and HOW to use it
```

> "The docstring IS Claude's interface. Not the code. Not the return value.
> Claude reads the docstring. Claude never sees the implementation.
> Write it for Claude, not for humans."

**The three design questions:**

Before building any tool, answer:
1. **What does Claude need that it can't get from WebSearch?** (structured data, verified sources, specific APIs)
2. **What format should the return be in?** (structure > prose — Claude reasons about tables and lists, not paragraphs)
3. **What parameters does Claude need to specify?** (fewer is better, defaults are your friend)

**Bad tool vs good tool:**

```python
# Bad: Claude gets HTML soup
def get_paper_info(url: str) -> str:
    """Fetch a webpage."""
    return requests.get(url).text  # 40KB of HTML

# Good: Claude gets structured data
def search_arxiv(query: str, max_results: int = 10) -> str:
    """Search arXiv. Returns title, authors, abstract, date, URL per paper."""
    # Parses XML, extracts fields, returns clean markdown
```

**How to connect it:**

Show `.claude/settings.json`:
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

And the `allowed-tools` line in SKILL.md:
```yaml
allowed-tools: WebSearch WebFetch Read Write mcp__research-tools__search_arxiv
```

> "The skill says WHAT to do. The tool provides HOW to do it.
> Swap the tool without changing the methodology. Swap the methodology without changing the tool."

Run it. Watch Claude call `search_arxiv`. Show real paper titles in the output. Score it.

**The principle:**
> "You just upgraded Claude's senses. Before, it could only see what Google shows.
> Now it can see structured academic data. 15 lines of Python.
> The MCP ecosystem means you can connect anything — APIs, databases, your own data.
> That's what you're going to build."

---

## Part 3: Rachitt's talk — Steps 4, 5, 6

(see DEMO.md for Rachitt's sections)

---

## Part 4: Score staircase reveal (5 min)

Show all 7 scores:
```
Step 0 (raw):           20/100  ─┐
Step 1 (context):       21/100   ├─ No tools
Step 2 (skill):         37/100  ─┘
Step 3 (tool):          58/100  ─┐
Step 4 (iterative):     53/100  ─┘  Tools  (heuristic dip — LLM scores correctly)
Step 5 (verification):  90/100  ─┐
Step 6 (team):          93/100  ─┘  Verification + Team
```

> "Same model. Six concepts. Now you build yours."

---

## Part 5: Build Briefing (Vishwajit, 10 min)

### What they get

```
scaffold/
  CLAUDE.md.template      — blank with field hints
  SKILL.md.template       — section headers only, no methodology
  mcp_skeleton.py         — FastMCP setup + one placeholder tool
```

**Show them each file.** They are intentionally incomplete. That's the point.

### What they must write

| File | What they write | What they must NOT do |
|------|----------------|----------------------|
| `CLAUDE.md` | Their domain, preferences, constraints | Copy the example exactly |
| `SKILL.md` | Their methodology, output format, trigger phrases | Copy the step-2 SKILL.md |
| `mcp_skeleton.py` | At least one working tool | Copy arxiv_server.py |

> "The example files in step-1, step-2, step-3 — you can read them.
> You can use them as a reference. You cannot copy them into your working directory.
> The prompting IS the work. You won't learn it by copy-pasting."

### The three tasks (in order)

**Task 1 — CLAUDE.md (15 min)**
Pick your group's research domain. Fill in the template with real answers:
- What field are you in? What conferences do you read?
- What citation format do you prefer?
- What sources do you trust? What should Claude never do?

Test it: run Claude on a practice question. Does the output feel like it's coming from someone who knows your field?

**Task 2 — SKILL.md (30 min)**
Design your research methodology. You need:
- A decompose-first step
- At least 3 search/extraction steps
- An output format spec that specifies every section
- Quality rules (what counts as a claim? what's not good enough?)

Test it: run on practice problem 2 (Q1 2026 foundation models). It should struggle — that's expected. That's what the tool is for.

**Task 3 — MCP server (40 min)**
Build one tool that gives Claude access to a data source it can't reach via WebSearch.

API options (all free, no auth required for basic access):
- **Wikipedia** — summaries, disambiguation, links
- **OpenAlex** — 250M academic papers, fully open
- **PubMed** — biomedical papers (useful for test problem 3)
- **CrossRef** — DOI verification, publication metadata
- **HackerNews** — tech discussion (Algolia API, no auth)
- **GitHub** — repos, issues, READMEs (rate-limited but works)

Your tool must:
- Return structured data (not raw HTML)
- Have a docstring Claude can use to decide when/how to call it
- Handle errors (return a message, don't crash)

Connect it. Update your SKILL.md to include the tool. Re-run on practice problem 2. Score it.

**Task 4 — Agent (optional, for fast groups)**
Design a verification or critic agent. What should an independent Claude process check?
Write the agent's instructions (another SKILL.md). What does it look for? What can it fix?

### Scoring

```bash
# During development (instant)
python3 benchmark/evaluate.py --input output.md --quick --question "your question"

# Before final submission (LLM judge)
python3 benchmark/evaluate.py --input output.md --question "your question"
```

Practice problems: in `benchmark/practice/`. Use these while building.
Test problems: in `benchmark/test/`. Run once when you're ready. Average of 3 = your score.

### What wins

Not just the highest score. The top 3 present. Audience votes for "best design."

Best design = most interesting engineering choice. A creative tool that doesn't quite work scores better for design than a copy of arxiv_server.py that does.

---

## Part 6: Top 3 teams present (Rachitt, 15 min)

Each team: 2-3 min.
1. Show your score progression. Where was the biggest jump?
2. What tool did you build? Show the function signature and docstring.
3. One thing that surprised you.

Audience vote: best design (separate from score).
