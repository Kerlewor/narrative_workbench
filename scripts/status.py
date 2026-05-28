#!/usr/bin/env python3
"""Project Status for Narrative Workbench.

Quick overview of project progress, active hooks, drift risks, and suggested next steps.

Usage:
    python3 scripts/status.py
    python3 scripts/status.py --verbose
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def count_chapters() -> tuple[int, int, int]:
    index_path = ROOT / "chapters/index.json"
    if not index_path.is_file():
        return 0, 0, 0
    index = json.loads(index_path.read_text(encoding="utf-8"))
    chapters = index.get("chapters", [])
    total = len(chapters)
    final = sum(1 for c in chapters if isinstance(c, dict) and c.get("status") == "final")
    return total, final, total - final


def count_hooks() -> tuple[int, int, int]:
    hooks_path = ROOT / "story/pending_hooks.md"
    if not hooks_path.is_file():
        return 0, 0, 0
    text = hooks_path.read_text(encoding="utf-8")
    active = 0
    expired = 0
    resolved = 0
    for line in text.splitlines():
        if not line.startswith("| H"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 11:
            continue
        status = cells[3] if len(cells) > 3 else ""
        if status == "resolved":
            resolved += 1
        elif status in ("dormant", "dropped"):
            continue
        else:
            active += 1
            try:
                last_adv = int(cells[5]) if len(cells) > 5 and cells[5].isdigit() else 0
                half_life = int(cells[10]) if len(cells) > 10 and cells[10].isdigit() else 999
                latest_ch = count_chapters()[0]
                if latest_ch - last_adv > half_life:
                    expired += 1
            except (ValueError, IndexError):
                continue
    return active, resolved, expired


def count_runtime() -> dict[str, int]:
    runtime_dir = ROOT / "story/runtime"
    if not runtime_dir.is_dir():
        return {}
    counts: dict[str, int] = {}
    for path in sorted(runtime_dir.glob("*.md")):
        if path.name.startswith("_template") or path.name.startswith("batch-"):
            continue
        parts = path.stem.split(".")
        if len(parts) >= 2:
            ch = parts[0]
            stage = parts[-1] if len(parts) > 1 else "unknown"
            key = f"{ch}:{stage}"
            counts[key] = counts.get(key, 0) + 1
    return counts


def check_role_drift_risks() -> list[str]:
    risks: list[str] = []
    roles_dir = ROOT / "story/roles"
    if not roles_dir.is_dir():
        return risks
    for path in sorted(roles_dir.glob("*.md")):
        if path.name.startswith("_template"):
            continue
        text = path.read_text(encoding="utf-8")
        has_personality_lock = "Personality Lock" in text
        has_constraints = "Behavioral Constraints" in text
        has_stress_test = "压力测试" in text and "关键决策点" in text
        if not has_personality_lock or not has_constraints:
            risks.append(f"{path.stem}: 缺少 Personality Lock 或 Behavioral Constraints")
        elif not has_stress_test:
            risks.append(f"{path.stem}: 缺少压力测试结论（建议运行 深化角色 {path.stem}）")
    return risks


def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    total_ch, final_ch, draft_ch = count_chapters()
    active_hooks, resolved_hooks, expired_hooks = count_hooks()
    drift_risks = check_role_drift_risks()

    print("Narrative Workbench — 项目状态")
    print(f"  章节: {total_ch} 章（定稿 {final_ch}，进行中 {draft_ch}）")
    print(f"  伏笔: {active_hooks} 活跃，{resolved_hooks} 已回收", end="")
    if expired_hooks > 0:
        print(f"，{expired_hooks} 超半衰期")
    else:
        print("")
    if drift_risks:
        print(f"  角色漂移风险: {len(drift_risks)} 个角色需关注")
    else:
        print(f"  角色漂移风险: 无")

    scripts_count = len(list((ROOT / "scripts").glob("*.py")))
    print(f"  脚本: {scripts_count} 个 Python 辅助脚本可用")
    print(f"  知识库索引: {'已构建' if (ROOT / '.nw_index/entity_index.json').is_file() else '未构建'}")

    print()
    suggestions: list[str] = []
    if expired_hooks > 0:
        suggestions.append(f"运行 hook_report.py --current {total_ch} 检查超半衰期伏笔")
    if drift_risks:
        suggestions.append(f"对 {len(drift_risks)} 个风险角色运行 深化角色 命令")
    if draft_ch > 0 and total_ch > 0:
        suggestions.append(f"运行 gatekeeper.py --chapter {total_ch} --stage final")
    if not (ROOT / '.nw_index/entity_index.json').is_file():
        suggestions.append("运行 knowledge_index.py build 构建知识库索引")
    if not suggestions:
        suggestions.append("项目状态良好，可以继续写作")

    print("建议下一步:")
    for s in suggestions:
        print(f"  - {s}")

    if verbose:
        print()
        print("--- Runtime 文件详情 ---")
        runtime_counts = count_runtime()
        for key, count in sorted(runtime_counts.items()):
            print(f"  {key}: {count} files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
