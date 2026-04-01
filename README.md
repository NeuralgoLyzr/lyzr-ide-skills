# LYZR IDE Skills

Cursor skills for the **LYZR ADK** Python SDK (`lyzr-adk`). This repo keeps `skills/*/SKILL.md` aligned with the official ADK documentation and automation scripts.

## Use with GitAgent (fastest)

Run this in your terminal (Cursor, Claw, or any shell) to pull this repo into your project as a git agent:

```bash
npx @open-gitagent/gitagent@0.1.7 run -r https://github.com/NeuralgoLyzr/lyzr-ide-skills -a claude
```

Then use the same skills in your IDE or agent workflow as usual.

## What’s in this repo

- **`skills/`** — One folder per skill (`lyzr-agent`, `lyzr-rag`, `lyzr-memory`, `lyzr-guardrails`, `lyzr-file-image-output`, `lyzr-assets`). Each contains `SKILL.md` with YAML frontmatter and instructions.
- **`doc-to-skill-mapping.yaml`** — Maps ADK doc paths to skill sections for doc-sync.
- **`scripts/`** — Build and apply sync payloads (`run_local_sync.py`, `build_sync_payload.py`, `apply_sync_payload.py`, etc.).
- **`.github/workflows/`** — CI that applies incoming sync payloads from your docs pipeline.

## How to sync from ADK docs locally

From this repo root:

```bash
python3 scripts/run_local_sync.py --docs-dir /path/to/documentation --full-sync
```

To apply changes into `skills/*/SKILL.md`:

```bash
python3 scripts/run_local_sync.py --docs-dir /path/to/documentation --full-sync --apply
```

Requires `OPENAI_API_KEY` or `GEMINI_API_KEY` (or `.env` in the repo root) for LLM-driven section patches.

## Contributing

Contributions are welcome. Please:

- Keep changes focused (skills, mapping, or scripts).
- Run a local sync against your docs branch when changing skill content that should track ADK docs.
- Open a PR with a short description of what changed and why.

## License

This repository is licensed under the **Apache License 2.0** — see [`LICENSE`](LICENSE). This is **not** the MIT License.

Skill frontmatter uses `license: Apache-2.0` to match the repository; the SPDX identifier is `Apache-2.0`.
