# ADK–Skills sync scripts

All skills live under **skills/** (`skills/<skill_name>/SKILL.md`). Scripts and mapping stay at repo root.

## apply_skill_updates.py

Applies section-level updates to a SKILL.md file. Used by the sync workflow after the LLM returns section replacements.

**Usage:**

```bash
# From ide_skills repo root; skill_dir is under skills/
python scripts/apply_skill_updates.py <skill_dir> '<json>'

# Example (skills live in skills/<name>/)
python scripts/apply_skill_updates.py skills/lyzr-agent '{"updates":[{"section_heading":"## Error Handling","content":"..."}]}'

# Read JSON from stdin
echo '{"updates":[...]}' | python scripts/apply_skill_updates.py skills/lyzr-agent --stdin
```

**Input JSON:** `{"updates": [{"section_heading": "## Exact Heading", "content": "markdown body"}]}`

- Replaces only the section(s) with matching `section_heading`.
- If a section_heading is not found, that update is appended as a new section.
- Preserves frontmatter and all other sections.

## apply_sync_payload.py

Applies the full payload from the ADK-docs-sync workflow (repository_dispatch). Writes new skills or runs apply_skill_updates per skill. All skills are under `repo_root/skills/<skill_name>/SKILL.md`.

**Usage:** `python scripts/apply_sync_payload.py <repo_root> @payload.json`

## llm_section_update_prompt.md

Prompt template and I/O contract for the LLM when doing section-level updates. The workflow should substitute `doc_path`, `skill_name`, `section_headings`, `current_skill_section_content`, and `doc_content` into the user prompt, then call the LLM and parse the JSON response.

## doc-to-skill-mapping.yaml

Location: `../doc-to-skill-mapping.yaml` (ide_skills root). Maps each ADK doc path to a skill and optional section headings. Used by the sync workflow to decide which skill to update and which sections to pass to the LLM.

## build_sync_payload.py

Builds the JSON payload for the sync workflow by reading changed ADK doc paths, loading the mapping, and calling the LLM (OpenAI) to produce section-level updates. Used by the documentation repo workflow.

**Usage:** `python scripts/build_sync_payload.py <ide_skills_root> <docs_root> <changed_files.json>`

**Requires:** `OPENAI_API_KEY` or `GEMINI_API_KEY`; `pip install pyyaml`

**Output:** JSON with `{"skills": [{"skill_name": "...", "new_skill": false, "section_updates": [...]}]}` to stdout.
