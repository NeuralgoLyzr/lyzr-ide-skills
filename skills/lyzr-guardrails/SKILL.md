---
name: lyzr-guardrails
description: Add responsible AI (RAI) safety guardrails to LYZR agents. Covers toxicity detection, PII protection, secrets masking, topic filtering, NSFW detection, and prompt injection prevention.
license: MIT
allowed-tools:
  - Studio
  - create_rai_policy
  - rai_policy
  - PIIType
  - PIIAction
  - SecretsAction
triggers:
  - lyzr guardrails
  - lyzr safety
  - lyzr rai
  - lyzr pii
  - lyzr toxicity
  - responsible ai lyzr
  - safe lyzr agent
metadata:
  author: LYZR AI
  version: "1.0.0"
  category: safety
---

# LYZR Guardrails (RAI) Skill

## Instructions

1. Use this skill for RAI policies, PII/secrets/toxicity/topics/NSFW/prompt-injection controls on LYZR agents.
2. Require `LYZR_API_KEY`; remind that streaming is disabled when guardrails are active where relevant.
3. Import paths and enum names must match this file and ADK (`lyzr.rai`, `create_rai_policy`, attach via `rai_policy`).
4. Do not rename mapped headings during doc sync—patch bodies only.

## Overview

LYZR's Responsible AI (RAI) system lets you add safety policies to agents to handle:

- **Toxicity detection** — block or flag harmful content
- **PII protection** — redact, mask, or block personal data
- **Secrets detection** — mask API keys, passwords, tokens
- **Topic filtering** — allow or ban specific discussion topics
- **Keyword filtering** — block or allow by keywords
- **NSFW detection** — block inappropriate content
- **Fairness and bias detection** — optional bias checks
- **Prompt injection prevention** — Prevent malicious prompt manipulation

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
    toxicity_threshold=0.4,

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
    banned_topics=["politics", "religion", "competitors"],
    allowed_topics={"enabled": True, "topics": ["support", "products"]},

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


## ADK: rai-guardrails/creating-policies


Source: `rai-guardrails/creating-policies.mdx`

    Create RAI policies to define safety guardrails for your agents. Policies can be created, updated, and applied to multiple agents.

    ## Quick Start

    ```python
    from lyzr import Studio
    from lyzr.rai import PIIType, PIIAction, SecretsAction

    studio = Studio(api_key="your-api-key")

    # Create a policy
    policy = studio.create_rai_policy(
        name="StandardSafety",
        description="Standard safety guardrails for production",
        toxicity_threshold=0.4,
        prompt_injection=True,
        pii_detection={
            PIIType.CREDIT_CARD: PIIAction.BLOCK,
            PIIType.EMAIL: PIIAction.REDACT
        }
    )

    print(f"Policy created: {policy.id}")
    ```

    ---

    ## studio.create_rai_policy()

    ```python
    studio.create_rai_policy(
        name: str,
        description: str,
        toxicity_threshold: float = 0.4,
        prompt_injection: bool = False,
        secrets_detection: SecretsAction = SecretsAction.DISABLED,
        pii_detection: Dict[PIIType, PIIAction] = None,
        banned_topics: List[str] = None,
        nsfw_check: bool = False,
        nsfw_threshold: float = 0.8,
        allowed_topics: Dict[str, Any] = None,
        keywords: Dict[str, Any] = None,
        fairness_and_bias: Dict[str, Any] = None
    ) -> RAIPolicy
    ```

    ### Parameters

    | Parameter | Type | Default | Description |
    |-----------|------|---------|-------------|
    | `name` | str | Required | Policy name |
    | `description` | str | Required | Policy description |
    | `toxicity_threshold` | float | 0.4 | Toxicity detection threshold (0.0-1.0) |
    | `prompt_injection` | bool | False | Enable prompt injection detection |
    | `secrets_detection` | SecretsAction | DISABLED | How to handle secrets |
    | `pii_d

_(truncated)_


Source: `rai-guardrails/creating-policies.mdx`

    Create RAI policies to define safety guardrails for your agents. Policies can be created, updated, and applied to multiple agents.

    ## Quick Start

    ```python
    from lyzr import Studio
    from lyzr.rai import PIIType, PIIAction, SecretsAction

    studio = Studio(api_key="your-api-key")

    # Create a policy
    policy = studio.create_rai_policy(
        name="StandardSafety",
        description="Standard safety guardrails for production",
        toxicity_threshold=0.4,
        prompt_injection=True,
        pii_detection={
            PIIType.CREDIT_CARD: PIIAction.BLOCK,
            PIIType.EMAIL: PIIAction.REDACT
        }
    )

    print(f"Policy created: {policy.id}")
    ```

    ---

    ## studio.create_rai_policy()

    ```python
    studio.create_rai_policy(
        name: str,
        description: str,
        toxicity_threshold: float = 0.4,
        prompt_injection: bool = False,
        secrets_detection: SecretsAction = SecretsAction.DISABLED,
        pii_detection: Dict[PIIType, PIIAction] = None,
        banned_topics: List[str] = None,
        nsfw_check: bool = False,
        nsfw_threshold: float = 0.8,
        allowed_topics: Dict[str, Any] = None,
        keywords: Dict[str, Any] = None,
        fairness_and_bias: Dict[str, Any] = None
    ) -> RAIPolicy
    ```

    ### Parameters

    | Parameter | Type | Default | Description |
    |-----------|------|---------|-------------|
    | `name` | str | Required | Policy name |
    | `description` | str | Required | Policy description |
    | `toxicity_threshold` | float | 0.4 | Toxicity detection threshold (0.0-1.0) |
    | `prompt_injection` | bool | False | Enable prompt injection detection |
    | `secrets_detection` | SecretsAction | DISABLED | How to handle secrets |
    | `pii_d

_(truncated)_


## ADK: rai-guardrails/rai-features

Source: `rai-guardrails/rai-features.mdx`

    Learn about each RAI feature in detail, including configuration options, thresholds, and best practices.

    ## Toxicity Detection

    Detect and filter toxic, harmful, or offensive content in user inputs and agent outputs.

    ### Configuration

    ```python
    policy = studio.create_rai_policy(
        name="ToxicityFilter",
        description="Filter toxic content",
        toxicity_threshold=0.4  # 0.0 = strictest, 1.0 = disabled
    )
    ```

    ### Threshold Guidelines

    | Threshold | Strictness | Use Case |
    |-----------|------------|----------|
    | 0.1 - 0.2 | Very strict | Children's content, healthcare |
    | 0.3 - 0.4 | Strict | Customer service, public apps |
    | 0.5 - 0.6 | Moderate | Internal tools, adult apps |
    | 0.7 - 0.9 | Relaxed | Research, content analysis |
    | 1.0 | Disabled | No filtering |

    ### Example

    ```python
    # Strict toxicity filtering
    strict_policy = studio.create_rai_policy(
        name="StrictToxicity",
        description="Very strict toxicity filtering",
        toxicity_threshold=0.2
    )

    # Moderate toxicity filtering
    moderate_policy = studio.create_rai_policy(
        name="ModerateToxicity",
        description="Standard toxicity filtering",
        toxicity_threshold=0.4
    )
    ```

    ---

    ## Prompt Injection Detection

    Protect agents from malicious prompt manipulation attacks that attempt to override instructions or extract sensitive information.

    ### Configuration

    ```python
    policy = studio.create_rai_policy(
        name="InjectionProtection",
        description="Prevent prompt injection",
        prompt_injection=True
    )
    ```

    ### What It Detects

    - Instruction override attempts ("Ignore previous instructions...")
    - Role manipulat

_(truncated)_

Source: `rai-guardrails/rai-features.mdx`

    Learn about each RAI feature in detail, including configuration options, thresholds, and best practices.

    ## Toxicity Detection

    Detect and filter toxic, harmful, or offensive content in user inputs and agent outputs.

    ### Configuration

    ```python
    policy = studio.create_rai_policy(
        name="ToxicityFilter",
        description="Filter toxic content",
        toxicity_threshold=0.4  # 0.0 = strictest, 1.0 = disabled
    )
    ```

    ### Threshold Guidelines

    | Threshold | Strictness | Use Case |
    |-----------|------------|----------|
    | 0.1 - 0.2 | Very strict | Children's content, healthcare |
    | 0.3 - 0.4 | Strict | Customer service, public apps |
    | 0.5 - 0.6 | Moderate | Internal tools, adult apps |
    | 0.7 - 0.9 | Relaxed | Research, content analysis |
    | 1.0 | Disabled | No filtering |

    ### Example

    ```python
    # Strict toxicity filtering
    strict_policy = studio.create_rai_policy(
        name="StrictToxicity",
        description="Very strict toxicity filtering",
        toxicity_threshold=0.2
    )

    # Moderate toxicity filtering
    moderate_policy = studio.create_rai_policy(
        name="ModerateToxicity",
        description="Standard toxicity filtering",
        toxicity_threshold=0.4
    )
    ```

    ---

    ## Prompt Injection Detection

    Protect agents from malicious prompt manipulation attacks that attempt to override instructions or extract sensitive information.

    ### Configuration

    ```python
    policy = studio.create_rai_policy(
        name="InjectionProtection",
        description="Prevent prompt injection",
        prompt_injection=True
    )
    ```

    ### What It Detects

    - Instruction override attempts ("Ignore previous instructions...")
    - Role manipulat

_(truncated)_
