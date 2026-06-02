"""Tests for core.hooks reports and dependency checks."""

from pathlib import Path

from core.hooks import build_hook_matrix, build_hook_report, detect_cycles


def _write_hooks(root: Path) -> None:
    (root / "story").mkdir(parents=True, exist_ok=True)
    (root / "story/pending_hooks.md").write_text(
        """
| hook_id | 起始章节 | 类型 | 状态 | 优先级 | 最近推进 | 预期回收 | 回收卷/章 | 回收节奏 | 上游依赖 | 半衰期 | 升级条件 | 正文证据 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H001 | Ch1 | mystery | open | core | Ch1 | Ch3 | V1/C3 | fast |  | 1 |  | 证据 |  |
| H002 | Ch1 | clue | open | high | Ch1 | Ch4 | V1/C4 | slow | H001 | 5 |  |  |  |
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_detect_cycles_finds_simple_cycle():
    cycles = detect_cycles({"H001": ["H002"], "H002": ["H001"]})
    assert cycles


def test_hook_report_flags_overdue(project_root: Path):
    _write_hooks(project_root)

    code, lines = build_hook_report(project_root, 4)

    assert code == 1
    assert any("overdueHooks" in line for line in lines)
    assert any("H001" in line for line in lines)


def test_hook_matrix_warns_without_errors(project_root: Path):
    _write_hooks(project_root)

    code, lines = build_hook_matrix(project_root, 4)

    assert code == 0
    assert any("OK with hook warnings" in line for line in lines)
    assert any("active hook missing text evidence" in line for line in lines)

