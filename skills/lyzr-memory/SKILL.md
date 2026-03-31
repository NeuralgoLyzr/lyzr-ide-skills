---
name: lyzr-memory
description: Add conversation memory and persistent context to LYZR agents. Covers built-in message memory, session management, and external memory providers (Mem0, AWS AgentCore, SuperMemory).
license: Apache-2.0
allowed-tools:
  - Studio
  - Agent
  - session_id
  - memory
  - create_memory_credential
triggers:
  - lyzr memory
  - lyzr conversation history
  - lyzr session memory
  - remember across messages lyzr
  - lyzr persistent memory
  - add memory to lyzr agent
metadata:
  author: LYZR AI
  version: "1.0.0"
  category: memory
---

# LYZR Memory Skill

## Instructions

1. Use this skill for built-in message memory, `session_id` continuity, and external providers (Mem0, AWS AgentCore, SuperMemory).
2. Require `LYZR_API_KEY`; provider keys belong in env or secure config, never in committed code.
3. Stress one stable `session_id` per conversation when explaining multi-turn behavior.
4. Preserve mapped section headings when documentation sync updates this file.

## Overview

LYZR supports two memory approaches:

1. **Built-in message memory** — maintains conversation context across multiple messages within a session (simple, no extra setup)
2. **External memory providers** — persistent memory options include Mem0, AWS AgentCore, and SuperMemory

---

## Setup

```bash
pip install lyzr-adk
export LYZR_API_KEY="your-api-key"
```

---

## Option 1: Built-in Message Memory

The simplest way to give an agent conversation memory.

### At Agent Creation

```python
from lyzr import Studio

studio = Studio()

agent = studio.create_agent(
    name="Conversational Bot",
    provider="gpt-4o",
    role="Helpful assistant",
    goal="Maintain context across a conversation",
    instructions="Remember what users tell you and refer back to it",
    memory=30  # Integer: number of messages to remember
)
```

### Add Memory to an Existing Agent

```python
agent = agent.add_memory(max_messages=10  # Messages to remember (1-50))
```

### Remove Memory

```python
agent = agent.remove_memory()
```

### Check Memory Status

```python
has_memory = agent.has_memory() -> bool  # Returns True or False
```

---

## Using Sessions for Context Continuity

Always pass a consistent `session_id` to link messages into a conversation:

```python
import uuid

session_id = str(uuid.uuid4())   # One UUID per user/conversation

# Message 1
agent.run("My name is Alice and I'm building a chatbot", session_id=session_id)

# Message 2 — agent remembers from message 1
response = agent.run("What was I building again?", session_id=session_id)
print(response.response)  # "You mentioned you're building a chatbot"
```

> **Important:** Without `session_id`, each `agent.run()` call is stateless.

---

## Option 2: External Memory Providers

For persistent memory that survives beyond a session window.

### Mem0

```python
mem0_credential = studio.create_memory_credential(
    provider="mem0",
    name="Mem0 Memory",
    api_key="your-mem0-api-key"  # From mem0.ai
)
```

### AWS AgentCore

```python
aws_credential = studio.create_memory_credential(
    provider="aws-agentcore",
    name="AWS Memory",
    aws_access_key_id="your-access-key-id",
    aws_secret_access_key="your-secret-access-key",
    aws_region="your-region"
)

# AWS-specific methods
status = aws_credential.get_status()
resources = aws_credential.list_resources()
aws_credential.use_existing(memory_id="existing-memory-id")
aws_credential.delete_resource()
```

### SuperMemory

```python
supermemory_credential = studio.create_memory_credential(
    provider="supermemory",
    name="SuperMemory",
    supermemory_api_key="your-supermemory-api-key",
    supermemory_api_url="https://api.supermemory.ai"  # optional, defaults to this URL
)
```

---

## Complete Memory Example

```python
from lyzr import Studio
import uuid

studio = Studio()

# Create agent with built-in memory
agent = studio.create_agent(
    name="Personal Assistant",
    provider="openai/gpt-4o",
    role="Personal productivity assistant",
    goal="Help users manage tasks while remembering their preferences",
    instructions="""
    Remember the user's name, preferences, and ongoing tasks.
    Reference previous messages naturally when relevant.
    """,
    memory=50   # Last 50 messages in context
)

# Simulate a conversation
session = str(uuid.uuid4())

agent.run("Hi! My name is Bob and I prefer bullet point summaries.", session_id=session)
agent.run("I'm working on a Python project this week.", session_id=session)

response = agent.run(
    "Give me a quick summary of what you know about me.",
    session_id=session
)
print(response.response)
# "Here's what I know about you, Bob:
#  • You prefer bullet point summaries
#  • You're working on a Python project this week"
```

---

## Best Practices

- Always use a unique `session_id` per user — `str(uuid.uuid4())` works well
- Set `memory=20–50` for most conversational agents; higher values use more context tokens
- **Memory size:** More messages = more tokens per request; balance context length with cost and latency
- Store `session_id` in your app's user session/database so it persists across page reloads
- Use external providers (Mem0, AWS) when you need memory that outlasts a single session window
- Validate credentials after creation: `credential.validate()`
- Remove memory for stateless task agents (code generation, one-shot analysis) to save tokens


## ADK: Unmapped Docs


## ADK: memory/add-memories


## ADK: memory/agent-memory


Source: `memory/agent-memory.mdx`

    Agent memory maintains conversation context across multiple messages. Configure memory at agent creation or add it to existing agents.

    ## Quick Start

    ```python
    from lyzr import Studio

    studio = Studio(api_key="your-api-key")

    # Create agent with memory
    agent = studio.create_agent(
        name="Assistant",
        provider="gpt-4o",
        role="Helpful assistant",
        goal="Have contextual conversations",
        instructions="Remember what the user told you",
        memory=30  # Remember last 30 messages
    )

    # Conversation with context
    session = "my_session"
    agent.run("My favorite color is blue", session_id=session)
    response = agent.run("What's my favorite color?", session_id=session)
    # "Your favorite color is blue"
    ```

    ---

    ## Adding Memory at Creation

    Use the `memory` parameter when creating an agent:

    ```python
    agent = studio.create_agent(
        name="Bot",
        provider="gpt-4o",
        role="Assistant",
        goal="Help users",
        instructions="Be helpful",
        memory=30  # Integer: number of messages to remember
    )
    ```

    ### Memory Parameter

    | Value | Range | Description |
    |-------|-------|-------------|
    | Integer | 1-50 | Number of recent messages to keep in context |

    ```python
    # Small memory (quick exchanges)
    agent = studio.create_agent(..., memory=10)

    # Medium memory (typical conversations)
    agent = studio.create_agent(..., memory=30)

    # Large memory (complex multi-turn tasks)
    agent = studio.create_agent(..., memory=50)

    # Maximum memory
    agent = studio.create_agent(..., memory=50)
    ```

    ---

    ## Adding Memory to Existing Agent

    Use `agent.add_memory()` to enable memory on an existing ag

_(truncated)_


## ADK: memory/cognis-overview


## ADK: memory/delete-memories


Source: `memory/delete-memories.mdx`

    Cognis provides two deletion methods: `delete()` removes a single memory by ID, and `delete_session()` clears all messages and memories from an entire session.

    ## Delete a Single Memory

    ```python
    from lyzr import Cognis

    cog = Cognis(api_key="sk-your-api-key")

    success = cog.delete(memory_id="mem_abc123")
    print(success)  # True
    ```

    ### `delete()` Method Signature

    ```python
    cog.delete(
        memory_id: str,
        owner_id: str | None = None,
    ) -> bool
    ```

    ### `delete()` Parameters

    | Parameter | Type | Required | Description |
    |-----------|------|----------|-------------|
    | `memory_id` | `str` | Yes | The ID of the memory to delete. |
    | `owner_id` | `str` | No | Owner identifier for additional scoping. |

    ### Response

    Returns `True` if the memory was successfully deleted.

    ## Delete an Entire Session

    Remove all messages and memories associated with a session:

    ```python
    success = cog.delete_session(
        owner_id="user_alice",
        session_id="sess_001",
    )
    print(success)  # True
    ```

    ### `delete_session()` Method Signature

    ```python
    cog.delete_session(
        owner_id: str,
        session_id: str,
        agent_id: str | None = None,
    ) -> bool
    ```

    ### `delete_session()` Parameters

    | Parameter | Type | Required | Description |
    |-----------|------|----------|-------------|
    | `owner_id` | `str` | Yes | Owner/user identifier. |
    | `session_id` | `str` | Yes | Session identifier to clear. |
    | `agent_id` | `str` | No | Agent identifier to further scope the deletion. |

    ### Response

    Returns `True` if the session was successfully cleared.

    ## Search and Delete Workflow

    A common pattern is to

_(truncated)_


## ADK: memory/get-memories


## ADK: memory/overview


Source: `memory/overview.mdx`

    Memory allows agents to maintain conversation context across multiple messages within a session. This enables natural, contextual conversations where the agent remembers previous interactions.

    ## Quick Start

    ```python
    from lyzr import Studio

    studio = Studio(api_key="your-api-key")

    # Create agent with memory
    agent = studio.create_agent(
        name="Conversational Bot",
        provider="gpt-4o",
        role="Helpful assistant",
        goal="Have natural conversations",
        instructions="Remember context from previous messages",
        memory=30  # Remember last 30 messages
    )

    # Start a conversation
    session_id = "user_123_session"

    agent.run("My name is Alice", session_id=session_id)
    agent.run("I'm interested in Python programming", session_id=session_id)
    response = agent.run("What's my name and what am I interested in?", session_id=session_id)

    # Agent remembers: "Your name is Alice and you're interested in Python programming"
    ```

    ## How Memory Works

    1. **Messages are stored** per session using the `session_id`
    2. **Context is maintained** across multiple `agent.run()` calls
    3. **Recent messages** are included in the agent's context window
    4. **Older messages** are automatically pruned based on `max_messages`

    ## Memory Configuration

    | Parameter | Range | Description |
    |-----------|-------|-------------|
    | `memory` | 1-50 | Number of recent messages to remember |

    ### At Agent Creation

    ```python
    agent = studio.create_agent(
        name="Bot",
        provider="gpt-4o",
        memory=30  # Keep last 30 messages
    )
    ```

    ### On Existing Agent

    ```python
    agent = agent.add_memory(max_messages=50)
    ```

    ## Session Management

_(truncated)_


## ADK: memory/search-memories

Source: `memory/search-memories.mdx`

    The `search` method performs a semantic search across stored memories, returning the most relevant results ranked by similarity score. Use it to find specific facts, preferences, or context from past conversations.

    ## Basic Usage

    ```python
    from lyzr import Cognis

    cog = Cognis(api_key="sk-your-api-key")

    results = cog.search(query="What is the user's name?", owner_id="user_alice")

    for result in results:
        print(f"{result.content} (score: {result.score})")
    ```

    ## Method Signature

    ```python
    cog.search(
        query: str,
        owner_id: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int | None = None,
        cross_session: bool | None = None,
    ) -> List[CognisSearchResult]
    ```

    ## Parameters

    | Parameter | Type | Required | Description |
    |-----------|------|----------|-------------|
    | `query` | `str` | Yes | Natural language search query. |
    | `owner_id` | `str` | No* | Filter by owner/user identifier. |
    | `agent_id` | `str` | No* | Filter by agent identifier. |
    | `session_id` | `str` | No* | Filter by session identifier. |
    | `limit` | `int` | No | Maximum number of results to return. |
    | `cross_session` | `bool` | No | Search across all sessions for the given owner. |



    ## Response

    Returns a `List[CognisSearchResult]`. Each result has the following fields:

    | Field | Type | Description |
    |-------|------|-------------|
    | `id` | `str` | Memory record ID. |
    | `content` | `str` | The memory content. |
    | `score` | `float \| None` | Semantic similarity score (higher is more relevant). |
    | `owner_id` | `str \| None` | Owner identifier. |
    | `agent_id` | `str \| None` | Agent ident

_(truncated)_


## ADK: memory/update-memories
