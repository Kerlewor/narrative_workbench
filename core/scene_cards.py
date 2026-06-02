"""Scene card helpers for Markdown-native chapter planning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SceneCardResult:
    data: dict[str, Any]
    path: Path


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def scene_dir(root: Path, chapter: int) -> Path:
    return root / "story/plans/scenes" / chapter_prefix(chapter)


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def create_scene_card(
    root: Path,
    chapter: int,
    scene_id: str,
    title: str,
    pov: str = "",
    location: str = "",
    purpose: str = "",
    characters: str | None = None,
    hooks: str | None = None,
    forbidden: str | None = None,
) -> SceneCardResult:
    directory = scene_dir(root, chapter)
    directory.mkdir(parents=True, exist_ok=True)
    safe_id = scene_id.replace("/", "-").replace(" ", "_")
    path = directory / f"{safe_id}.md"
    data = {
        "schema": "narrative_workbench.scene_card.v1",
        "chapter": chapter,
        "scene_id": scene_id,
        "title": title,
        "pov": pov,
        "location": location,
        "purpose": purpose,
        "characters": _split_csv(characters),
        "hooks": _split_csv(hooks),
        "forbidden_reveals": _split_csv(forbidden),
        "path": str(path),
    }
    lines = [
        "---",
        f"chapter: {chapter}",
        f"scene_id: {scene_id}",
        f"title: \"{title}\"",
        f"pov: \"{pov}\"",
        f"location: \"{location}\"",
        "characters:",
    ]
    lines.extend(f"  - {item}" for item in data["characters"])
    lines.append("hooks:")
    lines.extend(f"  - {item}" for item in data["hooks"])
    lines.append("forbidden_reveals:")
    lines.extend(f"  - {item}" for item in data["forbidden_reveals"])
    lines.extend(
        [
            "---",
            "",
            f"# {title}",
            "",
            "## 场景目的",
            purpose or "-",
            "",
            "## 输入状态",
            "- 人物情绪：",
            "- 物理位置：",
            "- 已知信息：",
            "",
            "## 输出状态",
            "- 人物情绪变化：",
            "- 关系变化：",
            "- 伏笔推进：",
            "- 下一场必须继承：",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return SceneCardResult(data=data, path=path)


def list_scene_cards(root: Path, chapter: int) -> dict[str, Any]:
    directory = scene_dir(root, chapter)
    cards = []
    for path in sorted(directory.glob("*.md")) if directory.is_dir() else []:
        cards.append({"id": path.stem, "path": str(path), "title": _title_from_card(path)})
    return {
        "schema": "narrative_workbench.scene_card_list.v1",
        "chapter": chapter,
        "cards": cards,
    }


def _title_from_card(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("title:"):
            return line.split(":", 1)[1].strip().strip('"')
    return path.stem


def render_scene_list(data: dict[str, Any]) -> str:
    lines = [
        f"# 第{data['chapter']}章场景卡",
        "",
        "| 场景 ID | 标题 | 文件 |",
        "|---|---|---|",
    ]
    for card in data.get("cards", []):
        lines.append(f"| {card['id']} | {card['title']} | `{card['path']}` |")
    if not data.get("cards"):
        lines.append("| - | 暂无场景卡 | - |")
    lines.append("")
    return "\n".join(lines)


def scene_list_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
