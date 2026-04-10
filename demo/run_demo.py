#!/usr/bin/env python3
"""
Research Agent Workshop — Rich TUI Demo Runner

Runs each step via its run.sh script, shows the output, then scores
with the full RACE breakdown (live LLM-as-judge, per-dimension).

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

# Load .env for ANTHROPIC_API_KEY
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
        "why_it_matters": "Without context, Claude is generic. With a 20-line CLAUDE.md, it becomes domain-specific. Same model — different context — different output.",
        "design_principle": "Context answers WHO, not HOW. Five sentences change the output.",
        "files": ["CLAUDE.md"],
        "color": "blue",
    },
    2: {
        "title": "Skill (SKILL.md)",
        "concept": "Methodology — HOW to do the work, one pass",
        "what_changes": "Claude follows a recipe: decompose → search → extract → cross-reference → synthesize.",
        "why_it_matters": "A skill is a RECIPE, not a CHEF. One pass, top to bottom. The output format is part of the methodology.",
        "design_principle": "A skill is a RECIPE, not a CHEF. One pass, top to bottom.",
        "files": ["CLAUDE.md", "SKILL.md"],
        "color": "green",
    },
    3: {
        "title": "Custom Tool (MCP Server)",
        "concept": "Capability — new actions Claude can take",
        "what_changes": "Claude calls search_arxiv() and search_semantic_scholar(). Real papers, real URLs.",
        "why_it_matters": "Structured data beats web search. 50 lines of Python gave Claude access to arXiv. This is usually the biggest single score jump.",
        "design_principle": "Structured data beats unstructured search. Build once, use everywhere.",
        "files": ["CLAUDE.md", "SKILL.md", "arxiv_server.py"],
        "color": "yellow",
    },
    4: {
        "title": "Iterative Skill (Loop Logic)",
        "concept": "Autonomy — Claude decides when to loop",
        "what_changes": "Claude evaluates coverage after searching. If gaps, refines queries, searches again. Max 3 rounds.",
        "why_it_matters": "Still one session, one context window — NOT an agent. The skill has decision logic: trigger, refine, stop.",
        "design_principle": "Three design choices: what triggers a loop, how to refine, when to STOP.",
        "files": ["CLAUDE.md", "SKILL.md", "arxiv_server.py"],
        "color": "magenta",
    },
    5: {
        "title": "Verification Agent",
        "concept": "Independence — separate context window, fresh eyes",
        "what_changes": "After research, a SECOND Claude process independently verifies every citation.",
        "why_it_matters": "THE KEY BOUNDARY. Separate process = own context window = no shared bias. Catches hallucinated papers.",
        "design_principle": "Verification must be independent. Same context = shared bias.",
        "files": ["CLAUDE.md", "SKILL.md", "SKILL-verify.md", "arxiv_server.py"],
        "color": "cyan",
    },
    6: {
        "title": "Team of Agents",
        "concept": "Specialization — each agent does one thing well",
        "what_changes": "Searcher → Critic → Synthesizer. Three agents, three context windows, file-based communication.",
        "why_it_matters": "Each agent focuses deeply on one thing. They communicate through FILES, not shared memory.",
        "design_principle": "The top scorers design a better team structure.",
        "files": ["CLAUDE.md", "SKILL-orchestrator.md", "SKILL-searcher.md",
                  "SKILL-critic.md", "SKILL-synthesizer.md", "arxiv_server.py"],
        "color": "red",
    },
}

# ── RACE dimension info ──────────────────────────────────────────────

DIM_INFO = {
    "comprehensiveness": {
        "label": "Comprehensiveness",
        "weight": 0.30,
        "what": "Covers all sub-topics with specific numbers, multiple perspectives, diverse sources.",
        "fix": "Add more sub-questions. Attribute every number to a source.",
    },
    "insight": {
        "label": "Insight",
        "weight": 0.35,
        "what": "Goes beyond description to causal reasoning. Shows where sources conflict and WHY.",
        "fix": "Add critic agent (step 6) for STRONG/MODERATE/WEAK evidence ratings.",
    },
    "instruction_following": {
        "label": "Instruction Following",
        "weight": 0.20,
        "what": "Addresses every part of the question. Stays in scope. Matches requested format.",
        "fix": "Ensure decomposition echoes every keyword from the question.",
    },
    "readability": {
        "label": "Readability",
        "weight": 0.15,
        "what": "Thesis upfront, organized by theme, tables, references section.",
        "fix": "Add output format template with ## References to SKILL.md.",
    },
    "citation_bonus": {
        "label": "Citation Bonus",
        "weight": 0.10,
        "what": "Real URLs, paper titles, arXiv IDs, DOIs. Verifiable sources.",
        "fix": "Add MCP tools (step 3) for real URLs. Use search_arxiv.",
    },
}


# ── Score using evaluate.py (live LLM judge) ────────────────────────

def score_output(output_path: Path, step: int, color: str) -> float | None:
    """Run evaluate.py and parse the full RACE breakdown."""
    scorer = None
    for candidate in [REPO / "presenter" / "evaluate.py", REPO / "benchmark" / "evaluate.py"]:
        if candidate.exists():
            scorer = candidate
            break

    if not scorer:
        console.print("[dim]Scorer not available.[/dim]")
        return None

    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY not set — cannot run live scoring.[/red]")
        return None

    console.print("  [dim]Scoring with Claude Sonnet (LLM-as-judge)...[/dim]")
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

    # Parse the pretty-printed JSON after "Raw scores:"
    score_data = {}
    stdout = result.stdout
    try:
        raw_idx = stdout.find("Raw scores:")
        if raw_idx >= 0:
            json_text = stdout[raw_idx:]
            brace_start = json_text.find("{")
            if brace_start >= 0:
                json_text = json_text[brace_start:]
                depth = 0
                end = 0
                for i, ch in enumerate(json_text):
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                if end > 0:
                    score_data = json.loads(json_text[:end])
    except (json.JSONDecodeError, ValueError):
        pass

    if not score_data:
        # Fallback: grab total from display output
        for line in stdout.splitlines():
            if "TOTAL SCORE" in line:
                m = re.search(r"([\d.]+)/100", line)
                if m:
                    console.print(f"  [yellow]Score: {m.group(1)}/100 (dimension breakdown unavailable)[/yellow]")
                    return float(m.group(1))
        console.print("[red]Could not parse scores.[/red]")
        console.print(f"[dim]{stdout[:500]}[/dim]")
        return None

    # ── Display each dimension with bar, score, justification, explanation ──
    total = score_data.get("weighted_total", 0)
    dim_scores = {}

    table = Table(
        title=f"[bold]RACE Evaluation — Step {step}[/bold]",
        show_lines=True,
        width=min(console.width, 110),
    )
    table.add_column("Dimension", style="bold", width=22)
    table.add_column("Score", justify="center", width=7)
    table.add_column("Bar", width=12)
    table.add_column("Pts", justify="right", width=6)
    table.add_column("LLM Justification")

    for key, info in DIM_INFO.items():
        if key not in score_data:
            continue
        d = score_data[key]
        s = d["score"] if isinstance(d, dict) else d
        just = d.get("justification", "") if isinstance(d, dict) else ""
        dim_scores[key] = s
        weighted = s * info["weight"] * 10
        bar = f"[{color}]{'█' * int(s)}{'░' * (10 - int(s))}[/{color}]"
        table.add_row(
            f"{info['label']}\n[dim]{int(info['weight']*100)}% weight[/dim]",
            f"[bold]{s}/10[/bold]",
            bar,
            f"{weighted:.0f}",
            just,
        )

    # Total row
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold {color}]{total:.1f}[/bold {color}]",
        "",
        "[bold]/100[/bold]",
        "[dim]= sum of weighted dimension scores[/dim]",
    )

    console.print(table)
    console.print()

    # ── Diagnosis: weakest + strongest + how to improve ──
    if dim_scores:
        weakest = min(dim_scores, key=dim_scores.get)
        strongest = max(dim_scores, key=dim_scores.get)

        console.print(
            f"  [yellow bold]⚠ Weakest: {DIM_INFO[weakest]['label']} ({dim_scores[weakest]}/10)[/yellow bold]  "
            f"→ {DIM_INFO[weakest]['fix']}"
        )
        console.print(
            f"  [green bold]✓ Strongest: {DIM_INFO[strongest]['label']} ({dim_scores[strongest]}/10)[/green bold]  "
            f"→ {DIM_INFO[strongest]['what']}"
        )
        console.print()
        console.print(
            "  [bold]Build → Score → Read weakest → Fix → Re-score. "
            "The eval tells you exactly what to change.[/bold]"
        )
        console.print()

    return total


# ── Run a step via its run.sh ────────────────────────────────────────

def run_step(step: int, prev_score: float = 0) -> tuple[str, float]:
    meta = STEPS[step]
    step_dir = DEMO_DIR / f"step-{step}"
    color = meta["color"]

    # ── Header ──
    console.print()
    console.print(Rule(f"[bold {color}] Step {step}: {meta['title']} [/]", style=color))
    console.print()

    # ── Why this step matters ──
    console.print(Panel(
        f"[bold]Concept:[/bold] {meta['concept']}\n"
        f"[bold]What changes:[/bold] {meta['what_changes']}\n"
        f"[bold]Why:[/bold] {meta['why_it_matters']}",
        title=f"[bold {color}]Step {step}[/bold {color}]",
        border_style=color,
        width=min(console.width, 110),
        padding=(1, 2),
    ))
    console.print()

    # ── Show ALL files — full contents ──
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

    # ── Run via run.sh ──
    run_sh = step_dir / "run.sh"
    if not run_sh.exists():
        console.print(f"[red]run.sh not found in {step_dir}[/red]")
        return "", 0

    # Steps 1-2: use haiku (fast, ~10s). Steps 3-6: sonnet (tools need reasoning).
    model = "haiku" if step <= 2 else "sonnet"
    console.print(Rule(f"[bold]Running step {step} (model: {model})[/bold]", style="bright_white"))
    console.print()

    start = time.time()
    env = os.environ.copy()
    env["DEMO_MODEL"] = model
    proc = subprocess.Popen(
        ["bash", str(run_sh)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(step_dir),
        env=env,
    )

    # Stream run.sh output live to terminal.
    # run.sh pipes through `tee` which buffers — show a spinner while waiting.
    import threading

    done_event = threading.Event()
    run_output = []

    def read_output():
        for line in proc.stdout:
            run_output.append(line)
            stripped = line.rstrip()
            if stripped:
                console.print(f"  {stripped}")
        done_event.set()

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()

    # Show elapsed time while waiting
    while not done_event.is_set():
        elapsed_so_far = time.time() - start
        console.print(f"\r  [dim]⏳ {elapsed_so_far:.0f}s elapsed...[/dim]", end="")
        done_event.wait(timeout=3)
    console.print()  # clear the timer line

    proc.wait()
    elapsed = time.time() - start

    console.print()
    console.print(f"  [green]✓ run.sh finished[/green] in {elapsed:.1f}s")
    console.print()

    # ── Read the output.md that run.sh created ──
    output_path = step_dir / "output.md"
    output_text = ""
    if output_path.exists():
        output_text = output_path.read_text()

    # ── Show full output as rendered Markdown ──
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
        console.print("[red]No output.md generated.[/red]")

    # ── Show agent artifact files ──
    for af_name in ["searcher_output.md", "critic_output.md", "final_report.md", "research_draft.md"]:
        af_path = step_dir / af_name
        if af_path.exists() and af_path.stat().st_mtime > start:
            content = af_path.read_text().strip()
            console.print()
            console.print(Panel(
                Markdown(content),
                title=f"[bold green]📄 {af_name}[/bold green]  ({len(content.splitlines())} lines)",
                border_style="green",
                width=min(console.width, 110),
                padding=(1, 2),
            ))

    # ── Design principle ──
    console.print()
    console.print(f"  [bold italic {color}]💡 {meta['design_principle']}[/]")
    console.print()

    # ── RACE Scoring (live LLM judge) ──
    console.print(Rule("[bold]RACE Evaluation[/bold]", style="bright_white"))
    console.print()

    score = None
    if output_path.exists() and output_text.strip():
        score = score_output(output_path, step, color)

    # ── Delta from previous step ──
    if prev_score > 0 and score:
        delta = score - prev_score
        delta_sign = "+" if delta > 0 else ""
        if delta > 10:
            console.print(
                f"  [green bold]▲ {delta_sign}{delta:.1f} from step {step - 1}[/green bold]  "
                f"← {meta['title'].split('(')[0].strip()} added this."
            )
        elif delta > 0:
            console.print(f"  [green]▲ {delta_sign}{delta:.1f} from step {step - 1}[/green]")
        elif delta < 0:
            console.print(f"  [yellow]▼ {delta:.1f} from step {step - 1}[/yellow]")
        console.print()

    # ── Summary ──
    console.print(Panel(
        f"[bold]Score:[/bold] {score or '?'}/100  |  "
        f"[bold]Words:[/bold] {len(output_text.split())}  |  "
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
    table.add_column("Concept", width=28)
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
    console.print("[bold]\"Same model. The system around the model matters more than the model itself.\"[/]")
    console.print()


# ── Main ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        console.print()
        console.print(Panel(
            "[bold]python demo/run_demo.py <step|all>[/bold]\n\n"
            "  [bold cyan]1[/]   Context (CLAUDE.md)\n"
            "  [bold cyan]2[/]   Skill (SKILL.md)\n"
            "  [bold cyan]3[/]   Custom Tool (MCP Server)\n"
            "  [bold cyan]4[/]   Iterative Skill\n"
            "  [bold cyan]5[/]   Verification Agent\n"
            "  [bold cyan]6[/]   Team of Agents\n"
            "  [bold cyan]all[/] Run all steps 1→6",
            title="[bold]Usage[/bold]",
            border_style="bright_blue",
        ))
        sys.exit(1)

    steps = [1, 2, 3, 4, 5, 6] if sys.argv[1] == "all" else [int(s) for s in sys.argv[1:]]

    console.print()
    console.print(Panel(
        f"[bold]Build Your Research Agent[/bold]\n"
        f"IISc Workshop\n\n"
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
