"""Tests for core.chapter planning helpers."""

from pathlib import Path

from core.chapter import validate_director_sheet, validate_scene_handoffs


def test_validate_director_sheet_accepts_complete_sheet(project_root: Path):
    path = project_root / "story/plans/chapter-0003_director_sheet.yaml"
    path.write_text(
        """
chapter: 3
title: "第三章"
pov: "lin_an"
chapter_purpose:
  plot: "推进"
opening_state:
  location: "民宿"
closing_state:
  location: "旧站台"
emotional_arc:
  start: "怀疑"
  middle: "对抗"
  end: "疏离"
forbidden_reveals:
  - "身份"
style_arc:
  scene_01: "冷静"
scene_chain:
  - id: scene_01
    role: "引发"
    input_state: "看见雪牌"
    output_state: "产生怀疑"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    report = validate_director_sheet(project_root, 3)
    assert report.ok


def test_validate_scene_handoffs_accepts_complete_handoff(project_root: Path):
    path = project_root / "story/runtime/chapter-0003_scene_handoffs.yaml"
    path.write_text(
        """
handoffs:
  scene_01:
    scene_id: scene_01
    handoff_to: scene_02
    physical_state:
      location: "民宿"
    emotional_state:
      lin_an: "怀疑"
    revealed_information:
      - "林安看见雪牌"
    unresolved_tension:
      - "周月回避"
    required_next_scene_input:
      - "林安继续追问"
    do_not_resolve_in_this_scene:
      - "不得揭示身份"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    report = validate_scene_handoffs(project_root, 3)
    assert report.ok


def test_validate_scene_handoffs_reports_missing_file(project_root: Path):
    report = validate_scene_handoffs(project_root, 99)
    assert not report.ok
    assert "not found" in report.lines[0]

