#!/usr/bin/env python3
"""Knowledge Index for Narrative Workbench.

Builds and queries a lightweight project knowledge index.
First version uses keyword + metadata — no vector database.

Usage:
    python3 scripts/knowledge_index.py build
    python3 scripts/knowledge_index.py query --chapter 12 --agent writer
    python3 scripts/knowledge_index.py query --domain 中医方剂 --keyword 金疮药

Output:
    runtime/chapter-0012.knowledge_packet.md (query mode)
    .nw_index/entity_index.json (build mode)
"""

from __future__ import annotations
from _project import add_root_argument, get_root

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

ROOT: Path = Path.cwd()  # Set in main() via --project-root or CWD
INDEX_DIR = ROOT / ".nw_index"
ENTITY_INDEX_PATH = INDEX_DIR / "entity_index.json"


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def ensure_index_dir() -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def extract_entities(text: str, source: str, file_type: str) -> list[dict]:
    entities: list[dict] = []
    entity_patterns = {
        "character": re.compile(
            r"(?:角色|姓名|name)[：:]\s*(.+)|"
            r"##\s*(?:核心标签|基础信息|Personality Lock)",
            re.MULTILINE
        ),
        "hook": re.compile(r"\| (H\d{3,}) \|"),
        "chapter": re.compile(r"\| (\d+) \|"),
    }

    if file_type == "roles":
        name_match = re.search(r"-\s*姓名[：:]\s*(.+)", text)
        if name_match:
            entities.append({
                "entity": name_match.group(1).strip(),
                "type": "character",
                "source": source,
            })

    elif file_type == "hooks":
        for match in entity_patterns["hook"].finditer(text):
            entities.append({
                "entity": match.group(1),
                "type": "hook",
                "source": source,
            })

    elif file_type == "chapters":
        for match in entity_patterns["chapter"].finditer(text):
            entities.append({
                "entity": f"Chapter {match.group(1)}",
                "type": "chapter",
                "source": source,
            })

    return entities


def scan_project() -> dict:
    index: dict = {
        "version": "0.3.0",
        "entities": [],
        "files": [],
        "domains": {},
    }

    scan_map = {
        "story/roles": "roles",
        "story/outline": "outline",
        "chapters": "chapters",
    }

    for scan_dir, file_type in scan_map.items():
        target = ROOT / scan_dir
        if not target.is_dir():
            continue
        for path in sorted(target.glob("*.md")):
            if path.name.startswith("_template") or path.name.startswith("."):
                continue
            rel = str(path.relative_to(ROOT))
            text = path.read_text(encoding="utf-8")
            entities = extract_entities(text, rel, file_type)
            index["entities"].extend(entities)
            index["files"].append({
                "path": rel,
                "type": file_type,
                "size": len(text),
            })

    hooks_path = ROOT / "story/pending_hooks.md"
    if hooks_path.is_file():
        rel = str(hooks_path.relative_to(ROOT))
        text = hooks_path.read_text(encoding="utf-8")
        index["entities"].extend(extract_entities(text, rel, "hooks"))

    return index


def cmd_build() -> int:
    ensure_index_dir()
    index = scan_project()
    ENTITY_INDEX_PATH.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"Index built: {len(index['entities'])} entities, {len(index['files'])} files")
    print(f"Output: {ENTITY_INDEX_PATH.relative_to(ROOT)}")
    return 0


def query_index(keyword: str = "", domain: str = "", chapter: int = 0) -> list[dict]:
    if not ENTITY_INDEX_PATH.is_file():
        return []
    index = json.loads(ENTITY_INDEX_PATH.read_text(encoding="utf-8"))
    results: list[dict] = []

    for entity in index.get("entities", []):
        name = entity.get("entity", "")
        etype = entity.get("type", "")
        if keyword and keyword not in name:
            continue
        if domain and etype != domain and domain != "all":
            continue
        results.append(entity)

    for f in index.get("files", []):
        if keyword and keyword in f.get("path", ""):
            results.append({"entity": f["path"], "type": "file", "source": f["path"]})

    return results


def build_knowledge_packet(chapter: int, agent: str = "writer") -> str:
    results = query_index(chapter=chapter)
    lines: list[str] = []
    lines.append(f"# Knowledge Packet - Chapter {chapter} ({agent})")
    lines.append("")
    lines.append("## 本章相关实体")
    lines.append("")

    entities = [r for r in results if r.get("type") != "file"]
    if entities:
        for e in entities[:20]:
            lines.append(f"- [{e.get('type', 'unknown')}] {e.get('entity', '?')} ({e.get('source', '?')})")
    else:
        lines.append("- (索引为空，请先运行 knowledge_index.py build)")

    lines.append("")
    lines.append("## 检索规则")
    lines.append("")
    lines.append("- 本索引基于关键词和元数据，未使用向量检索。")
    lines.append("- 如需更精确的语义检索，请在后续版本中配置 embedding 后端。")
    lines.append("- 当前仅返回与检索词精确匹配的实体和文件路径。")

    return "\n".join(lines)


def cmd_query(args: argparse.Namespace) -> int:
    if not ENTITY_INDEX_PATH.is_file():
        print("索引尚未构建。请先运行: python3 scripts/knowledge_index.py build")
        return 1

    if args.chapter:
        packet = build_knowledge_packet(args.chapter, args.agent or "writer")
        prefix = chapter_prefix(args.chapter)
        output = ROOT / "story/runtime" / f"{prefix}.knowledge_packet.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(packet, encoding="utf-8")
        print(f"Knowledge packet written to {output.relative_to(ROOT)}")
        return 0

    results = query_index(
        keyword=args.keyword or "",
        domain=args.domain or "",
    )
    if results:
        for r in results[:30]:
            print(f"[{r.get('type', '?')}] {r.get('entity', '?')} — {r.get('source', '?')}")
        print(f"\n({len(results)} results total)" if len(results) > 30 else "")
    else:
        print("No results found.")
    return 0


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Knowledge Index for Narrative Workbench")
    sub = parser.add_subparsers(dest="command", help="build | query")

    build_parser = sub.add_parser("build", help="扫描项目文件并构建索引")

    query_parser = sub.add_parser("query", help="查询知识库索引")
    add_root_argument(parser)
    query_parser.add_argument("--keyword", type=str, default=None, help="检索关键词")
    query_parser.add_argument("--domain", type=str, default=None, help="领域筛选")
    query_parser.add_argument("--chapter", type=int, default=0, help="生成知识包的目标章节")
    query_parser.add_argument("--agent", type=str, default="writer", help="目标 Agent")
    query_parser.add_argument("--output", type=str, default=None, help="输出路径")

    args = parser.parse_args()
    ROOT = get_root(args)

    if args.command == "build":
        return cmd_build()
    elif args.command == "query":
        return cmd_query(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
