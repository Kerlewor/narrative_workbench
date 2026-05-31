#!/usr/bin/env python3
"""Co-writing: Polish Author Chapter.

Prepares an author-written chapter for Polish Agent processing.
This script generates a structured polish brief — it does NOT call any
AI model, does NOT perform semantic polishing, and does NOT modify text.
The actual polishing is performed by Claude Code/Codex via the Polish Agent.
Supports 5 polish modes. Does NOT overwrite the original.

Usage:
    python scripts/polish_author_chapter.py --chapter 12 --mode light
    python scripts/polish_author_chapter.py --input chapters/drafts/my-chapter.md --mode anti-ai
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from _project import add_root_argument, get_root

ROOT: Path = Path.cwd()

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


def _chunk_text(text: str, max_chunk_chars: int = 8000) -> list[str]:
    """Split text into paragraph-preserving chunks with IDs."""
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0
    para_idx = 0

    for para in paragraphs:
        para_len = len(para)
        if current_len + para_len > max_chunk_chars and current_chunk:
            para_range = f"[段落 {para_idx - len(current_chunk) + 1}–{para_idx}]"
            chunks.append(f"## {para_range}\n\n" + "\n\n".join(current_chunk))
            current_chunk = [para]
            current_len = para_len
        else:
            current_chunk.append(para)
            current_len += para_len
        para_idx += 1

    if current_chunk:
        para_range = f"[段落 {para_idx - len(current_chunk) + 1}–{para_idx}]"
        chunks.append(f"## {para_range}\n\n" + "\n\n".join(current_chunk))

    return chunks


def _build_fulltext_section(text: str, max_total_chars: int = 50000) -> str:
    """Build the full-text section with chunking and warnings."""
    if len(text) <= 8000:
        return text

    chunks = _chunk_text(text)
    total_chars = len(text)

    if total_chars > max_total_chars:
        truncated = text[:max_total_chars]
        last_break = truncated.rfind("\n\n")
        if last_break > 0:
            truncated = truncated[:last_break]
        included_chunks = _chunk_text(truncated)
        warning = (
            f"⚠ **正文过长警告**: 全文共 {total_chars} 字符，已截取前 {max_total_chars} 字符 "
            f"（{len(included_chunks)} 个分块）。剩余约 {total_chars - max_total_chars} 字符未包含。\n"
            f"建议对超长章节分批次润色。\n\n"
            f"---\n\n"
        )
        return warning + "\n\n".join(included_chunks)

    header = (
        f"全文共 {total_chars} 字符，{len(chunks)} 个分块。"
        f"每块保留段落 ID 范围以供定位。\n\n"
        f"---\n\n"
    )
    return header + "\n\n".join(chunks)


def find_author_draft(chapter: int) -> Optional[Path]:
    drafts_dir = ROOT / "chapters/drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    prefix = chapter_prefix(chapter)
    candidate = drafts_dir / f"{prefix}.author.md"
    if candidate.is_file():
        return candidate
    matches = sorted(drafts_dir.glob(f"{prefix}*author*"))
    return matches[0] if matches else None


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Polish Author Chapter")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, default=0)
    parser.add_argument("--input", type=str, default=None)
    parser.add_argument("--mode", type=str, default="preserve-author-style",
                        choices=list(POLISH_MODES.keys()),
                        help="润色模式")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    ROOT = get_root(args)

    if args.input:
        source_path = Path(args.input)
    elif args.chapter:
        source_path = find_author_draft(args.chapter)
    else:
        print("请指定 --chapter 或 --input")
        return 1

    if not source_path or not source_path.is_file():
        print(f"手写稿不存在: {source_path}")
        drafts_dir = ROOT / "chapters/drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        print(f"已创建目录 {drafts_dir.relative_to(ROOT)}/，请将手写章节放入此目录。")
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
    fulltext_section = _build_fulltext_section(text)
    output_path.write_text(
        lines[0] + "\n" + "\n".join(lines[1:]) + "\n\n## 手写稿正文\n\n" + fulltext_section,
        encoding="utf-8"
    )

    print(f"Polish brief written to {output_path.relative_to(ROOT)}")
    print(f"Mode: {args.mode} ({mode['label']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
