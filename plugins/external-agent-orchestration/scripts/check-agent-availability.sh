#!/bin/bash
# check-agent-availability.sh
# Test which external CLI coding agents are available in the environment
# Returns JSON array of available agent names

set -euo pipefail

# Array to store available agents
available_agents=()

# Check claude-glm (zsh function defined in ~/.zshrc)
if zsh -c 'source ~/.zshrc 2>/dev/null && type claude-glm' &>/dev/null; then
  available_agents+=("claude-glm")
fi

# Check qwen (command)
if command -v qwen &>/dev/null; then
  available_agents+=("qwen")
fi

# Check gemini (command)
if command -v gemini &>/dev/null; then
  available_agents+=("gemini")
fi

# Check opencode (command)
if command -v opencode &>/dev/null; then
  available_agents+=("opencode")
fi

# Convert to JSON array
if [ ${#available_agents[@]} -eq 0 ]; then
  echo "[]"
else
  printf '%s\n' "${available_agents[@]}" | jq -R . | jq -s .
fi
