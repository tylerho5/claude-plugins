# Common Error Patterns

## Rate Limiting

Symptoms: `RateLimitError`, `429`, errors in bursts/intervals, failures after N iterations
Causes: Too many API calls, no backoff, concurrent agents, redundant calls

Fix:
```python
from langchain.llms import OpenAI
llm = OpenAI(max_retries=3, request_timeout=30)

# Rate limiting
import time
from functools import wraps
def rate_limit(calls_per_second=1):
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if (wait := min_interval - elapsed) > 0:
                time.sleep(wait)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator
```

Detect: error_type "RateLimitError"/"429", clustering at iteration counts, time intervals

## Timeout

Symptoms: `TimeoutError`, `ReadTimeout`, hangs, inconsistent durations
Causes: Slow LLM, no tool timeouts, network issues, large context

Fix:
```python
llm = OpenAI(request_timeout=30, max_tokens=1000)

# Tool timeout
import asyncio
async def tool_with_timeout(input_str):
    try:
        return await asyncio.wait_for(my_tool(input_str), timeout=10.0)
    except asyncio.TimeoutError:
        return "Tool timed out"
```

Detect: duration_ms >30000, "timeout" in errors, compare success vs fail durations

## Tool Execution

Symptoms: `ToolExecutionError`, `ValueError` in outputs, unexpected responses, invalid args
Causes: Unhandled errors, invalid args, unexpected format, missing validation

Fix:
```python
from langchain.tools import Tool
def safe_tool(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return str(result) if not isinstance(result, str) else result
        except Exception as e:
            return f"Error: {str(e)}"
    return wrapper

my_tool = Tool(
    name="calculator",
    func=safe_tool(calculate),
    description="Calculate expressions. Input: string"
)
```

Detect: run_type='tool' with error, specific tools failing, input/output patterns

## Memory

Symptoms: `OutOfMemoryError`, forgets context, inconsistent behavior, buffer overflow
Causes: Unbounded buffer, not clearing messages, too much stored, no summarization

Fix:
```python
from langchain.memory import ConversationBufferWindowMemory
memory = ConversationBufferWindowMemory(k=5, return_messages=True)

# Or summary
from langchain.memory import ConversationSummaryMemory
memory = ConversationSummaryMemory(llm=llm, max_token_limit=500)

# Clear periodically
if len(agent.memory.chat_memory.messages) > 20:
    agent.memory.clear()
```

Detect: High token counts, memory errors, long message history

## Agent Loops

Symptoms: Repeats actions, never finishes, exceeds max iterations, circular tool calls
Causes: Reasoning loop, tool outputs don't change state, no stopping condition, bad prompts

Fix:
```python
agent = initialize_agent(
    tools=tools, llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    max_iterations=10,
    early_stopping_method="generate"
)

# Loop detection
def detect_loops():
    history = []
    def callback(action, obs):
        action_str = f"{action.tool}:{action.tool_input}"
        history.append(action_str)
        if history[-3:].count(action_str) >= 3:
            raise ValueError("Loop detected")
    return callback
```

Detect: run_count >expected, repeated tool calls, execution flow cycles

## Output Parsing

Symptoms: `OutputParserException`, "Could not parse", malformed action/input
Causes: LLM ignores format, parser too strict, high temperature, unclear prompt

Fix:
```python
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent, tools=tools,
    handle_parsing_errors=True  # Catch and retry
)

# Custom handler
def handle_parse_error(error):
    return "Use format: Action: tool\\nAction Input: value"

agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent, tools=tools,
    handle_parsing_errors=handle_parse_error
)

llm = OpenAI(temperature=0.0)  # Lower temp
```

Detect: "OutputParserException", errors at LLM calls, failed LLM outputs

## Authentication

Symptoms: `AuthenticationError`, `401`, API key errors
Causes: Missing/invalid keys, expired credentials, env vars not loaded

Fix:
```python
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY missing")

llm = OpenAI(
    openai_api_key=api_key,
    openai_organization=os.getenv("OPENAI_ORG_ID")
)
```

Detect: 401/403 errors, "authentication"/"unauthorized" in errors

## Context Length

Symptoms: `maximum context length`, token limit exceeded, failures with long conversations, 400 errors
Causes: Long history, large docs, not tracking tokens, prompt+input+history exceeds limit

Fix:
```python
from langchain.callbacks import get_openai_callback
with get_openai_callback() as cb:
    response = agent.run(query)
    print(f"Tokens: {cb.total_tokens}")

# Split docs
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

# Larger model
llm = ChatOpenAI(model_name="gpt-4-turbo")  # 128k

# Prune history
from langchain.memory import ConversationSummaryBufferMemory
memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=2000)
```

Detect: total_tokens, "context length"/"token limit" in errors, token usage comparison

## Prevention Best Practices

1. Set timeouts on LLM/tools
2. Retry with exponential backoff
3. Validate inputs
4. Monitor token usage
5. Prune/summarize memory
6. Handle parsing errors gracefully
7. Set max iterations
8. Test tools independently

## Debug Workflow

1. Identify error type (which category?)
2. Check frequency (recurring or one-off?)
3. Analyze context (what was agent doing?)
4. Compare traces (failed vs successful)
5. Implement fix (use solutions above)
6. Validate (test new traces)
7. Iterate (refine)
