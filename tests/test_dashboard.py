"""Tests for the Markdown-native dashboard."""

from pathlib import Path

from core.dashboard import build_dashboard, write_dashboard


def test_build_dashboard_protocol(project_root: Path, sample_hooks_ledger: Path):
    result = build_dashboard(project_root)

    assert result.data["schema"] == "narrative_workbench.dashboard.v1"
    assert result.data["current_chapter"] == 1
    assert result.data["must_handle"]
    assert "创作控制台" in result.markdown
    assert "可直接输入的操作" in result.markdown


def test_write_dashboard_creates_markdown(project_root: Path):
    result = write_dashboard(project_root)
    output = project_root / "story/DASHBOARD.md"

    assert output.is_file()
    assert output.read_text(encoding="utf-8") == result.markdown


def test_dashboard_falls_back_to_pending_hooks_markdown(project_root: Path):
    hooks_ledger = project_root / "story/ledger/hooks.jsonl"
    hooks_ledger.write_text('{"_schema":"narrative_workbench.v1","_type":"hooks"}\n', encoding="utf-8")
    (project_root / "story/pending_hooks.md").write_text(
        "# 伏笔池\n\n"
        "| hook_id | 起始章节 | 类型 | 状态 | 优先级 | 最近推进 | 预期回收 | 回收卷/章 | 回收节奏 | 上游依赖 | 半衰期 | 升级条件 | 正文证据 | 备注 |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| H001 | 1 | 雪牌来源 | open | core | 1 | 第2-3章 |  |  |  | 3 |  | Ch1 |  |\n",
        encoding="utf-8",
    )

    result = build_dashboard(project_root)

    assert result.data["must_handle"]
    assert result.data["must_handle"][0]["id"] == "H001"
    assert "pending_hooks.md" == result.data["must_handle"][0]["source"]
