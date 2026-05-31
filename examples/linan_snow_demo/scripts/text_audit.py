#!/usr/bin/env python3
"""Audit a chapter text for formatting and style-risk signals.

Usage:
    python scripts/text_audit.py chapters/0001_title.md
"""

from __future__ import annotations
from _project import add_root_argument, get_root

import argparse
import re
from pathlib import Path


ROOT: Path = Path.cwd()  # Set in main() via --project-root or CWD

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


def count_cjk_words(text: str) -> int:
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    latin_words = re.findall(r"[A-Za-z0-9]+(?:[-_'][A-Za-z0-9]+)*", text)
    return len(cjk) + len(latin_words)


def paragraph_blocks(text: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]


def audit(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    paragraphs = paragraph_blocks(text)
    word_count = count_cjk_words(text)
    dialogue_count = len(re.findall(r"“[^”]+”", text))
    bad_quotes = len(re.findall(r"[「」『』]", text))
    western_dialogue = len(re.findall(r'(^|[\s])"[^"\n]{2,}"', text, flags=re.MULTILINE))
    parenthetical_inner = len(re.findall(r"（[^）]{4,120}[。！？!?][^）]*）", text))
    dash_count = text.count("——")
    short_paragraphs = [p for p in paragraphs if count_cjk_words(p) <= 40]

    max_short_run = 0
    current = 0
    for p in paragraphs:
        if count_cjk_words(p) <= 40:
            current += 1
            max_short_run = max(max_short_run, current)
        else:
            current = 0

    risk_counts = {word: text.count(word) for word in RISK_WORDS if text.count(word)}
    repeated_le = 0
    for p in paragraphs:
        sentences = re.split(r"[。！？!?]\s*", p)
        endings = [s.strip().endswith("了") for s in sentences if s.strip()]
        for i in range(len(endings) - 2):
            if endings[i] and endings[i + 1] and endings[i + 2]:
                repeated_le += 1

    print(f"text audit: {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    print(f"wordCount: {word_count}")
    print(f"paragraphs: {len(paragraphs)}")
    print(f"dialoguePairs: {dialogue_count}")
    print(f"shortParagraphs<=40: {len(short_paragraphs)}")
    print(f"maxShortParagraphRun: {max_short_run}")
    print(f"dashCount: {dash_count}")
    print(f"badCJKQuoteMarks「」『』: {bad_quotes}")
    print(f"westernDialogueQuotes: {western_dialogue}")
    print(f"possibleParentheticalInnerMonologue: {parenthetical_inner}")
    print(f"three-sentence repeated sentence-final 了 runs: {repeated_le}")

    if risk_counts:
        print("riskWords:")
        for word, count in sorted(risk_counts.items(), key=lambda item: (-item[1], item[0])):
            print(f"- {word}: {count}")

    failed = False
    if bad_quotes:
        print("ERROR: found forbidden quote marks 「」『』")
        failed = True
    if western_dialogue:
        print("WARN: possible western dialogue quotes found")
    if parenthetical_inner:
        print("WARN: possible parenthetical inner monologue found")
    if max_short_run > 4:
        print("WARN: continuous short paragraph run exceeds 4")
    if repeated_le:
        print("WARN: repeated sentence-final 了 pattern found")

    return 1 if failed else 0


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser()
    add_root_argument(parser)
    parser.add_argument("file", help="chapter markdown file")
    args = parser.parse_args()
    ROOT = get_root(args)
    path = Path(args.file)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        print(f"ERROR: file not found: {path}")
        return 1
    return audit(path)


if __name__ == "__main__":
    raise SystemExit(main())

