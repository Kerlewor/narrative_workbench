#!/usr/bin/env python3
"""Audit a chapter text for formatting and style-risk signals."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from _project import add_root_argument, get_root
from core.style import RISK_WORDS, audit_text, count_cjk_words, paragraph_blocks


ROOT: Path = Path.cwd()


def audit(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    try:
        display_path = path.relative_to(ROOT)
    except ValueError:
        display_path = path
    print(f"text audit: {display_path}")
    code, lines = audit_text(text)
    for line in lines:
        print(line)
    return code


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

