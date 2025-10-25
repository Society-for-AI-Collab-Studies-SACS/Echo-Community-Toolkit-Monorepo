"""Lightweight dictation listener used for integration tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional


@dataclass(slots=True)
class DictationInput:
    text: str
    source: str
    user_id: str
    workspace_id: str
    timestamp: str
    confidence: float = 1.0


class DictationListener:
    """Captures text or simulated voice input for a workspace."""

    def __init__(self, workspace_id: str) -> None:
        self.workspace_id = workspace_id
        self.is_listening = False
        self.on_input: Optional[Callable[[DictationInput], Awaitable[None]]] = None

    async def listen_text(self, text: str, user_id: str) -> DictationInput:
        entry = DictationInput(
            text=text,
            source="text",
            user_id=user_id,
            workspace_id=self.workspace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        if self.on_input:
            await self.on_input(entry)
        return entry

    async def listen_voice(self, user_id: str, duration: int = 5) -> DictationInput:
        await asyncio.sleep(duration)
        entry = DictationInput(
            text="Simulated voice input",
            source="voice",
            user_id=user_id,
            workspace_id=self.workspace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=0.9,
        )
        if self.on_input:
            await self.on_input(entry)
        return entry

    def start_continuous(self, user_id: str) -> None:
        self.is_listening = True

    def stop_continuous(self) -> None:
        self.is_listening = False
