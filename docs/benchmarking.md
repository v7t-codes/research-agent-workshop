# Benchmarking Guide: Scoring and Evaluation

This document covers every detail of how research agent outputs are scored in this workshop: the RACE framework, the two scoring modes (heuristic and LLM), evaluation commands, problem definitions, staircase verification, and DeepResearch-Bench integration.

---

## 1. The RACE Framework

RACE scores research reports on four weighted dimensions plus an additive citation bonus. The total scale is 0-100.

### Dimensions and Weights

| Dimension | Weight | What It Measures |
|---|---|---|
| Comprehensiveness | 30% | Coverage breadth, data support, multiple perspectives |
| Insight | 35% | Analysis depth, causal reasoning, problem insight |
| Instruction Following | 20% | Response to objectives, scope adherence, addressing all parts |
| Readability | 15% | Structure, clarity, logical flow, formatting |
| Citation Bonus | +10% (additive) | Real URLs, paper titles, verifiable citations |

Each dimension is scored 0-10. The weighted total is computed as:

```
weighted_total = (comprehensiveness * 0.30 + insight * 0.35 + instruction_following * 0.20 + readability * 0.15 + citation_bonus * 0.10) * 10
```

Maximum possible: 110 raw points (100 from RACE + 10 from citation bonus), capped at 100 after source grounding adjustment.

### Per-Dimension Criteria

**Comprehensiveness (30%)** -- Each criterion contributes to the 0-10 score:
1. Covers all major sub-topics of the research question
2. Includes specific data points and numbers (not vague claims)
3. Represents multiple perspectives and approaches
4. Uses diverse sources (not just one type)
5. Identifies what is NOT covered (gaps acknowledged)

**Insight (35%)** -- The highest-weighted dimension:
1. Goes beyond surface-level descriptions to analysis
2. Identifies causal relationships and mechanisms
3. Compares and contrasts approaches with specific trade-offs
4. Identifies where sources conflict and explains why
5. Provides forward-looking assessment of open problems

**Instruction Following (20%)**:
1. Addresses every part of the original question
2. Stays within scope (not padding with tangential content)
3. Follows any format or structure requirements in the question
4. Provides the type of analysis requested (comparison, evaluation, etc.)
5. Appropriate depth for the question's complexity

**Readability (15%)**:
1. Clear thesis or summary statement upfront
2. Organized by theme, not by source
3. Logical flow between sections
4. Professional academic tone
5. Properly formatted references and citations

**Citation Bonus (+10%)** -- Additive, not part of base RACE:
- Real URLs present in the report
- Real paper titles in quotes
- arXiv IDs (e.g., `arxiv.org/abs/2501.12948`)
- Year references in parentheses (e.g., `(2024)`)
- DOI references (e.g., `doi.org/...`)

### Quality Level Mapping

| Score Range | Quality Level | Typical Step |
|---|---|---|
| 80-100 | Excellent -- verification + team level | Steps 5-6 |
| 55-79 | Strong -- tool-augmented + iterative | Steps 3-4 |
| 40-54 | Good -- tool-augmented | Step 3 |
| 30-39 | Basic -- skill with methodology | Step 2 |
| 15-29 | Minimal -- context only | Steps 0-1 |
| 0-14 | Below baseline | Check output |

---

## 2. Two Scoring Modes

### Heuristic Scoring (`--quick`)

Fast, free, deterministic. Uses regex pattern matching and structural analysis. No API call required. Good for rapid iteration during development. **This is what you use while building.**

#### How It Works

The heuristic scorer extracts features from the report text via regex, computes a raw score per dimension, then applies a **source grounding factor** that scales the final score based on evidence of real external sources.

#### Comprehensiveness Scoring (Heuristic)

Features extracted and their contribution (each capped):

| Feature | Regex Pattern | Max Contribution |
|---|---|---|
| Sections | `^##\s+` (multiline) | `min(sections // 2, 2)` = max 2 |
| Attributed claims | `(?:according to\|reported\|found\|showed\|achieved\|demonstrated).*?\d+` | `min(count, 2)` = max 2 |
| Numerical claims | `\d+\.?\d*%\|\d+\.?\d*x\|\$\d+\|\d+[MBK]\b\|\d+\.\d+ ` | `min(count // 5, 2)` = max 2 |
| Perspectives | `approach\|method\|technique\|strategy\|framework\|model\|algorithm` | `min(count // 4, 2)` = max 2 |
| Gaps mentioned | `gap\|limitation\|not covered\|open question\|remain\|unclear` | `min(count, 1)` = max 1 |
| URLs | `https?://\S+` | `min(count // 3, 1)` = max 1 |

**Maximum heuristic comprehensiveness: 10** (sum of all caps).

#### Insight Scoring (Heuristic)

| Feature | Regex Pattern | Max Contribution |
|---|---|---|
| Analysis phrases | `because\|therefore\|suggests\|implies\|trade-off\|compared to\|in contrast\|whereas\|due to\|this means\|as a result\|consequently\|this indicates` | `min(count // 2, 4)` = max 4 |
| Conflict phrases | `however\|disagree\|conflict\|debate\|contrary\|challenge\|limitation\|caveat\|on the other hand\|alternatively\|despite\|nevertheless` | `min(count, 3)` = max 3 |
| Forward-looking | `future\|open problem\|remain\|promising\|emerging\|potential\|outlook` | `min(count // 2, 3)` = max 3 |
| Evidence quality | `\bevidence quality\b\|\bSTRONG\b\|\bMODERATE\b\|\bWEAK\b` (case-sensitive) | `min(count // 3, 2)` = max 2 |
| Verification markers | `\bverified\b\|\bunverified\b\|\bhallucinated\b\|\bcorrection` | `min(count // 2, 1)` = max 1 |

**Maximum heuristic insight: 13** (capped at 10). Evidence quality and verification markers are what separate steps 5-6 from steps 0-4 in heuristic scoring.

#### Instruction Following Scoring (Heuristic)

**With question provided** (`--question` flag):
1. Extract all 4+ character keywords from the question
2. Count how many appear in the report text (case-insensitive)
3. Coverage ratio = matched / total keywords
4. Base score = `coverage * 8`
5. Bonus +1 if question asks for comparison and report contains comparison language
6. Bonus +1 if question asks for numbers and report has `> 3` numerical claims
7. Final: `min(10, base + bonuses)`

**Without question** (structural proxy):
- Sections present: `min(sections, 4)`
- Has conclusion/summary: +2
- Has title heading: +2
- Final: `min(10, sum)`

#### Readability Scoring (Heuristic)

| Feature | Regex Pattern | Max Contribution |
|---|---|---|
| Thesis (title heading) | `^#\s+.+` | 2 |
| Sections | `^##\s+` | `min(count, 3)` = max 3 |
| Table | `\|.*\|.*\|` + `---` | 1 |
| Connectors | `^(First\|Second\|Third\|Finally\|Moreover\|Furthermore\|In addition\|Specifically)` at start of line | `min(count, 2)` = max 2 |
| References section | `^##\s*(References\|Sources\|Bibliography\|Works Cited)` | 2 |

**Maximum heuristic readability: 10.**

#### Citation Bonus Scoring (Heuristic)

| Feature | Regex Pattern | Max Contribution |
|---|---|---|
| URLs | `https?://\S+` | `min(count, 3)` = max 3 |
| Paper titles | `"[A-Z][^"]{15,}"` (quoted, 15+ chars, starts with capital) | `min(count, 2)` = max 2 |
| arXiv IDs | `arxiv\.org/abs/\d{4}\.\d+` | `min(count, 2)` = max 2 |
| Year references | `\(\d{4}\)` | `min(count // 2, 2)` = max 2 |
| DOI references | `doi\.org/` | `min(count, 1)` = max 1 |

**Maximum heuristic citation bonus: 10.**

#### The Source Grounding Factor

This is the critical mechanism that creates the scoring staircase. After computing the raw weighted total, the heuristic applies a multiplicative factor based on evidence of real external sources. This is why steps 0-2 (no tools, no URLs) score dramatically lower than steps 3+ (tools produce real URLs).

The factor is determined by a priority chain of conditions (first match wins):

| Condition | Factor Range | Staircase Steps | What Triggers It |
|---|---|---|---|
| `urls < 5` AND `evidence_quality < 3` | 0.35 - 0.55 | Steps 0-2 (no tools) | No real external sources. `factor = 0.35 + min(attributed_claims / 20, 0.15) + min(insight_score / 100, 0.05)` |
| `evidence_quality >= 3` | 1.00 - 1.05 | Steps 5-6 (team/critic) | STRONG/MODERATE/WEAK ratings present. `factor = 1.0 + min(evidence_quality / 100, 0.05)` |
| `verification_markers >= 3` AND `urls >= 10` | 1.00 | Step 5 (verification) | Verified/unverified/hallucinated markers + real sources |
| `urls >= 10` | 0.70 - 0.80 | Steps 3-4 (tools) | External sources present, no verification. `factor = 0.70 + min(urls / 200, 0.10)` |
| (else) | 0.55 | Edge case | 5-9 URLs, no evidence quality or verification markers |

**Final score**: `min(100, raw_total * factor)`

#### Known Limitations of Heuristic Scoring

1. **Step 3/4 inversion**: Step 4 (iterative) can score lower than step 3 (one-pass) in heuristic mode because both hit the same `urls >= 10` factor range (~0.70-0.80). The iteration quality improvement only shows up in LLM scoring. The architecture table in CLAUDE.md shows step 3 at ~58 heuristic, step 4 at ~53 heuristic, but step 4 at ~72 LLM vs step 3 at ~55 LLM.
2. **Keyword sensitivity**: The heuristic rewards using specific words (e.g., "however", "STRONG", "verified"). An adversarial report could game the heuristic by stuffing these keywords.
3. **No semantic understanding**: The heuristic cannot judge whether analysis is actually insightful or whether claims are correctly attributed. It counts surface markers only.
4. **Near-empty guard**: Reports under 100 words score 0 across all dimensions.

### LLM Scoring (no `--quick`)

Uses Claude Sonnet 4.6 as an LLM judge. Costs ~1 API call per evaluation. Requires `ANTHROPIC_API_KEY` environment variable. **This is the authoritative scoring mode for final evaluation.**

#### How It Works

1. `build_evaluation_prompt()` constructs a detailed prompt containing:
   - All RACE dimension definitions with their criteria
   - Citation bonus instructions (weight: 0.10)
   - The original research question (if provided via `--question`)
   - A reference report for calibration (if provided via `--reference`, first 8000 chars)
   - The report to evaluate (first 12000 chars)
   - Explicit JSON output format with scoring instructions
2. The prompt is sent to `claude-sonnet-4-6` with `max_tokens=2000`
3. The response is parsed for JSON: first tries `\`\`\`json ... \`\`\`` blocks, then falls back to finding a JSON object containing `"weighted_total"`
4. If JSON extraction fails, falls back to heuristic scoring with a warning

#### The Evaluation Prompt Structure

```
You are a research report evaluator using the RACE framework.

[Per-dimension definitions with criteria]
[Citation bonus definition]

## Original Research Question   <-- only if --question provided
## Reference Report             <-- only if --reference provided (first 8000 chars)
## Report to Evaluate           <-- first 12000 chars

## Instructions
For each dimension:
1. Assess each criterion (met / partially met / not met)
2. Give a score from 0-10
3. Provide a one-line justification

Be rigorous. 7+ means clearly met with strong evidence. 5 means adequate. Below 5 means significant gaps.
```

#### How Reference Reports Calibrate Scoring

When you provide `--reference`, the reference report is included in the prompt with this instruction:

> "Use this high-quality reference to calibrate scoring. A perfect score should match or exceed this quality."

This anchors the LLM judge to a known-quality baseline. Without a reference, the LLM scores in absolute terms (often more generous). With a reference, it has a concrete ceiling to compare against.

#### Cost

- 1 API call per evaluation
- Input: ~12000 chars of report + ~2000 chars of prompt + optional ~8000 chars of reference = ~5000-15000 tokens
- Output: ~500-1000 tokens (JSON + justifications)
- Estimated cost: $0.02-0.08 per evaluation depending on report and reference length

---

## 3. Evaluation Commands

### Quick Heuristic Score (instant, free)

```bash
python benchmark/evaluate.py --input output.md --quick
```

### Quick Score with Question Context (improves instruction-following scoring)

```bash
python benchmark/evaluate.py --input output.md --quick \
  --question "What are the most effective approaches to scaling ion trap quantum computing..."
```

### LLM Score (requires ANTHROPIC_API_KEY)

```bash
python benchmark/evaluate.py --input output.md
```

### LLM Score with Reference Calibration

```bash
python benchmark/evaluate.py --input output.md \
  --reference benchmark/reference/test-1-quantum.md
```

### LLM Score with Question + Reference (most accurate)

```bash
python benchmark/evaluate.py --input output.md \
  --question "What are the most effective approaches to scaling ion trap quantum computing..." \
  --reference benchmark/reference/test-1-quantum.md
```

### Verbose Output (shows raw JSON scores)

```bash
python benchmark/evaluate.py --input output.md --quick --verbose
```

With `--verbose`, you get the raw scores dict including hidden fields:
- `_raw_total`: The score before source grounding factor is applied
- `_source_factor`: The multiplicative factor applied (reveals which tier you're in)

### Batch Scoring (all test problems)

```bash
for i in 1 2 3; do
  echo "=== Test Problem $i ==="
  python benchmark/evaluate.py --input "output-test-${i}.md" --quick \
    --question "$(head -6 benchmark/test/test-${i}.md | tail -1)"
done
```

### Scoring with Full Context (recommended for final evaluation)

```bash
# Test problem 1 (quantum computing)
python benchmark/evaluate.py \
  --input output-test-1.md \
  --question "What are the most effective approaches to scaling ion trap quantum computing from small-scale demonstration projects to large-scale systems capable of solving real-world problems? For each approach, provide specific technical results from 2024-2026, identify the key engineering challenges that remain, and assess where the research community disagrees on the most promising path forward." \
  --reference benchmark/reference/test-1-quantum.md

# Test problem 2 (A2A vs MCP)
python benchmark/evaluate.py \
  --input output-test-2.md \
  --question "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation." \
  --reference benchmark/reference/test-2-a2a-mcp.md

# Test problem 3 (metal ions + cardiovascular)
python benchmark/evaluate.py \
  --input output-test-3.md \
  --question "Could therapeutic interventions aimed at modulating plasma metal ion concentrations represent effective preventive or therapeutic strategies against cardiovascular diseases? What types of interventions have been proposed, and is there clinical evidence supporting their feasibility and efficacy? Provide specific trial results, mechanisms of action, and identify where the clinical evidence is conflicting or insufficient." \
  --reference benchmark/reference/test-3-metal-ions.md
```

---

## 4. The Problems

### Practice Problems

These are for development and tuning. Each targets specific workshop steps.

#### Practice 1: Neural Architecture Search (Steps 1-2 warmup)

- **File**: `benchmark/practice/practice-1.md`
- **Question**: Compare three NAS approaches (weight-sharing, evolutionary, differentiable) -- core mechanisms, key papers, which is dominant
- **Domain**: ML/AI (well-covered in training data)
- **Why this problem**: Topic is in training data, so tools add marginal value. Tests whether CLAUDE.md + SKILL.md can turn a generic essay into a structured research report
- **Expected ceilings**: Step 0 ~18, Step 1 ~25, Step 2 ~55, Step 3+ ~65 (diminishing returns)
- **Reference**: `benchmark/reference/practice-1-nas.md`
- **Criteria**: `benchmark/criteria/practice-1-nas.json`

#### Practice 2: Q1 2026 Foundation Models (Steps 3-4 -- forces tools)

- **File**: `benchmark/practice/practice-2.md`
- **Question**: New foundation models released in Q1 2026 -- org, size, architecture, benchmarks, training techniques, most significant release
- **Domain**: AI (requires very recent information beyond training data)
- **Why this problem**: Claude's training data cannot fully answer this. Without tools, you get hallucinated model names and made-up benchmarks. Single search pass misses models; iteration is required for coverage
- **Expected ceilings**: Steps 0-2 ~20 (hallucinations), Step 3 ~50 (one pass misses models), Step 4 ~75 (multiple rounds), Steps 5-6 ~85
- **Reference**: `benchmark/reference/practice-2-foundation-models.md`
- **Criteria**: `benchmark/criteria/practice-2-foundation-models.json`

#### Practice 3: MoE Scaling Laws (Steps 5-6 -- forces verification)

- **File**: `benchmark/practice/practice-3.md`
- **Question**: Evidence on MoE scaling laws vs dense model scaling -- published results, researcher disagreements, methodological differences explaining conflicts
- **Domain**: ML (genuinely conflicting results in the literature)
- **Why this problem**: Different papers measure "efficiency" differently (total params vs active params vs FLOPs). Without verification, hallucinated papers pass through. Without a critic, real methodology disagreements are glossed over
- **Expected ceilings**: Steps 0-2 ~25, Steps 3-4 ~55 (finds papers but may hallucinate numbers), Step 5 ~75 (catches hallucinated citations), Step 6 ~90 (critic surfaces methodology disagreements)
- **Reference**: `benchmark/reference/practice-3-moe-scaling.md`
- **Criteria**: `benchmark/criteria/practice-3-moe-scaling.json`

### Test Problems

These are UNSEEN during development. Run your agent on them without modification. Scores reflect how general your agent is.

#### Test 1: Ion Trap Quantum Computing (Science and Technology)

- **File**: `benchmark/test/test-1.md`
- **Question**: Most effective approaches to scaling ion trap quantum computing -- technical results 2024-2026, engineering challenges, community disagreements
- **Domain**: Quantum computing (requires current technical depth)
- **Source**: Adapted from Deep Research Bench (Science and Technology category)
- **Reference**: `benchmark/reference/test-1-quantum.md`
- **Criteria**: `benchmark/criteria/test-1-quantum.json`

#### Test 2: A2A vs MCP Protocols (Software / AI Systems)

- **File**: `benchmark/test/test-2.md`
- **Question**: Detailed comparison of Google A2A and Anthropic MCP -- architecture, use cases, adoption, complementary vs competing
- **Domain**: AI infrastructure (requires very recent information -- A2A is recent)
- **Source**: Adapted from Deep Research Bench (Software Development category)
- **Reference**: `benchmark/reference/test-2-a2a-mcp.md`
- **Criteria**: `benchmark/criteria/test-2-a2a-mcp.json`

#### Test 3: Metal Ions and Cardiovascular Disease (Cross-Disciplinary)

- **File**: `benchmark/test/test-3.md`
- **Question**: Therapeutic interventions modulating plasma metal ion concentrations for cardiovascular disease -- trial results, mechanisms, conflicting evidence
- **Domain**: Biomedical (deliberately outside most CS students' comfort zone)
- **Source**: Adapted from Deep Research Bench (Health category)
- **Why it matters**: Tests whether the agent is genuinely general. The methodology should work regardless of domain knowledge
- **Reference**: `benchmark/reference/test-3-metal-ions.md`
- **Criteria**: `benchmark/criteria/test-3-metal-ions.json`

### Reference Reports

Location: `benchmark/reference/`

Reference reports are high-quality exemplars used to calibrate LLM scoring. When provided via `--reference`, the first 8000 characters are included in the evaluation prompt so the LLM judge has a concrete quality ceiling.

Available references:
- `benchmark/reference/practice-1-nas.md`
- `benchmark/reference/practice-2-foundation-models.md`
- `benchmark/reference/practice-3-moe-scaling.md`
- `benchmark/reference/test-1-quantum.md`
- `benchmark/reference/test-2-a2a-mcp.md`
- `benchmark/reference/test-3-metal-ions.md`

Reference quality level (from `test-2-a2a-mcp.md`): Opens with a structured executive summary, uses numbered sections (I through VII+), includes inline citations with footnote numbers, covers architecture/primitives/use cases with technical specifics, and provides comparative analysis tables.

Reference quality level (from `practice-2-foundation-models.md`): Chronologically organized with per-model sections, includes specific benchmark numbers (e.g., "SWE-bench Verified: 80.8%"), covers architecture details, training techniques, and cross-cutting analysis.

### Criteria JSON Files

Location: `benchmark/criteria/`

Each problem has a criteria JSON file used by DeepResearch-Bench evaluation. Structure:

```json
{
  "id": 62,
  "prompt": "Full text of the research question...",
  "dimension_weight": {
    "readability": 0.15,
    "insight": 0.39,
    "comprehensiveness": 0.3,
    "instruction_following": 0.16
  },
  "criterions": {
    "comprehensiveness": [
      {
        "criterion": "Coverage of Diverse Ion Trap Scaling Strategies",
        "explanation": "Assesses if the article comprehensively identifies...",
        "weight": 0.25
      }
    ],
    "insight": [...],
    "readability": [...],
    "instruction_following": [...]
  }
}
```

Note: The `dimension_weight` in criteria JSON files may differ slightly from the workshop RACE weights (e.g., insight 0.39 vs 0.35). The criteria JSON weights come from the original Deep Research Bench prompts. The workshop evaluator (`evaluate.py`) uses its own fixed weights defined in the `DIMENSIONS` dict.

---

## 5. Staircase Verification

### What It Is

`benchmark/verify_staircase.py` confirms that the scoring system produces a monotonically increasing staircase across workshop steps. It scores step-0 through step-6 outputs using the heuristic and checks that each falls within its expected tier.

### How to Run

```bash
# Heuristic only (no API calls)
python benchmark/verify_staircase.py

# With LLM scoring on steps 0 and 6 (2 API calls)
python benchmark/verify_staircase.py --llm

# Custom outputs directory
python benchmark/verify_staircase.py --outputs-dir path/to/step-outputs
```

Default outputs directory: `test-run/outputs` (expects files named `step-0.md` through `step-6.md`).

### Expected Tiers

| Step | Min Score | Max Score | What the Step Represents |
|---|---|---|---|
| 0 | 10 | 30 | Raw Claude, no context or skill |
| 1 | 15 | 35 | Context only (CLAUDE.md) |
| 2 | 25 | 50 | Skill with methodology (SKILL.md) |
| 3 | 40 | 70 | Custom tools (MCP server) |
| 4 | 40 | 75 | Iterative search (loop) |
| 5 | 70 | 100 | Verification agent (subagent) |
| 6 | 75 | 100 | Team of agents (searcher + critic + synthesizer) |

### Tier Separation Check

The script groups steps into three tiers and reports the gap between them:

| Tier | Steps | Description |
|---|---|---|
| No tools | 0, 1, 2 | Training data only |
| Tools | 3, 4 | Real external sources |
| Verification + Team | 5, 6 | Evidence quality audit |

A healthy staircase has clear gaps between tiers. The gap from "No tools" max to "Tools" min should be positive. The gap from "Tools" max to "Verification + Team" min should be positive.

### The Verification Question

The staircase verification uses the test-2 question (A2A vs MCP) as its benchmark question:

> "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol)..."

### What to Do If a Step Falls Outside Its Tier

1. Check the source grounding factor in verbose output (`[factor=X]` in the verification output)
2. If factor is too low: the report lacks URLs or evidence quality markers for its step level
3. If factor is correct but raw score is low: the report content itself is weak for that step
4. For steps 3-4: ensure the MCP server is actually producing URLs in the output
5. For steps 5-6: ensure `STRONG`/`MODERATE`/`WEAK` ratings and `verified`/`unverified` markers appear in the output
6. The heuristic is approximate. Run `evaluate.py` without `--quick` for definitive scoring

---

## 6. DeepResearch-Bench Integration

### What It Is

[DeepResearch-Bench](https://github.com/Ayanami0730/deep_research_bench) is a benchmark of 100 PhD-level research tasks scored on two axes:
- **RACE**: Report quality (comprehensiveness, insight, instruction following, readability) -- judged by Gemini 2.5 Pro
- **FACT**: Citation accuracy via Jina scraping -- verifies that cited URLs actually contain the claimed information

This is optional. Use it to see how your workshop agent compares to production systems.

### RACE vs FACT Scoring Dimensions

| Aspect | RACE | FACT |
|---|---|---|
| What it measures | Report quality (structure, depth, analysis) | Citation accuracy (do URLs contain the claimed info?) |
| Judge | Gemini 2.5 Pro (LLM) | Jina web scraping (deterministic) |
| Requires | `GEMINI_API_KEY` | `JINA_API_KEY` |
| Score meaning | 50 = parity with reference, >50 = better | Citation accuracy % and effective citation count |
| Workshop evaluator analogue | `evaluate.py` without `--quick` | No direct analogue |

### How the Adapter Works (`adapter.sh`)

The adapter bridges the workshop's step-based system to the bench's JSONL format.

**What it does:**
1. Reads tasks from `$BENCH_DIR/data/test_data/query.jsonl`
2. Filters by language (default: `en`)
3. For each task, builds a system prompt by concatenating the appropriate step's configuration files:
   - Step 2: `CLAUDE.md` + step-2 `SKILL.md`
   - Step 3: `CLAUDE.md` + step-3 `SKILL.md`
   - Step 4: `CLAUDE.md` + step-4 `SKILL.md`
   - Step 5: `CLAUDE.md` + step-5 research `SKILL.md` + step-5 verification `SKILL.md`
   - Step 6: `CLAUDE.md` + step-6 orchestrator + searcher + critic + synthesizer `SKILL.md` files
4. Configures tools based on step:
   - Step 2: No tools
   - Steps 3-4: `WebSearch, WebFetch, Read, Write, mcp__research-tools__search_arxiv, mcp__research-tools__search_semantic_scholar`
   - Steps 5-6: Same + `Agent` tool
5. Runs each task through `claude` CLI with `--dangerously-skip-permissions --no-session-persistence`
6. Outputs JSONL: `{"id": N, "prompt": "...", "article": "..."}`

**Adapter flags:**

| Flag | Default | Description |
|---|---|---|
| `--bench-dir` | (required) | Path to cloned bench repo |
| `--step` | `6` | Workshop step to use (2-6) |
| `--max` | `0` (all) | Limit number of tasks |
| `--model` | `sonnet` | Claude model |
| `--output` | `workshop-step{N}` | Output filename |
| `--lang` | `en` | Language filter: `en`, `zh`, or `all` |

### How Evaluation Works (`run-eval.sh`)

**RACE evaluation** (requires `GEMINI_API_KEY`):
```bash
# Runs deepresearch_bench_race.py from the bench repo
cd $BENCH_DIR && python deepresearch_bench_race.py workshop-step6
```
Results go to `benchmark/deepresearch-bench/results/race-workshop-step6.log`.

**FACT evaluation** (requires `JINA_API_KEY`):
```bash
# Runs the 5-step FACT pipeline from the bench repo:
# 1. extract: pull citations from reports
# 2. deduplicate: remove duplicate citations
# 3. scrape: fetch cited URLs via Jina
# 4. validate: check if scraped content supports claims
# 5. stat: compute aggregate accuracy statistics
```
Results go to `benchmark/deepresearch-bench/results/fact-workshop-step6.log`.

### Quick Start Commands

```bash
# 1. Clone the bench
git clone https://github.com/Ayanamo0730/deep_research_bench.git /tmp/deep_research_bench
cd /tmp/deep_research_bench && pip install -r requirements.txt && cd -

# 2. Run your agent on 3 tasks (quick test)
bash benchmark/deepresearch-bench/adapter.sh \
  --bench-dir /tmp/deep_research_bench \
  --step 6 \
  --max 3

# 3. Score with RACE (requires GEMINI_API_KEY)
bash benchmark/deepresearch-bench/run-eval.sh \
  --bench-dir /tmp/deep_research_bench \
  --model-name workshop-step6

# 4. Or score with workshop evaluator (no Gemini needed)
python benchmark/evaluate.py --input <report.md> --quick
```

### Cost and Time Estimates

| Mode | Tasks | Time | Cost (API) |
|---|---|---|---|
| `--max 3` | First 3 English tasks | ~15 min | ~$3-5 |
| `--max 10` | First 10 tasks | ~45 min | ~$10-20 |
| (default) | All 100 English tasks | ~3-4 hrs | ~$50-150 |

### Reference Scores

The [deep-research plugin](https://github.com/rachittshah/deep-research) (production-grade, optimized through 7 rounds of reflective mutation) scored **4.56/5.00** on 5 bench tasks with Opus 4.6.

Workshop agent target range at step 6: **3.5-4.5** depending on design choices.

### Workshop Evaluator vs Bench RACE

You can use the workshop's own `evaluate.py` as a quick alternative to the bench's Gemini-based RACE:

```bash
# Workshop evaluator (Claude Sonnet judge or heuristic)
python benchmark/evaluate.py --input output.md --question "..."

# Bench RACE (Gemini 2.5 Pro judge, requires GEMINI_API_KEY)
bash benchmark/deepresearch-bench/run-eval.sh --bench-dir /tmp/deep_research_bench --model-name workshop-step6
```

The workshop evaluator is faster and cheaper (single Claude call vs Gemini batch). The bench RACE is more authoritative (Gemini as independent judge, calibrated against the full 100-task dataset).
