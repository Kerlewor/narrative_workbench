#!/usr/bin/env python3
"""Context Builder for Narrative Workbench.

Builds per-agent context packets that include only what each agent needs.
Reduces context bloat by omitting files irrelevant to the agent's task.

Usage:
    python scripts/context_builder.py --chapter 12 --agent writer
    python scripts/context_builder.py --chapter 12 --agent review
    python scripts/context_builder.py --chapter 12 --agent polish

Output:
    story/runtime/chapter-0012.<agent>.context.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from _project import add_root_argument, get_root

ROOT: Path = Path.cwd()  # Set in main() via --project-root or CWD

AGENT_BUDGETS = {
    "writer": 18000,
    "polish": 12000,
    "review": 15000,
    "fixer": 8000,
    "librarian": 20000,
}

MUST_INCLUDE = {
    "writer": [
        "intent",
        "plan",
        "previous_chapter_summary",
        "active_character_cards",
        "active_hooks",
    ],
    "polish": [
        "writer_draft",
        "style_profile",
        "style_blacklist",
        "active_character_cards",
    ],
    "review": [
        "polish_draft",
        "intent",
        "plan",
        "previous_chapter_summary",
        "active_character_cards",
        "pending_hooks",
        "emotional_arcs",
    ],
    "fixer": [
        "polish_draft",
        "review_report",
        "active_character_cards",
    ],
    "librarian": [
        "current_state",
        "current_focus",
        "chapter_summaries",
        "pending_hooks",
        "hook_protocol",
        "volume_map",
        "story_frame",
        "emotional_arcs",
    ],
}

COMPRESSED = {
    "writer": ["volume_map", "emotional_arcs", "current_state", "book_rules"],
    "polish": ["intent", "plan"],
    "review": ["volume_map", "current_state", "style_guide"],
    "fixer": ["intent", "plan"],
    "librarian": ["style_guide", "style_blacklist", "book_rules"],
}

EXCLUDE = {
    "writer": ["review_history", "full_worldbuilding_files", "old_runtime_files"],
    "polish": ["full_worldbuilding", "hook_protocol", "review_history"],
    "review": ["full_worldbuilding_files", "old_runtime_files"],
    "fixer": ["full_worldbuilding", "old_runtime_files", "style_samples"],
    "librarian": ["old_runtime_files"],
}

FORBIDDEN_LEAK_HEADER = "## 禁止泄露信息"
LEAK_HARD_CONSTRAINT = "以下信息在本章写作中不得直接或间接泄露给读者"


def chapter_prefix(chapter: int) -> str:
    return f"chapter-{chapter:04d}"


def find_runtime_file(pattern: str, chapter: int) -> Optional[Path]:
    prefix = chapter_prefix(chapter)
    candidate = ROOT / "story/runtime" / f"{prefix}.{pattern}.md"
    if candidate.is_file():
        return candidate
    # Broader glob for files like "chapter-0001.scene-1.md"
    glob_pattern = f"{prefix}.{pattern}*.md"
    matches = sorted(
        p for p in (ROOT / "story/runtime").glob(glob_pattern)
        if not p.name.endswith((".context.md", ".prompt.md", ".gatekeeper.md"))
    )
    if matches:
        return matches[0]
    return None


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def read_summary(path: Path, max_lines: int = 40) -> str:
    if not path.is_file():
        return "(文件不存在)"
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[:max_lines]) + f"\n\n... (共 {len(lines)} 行，已截断)"


def _extract_yaml_list(text: str, key: str) -> list[str]:
    """Extract a YAML list from frontmatter or inline YAML block."""
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


def _get_chapter_cast_ids(chapter: int) -> list[str]:
    """Extract cast_ids from chapter plan frontmatter, if available."""
    prefix = chapter_prefix(chapter)
    # Check runtime markdown plans first
    for suffix in ["plan", "intent"]:
        path = ROOT / "story/runtime" / f"{prefix}.{suffix}.md"
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            cast = _extract_yaml_list(text, "cast_ids")
            if cast:
                return cast
    # Check YAML director sheets
    for ext in ["yaml", "yml"]:
        path = ROOT / "story/plans" / f"{prefix}_director_sheet.{ext}"
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            cast = _extract_yaml_list(text, "cast_ids")
            if cast:
                return cast
    return []


def _extract_chapter_summary(summary_text: str, chapter_num: int) -> str:
    """Extract a specific chapter's summary from chapter_summaries.md."""
    import re
    lines = summary_text.splitlines()
    target_prefixes = [
        f"第{chapter_num}章", f"第 {chapter_num} 章",
        f"第{chapter_num:02d}章", f"第 {chapter_num:02d} 章",
        f"Chapter {chapter_num}", f"chapter {chapter_num}",
        f"Chapter {chapter_num:02d}", f"chapter {chapter_num:02d}",
        f"## 第{chapter_num}章", f"## Chapter {chapter_num}",
        f"## 第{chapter_num:02d}章",
        f"### 第{chapter_num}章", f"### Chapter {chapter_num}",
    ]
    start_idx = None
    for i, line in enumerate(lines):
        for prefix in target_prefixes:
            if line.strip().startswith(prefix) or prefix in line:
                start_idx = i
                break
        if start_idx is not None:
            break

    if start_idx is None:
        # Try table row format: | N | Title | Cast | Events | ...
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("|") and not line.startswith("|---"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                if cells and cells[0].isdigit() and int(cells[0]) == chapter_num:
                    return line
        # Last resort: return last 40 lines
        return f"(未找到第{chapter_num}章摘要标记，返回文件尾部)\n\n" + "\n".join(lines[-40:])

    end_idx = None
    for i in range(start_idx + 1, len(lines)):
        line = lines[i].strip()
        # Heading-based boundary: ## 第N章, ### Chapter N, etc.
        if re.match(r'^#+\s*第?\d+章', line) or re.match(r'^#+\s*Chapter\s*\d+', line):
            end_idx = i
            break
        # Table row boundary: | N | Title | ... where N is a new chapter number
        if line.startswith("|") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0].isdigit():
                end_idx = i
                break

    if end_idx is None:
        end_idx = min(start_idx + 60, len(lines))

    return "\n".join(lines[start_idx:end_idx])


def _filter_hooks_by_relevance(hooks_text: str, chapter: int, cast_ids: list[str]) -> str:
    """Filter hooks relevant to the current chapter. Falls back to full text if unparseable."""
    import re

    lines = hooks_text.splitlines()
    relevant: list[str] = []
    header_lines: list[str] = []
    # Build word-boundary patterns for cast_ids
    cast_patterns = [re.compile(r'\b' + re.escape(cid) + r'\b', re.IGNORECASE) for cid in cast_ids if cid]
    ch_str = str(chapter)
    prev_ch_str = str(chapter - 1)

    for line in lines:
        if line.startswith("|") and "HOOK" in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            is_match = False
            for cell in cells:
                for pat in cast_patterns:
                    if pat.search(cell):
                        is_match = True
                        break
                if not is_match and (re.search(r'\b' + re.escape(ch_str) + r'\b', cell) or re.search(r'\b' + re.escape(prev_ch_str) + r'\b', cell)):
                    is_match = True
                if is_match:
                    break
            if is_match or not relevant:
                relevant.append(line)
        elif line.startswith("#") or line.startswith("|"):
            header_lines.append(line)
        elif relevant:
            relevant.append(line)

    if len(relevant) <= 5:
        return "\n".join(lines[:80])

    return "\n".join(header_lines + relevant)


def collect_must_include(agent: str, chapter: int) -> dict[str, str]:
    result: dict[str, str] = {}
    prefix = chapter_prefix(chapter)
    prev_prefix = chapter_prefix(chapter - 1) if chapter > 1 else None

    # Resolve cast_ids once for character + hook filtering
    cast_ids = _get_chapter_cast_ids(chapter)

    for item in MUST_INCLUDE.get(agent, []):
        if item == "intent":
            path = find_runtime_file("intent", chapter)
            result["intent"] = read_file(path) if path else "(intent 文件不存在)"
        elif item == "plan":
            path = find_runtime_file("plan", chapter)
            result["plan"] = read_file(path) if path else "(plan 文件不存在)"
        elif item == "previous_chapter_summary":
            if prev_prefix:
                summary_path = ROOT / "story/chapter_summaries.md"
                full_text = summary_path.read_text(encoding="utf-8") if summary_path.is_file() else ""
                result["previous_chapter_summary"] = _extract_chapter_summary(full_text, chapter - 1) if full_text else "(摘要文件不存在)"
            else:
                result["previous_chapter_summary"] = "(第1章无前章摘要)"
        elif item == "active_character_cards":
            roles_dir = ROOT / "story/roles"
            cards = []
            if cast_ids:
                for cid in cast_ids:
                    card_path = roles_dir / f"{cid}.md"
                    if card_path.is_file():
                        cards.append(f"--- {card_path.stem} (cast) ---\n{read_summary(card_path, 60)}")
                    else:
                        cards.append(f"--- {cid} ---\n(角色卡文件不存在: {cid}.md)")
            else:
                # Fallback: include all but mark as unfiltered
                for card in sorted(roles_dir.glob("*.md")):
                    if card.name.startswith("_template"):
                        continue
                    cards.append(f"--- {card.stem} (unfiltered) ---\n{read_summary(card, 60)}")
            result["active_character_cards"] = "\n\n".join(cards) if cards else "(无角色卡)"
        elif item == "active_hooks":
            hooks_path = ROOT / "story/pending_hooks.md"
            if hooks_path.is_file():
                hooks_text = hooks_path.read_text(encoding="utf-8")
                result["active_hooks"] = _filter_hooks_by_relevance(hooks_text, chapter, cast_ids)
            else:
                result["active_hooks"] = "(伏笔文件不存在)"
        elif item == "writer_draft":
            path = find_runtime_file("writer", chapter)
            if path and path.is_file():
                result["writer_draft"] = read_summary(path, 300)
            else:
                result["writer_draft"] = "(Writer 草稿不存在)"
        elif item == "polish_draft":
            path = find_runtime_file("polish", chapter)
            if path and path.is_file():
                result["polish_draft"] = read_summary(path, 300)
            else:
                result["polish_draft"] = "(Polish 润色稿不存在)"
        elif item == "review_report":
            path = find_runtime_file("review", chapter)
            if path and path.is_file():
                result["review_report"] = read_file(path)
            else:
                result["review_report"] = "(Review 报告不存在)"
        elif item == "style_profile":
            sp = ROOT / "story/style_profile.md"
            result["style_profile"] = read_summary(sp, 40) if sp.is_file() else "(未设置)"
        elif item == "style_blacklist":
            sb = ROOT / "story/style_blacklist.md"
            result["style_blacklist"] = read_summary(sb, 60) if sb.is_file() else "(未设置)"
        elif item == "pending_hooks":
            ph = ROOT / "story/pending_hooks.md"
            if ph.is_file():
                hooks_text = ph.read_text(encoding="utf-8")
                result["pending_hooks"] = _filter_hooks_by_relevance(hooks_text, chapter, cast_ids)
            else:
                result["pending_hooks"] = "(无伏笔)"
        elif item == "emotional_arcs":
            ea = ROOT / "story/emotional_arcs.md"
            result["emotional_arcs"] = read_summary(ea, 60) if ea.is_file() else "(无弧光记录)"
        elif item == "current_state":
            cs = ROOT / "story/current_state.md"
            result["current_state"] = read_summary(cs, 40)
        elif item == "current_focus":
            cf = ROOT / "story/current_focus.md"
            result["current_focus"] = read_summary(cf, 30)
        elif item == "chapter_summaries":
            sm = ROOT / "story/chapter_summaries.md"
            result["chapter_summaries"] = read_summary(sm, 60)
        elif item == "hook_protocol":
            hp = ROOT / "story/hook_protocol.md"
            result["hook_protocol"] = read_summary(hp, 40)
        elif item == "volume_map":
            vm = ROOT / "story/outline/volume_map.md"
            result["volume_map"] = read_summary(vm, 50)
        elif item == "story_frame":
            sf = ROOT / "story/outline/story_frame.md"
            result["story_frame"] = read_summary(sf, 50)
        elif item == "book_rules":
            br = ROOT / "story/book_rules.md"
            result["book_rules"] = read_summary(br, 30)
        elif item == "style_guide":
            sg = ROOT / "story/style_guide.md"
            result["style_guide"] = read_summary(sg, 40)

    return result


def collect_compressed(agent: str, chapter: int, must_include: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in COMPRESSED.get(agent, []):
        if item in must_include:
            continue
        path_map = {
            "volume_map": ROOT / "story/outline/volume_map.md",
            "emotional_arcs": ROOT / "story/emotional_arcs.md",
            "current_state": ROOT / "story/current_state.md",
            "book_rules": ROOT / "story/book_rules.md",
            "intent": find_runtime_file("intent", chapter),
            "plan": find_runtime_file("plan", chapter),
            "style_guide": ROOT / "story/style_guide.md",
        }
        path = path_map.get(item)
        if path and path.is_file():
            result[item] = read_summary(path, 20)
        elif path:
            result[item] = f"(文件不存在: {path})"
    return result


def collect_omitted(agent: str, chapter: int) -> list[str]:
    all_files = []
    for p in (ROOT / "story/outline").glob("*.md"):
        all_files.append(str(p.relative_to(ROOT)))
    for p in (ROOT / "story").glob("*.md"):
        all_files.append(str(p.relative_to(ROOT)))
    for p in (ROOT / "story/runtime").glob("*.md"):
        if p.name.startswith("_template") or p.name.startswith("batch-"):
            continue
        all_files.append(str(p.relative_to(ROOT)))
    for p in sorted((ROOT / "story/roles").glob("*.md")):
        if not p.name.startswith("_template"):
            all_files.append(str(p.relative_to(ROOT)))
    for p in sorted((ROOT / "chapters").glob("*.md")):
        all_files.append(str(p.relative_to(ROOT)))

    included = set()
    must = collect_must_include(agent, chapter)
    comp = collect_compressed(agent, chapter, must)
    included.update(must.keys())
    included.update(comp.keys())

    exclude_patterns = EXCLUDE.get(agent, [])
    omitted = []
    for f in sorted(set(all_files)):
        name = Path(f).stem
        skip = False
        for pat in exclude_patterns:
            if pat in f or pat in name:
                skip = True
                break
        if skip:
            continue
        if name not in included and f not in included:
            omitted.append(f)

    return omitted[:15]


def estimate_tokens(text: str) -> int:
    return len(text) // 2


def build_context(agent: str, chapter: int) -> str:
    budget = AGENT_BUDGETS.get(agent, 15000)
    must = collect_must_include(agent, chapter)
    compressed = collect_compressed(agent, chapter, must)
    omitted = collect_omitted(agent, chapter)

    lines: list[str] = []
    lines.append(f"# {agent.upper()} Context - Chapter {chapter}")
    lines.append("")
    lines.append(f"上下文预算: ~{budget} tokens")
    lines.append("")

    lines.append("## 1. 必读内容")
    lines.append("")
    total_tokens = 0
    for key, content in must.items():
        tokens = estimate_tokens(content)
        total_tokens += tokens
        label = {"intent": "本章 Intent", "plan": "本章 Plan",
                 "previous_chapter_summary": "前章摘要",
                 "active_character_cards": "相关角色卡",
                 "active_hooks": "活跃伏笔", "writer_draft": "Writer 草稿",
                 "polish_draft": "Polish 润色稿", "review_report": "Review 报告",
                 "style_profile": "文风画像", "style_blacklist": "文笔负面清单",
                 "pending_hooks": "伏笔池", "emotional_arcs": "角色弧光",
                 "current_state": "当前状态", "current_focus": "当前聚焦",
                 "chapter_summaries": "章节摘要", "hook_protocol": "伏笔协议",
                 "volume_map": "分卷地图", "story_frame": "故事框架",
                 "book_rules": "本书规则", "style_guide": "写作规则"}.get(key, key)
        lines.append(f"### {label} (~{tokens} tokens)")
        lines.append("")
        lines.append(content)
        lines.append("")

    lines.append("## 2. 压缩摘要")
    lines.append("")
    for key, content in compressed.items():
        tokens = estimate_tokens(content)
        total_tokens += tokens
        label = {"volume_map": "分卷地图", "emotional_arcs": "角色弧光",
                 "current_state": "当前状态", "book_rules": "本书规则",
                 "intent": "本章 Intent", "plan": "本章 Plan",
                 "style_guide": "写作规则"}.get(key, key)
        lines.append(f"### {label} (~{tokens} tokens)")
        lines.append("")
        lines.append(content)
        lines.append("")

    lines.append("## 3. 禁止泄露")
    lines.append("")
    lines.append("以下信息在本章写作中不得直接或间接泄露给读者：")
    lines.append("")
    lines.append("- 检查 intent/plan 中标注为\"暂不掀\"的内容；")
    lines.append("- 检查 pending_hooks 中状态为 open/progressing 且未到回收时机的伏笔；")
    lines.append("- 检查知识库中标注为 locked 的事实（如已配置知识库）。")
    lines.append("")
    lines.append("如果主会话已提供 Writing Brief，以 Brief 中的禁止事项为准。")

    lines.append("")
    lines.append("## 4. 输出契约")
    lines.append("")
    output_map = {
        "writer": f"story/runtime/{chapter_prefix(chapter)}.writer.md",
        "polish": f"story/runtime/{chapter_prefix(chapter)}.polish.md",
        "review": f"story/runtime/{chapter_prefix(chapter)}.review.md",
        "fixer": f"story/runtime/{chapter_prefix(chapter)}.fixer.md",
        "librarian": f"story/runtime/session-YYYYMMDD-context.md",
    }
    lines.append(f"- 输出文件: `{output_map.get(agent, 'story/runtime/')}`")
    lines.append(f"- 本 Agent 不应修改 canonical 文件。")
    lines.append(f"- 输出的 handoff 摘要应包含偏离记录和未处理问题。")

    lines.append("")
    lines.append("## 5. 省略的文件")
    lines.append("")
    lines.append("以下文件未进入本次上下文包，如有必要可由主会话手动读取：")
    lines.append("")
    if omitted:
        for f in omitted:
            lines.append(f"- {f}")
    else:
        lines.append("- (无)")

    lines.append("")
    estimated_total = total_tokens
    lines.append(f"## 6. 预算摘要")
    lines.append("")
    lines.append(f"- 预估 tokens: ~{estimated_total}")
    if estimated_total > budget:
        lines.append(f"- **超出预算**: 预算 {budget}, 实际 ~{estimated_total}")
        lines.append(f"- 建议: 减少必读内容或进一步提高压缩率。")
    else:
        lines.append(f"- 预算: {budget}, 预估 ~{estimated_total} (在预算内)")

    return "\n".join(lines)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Context Builder for Narrative Workbench")
    add_root_argument(parser)
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument("--agent", type=str, required=True,
                        choices=["writer", "polish", "review", "fixer", "librarian"],
                        help="目标 Agent")
    parser.add_argument("--output", type=str, default=None,
                        help="输出路径（默认 story/runtime/chapter-XXXX.<agent>.context.md）")
    args = parser.parse_args()
    ROOT = get_root(args)

    context = build_context(args.agent, args.chapter)

    if args.output:
        output_path = Path(args.output)
    else:
        prefix = chapter_prefix(args.chapter)
        output_path = ROOT / "story/runtime" / f"{prefix}.{args.agent}.context.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(context, encoding="utf-8")

    print(f"Context packet written to {output_path.relative_to(ROOT)}")
    print(f"Agent: {args.agent}, Chapter: {args.chapter}")

    budget = AGENT_BUDGETS.get(args.agent, 15000)
    estimated = estimate_tokens(context)
    if estimated > budget:
        print(f"WARNING: estimated {estimated} tokens exceeds budget of {budget}")
        return 1
    print(f"Estimated tokens: ~{estimated} (budget: {budget})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
