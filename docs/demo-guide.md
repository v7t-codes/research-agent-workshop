# Demo Guide: Running the Workshop

Presenter reference for the live demo half of the research agent workshop. Every command is copy-pasteable. Every score is from the pre-computed test run. If something breaks on stage, the fallback path is documented for every step.

---

## Pre-Workshop Setup

### Hardware

| Item | Why | Fallback |
|------|-----|----------|
| Presenter laptop (macOS or Linux) | Runs Claude Code CLI | Codespaces devcontainer |
| Projector / large screen | Audience sees terminal | Screen-share via Zoom/Meet |
| WiFi (venue) | Steps 3-6 call external APIs | Personal hotspot |
| Backup hotspot (phone) | Venue WiFi will drop at least once | Steps 0-2 work fully offline |
| USB-C adapter / dongle | Projector compatibility | Bring HDMI + USB-C variants |

### Software Requirements

All dependencies are captured in `.devcontainer/devcontainer.json`, but for bare-metal setup:

| Dependency | Minimum Version | Install Command |
|------------|-----------------|-----------------|
| Claude Code CLI | Latest | `npm install -g @anthropic-ai/claude-code` |
| Python | 3.11+ | System or `brew install python@3.11` |
| `anthropic` (Python) | Latest | `pip install anthropic` |
| `fastmcp` (Python) | Latest | `pip install fastmcp` |
| Node.js | 20+ | `brew install node` or `nvm install 20` |
| Git | Any | Pre-installed on macOS |

### Environment Variable

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

This must be set in the shell where you run Claude Code AND where you run `evaluate.py` (for LLM scoring). Add to `~/.zshrc` or `~/.bashrc` before the workshop.

### Running verify.sh

```bash
cd /path/to/research-agent-workshop
./verify.sh
```

The script checks 7 things in order. Expected output when everything passes:

```
=== Research Agent Workshop --- Setup Verification ===

check Claude Code installed (1.0.x)
check ANTHROPIC_API_KEY is set
check Python3 installed (Python 3.11.x)
check anthropic Python package installed
check fastmcp Python package installed
check Git installed
check Node.js installed (v20.x.x)

=== Results: 7 passed, 0 failed ===
check All checks passed. You're ready for the workshop!
```

What each check does:
1. **Claude Code** -- `command -v claude`. If missing, the CLI was not installed globally via npm.
2. **ANTHROPIC_API_KEY** -- checks `$ANTHROPIC_API_KEY` is non-empty. Does NOT validate the key.
3. **Python3** -- `command -v python3`. Checks existence, prints version.
4. **anthropic package** -- `python3 -c "import anthropic"`. Fails if pip install was skipped.
5. **fastmcp package** -- `python3 -c "import fastmcp"`. Required for the MCP server in step 3+.
6. **Git** -- `command -v git`. Should always pass on macOS.
7. **Node.js** -- `command -v node`. Required by Claude Code CLI.

### Terminal Configuration

- **Font size**: 18pt minimum. The back row needs to read code. Set in Terminal > Preferences > Profiles or iTerm2 > Settings > Profiles > Text.
- **Theme**: Dark background (e.g., Solarized Dark, One Dark). White backgrounds wash out on projectors.
- **Layout**: Split screen -- left half is the code/files being shown, right half is the running terminal.
- **Shell prompt**: Shorten it. `PS1='$ '` avoids long paths cluttering the screen.
- **Line wrap**: Ensure terminal is wide enough that command output does not wrap mid-word.
- **Zoom**: `Cmd+` three times in most terminals gets you close to 18pt from the default.

### Pre-Computing Fallback Outputs

The `test-run/` directory contains everything needed to recover from a live demo failure:

```
test-run/
  run_steps.sh          # Automated runner for all steps
  mcp-config.json       # MCP server config (absolute path -- will need updating)
  outputs/
    step-0.md           # Pre-computed output for each step
    step-1.md
    step-2.md
    step-3.md
    step-4.md
    step-5.md
    step-6.md
  scores/
    step-0.txt           # Pre-computed score for each step
    step-1.txt
    step-2.txt
    step-3.txt
    step-4.txt
    step-5.txt
    step-6.txt
```

To regenerate all fallbacks (takes 20-40 minutes, uses API):

```bash
bash test-run/run_steps.sh
```

To regenerate a single step:

```bash
bash test-run/run_steps.sh 3    # Only step 3
bash test-run/run_steps.sh 5 6  # Steps 5 and 6
```

**Before the workshop**: verify the `mcp-config.json` file has the correct absolute path to `arxiv_server.py`. The checked-in version points to `/Users/vsasi/dev/research-agent-workshop/...` -- update to your machine's path:

```bash
# Check current path
cat test-run/mcp-config.json

# If wrong, the run_steps.sh script auto-generates the correct one via setup_mcp()
# But for manual use, update it:
sed -i '' "s|/Users/vsasi/dev|$(pwd)|" test-run/mcp-config.json
```

---

## The Demo Question

### The Question Text (exact)

> "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."

Source: Deep Research Bench, query #69 (Software Development). Also used as test problem 2 (`benchmark/test/test-2.md`).

### Why A2A vs MCP Was Chosen

This question is the best possible choice for this audience because:

1. **Relevant to the audience** -- they are learning MCP in this very workshop. A2A is Google's competing/complementary protocol. They will immediately understand the domain.
2. **Requires current data** -- A2A was announced in April 2025, MCP formalized in late 2024. Training data alone produces vague or hallucinated answers. Steps 0-2 (no tools) will visibly struggle. Step 3+ (with arXiv/WebSearch) will find real specs and implementations.
3. **Has genuine technical depth** -- architecture differences, protocol layering, adoption ecosystems. Not a shallow topic that training data can handle with generic prose.
4. **Tests all RACE dimensions** -- requires comparison (instruction following), specific numbers (comprehensiveness), analysis of complementary-vs-competing (insight), structured output (readability), and real citations (citation bonus).
5. **Has a reference report** -- `benchmark/reference/test-2-a2a-mcp.md` enables calibrated scoring.

### Why Not the Other Questions

- Practice problem 1 (NAS) is too well-covered in training data -- step 0 already scores reasonably well.
- Practice problem 2 (Q1 2026 models) is good for tools but too listy -- doesn't test depth.
- Practice problem 3 (MoE scaling) is ideal for steps 5-6 but too niche for a hook.

---

## Step-by-Step Demo Walkthrough

### Step 0: Raw Claude (Baseline)

**Presenter**: Rachitt (part of the hook)
**Time**: 2 minutes
**Design principle**: Establish baseline -- this is what you get with no engineering

#### Commands

```bash
# Run raw Claude with no context, no skill, no tools
echo "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation." | claude -p --model sonnet --output-format text --disallowed-tools "WebSearch,WebFetch,Agent" > output.md
```

```bash
# Score it
python3 benchmark/evaluate.py --input output.md --quick --question "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."
```

#### Expected Score: 20/100

Actual pre-computed breakdown:
- Comprehensiveness: 6/10 (sections=10, numbers=9, perspectives=23, gaps=5)
- Insight: 2/10 (analysis=1, conflicts=1, forward=3, evidence_quality=0, verification=0)
- Instruction Following: 8/10
- Readability: 6/10
- Citation Bonus: 4/10 (urls=2, titles=5, arxiv=0)
- **Source grounding factor: ~0.35** -- massive penalty for no real external sources
- **Total: 20.0/100**

#### Talking Points While Running

- "This is Sonnet with zero engineering. No context about who you are. No methodology. No tools."
- "It'll produce something -- it always does. The question is whether it's *good enough*."

#### What to Point Out in Output

- Prose is fluent but generic
- May hallucinate specific version numbers or adoption statistics
- No real URLs (or very few from training data)
- No structured comparison table
- Missing: specific implementation examples, benchmark data

#### Fallback

```bash
cat test-run/outputs/step-0.md    # Pre-computed output
cat test-run/scores/step-0.txt    # Pre-computed score
```

---

### Step 1: Context (CLAUDE.md)

**Presenter**: Vishwajit
**Time**: 5 minutes
**Design principle**: Context answers WHO, not HOW. Five sentences change the output.

#### Show the File First

```bash
cat step-1-context/CLAUDE.md
```

This is 20 lines of markdown. Walk through each section:
- **Domain**: tells Claude the researcher's field (ML, AI systems)
- **Preferences**: citation format (Author Year), source priority (peer-reviewed > preprints > blogs)
- **Constraints**: attribution rules, uncertainty handling

#### Commands

```bash
echo "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation." | claude -p --model sonnet --output-format text --system-prompt "$(cat step-1-context/CLAUDE.md)" --disallowed-tools "WebSearch,WebFetch,Agent" > output.md
```

```bash
python3 benchmark/evaluate.py --input output.md --quick --question "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."
```

#### Expected Score: 21/100 (+1)

Actual pre-computed breakdown:
- Comprehensiveness: 5/10 (sections=8, numbers=2, perspectives=22, gaps=6)
- Insight: 4/10 (analysis=0, conflicts=4, forward=3, evidence_quality=0, verification=1)
- Instruction Following: 7/10
- Readability: 6/10
- Citation Bonus: 2/10 (urls=0, titles=7, arxiv=0)
- **Source grounding factor: ~0.38** -- still no real URLs
- **Total: 21.1/100**

#### Talking Points

- "Same model, same question. We added 20 lines of markdown."
- "The score barely moved. That's the point -- context alone doesn't teach methodology."
- "But LOOK at the output: terminology is more precise. It uses 'protocol' not 'system'. It mentions the right conferences."
- "Context is necessary but not sufficient. It's the foundation for everything else."

#### What to Point Out

- More precise terminology (protocol-specific language)
- Citation format matches the CLAUDE.md specification (Author Year)
- Mentions relevant venues (NeurIPS, ICML) even without finding actual papers
- BUT: still no real-time data, still one unstructured pass, still from training data

#### Fallback

```bash
cat test-run/outputs/step-1.md
cat test-run/scores/step-1.txt
```

---

### Step 2: Skill (SKILL.md)

**Presenter**: Vishwajit
**Time**: 7 minutes
**Design principle**: A skill is a RECIPE, not a CHEF. The output format is part of the methodology.

#### Show the File First

```bash
cat step-2-skill/.claude/skills/deep-research/SKILL.md
```

Walk through the structure (63 lines total):
1. **Frontmatter** (lines 1-6): name, description -- metadata that tells Claude when to use this skill
2. **5-Step Methodology**: Decompose -> Search -> Extract Claims -> Cross-Reference -> Synthesize
3. **Output format specification**: exact markdown structure with sections, tables, source list
4. **Quality rules**: "every claim needs a number", "synthesize ACROSS sources", "label inferences"

#### Key Talking Point

> "A skill is a RECIPE, not a CHEF. One pass, top to bottom. It doesn't loop. It doesn't verify. It doesn't search the web. It's methodology on disk -- telling Claude HOW to think about research."

#### Commands

```bash
echo "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation." | claude -p --model sonnet --output-format text --system-prompt "$(cat step-1-context/CLAUDE.md)
---
$(cat step-2-skill/.claude/skills/deep-research/SKILL.md)" --disallowed-tools "WebSearch,WebFetch,Agent" > output.md
```

```bash
python3 benchmark/evaluate.py --input output.md --quick --question "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."
```

#### Expected Score: 37/100 (+16)

Actual pre-computed breakdown:
- Comprehensiveness: 8/10 (sections=5, numbers=6, perspectives=13, gaps=7)
- Insight: 4/10 (analysis=1, conflicts=2, forward=5, evidence_quality=0, verification=1)
- Instruction Following: 8/10
- Readability: 8/10 (thesis=True, table=True, refs_section=True)
- Citation Bonus: 2/10 (urls=0, titles=3, arxiv=0)
- **Source grounding factor: ~0.50** -- still no real URLs, but attributed claims bump factor
- **Total: 36.7/100**

#### What to Point Out

- Output is now **STRUCTURED**: thesis, key findings with numbers, source conflicts table, open questions, references
- Decomposed the question into sub-questions before answering
- Has a "Source Conflicts" table (even if populated from training data)
- Has an "Open Questions" section acknowledging gaps
- Readability jumped from 6 to 8 because of structural elements
- BUT: still from training data only -- no real URLs, no real-time sources

#### Fallback

```bash
cat test-run/outputs/step-2.md
cat test-run/scores/step-2.txt
```

Open `step-2-skill/TEACHING.md` for deeper explanation of the design principle.

---

### Step 3: Custom Tool (MCP Server)

**Presenter**: Vishwajit
**Time**: 8 minutes
**Design principle**: Structured data beats unstructured search. 15 lines of Python = every paper on arXiv.

#### Show the MCP Server First

```bash
cat step-3-tool/mcp-servers/arxiv_server.py
```

Point out (the file is 150 lines total, but the key parts):
- Line 23: `from fastmcp import FastMCP` -- one import
- Line 29: `mcp = FastMCP("research-tools")` -- server declaration
- Line 32-33: `@mcp.tool` decorator + function signature -- that's the entire interface
- Line 33-42: Type hints + docstring = Claude's API documentation
- Lines 58-80: Parsing arXiv XML into structured `{title, authors, abstract, published, url}` dicts
- Lines 98-145: Semantic Scholar search -- same pattern, JSON API
- Line 148-149: `mcp.run()` -- that's the entire server startup

This is 50 lines of real logic. The rest is XML parsing and formatting.

#### Also Show the Updated SKILL.md

```bash
diff step-2-skill/.claude/skills/deep-research/SKILL.md step-3-tool/.claude/skills/deep-research/SKILL.md
```

Key differences:
- `allowed-tools` in frontmatter now lists `WebSearch WebFetch Read Write mcp__research-tools__search_arxiv mcp__research-tools__search_semantic_scholar`
- "Available Tools" section added -- tells Claude what each tool does
- Search step now says "First: search_arxiv and/or search_semantic_scholar for academic papers. Then: WebSearch for broader context."
- New quality rule: "Prefer data from custom tools (structured, verified) over web search results"

#### Commands

```bash
echo "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation." | claude -p --model sonnet --output-format text --system-prompt "$(cat step-1-context/CLAUDE.md)
---
$(cat step-3-tool/.claude/skills/deep-research/SKILL.md)" --mcp-config test-run/mcp-config.json --allowed-tools "WebSearch,WebFetch,Read,Write,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" > output.md
```

```bash
python3 benchmark/evaluate.py --input output.md --quick --question "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."
```

**IMPORTANT**: Before running this live, verify `test-run/mcp-config.json` has the correct absolute path to `arxiv_server.py` for YOUR machine. The `run_steps.sh` script auto-generates this, but manual runs need a correct config.

#### Expected Score: 58/100 (+21, biggest single jump)

Actual pre-computed breakdown:
- Comprehensiveness: 10/10 (sections=9, numbers=18, perspectives=27, gaps=4)
- Insight: 3/10 (analysis=1, conflicts=4, forward=1, evidence_quality=0, verification=1)
- Instruction Following: 8/10
- Readability: 8/10
- Citation Bonus: 5/10 (urls=17, titles=7, arxiv=0)
- **Source grounding factor: ~0.72** -- URLs >= 10 triggers higher factor
- **Total: 57.7/100**

#### Talking Points

- "THIS is usually the biggest single score jump. From 37 to 58."
- "The key insight: WebSearch gives you Google result snippets. The MCP server gives you *structured paper metadata* -- title, authors, abstract, date, URL. Same question, fundamentally different data quality."
- "Comprehensiveness went from 8 to 10. Number of real data points doubled."
- "Citation bonus jumped from 2 to 5. Now we have real URLs."

#### What to Point Out

- **Real papers** with URLs from 2024-2026
- Actual author names and publication dates
- Specific benchmark numbers from cited sources (not training data guesses)
- URLs that you can actually click and verify
- The source grounding factor jumped from ~0.50 to ~0.72 because of real URLs

#### Fallback

```bash
cat test-run/outputs/step-3.md
cat test-run/scores/step-3.txt
```

---

### Step 4: Iterative Skill

**Presenter**: Rachitt
**Time**: 7 minutes
**Design principle**: Three things to design in a loop -- what triggers another round, how you refine the query, and when you STOP.

#### Show the Diff

```bash
diff step-2-skill/.claude/skills/deep-research/SKILL.md step-4-iterative/.claude/skills/deep-research/SKILL.md
```

Or more usefully, show the step 4 SKILL.md directly:

```bash
cat step-4-iterative/.claude/skills/deep-research/SKILL.md
```

Point out the NEW sections (compared to step 3):
- **"What makes this different from Step 3"** (lines 13-16): "Now you ITERATE. After each search round, evaluate what you found."
- **Step 3: Evaluate Coverage** (lines 37-40): "Which sub-questions have strong coverage (3+ quality sources)? Which have gaps?"
- **Step 4: Search Round 2 -- depth-first, targeted** (lines 42-47): "Refine your search queries based on what you learned"
- **Step 5: Evaluate Again** (lines 49-53): "Do ONE more targeted round (max 3 rounds total)"
- **"Minimum 3 sources per sub-question before synthesizing"** (line 95)

#### Commands

```bash
echo "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation." | claude -p --model sonnet --output-format text --system-prompt "$(cat step-1-context/CLAUDE.md)
---
$(cat step-4-iterative/.claude/skills/deep-research/SKILL.md)" --mcp-config test-run/mcp-config.json --allowed-tools "WebSearch,WebFetch,Read,Write,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" > output.md
```

```bash
python3 benchmark/evaluate.py --input output.md --quick --question "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."
```

#### Expected Score: 53/100 (heuristic dip from step 3's 58)

Actual pre-computed breakdown:
- Comprehensiveness: 10/10 (sections=10, numbers=16, perspectives=30, gaps=6)
- Insight: 1/10 (analysis=0, conflicts=1, forward=1, evidence_quality=0, verification=0)
- Instruction Following: 8/10
- Readability: 8/10
- Citation Bonus: 5/10 (urls=18, titles=7, arxiv=0)
- **Source grounding factor: ~0.72**
- **Total: 52.5/100**

**Why the dip**: Insight dropped from 3 to 1. The iterative skill's self-evaluation text ("evaluating coverage... gap identified... searching again...") changes the keyword distribution -- it replaces analytical phrases with process narration. The heuristic looks for phrases like "because", "therefore", "suggests" and finds fewer of them. The LLM scorer ranks step 4 correctly above step 3 (~72 vs ~55) because it understands that the CONTENT is deeper even if the analytical language shifted.

#### Talking Points While Running

Narrate Claude's behavior live:
- "First search round -- it found 5 papers on A2A and 3 on MCP."
- "Now it's evaluating coverage -- sub-question 3 (adoption data) only has 1 source."
- "Second round -- searching with refined terms: 'A2A protocol adoption enterprise 2025'."
- "Found 3 more papers. Coverage sufficient. Moving to synthesis."

#### What to Point Out

- More sources found (perspectives: 30 vs 27 in step 3)
- Gaps acknowledged (gaps: 6 vs 4 in step 3)
- But the **heuristic dip is expected** -- address it directly:
  > "The heuristic score dipped. That's a KNOWN limitation. The iterative skill adds process text that shifts keyword patterns. The LLM scorer correctly ranks this at ~72. For the final staircase, we'll use LLM scoring."

#### Fallback

```bash
cat test-run/outputs/step-4.md
cat test-run/scores/step-4.txt
```

---

### Step 5: Verification Agent

**Presenter**: Rachitt
**Time**: 8 minutes
**Design principle**: Verification must be independent. Same context = biased. Separate context window = fresh eyes.

#### Show Both Skills

```bash
cat step-5-verification/.claude/skills/deep-research/SKILL.md
cat step-5-verification/.claude/skills/verify-research/SKILL.md
```

Walk through the key boundary:
- **Phase 1** (lines 19-36 of research SKILL.md): Same iterative research as step 4. Saves draft to `research_draft.md`.
- **Phase 2** (lines 38-77): "Use the Agent tool" -- this spawns a SEPARATE Claude process. The verification agent gets its own skill instructions, its own context window, its own tools.
- **Phase 3** (lines 79-86): After verification report comes back, remove hallucinated sources, qualify unverified claims, add verification summary.

The verification agent skill (`verify-research/SKILL.md`) is 71 lines. Key sections:
- "You have NO context about how the report was produced" (line 13)
- "Search for the paper by its EXACT title" (line 31)
- "Classification: EXISTS / DOES NOT EXIST / CANNOT VERIFY" (line 33)

#### Key Talking Point

> "THIS is the key boundary. Everything up to step 4 runs in one session -- one context window. Here, we spawn a SECOND Claude process. Own context window. Fresh eyes. No confirmation bias. It can't see the researcher's reasoning -- only the output."

#### Commands

```bash
echo "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation." | claude -p --model sonnet --output-format text --system-prompt "$(cat step-1-context/CLAUDE.md)
---
RESEARCH SKILL (follow this methodology):
$(cat step-5-verification/.claude/skills/deep-research/SKILL.md)
---
VERIFICATION AGENT SKILL (give this to the verification agent when dispatching):
$(cat step-5-verification/.claude/skills/verify-research/SKILL.md)" --mcp-config test-run/mcp-config.json --allowed-tools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" > output.md
```

```bash
python3 benchmark/evaluate.py --input output.md --quick --question "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."
```

**CRITICAL**: Note `Agent` in `--allowed-tools`. Without it, Claude cannot spawn the verification subprocess. This is the #1 student mistake at this step.

#### Expected Score: 90/100 (+37, second biggest jump)

Actual pre-computed breakdown:
- Comprehensiveness: 10/10 (sections=12, numbers=26, perspectives=46, gaps=6)
- Insight: 7/10 (analysis=0, conflicts=4, forward=7, evidence_quality=0, verification=6)
- Instruction Following: 8/10
- Readability: 8/10
- Citation Bonus: 7/10 (urls=30, titles=31, arxiv=0, years=23)
- **Source grounding factor: 1.0** -- verification_markers >= 3 and urls >= 10 triggers factor=1.0
- **Total: 89.5/100**

#### Why the Massive Jump

The score jumps from 53 to 90 because of two compounding effects:
1. **Verification markers** in the output (verified/unverified/hallucinated/correction) boost the insight score: verification_markers went from 0 to 6.
2. **Source grounding factor** goes from 0.72 to 1.0 because `verification_markers >= 3 and urls >= 10` -- the scorer recognizes this is verified output, not just training data with URLs bolted on.

#### Talking Points While Running

Narrate the verification agent's behavior:
- "Research phase done. Draft saved. Now dispatching the verification agent..."
- "It's checking each citation..."
- "Paper X: found on arXiv, confirmed."
- "Paper Y: CANNOT FIND. Flagged as potential hallucination."
- "Claim Z: number doesn't match the cited source -- it says 42% but the paper says 38%."

#### What to Point Out

Show the verification summary in the output:
- N citations checked
- N verified / N unverified / N hallucinated
- Specific corrections made
- Hallucinated sources REMOVED from the final report

#### Fallback

```bash
cat test-run/outputs/step-5.md
cat test-run/scores/step-5.txt
```

---

### Step 6: Team of Agents

**Presenter**: Rachitt
**Time**: 10 minutes
**Design principle**: Agents communicate through FILES, not shared memory. The structure of the team is a design choice.

#### Show the Architecture

```bash
ls step-6-team/.claude/skills/
# orchestrator/  searcher/  critic/  synthesizer/
```

Draw on the board (or show a slide):

```
Your session (orchestrator)
  |
  |--- Agent tool ---> Searcher  ---> searcher_output.md
  |                    (arXiv, Semantic Scholar, WebSearch)
  |
  |--- Agent tool ---> Critic    ---> critic_output.md
  |                    (reads searcher_output.md, WebSearch for verification)
  |
  |--- Agent tool ---> Synthesizer -> final_report.md
                       (reads both files, produces final report)
```

Show each skill file briefly:

```bash
cat step-6-team/.claude/skills/orchestrator/SKILL.md   # 120 lines -- dispatches all 3
cat step-6-team/.claude/skills/searcher/SKILL.md        # 46 lines -- find and extract
cat step-6-team/.claude/skills/critic/SKILL.md          # 50 lines -- evaluate and flag
cat step-6-team/.claude/skills/synthesizer/SKILL.md     # 71 lines -- merge and write
```

Key design choices to highlight:
- **Orchestrator** (lines 7): `allowed-tools: Agent Read Write` -- it does NOT search. It only dispatches.
- **Searcher** (line 6): Has arXiv + Semantic Scholar + WebSearch. ONLY finds information.
- **Critic** (line 6): Has WebSearch + WebFetch. ONLY evaluates. Does NOT search for new papers.
- **Synthesizer** (line 6): `allowed-tools: Read Write` only. Cannot search. Forced to work with what it has.
- **Communication via files**: Each agent writes to a named file. Next agent reads that file. No shared context.

#### Commands

```bash
echo "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation." | claude -p --model sonnet --output-format text --system-prompt "$(cat step-1-context/CLAUDE.md)
---
ORCHESTRATOR SKILL (follow this):
$(cat step-6-team/.claude/skills/orchestrator/SKILL.md)
---
SEARCHER AGENT SKILL (give this to the searcher agent):
$(cat step-6-team/.claude/skills/searcher/SKILL.md)
---
CRITIC AGENT SKILL (give this to the critic agent):
$(cat step-6-team/.claude/skills/critic/SKILL.md)
---
SYNTHESIZER AGENT SKILL (give this to the synthesizer agent):
$(cat step-6-team/.claude/skills/synthesizer/SKILL.md)" --mcp-config test-run/mcp-config.json --allowed-tools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" > output.md
```

```bash
python3 benchmark/evaluate.py --input output.md --quick --question "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."
```

#### Expected Score: 93/100 (+3)

Actual pre-computed breakdown:
- Comprehensiveness: 10/10 (sections=9, numbers=28, perspectives=19, gaps=11)
- Insight: 7/10 (analysis=0, conflicts=3, forward=3, evidence_quality=11, verification=3)
- Instruction Following: 8/10
- Readability: 8/10
- Citation Bonus: 6/10 (urls=4, titles=3, arxiv=0, years=2)
- **Source grounding factor: 1.05** -- evidence_quality >= 3 triggers factor=1.0 + bonus
- **Total: 92.9/100**

#### Why Only +3 from Step 5

The team architecture adds marginal improvement at this score level because:
- Comprehensiveness and readability were already maxed at step 5
- The critic adds `evidence_quality` markers (11 instances vs 0 in step 5), which slightly boosts the source factor above 1.0
- The real value of the team shows on harder problems (practice-3 MoE scaling) where conflicting sources need structured critique

#### What to Point Out

- **evidence_quality=11** -- the critic's STRONG/MODERATE/WEAK ratings flow into the final report
- **gaps=11** -- the critic identified more gaps than any previous step
- Show what the critic caught that the single verification agent (step 5) missed:
  - Methodology weakness in a cited study
  - Unfair benchmark comparison
  - Missing perspective from a key research group

#### Fallback

```bash
cat test-run/outputs/step-6.md
cat test-run/scores/step-6.txt
```

---

## The Score Staircase

### Actual Scores (from pre-computed test run)

```
Step 0 (raw):          20.0/100
Step 1 (context):      21.1/100  (+1.1)
Step 2 (skill):        36.7/100  (+15.6)
Step 3 (tool):         57.7/100  (+21.0, biggest jump)
Step 4 (iterative):    52.5/100  (-5.2, heuristic dip)
Step 5 (verification): 89.5/100  (+37.0)
Step 6 (team):         92.9/100  (+3.4)
```

### The Three Tiers

| Tier | Steps | Score Range | What's Different |
|------|-------|-------------|-----------------|
| No tools | 0, 1, 2 | 20-37 | Training data only. Source grounding factor ~0.35-0.50 |
| Tools | 3, 4 | 53-58 | Real URLs, real papers. Factor ~0.70-0.72 |
| Verification + Team | 5, 6 | 90-93 | Verified claims, evidence quality. Factor 1.0-1.05 |

### Why Step 4 Dips Below Step 3 (Heuristic)

This is the most important thing to address proactively. The audience will notice.

**Root cause**: The heuristic insight scorer looks for analytical phrases (`because`, `therefore`, `suggests`, `implies`, `trade-off`). Step 4's iterative SKILL.md adds self-evaluation text ("evaluating coverage... gap identified... searching again...") that replaces some of these analytical phrases with process narration. Insight drops from 3/10 to 1/10.

**The raw scores tell the story**: Step 4's `_raw_total` is higher than step 3's, but the source grounding factor is the same (both ~0.72), and the insight penalty dominates.

**LLM scoring fixes this**: The LLM scorer (without `--quick`) correctly ranks step 4 at ~72 and step 3 at ~55. It understands that deeper coverage with more sources is better research even if the analytical language shifted.

**What to say on stage**:
> "The heuristic dipped. That's a known limitation of regex-based scoring. The heuristic looks for analytical keywords and the iterative skill's process text shifts those patterns. The LLM scorer correctly ranks step 4 above step 3. This is actually a great lesson: your eval tool has limitations too."

### When to Use --quick vs LLM Scoring

| Use Case | Flag | Cost | Latency | Accuracy |
|----------|------|------|---------|----------|
| Iterating during build phase | `--quick` | Free | Instant | Good for ordering, poor for absolute scores |
| Final staircase reveal | (no flag) | ~$0.02/eval | 5-10 sec | Monotonic ordering, accurate scores |
| Calibrated scoring | `--reference benchmark/reference/test-2-a2a-mcp.md` | ~$0.02/eval | 5-10 sec | Best accuracy |

For the live demo: use `--quick` during each step (instant feedback), then show the LLM staircase at the end for the correct monotonic progression.

---

## Competition Phase

### Minute-by-Minute Timeline

| Clock | Duration | Activity | Who |
|-------|----------|----------|-----|
| 0:00 | 5 min | The Hook -- thesis slide + live step 6 demo | Rachitt |
| 0:05 | 5 min | Step 1: Context | Vishwajit |
| 0:10 | 7 min | Step 2: Skill | Vishwajit |
| 0:17 | 8 min | Step 3: Custom Tool | Vishwajit |
| 0:25 | 7 min | Step 4: Iterative Skill | Rachitt |
| 0:32 | 8 min | Step 5: Verification Agent | Rachitt |
| 0:40 | 10 min | Step 6: Team of Agents | Rachitt |
| 0:50 | 2 min | Score Staircase Summary | Rachitt |
| 0:52 | 3 min | Competition rules + team formation | Both |
| 0:55 | 5 min | Setup check -- every team runs verify.sh | Both (circulate) |
| 1:00 | 55 min | **BUILD PHASE** -- teams build their agents | Both (circulate) |
| 1:55 | 10 min | Teams score on test problems | Both |
| 2:05 | 10 min | Top 3 presentations (2-3 min each) | Teams |
| 2:15 | 5 min | Audience vote for "best design" + wrap-up | Both |
| 2:20 | | END | |

### Team Formation

- Groups of 2-3 people
- At least one person per group should have Claude Code installed and working (run verify.sh)
- If a group has setup issues, pair them with a working group or use the devcontainer:
  ```bash
  # VS Code with Dev Containers extension
  code .
  # Then: Cmd+Shift+P > "Dev Containers: Reopen in Container"
  ```

### Iteration on Practice Problems

Students should iterate on the 3 practice problems before touching test problems:

| Practice Problem | File | Best For | Difficulty |
|-----------------|------|----------|------------|
| 1. NAS comparison | `benchmark/practice/practice-1.md` | Warmup, steps 1-2 | Easy (training data covers it) |
| 2. Q1 2026 foundation models | `benchmark/practice/practice-2.md` | Steps 3-4 (forces tools) | Medium (needs current data) |
| 3. MoE scaling laws | `benchmark/practice/practice-3.md` | Steps 5-6 (conflicting sources) | Hard (easy to hallucinate) |

Recommended iteration cycle:
1. Run on practice-1 with current setup. Score with `--quick`.
2. Tweak SKILL.md or CLAUDE.md. Run again. Compare scores.
3. Move to practice-2 once scoring 50+ on practice-1.
4. Move to practice-3 once scoring 60+ on practice-2.
5. Only move to test problems when satisfied with practice scores.

### Scoring on Test Problems

There are 3 test problems in `benchmark/test/`:

| Test Problem | File | Domain |
|-------------|------|--------|
| 1. Ion trap quantum computing | `benchmark/test/test-1.md` | Science & Technology |
| 2. A2A vs MCP | `benchmark/test/test-2.md` | Software / AI Systems |
| 3. Plasma metal ions + cardiovascular | `benchmark/test/test-3.md` | Cross-Disciplinary (Health) |

Commands to score test outputs:

```bash
# Score each test output (--quick for speed during competition)
python3 benchmark/evaluate.py --input test-1-output.md --quick --question "What are the most effective approaches to scaling ion trap quantum computing from small-scale demonstration projects to large-scale systems capable of solving real-world problems? For each approach, provide specific technical results from 2024-2026, identify the key engineering challenges that remain, and assess where the research community disagrees on the most promising path forward."

python3 benchmark/evaluate.py --input test-2-output.md --quick --question "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."

python3 benchmark/evaluate.py --input test-3-output.md --quick --question "Could therapeutic interventions aimed at modulating plasma metal ion concentrations represent effective preventive or therapeutic strategies against cardiovascular diseases? What types of interventions have been proposed, and is there clinical evidence supporting their feasibility and efficacy? Provide specific trial results, mechanisms of action, and identify where the clinical evidence is conflicting or insufficient."
```

Competition score = average of all 3 test scores.

### Presentation Format (Top 3 Teams)

Each team gets 2-3 minutes. Cover:
1. **Score progression**: Show how your score climbed as you added each step. Where was the biggest jump?
2. **Design choices**: What MCP server did you build? How did you design iteration? What team structure?
3. **One surprise**: Something that worked unexpectedly well, or failed unexpectedly.

After all 3 present, audience votes for "best design" (separate from best score).

---

## Presenter Assignments

### Vishwajit

| Section | Time | Key Files to Show |
|---------|------|-------------------|
| Step 1: Context | 5 min | `step-1-context/CLAUDE.md` |
| Step 2: Skill | 7 min | `step-2-skill/.claude/skills/deep-research/SKILL.md` |
| Step 3: Custom Tool | 8 min | `step-3-tool/mcp-servers/arxiv_server.py`, `step-3-tool/.claude/skills/deep-research/SKILL.md` |
| Competition setup | 3 min | `BUILD.md` on screen |

Total: ~23 min

Vishwajit teaches the foundation: what goes into a CLAUDE.md, how a SKILL.md structures methodology, and how an MCP server extends capabilities. These are the building blocks students will modify during the competition.

### Rachitt

| Section | Time | Key Files to Show |
|---------|------|-------------------|
| The Hook (thesis + live step 6) | 5 min | Live terminal |
| Step 4: Iterative Skill | 7 min | Diff between step 2 and step 4 SKILL.md |
| Step 5: Verification Agent | 8 min | Both SKILL.md files in step 5 |
| Step 6: Team of Agents | 10 min | All 4 skills in step 6 |
| Score Staircase Summary | 2 min | Score table on screen |

Total: ~32 min

Rachitt teaches the agent architecture: iteration (same process, smarter instructions), verification (separate context = fresh eyes), and team (specialized agents communicating through files). These are the design patterns students will extend.

### Both

- **Build phase circulation** (55 min): Walk between teams. Answer questions. Help with setup issues. Point struggling teams to specific step files. Remind teams to score with `--quick` after each change.
- **Wrap-up** (5 min): Call up top 3, manage presentations, run audience vote.

---

## Emergency Procedures

### WiFi Goes Down

- Steps 0-2 work fully offline (no tool calls)
- Steps 3+ need internet for arXiv API, Semantic Scholar API, and WebSearch
- Switch to hotspot immediately
- If hotspot also fails: show pre-computed outputs from `test-run/outputs/` and teach the concepts from the code

### API Key Hits Rate Limit

- Symptoms: 429 errors, "rate limit exceeded"
- Immediate: wait 60 seconds, retry
- If persistent: switch to a backup API key
- For students: pairs should share one API key to halve the request load

### Claude Code CLI Crashes

- `claude --version` to verify installation
- `npm install -g @anthropic-ai/claude-code` to reinstall
- If still failing: use the devcontainer
- Last resort: show pre-computed outputs

### Projector / Display Issues

- Have the staircase scores written on a whiteboard as backup
- Have DEMO.md open on a phone/tablet for the talking points
- Code files can be shown from any text editor if terminal projection fails
