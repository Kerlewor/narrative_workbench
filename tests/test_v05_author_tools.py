"""Tests for v0.5 author-facing helper tools."""

import zipfile
from pathlib import Path

from core.exporter import export_book
from core.scene_cards import create_scene_card, list_scene_cards
from core.voice_lab import build_voice_lab


def test_scene_card_create_and_list(project_root: Path):
    result = create_scene_card(
        project_root,
        chapter=3,
        scene_id="scene_01",
        title="旧站台入口",
        pov="林安",
        location="旧站台",
        purpose="引出雪牌线索",
        characters="林安,周月",
        hooks="HOOK_017",
        forbidden="SECRET_004",
    )

    assert result.path.is_file()
    assert "旧站台入口" in result.path.read_text(encoding="utf-8")
    listing = list_scene_cards(project_root, 3)
    assert listing["cards"][0]["id"] == "scene_01"


def test_voice_lab_writes_runtime_packet(project_root: Path):
    role = project_root / "story/roles/林安.md"
    role.write_text("# 林安\n\n## Personality Lock\n谨慎。\n", encoding="utf-8")

    result = build_voice_lab(project_root, "林安", "你为什么知道这块雪牌？")

    assert result.path.is_file()
    assert "角色声音实验室" in result.markdown
    assert "谨慎" in result.markdown


def test_export_docx_and_epub(project_root: Path):
    chapter = project_root / "chapters/0001_test.md"
    chapter.write_text("# 第一章\n\n她到达旧站台。\n", encoding="utf-8")

    docx = project_root / "exports/book.docx"
    epub = project_root / "exports/book.epub"
    docx_result = export_book(project_root, docx, "docx")
    epub_result = export_book(project_root, epub, "epub")

    assert docx_result.data["chapter_count"] == 1
    with zipfile.ZipFile(docx) as archive:
        assert "word/document.xml" in archive.namelist()
    with zipfile.ZipFile(epub) as archive:
        assert "OEBPS/chapter.xhtml" in archive.namelist()
