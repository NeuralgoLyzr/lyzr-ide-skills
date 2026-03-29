---
name: lyzr-agent
description: Create and manage AI agents via the API. Supports CRUD, configuration, versioning, and agent lifecycle. **Total Endpoints:** 12
triggers:
- create a lyzr agent
- build an agent with lyzr
- use lyzr sdk
- lyzr agent
- lyzr-adk agent
- set up lyzr
version: 1.0.0
author: LYZR AI
---

# LYZR Agent Skill

## Overview

The ADK treats an agent as a configurable object: you define behavior with `role`, `goal`, and `instructions`, pick a `provider` / model, then layer optional capabilities (memory, tools, RAG, guardrails). The same agent instance can be run interactively, behind an API, or in batch jobs; only the calling pattern changes. Keep agent names and descriptions meaningful in Studio so operators can audit which automations map to which workloads.

## Setup

```bash
pip install lyzr-adk
export LYZR_API_KEY="your-api-key"   # Get from studio.lyzr.ai
```

For Jupyter/Colab:
```bash
pip install lyzr-adk[jupyter]
```

---

## Step 1: Initialize the Studio

```python
from lyzr import Studio

studio = Studio()  # Reads LYZR_API_KEY from env automatically
```

---

## Step 2: Create an Agent

```python
agent = studio.create_agent(
    name="My Agent",
    provider="openai/gpt-4o",        # See supported models below
    role="What this agent IS",        # e.g. "Customer support assistant"
    goal="What this agent ACHIEVES",  # e.g. "Resolve user queries"
    instructions="How it should behave",  # e.g. "Be concise and professional"
    temperature=0.7,                  # Optional: 0.0–1.0
    top_p=0.9                         # Optional; also: response_model, memory, contexts, rai_policy, file_output, image_model, reflection, bias_check, llm_judge
)
```

### Supported Providers & Models

| Provider    | Example values                                          |
|-------------|--------------------------------------------------------|
| OpenAI      | `openai/gpt-4o`, `openai/gpt-4o-mini`, `openai/o3`   |
| Anthropic   | `anthropic/claude-sonnet-4-5`, `anthropic/claude-opus-4-5` |
| Google      | `google/gemini-2.0-flash`, `google/gemini-2.5-pro`    |
| Groq        | `groq/llama-3.3`, `groq/kimi-k2`                      |
| Perplexity  | `perplexity/sonar-pro`                                 |
| AWS Bedrock | `bedrock/nova-pro`, `bedrock/claude`                   |

> Short names also work: `"gpt-4o"`, `"claude-sonnet-4-5"`, `"gemini-2.0-flash"`

---

## Step 3: Run the Agent

```python
response = agent.run("Your message here")
print(response.response)
```

With a session (for memory/context continuity):
```python
response = agent.run("Hello, my name is Alice", session_id="user_001")
```

---

## Structured Outputs (Type-Safe Responses)

Use Pydantic models to get structured, type-safe responses:

```python
from pydantic import BaseModel

class SentimentResult(BaseModel):
    sentiment: str       # "positive", "negative", "neutral"
    score: float         # 0.0 – 1.0
    summary: str

agent = studio.create_agent(
    name="Sentiment Analyzer",
    provider="gpt-4o",
    role="Sentiment analysis expert",
    goal="Classify sentiment in text",
    instructions="Return structured sentiment analysis",
    response_model=SentimentResult
)

result: SentimentResult = agent.run("I absolutely love this product!")
print(result.sentiment)   # "positive" - IDE autocomplete works!
print(result.score)       # 0.97
```

---

## Adding Tools (Local Python Functions)

No decorators needed — just pass any function:

```python
def get_weather(city: str) -> dict:
    """Get current weather for a city"""
    # Your implementation here
    return {"city": city, "temp": "22°C", "condition": "Sunny"}

def search_database(query: str) -> str:
    """Search the database for records"""
    return "Found results for query"

agent.add_tool(get_weather)
agent.add_tool(search_database)

response = agent.run("What's the weather in London?")
```

---

## Streaming Responses

```python
for chunk in agent.run("Tell me a detailed story", stream=True):
    print(chunk.content, end="", flush=True)
```

> Note: Streaming is disabled when RAI guardrails are active.

---

## Contexts

Provide background information to agents via key-value contexts:

```python
context = studio.create_context(
    name="company_info",
    value="Acme Corp is a technology company founded in 2020. We specialize in AI solutions."
)

agent = studio.create_agent(
    name="Support Bot",
    provider="gpt-4o",
    role="Customer support",
    goal="Help customers with inquiries"
)
agent = agent.add_context(context)

# Or pass at creation
agent = studio.create_agent(..., contexts=[context])
response = agent.run("What does your company do?")
```

---

## Agent Lifecycle Management

```python
# Update configuration
agent = agent.update(temperature=0.3, instructions="Be very concise")

# Clone an agent
clone = agent.clone("My Agent V2")

# Get existing agent by ID
agent = studio.get_agent("agent_id_here")

# List all agents
agents = studio.list_agents()

# Delete
agent.delete()
```

---

## Error Handling

```python
from lyzr.exceptions import (
    LyzrError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    APIError,
    TimeoutError,
    InvalidResponseError,
    ToolNotFoundError
)

try:
    agent = studio.create_agent(...)
    response = agent.run("message")
except AuthenticationError:
    print("Check your LYZR_API_KEY")
except NotFoundError:
    print("Resource not found (e.g. invalid agent ID)")
except RateLimitError:
    print("Rate limit hit — back off and retry")
except TimeoutError:
    print("Request timed out")
except InvalidResponseError:
    print("Response parsing or validation failed")
except ToolNotFoundError:
    print("Referenced local tool not found")
except ValidationError as e:
    print(f"Bad input: {e}")
except APIError as e:
    print(f"API error: {e}")
except LyzrError as e:
    print(f"ADK error: {e.message}")
```

---

## Environment & Logging

```python
studio = Studio(
    env="prod",       # "prod" (default), "dev", "local"
    timeout=30,       # seconds
    log="warning"     # "debug", "info", "warning", "error", "none"
)
```

---

## Best Practices

- Always store `LYZR_API_KEY` in environment variables, never hardcode it
- Use `session_id` with `uuid.uuid4()` to separate user conversations
- Use `response_model` with Pydantic when you need predictable output structure
- Use `temperature=0.1–0.3` for factual/analytical tasks, `0.7–0.9` for creative ones
- Use `agent.update()` instead of recreating agents to preserve agent ID
- Enable `log="debug"` during development to inspect tool calls and responses
