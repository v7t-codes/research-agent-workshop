#!/usr/bin/env python3
"""
Research Agent Workshop — Rich TUI Demo Runner

Beautiful terminal UI that streams Claude's output in real-time,
shows what's happening at each phase, and displays file artifacts
as they're created.

Usage:
    python demo/run_demo.py 1          # Run step 1
    python demo/run_demo.py 6          # Run step 6
    python demo/run_demo.py 1 2 3      # Run steps 1, 2, 3 in sequence
    python demo/run_demo.py all        # Run all steps (staircase demo)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

REPO = Path(__file__).resolve().parent.parent
DEMO_DIR = REPO / "demo"
QUESTION = (DEMO_DIR / "QUESTION.txt").read_text().strip()

console = Console()

# ── Step metadata ────────────────────────────────────────────────────

STEPS = {
    1: {
        "title": "Context (CLAUDE.md)",
        "concept": "Identity — WHO Claude works for",
        "what_changes": "Claude gets your domain, sources, citation format, constraints.",
        "what_to_watch": "Output shifts from generic to domain-appropriate terminology.",
        "design_principle": "Context answers WHO, not HOW. Five sentences change the output.",
        "files": ["CLAUDE.md"],
        "color": "blue",
    },
    2: {
        "title": "Skill (SKILL.md)",
        "concept": "Methodology — HOW to do the work, one pass",
        "what_changes": "Claude follows a recipe: decompose → search → extract → cross-reference → synthesize.",
        "what_to_watch": "Output is now STRUCTURED: thesis, findings with numbers, conflicts table, references.",
        "design_principle": "A skill is a RECIPE, not a CHEF. One pass, top to bottom.",
        "files": ["CLAUDE.md", "SKILL.md"],
        "color": "green",
    },
    3: {
        "title": "Custom Tool (MCP Server)",
        "concept": "Capability — new actions Claude can take",
        "what_changes": "Claude can call search_arxiv() and search_semantic_scholar(). Real papers, real URLs.",
        "what_to_watch": "Real paper titles from 2025-2026, arXiv URLs, citation counts. The source grounding factor unlocks.",
        "design_principle": "Structured data beats unstructured search. 50 lines of Python gave Claude access to arXiv.",
        "files": ["CLAUDE.md", "SKILL.md", "arxiv_server.py"],
        "color": "yellow",
    },
    4: {
        "title": "Iterative Skill (Loop Logic)",
        "concept": "Autonomy — Claude decides when to loop",
        "what_changes": "After searching, Claude evaluates coverage. If gaps remain, it refines queries and searches again.",
        "what_to_watch": "Multiple search rounds. Claude says 'coverage insufficient for sub-question 3, refining...'",
        "design_principle": "Three design choices: what triggers a loop, how to refine, when to STOP. Always set a max.",
        "files": ["CLAUDE.md", "SKILL.md", "arxiv_server.py"],
        "color": "magenta",
    },
    5: {
        "title": "Verification Agent",
        "concept": "Independence — separate context window, fresh eyes",
        "what_changes": "After researching, Claude spawns a SECOND process that independently checks every citation.",
        "what_to_watch": "A verification agent starts — searches for each paper by title, flags hallucinations.",
        "design_principle": "Verification must be independent. Same context = shared bias. Separate process = fresh eyes.",
        "files": ["CLAUDE.md", "SKILL.md", "SKILL-verify.md", "arxiv_server.py"],
        "color": "cyan",
    },
    6: {
        "title": "Team of Agents",
        "concept": "Specialization — each agent does one thing well",
        "what_changes": "Three specialized agents: Searcher → Critic → Synthesizer. Each has own context window.",
        "what_to_watch": "Three agents spawn in sequence. They communicate through FILES, not shared memory.",
        "design_principle": "The top scorers design a better team. Add a devil's advocate. Run parallel searchers.",
        "files": ["CLAUDE.md", "SKILL-orchestrator.md", "SKILL-searcher.md", "SKILL-critic.md", "SKILL-synthesizer.md", "arxiv_server.py"],
        "color": "red",
    },
}

# ── Phase detection from streaming output ────────────────────────────

PHASE_PATTERNS = [
    ("🔍 Decomposing question", ["decompos", "sub-question", "break the question", "sub_question"]),
    ("🌐 Searching (Round 1)", ["search_arxiv", "search_semantic_scholar", "WebSearch", "searching for"]),
    ("📊 Extracting claims", ["extract", "specific claim", "key finding", "methodology"]),
    ("🔄 Evaluating coverage", ["coverage", "gap", "insufficient", "round 2", "refin"]),
    ("🌐 Searching (Round 2)", ["second round", "targeted search", "follow-up"]),
    ("⚖️ Cross-referencing", ["cross-reference", "conflict", "disagree", "consensus"]),
    ("✍️ Synthesizing report", ["synthesiz", "final report", "thesis", "## Key Findings"]),
    ("🤖 Spawning verification agent", ["Agent tool", "verification agent", "spawn", "subagent"]),
    ("✅ Verifying citations", ["VERIFIED", "UNVERIFIED", "hallucinated", "checking citation"]),
    ("🤖 Spawning searcher agent", ["searcher agent", "Searcher"]),
    ("🤖 Spawning critic agent", ["critic agent", "Critic"]),
    ("🤖 Spawning synthesizer agent", ["synthesizer agent", "Synthesizer"]),
    ("📝 Writing final report", ["final_report.md", "Write tool", "saving"]),
]


def detect_phase(text: str) -> str | None:
    text_lower = text.lower()
    for label, patterns in PHASE_PATTERNS:
        for p in patterns:
            if p.lower() in text_lower:
                return label
    return None


# ── Build claude command for a step ──────────────────────────────────

def build_command(step: int) -> list[str]:
    step_dir = DEMO_DIR / f"step-{step}"

    # Detect auth mode
    env_file = REPO / ".workshop_env"
    auth_mode = "oauth"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("CLAUDE_AUTH_MODE="):
                auth_mode = line.split("=", 1)[1].strip()
    elif os.environ.get("ANTHROPIC_API_KEY"):
        auth_mode = "apikey"

    cmd = ["claude", "-p", "--model", "sonnet",
           "--output-format", "stream-json", "--verbose",
           "--dangerously-skip-permissions"]

    if auth_mode == "apikey":
        cmd.append("--bare")

    # Build system prompt
    claude_md = (step_dir / "CLAUDE.md").read_text()
    system_prompt = claude_md

    if step >= 2:
        skill = (step_dir / "SKILL.md").read_text()
        system_prompt += f"\n\n---\nSKILL INSTRUCTIONS (follow this methodology):\n{skill}"

    if step == 5:
        verify = (step_dir / "SKILL-verify.md").read_text()
        system_prompt += f"\n\n---\nVERIFICATION AGENT SKILL (dispatch as subagent):\n{verify}"

    if step == 6:
        # Replace SKILL.md section with orchestrator + agent skills
        system_prompt = claude_md
        for name in ["orchestrator", "searcher", "critic", "synthesizer"]:
            skill_file = step_dir / f"SKILL-{name}.md"
            if skill_file.exists():
                label = name.upper()
                system_prompt += f"\n\n---\n{label} AGENT SKILL:\n{skill_file.read_text()}"

    cmd.extend(["--system-prompt", system_prompt])

    # Tools
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


# ── Run a step with rich TUI ────────────────────────────────────────

def run_step(step: int) -> tuple[str, float]:
    meta = STEPS[step]
    step_dir = DEMO_DIR / f"step-{step}"
    color = meta["color"]

    # Header
    console.print()
    console.rule(f"[bold {color}]Step {step}: {meta['title']}[/]", style=color)
    console.print()

    # Info panel
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column(style="bold")
    info_table.add_column()
    info_table.add_row("Concept", meta["concept"])
    info_table.add_row("What changes", meta["what_changes"])
    info_table.add_row("Watch for", meta["what_to_watch"])
    info_table.add_row("Files", ", ".join(meta["files"]))
    console.print(Panel(info_table, title=f"[bold]Step {step}[/]", border_style=color))
    console.print()

    # Show ALL files for this step — full contents, bold and readable
    for fname in meta["files"]:
        fpath = step_dir / fname
        if not fpath.exists():
            continue
        content = fpath.read_text().strip()
        # Use Markdown rendering for .md files, plain text for .py
        if fname.endswith(".md"):
            renderable = Markdown(content)
        else:
            from rich.syntax import Syntax
            renderable = Syntax(content, "python", theme="monokai",
                                line_numbers=True, word_wrap=True)
        console.print(Panel(
            renderable,
            title=f"[bold]{fname}[/bold] ({len(content.splitlines())} lines)",
            border_style=color,
            width=min(console.width, 110),
            padding=(1, 2),
        ))
        console.print()

    # Run claude
    cmd = build_command(step)
    console.print(f"[dim]Running claude (model=sonnet, step={step})...[/dim]")
    console.print()

    start = time.time()
    output_text = ""
    current_phase = "🚀 Starting"
    tool_calls = []
    lines_shown = 0

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

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(current_phase, total=None)

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

                        # Detect phase changes
                        new_phase = detect_phase(text)
                        if new_phase and new_phase != current_phase:
                            current_phase = new_phase
                            progress.update(task, description=current_phase)

                        # Show output lines as they arrive
                        new_lines = output_text.count("\n")
                        if new_lines > lines_shown:
                            fresh = output_text.splitlines()[lines_shown:new_lines]
                            for fl in fresh:
                                if fl.strip():
                                    # Truncate long lines for display
                                    display = fl[:120] + "..." if len(fl) > 120 else fl
                                    console.print(f"  [dim]{display}[/dim]")
                            lines_shown = new_lines

                    elif ct == "tool_use":
                        tool_name = content.get("name", "unknown")
                        tool_calls.append(tool_name)
                        short = tool_name.split("__")[-1] if "__" in tool_name else tool_name
                        progress.update(task, description=f"🔧 Calling {short}")
                        console.print(f"  [yellow]→ tool: {short}[/yellow]")

            elif msg_type == "result":
                cost = msg.get("cost_usd", 0)
                duration = msg.get("duration_ms", 0)
                progress.update(task, description=f"✓ Done (${cost:.3f}, {duration/1000:.1f}s)")

    proc.wait()
    elapsed = time.time() - start

    # Save output
    output_path = step_dir / "output.md"
    output_path.write_text(output_text)

    # Check for agent-created files
    artifact_files = ["searcher_output.md", "critic_output.md", "final_report.md", "research_draft.md"]
    found_artifacts = []
    for af in artifact_files:
        af_path = step_dir / af
        if af_path.exists() and af_path.stat().st_mtime > start:
            found_artifacts.append(af)
            content = af_path.read_text()
            lines = content.strip().splitlines()
            snippet = "\n".join(lines[:8])
            if len(lines) > 8:
                snippet += f"\n... ({len(lines) - 8} more lines)"
            console.print()
            console.print(Panel(
                Text(snippet, style="dim"),
                title=f"[bold green]📄 {af}[/bold green] (created by agent)",
                border_style="green",
                width=min(console.width, 100),
            ))

    # Output summary
    console.print()
    word_count = len(output_text.split())
    console.print(Panel(
        Text(f"Words: {word_count}  |  Tools called: {len(tool_calls)}  |  "
             f"Time: {elapsed:.1f}s  |  Artifacts: {len(found_artifacts)}",
             style="bold"),
        title=f"[bold {color}]Step {step} Complete[/bold {color}]",
        border_style=color,
    ))

    # Show output snippet
    if output_text.strip():
        out_lines = output_text.strip().splitlines()
        # Show first 5 and last 5 lines
        if len(out_lines) > 12:
            snippet = "\n".join(out_lines[:5]) + f"\n\n... ({len(out_lines) - 10} lines omitted) ...\n\n" + "\n".join(out_lines[-5:])
        else:
            snippet = "\n".join(out_lines)
        console.print()
        console.print(Panel(
            Markdown(snippet),
            title="[bold]Output Preview[/bold]",
            border_style="dim",
            width=min(console.width, 100),
        ))

    # Design principle
    console.print()
    console.print(f"  [bold italic {color}]💡 {meta['design_principle']}[/]")
    console.print()

    # Score
    scorer = None
    for candidate in [REPO / "presenter" / "evaluate.py", REPO / "benchmark" / "evaluate.py"]:
        if candidate.exists():
            scorer = candidate
            break

    score = None
    if scorer:
        try:
            result = subprocess.run(
                [sys.executable, str(scorer), "--input", str(output_path),
                 "--quick", "--question", QUESTION],
                capture_output=True, text=True, timeout=30,
            )
            for sline in result.stdout.splitlines():
                if "TOTAL SCORE" in sline:
                    import re
                    m = re.search(r"([\d.]+)/100", sline)
                    if m:
                        score = float(m.group(1))
            if score is not None:
                bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
                console.print(f"  [bold]Score: {bar} {score}/100[/bold]")
        except Exception:
            pass

    return output_text, score or 0


# ── Staircase display ────────────────────────────────────────────────

def show_staircase(scores: dict[int, float]):
    console.print()
    console.rule("[bold]Score Staircase[/bold]")
    console.print()

    table = Table(title="Same Model. Six Engineering Concepts.", show_lines=True)
    table.add_column("Step", style="bold", justify="center")
    table.add_column("Concept", style="dim")
    table.add_column("Score", justify="right")
    table.add_column("", width=25)
    table.add_column("Delta", justify="right")

    prev = 0
    for step in sorted(scores.keys()):
        s = scores[step]
        meta = STEPS[step]
        bar_len = int(s / 4)
        bar = "█" * bar_len + "░" * (25 - bar_len)
        delta = f"+{s - prev:.0f}" if s > prev else f"{s - prev:.0f}"
        color = meta["color"]
        table.add_row(
            str(step),
            meta["title"],
            f"[bold {color}]{s:.1f}[/]",
            f"[{color}]{bar}[/]",
            delta if step > 0 else "—",
        )
        prev = s

    console.print(table)
    console.print()
    console.print("[bold]\"Same model. 20 to 93. Six engineering concepts make the difference.\"[/]")
    console.print()


# ── Main ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        console.print()
        console.print(Panel(
            "[bold]python demo/run_demo.py <step|all>[/bold]\n\n"
            "  [bold cyan]python demo/run_demo.py 1[/]        Run step 1 (Context)\n"
            "  [bold cyan]python demo/run_demo.py 2[/]        Run step 2 (Skill)\n"
            "  [bold cyan]python demo/run_demo.py 3[/]        Run step 3 (MCP Tool)\n"
            "  [bold cyan]python demo/run_demo.py 4[/]        Run step 4 (Iterative)\n"
            "  [bold cyan]python demo/run_demo.py 5[/]        Run step 5 (Verification Agent)\n"
            "  [bold cyan]python demo/run_demo.py 6[/]        Run step 6 (Team of Agents)\n"
            "  [bold cyan]python demo/run_demo.py all[/]      Run all steps 1-6 (full staircase)\n"
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
        f"[dim]Question: {QUESTION[:80]}...[/dim]",
        title="🔬 Research Agent Workshop",
        border_style="bright_blue",
        width=min(console.width, 100),
    ))

    scores = {}
    for step in steps:
        if step not in STEPS:
            console.print(f"[red]Unknown step: {step}[/red]")
            continue
        _, score = run_step(step)
        scores[step] = score

    if len(scores) > 1:
        show_staircase(scores)


if __name__ == "__main__":
    main()
