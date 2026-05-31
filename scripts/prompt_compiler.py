#!/usr/bin/env python3
"""Prompt Compiler for Narrative Workbench.

Compiles per-agent prompts using a three-layer structure:
  1. Base Prompt — agent role definition (from agents/*.md, never changes)
  2. Project Rules — book rules, genre constraints, style rules
  3. Task Injection — chapter intent/plan, context packet, risk alerts

Usage:
    python3 scripts/prompt_compiler.py --chapter 12 --agent writer
    python3 scripts/prompt_compiler.py --chapter 12 --agent review
    python3 scripts/prompt_compiler.py --chapter 12 --agent writer --context runtime/chapter-0012.writer.context.md

Output:
    story/runtime/chapter-0012.<agent>.prompt.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from _project import add_root_argument, get_root

ROOT: Path = Path.cwd()

AGENT_BASE_FILES = {
    "writer": "agents/writer.md",
    "polish": "agents/polish.md",
    "review": "agents/review.md",
    "fixer": "agents/fixer.md",
    "librarian": "agents/project-librarian.md",
}

PROJECT_RULE_FILES: list[tuple[str, str]] = [
    ("story/book_rules.md", "本书硬规则"),
    ("story/style_blacklist.md", "文笔负面清单"),
    ("story/style_profile.md", "文风画像"),
    ("story/system_protocol.md", "系统协议（浓缩）"),
    ("story/state_contract.md", "状态同步契约"),
]

CHAPTER_DRIVER_FILES: list[tuple[str, str]] = [
    ("intent", "本章 Intent"),
    ("plan", "本章 Plan"),
    ("context", "上下文包"),
]

HARD_CONSTRAINTS = [
    "不得改写 canonical 文件。",
    "不得自行新增重大设定。",
    "不得跳过本章计划中的核心事件。",
    "不得提前泄露 intent/plan 中标注为\"暂不掀\"的内容。",
    "输出必须包含 handoff 摘要。",
]


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def find_runtime_file(pattern: str, chapter: int) -> Optional[Path]:
    prefix = chapter_prefix(chapter)
    candidate = ROOT / "story/runtime" / f"{prefix}.{pattern}.md"
    if candidate.is_file():
        return candidate
    glob_pattern = f"{prefix}.*{pattern}*.md"
    matches = sorted(
        p for p in (ROOT / "story/runtime").glob(glob_pattern)
        if not p.name.endswith((".context.md", ".prompt.md", ".gatekeeper.md"))
    )
    return matches[0] if matches else None


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def read_summary(path: Path, max_lines: int = 40) -> str:
    if not path.is_file():
        return "(文件不存在)"
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines]) + f"\n\n... (共 {len(lines)} 行，已截断)"


def build_layer_base(agent: str) -> str:
    """Layer 1: Agent role definition from agents/*.md"""
    agent_file = AGENT_BASE_FILES.get(agent)
    if not agent_file:
        return f"(未知 Agent: {agent})"

    path = ROOT / agent_file
    if not path.is_file():
        return f"(Agent 文件不存在: {agent_file})"

    return read_file(path)


def build_layer_project_rules() -> str:
    """Layer 2: Project-wide rules that rarely change."""
    parts: list[str] = []
    parts.append("## 2. 项目规则\n")

    for rel, label in PROJECT_RULE_FILES:
        path = ROOT / rel
        if path.is_file():
            content = read_summary(path, 50)
            parts.append(f"### {label}\n")
            parts.append(content)
            parts.append("")

    parts.append("### 硬性约束\n")
    for constraint in HARD_CONSTRAINTS:
        parts.append(f"- {constraint}")
    parts.append("")

    return "\n".join(parts)


def build_layer_task(chapter: int, agent: str, context_path: Optional[str] = None) -> str:
    """Layer 3: Chapter-specific task injection."""
    parts: list[str] = []
    parts.append("## 3. 本章任务\n")

    intent_path = find_runtime_file("intent", chapter)
    if intent_path:
        parts.append(f"### 本章 Intent\n")
        parts.append(read_file(intent_path))
        parts.append("")
    else:
        parts.append(f"### 本章 Intent\n")
        parts.append(f"(intent 文件不存在: 章节 {chapter} 尚未规划)")
        parts.append("")

    plan_path = find_runtime_file("plan", chapter)
    if plan_path:
        parts.append(f"### 本章 Plan\n")
        parts.append(read_file(plan_path))
        parts.append("")
    else:
        parts.append(f"### 本章 Plan\n")
        parts.append(f"(plan 文件不存在)")
        parts.append("")

    if context_path:
        ctx_p = Path(context_path)
        if ctx_p.is_file():
            parts.append(f"### 上下文包\n")
            parts.append(read_summary(ctx_p, 200))
            parts.append("")
    else:
        ctx = find_runtime_file(f"{agent}.context", chapter)
        if ctx and ctx.is_file():
            parts.append(f"### 上下文包\n")
            parts.append(read_summary(ctx, 200))
            parts.append("")

    parts.append("### 风险提示\n")
    parts.append("- 检查 intent/plan 中标注为\"暂不掀\"的内容。")

    hooks_path = ROOT / "story/pending_hooks.md"
    if hooks_path.is_file():
        hooks_text = read_file(hooks_path)
        expired: list[str] = []
        for line in hooks_text.splitlines():
            if not line.startswith("| H"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 11:
                continue
            try:
                hook_id = cells[0]
                status = cells[3]
                last_advanced = cells[5]
                half_life = cells[10]
                if status in ("resolved", "dropped", "dormant"):
                    continue
                if not last_advanced.isdigit() or not half_life.isdigit():
                    continue
                last_ch = int(last_advanced)
                hl = int(half_life)
                if chapter - last_ch > hl:
                    expired.append(f"{hook_id} (Ch{last_ch}, 半衰期{hl})")
            except (ValueError, IndexError):
                continue
        if expired:
            parts.append(f"- **半衰期到期 hook ({len(expired)} 个):** {', '.join(expired)}")
        else:
            parts.append("- 半衰期检查: 无到期 hook")
    parts.append("")

    return "\n".join(parts)


def build_output_contract(agent: str, chapter: int) -> str:
    """Output contract section."""
    prefix = chapter_prefix(chapter)
    output_map = {
        "writer": f"story/runtime/{prefix}.writer.md",
        "polish": f"story/runtime/{prefix}.polish.md",
        "review": f"story/runtime/{prefix}.review.md",
        "fixer": f"story/runtime/{prefix}.fixer.md",
        "librarian": f"story/runtime/session-YYYYMMDD-context.md",
    }

    lines: list[str] = []
    lines.append("## 4. 输出契约\n")
    lines.append(f"- 输出文件: `{output_map.get(agent, f'story/runtime/{prefix}.<stage>.md')}`")
    lines.append("- 输出必须包含完整的章节草稿/润色稿/审阅报告/修复稿（根据 Agent 职责）。")
    lines.append("- 同时生成 handoff 摘要，记录偏离、未处理问题和事实变更声明。")
    lines.append("- 不得修改 canonical 文件。")
    lines.append("")

    return "\n".join(lines)


def compile_prompt(agent: str, chapter: int, context_path: Optional[str] = None) -> str:
    """Compile the full three-layer prompt."""
    parts: list[str] = []

    name_map = {
        "writer": "Writer Agent - Chapter Task",
        "polish": "Polish Agent - Chapter Task",
        "review": "Review Agent - Chapter Task",
        "fixer": "Fixer Agent - Chapter Task",
        "librarian": "Project Librarian - Context Packet",
    }

    parts.append(f"# {name_map.get(agent, f'{agent.upper()} Agent')} {chapter}\n")
    parts.append(f"> 本章编译时间: 自动生成")
    parts.append(f"> Agent: {agent}")
    parts.append(f"> 章节: {chapter}")
    parts.append(f"> 来源文件: agents/{agent}.md + 项目规则 + runtime 文件\n")

    parts.append("## 1. Agent 角色定义\n")
    parts.append(build_layer_base(agent))
    parts.append("")

    parts.append(build_layer_project_rules())
    parts.append("")

    parts.append(build_layer_task(chapter, agent, context_path))
    parts.append("")

    parts.append(build_output_contract(agent, chapter))

    return "\n".join(parts)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Prompt Compiler for Narrative Workbench")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument("--agent", type=str, required=True,
                        choices=["writer", "polish", "review", "fixer", "librarian"],
                        help="目标 Agent")
    parser.add_argument("--context", type=str, default=None,
                        help="预构建的上下文包路径（可选，默认自动查找）")
    parser.add_argument("--output", type=str, default=None,
                        help="输出路径（默认 story/runtime/chapter-XXXX.<agent>.prompt.md）")
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

    print(f"Compiled prompt written to {output_path.relative_to(ROOT)}")
    print(f"Agent: {args.agent}, Chapter: {args.chapter}")

    lines = prompt.count("\n") + 1
    chars = len(prompt)
    est_tokens = chars // 2
    print(f"Lines: {lines}, Estimated tokens: ~{est_tokens}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
