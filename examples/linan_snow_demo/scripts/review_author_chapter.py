#!/usr/bin/env python3
"""Co-writing: Review Author Chapter.

Prepares an author-written chapter for Review Agent analysis.
This script generates a structured review brief — it does NOT call any
AI model, does NOT perform semantic review, and does NOT modify text.
The actual review is performed by Claude Code/Codex via the Review Agent.

Usage:
    python scripts/review_author_chapter.py --chapter 12
    python scripts/review_author_chapter.py --input chapters/drafts/my-chapter.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from _project import add_root_argument, get_root

ROOT: Path = Path.cwd()

REVIEW_BRIEF_TEMPLATE = """# Author Chapter Review Brief

## 审查对象
{source}

## 审查原则
- **不改正文。** 只输出问题清单。
- 每条问题标注：位置、严重度、问题描述、修改方向建议。
- 严重度分级：阻塞 / 高 / 中 / 低。
- 是否采纳每一条建议由作者决定。

## 检查维度
1. 角色人格违背（对照 Personality Lock 和 Behavioral Constraints）
2. 伏笔遗漏（对照半衰期到期的活跃 hook）
3. 秘密泄露风险（对照 intent/plan 中的"暂不掀"）
4. 前文状态冲突（对照 current_state）
5. 节奏失衡（连续高压无喘息 / 连续日常无推进）
6. AI 味或说明腔
7. 场景目标不清

## 输出格式
```markdown
# Author Chapter Review - Chapter {chapter}

## 阻塞问题
| 位置 | 问题 | 修改建议 |
|---|---|---|

## 高优先级
| 位置 | 问题 | 修改建议 |
|---|---|---|

## 中优先级
| 位置 | 问题 | 修改建议 |
|---|---|---|

## 低优先级 / 可选优化
| 位置 | 问题 | 建议 |
```
"""


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def _chunk_text(text: str, max_chunk_chars: int = 8000) -> list[str]:
    """Split text into paragraph-preserving chunks with IDs.

    Each chunk preserves paragraph boundaries and is annotated with
    paragraph range IDs. Returns chunks suitable for sequential review.
    """
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
    """Build the full-text section with chunking and warnings.

    For short texts (< 8000 chars), return the full text unmodified.
    For longer texts, chunk by paragraph with IDs, and warn if
    exceeding max_total_chars.
    """
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
            f"建议对超长章节分批次审查。\n\n"
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
    parser = argparse.ArgumentParser(description="Review Author Chapter")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, default=0, help="章节编号")
    parser.add_argument("--input", type=str, default=None, help="手写稿路径")
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

    text = source_path.read_text(encoding="utf-8")
    brief = REVIEW_BRIEF_TEMPLATE.format(
        source=str(source_path),
        chapter=args.chapter or "?",
    )

    if args.output:
        output_path = Path(args.output)
    else:
        prefix = chapter_prefix(args.chapter) if args.chapter else "custom"
        output_path = ROOT / "story/runtime" / f"{prefix}.author_review_brief.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fulltext_section = _build_fulltext_section(text)
    output_path.write_text(brief + "\n\n## 手写稿正文\n\n" + fulltext_section, encoding="utf-8")

    print(f"Review brief written to {output_path.relative_to(ROOT)}")
    print(f"Source: {source_path} ({len(text)} chars)")
    print("Next: 将本文件发送给 Review Agent 进行审查")
    return 0


if __name__ == "__main__":
    sys.exit(main())
