"""Character voice laboratory prompt generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VoiceLabResult:
    data: dict[str, Any]
    markdown: str
    path: Path


def _find_role_card(root: Path, character: str) -> Path | None:
    roles = root / "story/roles"
    if not roles.is_dir():
        return None
    candidates = [roles / f"{character}.md"]
    candidates.extend(path for path in roles.glob("*.md") if character in path.stem)
    for path in candidates:
        if path.is_file() and not path.name.startswith("_template"):
            return path
    return None


def build_voice_lab(root: Path, character: str, line: str = "") -> VoiceLabResult:
    role_card = _find_role_card(root, character)
    role_excerpt = ""
    if role_card:
        text = role_card.read_text(encoding="utf-8")
        role_excerpt = text[:2400]
    data: dict[str, Any] = {
        "schema": "narrative_workbench.voice_lab.v1",
        "character": character,
        "line": line,
        "role_card": str(role_card) if role_card else "",
        "output_path": str(root / "story/runtime" / f"voice_lab.{character}.md"),
    }
    markdown = render_voice_lab(data, role_excerpt)
    path = Path(data["output_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return VoiceLabResult(data=data, markdown=markdown, path=path)


def render_voice_lab(data: dict[str, Any], role_excerpt: str) -> str:
    line = data.get("line") or "（请在这里填入待测试台词）"
    lines = [
        f"# 角色声音实验室：{data['character']}",
        "",
        "> 本文件是给主会话/Polish/Review 使用的角色声线测试包，不直接写入角色卡。",
        "",
        "## 待测试台词",
        "",
        line,
        "",
        "## 角色卡摘录",
        "",
        role_excerpt or "（未找到角色卡。请先创建或补全 `story/roles/` 中的角色卡。）",
        "",
        "## 实验任务",
        "",
        "1. 写出该角色会说的 3 个版本。",
        "2. 写出该角色不会说的 3 个版本，并说明违反了哪些 Personality Lock 或 Behavioral Constraints。",
        "3. 检查台词是否泄露角色不该知道的信息。",
        "4. 输出只作为候选，作者确认后才可写入角色卡或正文。",
        "",
    ]
    return "\n".join(lines)


def voice_lab_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
