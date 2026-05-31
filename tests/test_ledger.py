"""Tests for ledger_manager.py — CRUD operations and validation."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest
from ledger_manager import (
    _read_records,
    _write_records,
    cmd_init,
    cmd_add,
    cmd_validate,
    SCHEMAS,
    ledger_path,
    ROOT as ledger_root,
)


class TestLedgerCRUD:
    def test_init_creates_all_ledgers(self, project_root: Path):
        ledger_root = project_root
        for name in SCHEMAS:
            path = ledger_path(name)
            if path.is_file():
                path.unlink()

        # Patch ROOT to test project
        import ledger_manager
        ledger_manager.ROOT = project_root

        result = cmd_init()
        assert result == 0

        for name in SCHEMAS:
            path = project_root / "story/ledger" / f"{name}.jsonl"
            assert path.is_file(), f"{name}.jsonl should exist"

    def test_add_valid_record(self, project_root: Path):
        import ledger_manager
        ledger_manager.ROOT = project_root
        cmd_init()

        record = json.dumps({
            "id": "HOOK_TEST",
            "name": "测试伏笔",
            "status": "open",
            "introduced_in": "chapter_01",
        })
        result = cmd_add("hooks", record)
        assert result == 0

        records = _read_records("hooks")
        assert len(records) == 1
        assert records[0]["id"] == "HOOK_TEST"

    def test_add_missing_required_fields(self, project_root: Path):
        import ledger_manager
        ledger_manager.ROOT = project_root
        cmd_init()

        record = json.dumps({"id": "BAD_RECORD"})
        result = cmd_add("hooks", record)
        assert result == 1


class TestLedgerValidation:
    def test_validate_empty_ledgers(self, project_root: Path):
        import ledger_manager
        ledger_manager.ROOT = project_root
        cmd_init()

        result = cmd_validate()
        assert result == 0

    def test_filter_hooks_by_status(self, project_root: Path, sample_hooks_ledger: Path):
        import ledger_manager
        ledger_manager.ROOT = project_root

        records = _read_records("hooks")
        open_hooks = [r for r in records if r.get("status") == "open"]
        resolved_hooks = [r for r in records if r.get("status") == "resolved"]

        assert len(open_hooks) == 2
        assert len(resolved_hooks) == 1


class TestContextBudget:
    def test_budget_estimation(self):
        from relevance_resolver import estimate_tokens

        assert estimate_tokens("hello world") == 5
        assert estimate_tokens("你好世界") == 2
        assert estimate_tokens("") == 0

    def test_agent_budgets_defined(self):
        from relevance_resolver import AGENT_BUDGETS

        for agent in ["writer", "polish", "review", "fixer"]:
            assert agent in AGENT_BUDGETS
            assert AGENT_BUDGETS[agent] > 0
