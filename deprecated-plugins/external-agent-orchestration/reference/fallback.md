# Fallback Patterns

Load this file when agents fail or timeout and you need fallback strategies.

## Trigger Conditions
- `check-agent-availability.sh` returns `[]`
- All agents timeout
- All outputs malformed

## Fallback Mapping

| Task Type | Built-in Fallback |
|-----------|-------------------|
| Codebase exploration | `Task(subagent_type="Explore")` |
| Web research | `WebSearch()` or `WebFetch()` |
| Architecture | `Task(subagent_type="Plan")` |
| Code review | Grep + Read |

## Partial Failures

If some agents succeed: proceed with successful outputs, don't fall back.

Notify: "Used 2/4 agents (timeouts: gemini, opencode)"

---

## Worked Example: Handling Failures

Scenario: 2/4 agents timeout

```
claude-glm: Success (5 files)
qwen: Success (3 files)
gemini: Timeout
opencode: Timeout
```

Action: Proceed with 8 files from 2 agents.

Notify: "Used 2/4 agents (timeouts: gemini, opencode)"