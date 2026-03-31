#!/usr/bin/env python3
"""
Run ADK → skills sync locally: build payload with build_sync_payload.py, optionally apply.

Loads OPENAI_API_KEY / GEMINI_API_KEY from the environment or ide_skills/.env (same as build_sync_payload).

Examples:
  python scripts/run_local_sync.py --docs-dir ../documentation --files lyzr-adk/overview.mdx
  python scripts/run_local_sync.py --docs-dir ../documentation --full-sync
  python scripts/run_local_sync.py --docs-dir ../documentation --full-sync --apply
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _ide_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _collect_mdx_relative(docs_dir: Path) -> list[str]:
    adk = docs_dir / "lyzr-adk"
    if not adk.is_dir():
        print(f"No lyzr-adk under {docs_dir}", file=sys.stderr)
        sys.exit(1)
    return sorted(p.relative_to(docs_dir).as_posix() for p in adk.rglob("*.mdx"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Local ADK docs → skills sync driver")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        required=True,
        help="Documentation root containing lyzr-adk/ (e.g. ../documentation)",
    )
    parser.add_argument(
        "--files",
        type=str,
        default="",
        help="Space-separated doc paths relative to docs-dir (e.g. 'lyzr-adk/agents/overview.mdx')",
    )
    parser.add_argument("--full-sync", action="store_true", help="Process all *.mdx under lyzr-adk/")
    parser.add_argument(
        "--allow-doc-fallback",
        action="store_true",
        help="If LLM returns no valid patches, allow doc-append fallback (SYNC_ENABLE_DOC_APPEND_FALLBACK; off by default, matches CI)",
    )
    parser.add_argument("--apply", action="store_true", help="Run apply_sync_payload.py on built JSON")
    parser.add_argument(
        "--ide-root",
        type=Path,
        default=None,
        help="ide_skills repo root (default: parent of scripts/)",
    )
    args = parser.parse_args()

    ide = (args.ide_root or _ide_root()).resolve()
    docs_dir = args.docs_dir.resolve()
    build_script = ide / "scripts" / "build_sync_payload.py"
    apply_script = ide / "scripts" / "apply_sync_payload.py"
    if not build_script.is_file():
        print(f"Missing {build_script}", file=sys.stderr)
        sys.exit(1)

    if args.full_sync:
        changed = _collect_mdx_relative(docs_dir)
    else:
        changed = [p.strip() for p in args.files.split() if p.strip()]
        if not changed:
            parser.error("Provide --files or use --full-sync")

    tmp = ide / "scripts" / ".local_sync_changed.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(changed), encoding="utf-8")

    print(f"Building payload for {len(changed)} doc path(s)...", file=sys.stderr)
    env = os.environ.copy()
    if args.allow_doc_fallback:
        env["SYNC_ENABLE_DOC_APPEND_FALLBACK"] = "1"
    proc = subprocess.run(
        [sys.executable, str(build_script), str(ide), str(docs_dir), str(tmp)],
        cwd=str(ide),
        capture_output=True,
        text=True,
        env=env,
    )
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        print(proc.stdout, end="", file=sys.stderr)
        sys.exit(proc.returncode)

    out_json = proc.stdout.strip()
    try:
        payload = json.loads(out_json)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON from build_sync_payload: {e}", file=sys.stderr)
        print(out_json[:2000], file=sys.stderr)
        sys.exit(1)

    skills = payload.get("skills", [])
    print(json.dumps({"skills_count": len(skills), "skills": [s.get("skill_name") for s in skills]}, indent=2))
    out_path = ide / "scripts" / ".local_sync_payload.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}", file=sys.stderr)

    if not args.apply:
        return
    if not skills:
        print("Nothing to apply (empty skills).", file=sys.stderr)
        return
    if not apply_script.is_file():
        print(f"Missing {apply_script}", file=sys.stderr)
        sys.exit(1)
    r2 = subprocess.run(
        [sys.executable, str(apply_script), str(ide), f"@{out_path}"],
        cwd=str(ide),
    )
    sys.exit(r2.returncode)


if __name__ == "__main__":
    main()
