#!/usr/bin/env python3
"""
Apply a sync payload from the ADK-docs-sync workflow.
Payload: {"skills": [{"skill_name": "...", "new_skill": bool, "full_content"?: str, "section_patches"?: [...]}]}
Skills live under repo_root/skills/<skill_name>/SKILL.md.
Otherwise: run apply_skill_updates.py with section_patches.
"""
import json
import subprocess
import sys
from pathlib import Path

SKILLS_DIR = "skills"


def _validate_section_patches(skill_name: str, section_patches: list[dict]) -> list[str]:
    errors: list[str] = []
    for idx, section in enumerate(section_patches):
        if not isinstance(section, dict):
            errors.append(f"{skill_name}: section_patches[{idx}] must be an object.")
            continue
        heading = str(section.get("section_heading", "")).strip()
        patches = section.get("patches", [])
        if not heading:
            errors.append(f"{skill_name}: section_patches[{idx}] missing section_heading.")
        if not isinstance(patches, list) or not patches:
            errors.append(f"{skill_name}:{heading or '<missing-heading>'} missing patches[].")
            continue
        for p_idx, patch in enumerate(patches):
            if not isinstance(patch, dict):
                errors.append(f"{skill_name}:{heading}: patch[{p_idx}] must be an object.")
                continue
            before = str(patch.get("context_before", ""))
            old = str(patch.get("old", ""))
            after = str(patch.get("context_after", ""))
            if not (before or old or after):
                errors.append(f"{skill_name}:{heading}: patch[{p_idx}] has empty anchor context.")
    return errors


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
        else:
            section_patches = item.get("section_patches", item.get("section_updates", []))
            if not section_patches:
                continue
            validation_errors = _validate_section_patches(skill_name, section_patches)
            if validation_errors:
                for err in validation_errors:
                    print(err, file=sys.stderr)
                continue
            skill_path = skill_dir / "SKILL.md"
            if not skill_path.exists():
                print(f"SKILL.md not found: {skill_path}", file=sys.stderr)
                continue
            updates_json = json.dumps({"section_patches": section_patches})
            subprocess.run(
                [sys.executable, str(scripts_dir / "apply_skill_updates.py"), str(skill_dir), updates_json],
                check=True,
                cwd=str(repo_root),
            )
            print(f"Applied {len(section_patches)} patch section update(s) to {skill_name}")


if __name__ == "__main__":
    main()
