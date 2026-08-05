---
name: rnp
description: Use when starting a new task that needs both codebase exploration and web research before creating a plan
disable-model-invocation: true
argument-hint: "<task-description> [documentation-urls]"
---

# Research and Plan

## Input

TASK: $1
DOCUMENTATION_URLS: $2 (optional)

## Pipeline

Run Stage 1 and Stage 2 in parallel (they are independent), then run Stage 3 after both complete.

### Stage 1 + Stage 2 (parallel)

Invoke both skills simultaneously:

```
Skill("specflow:scout", args: "$1")
Skill("specflow:research", args: "$1 $2")
```

Each skill writes a report and returns its file path:
- Scout → `.claude/scout_files/<slug>-scout.md`
- Research → `.claude/doc_search/<slug>-research.md`

Store both returned paths — they are required inputs for Stage 3.

### Stage 3: Plan

After both Stage 1 and Stage 2 complete, invoke plan with the task description and both report paths:

```
Skill("specflow:plan", args: "$1 <scout-report-path> <research-report-path>")
```

This produces a task plan at `.claude/tasks/pending/TASK-XX-<description>.md`.

## Handling Failures

- If scout returns no relevant files, proceed with plan — note that no existing code was found.
- If research returns no findings, proceed with plan using only scout context.
- If both fail, create the plan from the task description alone and note the limited context.

## Return

After all stages complete, report:
1. Scout report path and key findings
2. Research report path and key findings
3. Task plan path and summary
