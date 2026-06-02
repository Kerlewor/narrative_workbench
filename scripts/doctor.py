#!/usr/bin/env python3
"""Health check for Narrative Workbench."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from _project import add_root_argument, get_root
from core.doctor import (  # noqa: E402
    HOOK_HEADER,
    HOOK_PRIORITIES,
    HOOK_STATUSES,
    JSON_FILES,
    REQUIRED_FILES,
    RUNTIME_STATUSES,
    Doctor as CoreDoctor,
)


ROOT: Path = Path.cwd()


class Doctor(CoreDoctor):
    def __init__(self) -> None:
        super().__init__(ROOT)


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Narrative Workbench doctor")
    add_root_argument(parser)
    args = parser.parse_args()
    ROOT = get_root(args)

    doctor = Doctor()
    code = doctor.run()
    print(doctor.render_report())
    return code


if __name__ == "__main__":
    sys.exit(main())
