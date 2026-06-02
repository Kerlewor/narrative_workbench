"""Unified local CLI for Narrative Workbench."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.dashboard import write_dashboard
from core.diff_workflow import apply_candidates, generate_candidates, show_candidate
from core.doctor import Doctor
from core.exporter import export_book
from core.gatekeeper import build_report as build_gatekeeper_report
from core.context import chapter_prefix
from core.scene_cards import create_scene_card, list_scene_cards, render_scene_list
from core.voice_lab import build_voice_lab


def _project_root(value: str | None) -> Path:
    return Path(value).resolve() if value else Path.cwd().resolve()


def cmd_dashboard(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    output = Path(args.output).resolve() if args.output else None
    result = write_dashboard(root, output)
    if args.json:
        print(json.dumps(result.data, ensure_ascii=False, indent=2))
    else:
        target = output or root / "story/DASHBOARD.md"
        print(f"Dashboard written to {target.relative_to(root)}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    doctor = Doctor(root)
    code = doctor.run()
    print(doctor.render_report())
    return code


def cmd_gatekeeper(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    report = build_gatekeeper_report(root, args.chapter, args.stage)
    output = Path(args.output).resolve() if args.output else root / "story/runtime" / f"{chapter_prefix(args.chapter)}.gatekeeper.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    if args.json:
        data = {
            "schema": "narrative_workbench.gatekeeper_result.v1",
            "chapter": args.chapter,
            "stage": args.stage,
            "status": "failed" if "**FAILED**" in report else "passed",
            "blocking_count": report.count("[BLOCKING]"),
            "warning_count": report.count("[WARN]"),
            "output_path": str(output),
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"Gatekeeper report written to {output.relative_to(root)}")
        if "**FAILED**" in report:
            print(f"RESULT: FAILED - {report.count('[BLOCKING]')} blocking issues")
            return 1
        print("RESULT: PASSED")
    return 1 if "**FAILED**" in report else 0


def cmd_diff_generate(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    result = generate_candidates(root, args.chapter, Path(args.original).resolve(), Path(args.revised).resolve())
    if args.json:
        print(json.dumps(result.data, ensure_ascii=False, indent=2))
    else:
        summary = result.data["summary"]
        print(f"Diff generated: {result.data['candidate_count']} candidate(s)")
        print(f"Index: {result.index_path.relative_to(root)}")
        print(f"JSONL: {result.jsonl_path.relative_to(root)}")
        print(f"By type: {summary['by_type']}")
        print(f"By risk: {summary['by_risk']}")
    return 0


def cmd_diff_show(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    print(show_candidate(root, args.chapter, args.id))
    return 0


def cmd_diff_apply(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    output = Path(args.output).resolve() if args.output else None
    result = apply_candidates(root, args.chapter, args.accept, args.reject, output)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Applied diff decisions for chapter {args.chapter}")
        print(f"Accepted: {', '.join(result['accepted']) or '-'}")
        print(f"Rejected: {', '.join(result['rejected']) or '-'}")
        print(f"Pending: {', '.join(result['pending']) or '-'}")
        print(f"Output: {Path(result['output_path']).relative_to(root)}")
        print(f"Decision log: {Path(result['decision_log']).relative_to(root)}")
    return 0


def cmd_scene_create(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    result = create_scene_card(
        root,
        args.chapter,
        args.id,
        args.title,
        pov=args.pov,
        location=args.location,
        purpose=args.purpose,
        characters=args.characters,
        hooks=args.hooks,
        forbidden=args.forbidden,
    )
    if args.json:
        print(json.dumps(result.data, ensure_ascii=False, indent=2))
    else:
        print(f"Scene card written to {result.path.relative_to(root)}")
    return 0


def cmd_scene_list(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    data = list_scene_cards(root, args.chapter)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_scene_list(data))
    return 0


def cmd_voice_lab(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    result = build_voice_lab(root, args.character, args.line)
    if args.json:
        print(json.dumps(result.data, ensure_ascii=False, indent=2))
    else:
        print(f"Voice lab written to {result.path.relative_to(root)}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    root = _project_root(args.project_root)
    output = Path(args.output).resolve()
    result = export_book(root, output, args.format)
    if args.json:
        print(json.dumps(result.data, ensure_ascii=False, indent=2))
    else:
        print(f"Exported {result.data['chapter_count']} chapter(s) to {result.output_path.relative_to(root) if result.output_path.is_relative_to(root) else result.output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nw", description="Narrative Workbench local entrypoint")
    parser.add_argument("--project-root", default=None, help="项目根目录，默认当前目录")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dashboard = subparsers.add_parser("dashboard", help="生成 story/DASHBOARD.md")
    dashboard.add_argument("--output", default=None)
    dashboard.add_argument("--json", action="store_true")
    dashboard.set_defaults(func=cmd_dashboard)

    doctor = subparsers.add_parser("doctor", help="运行项目健康检查")
    doctor.set_defaults(func=cmd_doctor)

    gatekeeper = subparsers.add_parser("gatekeeper", help="运行章节门禁检查")
    gatekeeper.add_argument("--chapter", type=int, required=True)
    gatekeeper.add_argument(
        "--stage",
        default="final",
        choices=["intent", "writer", "polish", "review", "fixer", "final"],
    )
    gatekeeper.add_argument("--output", default=None)
    gatekeeper.add_argument("--json", action="store_true")
    gatekeeper.set_defaults(func=cmd_gatekeeper)

    diff = subparsers.add_parser("diff", help="共创 diff 工作流")
    diff_sub = diff.add_subparsers(dest="diff_command", required=True)

    generate = diff_sub.add_parser("generate", help="根据作者稿和候选润色稿生成分层 diff")
    generate.add_argument("--chapter", type=int, required=True)
    generate.add_argument("--original", required=True)
    generate.add_argument("--revised", required=True)
    generate.add_argument("--json", action="store_true")
    generate.set_defaults(func=cmd_diff_generate)

    show = diff_sub.add_parser("show", help="显示单条 diff 详情")
    show.add_argument("--chapter", type=int, required=True)
    show.add_argument("--id", required=True)
    show.set_defaults(func=cmd_diff_show)

    apply = diff_sub.add_parser("apply", help="按编号接受/拒绝 diff")
    apply.add_argument("--chapter", type=int, required=True)
    apply.add_argument("--accept", default="")
    apply.add_argument("--reject", default="")
    apply.add_argument("--output", default=None)
    apply.add_argument("--json", action="store_true")
    apply.set_defaults(func=cmd_diff_apply)

    scene = subparsers.add_parser("scene", help="场景卡工具")
    scene_sub = scene.add_subparsers(dest="scene_command", required=True)
    scene_create = scene_sub.add_parser("create", help="创建 Markdown 场景卡")
    scene_create.add_argument("--chapter", type=int, required=True)
    scene_create.add_argument("--id", required=True)
    scene_create.add_argument("--title", required=True)
    scene_create.add_argument("--pov", default="")
    scene_create.add_argument("--location", default="")
    scene_create.add_argument("--purpose", default="")
    scene_create.add_argument("--characters", default="")
    scene_create.add_argument("--hooks", default="")
    scene_create.add_argument("--forbidden", default="")
    scene_create.add_argument("--json", action="store_true")
    scene_create.set_defaults(func=cmd_scene_create)
    scene_list = scene_sub.add_parser("list", help="列出章节场景卡")
    scene_list.add_argument("--chapter", type=int, required=True)
    scene_list.add_argument("--json", action="store_true")
    scene_list.set_defaults(func=cmd_scene_list)

    voice = subparsers.add_parser("voice-lab", help="生成角色声音实验室任务包")
    voice.add_argument("--character", required=True)
    voice.add_argument("--line", default="")
    voice.add_argument("--json", action="store_true")
    voice.set_defaults(func=cmd_voice_lab)

    export = subparsers.add_parser("export", help="导出章节为 Markdown/DOCX/EPUB")
    export.add_argument("--format", choices=["markdown", "md", "docx", "epub"], required=True)
    export.add_argument("--output", required=True)
    export.add_argument("--json", action="store_true")
    export.set_defaults(func=cmd_export)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
