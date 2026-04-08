# Self-Improvement Guide: How to Optimize Your Research Agent

This guide is a practical reference for diagnosing and fixing low scores in the RACE benchmark. Every recommendation maps directly to code, regex patterns, or file paths in this repo. No theory — just what to change and why it moves the score.

---

## 1. The Optimization Loop

The only loop that matters:

```
Build --> Score --> Diagnose --> Fix --> Re-score
```

### Two scoring modes

| Mode | Command | Speed | Use for |
|------|---------|-------|---------|
| Heuristic (`--quick`) | `python benchmark/evaluate.py --input output.md --quick` | Instant | Iteration — run after every change |
| LLM-as-judge | `python benchmark/evaluate.py --input output.md` | ~10s | Validation — run when you think you're done |
| With reference | `python benchmark/evaluate.py --input output.md --reference benchmark/reference/practice-1-nas.md` | ~10s | Gap analysis — find what you're missing |
| With question | `python benchmark/evaluate.py --input output.md --question "Compare NAS approaches..."` | Either | Better instruction_following scoring |

Always pass `--question` when available. Without it, instruction_following falls back to structural heuristics (section count + conclusion presence) which are less informative.

### Reading the output

The evaluator prints each dimension with a bar chart and the heuristic justification:

```
Comprehensiveness.............. ████░░░░░░ 4/10  (weight: 30%)
  → sections=3, numbers=8, perspectives=4, gaps=1
```

The justification tells you exactly which sub-signals fired. Use it to diagnose.

### The source grounding factor

The heuristic applies a multiplier (`_source_factor`) that gates your total score based on external evidence. This is the single biggest lever in the scoring system.

From `benchmark/evaluate.py` lines 259-274:

| Condition | Factor | Practical meaning |
|-----------|--------|-------------------|
| `urls < 5` and `evidence_quality < 3` | 0.35 + small bonus | Steps 0-2: capped around 35% of raw score |
| `evidence_quality >= 3` | ~1.0 | Step 6 with critic: full score or slight boost |
| `verification_markers >= 3` and `urls >= 10` | 1.0 | Step 5 with verification: full score |
| `urls >= 10` (no verification) | 0.70-0.80 | Steps 3-4 with tools: ~75% of raw score |
| Everything else | 0.55 | Limbo — some URLs but not enough |

**Implication:** You cannot brute-force past ~35 points without real URLs. You cannot brute-force past ~75 points without verification or evidence quality markers. The staircase is structural, not cosmetic.

---

## 2. Diagnosing Low Scores by Dimension

### Low Comprehensiveness (< 6/10)

**What the heuristic measures** (lines 107-137 of `evaluate.py`):

| Sub-signal | Regex / check | Max contribution | How to earn it |
|------------|---------------|-----------------|----------------|
| Sections | `^##\s+` (multiline) | 2 pts (need 4+ sections) | Use `## Heading` in output template |
| Attributed claims | `(?:according to\|reported\|found\|showed\|achieved\|demonstrated).*?\d+` | 2 pts | Phrase numbers as "X reported Y%" |
| Number claims | `\d+\.?\d*%\|\d+\.?\d*x\|\$\d+\|\d+[MBK]\b\|\d+\.\d+ ` | 2 pts (need 10+) | Include specific percentages, dollar amounts, counts |
| Perspectives | `approach\|method\|technique\|strategy\|framework\|model\|algorithm` | 2 pts (need 8+) | Cover multiple approaches explicitly |
| Gaps mentioned | `gap\|limitation\|not covered\|open question\|remain\|unclear` | 1 pt | Add "Open Questions" section |
| URLs | `https?://\S+` | 1 pt (need 3+) | Requires step 3+ tools |

**Common causes of low comprehensiveness:**

1. **Floating numbers with no attribution.** The heuristic distinguishes between `"accuracy was 95%"` (just a number claim, +0.2 each) and `"Smith et al. reported 95% accuracy"` (an attributed claim, much higher value). Fix: add `"according to"`, `"reported"`, `"found"`, `"showed"`, `"achieved"`, or `"demonstrated"` before numbers.

2. **Too few sections.** You need at least 4 `## Heading` lines to earn 2 points. The step-2 SKILL.md template already includes Key Findings, Detailed Analysis, Source Conflicts, Open Questions, and Sources — that's 5 sections.

3. **Missing perspectives.** The regex looks for the words "approach", "method", "technique", "strategy", "framework", "model", "algorithm". If your report describes three methods but calls them all "systems", the heuristic won't count them. Fix: use the vocabulary the heuristic expects.

**Fix: Add attribution instructions to your SKILL.md**

```markdown
## Quality Rules
- Every claim needs a number attributed to its source: "Author (Year) reported X"
- Use phrases: "according to", "found", "showed", "achieved", "demonstrated"
- Cover at least 3 approaches/methods/techniques per sub-topic
- Include an ## Open Questions section listing gaps and limitations
```

### Low Insight (< 4/10)

This is the highest-weighted dimension (35%). The heuristic checks five sub-signals.

**What the heuristic measures** (lines 140-177 of `evaluate.py`):

| Sub-signal | Regex | Max contribution | How to earn it |
|------------|-------|-----------------|----------------|
| Analysis phrases | `because\|therefore\|suggests\|implies\|trade-off\|compared to\|in contrast\|whereas\|due to\|this means\|as a result\|consequently\|this indicates` | 4 pts (need 8+) | Write causal analysis, not descriptions |
| Conflict phrases | `however\|disagree\|conflict\|debate\|contrary\|challenge\|limitation\|caveat\|on the other hand\|alternatively\|despite\|nevertheless` | 3 pts (need 3+) | Include a "Where Experts Disagree" section |
| Forward-looking | `future\|open problem\|remain\|promising\|emerging\|potential\|outlook` | 3 pts (need 6+) | Include "Future Directions" or "Open Problems" section |
| Evidence quality | `\bevidence quality\b\|\bSTRONG\b\|\bMODERATE\b\|\bWEAK\b` (case-sensitive) | 2 pts (need 6+) | Requires critic agent (step 6) |
| Verification markers | `\bverified\b\|\bunverified\b\|\bhallucinated\b\|\bcorrection` (case-insensitive) | 1 pt (need 2+) | Requires verification agent (step 5+) |

**Common causes of low insight:**

1. **Description instead of analysis.** The report says "Method A uses attention" instead of "Method A uses attention, which means it scales quadratically with sequence length, and therefore becomes impractical above 128K tokens." The difference is causal connectors: *because*, *therefore*, *this means*, *as a result*.

2. **No conflict identification.** If your report presents one viewpoint per topic, it earns 0 on conflict phrases. Even when sources genuinely agree, you can write: "However, Smith (2025) notes a caveat..." or "Despite this consensus, limitations remain."

3. **No evidence quality markers.** The strings `STRONG`, `MODERATE`, `WEAK` are checked **case-sensitively**. They must appear exactly as uppercase. This is designed to reward step 6 (critic agent output). Without a critic, you cannot earn these 2 points.

4. **No verification markers.** The words `verified`, `unverified`, `hallucinated`, `correction` earn 1 point when present. This rewards step 5+ (verification agent).

**Fix: Add explicit analysis instructions to your SKILL.md**

```markdown
### Cross-Reference
- For every finding, explain WHY it matters: use "because", "therefore",
  "this means", "as a result", "consequently"
- Where sources disagree, write: "However, [Source B] challenges this,
  arguing that..." — use "however", "despite", "on the other hand"
- Include a ## Future Directions section with "emerging", "promising",
  "open problem", "potential", "remain" language
```

**Fix: Add a critic agent (step 6) to earn evidence quality points**

In your critic's SKILL.md (`step-6-team/.claude/skills/critic/SKILL.md`), ensure the output includes:

```markdown
- Rating: STRONG / MODERATE / WEAK with specific reason
```

And in your synthesizer's SKILL.md, ensure it integrates these ratings:

```markdown
- [Finding with numbers + source] — evidence quality: STRONG
- [Finding with numbers + source] — evidence quality: MODERATE
```

### Low Instruction Following (< 6/10)

**What the heuristic measures** (lines 180-203 of `evaluate.py`):

When `--question` is provided:
1. **Keyword coverage**: Extracts all 4+ character words from the question, checks what fraction appear in the report. Worth up to 8 points.
2. **Structural match**: If the question asks for comparison (`compar|differ|versus|vs`), checks the report has comparison language. +1 bonus.
3. **Data match**: If the question asks for numbers (`specific|number|result|data|evidence`), checks the report has 3+ number claims. +1 bonus.

When `--question` is NOT provided:
- Falls back to: section count (up to 4 pts) + conclusion presence (2 pts) + title presence (2 pts). Maximum 8.

**Common causes of low instruction_following:**

1. **Poor keyword coverage.** If the question asks about "ion trap quantum computing" and your report discusses "trapped ion qubits" without ever using the exact phrase "ion trap", you lose coverage points. Fix: echo the question's key terms.

2. **Missing structural requirements.** If the question says "compare X and Y", the heuristic checks for comparison language in your output. If you write parallel descriptions without explicit comparison words (`compared to`, `versus`, `advantage`, `disadvantage`, `differ`), you lose the bonus.

3. **Not decomposing to cover all parts.** The question "For each approach, provide X, Y, and Z" requires coverage of X, Y, AND Z for each approach. A decomposition step that splits by approach but not by X/Y/Z will miss coverage.

**Fix: Parse the question type in your SKILL.md decomposition step**

```markdown
### Step 1: Decompose
Break the question into sub-questions. Before decomposing, identify:
- **Question type**: Is this a comparison? Evaluation? Survey? Explanation?
- **Required structure**: Does the question ask for "for each X, provide Y"?
- **Key terms**: List every significant term from the question. These MUST
  appear in the final report.
- **Scope markers**: What time range, which domains, how many examples?

Ensure every keyword from the original question appears in your output.
If the question asks to "compare", include explicit comparison language.
If the question asks for "specific numbers", ensure quantitative data.
```

### Low Readability (< 6/10)

**What the heuristic measures** (lines 206-226 of `evaluate.py`):

| Sub-signal | Check | Max contribution |
|------------|-------|-----------------|
| Thesis | `^#\s+.+` (has a top-level heading) | 2 pts |
| Sections | `^##\s+` count (capped at 3) | 3 pts |
| Table | `\|.*\|.*\|` AND `---` both present | 1 pt |
| Connectors | `^(First\|Second\|Third\|Finally\|Moreover\|Furthermore\|In addition\|Specifically)` at start of line | 2 pts (need 2+) |
| References section | `^##\s*(References\|Sources\|Bibliography\|Works Cited)` | 2 pts |

**Common causes of low readability:**

1. **No top-level heading.** The report must start with `# Title` (single `#`). Without it, you lose 2 points.

2. **No comparison table.** The heuristic checks for markdown tables (pipes and dashes). Even one table earns the point. The step-2 SKILL.md template already includes a `## Source Conflicts` table.

3. **No transition words at line start.** The regex checks for `First`, `Second`, `Third`, `Finally`, `Moreover`, `Furthermore`, `In addition`, `Specifically` at the beginning of a line (after newline). These must be the first word on the line.

4. **No References section.** Must be a `## References` or `## Sources` heading. Not just inline citations — a dedicated section.

**Fix: Hardcode the output template in your SKILL.md**

```markdown
### Synthesize
Write the report in EXACTLY this format:

# [Topic]: [One-sentence thesis]

First, [overview of the landscape].

## Key Findings
- [Finding 1]

## Detailed Analysis

### [Theme 1]
[Analysis with "because", "therefore" connectors]

Moreover, [cross-reference between sources].

### [Theme 2]
Furthermore, [additional analysis].

## Comparison
| Aspect | Approach A | Approach B | Approach C |
|--------|-----------|-----------|-----------|
| ...    | ...       | ...       | ...       |

## Where Experts Disagree
[Conflict analysis]

## Open Questions
[Gaps and future directions]

## References
- Author (Year). "Title." Venue. URL
```

### Low Citation Bonus (< 4/10)

**What the heuristic measures** (lines 229-244 of `evaluate.py`):

| Sub-signal | Regex | Max contribution |
|------------|-------|-----------------|
| URLs | `https?://\S+` | 3 pts (3+ URLs) |
| Paper titles | `"[A-Z][^"]{15,}"` (quoted, capitalized, 16+ chars) | 2 pts (2+ titles) |
| arXiv IDs | `arxiv\.org/abs/\d{4}\.\d+` | 2 pts (2+ IDs) |
| Year references | `\(\d{4}\)` | 2 pts (need 4+) |
| DOI references | `doi\.org/` | 1 pt |

**Common causes of low citation_bonus:**

1. **Score 0: No URLs at all.** You are at step 0-2 (no tools). You need to progress to step 3 to get real URLs. Without MCP tools, Claude generates from training data and has no URLs to cite.

2. **Score 1-2: URLs but no structured citations.** You have WebSearch but not arXiv/Semantic Scholar tools. The custom tools return structured metadata (title, authors, year, URL) which makes it trivial to format proper citations.

3. **Paper titles not in quotes.** The regex requires double-quoted titles starting with a capital letter and at least 16 characters. `"Attention Is All You Need"` matches. `Attention Is All You Need` does not.

4. **Missing year references.** The pattern `\(\d{4}\)` looks for `(2024)` or `(2025)` format. If you write `published in 2024` instead of `(2024)`, it doesn't count.

**Fix: Specify citation format in CLAUDE.md and SKILL.md**

In `step-1-context/CLAUDE.md`:

```markdown
## Preferences
- Citation format: Author (Year) inline, full reference list at end
- Quote all paper titles: "Title Here"
- Include arXiv URLs when available: https://arxiv.org/abs/XXXX.XXXXX
```

In your SKILL.md `## Sources` section:

```markdown
## References
- Author1, Author2 (Year). "Full Paper Title." Venue. https://arxiv.org/abs/XXXX.XXXXX
- Author1, Author2 (Year). "Full Paper Title." Venue. https://doi.org/XX.XXXX/XXXXX
```

---

## 3. Optimizing Each Component

### CLAUDE.md (Identity: WHO)

**File:** `step-1-context/CLAUDE.md`

This sets the agent's identity, domain, and preferences. It is NOT methodology (that belongs in SKILL.md).

**What a good CLAUDE.md includes:**

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
- Quote all paper titles in double quotes
- Include arXiv URLs and DOIs when available

## Constraints
- Never state claims without attribution
- Distinguish between "the paper claims X" and "X is established consensus"
- If you're uncertain, say so explicitly
```

**Optimization levers:**

| Change | Impact | Example |
|--------|--------|---------|
| Domain specificity | Better search terms, right venues | Adding "NeurIPS, ICML" helps the agent name-drop real venues |
| Source priority ordering | Changes what gets cited first | "peer-reviewed > preprints > blogs" |
| Citation format spec | Directly earns citation_bonus points | "Author (Year)" + quoted titles |
| Conflict handling | Earns insight conflict points | "show both with methodology notes" |
| Staleness threshold | Earns forward_looking points | "flag anything older than 12 months" |

**Diminishing returns:** After ~15-20 lines, more CLAUDE.md text doesn't help. The agent has enough identity. Spend your time on SKILL.md instead.

### SKILL.md (Methodology: HOW)

**Files:**
- Step 2: `step-2-skill/.claude/skills/deep-research/SKILL.md`
- Step 3: `step-3-tool/.claude/skills/deep-research/SKILL.md`
- Step 4: `step-4-iterative/.claude/skills/deep-research/SKILL.md`

This is where most of your score improvement comes from. The SKILL.md controls:

1. **Decomposition strategy** (affects instruction_following)
2. **Search methodology** (affects comprehensiveness)
3. **Analysis instructions** (affects insight)
4. **Output template** (affects readability)
5. **Citation format** (affects citation_bonus)

**The critical YAML frontmatter:**

```yaml
---
name: deep-research
description: >-
  Researches any topic using structured methodology with custom tools.
  Use when user says "research", "investigate", "deep dive", or "what do we know about".
allowed-tools: WebSearch WebFetch Read Write mcp__research-tools__search_arxiv mcp__research-tools__search_semantic_scholar
---
```

The `allowed-tools` field gates which tools the skill can use. If you add MCP tools to your server but forget to list them here, the skill cannot call them.

**Step-by-step SKILL.md evolution:**

Step 2 (no tools, one pass):
```markdown
allowed-tools:  (none — uses only training data)
```
- Methodology: Decompose, Search (from memory), Extract, Cross-Reference, Synthesize
- Max heuristic score: ~37 (capped by 0.35 source factor)

Step 3 (tools, one pass):
```markdown
allowed-tools: WebSearch WebFetch Read Write mcp__research-tools__search_arxiv mcp__research-tools__search_semantic_scholar
```
- Methodology: Same steps but "use custom tools first"
- Max heuristic score: ~58 (0.70-0.80 source factor with URLs)

Step 4 (tools, iterative):
```markdown
allowed-tools: WebSearch WebFetch Read Write mcp__research-tools__search_arxiv mcp__research-tools__search_semantic_scholar
```
- Methodology: Adds evaluate-coverage + search-again loop (max 3 rounds)
- Max heuristic score: ~72 (more URLs, better coverage)

**Key methodology additions for step 4:**

```markdown
### Step 3: Evaluate Coverage
After round 1, assess:
- Which sub-questions have strong coverage (3+ quality sources)?
- Which have gaps (fewer than 3 sources, or only superficial coverage)?
- Are there NEW sub-questions that emerged from what you found?

### Step 4: Search — Round 2 (depth-first, targeted)
For each gap identified:
- Refine your search queries based on what you learned in round 1
- Search for specific papers, specific authors, specific benchmarks
- Follow citation chains: if paper A cites paper B and B seems important, fetch B
```

### MCP Server (Tools)

**File:** `step-3-tool/mcp-servers/arxiv_server.py`

**Current tools:**

| Tool | API | Returns | Best for |
|------|-----|---------|----------|
| `search_arxiv` | arXiv API | Title, authors, abstract, date, URL | Recent papers, preprints |
| `search_semantic_scholar` | S2 API | Title, authors, year, venue, citations, URL | Highly-cited papers, impact |

**Adding tools — what to consider:**

1. **Structured output.** The whole point of custom tools over WebSearch is structured metadata. Return JSON-like fields (title, authors, year, URL), not raw HTML.

2. **Error handling.** Both current tools handle API timeouts (15s) and return human-readable error messages. Any new tool should do the same.

3. **Update `allowed-tools`** in your SKILL.md frontmatter after adding a tool. This is the #1 forgotten step.

**Example: Adding a new tool to the MCP server**

```python
@mcp.tool
def search_pubmed(query: str, max_results: int = 10) -> str:
    """Search PubMed for biomedical papers.

    Args:
        query: Search terms
        max_results: Number of papers (default 10, max 20)
    """
    # ... API call ...
    # Return structured: title, authors, year, journal, DOI, URL
```

Then update your SKILL.md:

```yaml
allowed-tools: WebSearch WebFetch Read Write mcp__research-tools__search_arxiv mcp__research-tools__search_semantic_scholar mcp__research-tools__search_pubmed
```

### Iteration Logic (Step 4)

The iteration loop in the step-4 SKILL.md has three design decisions:

**1. Trigger: When to search again**

```markdown
### Evaluate Coverage
- Which sub-questions have strong coverage (3+ quality sources)?
- Which have gaps?
```

The trigger is gap detection. "3+ quality sources per sub-question" is the threshold. If a sub-question has fewer, another round fires.

**2. Refinement: How to improve the next search**

```markdown
### Round 2 (depth-first, targeted)
- Refine queries based on round 1 findings
- Follow citation chains
- Search for specific papers, authors, benchmarks
```

Round 2 is targeted, not broad. It uses round 1 results to build better queries.

**3. Stop condition: When to quit**

```markdown
- If still gaps: do ONE more targeted round (max 3 rounds total)
- If sufficient: proceed to synthesis
```

Hard cap at 3 rounds. This prevents infinite loops and controls cost.

**Tuning the iteration:**

| Parameter | Default | Tighter | Looser |
|-----------|---------|---------|--------|
| Source threshold | 3 per sub-question | 5 per sub-question | 2 per sub-question |
| Max rounds | 3 | 2 (faster, cheaper) | 4 (more thorough) |
| New sub-questions | Allowed | Disabled (scope creep) | Allowed (exploration) |

For competition, 3 rounds and 3 sources per sub-question is the sweet spot. Going to 4 rounds rarely adds enough signal to justify the time cost.

### Verification Agent (Step 5)

**Files:**
- Main skill: `step-5-verification/.claude/skills/deep-research/SKILL.md`
- Verifier skill: `step-5-verification/.claude/skills/verify-research/SKILL.md`

The verification agent is a separate Claude instance spawned via the `Agent` tool. It reads `research_draft.md` and checks every source and claim.

**Why it must be separate:**

```markdown
## Why you're a separate agent
You run in your own context window. You don't share memory with the
research agent that produced this report. This is intentional — you
need fresh eyes, not the research agent's reasoning and biases.
```

If the verification agent shares context with the research agent, it inherits the same biases and is less likely to catch hallucinations. Independence is the whole point.

**What the verifier checks:**

1. **Source existence**: Searches for each paper by exact title. Classifies as EXISTS / DOES NOT EXIST / CANNOT VERIFY.
2. **Claim accuracy**: Checks if cited numbers actually appear in the cited source. Classifies as VERIFIED / UNVERIFIED / CONTRADICTED.
3. **Hallucination flags**: Sources that cannot be found are flagged.

**The scoring payoff:**

The verifier's output adds two types of signal the heuristic rewards:
- `verification_markers`: words like "verified", "unverified", "hallucinated", "correction" — worth up to 1 insight point
- Combined with `urls >= 10`: unlocks the 1.0 source factor (from 0.70-0.80)

This means step 5 can jump from ~58 to ~90 on the heuristic just by adding verification.

**Dispatching the verifier:**

```markdown
## Phase 2: Verification

Use the Agent tool with this prompt:

"You are a research verification agent. Your job is to independently
audit a research report for accuracy and citation validity.

Read the file research_draft.md.

For EACH cited source in the report:
1. Search for the paper by its exact title using WebSearch
2. Check: does this paper actually exist?
..."
```

Give the verifier these tools: `WebSearch, WebFetch, Read`

Note: the verifier gets `Read` but NOT `Write` to the main report. It reads the draft but outputs its own verification report. The main agent then integrates corrections.

### Team Structure (Step 6)

**Files:**
- `step-6-team/.claude/skills/orchestrator/SKILL.md`
- `step-6-team/.claude/skills/searcher/SKILL.md`
- `step-6-team/.claude/skills/critic/SKILL.md`
- `step-6-team/.claude/skills/synthesizer/SKILL.md`

**The pipeline:**

```
Orchestrator (your session, tools: Agent Read Write)
  |
  |--> Searcher agent  --> writes searcher_output.md
  |      tools: WebSearch, WebFetch, Read, Write,
  |             mcp__research-tools__search_arxiv,
  |             mcp__research-tools__search_semantic_scholar
  |
  |--> Critic agent    --> reads searcher_output.md, writes critic_output.md
  |      tools: WebSearch, WebFetch, Read, Write
  |
  |--> Synthesizer     --> reads both files, writes final_report.md
         tools: Read, Write
```

**Communication is file-based.** Agents do not share context. Each reads/writes markdown files. This ensures:
- No context bleed between stages
- Each agent can be debugged independently
- The orchestrator can retry any single agent without rerunning everything

**Role specialization is non-negotiable.** Each agent must have a distinct, exclusive role:

| Agent | Does | Does NOT |
|-------|------|----------|
| Searcher | Find papers, extract metadata, extract claims | Evaluate quality, synthesize, write final report |
| Critic | Rate evidence quality, find conflicts, flag hallucinations | Search for new papers, write final report |
| Synthesizer | Integrate findings + critique into coherent report | Search for papers, verify claims independently |

**The critic is the key differentiator** between step 5 and step 6. The critic's output introduces:
- `evidence quality` markers: STRONG / MODERATE / WEAK
- Conflict analysis with methodology differences
- Gap identification

These directly earn the `evidence_quality` insight sub-signal (up to 2 points) AND unlock the 1.0+ source factor.

---

## 4. Advanced Optimization Techniques

### A/B Testing SKILL.md Variants

Run the same question with two different SKILL.md files and compare scores:

```bash
# Variant A: current SKILL.md
cd step-4-iterative
claude "Research: Compare NAS approaches..."
python ../benchmark/evaluate.py --input output.md --quick --question "Compare NAS approaches..."

# Variant B: modified SKILL.md (e.g., added explicit analysis instructions)
# Edit SKILL.md, then:
claude "Research: Compare NAS approaches..."
python ../benchmark/evaluate.py --input output.md --quick --question "Compare NAS approaches..."
```

Compare the raw sub-signal counts in the justification strings. Did `analysis_phrases` go from 4 to 12? That's a confirmed improvement.

### Dimension Targeting

If your scores are Comprehensiveness=7, Insight=3, Instruction Following=6, Readability=5:

1. **Insight is the bottleneck** (3/10, weighted at 35% = costs you 2.45 weighted points per point missed)
2. Comprehensiveness at 7 is decent — improving it from 7 to 8 gains 0.30 weighted points
3. Insight from 3 to 6 gains 1.05 weighted points — 3.5x more impact

Always fix the lowest-scoring, highest-weighted dimension first. Priority order:

| Dimension | Weight | Points lost per 1-point deficit |
|-----------|--------|-------------------------------|
| Insight | 0.35 | 3.5 |
| Comprehensiveness | 0.30 | 3.0 |
| Instruction Following | 0.20 | 2.0 |
| Readability | 0.15 | 1.5 |
| Citation Bonus | 0.10 | 1.0 |

### Reference Calibration

Use the `--reference` flag to understand what a high-scoring report looks like:

```bash
python benchmark/evaluate.py \
  --input your-output.md \
  --reference benchmark/reference/practice-1-nas.md \
  --question "Compare the three main approaches to neural architecture search..."
```

Available reference reports:
- `benchmark/reference/practice-1-nas.md` (NAS comparison)
- `benchmark/reference/practice-2-foundation-models.md` (Foundation models)
- `benchmark/reference/practice-3-moe-scaling.md` (MoE scaling laws)
- `benchmark/reference/test-1-quantum.md` (Ion trap quantum computing)
- `benchmark/reference/test-2-a2a-mcp.md` (A2A vs MCP protocols)
- `benchmark/reference/test-3-metal-ions.md` (Metal ions)

Read a reference report with `cat benchmark/reference/practice-1-nas.md` and note:
- How many `##` sections it has
- How many times "because", "therefore", "however" appear
- How many URLs, quoted titles, year references
- Whether it has tables, connectors, a References section

Then compare those counts to your output. The gap tells you exactly what to add.

### Setting Up Self-Improving Loops

The most powerful optimization technique is a **closed-loop system** where the agent's output feeds back into improving the agent itself. This is eval-driven development.

#### The Basic Loop

```
┌─────────────────────────────────────────────────┐
│  1. Run agent on a question                      │
│  2. Score output with evaluate.py                │
│  3. Identify lowest RACE dimension               │
│  4. Edit SKILL.md with targeted fix              │
│  5. Re-run on SAME question                      │
│  6. Compare scores — did the fix help?           │
│  7. If yes: keep the change. If no: revert.      │
│  8. Move to next-lowest dimension. Repeat.       │
└─────────────────────────────────────────────────┘
```

Run this manually first to build intuition:

```bash
# Round 1: baseline
python benchmark/evaluate.py --input output-v1.md --quick --question "..." --verbose
# Look at: which dimension is lowest? What's the _source_factor?

# Round 2: after targeted SKILL.md edit
python benchmark/evaluate.py --input output-v2.md --quick --question "..." --verbose
# Compare: did the targeted dimension improve? Did others regress?
```

#### Automated Self-Improvement with Optimize-Anything

The [optimize-anything](https://github.com/rachittshah/deep-research) pattern automates this loop using **reflective mutation**:

1. **Candidate generation**: Claude reads the current SKILL.md + the eval scores and proposes N mutations (e.g., "add conflict detection instruction", "strengthen citation requirements")
2. **Evaluation**: Each candidate runs against a held-out test set and gets scored
3. **Selection**: Best candidate becomes the new baseline
4. **Reflection**: The optimizer reflects on why the winner won and uses that insight to guide next round's mutations
5. **Repeat**: 5-7 rounds typically converge

This is the same pattern behind the deep-research plugin's 4.56/5.00 score. Each round of reflective mutation targeted a specific weakness:

| Round | Weakness Identified | Fix Applied | Score Impact |
|-------|-------------------|-------------|-------------|
| 1 | Generic search queries | Added site: filters, date qualifiers | Completeness +0.3 |
| 2 | No contradiction handling | Added explicit contradiction format | Balance +0.4 |
| 3 | Diminishing returns in search | 3-query saturation rule | Efficiency, no score drop |
| 4 | Corroboration not tracked | Evidence-weighing hierarchy in critic | Accuracy +0.2 |
| 5 | Wikipedia reliance | Wikipedia banned (weight 0.0) | Source Credibility +0.3 |
| 6 | URL mismatches | "Every URL must be fetched in this session" | Citation Quality +0.2 |
| 7 | Temporal inconsistencies | "Publication year ≥ data year" rule | Accuracy +0.1 |

#### Building Your Own Eval Loop

For the workshop, the simplest self-improving loop:

```bash
#!/bin/bash
# self-improve.sh — Run 3 rounds of eval-driven optimization
QUESTION="Your research question here"

for round in 1 2 3; do
  echo "=== Round $round ==="
  # Run the agent (adjust step as needed)
  echo "$QUESTION" | claude -p --model sonnet \
    --system-prompt "$(cat step-1-context/CLAUDE.md)
---
$(cat your-skill/SKILL.md)" \
    --allowedTools "WebSearch,WebFetch,Read,Write" \
    > "output-round-${round}.md" 2>/dev/null

  # Score it
  python benchmark/evaluate.py \
    --input "output-round-${round}.md" \
    --quick --question "$QUESTION" --verbose

  echo "Review scores above. Edit SKILL.md to fix the lowest dimension."
  echo "Press Enter when ready for next round..."
  read
done
```

Run this and manually edit SKILL.md between rounds. After 3 rounds, you'll have a measurably better agent.

#### Eval-Driven Development: The Verification Loop (Tier 2)

For students building verification: the verification agent IS a self-improving loop. It catches errors and feeds corrections back:

```
Research agent → draft report → Verification agent → error list → Research agent corrects
```

This is the same pattern at the agent level: generate → evaluate → fix. The verification agent is your eval. When it flags a hallucinated paper, that's the same signal as a low RACE score — it tells you exactly what to fix.

### The Deep-Research Plugin Pattern

The [deep-research plugin](https://github.com/rachittshah/deep-research) scored **4.56/5.00** on DeepResearch-Bench through 7 rounds of reflective mutation. The key pattern:

1. Start with a working agent (equivalent to step 4)
2. Run against benchmark tasks
3. Score with RACE
4. Identify the lowest dimension
5. Add targeted instructions to the SKILL.md for that dimension
6. Re-score
7. Repeat for 7 rounds of reflective mutation

This is the same Build-Score-Diagnose-Fix loop in this guide, applied systematically over multiple rounds.

To run your agent against DeepResearch-Bench:

```bash
# Clone the bench
git clone https://github.com/Ayanamo0730/deep_research_bench.git /tmp/deep_research_bench
cd /tmp/deep_research_bench && pip install -r requirements.txt && cd -

# Run 3 tasks (quick test, ~15 min, ~$3-5)
bash benchmark/deepresearch-bench/adapter.sh \
  --bench-dir /tmp/deep_research_bench \
  --step 6 \
  --max 3
```

Target scores by step:

| Step | Expected DeepResearch-Bench Score |
|------|----------------------------------|
| 2 | 1.5-2.5 / 5.00 |
| 3-4 | 2.5-3.5 / 5.00 |
| 5-6 | 3.5-4.5 / 5.00 |
| Optimized (7+ rounds) | 4.5+ / 5.00 |

---

## 5. Competition Strategy

### Step-by-step Progression

Match each practice problem to the step that matters most:

| Practice Problem | Key Step | Why |
|-----------------|----------|-----|
| Practice 1: NAS comparison | Step 2 (SKILL.md) | Topic is in training data. Structure and specificity matter, not tools. |
| Practice 2: Q1 2026 models | Step 3-4 (tools + iteration) | Requires real-time data. One pass misses models. |
| Practice 3: MoE scaling laws | Step 5-6 (verification + critic) | Conflicting results need verification and methodology analysis. |

**Recommended progression:**

```
Time 0:00 - 0:10  → Step 0-1: Get CLAUDE.md working. Score practice-1.
Time 0:10 - 0:25  → Step 2: Write SKILL.md. Score practice-1. Target: 35+
Time 0:25 - 0:45  → Step 3: Add MCP server + tools. Score practice-2. Target: 55+
Time 0:45 - 1:00  → Step 4: Add iteration. Score practice-2. Target: 70+
Time 1:00 - 1:20  → Step 5: Add verification agent. Score practice-3. Target: 80+
Time 1:20 - 1:30  → Step 6: Add team (critic + synthesizer). Score practice-3. Target: 90+
```

### Score After Every Change

Track your scores in a table:

```
| Change Made                    | Practice | Heuristic | Delta |
|-------------------------------|----------|-----------|-------|
| Baseline (step 0)            | P1       | 18        | --    |
| Added CLAUDE.md              | P1       | 21        | +3    |
| Added SKILL.md               | P1       | 37        | +16   |
| Added MCP tools              | P2       | 55        | +18   |
| Added iteration              | P2       | 68        | +13   |
| Added verification agent     | P3       | 85        | +17   |
| Added critic + synthesizer   | P3       | 93        | +8    |
```

The staircase should be monotonically increasing. If adding a step DECREASES your score, something is misconfigured.

### Time Allocation

**Do not spend 60 minutes on step 2 when step 3 gives +18 points.**

The source grounding factor means:
- Steps 0-2 are hard-capped around 35-50 points regardless of output quality
- Step 3 (adding tools) typically gives the single largest jump
- Step 5 (verification) gives the second-largest jump

If you're at 35 points and have 30 minutes left: skip to step 3, not "improve my SKILL.md more."

Expected score ranges from `benchmark/verify_staircase.py`:

```python
EXPECTED_TIERS = {
    0: (10, 30),
    1: (15, 35),
    2: (25, 50),
    3: (40, 70),
    4: (40, 75),
    5: (70, 100),
    6: (75, 100),
}
```

### Customize Team Structure Based on Bottleneck

If your step-4 output scores low on a specific dimension, customize which agent you add in step 5-6:

| Bottleneck Dimension | Add This Agent | Why |
|---------------------|----------------|-----|
| Insight | Critic agent | Adds STRONG/MODERATE/WEAK ratings, conflict analysis |
| Comprehensiveness | Searcher agent with more rounds | More sources, more attributed claims |
| Citation Bonus | Dedicated citation-checker agent | Verifies URLs resolve, adds arXiv IDs |
| Instruction Following | Orchestrator with question-parsing | Ensures every keyword is covered before synthesis |
| Readability | Synthesizer with strict template | Enforces structure, tables, connectors |

---

## 6. Common Optimization Mistakes

### 1. Over-engineering CLAUDE.md

**Symptom:** 50+ lines of CLAUDE.md with elaborate personality, backstory, detailed domain knowledge.

**Problem:** CLAUDE.md is WHO, not HOW. After ~15-20 lines, additional identity text causes the model to spend tokens re-reading context that doesn't improve methodology. Worse, long CLAUDE.md can push SKILL.md instructions out of the effective attention window.

**Fix:** Keep CLAUDE.md under 20 lines. Domain, preferences, constraints. Move everything else to SKILL.md.

### 2. Adding Tools Without Updating `allowed-tools`

**Symptom:** You added `search_pubmed` to `arxiv_server.py` but the agent never calls it.

**Problem:** The SKILL.md frontmatter has an `allowed-tools` field that gates tool access:

```yaml
allowed-tools: WebSearch WebFetch Read Write mcp__research-tools__search_arxiv mcp__research-tools__search_semantic_scholar
```

If `mcp__research-tools__search_pubmed` isn't listed, the skill cannot use it.

**Fix:** After adding any tool to the MCP server, update the `allowed-tools` line in EVERY relevant SKILL.md file.

### 3. Making Iteration Infinite

**Symptom:** Agent runs 8+ search rounds, spends 10 minutes, and produces only marginally better output.

**Problem:** No hard cap on iteration rounds. The "evaluate coverage" step always finds more gaps.

**Fix:** Always set a max rounds limit:

```markdown
- If still gaps: do ONE more targeted round (max 3 rounds total)
```

The step-4 SKILL.md caps at 3 rounds. Going beyond 3 has sharply diminishing returns: round 1 gets 60% of sources, round 2 gets 25%, round 3 gets 10%, round 4+ gets noise.

### 4. Verification Agent That Shares Context

**Symptom:** Verification agent says "VERIFIED" for everything, including hallucinated sources.

**Problem:** The verification agent was given context from the research phase (e.g., via shared conversation history or pasted findings). It "remembers" the research agent's reasoning and inherits its confidence in hallucinated claims.

**Fix:** The verification agent MUST be spawned as a separate `Agent` tool call with its own context window. It should ONLY read the output file (`research_draft.md`), never see the search results or reasoning that produced it.

From `step-5-verification/.claude/skills/verify-research/SKILL.md`:

```markdown
You run in your own context window. You don't share memory with the
research agent that produced this report. This is intentional — you
need fresh eyes, not the research agent's reasoning and biases.
```

### 5. Team Agents That Duplicate Work

**Symptom:** The searcher, critic, and synthesizer all search for papers. The final report is three agents' worth of work but only marginally better than one.

**Problem:** Role boundaries are not enforced. Each agent does a little of everything instead of specializing.

**Fix:** Each agent's SKILL.md must start with what it does NOT do:

```markdown
# Searcher: "You do NOT evaluate quality. You do NOT synthesize."
# Critic: "You do NOT search for new information."
# Synthesizer: "You do NOT search. You do NOT critique."
```

And enforce via tools: the synthesizer gets only `Read, Write` — no search tools. If it can't search, it can't duplicate the searcher's work.

### 6. Not Using `--question` During Evaluation

**Symptom:** Instruction_following scores are low even though your output covers the question well.

**Problem:** Without the `--question` flag, instruction_following falls back to structural heuristics (section count + conclusion) instead of keyword coverage analysis. This is less sensitive to actual question-answer alignment.

**Fix:** Always pass the question when scoring:

```bash
python benchmark/evaluate.py \
  --input output.md \
  --quick \
  --question "What are the most effective approaches to scaling ion trap quantum computing..."
```

### 7. Ignoring the Source Factor When Debugging

**Symptom:** Your raw sub-signal scores are high but your total is low. You keep improving the report text with no score movement.

**Problem:** The source grounding factor is capping your total. Your raw total might be 70 but `factor=0.35` reduces it to 24.5.

**Fix:** Check `--verbose` output for `_source_factor` and `_raw_total`:

```bash
python benchmark/evaluate.py --input output.md --quick --verbose
```

Look at the bottom of the JSON output:

```json
{
  "weighted_total": 24.5,
  "_raw_total": 70.0,
  "_source_factor": 0.35
}
```

If `_source_factor < 0.7`, your problem is not report quality — it's lack of external sources. Add tools (step 3) or verification (step 5) to unlock the factor.

---

## Quick Reference: What Earns Points

| To earn this... | Add this to your SKILL.md or agent... |
|----------------|---------------------------------------|
| +2 comprehensiveness (attributed claims) | "Attribute every number: 'Author reported X%'" |
| +2 comprehensiveness (perspectives) | "Cover at least 3 approaches/methods/techniques" |
| +1 comprehensiveness (gaps) | "Include ## Open Questions listing limitations" |
| +4 insight (analysis phrases) | "Use: because, therefore, suggests, implies, this means, as a result" |
| +3 insight (conflicts) | "Include ## Where Experts Disagree with however, despite, on the other hand" |
| +3 insight (forward-looking) | "Include ## Future Directions with emerging, promising, potential" |
| +2 insight (evidence quality) | Add critic agent with STRONG/MODERATE/WEAK ratings |
| +1 insight (verification) | Add verification agent with verified/unverified markers |
| +8 instruction_following (coverage) | "Echo every keyword from the original question in your output" |
| +2 readability (thesis) | "Start with # Title: One-sentence thesis" |
| +2 readability (references) | "End with ## References section" |
| +1 readability (table) | "Include at least one comparison table" |
| +2 readability (connectors) | "Start paragraphs with: First, Moreover, Furthermore, Specifically" |
| +3 citation_bonus (URLs) | Use MCP tools (search_arxiv, search_semantic_scholar) |
| +2 citation_bonus (titles) | "Quote all paper titles in double quotes" |
| +2 citation_bonus (arXiv IDs) | Use search_arxiv tool — returns arxiv.org URLs automatically |
| +2 citation_bonus (years) | "Format citations as Author (Year)" |
| Unlock 1.0 source factor | Add verification agent OR critic with evidence quality ratings |
