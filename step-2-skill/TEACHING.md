# Step 2: Skill (SKILL.md) — Design Principles

## What it physically is

A `SKILL.md` file in `.claude/skills/<skill-name>/`. Claude discovers it and follows the instructions when triggered. It's persistent on disk, reusable across sessions, and portable across Claude Code, Cursor, Codex, and Copilot.

## The design principle: A skill is a recipe, not a chef

A skill is **ONE PASS** — Claude follows the instructions top to bottom. It doesn't decide to go back and search again. It doesn't evaluate its own output. It's a recipe: do step 1, then step 2, then step 3, done.

**Why this distinction matters:** If you want Claude to loop (search → evaluate → refine → repeat), that's an **iterative skill** (step 4). If you want Claude to dispatch another process, that's an **agent** (step 5). Understanding what a skill IS helps you know what to put in it.

## Anatomy of a SKILL.md

```yaml
---
name: deep-research
description: >-
  Researches any topic using multi-step web search with source verification.
  Use when user says "research", "investigate", "deep dive", or "what do we know about".
allowed-tools: WebSearch WebFetch Read Write
---
```

### The frontmatter matters

- **name**: How Claude identifies this skill
- **description**: Claude uses this to decide when to invoke the skill. Write trigger phrases: "Use when user says X, Y, Z"
- **allowed-tools**: What tools the skill can use. This is how you give a skill access to WebSearch, your MCP server, etc.

### The body: methodology

The body is the actual research methodology. Structure it as numbered steps:

1. **Decompose** — break the question into sub-questions
2. **Search** — for each sub-question, search
3. **Extract** — pull specific claims with numbers
4. **Cross-reference** — find agreements, conflicts, gaps
5. **Synthesize** — write the report

Each step should have clear instructions and quality criteria. "Search for papers" is vague. "Search for papers, prioritizing peer-reviewed > preprints > blogs, flagging anything older than 12 months" is actionable.

## How to design a research methodology

The key insight: **decompose before you search.**

Bad: "Search for information about X and write a report."
Good: "First, break X into 3-5 searchable sub-questions. For each, state what a good answer looks like. Then search for each sub-question separately."

Why? Decomposition forces Claude to think about coverage BEFORE searching. It prevents the "search for the obvious thing and stop" failure mode.

### The output format is part of the methodology

Specify exactly what the output should look like:
- Thesis sentence upfront
- Findings organized by theme (not by source)
- Source conflicts table (Claim | Source A | Source B | Assessment)
- Open questions section
- Full reference list at the end

If you don't specify output format, Claude will write a generic essay.

## What a skill is NOT

- **Not a prompt** — prompts die when the chat ends. Skills persist on disk.
- **Not an agent** — agents are separate processes. Skills run in your session.
- **Not a tool** — tools give Claude new capabilities. Skills tell Claude HOW to use capabilities.

## Score impact

| | Before (step 1) | After (step 2) |
|--|--|--|
| **What changes** | Unstructured essay, no methodology | Structured report: thesis, findings with numbers, conflicts table, citations |
| **What doesn't change** | Still from training data, still one pass, no real-time sources | Same — but now the training data is organized into a useful report |

The jump is significant because structure and specificity are exactly what RACE measures. The methodology forces Claude to be specific ("cite at least two papers with results") rather than vague.
