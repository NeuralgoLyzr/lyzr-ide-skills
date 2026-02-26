#!/usr/bin/env python3
"""
Apply section-level updates to a SKILL.md file.
Reads JSON with updates[] (section_heading, content), replaces only those sections.
Preserves frontmatter and other sections unchanged.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def extract_frontmatter(content: str) -> tuple[str, str]:
    if not content.strip().startswith("---"):
        return "", content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return "", content
    return "---" + parts[1] + "---", parts[2].lstrip("\n")


def parse_sections(body: str) -> list[tuple[str, str]]:
    parts = re.split(r"(?m)^(## .+)$", body)
    sections = []
    if parts[0].strip():
        sections.append(("", parts[0].strip()))
    for i in range(1, len(parts) - 1, 2):
        heading = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections.append((heading, content))
    return sections


def serialize_sections(sections: list[tuple[str, str]]) -> str:
    out = []
    for heading, content in sections:
        if heading:
            out.append(heading)
            if content:
                out.append("")
                out.append(content)
        else:
            if content:
                out.append(content)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def normalize_heading(h: str) -> str:
    h = h.strip()
    if not h.startswith("#"):
        return "## " + h
    return h


def apply_updates(skill_path: Path, updates: list[dict]) -> None:
    raw = skill_path.read_text(encoding="utf-8")
    front, body = extract_frontmatter(raw)
    sections = parse_sections(body)
    updates_by_heading = {normalize_heading(u["section_heading"]): (u["section_heading"].strip(), u.get("content", "").strip()) for u in updates}
    new_sections = []
    seen = set()
    for heading, content in sections:
        if heading:
            key = normalize_heading(heading)
            seen.add(key)
            if key in updates_by_heading:
                _, content = updates_by_heading[key]
        new_sections.append((heading, content))
    for key, (raw_heading, content) in updates_by_heading.items():
        if key not in seen:
            new_sections.append((raw_heading if raw_heading.startswith("##") else "## " + raw_heading, content))
    new_body = serialize_sections(new_sections)
    result = (front + "\n\n" + new_body) if front else new_body
    skill_path.write_text(result, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Apply section updates to SKILL.md")
    parser.add_argument("skill_dir", type=Path, help="Skill directory (e.g. lyzr-agent)")
    parser.add_argument("updates_json", type=str, help='JSON: {"updates": [{"section_heading": "## ...", "content": "..."}]}')
    parser.add_argument("--stdin", action="store_true", help="Read updates JSON from stdin")
    args = parser.parse_args()

    skill_path = args.skill_dir / "SKILL.md"
    if not skill_path.exists():
        print(f"SKILL.md not found: {skill_path}", file=sys.stderr)
        sys.exit(1)

    if args.stdin:
        payload = json.load(sys.stdin)
    else:
        payload = json.loads(args.updates_json)

    updates = payload.get("updates", payload) if isinstance(payload.get("updates"), list) else payload
    if not isinstance(updates, list):
        updates = [payload]
    apply_updates(skill_path, updates)
    print(f"Applied {len(updates)} update(s) to {skill_path}")


if __name__ == "__main__":
    main()
