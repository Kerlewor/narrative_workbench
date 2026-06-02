"""Tests for layered co-writing diff workflow."""

from pathlib import Path

from core.diff_workflow import apply_candidates, generate_candidates, show_candidate


def test_generate_show_and_apply_diff(project_root: Path):
    original = project_root / "chapters/drafts/chapter-0001.author.md"
    revised = project_root / "story/runtime/chapter-0001.polish_candidate.md"
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_text(
        "她心里忽然有一种难以言说的感觉。\n\n周月说：“你不该来。”\n",
        encoding="utf-8",
    )
    revised.write_text(
        "她的手指停在雪牌缺口上，没有继续往下摸。\n\n周月压低声音：“你不该来。”\n",
        encoding="utf-8",
    )

    result = generate_candidates(project_root, 1, original, revised)
    assert result.data["candidate_count"] == 2
    assert result.index_path.is_file()
    assert result.jsonl_path.is_file()
    assert (result.patch_dir / "patch-01.md").is_file()

    detail = show_candidate(project_root, 1, "01")
    assert "修改 01" in detail
    assert "建议:" in detail

    applied = apply_candidates(project_root, 1, accept="01", reject="02")
    output = Path(applied["output_path"])
    assert output.is_file()
    text = output.read_text(encoding="utf-8")
    assert "她的手指停在雪牌缺口上" in text
    assert "周月说" in text
    assert Path(applied["decision_log"]).is_file()
