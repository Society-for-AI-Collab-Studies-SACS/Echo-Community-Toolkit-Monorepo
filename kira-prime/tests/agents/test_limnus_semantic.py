import json
import os
from pathlib import Path

import pytest


from agents.limnus.limnus_agent import LimnusAgent


def run_recall(agent: LimnusAgent, query: str | None = None, **kwargs):
    """Helper that splits summary/JSON from recall output."""
    output = agent.recall(query, **kwargs)
    lines = output.splitlines()
    assert len(lines) >= 2
    summary = lines[0]
    payload = json.loads(lines[1])
    return summary, payload


@pytest.fixture
def temp_state(tmp_path, monkeypatch):
    """Place Limnus state (memory/vector store/logs) in a temp directory."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "state" / "vector_store").mkdir(parents=True)
    yield tmp_path


@pytest.mark.skipif(
    os.environ.get("CI") and os.environ.get("CI_SKIP_SBERT"),
    reason="SBERT runtime disabled in CI",
)
def test_semantic_recall_prefers_matching_entry(temp_state, monkeypatch):
    os.environ.setdefault("KIRA_VECTOR_BACKEND", "sbert")
    agent = LimnusAgent(Path(temp_state).resolve())
    agent.cache("The vessel sails at dawn.")
    agent.cache("Consent to bloom in the garden.")

    summary, payload = run_recall(agent, "ship at sunrise")

    assert payload["status"] == "ok"
    assert payload["matches"] >= 1
    first_text = payload["results"][0]["text"]
    assert "vessel" in first_text
    assert "Cons" not in first_text
    similarity = payload["results"][0]["similarity"]
    if similarity is not None:
        assert similarity >= 0.2


def test_semantic_recall_fallback_hash_backend(temp_state):
    os.environ["KIRA_VECTOR_BACKEND"] = "hash"
    agent = LimnusAgent(Path(temp_state).resolve())
    agent.cache("The vessel sails at dawn.")
    summary, payload = run_recall(agent, "ship at sunrise")

    assert payload["status"] == "ok"
    assert payload["matches"] >= 1
    assert agent.vector_store.embedder.backend_name == "hash"
    assert "vessel" in payload["results"][0]["text"]


def test_layer_filtering_returns_only_requested_layer(temp_state):
    agent = LimnusAgent(Path(temp_state).resolve())
    agent.cache("Layer one memory", layer="L1")
    agent.cache("Layer two memory", layer="L2")
    agent.cache("Layer three memory", layer="L3")

    summary, payload = run_recall(agent, None, layer="L2")
    assert payload["matches"] == 1
    assert payload["results"][0]["layer"] == "L2"


def test_auto_promote_raises_layer_over_threshold(temp_state):
    agent = LimnusAgent(Path(temp_state).resolve())
    agent.cache("Promote me", layer="L1")

    for _ in range(12):
        agent.recall("Promote", limit=5)

    promoted = agent.auto_promote(threshold=10)
    assert promoted >= 1
    # Validate status reflects promotion
    status = agent.status()
    assert status["by_layer"]["L1"] == 0
    assert status["by_layer"]["L2"] >= 1 or status["by_layer"]["L3"] >= 1


def test_cache_persists_vector_field(temp_state):
    agent = LimnusAgent(Path(temp_state).resolve())
    agent.cache("Vector memory", layer="L2")

    if agent.embedding_model is None:
        pytest.skip("Semantic embedder unavailable; vector persistence not applicable")

    mem_path = Path(temp_state) / "state" / "limnus_memory.json"
    raw = json.loads(mem_path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        entries = raw.get("entries", [])
    else:
        entries = raw
    assert entries, "Expected at least one memory entry"
    vector = entries[0].get("vector")
    assert isinstance(vector, list) and vector, "Vector embedding should be stored as list"
