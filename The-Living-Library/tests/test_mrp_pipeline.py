from __future__ import annotations

from pathlib import Path

import pytest

from library_core.dictation import DictationSession
from library_core.dictation.pipeline import MRPPipeline
from workspace.manager import WorkspaceManager


@pytest.fixture()
def temp_session(tmp_path: Path) -> DictationSession:
    manager = WorkspaceManager(root=tmp_path)
    return DictationSession.start(manager, "omega", session_id="s42")


def test_pipeline_invokes_scripts(monkeypatch, temp_session: DictationSession) -> None:
    issued_commands: list[tuple[tuple[str, ...], Path | None, bool]] = []
    copied_dirs: list[tuple[Path, Path]] = []

    pipeline = MRPPipeline(temp_session)

    def fake_run_command(cmd, *, cwd=None, check=True):
        issued_commands.append((tuple(cmd), cwd, check))

        class DummyResult:
            returncode = 0

        return DummyResult()

    def fake_copy_directory(src: Path, dst: Path) -> None:
        copied_dirs.append((src, dst))

    monkeypatch.setattr(MRPPipeline, "_run_command", staticmethod(fake_run_command))
    monkeypatch.setattr(MRPPipeline, "_copy_directory", staticmethod(fake_copy_directory))

    output_path = pipeline.run(run_schema=True, copy_templates=True, run_kira_validation=True)

    assert issued_commands[0][0] == ("python3", "src/schema_builder.py")
    assert issued_commands[1][0] == ("python3", "src/generate_chapters.py")
    assert issued_commands[2][0] == ("python3", "vesselos.py", "validate")
    assert "outputs/mrp" in str(output_path)
    assert temp_session.metadata()["mrp_output"] == str(output_path)
    assert len(copied_dirs) == 2
