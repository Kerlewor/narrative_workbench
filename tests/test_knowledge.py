"""Tests for core.knowledge indexing."""

from pathlib import Path

from core.knowledge import build_index, build_knowledge_packet, query_index


def test_build_index_extracts_role_entity(project_root: Path):
    (project_root / "story/roles/lin_an.md").write_text("- 姓名: 林安\n", encoding="utf-8")

    index, path = build_index(project_root)

    assert path.is_file()
    assert any(entity.get("entity") == "林安" for entity in index["entities"])


def test_query_index_by_keyword(project_root: Path):
    (project_root / "story/roles/lin_an.md").write_text("- 姓名: 林安\n", encoding="utf-8")
    build_index(project_root)

    results = query_index(project_root, keyword="林安")

    assert results
    assert results[0]["type"] == "character"


def test_knowledge_packet_mentions_empty_index(project_root: Path):
    packet = build_knowledge_packet(project_root, 1, "writer")

    assert "Knowledge Packet" in packet
    assert "索引为空" in packet

