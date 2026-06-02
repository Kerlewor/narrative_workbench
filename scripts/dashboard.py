#!/usr/bin/env python3
"""Generate the Markdown-native writing dashboard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _project import add_root_argument, get_root

from core.dashboard import write_dashboard


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate story/DASHBOARD.md")
    add_root_argument(parser)
    parser.add_argument("--output", default=None)
    parser.add_argument("--json", action="store_true", help="输出结构化 JSON 协议")
    args = parser.parse_args()
    root = get_root(args)
    output = Path(args.output) if args.output else None
    result = write_dashboard(root, output)
    if args.json:
        print(json.dumps(result.data, ensure_ascii=False, indent=2))
    else:
        target = output or root / "story/DASHBOARD.md"
        print(f"Dashboard written to {target.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
