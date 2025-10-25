"""
Shared dictation utilities for The Living Library.

This package provides the facilities required for self-collaboration
between a human operator and the Codex CLI agent.  Transcripts are
persisted inside the active workspace and can later be fed into the
MRP pipeline for chapter generation.
"""

from typing import Iterable

from workspace.manager import WorkspaceManager

from .session import DictationSession, DictationTurn


def start_session(
    workspace_id: str,
    *,
    manager: WorkspaceManager | None = None,
    session_id: str | None = None,
    participants: Iterable[str] | None = None,
    description: str | None = None,
) -> DictationSession:
    """
    Convenience helper for creating a dictation session.

    Parameters mirror :meth:`DictationSession.start`.  If a workspace
    manager is not supplied, a default instance rooted at ``.``
    (repository root) is created.
    """
    mgr = manager or WorkspaceManager()
    return DictationSession.start(
        mgr,
        workspace_id=workspace_id,
        session_id=session_id,
        participants=participants,
        description=description,
    )

__all__ = ["DictationSession", "DictationTurn", "start_session"]
