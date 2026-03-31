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
    # If the LLM supplies a short `old` snippet, we still try an old-only unique
    # replacement as long as we can prove uniqueness (count == 1).
    return True


def _old_variants(old: str) -> list[str]:
    seen: list[str] = []
    candidates = [
        old,
        old.rstrip("\n"),
        old.rstrip(),
        old + "\n" if old and not old.endswith("\n") else old,
        old.lstrip("\n") if old.startswith("\n") else old,
        old.lstrip(),
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
        # Insert-only patch: allow empty before/old/after when the section is empty (or whitespace).
        # This is used to populate newly created `## ADK: ...` sections deterministically.
        if not needle and old == "" and new.strip() and not text.strip():
            text = new
            continue

        if not needle and not old:
            return None, f"patch[{idx}] has empty anchor"

        needle_count = text.count(needle) if needle else 0
        if needle and needle_count == 1:
            text = text.replace(needle, before + new + after, 1)
            continue
        if needle and needle_count > 1:
            return None, f"patch[{idx}] anchor match count={needle_count}, expected 1"

        # Fallback: old-only unique replacement.
        # This helps when context_before/context_after changed slightly (whitespace/phrasing)
        # but the exact `old` snippet is still present exactly once.
        if old and _old_eligible_for_unique_replace(old):
            applied = False
            best_variant_count: int | None = None
            for variant in _old_variants(old):
                vc = text.count(variant)
                if best_variant_count is None:
                    best_variant_count = vc
                if vc == 1:
                    text = text.replace(variant, new, 1)
                    applied = True
                    break
            if applied:
                continue

            if needle:
                old_exact = text.count(old)
                return (
                    None,
                    "patch[{}] anchor match count=0, expected 1 (needle), "
                    "and no unique old-only replacement found (old_exact_count={}, any_old_variant_unique_count=false)".format(
                        idx,
                        old_exact,
                    ),
                )

        if needle:
            return None, f"patch[{idx}] anchor match count=0, expected 1"
        if old:
            oc = text.count(old)
            if oc == 0:
                return None, f"patch[{idx}] anchor match count=0, expected 1"
            return None, f"patch[{idx}] old text match count={oc}, expected 1"
        return None, f"patch[{idx}] anchor match count=0, expected 1"

    return text, None
