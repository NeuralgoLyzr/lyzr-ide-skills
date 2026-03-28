"""
Shared patch application for ADK → SKILL sync.
Tries full anchor (context_before + old + context_after) first, then safe fallbacks
so LLM-slightly-wrong context does not block surgical updates.
"""
from __future__ import annotations

MIN_OLD_ONLY_CHARS = 14


def normalize_patch_field(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _old_eligible_for_unique_replace(old: str) -> bool:
    o = old.strip()
    if len(o) < MIN_OLD_ONLY_CHARS:
        return False
    if "\n" in old:
        return True
    return len(o) >= 22


def _old_variants(old: str) -> list[str]:
    seen: list[str] = []
    candidates = [
        old,
        old.rstrip("\n"),
        old + "\n" if old and not old.endswith("\n") else old,
        old.lstrip("\n") if old.startswith("\n") else old,
    ]
    for c in candidates:
        c = normalize_patch_field(c)
        if c and c not in seen:
            seen.append(c)
    return seen


def apply_patch_series(section_text: str, patches: list[dict]) -> tuple[str | None, str | None]:
    text = normalize_patch_field(section_text)
    for idx, patch in enumerate(patches):
        if not isinstance(patch, dict):
            return None, f"patch[{idx}] is not an object"
        before = normalize_patch_field(str(patch.get("context_before", "")))
        old = normalize_patch_field(str(patch.get("old", "")))
        after = normalize_patch_field(str(patch.get("context_after", "")))
        new = normalize_patch_field(str(patch.get("new", "")))
        needle = before + old + after
        if not needle and not old:
            return None, f"patch[{idx}] has empty anchor"

        if needle:
            count = text.count(needle)
            if count == 1:
                text = text.replace(needle, before + new + after, 1)
                continue
            if count > 1:
                return None, f"patch[{idx}] anchor match count={count}, expected 1"

        if old and _old_eligible_for_unique_replace(old):
            applied = False
            for variant in _old_variants(old):
                vc = text.count(variant)
                if vc == 1:
                    text = text.replace(variant, new, 1)
                    applied = True
                    break
            if applied:
                continue

        if needle:
            return None, f"patch[{idx}] anchor match count=0, expected 1"
        if old:
            oc = text.count(old)
            if oc == 0:
                return None, f"patch[{idx}] anchor match count=0, expected 1"
            return None, f"patch[{idx}] old text match count={oc}, expected 1 (or old too short for fallback)"
        return None, f"patch[{idx}] anchor match count=0, expected 1"

    return text, None
