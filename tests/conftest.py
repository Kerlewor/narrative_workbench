"""Test fixtures for Narrative Workbench."""

import json
import sys
from pathlib import Path

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a minimal Narrative Workbench project structure."""
    root = tmp_path / "test_project"

    # Core directories
    (root / "chapters").mkdir(parents=True)
    (root / "story/runtime").mkdir(parents=True)
    (root / "story/outline").mkdir(parents=True)
    (root / "story/roles").mkdir(parents=True)
    (root / "story/ledger").mkdir(parents=True)
    (root / "story/views").mkdir(parents=True)
    (root / "story/plans").mkdir(parents=True)
    (root / "story/state").mkdir(parents=True)
    (root / "agents").mkdir(parents=True)

    # Minimal files
    (root / "chapters/index.json").write_text("{}", encoding="utf-8")
    (root / "story/chapter_summaries.md").write_text(
        "# Chapter Summaries\n\n"
        "| 章节 | 标题 | 出场人物 | 关键事件 | 状态变化 | 伏笔动态 | 情绪基调 | 章节类型 |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| 1 | 第一章标题 | 林安 | 到达民宿 | 初始状态 | 引入雪牌 | 悬疑 | setup |\n"
        "| 2 | 第二章标题 | 林安,周月 | 发现旧照片 | 周月回避 | 推进雪牌 | 紧张 | development |\n",
        encoding="utf-8"
    )
    (root / "story/pending_hooks.md").write_text(
        "# Pending Hooks\n\n| HOOK_001 | 雪牌来源 | open | Ch03 | ... |\n",
        encoding="utf-8"
    )
    (root / "story/current_state.md").write_text("# Current State\n\n", encoding="utf-8")

    # Initialize ledgers
    for ledger in ["facts", "hooks", "timeline", "characters", "relationships", "secrets", "locations"]:
        path = root / f"story/ledger/{ledger}.jsonl"
        header = json.dumps({"_schema": "narrative_workbench.v1", "_type": ledger})
        path.write_text(header + "\n", encoding="utf-8")

    return root


@pytest.fixture
def sample_hooks_ledger(project_root: Path) -> Path:
    """Create a ledger with sample hook records."""
    path = project_root / "story/ledger/hooks.jsonl"
    records = [
        {"_schema": "narrative_workbench.v1", "_type": "hooks"},
        {"id": "HOOK_001", "name": "雪牌来源", "status": "open",
         "introduced_in": "chapter_03", "last_touched": "chapter_11",
         "due_window": [18, 24], "related_characters": ["lin_an", "zhou_yue"],
         "reader_knows": True},
        {"id": "HOOK_002", "name": "周月身份", "status": "open",
         "introduced_in": "chapter_06", "last_touched": "chapter_15",
         "due_window": [25, 30], "related_characters": ["zhou_yue"],
         "reader_knows": False},
        {"id": "HOOK_003", "name": "旧车票线索", "status": "resolved",
         "introduced_in": "chapter_02", "last_touched": "chapter_05",
         "resolution_chapter": "chapter_05", "related_characters": ["lin_an"]},
    ]
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def sample_characters_ledger(project_root: Path) -> Path:
    """Create a ledger with sample character records."""
    path = project_root / "story/ledger/characters.jsonl"
    records = [
        {"_schema": "narrative_workbench.v1", "_type": "characters"},
        {"id": "lin_an", "name": "林安", "role": "protagonist",
         "first_appearance": "chapter_01", "last_appearance": "chapter_18",
         "current_status": "怀疑周月"},
        {"id": "zhou_yue", "name": "周月", "role": "supporting",
         "first_appearance": "chapter_03", "last_appearance": "chapter_18",
         "current_status": "回避林安"},
        {"id": "chen_yu", "name": "陈雨", "role": "minor",
         "first_appearance": "chapter_02", "last_appearance": "chapter_08",
         "current_status": "未出场"},
    ]
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
