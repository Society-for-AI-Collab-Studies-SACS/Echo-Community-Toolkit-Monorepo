"""
Lightweight event logger for VesselOS.

Writes JSON lines to `pipeline/state/voice_log.json` with fields:
  ts, agent, command, payload, status
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")


def log_event(agent: str, command: str, payload: Dict[str, Any] | None = None, status: str = "ok") -> None:
    entry = {
        "ts": _ts(),
        "agent": agent,
        "command": command,
        "status": status,
        "payload": payload or {},
    }
    root = Path(__file__).resolve().parents[1]
    # Primary log under pipeline/state (as per Repository Guidelines)
    out_pipeline = root / "pipeline" / "state" / "voice_log.json"
    ensure_file(out_pipeline)
    with out_pipeline.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    # Secondary mirror under state/voice_log.json to satisfy alternate scaffolds
    out_state = root / "state" / "voice_log.json"
    ensure_file(out_state)
    with out_state.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
