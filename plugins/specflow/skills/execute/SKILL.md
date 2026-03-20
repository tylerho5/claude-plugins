---
name: execute
description: Use when executing an existing task plan file, following its implementation steps with verification
disable-model-invocation: true
argument-hint: "[task-plan-file-path]"
---

# Execute

Read a task plan and execute it step by step with verification at each stage.

## Input

PLAN_FILE: $ARGUMENTS

## Workflow

### 1. Load and Review

1. Read the plan file at PLAN_FILE
2. Review it critically:
   - Are the steps clear and actionable?
   - Are there missing dependencies or prerequisites?
   - Do the steps have a logical order?
3. If the plan has no Testing & Validation section, confirm with the user what verification steps to run before marking the task complete.
4. If you have concerns, raise them before starting
5. If the plan looks sound, proceed

### 2. Execute Steps

For each step in the Implementation Plan:

1. **Announce** what you're about to do
2. **Implement** the step as described
3. **Verify** the step works:
   - Run any tests specified in the plan
   - Check that the change doesn't break existing functionality
   - Confirm the step's expected outcome
4. **Report** progress to the user before moving to the next step

### 3. Verify Completion

After all steps are done:
1. Run the full verification from the plan's "Testing & Validation" section
2. Check that all acceptance criteria (if any) are met
3. Run any relevant test suites

### 4. Move Plan to Completed

On successful completion:
1. Create `.claude/tasks/completed/` if it doesn't exist
2. Move PLAN_FILE from `.claude/tasks/pending/` to `.claude/tasks/completed/`

### 5. Report

Summarize what was done:
- Steps completed
- Any deviations from the plan and why
- Verification results
- Any remaining follow-up items

## When to Stop

**Stop executing immediately when:**
- A step is unclear or ambiguous — ask for clarification
- A verification fails — diagnose before continuing
- You discover the plan has a flaw — raise it rather than working around it
- A dependency is missing or unavailable

**Do not guess your way through blockers.** Stop and ask.

## Notes

- Follow the plan's steps as written. If you see a better approach, propose it before deviating.
- If the plan references specific files or functions that no longer exist, stop and report the discrepancy.
- Keep changes scoped to what the plan describes. Don't refactor surrounding code or add unplanned features.
