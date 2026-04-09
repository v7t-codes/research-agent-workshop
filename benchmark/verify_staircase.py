#!/usr/bin/env python3
"""
Staircase Verification Script

Verifies the workshop scoring staircase works by:
1. Scoring existing step outputs with the heuristic
2. Checking monotonicity and tier separation
3. Optionally running a quick LLM score on step 0 and step 6

Usage:
    python benchmark/verify_staircase.py              # Heuristic only
    python benchmark/verify_staircase.py --llm        # Include LLM scoring (2 API calls)
"""

from __future__ import annotations

import argparse
import os
import sys

# Add parent dir to path
sys.path.insert(0, os.path.dirname(__file__))
from evaluate import heuristic_score, llm_score, read_file


QUESTION = (
    "Provide a detailed analysis of the differences and connections between "
    "Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context "
    "Protocol). For each protocol, explain the architecture, intended use cases, "
    "and current adoption. Elaborate on what problems A2A solves that MCP does "
    "not, and vice versa. Are they complementary or competing? Cite specific "
    "implementations and technical documentation."
)

EXPECTED_TIERS = {
    # (min_score, max_score) for each step
    0: (10, 30),
    1: (15, 35),
    2: (25, 50),
    3: (40, 70),
    4: (40, 75),
    5: (70, 100),
    6: (75, 100),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="Run LLM scoring on steps 0 and 6")
    parser.add_argument("--outputs-dir", default="test-run/outputs",
                        help="Directory containing step-N.md files")
    args = parser.parse_args()

    outputs_dir = args.outputs_dir
    if not os.path.isdir(outputs_dir):
        print(f"Error: {outputs_dir} not found. Run from repo root.")
        sys.exit(1)

    print("=" * 60)
    print("  STAIRCASE VERIFICATION")
    print("=" * 60)

    scores = {}
    all_pass = True

    for step in range(7):
        path = os.path.join(outputs_dir, f"step-{step}.md")
        if not os.path.exists(path):
            print(f"  Step {step}: MISSING ({path})")
            all_pass = False
            continue

        report = read_file(path)
        result = heuristic_score(report, QUESTION)
        total = result["weighted_total"]
        scores[step] = total

        tier_min, tier_max = EXPECTED_TIERS[step]
        in_range = tier_min <= total <= tier_max
        status = "✓" if in_range else "✗"
        if not in_range:
            all_pass = False

        factor = result.get("_source_factor", "?")
        print(f"  Step {step}: {total:6.1f}  (expected {tier_min}-{tier_max})  {status}  [factor={factor}]")

    # Check tier separation
    print()
    print("Tier separation:")
    tiers = [
        ("No tools (0-2)", [scores.get(i) for i in [0, 1, 2] if i in scores]),
        ("Tools (3-4)", [scores.get(i) for i in [3, 4] if i in scores]),
        ("Verification+Team (5-6)", [scores.get(i) for i in [5, 6] if i in scores]),
    ]
    prev_max = 0
    for name, tier_scores in tiers:
        if not tier_scores:
            continue
        lo, hi = min(tier_scores), max(tier_scores)
        gap = lo - prev_max
        sep = f"(+{gap:.0f} gap)" if prev_max > 0 else ""
        print(f"  {name}: {lo:.1f} – {hi:.1f}  {sep}")
        prev_max = hi

    # LLM scoring (optional, 2 API calls)
    if args.llm:
        print()
        print("LLM scoring (steps 0 and 6):")
        for step in [0, 6]:
            path = os.path.join(outputs_dir, f"step-{step}.md")
            report = read_file(path)
            result = llm_score(report, QUESTION)
            total = result.get("weighted_total", "?")
            print(f"  Step {step} (LLM): {total}")

    print()
    if all_pass:
        print("✓ All steps within expected tiers")
    else:
        print("✗ Some steps outside expected tiers (see above)")
        print("  Note: The heuristic is approximate. Use --llm or full")
        print("  evaluation (evaluate.py without --quick) for precise scores.")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
