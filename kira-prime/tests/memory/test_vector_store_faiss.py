import pytest

from memory import vector_store
from memory.vector_store import VectorStore


@pytest.mark.skipif(
    vector_store.faiss is None or vector_store.np is None, reason="FAISS backend optional"
)
def test_faiss_backend_registers(tmp_path, monkeypatch):
    index_file = tmp_path / "index.json"
    faiss_index_path = tmp_path / "index.faiss"
    faiss_meta_path = tmp_path / "index.faiss.meta.json"
    monkeypatch.setenv("KIRA_VECTOR_BACKEND", "faiss")
    monkeypatch.setenv("KIRA_FAISS_INDEX", str(faiss_index_path))
    monkeypatch.setenv("KIRA_FAISS_META", str(faiss_meta_path))
    store = VectorStore(index_file=index_file)
    store.upsert("hello world", "m1")
    store.upsert("goodbye universe", "m2")
    results = store.semantic_search("hello")
    assert results, "FAISS backend should return at least one result"
    top_entry = results[0][1]
    assert top_entry.id in {"m1", "m2"}
    assert store.backend_name == "faiss"


def test_faiss_backend_falls_back_without_dependencies(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_store, "faiss", None)
    monkeypatch.setattr(vector_store, "np", None)
    index_file = tmp_path / "index.json"
    store = VectorStore(index_file=index_file, backend="faiss")
    store.upsert("fallback testing", "f1")
    results = store.semantic_search("fallback")
    assert results
    assert store.faiss_index is None
    assert store.index_backend == "memory"
