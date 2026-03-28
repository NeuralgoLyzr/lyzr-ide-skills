# ADK–Skills sync scripts

Skills live under **skills/** (`skills/<skill_name>/SKILL.md`). Mapping: **doc-to-skill-mapping.yaml** at repo root.

## Flow

1. **build_sync_payload.py** — For each mapped `(skill, section)` affected by changed `.mdx` files, calls the LLM to produce **patch hunks** (`context_before`, `old`, `new`, `context_after`). Output: `{"skills":[{"skill_name","new_skill","section_patches":[...]}]}`.
2. **apply_sync_payload.py** — Used by GitHub Actions on `ide_skills` after `repository_dispatch`; runs **apply_skill_updates.py** per skill (or writes new skill `full_content`).
3. **apply_skill_updates.py** — Applies hunks only inside the matching `##` / `###` section; uses **sync_patch_apply.py** (full anchor, then safe `old`-only fallback).

### LLM keys (OpenAI vs Gemini)

- **OPENAI_API_KEY** — Chat Completions (`https://api.openai.com/v1/chat/completions`). Default model `SYNC_LLM_MODEL=gpt-4o`.
- **GEMINI_API_KEY** — Google Generative Language API (`generateContent`). Default model `SYNC_LLM_MODEL=gemini-1.5-flash` (override with a Gemini model id; `provider/model` slugs use the segment after `/`).

If **both** keys are set, OpenAI is used unless **SYNC_LLM_PROVIDER=gemini** (repository variable or env).

### Local driver

**run_local_sync.py** — Builds payload and optionally applies (same logic as CI).

```bash
export OPENAI_API_KEY=...   # or GEMINI_API_KEY (+ optional SYNC_LLM_PROVIDER=gemini)

python scripts/run_local_sync.py --docs-dir /path/to/documentation --files "lyzr-adk/overview.mdx"
python scripts/run_local_sync.py --docs-dir /path/to/documentation --full-sync
python scripts/run_local_sync.py --docs-dir /path/to/documentation --full-sync --apply
```

Artifacts: `scripts/.local_sync_changed.json`, `scripts/.local_sync_payload.json` (gitignored).

### build_sync_payload.py

```bash
python scripts/build_sync_payload.py <ide_skills_root> <docs_root> <changed_files.json>
```

`changed_files.json` is a JSON array of paths like `lyzr-adk/agents/overview.mdx` (relative to `docs_root` or including `lyzr-adk/`). Loads **.env** from `ide_skills` root for keys when not set in the shell.

### apply_skill_updates.py

```bash
python scripts/apply_skill_updates.py skills/lyzr-agent '{"section_patches":[{"section_heading":"## ...","patches":[...]}]}'
```

### apply_sync_payload.py

```bash
python scripts/apply_sync_payload.py <repo_root> @payload.json
```

### Fallbacks and limits

- LLM patch validation fails twice → optional **doc-append** block (unless `SYNC_DISABLE_DOC_APPEND_FALLBACK=1`). The append is **small by default** so `repository_dispatch` stays under GitHub’s **65535-byte `client_payload`** limit.
- **`GITHUB_DISPATCH_SKILLS_JSON_MAX`** (default `52000`) — UTF-8 size of `{"skills":[...]}` before emit; larger payloads **drop section patches** (largest first) until under cap so CI dispatch does not return **422 client_payload is too large**.
- **`SYNC_FALLBACK_DOC_MAX_CHARS`** (default `500`) — max doc excerpt in the append fallback.
- `SYNC_STRICT_DOC_LINES=1` — stricter check that new lines trace to doc text.
- Unmapped `.mdx` paths are skipped (warnings on stderr).

### CI: OpenAI `400 Bad Request` (local works, Actions fails)

Same script runs locally and in CI; differences are **secrets**, **`SYNC_LLM_MODEL`**, and **org model access**.

- Use a model your key can call on Chat Completions (e.g. `gpt-4o`). Reasoning-only models may need different parameters.
- Set **`SYNC_OPENAI_USE_MAX_COMPLETION_TOKENS=1`** (or use a non–o-series model) if errors mention `max_tokens` / `max_completion_tokens`.
- Prefer **`GEMINI_API_KEY`** + **`SYNC_LLM_PROVIDER=gemini`** + **`SYNC_LLM_MODEL=gemini-1.5-flash`** if OpenAI is blocked in CI.

When every LLM call fails, the builder falls back to many small doc-append patches; if the API is fixed, surgical patches stay small and dispatch is reliable.
