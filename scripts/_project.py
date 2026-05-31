"""Shared project root resolution for all Narrative Workbench scripts.

Supports explicit --project-root and falls back to current working directory.
Replaces the former hardcoded `ROOT = Path(__file__).resolve().parents[1]` pattern.

Usage:
    from _project import add_root_argument, get_root

    parser = argparse.ArgumentParser(...)
    add_root_argument(parser)
    args = parser.parse_args()
    ROOT = get_root(args)
"""

import argparse
from pathlib import Path


def add_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project-root", type=str, default=None,
        help="Project root directory (default: current working directory)"
    )


def get_root(args: argparse.Namespace) -> Path:
    if args.project_root:
        return Path(args.project_root).resolve()
    return Path.cwd()
