"""Text style statistics and audit helpers."""

from __future__ import annotations

import re
from math import ceil
from pathlib import Path
from typing import Optional

from core.context import chapter_prefix


RISK_WORDS = [
    "然而",
    "因此",
    "于是",
    "此刻",
    "蓦然",
    "宛若",
    "弥漫",
    "充斥",
    "颇为",
    "意识到",
    "感到",
    "明白",
    "知道",
]

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


def count_cjk_words(text: str) -> int:
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    latin_words = re.findall(r"[A-Za-z0-9]+(?:[-_'][A-Za-z0-9]+)*", text)
    latin_units = sum(max(1, ceil(len(word) / 3)) for word in latin_words)
    return len(cjk) + latin_units


def paragraph_blocks(text: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]


def audit_text(text: str) -> tuple[int, list[str]]:
    paragraphs = paragraph_blocks(text)
    word_count = count_cjk_words(text)
    dialogue_count = len(re.findall(r"“[^”]+”", text))
    bad_quotes = len(re.findall(r"[「」『』]", text))
    western_dialogue = len(re.findall(r'(^|[\s])"[^"\n]{2,}"', text, flags=re.MULTILINE))
    parenthetical_inner = len(re.findall(r"（[^）]{4,120}[。！？!?][^）]*）", text))
    dash_count = text.count("——")
    short_paragraphs = [paragraph for paragraph in paragraphs if count_cjk_words(paragraph) <= 40]

    max_short_run = 0
    current = 0
    for paragraph in paragraphs:
        if count_cjk_words(paragraph) <= 40:
            current += 1
            max_short_run = max(max_short_run, current)
        else:
            current = 0

    risk_counts = {word: text.count(word) for word in RISK_WORDS if text.count(word)}
    repeated_le = 0
    for paragraph in paragraphs:
        sentences = re.split(r"[。！？!?]\s*", paragraph)
        endings = [sentence.strip().endswith("了") for sentence in sentences if sentence.strip()]
        for index in range(len(endings) - 2):
            if endings[index] and endings[index + 1] and endings[index + 2]:
                repeated_le += 1

    lines = [
        f"wordCount: {word_count}",
        f"paragraphs: {len(paragraphs)}",
        f"dialoguePairs: {dialogue_count}",
        f"shortParagraphs<=40: {len(short_paragraphs)}",
        f"maxShortParagraphRun: {max_short_run}",
        f"dashCount: {dash_count}",
        f"badCJKQuoteMarks「」『』: {bad_quotes}",
        f"westernDialogueQuotes: {western_dialogue}",
        f"possibleParentheticalInnerMonologue: {parenthetical_inner}",
        f"three-sentence repeated sentence-final 了 runs: {repeated_le}",
    ]

    if risk_counts:
        lines.append("riskWords:")
        for word, count in sorted(risk_counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {word}: {count}")

    failed = False
    if bad_quotes:
        lines.append("ERROR: found forbidden quote marks 「」『』")
        failed = True
    if western_dialogue:
        lines.append("WARN: possible western dialogue quotes found")
    if parenthetical_inner:
        lines.append("WARN: possible parenthetical inner monologue found")
    if max_short_run > 4:
        lines.append("WARN: continuous short paragraph run exceeds 4")
    if repeated_le:
        lines.append("WARN: repeated sentence-final 了 pattern found")
    return (1 if failed else 0), lines


def find_chapter_file(root: Path, chapter: int) -> Optional[Path]:
    prefix = chapter_prefix(chapter)
    matches = sorted((root / "chapters").glob(f"{prefix}_*.md"))
    return matches[0] if matches else None


def analyze_text(text: str) -> dict:
    lines = [line for line in text.splitlines() if line.strip() and not line.startswith("#")]
    if not lines:
        return {}

    sentences = re.split(r"[。！？!?…\n]+", text)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    short_sentences = [sentence for sentence in sentences if len(sentence) <= 15]
    medium_sentences = [sentence for sentence in sentences if 15 < len(sentence) <= 40]
    long_sentences = [sentence for sentence in sentences if len(sentence) > 40]
    total = len(sentences) or 1

    dialogue_lines = sum(1 for line in lines if '"' in line or "“" in line)
    pattern_hits: dict[str, int] = {}
    for pattern, label in AI_PATTERNS:
        hits = len(re.findall(pattern, text))
        if hits > 0:
            pattern_hits[label] = hits

    paragraphs = [line for line in lines if line.strip()]
    short_paragraphs = sum(1 for paragraph in paragraphs if len(paragraph) < 20)

    return {
        "total_sentences": total,
        "short_ratio": round(len(short_sentences) / total, 2),
        "medium_ratio": round(len(medium_sentences) / total, 2),
        "long_ratio": round(len(long_sentences) / total, 2),
        "dialogue_lines": dialogue_lines,
        "dialogue_ratio": round(dialogue_lines / max(len(lines), 1), 2),
        "total_paragraphs": len(paragraphs),
        "short_paragraphs": short_paragraphs,
        "pattern_hits": pattern_hits,
        "total_chars": len(text),
        "total_lines": len(lines),
    }


def build_style_report(root: Path, chapter: int, input_path: Optional[str] = None) -> str:
    if input_path:
        path = Path(input_path).resolve()
    else:
        path = find_chapter_file(root, chapter)

    if not path or not path.is_file():
        return f"# Style Report - Chapter {chapter}\n\n文件不存在: {path}"

    text = path.read_text(encoding="utf-8")
    stats = analyze_text(text)
    try:
        source = path.relative_to(root)
    except ValueError:
        source = path

    lines: list[str] = [
        f"# Style Report - Chapter {chapter}",
        f"来源: {source}",
        "",
        "## 句长分布",
        f"- 短句 (<15字): {stats.get('short_ratio', 0):.0%}",
        f"- 中句 (15-40字): {stats.get('medium_ratio', 0):.0%}",
        f"- 长句 (>40字): {stats.get('long_ratio', 0):.0%}",
        "",
        "## 对白密度",
        f"- 对白行数: {stats.get('dialogue_lines', 0)}",
        f"- 对白比例: {stats.get('dialogue_ratio', 0):.0%}",
        "",
        "## 段落形态",
        f"- 总段落: {stats.get('total_paragraphs', 0)}",
        f"- 短段落 (<20字): {stats.get('short_paragraphs', 0)}",
        "",
        "## 文本统计",
        f"- 总字符: {stats.get('total_chars', 0)}",
        f"- 有效行: {stats.get('total_lines', 0)}",
        f"- 总句数: {stats.get('total_sentences', 0)}",
        "",
    ]

    pattern_hits = stats.get("pattern_hits", {})
    lines.append("## AI 味模式命中")
    if pattern_hits:
        for label, count in sorted(pattern_hits.items(), key=lambda item: -item[1]):
            lines.append(f"- {label}: {count} 处")
    else:
        lines.append("- 未检测到已知 AI 味模式")
    lines.append("")

    lines.append("## 建议")
    short_ratio = stats.get("short_ratio", 0)
    long_ratio = stats.get("long_ratio", 0)
    dialogue_ratio = stats.get("dialogue_ratio", 0)
    suggestions: list[str] = []
    if short_ratio > 0.6:
        suggestions.append("短句比例偏高 (>60%)，考虑合并部分连续短段。")
    if long_ratio > 0.3:
        suggestions.append("长句比例偏高 (>30%)，考虑在高冲突场景中缩短句长。")
    if dialogue_ratio > 0.5:
        suggestions.append("对白比例偏高 (>50%)，确认场景推进是否充分。")
    if dialogue_ratio < 0.15 and stats.get("total_sentences", 0) > 50:
        suggestions.append("对白比例偏低 (<15%)，考虑增加对话攻防。")
    if pattern_hits:
        top = max(pattern_hits, key=pattern_hits.get)
        suggestions.append(f"最常见的 AI 味模式为「{top}」，建议 Polish 阶段重点关注。")

    if suggestions:
        lines.extend(f"- {suggestion}" for suggestion in suggestions)
    else:
        lines.append("- 各项指标在合理范围内，无需特别调整。")
    return "\n".join(lines)
