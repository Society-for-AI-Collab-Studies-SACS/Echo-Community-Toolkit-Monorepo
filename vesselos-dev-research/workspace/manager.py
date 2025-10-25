"""
Workspace manager scaffold for The Living Library.

The fully featured version will extend Kira Prime's multi-workspace
capabilities and tie in collaboration sessions plus shared resources.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable


@dataclass(slots=True)
class WorkspaceRecord:
    """Minimal description of a workspace."""

    workspace_id: str
    name: str
    path: Path

    def load_state(self, key: str, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
        state_file = self.path / "state" / f"{key}_state.json"
        if not state_file.exists():
            return default or {}
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default or {}

    def save_state(self, key: str, state: Dict[str, Any]) -> None:
        state_dir = self.path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / f"{key}_state.json"
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def append_log(self, log_type: str, entry: Dict[str, Any]) -> None:
        logs_dir = self.path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / f"{log_type}.jsonl"
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


class WorkspaceManager:
    """Local registry for Living Library workspaces."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = Path(root or ".").resolve()
        self._workspaces: Dict[str, WorkspaceRecord] = {}

    def register(self, workspace_id: str, name: str | None = None) -> WorkspaceRecord:
        record = WorkspaceRecord(
            workspace_id=workspace_id,
            name=name or workspace_id,
            path=self._workspace_root(workspace_id),
        )
        self._ensure_structure(record)
        self._workspaces[workspace_id] = record
        return record

    def get(self, workspace_id: str) -> WorkspaceRecord:
        if workspace_id in self._workspaces:
            return self._workspaces[workspace_id]
        return self.register(workspace_id)

    def list_workspaces(self) -> Iterable[WorkspaceRecord]:
        return tuple(self._workspaces.values())

    def _workspace_root(self, workspace_id: str) -> Path:
        return self._root / "workspaces" / workspace_id

    def _ensure_structure(self, record: WorkspaceRecord) -> None:
        record.path.mkdir(parents=True, exist_ok=True)
        for folder in ("logs", "state", "outputs", "collab"):
            (record.path / folder).mkdir(parents=True, exist_ok=True)
