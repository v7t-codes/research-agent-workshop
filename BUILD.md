# Build Session — Research Agent Hack

You have ~90 minutes. Work in groups of 2-3.

**Goal:** Build a research agent that scores as high as possible on 3 unseen test problems.
**Rule:** You write your own files. The `scaffold/` directory is your starting point — not the `step-*/` directories.

---

## What you're building

```
your-agent/
  CLAUDE.md                          ← Task 1: you write this
  .claude/
    settings.json                    ← copy from scaffold, edit server name
    skills/
      deep-research/
        SKILL.md                     ← Task 2: you write this
  mcp_server.py                      ← Task 3: you write this (from scaffold/mcp_skeleton.py)
```

The `step-*/` directories are reference material. Read them to understand the pattern. Don't copy them.

---

## Task 1 — CLAUDE.md (15 min)

Open `scaffold/CLAUDE.md`. Fill it in for your group's domain.

Specific questions to answer:
- What field are you in? Which subfield specifically?
- What conferences/journals do you read? (NeurIPS, CVPR, SIGMOD — be specific)
- What kind of evidence do you trust? (benchmarks? proofs? case studies?)
- What citation format? (Author Year inline? Numbered? IEEE?)
- What should Claude never do?

**Test it:**
```bash
claude
# Ask: "Research: What are the main approaches to [your topic]?"
# Does the output feel like it comes from your domain?
```

Score it:
```bash
python3 benchmark/evaluate.py --input output.md --quick --question "your question"
```

---

## Task 2 — SKILL.md (30 min)

Open `scaffold/.claude/skills/deep-research/SKILL.md`. Fill in all the `[TASK 2*]` sections.

You need to design:
- **Trigger phrases** — when should Claude invoke this skill?
- **Decompose step** — how do you break a question before searching?
- **Search strategy** — what do you search for? how many sources per sub-question?
- **Extraction rules** — what must every claim include to count?
- **Output format** — every section named and described
- **Quality rules** — what's not acceptable? what should Claude always flag?

Copy this to your working directory:
```bash
cp scaffold/.claude/skills/deep-research/SKILL.md .claude/skills/deep-research/SKILL.md
# (then edit it — it's your file now)
```

**Test it on practice problem 2** — it should struggle on "Q1 2026 foundation models" since that requires real-time data. That's fine. That's what the tool fixes.

```bash
claude
# Ask: "Research: What new foundation models were released in Q1 2026?"
python3 benchmark/evaluate.py --input output.md --quick --question "..."
```

---

## Task 3 — MCP server (40 min)

**Before writing code, answer the three design questions:**

1. What does Claude need that it **can't get from WebSearch?**
2. What format should the return be in? (structure > prose)
3. What parameters does Claude need to pass?

Then open `scaffold/mcp_skeleton.py`. Replace the `placeholder_tool` with your real tool.

**Free APIs to choose from:**

| API | Best for | Docs |
|-----|---------|------|
| OpenAlex | 250M academic papers, open access | `api.openalex.org/works?search=query` |
| PubMed/NCBI | Biomedical papers | `eutils.ncbi.nlm.nih.gov/entrez/eutils/` |
| CrossRef | DOI verification, citation counts | `api.crossref.org/works?query=...` |
| Wikipedia | Background knowledge, disambiguation | `en.wikipedia.org/api/rest_v1/page/summary/` |
| HackerNews | Tech discussions, community context | `hn.algolia.com/api/v1/search?query=...` |
| GitHub | Code, repos, README content | `api.github.com/search/repositories` |
| arXiv | Already done — pick something else | — |

**Your tool must:**
- Return structured text (markdown tables or lists, not HTML)
- Have a useful docstring (write it for Claude, not for humans)
- Handle errors without crashing (return a message)

Copy skeleton to working directory and implement:
```bash
cp scaffold/mcp_skeleton.py mcp_server.py
# Edit mcp_server.py — implement your tool
python3 mcp_server.py  # test it runs
```

Connect to Claude Code — add to `.claude/settings.json`:
```json
{
  "mcpServers": {
    "my-tools": {
      "command": "python3",
      "args": ["mcp_server.py"]
    }
  }
}
```

Update your SKILL.md `allowed-tools` to include your tool:
```yaml
allowed-tools: WebSearch WebFetch Read Write mcp__my-tools__your_tool_name
```

Test:
```bash
claude
# Ask: "Research: What new foundation models were released in Q1 2026?"
# Watch Claude call your tool. Check the output.
python3 benchmark/evaluate.py --input output.md --quick --question "..."
```

---

## Task 4 — Verification or team agent (optional)

If you've completed tasks 1-3 and your score is above 60, consider adding a verification or team structure.

**Verification agent:** A second Claude process that checks your output.
- What does it look for? Hallucinated papers? Unverifiable claims? Wrong numbers?
- Write it as a second SKILL.md in `.claude/skills/verify-research/`
- Look at `step-5-verification/.claude/skills/verify-research/SKILL.md` as reference

**Team structure:** Searcher + Critic + Synthesizer, each specialized.
- Each has its own SKILL.md in its own folder
- The orchestrator dispatches them via the `Agent` tool
- Look at `step-6-team/.claude/skills/` as reference

---

## Scoring

```bash
# While building (instant, no API call)
python3 benchmark/evaluate.py --input output.md --quick --question "your question"

# Before final submission (LLM judge, more accurate)
python3 benchmark/evaluate.py --input output.md --question "your question"
```

**Practice problems** (build against these, they're in `benchmark/practice/`):
- `practice-1.md` — NAS comparison — warmup, well-covered in training data
- `practice-2.md` — Q1 2026 foundation models — **use this one mainly**, forces tools
- `practice-3.md` — MoE scaling laws — conflicting results, forces verification

**Test problems** (run once when ready, scored for competition):
```bash
# Each group runs these once and records their scores
claude --input-file benchmark/test/test-1.md > test-1-output.md
python3 benchmark/evaluate.py --input test-1-output.md --quick --question "$(sed -n '3p' benchmark/test/test-1.md)"

claude --input-file benchmark/test/test-2.md > test-2-output.md
python3 benchmark/evaluate.py --input test-2-output.md --quick --question "$(sed -n '3p' benchmark/test/test-2.md)"

claude --input-file benchmark/test/test-3.md > test-3-output.md
python3 benchmark/evaluate.py --input test-3-output.md --quick --question "$(sed -n '3p' benchmark/test/test-3.md)"
```

Competition score = average of all 3 test problem scores.

---

## What wins

**Highest score** = competition winner.

**Best design** = audience vote. The three highest-scoring teams each present for 2-3 min:
1. Show your score progression (where was the biggest jump?)
2. Show your tool: function signature + docstring. Why did you choose this API?
3. One thing that surprised you.

A creative tool that scores 70 can beat a copy-paste step-6 that scores 80 on best design.

---

## Common pitfalls

**"My SKILL.md is not getting invoked"** — check the `description` field. Does it include trigger phrases that match what you're typing?

**"My MCP server isn't connecting"** — run `python3 mcp_server.py` in a separate terminal first to verify it starts. Check `.claude/settings.json` for typos.

**"Score didn't improve after adding my tool"** — check your SKILL.md `allowed-tools`. The tool name must match exactly: `mcp__my-tools__your_tool_name`.

**"Claude isn't using my tool"** — rewrite the docstring. Explain what the tool returns and when to prefer it over WebSearch.

**"Score went down after step 4"** — normal on the heuristic. The iterative skill's process text shifts keyword patterns. Use `--question` flag and LLM scoring for accurate comparison.
