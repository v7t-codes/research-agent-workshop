# Step 5: Verification Agent — Design Principles

## What it physically is

A **separate Claude instance**, spawned using the `Agent` tool. It has its own context window, its own tools, its own task. It runs independently and returns a result to your session.

This is the key boundary in the abstraction hierarchy. Everything up to step 4 runs in one session. Here, we spawn a SECOND Claude process.

## The design principle: Verification must be independent

If the verification runs in the same context as the research, it's biased. Claude has just spent its context window reasoning about why these papers are relevant and these claims are correct. Asking it to now verify those same claims IN THE SAME CONTEXT is like asking a student to grade their own exam.

A separate context window means **fresh eyes**. The verification agent reads the research output cold — no access to the reasoning that produced it, no confirmation bias.

## How to build a verification agent

### The two-skill model

You need two SKILL.md files:
1. **Research skill** (updated) — does the research, then dispatches the verification agent
2. **Verification skill** — tells the verification agent what to check

### The research skill (step 5 version)

Add a new phase at the end of your research skill:

```markdown
## Phase 2: Dispatch verification agent

Use the Agent tool to spawn a verification agent with this task:
"Read the research report I just produced. For each cited paper:
1. Search for its exact title to verify it exists
2. Check if the claimed numbers match the source
3. Flag any paper you cannot find

Return a verification summary: verified count, unverified count,
hallucinated count, and specific issues found."
```

### The verification skill

```markdown
# Verification Agent

You are an independent research auditor. Your job is to check,
not to create. You have NO access to the original research
reasoning — only the output.

## What to check
1. Paper existence — search for each cited paper by exact title
2. Claim attribution — do the numbers match the cited source?
3. Internal consistency — do claims contradict each other?

## Rules
- Be thorough: check EVERY citation, not just a sample
- Be honest: if you can't verify, say so
- Be specific: "Paper X not found" not "some papers unverified"
- Do NOT add new information — only verify what's there
```

## How to use the Agent tool in Claude Code

In your SKILL.md, you tell Claude to use the Agent tool:

```markdown
Dispatch using the Agent tool:
- Task: "Verify the research report at output.md. Check every citation..."
- The agent will have access to WebSearch and WebFetch
- Wait for the agent to return its verification summary
- Incorporate the findings: remove hallucinated papers, flag unverified claims
```

Claude Code's Agent tool spawns a new Claude subprocess. It's not a function call — it's a separate process with separate state.

## What the verification agent catches

Common findings:
- **Hallucinated papers** — titles that look plausible but don't exist. "Zhang et al. (2025), 'Efficient MoE Scaling with Adaptive Routing'" sounds real but may not be.
- **Misattributed numbers** — the paper exists but the claimed benchmark number is from a different paper
- **Outdated claims** — the cited result has been superseded by newer work
- **Author/year mismatches** — wrong year, wrong first author

## Score impact

| | Before (step 4) | After (step 5) |
|--|--|--|
| **What changes** | 2-3 hallucinated papers pass through. Some numbers misattributed. | Hallucinated citations caught and removed. Misattributed numbers corrected or flagged. |
| **What doesn't change** | Coverage and depth are the same. The research methodology didn't change. | Same — verification improves accuracy, not coverage. |

The RACE "insight" dimension rewards "identifies where sources conflict." The verification agent surfaces real conflicts (this paper says X, that paper says Y) rather than letting Claude gloss over them.

## Why not just add "verify your work" to the skill?

You can try it — add "after writing the report, go back and verify each citation" to step 4's iterative skill. It will partially work. But:

1. **Context pollution** — Claude has already committed to its claims. Self-verification in the same context is weaker than independent verification.
2. **Tool access** — the verification agent can use WebSearch independently. In the same session, the tool calls compete for context space.
3. **Specialization** — the verification agent's ONLY job is to check. It's not trying to also research, organize, and write.

This is the fundamental argument for agents: **independence produces objectivity**.
