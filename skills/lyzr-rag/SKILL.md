---
name: lyzr-rag
description: Add retrieval-augmented generation (RAG) to LYZR agents. Covers creating knowledge bases, ingesting documents (PDF, DOCX, websites, text), querying, and connecting to agents.
license: MIT
allowed-tools:
  - Studio
  - KnowledgeBase
  - create_knowledge_base
  - query
  - agent.run
triggers:
  - lyzr rag
  - lyzr knowledge base
  - add documents to lyzr agent
  - lyzr vector store
  - lyzr retrieval
  - build rag with lyzr
metadata:
  author: LYZR AI
  version: "1.0.0"
  category: rag
---

# LYZR RAG (Knowledge Base) Skill

## Instructions

1. Use this skill for knowledge bases, document ingestion, retrieval, and wiring KBs into `agent.run(..., knowledge_bases=[...])`.
2. Require `LYZR_API_KEY`; use vector store and embedding names from this file unless docs specify otherwise.
3. Prefer examples here over paraphrase; do not invent KB methods or parameters.
4. Preserve mapped `##` / `###` headings when syncing from documentation.

## Overview

LYZR's RAG system lets you ingest documents and websites into a vector store, then have your agents retrieve relevant context before answering questions.

**Supported vector stores:** Qdrant, Weaviate, PG Vector, Milvus, Neptune, Pinecone

---

## Setup

```bash
pip install lyzr-adk
export LYZR_API_KEY="your-api-key"
```

---

## Step 1: Create a Knowledge Base

```python
from lyzr import Studio

studio = Studio()api_key="your-api-key"

kb = studio.create_knowledge_base(
    name="my_knowledge_base",
    vector_store="qdrant",                    # qdrant | weaviate | pg_vector | milvus | neptune
    embedding_model="text-embedding-3-large", # OpenAI embedding model
    llm_model="gpt-4o",                       # LLM for query processing
    description="My custom knowledge base"    # Optional description
)

print(f"Created KB: {kb.id}")
```

---

## Step 2: Add Documents

### Add a PDF
```python
kb.add_pdf(
    "path/to/document.pdf",
    chunk_size=1024,      # tokens per chunk (default: 1024)
    chunk_overlap=128,    # overlap between chunks (default: 128)
    data_parser="llmsherpa", # PDF parser to use
    extra_info=None       # optional metadata as JSON string
)
```

### Add a Word Document
```python
kb.add_docx("path/to/report.docx",
    chunk_size=1024,      # tokens per chunk (default: 1024)
    chunk_overlap=128,    # overlap between chunks (default: 128)
    data_parser="docx2txt", # Document parser
    extra_info=None       # optional metadata
)
```

### Add a Plain Text File
```python
kb.add_txt("path/to/notes.txt",
    chunk_size=1024,      # tokens per chunk (default: 1024)
    chunk_overlap=128,    # overlap between chunks (default: 128)
    data_parser="simple", # Text parser
    extra_info=None       # optional metadata
)
```

### Add a Website (Crawled)
```python
kb.add_website(
    "https://docs.yoursite.com",
    max_pages=50,   # max pages to crawl (default: 1)
    max_depth=2,    # crawl depth (default: 0)
    chunk_size=1024,      # tokens per chunk (default: 1024)
    chunk_overlap=128,    # overlap between chunks (default: 128)
    dynamic_content_wait_secs=None, # wait time for dynamic content
    dynamic_content_wait_secs=5, # wait time for dynamic content
    crawler_type="cheerio" # Crawler type
)
```

### Add Raw Text
```python
kb.add_text(
    "Our support hours are Monday–Friday, 9am–5pm EST.",
    source="faq",  # label for tracking
    chunk_size=1024,      # tokens per chunk (default: 1024)
    chunk_overlap=128     # overlap between chunks (default: 128)
)
```

---

## Step 3: Query the Knowledge Base Directly

```python
results = kb.query(
    "What are the business hours?",
    top_k=3,                    # number of results to return
    retrieval_type="basic",     # "basic" (default) | "mmr" | "hyde" | "time_aware"
    score_threshold=0.5         # min similarity score (0.0–1.0)
    lambda_param=None,          # hybrid search parameter (0=keyword, 1=semantic)
    time_decay_factor=None      # time decay for time_aware retrieval
)

for result in results:
    print(f"Score: {result.score:.2f}")
    print(f"Text:  {result.text}")
    print()
```

**Retrieval types:** `basic` (default), `mmr` (diverse results), `hyde` (question-style), `time_aware` (recency-weighted).

---

## Step 4: Connect to an Agent

```python
agent = studio.create_agent(
    name="Docs Assistant",
    provider="gpt-4o"
)
response = agent.run(
    "What is the return policy?",
    knowledge_bases=[kb]
)
print(response.response)

# Pass knowledge base at run time
response = agent.run(
    "What does the manual say about installation?",
    knowledge_bases=[kb]
)
print(response.response)
```

### Custom Retrieval Config Per Run

```python
response = agent.run(
    "What is the refund policy?",
    knowledge_bases=[
        kb.with_config(
            top_k=5,
            score_threshold=0.7   # stricter threshold = more precise results
        )
    ]
)
```

---

## Managing Documents

```python
# List all ingested documents
docs = kb.list_documents()
for doc in docs:
    print(doc)

# Delete specific documents by ID
kb.delete_documents(["doc_id_1", "doc_id_2"])

# Clear all documents (keep the KB)
kb.reset()

# Delete the entire knowledge base
kb.delete()
```

---

## Full RAG Example

```python
from lyzr import Studio

studio = Studio()

# Build knowledge base from multiple sources
kb = studio.create_knowledge_base(
    name="company_knowledge",
    vector_store="qdrant",
    embedding_model="text-embedding-3-large"
)

kb.add_pdf("product_manual.pdf")
kb.add_website("https://docs.company.com", max_pages=30)
kb.add_text("Founded in 2020. HQ in San Francisco.", source="company_info")

# Create RAG-powered agent
agent = studio.create_agent(
    name="Support Bot",
    provider="openai/gpt-4o",
    role="Customer support specialist",
    goal="Help customers using official documentation",
    instructions="Only answer based on retrieved documents. Be concise and cite sources."
)

# Run with RAG
response = agent.run(
    "How do I install the product?",
    knowledge_bases=[kb],
    session_id="user_session_001"
)
print(response.response)
```

---

## Best Practices

- Set `score_threshold=0.6–0.8` in production to filter out low-relevance chunks
- Use `chunk_size=512` for precise Q&A, `chunk_size=1024` for broader context
- Use `chunk_overlap=10–20%` of chunk_size to avoid cutting context at boundaries
- Add a `source` label when using `add_text()` so you can track where content came from
- Use `kb.reset()` instead of deleting and recreating the KB when refreshing content
- Run `kb.query()` directly first to validate retrieval quality before connecting to an agent
- For large doc sets, increase `max_pages` and `max_depth` on `add_website()` carefully — it costs tokens


## ADK: knowledge-bases/overview

Source: `knowledge-bases/overview.mdx`

    Knowledge bases enable Retrieval Augmented Generation (RAG) by storing and querying documents. Agents can use knowledge bases to answer questions based on your documents, websites, and other content.

    ## Quick Start

    ```python
    from lyzr import Studio

    studio = Studio(api_key="your-api-key")

    # Create a knowledge base
    kb = studio.create_knowledge_base(
        name="product_docs",
        vector_store="qdrant",
        embedding_model="text-embedding-3-large"
    )

    # Add documents
    kb.add_pdf("manual.pdf")
    kb.add_website("https://docs.example.com", max_pages=50)

    # Create an agent with the knowledge base
    agent = studio.create_agent(
        name="Support Bot",
        provider="gpt-4o",
        role="Customer support",
        goal="Answer questions using documentation",
        instructions="Use the knowledge base to answer questions accurately"
    )

    # Query with the knowledge base
    response = agent.run(
        "How do I reset my password?",
        knowledge_bases=[kb]
    )
    print(response.response)
    ```

    ## What is a Knowledge Base?

    A knowledge base is a vector database that stores your documents as embeddings. When an agent receives a question, it:

    1. **Searches** the knowledge base for relevant content
    2. **Retrieves** the most relevant chunks
    3. **Generates** a response using the retrieved context

    This is called Retrieval Augmented Generation (RAG).

    ## Supported Document Types

    | Type | Method | Description |
    |------|--------|-------------|
    | PDF | `add_pdf()` | PDF documents |
    | DOCX | `add_docx()` | Word documents |
    | TXT | `add_txt()` | Plain text files |
    | Website | `add_website()` | Web pages with crawling |
    | Text | `add_text()` | Raw t

_(truncated)_


## ADK: knowledge-bases/querying


## ADK: knowledge-bases/managing-kb
