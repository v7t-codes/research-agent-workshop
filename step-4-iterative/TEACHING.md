# Step 4: Iterative Skill (Loop Logic) — Design Principles

## What it physically is

The same `SKILL.md` file — but now with **decision logic**. After the initial search, the skill tells Claude: "Evaluate your coverage. If any sub-question has fewer than 3 sources, refine your queries and search again. Repeat up to 3 iterations."

Still one process. Still one context window. Still your session. The difference is Claude makes decisions within the methodology instead of just following it linearly.

## The design principle: Evaluate then decide, don't just execute

A one-pass skill is a recipe: do A, then B, then C, done. An iterative skill is a recipe with taste-testing: do A, check if it's enough, if not do A again differently, then B, check, then C.

**Why this matters:** A single search rarely covers everything. Claude finds the obvious papers but misses:
- Papers using different terminology for the same concept
- Papers from adjacent fields
- Very recent papers not yet indexed by the first query

Iteration catches what one pass misses.

## How to design iteration

### The loop structure

```
Search (breadth-first)
   ↓
Evaluate coverage
   ↓
[if gaps] → Refine queries → Search again (targeted)
   ↓
[if sufficient] → Continue to extraction
```

### Three key design choices

**1. What triggers another round?**

Bad: "Search again if needed." (Vague — Claude doesn't know when to stop.)
Good: "For each sub-question, count your sources. If any sub-question has fewer than 3 sources, search again with refined queries."

A concrete threshold prevents both too little (stopping after 1 search) and too much (searching forever).

**2. How do you refine queries?**

Bad: "Search again with a different query." (How different?)
Good: "If a sub-question has insufficient coverage, try: (a) different terminology, (b) broader scope, (c) specific author names from found papers' references."

Give Claude specific strategies for query refinement.

**3. When do you stop?**

Bad: "Keep searching until you're satisfied." (Never stops.)
Good: "Maximum 3 search rounds. Stop early if all sub-questions have 3+ sources."

Always set a maximum. LLM loops without bounds burn tokens and time.

## Why this is NOT an agent

This is the most common confusion. An iterative skill:
- Runs in YOUR session, YOUR context window
- Shares memory with everything else in your conversation
- Is the SAME Claude process making decisions

An agent (step 5):
- Is a SEPARATE Claude process
- Has its OWN context window
- Runs independently and returns a result

The iteration here is like a chef tasting and adjusting. An agent is like hiring a second chef.

## Real example: the diff from step 2 to step 4

Step 2 SKILL.md:
```markdown
### Step 2: Search
For each sub-question, run WebSearch.
```

Step 4 SKILL.md:
```markdown
### Step 2: Search (breadth-first)
For each sub-question, search using both WebSearch and arXiv/Semantic Scholar tools.

### Step 3: Evaluate coverage
For each sub-question, count sources found:
- 3+ sources → sufficient
- 1-2 sources → needs more
- 0 sources → needs different query terms

### Step 4: Targeted depth search (if needed)
For sub-questions with insufficient coverage:
- Try alternative terminology
- Search for authors cited in found papers
- Broaden or narrow the query
Maximum 3 total search rounds.

### Step 5: Evaluate again
If all sub-questions have 3+ sources, proceed to extraction.
Otherwise, note gaps explicitly in the report.
```

## Score impact

| | Before (step 3) | After (step 4) |
|--|--|--|
| **What changes** | Found some papers but missed several. Coverage gaps visible. | Multiple search rounds fill gaps. Papers found via alternative terminology, author names. |
| **What doesn't change** | May still cite hallucinated papers. No independent verification. | Same risk — iteration improves coverage, not accuracy. |

The jump comes from **coverage and depth**. The RACE "comprehensiveness" dimension rewards breadth, and iteration is how you get breadth systematically.
