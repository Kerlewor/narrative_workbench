"""Hook table parsing, reporting, and dependency checks."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from core.context import read_file


ACTIVE = {"open", "progressing", "escalated", "dormant"}
TERMINAL = {"resolved", "dropped"}
VALID_STATUSES = ACTIVE | TERMINAL
VALID_PRIORITIES = {"core", "high", "normal", "low"}


def parse_table(root: Path) -> tuple[list[str], list[dict[str, str]]]:
    hooks_path = root / "story/pending_hooks.md"
    if not hooks_path.is_file():
        return [], []
    lines = read_file(hooks_path).splitlines()
    table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
    if len(table_lines) < 2:
        return [], []
    header = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))
    return header, rows


def as_int(value: str) -> int | None:
    match = re.search(r"\d+", value or "")
    return int(match.group(0)) if match else None


def ids_from_dependency(value: str) -> list[str]:
    return re.findall(r"H\d{3,}", value or "")


def detect_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> None:
        if node in visiting:
            if node in stack:
                cycles.append(stack[stack.index(node):] + [node])
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for next_node in graph.get(node, []):
            visit(next_node)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return cycles


def build_hook_report(root: Path, current: int) -> tuple[int, list[str]]:
    _, rows = parse_table(root)
    active = [row for row in rows if row.get("状态") in ACTIVE]
    core = [row for row in active if row.get("优先级") == "core"]
    escalated = [row for row in active if row.get("状态") == "escalated"]

    lines = [
        f"hook report: current chapter {current}",
        f"activeHooks: {len(active)} / 15",
        f"coreHooks: {len(core)} / 5",
        f"escalatedHooks: {len(escalated)}",
    ]
    warnings = 0
    if len(active) > 15:
        lines.append("WARN: active hooks exceed budget")
        warnings += 1
    if len(core) > 5:
        lines.append("WARN: core hooks exceed budget")
        warnings += 1

    overdue: list[tuple[str, int, int, int]] = []
    missing_evidence: list[str] = []
    for row in active:
        hook_id = row.get("hook_id", "")
        if not re.fullmatch(r"H\d{3,}", hook_id):
            lines.append(f"WARN: invalid hook_id format: {hook_id!r}")
            warnings += 1
        last = as_int(row.get("最近推进", "")) or as_int(row.get("起始章节", ""))
        half_life = as_int(row.get("半衰期", ""))
        evidence = row.get("正文证据", "")
        if not evidence:
            missing_evidence.append(hook_id)
        if last is not None and half_life is not None:
            age = current - last
            if age > half_life:
                overdue.append((hook_id, last, half_life, age))

    if overdue:
        lines.append("overdueHooks:")
        for hook_id, last, half_life, age in overdue:
            lines.append(f"- {hook_id}: lastAdvanced={last}, halfLife={half_life}, age={age}")
        warnings += len(overdue)

    if missing_evidence:
        lines.append("activeHooksMissingTextEvidence:")
        for hook_id in missing_evidence:
            lines.append(f"- {hook_id}")
        warnings += len(missing_evidence)

    if warnings:
        lines.append("hook report completed with warnings")
        return 1, lines
    lines.append("hook report OK")
    return 0, lines


def build_hook_matrix(root: Path, current: int) -> tuple[int, list[str]]:
    _, rows = parse_table(root)
    lines = [f"hook matrix: current chapter {current}"]
    if not rows:
        lines.append("no hooks found")
        return 0, lines

    by_id = {row.get("hook_id", ""): row for row in rows}
    active = [row for row in rows if row.get("状态") in ACTIVE]
    core = [row for row in active if row.get("优先级") == "core"]

    lines.extend(
        [
            f"totalHooks: {len(rows)}",
            f"activeHooks: {len(active)} / 15",
            f"coreHooks: {len(core)} / 5",
        ]
    )

    warnings: list[str] = []
    errors: list[str] = []
    if len(active) > 15:
        warnings.append("active hook budget exceeded")
    if len(core) > 5:
        warnings.append("core hook budget exceeded")

    graph: dict[str, list[str]] = {}
    reverse: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        hook_id = row.get("hook_id", "")
        if not re.fullmatch(r"H\d{3,}", hook_id):
            errors.append(f"invalid hook id: {hook_id}")
            continue
        status = row.get("状态", "")
        priority = row.get("优先级", "")
        if status not in VALID_STATUSES:
            errors.append(f"{hook_id}: invalid status {status}")
        if priority not in VALID_PRIORITIES:
            errors.append(f"{hook_id}: invalid priority {priority}")

        deps = ids_from_dependency(row.get("上游依赖", ""))
        graph[hook_id] = deps
        for dep in deps:
            reverse[dep].append(hook_id)
            if dep not in by_id:
                errors.append(f"{hook_id}: missing upstream dependency {dep}")
            elif by_id[dep].get("状态") in TERMINAL and status in ACTIVE:
                warnings.append(f"{hook_id}: depends on terminal hook {dep}")

        last = as_int(row.get("最近推进", "")) or as_int(row.get("起始章节", ""))
        half_life = as_int(row.get("半衰期", ""))
        if status in ACTIVE and last is not None and half_life is not None:
            age = current - last
            if age > half_life:
                warnings.append(f"{hook_id}: overdue half-life age={age}, halfLife={half_life}")
        if status in ACTIVE and not row.get("正文证据", ""):
            warnings.append(f"{hook_id}: active hook missing text evidence")
        if status == "resolved" and not row.get("正文证据", ""):
            warnings.append(f"{hook_id}: resolved hook missing recovery evidence")
        if status in ACTIVE and not row.get("预期回收", ""):
            warnings.append(f"{hook_id}: active hook missing expected recovery")

    for cycle in detect_cycles(graph):
        errors.append("dependency cycle: " + " -> ".join(cycle))

    lines.append("")
    lines.append("activeByPriority:")
    for priority in ["core", "high", "normal", "low"]:
        count = sum(1 for row in active if row.get("优先级") == priority)
        lines.append(f"- {priority}: {count}")

    lines.append("")
    lines.append("recoveryCadence:")
    cadence_counts: dict[str, int] = defaultdict(int)
    for row in active:
        cadence_counts[row.get("回收节奏", "未填写") or "未填写"] += 1
    for cadence, count in sorted(cadence_counts.items()):
        lines.append(f"- {cadence}: {count}")

    blocked = [
        hook_id
        for hook_id, deps in graph.items()
        if by_id.get(hook_id, {}).get("状态") in ACTIVE
        and any(by_id.get(dep, {}).get("状态") in ACTIVE for dep in deps)
    ]
    if blocked:
        lines.append("")
        lines.append("blockedByActiveDependencies:")
        for hook_id in sorted(blocked):
            deps = [dep for dep in graph[hook_id] if by_id.get(dep, {}).get("状态") in ACTIVE]
            lines.append(f"- {hook_id}: waits for {', '.join(deps)}")

    if errors:
        lines.append("")
        lines.append("ERRORS:")
        lines.extend(f"- {item}" for item in errors)
    if warnings:
        lines.append("")
        lines.append("WARNINGS:")
        lines.extend(f"- {item}" for item in warnings)
    if not errors and not warnings:
        lines.append("")
        lines.append("OK: hook matrix is coherent.")
    elif not errors:
        lines.append("")
        lines.append("OK with hook warnings.")
    else:
        lines.append("")
        lines.append("FAILED.")
    return (1 if errors else 0), lines

