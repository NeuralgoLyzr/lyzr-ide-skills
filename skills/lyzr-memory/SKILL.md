---
name: lyzr-memory
description: Add conversation memory and persistent context to LYZR agents. Covers built-in message memory, session management, and external memory providers (Mem0, AWS AgentCore, SuperMemory).
triggers:
  - lyzr memory
  - lyzr conversation history
  - lyzr session memory
  - remember across messages lyzr
  - lyzr persistent memory
  - add memory to lyzr agent
version: 1.0.0
author: LYZR AI
---

# LYZR Memory Skill

## Overview

LYZR supports two memory approaches:

1. **Built-in message memory** — keeps the last N messages in context (simple, no extra setup)
2. **External memory providers** — persistent memory via Mem0, AWS AgentCore, or SuperMemory

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
    provider="openai/gpt-4o",
    role="Helpful assistant",
    goal="Maintain context across a conversation",
    instructions="Remember what users tell you and refer back to it",
    memory=30    # Keep last 30 messages in context window
)
```

### Add Memory to an Existing Agent

```python
agent = agent.add_memory(max_messages=50)
```

### Remove Memory

```python
agent = agent.remove_memory()
```

### Check Memory Status

```python
has_memory = agent.has_memory()   # Returns True/False
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
    mem0_api_key="your-mem0-api-key"   # From mem0.ai
)
```

### AWS AgentCore

```python
aws_credential = studio.create_memory_credential(
    provider="aws-agentcore",
    name="AWS Memory",
    aws_access_key_id="AKIA...",
    aws_secret_access_key="your-secret",
    aws_region="us-east-1"
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
