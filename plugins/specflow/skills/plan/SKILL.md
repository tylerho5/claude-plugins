---
name: plan
description: Use when creating a structured task plan or specification from requirements, with optional codebase and research context
disable-model-invocation: true
argument-hint: "[task-description] [optional: scout-report-path] [optional: research-report-path]"
---

# Plan

Create a structured task specification from a prompt, optionally incorporating scout and research context.

## Input

TASK: $1
SCOUT_REPORT: $2
RESEARCH_REPORT: $3

## Workflow

### 1. Gather Context

- If SCOUT_REPORT path is provided, read it for codebase context
- If RESEARCH_REPORT path is provided, read it for documentation context
- If neither is provided, do a quick codebase scan yourself (Glob + Grep) to understand the relevant area

### 2. Infer Task Type

Determine the type from the prompt. If ambiguous, state your assumption.

| Type | Signals |
|------|---------|
| **Bug** | "fix", "broken", "error", "regression", "not working" |
| **Feature** | "add", "create", "new", "implement", "build" |
| **Improvement** | "improve", "optimize", "refactor", "update", "enhance" |
| **Chore** | "upgrade", "migrate", "cleanup", "configure", "setup" |

### 3. Write the Plan

Structure the plan with these sections. Use the appropriate variant for sections marked with `|`:

#### Required Sections (all task types)

```markdown
# TASK-XX: <title>
**Type**: Bug | Feature | Improvement | Chore

## Summary
2-4 sentences: what needs to be done and why it matters.

## Problem | Opportunity
What's wrong (Bug) or what's possible (Feature/Improvement).

## Evidence / Observations
- Relevant code snippets (10-25 lines max, reference file paths for longer blocks)
- Error messages, logs, screenshots
- Current behavior vs expected behavior

## Root Cause | Rationale
Deeper analysis: why this is happening (Bug) or why this approach (Feature).

## Proposed Solution | Suggested Fixes
Actionable steps with pros/cons if multiple approaches exist.
If the fix is obvious, present it as the solution, not a suggestion.

## Implementation Plan
Ordered steps. Reference specific files and functions.
Each step should be small enough to verify independently.

## Testing & Validation
How to verify the solution works. Specific test cases or commands.
```

#### Conditional Sections

**For Bugs** — add before Implementation Plan:
- **Steps to Reproduce**: Numbered steps to trigger the issue
- **Expected vs Actual Behavior**: Side-by-side comparison
- **Impact Assessment**: Who/what is affected, severity

**For Features** — add before Implementation Plan:
- **User Stories**: "As a [user], I want [feature] so that [benefit]"
- **Acceptance Criteria**: Checkboxes for done-ness
- **High-Level Design**: Architecture decisions, component interactions

**For Improvements/Chores** — add after Implementation Plan:
- **Risks & Mitigations**: What could go wrong, how to handle it

### 4. Guidelines

- **Length**: 150-300 lines. Prioritize completeness over brevity.
- **No time estimates**: They clutter the plan with unreliable detail.

### 5. Save the Plan

Create `.claude/tasks/pending/` directory if it doesn't exist.

Find the highest `TASK-XX` number in `.claude/tasks/pending/` and increment by 1. Default to `TASK-01` if the directory is empty or no task files exist.

Save to `.claude/tasks/pending/TASK-XX-<brief-description>.md` where:
- `XX` is the next sequential task number (zero-padded)
- `<brief-description>` is a 3-5 word kebab-case summary

### 6. Return

Report the saved file path and a brief summary of the plan.
