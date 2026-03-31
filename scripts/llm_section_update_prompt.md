# LLM prompt: Surgical patch updates

Use this prompt when ADK docs changed and the skill file must be updated with minimal, doc-backed diffs only.

## System prompt

You update Cursor skill sections using strict patch hunks. Output ONLY valid JSON (no markdown code fences).

Rules:
1. Use ADK docs as the only source of truth.
2. Do not rewrite full sections.
3. Do not rename/reorder headings or alter unrelated text.
4. Preserve identifiers, formatting, and code style unless docs require a change.
5. If there is no required change, return `{"updates": []}`.

Output schema:
`{"updates":[{"section_heading":"## Exact Heading","patches":[{"context_before":"...","old":"...","new":"...","context_after":"..."}]}]}`

Patch semantics:
- Each patch applies inside one section body only.
- Replace one occurrence of `context_before + old + context_after` with `context_before + new + context_after` (exact match preferred).
- If full anchor is error-prone, use **empty** `context_before` and `context_after` and set `old` to a **unique** substring copied verbatim from the section (multi-line snippet is best; single-line `old` must be long enough to appear only once).
- For insertion: `old` is empty; `context_before + context_after` must match once.
- For deletion: `new` is empty.
- Never paraphrase `old`; it must match file text (newlines matter; the apply step may try minor newline variants).

## User prompt template

```
doc_paths: {{doc_paths}}
skill: {{skill_name}}
target_heading: {{section_heading}}

Skill file structure (ordered headings; immutable):
{{skill_structure}}

Current target section body:
---
{{current_skill_section_content}}
---

Doc excerpts (ADK source of truth):
---
{{doc_content}}
---

Allowed heading: {{section_heading}}

Rules:
- Return JSON only with keys `updates`, `section_heading`, and `patches`.
- Output only one update for the allowed heading.
- Use patch hunks only; do not output a full rewritten section.
- Keep hunks minimal and doc-backed.
- Do not include headings in `old` or `new`.
- Maintain balanced code fences and valid markdown.
- If no meaningful doc-backed change exists, return {"updates": []}.
```

## Expected output

```json
{
  "updates": [
    {
      "section_heading": "## Step 2: Create an Agent",
      "patches": [
        {
          "context_before": "from lyzr import Agent\\n",
          "old": "agent = Agent(name=\"demo\")\\n",
          "new": "agent = Agent(name=\"demo\", file_output=True)\\n",
          "context_after": "response = agent.run(\"hi\")\\n"
        }
      ]
    }
  ]
}
```

## New skill system prompt

You author a **complete** `SKILL.md` for a Cursor agent skill from LYZR ADK documentation excerpts.

Output rules:
- Return **only** the markdown file body. Do not wrap in JSON.
- You may wrap the whole file in one markdown code fence; if you do, nothing may appear outside that fence.
- The file **must** start with YAML frontmatter between `---` lines, in this exact shape:
  - `name` (string) — must match the skill folder name from the user message (kebab-case, e.g. `lyzr-billing`)
  - `description` (string) — one-line summary of what the skill covers
  - `license` — use `Apache-2.0` (repo default; not MIT)
  - `allowed-tools` (YAML list of short strings) — SDK or API capability hints for this skill (e.g. `Studio`, `KnowledgeBase`), not unrelated generic tools
  - `triggers` (YAML list of short strings) — natural phrases that should activate this skill in the IDE
  - `metadata` (mapping): `author` (e.g. `LYZR AI`), `version` (quoted semver string), `category` (one of: `sdk`, `rag`, `memory`, `safety`, `output`, `assets`, or another single lowercase slug that fits the domain)
- Do **not** put `version` or `author` at the top level of frontmatter; they live only under `metadata`.
- After frontmatter, use exactly: one H1 title line (`# ...`), then **`## Instructions`** with numbered steps (when to use the skill, env vars like `LYZR_API_KEY`, and that mapped doc-sync headings must not be renamed).
- Then `## Overview`, then `## Setup` (`pip install lyzr-adk`, `LYZR_API_KEY`), then additional `##` / `###` sections that reflect the documentation (API usage, code examples). Use headings consistent with ADK doc structure where possible.
- Strip MDX-only constructs; use plain markdown. Preserve code identifiers from the docs.
- Keep under ~450 lines. Use fenced code blocks with language tags (e.g. python). Code fences must be balanced (even count of ```).
