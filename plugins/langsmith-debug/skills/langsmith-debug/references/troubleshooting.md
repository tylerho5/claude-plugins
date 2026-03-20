# Troubleshooting Guide

## "No traces found matching criteria"

Causes:
- No agent activity in timeframe
- Tracing disabled in code
- Wrong project name
- API key issues

Solutions:
```bash
# Try longer timeframe
langsmith trace list --last-n-minutes 1440 --limit 50

# Check environment
echo $LANGSMITH_API_KEY
echo $LANGSMITH_PROJECT

# List available projects
langsmith project list

# Try threads instead
langsmith thread list --limit 10
```

Check code has tracing enabled:
```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "lsv2_..."
os.environ["LANGSMITH_PROJECT"] = "your-project-name"
```

## "Project not found"

```bash
# List available projects to find the correct name
langsmith project list

# Set correct project
export LANGSMITH_PROJECT="correct-project-name"

# Persist in shell config
echo 'export LANGSMITH_PROJECT="correct-project-name"' >> ~/.bashrc
source ~/.bashrc
```

## "Authentication failed"

```bash
# Check API key
echo $LANGSMITH_API_KEY

# Set if missing
export LANGSMITH_API_KEY="lsv2_pt_..."

# Persist in shell config
echo 'export LANGSMITH_API_KEY="lsv2_..."' >> ~/.bashrc
echo 'export LANGSMITH_PROJECT="your-project"' >> ~/.bashrc
source ~/.bashrc
```

## "langsmith: command not found"

```bash
# Install CLI
curl -fsSL https://cli.langsmith.com/install.sh | sh

# Verify
langsmith --version

# If not in PATH, add the install location
export PATH="$PATH:$HOME/.langsmith/bin"
```

## Environment variables not persisting

Add to shell config:
```bash
# Bash
echo 'export LANGSMITH_API_KEY="your_key"' >> ~/.bashrc
echo 'export LANGSMITH_PROJECT="your_project"' >> ~/.bashrc

# Zsh
echo 'export LANGSMITH_API_KEY="your_key"' >> ~/.zshrc
echo 'export LANGSMITH_PROJECT="your_project"' >> ~/.zshrc

# Reload
source ~/.bashrc  # or source ~/.zshrc
```

## Tracing not working in code

Requirements:
```python
import os

# Set BEFORE any LangChain imports
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "lsv2_..."
os.environ["LANGSMITH_PROJECT"] = "your-project-name"

# Then import and use LangChain
from langchain.chat_models import ChatOpenAI
# ...
```

For LangGraph, add callback:
```python
from langchain.callbacks import LangChainTracer
tracer = LangChainTracer(project_name="your-project-name")
```

## Scripts fail to run

```bash
# Check Python version
python3 --version  # Need 3.7+

# Verify script exists
ls <skill-dir>/scripts/analyze_traces.py

# Run from repo root (use subcommand)
python3 <skill-dir>/scripts/analyze_traces.py summary ./.claude/langsmith_traces

# Check trace files valid (supports .json and .jsonl)
cat ./.claude/langsmith_traces/trace_*.json | jq .
cat ./.claude/langsmith_traces/trace_*.jsonl | head -1 | jq .

# Verify directory has traces
ls -la ./.claude/langsmith_traces/
```

## Agent not responding (no traces)

Debug steps:
```bash
# Check if any traces exist
langsmith trace list --last-n-minutes 1440 --limit 5

# If none, add debug to code:
import os
print("Tracing:", os.getenv("LANGCHAIN_TRACING_V2"))
print("API Key set:", bool(os.getenv("LANGCHAIN_API_KEY")))
print("Project:", os.getenv("LANGSMITH_PROJECT"))

# Check LangSmith Studio web interface
# Visit: https://smith.langchain.com/

# Test network
curl -H "x-api-key: $LANGSMITH_API_KEY" \
  https://api.smith.langchain.com/info
```
