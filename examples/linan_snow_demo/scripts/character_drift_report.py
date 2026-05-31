#!/usr/bin/env python3
"""Character Drift Report for Narrative Workbench.

Scans chapter text against structured character constraints (cannot_do,
stress_response, speech_style) and outputs potential drift warnings.
Does NOT make final judgments — only flags items for Review attention.

Usage:
    python3 scripts/character_drift_report.py --chapter 12
    python3 scripts/character_drift_report.py --chapter 12 --character 林半夏
"""

from __future__ import annotations
from _project import add_root_argument, get_root

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

ROOT: Path = Path.cwd()  # Set in main() via --project-root or CWD


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def find_chapter_file(chapter: int) -> Optional[Path]:
    prefix = chapter_prefix(chapter)
    matches = sorted((ROOT / "chapters").glob(f"{prefix}_*.md"))
    if matches:
        return matches[0]
    polish = ROOT / "story/runtime" / f"{prefix}.polish.md"
    if polish.is_file():
        return polish
    fixer = ROOT / "story/runtime" / f"{prefix}.fixer.md"
    return fixer if fixer.is_file() else None


def parse_character_constraints(card_path: Path) -> dict:
    text = card_path.read_text(encoding="utf-8")
    constraints: dict = {
        "name": card_path.stem,
        "cannot_do": [],
        "stress_response": [],
        "speech_style": [],
    }

    in_section = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("##") and "禁止写法" in stripped:
            in_section = "forbidden"
            continue
        elif stripped.startswith("##") and "对白风味" in stripped:
            in_section = "speech"
            continue
        elif stripped.startswith("##") and "Behavioral" in stripped:
            in_section = "constraints"
            continue
        elif stripped.startswith("##"):
            in_section = None
            continue

        if in_section == "forbidden" and stripped.startswith(("- ", "1. ", "2. ", "3. ")):
            item = re.sub(r"^[\d.-]+\s*", "", stripped)
            if item:
                constraints["cannot_do"].append(item)
        elif in_section == "speech" and stripped.startswith("- "):
            item = stripped[2:]
            if item:
                constraints["speech_style"].append(item)
        elif in_section == "constraints" and stripped.startswith(("- ", "1. ", "2. ", "3. ")):
            item = re.sub(r"^[\d.-]+\s*", "", stripped)
            if item:
                constraints["stress_response"].append(item)

    return constraints


def scan_text_for_patterns(text: str, constraints: dict) -> list[dict]:
    issues: list[dict] = []

    for item in constraints.get("cannot_do", []):
        keywords = re.sub(r"[的得了着过在地]", "", item)
        keywords_short = keywords[:6] if len(keywords) > 6 else keywords
        if len(keywords_short) >= 2 and keywords_short in text:
            context = find_context(text, keywords_short)
            issues.append({
                "type": "cannot_do_warning",
                "character": constraints["name"],
                "constraint": item,
                "context": context,
            })

    speech_items = constraints.get("speech_style", [])
    if speech_items:
        dialogue_patterns = re.findall(r'"[^"]{20,}"', text)
        if dialogue_patterns and any("长句" in s or "短句" in s for s in speech_items):
            for dp in dialogue_patterns[:3]:
                if "短句" in str(speech_items) and len(dp) > 60:
                    issues.append({
                        "type": "speech_style_mismatch",
                        "character": constraints["name"],
                        "constraint": "对白应为短句",
                        "context": dp[:80] + "...",
                    })
                    break

    return issues


def find_context(text: str, keyword: str) -> str:
    idx = text.find(keyword)
    if idx < 0:
        return "(未找到上下文)"
    start = max(0, idx - 30)
    end = min(len(text), idx + 80)
    return text[start:end].replace("\n", " ")


def build_report(chapter: int, character_name: Optional[str] = None) -> str:
    chapter_path = find_chapter_file(chapter)
    if not chapter_path:
        return f"# Character Drift Report - Chapter {chapter}\n\n章节文件不存在"

    chapter_text = chapter_path.read_text(encoding="utf-8")
    roles_dir = ROOT / "story/roles"
    all_issues: list[dict] = []

    for card_path in sorted(roles_dir.glob("*.md")):
        if card_path.name.startswith("_template"):
            continue
        if character_name and card_path.stem != character_name:
            continue
        constraints = parse_character_constraints(card_path)
        if not constraints["cannot_do"] and not constraints["speech_style"]:
            continue
        issues = scan_text_for_patterns(chapter_text, constraints)
        all_issues.extend(issues)

    lines: list[str] = []
    lines.append(f"# Character Drift Report - Chapter {chapter}")
    lines.append("")
    lines.append("> 本报告仅输出预警，不做最终判断。请 Review Agent 逐条评估。")
    lines.append("")

    if all_issues:
        lines.append(f"## 发现 {len(all_issues)} 个疑似漂移")
        lines.append("")
        for i, issue in enumerate(all_issues, 1):
            lines.append(f"### {i}. [{issue['type']}] {issue['character']}")
            lines.append(f"- 约束: {issue['constraint']}")
            lines.append(f"- 上下文: ...{issue['context']}...")
            lines.append("")
    else:
        lines.append("## 未发现疑似漂移")
        lines.append("")
        lines.append("当前章节中角色行为与约束无明显冲突。")

    lines.append("## 建议")
    if all_issues:
        lines.append(f"- 将以上 {len(all_issues)} 个预警提交 Review Agent 逐条评估。")
        lines.append("- 区分弧光成长（接受）与设定漂移（修正）。")
    else:
        lines.append("- 无需特别处理。")

    return "\n".join(lines)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Character Drift Report")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--character", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    ROOT = get_root(args)

    report = build_report(args.chapter, args.character)

    if args.output:
        output_path = Path(args.output)
    else:
        prefix = chapter_prefix(args.chapter)
        output_path = ROOT / "story/runtime" / f"{prefix}.character_drift.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Character drift report written to {output_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
