---
name: scout
description: Use when you need to find codebase files relevant to a task before planning or implementing
argument-hint: "[task-description]"
---

# Scout

Explore the codebase to find files relevant to a task using parallel search agents.

## Input

TASK: $ARGUMENTS

## Workflow

### 1. Analyze the Task

Break down the task into searchable dimensions:
- **Keywords**: function names, class names, error messages, identifiers
- **Patterns**: file types, directory structures, naming conventions
- **Dependencies**: imports, call chains, data flow entry points

### 2. Dispatch Parallel Explore Agents

If the task is narrow (single file fix, typo), dispatch 1 agent. Otherwise, launch 3 Explore agents in a **single message** (parallel execution), each with a different search strategy:

**Agent 1 — Keyword Search**
Search for terms, identifiers, error messages, and strings directly related to the task. Use Grep for content, Glob for filenames.

**Agent 2 — Structure Search**
Find files by structural patterns: directory names, module boundaries, config files, test files, related components in the task area.

**Agent 3 — Dependency Trace**
From any known entry points, trace imports and function calls to find connected files. Follow the dependency graph.

Each agent prompt MUST include:
- The full task description
- "You are ONLY searching for relevant files. Do NOT implement or modify anything."
- "Return a structured file list: `- <file-path> (offset: N, limit: M)` with a brief reason for each entry"
- `subagent_type: "Explore"` and `model: "haiku"`

The `offset` and `limit` values specify which section of the file is relevant, minimizing token usage for downstream skills.

### 3. Collect Results

- Deduplicate files across agents; keep separate entries if multiple sections of the same file are relevant
- Drop irrelevant entries
- Sort by relevance to the task

### 4. Save Report

Create `.claude/scout_files/` if it doesn't exist. Save to `.claude/scout_files/<brief-task-slug>-scout.md`:

```markdown
# Scout Report: <brief task summary>

## Task
<task description>

## Relevant Files
- path/to/file.ts (offset: 1, limit: 50) — reason this section matters
- path/to/other.ts (offset: 120, limit: 30) — reason this section matters
```

### 5. Return

Report the saved file path and a brief summary: number of files found and key areas identified.
