"""Relevance-resolved context packet construction."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from core.ledger import read_records


AGENT_BUDGETS = {
    "writer": 8000,
    "polish": 4000,
    "review": 10000,
    "fixer": 4000,
    "librarian": 20000,
}

AGENT_PROFILES = {
    "writer": {
        "include": [
            "chapter_purpose",
            "scene_beats",
            "cast_states",
            "hooks_to_advance",
            "forbidden_reveals",
            "previous_chapter_connection",
            "style_preferences",
        ],
        "exclude": ["full_hook_library", "full_character_archive", "global_rules"],
    },
    "polish": {
        "include": [
            "current_draft",
            "style_delta",
            "language_taboos",
            "immutable_facts",
            "target_sentences",
        ],
        "exclude": ["full_hook_library", "full_character_cards"],
    },
    "review": {
        "include": [
            "candidate_draft",
            "task_objectives",
            "relevant_fact_evidence",
            "hook_handling_requirements",
            "coherence_boundaries",
            "gatekeeper_output",
        ],
        "exclude": ["irrelevant_character_cards", "other_volume_summaries"],
    },
    "fixer": {
        "include": [
            "final_draft",
            "review_issues",
            "allowed_edit_ranges",
            "immutable_fact_boundaries",
        ],
        "exclude": ["entire_project_system"],
    },
    "librarian": {
        "include": [
            "current_state",
            "current_focus",
            "chapter_summaries",
            "pending_hooks",
            "hook_protocol",
            "volume_map",
            "story_frame",
            "emotional_arcs",
        ],
        "exclude": ["old_runtime_files"],
    },
}


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def estimate_tokens(text: str) -> int:
    return len(text) // 2


def to_list(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return []


def extract_yaml_field(text: str, key: str) -> list[str]:
    pattern = rf"{key}:\s*\n?((?:\s+-.*\n?)*)"
    match = re.search(pattern, text)
    if not match:
        pattern_inline = rf"{key}:\s*\[(.*?)\]"
        match_inline = re.search(pattern_inline, text)
        if match_inline:
            return [value.strip().strip('"').strip("'") for value in match_inline.group(1).split(",")]
        return []
    items = re.findall(r"\s+-\s+(.+)", match.group(1))
    return [item.strip().strip('"').strip("'") for item in items]


def find_plan_file(root: Path, chapter: int) -> Optional[Path]:
    prefix = chapter_prefix(chapter)
    for name in [
        f"{prefix}_director_sheet.yaml",
        f"{prefix}.plan.yaml",
        f"{prefix}.plan.md",
        f"{prefix}.intent.md",
    ]:
        for subdir in ["story/plans", "story/runtime"]:
            path = root / subdir / name
            if path.is_file():
                return path
    return None


def empty_plan() -> dict:
    return {
        "cast_ids": [],
        "hook_ids": [],
        "secret_ids": [],
        "location_ids": [],
        "knowledge_domains": [],
        "required_previous_chapters": [],
        "forbidden_reveals": [],
        "pov": "",
        "title": "",
    }


def resolve_plan(root: Path, chapter: int, plan_path: Optional[str] = None) -> dict:
    """Resolve structured chapter plan fields from YAML or Markdown frontmatter."""

    result = empty_plan()
    plan_file = Path(plan_path) if plan_path else find_plan_file(root, chapter)
    if not plan_file or not plan_file.is_file():
        return result

    text = read_file(plan_file)

    if plan_file.suffix in (".yaml", ".yml"):
        try:
            import yaml

            data = yaml.safe_load(text) or {}
        except Exception:
            data = {}
        if isinstance(data, dict):
            result["cast_ids"] = to_list(data.get("cast_ids", data.get("cast", [])))
            result["hook_ids"] = to_list(data.get("hook_ids", []))
            result["secret_ids"] = to_list(data.get("secret_ids", []))
            result["location_ids"] = to_list(data.get("location_ids", []))
            result["knowledge_domains"] = to_list(data.get("knowledge_domains", []))
            result["required_previous_chapters"] = to_list(data.get("required_previous_chapters", []))
            result["forbidden_reveals"] = to_list(data.get("forbidden_reveals", []))
            result["pov"] = data.get("pov", "")
            result["title"] = data.get("title", "")
            return result

    if "---" in text:
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            result["cast_ids"] = extract_yaml_field(frontmatter, "cast_ids")
            result["hook_ids"] = extract_yaml_field(frontmatter, "hook_ids")
            result["secret_ids"] = extract_yaml_field(frontmatter, "secret_ids")
            result["location_ids"] = extract_yaml_field(frontmatter, "location_ids")
            result["knowledge_domains"] = extract_yaml_field(frontmatter, "knowledge_domains")
            result["required_previous_chapters"] = [
                int(value)
                for value in extract_yaml_field(frontmatter, "required_previous_chapters")
                if value.isdigit()
            ]
            result["forbidden_reveals"] = extract_yaml_field(frontmatter, "forbidden_reveals")
            for line in frontmatter.splitlines():
                if line.strip().startswith("pov:"):
                    result["pov"] = line.split(":", 1)[1].strip().strip('"').strip("'")

    return result


def inject_cast_states(root: Path, plan: dict) -> tuple[list[dict], list[dict]]:
    included = []
    omitted = []
    all_chars = read_records(root, "characters")
    cast_ids = plan.get("cast_ids", [])
    pov = plan.get("pov", "")

    if not cast_ids:
        cast_ids = [pov] if pov else []
        for character in all_chars[:3]:
            character_id = character.get("id", "")
            if character_id and character_id not in cast_ids:
                cast_ids.append(character_id)

    for character in all_chars:
        character_id = character.get("id", "")
        if character_id in cast_ids or character_id == pov:
            included.append(
                {
                    "item": f"character/{character_id}",
                    "reason": "本章 POV 角色" if character_id == pov else "本章 cast",
                    "content": json.dumps(character, ensure_ascii=False, indent=2),
                }
            )
        else:
            omitted.append(
                {
                    "item": f"character/{character_id}",
                    "reason": "本章无出场、无关系状态变化",
                }
            )

    matched_ids = {item["item"].split("/")[-1] for item in included}
    unmatched_ids = [character_id for character_id in cast_ids if character_id not in matched_ids]
    for character_id in unmatched_ids:
        card_path = root / "story/roles" / f"{character_id}.md"
        if card_path.is_file():
            included.append(
                {
                    "item": f"character/{character_id}",
                    "reason": "本章 cast (from file, not in ledger)",
                    "content": read_file(card_path)[:2000],
                }
            )
        else:
            omitted.append(
                {
                    "item": f"character/{character_id}",
                    "reason": "角色卡文件不存在，账本中亦无记录",
                }
            )

    if not all_chars:
        roles_dir = root / "story/roles"
        if roles_dir.is_dir():
            for card in sorted(roles_dir.glob("*.md")):
                if card.name.startswith("_template"):
                    continue
                character_id = card.stem
                if character_id in cast_ids or character_id == pov:
                    included.append(
                        {
                            "item": f"character/{character_id}",
                            "reason": "本章 POV 角色 (from file)" if character_id == pov else "本章 cast (from file)",
                            "content": read_file(card)[:2000],
                        }
                    )

    return included, omitted


def inject_hooks(root: Path, plan: dict, chapter: int) -> tuple[list[dict], list[dict]]:
    included = []
    omitted = []
    hooks = read_records(root, "hooks")
    hook_ids = plan.get("hook_ids", [])

    if not hooks:
        pending_hooks = root / "story/pending_hooks.md"
        if pending_hooks.is_file():
            omitted.append({"item": "hooks_ledger", "reason": "账本为空，回退至 pending_hooks.md"})
            included.append(
                {
                    "item": "pending_hooks",
                    "reason": "伏笔池（账本为空时的文件回退）",
                    "content": read_file(pending_hooks)[:3000],
                }
            )
        return included, omitted

    for hook in hooks:
        hook_id = hook.get("id", "")
        status = hook.get("status", "")
        if hook_id in hook_ids:
            included.append(
                {
                    "item": f"hook/{hook_id}",
                    "reason": "当前章节计划要求推进",
                    "content": json.dumps(hook, ensure_ascii=False, indent=2),
                }
            )
            continue

        due = hook.get("due_window", [])
        if isinstance(due, list) and len(due) >= 2:
            if chapter >= due[0] and status not in ("resolved", "dropped", "dormant"):
                included.append(
                    {
                        "item": f"hook/{hook_id}",
                        "reason": f"已到推进窗口 (第{due[0]}-{due[1]}章)",
                        "content": json.dumps(hook, ensure_ascii=False, indent=2),
                    }
                )
                continue

        if status in ("resolved", "dropped", "dormant"):
            omitted.append({"item": f"hook/{hook_id}", "reason": f"已{status}"})
        else:
            omitted.append({"item": f"hook/{hook_id}", "reason": "未在当前章计划中"})

    return included, omitted


def inject_secrets(root: Path, plan: dict) -> tuple[list[dict], list[dict]]:
    included = []
    omitted = []
    secrets = read_records(root, "secrets")
    secret_ids = plan.get("secret_ids", [])

    for secret in secrets:
        secret_id = secret.get("id", "")
        if secret_id in secret_ids:
            included.append(
                {
                    "item": f"secret/{secret_id}",
                    "reason": "本章涉及此秘密边界",
                    "content": json.dumps(secret, ensure_ascii=False, indent=2),
                }
            )
        elif secret.get("revealed_in"):
            omitted.append({"item": f"secret/{secret_id}", "reason": "已揭示"})
        else:
            omitted.append({"item": f"secret/{secret_id}", "reason": "未在当前章 plan 中"})

    return included, omitted


def inject_previous_chapter_summary(root: Path, chapter: int) -> dict:
    previous = chapter - 1
    if previous < 1:
        return {"item": "previous_chapter_summary", "reason": "第1章无前章", "content": "(第 1 章)"}

    summary_path = root / "story/chapter_summaries.md"
    if not summary_path.is_file():
        return {"item": "previous_chapter_summary", "reason": "", "content": "(无摘要文件)"}

    lines = read_file(summary_path).splitlines()
    target_prefixes = [
        f"第{previous}章",
        f"第 {previous} 章",
        f"Chapter {previous}",
        f"chapter {previous}",
        f"## 第{previous}章",
        f"## Chapter {previous}",
    ]
    start = None
    for index, line in enumerate(lines):
        for prefix in target_prefixes:
            if line.strip().startswith(prefix):
                start = index
                break
        if start is not None:
            break

    if start is None:
        return {
            "item": "previous_chapter_summary",
            "reason": "上一章直接连续场景",
            "content": "\n".join(lines[-40:]),
        }

    end = None
    for index in range(start + 1, len(lines)):
        if re.match(r"^#+\s*第?\d+章", lines[index]) or re.match(r"^#+\s*Chapter\s*\d+", lines[index]):
            end = index
            break
    if end is None:
        end = min(start + 60, len(lines))

    return {
        "item": "previous_chapter_summary",
        "reason": "上一章直接连续场景",
        "content": "\n".join(lines[start:end]),
    }


def build_task_packet(root: Path, agent: str, chapter: int, plan: dict) -> str:
    """Build a relevance-resolved task packet for the given agent."""

    budget = AGENT_BUDGETS.get(agent, 8000)
    profile = AGENT_PROFILES.get(agent, {"include": [], "exclude": []})
    included_items: list[dict] = []
    omitted_items: list[dict] = []
    total_tokens = 0

    if "chapter_purpose" in profile["include"]:
        title = plan.get("title", f"第{chapter}章")
        included_items.append(
            {
                "item": "chapter_purpose",
                "reason": "本章核心目标",
                "content": f"第{chapter}章: {title}\nPOV: {plan.get('pov', '?')}",
            }
        )

    if "cast_states" in profile["include"]:
        included, omitted = inject_cast_states(root, plan)
        included_items.extend(included)
        omitted_items.extend(omitted)

    if "hooks_to_advance" in profile["include"]:
        included, omitted = inject_hooks(root, plan, chapter)
        included_items.extend(included)
        omitted_items.extend(omitted)

    if "forbidden_reveals" in profile["include"]:
        included, omitted = inject_secrets(root, plan)
        included_items.extend(included)
        omitted_items.extend(omitted)
        for forbidden in plan.get("forbidden_reveals", []):
            included_items.append(
                {
                    "item": "forbidden_reveal",
                    "reason": "本章禁止揭示",
                    "content": f"禁止: {forbidden}",
                }
            )

    if "previous_chapter_connection" in profile["include"]:
        included_items.append(inject_previous_chapter_summary(root, chapter))

    if "style_preferences" in profile["include"]:
        style_profile = root / "story/style_profile.md"
        if style_profile.is_file():
            included_items.append(
                {
                    "item": "style_profile",
                    "reason": "本章风格偏好",
                    "content": read_file(style_profile)[:1500],
                }
            )

    lines: list[str] = []
    lines.append(f"# {agent.upper()} Task Packet - Chapter {chapter}")
    lines.append(f"预算目标: <= {budget} tokens (非正文上下文)")
    lines.append("")
    lines.append("## 注入内容 (Included Context)")
    lines.append("")

    for item in included_items:
        content = item.get("content", "")
        displayed = content[:3000] if len(content) > 3000 else content
        tokens = estimate_tokens(displayed)
        total_tokens += tokens
        trunc_note = " (已截断)" if len(content) > 3000 else ""
        lines.append(f"### {item['item']}")
        lines.append(f"**原因:** {item['reason']}  |  ~{tokens} tokens{trunc_note}")
        lines.append("")
        lines.append(displayed)
        lines.append("")

    lines.append("## 省略内容 (Omitted Context)")
    lines.append("")
    lines.append("| 条目 | 省略原因 |")
    lines.append("|---|---|")
    for item in omitted_items[:20]:
        lines.append(f"| {item['item']} | {item['reason']} |")
    if len(omitted_items) > 20:
        lines.append(f"| ... 共 {len(omitted_items)} 项省略 | |")
    lines.append("")

    lines.append("## 预算状态")
    lines.append("")
    lines.append(f"- 预估非正文 tokens: ~{total_tokens}")
    if total_tokens > budget:
        lines.append(f"- **超出预算**: 预算 {budget}, 实际 ~{total_tokens}")
        lines.append("- 已在编译阶段裁剪。如有必要，手动增加预算或减少注入项。")
    else:
        lines.append(f"- 预算内: ~{total_tokens} / {budget}")
    lines.append("")

    return "\n".join(lines)

