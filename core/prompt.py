"""Three-layer prompt compiler."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from core.context import chapter_prefix, read_file
from core.hooks import as_int


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

HARD_CONSTRAINTS = [
    "不得改写 canonical 文件。",
    "不得自行新增重大设定。",
    "不得跳过本章计划中的核心事件。",
    "不得提前泄露 intent/plan 中标注为\"暂不掀\"的内容。",
    "输出必须包含 handoff 摘要。",
]


def find_runtime_file(root: Path, pattern: str, chapter: int) -> Optional[Path]:
    prefix = chapter_prefix(chapter)
    candidate = root / "story/runtime" / f"{prefix}.{pattern}.md"
    if candidate.is_file():
        return candidate
    glob_pattern = f"{prefix}.*{pattern}*.md"
    matches = sorted(
        path
        for path in (root / "story/runtime").glob(glob_pattern)
        if not path.name.endswith((".context.md", ".prompt.md", ".gatekeeper.md"))
    )
    return matches[0] if matches else None


def read_summary(path: Path, max_lines: int = 40) -> str:
    if not path.is_file():
        return "(文件不存在)"
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines]) + f"\n\n... (共 {len(lines)} 行，已截断)"


def build_layer_base(root: Path, agent: str) -> str:
    agent_file = AGENT_BASE_FILES.get(agent)
    if not agent_file:
        return f"(未知 Agent: {agent})"
    path = root / agent_file
    if not path.is_file():
        return f"(Agent 文件不存在: {agent_file})"
    return read_file(path)


def build_layer_project_rules(root: Path) -> str:
    parts: list[str] = ["## 2. 项目规则\n"]
    for rel, label in PROJECT_RULE_FILES:
        path = root / rel
        if path.is_file():
            parts.append(f"### {label}\n")
            parts.append(read_summary(path, 50))
            parts.append("")

    parts.append("### 硬性约束\n")
    parts.extend(f"- {constraint}" for constraint in HARD_CONSTRAINTS)
    parts.append("")
    return "\n".join(parts)


def expired_hook_lines(root: Path, chapter: int) -> list[str]:
    hooks_path = root / "story/pending_hooks.md"
    if not hooks_path.is_file():
        return []

    expired: list[str] = []
    for line in read_file(hooks_path).splitlines():
        if not line.startswith("| H"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 11:
            continue
        hook_id = cells[0]
        status = cells[3]
        if status in ("resolved", "dropped", "dormant"):
            continue
        last_chapter = as_int(cells[5])
        half_life = as_int(cells[10])
        if last_chapter is None or half_life is None:
            continue
        if chapter - last_chapter > half_life:
            expired.append(f"{hook_id} (Ch{last_chapter}, 半衰期{half_life})")
    return expired


def build_layer_task(root: Path, chapter: int, agent: str, context_path: Optional[str] = None) -> str:
    parts: list[str] = ["## 3. 本章任务\n"]

    intent_path = find_runtime_file(root, "intent", chapter)
    parts.append("### 本章 Intent\n")
    if intent_path:
        parts.append(read_file(intent_path))
    else:
        parts.append(f"(intent 文件不存在: 章节 {chapter} 尚未规划)")
    parts.append("")

    plan_path = find_runtime_file(root, "plan", chapter)
    parts.append("### 本章 Plan\n")
    if plan_path:
        parts.append(read_file(plan_path))
    else:
        parts.append("(plan 文件不存在)")
    parts.append("")

    if context_path:
        context_file = Path(context_path)
    else:
        context_file = find_runtime_file(root, f"{agent}.context", chapter)
    if context_file and context_file.is_file():
        parts.append("### 上下文包\n")
        parts.append(read_summary(context_file, 200))
        parts.append("")

    parts.append("### 风险提示\n")
    parts.append("- 检查 intent/plan 中标注为\"暂不掀\"的内容。")
    expired = expired_hook_lines(root, chapter)
    if expired:
        parts.append(f"- **半衰期到期 hook ({len(expired)} 个):** {', '.join(expired)}")
    else:
        parts.append("- 半衰期检查: 无到期 hook")
    parts.append("")
    return "\n".join(parts)


def build_output_contract(agent: str, chapter: int) -> str:
    prefix = chapter_prefix(chapter)
    output_map = {
        "writer": f"story/runtime/{prefix}.writer.md",
        "polish": f"story/runtime/{prefix}.polish.md",
        "review": f"story/runtime/{prefix}.review.md",
        "fixer": f"story/runtime/{prefix}.fixer.md",
        "librarian": "story/runtime/session-YYYYMMDD-context.md",
    }
    return "\n".join(
        [
            "## 4. 输出契约\n",
            f"- 输出文件: `{output_map.get(agent, f'story/runtime/{prefix}.<stage>.md')}`",
            "- 输出必须包含完整的章节草稿/润色稿/审阅报告/修复稿（根据 Agent 职责）。",
            "- 同时生成 handoff 摘要，记录偏离、未处理问题和事实变更声明。",
            "- 不得修改 canonical 文件。",
            "",
        ]
    )


def compile_prompt(root: Path, agent: str, chapter: int, context_path: Optional[str] = None) -> str:
    name_map = {
        "writer": "Writer Agent - Chapter Task",
        "polish": "Polish Agent - Chapter Task",
        "review": "Review Agent - Chapter Task",
        "fixer": "Fixer Agent - Chapter Task",
        "librarian": "Project Librarian - Context Packet",
    }
    parts = [
        f"# {name_map.get(agent, f'{agent.upper()} Agent')} {chapter}\n",
        "> 本章编译时间: 自动生成",
        f"> Agent: {agent}",
        f"> 章节: {chapter}",
        f"> 来源文件: agents/{agent}.md + 项目规则 + runtime 文件\n",
        "## 1. Agent 角色定义\n",
        build_layer_base(root, agent),
        "",
        build_layer_project_rules(root),
        "",
        build_layer_task(root, chapter, agent, context_path),
        "",
        build_output_contract(agent, chapter),
    ]
    return "\n".join(parts)

