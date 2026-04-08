# Step 1: Context (CLAUDE.md)

## What you're adding
A `CLAUDE.md` file — static identity and domain knowledge that Claude reads at the start of every session.

## What it is
Context tells Claude WHO it's working for. Your field, your preferred sources, your citation format, what "good" looks like in your domain. It's not methodology — it doesn't tell Claude HOW to research. It just sets the frame.

## What changes
- Output uses correct terminology for your field
- Sources are more relevant (right journals, right conferences)
- Citation format matches your preference
- Generic language replaced with domain-appropriate framing

## What to do
1. Copy `CLAUDE.md` to your working directory root
2. Edit it for YOUR domain — your field, your conferences, your preferences
3. Run: ask Claude to research your practice problem
4. Run `python benchmark/evaluate.py --input output.md` to see your score

## What you'll see
Score jumps from ~18 (raw) to ~25. Better framing, but still no structure, no real sources, no depth.
