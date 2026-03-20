# Specflow

A Claude Code plugin for spec-driven development workflows.

## Plugin Structure

```
specflow/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── skills/
│   ├── scout/SKILL.md       # Codebase exploration via parallel Explore agents
│   ├── research/SKILL.md    # Web documentation search via parallel agents
│   ├── plan/SKILL.md        # Structured task specification creation
│   ├── rnp/SKILL.md         # Pipeline: scout + research (parallel) → plan
│   └── execute/SKILL.md     # Step-by-step plan execution with verification
└── CLAUDE.md
```

## Skills Overview

| Skill | Invocation | Purpose |
|-------|-----------|---------|
| `specflow:scout` | User + Model | Dispatch Explore agents to find relevant codebase files |
| `specflow:research` | User + Model | Dispatch agents to search web for documentation |
| `specflow:plan` | User only | Create structured task plan from requirements |
| `specflow:rnp` | User only | Full pipeline: scout → research → plan |
| `specflow:execute` | User only | Execute a task plan file step by step |

## Artifacts

Skills produce artifacts in `.claude/` subdirectories:
- `.claude/scout_files/` — Scout reports (file lists with line ranges)
- `.claude/doc_search/` — Research reports (URLs + summaries)
- `.claude/tasks/pending/` — Task plans awaiting execution
- `.claude/tasks/completed/` — Executed task plans

## Development

### Testing locally

```bash
claude --plugin-dir /Users/tylerho/dev/specflow
```

### Reloading after changes

```
/reload-plugins
```

## Skill Authoring Guidelines

- Frontmatter: only `name`, `description`, and optional fields (`argument-hint`, `disable-model-invocation`)
- Description starts with "Use when..." — triggering conditions only, no workflow summary
- Written in third person (injected into system prompt)
- Keep SKILL.md under 500 lines (prefer under 100)
- Use `$ARGUMENTS` for single-argument skills, `$1`/`$2`/`$3` for multi-argument
