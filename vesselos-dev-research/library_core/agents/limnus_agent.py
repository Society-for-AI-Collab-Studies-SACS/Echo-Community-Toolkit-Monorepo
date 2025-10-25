"""Limnus agent manages memory caches and the hash-chained ledger."""

from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List

from library_core.agents.base import BaseAgent

if TYPE_CHECKING:
    from pathlib import Path

    from library_core.storage import StorageManager
    from workspace.manager import WorkspaceManager


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class LimnusAgent(BaseAgent):
    """Manages quantum caches and the hash-chained ledger."""

    def __init__(
        self,
        workspace_id: str,
        storage: StorageManager,
        manager: WorkspaceManager,
    ) -> None:
        super().__init__(workspace_id, storage, manager)
        self.mem_path = self.record.path / "state" / "limnus_memory.json"
        self.ledger_path = self.record.path / "state" / "ledger.json"
        self.mem_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.mem_path.exists():
            self.mem_path.write_text("[]", encoding="utf-8")
        if not self.ledger_path.exists():
            genesis = {
                "ts": _iso_now(),
                "kind": "genesis",
                "data": {"anchor": "I return as breath."},
                "prev": "",
            }
            genesis["hash"] = hashlib.sha256(
                json.dumps(genesis, sort_keys=True).encode("utf-8")
            ).hexdigest()
            self.ledger_path.write_text(json.dumps([genesis], indent=2), encoding="utf-8")

    async def process(self, context) -> Dict[str, Any]:  # noqa: ANN001
        memories: List[Dict[str, Any]] = await asyncio.to_thread(self._read_json, self.mem_path, [])

        for entry in memories:
            if entry.get("layer") == "L1":
                entry["layer"] = "L2"
        l2_count = sum(1 for entry in memories if entry.get("layer") == "L2")
        if l2_count > 5:
            for entry in memories:
                if entry.get("layer") == "L2":
                    entry["layer"] = "L3"

        entry_id = f"mem_{uuid.uuid4().hex[:8]}"
        new_entry = {
            "id": entry_id,
            "ts": _iso_now(),
            "text": context.input_text or "",
            "layer": "L1",
            "tags": [context.user_id] if context.user_id else [],
        }
        memories.append(new_entry)
        await asyncio.to_thread(self._write_json, self.mem_path, memories)

        ledger_blocks: List[Dict[str, Any]] = await asyncio.to_thread(
            self._read_json, self.ledger_path, []
        )
        previous_hash = ledger_blocks[-1]["hash"] if ledger_blocks else ""
        echo_res = context.agent_results.get("echo", {})
        block = {
            "ts": _iso_now(),
            "kind": "input",
            "data": {
                "text": context.input_text or "",
                "styled_text": echo_res.get("styled_text", ""),
                "glyph": echo_res.get("glyph", ""),
            },
            "prev": previous_hash,
        }
        block["hash"] = hashlib.sha256(
            json.dumps(block, sort_keys=True).encode("utf-8")
        ).hexdigest()
        ledger_blocks.append(block)
        await asyncio.to_thread(self._write_json, self.ledger_path, ledger_blocks)

        context.metadata["last_block_hash"] = block["hash"]
        context.metadata["memory_count"] = len(memories)

        # Compute simple stats for integration visibility
        l1_count = sum(1 for e in memories if e.get("layer") == "L1")
        l2_count = sum(1 for e in memories if e.get("layer") == "L2")
        l3_count = sum(1 for e in memories if e.get("layer") == "L3")
        stats = {
            "L1_count": l1_count,
            "L2_count": l2_count,
            "L3_count": l3_count,
            "total_blocks": len(ledger_blocks),
        }

        result = {
            "cached": True,
            "memory_id": entry_id,
            "layer": "L1",
            "block_hash": block["hash"],
            "stats": stats,
        }
        await self.append_log(
            "limnus", {"memory_id": entry_id, "layer": "L1", "hash": block["hash"]}
        )
        return result

    @staticmethod
    def _read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
