from __future__ import annotations

"""Limnus Agent (Memory Engine & Ledger Steward)

Commands:
- cache <text>
- recall [query]
- commit_block(kind, data)
- encode_ledger / decode_ledger (stubs)

Maintains:
- state/limnus_memory.json (list of {ts, text, tags})
- state/ledger.json (hash-chained blocks)
"""
import hashlib
import json
import math
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from interface.logger import log_event
from memory.vector_store import VectorStore

try:  # optional dependency
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore

try:  # optional dependency
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _parse_iso(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


TTL_BY_LAYER: Dict[str, Optional[int]] = {"L1": 3600, "L2": 86400, "L3": None}
DEFAULT_LAYER = "L2"


@dataclass
class Block:
    ts: str
    kind: str
    data: Dict[str, Any]
    prev: str
    hash: str


class LimnusAgent:
    """Memory steward with semantic recall and ledger management."""

    _shared_embedder = None
    _embedder_error: Optional[str] = None
    def __init__(self, root: Path):
        self.root = root
        self.mem_path = self.root / "state" / "limnus_memory.json"
        self.ledger_path = self.root / "state" / "ledger.json"
        self.vector_store = VectorStore()
        self.embedding_model = self._load_embedding_model()
        for p in [self.mem_path, self.ledger_path]:
            p.parent.mkdir(parents=True, exist_ok=True)
        if not self.mem_path.exists():
            self.mem_path.write_text("[]", encoding="utf-8")
        if not self.ledger_path.exists():
            self._init_ledger()
        self._backfill_vector_index()

    def _init_ledger(self) -> None:
        genesis = {"ts": _ts(), "kind": "genesis", "data": {"anchor": "I return as breath."}, "prev": ""}
        content = json.dumps(genesis, sort_keys=True)
        genesis["hash"] = _sha256(content)
        self.ledger_path.write_text(json.dumps([genesis], indent=2), encoding="utf-8")

    def _read_ledger(self) -> List[Dict[str, Any]]:
        return json.loads(self.ledger_path.read_text(encoding="utf-8"))

    def _write_ledger(self, blocks: List[Dict[str, Any]]) -> None:
        self.ledger_path.write_text(json.dumps(blocks, indent=2), encoding="utf-8")

    def cache(self, text: str, layer: str = DEFAULT_LAYER, tags: Optional[List[str]] = None) -> str:
        layer = (layer or DEFAULT_LAYER).upper()
        if layer not in TTL_BY_LAYER:
            raise ValueError(f"Invalid memory layer: {layer}")
        tags = [t for t in (tags or []) if t]
        memories, wrapped = self._load_active_memory()
        ts = _ts()
        entry_id = f"mem_{uuid.uuid4().hex[:8]}"
        embedding = self._embed(text)
        entry: Dict[str, Any] = {
            "id": entry_id,
            "ts": ts,
            "timestamp": ts,
            "text": text,
            "layer": layer,
            "tags": tags,
            "ttl": TTL_BY_LAYER[layer],
            "access_count": 0,
        }
        if embedding is not None:
            entry["embedding"] = embedding
            entry["vector"] = list(embedding)
        memories.append(entry)
        self._write_memory(memories, wrapped)
        metadata = {"layer": layer, "tags": ",".join(tags)}
        self.vector_store.upsert(text, entry_id=entry_id, metadata=metadata)
        payload = {
            "status": "ok",
            "cached": True,
            "id": entry_id,
            "layer": layer,
            "tags": tags,
            "ts": ts,
        }
        log_event("limnus", "cache", payload)
        summary = f"💾 Limnus cached memory {entry_id} ({layer})."
        return summary + "\n" + json.dumps(payload)

    def recall(
        self,
        query: Optional[str] = None,
        *,
        tags: Optional[List[str]] = None,
        layer: Optional[str] = None,
        limit: int = 5,
        min_similarity: float = 0.0,
    ) -> str:
        memories, wrapped = self._load_active_memory()
        tags_filter = {t for t in (tags or []) if t}
        layer_filter = layer.upper() if layer else None
        if layer_filter and layer_filter not in TTL_BY_LAYER:
            raise ValueError(f"Invalid layer: {layer}")

        candidates = []
        for entry in memories:
            if layer_filter and entry.get("layer", DEFAULT_LAYER) != layer_filter:
                continue
            if tags_filter:
                entry_tags = {t for t in entry.get("tags", []) if t}
                if tags_filter.isdisjoint(entry_tags):
                    continue
            candidates.append(entry)

        if not query:
            subset = candidates[: max(1, limit)]
            payload = {
                "status": "ok",
                "matches": len(subset),
                "query": None,
                "results": [
                    {
                        "id": entry.get("id"),
                        "ts": entry.get("ts") or entry.get("timestamp"),
                        "text": entry.get("text"),
                        "layer": entry.get("layer", DEFAULT_LAYER),
                        "tags": entry.get("tags", []),
                        "similarity": None,
                    }
                    for entry in subset
                ],
            }
            summary = f"✅ Limnus listed {len(subset)} memories (filtered {len(candidates)})."
            log_event("limnus", "recall", payload)
            return summary + "\n" + json.dumps(payload)

        keyword_hits = self._keyword_search(candidates, query)
        query_vec = self._embed(query)
        semantic_hits: List[tuple[float, Dict[str, Any]]] = []

        if query_vec is not None:
            semantic_hits = self._semantic_search(candidates, query_vec, top_k=limit * 3)
        elif not keyword_hits:
            fallback_hits = self.vector_store.semantic_search(query, top_k=limit * 3)
            lookup = {
                entry.get("id") or entry.get("ts") or entry.get("timestamp"): entry for entry in candidates
            }
            for score, vec_entry in fallback_hits:
                match = lookup.get(vec_entry.id)
                if match is None:
                    text = getattr(vec_entry, "text", None)
                    if text:
                        for entry in candidates:
                            if entry.get("text") == text:
                                match = entry
                                break
                if match:
                    semantic_hits.append((score, match))

        combined = self._combine_hits(keyword_hits, semantic_hits, top_k=limit * 3)
        scored: Dict[str, tuple[float, Dict[str, Any]]] = {}

        def add_entry(entry: Dict[str, Any], score: float) -> None:
            entry_id = entry.get("id") or entry.get("ts") or entry.get("timestamp")
            if not entry_id:
                return
            existing = scored.get(entry_id)
            if not existing or score > existing[0]:
                scored[entry_id] = (score, entry)

        for entry in keyword_hits:
            add_entry(entry, 0.05)
        for score, entry in semantic_hits:
            add_entry(entry, float(score))

        final_results: List[tuple[float, Dict[str, Any]]] = []
        for entry_id, (score, entry) in scored.items():
            similarity = score
            entry_vec = self._entry_vector(entry)
            if query_vec is not None and entry_vec is not None:
                similarity = self._vector_similarity(query_vec, entry_vec)
            if query_vec is not None and similarity < min_similarity:
                continue
            entry["access_count"] = entry.get("access_count", 0) + 1
            final_results.append((similarity, entry))

        final_results.sort(key=lambda item: item[0], reverse=True)
        trimmed = final_results[: max(1, limit)]

        if trimmed:
            summary = f"✅ Limnus recalled {len(trimmed)} memories for '{query}'."
        else:
            summary = f"⚠️ Limnus found no memories for query '{query}'."

        results_payload = [
            {
                "id": entry.get("id"),
                "ts": entry.get("ts") or entry.get("timestamp"),
                "text": entry.get("text"),
                "layer": entry.get("layer", DEFAULT_LAYER),
                "tags": entry.get("tags", []),
                "similarity": float(score),
            }
            for score, entry in trimmed
        ]

        if trimmed:
            self._write_memory(memories, wrapped)

        top_score = float(trimmed[0][0]) if trimmed else 0.0
        payload = {
            "status": "ok",
            "matches": len(trimmed),
            "query": query,
            "results": results_payload,
            "top_score": top_score,
        }
        log_event("limnus", "recall", payload)
        return summary + "\n" + json.dumps(payload)

    def commit_block(self, kind: str, data: Dict[str, Any]) -> str:
        blocks = self._read_ledger()
        prev_hash = blocks[-1]["hash"] if blocks else ""
        block = {"ts": _ts(), "kind": kind, "data": data, "prev": prev_hash}
        block["hash"] = _sha256(json.dumps(block, sort_keys=True))
        blocks.append(block)
        self._write_ledger(blocks)
        log_event("limnus", "commit_block", {"kind": kind})
        return block["hash"]

    # Stubs for stego
    def encode_ledger(self, out_path: str | None = None) -> str:
        """Embed the ledger payload into a simple artifact.

        If Pillow is available, write a small PNG placeholder with the JSON
        stored in a sibling `.json` file. Otherwise, write the JSON to
        `frontend/assets/ledger.json`.
        Returns the path to the produced artifact.
        """
        assets = self.root / "frontend" / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        ledger_json = json.dumps(self._read_ledger(), ensure_ascii=False)
        # Always write JSON alongside
        json_path = assets / "ledger.json"
        json_path.write_text(ledger_json, encoding="utf-8")
        artifact = json_path
        try:
            from PIL import Image  # type: ignore

            img = Image.new("RGBA", (64, 64), (10, 14, 20, 255))
            png_path = assets / "ledger.png"
            img.save(png_path)
            artifact = png_path
        except Exception:
            # Pillow not available; JSON artifact only
            pass
        log_event("limnus", "encode_ledger", {"out": str(artifact)})
        return str(artifact)

    def decode_ledger(self, src: str | None = None) -> str:
        # Minimal: return current ledger JSON
        payload = json.dumps(self._read_ledger())
        log_event("limnus", "decode_ledger", {"src": src})
        return payload

    def reindex(self, backend: Optional[str] = None) -> Dict[str, Any]:
        """Rebuild the semantic vector index, optionally forcing a backend."""
        if backend:
            os.environ["KIRA_VECTOR_BACKEND"] = backend
        memories, wrapped = self._load_active_memory()
        requested_backend = os.getenv("KIRA_VECTOR_BACKEND")
        self.vector_store = VectorStore(backend=requested_backend)
        self.vector_store.ensure_indexed(memories, id_key="id")
        self._backfill_embeddings(memories, wrapped)
        current_status = self.status()
        log_event("limnus", "reindex", current_status)
        return {"ok": True, "backend": current_status.get("vector_backend"), "status": current_status}

    def _backfill_vector_index(self) -> None:
        """Ensure historic memories are represented in the vector index."""

        mem, wrapped = self._load_active_memory()
        self.vector_store.ensure_indexed(mem, id_key="id")
        self._backfill_embeddings(mem, wrapped)

    def _load_memory(self) -> tuple[List[Dict[str, Any]], bool]:
        raw = json.loads(self.mem_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "entries" in raw:
            return list(raw.get("entries", [])), True
        if isinstance(raw, list):
            return list(raw), False
        return [], False

    def _load_active_memory(self) -> tuple[List[Dict[str, Any]], bool]:
        mem, wrapped = self._load_memory()
        if not mem:
            return mem, wrapped
        now = datetime.now(timezone.utc).timestamp()
        keep: List[Dict[str, Any]] = []
        expired_ids: List[str] = []
        for entry in mem:
            ttl = entry.get("ttl")
            ts = entry.get("ts") or entry.get("timestamp")
            if ttl in (None, 0) or not ts:
                keep.append(entry)
                continue
            try:
                entry_time = _parse_iso(str(ts)).timestamp()
            except Exception:
                keep.append(entry)
                continue
            if (now - entry_time) <= float(ttl):
                keep.append(entry)
            else:
                entry_id = entry.get("id") or str(ts)
                expired_ids.append(entry_id)
        if expired_ids:
            self._write_memory(keep, wrapped)
            for entry_id in expired_ids:
                self.vector_store.delete(entry_id)
            log_event("limnus", "expire", {"count": len(expired_ids)})
        return keep, wrapped

    def _write_memory(self, entries: List[Dict[str, Any]], wrapped: bool) -> None:
        payload: Any = {"entries": entries} if wrapped else entries
        self.mem_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_embedding_model(self):
        if SentenceTransformer is None:
            return None
        if self.__class__._shared_embedder is not None:
            return self.__class__._shared_embedder
        if self.__class__._embedder_error:
            return None
        model_name = os.getenv("KIRA_SBERT_MODEL", "all-MiniLM-L6-v2")
        try:
            embedder = SentenceTransformer(model_name)
        except Exception as exc:  # pragma: no cover - defensive
            err = str(exc)
            self.__class__._embedder_error = err
            log_event("limnus", "embedding_model_error", {"error": err}, status="error")
            return None
        self.__class__._shared_embedder = embedder
        return embedder

    def _embed(self, text: str) -> Optional[List[float]]:
        if not text or self.embedding_model is None:
            return None
        try:
            vec = self.embedding_model.encode(text)
        except Exception as exc:  # pragma: no cover - defensive
            log_event("limnus", "embedding_error", {"error": str(exc)}, status="error")
            return None
        if np is not None:
            vec = np.asarray(vec, dtype=float)
            norm = np.linalg.norm(vec) or 1.0
            return (vec / norm).tolist()
        norm = math.sqrt(sum(float(v) * float(v) for v in vec)) or 1.0
        return [float(v) / norm for v in vec]

    def _keyword_search(self, memories: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        return [m for m in memories if q in m.get("text", "").lower()]

    def _semantic_search(
        self, memories: List[Dict[str, Any]], query_vec: List[float], top_k: int = 5
    ) -> List[tuple[float, Dict[str, Any]]]:
        results: List[tuple[float, Dict[str, Any]]] = []
        for entry in memories:
            vec = self._entry_vector(entry)
            if not isinstance(vec, list):
                continue
            score = self._vector_similarity(query_vec, vec)
            if score > 0:
                results.append((score, entry))
        results.sort(key=lambda item: item[0], reverse=True)
        return results[:top_k]

    def _combine_hits(
        self,
        keyword_hits: List[Dict[str, Any]],
        semantic_hits: List[tuple[float, Dict[str, Any]]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        combined: List[Dict[str, Any]] = []
        seen: set[str] = set()
        semantic_entries = [entry for _score, entry in semantic_hits]
        for entry in keyword_hits + semantic_entries:
            entry_id = entry.get("id") or entry.get("ts") or entry.get("timestamp")
            if entry_id and entry_id not in seen:
                combined.append(entry)
                seen.add(entry_id)
        return combined[:top_k]

    def _backfill_embeddings(self, memories: List[Dict[str, Any]], wrapped: bool) -> None:
        if self.embedding_model is None:
            return
        changed = False
        for entry in memories:
            if not isinstance(entry, dict):
                continue
            if "embedding" not in entry or not isinstance(entry["embedding"], list):
                embedding = self._embed(entry.get("text", ""))
                if embedding is not None:
                    entry["embedding"] = embedding
                    entry["vector"] = list(embedding)
                    changed = True
            elif "vector" not in entry or not isinstance(entry["vector"], list):
                vector = entry.get("embedding")
                if isinstance(vector, list):
                    entry["vector"] = list(vector)
                    changed = True
        if changed:
            self._write_memory(memories, wrapped)

    def _vector_similarity(self, u: List[float], v: List[float]) -> float:
        if np is not None:
            return float(np.dot(np.asarray(u, dtype=float), np.asarray(v, dtype=float)))
        return float(sum(float(a) * float(b) for a, b in zip(u, v)))

    def _entry_vector(self, entry: Dict[str, Any]) -> Optional[List[float]]:
        vec = entry.get("embedding")
        if isinstance(vec, list):
            return vec
        vec = entry.get("vector")
        if isinstance(vec, list):
            return vec
        return None

    def promote_memory(self, memory_id: str, to_layer: str) -> bool:
        target = (to_layer or DEFAULT_LAYER).upper()
        if target not in TTL_BY_LAYER:
            raise ValueError(f"Invalid layer: {to_layer}")
        memories, wrapped = self._load_active_memory()
        promoted = False
        for entry in memories:
            entry_ids = {
                entry.get("id"),
                entry.get("ts"),
                entry.get("timestamp"),
            }
            if memory_id not in entry_ids:
                continue
            old_layer = entry.get("layer", DEFAULT_LAYER)
            if old_layer == target:
                promoted = True
                break
            entry["layer"] = target
            entry["ttl"] = TTL_BY_LAYER[target]
            entry["access_count"] = entry.get("access_count", 0)
            entry_id = entry.get("id") or entry.get("ts") or entry.get("timestamp")
            text = entry.get("text", "")
            metadata = {"layer": target, "tags": ",".join(entry.get("tags", []))}
            if entry_id and text:
                self.vector_store.upsert(text, entry_id=entry_id, metadata=metadata)
            promoted = True
            log_event("limnus", "promote", {"id": entry_id or memory_id, "from": old_layer, "to": target})
            break
        if promoted:
            self._write_memory(memories, wrapped)
        return promoted

    def auto_promote(self, threshold: int = 10) -> int:
        memories, wrapped = self._load_active_memory()
        promoted = 0
        for entry in memories:
            count = entry.get("access_count", 0)
            layer = entry.get("layer", DEFAULT_LAYER)
            if count < threshold:
                continue
            if layer == "L1":
                target = "L2"
            elif layer == "L2":
                target = "L3"
            else:
                continue
            entry["layer"] = target
            entry["ttl"] = TTL_BY_LAYER[target]
            entry_id = entry.get("id") or entry.get("ts") or entry.get("timestamp")
            text = entry.get("text", "")
            metadata = {"layer": target, "tags": ",".join(entry.get("tags", []))}
            if entry_id and text:
                self.vector_store.upsert(text, entry_id=entry_id, metadata=metadata)
            promoted += 1
        if promoted:
            self._write_memory(memories, wrapped)
            log_event("limnus", "auto_promote", {"count": promoted, "threshold": threshold})
        return promoted

    def status(self) -> Dict[str, Any]:
        memories, _ = self._load_active_memory()
        layer_counts = {layer: 0 for layer in TTL_BY_LAYER}
        for entry in memories:
            layer = entry.get("layer", DEFAULT_LAYER)
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
        embedding_dim = 0
        for entry in memories:
            vec = entry.get("embedding")
            if isinstance(vec, list):
                embedding_dim = len(vec)
                break
        model_name = None
        if self.embedding_model is not None:
            model_name = getattr(self.embedding_model, "__class__", type(self.embedding_model)).__name__
        embedder_backend = getattr(self.vector_store.embedder, "backend_name", "unknown")
        return {
            "total": len(memories),
            "by_layer": layer_counts,
            "model": model_name or "fallback",
            "vector_backend": getattr(self.vector_store, "backend_name", embedder_backend),
            "embedder_backend": embedder_backend,
            "embedding_dim": embedding_dim,
        }
