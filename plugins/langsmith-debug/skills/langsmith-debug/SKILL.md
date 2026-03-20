---
name: langsmith-debug
description: "Use when debugging LangChain agents using LangSmith traces. Trigger when user mentions debugging agents, reports agent behavior issues, asks about traces/runs/threads, wants to analyze agent performance, encounters LangChain errors, or asks to check LangSmith or investigate agent failures."
---

# LangSmith Debugging Skill

Debug LangChain agents by fetching and analyzing LangSmith traces.

## Prerequisites

1. Install the CLI:
```bash
curl -fsSL https://cli.langsmith.com/install.sh | sh
```

2. Verify `LANGSMITH_API_KEY` is set:
```bash
echo $LANGSMITH_API_KEY
```
If not set, check `.env` files or ask the user. See `references/troubleshooting.md` for setup help.

3. Set `LANGSMITH_PROJECT` based on context. Discover available projects with `langsmith project list`. Infer project from request context (e.g., "staging is broken" → staging project). If ambiguous, ask.

## Operation Modes

**Quick Inspect** — CLI-only, no scripts, no file I/O. For viewing traces and answering simple questions.

**Deep Analysis** — CLI export + script analysis + agent reasoning. For debugging, root cause analysis, and recommendations.

**Decision rule:**
- Specific trace + simple question → Quick Inspect
- Multiple traces / "debug" / "why" / "analyze" / performance → Deep Analysis
- When in doubt, start Quick Inspect; escalate if complexity emerges

## Quick Inspect Workflow

All commands use `--project <proj>` where `<proj>` is the active project.

**Recent activity:**
```bash
langsmith trace list --last-n-minutes 5 --limit 5 --format pretty --project <proj>
```

**Specific trace:**
```bash
langsmith trace get <id> --full --format pretty
```

**Check errors:**
```bash
langsmith trace list --error --last-n-minutes 30 --project <proj>
```

**Slow traces:**
```bash
langsmith trace list --min-latency 10 --last-n-minutes 60 --project <proj>
```

**Trace tree:**
```bash
langsmith trace get <id> --show-hierarchy --format pretty
```

**List threads:**
```bash
langsmith thread list --project <proj> --limit 10 --format pretty
```

**Specific thread:**
```bash
langsmith thread get <id> --project <proj> --full
```

**Discover projects:**
```bash
langsmith project list
```

Report concisely: count, success/failure ratio, errors, tools used, brief summary.

## Deep Analysis Workflow

### 1. Determine what to fetch

Specific trace ID, time window, or default to last hour.

### 2. Set up trace directory

```bash
mkdir -p ./.claude/langsmith_traces
```

This directory is gitignored — never commit trace files.

### 3. Export traces

General (last hour):
```bash
langsmith trace export ./.claude/langsmith_traces/traces.jsonl --project <proj> --last-n-minutes 60 --full
```

Specific trace:
```bash
langsmith trace get <id> --full -o ./.claude/langsmith_traces/<id>.json
```

Time window:
```bash
langsmith trace export ./.claude/langsmith_traces/traces.jsonl --project <proj> --since "2026-01-17T10:00:00Z" --full
```

Errors only — add `--error` to any export command.

### 4. Run analysis script

The analysis script is bundled with this skill. Find its path relative to this skill's installation directory.

Choose subcommand based on the problem:

**General summary:**
```bash
python3 <skill-dir>/scripts/analyze_traces.py summary ./.claude/langsmith_traces
```

**Compare success vs failure:**
```bash
python3 <skill-dir>/scripts/analyze_traces.py compare ./.claude/langsmith_traces
```

**Error investigation:**
```bash
python3 <skill-dir>/scripts/analyze_traces.py errors ./.claude/langsmith_traces --group-by type
```

Where `<skill-dir>` is the directory containing this SKILL.md file. To find it, use `dirname` on this skill's path or locate it via the plugin's installed skills directory.

### 5. Apply reasoning

Consult `references/common_patterns.md` to match script findings to known solutions. Generate actionable recommendations based on the data and reference patterns.

### 6. Present findings

Report concisely. Offer follow-up: implement fix, fetch fresh traces after changes, or investigate deeper.

## Script Reference

```
python3 <skill-dir>/scripts/analyze_traces.py summary <input> [--json] [--verbose]
python3 <skill-dir>/scripts/analyze_traces.py compare <input> [<input2>] [--json] [--verbose]
python3 <skill-dir>/scripts/analyze_traces.py errors <input> [--group-by type|time|trace] [--json] [--verbose]
```

Input: JSONL file, JSON file, or directory. Run `--help` for full options.

## Reference Files

All paths relative to this skill's directory:

| File | When to consult |
|------|-----------------|
| `references/cli_reference.md` | Full CLI command and flag reference |
| `references/common_patterns.md` | Known error patterns and solutions (after running script) |
| `references/analysis_guide.md` | Systematic trace analysis methodology |
| `references/troubleshooting.md` | Setup and configuration issues |
| `references/use_cases.md` | Common debugging scenarios |
