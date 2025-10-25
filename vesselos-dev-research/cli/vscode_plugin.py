"""
VS Code integration hooks for Prime.

The current scaffold mirrors status snapshots into ``state/prime_status.json`` so
the accompanying VS Code extension can display live updates.  Future work will
expand this module to emit richer events and surface diagnostics directly in the
editor.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from . import commands
from .plugins import subscribe

ROOT = Path(__file__).resolve().parents[1]
STATUS_FILE = ROOT / "state" / "prime_status.json"


def _write_status(_payload: Dict[str, Any]) -> None:
    snapshot = commands.build_status_snapshot()
    try:
        STATUS_FILE.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    except Exception as exc:  # pragma: no cover - best effort logging
        print(f"[prime:vscode] unable to write status file: {exc}")


subscribe("after_command", _write_status)

# TODO: surface richer feedback (e.g. validation messages) once the VS Code
# extension exposes dedicated channels for them.

