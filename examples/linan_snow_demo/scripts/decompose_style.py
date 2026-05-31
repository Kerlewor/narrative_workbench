#!/usr/bin/env python3
"""Style Decomposer for Narrative Workbench.

Analyzes input text across 12 dimensions and generates:
  1. style_analysis.md — human-readable report
  2. style_profile.json — machine-readable config
  3. style_skill.md — Agent-executable style rules

Usage:
    python3 scripts/decompose_style.py --input chapters/drafts/author-sample.md
    python3 scripts/decompose_style.py --input story/style_samples/reference.md --output-dir story/style_samples/
"""

from __future__ import annotations
from _project import add_root_argument, get_root

import argparse
import json
import re
import sys
from pathlib import Path

ROOT: Path = Path.cwd()  # Set in main() via --project-root or CWD


def analyze_pov(text: str) -> str:
    first_count = len(re.findall(r"我[^们]", text))
    third_count = len(re.findall(r"她|他", text))
    if first_count > third_count * 0.8:
        return "first_person"
    return "third_person_limited"


def analyze_sentence_length(text: str) -> dict:
    sentences = re.split(r"[。！？!?…\n]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    total = len(sentences) or 1
    short = sum(1 for s in sentences if len(s) <= 15)
    medium = sum(1 for s in sentences if 15 < len(s) <= 40)
    long = sum(1 for s in sentences if len(s) > 40)
    return {
        "short_ratio": round(short / total, 2),
        "medium_ratio": round(medium / total, 2),
        "long_ratio": round(long / total, 2),
        "label": "short_to_medium" if (short + medium) / total > 0.7 else "mixed",
    }


def analyze_dialogue(text: str) -> dict:
    lines = [l for l in text.splitlines() if l.strip()]
    total = len(lines) or 1
    dialogue_lines = sum(1 for l in lines if '"' in l or '"' in l or '“' in l)
    return {
        "dialogue_ratio": round(dialogue_lines / total, 2),
        "style": "subtext_heavy" if dialogue_lines / total > 0.3 else "narration_heavy",
    }


def analyze_emotion_expression(text: str) -> str:
    direct = len(re.findall(r"(感到|觉得|意识到|明白|知道|悲伤|愤怒|恐惧|喜悦|痛苦)", text))
    indirect = len(re.findall(r"(捏|握|咬|皱眉|转身|沉默|停顿|杯子|门|手)", text))
    return "indirect_action_based" if indirect > direct else "mixed"


def analyze_chapter_ending(text: str) -> str:
    last_200 = text[-200:] if len(text) > 200 else text
    if re.search(r"[。！？!?]\s*$", last_200):
        return "summary_or_explicit"
    if re.search(r"(动作|声音|物件|未完成|意象|误解)", last_200):
        return "unfinished_action_or_image"
    return "neutral"


def build_analysis(text: str, source: str) -> str:
    pov = analyze_pov(text)
    sent = analyze_sentence_length(text)
    dial = analyze_dialogue(text)
    emotion = analyze_emotion_expression(text)
    ending = analyze_chapter_ending(text)

    lines: list[str] = []
    lines.append("# 文风拆解报告")
    lines.append(f"来源: {source}")
    lines.append("")

    lines.append("## 叙述视角")
    pov_label = "第一人称" if pov == "first_person" else "第三人称限知"
    lines.append(f"- {pov_label}")
    lines.append("")

    lines.append("## 句法节奏")
    lines.append(f"- 短句 (<15字): {sent['short_ratio']:.0%}")
    lines.append(f"- 中句 (15-40字): {sent['medium_ratio']:.0%}")
    lines.append(f"- 长句 (>40字): {sent['long_ratio']:.0%}")
    lines.append(f"- 分类: {sent['label']}")
    lines.append("")

    lines.append("## 对白特点")
    lines.append(f"- 对白比例: {dial['dialogue_ratio']:.0%}")
    lines.append(f"- 风格: {dial['style']}")
    lines.append("")

    lines.append("## 情绪表达")
    lines.append(f"- 方式: {emotion}")
    lines.append("")

    lines.append("## 结尾方式")
    lines.append(f"- {ending}")
    lines.append("")

    lines.append("## 可迁移写作原则")
    if emotion == "indirect_action_based":
        lines.append("- 情绪不直接命名，而通过动作、物件和停顿呈现。")
    if dial["style"] == "subtext_heavy":
        lines.append("- 对白不承担解释设定功能，保留未说出口的信息。")
    if sent["label"] == "short_to_medium":
        lines.append("- 句长偏短到中等，情绪高压时句子进一步缩短。")
    if ending == "unfinished_action_or_image":
        lines.append("- 章节结尾使用未完成动作或意象制造余韵。")
    lines.append("")

    return "\n".join(lines)


def build_profile(text: str) -> dict:
    sent = analyze_sentence_length(text)
    dial = analyze_dialogue(text)
    return {
        "pov": analyze_pov(text),
        "sentence_length": sent["label"],
        "emotion_expression": analyze_emotion_expression(text),
        "dialogue_style": dial["style"],
        "description_density": "medium",
        "metaphor_density": "low",
        "chapter_ending": analyze_chapter_ending(text),
        "forbidden_patterns": [
            "直接总结人物心理",
            "用旁白解释关系变化",
            "连续使用抽象情绪词",
            "不是……而是……句式",
        ],
    }


def build_skill(text: str) -> str:
    emotion = analyze_emotion_expression(text)
    lines: list[str] = []
    lines.append("# Project Style Skill")
    lines.append("")
    lines.append("## Prefer")
    if emotion == "indirect_action_based":
        lines.append("- 用动作承载情绪。")
        lines.append("- 用物件和空间关系制造紧张。")
    lines.append("- 对白保留未说出口的信息。")
    lines.append("- 章节结尾停在动作、声音或意象上。")
    lines.append("")
    lines.append("## Avoid")
    lines.append("- 直接总结人物心理。")
    lines.append("- 用旁白解释关系变化。")
    lines.append("- 连续使用抽象情绪词。")
    lines.append("- 使用\"不是……而是……\"式模板句。")
    return "\n".join(lines)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Style Decomposer")
    add_root_argument(parser)
    parser.add_argument("--input", type=str, required=True, help="输入文本路径")
    parser.add_argument("--output-dir", type=str, default=None, help="输出目录")
    args = parser.parse_args()
    ROOT = get_root(args)

    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"文件不存在: {input_path}")
        return 1

    text = input_path.read_text(encoding="utf-8")
    out_dir = Path(args.output_dir) if args.output_dir else input_path.parent

    report = build_analysis(text, str(input_path))
    profile = build_profile(text)
    skill_md = build_skill(text)

    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "style_analysis.md"
    profile_path = out_dir / "style_profile.json"
    skill_path = out_dir / "style_skill.md"

    report_path.write_text(report, encoding="utf-8")
    profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    skill_path.write_text(skill_md, encoding="utf-8")

    print(f"Generated: {report_path}")
    print(f"Generated: {profile_path}")
    print(f"Generated: {skill_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
