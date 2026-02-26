---
name: lyzr-rag
description: Add retrieval-augmented generation (RAG) to LYZR agents. Covers creating knowledge bases, ingesting documents (PDF, DOCX, websites, text), querying, and connecting to agents.
triggers:
  - lyzr rag
  - lyzr knowledge base
  - add documents to lyzr agent
  - lyzr vector store
  - lyzr retrieval
  - build rag with lyzr
version: 1.0.0
author: LYZR AI
---

# LYZR RAG (Knowledge Base) Skill

## Overview
 
LYZR's RAG system lets you ingest documents and websites into a vector store, then have your agents retrieve relevant context before answering questions.

**Supported vector stores:** Qdrant, Weaviate, PG-Vector, Milvus, Amazon Neptune

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

studio = Studio()

kb = studio.create_knowledge_base(
    name="my_knowledge_base",
    vector_store="qdrant",                    # qdrant | weaviate | pg_vector | milvus | neptune
    embedding_model="text-embedding-3-large"  # OpenAI embedding model
)
```

---

## Step 2: Add Documents

### Add a PDF
```python
kb.add_pdf(
    "path/to/document.pdf",
    chunk_size=1024,      # tokens per chunk (default: 1024)
    chunk_overlap=128     # overlap between chunks (default: 128)
)
```

### Add a Word Document
```python
kb.add_docx("path/to/report.docx")
```

### Add a Plain Text File
```python
kb.add_txt("path/to/notes.txt")
```

### Add a Website (Crawled)
```python
kb.add_website(
    "https://docs.yoursite.com",
    max_pages=50,   # max pages to crawl (default: 10)
    max_depth=2     # crawl depth (default: 2)
)
```

### Add Raw Text
```python
kb.add_text(
    "Our support hours are Monday–Friday, 9am–5pm EST.",
    source="faq"   # label for tracking
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
    provider="openai/gpt-4o",
    role="Documentation expert",
    goal="Answer questions using company documentation",
    instructions="Always base answers on the provided documents. If unsure, say so."
)

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
