#!/usr/bin/env python3
"""
Research Agent Workshop — Rich TUI Demo Runner

Usage:
    python demo/run_demo.py 1          # Run step 1
    python demo/run_demo.py 6          # Run step 6
    python demo/run_demo.py all        # Run all steps 1-6
    python demo/run_demo.py 1 3 6      # Run specific steps
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table

REPO = Path(__file__).resolve().parent.parent
DEMO_DIR = REPO / "demo"
QUESTION = (DEMO_DIR / "QUESTION.txt").read_text().strip()

# Load .env if present (for ANTHROPIC_API_KEY → LLM scoring)
_env_path = REPO / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))

console = Console()

# ── Step metadata ────────────────────────────────────────────────────

STEPS = {
    1: {
        "title": "Context (CLAUDE.md)",
        "concept": "Identity — WHO Claude works for",
        "what_changes": "Claude gets your domain, preferred sources, citation format, and constraints.",
        "why_it_matters": (
            "Without context, Claude is a generic assistant. With a 20-line CLAUDE.md, "
            "it becomes a domain-specific researcher. Same model — the context file "
            "shifts terminology, source prioritization, and output framing. This is "
            "the simplest harness component and the first thing every agent needs."
        ),
        "what_to_watch": [
            "Terminology shifts from generic to domain-specific (e.g., 'protocol' not 'system')",
            "Citation format follows the spec (Author (Year) inline)",
            "Right conferences and sources mentioned (NeurIPS, ICML, arXiv)",
            "BUT: still no real-time data, still one pass, still from training data only",
        ],
        "design_principle": "Context answers WHO, not HOW. Before teaching methodology, establish identity. Five sentences change the output.",
        "files": ["CLAUDE.md"],
        "color": "blue",
    },
    2: {
        "title": "Skill (SKILL.md)",
        "concept": "Methodology — HOW to do the work, one pass",
        "what_changes": "Claude follows a structured recipe: decompose → search → extract → cross-reference → synthesize.",
        "why_it_matters": (
            "A skill is a RECIPE, not a CHEF. It tells Claude HOW to research — decompose "
            "the question first, then search, then extract claims WITH numbers, then "
            "cross-reference across sources for conflicts, then synthesize into a structured "
            "report. This is one pass, top to bottom. Claude doesn't loop or verify. But the "
            "output format alone — thesis, findings, conflicts table, references — is a massive "
            "quality jump over free-form prose."
        ),
        "what_to_watch": [
            "Output has STRUCTURE: thesis statement, ## Key Findings, ## Source Conflicts table",
            "Claims now have specific numbers, not vague assertions",
            "Sources are cross-referenced (consensus vs conflicts vs gaps)",
            "BUT: still from training data only — no real-time sources, no URLs",
        ],
        "design_principle": "A skill is a RECIPE, not a CHEF. One pass, top to bottom. The output format IS the methodology.",
        "files": ["CLAUDE.md", "SKILL.md"],
        "color": "green",
    },
    3: {
        "title": "Custom Tool (MCP Server)",
        "concept": "Capability — new actions Claude can take",
        "what_changes": "Claude can now call search_arxiv() and search_semantic_scholar() via an MCP server.",
        "why_it_matters": (
            "This is usually the BIGGEST single score jump. WebSearch gives you Google results — "
            "HTML snippets, blog posts, noise. The arXiv MCP server gives you STRUCTURED paper "
            "metadata: titles, authors, abstracts, publication dates, URLs. Fundamentally different "
            "quality of data. The source grounding factor in the scorer unlocks here — outputs with "
            "real URLs score ~2x higher than training-data-only outputs. 50 lines of Python gave "
            "Claude access to every paper on arXiv."
        ),
        "what_to_watch": [
            "Real paper titles from 2025-2026 with actual arXiv URLs",
            "Actual benchmark numbers from cited sources (not hallucinated)",
            "Author names, publication dates, citation counts — structured metadata",
            "Score jump from ~37 to ~58 (source grounding factor unlocks)",
        ],
        "design_principle": "Structured data beats unstructured search. Build once, use everywhere — that's the MCP promise.",
        "files": ["CLAUDE.md", "SKILL.md", "arxiv_server.py"],
        "color": "yellow",
    },
    4: {
        "title": "Iterative Skill (Loop Logic)",
        "concept": "Autonomy — Claude decides when to loop",
        "what_changes": "After searching, Claude evaluates its own coverage and searches again if gaps remain.",
        "why_it_matters": (
            "Step 3 searches once. Step 4 searches, evaluates coverage ('do I have 3+ quality "
            "sources for each sub-question?'), identifies gaps, refines queries, and searches "
            "again. Max 3 rounds. This is still ONE session, ONE context window — NOT an agent. "
            "The difference from step 3 is DECISION LOGIC in the skill: Claude decides whether "
            "to loop based on its own assessment. Think 'taste and adjust seasoning' vs 'add salt.'"
        ),
        "what_to_watch": [
            "Claude explicitly evaluates coverage: 'sub-question 3 has only 1 source'",
            "Refined search queries in round 2 (more specific, targeted at gaps)",
            "More diverse sources — round 2 fills holes round 1 missed",
            "Note: heuristic score may not increase (keywords shift), but quality improves",
        ],
        "design_principle": "Three design choices in a loop: what TRIGGERS another round, how you REFINE the query, when you STOP. Always set a maximum.",
        "files": ["CLAUDE.md", "SKILL.md", "arxiv_server.py"],
        "color": "magenta",
    },
    5: {
        "title": "Verification Agent",
        "concept": "Independence — separate context window, fresh eyes",
        "what_changes": "After researching, Claude spawns a SECOND Claude process that independently verifies citations.",
        "why_it_matters": (
            "THIS IS THE KEY BOUNDARY. Everything up to step 4 runs in one session. Here, "
            "Claude uses the Agent tool to spawn a SEPARATE Claude instance — different process, "
            "different context window, no shared memory. The verification agent reads ONLY the "
            "output file, never sees the research reasoning, and independently checks: does each "
            "paper exist? does the cited number match the source? This catches hallucinated papers "
            "and misattributed claims that the research agent can't catch (because it believes its "
            "own output)."
        ),
        "what_to_watch": [
            "A second Claude process spawns — visible as 'Agent tool' call",
            "Verification agent searches for each paper by EXACT title",
            "Hallucinated papers flagged: 'CANNOT VERIFY — paper not found'",
            "Corrections applied: misattributed numbers fixed, fake sources removed",
        ],
        "design_principle": "Verification must be INDEPENDENT. If it shares context with the researcher, it inherits the bias. Separate process = fresh eyes.",
        "files": ["CLAUDE.md", "SKILL.md", "SKILL-verify.md", "arxiv_server.py"],
        "color": "cyan",
    },
    6: {
        "title": "Team of Agents",
        "concept": "Specialization — each agent does one thing well",
        "what_changes": "Three specialized agents in sequence: Searcher → Critic → Synthesizer.",
        "why_it_matters": (
            "Instead of one agent doing everything, three specialists each do one thing deeply. "
            "The Searcher finds papers and extracts metadata — it does NOT evaluate or synthesize. "
            "The Critic evaluates evidence quality, finds methodology conflicts, flags weak studies "
            "— it does NOT search. The Synthesizer weaves findings and critique into a final report "
            "— it does NOT search or critique. They communicate through FILES (searcher_output.md → "
            "critic_output.md → final_report.md). Each has its own context window. Anthropic's "
            "research found multi-agent (specialized) outperforms single-agent by 90.2%."
        ),
        "what_to_watch": [
            "Searcher agent spawns → writes searcher_output.md with raw findings",
            "Critic agent spawns → reads searcher output, writes critic_output.md with quality ratings",
            "Synthesizer agent spawns → reads both files, writes final_report.md",
            "Evidence quality ratings: STRONG / MODERATE / WEAK per source",
            "Conflicts table with both sides + methodology differences",
        ],
        "design_principle": "Agents communicate through FILES, not shared memory. The top scorers design a better team structure.",
        "files": ["CLAUDE.md", "SKILL-orchestrator.md", "SKILL-searcher.md",
                  "SKILL-critic.md", "SKILL-synthesizer.md", "arxiv_server.py"],
        "color": "red",
    },
}

# ── Phase explanations (shown during streaming) ─────────────────────

PHASE_RULES = [
    {
        "patterns": ["decompos", "sub-question", "break the question"],
        "label": "Decomposing Question",
        "emoji": "🔍",
        "explanation": "Breaking the research question into 3-5 specific, searchable sub-questions. This prevents tunnel vision and ensures comprehensive coverage.",
    },
    {
        "patterns": ["search_arxiv"],
        "label": "Calling search_arxiv",
        "emoji": "📚",
        "explanation": "Querying the arXiv API for academic papers. Returns structured metadata: title, authors, abstract, date, URL.",
    },
    {
        "patterns": ["search_semantic_scholar"],
        "label": "Calling search_semantic_scholar",
        "emoji": "📖",
        "explanation": "Querying Semantic Scholar for citation-aware paper search. Returns papers with citation counts and influence scores.",
    },
    {
        "patterns": ["WebSearch"],
        "label": "Web Search",
        "emoji": "🌐",
        "explanation": "Searching the web for broader context — blog posts, announcements, benchmarks, documentation.",
    },
    {
        "patterns": ["WebFetch"],
        "label": "Fetching URL",
        "emoji": "📄",
        "explanation": "Reading the full content of a specific URL to extract detailed information.",
    },
    {
        "patterns": ["coverage", "gap", "insufficient"],
        "label": "Evaluating Coverage",
        "emoji": "🔄",
        "explanation": "Assessing which sub-questions have strong evidence (3+ sources) and which have gaps. This is the iteration trigger.",
    },
    {
        "patterns": ["round 2", "refined", "targeted search", "follow-up", "second round"],
        "label": "Search Round 2 (Targeted)",
        "emoji": "🎯",
        "explanation": "Using what was learned in round 1 to craft more specific queries targeting identified gaps.",
    },
    {
        "patterns": ["cross-reference", "conflict", "disagree", "consensus"],
        "label": "Cross-Referencing Sources",
        "emoji": "⚖️",
        "explanation": "Comparing what different sources say. Where do they agree (consensus)? Where do they conflict? What is nobody saying (gaps)?",
    },
    {
        "patterns": ["synthesiz", "## Key Findings", "thesis"],
        "label": "Synthesizing Report",
        "emoji": "✍️",
        "explanation": "Writing the final report: thesis first, then evidence grouped by theme (not by source), conflicts with both sides, open questions.",
    },
    {
        "patterns": ["verification agent", "spawn", "Agent tool", "subagent"],
        "label": "Spawning Verification Agent",
        "emoji": "🤖",
        "explanation": "Launching a SEPARATE Claude process with its own context window. It will independently verify every citation and claim.",
    },
    {
        "patterns": ["VERIFIED", "UNVERIFIED", "hallucinated", "checking citation"],
        "label": "Verifying Citations",
        "emoji": "✅",
        "explanation": "The verification agent is checking each paper: does it exist? Does the cited number match the source? Flagging hallucinations.",
    },
    {
        "patterns": ["searcher agent", "Searcher"],
        "label": "Searcher Agent Active",
        "emoji": "🔎",
        "explanation": "The searcher specialist is finding papers. It does NOT evaluate or synthesize — just finds and extracts structured data.",
    },
    {
        "patterns": ["critic agent", "Critic"],
        "label": "Critic Agent Active",
        "emoji": "🧐",
        "explanation": "The critic specialist is evaluating evidence quality. Rating each source STRONG/MODERATE/WEAK. Finding methodology conflicts.",
    },
    {
        "patterns": ["synthesizer agent", "Synthesizer"],
        "label": "Synthesizer Agent Active",
        "emoji": "📝",
        "explanation": "The synthesizer specialist is writing the final report from searcher findings + critic assessment. It does NOT search or critique.",
    },
    {
        "patterns": ["final_report.md", "Write tool", "saving"],
        "label": "Writing Final Report",
        "emoji": "💾",
        "explanation": "Saving the final research report to disk. This is the deliverable.",
    },
]


def detect_phase(text: str) -> dict | None:
    text_lower = text.lower()
    for rule in PHASE_RULES:
        for p in rule["patterns"]:
            if p.lower() in text_lower:
                return rule
    return None


# ── Build claude command ─────────────────────────────────────────────

def build_command(step: int) -> list[str]:
    step_dir = DEMO_DIR / f"step-{step}"

    env_file = REPO / ".workshop_env"
    auth_mode = "oauth"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("CLAUDE_AUTH_MODE="):
                auth_mode = line.split("=", 1)[1].strip()
    elif os.environ.get("ANTHROPIC_API_KEY"):
        auth_mode = "apikey"

    # Steps 1-2 use haiku (fast, no tools needed — ~10s each)
    # Steps 3-6 use sonnet (tools + agents need reasoning depth — ~60-180s each)
    model = "haiku" if step <= 2 else "sonnet"

    cmd = ["claude", "-p", "--model", model,
           "--output-format", "stream-json", "--verbose",
           "--dangerously-skip-permissions",
           "--no-session-persistence"]

    if auth_mode == "apikey":
        # --bare skips CLAUDE.md auto-discovery, hooks, plugins — clean isolated run
        cmd.append("--bare")
    else:
        # OAuth mode: disable CLAUDE.md auto-discovery so Claude doesn't read
        # the repo's reference reports and other files as context
        cmd.extend(["--add-dir", str(step_dir)])

    claude_md = (step_dir / "CLAUDE.md").read_text()
    system_prompt = claude_md

    if step >= 2 and step < 6:
        skill = (step_dir / "SKILL.md").read_text()
        system_prompt += f"\n\n---\nSKILL INSTRUCTIONS (follow this methodology):\n{skill}"

    if step == 5:
        verify = (step_dir / "SKILL-verify.md").read_text()
        system_prompt += f"\n\n---\nVERIFICATION AGENT SKILL (dispatch as subagent):\n{verify}"

    if step == 6:
        system_prompt = claude_md
        for name in ["orchestrator", "searcher", "critic", "synthesizer"]:
            skill_file = step_dir / f"SKILL-{name}.md"
            if skill_file.exists():
                label = name.upper()
                system_prompt += f"\n\n---\n{label} AGENT SKILL:\n{skill_file.read_text()}"

    cmd.extend(["--system-prompt", system_prompt])

    if step <= 2:
        cmd.extend(["--disallowed-tools", "WebSearch,WebFetch,Agent"])
    elif step <= 4:
        cmd.extend(["--allowed-tools",
                     "WebSearch,WebFetch,Read,Write,"
                     "mcp__research-tools__search_arxiv,"
                     "mcp__research-tools__search_semantic_scholar"])
        cmd.extend(["--mcp-config", str(step_dir / "mcp.json")])
    else:
        cmd.extend(["--allowed-tools",
                     "WebSearch,WebFetch,Read,Write,Agent,"
                     "mcp__research-tools__search_arxiv,"
                     "mcp__research-tools__search_semantic_scholar"])
        cmd.extend(["--mcp-config", str(step_dir / "mcp.json")])

    return cmd


# ── Dimension definitions (what each eval measures + how to improve) ─

DIM_INFO = {
    "comprehensiveness": {
        "label": "Comprehensiveness",
        "weight": 0.30,
        "what": "Does the report cover all sub-topics with specific numbers, multiple perspectives, and diverse sources?",
        "fix": "Add more sub-questions in decomposition. Attribute every number to a source. Include 'at least 3 perspectives' in SKILL.md.",
    },
    "insight": {
        "label": "Insight",
        "weight": 0.35,
        "what": "Does the report go beyond description to causal reasoning? Does it show where sources conflict and explain WHY?",
        "fix": "Add 'where do sources disagree?' to SKILL.md. Add a critic agent (step 6) for STRONG/MODERATE/WEAK evidence ratings.",
    },
    "instruction_following": {
        "label": "Instruction Following",
        "weight": 0.20,
        "what": "Did it address every part of the question, stay in scope, and match the requested format?",
        "fix": "Ensure decomposition echoes every keyword from the question. Add explicit output format template to SKILL.md.",
    },
    "readability": {
        "label": "Readability",
        "weight": 0.15,
        "what": "Thesis upfront, organized by theme not source, logical flow, comparison tables, references section.",
        "fix": "Add '## References' section to output template. Add 'include comparison table'. Use transition phrases.",
    },
    "citation_bonus": {
        "label": "Citation Bonus",
        "weight": 0.10,
        "what": "Real URLs, quoted paper titles, arXiv IDs, DOIs. The bridge between 'sounds good' and 'is verifiable.'",
        "fix": "Add MCP tools (step 3) for real URLs. Use search_arxiv for arXiv IDs. Add 'cite Author (Year)' to SKILL.md.",
    },
}


# ── Score with full RACE breakdown ───────────────────────────────────

def score_output(output_path: Path, step: int, color: str) -> float | None:
    scorer = None
    for candidate in [REPO / "presenter" / "evaluate.py", REPO / "benchmark" / "evaluate.py"]:
        if candidate.exists():
            scorer = candidate
            break

    if not scorer:
        console.print(Panel(
            "[dim]Scorer not available — presenters run scoring separately.[/dim]",
            title="[bold]Score[/bold]",
            border_style="dim",
        ))
        return None

    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY not set — cannot run live LLM scoring.[/red]")
        console.print("[dim]Set it in .env or export it, then re-run.[/dim]")
        return None

    console.print("  [dim]Scoring: Claude Sonnet judges the output on 5 RACE dimensions...[/dim]")
    console.print()

    try:
        result = subprocess.run(
            [sys.executable, str(scorer), "--input", str(output_path),
             "--question", QUESTION, "--verbose"],
            capture_output=True, text=True, timeout=120,
        )
    except Exception as e:
        console.print(f"[red]Scoring failed: {e}[/red]")
        return None

    # Parse the JSON from verbose output
    score_data = {}
    try:
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("{") and "weighted_total" in line:
                score_data = json.loads(line)
                break
        if not score_data and "weighted_total" in result.stdout:
            json_match = re.search(
                r"\{[^{}]*\"weighted_total\"[^{}]*\}", result.stdout, re.DOTALL
            )
            if json_match:
                score_data = json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    if not score_data:
        for line in result.stdout.splitlines():
            if "TOTAL SCORE" in line:
                m = re.search(r"([\d.]+)/100", line)
                if m:
                    return float(m.group(1))
        return None

    total = score_data.get("weighted_total", 0)

    # ── Per-dimension breakdown with explanation ──
    dim_scores = {}
    for key, info in DIM_INFO.items():
        if key not in score_data:
            continue
        d = score_data[key]
        s = d["score"] if isinstance(d, dict) else d
        just = d.get("justification", "") if isinstance(d, dict) else ""
        dim_scores[key] = s

        bar = f"[{color}]{'█' * int(s)}{'░' * (10 - int(s))}[/{color}]"
        weighted = s * info["weight"] * 10

        console.print(
            f"  [bold]{info['label']}[/bold]  ({int(info['weight'] * 100)}% weight)"
        )
        console.print(
            f"  {bar}  [bold]{s}/10[/bold]  →  {weighted:.1f} points"
        )
        if just:
            console.print(f"  [italic]{just}[/italic]")
        console.print(f"  [dim]What this measures: {info['what']}[/dim]")
        console.print()

    # ── Total ──
    bar_len = int(total / 2.5)
    bar = f"[bold {color}]{'█' * bar_len}{'░' * (40 - bar_len)}[/bold {color}]"
    console.print(Rule("[bold]Total[/bold]"))
    console.print(f"  {bar}  [bold]{total}/100[/bold]")
    console.print()

    # ── Weakest dimension diagnosis ──
    if dim_scores:
        weakest = min(dim_scores, key=dim_scores.get)
        strongest = max(dim_scores, key=dim_scores.get)

        console.print(Panel(
            f"[yellow bold]⚠ Weakest: {DIM_INFO[weakest]['label']} "
            f"({dim_scores[weakest]}/10)[/yellow bold]\n"
            f"[bold]How to improve:[/bold] {DIM_INFO[weakest]['fix']}\n\n"
            f"[green bold]✓ Strongest: {DIM_INFO[strongest]['label']} "
            f"({dim_scores[strongest]}/10)[/green bold]\n\n"
            "[bold]This is eval-driven development.[/bold] The score tells you exactly "
            "what to fix. Read the weakest dimension → apply the fix → re-score. "
            "The eval is a first-class citizen in your agent workflow, not an afterthought.",
            title="[bold]📊 Diagnosis[/bold]",
            border_style="bright_white",
            width=min(console.width, 110),
            padding=(1, 2),
        ))
        console.print()

    return total


# ── Run a step ───────────────────────────────────────────────────────

def run_step(step: int, prev_score: float = 0) -> tuple[str, float]:
    meta = STEPS[step]
    step_dir = DEMO_DIR / f"step-{step}"
    color = meta["color"]
    model = "haiku" if step <= 2 else "sonnet"

    # ── Header ──
    console.print()
    console.print(Rule(f"[bold {color}] Step {step}: {meta['title']} [/]", style=color))
    console.print()

    # ── Why this step matters ──
    console.print(Panel(
        f"[bold]Concept:[/bold] {meta['concept']}\n\n"
        f"[bold]What changes:[/bold] {meta['what_changes']}\n\n"
        f"[bold]Why it matters:[/bold]\n{meta['why_it_matters']}",
        title=f"[bold {color}]Step {step}: {meta['title']}[/bold {color}]",
        border_style=color,
        width=min(console.width, 110),
        padding=(1, 2),
    ))
    console.print()

    # ── What to watch for ──
    watch_items = "\n".join(f"  • {w}" for w in meta["what_to_watch"])
    console.print(Panel(
        f"[bold]Watch for:[/bold]\n{watch_items}",
        title="[bold]👀 What to Watch[/bold]",
        border_style="bright_white",
        width=min(console.width, 110),
        padding=(1, 2),
    ))
    console.print()

    # ── Show ALL files — full contents, bold and readable ──
    for fname in meta["files"]:
        fpath = step_dir / fname
        if not fpath.exists():
            continue
        content = fpath.read_text().strip()
        line_count = len(content.splitlines())
        if fname.endswith(".py"):
            renderable = Syntax(content, "python", theme="monokai",
                                line_numbers=True, word_wrap=True)
        else:
            renderable = Markdown(content)
        console.print(Panel(
            renderable,
            title=f"[bold {color}]{fname}[/bold {color}]  ({line_count} lines)",
            border_style=color,
            width=min(console.width, 110),
            padding=(1, 2),
        ))
        console.print()

    # ── Run claude ──
    cmd = build_command(step)
    console.print(Rule(f"[bold]Running Step {step}  (model: {model})[/bold]", style="bright_white"))
    console.print()

    start = time.time()
    output_text = ""
    tool_calls = []
    seen_phases = set()

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        cwd=str(step_dir),
    )
    proc.stdin.write(QUESTION)
    proc.stdin.close()

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = msg.get("type", "")

        if msg_type == "assistant":
            content_list = msg.get("message", {}).get("content", [])
            for content in content_list:
                ct = content.get("type", "")

                if ct == "text":
                    text = content.get("text", "")
                    output_text += text

                    # Detect and display phase changes with explanations
                    phase = detect_phase(text)
                    if phase and phase["label"] not in seen_phases:
                        seen_phases.add(phase["label"])
                        console.print(
                            f"  {phase['emoji']} [bold]{phase['label']}[/bold]"
                        )
                        console.print(
                            f"     [dim]{phase['explanation']}[/dim]"
                        )
                        console.print()

                elif ct == "tool_use":
                    tool_name = content.get("name", "unknown")
                    tool_input = content.get("input", {})
                    tool_calls.append(tool_name)
                    short = tool_name.split("__")[-1] if "__" in tool_name else tool_name

                    # Show tool call with input context
                    tool_detail = ""
                    if "query" in tool_input:
                        tool_detail = f' query="{tool_input["query"]}"'
                    elif "url" in tool_input:
                        tool_detail = f' url="{tool_input["url"][:60]}"'
                    elif "command" in tool_input:
                        tool_detail = f' cmd="{tool_input["command"][:60]}"'

                    console.print(f"  [yellow]→ {short}[/yellow]{tool_detail}")

                    # Show phase explanation for tool calls
                    phase = detect_phase(tool_name)
                    if phase and phase["label"] not in seen_phases:
                        seen_phases.add(phase["label"])
                        console.print(f"     [dim]{phase['explanation']}[/dim]")
                        console.print()

        elif msg_type == "result":
            cost = msg.get("cost_usd", 0)
            duration = msg.get("duration_ms", 0)
            console.print()
            console.print(
                f"  [green]✓ Complete[/green] — "
                f"${cost:.3f} | {duration/1000:.1f}s | "
                f"{len(tool_calls)} tool calls"
            )

    proc.wait()
    elapsed = time.time() - start

    # ── Save output ──
    output_path = step_dir / "output.md"
    output_path.write_text(output_text)

    # ── Show agent-created artifact files (FULL contents) ──
    artifact_files = [
        ("research_draft.md", "Research Draft (pre-verification)"),
        ("searcher_output.md", "Searcher Agent Output"),
        ("critic_output.md", "Critic Agent Assessment"),
        ("final_report.md", "Final Synthesized Report"),
    ]
    found_artifacts = []
    for af_name, af_label in artifact_files:
        af_path = step_dir / af_name
        if af_path.exists() and af_path.stat().st_mtime > start:
            found_artifacts.append(af_name)
            content = af_path.read_text().strip()
            console.print()
            console.print(Panel(
                Markdown(content),
                title=f"[bold green]📄 {af_label}[/bold green]  ({af_name}, {len(content.splitlines())} lines)",
                border_style="green",
                width=min(console.width, 110),
                padding=(1, 2),
            ))

    # ── Show the FULL output as rendered Markdown ──
    console.print()
    console.print(Rule(f"[bold {color}]Output: Step {step}[/bold {color}]", style=color))
    console.print()

    if output_text.strip():
        word_count = len(output_text.split())
        console.print(Panel(
            Markdown(output_text.strip()),
            title=f"[bold {color}]Research Report[/bold {color}]  ({word_count} words)",
            border_style=color,
            width=min(console.width, 110),
            padding=(1, 2),
        ))
    else:
        console.print("[red]No output generated. Check if Claude is authenticated.[/red]")

    # ── Design principle ──
    console.print()
    console.print(Panel(
        f"[bold italic]{meta['design_principle']}[/bold italic]",
        title="[bold]💡 Design Principle[/bold]",
        border_style=color,
        padding=(0, 2),
    ))
    console.print()

    # ── Full RACE scoring breakdown (live LLM judge) ──
    console.print(Rule("[bold]Scoring[/bold]", style="bright_white"))
    console.print()
    score = score_output(output_path, step, color)

    # ── Delta from previous step ──
    EXPECTED_STAIRCASE = {1: 21, 2: 37, 3: 58, 4: 53, 5: 90, 6: 93}
    expected = EXPECTED_STAIRCASE.get(step, 0)

    if prev_score > 0 and score:
        delta = score - prev_score
        delta_sign = "+" if delta > 0 else ""
        if delta > 15:
            console.print(
                f"  [green bold]▲ {delta_sign}{delta:.1f} points from step {step - 1}[/green bold]  "
                f"[bold]← Big jump! This is what {meta['title'].split('(')[0].strip()} adds.[/bold]"
            )
        elif delta > 0:
            console.print(
                f"  [green]▲ {delta_sign}{delta:.1f} points[/green] from step {step - 1}"
            )
        elif delta < 0:
            console.print(
                f"  [yellow]▼ {delta:.1f} points[/yellow] from step {step - 1}  "
                f"[dim](expected: {expected})[/dim]"
            )
        console.print()

    # ── Compact summary ──
    console.print(Panel(
        f"[bold]Score:[/bold] {score or '?'}/100  (expected: {expected})  |  "
        f"[bold]Words:[/bold] {len(output_text.split())}  |  "
        f"[bold]Tools:[/bold] {len(tool_calls)}  |  "
        f"[bold]Time:[/bold] {elapsed:.1f}s",
        title=f"[bold {color}]Step {step} Complete[/bold {color}]",
        border_style=color,
    ))
    console.print()

    return output_text, score or 0


# ── Staircase ────────────────────────────────────────────────────────

def show_staircase(scores: dict[int, float]):
    console.print()
    console.print(Rule("[bold]Score Staircase[/bold]", style="bright_white"))
    console.print()

    table = Table(title="[bold]Same Model. Six Engineering Concepts.[/bold]",
                  show_lines=True, width=min(console.width, 90))
    table.add_column("Step", style="bold", justify="center", width=6)
    table.add_column("Concept", width=30)
    table.add_column("Score", justify="right", width=8)
    table.add_column("", width=25)
    table.add_column("Delta", justify="right", width=8)

    prev = 0
    for step in sorted(scores.keys()):
        s = scores[step]
        meta = STEPS[step]
        bar_len = int(s / 4)
        bar = f"{'█' * bar_len}{'░' * (25 - bar_len)}"
        delta = f"+{s - prev:.0f}" if s > prev else f"{s - prev:.0f}"
        color = meta["color"]
        table.add_row(
            str(step),
            meta["title"],
            f"[bold {color}]{s:.1f}[/]",
            f"[{color}]{bar}[/]",
            delta if step > min(scores.keys()) else "—",
        )
        prev = s

    console.print(table)
    console.print()
    console.print("[bold]\"Same model. Six engineering concepts. The system around the model matters more than the model itself.\"[/]")
    console.print()


# ── Main ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        console.print()
        console.print(Panel(
            "[bold]python demo/run_demo.py <step|all>[/bold]\n\n"
            "  [bold cyan]python demo/run_demo.py 1[/]        Step 1: Context (CLAUDE.md)\n"
            "  [bold cyan]python demo/run_demo.py 2[/]        Step 2: Skill (SKILL.md)\n"
            "  [bold cyan]python demo/run_demo.py 3[/]        Step 3: Custom Tool (MCP Server)\n"
            "  [bold cyan]python demo/run_demo.py 4[/]        Step 4: Iterative Skill\n"
            "  [bold cyan]python demo/run_demo.py 5[/]        Step 5: Verification Agent\n"
            "  [bold cyan]python demo/run_demo.py 6[/]        Step 6: Team of Agents\n"
            "  [bold cyan]python demo/run_demo.py all[/]      Run all steps 1→6 (full staircase)\n"
            "  [bold cyan]python demo/run_demo.py 1 3 6[/]    Run specific steps",
            title="[bold]Usage[/bold]",
            border_style="bright_blue",
        ))
        console.print()
        sys.exit(1)

    if sys.argv[1] == "all":
        steps = [1, 2, 3, 4, 5, 6]
    else:
        steps = [int(s) for s in sys.argv[1:]]

    console.print()
    console.print(Panel(
        "[bold]Build Your Research Agent[/bold]\n"
        "IISc Workshop — Compound AI Systems\n\n"
        f"[bold]Question:[/bold] {QUESTION}",
        title="[bold bright_blue]🔬 Research Agent Workshop[/bold bright_blue]",
        border_style="bright_blue",
        width=min(console.width, 110),
        padding=(1, 2),
    ))

    scores = {}
    prev_score = 0
    for step in steps:
        if step not in STEPS:
            console.print(f"[red]Unknown step: {step}[/red]")
            continue
        _, score = run_step(step, prev_score=prev_score)
        scores[step] = score
        prev_score = score

    if len(scores) > 1:
        show_staircase(scores)


if __name__ == "__main__":
    main()
