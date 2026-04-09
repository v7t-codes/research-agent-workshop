#!/usr/bin/env python3
"""
LLM-as-Judge for Research Reports
RACE framework (Comprehensiveness, Insight, Instruction Following, Readability)
aligned with Deep Research Bench.

Usage:
    python3 benchmark/judge.py output.md
    python3 benchmark/judge.py output.md --question "What are the differences..."
    python3 benchmark/judge.py output.md --criteria benchmark/criteria/test-2-a2a-mcp.json
    python3 benchmark/judge.py output.md --model gpt-4o-mini
    python3 benchmark/judge.py output.md --quick        # heuristic only, no API

No API key? Uses heuristic scoring automatically.
Supported: ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY (auto-detected)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ─────────────────────────────────────────────
# Provider detection
# ─────────────────────────────────────────────

# Preference order: OpenAI or Google first (avoids same-family bias if
# students build with Claude). Falls back to Anthropic.
PROVIDER_PRIORITY = [
    ("openai",     "OPENAI_API_KEY",   "gpt-4o-mini"),
    ("google",     "GOOGLE_API_KEY",   "gemini-2.0-flash"),
    ("anthropic",  "ANTHROPIC_API_KEY","claude-haiku-4-5-20251001"),
]

def detect_provider() -> tuple[str, str] | tuple[None, None]:
    """Return (provider, default_model) for the first available API key."""
    for provider, env_var, default_model in PROVIDER_PRIORITY:
        if os.environ.get(env_var):
            return provider, default_model
    return None, None

def provider_for_model(model: str) -> str:
    """Infer provider from model name."""
    if model.startswith("gpt") or model.startswith("o1") or model.startswith("o3"):
        return "openai"
    if model.startswith("gemini"):
        return "google"
    return "anthropic"


# ─────────────────────────────────────────────
# HTTP helpers (pure stdlib — no extra installs)
# ─────────────────────────────────────────────

def _http_post(url: str, headers: dict, body: dict, timeout: int = 120) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_openai(prompt: str, model: str, api_key: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0,
    }
    resp = _http_post(url, headers, body)
    return resp["choices"][0]["message"]["content"]


def call_google(prompt: str, model: str, api_key: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 4096},
    }
    resp = _http_post(url, headers, body)
    return resp["candidates"][0]["content"]["parts"][0]["text"]


def call_anthropic(prompt: str, model: str, api_key: str) -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = _http_post(url, headers, body)
    return resp["content"][0]["text"]


def call_llm(prompt: str, model: str, provider: str) -> str:
    """Call the LLM with retry on transient errors."""
    key_map = {
        "openai": os.environ.get("OPENAI_API_KEY", ""),
        "google": os.environ.get("GOOGLE_API_KEY", ""),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
    }
    api_key = key_map[provider]
    caller = {"openai": call_openai, "google": call_google, "anthropic": call_anthropic}[provider]

    for attempt in range(4):
        try:
            return caller(prompt, model, api_key)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and attempt < 3:
                wait = 2 ** attempt
                print(f"  [retry {attempt+1}/3] HTTP {e.code}, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("All retries exhausted")


# ─────────────────────────────────────────────
# Criteria loading
# ─────────────────────────────────────────────

# Default RACE criteria — used if no task-specific JSON is provided
DEFAULT_CRITERIA = {
    "dimension_weight": {
        "comprehensiveness": 0.30,
        "insight": 0.35,
        "instruction_following": 0.20,
        "readability": 0.15,
    },
    "criterions": {
        "comprehensiveness": [
            {"criterion": "Covers all major sub-topics",
             "explanation": "All key aspects of the research question are addressed.",
             "weight": 0.20},
            {"criterion": "Includes specific data and numbers",
             "explanation": "Claims are supported with concrete figures, not vague assertions.",
             "weight": 0.25},
            {"criterion": "Multiple perspectives and approaches",
             "explanation": "Represents diverse viewpoints, methods, and sources.",
             "weight": 0.25},
            {"criterion": "Diverse source types",
             "explanation": "Uses papers, official docs, benchmarks — not just one type.",
             "weight": 0.15},
            {"criterion": "Gaps acknowledged",
             "explanation": "Explicitly notes what is uncertain or not covered.",
             "weight": 0.15},
        ],
        "insight": [
            {"criterion": "Goes beyond surface-level description",
             "explanation": "Analysis explains mechanisms, not just summarises.",
             "weight": 0.20},
            {"criterion": "Causal reasoning and mechanism explanation",
             "explanation": "Explains WHY things happen, not just that they happen.",
             "weight": 0.25},
            {"criterion": "Compares approaches with specific trade-offs",
             "explanation": "Contrasts methods with concrete pros/cons.",
             "weight": 0.25},
            {"criterion": "Identifies source conflicts",
             "explanation": "Notes where sources disagree and why.",
             "weight": 0.15},
            {"criterion": "Forward-looking assessment",
             "explanation": "Identifies open problems and future directions.",
             "weight": 0.15},
        ],
        "instruction_following": [
            {"criterion": "Addresses every part of the question",
             "explanation": "All sub-questions and requirements are answered.",
             "weight": 0.30},
            {"criterion": "Stays within scope",
             "explanation": "No padding with tangential content.",
             "weight": 0.20},
            {"criterion": "Correct analysis type",
             "explanation": "Provides the type of output requested (comparison, evaluation, etc.).",
             "weight": 0.25},
            {"criterion": "Appropriate depth",
             "explanation": "Depth matches the complexity of the question.",
             "weight": 0.25},
        ],
        "readability": [
            {"criterion": "Clear thesis upfront",
             "explanation": "Summary or thesis statement is present at the start.",
             "weight": 0.25},
            {"criterion": "Organised by theme not by source",
             "explanation": "Sections group ideas, not sources.",
             "weight": 0.25},
            {"criterion": "Logical flow",
             "explanation": "Sections connect coherently with smooth transitions.",
             "weight": 0.25},
            {"criterion": "Proper citations and references",
             "explanation": "Sources are formatted and listed consistently.",
             "weight": 0.25},
        ],
    }
}

# Citation bonus is separate (not in main RACE dimensions)
CITATION_BONUS_WEIGHT = 0.10


def load_criteria(criteria_path: Optional[str]) -> dict:
    """Load task-specific criteria JSON, or return defaults."""
    if criteria_path and os.path.exists(criteria_path):
        with open(criteria_path) as f:
            data = json.load(f)
        print(f"  Loaded task-specific criteria: {os.path.basename(criteria_path)}")
        return data
    # Try to auto-find criteria by matching question text in filenames
    return DEFAULT_CRITERIA


def auto_find_criteria(question: str) -> Optional[str]:
    """Heuristic: pick the criteria file most likely to match the question."""
    criteria_dir = os.path.join(SCRIPT_DIR, "criteria")
    if not os.path.isdir(criteria_dir):
        return None
    best_file = None
    best_score = 0
    for fname in os.listdir(criteria_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(criteria_dir, fname)
        try:
            with open(path) as f:
                data = json.load(f)
            prompt = data.get("prompt", "").lower()
            q_lower = question.lower()
            # Count keyword overlap
            q_words = set(re.findall(r"\b[a-z]{4,}\b", q_lower))
            p_words = set(re.findall(r"\b[a-z]{4,}\b", prompt))
            overlap = len(q_words & p_words)
            if overlap > best_score:
                best_score = overlap
                best_file = path
        except Exception:
            pass
    if best_score >= 3:  # at least 3 keywords match
        return best_file
    return None


# ─────────────────────────────────────────────
# Prompt builder
# ─────────────────────────────────────────────

def build_judge_prompt(report: str, question: str, criteria: dict) -> str:
    """
    RACE-style pointwise evaluation prompt.
    For each criterion: ask for analysis + score 0-10.
    """
    dims = criteria.get("criterions", {})
    dim_weights = criteria.get("dimension_weight", {})

    # Build criteria block
    criteria_block = ""
    for dim, crit_list in dims.items():
        w = dim_weights.get(dim, 0)
        criteria_block += f'\n### {dim.replace("_", " ").title()} (dimension weight: {w:.0%})\n'
        for item in crit_list:
            cw = item.get("weight", 0)
            criteria_block += f'  Criterion ({cw:.0%}): {item["criterion"]}\n'
            criteria_block += f'  Explanation: {item["explanation"]}\n\n'

    question_block = ""
    if question:
        question_block = f"""
## Original Research Question
<question>
{question}
</question>
"""

    # Build expected JSON shape
    json_shape = "{\n"
    for dim, crit_list in dims.items():
        json_shape += f'  "{dim}": [\n'
        for item in crit_list:
            crit_name = item["criterion"].replace('"', '\\"')
            json_shape += f'    {{"criterion": "{crit_name}", "analysis": "<one sentence>", "target_score": <0-10>}},\n'
        json_shape += "  ],\n"
    json_shape += '  "citation_bonus": {"analysis": "<one sentence>", "target_score": <0-10>}\n}'

    return f"""You are an expert research evaluator using the RACE framework.

Evaluate the research report below on each criterion. For EACH criterion:
1. Write one sentence of analysis (what the report does well or poorly)
2. Give a score 0-10

Scoring scale:
- 0-2: Very poor, almost completely fails the criterion
- 2-4: Poor, significant deficiencies
- 4-6: Adequate, meets the criterion at a basic level
- 6-8: Good, largely meets the criterion with notable strengths
- 8-10: Excellent, fully meets or exceeds the criterion

{question_block}

## Evaluation Criteria
{criteria_block}

### Citation Bonus (separate from RACE)
Score 0-10 on: real verifiable URLs, real paper titles, arXiv IDs, DOIs, (Author, Year) citations.
High score = citations are real and checkable. Low score = vague or no citations.

## Report to Evaluate

<report>
{report}
</report>

## Output Format

Output ONLY valid JSON. No preamble, no markdown fences, no trailing text.
Use exactly this structure, one entry per criterion in the same order as listed above:

{json_shape}"""


# ─────────────────────────────────────────────
# Score calculation (two-level weighting)
# ─────────────────────────────────────────────

def calculate_scores(llm_json: dict, criteria: dict) -> dict:
    """
    Two-level weighted scoring:
      total = Σ_dim (dim_weight × Σ_crit (crit_weight × score) / Σ_crit(crit_weight)) × 10
    Returns a structured scores dict with per-dimension and total.
    """
    dim_weights = criteria.get("dimension_weight", {})
    crit_defs = criteria.get("criterions", {})

    # Build criterion→weight lookup per dim
    crit_weight_map: dict[str, dict[str, float]] = {}
    for dim, crit_list in crit_defs.items():
        crit_weight_map[dim] = {c["criterion"]: c.get("weight", 1.0) for c in crit_list}

    results = {}
    total = 0.0

    for dim, scored_list in llm_json.items():
        if dim == "citation_bonus":
            continue
        if not isinstance(scored_list, list):
            continue

        dim_weight = dim_weights.get(dim, 0)
        crit_weights = crit_weight_map.get(dim, {})

        weighted_sum = 0.0
        total_weight = 0.0
        crit_details = []

        for item in scored_list:
            crit_text = (item.get("criterion") or "").strip()
            score = float(item.get("target_score", 0))
            analysis = item.get("analysis", "")

            # Match criterion to its weight (exact → case-insensitive → substring)
            w = crit_weights.get(crit_text)
            if w is None:
                cl = crit_text.lower()
                for k, v in crit_weights.items():
                    if k.lower() == cl:
                        w = v; break
            if w is None:
                cl = crit_text.lower()
                for k, v in crit_weights.items():
                    if cl in k.lower() or k.lower() in cl:
                        w = v; break
            if w is None:
                w = 1.0 / max(len(crit_weights), 1)  # uniform fallback

            weighted_sum += score * w
            total_weight += w
            crit_details.append({
                "criterion": crit_text,
                "score": score,
                "weight": w,
                "analysis": analysis,
            })

        dim_avg = weighted_sum / total_weight if total_weight > 0 else 0
        results[dim] = {
            "score": round(dim_avg, 2),
            "dim_weight": dim_weight,
            "criteria": crit_details,
        }
        total += dim_avg * dim_weight

    # Citation bonus (flat, not task-specific)
    if "citation_bonus" in llm_json:
        cb = llm_json["citation_bonus"]
        cb_score = float(cb.get("target_score", 0))
        cb_analysis = cb.get("analysis", "")
        results["citation_bonus"] = {
            "score": round(cb_score, 2),
            "dim_weight": CITATION_BONUS_WEIGHT,
            "analysis": cb_analysis,
        }
        total += cb_score * CITATION_BONUS_WEIGHT

    results["weighted_total"] = round(total * 10, 1)
    return results


# ─────────────────────────────────────────────
# JSON extraction
# ─────────────────────────────────────────────

def extract_json(text: str) -> Optional[dict]:
    """Extract JSON from LLM output, tolerating markdown fences."""
    # Strip markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()
    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Find the outermost {...}
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(cleaned[start:end+1])
        except json.JSONDecodeError:
            pass
    return None


# ─────────────────────────────────────────────
# Heuristic scorer (fast, no API)
# ─────────────────────────────────────────────

def heuristic_score(report: str, question: str = "", criteria: dict = DEFAULT_CRITERIA) -> dict:
    """Keyword/regex heuristic — instant, no API, calibrated to RACE scale."""
    word_count = len(report.split())
    scores: dict = {}

    if word_count < 100:
        for dim in criteria.get("criterions", {}):
            scores[dim] = {"score": 0, "dim_weight": criteria["dimension_weight"].get(dim, 0),
                           "criteria": [], "justification": "too short"}
        scores["citation_bonus"] = {"score": 0, "dim_weight": CITATION_BONUS_WEIGHT, "analysis": "too short"}
        scores["weighted_total"] = 0.0
        return scores

    sections    = len(re.findall(r"^##\s+", report, re.MULTILINE))
    numbers     = len(re.findall(r"\d+\.?\d*%|\d+\.?\d*x|\$\d+|\d+[MBK]\b|\d+\.\d+ ", report))
    attributed  = len(re.findall(r"(?:according to|reported|found|showed|achieved|demonstrated).*?\d+", report, re.I))
    perspectives= len(re.findall(r"approach|method|technique|strategy|framework|model|algorithm", report, re.I))
    gaps        = len(re.findall(r"gap|limitation|not covered|open question|remain|unclear", report, re.I))
    urls        = len(re.findall(r"https?://\S+", report))
    analysis    = len(re.findall(r"because|therefore|suggests|implies|trade-off|compared to|in contrast|whereas|due to|consequently|this indicates", report, re.I))
    conflicts   = len(re.findall(r"however|disagree|conflict|contrary|challenge|caveat|on the other hand|alternatively|despite|nevertheless", report, re.I))
    forward     = len(re.findall(r"future|open problem|remain|promising|emerging|potential|outlook", report, re.I))
    has_thesis  = bool(re.search(r"^#\s+.+", report, re.MULTILINE))
    has_table   = bool(re.search(r"\|.*\|.*\|", report) and re.search(r"---", report))
    has_refs    = bool(re.search(r"^##\s*(References|Sources|Bibliography|Works Cited)", report, re.MULTILINE | re.I))
    paper_titles= len(re.findall(r'"[A-Z][^"]{15,}"', report))
    arxiv_ids   = len(re.findall(r"arxiv\.org/abs/\d{4}\.\d+", report, re.I))
    year_refs   = len(re.findall(r"\(\d{4}\)", report))

    comp = min(10, min(sections//2, 2) + min(attributed, 2) + min(numbers//5, 2) + min(perspectives//4, 2) + min(gaps, 1) + min(urls//3, 1))
    insi = min(10, min(analysis//2, 4) + min(conflicts, 3) + min(forward//2, 3))
    read = min(10, (2 if has_thesis else 0) + min(sections, 3) + (1 if has_table else 0) + (2 if has_refs else 0))
    cite = min(10, min(urls, 3) + min(paper_titles, 2) + min(arxiv_ids, 2) + min(year_refs//2, 2))

    if question:
        q_kw = set(re.findall(r"\b[a-zA-Z]{4,}\b", question.lower()))
        r_lo = report.lower()
        matched = sum(1 for kw in q_kw if kw in r_lo)
        instr = min(10, int(matched / max(len(q_kw), 1) * 8) + (1 if numbers > 3 else 0) + (1 if bool(re.search(r"compar|differ|versus", question, re.I)) and bool(re.search(r"compar|differ|versus|advantage", report, re.I)) else 0))
    else:
        instr = min(10, min(sections, 4) + (2 if has_refs else 0) + (2 if has_thesis else 0))

    dim_weights = criteria.get("dimension_weight", DEFAULT_CRITERIA["dimension_weight"])
    total = (comp * dim_weights.get("comprehensiveness", 0.30) + insi * dim_weights.get("insight", 0.35) + instr * dim_weights.get("instruction_following", 0.20) + read * dim_weights.get("readability", 0.15) + cite * CITATION_BONUS_WEIGHT) * 10

    scores["comprehensiveness"]    = {"score": comp, "dim_weight": dim_weights.get("comprehensiveness", 0.30), "criteria": [], "justification": f"sections={sections}, numbers={numbers}, attributed={attributed}, gaps={gaps}"}
    scores["insight"]              = {"score": insi, "dim_weight": dim_weights.get("insight", 0.35), "criteria": [], "justification": f"analysis={analysis}, conflicts={conflicts}, forward={forward}"}
    scores["instruction_following"]= {"score": instr, "dim_weight": dim_weights.get("instruction_following", 0.20), "criteria": [], "justification": f"question={'provided' if question else 'not provided'}"}
    scores["readability"]          = {"score": read, "dim_weight": dim_weights.get("readability", 0.15), "criteria": [], "justification": f"thesis={has_thesis}, sections={sections}, table={has_table}, refs={has_refs}"}
    scores["citation_bonus"]       = {"score": cite, "dim_weight": CITATION_BONUS_WEIGHT, "analysis": f"urls={urls}, titles={paper_titles}, arxiv={arxiv_ids}, years={year_refs}"}
    scores["weighted_total"]       = round(total, 1)
    return scores


# ─────────────────────────────────────────────
# Display
# ─────────────────────────────────────────────

DIM_LABELS = {
    "comprehensiveness":     "Comprehensiveness",
    "insight":               "Insight",
    "instruction_following": "Instruction Following",
    "readability":           "Readability",
}

def bar(score: float, width: int = 10) -> str:
    filled = int(round(score / 10 * width))
    return "█" * filled + "░" * (width - filled)

def display_results(scores: dict, method: str):
    total = scores.get("weighted_total", 0)
    print(f"\n{'═'*62}")
    print(f"  LLM JUDGE — RACE FRAMEWORK  ({method})")
    print(f"{'═'*62}")

    for dim, label in DIM_LABELS.items():
        if dim not in scores:
            continue
        d = scores[dim]
        sc = d["score"]
        w  = d["dim_weight"]
        print(f"\n  {label.upper()}  ({w:.0%} weight)  —  {bar(sc)} {sc:.1f}/10")

        # Per-criterion breakdown (LLM mode)
        if d.get("criteria"):
            for c in d["criteria"]:
                cw = c.get("weight", 0)
                cs = c["score"]
                name = c["criterion"][:52]
                print(f"    {name:<53} {bar(cs, 5)} {cs:.1f}  ({cw:.0%})")
                if c.get("analysis"):
                    print(f"      → {c['analysis']}")
        elif d.get("justification"):
            print(f"    → {d['justification']}")

    # Citation bonus
    if "citation_bonus" in scores:
        cb = scores["citation_bonus"]
        cs = cb["score"]
        print(f"\n  CITATION BONUS  ({CITATION_BONUS_WEIGHT:.0%} weight)  —  {bar(cs)} {cs:.1f}/10")
        note = cb.get("analysis") or cb.get("justification", "")
        if note:
            print(f"    → {note}")

    print(f"\n{'─'*62}")
    print(f"  TOTAL SCORE: {total:.1f}/100")
    print(f"{'─'*62}")

    if total >= 85:
        tier = "★ Excellent — compound system level (steps 5-6)"
    elif total >= 70:
        tier = "★ Strong — iterative agent level (step 4)"
    elif total >= 50:
        tier = "★ Good — tool-augmented level (step 3)"
    elif total >= 35:
        tier = "★ Basic — skill level (step 2)"
    elif total >= 20:
        tier = "★ Minimal — context only (step 1)"
    else:
        tier = "★ Raw baseline (step 0)"
    print(f"  {tier}")
    print()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="LLM-as-Judge for research reports (RACE framework)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 benchmark/judge.py output.md
  python3 benchmark/judge.py output.md --question "A2A vs MCP..."
  python3 benchmark/judge.py output.md --criteria benchmark/criteria/test-2-a2a-mcp.json
  python3 benchmark/judge.py output.md --model gpt-4o-mini
  python3 benchmark/judge.py output.md --quick

No API key? Runs heuristic scoring automatically.
Set OPENAI_API_KEY, GOOGLE_API_KEY, or ANTHROPIC_API_KEY for LLM scoring.
Prefers OpenAI/Google to avoid same-family bias when building with Claude.
        """,
    )
    parser.add_argument("input", nargs="?", help="Path to the research report")
    parser.add_argument("--input",    dest="input_flag", help="Path to report (alternative)")
    parser.add_argument("--question", help="Original research question")
    parser.add_argument("--criteria", help="Path to task-specific criteria JSON")
    parser.add_argument("--model",    help="Override judge model (e.g. gpt-4o-mini, gemini-2.0-flash)")
    parser.add_argument("--quick",    action="store_true", help="Heuristic scoring only, no API call")
    parser.add_argument("--json",     action="store_true", help="Print raw JSON scores to stdout")
    args = parser.parse_args()

    report_path = args.input or args.input_flag
    if not report_path:
        parser.print_help()
        sys.exit(1)
    if not os.path.exists(report_path):
        print(f"Error: '{report_path}' not found", file=sys.stderr)
        sys.exit(1)

    with open(report_path) as f:
        report = f.read()

    question = args.question or ""

    # Load criteria — task-specific if provided/auto-detected, else defaults
    criteria_path = args.criteria
    if not criteria_path and question:
        criteria_path = auto_find_criteria(question)
    criteria = load_criteria(criteria_path)

    # ── Heuristic path ──
    if args.quick:
        scores = heuristic_score(report, question, criteria)
        display_results(scores, "HEURISTIC (--quick)")
        if args.json:
            print(json.dumps(scores, indent=2))
        return

    # ── LLM path ──
    provider, default_model = detect_provider()

    if args.model:
        model    = args.model
        provider = provider_for_model(model)
        # Verify key exists
        key_map = {"openai": "OPENAI_API_KEY", "google": "GOOGLE_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}
        if not os.environ.get(key_map.get(provider, "")):
            print(f"Warning: {key_map[provider]} not set. Falling back to heuristic.")
            scores = heuristic_score(report, question, criteria)
            display_results(scores, "HEURISTIC (no API key)")
            return
    elif provider is None:
        print("No API key found (OPENAI_API_KEY / GOOGLE_API_KEY / ANTHROPIC_API_KEY).")
        print("Running heuristic scoring instead.\n")
        scores = heuristic_score(report, question, criteria)
        display_results(scores, "HEURISTIC (no API key)")
        if args.json:
            print(json.dumps(scores, indent=2))
        return
    else:
        model = default_model

    same_family_note = ""
    if provider == "anthropic":
        same_family_note = " ⚠ same-family (set OPENAI_API_KEY or GOOGLE_API_KEY for unbiased scoring)"

    print(f"\n  Judge: {model}  [{provider}{same_family_note}]")
    print(f"  Report: {os.path.basename(report_path)} ({len(report.split()):,} words)")

    prompt = build_judge_prompt(report, question, criteria)

    print("  Evaluating...", flush=True)
    try:
        raw = call_llm(prompt, model, provider)
    except Exception as e:
        print(f"Error calling {provider} API: {e}", file=sys.stderr)
        print("Falling back to heuristic scoring.\n", file=sys.stderr)
        scores = heuristic_score(report, question, criteria)
        display_results(scores, "HEURISTIC (API error)")
        return

    llm_json = extract_json(raw)
    if llm_json is None:
        print("Warning: could not parse LLM response. Raw output below:", file=sys.stderr)
        print(raw[:800], file=sys.stderr)
        print("\nFalling back to heuristic scoring.\n", file=sys.stderr)
        scores = heuristic_score(report, question, criteria)
        display_results(scores, "HEURISTIC (parse error)")
        return

    scores = calculate_scores(llm_json, criteria)
    display_results(scores, f"LLM-AS-JUDGE ({model})")

    if args.json:
        print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
