"""Skills Sync Script for Narrative Workbench.

Synchronizes skills/ (the single source of truth) to platform-specific
lightweight entry wrappers:
  - .claude/skills/   — Claude Code native skills
  - .agents/skills/   — Codex native skills

Each wrapper is a thin file that tells the platform:
  - When to invoke (trigger phrases)
  - Which scripts to run or files to read
  - Where output should go

The canonical skill implementation lives in skills/<name>/prompt.md.
The wrapper just points to it.

Usage:
    python scripts/sync_skills.py              # Sync all skills
    python scripts/sync_skills.py --dry-run    # Show what would be created
    python scripts/sync_skills.py --clean      # Remove stale wrappers
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _project import add_root_argument, get_root

ROOT: Path = Path.cwd()

SKILLS_SOURCE = "skills"
CLAUDE_SKILLS = ".claude/skills"
CODEX_SKILLS = ".agents/skills"
CODEX_AGENTS = ".codex/agents"

# Skill definitions — maps source dir to platform metadata
SKILL_DEFS = {
    "plan_chapter": {
        "description": "为指定章节生成写作简报与约束包",
        "triggers": ["规划第N章", "第N章写作简报", "第N章 plan", "writing brief 第N章"],
        "scripts": ["scripts/hook_report.py --current N-1", "scripts/hook_matrix.py --current N-1"],
        "prompt": "skills/plan_chapter/prompt.md",
    },
    "write_chapter": {
        "description": "执行单章完整写作流水线 (Writer→Polish→Review→Fixer→Gatekeeper)",
        "triggers": ["写第N章", "继续下一章", "write chapter N"],
        "scripts": ["scripts/relevance_resolver.py --chapter N --agent writer"],
        "prompt": "skills/write_chapter/prompt.md",
    },
    "review_chapter": {
        "description": "审查章节 — AI 写或作者手写",
        "triggers": ["审阅第N章", "审查第N章", "review 第N章"],
        "scripts": ["scripts/relevance_resolver.py --chapter N --agent review"],
        "prompt": "skills/review_chapter/prompt.md",
    },
    "polish_author_draft": {
        "description": "对作者手写章节按模式润色 (5种模式)",
        "triggers": ["润色第N章", "polish 第N章", "润色我的手写稿"],
        "scripts": ["scripts/polish_author_chapter.py --chapter N"],
        "prompt": "skills/polish_author_draft/prompt.md",
    },
    "import_outline": {
        "description": "搭建或导入现成大纲",
        "triggers": ["搭建大纲", "导入大纲", "我有现成大纲", "导入现成大纲"],
        "scripts": ["scripts/structure_report.py", "scripts/doctor.py"],
        "prompt": "skills/import_outline/prompt.md",
    },
    "deepen_character": {
        "description": "对已创建角色进行四轮深度讨论",
        "triggers": ["深化角色", "深化", "角色深度讨论", "补全角色"],
        "scripts": [],
        "prompt": "skills/deepen_character/prompt.md",
    },
}


def _write_claude_skill(skill_dir: Path, name: str, defn: dict) -> None:
    """Write a Claude Code skill wrapper with YAML frontmatter."""
    triggers_yaml = "\n".join(f"  - {t}" for t in defn['triggers'])
    scripts_yaml = "\n".join(f"  - {s}" for s in defn.get("scripts", []))
    content = f"""---
name: {name}
description: {defn['description']}
triggers:
{triggers_yaml}
prompt: {defn['prompt']}
{("scripts:" if scripts_yaml else "")}
{scripts_yaml if scripts_yaml else ""}
---

# {name}

{defn['description']}

Canonical prompt: `{defn['prompt']}`
"""
    if defn.get("scripts"):
        content += "\n## Scripts\n\n"
        for s in defn["scripts"]:
            content += f"- `{s}`\n"

    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / f"{name}.md").write_text(content, encoding="utf-8")


def _write_codex_skill(skill_dir: Path, name: str, defn: dict) -> None:
    """Write a Codex skill wrapper (AGENTS.md-compatible)."""
    content = f"""# {name}

{defn['description']}

## Triggers
{chr(10).join(f'- "{t}"' for t in defn['triggers'])}

## Canonical Prompt
{defn['prompt']}

## Scripts
{chr(10).join(f'- `{s}`' for s in defn.get('scripts', []))}
"""
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / f"{name}.md").write_text(content, encoding="utf-8")


def _ensure_skill_dirs() -> None:
    """Create the skill source directories if they don't exist."""
    for name in SKILL_DEFS:
        skill_dir = ROOT / SKILLS_SOURCE / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = skill_dir / "prompt.md"
        if not prompt_file.is_file():
            prompt_file.write_text(
                f"# {name}\n\n"
                f"{SKILL_DEFS[name]['description']}\n\n"
                f"## 工作流\n\n待编写。\n\n"
                f"## 输入\n\n待定义。\n\n"
                f"## 输出\n\n待定义。\n",
                encoding="utf-8"
            )


def _write_codex_hooks() -> None:
    """Write .codex/hooks.json for lifecycle script bindings."""
    hooks_dir = ROOT / ".codex"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hooks = {
        "description": "Narrative Workbench lifecycle hooks for Codex",
        "hooks": {
            "post-chapter": {
                "description": "Run after writing a chapter to canonical",
                "scripts": [
                    "python scripts/chapter_index.py --write",
                    "python scripts/doctor.py",
                ],
            },
            "pre-batch": {
                "description": "Run before batch writing",
                "scripts": [
                    "python scripts/hook_report.py --current N-1",
                    "python scripts/hook_matrix.py --current N-1",
                    "python scripts/structure_report.py",
                ],
            },
            "gatekeeper": {
                "description": "Gatekeeper check before final-check",
                "scripts": [
                    "python scripts/gatekeeper.py --chapter N --stage final",
                ],
            },
        },
    }

    import json
    hooks_path = hooks_dir / "hooks.json"
    hooks_path.write_text(json.dumps(hooks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  .codex/hooks.json")


def _write_codex_agents() -> None:
    """Write .codex/agents/ registration files (mirroring .claude/agents/)."""
    agents_dir = ROOT / CODEX_AGENTS
    agents_dir.mkdir(parents=True, exist_ok=True)

    agent_defs = {
        "project-librarian": {
            "description": "上下文路由 — 读取规则和状态，生成 Context Packet",
            "source": "agents/project-librarian.md",
        },
        "novel-writer": {
            "description": "Writer — 写原始草稿",
            "source": "agents/writer.md",
        },
        "novel-polish": {
            "description": "Polish — 去 AI 味、校准文风",
            "source": "agents/polish.md",
        },
        "novel-review": {
            "description": "Review — 审阅，找 bug 和漂移",
            "source": "agents/review.md",
        },
        "novel-fixer": {
            "description": "Fixer — 按 Review 报告修复",
            "source": "agents/fixer.md",
        },
    }

    for name, defn in agent_defs.items():
        content = f"""# {name}
{defn['description']}

Source: {defn['source']}

This is a Codex agent registration. The detailed agent prompt lives in agents/.
"""
        (agents_dir / f"{name}.md").write_text(content, encoding="utf-8")

    print(f"  .codex/agents/ ({len(agent_defs)} agents)")


def cmd_sync(dry_run: bool = False) -> int:
    """Sync all skills from source to platform-specific wrappers."""
    if not dry_run:
        _ensure_skill_dirs()

    claude_dir = ROOT / CLAUDE_SKILLS
    codex_dir = ROOT / CODEX_SKILLS

    for name, defn in SKILL_DEFS.items():
        if dry_run:
            print(f"  [DRY RUN] {name} → {CLAUDE_SKILLS}/{name}.md + {CODEX_SKILLS}/{name}.md")
            continue

        _write_claude_skill(claude_dir, name, defn)
        _write_codex_skill(codex_dir, name, defn)
        print(f"  {name} → {CLAUDE_SKILLS}/ + {CODEX_SKILLS}/")

    # Codex-specific extras
    if not dry_run:
        _write_codex_hooks()
        _write_codex_agents()
    else:
        print("  [DRY RUN] .codex/hooks.json")
        print("  [DRY RUN] .codex/agents/ (5 agents)")

    return 0


def cmd_clean() -> int:
    """Remove stale wrappers that don't have a source definition."""
    removed = 0
    for target_dir in [CLAUDE_SKILLS, CODEX_SKILLS]:
        td = ROOT / target_dir
        if not td.is_dir():
            continue
        for wrapper in sorted(td.glob("*.md")):
            name = wrapper.stem
            if name not in SKILL_DEFS:
                wrapper.unlink()
                print(f"  Removed stale: {target_dir}/{name}.md")
                removed += 1
    if removed == 0:
        print("  No stale wrappers found")
    return 0


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Skills Sync for Narrative Workbench")
    add_root_argument(parser)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    parser.add_argument("--clean", action="store_true", help="Remove stale wrappers")
    args = parser.parse_args()
    ROOT = get_root(args)

    if args.clean:
        return cmd_clean()
    return cmd_sync(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
