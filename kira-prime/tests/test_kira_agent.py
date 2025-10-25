from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from agents.kira.kira_agent import KiraAgent


@pytest.fixture()
def kira_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()

    # Basic structure expected by Limnus/Kira helpers
    for rel in ("state", "frontend/assets", "pipeline/state", "dist"):
        dir_path = root / rel
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / ".gitkeep").touch()

    (root / "README.md").write_text("# test repo\n", encoding="utf-8")

    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True)

    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=root, check=True)
    subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=root, check=True, capture_output=True)

    # Pre-create empty log files so log_event writes succeed quietly
    (root / "pipeline" / "state" / "voice_log.json").write_text("", encoding="utf-8")
    return root


def test_push_dry_run_reports_dirty(kira_repo: Path) -> None:
    (kira_repo / "new_file.txt").write_text("payload", encoding="utf-8")
    agent = KiraAgent(kira_repo)
    result = agent.push(run=False, message="test")
    assert result == "dry-run"


def test_push_returns_no_changes_when_clean(kira_repo: Path) -> None:
    agent = KiraAgent(kira_repo)
    result = agent.push(run=True, message="test")
    assert result in {"no-changes", "pushed"}


def test_publish_dry_run(kira_repo: Path) -> None:
    agent = KiraAgent(kira_repo)
    result = agent.publish(run=False, release=False)
    assert result == "dry-run"


def test_publish_with_release_uses_gh(monkeypatch: pytest.MonkeyPatch, kira_repo: Path) -> None:
    # Ensure there is a change for the commit performed during publish.
    (kira_repo / "state" / "sync.txt").write_text("update", encoding="utf-8")

    # Stub gh CLI to simulate successful release creation.
    bin_dir = kira_repo / "tmp-bin"
    bin_dir.mkdir()
    gh_stub = bin_dir / "gh"
    gh_stub.write_text("#!/usr/bin/env bash\nprintf 'https://example.com/release\\n'\n", encoding="utf-8")
    gh_stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    agent = KiraAgent(kira_repo)
    result = agent.publish(run=True, release=True, tag="vtest-ci")
    assert result == "published"

    artifacts = list((kira_repo / "dist").glob("codex_release_*"))
    assert artifacts, "Expected packaged artifact in dist/"


def test_validate_returns_issue_report(kira_repo: Path) -> None:
    agent = KiraAgent(kira_repo)
    result = agent.validate()
    assert isinstance(result, dict)
    assert "passed" in result
    assert isinstance(result["issues"], list)
