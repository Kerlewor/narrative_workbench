"""Tests for core.gatekeeper deterministic checks."""

from pathlib import Path

from core.gatekeeper import build_report


def _write_complete_runtime(root: Path, chapter: int = 1) -> None:
    prefix = f"chapter-{chapter:04d}"
    runtime = root / "story/runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    for stage in ["plan", "writer", "polish", "review", "fixer"]:
        (runtime / f"{prefix}.{stage}.md").write_text(f"# {stage}\n", encoding="utf-8")
    (runtime / f"{prefix}.intent.md").write_text("status: fixed\n# intent\n", encoding="utf-8")


def test_missing_scene_handoff_is_warning_not_blocking(project_root: Path):
    _write_complete_runtime(project_root, 1)

    report = build_report(project_root, 1, "final")

    assert "**PASSED**" in report
    assert "场景接力卡不存在" in report
    assert "[BLOCKING] 场景接力卡" not in report


def test_malformed_scene_handoff_blocks(project_root: Path):
    _write_complete_runtime(project_root, 1)
    (project_root / "story/runtime/chapter-0001_scene_handoffs.yaml").write_text(
        "handoffs:\n  scene_01:\n    scene_id: scene_01\n",
        encoding="utf-8",
    )

    report = build_report(project_root, 1, "final")

    assert "**FAILED**" in report
    assert "[BLOCKING] 场景接力卡校验失败" in report
    assert "MISSING scene_01: handoff_to" in report or "MISSING handoff target" in report
