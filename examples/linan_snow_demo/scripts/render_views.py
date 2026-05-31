"""View Renderer for Narrative Workbench.

Renders structured JSONL ledger files into author-readable Markdown views
in story/views/. The dual-track system preserves both program-retrievable
JSONL (for scripts/agents) and human-readable Markdown (for authors).

Usage:
    python scripts/render_views.py all              # Render all views
    python scripts/render_views.py hooks            # Render only hook dashboard
    python scripts/render_views.py knowledge        # Render knowledge boundary matrix
    python scripts/render_views.py timeline         # Render timeline view
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from _project import add_root_argument, get_root

ROOT: Path = Path.cwd()

LEDGER_DIR = "story/ledger"
VIEWS_DIR = "story/views"


def _read_records(ledger: str) -> list[dict]:
    path = ROOT / LEDGER_DIR / f"{ledger}.jsonl"
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "_schema" in record:
            continue
        records.append(record)
    return records


def _ensure_views_dir() -> Path:
    views = ROOT / VIEWS_DIR
    views.mkdir(parents=True, exist_ok=True)
    return views


def render_hook_dashboard() -> str:
    """Render hooks.jsonl into a Markdown hook dashboard."""
    hooks = _read_records("hooks")
    if not hooks:
        return "# 伏笔看板\n\n（暂无伏笔记录。运行 `ledger_manager.py init` 初始化账本。）\n"

    status_labels = {
        "open": "开放", "progressing": "推进中", "escalated": "升级",
        "resolved": "已回收", "dormant": "休眠", "dropped": "废弃",
    }

    lines = [
        "# 伏笔看板",
        "",
        f"> 更新时间: 自动生成 | 活跃伏笔: {sum(1 for h in hooks if h.get('status') not in ('resolved', 'dropped', 'dormant'))}",
        "",
        "## 活跃伏笔",
        "",
        "| 伏笔 ID | 名称 | 状态 | 首次出现 | 最近推进 | 建议窗口 | 风险 |",
        "|---|---|---|---|---|---|---|",
    ]

    for hook in hooks:
        if hook.get("status") in ("resolved", "dropped", "dormant"):
            continue
        status = status_labels.get(hook.get("status", "open"), hook.get("status", "open"))
        due = hook.get("due_window", [])
        due_str = f"第{due[0]}-{due[1]}章" if len(due) >= 2 else str(due) if due else "—"
        risk = "—"
        if due and len(due) >= 2:
            last = hook.get("last_touched", "")
            try:
                last_ch = int(last.replace("chapter_", "")) if isinstance(last, str) and "chapter_" in str(last) else 0
                if last_ch > due[1]:
                    risk = "⚠ 过期未收"
                elif last_ch >= due[0]:
                    risk = "● 应推进"
            except (ValueError, TypeError):
                pass
        lines.append(
            f"| {hook.get('id', '?')} | {hook.get('name', '?')} | {status} | "
            f"{hook.get('introduced_in', '?')} | {hook.get('last_touched', '?')} | "
            f"{due_str} | {risk} |"
        )

    lines.append("")
    lines.append("## 已回收 / 休眠伏笔")
    lines.append("")
    lines.append("| 伏笔 ID | 名称 | 状态 | 首次出现 | 回收章节 |")
    lines.append("|---|---|---|---|---|")
    for hook in hooks:
        if hook.get("status") not in ("resolved", "dropped", "dormant"):
            continue
        lines.append(
            f"| {hook.get('id', '?')} | {hook.get('name', '?')} | "
            f"{status_labels.get(hook.get('status', '?'), '?')} | "
            f"{hook.get('introduced_in', '?')} | {hook.get('resolution_chapter', '—')} |"
        )

    lines.append("")
    return "\n".join(lines)


def render_knowledge_matrix() -> str:
    """Render secrets and character knowledge into a boundary matrix."""
    secrets = _read_records("secrets")
    characters = _read_records("characters")

    if not secrets:
        return "# 角色知识边界矩阵\n\n（暂无秘密记录。）\n"

    char_ids = [c.get("id", "?") for c in characters]
    if not char_ids:
        char_ids = sorted(set(
            cid for s in secrets
            for cid in (s.get("known_by", []) + s.get("unknown_by", []))
        ))

    lines = [
        "# 角色知识边界矩阵",
        "",
        "> 每个角色对关键事实的知情状态。✓ = 知道，✗ = 不知道，◐ = 部分知道。",
        "",
        "## 事实",
        "",
    ]

    header = "| 事实 | " + " | ".join(char_ids) + " | 读者知道 |"
    sep = "|---|" + "|".join(["---"] * (len(char_ids) + 1)) + "|"
    lines.append(header)
    lines.append(sep)

    for secret in secrets:
        row = [secret.get("name", "?")]
        known = secret.get("known_by", [])
        unknown = secret.get("unknown_by", [])
        for cid in char_ids:
            if cid in known:
                row.append("✓")
            elif cid in unknown:
                row.append("✗")
            else:
                row.append("—")
        row.append("✓" if secret.get("revealed_in") else ("◐" if secret.get("partial_reveal_in") else "✗"))
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    return "\n".join(lines)


def render_timeline() -> str:
    """Render timeline.jsonl into a chronological view."""
    events = _read_records("timeline")
    if not events:
        return "# 时间线\n\n（暂无事件记录。）\n"

    events.sort(key=lambda e: (e.get("chapter", 999), e.get("relative_time", "")))

    lines = [
        "# 时间线",
        "",
        "| 章节 | 事件 | 地点 | 出场角色 |",
        "|---|---|---|---|",
    ]

    for event in events:
        chars = event.get("characters_present", [])
        chars_str = ", ".join(chars) if isinstance(chars, list) else str(chars)
        lines.append(
            f"| {event.get('chapter', '?')} | {event.get('description', '?')} | "
            f"{event.get('location', '—')} | {chars_str} |"
        )

    lines.append("")
    return "\n".join(lines)


def render_relationships() -> str:
    """Render relationships.jsonl into a relationship map."""
    rels = _read_records("relationships")
    if not rels:
        return "# 关系网络\n\n（暂无关系记录。）\n"

    lines = [
        "# 关系网络",
        "",
        "| 角色 A | 关系 | 角色 B | 当前状态 | 最后变化 |",
        "|---|---|---|---|---|",
    ]
    for r in rels:
        lines.append(
            f"| {r.get('from_char', '?')} | {r.get('type', '?')} | "
            f"{r.get('to_char', '?')} | {r.get('current_state', '—')} | "
            f"{r.get('last_changed_in', '—')} |"
        )
    lines.append("")
    return "\n".join(lines)


RENDERERS = {
    "hooks": (render_hook_dashboard, "hook_dashboard.md"),
    "knowledge": (render_knowledge_matrix, "knowledge_matrix.md"),
    "timeline": (render_timeline, "timeline.md"),
    "relationships": (render_relationships, "relationships.md"),
}


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="View Renderer for Narrative Workbench")
    add_root_argument(parser)
    parser.add_argument("view", nargs="?", default="all",
                        choices=["all", "hooks", "knowledge", "timeline", "relationships"],
                        help="Which view to render (default: all)")
    args = parser.parse_args()
    ROOT = get_root(args)

    views_dir = _ensure_views_dir()

    if args.view == "all":
        for name, (render_fn, filename) in RENDERERS.items():
            content = render_fn()
            output = views_dir / filename
            output.write_text(content, encoding="utf-8")
            print(f"  {filename}")
        print(f"\nAll views rendered to {views_dir.relative_to(ROOT)}/")
    else:
        render_fn, filename = RENDERERS[args.view]
        content = render_fn()
        output = views_dir / filename
        output.write_text(content, encoding="utf-8")
        print(f"Rendered {filename} to {views_dir.relative_to(ROOT)}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
