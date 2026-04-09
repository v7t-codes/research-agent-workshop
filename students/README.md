# Build Session — Your Research Agent

## Setup (do this first, takes 5 minutes)

```bash
# 1. Clone the repo
git clone https://github.com/v7t-codes/research-agent-workshop
cd research-agent-workshop

# 2. Install Python dependency
pip install fastmcp

# 3. Log in to Claude Code
claude auth login
# Opens browser → log in with your claude.ai account → done

# 4. Confirm everything works
./verify.sh
```

---

## Your working directory

```bash
cp -r students/template students/your-name
cd students/your-name
```

You now have:
```
students/your-name/
  CLAUDE.md                              ← Task 1
  .claude/
    settings.json                        ← tells Claude Code about your MCP server
    skills/
      deep-research/
        SKILL.md                         ← Task 2
  mcp_server.py                          ← Task 3
```

Run `claude` from inside your folder. It auto-loads your CLAUDE.md and skills.

---

## The three tasks

### Task 1 — CLAUDE.md (15 min)

Open `CLAUDE.md`. Fill it in for your group's research domain.

You need to answer:
- What field are you in? (be specific — not "computer science", say "distributed systems" or "NLP")
- What conferences and journals do you read?
- What kind of evidence do you trust? (benchmarks? proofs? case studies?)
- What citation format?
- What should Claude never do?

**Test it:**
```bash
claude
# Type: "Research: What are the main approaches to [your topic]?"
# Does the output sound like it comes from your field?
```

---

### Task 2 — SKILL.md (30 min)

Open `.claude/skills/deep-research/SKILL.md`. Write your research methodology.

You must include:
- **Trigger phrases** — when does this skill activate? (e.g., "when user says research, investigate...")
- **Decompose step** — how do you break a question into sub-questions *before* searching?
- **Search strategy** — what do you search for? How many sources per sub-question?
- **Extraction rules** — what must every claim include to be accepted?
- **Output format** — every section named and described (thesis, findings, analysis by theme, conflicts table, sources)
- **Quality rules** — what's not acceptable?

**Test it:**
```bash
claude
# Type: "Research: What new foundation models were released in Q1 2026?"
# This should struggle without tools — that's expected. It forces you to build Task 3.
```

---

### Task 3 — MCP server (40 min)

Open `mcp_server.py`. Before writing code, write down answers to these three questions:

1. What does Claude need that it can't get from WebSearch?
2. What format should the return be? (structured lists/tables beat paragraphs)
3. What parameters does Claude need to pass?

Then implement. The placeholder tool at the top of the file shows the pattern.

**Free APIs (no authentication required):**

| API | Best for | Example URL |
|-----|---------|-------------|
| OpenAlex | 250M academic papers, fully open | `api.openalex.org/works?search=query` |
| Wikipedia | Background context, disambiguation | `en.wikipedia.org/api/rest_v1/page/summary/title` |
| PubMed/NCBI | Biomedical papers | `eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` |
| CrossRef | DOI verification, citation counts | `api.crossref.org/works?query=...` |
| HackerNews | Tech discussion threads | `hn.algolia.com/api/v1/search?query=...` |
| GitHub | Repos, READMEs, issues | `api.github.com/search/repositories?q=...` |
| arXiv | Already in the demo — pick something different | — |

**Your tool must:**
- Return structured text (markdown tables or bullet lists — not raw HTML)
- Have a docstring that tells Claude *when* to use it vs WebSearch
- Return an error message on failure (never crash with an exception)

**Test your server starts:**
```bash
python3 mcp_server.py
# Should start without errors. Ctrl+C to stop.
```

**Connect it to Claude Code:**

`.claude/settings.json` already points to `mcp_server.py`. Just run `claude` and your tool will be available.

Update your SKILL.md `allowed-tools` line to include your tool:
```yaml
allowed-tools: WebSearch WebFetch Read Write mcp__my-tools__your_tool_name
```

(Replace `my-tools` with whatever name is in your `mcp_server.py`: `mcp = FastMCP("my-tools")`)

**Test it works:**
```bash
claude
# Type: "Research: What new foundation models were released in Q1 2026?"
# Watch Claude call your tool. Does the output improve?
```

---

### Task 4 — Verification or team agent (optional, if you're ahead)

If you've completed Tasks 1-3, look at `demo/step-5/` and `demo/step-6/` for reference. Design your own verification or team structure — different from the examples.

---

## Practice problems

Test your agent against these (in `benchmark/practice/`):

| Problem | What it tests |
|---------|--------------|
| `practice-1.md` | Warmup — well-covered in training data |
| `practice-2.md` | **Use this one** — Q1 2026 models, forces real-time tools |
| `practice-3.md` | MoE scaling laws — conflicting results, forces verification |

```bash
# Run your agent on a practice problem
claude
# Copy the question from benchmark/practice/practice-2.md and type it
```

---

## Submitting for the competition

**When you're ready (last 15 min of session):**

```bash
# From repo root
git checkout -b student/your-name
git add students/your-name/
git status
# Confirm you only see these files:
#   students/your-name/CLAUDE.md
#   students/your-name/.claude/settings.json
#   students/your-name/.claude/skills/deep-research/SKILL.md
#   students/your-name/mcp_server.py

git commit -m "your-name submission"
git push origin student/your-name
```

Then open a pull request on GitHub. Title: your group name.

**That's it.** You don't run the scorer. The presenters score all submissions after you push.

---

## What exactly gets scored

The presenters run your agent against 3 unseen research questions.
Your agent is scored on **RACE** — see `SCORING.md` for what that means.

What matters:
- Your `CLAUDE.md` gives Claude the right identity
- Your `SKILL.md` gives Claude a methodology that produces structured, evidence-based reports
- Your `mcp_server.py` gives Claude access to real external sources

The competition score is the average across all 3 test problems.

---

## Rules

- You can look at `demo/step-1/` through `demo/step-6/` as reference
- You **cannot** copy those files into your folder — write your own
- Your `mcp_server.py` must implement at least one working tool (not the arxiv server verbatim)
- Group size: 2-3 people
