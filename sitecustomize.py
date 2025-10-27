"""Shared runtime tweaks for consistent test execution."""

import os
import sys
from pathlib import Path

os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

ROOT = Path(__file__).resolve().parent
TOOLKIT = ROOT / "Echo-Community-Toolkit"
SOULCODE = TOOLKIT / "echo-soulcode-architecture"

def _extend_sys_path(candidate: Path) -> None:
    resolved = candidate.resolve()
    if resolved.exists():
        path_str = str(resolved)
        if path_str not in sys.path:
            sys.path.append(path_str)

_extend_sys_path(TOOLKIT / "src")
_extend_sys_path(SOULCODE / "src")
