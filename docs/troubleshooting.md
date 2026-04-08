# Troubleshooting Guide

Quick-reference for presenters and students. Every issue has the exact error message, root cause, and fix command.

---

## Setup Issues

### Claude Code CLI Not Found

**Error**:
```
✗ Claude Code not found. Run: npm install -g @anthropic-ai/claude-code
zsh: command not found: claude
```

**Root cause**: The Claude Code CLI is an npm package that installs a global `claude` binary. Either Node.js is missing or the global npm bin directory is not in `$PATH`.

**Fix**:
```bash
# Step 1: Check Node.js is installed
node --version
# If missing: brew install node   (macOS)
# Or: nvm install 20               (any platform)

# Step 2: Install Claude Code
npm install -g @anthropic-ai/claude-code

# Step 3: Verify
claude --version

# Step 4: If still not found, check PATH
npm bin -g
# This prints the global bin path. Add it to PATH:
export PATH="$(npm bin -g):$PATH"
# Add to ~/.zshrc or ~/.bashrc to persist
```

**Devcontainer fallback**: The devcontainer runs `npm install -g @anthropic-ai/claude-code` automatically on creation. Use VS Code > Cmd+Shift+P > "Dev Containers: Reopen in Container".

---

### ANTHROPIC_API_KEY Not Set

**Error**:
```
✗ ANTHROPIC_API_KEY not set. Get one at console.anthropic.com
```

Or when running evaluate.py without `--quick`:
```
Warning: ANTHROPIC_API_KEY not set. Using heuristic scoring.
```

**Root cause**: The environment variable is not exported in the current shell.

**Fix**:
```bash
# Set for current session
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Persist across sessions (add to shell config)
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-..."' >> ~/.zshrc
source ~/.zshrc

# Verify
echo $ANTHROPIC_API_KEY
# Should print the key (starts with sk-ant-)
```

**Where to get a key**: https://console.anthropic.com/settings/keys

**Common mistake**: Setting the variable without `export`. Plain `ANTHROPIC_API_KEY="..."` makes it a shell variable, not an environment variable. Child processes (like `claude` and `python3`) won't see it.

**Devcontainer**: The devcontainer.json maps `${localEnv:ANTHROPIC_API_KEY}` so it inherits the key from your host machine. If not set on the host, it won't be available in the container either.

---

### Python Version Issues

**Error**:
```
✗ Python3 not found
```

Or:
```
SyntaxError: f-string expression part cannot include a backslash
```
(This happens on Python 3.9 and below -- the evaluate.py script uses Python 3.11+ features.)

**Root cause**: Python 3.11+ is required. macOS ships with Python but it may be an older version.

**Fix**:
```bash
# Check version
python3 --version

# If below 3.11, install via brew
brew install python@3.11

# Or via pyenv
pyenv install 3.11.9
pyenv global 3.11.9

# Verify
python3 --version
# Should print Python 3.11.x or higher
```

**Devcontainer fallback**: The devcontainer image is `mcr.microsoft.com/devcontainers/python:3.11`, guaranteeing the correct version.

---

### fastmcp Import Error

**Error**:
```
✗ fastmcp package not found. Run: pip install fastmcp
```

Or when step 3+ runs:
```
ModuleNotFoundError: No module named 'fastmcp'
```

**Root cause**: The `fastmcp` package is not installed in the Python environment that Claude Code uses to run the MCP server.

**Fix**:
```bash
pip install fastmcp

# If you have multiple Python installations, ensure you install for the right one:
python3 -m pip install fastmcp

# Verify
python3 -c "import fastmcp; print('OK')"
```

**Common mistake**: Installing fastmcp in a virtualenv but running the MCP server outside it. The MCP server runs as a subprocess of Claude Code, which uses the system Python. Either install globally or ensure the MCP config points to the venv's Python:

```json
{
    "mcpServers": {
        "research-tools": {
            "command": "/path/to/venv/bin/python3",
            "args": ["/absolute/path/to/arxiv_server.py"]
        }
    }
}
```

---

### anthropic Package Missing

**Error**:
```
✗ anthropic package not found. Run: pip install anthropic
```

Or when running `evaluate.py` without `--quick`:
```
Warning: anthropic package not installed. Using heuristics.
```

**Fix**:
```bash
pip install anthropic

# Verify
python3 -c "import anthropic; print('OK')"
```

This only matters for LLM scoring (without `--quick`). Heuristic scoring works without the `anthropic` package.

---

### Node.js Missing

**Error**:
```
✗ Node.js not found
```

**Root cause**: Node.js 20+ is required for the Claude Code CLI.

**Fix**:
```bash
# macOS
brew install node

# Or via nvm (preferred for managing multiple versions)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.zshrc
nvm install 20
nvm use 20

# Verify
node --version
# Should print v20.x.x or higher
```

---

### Git Not Found

**Error**:
```
✗ Git not found
```

**Fix**:
```bash
# macOS (installs via Xcode Command Line Tools)
xcode-select --install

# Or via brew
brew install git
```

This is rare on macOS -- git ships with Xcode tools.

---

## Demo Failures

### API Timeout During Live Demo

**Symptoms**: Claude Code hangs for >60 seconds, or prints a timeout/connection error.

**Root cause**: Network issues, API load, or venue WiFi instability.

**Immediate fix**:
```bash
# Kill the running command: Ctrl+C

# Show pre-computed fallback
cat test-run/outputs/step-N.md    # Replace N with current step
cat test-run/scores/step-N.txt

# Say: "Here's what it produces. Let me show you the code that makes it work."
```

**Prevention**: Run `test-run/run_steps.sh` before the workshop to have fresh fallback outputs. These are committed to the repo but may be stale if the model version changed.

---

### MCP Server Won't Start

**Symptoms**: Claude Code reports "failed to connect to MCP server" or the step 3+ command hangs at startup.

**Possible causes and fixes**:

1. **Wrong Python path**: The MCP config uses `python3` but the system resolves it to a different Python than where `fastmcp` is installed.
   ```bash
   # Check which python3
   which python3
   
   # Test the server directly
   python3 step-3-tool/mcp-servers/arxiv_server.py
   # Should start without errors. Ctrl+C to stop.
   
   # If it fails, use the full path in mcp-config.json:
   # "command": "/usr/local/bin/python3"
   ```

2. **Port conflict**: The MCP server uses stdio (not a port), so this is rare. But if another fastmcp server is running, it may conflict.
   ```bash
   # Check for running Python processes
   ps aux | grep arxiv_server
   # Kill any stale processes
   kill <PID>
   ```

3. **Absolute path wrong in mcp-config.json**: The MCP config must use absolute paths.
   ```bash
   cat test-run/mcp-config.json
   # Verify the path exists:
   ls -la /absolute/path/to/arxiv_server.py
   ```

4. **fastmcp version mismatch**: Older versions of fastmcp have different APIs.
   ```bash
   pip install --upgrade fastmcp
   ```

---

### arXiv API Returns Unrelated Results

**Symptoms**: The search for "A2A protocol agent-to-agent" returns papers about amino acids, aerodynamics, or other "A2A" matches.

**Root cause**: arXiv's search API uses `sortBy=submittedDate&sortOrder=descending`, which returns the most recent papers matching ANY of the search terms. For ambiguous queries, recent but unrelated papers may dominate.

**Explanation for audience**:
> "arXiv sorts by submission date by default. The most recent paper containing 'A2A' might be about something completely different. This is why iteration matters -- you need to refine the query, try exact phrases, or combine with other terms."

**The MCP server handles this**: The `search_arxiv` function in `arxiv_server.py` (line 46) uses `all:{query}` which searches all fields. For better precision, students can modify the server to use `ti:{query}` (title only) or `abs:{query}` (abstract only).

---

### Semantic Scholar 429 (Rate Limit)

**Symptoms**:
```
Semantic Scholar API error: HTTP Error 429: Too Many Requests
```

**Root cause**: Semantic Scholar's public API has a rate limit of ~100 requests per 5 minutes without an API key.

**Fix**:
```bash
# Option 1: Wait 60 seconds and retry
# Option 2: Use arXiv instead (no rate limit)
# Option 3: Add a Semantic Scholar API key (free, from semanticscholar.org/product/api)
```

**For the live demo**: If Semantic Scholar is rate-limited, just use arXiv results. The score impact is minimal -- arXiv provides the same metadata minus citation counts.

**For students**: Tell them to use arXiv as their primary source and Semantic Scholar sparingly. Or have them get a free API key from https://www.semanticscholar.org/product/api and modify the MCP server to include it in the request headers.

---

### Score Looks Wrong

**Symptoms**: A step that should score higher scores lower than the previous step, or a score seems too low for good-looking output.

**Root cause**: Heuristic scoring (`--quick`) uses regex patterns, not semantic understanding. It can be fooled by formatting changes, process narration text, or unusual output structure.

**Diagnosis**:
```bash
# Run with --verbose to see the raw dimension scores and source grounding factor
python3 benchmark/evaluate.py --input output.md --quick --verbose --question "..."

# Look at:
# - _raw_total: the score before source grounding adjustment
# - _source_factor: the multiplier applied (0.35 to 1.05)
# - Individual dimension scores: which one dropped?
```

**Fix**: Use LLM scoring for the authoritative result:
```bash
# LLM scoring (costs ~$0.02, takes 5-10 seconds)
python3 benchmark/evaluate.py --input output.md --question "..."
```

**For the live demo**: Use `--quick` during individual steps for instant feedback, then show the LLM staircase at the end. Say: "Heuristic scoring is fast but imperfect. The LLM scorer gets the ordering right."

---

### Agent Tool Fails or is Unavailable

**Symptoms**: Claude Code says it doesn't have access to the Agent tool, or tries to do everything in one context window instead of spawning subagents.

**Root cause**: The `Agent` tool is not in the `--allowedTools` list.

**Fix**: Steps 5 and 6 require `Agent` in the allowed tools:
```bash
# WRONG (missing Agent):
--allowed-tools "WebSearch,WebFetch,Read,Write,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar"

# RIGHT (includes Agent):
--allowed-tools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar"
```

Steps 0-4 do NOT use Agent (everything runs in one session). Steps 5-6 MUST have it.

---

### WiFi Goes Down

**Impact by step**:
- Steps 0-2: **Work fully offline.** No tool calls are made. All output comes from training data.
- Step 3+: **Requires internet.** arXiv API, Semantic Scholar API, and WebSearch all need connectivity.

**Immediate actions**:
1. Switch to personal hotspot
2. If hotspot also fails, fall back to pre-computed outputs:
   ```bash
   cat test-run/outputs/step-N.md
   cat test-run/scores/step-N.txt
   ```
3. Say: "Network is down. Let me show you the output and explain the code."

**For students during build phase**: Steps 0-2 work offline. They can iterate on CLAUDE.md and SKILL.md without internet. When connectivity returns, they can add tools.

---

## Student Issues

### "My score is 0"

**Diagnosis checklist**:

1. **Is the output file empty?**
   ```bash
   wc -c output.md
   # If 0 bytes: Claude produced no output. Check for errors.
   cat output.md
   ```

2. **Is the output too short?**
   ```bash
   wc -w output.md
   # If fewer than 100 words: the heuristic scorer returns 0 for reports under 100 words.
   # (See evaluate.py lines 99-104)
   ```

3. **Is the file path wrong?**
   ```bash
   # Are you scoring the right file?
   python3 benchmark/evaluate.py --input output.md --quick --question "..."
   # Make sure output.md exists in the current directory
   ls -la output.md
   ```

4. **Did Claude error out?**
   ```bash
   # Re-run without redirecting stderr
   echo "your question" | claude -p --model sonnet 2>&1 | head -20
   # Check for error messages
   ```

---

### "My score didn't change"

**Diagnosis checklist**:

1. **Are you using the right SKILL.md?**
   ```bash
   # Check which SKILL.md is in your active directory
   cat .claude/skills/deep-research/SKILL.md | head -5
   # The header line tells you which step: "Step 2", "Step 3", etc.
   ```

2. **Did you copy the new SKILL.md?**
   ```bash
   # Example: moving from step 2 to step 3
   cp step-3-tool/.claude/skills/deep-research/SKILL.md .claude/skills/deep-research/
   ```

3. **Are you passing it to Claude correctly?**
   If using `--system-prompt`, make sure you're concatenating CLAUDE.md AND SKILL.md:
   ```bash
   --system-prompt "$(cat CLAUDE.md)
   ---
   $(cat .claude/skills/deep-research/SKILL.md)"
   ```

4. **Did you add the MCP config for step 3+?**
   ```bash
   # Must include --mcp-config and --allowed-tools for tools to work
   --mcp-config test-run/mcp-config.json --allowed-tools "WebSearch,WebFetch,Read,Write,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar"
   ```

5. **Are you scoring a different file than you wrote?**
   ```bash
   # Check the file's modification time
   ls -la output.md
   # If the timestamp is old, you're scoring the previous run's output
   ```

---

### "MCP server not connecting"

**Symptoms**: Claude Code starts but doesn't use the MCP tools, or reports a connection error to the MCP server.

**Diagnosis**:

1. **Check mcp-config.json path is absolute**:
   ```bash
   cat test-run/mcp-config.json
   ```
   The `args` array must contain the ABSOLUTE path to `arxiv_server.py`. Relative paths fail silently.
   
   **WRONG**:
   ```json
   {"args": ["mcp-servers/arxiv_server.py"]}
   ```
   
   **RIGHT**:
   ```json
   {"args": ["/Users/yourname/research-agent-workshop/step-3-tool/mcp-servers/arxiv_server.py"]}
   ```

2. **Test the MCP server manually**:
   ```bash
   python3 /absolute/path/to/arxiv_server.py
   # Should start without errors. Ctrl+C to stop.
   # If it errors: check fastmcp installation
   ```

3. **Check the mcp-config.json is being passed**:
   ```bash
   # Must include --mcp-config flag in the command
   --mcp-config test-run/mcp-config.json
   ```

4. **Check the config file exists at the specified path**:
   ```bash
   ls -la test-run/mcp-config.json
   cat test-run/mcp-config.json
   ```

---

### "Agent tool not available"

**Root cause**: The `Agent` tool is only used in steps 5 and 6. It must be explicitly included in `--allowedTools`.

**Fix**:
```bash
# Steps 0-4: Agent is NOT used. Do not include it.
# Steps 5-6: Agent IS required. Include it:
--allowed-tools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar"
```

**Common mistake**: Trying to use the Agent tool in step 3 or 4. Those steps use iteration within one session (same context window). The Agent tool spawns a separate process.

---

### "How do I run on test problems?"

**Exact commands**:

```bash
# Read the test problem
cat benchmark/test/test-1.md

# Run your agent on test problem 1
echo "What are the most effective approaches to scaling ion trap quantum computing from small-scale demonstration projects to large-scale systems capable of solving real-world problems? For each approach, provide specific technical results from 2024-2026, identify the key engineering challenges that remain, and assess where the research community disagrees on the most promising path forward." | claude -p --model sonnet --output-format text --system-prompt "$(cat CLAUDE.md)
---
$(cat .claude/skills/deep-research/SKILL.md)" --mcp-config test-run/mcp-config.json --allowed-tools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" > test-1-output.md

# Score it
python3 benchmark/evaluate.py --input test-1-output.md --quick --question "What are the most effective approaches to scaling ion trap quantum computing from small-scale demonstration projects to large-scale systems capable of solving real-world problems? For each approach, provide specific technical results from 2024-2026, identify the key engineering challenges that remain, and assess where the research community disagrees on the most promising path forward."
```

```bash
# Test problem 2
echo "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation." | claude -p --model sonnet --output-format text --system-prompt "$(cat CLAUDE.md)
---
$(cat .claude/skills/deep-research/SKILL.md)" --mcp-config test-run/mcp-config.json --allowed-tools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" > test-2-output.md

python3 benchmark/evaluate.py --input test-2-output.md --quick --question "Provide a detailed analysis of the differences and connections between Google's A2A (Agent-to-Agent) protocol and Anthropic's MCP (Model Context Protocol). For each protocol, explain the architecture, intended use cases, and current adoption. Elaborate on what problems A2A solves that MCP does not, and vice versa. Are they complementary or competing? Cite specific implementations and technical documentation."
```

```bash
# Test problem 3
echo "Could therapeutic interventions aimed at modulating plasma metal ion concentrations represent effective preventive or therapeutic strategies against cardiovascular diseases? What types of interventions have been proposed, and is there clinical evidence supporting their feasibility and efficacy? Provide specific trial results, mechanisms of action, and identify where the clinical evidence is conflicting or insufficient." | claude -p --model sonnet --output-format text --system-prompt "$(cat CLAUDE.md)
---
$(cat .claude/skills/deep-research/SKILL.md)" --mcp-config test-run/mcp-config.json --allowed-tools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar" > test-3-output.md

python3 benchmark/evaluate.py --input test-3-output.md --quick --question "Could therapeutic interventions aimed at modulating plasma metal ion concentrations represent effective preventive or therapeutic strategies against cardiovascular diseases? What types of interventions have been proposed, and is there clinical evidence supporting their feasibility and efficacy? Provide specific trial results, mechanisms of action, and identify where the clinical evidence is conflicting or insufficient."
```

**Competition score** = average of all 3 test scores.

---

## Scoring Issues

### Heuristic Score Seems Too Low

**Root cause**: The heuristic scorer applies a **source grounding factor** that penalizes reports without real external URLs. This is the single biggest source of "why is my score so low?"

**How the factor works** (from `evaluate.py` lines 254-278):

| Condition | Factor | Effect |
|-----------|--------|--------|
| `urls < 5 AND evidence_quality < 3` | 0.35 + small bonus | Cuts raw score by ~65%. Training data only. |
| `urls >= 5 BUT urls < 10` | 0.55 | Cuts raw score by ~45% |
| `urls >= 10, no verification` | 0.70 + small bonus | Cuts raw score by ~30% |
| `verification_markers >= 3 AND urls >= 10` | 1.0 | No penalty. Verified output. |
| `evidence_quality >= 3` | 1.0 + small bonus | Slight boost. Team/critic output. |

**Diagnosis**:
```bash
python3 benchmark/evaluate.py --input output.md --quick --verbose --question "..."
# Check the _source_factor in the output
# If it's 0.35: your output has no real URLs
# If it's 0.70: you have URLs but no verification markers
# If it's 1.0: you have verified output
```

**Fix**: To increase the source grounding factor:
- Add tools (step 3+) to get real URLs: factor goes from ~0.35 to ~0.70
- Add verification (step 5+) to add verification markers: factor goes from ~0.70 to 1.0
- Add evidence quality ratings (step 6 critic output): factor goes above 1.0

---

### Step 4 Scores Lower Than Step 3 (Heuristic)

**This is expected and documented.**

**Pre-computed scores**:
- Step 3: 57.7/100 (insight=3)
- Step 4: 52.5/100 (insight=1)

**Root cause**: The iterative skill's self-evaluation text ("evaluating coverage... gap identified... searching again...") replaces analytical phrases that the heuristic looks for. The insight dimension counts regex matches for words like `because`, `therefore`, `suggests`, `implies`, `trade-off`, `compared to`. Step 4's process narration has fewer of these.

**The LLM scorer ranks them correctly**:
- Step 3 LLM: ~55/100
- Step 4 LLM: ~72/100

**What to tell students**: "The heuristic is a fast proxy. It's wrong here. Use `--quick` for iteration speed, but trust the LLM scorer for final rankings."

---

### LLM Scoring Fails

**Symptoms**:
```
Warning: ANTHROPIC_API_KEY not set. Using heuristic scoring.
```

Or:
```
Warning: Could not parse LLM response. Falling back to heuristics.
```

**Fixes**:

1. **API key not set**:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

2. **API key invalid or expired**:
   ```bash
   # Test the key directly
   python3 -c "
   import anthropic
   c = anthropic.Anthropic()
   r = c.messages.create(model='claude-sonnet-4-6', max_tokens=10, messages=[{'role':'user','content':'hi'}])
   print(r.content[0].text)
   "
   ```

3. **LLM response unparseable**: The evaluator expects JSON in a specific format. If the LLM returns malformed JSON, it falls back to heuristics. Re-running usually fixes this.

4. **Fallback**: Use `--quick` for heuristic scoring. It's always available, instant, and free.

---

### Score Varies Between Runs

**This is expected.** Two sources of variance:

1. **Claude's output varies**: Same prompt, different output. Different output, different score. This is inherent to LLMs with temperature > 0.
2. **LLM scoring varies**: The LLM judge also has variance. A report might score 72 on one run and 68 on the next.

**Mitigation**:
- Use `--quick` for consistent heuristic scores (deterministic regex matching on the same output)
- For the competition: score each test problem once with `--quick`, take the score as-is
- For the staircase demo: use pre-computed scores from `test-run/scores/`

---

## Common Mistakes

### Mixing CLAUDE.md (Identity) with SKILL.md (Methodology)

**The boundary**:
- **CLAUDE.md** = WHO. The researcher's field, preferred sources, citation format, constraints. Static identity. Does not change between research tasks.
- **SKILL.md** = HOW. The research methodology. Decompose, search, extract, cross-reference, synthesize. Changes as you add iteration, tools, verification.

**Wrong** (putting methodology in CLAUDE.md):
```markdown
# CLAUDE.md
You are a research assistant.
When asked to research, decompose into sub-questions...
Search arXiv first...
Write the report with this structure...
```

**Right** (keeping them separate):
```markdown
# CLAUDE.md
You are assisting a researcher in computer science and AI.
Primary fields: ML, deep learning, AI systems.
Citation format: Author (Year).

# SKILL.md
## Research Methodology
### Step 1: Decompose
### Step 2: Search
...
```

**Why it matters**: CLAUDE.md persists across all tasks. SKILL.md is specific to one type of task. If you put methodology in CLAUDE.md, every interaction (even simple questions) gets the full research process.

---

### Forgetting to Update allowed-tools When Adding MCP Server

**Symptom**: You added the MCP server config but Claude never calls `search_arxiv` or `search_semantic_scholar`.

**Root cause**: The `--allowedTools` (CLI) or `allowed-tools` (SKILL.md frontmatter) list does not include the MCP tool names.

**Fix**: When adding the MCP server, you must update BOTH the config and the tool list:

```bash
# 1. MCP config (tells Claude Code how to start the server)
--mcp-config test-run/mcp-config.json

# 2. Allowed tools (tells Claude it's permitted to use these tools)
--allowed-tools "WebSearch,WebFetch,Read,Write,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar"
```

The tool names follow the pattern `mcp__<server-name>__<tool-function-name>`. For the workshop's MCP server named "research-tools" with functions `search_arxiv` and `search_semantic_scholar`, the tool names are:
- `mcp__research-tools__search_arxiv`
- `mcp__research-tools__search_semantic_scholar`

---

### Running Step 5/6 Without Agent in Allowed Tools

**Symptom**: Claude does all the research in one session instead of spawning verification or specialist agents.

**Root cause**: `Agent` is not in `--allowedTools`. Without it, Claude cannot spawn subprocesses.

**Fix**:
```bash
# Add Agent to the allowed tools list
--allowed-tools "WebSearch,WebFetch,Read,Write,Agent,mcp__research-tools__search_arxiv,mcp__research-tools__search_semantic_scholar"
```

**Why it's easy to miss**: Steps 0-4 work without `Agent`. When students copy the step 3 command and modify the SKILL.md for step 5, they forget to add `Agent` to the tool list.

---

### Using Relative Paths in mcp-config.json

**Symptom**: MCP server fails to start, or Claude Code cannot find the server script.

**Root cause**: `mcp-config.json` requires absolute paths. Relative paths are resolved from Claude Code's working directory, which may not be the workshop directory.

**Wrong**:
```json
{
    "mcpServers": {
        "research-tools": {
            "command": "python3",
            "args": ["mcp-servers/arxiv_server.py"]
        }
    }
}
```

**Right**:
```json
{
    "mcpServers": {
        "research-tools": {
            "command": "python3",
            "args": ["/Users/yourname/research-agent-workshop/step-3-tool/mcp-servers/arxiv_server.py"]
        }
    }
}
```

**Quick fix**:
```bash
# Generate the correct path
echo "$(pwd)/step-3-tool/mcp-servers/arxiv_server.py"
# Copy this absolute path into your mcp-config.json
```

The `test-run/run_steps.sh` script auto-generates the correct absolute path via the `setup_mcp()` function (line 52-62).

---

### Not Saving Output to a File

**Symptom**: Claude runs successfully but there's no file to score.

**Root cause**: Claude Code prints to stdout in pipe mode (`-p`). Without redirecting to a file, the output is lost.

**Fix**: Always redirect to a file:
```bash
# With file redirect
echo "your question" | claude -p --model sonnet ... > output.md

# Then score
python3 benchmark/evaluate.py --input output.md --quick --question "..."
```

**Alternative**: Use the `Write` tool in the SKILL.md to have Claude save the output itself:
```markdown
### Final Step
Save your report to `output.md` using the Write tool.
```

---

### Running Steps Out of Order During Competition

**Symptom**: Student jumps to step 6 without understanding steps 1-3. Their agent doesn't work because foundational pieces are missing.

**What to tell them**:
> "Each step builds on the previous one. Start with step 1 (copy CLAUDE.md), add step 2 (copy SKILL.md), then step 3 (add MCP server). Get each one working before moving to the next. You can't build a team (step 6) if you don't have a working searcher (step 3)."

**Quick recovery path**:
```bash
# Reset to a known good state -- copy all step 6 files at once
cp step-1-context/CLAUDE.md ./CLAUDE.md
mkdir -p .claude/skills/{orchestrator,searcher,critic,synthesizer}
cp step-6-team/.claude/skills/orchestrator/SKILL.md .claude/skills/orchestrator/
cp step-6-team/.claude/skills/searcher/SKILL.md .claude/skills/searcher/
cp step-6-team/.claude/skills/critic/SKILL.md .claude/skills/critic/
cp step-6-team/.claude/skills/synthesizer/SKILL.md .claude/skills/synthesizer/
cp -r step-3-tool/mcp-servers ./mcp-servers
```

---

## Reference: Exact Error Messages and Their Meaning

| Error Message | Source | Meaning | Fix |
|--------------|--------|---------|-----|
| `command not found: claude` | Shell | CLI not installed | `npm install -g @anthropic-ai/claude-code` |
| `ANTHROPIC_API_KEY not set` | verify.sh | Env var missing | `export ANTHROPIC_API_KEY="..."` |
| `ModuleNotFoundError: No module named 'fastmcp'` | Python | Package missing | `pip install fastmcp` |
| `ModuleNotFoundError: No module named 'anthropic'` | Python | Package missing | `pip install anthropic` |
| `HTTP Error 429: Too Many Requests` | Semantic Scholar | Rate limited | Wait 60s or use arXiv instead |
| `No papers found for query:` | MCP server | arXiv returned 0 results | Broaden query terms |
| `Semantic Scholar API error:` | MCP server | API error | Check network, try arXiv |
| `Error: output.md not found` | evaluate.py | File path wrong | Check file exists: `ls output.md` |
| `too short (N words)` | evaluate.py | Report under 100 words | Claude produced minimal output; re-run |
| `Warning: Could not parse LLM response` | evaluate.py | Judge returned bad JSON | Re-run, or use `--quick` |
| `TOTAL SCORE: 0.0/100` | evaluate.py | Empty or too-short output | Check output file content |
| `EMPTY OUTPUT` | run_steps.sh | Claude produced nothing | Check API key, network |
