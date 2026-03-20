# LangSmith CLI Reference

## Installation

```bash
curl -fsSL https://cli.langsmith.com/install.sh | sh
# Or: go install github.com/langchain-ai/langsmith-cli/cmd/langsmith@latest
```

## Authentication

Environment variables (recommended):
- `LANGSMITH_API_KEY` — your API key
- `LANGSMITH_ENDPOINT` — API endpoint (optional, defaults to hosted)
- `LANGSMITH_PROJECT` — default project name

CLI flag overrides: `--api-key`, `--endpoint`, `--project`

## Command Reference

### Projects

```bash
langsmith project list [--limit N] [--name-contains text]
```

### Traces

```bash
# List traces
langsmith trace list --project <name> [filters]

# Get single trace
langsmith trace get <trace-id> [--full] [--show-hierarchy] [--format pretty]

# Export traces to directory
langsmith trace export <path> --project <name> [filters]
```

### Runs

```bash
# List runs (filter by type: llm, tool, etc.)
langsmith run list --project <name> [--run-type llm|tool] [filters]

# Get single run
langsmith run get <run-id> [--full]

# Export runs to directory
langsmith run export <path> --project <name> [filters]
```

### Threads

```bash
# List threads
langsmith thread list --project <name> [--last-n-minutes N]

# Get single thread
langsmith thread get <thread-id> --project <name> [--full]
```

### Datasets

```bash
langsmith dataset list
langsmith dataset get <dataset-id>
langsmith dataset create --name <name>
langsmith dataset delete <dataset-id>
langsmith dataset export <path>
langsmith dataset upload <path>
```

### Evaluators & Experiments

```bash
langsmith evaluator list | upload | delete
langsmith experiment list | get
```

## Common Filter Flags

| Flag | Description |
|------|-------------|
| `--project` | Target project |
| `--limit, -n` | Max results |
| `--last-n-minutes` | Time window (minutes) |
| `--since` | After ISO timestamp |
| `--error / --no-error` | Error status filter |
| `--name` | Name search (case-insensitive) |
| `--run-type` | Filter by type (`llm`, `tool`, etc.) |
| `--min-latency` / `--max-latency` | Latency filter (seconds) |
| `--min-tokens` | Minimum total tokens |
| `--tags` | Comma-separated tag filter (OR logic) |
| `--filter` | Raw LangSmith filter DSL |
| `--trace-ids` | Specific trace IDs |

## Detail Flags

| Flag | Description |
|------|-------------|
| `--include-metadata` | Status, duration, tokens, costs |
| `--include-io` | Inputs, outputs, error details |
| `--include-feedback` | Feedback statistics |
| `--full` | All fields |
| `--show-hierarchy` | Trace tree structure |

## Output Options

- Default: JSON to stdout
- `--format pretty` — human-readable tables/trees
- `-o filename` — write to file

## Quick Patterns

### Error hunting
```bash
langsmith trace list --project <name> --error --last-n-minutes 30 --limit 50 --format pretty
```

### Performance check
```bash
langsmith run list --project <name> --run-type llm --last-n-minutes 60 --include-metadata --min-latency 5
```

### Before/after comparison
```bash
langsmith trace export ./before --project <name> --since "2026-01-17T10:00:00Z" --limit 30
# Make changes
langsmith trace export ./after --project <name> --since "2026-01-17T14:00:00Z" --limit 30
```

### Session export
```bash
SESSION="langsmith-debug/session-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$SESSION"
langsmith trace export "$SESSION/traces" --project <name> --last-n-minutes 60 --limit 50 --full
langsmith thread list --project <name> --last-n-minutes 60 -o "$SESSION/threads.json"
```
