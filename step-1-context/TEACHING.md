# Step 1: Context (CLAUDE.md) — Design Principles

## What it physically is

A `CLAUDE.md` file in your project root. Claude reads it automatically at the start of every session. It's a plain markdown file — nothing special about the format.

## The design principle: Identity before methodology

Context answers **WHO**, not **HOW**.

Before telling Claude how to research, you tell it who it's working for. Same question asked by a physicist vs. a policy analyst should produce different outputs. Without context, Claude defaults to "helpful assistant" — generic, unfocused, wrong sources.

**Why this matters for research agents:** A research report on protein folding written for a molecular biologist should cite PDB IDs and mention force fields. The same report written for a biotech investor should focus on IP landscape and clinical timelines. The CLAUDE.md is what makes this distinction.

## What goes in a good CLAUDE.md

1. **Your field and sub-field** — "computational neuroscience, focusing on neural coding" not just "CS"
2. **Your preferred sources** — specific conferences (NeurIPS, ICML), journals (Nature, Science), databases (arXiv cs.AI)
3. **Your citation format** — Author (Year) inline, APA, IEEE, whatever your field uses
4. **Your constraints** — "never state claims without attribution", "flag anything older than 12 months"
5. **What "good" looks like** — "I value empirical results with specific numbers, reproducibility, clear methodology"

## What does NOT go in CLAUDE.md

- Methodology (→ that's a **skill**, step 2)
- Tool configuration (→ that's step 3)
- Iteration logic (→ that's step 4)
- How to verify (→ that's step 5)

Mixing these in CLAUDE.md makes it fragile. Keep identity separate from methodology.

## Design exercise

> "If you could only give Claude 5 sentences before it started researching for you, what would those 5 sentences be?"

Those 5 sentences are your CLAUDE.md. Everything else is methodology.

## Real example

The workshop CLAUDE.md:
```markdown
# Research Context
You are assisting a researcher in computer science and artificial intelligence.

## Domain
- Primary fields: machine learning, deep learning, AI systems, agent architectures
- I read papers from: NeurIPS, ICML, ICLR, ACL, EMNLP, CVPR, arXiv cs.AI/cs.CL/cs.LG

## Preferences
- Citation format: Author (Year) inline, full reference list at end
- Prioritize: peer-reviewed papers > preprints > technical blogs > news articles

## Constraints
- Never state claims without attribution
- If you're uncertain, say so explicitly
```

## Score impact

| | Before (step 0) | After (step 1) |
|--|--|--|
| **What changes** | Generic assistant voice, wrong journals, no citation format | Domain-appropriate framing, right terminology, right sources |
| **What doesn't change** | No structure, no real sources, one pass, shallow | Still no structure, still from training data, still one pass |

The jump is small but foundational. Every subsequent step builds on this identity.
