"""Relevance Resolver for Narrative Workbench.

Builds precision context packets from chapter plan structure and ledger queries.
This script is the CLI wrapper; reusable context logic lives in core.context.
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
from core.context import (  # noqa: E402
    AGENT_BUDGETS,
    AGENT_PROFILES,
    build_task_packet as core_build_task_packet,
    chapter_prefix,
    estimate_tokens,
    extract_yaml_field as _extract_yaml_field,
    find_plan_file as core_find_plan_file,
    inject_cast_states as core_inject_cast_states,
    inject_hooks as core_inject_hooks,
    inject_previous_chapter_summary as core_inject_previous_chapter_summary,
    inject_secrets as core_inject_secrets,
    read_file as _read_file,
    resolve_plan as core_resolve_plan,
    to_list as _to_list,
)


ROOT: Path = Path.cwd()


def _find_plan_file(chapter: int) -> Optional[Path]:
    return core_find_plan_file(ROOT, chapter)


def resolve_plan(chapter: int, plan_path: Optional[str] = None) -> dict:
    return core_resolve_plan(ROOT, chapter, plan_path)


def inject_cast_states(plan: dict) -> tuple[list[dict], list[dict]]:
    return core_inject_cast_states(ROOT, plan)


def inject_hooks(plan: dict, chapter: int) -> tuple[list[dict], list[dict]]:
    return core_inject_hooks(ROOT, plan, chapter)


def inject_secrets(plan: dict) -> tuple[list[dict], list[dict]]:
    return core_inject_secrets(ROOT, plan)


def inject_previous_chapter_summary(chapter: int, plan: dict) -> dict:
    return core_inject_previous_chapter_summary(ROOT, chapter)


def build_task_packet(agent: str, chapter: int, plan: dict) -> str:
    return core_build_task_packet(ROOT, agent, chapter, plan)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Relevance Resolver for Narrative Workbench")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument(
        "--agent",
        type=str,
        required=True,
        choices=["writer", "polish", "review", "fixer", "librarian"],
        help="目标 Agent",
    )
    parser.add_argument("--from-plan", type=str, default=None, help="章节计划文件路径（可选，默认自动查找）")
    parser.add_argument("--output", type=str, default=None, help="输出路径")
    args = parser.parse_args()
    ROOT = get_root(args)

    plan = resolve_plan(args.chapter, args.from_plan)
    if not find_plan_file_or_argument(args.chapter, args.from_plan):
        print(
            f"NOTE: No plan file found for chapter {args.chapter}. "
            "Using empty plan (all contexts will be minimal).",
            file=sys.stderr,
        )

    packet = build_task_packet(args.agent, args.chapter, plan)
    prefix = chapter_prefix(args.chapter)
    output_path = Path(args.output) if args.output else ROOT / "story/runtime" / f"{prefix}.{args.agent}.resolved.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(packet, encoding="utf-8")

    try:
        display_path = output_path.relative_to(ROOT)
    except ValueError:
        display_path = output_path
    print(f"Resolved task packet -> {display_path}")
    print(f"Agent: {args.agent}, Chapter: {args.chapter}")
    if plan.get("cast_ids"):
        print(f"Cast: {', '.join(plan['cast_ids'])}")
    if plan.get("hook_ids"):
        print(f"Hooks: {', '.join(plan['hook_ids'])}")
    return 0


def find_plan_file_or_argument(chapter: int, plan_path: Optional[str]) -> Optional[Path]:
    if plan_path:
        path = Path(plan_path)
        return path if path.is_file() else None
    return _find_plan_file(chapter)


if __name__ == "__main__":
    sys.exit(main())
