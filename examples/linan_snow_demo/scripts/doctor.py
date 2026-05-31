#!/usr/bin/env python3
"""Health check for Narrative Workbench.

Run from the project root:
    python scripts/doctor.py
"""

from __future__ import annotations
from _project import add_root_argument, get_root

import json
import re
import sys
from pathlib import Path


ROOT: Path = Path.cwd()  # Set in main() via --project-root or CWD

REQUIRED_FILES = [
    "CLAUDE.md",
    "AGENTS.md",
    "START_HERE.md",
    "RUN_RULES.md",
    "PROJECT_INTRO.md",
    "workflow/constitution.md",
    "workflow/lifecycle.md",
    "scripts/chapter_index.py",
    "scripts/context_builder.py",
    "scripts/create_project.py",
    "scripts/prompt_compiler.py",
    "scripts/gatekeeper.py",
    "scripts/hook_report.py",
    "scripts/hook_matrix.py",
    "scripts/structure_report.py",
    "scripts/text_audit.py",
    "scripts/knowledge_index.py",
    "scripts/status.py",
    "scripts/skill_check.py",
    "scripts/style_report.py",
    "scripts/character_drift_report.py",
    "scripts/decompose_style.py",
    "scripts/import_inkos_project.py",
    "scripts/review_author_chapter.py",
    "scripts/polish_author_chapter.py",
    "scripts/relevance_resolver.py",
    "scripts/ledger_manager.py",
    "scripts/render_views.py",
    "scripts/director_sheet.py",
    "scripts/sync_skills.py",
    "skills/skill_protocol.md",
    "skills/skill_registry.md",
    "skills/_template.skill-entry.md",
    "skills/_template.skill-request.md",
    "story/system_protocol.md",
    "story/state_contract.md",
    "story/hook_protocol.md",
    "story/style_blacklist.md",
    "story/current_focus.md",
    "story/current_state.md",
    "story/chapter_summaries.md",
    "story/pending_hooks.md",
    "story/emotional_arcs.md",
    "story/outline/story_frame.md",
    "story/outline/volume_map.md",
    "story/outline/_template.discovery.md",
    "story/outline/_template.import-outline.md",
    "story/runtime/_template.intent.md",
    "story/runtime/_template.plan.md",
    "story/runtime/_template.final-check.md",
    "story/runtime/_template.agent-handoff.md",
    "story/runtime/_template.scene-beat.md",
    "story/runtime/_template.context-packet.md",
    "story/runtime/_template.batch-audit.md",
    "story/runtime/_template.batch-plan.md",
    "story/runtime/_template.coherence_review.md",
    "story/runtime/_template.session-close.md",
    "story/runtime/_template.scene_handoffs.yaml",
    "agents/project-librarian.md",
    "agents/writer.md",
    "agents/polish.md",
    "agents/review.md",
    "agents/fixer.md",
    ".claude/agents/project-librarian.md",
    ".claude/agents/novel-writer.md",
    ".claude/agents/novel-polish.md",
    ".claude/agents/novel-review.md",
    ".claude/agents/novel-fixer.md",
]

JSON_FILES = [
    "chapters/index.json",
    "story/state/manifest.json",
    "story/state/current_state.json",
    "story/state/chapter_summaries.json",
    "story/state/hooks.json",
]

HOOK_STATUSES = {"open", "progressing", "escalated", "resolved", "dormant", "dropped"}
HOOK_PRIORITIES = {"core", "high", "normal", "low"}
HOOK_HEADER = [
    "hook_id",
    "起始章节",
    "类型",
    "状态",
    "优先级",
    "最近推进",
    "预期回收",
    "回收卷/章",
    "回收节奏",
    "上游依赖",
    "半衰期",
    "升级条件",
    "正文证据",
    "备注",
]

RUNTIME_STATUSES = {
    "planned",
    "drafted",
    "polished",
    "reviewed",
    "fixed",
    "final-check",
    "final-aligned",
    "superseded",
    "needs-repair",
    "needs-rewrite",
    "audited",
    "context-packed",
}


class Doctor:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def check_required_files(self) -> None:
        for rel in REQUIRED_FILES:
            if not (ROOT / rel).is_file():
                self.error(f"missing required file: {rel}")

    def check_json(self) -> dict[str, object]:
        loaded: dict[str, object] = {}
        for rel in JSON_FILES:
            path = ROOT / rel
            if not path.is_file():
                self.error(f"missing json file: {rel}")
                continue
            try:
                loaded[rel] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                self.error(f"invalid json: {rel}: {exc}")
        return loaded

    def check_claude_agents(self) -> None:
        for path in sorted((ROOT / ".claude/agents").glob("*.md")):
            lines = path.read_text(encoding="utf-8").splitlines()
            rel = path.relative_to(ROOT)
            if len(lines) < 4:
                self.error(f"invalid agent frontmatter: {rel}")
                continue
            if lines[0] != "---" or lines[3] != "---":
                self.error(f"invalid agent frontmatter delimiter: {rel}")
            if not lines[1].startswith("name: "):
                self.error(f"missing agent name: {rel}")
            if not lines[2].startswith("description: "):
                self.error(f"missing agent description: {rel}")

    def check_chapter_index(self, loaded: dict[str, object]) -> None:
        index = loaded.get("chapters/index.json")
        if not isinstance(index, dict):
            return
        chapters = index.get("chapters", [])
        if not isinstance(chapters, list):
            self.error("chapters/index.json: chapters must be a list")
            return
        seen: set[int] = set()
        for item in chapters:
            if not isinstance(item, dict):
                self.error("chapters/index.json: chapter item must be object")
                continue
            chapter = item.get("chapter")
            file_name = item.get("file")
            if not isinstance(chapter, int):
                self.error(f"chapters/index.json: invalid chapter number: {item}")
            elif chapter in seen:
                self.error(f"chapters/index.json: duplicate chapter: {chapter}")
            else:
                seen.add(chapter)
            if not isinstance(file_name, str) or not file_name:
                self.error(f"chapters/index.json: missing file for chapter {chapter}")
            elif not (ROOT / file_name).is_file():
                self.error(f"chapters/index.json: indexed chapter file missing: {file_name}")

        actual = sorted(p for p in (ROOT / "chapters").glob("*.md") if p.name != "index.md")
        indexed = {ROOT / item.get("file", "") for item in chapters if isinstance(item, dict)}
        for path in actual:
            if path not in indexed:
                self.warn(f"chapter file not indexed: {path.relative_to(ROOT)}")

    def parse_markdown_table(self, rel: str) -> tuple[list[str], list[list[str]]]:
        path = ROOT / rel
        if not path.is_file():
            return [], []
        lines = path.read_text(encoding="utf-8").splitlines()
        tables = [line for line in lines if line.startswith("|") and line.endswith("|")]
        if len(tables) < 2:
            return [], []
        header = [cell.strip() for cell in tables[0].strip("|").split("|")]
        rows = []
        for line in tables[2:]:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) == len(header):
                rows.append(cells)
        return header, rows

    def check_hooks_markdown(self) -> None:
        header, rows = self.parse_markdown_table("story/pending_hooks.md")
        if not header:
            self.warn("pending_hooks.md has no hook table")
            return
        if header != HOOK_HEADER:
            self.error("pending_hooks.md header does not match hook_protocol.md contract")
            return
        ids: set[str] = set()
        for row in rows:
            hook = dict(zip(header, row))
            hook_id = hook["hook_id"]
            if not re.fullmatch(r"H\d{3,}", hook_id):
                self.error(f"invalid hook_id: {hook_id}")
            if hook_id in ids:
                self.error(f"duplicate hook_id: {hook_id}")
            ids.add(hook_id)
            if hook["状态"] not in HOOK_STATUSES:
                self.error(f"{hook_id}: invalid status: {hook['状态']}")
            if hook["优先级"] not in HOOK_PRIORITIES:
                self.error(f"{hook_id}: invalid priority: {hook['优先级']}")
            if hook["状态"] != "resolved" and not hook["正文证据"]:
                self.warn(f"{hook_id}: active hook has no text evidence")
            if hook["半衰期"] and not hook["半衰期"].isdigit():
                self.error(f"{hook_id}: halfLife must be numeric when set")

    def check_hooks_json(self, loaded: dict[str, object]) -> None:
        hooks_json = loaded.get("story/state/hooks.json")
        if not isinstance(hooks_json, dict):
            return
        hooks = hooks_json.get("hooks", [])
        if not isinstance(hooks, list):
            self.error("story/state/hooks.json: hooks must be a list")
            return
        for item in hooks:
            if not isinstance(item, dict):
                self.error("story/state/hooks.json: hook item must be object")
                continue
            hook_id = item.get("hookId")
            status = item.get("status")
            priority = item.get("priority")
            if not isinstance(hook_id, str) or not re.fullmatch(r"H\d{3,}", hook_id):
                self.error(f"story/state/hooks.json: invalid hookId: {hook_id}")
            if status not in HOOK_STATUSES:
                self.error(f"{hook_id}: invalid json status: {status}")
            if priority not in HOOK_PRIORITIES:
                self.error(f"{hook_id}: invalid json priority: {priority}")

    def check_runtime_statuses(self) -> None:
        for path in sorted((ROOT / "story/runtime").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT)
            match = re.search(r"^status:\s*([A-Za-z0-9_-]+)\s*$", text, re.MULTILINE)
            if not match:
                skip_prefixes = ("_template.",)
                skip_suffixes = (".context.md", ".gatekeeper.md", ".prompt.md", ".knowledge_packet.md", ".style_report.md", ".character_drift.md", ".author_review_brief.md", ".author_polish_", ".resolved.md")
                if not (path.name.startswith(skip_prefixes) or path.name.endswith(skip_suffixes)):
                    self.warn(f"runtime file has no status: {rel}")
                continue
            status = match.group(1)
            if status not in RUNTIME_STATUSES:
                self.error(f"{rel}: invalid runtime status: {status}")

    def check_startup_references(self) -> None:
        claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        for rel in ["RUN_RULES.md", "story/system_protocol.md", "story/state_contract.md", "story/hook_protocol.md"]:
            if rel not in claude:
                self.error(f"CLAUDE.md does not reference {rel}")

    def check_skill_registry(self) -> None:
        registry = ROOT / "skills/skill_registry.md"
        if not registry.is_file():
            self.error("missing skills/skill_registry.md")
            return
        lines = registry.read_text(encoding="utf-8").splitlines()
        tables = [line for line in lines if line.startswith("|") and line.endswith("|")]
        if len(tables) < 2:
            self.error("skills/skill_registry.md has no registry table")
            return
        header = [cell.strip() for cell in tables[0].strip("|").split("|")]
        expected = ["skill", "用途", "触发条件", "入口文件/说明", "输出位置", "状态"]
        if header != expected:
            self.error("skills/skill_registry.md header does not match expected structure")
            return
        valid_statuses = {"enabled", "disabled", "deprecated"}
        seen: set[str] = set()
        for line in tables[2:]:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) != len(header):
                continue
            row = dict(zip(header, cells))
            skill = row["skill"]
            status = row["状态"]
            if skill in seen:
                self.error(f"duplicate skill registry entry: {skill}")
            seen.add(skill)
            if status not in valid_statuses:
                self.error(f"{skill}: invalid skill status: {status}")

    def run(self) -> int:
        self.check_required_files()
        loaded = self.check_json()
        self.check_claude_agents()
        self.check_chapter_index(loaded)
        self.check_hooks_markdown()
        self.check_hooks_json(loaded)
        self.check_runtime_statuses()
        self.check_startup_references()
        self.check_skill_registry()

        print("Narrative Workbench doctor")
        print(f"root: {ROOT}")
        if self.errors:
            print("\nERRORS:")
            for item in self.errors:
                print(f"- {item}")
        if self.warnings:
            print("\nWARNINGS:")
            for item in self.warnings:
                print(f"- {item}")
        if not self.errors and not self.warnings:
            print("\nOK: no issues found.")
        elif not self.errors:
            print("\nOK with warnings.")
        else:
            print("\nFAILED.")
        return 1 if self.errors else 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Narrative Workbench doctor")
    add_root_argument(parser)
    args = parser.parse_args()
    ROOT = get_root(args)
    sys.exit(Doctor().run())
