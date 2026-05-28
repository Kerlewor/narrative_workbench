#!/usr/bin/env python3
"""Style Report for Narrative Workbench.

Analyzes chapter text for sentence length distribution, dialogue ratio,
AI-style pattern hits, and generates a quantitative style report.

Usage:
    python3 scripts/style_report.py --chapter 12
    python3 scripts/style_report.py --input chapters/0012_标题.md

Output:
    story/runtime/chapter-0012.style_report.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]

AI_PATTERNS = [
    (r"某种难以言说的", "AI 味: 抽象情绪短语"),
    (r"仿佛有什么东西", "AI 味: 万能氛围句"),
    (r"不是.{1,20}而是", "AI 味: 否定式排比"),
    (r"命运的齿轮", "主题金句"),
    (r"空气仿佛凝固", "万能氛围句"),
    (r"她终于意识到", "抽象心理总结"),
    (r"这一刻，她明白", "主题金句"),
    (r"前所未有的.{1,10}感", "抽象情绪命名"),
    (r"内心充满了", "直接心理描写"),
    (r"这就是.{1,20}的.{1,10}意义", "主题总结句"),
    (r"所有的.{1,10}都.{1,10}了答案", "主题升华句"),
    (r"然而", "连接词密度"),
    (r"因此", "连接词密度"),
    (r"于是", "连接词密度"),
    (r"蓦然", "AI 高频词"),
    (r"宛若", "AI 高频词"),
    (r"弥漫", "AI 高频词"),
    (r"充斥", "AI 高频词"),
]


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def find_chapter_file(chapter: int) -> Optional[Path]:
    prefix = chapter_prefix(chapter)
    matches = sorted((ROOT / "chapters").glob(f"{prefix}_*.md"))
    return matches[0] if matches else None


def analyze_text(text: str) -> dict:
    lines = [l for l in text.splitlines() if l.strip() and not l.startswith("#")]
    if not lines:
        return {}

    sentences = re.split(r"[。！？!?…\n]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    short_sentences = [s for s in sentences if len(s) <= 15]
    medium_sentences = [s for s in sentences if 15 < len(s) <= 40]
    long_sentences = [s for s in sentences if len(s) > 40]
    total = len(sentences) or 1

    dialogue_lines = sum(1 for line in lines if '"' in line or '"' in line or '“' in line)

    pattern_hits: dict[str, int] = {}
    for pattern, label in AI_PATTERNS:
        hits = len(re.findall(pattern, text))
        if hits > 0:
            pattern_hits[label] = hits

    paragraphs = [l for l in lines if l.strip()]
    short_paras = sum(1 for p in paragraphs if len(p) < 20)

    return {
        "total_sentences": total,
        "short_ratio": round(len(short_sentences) / total, 2),
        "medium_ratio": round(len(medium_sentences) / total, 2),
        "long_ratio": round(len(long_sentences) / total, 2),
        "dialogue_lines": dialogue_lines,
        "dialogue_ratio": round(dialogue_lines / max(len(lines), 1), 2),
        "total_paragraphs": len(paragraphs),
        "short_paragraphs": short_paras,
        "pattern_hits": pattern_hits,
        "total_chars": len(text),
        "total_lines": len(lines),
    }


def build_report(chapter: int, input_path: Optional[str] = None) -> str:
    if input_path:
        path = Path(input_path)
    else:
        path = find_chapter_file(chapter)

    if not path or not path.is_file():
        return f"# Style Report - Chapter {chapter}\n\n文件不存在: {path}"

    text = path.read_text(encoding="utf-8")
    stats = analyze_text(text)

    lines: list[str] = []
    lines.append(f"# Style Report - Chapter {chapter}")
    lines.append(f"来源: {path.relative_to(ROOT)}")
    lines.append("")

    lines.append("## 句长分布")
    lines.append(f"- 短句 (<15字): {stats.get('short_ratio', 0):.0%}")
    lines.append(f"- 中句 (15-40字): {stats.get('medium_ratio', 0):.0%}")
    lines.append(f"- 长句 (>40字): {stats.get('long_ratio', 0):.0%}")
    lines.append("")

    lines.append("## 对白密度")
    lines.append(f"- 对白行数: {stats.get('dialogue_lines', 0)}")
    lines.append(f"- 对白比例: {stats.get('dialogue_ratio', 0):.0%}")
    lines.append("")

    lines.append("## 段落形态")
    lines.append(f"- 总段落: {stats.get('total_paragraphs', 0)}")
    lines.append(f"- 短段落 (<20字): {stats.get('short_paragraphs', 0)}")
    lines.append("")

    lines.append("## 文本统计")
    lines.append(f"- 总字符: {stats.get('total_chars', 0)}")
    lines.append(f"- 有效行: {stats.get('total_lines', 0)}")
    lines.append(f"- 总句数: {stats.get('total_sentences', 0)}")
    lines.append("")

    pattern_hits = stats.get("pattern_hits", {})
    if pattern_hits:
        lines.append("## AI 味模式命中")
        for label, count in sorted(pattern_hits.items(), key=lambda x: -x[1]):
            lines.append(f"- {label}: {count} 处")
    else:
        lines.append("## AI 味模式命中")
        lines.append("- 未检测到已知 AI 味模式")
    lines.append("")

    lines.append("## 建议")
    short_r = stats.get("short_ratio", 0)
    long_r = stats.get("long_ratio", 0)
    dialogue_r = stats.get("dialogue_ratio", 0)

    suggestions: list[str] = []
    if short_r > 0.6:
        suggestions.append("短句比例偏高 (>60%)，考虑合并部分连续短段。")
    if long_r > 0.3:
        suggestions.append("长句比例偏高 (>30%)，考虑在高冲突场景中缩短句长。")
    if dialogue_r > 0.5:
        suggestions.append("对白比例偏高 (>50%)，确认场景推进是否充分。")
    if dialogue_r < 0.15 and stats.get("total_sentences", 0) > 50:
        suggestions.append("对白比例偏低 (<15%)，考虑增加对话攻防。")
    if pattern_hits:
        top = max(pattern_hits, key=pattern_hits.get)
        suggestions.append(f"最常见的 AI 味模式为「{top}」，建议 Polish 阶段重点关注。")

    if suggestions:
        for s in suggestions:
            lines.append(f"- {s}")
    else:
        lines.append("- 各项指标在合理范围内，无需特别调整。")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Style Report for Narrative Workbench")
    parser.add_argument("--chapter", type=int, default=0, help="章节编号")
    parser.add_argument("--input", type=str, default=None, help="直接指定文件路径")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    report = build_report(args.chapter, args.input)

    if args.output:
        output_path = Path(args.output)
    else:
        prefix = chapter_prefix(args.chapter) if args.chapter else "custom"
        output_path = ROOT / "story/runtime" / f"{prefix}.style_report.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Style report written to {output_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
