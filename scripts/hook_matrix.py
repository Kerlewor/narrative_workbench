#!/usr/bin/env python3
"""Produce a dependency and recovery matrix for hooks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from _project import add_root_argument, get_root
from core.hooks import (  # noqa: E402
    ACTIVE,
    TERMINAL,
    VALID_PRIORITIES,
    VALID_STATUSES,
    as_int,
    build_hook_matrix,
    detect_cycles,
    ids_from_dependency,
    parse_table,
)


ROOT: Path = Path.cwd()


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser()
    add_root_argument(parser)
    parser.add_argument("--current", type=int, required=True, help="current finalized chapter")
    args = parser.parse_args()
    ROOT = get_root(args)

    code, lines = build_hook_matrix(ROOT, args.current)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
