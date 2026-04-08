# Step 5: Verification Agent (Agent Tool)

## What you're adding
A SEPARATE Claude instance that audits your research output. Spawned via the `Agent` tool. Runs in its own context window. Returns a verification report.

## What it is — this is the key boundary
Everything up to step 4 runs in ONE Claude session. Your context, your skill, your tools, your iteration loop — all one process, one context window.

Step 5 introduces a SECOND process. When the research skill calls:
```
Use the Agent tool to spawn a verification agent...
```
Claude Code creates a new Claude instance. This new instance:
- Has its **own context window** (doesn't see your research reasoning)
- Has its **own tools** (WebSearch, WebFetch, Read — but not your MCP server)
- Has a **specific task** ("verify this report")
- **Runs independently** and returns a result

This is physically a different process. That's what an agent IS in Claude Code.

## Why a separate process matters
If the verification ran in the SAME session as the research, it would be biased by the research agent's reasoning. It would "remember" finding the papers and assume they're real. A separate context window means fresh eyes — the verification agent has to independently confirm everything.

## The two skills
- `deep-research/SKILL.md` — the research skill (runs in your session, does the research, then dispatches the verification agent)
- `verify-research/SKILL.md` — the verification agent's skill (runs in the AGENT's session, defines how to audit)

## What changes
- Hallucinated papers get caught and removed
- Misattributed claims get flagged
- The final report has a verification summary
- You can TRUST the output

## What to do
1. Copy everything from steps 1-4
2. Replace the research SKILL.md with this version (has the Agent dispatch)
3. Add the `verify-research/SKILL.md` 
4. Run: `/deep-research [practice problem 3]`
5. Watch the research run, then see a SEPARATE agent spawn to verify
6. Evaluate: `python benchmark/evaluate.py --input output.md`

## What you'll see
Score jumps from ~72 to ~85. Citation validity jumps hard. This is eval-driven development — the most important production concept.
