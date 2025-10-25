from __future__ import annotations

"""Garden Agent (Ritual Orchestrator & Scroll Keeper)

Commands:
- start, next, open <scroll>, resume, log <text>, ledger

State stored in `state/garden_ledger.json` with fields:
  stage, entries[] (each with ts, kind, data)
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from interface.logger import log_event


STAGES = ["scatter", "witness", "plant", "return", "give", "begin_again"]


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class GardenAgent:
    def __init__(self, root: Path):
        self.root = root
        self.ledger_path = self.root / "state" / "garden_ledger.json"
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_ledger()

    def _ensure_ledger(self) -> None:
        if not self.ledger_path.exists():
            self._save({"stage": "scatter", "entries": []})

    def _load(self) -> Dict:
        try:
            d = json.loads(self.ledger_path.read_text(encoding="utf-8"))
            if "stage" not in d:
                d["stage"] = "scatter"
            if "entries" not in d or not isinstance(d["entries"], list):
                d["entries"] = []
            return d
        except Exception:
            d = {"stage": "scatter", "entries": []}
            self._save(d)
            return d

    def _save(self, data: Dict) -> None:
        self.ledger_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def start(self) -> str:
        data = {"stage": "scatter", "entries": [{"ts": _ts(), "kind": "genesis", "data": {}}]}
        self._save(data)
        log_event("garden", "start", data)
        return "genesis"

    def next(self) -> str:
        d = self._load()
        stage = d.get("stage", "scatter")
        idx = (STAGES.index(stage) + 1) % len(STAGES) if stage in STAGES else 0
        d["stage"] = STAGES[idx]
        d.setdefault("entries", []).append({"ts": _ts(), "kind": "advance", "data": {"to": d["stage"]}})
        self._save(d)
        log_event("garden", "next", {"stage": d["stage"]})
        return d["stage"]

    def open(self, scroll: str, prev: bool = False, reset: bool = False) -> str:
        d = self._load()
        event = {"ts": _ts(), "kind": "open", "data": {"scroll": scroll, "prev": prev, "reset": reset}}
        d.setdefault("entries", []).append(event)
        self._save(d)
        log_event("garden", "open", event)
        return f"open:{scroll}"

    def resume(self) -> str:
        d = self._load()
        log_event("garden", "resume", {"stage": d.get("stage")})
        return d.get("stage", "scatter")

    def log(self, text: str) -> str:
        d = self._load()
        entry = {"ts": _ts(), "kind": "note", "data": {"text": text}}
        d.setdefault("entries", []).append(entry)
        self._save(d)
        log_event("garden", "log", entry)
        return f"note:{len(d['entries'])}"

    def ledger(self) -> str:
        return self.ledger_path.read_text(encoding="utf-8")
