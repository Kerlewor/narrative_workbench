#!/usr/bin/env python3
"""Produce a dependency and recovery matrix for hooks.

This script does not judge story quality. It checks whether hook dependencies,
budgets, evidence fields, and recovery metadata are mechanically coherent.

Usage:
    python scripts/hook_matrix.py --current 42
"""

from __future__ import annotations
from _project import add_root_argument, get_root

import argparse
import re
from collections import defaultdict, deque
from pathlib import Path


ROOT: Path = Path.cwd()  # Set in main() via --project-root or CWD
HOOKS_PATH = ROOT / "story/pending_hooks.md"

ACTIVE = {"open", "progressing", "escalated", "dormant"}
TERMINAL = {"resolved", "dropped"}
VALID_STATUSES = ACTIVE | TERMINAL
VALID_PRIORITIES = {"core", "high", "normal", "low"}


def parse_table() -> tuple[list[str], list[dict[str, str]]]:
    lines = HOOKS_PATH.read_text(encoding="utf-8").splitlines()
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


def ids_from_dependency(value: str) -> list[str]:
    return re.findall(r"H\d{3,}", value or "")


def as_int(value: str) -> int | None:
    match = re.search(r"\d+", value or "")
    return int(match.group(0)) if match else None


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
        for nxt in graph.get(node, []):
            visit(nxt)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return cycles


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser()
    add_root_argument(parser)
    parser.add_argument("--current", type=int, required=True, help="current finalized chapter")
    args = parser.parse_args()
    ROOT = get_root(args)

    header, rows = parse_table()
    print(f"hook matrix: current chapter {args.current}")
    if not rows:
        print("no hooks found")
        return 0

    by_id = {row.get("hook_id", ""): row for row in rows}
    active = [row for row in rows if row.get("状态") in ACTIVE]
    core = [row for row in active if row.get("优先级") == "core"]

    print(f"totalHooks: {len(rows)}")
    print(f"activeHooks: {len(active)} / 15")
    print(f"coreHooks: {len(core)} / 5")

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
                # This is often fine, but worth making visible.
                warnings.append(f"{hook_id}: depends on terminal hook {dep}")

        last = as_int(row.get("最近推进", "")) or as_int(row.get("起始章节", ""))
        half_life = as_int(row.get("半衰期", ""))
        if status in ACTIVE and last is not None and half_life is not None:
            age = args.current - last
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

    print("\nactiveByPriority:")
    for priority in ["core", "high", "normal", "low"]:
        count = sum(1 for row in active if row.get("优先级") == priority)
        print(f"- {priority}: {count}")

    print("\nrecoveryCadence:")
    cadence_counts: dict[str, int] = defaultdict(int)
    for row in active:
        cadence_counts[row.get("回收节奏", "未填写") or "未填写"] += 1
    for cadence, count in sorted(cadence_counts.items()):
        print(f"- {cadence}: {count}")

    blocked = [
        hook_id
        for hook_id, deps in graph.items()
        if by_id.get(hook_id, {}).get("状态") in ACTIVE
        and any(by_id.get(dep, {}).get("状态") in ACTIVE for dep in deps)
    ]
    if blocked:
        print("\nblockedByActiveDependencies:")
        for hook_id in sorted(blocked):
            deps = [dep for dep in graph[hook_id] if by_id.get(dep, {}).get("状态") in ACTIVE]
            print(f"- {hook_id}: waits for {', '.join(deps)}")

    if errors:
        print("\nERRORS:")
        for item in errors:
            print(f"- {item}")
    if warnings:
        print("\nWARNINGS:")
        for item in warnings:
            print(f"- {item}")
    if not errors and not warnings:
        print("\nOK: hook matrix is coherent.")
    elif not errors:
        print("\nOK with hook warnings.")
    else:
        print("\nFAILED.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

