# Step 4: Iterative Skill (Making it Loop)

## What you're adding
Decision logic to the skill. "After searching, evaluate coverage. If gaps found, search again with refined queries. Repeat up to 3 rounds."

## What it is
An iterative skill includes instructions that make Claude LOOP — search, evaluate, decide whether to continue, search again with better queries. Claude is now making autonomous decisions about when to stop.

## What it is NOT — this is important
**This is NOT an agent yet.** It's still running in YOUR Claude session, YOUR context window. The same process. The skill just has smarter instructions — instructions that include evaluation and decision points.

Think of it this way:
- Step 2 skill: "Follow these 5 steps in order" (a recipe)
- Step 4 skill: "Follow these steps, then check if the result is good enough, and if not, go back to step 2 with better inputs" (a recipe with a taste-and-adjust loop)

Both run in the same kitchen (your session). The difference is the recipe now includes judgment calls.

## Why this is different from an agent (step 5)
In step 5, you'll spawn a SEPARATE Claude instance — a different process with its own context window. That's physically different. This step is still one process that loops.

## What changes
- Coverage jumps: the agent identifies gaps and fills them
- Depth increases: follow-up queries are more targeted
- New sub-questions emerge from initial findings

## What to do
1. Copy everything from steps 1-3 into your working directory
2. Replace your SKILL.md with this version (has the iteration loop)
3. Run: `/deep-research [practice problem 2]`
4. Watch Claude search, evaluate, refine, and search again
5. Evaluate: `python benchmark/evaluate.py --input output.md`

## What you'll see
Score jumps from ~55 to ~72. Coverage and depth dimensions jump. But citations may still include hallucinations — no verification yet.
