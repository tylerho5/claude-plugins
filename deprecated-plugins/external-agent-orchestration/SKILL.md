---
name: external-agent-orchestration
description: For tasks involving external CLI coding agents (Claude Code, Qwen Code, Gemini CLI, OpenCode CLI). Load when user mentions these agents by name, requests "subagents", "parallel search", "multiple perspectives", or to take advantage of multiple LLM services usage quotas to reduce pressure on Claude Pro session/weekly limits. Effectively extends Claude Code's capabilities by distributing work across multiple services for "free" token usage within a Claude Code session.

---

# External Agent Orchestration

Orchestrate external CLI coding agents to leverage other LLM services usage quotas to reduce the pressure on Claude Pro session/weekly limits. This allows for "free" token usage within a Claude Code session by offloading work to other coding agents.

Key benefits: Quota distribution, parallel execution, diverse perspectives, graceful fallback.

## Agent Types

Two permission modes create distinct agent types. Configured via CLI flags (Qwen, Claude GLM) or config files (Gemini, OpenCode).

Research Agents: Explore code + search web, limited commands and cannot modify files. Block sensitive files (.env, .ssh, credentials, tokens).
Implement Agents: Edit/write code, limited commands and cannot access web or git.

## Agents

### Claude Code (GLM)
Hacked Claude Code harness using Z.ai's API | Model: `glm-4.7`

Best for: Lightweight coding tasks, tasks where Claude Code workflow is valuable, generous usage quota
Limitations: Powered by model less powerful than frontier models

Invocations:
- Research: `claude-glm --permission-mode plan --allowedTools "Read,Grep,Glob,WebSearch,WebFetch,Bash(curl:*),Bash(wget:*)" --disallowedTools "Edit,Write,Bash(git:*),Bash(rm:*),Bash(sudo:*),Bash(pip install:*),Bash(npm install:*)" -p "[prompt]"`
- Implement: `claude-glm --allowedTools "Read,Edit,Write,Grep,Glob,Bash(npm test:*),Bash(npm run:*)" --disallowedTools "Bash(git:*),Bash(rm:*),Bash(sudo:*),Bash(pip install:*),Bash(npm install:*)" -p "[prompt]"`

### Qwen Code
Alibaba's coding agent via CLI harness Model: `qwen3-coder-plus`

Best for: High-volume experimentation, code generation, standard coding problems
Limitations: Struggles with complex architectural decisions, weaker instruction-following

Invocations:
- Research: `qwen --approval-mode plan --web-search-default tavily --exclude-tools "edit_file" --exclude-tools "write_file" --exclude-tools "run_shell_command(git *)" --exclude-tools "run_shell_command(rm *)" --exclude-tools "run_shell_command(sudo *)" --exclude-tools "run_shell_command(pip install*)" --exclude-tools "run_shell_command(npm install*)" -p "[prompt]"`
- Implement: `qwen --approval-mode auto-edit --exclude-tools "run_shell_command(git *)" --exclude-tools "run_shell_command(rm *)" --exclude-tools "run_shell_command(sudo *)" --exclude-tools "run_shell_command(pip install*)" --exclude-tools "run_shell_command(npm install*)" -p "[prompt]"`

### Gemini CLI
Google's coding agent via CLI harness | Model: `gemini-3-flash-preview`

Best for: General-purpose coding tasks, fast execution with excellent performance

Invocations:
- Research: `GEMINI_CONFIG=<skill-dir>/configs/gemini-research.json gemini -p "[prompt]"`
- Implement: `GEMINI_CONFIG=<skill-dir>/configs/gemini-implement.json gemini -p "[prompt]"`

### OpenCode CLI
Open source coding agent harness | Model: `opencode/glm-4.7-free`

Best for: General purpose coding tasks, code exploration and analysis

Invocations:
- Research: `OPENCODE_CONFIG=<skill-dir>/configs/opencode-research.json opencode run "[prompt]"`
- Implement: `OPENCODE_CONFIG=<skill-dir>/configs/opencode-implement.json opencode run "[prompt]"`

(Notice OpenCode uses `run [prompt]` instead of `-p [prompt]`)

---

## Prompt Passing

Never use heredocs with command substitution - causes infinite hang:
```bash
# BROKEN: agent -p "$(cat <<'EOF' ... EOF)"
```

Simple prompts (< 200 chars, no code): Multi-line strings with `-p` flag
```bash
qwen --approval-mode plan -p "Search for error handling patterns

Focus on try/catch blocks and logging"
```

Complex prompts (code, special chars, long text): Stdin redirection, no `-p` flag
```bash
PROMPT_FILE=$(mktemp)
cat > "$PROMPT_FILE" << 'EOF'
Refactor CardEmbeddingModel (embedding.py lines 10-50):
- Add type hints: embedding_dim: int
- Use: embeddings * (1 + 0.1 * normalized_levels)
EOF

qwen --approval-mode auto-edit --exclude-tools "run_shell_command(git *)" < "$PROMPT_FILE"
rm "$PROMPT_FILE"
```

---

## Usage

Always use `run_in_background=true` in Bash tool. Use TaskOutput to retrieve results.

Check availability: `<skill-dir>/scripts/check-agent-availability.sh` returns JSON array of available agents.

Single agent: One agent handles the task. Choose based on task type and agent strengths.

Parallel execution: Multiple Bash tool calls in a single message. Use for diverse perspectives on same task or higher throughput on different tasks.

Timeouts:
- Exploration/Research: `timeout=120000` (2min)
- Implementation: `timeout=180000` (3min)
- Complex analysis: `timeout=300000` (5min)

Start with shorter timeouts to fail fast. If agent times out, proceed with other agents' outputs.

---

## Prompt Tips

Exploration: Be specific, include output format.
```
Search for neural network encoders. Focus on attention mechanisms.
Return: - <file-path>:<line-range> - Brief description
```

Web research: Use specific identifiers (repo names, URLs).
```
Research sst/opencode GitHub repo architecture. Return URLs and summaries.
```

Implementation: Keep scoped, reference file locations.
```
Fix level scaling in embedding.py:6-29. Use normalized scaling: (x - mean) / std
```

Single-file changes work best. "Remove X from Y" outperforms "Implement algorithm Z".

---

## Result Handling & Fallback

1. Merge outputs from all agents, deduplicate file paths/URLs/findings
2. If agents fail/timeout: use built-in tools (Explore, Plan, WebSearch)
3. Notify user: "Used N/M agents (timeouts: X, Y)"

---

## Additional Context

For most tasks, SKILL.md provides sufficient guidance.

Load reference files only for advanced scenarios:

[reference/advanced-strategies.md](reference/advanced-strategies.md): Multi-agent consensus, voting strategies, quality filtering, agent count guidelines.

[reference/fallback.md](reference/fallback.md): Detailed fallback mapping, partial failure handling, timeout recovery.