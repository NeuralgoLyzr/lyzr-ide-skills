---
name: lyzr-file-image-output
description: Generate files (PDF, DOCX, CSV) and images with LYZR agents. Enable file_output or image_model; download artifacts via response.files.
triggers:
  - lyzr file generation
  - lyzr image generation
  - generate pdf with lyzr
  - lyzr artifact
  - lyzr file output
  - lyzr image output
  - create document with lyzr agent
version: 1.0.0
author: LYZR AI
---

# LYZR File & Image Output Skill

## Overview

Enable agents to generate files (PDFs, DOCX, CSV, etc.) and images during conversations. Outputs are returned as downloadable artifacts. Use `file_output=True` for documents and `image_model=...` for images.

---

## Setup

```bash
pip install lyzr-adk
export LYZR_API_KEY="your-api-key"
```

---

## File Output

Enable document generation with `file_output=True` at agent creation:

```python
from lyzr import Studio

studio = Studio()

agent = studio.create_agent(
    name="Report Generator",
    provider="gpt-4o",
    role="Document creator",
    goal="Generate professional reports",
    file_output=True
)

response = agent.run("Create a Q4 sales report in PDF format")

if response.has_files():
    for file in response.files:
        print(f"Generated: {file.name} ({file.format_type})")
        file.download("./reports/q4_sales.pdf")
```

### Supported File Types

| Format | Description | Use Cases |
|--------|-------------|-----------|
| PDF | Portable Document | Reports, invoices, certificates |
| DOCX | Word Document | Editable documents, proposals |
| CSV | Comma-Separated | Data exports, spreadsheets |
| XLSX | Excel | Structured data, analytics |
| PPT/PPTX | PowerPoint | Presentations, slides |
| TXT | Plain Text | Simple text files |

### Enable on Existing Agent

```python
agent = studio.get_agent("agent_id")
agent = agent.update(file_output=True)
```

---

## Image Output

Enable image generation with `image_model` (Gemini or DALL-E):

```python
from lyzr import Studio
from lyzr.image_models import Gemini, DallE

studio = Studio()

agent = studio.create_agent(
    name="Image Creator",
    provider="gpt-4o",
    role="Visual designer",
    goal="Create images",
    image_model=Gemini.PRO
)

response = agent.run("Create an image of a futuristic cityscape")

if response.has_files():
    for img in response.files:
        print(f"Image: {img.url}")
        img.download("./images/city.png")
```

### Image Models

```python
from lyzr.image_models import Gemini, DallE

# Google Gemini
Gemini.PRO      # gemini/gemini-3-pro-image-preview
Gemini.FLASH    # gemini/gemini-2.5-flash-image

# OpenAI DALL-E
DallE.DALL_E_3      # dall-e-3
DallE.DALL_E_2      # dall-e-2
DallE.GPT_IMAGE_1   # gpt-image-1
DallE.GPT_IMAGE_1_5 # gpt-image-1.5
```

---

## Combined File & Image Output

Enable both in the same agent:

```python
from lyzr.image_models import Gemini

agent = studio.create_agent(
    name="Content Creator",
    provider="gpt-4o",
    role="Marketing content creator",
    goal="Create documents with images",
    instructions="Generate brochures, presentations, and marketing materials",
    file_output=True,
    image_model=Gemini.FLASH
)

response = agent.run("Create a product brochure for our new smartphone with product images")

if response.has_files():
    for artifact in response.files:
        print(f"{artifact.format_type.upper()}: {artifact.name}")
        if artifact.format_type == "pdf":
            artifact.download("./brochures/smartphone.pdf")
        elif artifact.format_type == "image":
            artifact.download("./images/smartphone.png")
```

---

## Artifact Class

Generated files are returned as `Artifact` objects.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | File name |
| `url` | str | Download URL |
| `format_type` | str | File format (pdf, docx, image, etc.) |
| `artifact_id` | str | Unique artifact identifier |

### Download

```python
artifact.download(save_path: str)

# Examples
artifact.download("./output/report.pdf")
artifact.download(f"./output/{artifact.name}")
```

---

## Working with Artifacts

### Check for Files

```python
if response.has_files():
    print(f"Files generated: {len(response.files)}")
for file in response.files:
    print(file.name)
```

### Filter by Type

```python
pdfs = [f for f in response.files if f.format_type == "pdf"]
images = [f for f in response.files if f.format_type == "image"]
```

### Batch Download

```python
import os
output_dir = "./outputs"
os.makedirs(output_dir, exist_ok=True)
for artifact in response.files:
    save_path = os.path.join(output_dir, artifact.name)
    artifact.download(save_path)
```

---

## Best Practices

- Use `file_output=True` only when the agent should produce documents; omit for text-only agents.
- Use `image_model=Gemini.FLASH` for faster image generation, `Gemini.PRO` or `DallE.DALL_E_3` for higher quality.
- Always check `response.has_files()` before iterating `response.files`.
- Store downloads with meaningful paths; use `artifact.name` or `artifact.format_type` to organize outputs.
