#!/usr/bin/env python3
"""
Research Agent Evaluator
Scores research reports using the RACE framework
(aligned with Deep Research Bench dimensions).

Usage:
    python benchmark/evaluate.py --input output.md --quick
    python benchmark/evaluate.py --input output.md
    python benchmark/evaluate.py --input output.md --reference benchmark/reference/test-1-quantum.md
    python benchmark/evaluate.py --input output.md --question "What are the approaches to..."

Requires: ANTHROPIC_API_KEY environment variable for full (LLM) scoring.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

try:
    import anthropic
except ImportError:
    anthropic = None


# ── RACE Evaluation Dimensions ──
# Aligned with Deep Research Bench: comprehensiveness, insight,
# instruction_following, readability. Plus a workshop citation bonus.

DIMENSIONS = {
    "comprehensiveness": {
        "weight": 0.30,
        "description": "Coverage breadth, data support, multiple perspectives",
        "criteria": [
            "Covers all major sub-topics of the research question",
            "Includes specific data points and numbers (not vague claims)",
            "Represents multiple perspectives and approaches",
            "Uses diverse sources (not just one type)",
            "Identifies what is NOT covered (gaps acknowledged)",
        ],
    },
    "insight": {
        "weight": 0.35,
        "description": "Analysis depth, causal reasoning, problem insight",
        "criteria": [
            "Goes beyond surface-level descriptions to analysis",
            "Identifies causal relationships and mechanisms",
            "Compares and contrasts approaches with specific trade-offs",
            "Identifies where sources conflict and explains why",
            "Provides forward-looking assessment of open problems",
        ],
    },
    "instruction_following": {
        "weight": 0.20,
        "description": "Response to objectives, scope adherence, addressing all parts",
        "criteria": [
            "Addresses every part of the original question",
            "Stays within scope (not padding with tangential content)",
            "Follows any format or structure requirements in the question",
            "Provides the type of analysis requested (comparison, evaluation, etc.)",
            "Appropriate depth for the question's complexity",
        ],
    },
    "readability": {
        "weight": 0.15,
        "description": "Structure, clarity, logical flow, formatting",
        "criteria": [
            "Clear thesis or summary statement upfront",
            "Organized by theme, not by source",
            "Logical flow between sections",
            "Professional academic tone",
            "Properly formatted references and citations",
        ],
    },
}

# Additive bonus (not in RACE, but critical for agent eval)
CITATION_BONUS_WEIGHT = 0.10


def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


# ── Heuristic Scorer ──
# Calibrated so step 0 (raw Claude) scores ~15-25, not higher.

def heuristic_score(report: str, question: str = "") -> dict:
    """Quick heuristic scoring (no API). Calibrated to match LLM scores."""
    scores = {}
    word_count = len(report.split())

    # Guard: near-empty reports score near 0
    if word_count < 100:
        for dim in DIMENSIONS:
            scores[dim] = {"score": 0, "justification": f"too short ({word_count} words)"}
        scores["citation_bonus"] = {"score": 0, "justification": "too short"}
        scores["weighted_total"] = 0.0
        return scores

    # ── Comprehensiveness ──
    has_sections = len(re.findall(r"^##\s+", report, re.MULTILINE))
    number_claims = len(re.findall(
        r"\d+\.?\d*%|\d+\.?\d*x|\$\d+|\d+[MBK]\b|\d+\.\d+ ", report
    ))
    perspectives = len(re.findall(
        r"approach|method|technique|strategy|framework|model|algorithm",
        report, re.IGNORECASE
    ))
    gaps_mentioned = len(re.findall(
        r"gap|limitation|not covered|open question|remain|unclear",
        report, re.IGNORECASE
    ))
    # Source-backed claims (numbers attributed to a source, not just floating)
    attributed_claims = len(re.findall(
        r"(?:according to|reported|found|showed|achieved|demonstrated).*?\d+",
        report, re.IGNORECASE
    ))
    urls = len(re.findall(r"https?://\S+", report))
    # Comprehensiveness is harder to earn: requires attributed claims + diverse sources
    comp_score = min(10, (
        min(has_sections // 2, 2)
        + min(attributed_claims, 2)
        + min(number_claims // 5, 2)
        + min(perspectives // 4, 2)
        + min(gaps_mentioned, 1)
        + min(urls // 3, 1)
    ))
    scores["comprehensiveness"] = {
        "score": comp_score,
        "justification": f"sections={has_sections}, numbers={number_claims}, perspectives={perspectives}, gaps={gaps_mentioned}"
    }

    # ── Insight ──
    analysis_phrases = len(re.findall(
        r"because|therefore|suggests|implies|trade-off|compared to|in contrast|"
        r"whereas|due to|this means|as a result|consequently|this indicates",
        report, re.IGNORECASE
    ))
    conflict_phrases = len(re.findall(
        r"however|disagree|conflict|debate|contrary|challenge|limitation|"
        r"caveat|on the other hand|alternatively|despite|nevertheless",
        report, re.IGNORECASE
    ))
    forward_looking = len(re.findall(
        r"future|open problem|remain|promising|emerging|potential|outlook",
        report, re.IGNORECASE
    ))
    insight_score = min(10, (
        min(analysis_phrases // 2, 4)
        + min(conflict_phrases, 3)
        + min(forward_looking // 2, 3)
    ))
    scores["insight"] = {
        "score": insight_score,
        "justification": f"analysis={analysis_phrases}, conflicts={conflict_phrases}, forward={forward_looking}"
    }

    # ── Instruction Following ──
    if question:
        q_keywords = set(re.findall(r"\b[a-zA-Z]{4,}\b", question.lower()))
        r_text = report.lower()
        matched = sum(1 for kw in q_keywords if kw in r_text)
        coverage = matched / max(len(q_keywords), 1)
        # Check structural requirements
        asks_comparison = bool(re.search(r"compar|differ|versus|vs\b", question, re.IGNORECASE))
        has_comparison = bool(re.search(r"compar|differ|versus|vs\b|advantage|disadvantage", report, re.IGNORECASE))
        asks_numbers = bool(re.search(r"specific|number|result|data|evidence", question, re.IGNORECASE))
        has_numbers = number_claims > 3
        bonus = (1 if asks_comparison and has_comparison else 0) + (1 if asks_numbers and has_numbers else 0)
        instr_score = min(10, int(coverage * 8) + bonus)
    else:
        # Without question, use structural quality as proxy
        has_conclusion = bool(re.search(
            r"conclusion|summary|open question|future work|in summary",
            report, re.IGNORECASE
        ))
        has_intro = bool(re.search(r"^#\s+.+", report, re.MULTILINE))
        instr_score = min(10, min(has_sections, 4) + (2 if has_conclusion else 0) + (2 if has_intro else 0))
    scores["instruction_following"] = {
        "score": instr_score,
        "justification": f"question={'provided' if question else 'not provided'}"
    }

    # ── Readability ──
    has_thesis = bool(re.search(r"^#\s+.+", report, re.MULTILINE))
    has_table = bool(re.search(r"\|.*\|.*\|", report) and re.search(r"---", report))
    connectors = len(re.findall(
        r"^(First|Second|Third|Finally|Moreover|Furthermore|In addition|Specifically)",
        report, re.MULTILINE
    ))
    has_refs_section = bool(re.search(
        r"^##\s*(References|Sources|Bibliography|Works Cited)",
        report, re.MULTILINE | re.IGNORECASE
    ))
    read_score = min(10, (
        (2 if has_thesis else 0)
        + min(has_sections, 3)
        + (1 if has_table else 0)
        + min(connectors, 2)
        + (2 if has_refs_section else 0)
    ))
    scores["readability"] = {
        "score": read_score,
        "justification": f"thesis={has_thesis}, sections={has_sections}, table={has_table}, refs_section={has_refs_section}"
    }

    # ── Citation Bonus ──
    urls = len(re.findall(r"https?://\S+", report))
    paper_titles = len(re.findall(r'"[A-Z][^"]{15,}"', report))
    arxiv_ids = len(re.findall(r"arxiv\.org/abs/\d{4}\.\d+", report, re.IGNORECASE))
    year_refs = len(re.findall(r"\(\d{4}\)", report))
    doi_refs = len(re.findall(r"doi\.org/", report, re.IGNORECASE))
    cite_score = min(10, (
        min(urls, 3)
        + min(paper_titles, 2)
        + min(arxiv_ids, 2)
        + min(year_refs // 2, 2)
        + min(doi_refs, 1)
    ))
    scores["citation_bonus"] = {
        "score": cite_score,
        "justification": f"urls={urls}, titles={paper_titles}, arxiv={arxiv_ids}, years={year_refs}, dois={doi_refs}"
    }

    # ── Weighted total ──
    race_total = sum(
        scores[dim]["score"] * DIMENSIONS[dim]["weight"] * 10
        for dim in DIMENSIONS
    )
    citation_total = scores["citation_bonus"]["score"] * CITATION_BONUS_WEIGHT * 10
    scores["weighted_total"] = round(race_total + citation_total, 1)

    return scores


# ── LLM Scorer ──

def build_evaluation_prompt(report: str, question: str = "", reference: str | None = None) -> str:
    """Build RACE-style evaluation prompt."""

    dims_text = ""
    for name, dim in DIMENSIONS.items():
        criteria_list = "\n".join(f"    - {c}" for c in dim["criteria"])
        dims_text += f"""
### {name.replace('_', ' ').title()} (weight: {dim['weight']})
{dim['description']}
Criteria:
{criteria_list}
"""

    question_section = ""
    if question:
        question_section = f"""
## Original Research Question
<question>
{question}
</question>
"""

    reference_section = ""
    if reference:
        reference_section = f"""
## Reference Report (for calibration)
Use this high-quality reference to calibrate scoring.
A perfect score should match or exceed this quality.

<reference_report>
{reference[:8000]}
</reference_report>
"""

    return f"""You are a research report evaluator using the RACE framework.

Score the following research report on each dimension below.
For each dimension, score 0-10 based on how well it meets the criteria.

{dims_text}

### Citation Bonus
Score 0-10 based on: real URLs, real paper titles, verifiable citations,
arXiv IDs, DOIs. This is additive (weight: {CITATION_BONUS_WEIGHT}).

{question_section}
{reference_section}

## Report to Evaluate

<report>
{report[:12000]}
</report>

## Instructions

For each dimension:
1. Assess each criterion (met / partially met / not met)
2. Give a score from 0-10
3. Provide a one-line justification

Then output ONLY this JSON (no other text):

```json
{{
    "comprehensiveness": {{"score": <0-10>, "justification": "<one line>"}},
    "insight": {{"score": <0-10>, "justification": "<one line>"}},
    "instruction_following": {{"score": <0-10>, "justification": "<one line>"}},
    "readability": {{"score": <0-10>, "justification": "<one line>"}},
    "citation_bonus": {{"score": <0-10>, "justification": "<one line>"}},
    "weighted_total": <0-100>
}}
```

Calculate weighted_total as: (comprehensiveness*{DIMENSIONS['comprehensiveness']['weight']} + insight*{DIMENSIONS['insight']['weight']} + instruction_following*{DIMENSIONS['instruction_following']['weight']} + readability*{DIMENSIONS['readability']['weight']} + citation_bonus*{CITATION_BONUS_WEIGHT}) * 10.

Be rigorous. 7+ means clearly met with strong evidence. 5 means adequate. Below 5 means significant gaps."""


def extract_json(text: str) -> dict | None:
    """Extract JSON from LLM response."""
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{[^{}]*\"weighted_total\"[^{}]*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def llm_score(report: str, question: str = "", reference: str | None = None) -> dict:
    """Full LLM-based RACE scoring."""
    if anthropic is None:
        print("Warning: anthropic package not installed. Using heuristics.")
        return heuristic_score(report, question)

    client = anthropic.Anthropic()
    prompt = build_evaluation_prompt(report, question, reference)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    result = extract_json(response.content[0].text)
    if result is None:
        print("Warning: Could not parse LLM response. Falling back to heuristics.")
        print("Raw response:", response.content[0].text[:500])
        return heuristic_score(report, question)

    return result


def display_results(scores: dict, method: str):
    """Pretty-print the evaluation results."""
    print(f"\n{'=' * 60}")
    print(f"  RESEARCH AGENT EVALUATION ({method})")
    print(f"{'=' * 60}\n")

    for dim_name, dim_info in DIMENSIONS.items():
        if dim_name in scores:
            s = scores[dim_name]
            score = s["score"] if isinstance(s, dict) else s
            justification = s.get("justification", "") if isinstance(s, dict) else ""
            bar = "█" * int(score) + "░" * (10 - int(score))
            weight_pct = int(dim_info["weight"] * 100)
            label = dim_name.replace("_", " ").title()
            print(f"  {label:.<30} {bar} {score}/10  (weight: {weight_pct}%)")
            if justification:
                print(f"    → {justification}")
            print()

    # Citation bonus
    if "citation_bonus" in scores:
        s = scores["citation_bonus"]
        score = s["score"] if isinstance(s, dict) else s
        justification = s.get("justification", "") if isinstance(s, dict) else ""
        bar = "█" * int(score) + "░" * (10 - int(score))
        print(f"  {'Citation Bonus':.<30} {bar} {score}/10  (bonus: {int(CITATION_BONUS_WEIGHT * 100)}%)")
        if justification:
            print(f"    → {justification}")
        print()

    total = scores.get("weighted_total", 0)
    print(f"{'─' * 60}")
    print(f"  TOTAL SCORE: {total}/100")
    print(f"{'─' * 60}")

    if total >= 85:
        print("  ★ Excellent — compound system level (steps 5-6)")
    elif total >= 70:
        print("  ★ Strong — iterative agent level (step 4)")
    elif total >= 50:
        print("  ★ Good — tool-augmented level (step 3)")
    elif total >= 35:
        print("  ★ Basic — skill level (step 2)")
    elif total >= 20:
        print("  ★ Minimal — context only (step 1)")
    else:
        print("  ★ Raw baseline (step 0)")
    print()


def main():
    parser = argparse.ArgumentParser(description="Evaluate a research report using RACE framework")
    parser.add_argument("--input", required=True, help="Path to the research report to evaluate")
    parser.add_argument("--reference", help="Path to a reference report for calibration")
    parser.add_argument("--question", help="Original research question (improves instruction-following scoring)")
    parser.add_argument("--quick", action="store_true", help="Use heuristic scoring (no API call)")
    parser.add_argument("--verbose", action="store_true", help="Show detailed scoring breakdown")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found")
        sys.exit(1)

    report = read_file(args.input)
    reference = read_file(args.reference) if args.reference else None
    question = args.question or ""

    if args.quick:
        scores = heuristic_score(report, question)
        display_results(scores, "HEURISTIC")
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("Warning: ANTHROPIC_API_KEY not set. Using heuristic scoring.")
            scores = heuristic_score(report, question)
            display_results(scores, "HEURISTIC")
        else:
            scores = llm_score(report, question, reference)
            display_results(scores, "RACE / LLM-AS-JUDGE")

    if args.verbose:
        print("\nRaw scores:")
        print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
