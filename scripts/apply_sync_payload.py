#!/usr/bin/env python3
"""
Apply a sync payload from the ADK-docs-sync workflow.
Payload: {"skills": [{"skill_name": "...", "new_skill": bool, "full_content"?: str, "section_updates"?: [...]}]}
Skills live under repo_root/skills/<skill_name>/SKILL.md.
Otherwise: run apply_skill_updates.py with section_updates.
"""
import json
import subprocess
import sys
from pathlib import Path

SKILLS_DIR = "skills"


def main():
    if len(sys.argv) < 3:
        print("Usage: apply_sync_payload.py <repo_root> <payload_json|@payload.json>", file=sys.stderr)
        sys.exit(1)
    repo_root = Path(sys.argv[1]).resolve()
    payload_arg = sys.argv[2]
    if payload_arg.startswith("@"):
        payload = json.loads(Path(payload_arg[1:]).read_text(encoding="utf-8"))
    else:
        payload = json.loads(payload_arg)
    skills = payload.get("skills", [])
    if not skills:
        print("No skills in payload", file=sys.stderr)
        sys.exit(0)
    scripts_dir = Path(__file__).resolve().parent
    for item in skills:
        skill_name = item.get("skill_name")
        if not skill_name:
            continue
        skill_dir = repo_root / SKILLS_DIR / skill_name
        if item.get("new_skill") and item.get("full_content"):
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(item["full_content"].strip() + "\n", encoding="utf-8")
            print(f"Wrote new skill: {SKILLS_DIR}/{skill_name}/SKILL.md")
        elif item.get("section_updates"):
            skill_path = skill_dir / "SKILL.md"
            if not skill_path.exists():
                print(f"SKILL.md not found: {skill_path}", file=sys.stderr)
                continue
            updates_json = json.dumps({"updates": item["section_updates"]})
            subprocess.run(
                [sys.executable, str(scripts_dir / "apply_skill_updates.py"), str(skill_dir), updates_json],
                check=True,
                cwd=str(repo_root),
            )
            print(f"Applied {len(item['section_updates'])} update(s) to {skill_name}")


if __name__ == "__main__":
    main()
