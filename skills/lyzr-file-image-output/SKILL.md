---
name: lyzr-file-image-output
description: Generate files (PDF, DOCX, CSV) and images with LYZR agents. Enable file_output or image_model; download artifacts via response.files.
license: Apache-2.0
allowed-tools: Studio file_output image_model Artifact response.files
triggers:
  - lyzr file generation
  - lyzr image generation
  - generate pdf with lyzr
  - lyzr artifact
  - lyzr file output
  - lyzr image output
  - create document with lyzr agent
metadata:
  author: LYZR AI
  version: "1.0.0"
  category: output
---

# LYZR File & Image Output Skill

## Instructions

1. Use this skill when enabling document generation (`file_output`), image generation (`image_model`), and downloading `Artifact` instances from `response.files`.
2. Require `LYZR_API_KEY`; use `response.has_files()` before iterating artifacts.
3. Match image model enums (`Gemini`, `DallE`) and file behavior to this file and ADK docs.
4. Preserve mapped section headings when syncing from documentation.

## Overview

Enable agents to generate files (PDFs, DOCX, CSV) and images during conversations. Outputs are returned as downloadable artifacts. 
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
    name="Document Generator",
    provider="gpt-4o",
    role="Professional document creator",
    goal="Generate well-formatted documents",
    instructions="Create professional documents in the requested format",
    file_output=True  # Enable file generation
)

response = agent.run("Create a project status report in PDF format")

if response.has_files():
    for file in response.files:
        print(f"Generated: {file.name} ({file.format_type})")
        print(f"Download URL: {file.url}")
        file.download(f"./output/{file.name}")
```

### Supported File Types

| Format | Extension | Description |
|--------|-----------|-------------|
| PDF | .pdf | Portable Document Format |
| DOCX | .docx | Microsoft Word Document |
| CSV | .csv | Comma-Separated Values |
| XLSX | .xlsx | Microsoft Excel Spreadsheet |
| PPTX | .pptx | Microsoft PowerPoint |
| TXT | .txt | Plain Text |
| HTML | .html | HTML Document |
| JSON | .json | JSON Data File |

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
    goal="Create images from descriptions",
    image_model=Gemini.PRO  # Enable image generation
)

response = agent.run("Create an image of a futuristic city at sunset")

if response.has_files():
    for img in response.files:
        print(f"Image URL: {img.url}")
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

### Methods

#### download()

```python
artifact.download(save_path: str) -> None

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


## ADK: file-image-output/file-generation

Source: `file-image-output/file-generation.mdx`

    Enable agents to generate PDFs, Word documents, spreadsheets, and other file formats during conversations.

    ## Quick Start

    ```python
    from lyzr import Studio

    studio = Studio(api_key="your-api-key")

    # Create agent with file output enabled
    agent = studio.create_agent(
        name="Document Generator",
        provider="gpt-4o",
        role="Professional document creator",
        goal="Generate well-formatted documents",
        instructions="Create professional documents in the requested format",
        file_output=True  # Enable file generation
    )

    # Generate a PDF report
    response = agent.run("Create a project status report in PDF format")

    # Access generated files
    if response.has_files():
        for file in response.files:
            print(f"Generated: {file.name} ({file.format_type})")
            print(f"Download URL: {file.url}")
            file.download(f"./output/{file.name}")
    ```

    ---

    ## Enabling File Output

    ### At Agent Creation

    ```python
    agent = studio.create_agent(
        name="Doc Generator",
        provider="gpt-4o",
        role="Document creator",
        goal="Generate documents",
        file_output=True  # Enable file generation
    )
    ```

    ### Update Existing Agent

    ```python
    # Get existing agent
    agent = studio.get_agent("agent_id")

    # Enable file output
    agent = agent.update(file_output=True)
    ```

    ---

    ## Supported File Formats

    | Format | Extension | Description |
    |--------|-----------|-------------|
    | PDF | .pdf | Portable Document Format |
    | DOCX | .docx | Microsoft Word Document |
    | CSV | .csv | Comma-Separated Values |
    | XLSX | .xlsx | Microsoft Excel Spreadsheet |
    | PPTX | .pptx | Microsoft PowerPo

_(truncated)_


## ADK: file-image-output/overview


Source: `file-image-output/overview.mdx`

    Enable agents to generate files (PDFs, DOCX, CSV) and images during conversations. Outputs are returned as downloadable artifacts.

    ## Quick Start

    ```python
    from lyzr import Studio
    from lyzr.image_models import Gemini, DallE

    studio = Studio(api_key="your-api-key")

    # File generation
    file_agent = studio.create_agent(
        name="Report Generator",
        provider="gpt-4o",
        role="Report creator",
        goal="Generate professional reports",
        file_output=True  # Enable file generation
    )

    response = file_agent.run("Create a Q4 sales report in PDF format")

    if response.has_files():
        for file in response.files:
            print(f"Generated: {file.name} ({file.format_type})")
            file.download("./reports/q4_sales.pdf")

    # Image generation
    image_agent = studio.create_agent(
        name="Image Creator",
        provider="gpt-4o",
        role="Visual designer",
        goal="Create images",
        image_model=Gemini.PRO  # Enable image generation
    )

    response = image_agent.run("Create an image of a futuristic cityscape")

    if response.has_files():
        for img in response.files:
            print(f"Image: {img.url}")
            img.download("./images/city.png")
    ```

    ---

    ## File Output

    Enable agents to generate documents like PDFs, DOCX, CSV, and more.

    ### Enable File Output

    ```python
    agent = studio.create_agent(
        name="Doc Generator",
        provider="gpt-4o",
        role="Document creator",
        file_output=True  # Enable file generation
    )
    ```

    ### Supported File Types

    | Format | Description | Use Cases |
    |--------|-------------|-----------|
    | PDF | Portable Document | Reports, invoices, certificates |

_(truncated)_


Source: `file-image-output/overview.mdx`

    Enable agents to generate files (PDFs, DOCX, CSV) and images during conversations. Outputs are returned as downloadable artifacts.

    ## Quick Start

    ```python
    from lyzr import Studio
    from lyzr.image_models import Gemini, DallE

    studio = Studio(api_key="your-api-key")

    # File generation
    file_agent = studio.create_agent(
        name="Report Generator",
        provider="gpt-4o",
        role="Report creator",
        goal="Generate professional reports",
        file_output=True  # Enable file generation
    )

    response = file_agent.run("Create a Q4 sales report in PDF format")

    if response.has_files():
        for file in response.files:
            print(f"Generated: {file.name} ({file.format_type})")
            file.download("./reports/q4_sales.pdf")

    # Image generation
    image_agent = studio.create_agent(
        name="Image Creator",
        provider="gpt-4o",
        role="Visual designer",
        goal="Create images",
        image_model=Gemini.PRO  # Enable image generation
    )

    response = image_agent.run("Create an image of a futuristic cityscape")

    if response.has_files():
        for img in response.files:
            print(f"Image: {img.url}")
            img.download("./images/city.png")
    ```

    ---

    ## File Output

    Enable agents to generate documents like PDFs, DOCX, CSV, and more.

    ### Enable File Output

    ```python
    agent = studio.create_agent(
        name="Doc Generator",
        provider="gpt-4o",
        role="Document creator",
        file_output=True  # Enable file generation
    )
    ```

    ### Supported File Types

    | Format | Description | Use Cases |
    |--------|-------------|-----------|
    | PDF | Portable Document | Reports, invoices, certificates |

_(truncated)_



    Enable agents to generate files (PDFs, DOCX, CSV) and images during conversations. Outputs are returned as downloadable artifacts.

    ## Quick Start

    ```python
    from lyzr import Studio
    from lyzr.image_models import Gemini, DallE

    studio = Studio(api_key="your-api-key")

    # File generation
    file_agent = studio.create_agent(
        name="Report Generator",
        provider="gpt-4o",
        role="Report creator",
        goal="Generate professional reports",
        file_output=True  # Enable file generation
    )

    response = file_agent.run("Create a Q4 sales report in PDF format")

    if response.has_files():
        for file in response.files:
            print(f"Generated: {file.name} ({file.format_type})")
            file.download("./reports/q4_sales.pdf")

    # Image generation
    image_agent = studio.create_agent(
        name="Image Creator",
        provider="gpt-4o",
        role="Visual designer",
        goal="Create images",
        image_model=Gemini.PRO  # Enable image generation
    )

    response = image_agent.run("Create an image of a futuristic cityscape")

    if response.has_files():
        for img in response.files:
            print(f"Image: {img.url}")
            img.download("./images/city.png")
    ```

    ---

    ## File Output

    Enable agents to generate documents like PDFs, DOCX, CSV, and more.

    ### Enable File Output

    ```python
    agent = studio.create_agent(
        name="Doc Generator",
        provider="gpt-4o",
        role="Document creator",
        file_output=True  # Enable file generation
    )
    ```

    ### Supported File Types

    | Format | Description | Use Cases |
    |--------|-------------|-----------|
    | PDF | Portable Document | Reports, invoices, certificates |

_(truncated)_


## ADK: file-image-output/image-generation

Source: `file-image-output/image-generation.mdx`

    Enable agents to generate images using Google Gemini or OpenAI DALL-E models. Images are returned as downloadable artifacts.

    ## Quick Start

    ```python
    from lyzr import Studio
    from lyzr.image_models import Gemini, DallE

    studio = Studio(api_key="your-api-key")

    # Create agent with image generation
    agent = studio.create_agent(
        name="Image Creator",
        provider="gpt-4o",
        role="Visual designer",
        goal="Create images from descriptions",
        image_model=Gemini.PRO  # Enable image generation
    )

    # Generate an image
    response = agent.run("Create an image of a futuristic city at sunset")

    # Access generated images
    if response.has_files():
        for img in response.files:
            print(f"Image URL: {img.url}")
            img.download("./images/city.png")
    ```

    ---

    ## Image Models

    ### Google Gemini

    ```python
    from lyzr.image_models import Gemini

    # Available Gemini models
    Gemini.PRO     # gemini/gemini-3-pro-image-preview - High quality
    Gemini.FLASH   # gemini/gemini-2.5-flash-image - Fast generation
    ```

    ### OpenAI DALL-E

    ```python
    from lyzr.image_models import DallE

    # Available DALL-E models
    DallE.DALL_E_3      # dall-e-3 - Highest quality
    DallE.DALL_E_2      # dall-e-2 - Standard quality
    DallE.GPT_IMAGE_1   # gpt-image-1 - GPT-based
    DallE.GPT_IMAGE_1_5 # gpt-image-1.5 - Enhanced GPT-based
    ```

    ---

    ## Enabling Image Generation

    ### At Agent Creation

    ```python
    from lyzr.image_models import Gemini

    agent = studio.create_agent(
        name="Image Agent",
        provider="gpt-4o",
        role="Image creator",
        image_model=Gemini.PRO  # Use Gemini PRO
    )
    ```

    ### Change I

_(truncated)_
