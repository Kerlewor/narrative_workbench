#!/usr/bin/env python3
"""Check or update chapters/index.json from chapter files.

Usage:
    python3 scripts/chapter_index.py --check
    python3 scripts/chapter_index.py --write
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTERS_DIR = ROOT / "chapters"
INDEX_PATH = CHAPTERS_DIR / "index.json"
CHAPTER_RE = re.compile(r"^(?P<num>\d{4})_(?P<title>.+)\.md$")


def count_cjk_words(text: str) -> int:
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    latin_words = re.findall(r"[A-Za-z0-9]+(?:[-_'][A-Za-z0-9]+)*", text)
    return len(cjk) + len(latin_words)


def scan_chapters() -> list[dict[str, object]]:
    chapters: list[dict[str, object]] = []
    for path in sorted(CHAPTERS_DIR.glob("*.md")):
        match = CHAPTER_RE.match(path.name)
        if not match:
            continue
        text = path.read_text(encoding="utf-8")
        stat = path.stat()
        chapters.append(
            {
                "chapter": int(match.group("num")),
                "title": match.group("title"),
                "file": str(path.relative_to(ROOT)),
                "status": "final",
                "wordCount": count_cjk_words(text),
                "updatedAt": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            }
        )
    return chapters


def load_existing() -> dict[str, object]:
    if not INDEX_PATH.exists():
        return {"chapters": []}
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def build_index() -> dict[str, object]:
    return {
        "chapters": scan_chapters(),
        "schema": {
            "chapter": "number",
            "title": "string",
            "file": "string",
            "status": "final",
            "wordCount": "number",
            "updatedAt": "string",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="check chapters/index.json without writing")
    mode.add_argument("--write", action="store_true", help="rewrite chapters/index.json from chapter files")
    args = parser.parse_args()

    generated = build_index()

    if args.write:
        INDEX_PATH.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"updated {INDEX_PATH.relative_to(ROOT)} with {len(generated['chapters'])} chapters")
        return 0

    existing = load_existing()
    if existing == generated:
        print("chapter index OK")
        return 0

    existing_chapters = existing.get("chapters", []) if isinstance(existing, dict) else []
    generated_chapters = generated["chapters"]
    print("chapter index differs")
    print(f"existing chapters: {len(existing_chapters)}")
    print(f"actual chapters:   {len(generated_chapters)}")

    existing_files = {item.get("file") for item in existing_chapters if isinstance(item, dict)}
    actual_files = {item.get("file") for item in generated_chapters if isinstance(item, dict)}
    missing = sorted(actual_files - existing_files)
    stale = sorted(existing_files - actual_files)
    if missing:
        print("missing from index:")
        for item in missing:
            print(f"- {item}")
    if stale:
        print("stale index entries:")
        for item in stale:
            print(f"- {item}")
    print("run: python3 scripts/chapter_index.py --write")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

