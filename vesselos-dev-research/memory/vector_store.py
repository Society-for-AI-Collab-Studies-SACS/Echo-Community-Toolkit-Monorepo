from __future__ import annotations

"""Semantic vector store utilities for Limnus memories."""

import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from interface.logger import log_event

try:  # optional dependency
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional
    faiss = None  # type: ignore

try:  # optional dependency
    from sklearn.feature_extraction.text import HashingVectorizer  # type: ignore
except Exception:  # pragma: no cover - optional
    HashingVectorizer = None  # type: ignore

try:  # optional dependency
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
except Exception:  # pragma: no cover
    TfidfVectorizer = None  # type: ignore

try:  # optional dependency
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore

try:  # optional dependency
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - optional
    np = None  # type: ignore

try:  # optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


STATE_DIR = Path(__file__).resolve().parents[1] / "state"
VECTOR_DIR = STATE_DIR / "vector_store"
VECTOR_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE = VECTOR_DIR / "limnus_vectors.json"
CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
CONFIG_FILE = CONFIG_DIR / "memory.yaml"
DEFAULT_DIMENSIONS = 384
FAISS_INDEX_FILE = STATE_DIR / "limnus.faiss"
FAISS_META_FILE = STATE_DIR / "limnus.faiss.meta.json"


class FaissUnavailable(RuntimeError):
    """Raised when FAISS backend is requested but dependencies are missing."""

    pass


def _load_config() -> Dict[str, Any]:
    if not (yaml and CONFIG_FILE.exists()):
        return {}
    try:
        return yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
    except Exception:  # pragma: no cover - config optional
        return {}


@dataclass
class VectorEntry:
    """Stored vector plus associated metadata."""

    id: str
    text: str
    vector: List[float]
    metadata: Dict[str, str]


class FaissIndex:
    """Thin wrapper around a FAISS index with ID bookkeeping."""

    def __init__(self, dims: int, index_path: Path, meta_path: Path) -> None:
        if faiss is None or np is None:
            raise FaissUnavailable("faiss (and numpy) are required for the FAISS backend")
        self.index_path = index_path
        self.meta_path = meta_path
        self.dims = dims
        self._index = faiss.IndexFlatIP(dims)
        self.ids: List[str] = []
        self._load()

    # ------------------------------------------------------------------ helpers
    def _reset(self, dims: Optional[int] = None) -> None:
        if dims is not None and dims > 0:
            self.dims = dims
        self._index = faiss.IndexFlatIP(self.dims)
        self.ids = []

    def _load(self) -> None:
        if not (self.index_path.exists() and self.meta_path.exists()):
            return
        try:
            self._index = faiss.read_index(str(self.index_path))
            self.dims = self._index.d
            meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
            raw_ids = meta.get("ids", [])
            self.ids = [str(item) for item in raw_ids if isinstance(item, str)]
        except Exception as exc:  # pragma: no cover - defensive
            log_event("vector_store", "faiss_load_error", {"error": str(exc)}, status="warn")
            self._reset()

    def _save(self) -> None:
        if not self.ids:
            for path in (self.index_path, self.meta_path):
                try:
                    if path.exists():
                        path.unlink()
                except Exception:  # pragma: no cover - best effort cleanup
                    pass
            return
        try:
            faiss.write_index(self._index, str(self.index_path))
            payload = {"ids": self.ids, "dim": self.dims}
            self.meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as exc:  # pragma: no cover - defensive
            log_event("vector_store", "faiss_save_error", {"error": str(exc)}, status="error")

    # ------------------------------------------------------------------- public
    def rebuild(self, entries: Dict[str, VectorEntry]) -> None:
        ordered = [(key, entry) for key, entry in entries.items() if entry.vector]
        if not ordered:
            self._reset()
            self._save()
            return
        dims = len(ordered[0][1].vector)
        if dims <= 0:
            self._reset()
            self._save()
            return
        if dims != self.dims:
            self._reset(dims=dims)
        matrix = np.array([entry.vector for _, entry in ordered], dtype="float32")
        if matrix.size > 0:
            faiss.normalize_L2(matrix)
        self._index.reset()
        self._index.add(matrix)
        self.ids = [key for key, _ in ordered]
        self._save()

    def search(self, query_vector: List[float], top_k: int) -> List[tuple[float, str]]:
        if not self.ids:
            return []
        dims = len(query_vector)
        if dims != self._index.d:
            raise ValueError(f"Query dimensions ({dims}) do not match FAISS index ({self._index.d})")
        query = np.array([query_vector], dtype="float32")
        faiss.normalize_L2(query)
        limit = min(top_k, len(self.ids))
        scores, indices = self._index.search(query, limit)
        hits: List[tuple[float, str]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.ids):
                continue
            hits.append((float(score), self.ids[idx]))
        return hits


class BaseBackend:
    def embed(self, text: str) -> List[float]:  # pragma: no cover - protocol
        raise NotImplementedError

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]


class HashBackend(BaseBackend):
    """Pure Python hashing embedder (dependency-free)."""

    def __init__(self, dims: int = DEFAULT_DIMENSIONS) -> None:
        self.dims = dims

    def embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dims
        for token in text.lower().split():
            idx = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dims
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class SklearnHashBackend(BaseBackend):
    """HashingVectorizer backend (requires scikit-learn)."""

    def __init__(self, dims: int = DEFAULT_DIMENSIONS) -> None:
        if HashingVectorizer is None:  # pragma: no cover - defensive
            raise RuntimeError("HashingVectorizer unavailable")
        self.vectorizer = HashingVectorizer(
            n_features=dims,
            alternate_sign=False,
            norm="l2",
        )

    def embed(self, text: str) -> List[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        matrix = self.vectorizer.transform(texts)
        return matrix.toarray().tolist()


class TFIDFBackend(BaseBackend):
    def __init__(self, dims: int = DEFAULT_DIMENSIONS) -> None:
        if TfidfVectorizer is None:  # pragma: no cover - defensive
            raise RuntimeError("TfidfVectorizer unavailable")
        self.vectorizer = TfidfVectorizer(max_features=dims)

    def embed(self, text: str) -> List[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        matrix = self.vectorizer.fit_transform(texts)
        return matrix.toarray().tolist()


class SBERTBackend(BaseBackend):
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, model_name: Optional[str] = None) -> None:
        if SentenceTransformer is None:  # pragma: no cover - defensive
            raise RuntimeError("SentenceTransformer unavailable")
        self.model_name = model_name or self.DEFAULT_MODEL
        try:
            self.model = SentenceTransformer(self.model_name)
        except Exception as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"Unable to load SentenceTransformer: {exc}") from exc

    def embed(self, text: str) -> List[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        vectors = self.model.encode(texts, show_progress_bar=False)
        return [vec.tolist() for vec in vectors]


class Embedder:
    """Selects the best available backend for text embeddings."""

    def __init__(self, dims: int = DEFAULT_DIMENSIONS, backend: Optional[str] = None) -> None:
        cfg = _load_config().get("embedding", {})
        backend = (backend or os.getenv("KIRA_VECTOR_BACKEND") or cfg.get("backend"))
        backend = str(backend).lower() if backend else self._auto_backend()
        model_name = os.getenv("KIRA_VECTOR_MODEL") or cfg.get("model_name")

        if backend == "tfidf" and TfidfVectorizer is not None:
            self.impl = TFIDFBackend(dims)
            self.backend_name = "tfidf"
        elif backend == "faiss":
            if SentenceTransformer is not None:
                self.impl = SBERTBackend(model_name=model_name)
                self.backend_name = "faiss"
            else:  # pragma: no cover - fallback
                self.impl = HashBackend(dims)
                self.backend_name = "hash"
        elif backend in {"sbert", "sentence-bert", "sentence_transformer"} and SentenceTransformer is not None:
            self.impl = SBERTBackend(model_name=model_name)
            self.backend_name = "sbert"
        elif backend == "sklearn-hash" and HashingVectorizer is not None:
            self.impl = SklearnHashBackend(dims)
            self.backend_name = "sklearn-hash"
        else:
            self.impl = HashBackend(dims)
            self.backend_name = "hash"

    def embed(self, text: str) -> List[float]:
        return self.impl.embed(text)

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        return self.impl.embed_many(texts)

    # ------------------------------------------------------------------ helpers
    def _auto_backend(self) -> str:
        # Preferred order: SBERT -> TF-IDF -> sklearn hash -> fallback hash
        if SentenceTransformer is not None:
            return "sbert"
        if TfidfVectorizer is not None:
            return "tfidf"
        if HashingVectorizer is not None:
            return "sklearn-hash"
        return "hash"


class VectorStore:
    """Persists memory embeddings for semantic recall."""

    def __init__(
        self,
        index_file: Path = INDEX_FILE,
        dims: int = DEFAULT_DIMENSIONS,
        backend: Optional[str] = None,
    ) -> None:
        self.index_file = index_file
        requested_backend = (backend or os.getenv("KIRA_VECTOR_BACKEND") or "").strip().lower()
        embed_backend = "sbert" if requested_backend == "faiss" else backend
        self.embedder = Embedder(dims=dims, backend=embed_backend)
        self.index_backend = "memory"
        self.faiss_index: Optional[FaissIndex] = None
        self._requested_backend = requested_backend or self.embedder.backend_name
        if requested_backend == "faiss":
            index_path = Path(os.getenv("KIRA_FAISS_INDEX") or FAISS_INDEX_FILE)
            meta_path = Path(os.getenv("KIRA_FAISS_META") or FAISS_META_FILE)
            try:
                self.faiss_index = FaissIndex(dims=dims, index_path=index_path, meta_path=meta_path)
                self.index_backend = "faiss"
            except FaissUnavailable as exc:
                log_event(
                    "vector_store",
                    "faiss_unavailable",
                    {"error": str(exc), "index_path": str(index_path), "meta_path": str(meta_path)},
                    status="warn",
                )
                self.faiss_index = None
            except Exception as exc:  # pragma: no cover - defensive
                log_event(
                    "vector_store",
                    "faiss_init_error",
                    {"error": str(exc), "index_path": str(index_path), "meta_path": str(meta_path)},
                    status="error",
                )
                self.faiss_index = None
        self.backend_name = "faiss" if self.faiss_index else self.embedder.backend_name
        self.entries: Dict[str, VectorEntry] = {}
        self._load()
        self._refresh_embeddings()

    def _load(self) -> None:
        if not self.index_file.exists():
            return
        try:
            raw = json.loads(self.index_file.read_text(encoding="utf-8"))
            for item in raw:
                entry = VectorEntry(
                    id=item["id"],
                    text=item.get("text", ""),
                    vector=item.get("vector", []),
                    metadata=item.get("metadata", {}),
                )
                self.entries[entry.id] = entry
        except Exception as exc:  # pragma: no cover - defensive
            log_event("vector_store", "load_error", {"error": str(exc)}, status="error")
            self.entries.clear()

    def _save(self) -> None:
        payload = [
            {
                "id": entry.id,
                "text": entry.text,
                "vector": entry.vector,
                "metadata": entry.metadata,
            }
            for entry in self.entries.values()
        ]
        self.index_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def upsert(
        self,
        text: str,
        entry_id: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        entry = self.entries.get(entry_id)
        if entry:
            entry.text = text
            if metadata:
                entry.metadata.update(metadata)
        else:
            entry = VectorEntry(entry_id, text, [], metadata or {})
            self.entries[entry_id] = entry
        self._refresh_embeddings()
        log_event("vector_store", "upsert", {"id": entry_id, "metadata": metadata or {}})

    def ensure_indexed(
        self,
        items: Iterable[Dict[str, str]],
        *,
        text_key: str = "text",
        id_key: str = "id",
    ) -> None:
        changed = False
        for item in items:
            if not isinstance(item, dict):
                continue
            entry_id = item.get(id_key) or item.get("ts") or item.get("timestamp")
            text = item.get(text_key) or item.get("text")
            if not entry_id or not text:
                continue
            tags = item.get("tags") or []
            metadata = {"tags": ",".join(tags) if isinstance(tags, list) else str(tags)}
            existing = self.entries.get(entry_id)
            if existing:
                updated = False
                if existing.text != text:
                    existing.text = text
                    updated = True
                if metadata and metadata != existing.metadata:
                    existing.metadata.update(metadata)
                    updated = True
                if updated:
                    changed = True
                continue
            self.entries[entry_id] = VectorEntry(entry_id, text, [], metadata)
            changed = True
        if changed:
            self._refresh_embeddings()

    def semantic_search(self, text: str, top_k: int = 3) -> List[tuple[float, VectorEntry]]:
        if not text or not self.entries:
            return []
        query_vec = self.embedder.embed(text)
        if self.faiss_index:
            try:
                hits = self.faiss_index.search(query_vec, top_k)
                results: List[tuple[float, VectorEntry]] = []
                for score, entry_id in hits:
                    entry = self.entries.get(entry_id)
                    if entry:
                        results.append((score, entry))
                if results:
                    return results
            except Exception as exc:  # pragma: no cover - defensive
                log_event(
                    "vector_store",
                    "faiss_search_error",
                    {"error": str(exc), "index_path": str(self.faiss_index.index_path)},
                    status="error",
                )
                self.faiss_index = None
                self.index_backend = "memory"
                self.backend_name = self.embedder.backend_name

        def normalize(vec: List[float]) -> List[float]:
            length = math.sqrt(sum(v * v for v in vec)) or 1.0
            return [v / length for v in vec]

        q_norm = normalize(query_vec)

        def similarity(entry: VectorEntry) -> float:
            if not entry.vector:
                return 0.0
            v_norm = normalize(entry.vector)
            return float(sum(a * b for a, b in zip(q_norm, v_norm)))

        ranked = sorted(self.entries.values(), key=similarity, reverse=True)
        return [(similarity(entry), entry) for entry in ranked[:top_k]]

    def _refresh_embeddings(self) -> None:
        if not self.entries:
            self._save()
            self._sync_faiss_index()
            return
        texts = [entry.text for entry in self.entries.values()]
        vectors = self.embedder.embed_many(texts)
        for entry, vec in zip(self.entries.values(), vectors):
            entry.vector = [float(v) for v in vec]
        self._save()
        self._sync_faiss_index()

    def delete(self, entry_id: str) -> None:
        if entry_id in self.entries:
            del self.entries[entry_id]
            self._save()
            self._sync_faiss_index()
            log_event("vector_store", "delete", {"id": entry_id})

    def _sync_faiss_index(self) -> None:
        if not self.faiss_index:
            return
        try:
            self.faiss_index.rebuild(self.entries)
        except Exception as exc:  # pragma: no cover - defensive
            log_event(
                "vector_store",
                "faiss_rebuild_error",
                {
                    "error": str(exc),
                    "index_path": str(self.faiss_index.index_path),
                    "meta_path": str(self.faiss_index.meta_path),
                },
                status="error",
            )
            self.faiss_index = None
            self.index_backend = "memory"
            self.backend_name = self.embedder.backend_name
