---
name: research
description: Use when needing web documentation, API references, or technical context from the web to inform a task
argument-hint: "[task-description] [optional: documentation-urls]"
---

# Research

Search the web for documentation and technical information relevant to a task using parallel agents.

## Input

TASK: $1
DOCUMENTATION_URLS: $2

## Workflow

### 1. Identify Search Angles

Based on the task, determine 2-3 distinct search angles:
- **Official docs**: Framework/library documentation, API references
- **Community**: Stack Overflow, GitHub issues, blog posts with solutions
- **Related**: Similar implementations, migration guides, changelog entries

### 2. Dispatch Parallel Research Agents

Launch **2 agents by default**. Add a third if DOCUMENTATION_URLS were provided or if more than 2 clearly distinct search angles exist. Dispatch all in a **single message** (parallel execution). Use `model: "sonnet"` for each agent.

Each agent prompt MUST include:
- The full task description
- "You are ONLY searching for relevant documentation. Do NOT implement anything."
- "Use WebSearch to find sources, then WebFetch to read the most promising results"
- If DOCUMENTATION_URLS were provided, one agent should prioritize fetching and analyzing those specific URLs
- "Return structured findings in this format:"

```
## <Topic/Source>
**URLs**: <url1>, <url2>
**Summary**: <brief summary of what was found and why it's relevant>
**Key Details**: <specific code patterns, API signatures, config values, etc.>
```

### 3. Collect Results

- Merge findings from all agents
- Group related URLs together (e.g., multiple pages from same docs site)
- Drop irrelevant or low-quality results
- Prioritize: official docs > GitHub issues/PRs > blog posts > forum answers

### 4. Save Report

Create `.claude/doc_search/` directory if it doesn't exist. Save to `.claude/doc_search/<brief-task-slug>-research.md`:

```markdown
# Research Report: <brief task summary>

## Task
<task description>

## Findings

### <Topic 1>
**Sources**: <urls>
**Summary**: ...
**Key Details**: ...

### <Topic 2>
...
```

### 5. Return

Report the saved file path and a brief summary of key findings.
