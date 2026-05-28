#!/usr/bin/env python3
"""InkOS Project Importer for Narrative Workbench.

Maps InkOS-generated project files to Narrative Workbench equivalents.
This importer is intended for user-owned InkOS-style projects.
It does NOT include, copy, or redistribute InkOS source code or prompt text.

Usage:
    python3 scripts/import_inkos_project.py /path/to/inkos-book
    python3 scripts/import_inkos_project.py /path/to/inkos-book --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILE_MAP: list[tuple[str, str, str]] = [
    ("current_state.md", "story/current_state.md", "直接映射"),
    ("pending_hooks.md", "story/pending_hooks.md", "直接映射"),
    ("chapter_summaries.md", "story/chapter_summaries.md", "直接映射"),
    ("emotional_arcs.md", "story/emotional_arcs.md", "直接映射"),
    ("character_matrix.md", "story/character_matrix.md", "直接映射"),
    ("current_focus.md", "story/current_focus.md", "直接映射"),
    ("author_intent.md", "story/author_intent.md", "直接映射"),
    ("book_rules.md", "story/book_rules.md", "直接映射"),
    ("bible.md", "story/outline/story_frame.md", "需手动审核——InkOS bible.md 与 NW story_frame.md 结构不同"),
    ("subplot_board.md", "story/import_review.md", "无直接对应——支线面板内容需拆解"),
    ("particle_ledger.md", "story/import_review.md", "无直接对应——资源账本需人工迁移"),
]


def import_project(source: str, dry_run: bool = False) -> dict:
    src = Path(source)
    if not src.is_dir():
        return {"error": f"源目录不存在: {src}"}

    imported: list[str] = []
    needs_review: list[str] = []
    chapters_imported = 0

    for inkos_file, nw_path, note in FILE_MAP:
        src_file = src / inkos_file
        if not src_file.is_file():
            continue

        dest = ROOT / nw_path
        if "需手动审核" in note or "无直接对应" in note or "import_review" in nw_path:
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if "import_review" in nw_path:
                    content = src_file.read_text(encoding="utf-8")
                    with open(dest, "a", encoding="utf-8") as f:
                        f.write(f"\n## {inkos_file}\n\n{content[:2000]}\n\n")
            needs_review.append(f"{inkos_file} → {nw_path} ({note})")
        else:
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest)
            imported.append(f"{inkos_file} → {nw_path}")

    chapters_dir = src / "chapters"
    if chapters_dir.is_dir():
        dest_chapters = ROOT / "chapters"
        dest_chapters.mkdir(parents=True, exist_ok=True)
        for ch_file in sorted(chapters_dir.glob("*.md")):
            if not dry_run:
                shutil.copy2(ch_file, dest_chapters / ch_file.name)
            chapters_imported += 1

    roles_dir = src / "story" / "roles"
    if roles_dir.is_dir():
        dest_roles = ROOT / "story/roles"
        dest_roles.mkdir(parents=True, exist_ok=True)
        for role_file in sorted(roles_dir.glob("*.md")):
            if role_file.name.startswith("_template"):
                continue
            if not dry_run:
                shutil.copy2(role_file, dest_roles / role_file.name)
            imported.append(f"story/roles/{role_file.name} → story/roles/{role_file.name}")

    return {
        "imported": imported,
        "needs_review": needs_review,
        "chapters": chapters_imported,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="InkOS Project Importer")
    parser.add_argument("source", type=str, help="InkOS 项目目录路径")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际复制文件")
    args = parser.parse_args()

    result = import_project(args.source, args.dry_run)

    if "error" in result:
        print(f"Error: {result['error']}")
        return 1

    print("# InkOS Import Report")
    print()
    print(f"## 已导入 ({len(result['imported'])} 项)")
    for item in result["imported"]:
        print(f"- {item}")

    print(f"\n## 需手动审核 ({len(result['needs_review'])} 项)")
    for item in result["needs_review"]:
        print(f"- {item}")

    print(f"\n## 章节")
    print(f"- {result['chapters']} 章")

    if args.dry_run:
        print("\n(仅预览模式，未实际复制文件。去掉 --dry-run 执行实际导入。)")
    else:
        print("\n导入完成。建议运行: python3 scripts/doctor.py + python3 scripts/structure_report.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
