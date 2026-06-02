"""Ledger Manager for Narrative Workbench.

Manages structured JSONL ledgers for hooks, facts, timeline, characters,
relationships, secrets, and locations. This script is the CLI wrapper; reusable
ledger logic lives in core.ledger.

Usage:
    python scripts/ledger_manager.py init
    python scripts/ledger_manager.py add hooks '{"id":"HOOK_001",...}'
    python scripts/ledger_manager.py query hooks --filter 'status=="open"'
    python scripts/ledger_manager.py validate
    python scripts/ledger_manager.py list hooks
    python scripts/ledger_manager.py extract --chapter 19
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from _project import add_root_argument, get_root
from core.ledger import (  # noqa: E402
    SCHEMAS,
    LedgerError,
    add_record,
    eval_filter,
    extract_chapter_metadata,
    init_ledgers,
    ledger_path as core_ledger_path,
    parse_record,
    query_records,
    read_records,
    update_record,
    validate_ledgers,
    write_records,
)


ROOT: Path = Path.cwd()


def ledger_path(ledger: str) -> Path:
    return core_ledger_path(ROOT, ledger)


def _warn(message: str) -> None:
    print(message, file=sys.stderr)


def _read_records(ledger: str) -> list[dict]:
    return read_records(ROOT, ledger, warn=_warn)


def _write_records(ledger: str, records: list[dict]) -> None:
    write_records(ROOT, ledger, records)


def cmd_init() -> int:
    """Initialize all ledger files if they do not exist."""
    for result in init_ledgers(ROOT):
        if result.created:
            print(f"  {result.ledger}.jsonl - created")
        else:
            print(f"  {result.ledger}.jsonl - exists (skipped)")
    return 0


def cmd_add(ledger: str, record_json: str) -> int:
    try:
        record = parse_record(record_json)
        record_id = add_record(ROOT, ledger, record)
    except LedgerError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Added to {ledger}: {record_id}")
    return 0


def cmd_query(ledger: str, filter_expr: Optional[str] = None) -> int:
    try:
        records = query_records(ROOT, ledger, filter_expr)
    except LedgerError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Filter error: {exc}", file=sys.stderr)
        return 1

    for record in records:
        print(json.dumps(record, ensure_ascii=False))
    print(f"\n{len(records)} record(s)")
    return 0


def cmd_list(ledger: str) -> int:
    return cmd_query(ledger)


def cmd_validate() -> int:
    report = validate_ledgers(ROOT)
    for line in report.lines:
        print(line)
    if report.errors:
        print(f"\n{report.errors} validation error(s)")
        return 1
    print("\nAll ledgers valid")
    return 0


def cmd_update(ledger: str, record_id: str, field: str, value: str) -> int:
    try:
        update_record(ROOT, ledger, record_id, field, value)
    except LedgerError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Updated {ledger}#{record_id}: {field} = {value}")
    return 0


def cmd_extract(chapter: int) -> int:
    for line in extract_chapter_metadata(ROOT, chapter):
        print(line)
    return 0


def _eval_filter(record: dict, expr: str) -> bool:
    return eval_filter(record, expr)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Ledger Manager for Narrative Workbench")
    add_root_argument(parser)

    subparsers = parser.add_subparsers(dest="command", help="Command")

    subparsers.add_parser("init", help="Initialize all ledger files")

    p_add = subparsers.add_parser("add", help="Add a record to a ledger")
    p_add.add_argument("ledger", choices=list(SCHEMAS), help="Ledger type")
    p_add.add_argument("record", help="JSON record string")

    p_query = subparsers.add_parser("query", help="Query records in a ledger")
    p_query.add_argument("ledger", choices=list(SCHEMAS), help="Ledger type")
    p_query.add_argument("--filter", type=str, default=None, help="Filter expression")

    p_list = subparsers.add_parser("list", help="List all records in a ledger")
    p_list.add_argument("ledger", choices=list(SCHEMAS), help="Ledger type")

    subparsers.add_parser("validate", help="Validate all ledger records")

    p_update = subparsers.add_parser("update", help="Update a record field")
    p_update.add_argument("ledger", choices=list(SCHEMAS), help="Ledger type")
    p_update.add_argument("record_id", help="Record ID")
    p_update.add_argument("field", help="Field name")
    p_update.add_argument("value", help="New value (JSON literal)")

    p_extract = subparsers.add_parser("extract", help="Extract facts from chapter runtime")
    p_extract.add_argument("--chapter", type=int, required=True, help="Chapter number")

    args = parser.parse_args()
    ROOT = get_root(args)

    if args.command == "init":
        return cmd_init()
    if args.command == "add":
        return cmd_add(args.ledger, args.record)
    if args.command == "query":
        return cmd_query(args.ledger, args.filter)
    if args.command == "list":
        return cmd_list(args.ledger)
    if args.command == "validate":
        return cmd_validate()
    if args.command == "update":
        return cmd_update(args.ledger, args.record_id, args.field, args.value)
    if args.command == "extract":
        return cmd_extract(args.chapter)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
