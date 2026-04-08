# Practice Problem 3: Forces Verification + Team (Steps 5-6)

## Question

What is the current evidence on scaling laws for mixture-of-experts (MoE) models? Specifically: what do published results show about how MoE scaling differs from dense model scaling? Where do researchers disagree on the efficiency gains? What methodological differences explain conflicting results? Provide specific numbers from at least 5 papers.

## Why this problem

This topic has genuinely conflicting results in the literature. Different papers measure "efficiency" differently. Some compare total parameters, some compare active parameters, some compare FLOPs. Easy to hallucinate specific scaling law coefficients.

Without verification (step 5), hallucinated papers and misattributed numbers will pass through. Without a critic agent (step 6), the real methodological disagreements won't be surfaced properly.

## Expected ceiling by step

- Step 0-2 (no tools): ~25 — will mix up scaling law numbers
- Step 3-4 (tools + iteration): ~55 — finds real papers but may hallucinate some numbers
- Step 5 (verification): ~75 — catches hallucinated citations
- Step 6 (team with critic): ~90 — critic surfaces the real methodology disagreements

## What to focus on

This is where your verification agent and team composition matter. The critic agent is crucial — it needs to identify that different papers measure "efficiency" differently, which is why their results seem to conflict. A single research agent will either miss this or gloss over it.
