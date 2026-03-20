# Common Use Cases

## Quick Health Check

Before committing code:
```bash
langsmith trace list --last-n-minutes 10 --limit 5 --format pretty
```

Look for:
- New errors introduced
- Performance regressions
- Unexpected tool calls

If issues found, switch to Deep Analysis mode.

## Wrong Tool Called

Quick inspect:
```bash
langsmith trace get <trace-id> --full
```

Review:
1. Available tools at execution time
2. Agent's reasoning for tool selection
3. Tool descriptions/instructions
4. User prompt

Deep analysis if pattern:
```bash
langsmith trace export ./.claude/langsmith_traces/traces.jsonl --project <project-name> --last-n-minutes 60 --limit 30
python3 <skill-dir>/scripts/analyze_traces.py summary ./.claude/langsmith_traces
```

Look for tool usage patterns.

## Memory Not Working

Quick check:
```bash
langsmith run list --name memory --last-n-minutes 30 --limit 20
```

Verify:
- Memory tools called?
- Recall returned results?
- Memories stored successfully?
- Retrieved memories used?

Deep analysis:
```bash
langsmith trace export ./.claude/langsmith_traces/traces.jsonl --project <project-name> --last-n-minutes 60 --limit 50 --full
python3 <skill-dir>/scripts/analyze_traces.py summary ./.claude/langsmith_traces
```

Check memory tool success rates.

## Performance Bottleneck

Quick check:
```bash
langsmith trace list --last-n-minutes 30 --limit 10 --min-latency 5 --format pretty
```

Look for duration outliers.

Deep analysis:
```bash
langsmith trace export ./.claude/langsmith_traces/traces.jsonl --project <project-name> --last-n-minutes 60 --limit 50 --min-latency 5
python3 <skill-dir>/scripts/analyze_traces.py summary ./.claude/langsmith_traces
```

Analyze:
- Execution time per trace
- Tool call latencies
- Token usage (context size)
- Iteration counts
- Slowest operations

## Before/After Validation

```bash
# Before changes
langsmith trace export ./traces_before/traces.jsonl --project <project-name> --last-n-minutes 60 --limit 30 --full

# Make code changes and test

# After changes
langsmith trace export ./traces_after/traces.jsonl --project <project-name> --last-n-minutes 60 --limit 30 --full

# Compare
python3 <skill-dir>/scripts/analyze_traces.py compare ./traces_before/traces.jsonl ./traces_after/traces.jsonl
```

## Continuous Monitoring

Daily analysis:
```bash
langsmith trace export ./traces_$(date +%Y%m%d)/traces.jsonl --project <project-name> --last-n-minutes 1440 --full
python3 <skill-dir>/scripts/analyze_traces.py summary ./traces_$(date +%Y%m%d)
```

## Trace-Driven Testing

Baseline comparison:
```bash
# Save known good trace
langsmith trace get <good-trace-id> -o ./test_fixtures/good_trace.json

# After changes, compare
langsmith trace get <new-trace-id> -o ./test_fixtures/new_trace.json
python3 <skill-dir>/scripts/analyze_traces.py compare ./test_fixtures/good_trace.json ./test_fixtures/new_trace.json
```
