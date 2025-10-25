"""
Remote collaboration runtime scaffolding.

This module exposes the collaboration server and client interfaces used
throughout The Living Library. ``CollaborationServer`` implements the
async WebSocket/Redis/PostgreSQL stack described in the Phase 3
specification, while ``create_app`` returns the FastAPI application used
by development and production deployments.
"""

from .client import CollaborationClient
from .server import CollaborationConfig, CollaborationServer, create_app

__all__ = [
    "CollaborationServer",
    "CollaborationClient",
    "CollaborationConfig",
    "create_app",
]
