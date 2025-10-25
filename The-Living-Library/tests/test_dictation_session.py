from __future__ import annotations

import json
from pathlib import Path

from library_core.dictation import DictationSession, start_session
from workspace.manager import WorkspaceManager


def test_session_start_creates_files(tmp_path: Path) -> None:
    manager = WorkspaceManager(root=tmp_path)
    session = start_session("alpha", manager=manager, session_id="demo", participants=["user", "agent"])

    assert session.log_path.exists()

    meta_content = json.loads(session.meta_path.read_text())
    assert meta_content["session_id"] == "demo"
    assert meta_content["participants"] == ["user", "agent"]


def test_record_turn_appends(tmp_path: Path) -> None:
    manager = WorkspaceManager(root=tmp_path)
    session = DictationSession.start(manager, "beta", session_id="s1", participants=["user", "agent"])

    session.record_turn("user", "Hello agent", tags={"stage": "scatter"})
    session.record_turn("agent", "Greetings traveller")

    turns = list(session.iter_turns())
    assert len(turns) == 2
    assert turns[0].speaker == "user"
    assert turns[0].tags == {"stage": "scatter"}
    assert turns[1].speaker == "agent"
