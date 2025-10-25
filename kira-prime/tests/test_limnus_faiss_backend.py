import json
import os
from pathlib import Path

import pytest

faiss = pytest.importorskip("faiss")

from agents.limnus.limnus_agent import LimnusAgent


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_faiss_backend_registers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KIRA_VECTOR_BACKEND", "faiss")
    monkeypatch.setenv("KIRA_FAISS_INDEX", str(tmp_path / "state" / "limnus.faiss"))
    monkeypatch.setenv("KIRA_FAISS_META", str(tmp_path / "state" / "limnus.faiss.meta.json"))
    lim = LimnusAgent(root=tmp_path)
    lim.cache("I love driving my car", layer="L2", tags=["veh"])
    lim.cache("My automobile is red", layer="L2", tags=["veh"])
    lim.cache("The weather is nice", layer="L2", tags=["weather"])
    stat = lim.reindex(backend="faiss")
    assert stat["ok"] is True
    assert stat["backend"] == "faiss"
    output = lim.recall(query="vehicle transportation", limit=3)
    payload = json.loads(output.splitlines()[-1])
    assert payload["matches"] >= 2
    assert payload["results"][0]["similarity"] > 0.2


def test_faiss_fallback_if_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KIRA_VECTOR_BACKEND", "faiss")
    monkeypatch.setenv("KIRA_FAISS_INDEX", str(tmp_path / "state" / "limnus.faiss"))
    monkeypatch.setenv("KIRA_FAISS_META", str(tmp_path / "state" / "limnus.faiss.meta.json"))
    monkeypatch.setattr("memory.vector_store.faiss", None)
    monkeypatch.setattr("memory.vector_store.np", None)
    lim = LimnusAgent(root=tmp_path)
    assert lim.vector_store.backend_name != "faiss"
