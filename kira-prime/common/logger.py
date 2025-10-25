"""
Compatibility logger shim.

Some scaffolds expect a common/logger.py with a Logger class that writes to
state/voice_log.json. This module wraps the core logger in
interface/logger.py and mirrors entries to the expected location.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from interface.logger import log_event as _core_log_event


class Logger:
    def __init__(self, log_file: str = "state/voice_log.json") -> None:
        self.log_file = log_file

    def log(self, agent: str, action: str, details: Dict[str, Any] | None = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": agent,
            "action": action,
            "details": details or {},
        }
        # delegate to core logger for unified logging (writes both pipeline/state and state)
        _core_log_event(agent, action, details or {})
        # also ensure an array-style JSON exists at the path this shim was initialized with
        root = Path(__file__).resolve().parents[1]
        path = root / self.log_file
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        except Exception:
            data = []
        data.append(entry)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return entry

