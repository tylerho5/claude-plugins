---
name: adversarial-code-review
description: "Structured adversarial code review: spawns a Sonnet critiquer agent that debates design decisions in real time. Use when you want rigorous scrutiny of recent changes — refactors, integrations, or architectural decisions. The critiquer looks for logical flaws, simpler alternatives, pattern violations, and naming inconsistencies. You defend choices (Concede / Defend / Rebuttal). Net actions agreed before any code is touched. Trigger on: 'adversarial review', 'critiquer agent', 'debate my changes', 'defend my design', 'review my changes before I merge', 'sanity check this refactor', 'what did I miss', 'second opinion on this code'."
---

# Adversarial Code Review

A two-agent debate: you defend, a Sonnet critiquer challenges. Net actions agreed before any code changes.

## Phase 1: Scope and Gather Context

Before spawning anything, figure out what's being reviewed.

1. Run `git diff` (or `git diff --staged`, or `git diff main..HEAD` — whatever matches the user's intent) to get the changeset.
2. If the diff is large, confirm scope with the user: "There are changes across 12 files — do you want me to review all of them, or focus on a specific area?"
3. Identify context files the critiquer will need — files that import or are imported by the changed code, relevant tests, config. Trace the dependency graph rather than guessing.

## Phase 2: Spawn the Critiquer

Create the team and spawn the critiquer agent:

1. `TeamCreate` with a descriptive name for the review.
2. Spawn the critiquer with `subagent_type=general-purpose`, `model=sonnet`, `team_name=<team>`, `name=critiquer`, `run_in_background=true`.

The critiquer's prompt should be:

```
Read <skill-dir>/critiquer-prompt.md for your review instructions and output format.

Here is the diff to review:
<paste the diff>

For additional context, read these files: <list of context files from Phase 1>

When your review is complete, send the full critique to team-lead via SendMessage.
```

Do not read `critiquer-prompt.md` yourself — it contains the critiquer's instructions and loading it into your own context mixes concerns.

## Phase 3: Defend

When the critique arrives, respond to every issue with one of:

| Label | Meaning |
|-------|---------|
| Concede | The critiquer is right. State what you'll change. |
| Defend | The choice is correct. Explain the reasoning the critiquer missed. |
| Rebuttal | The concern is based on a false premise. Provide evidence (import graph, call chain, test output). |

End your response with proposed net actions — a numbered list of concrete changes — and ask the critiquer to accept or push back.

## Phase 4: Negotiate (max 3 rounds per issue)

Continue exchanging until each issue is resolved. The critiquer should explicitly accept or push back on each point.

Cap at 3 rounds per issue. If you and the critiquer can't agree after 3 exchanges on the same point, flag it as unresolved and move on — the user will decide.

## Phase 5: User Checkpoint

Before implementing anything, present a summary to the user:

```
## Review Summary

### Conceded (will fix)
- Issue 2: Missing error propagation in handleAuth — will add try/catch
- Issue 5: Unused import left behind — will remove

### Defended (no change)
- Issue 1: Critiquer suggested extracting a helper, but the inline version is clearer here
- Issue 3: Naming concern — matches existing convention in auth module

### Unresolved (need your input)
- Issue 4: Whether to keep the retry logic or use the existing retry util

### Proposed changes
1. Add error propagation in src/auth.ts:42
2. Remove unused import in src/handlers.ts:3
```

Wait for the user to confirm or adjust before touching code.

## Phase 6: Implement and Teardown

Apply the agreed changes, then clean up:

1. Make only the changes listed in the net actions.
2. Send a shutdown request to the critiquer via `SendMessage`.
3. `TeamDelete` to clean up the team.

## Key Rules

- No code changes during the debate. The debate determines what to change.
- Label every response (Concede / Defend / Rebuttal). Unlabeled responses are harder to negotiate.
- Rebuttals require evidence — trace the import graph, read the file, run the test before asserting something is fine.
- Conceding is not failure. The goal is the best code, not winning.
- Out-of-scope issues should be acknowledged and proposed as follow-up work, not dismissed.
