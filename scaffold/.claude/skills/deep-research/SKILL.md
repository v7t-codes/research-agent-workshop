---
name: deep-research
description: >-
  [TASK 2A: Write the trigger phrases. When should Claude invoke this skill?
  e.g., "Use when user says research, investigate, deep dive, what do we know about."]
allowed-tools: WebSearch WebFetch Read Write
---

# Deep Research

<!--
  TASK 2B: Write your research methodology.
  
  Requirements:
  - Must start with a Decompose step (break the question BEFORE searching)
  - Must include at least 3 search/extraction steps
  - Must specify an output format with every section named
  - Must include quality rules (what counts as a claim? what's not acceptable?)
  
  Do NOT copy the step-2 methodology. Design your own.
  Think: how would a careful researcher in your domain actually approach a question?
-->

## Step 1: Decompose

[How do you break a question into searchable sub-questions?
What do you do before searching? What does "a good answer" look like?]

## Step 2: [Name your search strategy]

[For each sub-question, what do you search for?
What sources do you prioritize? How many sources per sub-question?]

## Step 3: [Name your extraction strategy]

[What do you pull from each source?
What must every claim include? What makes a claim not good enough?]

## Step 4: [Name your cross-reference strategy]

[How do you find agreements? Conflicts? Gaps?
What do you do when sources disagree?]

## Step 5: Synthesize

Write the report in this exact format:

```
[TASK 2C: Design your output format here.
Every section must be named.
Don't just say "write a report" — say exactly what sections exist and what goes in each.

Example sections to consider:
- Opening thesis (one sentence)
- Key findings with numbers + sources
- Analysis by theme (NOT by source)
- Conflicts table (Claim | Source A says | Source B says | Your assessment)
- Open questions / what we don't know
- Full reference list]
```

## Quality Rules

<!--
  TASK 2D: Write your quality rules.
  What is NOT acceptable in the output?
  What must every claim have?
  What should Claude flag explicitly?
-->

- [Rule 1]
- [Rule 2]
- [Rule 3]
