"""Director Sheet Generator for Narrative Workbench.

Generates a chapter director sheet from a chapter plan/intent and existing
story state. The director sheet is a YAML file that serves as the blueprint
for the entire chapter, defining emotional arcs, information release plans,
style arcs, and scene chain.

Usage:
    python scripts/director_sheet.py --chapter 19            # Generate from plan
    python scripts/director_sheet.py --chapter 19 --from-template  # Generate from template
    python scripts/director_sheet.py --validate --chapter 19  # Validate existing sheet
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from _project import add_root_argument, get_root

ROOT: Path = Path.cwd()


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def _read_yaml(path: Path) -> dict | None:
    try:
        import yaml
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return None
    except Exception:
        return None


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def generate_from_template(chapter: int, chapter_title: str) -> str:
    """Generate a director sheet from the template, ready for author editing."""
    template_path = ROOT / "story/plans/_template.director_sheet.yaml"
    if not template_path.is_file():
        print(f"Template not found: {template_path}", file=sys.stderr)
        return ""

    template = template_path.read_text(encoding="utf-8")
    template = template.replace("chapter: 0", f"chapter: {chapter}")
    template = template.replace('title: "章节标题"', f'title: "{chapter_title}"')

    return template


def generate_from_plan(chapter: int) -> str:
    """Generate a director sheet by reading intent/plan and extracting structured info.

    This is a best-effort extraction. Full director sheet creation requires AI
    input for emotional arcs and style arcs. This function extracts what's
    deterministically available.
    """
    prefix = chapter_prefix(chapter)

    intent_text = _read_file(ROOT / "story/runtime" / f"{prefix}.intent.md")
    plan_text = _read_file(ROOT / "story/runtime" / f"{prefix}.plan.md")

    if not intent_text and not plan_text:
        print(f"No intent or plan found for chapter {chapter}. Run --from-template instead.", file=sys.stderr)
        return ""

    # Try to extract title from intent or plan
    title = f"第{chapter}章"
    for text in [intent_text, plan_text]:
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("title:") or line.startswith("标题:") or line.startswith("chapter:") or line.startswith("章节:"):
                val = line.split(":", 1)[1].strip().strip('"').strip("'")
                if val and not val.isdigit():
                    title = val
                    break

    # Build basic skeleton from template
    body = generate_from_template(chapter, title)

    # Append extracted context hints from plan/intent
    hints = []
    combined = intent_text + "\n" + plan_text

    for marker, label in [
        ("POV", "pov"), ("cast", "cast"), ("hook", "hook"),
        ("伏笔", "hook"), ("角色", "cast"), ("场景", "scene"),
        ("禁止", "forbidden"), ("不得", "forbidden"),
    ]:
        for line in combined.splitlines():
            if marker.lower() in line.lower():
                hints.append(f"  # Plan reference: {line.strip()[:120]}")
                break

    if hints:
        body += "\n# === Extracted from plan/intent ===\n"
        body += "\n".join(hints[:10])
        body += "\n"

    return body


def validate_sheet(chapter: int) -> int:
    """Validate an existing director sheet for completeness."""
    prefix = chapter_prefix(chapter)
    sheet_path = ROOT / "story/plans" / f"{prefix}_director_sheet.yaml"

    if not sheet_path.is_file():
        print(f"Director sheet not found: {sheet_path}")
        print(f"Generate one with: python scripts/director_sheet.py --chapter {chapter} --from-template")
        return 1

    data = _read_yaml(sheet_path)
    if data is None:
        print("Cannot validate: pyyaml not installed. Install with: pip install pyyaml")
        print("Manual checks:")
        text = sheet_path.read_text(encoding="utf-8")
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
        all_ok = True
        for field, label in checks:
            if field in text:
                print(f"  ✓ {label}")
            else:
                print(f"  ✗ {label} — MISSING")
                all_ok = False
        return 0 if all_ok else 1

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

    errors = 0
    for field, label in checks:
        if field not in data or not data[field]:
            print(f"  ✗ {label} ({field}) — MISSING")
            errors += 1
        else:
            print(f"  ✓ {label}")

    if "scene_chain" in data and isinstance(data["scene_chain"], list):
        print(f"    Scenes: {len(data['scene_chain'])}")
        for scene in data["scene_chain"]:
            sid = scene.get("id", "?")
            role = scene.get("role", "?")
            has_input = "input_state" in scene
            has_output = "output_state" in scene
            if not has_input or not has_output:
                print(f"    ✗ {sid}: missing {'input_state' if not has_input else 'output_state'}")
                errors += 1

    if errors:
        print(f"\n{errors} issue(s) found")
        return 1
    print("\nDirector sheet valid")
    return 0


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Director Sheet Generator")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument("--from-template", action="store_true",
                        help="从模板生成（推荐，适合首次创建）")
    parser.add_argument("--from-plan", action="store_true",
                        help="从 intent/plan 生成（提取已有规划）")
    parser.add_argument("--validate", action="store_true",
                        help="验证已有导演表")
    parser.add_argument("--title", type=str, default="",
                        help="章节标题")
    args = parser.parse_args()
    ROOT = get_root(args)

    prefix = chapter_prefix(args.chapter)

    if args.validate:
        return validate_sheet(args.chapter)

    if args.from_template:
        title = args.title or f"第{args.chapter}章"
        content = generate_from_template(args.chapter, title)
    elif args.from_plan:
        content = generate_from_plan(args.chapter)
    else:
        # Default: try from-plan first, fallback to template
        content = generate_from_plan(args.chapter)
        if not content:
            title = args.title or f"第{args.chapter}章"
            content = generate_from_template(args.chapter, title)

    if not content:
        return 1

    output_path = ROOT / "story/plans" / f"{prefix}_director_sheet.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.is_file():
        print(f"WARNING: {output_path.relative_to(ROOT)} already exists.")
        print(f"Use --validate to check it, or delete it and re-run to regenerate.")
        return 1

    output_path.write_text(content, encoding="utf-8")
    print(f"Director sheet written to {output_path.relative_to(ROOT)}")
    print(f"Next: edit the sheet, then run with --validate to check completeness")
    return 0


if __name__ == "__main__":
    sys.exit(main())
