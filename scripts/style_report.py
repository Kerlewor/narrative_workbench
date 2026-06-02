#!/usr/bin/env python3
"""Style Report for Narrative Workbench."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from _project import add_root_argument, get_root
from core.context import chapter_prefix
from core.style import AI_PATTERNS, analyze_text, build_style_report, find_chapter_file


ROOT: Path = Path.cwd()


def build_report(chapter: int, input_path: str | None = None) -> str:
    return build_style_report(ROOT, chapter, input_path)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Style Report for Narrative Workbench")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, default=0, help="章节编号")
    parser.add_argument("--input", type=str, default=None, help="直接指定文件路径")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    ROOT = get_root(args)

    report = build_report(args.chapter, args.input)
    if args.output:
        output_path = Path(args.output)
    else:
        prefix = chapter_prefix(args.chapter) if args.chapter else "custom"
        output_path = ROOT / "story/runtime" / f"{prefix}.style_report.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    try:
        display_path = output_path.relative_to(ROOT)
    except ValueError:
        display_path = output_path
    print(f"Style report written to {display_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
