#!/usr/bin/env python3
"""Report hook budget and half-life status from story/pending_hooks.md.

Usage:
    python scripts/hook_report.py --current 42
"""

from __future__ import annotations
from _project import add_root_argument, get_root

import argparse
import re
from pathlib import Path


ROOT: Path = Path.cwd()  # Set in main() via --project-root or CWD
HOOKS_PATH = ROOT / "story/pending_hooks.md"
ACTIVE_STATUSES = {"open", "progressing", "escalated", "dormant"}


def parse_table() -> tuple[list[str], list[dict[str, str]]]:
    lines = HOOKS_PATH.read_text(encoding="utf-8").splitlines()
    tables = [line for line in lines if line.startswith("|") and line.endswith("|")]
    if len(tables) < 2:
        return [], []
    header = [cell.strip() for cell in tables[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in tables[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))
    return header, rows


def as_int(value: str) -> int | None:
    match = re.search(r"\d+", value or "")
    if not match:
        return None
    return int(match.group(0))


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser()
    add_root_argument(parser)
    parser.add_argument("--current", type=int, required=True, help="current chapter number")
    args = parser.parse_args()
    ROOT = get_root(args)

    _, rows = parse_table()
    active = [row for row in rows if row.get("状态") in ACTIVE_STATUSES]
    core = [row for row in active if row.get("优先级") == "core"]
    escalated = [row for row in active if row.get("状态") == "escalated"]

    print(f"hook report: current chapter {args.current}")
    print(f"activeHooks: {len(active)} / 15")
    print(f"coreHooks: {len(core)} / 5")
    print(f"escalatedHooks: {len(escalated)}")

    warnings = 0
    if len(active) > 15:
        print("WARN: active hooks exceed budget")
        warnings += 1
    if len(core) > 5:
        print("WARN: core hooks exceed budget")
        warnings += 1

    overdue: list[tuple[str, int, int, int]] = []
    missing_evidence: list[str] = []
    for row in active:
        hook_id = row.get("hook_id", "")
        if not re.fullmatch(r"H\d{3,}", hook_id):
            print(f"WARN: invalid hook_id format: {hook_id!r}")
            warnings += 1
        last = as_int(row.get("最近推进", "")) or as_int(row.get("起始章节", ""))
        half_life = as_int(row.get("半衰期", ""))
        evidence = row.get("正文证据", "")
        if not evidence:
            missing_evidence.append(hook_id)
        if last is not None and half_life is not None:
            age = args.current - last
            if age > half_life:
                overdue.append((hook_id, last, half_life, age))

    if overdue:
        print("overdueHooks:")
        for hook_id, last, half_life, age in overdue:
            print(f"- {hook_id}: lastAdvanced={last}, halfLife={half_life}, age={age}")
        warnings += len(overdue)

    if missing_evidence:
        print("activeHooksMissingTextEvidence:")
        for hook_id in missing_evidence:
            print(f"- {hook_id}")
        warnings += len(missing_evidence)

    if warnings:
        print("hook report completed with warnings")
        return 1
    print("hook report OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

