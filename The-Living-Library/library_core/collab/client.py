"""
Client shim for collaboration endpoints.

The eventual implementation will manage WebSocket sessions, heartbeats,
cursor sharing, and offline queues. For now we expose a synchronous API
that allows higher layers to begin wiring unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class ConnectionState:
    """Represents the last known connection details."""

    server: str
    session: str
    user: str


class CollaborationClient:
    """Placeholder client that records connection intent."""

    def __init__(self) -> None:
        self._state: Optional[ConnectionState] = None

    def connect(self, server: str, session: str, user: str) -> ConnectionState:
        """Simulate establishing a collaboration connection."""
        self._state = ConnectionState(server=server, session=session, user=user)
        return self._state

    def disconnect(self) -> None:
        """Clear the simulated connection."""
        self._state = None

    @property
    def state(self) -> Optional[ConnectionState]:
        """Return the last recorded connection details."""
        return self._state
