"""Abstract agent base classes used by the enhanced dispatcher."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from library_core.storage import StorageManager
from workspace.manager import WorkspaceManager


@dataclass(slots=True)
class AgentConfig:
    enabled: bool = True
    timeout_seconds: int = 30
    retry_attempts: int = 3
    verbose_logging: bool = False


class BaseAgent(ABC):
    def __init__(
        self,
        workspace_id: str,
        storage: StorageManager,
        manager: WorkspaceManager,
        config: Optional[AgentConfig] = None,
    ) -> None:
        self.workspace_id = workspace_id
        self.storage = storage
        self.manager = manager
        self.config = config or AgentConfig()
        self.record = manager.get(workspace_id)

    @abstractmethod
    async def process(self, context) -> Dict[str, Any]:  # noqa: ANN001
        """Process pipeline context and return agent result."""

    async def get_state(self, key: str) -> Dict[str, Any]:
        return await asyncio.to_thread(self.record.load_state, key, {})

    async def save_state(self, key: str, state: Dict[str, Any]) -> None:
        await asyncio.to_thread(self.record.save_state, key, state)

    async def append_log(self, log_type: str, entry: Dict[str, Any]) -> None:
        await asyncio.to_thread(self.record.append_log, log_type, entry)

    async def _run_blocking(self, func, *args, **kwargs):  # type: ignore[no-untyped-def]
        return await asyncio.to_thread(func, *args, **kwargs)
