#!/usr/bin/env python3
"""
Build a sync payload from changed ADK docs.
Outputs patch hunks scoped to mapped skill sections:
{"skills":[{"skill_name":"...","new_skill":false,"section_patches":[...]}]}
"""
import json
import os
import re
import sys
from pathlib import Path

from sync_patch_apply import apply_patch_series, normalize_patch_field as _normalize_patch_field
from validate_skill_md import validate_skill_frontmatter

try:
    import yaml
except ImportError:
    yaml = None

FALLBACK_SYSTEM_PROMPT = (
    "You output only valid JSON. No markdown code fence. "
    "Surgical edits only: change the smallest substring needed to align the skill section with the docs. "
    "Do not rewrite whole sections, reorder unrelated content, or add filler. "
    "Generate minimal patch hunks for a single skill section. "
    'Schema: {"updates":[{"section_heading":"## Exact Heading","patches":[{"context_before":"","old":"","new":"","context_after":""}]}]}. '
    'Return {"updates": []} when the section already matches the docs or no doc-backed change is required.'
)

MAX_DOC_BUNDLE_CHARS = 50000
MAX_SECTION_CHARS = 25000
MIN_DOC_LINE_LEN = 4
DEFAULT_GITHUB_DISPATCH_SKILLS_JSON_MAX = 52000


def _env_int(name: str, default: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _load_env_file(ide_root: Path) -> None:
    path = ide_root / ".env"
    if not path.is_file():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if not key or key in os.environ:
                continue
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            os.environ[key] = val
    except OSError:
        pass


def load_mapping(ide_root: Path) -> dict:
    path = ide_root / "doc-to-skill-mapping.yaml"
    if not yaml:
        raise RuntimeError("PyYAML required: pip install pyyaml")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def strip_mdx(content: str) -> str:
    content = re.sub(r"^---\n.*?\n---\n?", "", content, flags=re.DOTALL)
    content = re.sub(r"<Warning[^>]*>.*?</Warning>", "", content, flags=re.DOTALL)
    content = re.sub(r"<Note[^>]*>.*?</Note>", "", content, flags=re.DOTALL)
    content = re.sub(r"<Card[^>]*>.*?</Card>", "", content, flags=re.DOTALL)
    content = re.sub(r"<CardGroup[^>]*>.*?</CardGroup>", "", content, flags=re.DOTALL)
    return content.strip()


def _sanitize_doc_for_skill_section(doc_text: str) -> str:
    """
    Make doc-derived content safe to insert into a SKILL.md section body.

    We intentionally avoid fenced code blocks and markdown headings because apply_skill_updates
    rejects unbalanced ``` fences and headings at or above the section level.

    Strategy: strip MDX wrappers, then indent every line to make it a markdown code block.
    This preserves the raw doc text (doc-derived only) while preventing accidental headings/fences.
    """
    body = strip_mdx(doc_text).strip()
    if not body:
        return ""
    lines = body.splitlines()
    # Keep blank lines, but indent everything so headings/fences are inert.
    return "\n".join(("    " + ln) if ln else "" for ln in lines).rstrip()

def _heading_from_doc_path(doc_path: str) -> str:
    # Deterministic per-doc heading for unmapped docs.
    # Example: memory/add-memories.mdx -> "## ADK: memory/add-memories"
    base = doc_path.replace("\\", "/").strip().strip("/")
    if base.endswith(".mdx"):
        base = base[:-4]
    return f"## ADK: {base}"


def _doc_to_new_section_patch(section_heading: str, doc_paths: list[str], docs_texts: list[str]) -> dict:
    # Insert doc-backed content as a standalone section body.
    # apply_skill_updates will create the heading if missing (when allow-new-sections is enabled),
    # and sync_patch_apply supports inserting into an empty section with old=="".
    per_doc_max = _env_int("SYNC_UNMAPPED_DOC_PER_DOC_MAX_CHARS", 1800)
    max_total = _env_int("SYNC_UNMAPPED_DOC_SECTION_MAX_CHARS", 7000)
    parts: list[str] = []
    for dp, txt in zip(doc_paths, docs_texts):
        raw = strip_mdx(txt).strip()
        body = _sanitize_doc_for_skill_section(raw)
        if len(body) > per_doc_max:
            body = body[:per_doc_max].rstrip() + "\n\n_(truncated)_"
        parts.append(f"Source: `{dp}`\n\n{body}".strip())
    combined = "\n\n---\n\n".join(parts).strip()
    if len(combined) > max_total:
        combined = combined[:max_total].rstrip() + "\n\n_(truncated)_"
    new_body = combined
    return {
        "section_heading": section_heading,
        "patches": [
            {"context_before": "", "old": "", "new": new_body, "context_after": ""},
        ],
    }


def _doc_section_patches_for_doc_paths(doc_paths: list[str], docs_root: Path) -> list[dict]:
    """Create per-doc ADK section insert patches (doc-derived only)."""
    out: list[dict] = []
    for dp in doc_paths:
        heading = _heading_from_doc_path(dp)
        full = _resolve_doc_file(docs_root, dp)
        if not full:
            continue
        out.append(_doc_to_new_section_patch(heading, [dp], [full.read_text(encoding="utf-8")]))
    return out


def _strip_frontmatter(raw: str) -> str:
    if raw.strip().startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip()
    return raw


def _normalize_doc_path(path: str) -> str:
    doc_path = path.replace("\\", "/")
    if "lyzr-adk/" in doc_path:
        doc_path = doc_path.split("lyzr-adk/", 1)[-1]
    if "documentation/" in doc_path:
        doc_path = doc_path.split("documentation/", 1)[-1]
        if doc_path.startswith("lyzr-adk/"):
            doc_path = doc_path.split("lyzr-adk/", 1)[-1]
    return doc_path


def _resolve_doc_file(docs_root: Path, doc_path: str) -> Path | None:
    p1 = docs_root / "lyzr-adk" / doc_path
    p2 = docs_root / doc_path
    if p1.exists():
        return p1
    if p2.exists():
        return p2
    return None


def extract_section_body(skill_path: Path, heading: str) -> str:
    if not skill_path.exists():
        return ""
    body = _strip_frontmatter(skill_path.read_text(encoding="utf-8"))
    lines = body.split("\n")
    target = heading.strip()
    level = len(target) - len(target.lstrip("#"))
    collecting = False
    section_lines: list[str] = []
    for line in lines:
        if not collecting and line.strip() == target:
            collecting = True
            continue
        if collecting:
            m = re.match(r"^(#{1,6})\s+", line)
            if m and len(m.group(1)) <= level:
                break
            section_lines.append(line)
    return "\n".join(section_lines).strip()


def get_skill_headings(skill_path: Path) -> list[str]:
    if not skill_path.exists():
        return []
    raw = _strip_frontmatter(skill_path.read_text(encoding="utf-8"))
    return [line.strip() for line in raw.splitlines() if re.match(r"^#{2,3}\s+.+", line)]


def _is_auto_doc_section_heading(heading: str) -> bool:
    return heading.strip().startswith("## ADK: ")


def load_system_prompt(scripts_dir: Path) -> str:
    prompt_path = scripts_dir / "llm_section_update_prompt.md"
    if not prompt_path.exists():
        return FALLBACK_SYSTEM_PROMPT
    raw = prompt_path.read_text(encoding="utf-8")
    m = re.search(r"## System prompt.*?\n(.*?)(?=\n## |\Z)", raw, re.DOTALL)
    if not m:
        return FALLBACK_SYSTEM_PROMPT
    text = m.group(1).strip()
    return text or FALLBACK_SYSTEM_PROMPT


NEW_SKILL_FALLBACK_SYSTEM = (
    "You author a complete Cursor SKILL.md from LYZR ADK documentation. "
    "YAML frontmatter: name, description, license Apache-2.0, allowed-tools (list), triggers (list), "
    "metadata {author, version, category}. Body: # H1, ## Instructions (numbered), ## Overview, ## Setup, "
    "then doc sections with ##/### headings; balanced code fences. Start with ---. Under 450 lines. No JSON."
)


def load_new_skill_system_prompt(scripts_dir: Path) -> str:
    prompt_path = scripts_dir / "llm_section_update_prompt.md"
    if not prompt_path.exists():
        return NEW_SKILL_FALLBACK_SYSTEM
    raw = prompt_path.read_text(encoding="utf-8")
    m = re.search(r"## New skill system prompt.*?\n(.*?)(?=\n## |\Z)", raw, re.DOTALL)
    if not m:
        return NEW_SKILL_FALLBACK_SYSTEM
    text = m.group(1).strip()
    return text or NEW_SKILL_FALLBACK_SYSTEM


def call_llm_openai(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    *,
    max_tokens: int | None = None,
    timeout: int = 120,
) -> str:
    try:
        import urllib.error
        import urllib.request

        model = (os.environ.get("SYNC_LLM_MODEL") or "gpt-4o").strip()
        max_user = _env_int("SYNC_LLM_USER_MAX_CHARS", 28000)
        if len(user_prompt) > max_user:
            user_prompt = (
                user_prompt[:max_user]
                + f"\n\n_(user prompt truncated to {max_user} chars; set SYNC_LLM_USER_MAX_CHARS to raise)_\n"
            )
        tok = 4096 if max_tokens is None else max_tokens
        model_l = model.lower()
        use_completion_tok = (
            model_l.startswith("o1")
            or model_l.startswith("o3")
            or "gpt-5" in model_l
            or os.environ.get("SYNC_OPENAI_USE_MAX_COMPLETION_TOKENS", "").lower() in ("1", "true", "yes")
        )
        payload: dict = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if not use_completion_tok:
            payload["temperature"] = 0.0
            payload["max_tokens"] = tok
        else:
            payload["max_completion_tokens"] = tok
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        if data.get("error"):
            return json.dumps({"updates": [], "_error": str(data["error"])})
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:2000]
        except OSError:
            detail = ""
        return json.dumps({"updates": [], "_error": f"{exc} {detail}"})
    except Exception as exc:
        return json.dumps({"updates": [], "_error": str(exc)})


def call_llm_gemini(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    *,
    max_tokens: int | None = None,
    timeout: int = 120,
) -> str:
    try:
        import urllib.error
        import urllib.parse
        import urllib.request

        model = (os.environ.get("SYNC_LLM_MODEL") or "gemini-1.5-flash").strip()
        if model.startswith("gpt-") or model.startswith("openai/"):
            model = "gemini-1.5-flash"
        elif "/" in model:
            model = model.split("/")[-1]
        max_user = _env_int("SYNC_LLM_USER_MAX_CHARS", 28000)
        if len(user_prompt) > max_user:
            user_prompt = (
                user_prompt[:max_user]
                + f"\n\n_(user prompt truncated to {max_user} chars)_\n"
            )
        out_cap = 8192 if max_tokens is None else min(8192, max_tokens)
        body: dict = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": out_cap,
            },
        }
        q = urllib.parse.urlencode({"key": api_key})
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?{q}"
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        if data.get("error"):
            return json.dumps({"updates": [], "_error": str(data["error"])})
        candidates = data.get("candidates") or []
        if not candidates:
            return json.dumps({"updates": [], "_error": "Gemini returned no candidates (blocked or empty)"})
        parts = (candidates[0].get("content") or {}).get("parts") or []
        texts = [p.get("text", "") for p in parts if isinstance(p, dict)]
        text = "".join(texts).strip()
        return text if text else json.dumps({"updates": [], "_error": "Gemini empty text response"})
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:2000]
        except OSError:
            detail = ""
        return json.dumps({"updates": [], "_error": f"{exc} {detail}"})
    except Exception as exc:
        return json.dumps({"updates": [], "_error": str(exc)})


def invoke_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int | None = None,
    timeout: int = 120,
) -> str:
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    pref = (os.environ.get("SYNC_LLM_PROVIDER") or "").strip().lower()
    if pref == "gemini" and gemini_key:
        return call_llm_gemini(system_prompt, user_prompt, gemini_key, max_tokens=max_tokens, timeout=timeout)
    if pref == "openai" and openai_key:
        return call_llm_openai(system_prompt, user_prompt, openai_key, max_tokens=max_tokens, timeout=timeout)
    if openai_key:
        return call_llm_openai(system_prompt, user_prompt, openai_key, max_tokens=max_tokens, timeout=timeout)
    if gemini_key:
        return call_llm_gemini(system_prompt, user_prompt, gemini_key, max_tokens=max_tokens, timeout=timeout)
    return json.dumps({"updates": [], "_error": "No OPENAI_API_KEY or GEMINI_API_KEY"})


def _safe_json_loads(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```\w*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _line_set(text: str) -> set[str]:
    out: set[str] = set()
    for line in text.splitlines():
        s = re.sub(r"\s+", " ", line.strip()).lower()
        if len(s) >= MIN_DOC_LINE_LEN:
            out.add(s)
    return out


def _doc_supports_new_line(norm_line: str, doc_lines: set[str], doc_bundle: str) -> bool:
    if norm_line in doc_lines:
        return True
    flat = re.sub(r"\s+", " ", doc_bundle.lower())
    if norm_line in flat:
        return True
    if "|" in norm_line and norm_line.count("|") >= 2:
        pipe_norm = re.sub(r"\s*\|\s*", "|", norm_line.strip())
        pipe_flat = re.sub(r"\s*\|\s*", "|", flat)
        if pipe_norm in pipe_flat:
            return True
    return False


def _unsupported_added_lines(old: str, new: str, doc_bundle: str) -> list[str]:
    old_lines = _line_set(old)
    doc_lines = _line_set(doc_bundle)
    bad: list[str] = []
    for raw in new.splitlines():
        norm = re.sub(r"\s+", " ", raw.strip()).lower()
        if len(norm) < MIN_DOC_LINE_LEN:
            continue
        if norm in old_lines:
            continue
        if _doc_supports_new_line(norm, doc_lines, doc_bundle):
            continue
        bad.append(raw.strip())
    return bad


def _unique_suffix_anchor(section_text: str, min_len: int = 100, max_len: int = 2400) -> str:
    """Prefer a short unique tail of the section so patches stay small for repository_dispatch limits."""
    text = section_text
    if len(text) <= min_len:
        return text
    upper = min(len(text), max_len)
    for size in range(min_len, upper + 1, 50):
        suffix = text[-size:]
        if text.count(suffix) == 1:
            return suffix
    return text


def _doc_append_fallback_patch(
    section_heading: str,
    current_body: str,
    doc_bundle: str,
) -> dict | None:
    """
    Optional: when the LLM returns no valid patches, append a short doc excerpt (not surgical).
    Off by default. Enable with SYNC_ENABLE_DOC_APPEND_FALLBACK=1 (e.g. local debugging).
    SYNC_DISABLE_DOC_APPEND_FALLBACK=1 forces off.
    """
    if os.environ.get("SYNC_DISABLE_DOC_APPEND_FALLBACK", "").lower() in ("1", "true", "yes"):
        return None
    if os.environ.get("SYNC_ENABLE_DOC_APPEND_FALLBACK", "").lower() not in ("1", "true", "yes"):
        return None
    body = current_body.strip()
    if not body or not doc_bundle.strip():
        return None
    snippet = doc_bundle.strip()
    max_snip = _env_int("SYNC_FALLBACK_DOC_MAX_CHARS", 500)
    if len(snippet) > max_snip:
        snippet = snippet[:max_snip] + "\n\n_(truncated)_"
    append_block = (
        "\n\n---\n\n**ADK doc sync** (no LLM patch). Fix LLM/API and re-sync, or edit from `lyzr-adk/`.\n\n"
        f"{snippet}\n"
    )
    old_anchor = _unique_suffix_anchor(current_body, min_len=40, max_len=320)
    new_text = old_anchor + append_block
    tentative = {
        "section_heading": section_heading,
        "patches": [
            {
                "context_before": "",
                "old": old_anchor,
                "new": new_text,
                "context_after": "",
            }
        ],
    }
    cleaned, err = _validate_patch_update(section_heading, current_body, tentative, doc_bundle)
    if err:
        print(
            f"[{section_heading}] doc-append fallback failed validation: {err}",
            file=sys.stderr,
        )
        return None
    return cleaned


def _validate_patch_update(section_heading: str, section_before: str, update: dict, doc_bundle: str) -> tuple[dict | None, str | None]:
    if not isinstance(update, dict):
        return None, "update is not an object"
    heading = str(update.get("section_heading", "")).strip()
    if heading != section_heading:
        return None, f"unexpected heading '{heading}'"
    patches = update.get("patches", [])
    if not isinstance(patches, list):
        return None, "patches must be a list"
    cleaned_patches: list[dict] = []
    for idx, patch in enumerate(patches):
        if not isinstance(patch, dict):
            return None, f"patch[{idx}] is not an object"
        obj = {
            "context_before": _normalize_patch_field(str(patch.get("context_before", ""))),
            "old": _normalize_patch_field(str(patch.get("old", ""))),
            "new": _normalize_patch_field(str(patch.get("new", ""))),
            "context_after": _normalize_patch_field(str(patch.get("context_after", ""))),
        }
        if not (obj["context_before"] or obj["old"] or obj["context_after"]):
            return None, f"patch[{idx}] has no anchor context"
        cleaned_patches.append(obj)
    preview, err = apply_patch_series(section_before, cleaned_patches)
    if err:
        return None, err
    if preview is None:
        return None, "failed to build patched preview"
    if os.environ.get("SYNC_STRICT_DOC_LINES", "").lower() in ("1", "true", "yes"):
        unsupported = _unsupported_added_lines(section_before, preview, doc_bundle)
        if unsupported:
            return None, f"contains non-doc lines: {unsupported[:3]}"
    return {"section_heading": section_heading, "patches": cleaned_patches}, None


def _build_section_targets(changed: list[str], mapping: dict) -> tuple[dict[tuple[str, str], list[str]], list[str]]:
    path_rules = mapping.get("path_prefix_rules", {})
    mappings_list = mapping.get("mappings", [])
    doc_map = {m.get("doc_path"): m for m in mappings_list if isinstance(m, dict)}
    targets: dict[tuple[str, str], list[str]] = {}
    skipped: list[str] = []
    for rel in changed:
        if not str(rel).endswith(".mdx"):
            continue
        doc_path = _normalize_doc_path(str(rel))
        mapping_item = doc_map.get(doc_path)
        if not mapping_item:
            prefix = doc_path.split("/")[0] if "/" in doc_path else doc_path.split(".")[0]
            skill = path_rules.get(prefix)
            if skill:
                # Full sync requirement: do not skip unmapped docs. Route them to a deterministic
                # auto-created section under the resolved skill.
                auto_heading = _heading_from_doc_path(doc_path)
                key = (skill, auto_heading)
                targets.setdefault(key, [])
                if doc_path not in targets[key]:
                    targets[key].append(doc_path)
                skipped.append(
                    f"Unmapped doc_path '{doc_path}' routed to auto section '{auto_heading}' under skill '{skill}'."
                )
            continue
        skill_name = str(mapping_item.get("skill", "")).strip()
        if not skill_name:
            continue
        sections = mapping_item.get("sections", [])
        section_headings = [str(s.get("skill_heading", "")).strip() for s in sections if isinstance(s, dict) and s.get("skill_heading")]
        if not section_headings:
            section_headings = ["## Overview"]
        for heading in section_headings:
            key = (skill_name, heading)
            targets.setdefault(key, [])
            if doc_path not in targets[key]:
                targets[key].append(doc_path)
    return targets, skipped


def _collect_new_skill_jobs(
    changed: list,
    mapping: dict,
    ide_root: Path,
    docs_root: Path,
) -> list[dict]:
    triggers = mapping.get("new_skill_triggers") or []
    if not triggers:
        return []
    changed_paths: list[str] = []
    for rel in changed:
        if not str(rel).endswith(".mdx"):
            continue
        changed_paths.append(_normalize_doc_path(str(rel)))
    seen_skill: set[str] = set()
    jobs: list[dict] = []
    for trig in triggers:
        if not isinstance(trig, dict):
            continue
        prefix = str(trig.get("path_prefix", "")).strip().strip("/")
        skill_name = str(trig.get("skill_name", "")).strip()
        if not prefix or not skill_name:
            continue
        if (ide_root / "skills" / skill_name / "SKILL.md").exists():
            continue
        paths = sorted({p for p in changed_paths if p == f"{prefix}.mdx" or p.startswith(f"{prefix}/")})
        if not paths:
            continue
        if skill_name in seen_skill:
            continue
        seen_skill.add(skill_name)
        bundle_parts: list[str] = []
        for doc_path in paths:
            full = _resolve_doc_file(docs_root, doc_path)
            if full and full.exists():
                bundle_parts.append(f"### {doc_path}\n{strip_mdx(full.read_text(encoding='utf-8'))}")
        if not bundle_parts:
            continue
        title = str(trig.get("skill_title", "")).strip() or skill_name.replace("lyzr-", "").replace("-", " ").title()
        jobs.append({
            "skill_name": skill_name,
            "skill_title": title,
            "doc_paths": paths,
            "doc_bundle": "\n\n".join(bundle_parts)[:60000],
        })
    return jobs


def _strip_outer_markdown_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```\w*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t)
    return t.strip()


def _llm_error_from_raw(raw: str) -> str | None:
    if not raw.strip().startswith("{"):
        return None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None
    err = obj.get("_error")
    return str(err) if err else None


def _skills_json_utf8_len(skills: list[dict]) -> int:
    return len(json.dumps({"skills": skills}, ensure_ascii=False).encode("utf-8"))


def _skill_entry_json_bytes(sk: dict) -> int:
    return len(json.dumps(sk, ensure_ascii=False).encode("utf-8"))


def shrink_skills_for_github_dispatch(skills: list[dict]) -> None:
    cap = _env_int("GITHUB_DISPATCH_SKILLS_JSON_MAX", DEFAULT_GITHUB_DISPATCH_SKILLS_JSON_MAX)
    while skills and _skills_json_utf8_len(skills) > cap:
        candidates: list[tuple[int, int | None, int]] = []
        for si, sk in enumerate(skills):
            if sk.get("new_skill"):
                candidates.append((si, None, _skill_entry_json_bytes(sk)))
            for ei, sec in enumerate(sk.get("section_patches") or []):
                cost = len(json.dumps(sec, ensure_ascii=False).encode("utf-8"))
                # Prefer dropping bulky per-doc ADK inserts before mapped sections.
                heading = str(sec.get("section_heading") or "")
                if heading.startswith("## ADK: "):
                    cost += 20000
                candidates.append((si, ei, cost))
        if not candidates:
            break
        si, ei, _cost = max(candidates, key=lambda x: x[2])
        if ei is None:
            print(f"[dispatch-limit] dropping new_skill {skills[si].get('skill_name')}", file=sys.stderr)
            skills.pop(si)
            continue
        heading = skills[si]["section_patches"][ei].get("section_heading")
        del skills[si]["section_patches"][ei]
        print(f"[dispatch-limit] dropped {skills[si].get('skill_name')}:{heading}", file=sys.stderr)
        if not skills[si].get("section_patches"):
            skills.pop(si)


def _run_new_skill_generation(job: dict, scripts_dir: Path) -> tuple[str | None, str | None]:
    sys_p = load_new_skill_system_prompt(scripts_dir)
    user_p = (
        f"skill_folder_name: {job['skill_name']}\n"
        f"skill_title_hint: {job['skill_title']}\n"
        f"source_doc_paths: {json.dumps(job['doc_paths'])}\n\n"
        "Documentation excerpts:\n---\n"
        f"{job['doc_bundle']}\n---\n\n"
        "Write the complete SKILL.md now."
    )
    raw = invoke_llm(sys_p, user_p, max_tokens=16000, timeout=180)
    err = _llm_error_from_raw(raw)
    if err:
        return None, err
    body = _strip_outer_markdown_fence(raw)
    if not body.strip().startswith("---"):
        return None, "LLM output missing YAML frontmatter (must start with ---)"
    if body.count("```") % 2 != 0:
        return None, "LLM output has unbalanced code fences"
    ok, v_err = validate_skill_frontmatter(body)
    if not ok:
        return None, v_err
    return body.strip(), None


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: build_sync_payload.py <ide_skills_root> <docs_root> <changed_files.json>", file=sys.stderr)
        sys.exit(1)

    ide_root = Path(sys.argv[1]).resolve()
    _load_env_file(ide_root)
    docs_root = Path(sys.argv[2]).resolve()
    changed_raw = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    changed = changed_raw if isinstance(changed_raw, list) else changed_raw.get("files", [changed_raw])

    mapping = load_mapping(ide_root)
    section_targets, skipped = _build_section_targets(changed, mapping)
    for msg in skipped:
        print(msg, file=sys.stderr)

    if not (os.environ.get("OPENAI_API_KEY", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()):
        print("Set OPENAI_API_KEY or GEMINI_API_KEY", file=sys.stderr)
        sys.exit(1)

    scripts_dir = ide_root / "scripts"
    system_prompt = load_system_prompt(scripts_dir)

    skills_updates: dict[str, dict] = {}

    for (skill_name, section_heading), doc_paths in section_targets.items():
        skill_path = ide_root / "skills" / skill_name / "SKILL.md"
        if not skill_path.exists():
            print(f"[{skill_name}:{section_heading}] SKILL.md missing; skipping.", file=sys.stderr)
            continue
        all_headings = get_skill_headings(skill_path)
        # For auto doc sections (## ADK: ...), allow creation downstream (apply step).
        if section_heading not in set(all_headings) and not _is_auto_doc_section_heading(section_heading):
            print(f"[{skill_name}:{section_heading}] heading not found; skipping.", file=sys.stderr)
            continue

        current_body = extract_section_body(skill_path, section_heading) if section_heading in set(all_headings) else ""
        if len(current_body) > MAX_SECTION_CHARS:
            print(f"[{skill_name}:{section_heading}] section truncated to {MAX_SECTION_CHARS} chars.", file=sys.stderr)
            current_body = current_body[:MAX_SECTION_CHARS]

        docs_chunks: list[str] = []
        for doc_path in doc_paths:
            full = _resolve_doc_file(docs_root, doc_path)
            if not full:
                print(f"[{skill_name}:{section_heading}] missing doc: {doc_path}", file=sys.stderr)
                continue
            docs_chunks.append(f"### {doc_path}\n{strip_mdx(full.read_text(encoding='utf-8'))}")
        if not docs_chunks:
            continue
        doc_bundle = "\n\n".join(docs_chunks)
        if len(doc_bundle) > MAX_DOC_BUNDLE_CHARS:
            print(f"[{skill_name}:{section_heading}] doc bundle truncated to {MAX_DOC_BUNDLE_CHARS} chars.", file=sys.stderr)
            doc_bundle = doc_bundle[:MAX_DOC_BUNDLE_CHARS]

        structure_lines = "\n".join(f"  {idx + 1}. {h}" for idx, h in enumerate(all_headings))
        prompt = (
            f"doc_paths: {json.dumps(doc_paths)}\n"
            f"skill: {skill_name}\n"
            f"target_heading: {section_heading}\n\n"
            "Skill file structure (ordered headings; immutable):\n"
            f"{structure_lines}\n\n"
            "Current target section body:\n---\n"
            f"{current_body}\n---\n\n"
            "Doc excerpts (ADK source of truth):\n---\n"
            f"{doc_bundle}\n---\n\n"
            f"Allowed heading: {section_heading}\n\n"
            "SURGICAL: Update only what the doc excerpts require; preserve tone, structure, and unrelated bullets. "
            "Do not replace the entire section unless every part is wrong per the docs.\n\n"
            "ANCHOR RULES: Prefer the full anchor context_before+old+context_after copied EXACTLY from the "
            "section body (must match once). If that is fragile, use empty context_before and context_after "
            "and set old to a UNIQUE substring that appears exactly once (multi-line code block preferred; "
            "single-line old must be long enough to be unique).\n\n"
            "Return JSON only with patch hunks. "
            'Use schema {"updates":[{"section_heading":"## Heading","patches":[{"context_before":"","old":"","new":"","context_after":""}]}]}. '
            'If no change is needed, return {"updates":[]}.'
        )
        user_prompt = prompt
        accepted = None
        # Auto doc sections: skip LLM and inject doc content deterministically.
        if _is_auto_doc_section_heading(section_heading):
            texts: list[str] = []
            resolved: list[str] = []
            for dp in doc_paths:
                full = _resolve_doc_file(docs_root, dp)
                if not full:
                    continue
                resolved.append(dp)
                texts.append(full.read_text(encoding="utf-8"))
            if not resolved:
                continue
            accepted = _doc_to_new_section_patch(section_heading, resolved, texts)
        else:
            for attempt in range(2):
                raw = invoke_llm(system_prompt, user_prompt)
                parsed = _safe_json_loads(raw)
                if parsed.get("_error"):
                    print(f"[{skill_name}:{section_heading}] LLM error: {parsed['_error']}", file=sys.stderr)
                    break
                updates = parsed.get("updates", [])
                if not isinstance(updates, list) or not updates:
                    break
                round_errors: list[str] = []
                for update in updates:
                    cleaned, err = _validate_patch_update(section_heading, current_body, update, doc_bundle)
                    if err:
                        round_errors.append(err)
                        print(
                            f"[{skill_name}:{section_heading}] rejecting update (attempt {attempt + 1}): {err}",
                            file=sys.stderr,
                        )
                        continue
                    accepted = cleaned
                    break
                if accepted:
                    break
                if attempt == 0 and round_errors:
                    user_prompt = (
                        f"{prompt}\n\n---\nRETRY: Previous patches failed validation:\n"
                        + "\n".join(f"- {e}" for e in round_errors[:5])
                        + "\nReturn fixed JSON only. Use empty context_before/context_after and a unique "
                        "multi-line `old` copied verbatim from the section if needed.\n"
                    )
        if not accepted:
            # Full-doc sync fallback: if we cannot surgically patch a mapped section, do not write any
            # error text into SKILL.md. Instead, ensure the doc content lands in per-doc `## ADK: ...`
            # sections for traceability.
            fallback_docs = _doc_section_patches_for_doc_paths(doc_paths, docs_root)
            if fallback_docs:
                print(
                    f"[{skill_name}:{section_heading}] falling back to per-doc ADK sections for {len(fallback_docs)} doc(s).",
                    file=sys.stderr,
                )
                # Attach these extra sections to the same skill entry.
                skill_entry = skills_updates.setdefault(
                    skill_name,
                    {"skill_name": skill_name, "new_skill": False, "section_patches": []},
                )
                for sec in fallback_docs:
                    skill_entry["section_patches"].append(sec)
            accepted = None
        if not accepted:
            continue
        skill_entry = skills_updates.setdefault(
            skill_name,
            {"skill_name": skill_name, "new_skill": False, "section_patches": []},
        )
        exists = any(p.get("section_heading") == section_heading for p in skill_entry["section_patches"])
        if exists:
            skill_entry["section_patches"] = [
                p for p in skill_entry["section_patches"] if p.get("section_heading") != section_heading
            ]
        skill_entry["section_patches"].append(accepted)

    out_skills: list[dict] = list(skills_updates.values())
    ns_prompt_dir = ide_root / "scripts"
    for job in _collect_new_skill_jobs(changed, mapping, ide_root, docs_root):
        full_md, ns_err = _run_new_skill_generation(job, ns_prompt_dir)
        if ns_err:
            print(f"[new_skill:{job['skill_name']}] {ns_err}", file=sys.stderr)
            continue
        if full_md:
            out_skills.append({
                "skill_name": job["skill_name"],
                "new_skill": True,
                "full_content": full_md,
            })

    shrink_skills_for_github_dispatch(out_skills)
    print(json.dumps({"skills": out_skills}))


if __name__ == "__main__":
    main()
