# Scaffold

Starting files for the build session. These are intentionally incomplete.

| File | What it is | What you fill in |
|------|-----------|-----------------|
| `CLAUDE.md` | Research identity template | Your domain, preferences, constraints |
| `.claude/skills/deep-research/SKILL.md` | Research methodology skeleton | Your methodology, output format, quality rules |
| `mcp_skeleton.py` | FastMCP server with one placeholder tool | Your tool implementation |

**The `step-*/` directories show a complete example at each level.
Read them. Don't copy them into your working directory.**

Start here:
```bash
cp scaffold/CLAUDE.md ./CLAUDE.md
cp scaffold/.claude/skills/deep-research/SKILL.md .claude/skills/deep-research/SKILL.md
cp scaffold/mcp_skeleton.py mcp_server.py
```

Then edit each file. See `BUILD.md` for the full task breakdown.
