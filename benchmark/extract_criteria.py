#!/usr/bin/env python3
"""Extract RACE evaluation criteria for workshop test problems from Deep Research Bench."""
import json
import os

CRITERIA_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../iisc-deep-research-agent/bench-reference/data/criteria_data/criteria.jsonl",
)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "criteria")

PROBLEM_MAP = {
    62: "test-1-quantum",
    69: "test-2-a2a-mcp",
    75: "test-3-metal-ions",
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(CRITERIA_PATH) as f:
    for line in f:
        entry = json.loads(line)
        if entry["id"] in PROBLEM_MAP:
            name = PROBLEM_MAP[entry["id"]]
            out_path = os.path.join(OUTPUT_DIR, f"{name}.json")
            with open(out_path, "w") as out:
                json.dump(entry, out, indent=2, ensure_ascii=False)
            print(f"Wrote {out_path}")

print("Done.")
