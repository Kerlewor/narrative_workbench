"""Relevance Resolver for Narrative Workbench.

Replaces context_builder.py's core logic with precision context injection
based on chapter plan structured frontmatter and structured ledger queries.

Key improvements over context_builder:
  - Only injects characters in cast_ids (not all characters)
  - Only injects hooks relevant to the current chapter
  - Only injects previous chapter summary (not whole file head)
  - Different budgets and injection profiles per agent type
  - Every injection item lists its reason; omissions list omission reason
  - Budget-aware: proactive trimming with explanations

Usage:
    python scripts/relevance_resolver.py --chapter 19 --agent writer
    python scripts/relevance_resolver.py --chapter 19 --agent review
    python scripts/relevance_resolver.py --chapter 19 --from-plan plan.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from _project import add_root_argument, get_root

ROOT: Path = Path.cwd()

# Token budgets per agent (non-body context)
AGENT_BUDGETS = {
    "writer": 8000,
    "polish": 4000,
    "review": 10000,
    "fixer": 4000,
    "librarian": 20000,
}

# What each agent needs (and what it doesn't)
AGENT_PROFILES = {
    "writer": {
        "include": [
            "chapter_purpose", "scene_beats", "cast_states",
            "hooks_to_advance", "forbidden_reveals",
            "previous_chapter_connection", "style_preferences",
        ],
        "exclude": ["full_hook_library", "full_character_archive", "global_rules"],
    },
    "polish": {
        "include": [
            "current_draft", "style_delta", "language_taboos",
            "immutable_facts", "target_sentences",
        ],
        "exclude": ["full_hook_library", "full_character_cards"],
    },
    "review": {
        "include": [
            "candidate_draft", "task_objectives", "relevant_fact_evidence",
            "hook_handling_requirements", "coherence_boundaries",
            "gatekeeper_output",
        ],
        "exclude": ["irrelevant_character_cards", "other_volume_summaries"],
    },
    "fixer": {
        "include": [
            "final_draft", "review_issues", "allowed_edit_ranges",
            "immutable_fact_boundaries",
        ],
        "exclude": ["entire_project_system"],
    },
    "librarian": {
        "include": [
            "current_state", "current_focus", "chapter_summaries",
            "pending_hooks", "hook_protocol", "volume_map",
            "story_frame", "emotional_arcs",
        ],
        "exclude": ["old_runtime_files"],
    },
}


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def _read_jsonl(ledger: str) -> list[dict]:
    path = ROOT / "story/ledger" / f"{ledger}.jsonl"
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "_schema" in rec:
            continue
        records.append(rec)
    return records


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _extract_yaml_field(text: str, key: str) -> list[str]:
    """Extract a YAML list field from text."""
    import re
    pattern = rf'{key}:\s*\n?((?:\s+-.*\n?)*)'
    match = re.search(pattern, text)
    if not match:
        pattern_inline = rf'{key}:\s*\[(.*?)\]'
        match_inline = re.search(pattern_inline, text)
        if match_inline:
            return [v.strip().strip('"').strip("'") for v in match_inline.group(1).split(",")]
        return []
    items = re.findall(r'\s+-\s+(.+)', match.group(1))
    return [item.strip().strip('"').strip("'") for item in items]


def _find_plan_file(chapter: int) -> Optional[Path]:
    """Find the chapter plan file (YAML or Markdown with frontmatter)."""
    prefix = chapter_prefix(chapter)
    for name in [
        f"{prefix}_director_sheet.yaml",
        f"{prefix}.plan.yaml",
        f"{prefix}.plan.md",
        f"{prefix}.intent.md",
    ]:
        for subdir in ["story/plans", "story/runtime"]:
            path = ROOT / subdir / name
            if path.is_file():
                return path
    return None


def resolve_plan(chapter: int, plan_path: Optional[str] = None) -> dict:
    """Resolve the chapter plan, extracting structured fields.

    Returns a dict with:
        cast_ids, hook_ids, secret_ids, location_ids, knowledge_domains,
        required_previous_chapters, forbidden_reveals, pov, title
    """
    result: dict = {
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

    plan_file = Path(plan_path) if plan_path else _find_plan_file(chapter)
    if not plan_file or not plan_file.is_file():
        print(f"NOTE: No plan file found for chapter {chapter}. Using empty plan (all contexts will be minimal).", file=sys.stderr)
        return result

    text = _read_file(plan_file)

    # Try YAML first
    if plan_file.suffix in (".yaml", ".yml"):
        try:
            import yaml
            data = yaml.safe_load(text) or {}
        except (ImportError, Exception):
            data = {}
        if isinstance(data, dict):
            result["cast_ids"] = _to_list(data.get("cast_ids", data.get("cast", [])))
            result["hook_ids"] = _to_list(data.get("hook_ids", []))
            result["secret_ids"] = _to_list(data.get("secret_ids", []))
            result["location_ids"] = _to_list(data.get("location_ids", []))
            result["knowledge_domains"] = _to_list(data.get("knowledge_domains", []))
            result["required_previous_chapters"] = _to_list(data.get("required_previous_chapters", []))
            result["forbidden_reveals"] = _to_list(data.get("forbidden_reveals", []))
            result["pov"] = data.get("pov", "")
            result["title"] = data.get("title", "")
            return result

    # Markdown — extract YAML frontmatter
    if "---" in text:
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            result["cast_ids"] = _extract_yaml_field(frontmatter, "cast_ids")
            result["hook_ids"] = _extract_yaml_field(frontmatter, "hook_ids")
            result["secret_ids"] = _extract_yaml_field(frontmatter, "secret_ids")
            result["location_ids"] = _extract_yaml_field(frontmatter, "location_ids")
            result["knowledge_domains"] = _extract_yaml_field(frontmatter, "knowledge_domains")
            result["required_previous_chapters"] = [
                int(x) for x in _extract_yaml_field(frontmatter, "required_previous_chapters")
                if x.isdigit()
            ]
            result["forbidden_reveals"] = _extract_yaml_field(frontmatter, "forbidden_reveals")
            # POV from frontmatter
            for line in frontmatter.splitlines():
                if line.strip().startswith("pov:"):
                    result["pov"] = line.split(":", 1)[1].strip().strip('"').strip("'")

    return result


def _to_list(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return []


def inject_cast_states(plan: dict) -> list[dict]:
    """Resolve which character cards to inject."""
    included = []
    omitted = []

    all_chars = _read_jsonl("characters")
    cast_ids = plan.get("cast_ids", [])
    pov = plan.get("pov", "")

    if not cast_ids:
        # No cast specified — include POV and first 3 characters as fallback
        cast_ids = [pov] if pov else []
        for c in all_chars[:3]:
            cid = c.get("id", "")
            if cid and cid not in cast_ids:
                cast_ids.append(cid)

    for char in all_chars:
        cid = char.get("id", "")
        if cid in cast_ids or cid == pov:
            included.append({
                "item": f"character/{cid}",
                "reason": "本章 POV 角色" if cid == pov else "本章 cast",
                "content": json.dumps(char, ensure_ascii=False, indent=2),
            })
        else:
            omitted.append({
                "item": f"character/{cid}",
                "reason": "本章无出场、无关系状态变化",
            })

    # Check for cast_ids not found in ledger and try file-based lookup
    matched_ids = {item["item"].split("/")[-1] for item in included}
    unmatched_ids = [cid for cid in cast_ids if cid not in matched_ids]
    for cid in unmatched_ids:
        card_path = ROOT / "story/roles" / f"{cid}.md"
        if card_path.is_file():
            included.append({
                "item": f"character/{cid}",
                "reason": "本章 cast (from file, not in ledger)",
                "content": card_path.read_text(encoding="utf-8")[:2000],
            })
        else:
            omitted.append({
                "item": f"character/{cid}",
                "reason": "角色卡文件不存在，账本中亦无记录",
            })

    # If no ledger characters found at all, fall back to file-based cards
    if not all_chars:
        roles_dir = ROOT / "story/roles"
        if roles_dir.is_dir():
            for card in sorted(roles_dir.glob("*.md")):
                if card.name.startswith("_template"):
                    continue
                cid = card.stem
                if cid in cast_ids or cid == pov:
                    included.append({
                        "item": f"character/{cid}",
                        "reason": "本章 POV 角色 (from file)" if cid == pov else "本章 cast (from file)",
                        "content": card.read_text(encoding="utf-8")[:2000],
                    })

    return included, omitted


def inject_hooks(plan: dict, chapter: int) -> tuple[list[dict], list[dict]]:
    """Resolve which hooks to inject."""
    included = []
    omitted = []

    hooks = _read_jsonl("hooks")
    hook_ids = plan.get("hook_ids", [])

    if not hooks:
        # Fall back to pending_hooks.md when ledger is empty
        ph = ROOT / "story/pending_hooks.md"
        if ph.is_file():
            hooks_text = ph.read_text(encoding="utf-8")
            omitted.append({"item": "hooks_ledger", "reason": "账本为空，回退至 pending_hooks.md"})
            included.append({
                "item": "pending_hooks",
                "reason": "伏笔池（账本为空时的文件回退）",
                "content": hooks_text[:3000],
            })
        return included, omitted

    for hook in hooks:
        hid = hook.get("id", "")
        status = hook.get("status", "")

        # Always include hooks explicitly named in the plan
        if hid in hook_ids:
            included.append({
                "item": f"hook/{hid}",
                "reason": "当前章节计划要求推进",
                "content": json.dumps(hook, ensure_ascii=False, indent=2),
            })
            continue

        # Include expired hooks (past due_window)
        due = hook.get("due_window", [])
        if isinstance(due, list) and len(due) >= 2:
            if chapter >= due[0] and status not in ("resolved", "dropped", "dormant"):
                included.append({
                    "item": f"hook/{hid}",
                    "reason": f"已到推进窗口 (第{due[0]}-{due[1]}章)",
                    "content": json.dumps(hook, ensure_ascii=False, indent=2),
                })
                continue

        # Omit resolved/dropped hooks
        if status in ("resolved", "dropped", "dormant"):
            omitted.append({"item": f"hook/{hid}", "reason": f"已{status}"})
        else:
            omitted.append({"item": f"hook/{hid}", "reason": "未在当前章计划中"})

    return included, omitted


def inject_secrets(plan: dict) -> tuple[list[dict], list[dict]]:
    """Resolve which secret boundaries to inject."""
    included = []
    omitted = []

    secrets = _read_jsonl("secrets")
    secret_ids = plan.get("secret_ids", [])

    for secret in secrets:
        sid = secret.get("id", "")
        if sid in secret_ids:
            included.append({
                "item": f"secret/{sid}",
                "reason": "本章涉及此秘密边界",
                "content": json.dumps(secret, ensure_ascii=False, indent=2),
            })
        elif secret.get("revealed_in"):
            omitted.append({"item": f"secret/{sid}", "reason": "已揭示"})
        else:
            omitted.append({"item": f"secret/{sid}", "reason": "未在当前章 plan 中"})

    return included, omitted


def inject_previous_chapter_summary(chapter: int, plan: dict) -> dict:
    """Extract the previous chapter's summary."""
    prev = chapter - 1
    if prev < 1:
        return {"item": "previous_chapter_summary", "reason": "第1章无前章", "content": "(第 1 章)"}

    summary_path = ROOT / "story/chapter_summaries.md"
    if not summary_path.is_file():
        return {"item": "previous_chapter_summary", "reason": "", "content": "(无摘要文件)"}

    text = summary_path.read_text(encoding="utf-8")
    import re
    lines = text.splitlines()

    # Search for the chapter marker
    target_prefixes = [
        f"第{prev}章", f"第 {prev} 章",
        f"Chapter {prev}", f"chapter {prev}",
        f"## 第{prev}章", f"## Chapter {prev}",
    ]
    start = None
    for i, line in enumerate(lines):
        for prefix in target_prefixes:
            if line.strip().startswith(prefix):
                start = i
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
    for i in range(start + 1, len(lines)):
        if re.match(r'^#+\s*第?\d+章', lines[i]) or re.match(r'^#+\s*Chapter\s*\d+', lines[i]):
            end = i
            break
    if end is None:
        end = min(start + 60, len(lines))

    return {
        "item": "previous_chapter_summary",
        "reason": "上一章直接连续场景",
        "content": "\n".join(lines[start:end]),
    }


def estimate_tokens(text: str) -> int:
    return len(text) // 2


def build_task_packet(agent: str, chapter: int, plan: dict) -> str:
    """Build a relevance-resolved task packet for the given agent."""
    budget = AGENT_BUDGETS.get(agent, 8000)
    profile = AGENT_PROFILES.get(agent, {"include": [], "exclude": []})

    included_items: list[dict] = []
    omitted_items: list[dict] = []
    total_tokens = 0

    # 1. Chapter purpose (always for writer/review)
    if "chapter_purpose" in profile["include"]:
        title = plan.get("title", f"第{chapter}章")
        included_items.append({
            "item": "chapter_purpose",
            "reason": "本章核心目标",
            "content": f"第{chapter}章: {title}\nPOV: {plan.get('pov', '?')}",
        })

    # 2. Cast states
    if "cast_states" in profile["include"]:
        inc, omt = inject_cast_states(plan)
        included_items.extend(inc)
        omitted_items.extend(omt)

    # 3. Hooks
    if "hooks_to_advance" in profile["include"]:
        inc, omt = inject_hooks(plan, chapter)
        included_items.extend(inc)
        omitted_items.extend(omt)

    # 4. Secrets / forbidden reveals
    if "forbidden_reveals" in profile["include"]:
        inc, omt = inject_secrets(plan)
        included_items.extend(inc)
        omitted_items.extend(omt)
        for fr in plan.get("forbidden_reveals", []):
            included_items.append({
                "item": "forbidden_reveal",
                "reason": "本章禁止揭示",
                "content": f"禁止: {fr}",
            })

    # 5. Previous chapter connection
    if "previous_chapter_connection" in profile["include"]:
        prev = inject_previous_chapter_summary(chapter, plan)
        included_items.append(prev)

    # 6. Style preferences (only for writer)
    if "style_preferences" in profile["include"]:
        sp = ROOT / "story/style_profile.md"
        if sp.is_file():
            content = sp.read_text(encoding="utf-8")[:1500]
            included_items.append({
                "item": "style_profile",
                "reason": "本章风格偏好",
                "content": content,
            })

    # Build the output
    lines: list[str] = []
    lines.append(f"# {agent.upper()} Task Packet — Chapter {chapter}")
    lines.append(f"预算目标: ≤ {budget} tokens (非正文上下文)")
    lines.append("")

    # Included section
    lines.append("## 注入内容 (Included Context)")
    lines.append("")
    for item in included_items:
        content = item.get("content", "")
        displayed = content[:3000] if len(content) > 3000 else content
        t = estimate_tokens(displayed)
        total_tokens += t
        trunc_note = " (已截断)" if len(content) > 3000 else ""
        lines.append(f"### {item['item']}")
        lines.append(f"**原因:** {item['reason']}  |  ~{t} tokens{trunc_note}")
        lines.append("")
        lines.append(displayed)
        lines.append("")

    # Omitted section
    lines.append("## 省略内容 (Omitted Context)")
    lines.append("")
    lines.append("| 条目 | 省略原因 |")
    lines.append("|---|---|")
    for item in omitted_items[:20]:
        lines.append(f"| {item['item']} | {item['reason']} |")
    if len(omitted_items) > 20:
        lines.append(f"| ... 共 {len(omitted_items)} 项省略 | |")
    lines.append("")

    # Budget status
    lines.append("## 预算状态")
    lines.append("")
    lines.append(f"- 预估非正文 tokens: ~{total_tokens}")
    if total_tokens > budget:
        lines.append(f"- ⚠ **超出预算**: 预算 {budget}, 实际 ~{total_tokens}")
        lines.append(f"- 已在编译阶段裁剪。如有必要，手动增加预算或减少注入项。")
    else:
        lines.append(f"- ✓ 预算内: ~{total_tokens} / {budget}")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Relevance Resolver for Narrative Workbench")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument("--agent", type=str, required=True,
                        choices=["writer", "polish", "review", "fixer", "librarian"],
                        help="目标 Agent")
    parser.add_argument("--from-plan", type=str, default=None,
                        help="章节计划文件路径（可选，默认自动查找）")
    parser.add_argument("--output", type=str, default=None,
                        help="输出路径")
    args = parser.parse_args()
    ROOT = get_root(args)

    plan = resolve_plan(args.chapter, args.from_plan)
    packet = build_task_packet(args.agent, args.chapter, plan)

    prefix = chapter_prefix(args.chapter)
    output_path = Path(args.output) if args.output else (
        ROOT / "story/runtime" / f"{prefix}.{args.agent}.resolved.md"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(packet, encoding="utf-8")

    print(f"Resolved task packet → {output_path.relative_to(ROOT)}")
    print(f"Agent: {args.agent}, Chapter: {args.chapter}")
    if plan.get("cast_ids"):
        print(f"Cast: {', '.join(plan['cast_ids'])}")
    if plan.get("hook_ids"):
        print(f"Hooks: {', '.join(plan['hook_ids'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
