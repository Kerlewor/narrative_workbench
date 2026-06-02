"""Structured JSONL ledger operations for Narrative Workbench."""

from __future__ import annotations

import ast
import json
import operator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional


LEDGER_DIR = "story/ledger"

SCHEMAS: dict[str, dict] = {
    "facts": {
        "required": ["id", "name", "category", "content", "introduced_in"],
        "optional": [
            "related_characters",
            "related_hooks",
            "evidence_refs",
            "last_updated",
            "status",
            "notes",
        ],
    },
    "hooks": {
        "required": ["id", "name", "status", "introduced_in"],
        "optional": [
            "last_touched",
            "due_window",
            "related_characters",
            "reader_knows",
            "per_character_knowledge",
            "evidence_refs",
            "notes",
            "resolution_chapter",
            "resolution_evidence",
        ],
    },
    "timeline": {
        "required": ["event_id", "chapter", "description"],
        "optional": [
            "relative_time",
            "location",
            "characters_present",
            "preceding_event",
            "following_event",
            "evidence_ref",
        ],
    },
    "characters": {
        "required": ["id", "name", "role"],
        "optional": [
            "first_appearance",
            "last_appearance",
            "current_status",
            "knowledge_boundaries",
            "arc_stage",
            "evidence_ref",
        ],
    },
    "relationships": {
        "required": ["id", "from_char", "to_char", "type"],
        "optional": ["current_state", "last_changed_in", "evidence_ref", "notes"],
    },
    "secrets": {
        "required": ["id", "name", "content", "known_by", "unknown_by"],
        "optional": ["revealed_in", "partial_reveal_in", "evidence_ref", "notes"],
    },
    "locations": {
        "required": ["id", "name", "first_appears_in"],
        "optional": ["type", "description", "related_characters", "evidence_ref", "notes"],
    },
}


class LedgerError(ValueError):
    """Raised when a ledger operation cannot be completed."""


@dataclass(frozen=True)
class InitResult:
    ledger: str
    path: Path
    created: bool


@dataclass(frozen=True)
class ValidationReport:
    errors: int
    lines: list[str]

    @property
    def ok(self) -> bool:
        return self.errors == 0


def ledger_path(root: Path, ledger: str) -> Path:
    return root / LEDGER_DIR / f"{ledger}.jsonl"


def primary_key_field(ledger: str) -> str:
    return "event_id" if ledger == "timeline" else "id"


def ensure_known_ledger(ledger: str) -> None:
    if ledger not in SCHEMAS:
        available = ", ".join(SCHEMAS)
        raise LedgerError(f"Unknown ledger: {ledger}. Available: {available}")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def schema_header(ledger: str) -> str:
    return json.dumps({"_schema": "narrative_workbench.v1", "_type": ledger})


def read_records(
    root: Path,
    ledger: str,
    warn: Optional[Callable[[str], None]] = None,
) -> list[dict]:
    ensure_known_ledger(ledger)
    path = ledger_path(root, ledger)
    if not path.is_file():
        return []

    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            if warn:
                warn(f"WARNING: Skipping unparseable line in {ledger}: {line[:80]}...")
            continue
        if "_schema" in record:
            continue
        records.append(record)
    return records


def write_records(root: Path, ledger: str, records: list[dict]) -> None:
    ensure_known_ledger(ledger)
    path = ledger_path(root, ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(schema_header(ledger) + "\n")
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def init_ledgers(root: Path) -> list[InitResult]:
    results: list[InitResult] = []
    for name in SCHEMAS:
        path = ledger_path(root, name)
        if path.is_file():
            results.append(InitResult(name, path, False))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(schema_header(name) + "\n", encoding="utf-8")
        results.append(InitResult(name, path, True))
    return results


def missing_required_fields(ledger: str, record: dict) -> list[str]:
    ensure_known_ledger(ledger)
    schema = SCHEMAS[ledger]
    return [key for key in schema["required"] if key not in record or record[key] is None]


def parse_record(record_json: str) -> dict:
    try:
        record = json.loads(record_json)
    except json.JSONDecodeError as exc:
        raise LedgerError(f"Invalid JSON: {exc}") from exc
    if not isinstance(record, dict):
        raise LedgerError("Record JSON must be an object")
    return record


def add_record(root: Path, ledger: str, record: dict) -> str:
    ensure_known_ledger(ledger)
    missing = missing_required_fields(ledger, record)
    if missing:
        raise LedgerError(f"Missing required fields for {ledger}: {missing}")

    record = dict(record)
    if "last_updated" not in record:
        record["last_updated"] = now_iso()

    pk_field = primary_key_field(ledger)
    record_id = record.get(pk_field)
    records = read_records(root, ledger)
    if record_id in {item.get(pk_field) for item in records}:
        raise LedgerError(f"Duplicate id '{record_id}' - use update instead")

    records.append(record)
    write_records(root, ledger, records)
    return str(record_id)


def query_records(root: Path, ledger: str, filter_expr: Optional[str] = None) -> list[dict]:
    ensure_known_ledger(ledger)
    records = read_records(root, ledger)
    if not filter_expr:
        return records
    return [record for record in records if eval_filter(record, filter_expr)]


def update_record(root: Path, ledger: str, record_id: str, field: str, value: str) -> None:
    ensure_known_ledger(ledger)
    pk_field = primary_key_field(ledger)
    records = read_records(root, ledger)
    for record in records:
        if record.get(pk_field) == record_id:
            try:
                record[field] = json.loads(value)
            except json.JSONDecodeError:
                record[field] = value
            record["last_updated"] = now_iso()
            write_records(root, ledger, records)
            return
    raise LedgerError(f"Record '{record_id}' not found in {ledger}")


def validate_ledgers(root: Path) -> ValidationReport:
    errors = 0
    lines: list[str] = []
    for name, schema in SCHEMAS.items():
        path = ledger_path(root, name)
        if not path.is_file():
            lines.append(f"  {name}.jsonl - MISSING")
            errors += 1
            continue
        records = read_records(root, name)
        for index, record in enumerate(records):
            missing = [key for key in schema["required"] if key not in record]
            if missing:
                lines.append(f"  {name}#{index}: missing {missing}")
                errors += 1
        lines.append(f"  {name}.jsonl - {len(records)} record(s)")
    return ValidationReport(errors=errors, lines=lines)


def eval_filter(record: dict, expr: str) -> bool:
    """Evaluate a simple filter expression against a record."""

    if " in " in expr:
        field, value = expr.split(" in ", 1)
        field = field.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            try:
                values = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return False
            return record.get(field) in values

    ops = {
        "==": operator.eq,
        "!=": operator.ne,
        ">=": operator.ge,
        "<=": operator.le,
        ">": operator.gt,
        "<": operator.lt,
    }

    for op_text, op_func in ops.items():
        if op_text not in expr:
            continue
        field, value = expr.split(op_text, 1)
        field = field.strip()
        parsed_value: object = value.strip()

        if isinstance(parsed_value, str) and parsed_value.startswith("[") and parsed_value.endswith("]"):
            try:
                values = ast.literal_eval(parsed_value)
            except (ValueError, SyntaxError):
                return False
            return record.get(field) in values

        if isinstance(parsed_value, str) and parsed_value.startswith('"') and parsed_value.endswith('"'):
            parsed_value = parsed_value.strip('"')
        elif isinstance(parsed_value, str) and parsed_value.startswith("'") and parsed_value.endswith("'"):
            parsed_value = parsed_value.strip("'")
        else:
            try:
                parsed_value = int(parsed_value)
            except (TypeError, ValueError):
                pass

        return op_func(record.get(field), parsed_value)

    return True


def extract_chapter_metadata(root: Path, chapter: int) -> list[str]:
    """Extract deterministic metadata from a chapter director sheet."""

    prefix = f"chapter-{chapter:04d}"
    plan_path = root / "story/runtime" / f"{prefix}.plan.md"
    intent_path = root / "story/runtime" / f"{prefix}.intent.md"
    director_path = root / "story/plans" / f"{prefix}_director_sheet.yaml"

    lines = [
        f"Extracting facts for chapter {chapter}...",
        f"  Plan: {'found' if plan_path.is_file() else 'not found'}",
        f"  Intent: {'found' if intent_path.is_file() else 'not found'}",
        f"  Director sheet: {'found' if director_path.is_file() else 'not found'}",
        "",
        "(Note: Full NL-to-fact extraction requires AI. This script extracts",
        " structured metadata from known fields only. For full extraction, run",
        " the chapter through Review Agent with ledger sync enabled.)",
        "",
    ]

    if not director_path.is_file():
        lines.append("Done. Run 'ledger_manager.py validate' to verify all records.")
        return lines

    try:
        import yaml
    except ImportError:
        lines.append("  (yaml module not available, skipping director sheet extraction)")
        lines.append("")
        lines.append("Done. Run 'ledger_manager.py validate' to verify all records.")
        return lines

    try:
        with director_path.open("r", encoding="utf-8") as handle:
            director = yaml.safe_load(handle) or {}
        if not isinstance(director, dict):
            lines.append("  (director sheet is not a YAML mapping, skipping)")
            director = {}
    except Exception as exc:
        lines.append(f"  (YAML parse error: {exc}, skipping)")
        director = {}

    if not director:
        lines.append("")
        lines.append("Done. Run 'ledger_manager.py validate' to verify all records.")
        return lines

    opening_state = director.get("opening_state")
    if isinstance(opening_state, dict) and opening_state.get("location"):
        location_name = opening_state["location"]
        records = read_records(root, "locations")
        records.append(
            {
                "id": f"LOC_{chapter:04d}",
                "name": location_name,
                "first_appears_in": f"chapter_{chapter:04d}",
                "type": "scene",
            }
        )
        write_records(root, "locations", records)
        lines.append(f"  + location: {location_name}")

    scene_chain = director.get("scene_chain")
    if isinstance(scene_chain, list):
        chars_seen: set[str] = set()
        existing_chars = read_records(root, "characters")
        existing_ids = {record.get("id") for record in existing_chars}
        original_count = len(existing_chars)

        for scene in scene_chain:
            if not isinstance(scene, dict):
                continue
            for field in ["pov", "cast"]:
                if field not in scene:
                    continue
                value = scene[field]
                chars = value if isinstance(value, list) else [value]
                for char in chars:
                    if not char or char in chars_seen:
                        continue
                    chars_seen.add(char)
                    if char in existing_ids:
                        continue
                    existing_chars.append(
                        {
                            "id": char,
                            "name": char,
                            "role": "character",
                            "first_appearance": f"chapter_{chapter:04d}",
                        }
                    )
                    existing_ids.add(char)
                    lines.append(f"  + character: {char}")

        if len(existing_chars) > original_count:
            write_records(root, "characters", existing_chars)

    lines.append("")
    lines.append("Done. Run 'ledger_manager.py validate' to verify all records.")
    return lines

