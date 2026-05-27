#!/usr/bin/env python3
"""Validate skills/skill_registry.md.

Usage:
    python3 scripts/skill_check.py
    python3 scripts/skill_check.py --skill skill-name
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "skills/skill_registry.md"
VALID_STATUSES = {"enabled", "disabled", "deprecated"}
EXPECTED_HEADER = ["skill", "用途", "触发条件", "入口文件/说明", "输出位置", "状态"]


def parse_table() -> tuple[list[str], list[dict[str, str]]]:
    lines = REGISTRY.read_text(encoding="utf-8").splitlines()
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


def extract_paths(value: str) -> list[str]:
    code_paths = re.findall(r"`([^`]+)`", value or "")
    plain_paths = re.findall(r"(skills/[^\s|]+\.md)", value or "")
    paths = code_paths + plain_paths
    return sorted(set(paths))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", help="require a specific skill to be registered")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    header, rows = parse_table()
    print("skill registry check")
    print(f"root: {ROOT}")

    if header != EXPECTED_HEADER:
        errors.append("skill_registry.md header does not match expected structure")

    seen: set[str] = set()
    enabled = 0
    for row in rows:
        skill = row.get("skill", "")
        status = row.get("状态", "")
        entry = row.get("入口文件/说明", "")
        if not skill:
            errors.append("empty skill name")
            continue
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", skill):
            errors.append(f"{skill}: invalid skill name; use letters, numbers, hyphen, underscore")
        if skill in seen:
            errors.append(f"{skill}: duplicate registry entry")
        seen.add(skill)
        if status not in VALID_STATUSES:
            errors.append(f"{skill}: invalid status {status}")
        if status == "enabled":
            enabled += 1
        if not row.get("触发条件", ""):
            warnings.append(f"{skill}: missing trigger condition")
        if not row.get("输出位置", ""):
            warnings.append(f"{skill}: missing output location")
        paths = extract_paths(entry)
        if not paths:
            warnings.append(f"{skill}: entry file/description has no explicit path")
        for rel in paths:
            if rel.startswith("skills/") and not (ROOT / rel).is_file():
                errors.append(f"{skill}: entry file missing: {rel}")

    if args.skill and args.skill not in seen:
        errors.append(f"required skill is not registered: {args.skill}")

    print(f"registeredSkills: {len(rows)}")
    print(f"enabledSkills: {enabled}")

    if errors:
        print("\nERRORS:")
        for item in errors:
            print(f"- {item}")
    if warnings:
        print("\nWARNINGS:")
        for item in warnings:
            print(f"- {item}")
    if not errors and not warnings:
        print("\nOK: skill registry is valid.")
    elif not errors:
        print("\nOK with skill warnings.")
    else:
        print("\nFAILED.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

