"""Tests for core.style text audits."""

from pathlib import Path

from core.style import audit_text, build_style_report, count_cjk_words


def test_count_cjk_words_counts_chinese_and_latin():
    assert count_cjk_words("林安 saw snow") == 5


def test_audit_text_flags_forbidden_quotes():
    code, lines = audit_text("「错误引号」")

    assert code == 1
    assert any("forbidden quote marks" in line for line in lines)


def test_build_style_report_from_input(tmp_path: Path):
    chapter = tmp_path / "chapter.md"
    chapter.write_text("她终于意识到。\n\n“你来了。”\n", encoding="utf-8")

    report = build_style_report(tmp_path, 1, str(chapter))

    assert "Style Report" in report
    assert "AI 味模式命中" in report
    assert "抽象心理总结" in report

