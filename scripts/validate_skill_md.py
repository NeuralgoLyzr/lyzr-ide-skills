#!/usr/bin/env python3
"""
Validate canonical SKILL.md YAML frontmatter for new-skill LLM output.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


REQUIRED_TOP = ("name", "description", "license", "allowed-tools", "triggers", "metadata")
REQUIRED_META = ("author", "version", "category")


def validate_skill_frontmatter(content: str) -> tuple[bool, str]:
    if yaml is None:
        return False, "PyYAML required: pip install pyyaml"
    raw = content.strip()
    if not raw.startswith("---"):
        return False, "SKILL.md must start with YAML frontmatter (---)"
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return False, "Malformed frontmatter (missing closing ---)"
    fm_raw = parts[1].strip()
    body = parts[2].lstrip("\n")
    try:
        data = yaml.safe_load(fm_raw)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML frontmatter: {e}"
    if not isinstance(data, dict):
        return False, "Frontmatter must be a YAML mapping"
    for key in REQUIRED_TOP:
        if key not in data:
            return False, f"Frontmatter missing required key: {key}"
    if not isinstance(data.get("allowed-tools"), list):
        return False, "allowed-tools must be a YAML list"
    if not isinstance(data.get("triggers"), list):
        return False, "triggers must be a YAML list"
    meta = data.get("metadata")
    if not isinstance(meta, dict):
        return False, "metadata must be a YAML mapping"
    for mk in REQUIRED_META:
        if mk not in meta:
            return False, f"metadata missing required key: {mk}"
    if "## Instructions" not in body:
        return False, "Body must include a ## Instructions section after frontmatter"
    return True, ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate SKILL.md frontmatter + Instructions section")
    parser.add_argument("skill_md", type=Path, help="Path to SKILL.md")
    args = parser.parse_args()
    text = args.skill_md.read_text(encoding="utf-8")
    ok, err = validate_skill_frontmatter(text)
    if ok:
        print("OK", args.skill_md)
        sys.exit(0)
    print(err, file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
