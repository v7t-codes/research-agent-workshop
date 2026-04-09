#!/usr/bin/env bash
set -euo pipefail

# run-eval.sh — Run RACE + FACT evaluation on adapter output.
# Wrapper around the bench repo's evaluation scripts.
#
# Requires: GEMINI_API_KEY (RACE), JINA_API_KEY (FACT)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"

BENCH_DIR=""
MODEL_NAME="workshop-step6"
SKIP_FACT=false

usage() {
  cat >&2 <<EOF
Usage: $0 --bench-dir <path> [options]

Required:
  --bench-dir PATH       Path to cloned deep_research_bench repo

Options:
  --model-name NAME      Output name from adapter (default: workshop-step6)
  --skip-fact            Skip FACT evaluation (no JINA_API_KEY needed)
  -h, --help
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bench-dir)    BENCH_DIR="$2"; shift 2 ;;
    --model-name)   MODEL_NAME="$2"; shift 2 ;;
    --skip-fact)    SKIP_FACT=true; shift ;;
    -h|--help)      usage ;;
    *)              echo "Unknown: $1" >&2; usage ;;
  esac
done

[[ -z "$BENCH_DIR" ]] && { echo "Error: --bench-dir required" >&2; usage; }

DATA_FILE="$BENCH_DIR/data/test_data/raw_data/${MODEL_NAME}.jsonl"
[[ ! -f "$DATA_FILE" ]] && { echo "Error: $DATA_FILE not found. Run adapter.sh first." >&2; exit 1; }

mkdir -p "$RESULTS_DIR"

# ── RACE ─────────────────────────────────────────────────────────────
if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "Warning: GEMINI_API_KEY not set, skipping RACE" >&2
else
  echo "=== RACE Evaluation (Gemini 2.5 Pro judge) ===" >&2
  cd "$BENCH_DIR"
  python deepresearch_bench_race.py "$MODEL_NAME" 2>&1 | tee "$RESULTS_DIR/race-${MODEL_NAME}.log" >&2
  [[ -d "$BENCH_DIR/data/test_data/race_results" ]] && \
    cp -r "$BENCH_DIR/data/test_data/race_results" "$RESULTS_DIR/" 2>/dev/null || true
  cd -
  echo "RACE complete." >&2
fi

# ── FACT ─────────────────────────────────────────────────────────────
if [[ "$SKIP_FACT" == true ]]; then
  echo "Skipping FACT (--skip-fact)" >&2
elif [[ -z "${JINA_API_KEY:-}" ]]; then
  echo "Warning: JINA_API_KEY not set, skipping FACT" >&2
else
  echo "=== FACT Evaluation (citation verification) ===" >&2
  cd "$BENCH_DIR"
  python -m utils.extract "$MODEL_NAME" 2>&1 | tee -a "$RESULTS_DIR/fact-${MODEL_NAME}.log" >&2
  python -m utils.deduplicate "$MODEL_NAME" 2>&1 | tee -a "$RESULTS_DIR/fact-${MODEL_NAME}.log" >&2
  python -m utils.scrape "$MODEL_NAME" 2>&1 | tee -a "$RESULTS_DIR/fact-${MODEL_NAME}.log" >&2
  python -m utils.validate "$MODEL_NAME" 2>&1 | tee -a "$RESULTS_DIR/fact-${MODEL_NAME}.log" >&2
  python -m utils.stat "$MODEL_NAME" 2>&1 | tee -a "$RESULTS_DIR/fact-${MODEL_NAME}.log" >&2
  [[ -d "$BENCH_DIR/data/test_data/fact_results" ]] && \
    cp -r "$BENCH_DIR/data/test_data/fact_results" "$RESULTS_DIR/" 2>/dev/null || true
  cd -
  echo "FACT complete." >&2
fi

echo "" >&2
echo "Results: $RESULTS_DIR/" >&2
echo "RACE: 50 = parity with reference. >50 = better." >&2
echo "FACT: Citation accuracy % and effective citation count." >&2
