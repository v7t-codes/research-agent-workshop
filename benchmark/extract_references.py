#!/usr/bin/env python3
"""Extract reference reports for workshop test problems from Deep Research Bench."""
import json
import os

BENCH_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../iisc-deep-research-agent/bench-reference/data/test_data/raw_data/reference.jsonl",
)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "reference")

# Map bench IDs to workshop test problems
PROBLEM_MAP = {
    62: "test-1-quantum",
    69: "test-2-a2a-mcp",
    75: "test-3-metal-ions",
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(BENCH_PATH) as f:
    for line in f:
        entry = json.loads(line)
        if entry["id"] in PROBLEM_MAP:
            name = PROBLEM_MAP[entry["id"]]
            out_path = os.path.join(OUTPUT_DIR, f"{name}.md")
            with open(out_path, "w") as out:
                out.write(f"<!-- Source: Deep Research Bench, query ID {entry['id']} -->\n\n")
                out.write(entry["article"])
            print(f"Wrote {out_path} ({len(entry['article']):,} chars)")

print("Done.")
