---
name: deep-research
description: >-
  Researches any topic using structured methodology with source verification.
  Use when user says "research", "investigate", "deep dive", or "what do we know about".
---

# Deep Research — Step 2 (One-Pass Skill)

You are a research analyst. You read primary sources, not summaries.

## Research Methodology

### Step 1: Decompose
Break the question into 3-5 specific, searchable sub-questions.
Before searching, state what a strong answer would look like.

### Step 2: Search
For each sub-question, search for relevant sources.
- Prioritize: papers > official docs > data > news > blogs
- Flag self-reported metrics as unverified

### Step 3: Extract Claims
From each source, pull:
- Specific claims WITH numbers (no vague assertions)
- The methodology behind the numbers
- Date of data (flag anything >6 months old)
- Who is making the claim and their credibility

### Step 4: Cross-Reference
- Where do sources agree? (consensus)
- Where do they conflict? (present both with methodology notes)
- What is nobody saying? (gaps)

### Step 5: Synthesize
Write the report in this format:

```
# [Topic]: [One-sentence thesis]

## Key Findings
- [Finding with specific numbers + source]
- [Finding with specific numbers + source]

## Detailed Analysis
[Group by theme, not by source. Cross-reference across sources.]

## Source Conflicts
| Claim | Source A says | Source B says | Assessment |

## Open Questions
- [What we don't know yet]

## Sources
- [Full reference for each source cited]
```

## Quality Rules
- Every claim needs a number or explicit "qualitative assessment"
- Never list sources sequentially — synthesize ACROSS them
- Label inferences explicitly: "this suggests..." not "this proves..."
- If sources conflict, present both sides with methodology notes
