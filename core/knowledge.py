"""Lightweight keyword knowledge index."""

from __future__ import annotations

import json
import re
from pathlib import Path

from core.context import chapter_prefix, read_file


def index_dir(root: Path) -> Path:
    return root / ".nw_index"


def entity_index_path(root: Path) -> Path:
    return index_dir(root) / "entity_index.json"


def ensure_index_dir(root: Path) -> None:
    index_dir(root).mkdir(parents=True, exist_ok=True)


def extract_entities(text: str, source: str, file_type: str) -> list[dict]:
    entities: list[dict] = []
    entity_patterns = {
        "hook": re.compile(r"\| (H\d{3,}) \|"),
        "chapter": re.compile(r"\| (\d+) \|"),
    }

    if file_type == "roles":
        name_match = re.search(r"-\s*姓名[：:]\s*(.+)", text)
        if name_match:
            entities.append({"entity": name_match.group(1).strip(), "type": "character", "source": source})
    elif file_type == "hooks":
        for match in entity_patterns["hook"].finditer(text):
            entities.append({"entity": match.group(1), "type": "hook", "source": source})
    elif file_type == "chapters":
        for match in entity_patterns["chapter"].finditer(text):
            entities.append({"entity": f"Chapter {match.group(1)}", "type": "chapter", "source": source})
    return entities


def scan_project(root: Path) -> dict:
    index: dict = {"version": "0.4.0", "entities": [], "files": [], "domains": {}}
    scan_map = {
        "story/roles": "roles",
        "story/outline": "outline",
        "chapters": "chapters",
    }

    for scan_dir, file_type in scan_map.items():
        target = root / scan_dir
        if not target.is_dir():
            continue
        for path in sorted(target.glob("*.md")):
            if path.name.startswith("_template") or path.name.startswith("."):
                continue
            rel = str(path.relative_to(root))
            text = read_file(path)
            index["entities"].extend(extract_entities(text, rel, file_type))
            index["files"].append({"path": rel, "type": file_type, "size": len(text)})

    hooks_path = root / "story/pending_hooks.md"
    if hooks_path.is_file():
        rel = str(hooks_path.relative_to(root))
        index["entities"].extend(extract_entities(read_file(hooks_path), rel, "hooks"))
    return index


def write_index(root: Path, index: dict) -> Path:
    ensure_index_dir(root)
    path = entity_index_path(root)
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_index(root: Path) -> tuple[dict, Path]:
    index = scan_project(root)
    path = write_index(root, index)
    return index, path


def load_index(root: Path) -> dict | None:
    path = entity_index_path(root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def query_index(root: Path, keyword: str = "", domain: str = "", chapter: int = 0) -> list[dict]:
    index = load_index(root)
    if not index:
        return []

    results: list[dict] = []
    for entity in index.get("entities", []):
        name = entity.get("entity", "")
        entity_type = entity.get("type", "")
        if keyword and keyword not in name:
            continue
        if domain and entity_type != domain and domain != "all":
            continue
        results.append(entity)

    for file_record in index.get("files", []):
        if keyword and keyword in file_record.get("path", ""):
            results.append(
                {
                    "entity": file_record["path"],
                    "type": "file",
                    "source": file_record["path"],
                }
            )
    return results


def build_knowledge_packet(root: Path, chapter: int, agent: str = "writer") -> str:
    results = query_index(root, chapter=chapter)
    lines = [
        f"# Knowledge Packet - Chapter {chapter} ({agent})",
        "",
        "## 本章相关实体",
        "",
    ]

    entities = [result for result in results if result.get("type") != "file"]
    if entities:
        for entity in entities[:20]:
            lines.append(f"- [{entity.get('type', 'unknown')}] {entity.get('entity', '?')} ({entity.get('source', '?')})")
    else:
        lines.append("- (索引为空，请先运行 knowledge_index.py build)")

    lines.extend(
        [
            "",
            "## 检索规则",
            "",
            "- 本索引基于关键词和元数据，未使用向量检索。",
            "- 如需更精确的语义检索，请在后续版本中配置 embedding 后端。",
            "- 当前仅返回与检索词精确匹配的实体和文件路径。",
        ]
    )
    return "\n".join(lines)


def knowledge_packet_path(root: Path, chapter: int) -> Path:
    prefix = chapter_prefix(chapter)
    return root / "story/runtime" / f"{prefix}.knowledge_packet.md"

