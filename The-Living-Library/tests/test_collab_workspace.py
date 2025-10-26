from __future__ import annotations

import json
from pathlib import Path

import pytest
pytest.importorskip('httpx')
from fastapi.testclient import TestClient

from library_core.collab import CollaborationConfig, create_app
from library_core.dictation.pipeline import MRPPipeline
from workspace.manager import WorkspaceManager


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_websocket_dictation_hydrates_workspace(tmp_path: Path) -> None:
    manager = WorkspaceManager(root=tmp_path)
    config = CollaborationConfig(redis_url=None, postgres_dsn=None)
    app = create_app(manager=manager, config=config)

    with TestClient(app) as client:
        with client.websocket_connect("/ws?workspaceId=alpha&userId=alice&sessionId=demo") as ws:
            ws.send_json({"type": "dictation", "text": "Seeds take root."})
            ws.send_json({"type": "ping"})
            assert ws.receive_json()["type"] == "pong"

    events_path = tmp_path / "workspaces" / "alpha" / "collab" / "events.jsonl"
    events = _read_jsonl(events_path)
    assert any(entry["event_type"] == "dictation" for entry in events)

    transcript_path = tmp_path / "workspaces" / "alpha" / "logs" / "dictation_demo.jsonl"
    transcript = _read_jsonl(transcript_path)
    assert any(turn["text"] == "Seeds take root." for turn in transcript)


def test_mrp_endpoint_runs_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    manager = WorkspaceManager(root=tmp_path)
    config = CollaborationConfig(redis_url=None, postgres_dsn=None)
    app = create_app(manager=manager, config=config)

    outputs: list[Path] = []

    def fake_run(self: MRPPipeline, run_schema: bool = True, run_kira_validation: bool = False) -> Path:
        out = self.session.workspace.path / "outputs" / "mrp" / self.session.session_id
        out.mkdir(parents=True, exist_ok=True)
        outputs.append(out)
        return out

    monkeypatch.setattr(MRPPipeline, "run", fake_run, raising=False)

    with TestClient(app) as client:
        with client.websocket_connect("/ws?workspaceId=alpha&userId=alice&sessionId=demo") as ws:
            ws.send_json({"type": "dictation", "text": "Run the cycle."})

        response = client.post(
            "/api/workspaces/alpha/mrp",
            json={"sessionId": "demo", "runSchema": False, "runValidation": False},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workspaceId"] == "alpha"
    assert payload["sessionId"] == "demo"
    assert Path(payload["outputPath"]).exists()
    assert outputs and outputs[0] == Path(payload["outputPath"])

    events_path = tmp_path / "workspaces" / "alpha" / "collab" / "events.jsonl"
    events = _read_jsonl(events_path)
    assert any(entry["event_type"] == "mrp_complete" for entry in events)

    meta_path = tmp_path / "workspaces" / "alpha" / "logs" / "dictation_demo.meta.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    assert metadata["mrp_output"] == payload["outputPath"]
