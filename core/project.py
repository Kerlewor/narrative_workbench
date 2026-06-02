"""Project root helpers shared by scripts and core modules."""

from __future__ import annotations

import argparse
from pathlib import Path


def add_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Project root directory (default: current working directory)",
    )


def get_root(args: argparse.Namespace) -> Path:
    if args.project_root:
        return Path(args.project_root).resolve()
    return Path.cwd()

