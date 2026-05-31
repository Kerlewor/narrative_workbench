"""Ledger Manager for Narrative Workbench.

Manages the structured novel fact ledger — a set of JSONL files that provide
program-retrievable records of hooks, facts, timeline, characters, relationships,
secrets, and locations. JSONL is the primary format for script consumption;
Markdown views are rendered separately for author readability.

Usage:
    python scripts/ledger_manager.py init                    # Initialize all ledger files
    python scripts/ledger_manager.py add hooks '{"id":"HOOK_001",...}'
    python scripts/ledger_manager.py query hooks --filter 'status=="open"'
    python scripts/ledger_manager.py validate                # Validate all records against schemas
    python scripts/ledger_manager.py list hooks              # List all records in a ledger
    python scripts/ledger_manager.py extract --chapter 19    # Extract facts from chapter runtime

Schema:
    Each JSONL line is a JSON object. The first line of each file is a schema
    version marker: {"_schema": "narrative_workbench.v1", "_type": "<type>"}
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from _project import add_root_argument, get_root

ROOT: Path = Path.cwd()

LEDGER_DIR = "story/ledger"

SCHEMAS: dict[str, dict] = {
    "facts": {
        "required": ["id", "name", "category", "content", "introduced_in"],
        "optional": ["related_characters", "related_hooks", "evidence_refs",
                      "last_updated", "status", "notes"],
    },
    "hooks": {
        "required": ["id", "name", "status", "introduced_in"],
        "optional": ["last_touched", "due_window", "related_characters",
                      "reader_knows", "per_character_knowledge", "evidence_refs",
                      "notes", "resolution_chapter", "resolution_evidence"],
    },
    "timeline": {
        "required": ["event_id", "chapter", "description"],
        "optional": ["relative_time", "location", "characters_present",
                      "preceding_event", "following_event", "evidence_ref"],
    },
    "characters": {
        "required": ["id", "name", "role"],
        "optional": ["first_appearance", "last_appearance", "current_status",
                      "knowledge_boundaries", "arc_stage", "evidence_ref"],
    },
    "relationships": {
        "required": ["id", "from_char", "to_char", "type"],
        "optional": ["current_state", "last_changed_in", "evidence_ref",
                      "notes"],
    },
    "secrets": {
        "required": ["id", "name", "content", "known_by", "unknown_by"],
        "optional": ["revealed_in", "partial_reveal_in", "evidence_ref",
                      "notes"],
    },
    "locations": {
        "required": ["id", "name", "first_appears_in"],
        "optional": ["type", "description", "related_characters",
                      "evidence_ref", "notes"],
    },
}


def ledger_path(ledger: str) -> Path:
    return ROOT / LEDGER_DIR / f"{ledger}.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_records(ledger: str) -> list[dict]:
    """Read all records from a ledger file, skipping schema header."""
    path = ledger_path(ledger)
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
            print(f"WARNING: Skipping unparseable line in {ledger}: {line[:80]}...", file=sys.stderr)
            continue
        if "_schema" in record:
            continue
        records.append(record)
    return records


def _write_records(ledger: str, records: list[dict]) -> None:
    path = ledger_path(ledger)
    header = json.dumps({"_schema": "narrative_workbench.v1", "_type": ledger})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(header + "\n")
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def cmd_init() -> int:
    """Initialize all ledger files if they don't exist."""
    for name in SCHEMAS:
        path = ledger_path(name)
        if path.is_file():
            print(f"  {name}.jsonl — exists (skipped)")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        header = json.dumps({"_schema": "narrative_workbench.v1", "_type": name})
        path.write_text(header + "\n", encoding="utf-8")
        print(f"  {name}.jsonl — created")
    return 0


def cmd_add(ledger: str, record_json: str) -> int:
    if ledger not in SCHEMAS:
        print(f"Unknown ledger: {ledger}. Available: {', '.join(SCHEMAS)}", file=sys.stderr)
        return 1

    try:
        record = json.loads(record_json)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return 1

    schema = SCHEMAS[ledger]
    missing = [k for k in schema["required"] if k not in record or record[k] is None]
    if missing:
        print(f"Missing required fields for {ledger}: {missing}", file=sys.stderr)
        return 1

    if "last_updated" not in record:
        record["last_updated"] = _now_iso()

    # Timeline uses event_id as primary key; all others use id
    pk_field = "event_id" if ledger == "timeline" else "id"
    records = _read_records(ledger)
    existing_ids = {r.get(pk_field) for r in records}
    if record.get(pk_field) in existing_ids:
        dup_id = record.get(pk_field, record.get('id', '<unknown>'))
        print(f"WARNING: Duplicate id '{dup_id}' — use update instead", file=sys.stderr)
        return 1

    records.append(record)
    _write_records(ledger, records)
    print(f"Added to {ledger}: {record.get(pk_field)}")
    return 0


def cmd_query(ledger: str, filter_expr: Optional[str] = None) -> int:
    if ledger not in SCHEMAS:
        print(f"Unknown ledger: {ledger}", file=sys.stderr)
        return 1

    records = _read_records(ledger)

    if filter_expr:
        try:
            records = [r for r in records if _eval_filter(r, filter_expr)]
        except Exception as e:
            print(f"Filter error: {e}", file=sys.stderr)
            return 1

    for rec in records:
        print(json.dumps(rec, ensure_ascii=False))
    print(f"\n{len(records)} record(s)")
    return 0


def cmd_list(ledger: str) -> int:
    return cmd_query(ledger)


def cmd_validate() -> int:
    errors = 0
    for name, schema in SCHEMAS.items():
        path = ledger_path(name)
        if not path.is_file():
            print(f"  {name}.jsonl — MISSING")
            errors += 1
            continue
        records = _read_records(name)
        for i, rec in enumerate(records):
            missing = [k for k in schema["required"] if k not in rec]
            if missing:
                print(f"  {name}#{i}: missing {missing}")
                errors += 1
        print(f"  {name}.jsonl — {len(records)} record(s)")
    if errors:
        print(f"\n{errors} validation error(s)")
        return 1
    print("\nAll ledgers valid")
    return 0


def cmd_update(ledger: str, record_id: str, field: str, value: str) -> int:
    if ledger not in SCHEMAS:
        print(f"Unknown ledger: {ledger}", file=sys.stderr)
        return 1

    pk_field = "event_id" if ledger == "timeline" else "id"
    records = _read_records(ledger)
    found = False
    for rec in records:
        if rec.get(pk_field) == record_id:
            try:
                rec[field] = json.loads(value)
            except json.JSONDecodeError:
                rec[field] = value
            rec["last_updated"] = _now_iso()
            found = True
            break

    if not found:
        print(f"Record '{record_id}' not found in {ledger}", file=sys.stderr)
        return 1

    _write_records(ledger, records)
    print(f"Updated {ledger}#{record_id}: {field} = {value}")
    return 0


def cmd_extract(chapter: int) -> int:
    """Best-effort extraction of facts from chapter runtime files.

    Reads chapter plan (for cast_ids, hook_ids, etc.) and director sheet
    (if available), then extracts structured records into appropriate ledgers.
    """
    def _chapter_prefix(n: int) -> str:
        return f"chapter-{n:04d}"

    prefix = _chapter_prefix(chapter)

    plan_path = ROOT / "story/runtime" / f"{prefix}.plan.md"
    intent_path = ROOT / "story/runtime" / f"{prefix}.intent.md"
    director_path = ROOT / "story/plans" / f"{prefix}_director_sheet.yaml"
    chapter_path = ROOT / "chapters" / f"{prefix}*.md"

    print(f"Extracting facts for chapter {chapter}...")
    print(f"  Plan: {'found' if plan_path.is_file() else 'not found'}")
    print(f"  Intent: {'found' if intent_path.is_file() else 'not found'}")
    print(f"  Director sheet: {'found' if director_path.is_file() else 'not found'}")
    print("\n(Note: Full NL-to-fact extraction requires AI. This script extracts")
    print(" structured metadata from known fields only. For full extraction, run")
    print(" the chapter through Review Agent with ledger sync enabled.)\n")

    # Extract from director sheet if available
    if director_path.is_file():
        try:
            import yaml
            with director_path.open("r", encoding="utf-8") as f:
                director = yaml.safe_load(f) or {}
            if not isinstance(director, dict):
                print("  (director sheet is not a YAML mapping, skipping)")
                director = {}
        except ImportError:
            print("  (yaml module not available, skipping director sheet extraction)")
            director = {}
        except Exception as e:
            print(f"  (YAML parse error: {e}, skipping)")
            director = {}

        if director:
            # Extract location from director sheet
            if "opening_state" in director and "location" in director["opening_state"]:
                loc_name = director["opening_state"]["location"]
                loc_rec = {
                    "id": f"LOC_{chapter:04d}",
                    "name": loc_name,
                    "first_appears_in": f"chapter_{chapter:04d}",
                    "type": "scene",
                }
                records = _read_records("locations")
                records.append(loc_rec)
                _write_records("locations", records)
                print(f"  + location: {loc_name}")

            # Extract character appearances from cast
            if "scene_chain" in director:
                chars_seen = set()
                existing_chars = _read_records("characters")
                existing_ids = {r.get("id") for r in existing_chars}
                for scene in director["scene_chain"]:
                    for field in ["pov", "cast"]:
                        if field in scene:
                            for char in (scene[field] if isinstance(scene[field], list) else [scene[field]]):
                                if char not in chars_seen:
                                    chars_seen.add(char)
                                    if char not in existing_ids:
                                        char_rec = {
                                            "id": char,
                                            "name": char,
                                            "role": "character",
                                            "first_appearance": f"chapter_{chapter:04d}",
                                        }
                                        existing_chars.append(char_rec)
                                        existing_ids.add(char)
                                        print(f"  + character: {char}")
                if len(existing_chars) > len(_read_records("characters")):
                    _write_records("characters", existing_chars)

    print("\nDone. Run 'ledger_manager.py validate' to verify all records.")
    return 0


def _eval_filter(record: dict, expr: str) -> bool:
    """Evaluate a simple filter expression against a record.

    Supported syntax:
        field=="value"       — exact match
        field!="value"       — not equal
        field in ["a","b"]   — field in list
        chapter >= N         — numeric comparison (for 'chapter' or 'last_advanced')
    """
    import ast
    import operator
    import re

    # Handle "field in [...]" first (no standard comparison operator)
    if " in " in expr:
        parts = expr.split(" in ", 1)
        field = parts[0].strip()
        val = parts[1].strip()
        if val.startswith("[") and val.endswith("]"):
            try:
                lst = ast.literal_eval(val)
            except (ValueError, SyntaxError):
                return False
            return record.get(field) in lst

    ops = {
        "==": operator.eq,
        "!=": operator.ne,
        ">=": operator.ge,
        "<=": operator.le,
        ">": operator.gt,
        "<": operator.lt,
    }

    for op_str, op_func in ops.items():
        if op_str in expr:
            parts = expr.split(op_str, 1)
            field = parts[0].strip()
            val = parts[1].strip()

            if val.startswith("[") and val.endswith("]"):
                try:
                    lst = ast.literal_eval(val)
                except (ValueError, SyntaxError):
                    return False
                return record.get(field) in lst

            if val.startswith('"') and val.endswith('"'):
                val = val.strip('"')
            elif val.startswith("'") and val.endswith("'"):
                val = val.strip("'")
            else:
                try:
                    val = int(val)
                except ValueError:
                    pass

            return op_func(record.get(field), val)

    return True


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Ledger Manager for Narrative Workbench")
    add_root_argument(parser)

    subparsers = parser.add_subparsers(dest="command", help="Command")

    p_init = subparsers.add_parser("init", help="Initialize all ledger files")
    p_add = subparsers.add_parser("add", help="Add a record to a ledger")
    p_add.add_argument("ledger", choices=list(SCHEMAS), help="Ledger type")
    p_add.add_argument("record", help="JSON record string")

    p_query = subparsers.add_parser("query", help="Query records in a ledger")
    p_query.add_argument("ledger", choices=list(SCHEMAS), help="Ledger type")
    p_query.add_argument("--filter", type=str, default=None, help="Filter expression")

    p_list = subparsers.add_parser("list", help="List all records in a ledger")
    p_list.add_argument("ledger", choices=list(SCHEMAS), help="Ledger type")

    p_validate = subparsers.add_parser("validate", help="Validate all ledger records")

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
    elif args.command == "add":
        return cmd_add(args.ledger, args.record)
    elif args.command == "query":
        return cmd_query(args.ledger, args.filter)
    elif args.command == "list":
        return cmd_list(args.ledger)
    elif args.command == "validate":
        return cmd_validate()
    elif args.command == "update":
        return cmd_update(args.ledger, args.record_id, args.field, args.value)
    elif args.command == "extract":
        return cmd_extract(args.chapter)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
