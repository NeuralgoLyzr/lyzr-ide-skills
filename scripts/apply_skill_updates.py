#!/usr/bin/env python3
"""
Apply validated patch hunks to mapped sections in SKILL.md.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from sync_patch_apply import apply_patch_series


def extract_frontmatter(content: str) -> tuple[str, str]:
    if not content.strip().startswith("---"):
        return "", content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return "", content
    return "---" + parts[1] + "---", parts[2].lstrip("\n")


def is_balanced_fenced_code(content: str) -> bool:
    return content.count("```") % 2 == 0


def content_has_invalid_headings(content: str, target_level: int) -> bool:
    in_fence = False
    for line in content.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s+", line)
        if m and len(m.group(1)) <= target_level:
            return True
    return False


def _extract_section_indices(lines: list[str], heading_text: str) -> tuple[int, int, int] | None:
    headings: list[tuple[int, str, int]] = []
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,6})\s+", line)
        if m:
            headings.append((i, line.strip(), len(m.group(1))))
    for idx, (line_idx, text, level) in enumerate(headings):
        if text != heading_text:
            continue
        content_start = line_idx + 1
        content_end = len(lines)
        for next_idx in range(idx + 1, len(headings)):
            if headings[next_idx][2] <= level:
                content_end = headings[next_idx][0]
                break
        return content_start, content_end, level
    return None


def _apply_hunks(section_text: str, patches: list[dict], heading: str) -> tuple[str | None, str | None]:
    result, err = apply_patch_series(section_text, patches)
    if err:
        return None, f"{heading}: {err}"
    return result, None


def _changed_line_count(old: str, new: str) -> int:
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    changed = 0
    limit = max(len(old_lines), len(new_lines))
    for i in range(limit):
        a = old_lines[i] if i < len(old_lines) else ""
        b = new_lines[i] if i < len(new_lines) else ""
        if a != b:
            changed += 1
    return changed


def apply_updates(
    skill_path: Path,
    updates: list[dict],
    allow_new_sections: bool = False,
    max_changed_lines: int = 120,
) -> int:
    raw = skill_path.read_text(encoding="utf-8")
    front, body = extract_frontmatter(raw)
    lines = body.split("\n")
    replacements: list[tuple[int, int, list[str]]] = []
    applied_count = 0

    for item in updates:
        if not isinstance(item, dict):
            continue
        heading = str(item.get("section_heading", "")).strip()
        patches = item.get("patches", [])
        if not heading or not isinstance(patches, list) or not patches:
            continue
        section_idx = _extract_section_indices(lines, heading)
        if section_idx is None:
            if allow_new_sections:
                lines.append("")
                lines.append(heading if heading.startswith("#") else f"## {heading}")
                lines.append("")
                section_idx = _extract_section_indices(lines, heading if heading.startswith("#") else f"## {heading}")
                if section_idx is None:
                    continue
            else:
                print(f"Heading not found, skipping: {heading}", file=sys.stderr)
                continue
        start, end, heading_level = section_idx
        old_text = "\n".join(lines[start:end]).strip()
        new_text, err = _apply_hunks(old_text, patches, heading)
        if err:
            print(err, file=sys.stderr)
            continue
        if new_text is None or new_text == old_text:
            continue
        if not is_balanced_fenced_code(new_text):
            print(f"{heading}: skipping due to unbalanced code fences", file=sys.stderr)
            continue
        if content_has_invalid_headings(new_text, heading_level):
            print(f"{heading}: skipping due to invalid heading level in patched content", file=sys.stderr)
            continue
        changed_lines = _changed_line_count(old_text, new_text)
        if changed_lines > max_changed_lines:
            print(
                f"{heading}: skipping because patch changed {changed_lines} lines (limit {max_changed_lines})",
                file=sys.stderr,
            )
            continue
        leading_blanks = 0
        for i in range(start, min(end, len(lines))):
            if lines[i].strip():
                break
            leading_blanks += 1
        trailing_blanks = 0
        for i in range(end - 1, start - 1, -1):
            if lines[i].strip():
                break
            trailing_blanks += 1
        if leading_blanks == 0:
            leading_blanks = 1
        if trailing_blanks == 0:
            trailing_blanks = 1
        new_lines = [""] * leading_blanks + new_text.split("\n") + [""] * trailing_blanks
        replacements.append((start, end, new_lines))
        applied_count += 1

    replacements.sort(key=lambda x: x[0], reverse=True)
    for start, end, new_lines in replacements:
        lines[start:end] = new_lines

    new_body = "\n".join(lines)
    result = (front + "\n\n" + new_body) if front else new_body
    if result == raw:
        return 0
    skill_path.write_text(result, encoding="utf-8")
    return applied_count


def _load_updates(payload: dict) -> list[dict]:
    if isinstance(payload.get("section_patches"), list):
        return payload.get("section_patches", [])
    if isinstance(payload.get("updates"), list):
        return payload.get("updates", [])
    if isinstance(payload, list):
        return payload
    return [payload]


def main():
    parser = argparse.ArgumentParser(description="Apply validated patch hunks to SKILL.md")
    parser.add_argument("skill_dir", type=Path, help="Skill directory (e.g. skills/lyzr-agent)")
    parser.add_argument("updates_json", type=str, help='JSON payload with updates/section_patches')
    parser.add_argument("--stdin", action="store_true", help="Read updates JSON from stdin")
    parser.add_argument("--allow-new-sections", action="store_true", help="Allow appending missing section heading")
    parser.add_argument(
        "--max-changed-lines",
        type=int,
        default=120,
        help="Reject a section patch that changes more than this many lines.",
    )
    args = parser.parse_args()

    skill_path = args.skill_dir / "SKILL.md"
    if not skill_path.exists():
        print(f"SKILL.md not found: {skill_path}", file=sys.stderr)
        sys.exit(1)

    payload = json.load(sys.stdin) if args.stdin else json.loads(args.updates_json)
    updates = _load_updates(payload)
    count = apply_updates(
        skill_path,
        updates,
        allow_new_sections=args.allow_new_sections,
        max_changed_lines=args.max_changed_lines,
    )
    if count == 0:
        print(f"No changes needed for {skill_path}")
    else:
        print(f"Applied {count} surgical patch update(s) to {skill_path}")


if __name__ == "__main__":
    main()
