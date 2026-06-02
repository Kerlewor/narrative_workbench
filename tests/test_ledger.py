"""Tests for core.ledger and the ledger_manager CLI wrapper."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from core.ledger import (
    SCHEMAS,
    LedgerError,
    add_record,
    init_ledgers,
    ledger_path,
    query_records,
    read_records,
    validate_ledgers,
)


class TestLedgerCRUD:
    def test_init_creates_all_ledgers(self, project_root: Path):
        for name in SCHEMAS:
            path = ledger_path(project_root, name)
            if path.is_file():
                path.unlink()

        results = init_ledgers(project_root)
        assert all(result.created for result in results)

        for name in SCHEMAS:
            path = project_root / "story/ledger" / f"{name}.jsonl"
            assert path.is_file(), f"{name}.jsonl should exist"

    def test_add_valid_record(self, project_root: Path):
        init_ledgers(project_root)

        record = {
            "id": "HOOK_TEST",
            "name": "测试伏笔",
            "status": "open",
            "introduced_in": "chapter_01",
        }
        record_id = add_record(project_root, "hooks", record)
        assert record_id == "HOOK_TEST"

        records = read_records(project_root, "hooks")
        assert len(records) == 1
        assert records[0]["id"] == "HOOK_TEST"

    def test_add_missing_required_fields(self, project_root: Path):
        init_ledgers(project_root)

        with pytest.raises(LedgerError):
            add_record(project_root, "hooks", {"id": "BAD_RECORD"})


class TestLedgerValidation:
    def test_validate_empty_ledgers(self, project_root: Path):
        init_ledgers(project_root)

        report = validate_ledgers(project_root)
        assert report.ok

    def test_filter_hooks_by_status(self, project_root: Path, sample_hooks_ledger: Path):
        open_hooks = query_records(project_root, "hooks", 'status=="open"')
        resolved_hooks = query_records(project_root, "hooks", 'status=="resolved"')

        assert len(open_hooks) == 2
        assert len(resolved_hooks) == 1


class TestLedgerCLI:
    def test_validate_command_uses_project_root(self, project_root: Path):
        script = Path(__file__).resolve().parents[1] / "scripts" / "ledger_manager.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--project-root",
                str(project_root),
                "validate",
            ],
            capture_output=True,
            encoding="utf-8",
            check=False,
        )

        assert result.returncode == 0
        assert "All ledgers valid" in result.stdout


class TestContextBudget:
    def test_budget_estimation(self):
        from core.context import estimate_tokens

        assert estimate_tokens("hello world") == 5
        assert estimate_tokens("你好世界") == 2
        assert estimate_tokens("") == 0

    def test_agent_budgets_defined(self):
        from core.context import AGENT_BUDGETS

        for agent in ["writer", "polish", "review", "fixer"]:
            assert agent in AGENT_BUDGETS
            assert AGENT_BUDGETS[agent] > 0
