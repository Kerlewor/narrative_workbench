"""Compatibility wrapper for project root resolution."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.project import add_root_argument, get_root  # noqa: E402,F401
