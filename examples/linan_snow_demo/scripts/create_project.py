#!/usr/bin/env python3
"""Create a new novel project from Narrative Workbench.

Usage:
    python3 scripts/create_project.py "我的新小说"
    python3 scripts/create_project.py "我的新小说" --target /path/to/books
"""

from __future__ import annotations
from _project import add_root_argument, get_root

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


TEMPLATE_ROOT: Path = Path(__file__).resolve().parents[1]
DEFAULT_TARGET_ROOT = TEMPLATE_ROOT.parents[1]  # .../books


def slugify(name: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", name.strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned or "new_novel_project"


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_manifest(project_root: Path, project_name: str) -> None:
    manifest_path = project_root / "story/state/manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["project"] = project_name
    data["createdFrom"] = "narrative_workbench"
    data["createdAt"] = datetime.now(timezone.utc).isoformat()
    write_json(manifest_path, data)


def write_project_intro(project_root: Path, project_name: str) -> None:
    content = f"""# {project_name}

本项目由 Narrative Workbench / 叙事工作台模板创建。

## 项目说明

- 项目名称：{project_name}
- 创建时间：{datetime.now(timezone.utc).isoformat()}
- 工作流来源：`narrative_workbench`

## 启动方式

在本目录启动 Claude Code，然后让 AI 先读取：

1. `START_HERE.md`
2. `CLAUDE.md`
3. `RUN_RULES.md`

如果尚未搭建大纲，对 AI 说：

```text
搭建大纲
```

## 注意

- 不要直接在 `_frameworks/narrative_workbench` 模板目录里写作。
- 正文写入 `chapters/`。
- 大纲、状态、伏笔、角色卡写入 `story/`。
- Agent 中间产物写入 `story/runtime/`。
- Python 辅助脚本按 `RUN_RULES.md` 执行。
"""
    (project_root / "PROJECT.md").write_text(content, encoding="utf-8")


def reset_runtime_outputs(project_root: Path) -> None:
    runtime_dir = project_root / "story/runtime"
    for pattern in ("chapter-*.md", "batch-*.md", "*.skill-*.md"):
        for path in runtime_dir.glob(pattern):
            path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    add_root_argument(parser)
    parser.add_argument("project_name", help="new project display name")
    parser.add_argument("--target", default=str(DEFAULT_TARGET_ROOT), help="target parent directory")
    parser.add_argument("--force", action="store_true", help="overwrite target project directory")
    args = parser.parse_args()
    # --project-root is accepted but has no effect: TEMPLATE_ROOT is always
    # the directory containing this script's parent (the template root).

    target_root = Path(args.target).expanduser()
    if not target_root.is_absolute():
        target_root = (Path.cwd() / target_root).resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    project_root = target_root / slugify(args.project_name)
    if project_root.exists():
        if not args.force:
            print(f"ERROR: target already exists: {project_root}")
            print("Use --force to overwrite.")
            return 1
        shutil.rmtree(project_root)

    ignore = shutil.ignore_patterns("__pycache__", ".DS_Store", ".git", ".github", ".gitattributes")
    shutil.copytree(TEMPLATE_ROOT, project_root, ignore=ignore)
    reset_runtime_outputs(project_root)
    update_manifest(project_root, args.project_name)
    write_project_intro(project_root, args.project_name)

    print(f"created project: {project_root}")
    print("next:")
    print(f"  cd {project_root}")
    print("  claude")
    print("  tell AI: 搭建大纲")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

