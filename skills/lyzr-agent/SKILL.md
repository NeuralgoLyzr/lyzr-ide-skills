---
name: lyzr-agent
description: Create and manage AI agents via the API. Supports CRUD, configuration, versioning, and agent lifecycle. **Total Endpoints:** 12
license: MIT
allowed-tools:
  - Studio
  - Agent
  - create_agent
  - tools
  - contexts
  - sessions
triggers:
- create a lyzr agent
- build an agent with lyzr
- use lyzr sdk
- lyzr agent
- lyzr-adk agent
- set up lyzr
metadata:
  author: LYZR AI
  version: "1.0.0"
  category: sdk
---

# LYZR Agent Skill

## Instructions

1. Use this skill when the user builds or configures LYZR agents with `lyzr-adk` (`Studio`, `create_agent`, tools, contexts, streaming, lifecycle, errors).
2. Require `LYZR_API_KEY` in the environment; never hardcode secrets in examples.
3. Use API names, parameters, and patterns from this file and official ADK docs only.
4. When updating from documentation sync, change only section bodies under mapped headings—do not rename or remove `##` / `###` headings listed in `doc-to-skill-mapping.yaml`.

## Overview

Create and manage AI agents via the API. Agents are AI-powered entities that can understand and respond to messages. Each agent is backed by an LLM provider and can be customized with roles, goals, instructions, and additional features like memory, tools, and RAG.

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

studio = Studio(api_key="your-api-key")
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
    top_p=0.9,                        # Optional: 0.0–1.0
    description=None,                # Optional: Agent description
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
print(response.response)
print(response.session_id)

# Example with user_id
response = agent.run("What's the weather?", user_id="user_456")
print(response.response)
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
    response_format=SentimentResult
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
    """Fetch current weather for a city"""
    # Your implementation here
    return {"city": city, "temp": "22°C", "condition": "Sunny"}

def search_database(query: str, limit: int = 10) -> str:
    """Search the database for records"""
    return f"Found {limit} results for '{query}'"

agent.add_tool(get_weather)
agent.add_tool(search_database)

response = agent.run("What's the weather in London?")
print(response.response)
```

---

## Streaming Responses

```python
for chunk in agent.run("Tell me a detailed story", stream=True):
    print(chunk.content, end="", flush=True)
```

> Note: Streaming is supported with `stream=True` in `agent.run()`, but not when RAI guardrails are enabled.

```python
for chunk in agent.run("Tell me a detailed story", stream=True):
    print(chunk.content, end="", flush=True)

    if chunk.done:
        print("\n--- Generation complete ---")
        print(f"Session: {chunk.session_id}")
```

> Note: Streaming is supported with `stream=True` in `agent.run()`, but not when RAI guardrails are enabled.

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
agent.add_context(context)

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
    if e.status_code:
        print(f"Status: {e.status_code}")
    if e.response:
        print(f"Response: {e.response}")
    if hasattr(e, 'validation_error') and e.validation_error:
        print(f"Validation error: {e.validation_error}")
    if e.validation_error:
        print(f"Validation error: {e.validation_error}")
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


## ADK: Unmapped Docs


## ADK: agents/creating-agents


Source: `agents/creating-agents.mdx`

    Create agents using `studio.create_agent()` with customizable LLM providers, roles, and features.

    ## Quick Start

    ```python
    from lyzr import Studio

    studio = Studio(api_key="your-api-key")

    agent = studio.create_agent(
        name="Support Bot",
        provider="gpt-4o",
        role="Customer support agent",
        goal="Help customers resolve their issues",
        instructions="Be empathetic, clear, and solution-oriented"
    )
    ```

    ## Function Signature

    ```python
    studio.create_agent(
        name: str,
        provider: str = None,
        role: str = None,
        goal: str = None,
        instructions: str = None,
        description: str = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        response_model: BaseModel = None,
        memory: int = None,
        contexts: List[Context] = None,
        rai_policy: RAIPolicy = None,
        file_output: bool = False,
        image_model: ImageModelConfig = None,
        reflection: bool = False,
        bias_check: bool = False,
        llm_judge: bool = False,
        groundedness_facts: List[str] = None,
        llm_credential_id: str = None,
        additional_model_params: Dict = None,
    ) -> Agent
    ```

    ## Parameters

    ### Required Parameters

    | Parameter | Type | Description |
    |-----------|------|-------------|
    | `name` | str | Agent name (1-200 characters) |

    ### Core Parameters

    | Parameter | Type | Default | Description |
    |-----------|------|---------|-------------|
    | `provider` | str | None | LLM provider and model. Examples: `"gpt-4o"`, `"claude-sonnet-4.5"`, `"openai/gpt-4o"` |
    | `role` | str | None | Agent's role or persona (e.g., "Customer support agent") |
    | `goal` | str | None | Agent's

_(truncated)_


## ADK: agents/overview


Source: `agents/overview.mdx`

    Agents are AI-powered entities that can understand and respond to messages. Each agent is backed by an LLM provider and can be customized with roles, goals, instructions, and additional features like memory, tools, and RAG.

    ## Quick Start

    ```python
    from lyzr import Studio

    studio = Studio(api_key="your-api-key")

    # Create an agent
    agent = studio.create_agent(
        name="Support Bot",
        provider="gpt-4o",
        role="Customer support agent",
        goal="Help customers resolve issues",
        instructions="Be empathetic, concise, and solution-oriented"
    )

    # Run the agent
    response = agent.run("I can't login to my account")
    print(response.response)
    ```

    ## Agent Lifecycle

    ```
    Create → Configure → Run → Manage
    ```

    1. **Create**: Use `studio.create_agent()` to create an agent with a name, provider, and configuration
    2. **Configure**: Add features like memory, tools, contexts, or RAI policies
    3. **Run**: Execute the agent with `agent.run()` to get responses
    4. **Manage**: Update, clone, or delete agents as needed

    ## Key Features

    ### Provider Selection

    Choose from multiple LLM providers:

    ```python
    # OpenAI
    agent = studio.create_agent(provider="gpt-4o", ...)

    # Anthropic
    agent = studio.create_agent(provider="claude-sonnet-4.5", ...)

    # Google
    agent = studio.create_agent(provider="gemini-2.5-pro", ...)

    # Full format with provider prefix
    agent = studio.create_agent(provider="openai/gpt-4o", ...)
    ```

    ### Streaming Responses

    Get real-time responses:

    ```python
    for chunk in agent.run("Tell me a story", stream=True):
        print(chunk.content, end="", flush=True)
    ```

    ### Structured Outputs

    Get type-

_(truncated)_


## ADK: overview


## ADK: agents/running-agents


## ADK: providers/providers


## ADK: responses/responses


Source: `responses/responses.mdx`

    The Lyzr ADK provides several response types for different execution modes. This reference covers all response objects and their properties.

    ## Quick Start

    ```python
    from lyzr import Studio

    studio = Studio(api_key="your-api-key")
    agent = studio.create_agent(
        name="Assistant",
        provider="gpt-4o"
    )

    # AgentResponse
    response = agent.run("Hello!")
    print(response.response)
    print(response.session_id)

    # AgentStream (streaming)
    for chunk in agent.run("Tell a story", stream=True):
        print(chunk.content, end="")
    ```

    ---

    ## AgentResponse

    The main response object returned by `agent.run()`.

    ```python
    class AgentResponse:
        response: str                           # The agent's text response
        session_id: str                         # Session identifier
        message_id: str | None                  # Unique message ID
        metadata: dict | None                   # Additional metadata
        tool_calls: List[dict] | None           # Tool calls made
        raw_response: dict | None               # Raw API response
        artifact_files: List[Artifact] | None   # Generated files
    ```

    ### Properties

    | Property | Type | Description |
    |----------|------|-------------|
    | `response` | str | The agent's text response |
    | `session_id` | str | Session identifier for conversation continuity |
    | `message_id` | str \| None | Unique identifier for this message |
    | `metadata` | dict \| None | Additional metadata (tokens, timing, etc.) |
    | `tool_calls` | List[dict] \| None | Tools called during execution |
    | `raw_response` | dict \| None | Raw API response for debugging |
    | `artifact_files` | List[Artifact] \| None | Generated files |

_(truncated)_


## ADK: studio


## ADK: tools/tool-execution


## ADK: contexts/contexts


## ADK: agents/managing-agents
