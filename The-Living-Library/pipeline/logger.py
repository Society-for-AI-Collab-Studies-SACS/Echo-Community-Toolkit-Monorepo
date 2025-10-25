"""Pipeline logger that mirrors the voice log behaviour used in docs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from workspace.manager import WorkspaceManager


class PipelineLogger:
    """Persist pipeline activity to the workspace `voice_log.json`."""

    def __init__(self, workspace_id: str, manager: WorkspaceManager | None = None) -> None:
        self._manager = manager or WorkspaceManager()
        self._record = self._manager.get(workspace_id)
        self.workspace_id = workspace_id
        self._log_path = self._record.path / "logs" / "voice_log.json"
        self._ensure_log_file()

    async def log_start(self, context) -> None:  # noqa: ANN001
        self._append(
            {
                "event": "pipeline_start",
                "timestamp": context.timestamp,
                "user_id": context.user_id,
                "workspace_id": context.workspace_id,
                "input": context.input_text,
                "intent": context.intent.intent_type,
            }
        )

    async def log_agent_step(self, agent_name: str, context, result: Dict[str, Any]) -> None:  # noqa: ANN001
        self._append(
            {
                "event": "agent_step",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": agent_name,
                "user_id": context.user_id,
                "result": result,
            }
        )

    async def log_complete(self, context, response: Dict[str, Any]) -> None:  # noqa: ANN001
        self._append(
            {
                "event": "pipeline_complete",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": context.user_id,
                "success": response["success"],
                "response": response,
            }
        )

    # ------------------------------------------------------------------

    def _ensure_log_file(self) -> None:
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._log_path.exists():
            self._log_path.write_text("[]", encoding="utf-8")

    def _append(self, entry: Dict[str, Any]) -> None:
        logs = self._read()
        logs.append(entry)
        self._log_path.write_text(json.dumps(logs, indent=2), encoding="utf-8")

    def _read(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self._log_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:  # pragma: no cover - defensive
            return []
