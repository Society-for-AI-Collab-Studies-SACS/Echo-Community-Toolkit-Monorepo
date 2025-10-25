"""Vessel index agent builds a consolidated ritual ledger snapshot."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from library_core.agents.base import AgentConfig, BaseAgent

if TYPE_CHECKING:
    from library_core.storage import StorageManager
    from workspace.manager import WorkspaceManager


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class VesselIndexAgent(BaseAgent):
    """Aggregates Garden, Echo, Limnus, and Kira outputs into an index."""

    INDEX_FILE = Path("state") / "vessel_index.json"

    def __init__(
        self,
        workspace_id: str,
        storage: "StorageManager",
        manager: "WorkspaceManager",
        config: Optional[AgentConfig] = None,
    ) -> None:
        super().__init__(workspace_id, storage, manager, config)
        self.index_path = self.record.path / self.INDEX_FILE

    async def process(self, context) -> Dict[str, Any]:  # noqa: ANN001
        index = await self._load_index()
        entry = self._build_entry(context)

        entries: List[Dict[str, Any]] = index.get("entries", [])
        entries.append(entry)

        index["entries"] = entries
        index["updated_at"] = _iso_now()
        index["workspace_id"] = self.workspace_id
        index["summary"] = self._summarise(entries)

        await self._write_index(index)
        await self.append_log(
            "vessel_index",
            {
                "entry_id": entry["id"],
                "stage": entry["garden"].get("stage"),
                "memory_id": entry["memory"].get("memory_id"),
                "validation_passed": entry["validation"].get("passed"),
            },
        )

        context.metadata["vessel_index_count"] = len(entries)
        context.metadata["vessel_last_entry_id"] = entry["id"]
        context.metadata["vessel_last_stage"] = entry["garden"].get("stage")

        return {
            "entry_id": entry["id"],
            "total_entries": len(entries),
            "stage": entry["garden"].get("stage"),
            "memory_id": entry["memory"].get("memory_id"),
            "validation_passed": entry["validation"].get("passed"),
            "summary": index["summary"],
        }

    # ------------------------------------------------------------------ helpers

    async def _load_index(self) -> Dict[str, Any]:
        return await asyncio.to_thread(self._read_index)

    def _read_index(self) -> Dict[str, Any]:
        if not self.index_path.exists():
            return {"entries": []}
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"entries": []}

    async def _write_index(self, index: Dict[str, Any]) -> None:
        await asyncio.to_thread(self._write_index_sync, index)

    def _write_index_sync(self, index: Dict[str, Any]) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    def _build_entry(self, context) -> Dict[str, Any]:  # noqa: ANN001
        garden_result = context.agent_results.get("garden", {}) if hasattr(context, "agent_results") else {}
        echo_result = context.agent_results.get("echo", {})
        limnus_result = context.agent_results.get("limnus", {})
        kira_result = context.agent_results.get("kira", {})

        entry_id = uuid.uuid4().hex
        glyph = echo_result.get("glyph")
        persona = context.metadata.get("dominant_persona") if hasattr(context, "metadata") else None

        return {
            "id": entry_id,
            "ts": _iso_now(),
            "input": context.input_text if hasattr(context, "input_text") else "",
            "user_id": getattr(context, "user_id", None),
            "garden": {
                "stage": garden_result.get("stage"),
                "cycle": garden_result.get("cycle"),
                "ledger_ref": garden_result.get("ledger_ref"),
                "consent_count": garden_result.get("consent_count"),
            },
            "echo": {
                "glyph": glyph,
                "persona": persona or echo_result.get("persona"),
                "mode_weights": echo_result.get("state"),
            },
            "memory": {
                "memory_id": limnus_result.get("memory_id"),
                "layer": limnus_result.get("layer"),
                "block_hash": limnus_result.get("block_hash"),
            },
            "validation": {
                "passed": self._as_bool(kira_result),
                "issues": kira_result.get("issues", []),
            },
        }

    @staticmethod
    def _as_bool(kira_result: Dict[str, Any]) -> bool:
        if "passed" in kira_result:
            return bool(kira_result["passed"])
        if "valid" in kira_result:
            return bool(kira_result["valid"])
        return False

    @staticmethod
    def _summarise(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(entries)
        stage_counts: Dict[str, int] = {}
        validation_failures = 0

        for entry in entries:
            stage = entry.get("garden", {}).get("stage") or "unknown"
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            if not entry.get("validation", {}).get("passed", False):
                validation_failures += 1

        latest = entries[-1] if entries else {}
        return {
            "total_entries": total,
            "by_stage": stage_counts,
            "validation_failures": validation_failures,
            "latest_entry_id": latest.get("id"),
            "latest_stage": latest.get("garden", {}).get("stage"),
            "latest_memory_id": latest.get("memory", {}).get("memory_id"),
            "latest_persona": latest.get("echo", {}).get("persona"),
        }
