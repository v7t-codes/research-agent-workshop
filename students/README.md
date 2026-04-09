# Students

## Setup (do this once, before the build session)

```bash
# 1. Install Claude Code
npm install -g @anthropic-ai/claude-code

# 2. Log in with your claude.ai account (free tier works)
claude auth login
# Opens browser → log in → done

# 3. Install Python dependency for MCP server
pip install fastmcp

# 4. Clone the repo
git clone https://github.com/v7t-codes/research-agent-workshop
cd research-agent-workshop
```

No API key needed for the build session.
The `--quick` scorer (heuristic) runs offline. The LLM scorer needs an API key — the presenters handle final scoring.

---

## Your working directory

```bash
# Copy the template to your group's folder (use your names, no spaces)
cp -r students/template students/alice-bob

# Work from your folder
cd students/alice-bob
```

Your folder structure:
```
students/alice-bob/
  CLAUDE.md                          ← Task 1: fill this in
  .claude/
    settings.json                    ← copy as-is, update server path if needed
    skills/
      deep-research/
        SKILL.md                     ← Task 2: fill this in
  mcp_server.py                      ← Task 3: implement your tool
```

Run `claude` from inside your folder. CLAUDE.md is auto-loaded. Your skills are auto-loaded. Your MCP server starts via settings.json.

---

## Scoring your output

```bash
# From repo root:
python3 benchmark/evaluate.py --input students/alice-bob/output.md \
  --quick --question "your question here"
```

---

## Submitting for the competition

When you're ready to compete:

```bash
# From repo root
git checkout -b student/alice-bob
git add students/alice-bob/
git commit -m "alice-bob submission"
git push origin student/alice-bob
```

Open a PR against main. Title: your group name.
The presenters will run the benchmark across all submissions and post the leaderboard.

---

## Rules

- You can READ step-1 through step-6 as reference. You cannot copy them into your folder.
- Your CLAUDE.md, SKILL.md, and mcp_server.py must be substantially different from the examples.
- Your MCP server must implement at least one tool that calls an external API (not just the arxiv server copied verbatim).
