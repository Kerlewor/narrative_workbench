#!/usr/bin/env python3
"""Gatekeeper for Narrative Workbench.

This script is the CLI wrapper; reusable deterministic checks live in
core.gatekeeper.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from _project import add_root_argument, get_root
from core.context import chapter_prefix  # noqa: E402
from core.gatekeeper import (  # noqa: E402
    AI_PATTERNS,
    HARD_CONSTRAINT_PATTERNS,
    PIPELINE_STAGES,
    build_report as core_build_report,
    check_forbidden_patterns as core_check_forbidden_patterns,
    check_hook_sync as core_check_hook_sync,
    check_intent_status as core_check_intent_status,
    check_pipeline_files as core_check_pipeline_files,
    check_review_items_addressed as core_check_review_items_addressed,
    check_scene_handoff_status as core_check_scene_handoff_status,
    find_runtime_file as core_find_runtime_file,
)


ROOT: Path = Path.cwd()


def find_runtime_file(stage: str, chapter: int) -> Optional[Path]:
    return core_find_runtime_file(ROOT, stage, chapter)


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def check_pipeline_files(chapter: int) -> tuple[list[str], list[str]]:
    return core_check_pipeline_files(ROOT, chapter)


def check_review_items_addressed(chapter: int) -> tuple[bool, list[str]]:
    return core_check_review_items_addressed(ROOT, chapter)


def check_hook_sync(chapter: int) -> tuple[bool, list[str]]:
    return core_check_hook_sync(ROOT, chapter)


def check_forbidden_patterns(chapter: int) -> tuple[bool, list[str]]:
    return core_check_forbidden_patterns(ROOT, chapter)


def check_chapter_index(chapter: int) -> tuple[bool, list[str]]:
    return True, []


def check_intent_status(chapter: int) -> tuple[bool, list[str]]:
    return core_check_intent_status(ROOT, chapter)


def check_scene_handoff_status(chapter: int) -> tuple[bool, list[str], list[str]]:
    return core_check_scene_handoff_status(ROOT, chapter)


def build_report(chapter: int, stage: str) -> str:
    return core_build_report(ROOT, chapter, stage)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Gatekeeper for Narrative Workbench")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument(
        "--stage",
        type=str,
        default="final",
        choices=["intent", "writer", "polish", "review", "fixer", "final"],
        help="检查阶段 (default: final)",
    )
    parser.add_argument("--output", type=str, default=None, help="输出路径（默认 story/runtime/chapter-XXXX.gatekeeper.md）")
    args = parser.parse_args()
    ROOT = get_root(args)

    report = build_report(args.chapter, args.stage)
    if args.output:
        output_path = Path(args.output)
    else:
        prefix = chapter_prefix(args.chapter)
        output_path = ROOT / "story/runtime" / f"{prefix}.gatekeeper.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    try:
        display_path = output_path.relative_to(ROOT)
    except ValueError:
        display_path = output_path
    print(f"Gatekeeper report written to {display_path}")

    if "**FAILED**" in report:
        blocking_count = report.count("[BLOCKING]")
        print(f"RESULT: FAILED - {blocking_count} blocking issues")
        return 1
    print("RESULT: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
