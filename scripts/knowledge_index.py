#!/usr/bin/env python3
"""Knowledge Index for Narrative Workbench."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from _project import add_root_argument, get_root
from core.context import chapter_prefix
from core.knowledge import (  # noqa: E402
    build_index,
    build_knowledge_packet,
    entity_index_path,
    ensure_index_dir,
    extract_entities,
    knowledge_packet_path,
    query_index,
    scan_project,
)


ROOT: Path = Path.cwd()
INDEX_DIR = ROOT / ".nw_index"
ENTITY_INDEX_PATH = INDEX_DIR / "entity_index.json"


def cmd_build() -> int:
    index, path = build_index(ROOT)
    print(f"Index built: {len(index['entities'])} entities, {len(index['files'])} files")
    print(f"Output: {path.relative_to(ROOT)}")
    return 0


def build_knowledge_packet_compat(chapter: int, agent: str = "writer") -> str:
    return build_knowledge_packet(ROOT, chapter, agent)


def cmd_query(args: argparse.Namespace) -> int:
    if not entity_index_path(ROOT).is_file():
        print("索引尚未构建。请先运行: python scripts/knowledge_index.py build")
        return 1

    if args.chapter:
        packet = build_knowledge_packet(ROOT, args.chapter, args.agent or "writer")
        output = Path(args.output) if args.output else knowledge_packet_path(ROOT, args.chapter)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(packet, encoding="utf-8")
        print(f"Knowledge packet written to {output.relative_to(ROOT)}")
        return 0

    results = query_index(ROOT, keyword=args.keyword or "", domain=args.domain or "")
    if results:
        for result in results[:30]:
            print(f"[{result.get('type', '?')}] {result.get('entity', '?')} - {result.get('source', '?')}")
        if len(results) > 30:
            print(f"\n({len(results)} results total)")
    else:
        print("No results found.")
    return 0


def main() -> int:
    global ROOT, INDEX_DIR, ENTITY_INDEX_PATH
    parser = argparse.ArgumentParser(description="Knowledge Index for Narrative Workbench")
    add_root_argument(parser)
    sub = parser.add_subparsers(dest="command", help="build | query")

    sub.add_parser("build", help="扫描项目文件并构建索引")

    query_parser = sub.add_parser("query", help="查询知识库索引")
    query_parser.add_argument("--keyword", type=str, default=None, help="检索关键词")
    query_parser.add_argument("--domain", type=str, default=None, help="领域筛选")
    query_parser.add_argument("--chapter", type=int, default=0, help="生成知识包的目标章节")
    query_parser.add_argument("--agent", type=str, default="writer", help="目标 Agent")
    query_parser.add_argument("--output", type=str, default=None, help="输出路径")

    args = parser.parse_args()
    ROOT = get_root(args)
    INDEX_DIR = ROOT / ".nw_index"
    ENTITY_INDEX_PATH = INDEX_DIR / "entity_index.json"

    if args.command == "build":
        return cmd_build()
    if args.command == "query":
        return cmd_query(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
