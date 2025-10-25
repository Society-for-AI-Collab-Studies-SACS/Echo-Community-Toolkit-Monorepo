"""Minimal storage adapter used by the enhanced dispatcher."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class StorageManager:
    """Utility wrapper providing JSON file helpers within a workspace."""

    def __init__(self, workspace_path: Path) -> None:
        self.workspace_path = workspace_path

    def read_json(self, relative: Path, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
        path = self.workspace_path / relative
        if not path.exists():
            return default or {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default or {}

    def write_json(self, relative: Path, data: Dict[str, Any]) -> None:
        path = self.workspace_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def append_jsonl(self, relative: Path, entry: Dict[str, Any]) -> None:
        path = self.workspace_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
