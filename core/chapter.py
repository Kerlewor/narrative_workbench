"""Chapter planning helpers and scene handoff validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.context import chapter_prefix, read_file


@dataclass(frozen=True)
class ChapterValidation:
    errors: int
    lines: list[str]

    @property
    def ok(self) -> bool:
        return self.errors == 0


def read_yaml(path: Path) -> dict | list | None:
    try:
        import yaml

        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except Exception:
        return None


def generate_director_from_template(root: Path, chapter: int, chapter_title: str) -> str:
    template_path = root / "story/plans/_template.director_sheet.yaml"
    if not template_path.is_file():
        return ""

    template = read_file(template_path)
    template = template.replace("chapter: 0", f"chapter: {chapter}")
    template = template.replace('title: "章节标题"', f'title: "{chapter_title}"')
    return template


def generate_director_from_plan(root: Path, chapter: int) -> str:
    """Generate a director sheet skeleton from runtime intent/plan files."""

    prefix = chapter_prefix(chapter)
    intent_text = read_file(root / "story/runtime" / f"{prefix}.intent.md")
    plan_text = read_file(root / "story/runtime" / f"{prefix}.plan.md")
    if not intent_text and not plan_text:
        return ""

    title = f"第{chapter}章"
    for text in [intent_text, plan_text]:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("title:", "标题:", "chapter:", "章节:")):
                value = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                if value and not value.isdigit():
                    title = value
                    break

    body = generate_director_from_template(root, chapter, title)
    combined = intent_text + "\n" + plan_text
    hints: list[str] = []
    for marker in ["POV", "cast", "hook", "伏笔", "角色", "场景", "禁止", "不得"]:
        for line in combined.splitlines():
            if marker.lower() in line.lower():
                hints.append(f"  # Plan reference: {line.strip()[:120]}")
                break

    if hints:
        body += "\n# === Extracted from plan/intent ===\n"
        body += "\n".join(hints[:10])
        body += "\n"
    return body


def validate_director_sheet(root: Path, chapter: int) -> ChapterValidation:
    prefix = chapter_prefix(chapter)
    sheet_path = root / "story/plans" / f"{prefix}_director_sheet.yaml"
    lines: list[str] = []
    errors = 0

    if not sheet_path.is_file():
        lines.append(f"Director sheet not found: {sheet_path}")
        lines.append(f"Generate one with: python scripts/director_sheet.py --chapter {chapter} --from-template")
        return ChapterValidation(errors=1, lines=lines)

    data = read_yaml(sheet_path)
    if data is None:
        text = read_file(sheet_path)
        checks = [
            ("chapter:", "chapter number"),
            ("chapter_purpose:", "chapter purpose"),
            ("opening_state:", "opening state"),
            ("closing_state:", "closing state"),
            ("emotional_arc:", "emotional arc"),
            ("forbidden_reveals:", "forbidden reveals"),
            ("style_arc:", "style arc"),
            ("scene_chain:", "scene chain"),
        ]
        for field, label in checks:
            if field in text:
                lines.append(f"  OK {label}")
            else:
                lines.append(f"  MISSING {label}")
                errors += 1
        return ChapterValidation(errors=errors, lines=lines)

    if not isinstance(data, dict):
        return ChapterValidation(errors=1, lines=["Director sheet must be a YAML mapping"])

    checks = [
        ("chapter", "章节编号"),
        ("chapter_purpose", "章节目的"),
        ("opening_state", "开篇状态"),
        ("closing_state", "结尾状态"),
        ("emotional_arc", "情绪曲线"),
        ("forbidden_reveals", "禁止揭示"),
        ("style_arc", "语言节奏曲线"),
        ("scene_chain", "场景接力链"),
    ]

    for field, label in checks:
        if field not in data or not data[field]:
            lines.append(f"  MISSING {label} ({field})")
            errors += 1
        else:
            lines.append(f"  OK {label}")

    scene_chain = data.get("scene_chain")
    if isinstance(scene_chain, list):
        lines.append(f"    Scenes: {len(scene_chain)}")
        for scene in scene_chain:
            if not isinstance(scene, dict):
                lines.append("    MISSING scene mapping")
                errors += 1
                continue
            scene_id = scene.get("id", "?")
            has_input = bool(scene.get("input_state"))
            has_output = bool(scene.get("output_state"))
            if not has_input:
                lines.append(f"    MISSING {scene_id}: input_state")
                errors += 1
            if not has_output:
                lines.append(f"    MISSING {scene_id}: output_state")
                errors += 1

    return ChapterValidation(errors=errors, lines=lines)


def validate_scene_handoffs(root: Path, chapter: int) -> ChapterValidation:
    prefix = chapter_prefix(chapter)
    handoff_path = root / "story/runtime" / f"{prefix}_scene_handoffs.yaml"
    lines: list[str] = []
    errors = 0

    if not handoff_path.is_file():
        lines.append(f"Scene handoff file not found: {handoff_path}")
        return ChapterValidation(errors=1, lines=lines)

    data = read_yaml(handoff_path)
    if data is None:
        text = read_file(handoff_path)
        checks = [
            ("handoffs:", "handoffs root"),
            ("scene_id:", "scene id"),
            ("handoff_to:", "handoff target"),
            ("physical_state:", "physical state"),
            ("emotional_state:", "emotional state"),
            ("required_next_scene_input:", "required next scene input"),
        ]
        for field, label in checks:
            if field in text:
                lines.append(f"  OK {label}")
            else:
                lines.append(f"  MISSING {label}")
                errors += 1
        return ChapterValidation(errors=errors, lines=lines)

    if not isinstance(data, dict):
        return ChapterValidation(errors=1, lines=["Scene handoff file must be a YAML mapping"])

    handoffs = data.get("handoffs")
    if not isinstance(handoffs, dict) or not handoffs:
        return ChapterValidation(errors=1, lines=["  MISSING handoffs mapping"])

    required_fields = [
        "scene_id",
        "handoff_to",
        "physical_state",
        "emotional_state",
        "revealed_information",
        "unresolved_tension",
        "required_next_scene_input",
        "do_not_resolve_in_this_scene",
    ]

    for key, handoff in handoffs.items():
        if not isinstance(handoff, dict):
            lines.append(f"  MISSING {key}: handoff mapping")
            errors += 1
            continue
        for field in required_fields:
            if field not in handoff:
                lines.append(f"  MISSING {key}: {field}")
                errors += 1
        scene_id = handoff.get("scene_id")
        if scene_id and scene_id != key:
            lines.append(f"  WARNING {key}: scene_id is {scene_id}")

    if errors == 0:
        lines.append(f"Scene handoffs valid: {len(handoffs)} handoff(s)")
    return ChapterValidation(errors=errors, lines=lines)

