#!/usr/bin/env python3
"""Report structural completeness for the novel workflow.

This script does not score story quality. It checks whether the structural
control files are present and whether chapter/summary/runtime coverage is
coherent enough for the AI workflow to proceed.

Usage:
    python3 scripts/structure_report.py
"""

from __future__ import annotations
from _project import add_root_argument, get_root

import json
import re
from pathlib import Path


ROOT: Path = Path.cwd()  # Set in main() via --project-root or CWD

REQUIRED_OUTLINE_FILES = [
    "story/brief.md",
    "story/author_intent.md",
    "story/book_rules.md",
    "story/outline/story_frame.md",
    "story/outline/volume_map.md",
    "story/fiction_style_skill.md",
    "story/style_profile.md",
]

SUMMARY_COLUMNS = ["章节", "标题", "出场人物", "关键事件", "状态变化", "伏笔动态", "情绪基调", "章节类型"]
ARC_COLUMNS = ["章节", "角色", "章初状态", "本章选择", "章末状态", "可见证据", "下一章欠账"]


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def markdown_table(rel: str) -> tuple[list[str], list[dict[str, str]]]:
    path = ROOT / rel
    if not path.is_file():
        return [], []
    lines = path.read_text(encoding="utf-8").splitlines()
    table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
    if len(table_lines) < 2:
        return [], []
    header = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))
    return header, rows


def chapter_files() -> dict[int, Path]:
    result: dict[int, Path] = {}
    for path in (ROOT / "chapters").glob("*.md"):
        match = re.match(r"^(\d{4})_", path.name)
        if match:
            result[int(match.group(1))] = path
    return result


def runtime_chapters(kind: str) -> set[int]:
    result: set[int] = set()
    pattern = re.compile(rf"^chapter-(\d{{4}})\.{re.escape(kind)}\.md$")
    for path in (ROOT / "story/runtime").glob(f"chapter-*.{kind}.md"):
        match = pattern.match(path.name)
        if match:
            result.add(int(match.group(1)))
    return result


def frontmatter_status(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^status:\s*([A-Za-z0-9_-]+)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def non_placeholder(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    placeholders = ["待填写", "未开始", "（", "）", "- \n", "| ---"]
    meaningful_lines = [
        line.strip()
        for line in stripped.splitlines()
        if line.strip() and not line.strip().startswith("| ---")
    ]
    joined = "\n".join(meaningful_lines)
    return bool(joined) and not all(token in joined for token in ["待填写"])


def main() -> int:
    global ROOT
    warnings: list[str] = []
    errors: list[str] = []

    print("structure report")
    print(f"root: {ROOT}")

    chapters = chapter_files()
    initialized = bool(chapters)

    for rel in REQUIRED_OUTLINE_FILES:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing structure file: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if initialized and not non_placeholder(text):
            warnings.append(f"structure file appears unfilled: {rel}")

    # Check v0.3+ structural directories
    for d in ["story/ledger", "story/views", "story/plans", "workflow"]:
        if not (ROOT / d).is_dir():
            errors.append(f"missing structural directory: {d}")

    print(f"chapterFiles: {len(chapters)}")
    if chapters:
        nums = sorted(chapters)
        missing = [n for n in range(nums[0], nums[-1] + 1) if n not in chapters]
        if missing:
            errors.append(f"missing chapter files in sequence: {missing}")

    summary_header, summary_rows = markdown_table("story/chapter_summaries.md")
    if summary_header and summary_header != SUMMARY_COLUMNS:
        errors.append("chapter_summaries.md table header does not match expected structure")
    summary_nums = {
        int(row["章节"])
        for row in summary_rows
        if row.get("章节", "").isdigit()
    }
    for n in sorted(chapters):
        if n not in summary_nums:
            warnings.append(f"chapter {n:04d} has file but no chapter summary row")
    for n in sorted(summary_nums):
        if n not in chapters:
            warnings.append(f"chapter summary exists without chapter file: {n:04d}")

    arc_header, arc_rows = markdown_table("story/emotional_arcs.md")
    if arc_header and arc_header != ARC_COLUMNS:
        errors.append("emotional_arcs.md table header does not match expected structure")
    arc_nums = {
        int(row["章节"])
        for row in arc_rows
        if row.get("章节", "").isdigit()
    }
    for n in sorted(summary_nums):
        if n not in arc_nums:
            warnings.append(f"chapter {n:04d} has summary but no emotional arc row")

    runtime_sets = {
        "intent": runtime_chapters("intent"),
        "plan": runtime_chapters("plan"),
        "writer": runtime_chapters("writer"),
        "polish": runtime_chapters("polish"),
        "review": runtime_chapters("review"),
        "fixer": runtime_chapters("fixer"),
        "final-check": runtime_chapters("final-check"),
    }
    for n in sorted(chapters):
        if n not in runtime_sets["intent"]:
            warnings.append(f"chapter {n:04d} has file but no runtime intent")
        if n not in runtime_sets["plan"]:
            warnings.append(f"chapter {n:04d} has file but no runtime plan")
        if n not in runtime_sets["final-check"]:
            warnings.append(f"chapter {n:04d} has file but no final-check")

    runtime_files = sorted((ROOT / "story/runtime").glob("chapter-*.md"))
    dangling = []
    for path in runtime_files:
        match = re.match(r"^chapter-(\d{4})\.", path.name)
        if not match:
            continue
        n = int(match.group(1))
        status = frontmatter_status(path)
        if n not in chapters and status == "final-aligned":
            errors.append(f"runtime final-aligned but chapter file missing: {path.relative_to(ROOT)}")
        if n not in chapters and status not in {"planned", "drafted", "polished", "reviewed", "fixed", "final-check", "needs-repair", "needs-rewrite", "superseded", None}:
            dangling.append(str(path.relative_to(ROOT)))
    if dangling:
        warnings.append("runtime files without matching chapters: " + ", ".join(dangling))

    try:
        index = json.loads((ROOT / "chapters/index.json").read_text(encoding="utf-8"))
        indexed_nums = {
            item.get("chapter")
            for item in index.get("chapters", [])
            if isinstance(item, dict)
        }
        for n in sorted(chapters):
            if n not in indexed_nums:
                warnings.append(f"chapter {n:04d} file exists but is not indexed")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"cannot read chapters/index.json: {exc}")

    if errors:
        print("\nERRORS:")
        for item in errors:
            print(f"- {item}")
    if warnings:
        print("\nWARNINGS:")
        for item in warnings:
            print(f"- {item}")
    if not errors and not warnings:
        print("\nOK: structure is coherent.")
    elif not errors:
        print("\nOK with structural warnings.")
    else:
        print("\nFAILED.")
    return 1 if errors else 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Structure Report")
    add_root_argument(parser)
    args = parser.parse_args()
    ROOT = get_root(args)
    raise SystemExit(main())
