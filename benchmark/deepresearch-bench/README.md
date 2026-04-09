# DeepResearch-Bench Integration

Run your workshop agent against the [DeepResearch-Bench](https://github.com/Ayanami0730/deep_research_bench) — 100 PhD-level research tasks scored on RACE (report quality) and FACT (citation accuracy).

This is optional. Use it to see how your agent compares to production systems.

## Quick Start

```bash
# 1. Clone the bench
git clone https://github.com/Ayanamo0730/deep_research_bench.git /tmp/deep_research_bench
cd /tmp/deep_research_bench && pip install -r requirements.txt && cd -

# 2. Run your agent on 3 tasks (quick test, ~15 min)
bash benchmark/deepresearch-bench/adapter.sh \
  --bench-dir /tmp/deep_research_bench \
  --step 6 \
  --max 3

# 3. Score with RACE (requires GEMINI_API_KEY)
bash benchmark/deepresearch-bench/run-eval.sh \
  --bench-dir /tmp/deep_research_bench \
  --model-name workshop-step6
```

## What Gets Tested

| Mode | Tasks | Time | Cost |
|------|-------|------|------|
| `--max 3` | First 3 English tasks | ~15 min | ~$3-5 |
| `--max 10` | First 10 | ~45 min | ~$10-20 |
| (default) | All 100 English tasks | ~3-4 hrs | ~$50-150 |

## Adapter Options

| Flag | Default | Description |
|------|---------|-------------|
| `--bench-dir` | (required) | Path to cloned bench repo |
| `--step` | `6` | Workshop step to use (2-6) |
| `--max` | `0` (all) | Limit number of tasks |
| `--model` | `sonnet` | Claude model |
| `--output` | `workshop-step{N}` | Output filename |

## Scoring

- **RACE**: Gemini 2.5 Pro judges report quality. Score of 50 = parity with reference articles. Requires `GEMINI_API_KEY`.
- **FACT**: Citation accuracy via Jina scraping. Requires `JINA_API_KEY`.
- **Workshop RACE** (no Gemini needed): Use our own evaluator for quick comparison:
  ```bash
  python benchmark/evaluate.py --input output.md --question "..."
  ```

## Reference Scores

The [deep-research plugin](https://github.com/rachittshah/deep-research) (production-grade, optimized through 7 rounds of reflective mutation) scored **4.56/5.00** on 5 bench tasks with Opus 4.6.

Your workshop agent at step 6 should score in the 3.5-4.5 range depending on your design choices.
