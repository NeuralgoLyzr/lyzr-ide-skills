---
name: lyzr-guardrails
description: Add responsible AI (RAI) safety guardrails to LYZR agents. Covers toxicity detection, PII protection, secrets masking, topic filtering, NSFW detection, and prompt injection prevention.
triggers:
  - lyzr guardrails
  - lyzr safety
  - lyzr rai
  - lyzr pii
  - lyzr toxicity
  - responsible ai lyzr
  - safe lyzr agent
version: 1.0.0
author: LYZR AI
---

# LYZR Guardrails (RAI) Skill

## Overview

LYZR's Responsible AI (RAI) system lets you add safety policies to agents to handle:

- **Toxicity detection** — block or flag harmful content
- **PII protection** — redact, mask, or block personal data
- **Secrets detection** — mask API keys, passwords, tokens
- **Topic filtering** — allow or ban specific discussion topics
- **Keyword filtering** — block or allow by keywords
- **NSFW detection** — block inappropriate content
- **Fairness and bias detection** — optional bias checks
- **Prompt injection prevention** — stop jailbreak attempts

---

## Setup

```bash
pip install lyzr-adk
export LYZR_API_KEY="your-api-key"
```

---

## Step 1: Import RAI Types

```python
from lyzr import Studio
from lyzr.rai import PIIType, PIIAction, SecretsAction
```

### PIIType — What personal data to detect

| PIIType              | What it catches            |
|---------------------|----------------------------|
| `PIIType.EMAIL`     | Email addresses            |
| `PIIType.PHONE`     | Phone numbers              |
| `PIIType.CREDIT_CARD` | Credit card numbers      |
| `PIIType.SSN`       | Social security numbers    |
| `PIIType.PERSON`    | Personal names             |
| `PIIType.LOCATION`  | Physical addresses         |
| `PIIType.IP_ADDRESS`| IP addresses               |
| `PIIType.URL`       | URLs                       |
| `PIIType.DATE_TIME` | Dates and times            |

### PIIAction — What to do when PII is found

| PIIAction           | Behavior                                      |
|---------------------|-----------------------------------------------|
| `PIIAction.BLOCK`   | Reject the message entirely                   |
| `PIIAction.REDACT`  | Replace or obscure with `[REDACTED]`         |
| `PIIAction.DISABLED`| No action                                    |

### SecretsAction — What to do with detected secrets

| SecretsAction         | Behavior                        |
|----------------------|---------------------------------|
| `SecretsAction.MASK`  | Mask detected API keys/tokens   |
| `SecretsAction.BLOCK` | Reject the message              |

---

## Step 2: Create a Safety Policy

```python
studio = Studio()

policy = studio.create_rai_policy(
    name="ProductionSafety",
    description="Standard guardrails for customer-facing agents",

    # Toxicity: 0.0 = strictest, 1.0 = most permissive
    toxicity_threshold=0.3,

    # Secrets: mask any detected API keys, tokens, passwords
    secrets_detection=SecretsAction.MASK,

    # PII: define per-type actions
    pii_detection={
        PIIType.CREDIT_CARD: PIIAction.BLOCK,    # Hard block CC numbers
        PIIType.EMAIL: PIIAction.REDACT,          # Replace emails with [REDACTED]
        PIIType.PHONE: PIIAction.REDACT,
        PIIType.SSN: PIIAction.BLOCK
    },

    # Topics
    banned_topics=["politics", "religion", "competitor products"],
    # allowed_topics={"enabled": True, "topics": ["technology", "support"]}  # Optional whitelist

    # NSFW
    nsfw_check=True,
    nsfw_threshold=0.8,    # 0.0 = block almost everything, 1.0 = very permissive

    # Security
    prompt_injection=True  # Prevent jailbreak attempts
)
```

---

## Step 3: Attach Policy to an Agent

### At Creation

```python
agent = studio.create_agent(
    name="Safe Customer Bot",
    provider="openai/gpt-4o",
    role="Customer support agent",
    goal="Help customers safely",
    instructions="Be helpful, professional, and safe",
    rai_policy=policy
)
```

### On an Existing Agent

```python
agent = agent.add_rai_policy(policy)
```

### Remove Policy

```python
agent = agent.remove_rai_policy()
```

### Check if Policy is Active

```python
has_policy = agent.has_rai_policy()   # Returns True/False
```

---

## Managing Policies

```python
# Update a policy
policy.update(toxicity_threshold=0.5, nsfw_check=False)

# Get existing policy
policy = studio.get_rai_policy("policy_id")

# List all policies
policies = studio.list_rai_policies()

# Delete
policy.delete()
```

---

## Complete Example: Production Support Bot

```python
from lyzr import Studio
from lyzr.rai import PIIType, PIIAction, SecretsAction

studio = Studio()

# Define safety policy
policy = studio.create_rai_policy(
    name="SupportBotPolicy",
    description="Guardrails for public-facing support agent",
    toxicity_threshold=0.3,
    secrets_detection=SecretsAction.MASK,
    pii_detection={
        PIIType.CREDIT_CARD: PIIAction.BLOCK,
        PIIType.EMAIL: PIIAction.REDACT,
        PIIType.PHONE: PIIAction.REDACT
    },
    banned_topics=["politics", "religion"],
    nsfw_check=True,
    nsfw_threshold=0.8,
    prompt_injection=True
)

# Create agent with guardrails
agent = studio.create_agent(
    name="Safe Support Bot",
    provider="openai/gpt-4o",
    role="Customer support specialist",
    goal="Resolve customer issues safely",
    instructions="Help users with product questions. Never discuss politics or religion.",
    rai_policy=policy
)

# Run — guardrails are applied automatically
response = agent.run("How do I reset my password?")
print(response.response)
```

---

## Best Practices

- Start with `toxicity_threshold=0.5` and tighten to `0.3` if you see issues in production
- Always use `PIIAction.BLOCK` for financial data (credit cards, SSNs), `REDACT` for contact info
- Enable `prompt_injection=True` on any public-facing agent — always
- `banned_topics` is case-insensitive and does fuzzy matching — keep topic names broad
- Note: **Streaming is disabled** when RAI guardrails are active (by design, for safety)
- Test your policy with edge-case inputs before going to production
- Use separate policies for different agent types (internal vs. customer-facing)
