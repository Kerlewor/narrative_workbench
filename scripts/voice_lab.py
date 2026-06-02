#!/usr/bin/env python3
"""Character voice lab wrapper. Prefer `nw voice-lab ...`."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.cli import main


def normalize_args(argv: list[str]) -> list[str]:
    normalized = list(argv)
    project_root = None
    if "--project-root" in normalized:
        idx = normalized.index("--project-root")
        if idx + 1 < len(normalized):
            project_root = normalized[idx + 1]
            del normalized[idx:idx + 2]
    if project_root:
        return ["--project-root", project_root, "voice-lab", *normalized]
    return ["voice-lab", *normalized]


if __name__ == "__main__":
    sys.exit(main(normalize_args(sys.argv[1:])))
