"""Convenience helpers for accessing Living Library workspaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from workspace.manager import WorkspaceManager, WorkspaceRecord

from .storage import StorageManager

_MANAGER = WorkspaceManager()


class Workspace:
    """Thin wrapper around ``WorkspaceRecord`` providing convenience helpers."""

    def __init__(self, workspace_id: str, *, manager: WorkspaceManager | None = None) -> None:
        self._manager = manager or _MANAGER
        self._record: WorkspaceRecord = self._manager.get(workspace_id)

    @property
    def workspace_id(self) -> str:
        return self._record.workspace_id

    @property
    def path(self) -> Path:
        return self._record.path

    def load_state(self, key: str, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return self._record.load_state(key, default or {})

    def save_state(self, key: str, state: Dict[str, Any]) -> None:
        self._record.save_state(key, state)

    def append_log(self, log_type: str, entry: Dict[str, Any]) -> None:
        self._record.append_log(log_type, entry)

    def storage(self) -> StorageManager:
        """Return a storage adapter rooted at this workspace path."""
        return StorageManager(self._record.path)


def get_manager() -> WorkspaceManager:
    """Return the shared workspace manager instance."""
    return _MANAGER


def get_workspace(workspace_id: str) -> Workspace:
    """Retrieve a ``Workspace`` wrapper for ``workspace_id``."""
    return Workspace(workspace_id)


def get_storage(workspace_id: str) -> StorageManager:
    """Convenience helper to obtain a ``StorageManager`` for ``workspace_id``."""
    return StorageManager(_MANAGER.get(workspace_id).path)
