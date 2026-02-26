# LLM prompt: Section-level skill update

Use this prompt when the ADK doc has changed and you need to output **only** the updated content for the affected skill section(s). The LLM must not return the entire SKILL.md.

## System prompt (optional)

You are updating a Cursor Agent Skill from LYZR ADK documentation. Output ONLY the replacement content for the affected skill section(s). Preserve the same heading level and format. Do not output the entire file. Use the same SKILL.md style: concise, code blocks with python, tables where the doc has tables. Strip any MDX/React components (e.g. Card, Warning) into plain markdown.

## User prompt template

```
doc_path: {{doc_path}}
skill: {{skill_name}}
section_heading(s) to update: {{section_headings}}

Current content of the section(s) in the skill file:
---
{{current_skill_section_content}}
---

New doc content (from LYZR ADK):
---
{{doc_content}}
---

Instructions: Output valid JSON only, no markdown code fence. Format:
{"updates": [{"section_heading": "## Exact Heading From Skill", "content": "markdown content for that section only"}]}

Merge the new doc content into the skill style. Update only what changed; keep the same structure. If the doc adds a new subsection, include it under the same section_heading or add a new object with the new section_heading. Do not include the frontmatter or other sections.
```

## Expected output (JSON)

```json
{
  "updates": [
    {
      "section_heading": "## Step 2: Create an Agent",
      "content": "Updated markdown for this section only..."
    }
  ]
}
```

- `section_heading`: Must match the skill file exactly (e.g. `## Error Handling`, `## Contexts`).
- `content`: Full markdown body for that section (no extra `##` in the content; the applier uses section_heading to replace).

## New skill (full SKILL.md)

When the doc path maps to a **new** skill (e.g. new folder in ADK), use a separate prompt that asks for a **full** SKILL.md:

- Input: full doc content, skill name (e.g. `lyzr-file-image-output`), instruction to output one markdown document with YAML frontmatter (name, description, triggers, version, author) and body (Overview, Setup, step-by-step sections, Best Practices). Strip MDX. Keep under ~500 lines.
- Output: full file content as a single markdown string (or JSON `{"full_content": "..."}`).
