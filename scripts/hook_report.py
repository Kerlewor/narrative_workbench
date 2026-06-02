#!/usr/bin/env python3
"""Report hook budget and half-life status from story/pending_hooks.md."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from _project import add_root_argument, get_root
from core.hooks import ACTIVE, as_int, build_hook_report, parse_table


ROOT: Path = Path.cwd()
ACTIVE_STATUSES = ACTIVE


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser()
    add_root_argument(parser)
    parser.add_argument("--current", type=int, required=True, help="current chapter number")
    args = parser.parse_args()
    ROOT = get_root(args)

    code, lines = build_hook_report(ROOT, args.current)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

