#!/usr/bin/env python3
"""Gatekeeper for Narrative Workbench.

Deterministic pre-flight checks before a chapter can be written to canonical.
This is NOT an AI review — it checks file existence, pipeline completeness,
Review→Fixer response coverage, hook synchronization, and forbidden patterns.

Usage:
    python3 scripts/gatekeeper.py --chapter 12 --stage final
    python3 scripts/gatekeeper.py --chapter 12 --stage fixer

Output:
    story/runtime/chapter-0012.gatekeeper.md
"""

from __future__ import annotations
from _project import add_root_argument, get_root

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

ROOT: Path = Path.cwd()  # Set in main() via --project-root or CWD

PIPELINE_STAGES = ["intent", "plan", "writer", "polish", "review", "fixer"]

AI_PATTERNS: list[tuple[str, str]] = [
    (r"某种难以言说的", "AI 味: 抽象情绪短语"),
    (r"仿佛有什么东西", "AI 味: 万能氛围句"),
    (r"不是.{1,20}而是", "AI 味: 否定式排比"),
    (r"命运的齿轮", "主题金句残留"),
    (r"空气仿佛凝固", "万能氛围句"),
    (r"时间像是停止", "万能氛围句"),
    (r"她终于意识到", "抽象心理总结"),
    (r"这一刻，她明白", "主题金句"),
    (r"前所未有的.{1,10}感", "抽象情绪命名"),
    (r"内心充满了", "直接心理描写（可能为 AI 腔）"),
    (r"羁绊|救赎|照亮|温暖了.{1,10}的心", "主题金句模式"),
    (r"这就是.{1,20}的.{1,10}意义", "主题总结句"),
    (r"所有的.{1,10}都.{1,10}了答案", "主题升华句"),
]

HARD_CONSTRAINT_PATTERNS: list[tuple[str, str]] = [
    (r"\([^)]*独白[^)]*\)", "括号内心独白（禁止）"),
    (r"「[^」]*」", "非中文双引号（应使用 "" 而非 「」）"),
]


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def find_runtime_file(stage: str, chapter: int) -> Optional[Path]:
    prefix = chapter_prefix(chapter)
    candidate = ROOT / "story/runtime" / f"{prefix}.{stage}.md"
    if candidate.is_file():
        return candidate
    glob_pattern = f"{prefix}.{stage}*.md"
    matches = sorted(
        p for p in (ROOT / "story/runtime").glob(glob_pattern)
        if not p.name.endswith((".context.md", ".prompt.md", ".gatekeeper.md"))
    )
    return matches[0] if matches else None


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def check_pipeline_files(chapter: int) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    present: list[str] = []
    for stage in PIPELINE_STAGES:
        path = find_runtime_file(stage, chapter)
        if path and path.is_file():
            present.append(stage)
        else:
            missing.append(stage)
    return present, missing


def check_review_items_addressed(chapter: int) -> tuple[bool, list[str]]:
    review_path = find_runtime_file("review", chapter)
    fixer_path = find_runtime_file("fixer", chapter)

    if not review_path or not fixer_path:
        return True, []

    review_text = read_file(review_path)
    fixer_text = read_file(fixer_path)

    review_sections = re.findall(
        r"\| (严重|高|中|低)\s*\|.*?\|.*?\|",
        review_text, re.MULTILINE
    )
    # Exclude header rows like "| 严重度 | 位置 | ..."
    review_sections = [s for s in review_sections if s not in ("严重",)]
    mandatory_count = len(review_sections)

    if mandatory_count == 0:
        return True, []

    issues: list[str] = []
    if len(review_sections) > 0:
        fixer_mentions = len(re.findall(r"(修复|修正|已处理|applied|fixed)", fixer_text, re.IGNORECASE))
        if fixer_mentions == 0:
            issues.append(
                f"Review 报告包含 {mandatory_count} 个必修问题，"
                f"但 Fixer 输出中未检测到修复记录"
            )
        elif fixer_mentions < mandatory_count:
            issues.append(
                f"Review 报告包含 {mandatory_count} 个必修问题，"
                f"Fixer 输出中仅检测到 {fixer_mentions} 处修复提及——"
                f"可能存在未处理的 Review 项"
            )

    review_conclusion = re.search(
        r"(是否可进入 Fixer|结论).*?(是|否|可|不可)",
        review_text, re.MULTILINE
    )
    if review_conclusion and "否" in review_conclusion.group(0):
        issues.append("Review 结论为不可进入 Fixer，但已存在 Fixer 输出")

    return len(issues) == 0, issues


def check_hook_sync(chapter: int) -> tuple[bool, list[str]]:
    hooks_path = ROOT / "story/pending_hooks.md"
    if not hooks_path.is_file():
        return True, []

    hooks_text = read_file(hooks_path)
    issues: list[str] = []

    expired = []
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

            if status in ("resolved", "dropped", "dormant", "candidate"):
                continue
            if not last_advanced.isdigit() or not half_life.isdigit():
                continue

            last_ch = int(last_advanced)
            hl = int(half_life)
            if chapter - last_ch > hl:
                expired.append(f"{hook_id} (最近推进 Ch{last_ch}, 半衰期 {hl}, 当前 Ch{chapter})")
        except (ValueError, IndexError):
            continue

    if expired:
        issues.append(
            f"以下 {len(expired)} 个活跃 hook 已超半衰期:"
        )
        for h in expired:
            issues.append(f"  - {h}")
        issues.append("  这些 hook 必须在本章 advance / defer / resolve / dormant / dropped。")

    return len(issues) == 0, issues


def check_forbidden_patterns(chapter: int) -> tuple[bool, list[str]]:
    fixer_path = find_runtime_file("fixer", chapter)
    polish_path = find_runtime_file("polish", chapter)

    target_path = fixer_path if fixer_path else polish_path
    if not target_path:
        return True, []

    text = read_file(target_path)
    issues: list[str] = []

    for pattern, label in HARD_CONSTRAINT_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            issues.append(f"{label}: 发现 {len(matches)} 处")

    warnings: list[str] = []
    for pattern, label in AI_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            warnings.append(f"{label}: 发现 {len(matches)} 处")

    if warnings and not issues:
        return True, [f"[非阻塞警告] {w}" for w in warnings]

    return len(issues) == 0, issues + [f"[非阻塞警告] {w}" for w in warnings]


def check_chapter_index(chapter: int) -> tuple[bool, list[str]]:
    index_path = ROOT / "chapters/index.json"
    if not index_path.is_file():
        return True, []

    import json
    index = json.loads(index_path.read_text(encoding="utf-8"))
    chapters = index.get("chapters", [])
    issues: list[str] = []

    indexed_nums = {c.get("chapter") for c in chapters if isinstance(c, dict)}
    chapter_files = sorted(
        p for p in (ROOT / "chapters").glob("*.md")
        if p.name != "index.md"
    )
    max_ch = max(indexed_nums) if indexed_nums else 0

    if chapter <= max_ch and chapter not in indexed_nums:
        pass

    return len(issues) == 0, issues


def check_intent_status(chapter: int) -> tuple[bool, list[str]]:
    intent_path = find_runtime_file("intent", chapter)
    if not intent_path:
        return False, [f"intent 文件不存在: 章节 {chapter} 尚未规划"]

    text = read_file(intent_path)
    match = re.search(r"^status:\s*([a-zA-Z0-9_-]+)\s*$", text, re.MULTILINE)
    if not match:
        return False, ["intent 文件缺少 status 字段"]

    status = match.group(1)
    if status not in {
        "planned", "drafted", "polished", "reviewed", "fixed",
        "final-check", "final-aligned", "needs-repair", "needs-rewrite",
        "superseded",
    }:
        return False, [f"intent 状态非法: {status}"]

    return True, []


def build_report(chapter: int, stage: str) -> str:
    lines: list[str] = []
    lines.append(f"# Gatekeeper Report - Chapter {chapter}")
    lines.append("")
    lines.append(f"检查阶段: {stage}")
    lines.append(f"项目根目录: {ROOT}")
    lines.append("")

    blocking: list[str] = []
    warnings: list[str] = []

    present_files, missing_files = check_pipeline_files(chapter)
    if missing_files:
        for m in missing_files:
            blocking.append(f"缺少 {m} 阶段产物")

    if "review" in present_files and "fixer" in present_files:
        ok, issues = check_review_items_addressed(chapter)
        if not ok:
            blocking.extend(issues)
        else:
            for i in issues:
                warnings.append(i)

    ok, issues = check_intent_status(chapter)
    if not ok:
        blocking.extend(issues)

    ok, issues = check_hook_sync(chapter)
    if not ok:
        blocking.extend(issues)
    else:
        for i in issues:
            warnings.append(i)

    ok, issues = check_forbidden_patterns(chapter)
    if not ok:
        blocking.extend(issues)
    else:
        for i in issues:
            if "非阻塞" in i:
                warnings.append(i)
            else:
                blocking.append(i)

    chapter_files = sorted((ROOT / "chapters").glob(f"{chapter_prefix(chapter)}_*.md"))
    if chapter_files:
        warnings.append(f"章节文件已存在于 chapters/: {[p.name for p in chapter_files]}")

    lines.append("## 检查结果")
    lines.append("")

    if blocking:
        lines.append(f"**FAILED** — {len(blocking)} 个阻塞问题")
        lines.append("")
        lines.append("### 阻塞问题")
        lines.append("")
        for item in blocking:
            lines.append(f"- [BLOCKING] {item}")
    else:
        lines.append("**PASSED** — 所有阻塞检查通过")
    lines.append("")

    if warnings:
        lines.append("### 非阻塞警告")
        lines.append("")
        for item in warnings:
            lines.append(f"- [WARN] {item}")
        lines.append("")

    lines.append("## 建议下一步")
    lines.append("")
    if blocking:
        lines.append(f"- 修复以上 {len(blocking)} 个阻塞问题后重新运行 gatekeeper。")
        lines.append("- 如果问题需要 AI 判断，交由主会话处理。")
    elif stage == "final":
        lines.append("- 所有门禁检查通过。可执行 final-check 并写入 canonical。")
        lines.append("- 建议运行 text_audit.py 做最后一次文本审计。")
        lines.append("- 确认后运行 chapter_index.py --write 更新索引。")
    else:
        lines.append("- 当前阶段门禁通过。继续流水线下一阶段。")

    return "\n".join(lines)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Gatekeeper for Narrative Workbench")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument("--stage", type=str, default="final",
                        choices=["intent", "writer", "polish", "review", "fixer", "final"],
                        help="检查阶段 (default: final)")
    parser.add_argument("--output", type=str, default=None,
                        help="输出路径（默认 story/runtime/chapter-XXXX.gatekeeper.md）")
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

    print(f"Gatekeeper report written to {output_path.relative_to(ROOT)}")

    has_blocking = "**FAILED**" in report
    if has_blocking:
        blocking_count = report.count("[BLOCKING]")
        print(f"RESULT: FAILED — {blocking_count} blocking issues")
        return 1
    else:
        print("RESULT: PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
