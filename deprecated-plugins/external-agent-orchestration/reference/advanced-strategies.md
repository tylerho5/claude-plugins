# Advanced Orchestration Strategies

Load this file when you need consensus strategies, voting patterns, or multi-agent output synthesis.

## Consensus Strategies

### Majority Voting
For binary decisions (yes/no, A vs B):
1. Use odd N (3-5) to prevent ties
2. Parse each agent's vote
3. Report: "4/5 agents recommend X (80% confidence)"

Thresholds: ≥80% high, 60-79% medium, <60% show all perspectives.

### Quality Filtering (Code Review)
1. Each agent reviews independently
2. Issues found by 2+ agents = high confidence
3. Single-agent issues = informational
4. Present high-confidence first

```
High Confidence (2+ agents):
- Missing null check (claude-glm, opencode)

Single Agent:
- Performance concern (qwen only)
```

### Diverse Perspectives (Architecture)
1. Give each agent a different lens: minimal, clean architecture, pragmatic
2. Present all perspectives side-by-side with labels
3. Don't synthesize - user chooses

### Source Validation (Web Research)
1. Multiple agents research the same topic independently
2. Cross-reference findings across agents
3. High-confidence facts: mentioned by 2+ agents with source URLs
4. Single-source claims: flag as "requires verification"

```
High Confidence (3/3 agents, multiple sources):
- Feature X released in v2.0 (source: docs.example.com, github.com/repo/releases)

Medium Confidence (2/3 agents):
- Performance improvement of 30% (source: blog.example.com, reddit.com/r/topic)

Single Source (verify independently):
- Breaking change in API endpoint (qwen only, source: forum.example.com)
```

## Agent Count Guidelines

| Task | Agents |
|------|--------|
| Codebase exploration | 3-5 |
| Web research | 2-3 |
| Architecture perspectives | 2-3 |
| Code review | 3 |

---

## Worked Examples

### Consensus Code Review

User: "Review this auth code for issues"

Select 3 agents, each reviews independently. Aggregate:

```
High Confidence (3/3):
- SQL injection at line 6

Medium Confidence (2/3):
- Missing null check at line 10

Single Agent:
- Performance issue at line 73 (claude-glm only)
```

### Diverse Perspectives

User: "How should we implement feature flags?"

Give each agent a different prompt:
- Agent 1: "Design minimal approach"
- Agent 2: "Design clean architecture approach"
- Agent 3: "Design pragmatic approach"

Present all three side-by-side. Don't synthesize.

### Web Research with Source Validation

User: "Research the latest features in TypeScript 5.7"

Run 3 agents in parallel with identical prompts. Cross-reference results:

```
High Confidence (3/3 agents):
- Isolated Declarations feature (sources: typescriptlang.org/docs, devblogs.microsoft.com, github.com/microsoft/TypeScript/releases)
- Path Mapping Improvements (sources: typescriptlang.org/docs, typescript.tv/release-notes)

Medium Confidence (2/3 agents):
- 15% faster type checking (sources: devblogs.microsoft.com, reddit.com/r/typescript)

Verify Independently (1 agent only):
- Breaking change in module resolution (qwen only, source: stackoverflow.com/questions/...)
```

Action: Present high-confidence findings immediately. Flag single-source claims for user verification.