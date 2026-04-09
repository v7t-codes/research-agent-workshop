# Workshop Demo Script

> Presenter guide for the first half. Each step: run the agent, show the score, teach the principle.

## Setup (before workshop)

- Terminal: font 18pt+, dark theme, half-screen code / half-screen terminal
- Pre-run `./verify.sh` to confirm setup
- Have `test-run/outputs/` and `test-run/scores/` as pre-computed fallback
- MCP server tested: `python3 step-3-tool/mcp-servers/arxiv_server.py` starts cleanly

## Demo Question

> "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."

From Deep Research Bench, query #69 (Software Development). This question is ideal because:
- Relevant to the audience (they're learning MCP today)
- Requires current 2025-2026 data
- Has genuine technical depth
- Has a reference report for calibration

---

## The Hook (5 min) — Rachitt

### Slide 1: The Thesis (90 seconds)

> "Same Opus 4.5, raw: 30.5% on OSWorld. With a harness: 66.3%. The system around the model matters more than the model itself."

One slide. Show the number. Move on.

### Live demo: The finished product (3 min)

Run the fully-built agent (step 6) on the demo question:

```bash
# From the workshop directory
claude
# Then: "Research: Provide a detailed analysis of A2A vs MCP..."
```

While it runs, narrate:
- "Watch — it's dispatching a searcher agent. Separate process."
- "Now the critic. Fresh eyes, independent verification."
- "Now the synthesizer. Clean context, focused on writing."

Show the output. Point out: real paper citations, source conflicts table, structured analysis.

### Show the score

```bash
python3 benchmark/evaluate.py --input final_report.md --quick --question "Provide a detailed analysis of A2A vs MCP..."
```

**Expected: ~85-95**

### Then show raw Claude

```bash
echo "Provide a detailed analysis of A2A vs MCP..." | claude -p --model sonnet --disallowed-tools "WebSearch,WebFetch,Agent"
```

**Expected: ~40-55 (LLM) / ~20 (heuristic)** — decent prose but shallow, no verified sources. Heuristic penalizes missing URLs.

> "Six things make the difference. You're going to see each one."

---

## Step 1: Context (5 min) — Vishwajit

### What to show
Open the CLAUDE.md file:
```bash
cat step-1-context/CLAUDE.md
```

### Key talking point
> "This is 20 lines of markdown. It tells Claude WHO it's working for. Your field, your preferred sources, your citation format. Same model — different context — different output."

### Run it
```bash
echo "Provide a detailed analysis of A2A vs MCP..." | claude -p --model sonnet --system-prompt "$(cat step-1-context/CLAUDE.md)" --disallowed-tools "WebSearch,WebFetch,Agent"
```

### Score it
```bash
python3 benchmark/evaluate.py --input output.md --quick --question "Provide a detailed analysis of A2A vs MCP..."
```

### What to point out
- Terminology is more precise (uses "protocol", not "system")
- Citation format matches specification
- Right conferences/sources mentioned
- BUT: still no real-time data, still one pass

### Design principle
> "Context answers WHO, not HOW. Before teaching Claude methodology, tell it who it's working for. Five sentences change the output."

Open TEACHING.md: `step-1-context/TEACHING.md`

---

## Step 2: Skill (7 min) — Vishwajit

### What to show
Open the SKILL.md:
```bash
cat step-2-skill/.claude/skills/deep-research/SKILL.md
```

Walk through the structure:
1. Frontmatter (name, description, allowed-tools)
2. Decompose → Search → Extract → Cross-reference → Synthesize
3. Output format specification

### Key talking point
> "A skill is a RECIPE, not a CHEF. One pass, top to bottom. It doesn't loop. It doesn't verify. It's methodology on disk."

### Run it
```bash
echo "Provide a detailed analysis of A2A vs MCP..." | claude -p --model sonnet --system-prompt "$(cat step-1-context/CLAUDE.md)
---
$(cat step-2-skill/.claude/skills/deep-research/SKILL.md)" --disallowed-tools "WebSearch,WebFetch,Agent"
```

### Score it
```bash
python3 benchmark/evaluate.py --input output.md --quick --question "Provide a detailed analysis of A2A vs MCP..."
```

### What to point out
- Output is now STRUCTURED: thesis, findings with numbers, source conflicts table
- Decomposed into sub-questions before answering
- But: still from training data only — no real-time sources

### Design principle
> "The output format is part of the methodology. If you don't specify structure, you get an essay. Specify exactly what good looks like."

---

## Step 3: Custom Tool (8 min) — Vishwajit

### What to show
Open the MCP server:
```bash
cat step-3-tool/mcp-servers/arxiv_server.py
```

Point out:
- 50 lines of Python
- `@mcp.tool` decorator
- Type hints + docstring = Claude's interface
- Returns structured data (titles, authors, abstracts, dates)

### Key talking point
> "WebSearch gives you Google results — HTML snippets, blog posts. This MCP server gives you structured paper metadata. Same question, fundamentally different data quality."

### Run it
```bash
# (With MCP server connected)
echo "Provide a detailed analysis of A2A vs MCP..." | claude -p --model sonnet --system-prompt "..." --mcp-config test-run/mcp-config.json --allowed-tools "WebSearch,WebFetch,Read,Write,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar"
```

### Score it
```bash
python3 benchmark/evaluate.py --input output.md --quick --question "Provide a detailed analysis of A2A vs MCP..."
```

### What to point out
- **Real papers** from 2025-2026 with URLs
- Actual benchmark numbers from cited sources
- arXiv IDs, author names, publication dates
- THIS is usually the biggest single score jump

### Design principle
> "Structured data beats unstructured search. 15 lines of Python gave Claude access to every paper on arXiv. That's the MCP promise — build once, use everywhere."

---

## Step 4: Iterative Skill (7 min) — Rachitt

### What to show
Diff between step 2 and step 4 SKILL.md:
```bash
diff step-2-skill/.claude/skills/deep-research/SKILL.md step-4-iterative/.claude/skills/deep-research/SKILL.md
```

Point out the new sections: "Evaluate coverage", "Targeted depth search", "Maximum 3 rounds."

### Key talking point
> "Same process, same context window. NOT an agent. The skill just has smarter instructions — 'taste and adjust seasoning' instead of just 'add salt.'"

### Run it and watch Claude loop
Narrate as it runs:
- "First search round — found 5 papers"
- "Evaluating coverage — sub-question 3 only has 1 source"
- "Second round — searching with refined terms"
- "Found 3 more papers. Coverage sufficient. Moving to synthesis."

### Design principle
> "Three things to design in a loop: what triggers another round, how you refine the query, and when you STOP. Always set a maximum."

---

## Step 5: Verification Agent (8 min) — Rachitt

### What to show
The two skills:
```bash
cat step-5-verification/.claude/skills/deep-research/SKILL.md   # Research + dispatch
cat step-5-verification/.claude/skills/verify-research/SKILL.md  # Verification agent
```

### Key talking point
> "THIS is the key boundary. Everything up to step 4 runs in one session. Here, we spawn a SECOND Claude process. Own context window. Fresh eyes. No confirmation bias."

### Run it
Watch the verification agent:
- "It's checking each citation..."
- "Paper X: found on arXiv, confirmed"
- "Paper Y: CANNOT FIND. Flagged as potential hallucination."
- "Claim Z: number doesn't match the cited source"

### What to point out
Show the verification summary:
- N citations checked
- N verified
- N unverified / hallucinated
- Specific corrections made

### Design principle
> "Verification must be independent. If it runs in the same context as the research, it's biased. A separate context window means fresh eyes."

---

## Step 6: Team of Agents (10 min) — Rachitt

### What to show
The four skills:
```bash
ls step-6-team/.claude/skills/
# orchestrator/  searcher/  critic/  synthesizer/
```

Draw the architecture on the board:
```
Your session (orchestrator)
├── Searcher → searcher_output.md
├── Critic → critic_output.md  
└── Synthesizer → final_report.md
```

### Key talking point
> "Agents communicate through FILES, not shared memory. The critic doesn't see the searcher's reasoning — only its output. That's intentional."

### Run it
Watch three agents spawn in sequence. Point out what each contributes.

### What to point out
Show what the CRITIC caught that the single agent (step 5) missed:
- Methodology weakness in a cited study
- Unfair benchmark comparison
- Missing perspective from a key research group

### Design principle
> "The top scorers in the competition will be teams that design a better team structure. Add a devil's advocate. Run parallel searchers. Add an editor. The structure is a design choice."

---

## Score Staircase Summary (2 min)

Show all scores on screen:

```
Step 0 (raw):          20/100
Step 1 (context):      21/100  (+1)
Step 2 (skill):        37/100  (+16)
Step 3 (tool):         58/100  (+21, biggest jump)
Step 4 (iterative):    53/100  (heuristic dip — see note)
Step 5 (verification): 90/100  (+37)
Step 6 (team):         93/100  (+3)
```

> **Note:** Heuristic scoring (`--quick`) applies a source grounding factor — outputs without real URLs (steps 0-2) are penalized, reflecting reliance on training data. Step 4 can dip below step 3 because the iterative skill's self-evaluation text sometimes shifts keyword patterns. For the final staircase reveal, consider using LLM scoring (drop `--quick`) which correctly ranks all steps monotonically.

> "Same model. Six engineering concepts. You just saw a chatbot turn into a compound research system. Now you build yours — and try to beat our score."

→ Hand off to BUILD.md for the second half.

---

## Fallback Plan

If any live demo fails:
1. Show pre-computed output from `test-run/outputs/step-N.md`
2. Show pre-computed score from `test-run/scores/step-N.txt`
3. Say: "Here's what it looks like. Let's look at the code that made it work."

Have a GIF of the full step-6 run as emergency backup.
