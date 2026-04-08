# Step 2: Skill (SKILL.md)

## What you're adding
A `SKILL.md` file — a methodology that Claude follows when triggered. This is persistent (survives sessions), reusable (trigger it any time), and portable (works in Claude Code, Cursor, Codex, Copilot).

## What it is
A skill tells Claude HOW to do the work. The research loop: decompose → search → extract claims → cross-reference → synthesize. It's a recipe on disk.

## What it is NOT
A skill is **one pass**. Claude follows the instructions top to bottom. It does NOT decide to go back and search again. It does NOT spawn separate processes. It's methodology, not autonomy.

## The physical difference from an agent
A skill runs in YOUR Claude session. Same process, same context window. An agent (step 5) is a SEPARATE Claude instance with its own context window. That's a completely different thing.

## What changes
- Output is structured: thesis, findings, conflicts, gaps
- Claims have specific numbers, not vague assertions
- Sources are cross-referenced, not listed sequentially

## What to do
1. Copy `CLAUDE.md` from step-1 to your working directory
2. Copy `.claude/skills/deep-research/SKILL.md` to your working directory
3. Run: `/deep-research [practice problem]`
4. Evaluate: `python benchmark/evaluate.py --input output.md`

## What you'll see
Score jumps from ~25 to ~38. Structure and specificity improve. But still one-pass, still from training data.
