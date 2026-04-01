---
name: lyzr-assets
description: Upload, store, and manage file assets (PDF, DOCX, images). Extract text from documents; list, get, and delete assets via the API. **Total Endpoints:** 4
license: Apache-2.0
allowed-tools: Studio assets-api upload list-assets
triggers:
- lyzr assets
- lyzr file upload
- upload assets lyzr
- lyzr document upload
metadata:
  author: LYZR AI
  version: "1.0.0"
  category: assets
---

# Lyzr Assets Skill

## Instructions

1. Use this skill for LYZR asset upload, listing, retrieval, deletion, and text extraction via the ADK assets API (four endpoints).
2. Require `LYZR_API_KEY`; never expose keys in examples.
3. Extend **Step 1** and following sections only from ADK documentation—do not invent endpoint paths or response shapes.
4. Preserve `##` headings used in `doc-to-skill-mapping.yaml` when documentation sync runs.

## Overview

Upload, store, and manage file assets (PDF, DOCX, images). Extract text from documents; list, get, and delete assets via the API. **Total Endpoints:** 4

---

## Setup

```bash
pip install lyzr-adk
export LYZR_API_KEY="your-api-key"
```

---

## Step 1: (Add steps)

(Add SDK steps here.)
