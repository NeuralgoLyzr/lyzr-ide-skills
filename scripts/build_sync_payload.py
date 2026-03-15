#!/usr/bin/env python3
"""
Build a sync payload from changed ADK doc files.
Reads doc-to-skill-mapping.yaml, fetches current skill content from ide_skills,
calls LLM with section-update prompt, outputs JSON payload for apply_sync_payload.
Requires: OPENAI_API_KEY or GEMINI_API_KEY; pyyaml.
Usage: build_sync_payload.py <ide_skills_root> <docs_root> <changed_files.json>
  changed_files.json: ["lyzr-adk/agents/creating-agents.mdx", ...]
Output: JSON to stdout with {"skills": [...]}
"""
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_mapping(ide_root: Path) -> dict:
    path = ide_root / "doc-to-skill-mapping.yaml"
    if not yaml:
        raise RuntimeError("PyYAML required: pip install pyyaml")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def strip_mdx(content: str) -> str:
    content = re.sub(r"<Warning[^>]*>.*?</Warning>", "", content, flags=re.DOTALL)
    content = re.sub(r"<Note[^>]*>.*?</Note>", "", content, flags=re.DOTALL)
    content = re.sub(r"<Card[^>]*>.*?</Card>", "", content, flags=re.DOTALL)
    content = re.sub(r"<CardGroup[^>]*>.*?</CardGroup>", "", content, flags=re.DOTALL)
    return content.strip()


def get_skill_section_content(skill_path: Path, section_headings: list[str]) -> str:
    if not skill_path.exists():
        return ""
    raw = skill_path.read_text(encoding="utf-8")
    if "---" in raw.split("\n")[0]:
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            raw = parts[2].lstrip()
    out = []
    for line in raw.split("\n"):
        if re.match(r"^## .+", line) and any(h in line for h in section_headings):
            out.append(line)
            continue
        if out and re.match(r"^## ", line):
            break
        if out:
            out.append(line)
    return "\n".join(out) if out else raw[:2000]


def call_llm_openai(prompt: str, api_key: str) -> str:
    try:
        import urllib.request
        body = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You output only valid JSON. No markdown code fence. Merge doc content into skill style. Output format: {\"updates\": [{\"section_heading\": \"## Exact Heading\", \"content\": \"markdown\"}]}"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode())
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return json.dumps({"updates": [], "_error": str(e)})


def main():
    if len(sys.argv) < 4:
        print("Usage: build_sync_payload.py <ide_skills_root> <docs_root> <changed_files.json>", file=sys.stderr)
        sys.exit(1)
    ide_root = Path(sys.argv[1]).resolve()
    docs_root = Path(sys.argv[2]).resolve()
    changed = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    if not isinstance(changed, list):
        changed = changed.get("files", [changed])
    mapping = load_mapping(ide_root)
    path_rules = mapping.get("path_prefix_rules", {})
    mappings_list = mapping.get("mappings", [])
    doc_to_skill = {}
    for m in mappings_list:
        doc_to_skill[m["doc_path"]] = m
    skills_updates = {}
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Set OPENAI_API_KEY or GEMINI_API_KEY", file=sys.stderr)
        sys.exit(1)
    for rel in changed:
        if not rel.endswith(".mdx"):
            continue
        doc_path = rel.replace("\\", "/")
        if "lyzr-adk/" in doc_path:
            doc_path = doc_path.split("lyzr-adk/", 1)[-1]
        if "documentation/" in doc_path:
            doc_path = doc_path.split("documentation/", 1)[-1]
            if doc_path.startswith("lyzr-adk/"):
                doc_path = doc_path.split("lyzr-adk/", 1)[-1]
        m = doc_to_skill.get(doc_path)
        if not m:
            prefix = doc_path.split("/")[0] if "/" in doc_path else doc_path.split(".")[0]
            skill = path_rules.get(prefix)
            if not skill:
                continue
            m = {"skill": skill, "sections": [{"skill_heading": "## Overview"}]}
        skill_name = m["skill"]
        sections = m.get("sections", [])
        section_headings = [s.get("skill_heading", "") for s in sections if s.get("skill_heading")]
        if not section_headings:
            section_headings = ["## Overview"]
        doc_full = docs_root / "lyzr-adk" / doc_path if (docs_root / "lyzr-adk").exists() else docs_root / doc_path
        if not doc_full.exists():
            doc_full = docs_root / doc_path
        if not doc_full.exists():
            continue
        doc_content = strip_mdx(doc_full.read_text(encoding="utf-8"))[:8000]
        skill_path = ide_root / "skills" / skill_name / "SKILL.md"
        current = get_skill_section_content(skill_path, section_headings) if section_headings else ""
        prompt = f"""doc_path: {doc_path}
skill: {skill_name}
section_heading(s) to update: {json.dumps(section_headings)}

Current content of the section(s) in the skill file:
---
{current[:3000]}
---

New doc content (from LYZR ADK):
---
{doc_content}
---

Output valid JSON only: {{"updates\": [{{\"section_heading\": \"## Exact Heading\", \"content\": \"markdown content\"}}]}}"""
        raw_out = call_llm_openai(prompt, api_key)
        if raw_out.startswith("```"):
            raw_out = re.sub(r"^```\w*\n?", "", raw_out)
            raw_out = re.sub(r"\n?```$", "", raw_out)
        try:
            parsed = json.loads(raw_out)
        except json.JSONDecodeError:
            parsed = {"updates": []}
        updates = parsed.get("updates", [])
        if not updates:
            continue
        if skill_name not in skills_updates:
            skills_updates[skill_name] = {"skill_name": skill_name, "new_skill": False, "section_updates": []}
        for u in updates:
            if u not in skills_updates[skill_name]["section_updates"]:
                skills_updates[skill_name]["section_updates"].append(u)
    result = {"skills": list(skills_updates.values())}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
