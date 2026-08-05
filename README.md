# th-plugins

Claude Code plugins by Tyler Ho.

## Installation

```bash
claude plugin add --marketplace https://github.com/tylerho5/claude-plugins <plugin-name>
```

## Plugins

### langsmith-debug

Debug and analyze LangChain agents using LangSmith traces. Two operation modes: **Quick Inspect** for CLI-only trace viewing, and **Deep Analysis** for exporting traces and running a bundled Python analysis script with summary, comparison, and error investigation subcommands.

**Requirements:**

- [LangSmith CLI](https://github.com/langchain-ai/langsmith-cli) installed and on PATH
- `LANGSMITH_API_KEY` environment variable set

---

### datamining-claude-code-binary

Inspect and reverse-engineer the Claude Code native binary. Locates the compiled executable across install methods (native installer, npm, Homebrew), then carves byte windows to extract embedded system prompts, tool definitions, `tengu_*` feature-flag gates, and telemetry event names.

## Deprecated

These plugins are no longer maintained and have been moved to `deprecated-plugins/`. They stay in the repository for reference but are not part of the marketplace catalog:

- **specflow** — Spec-driven development workflow (scout, research, plan, execute).
- **external-agent-orchestration** — Orchestrate external CLI coding agents (Qwen Code, Gemini CLI, OpenCode CLI).
- **adversarial-code-review** — Two-agent adversarial code review with a Sonnet critiquer.

## License

MIT
