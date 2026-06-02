#!/usr/bin/env python3
"""Prompt Compiler for Narrative Workbench."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from _project import add_root_argument, get_root
from core.context import chapter_prefix
from core.prompt import (  # noqa: E402
    AGENT_BASE_FILES,
    HARD_CONSTRAINTS,
    PROJECT_RULE_FILES,
    build_layer_base as core_build_layer_base,
    build_layer_project_rules as core_build_layer_project_rules,
    build_layer_task as core_build_layer_task,
    build_output_contract,
    compile_prompt as core_compile_prompt,
    find_runtime_file as core_find_runtime_file,
    read_summary,
)


ROOT: Path = Path.cwd()
CHAPTER_DRIVER_FILES: list[tuple[str, str]] = [
    ("intent", "本章 Intent"),
    ("plan", "本章 Plan"),
    ("context", "上下文包"),
]


def find_runtime_file(pattern: str, chapter: int) -> Optional[Path]:
    return core_find_runtime_file(ROOT, pattern, chapter)


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def build_layer_base(agent: str) -> str:
    return core_build_layer_base(ROOT, agent)


def build_layer_project_rules() -> str:
    return core_build_layer_project_rules(ROOT)


def build_layer_task(chapter: int, agent: str, context_path: Optional[str] = None) -> str:
    return core_build_layer_task(ROOT, chapter, agent, context_path)


def compile_prompt(agent: str, chapter: int, context_path: Optional[str] = None) -> str:
    return core_compile_prompt(ROOT, agent, chapter, context_path)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Prompt Compiler for Narrative Workbench")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument(
        "--agent",
        type=str,
        required=True,
        choices=["writer", "polish", "review", "fixer", "librarian"],
        help="目标 Agent",
    )
    parser.add_argument("--context", type=str, default=None, help="预构建的上下文包路径（可选，默认自动查找）")
    parser.add_argument("--output", type=str, default=None, help="输出路径（默认 story/runtime/chapter-XXXX.<agent>.prompt.md）")
    args = parser.parse_args()
    ROOT = get_root(args)

    prompt = compile_prompt(args.agent, args.chapter, args.context)
    if args.output:
        output_path = Path(args.output)
    else:
        prefix = chapter_prefix(args.chapter)
        output_path = ROOT / "story/runtime" / f"{prefix}.{args.agent}.prompt.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prompt, encoding="utf-8")

    try:
        display_path = output_path.relative_to(ROOT)
    except ValueError:
        display_path = output_path
    print(f"Compiled prompt written to {display_path}")
    print(f"Agent: {args.agent}, Chapter: {args.chapter}")
    print(f"Lines: {prompt.count(chr(10)) + 1}, Estimated tokens: ~{len(prompt) // 2}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
