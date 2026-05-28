#!/usr/bin/env python3
"""Co-writing: Polish Author Chapter.

Prepares an author-written chapter for Polish Agent processing.
Supports 5 polish modes. Does NOT overwrite the original.

Usage:
    python3 scripts/polish_author_chapter.py --chapter 12 --mode light
    python3 scripts/polish_author_chapter.py --input chapters/drafts/my-chapter.md --mode anti-ai
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]

POLISH_MODES = {
    "preserve-author-style": {
        "alias": "light",
        "label": "保留作者风格",
        "instructions": [
            "只改病句、重复和节奏问题。",
            "保留所有作者的用词习惯和表达方式。",
            "不改变任何句子的核心含义。",
            "标注所有改动位置和原因。",
        ],
    },
    "project-style-align": {
        "alias": "style",
        "label": "对齐项目文风",
        "instructions": [
            "按项目 style_profile 对齐句长、对白密度和段落形态。",
            "参考 style_samples 中的文风样本。",
            "保持作者的情节和角色选择不变。",
            "标注哪些改动是风格对齐，哪些是必要的语法修正。",
        ],
    },
    "anti-ai-only": {
        "alias": "anti-ai",
        "label": "仅去 AI 味",
        "instructions": [
            "只处理 AI 腔问题：模板感、解释感、抽象情绪词、万能氛围句。",
            "参照 story/style_blacklist.md 进行修正。",
            "不改变节奏、不对齐文风、不修饰对白。",
        ],
    },
    "dialogue-only": {
        "alias": "dialogue",
        "label": "仅修对白",
        "instructions": [
            "只修改对白部分。",
            "让角色的说话方式与角色卡中的对白风味对齐。",
            "检查对白中的信息泄露风险。",
            "不修改叙述、描写和心理活动。",
        ],
    },
    "rhythm-only": {
        "alias": "rhythm",
        "label": "仅调节奏",
        "instructions": [
            "只调整段落长短、高压喘息交替和章尾落点。",
            "对照卷纲中的情绪曲线节点。",
            "不修改对白内容、不调整风格表达。",
        ],
    },
}


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def find_author_draft(chapter: int) -> Optional[Path]:
    drafts_dir = ROOT / "chapters/drafts"
    prefix = chapter_prefix(chapter)
    candidate = drafts_dir / f"{prefix}.author.md"
    if candidate.is_file():
        return candidate
    matches = sorted(drafts_dir.glob(f"{prefix}*author*"))
    return matches[0] if matches else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Polish Author Chapter")
    parser.add_argument("--chapter", type=int, default=0)
    parser.add_argument("--input", type=str, default=None)
    parser.add_argument("--mode", type=str, default="preserve-author-style",
                        choices=list(POLISH_MODES.keys()),
                        help="润色模式")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    if args.input:
        source_path = Path(args.input)
    elif args.chapter:
        source_path = find_author_draft(args.chapter)
    else:
        print("请指定 --chapter 或 --input")
        return 1

    if not source_path or not source_path.is_file():
        print(f"手写稿不存在: {source_path}")
        return 1

    mode = POLISH_MODES[args.mode]
    text = source_path.read_text(encoding="utf-8")

    lines: list[str] = []
    lines.append(f"# Author Chapter Polish Brief")
    lines.append(f"来源: {source_path}")
    lines.append(f"模式: {args.mode} ({mode['label']})")
    lines.append("")
    lines.append("## 润色指令")
    for inst in mode["instructions"]:
        lines.append(f"- {inst}")
    lines.append("")
    lines.append("## 重要约束")
    lines.append("- **不覆盖原稿。** 输出为独立的润色稿。")
    lines.append("- 标注所有改动的位置和原因。")
    lines.append("- 不改情节、不改角色选择、不新增事实。")
    lines.append("- 不确定时保留原文。")
    lines.append("")

    if args.output:
        output_path = Path(args.output)
    else:
        prefix = chapter_prefix(args.chapter) if args.chapter else "custom"
        mode_alias = mode["alias"]
        output_path = ROOT / "story/runtime" / f"{prefix}.author_polish_{mode_alias}.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        lines[0] + "\n" + "\n".join(lines[1:]) + "\n\n## 手写稿正文\n\n" + text[:5000],
        encoding="utf-8"
    )

    print(f"Polish brief written to {output_path.relative_to(ROOT)}")
    print(f"Mode: {args.mode} ({mode['label']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
