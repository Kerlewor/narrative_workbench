"""Tests for core.prompt compilation."""

from pathlib import Path

from core.prompt import compile_prompt, expired_hook_lines


def test_compile_prompt_includes_missing_intent_message(project_root: Path):
    prompt = compile_prompt(project_root, "writer", 7)

    assert "Writer Agent" in prompt
    assert "intent 文件不存在" in prompt
    assert "输出契约" in prompt


def test_expired_hook_lines(project_root: Path):
    (project_root / "story/pending_hooks.md").write_text(
        """
| hook_id | 起始章节 | 类型 | 状态 | 优先级 | 最近推进 | 预期回收 | 回收卷/章 | 回收节奏 | 上游依赖 | 半衰期 | 升级条件 | 正文证据 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H001 | Ch1 | mystery | open | core | 1 | Ch2 | V1/C2 | fast |  | 1 |  | 证据 |  |
""".strip()
        + "\n",
        encoding="utf-8",
    )

    expired = expired_hook_lines(project_root, 3)

    assert expired
    assert "H001" in expired[0]

