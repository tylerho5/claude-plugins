# Analysis Guide

## Trace Structure

Traces are exported as JSONL files. Each line is a run, grouped by `trace_id`. Run hierarchy is expressed via `parent_run_id` (null for root runs).

```
Thread (Conversation)
└── Trace (Single turn, identified by trace_id)
    └── Runs (Operations: llm, tool, chain, agent — linked by parent_run_id)
```

Key run fields: id, trace_id, parent_run_id, name, run_type, inputs, outputs, error, start_time, end_time, total_tokens, feedback

## Analysis Philosophy

The analysis scripts surface data and findings. The agent reasons about root causes and generates recommendations using `common_patterns.md` as a reference. Scripts do the counting; the agent does the thinking.

## 6-Step Analysis Method

1. Quick Overview
   - Export traces: `langsmith trace export ./.claude/langsmith_traces/traces.jsonl --project <proj> --last-n-minutes 60 --full`
   - Run: `python3 <skill-dir>/scripts/analyze_traces.py summary ./.claude/langsmith_traces/traces.jsonl`
   - Check: error rate, avg duration/tokens, patterns

2. Error Investigation
   - Run: `python3 <skill-dir>/scripts/analyze_traces.py errors ./.claude/langsmith_traces/traces.jsonl --group-by type`
   - Answer: most common error, clustering (time/trace), failing step, input correlation

3. Pattern Analysis
   - Run: `python3 <skill-dir>/scripts/analyze_traces.py compare ./.claude/langsmith_traces/traces.jsonl`
   - Compare: execution paths, performance, tool usage, divergence points

4. Performance Check
   - Duration thresholds: <5s excellent, 5-15s good, 15-30s acceptable, >30s investigate
   - Token usage: compare to expected, check for verbosity/repetition
   - Cost: per-trace cost × usage volume

5. Behavior Validation
   - Tool usage: right tools, correct order, appropriate inputs
   - Execution flow: expected paths, unnecessary steps, loops
   - Output quality: matches expectations, correct format, relevant

6. Feedback Correlation
   - Correlate: low scores with errors, high scores with patterns, comments with issues

## Deep Dive Techniques

Compare specific traces: `python3 <skill-dir>/scripts/analyze_traces.py compare trace1.json trace2.json`
Useful for: understanding success/failure differences, finding divergence points, debugging non-determinism

List recent traces (quick view): `langsmith trace list --format pretty --project <proj> --last-n-minutes 60`
Get a single trace: `langsmith trace get <trace_id>`

Timeline analysis:
- Extract run sequence, note timestamps/durations
- Identify bottlenecks (unusually long steps)
- Check parallelizable operations

Input/Output analysis:
- Examine inputs to failed runs (malformed, edge cases, missing fields)
- Check previous run outputs (bad data, error propagation, formatting)
- Trace data flow (transformations, incorrect data origin)

## Common Scenarios

Intermittent Failures:
- Export successful + failed traces, compare
- Check: input differences, execution paths, timing, external factors (API, rate limits)

Performance Degradation:
- Export from different time periods, compare
- Check: growing history (memory), increased tool calls, longer LLM times, network issues

Unexpected Behavior:
- Export problematic trace, examine step-by-step
- Compare to successful trace, identify divergence

High Error Rate:
- Run: `python3 <skill-dir>/scripts/analyze_traces.py errors <dir> --group-by type`
- Check common_patterns.md for solutions
- Examine traces before errors started
- Look for external changes (code, API, config, data)

## Best Practices

Export right data:
- Debugging: `langsmith trace export ./.claude/langsmith_traces/traces.jsonl --project <proj> --last-n-minutes 60 --full`
- Performance: `langsmith trace export ./.claude/langsmith_traces/traces.jsonl --project <proj> --last-n-minutes 120 --full`
- Quick listing: `langsmith trace list --format pretty --project <proj> --last-n-minutes 60`

Workflow:
1. Start broad (`analyze_traces.py summary`)
2. Narrow down (focus on issues)
3. Compare (`analyze_traces.py compare`)
4. Deep dive (individual traces via `langsmith trace get <id>`)
5. Document findings
6. Validate fixes (export new traces)

Statistical significance: >30 traces ideal, look for patterns not outliers, consider variance

Root cause process:
1. Observe problem
2. Gather traces
3. Identify patterns
4. Form hypothesis
5. Test hypothesis
6. Implement fix
7. Validate
