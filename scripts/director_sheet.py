"""Director Sheet Generator for Narrative Workbench.

This script is the CLI wrapper; reusable chapter planning logic lives in
core.chapter.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from _project import add_root_argument, get_root
from core.chapter import (  # noqa: E402
    generate_director_from_plan,
    generate_director_from_template,
    validate_director_sheet,
    validate_scene_handoffs,
)
from core.context import chapter_prefix  # noqa: E402


ROOT: Path = Path.cwd()


def generate_from_template(chapter: int, chapter_title: str) -> str:
    return generate_director_from_template(ROOT, chapter, chapter_title)


def generate_from_plan(chapter: int) -> str:
    return generate_director_from_plan(ROOT, chapter)


def validate_sheet(chapter: int) -> int:
    report = validate_director_sheet(ROOT, chapter)
    for line in report.lines:
        print(line)
    if report.ok:
        print("\nDirector sheet valid")
        return 0
    print(f"\n{report.errors} issue(s) found")
    return 1


def validate_handoffs(chapter: int) -> int:
    report = validate_scene_handoffs(ROOT, chapter)
    for line in report.lines:
        print(line)
    if report.ok:
        return 0
    print(f"\n{report.errors} issue(s) found")
    return 1


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Director Sheet Generator")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument("--from-template", action="store_true", help="从模板生成（推荐，适合首次创建）")
    parser.add_argument("--from-plan", action="store_true", help="从 intent/plan 生成（提取已有规划）")
    parser.add_argument("--validate", action="store_true", help="验证已有导演表")
    parser.add_argument("--validate-handoffs", action="store_true", help="验证已有场景接力卡")
    parser.add_argument("--title", type=str, default="", help="章节标题")
    args = parser.parse_args()
    ROOT = get_root(args)

    prefix = chapter_prefix(args.chapter)

    if args.validate:
        return validate_sheet(args.chapter)
    if args.validate_handoffs:
        return validate_handoffs(args.chapter)

    if args.from_template:
        title = args.title or f"第{args.chapter}章"
        content = generate_from_template(args.chapter, title)
    elif args.from_plan:
        content = generate_from_plan(args.chapter)
        if not content:
            print(f"No intent or plan found for chapter {args.chapter}. Run --from-template instead.", file=sys.stderr)
    else:
        content = generate_from_plan(args.chapter)
        if not content:
            title = args.title or f"第{args.chapter}章"
            content = generate_from_template(args.chapter, title)

    if not content:
        template_path = ROOT / "story/plans/_template.director_sheet.yaml"
        if not template_path.is_file():
            print(f"Template not found: {template_path}", file=sys.stderr)
        return 1

    output_path = ROOT / "story/plans" / f"{prefix}_director_sheet.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.is_file():
        print(f"WARNING: {output_path.relative_to(ROOT)} already exists.")
        print("Use --validate to check it, or delete it and re-run to regenerate.")
        return 1

    output_path.write_text(content, encoding="utf-8")
    print(f"Director sheet written to {output_path.relative_to(ROOT)}")
    print("Next: edit the sheet, then run with --validate to check completeness")
    return 0


if __name__ == "__main__":
    sys.exit(main())
