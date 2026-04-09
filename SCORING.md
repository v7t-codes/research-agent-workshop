# How Scoring Works

Every research report gets scored 0–100 using the **RACE framework** —
the same methodology used to evaluate Gemini Deep Research, Perplexity,
and other production research systems.

---

## The five dimensions

| Dimension | Weight | What it actually checks |
|-----------|--------|------------------------|
| **Comprehensiveness** | 30% | Did you cover all the sub-questions? Are there specific numbers and data points? Multiple perspectives? |
| **Insight** | 35% | Did you find where sources *disagree*? Did you explain *why* things work the way they do, not just what they are? |
| **Instruction Following** | 20% | Did you answer every part of the question? Did you stay in scope? |
| **Readability** | 15% | Is there a clear thesis? Logical structure? Headers? A references section? |
| **Citation Bonus** | +10% | Are there real, verifiable URLs? arXiv IDs? Paper titles with authors and years? |

---

## The source grounding factor

On top of RACE, a multiplier is applied based on whether your sources are real:

```
No real URLs (training data only)    ×0.35–0.55   score cut by ~50%
10+ real URLs, no verification       ×0.70–0.80   score cut by ~25%
Verified citations section present   ×1.0–1.05    no penalty
```

**This is why the staircase has two cliffs:**
- Step 3 (add MCP tools): factor jumps from 0.45 → 0.75. Real APIs give you real URLs.
- Step 5 (add verification): factor jumps from 0.75 → 1.0. Independent process removes hallucinated sources.

---

## Two scoring modes

```bash
# Fast — heuristic, instant, no API call, use while iterating
python3 benchmark/evaluate.py --input output.md --quick --question "your question"

# Accurate — LLM as judge, ~5 seconds, ~$0.02 per call, use for final score
python3 benchmark/evaluate.py --input output.md --question "your question"
```

Use `--quick` while you're building. Drop `--quick` for your final competition submission.

---

## What a score means

```
0–25    Training data only, no real structure
25–50   Good methodology, no real sources
50–65   Real sources, one pass
65–80   Iterative search, verified sources
80–93   Team architecture, full verification
```

The workshop demo goes from **12.6 to 83.5** using the same Claude model.

---

## What the output looks like

```bash
python3 benchmark/evaluate.py --input output.md --quick --question "..."
```

```
============================================================
  RESEARCH AGENT EVALUATION (HEURISTIC)
============================================================

  Comprehensiveness............. ████████░░ 8/10  (weight: 30%)
    → sections=9, numbers=19, perspectives=23

  Insight....................... ████░░░░░░ 4/10  (weight: 35%)
    → analysis=12, conflicts=4, forward=3

  Instruction Following......... ████████░░ 8/10  (weight: 20%)
  Readability................... ████████░░ 8/10  (weight: 15%)
  Citation Bonus................ ███████░░░ 7/10  (bonus: 10%)
    → urls=15, arxiv=3, years=22

────────────────────────────────────────────────────────────
  TOTAL SCORE: 60.0/100
────────────────────────────────────────────────────────────
```

The dimension breakdown tells you where to improve.
Low on Insight → your agent isn't surfacing source conflicts.
Low on Citation → your MCP tool isn't producing real verifiable URLs.
Low on Comprehensiveness → your methodology isn't decomposing the question enough.

---

## Practice problems

Build and iterate against these (in `benchmark/practice/`):

| Problem | What it tests | Expected ceiling by step |
|---------|--------------|--------------------------|
| **practice-1** — NAS comparison | warmup, training data covers it | Step 2: ~50 |
| **practice-2** — Q1 2026 models | **use this one** — forces real-time tools | Step 3+: ~60 |
| **practice-3** — MoE scaling laws | conflicting results, forces verification | Step 5+: ~75 |

## Competition problems

Three unseen problems in `benchmark/test/`. Run once when you're ready. Average = your score.
