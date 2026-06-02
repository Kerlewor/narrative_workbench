"""Markdown-native project dashboard generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.ledger import read_records
from core.hooks import parse_table


@dataclass(frozen=True)
class DashboardResult:
    data: dict[str, Any]
    markdown: str


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _chapter_records(root: Path) -> list[dict[str, Any]]:
    index = _read_json(root / "chapters/index.json")
    chapters = index.get("chapters", [])
    return [item for item in chapters if isinstance(item, dict)]


def _chapter_number(item: dict[str, Any]) -> int:
    value = item.get("chapter", item.get("number", 0))
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _chapter_status(item: dict[str, Any]) -> str:
    return str(item.get("status", item.get("state", "unknown")) or "unknown")


def _next_chapter(chapters: list[dict[str, Any]]) -> int:
    if not chapters:
        return 1
    return max(_chapter_number(item) for item in chapters) + 1


def _active_hooks(root: Path) -> list[dict[str, Any]]:
    hooks = read_records(root, "hooks")
    active = [
        hook for hook in hooks
        if hook.get("status", "open") not in {"resolved", "dropped", "dormant"}
    ]
    if active:
        return active
    return _active_hooks_from_markdown(root)


def _active_hooks_from_markdown(root: Path) -> list[dict[str, Any]]:
    _, rows = parse_table(root)
    hooks: list[dict[str, Any]] = []
    for row in rows:
        status = row.get("状态", "open")
        if status in {"resolved", "dropped", "dormant", "candidate"}:
            continue
        due_window = _parse_due_window(row.get("预期回收", ""))
        hooks.append(
            {
                "id": row.get("hook_id", "?"),
                "name": row.get("类型", "?"),
                "status": status,
                "introduced_in": row.get("起始章节", "?"),
                "last_touched": row.get("最近推进", "?"),
                "due_window": due_window,
                "source": "pending_hooks.md",
            }
        )
    return hooks


def _parse_due_window(value: str) -> list[int]:
    import re

    nums = [int(item) for item in re.findall(r"\d+", value or "")]
    if len(nums) >= 2:
        return nums[:2]
    if len(nums) == 1:
        return [nums[0], nums[0]]
    return []


def _hook_risk(hook: dict[str, Any], current_chapter: int) -> str:
    due_window = hook.get("due_window", [])
    if isinstance(due_window, list) and len(due_window) >= 2:
        try:
            start = int(due_window[0])
            end = int(due_window[1])
        except (TypeError, ValueError):
            return "未评估"
        if current_chapter > end:
            return "高：已超过建议窗口"
        if current_chapter >= start:
            return "中：当前应推进"
        if current_chapter + 3 >= start:
            return "低：即将进入窗口"
    if hook.get("status") == "escalated":
        return "高：已升级"
    return "未评估"


def _top_hook_items(root: Path, current_chapter: int, limit: int = 5) -> list[dict[str, Any]]:
    risk_rank = {"高": 3, "中": 2, "低": 1}
    items = []
    for hook in _active_hooks(root):
        risk = _hook_risk(hook, current_chapter)
        items.append(
            {
                "id": hook.get("id", "?"),
                "name": hook.get("name", "?"),
                "status": hook.get("status", "open"),
                "introduced_in": hook.get("introduced_in", "?"),
                "last_touched": hook.get("last_touched", "?"),
                "due_window": hook.get("due_window", []),
                "risk": risk,
                "source": hook.get("source", "ledger"),
                "rank": risk_rank.get(risk[:1], 0),
            }
        )
    return sorted(items, key=lambda item: item["rank"], reverse=True)[:limit]


def _secret_items(root: Path, limit: int = 5) -> list[dict[str, Any]]:
    secrets = read_records(root, "secrets")
    items = []
    for secret in secrets:
        if secret.get("revealed_in"):
            continue
        items.append(
            {
                "id": secret.get("id", "?"),
                "name": secret.get("name", "?"),
                "known_by": secret.get("known_by", []),
                "unknown_by": secret.get("unknown_by", []),
            }
        )
    return items[:limit]


def _timeline_risks(root: Path, current_chapter: int) -> list[str]:
    events = read_records(root, "timeline")
    risks: list[str] = []
    chapter_events: dict[int, int] = {}
    for event in events:
        try:
            chapter = int(event.get("chapter", 0))
        except (TypeError, ValueError):
            continue
        chapter_events[chapter] = chapter_events.get(chapter, 0) + 1
    if current_chapter > 1 and (current_chapter - 1) not in chapter_events:
        risks.append(f"第 {current_chapter - 1} 章缺少时间线事件记录")
    if not events:
        risks.append("时间线账本为空，后续章节建议补充关键事件")
    return risks[:5]


def build_dashboard(root: Path) -> DashboardResult:
    chapters = _chapter_records(root)
    next_chapter = _next_chapter(chapters)
    current_chapter = next_chapter
    previous = max((_chapter_number(item) for item in chapters), default=0)
    final_count = sum(1 for item in chapters if _chapter_status(item) in {"final", "final-aligned"})
    in_progress = len(chapters) - final_count
    hook_items = _top_hook_items(root, current_chapter)
    secret_items = _secret_items(root)
    timeline_risks = _timeline_risks(root, current_chapter)

    data: dict[str, Any] = {
        "schema": "narrative_workbench.dashboard.v1",
        "project_root": str(root),
        "current_chapter": current_chapter,
        "previous_chapter": previous,
        "chapter_counts": {
            "total": len(chapters),
            "final": final_count,
            "in_progress": in_progress,
        },
        "must_handle": hook_items,
        "forbidden_reveals": secret_items,
        "timeline_risks": timeline_risks,
        "suggested_commands": [
            f"为第 {current_chapter} 章生成写作简报",
            f"规划第 {current_chapter} 章场景卡",
            f"审查第 {previous} 章" if previous else "搭建大纲",
            "显示当前全部高风险伏笔",
            "更新伏笔看板",
        ],
    }

    markdown = render_dashboard(data)
    return DashboardResult(data=data, markdown=markdown)


def _format_due_window(value: Any) -> str:
    if isinstance(value, list) and len(value) >= 2:
        return f"第{value[0]}-{value[1]}章"
    return "未设定"


def _list_or_dash(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "-"
    return str(value) if value else "-"


def render_dashboard(data: dict[str, Any]) -> str:
    chapter_counts = data["chapter_counts"]
    lines = [
        "# 创作控制台",
        "",
        "> 自动生成。对话窗口只负责调度，详细状态以本文件和 `story/views/` 为准。",
        "",
        "## 当前进度",
        "",
        f"- 当前建议章节：第 {data['current_chapter']} 章",
        f"- 上一章：{'第 ' + str(data['previous_chapter']) + ' 章' if data['previous_chapter'] else '暂无'}",
        f"- 章节统计：总计 {chapter_counts['total']}，定稿 {chapter_counts['final']}，进行中 {chapter_counts['in_progress']}",
        "",
        "## 本章必须处理",
        "",
    ]

    must_handle = data.get("must_handle", [])
    if must_handle:
        lines.extend(["| 伏笔 | 状态 | 建议窗口 | 风险 |", "|---|---|---|---|"])
        for item in must_handle:
            lines.append(
                f"| {item['id']} {item['name']} | {item['status']} | "
                f"{_format_due_window(item.get('due_window'))} | {item['risk']} |"
            )
    else:
        lines.append("- 暂无到期或高风险伏笔。")

    lines.extend(["", "## 本章禁止出现", ""])
    forbidden = data.get("forbidden_reveals", [])
    if forbidden:
        lines.extend(["| 秘密 | 已知角色 | 未知角色 |", "|---|---|---|"])
        for item in forbidden:
            lines.append(
                f"| {item['id']} {item['name']} | "
                f"{_list_or_dash(item.get('known_by'))} | {_list_or_dash(item.get('unknown_by'))} |"
            )
    else:
        lines.append("- 暂无未揭示秘密记录。")

    lines.extend(["", "## 待处理问题", ""])
    risks = data.get("timeline_risks", [])
    if risks:
        lines.extend(f"- {risk}" for risk in risks)
    else:
        lines.append("- 暂无时间线风险。")

    lines.extend(["", "## 可直接输入的操作", ""])
    for command in data.get("suggested_commands", []):
        lines.append(f"- {command}")

    lines.extend(
        [
            "",
            "## 文件入口",
            "",
            "- `story/views/hook_dashboard.md`：伏笔看板",
            "- `story/views/knowledge_matrix.md`：角色知识边界矩阵",
            "- `story/views/timeline.md`：时间线",
            "- `story/runtime/`：本章任务包、审查、diff 与决策日志",
            "",
        ]
    )
    return "\n".join(lines)


def write_dashboard(root: Path, output: Path | None = None) -> DashboardResult:
    result = build_dashboard(root)
    target = output or root / "story/DASHBOARD.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(result.markdown, encoding="utf-8")
    return result
