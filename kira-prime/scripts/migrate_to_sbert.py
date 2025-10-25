#!/usr/bin/env python3
# Optional: to build a FAISS index after migration,
# run: KIRA_VECTOR_BACKEND=faiss python scripts/build_faiss_index.py
# This writes: state/limnus.faiss and state/limnus.faiss.meta.json
"""Migrate Limnus memory entries to include SBERT embeddings and metadata.

Set KIRA_VECTOR_BACKEND=faiss (and optionally KIRA_FAISS_INDEX / KIRA_FAISS_META) before running
to let the script refresh the FAISS index when KIRA_EXPORT_FAISS=1.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
except Exception as exc:  # pragma: no cover - dependency optional
    raise SystemExit(f"sentence-transformers missing: {exc}") from exc


STATE_DIR = Path(__file__).resolve().parents[1] / "state"
MEM_PATH = STATE_DIR / "limnus_memory.json"
TTL_BY_LAYER = {"L1": 3600, "L2": 86400, "L3": None}


def load_memory() -> tuple[list[dict], bool]:
    if not MEM_PATH.exists():
        raise FileNotFoundError(f"No memory file found at {MEM_PATH}")
    raw = json.loads(MEM_PATH.read_text(encoding="utf-8") or "[]")
    if isinstance(raw, dict):
        return list(raw.get("entries", [])), True
    if isinstance(raw, list):
        return list(raw), False
    raise ValueError("Unsupported memory format")


def save_memory(entries: list[dict], wrapped: bool) -> None:
    payload = {"entries": entries} if wrapped else entries
    MEM_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def migrate_memory() -> None:
    entries, wrapped = load_memory()
    if not entries:
        print("No entries to migrate.")
        return

    print(f"Loading SBERT model ({len(entries)} entries)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    changed = False
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        entry.setdefault("layer", "L2")
        ttl = TTL_BY_LAYER.get(entry["layer"].upper(), TTL_BY_LAYER["L2"])
        if entry.get("ttl") != ttl:
            entry["ttl"] = ttl
            changed = True
        entry.setdefault("access_count", 0)
        if "id" not in entry:
            source = entry.get("ts") or entry.get("timestamp") or f"mem_{idx:06d}"
            entry["id"] = f"mem_{str(source)[-8:]}"
            changed = True
        if "tags" not in entry or not isinstance(entry["tags"], list):
            entry["tags"] = []
            changed = True
        if "embedding" not in entry or not isinstance(entry["embedding"], list):
            text = entry.get("text", "")
            if text:
                entry["embedding"] = model.encode(text).tolist()
                entry["vector"] = list(entry["embedding"])
                changed = True
        elif "vector" not in entry or not isinstance(entry["vector"], list):
            entry["vector"] = list(entry["embedding"])
            changed = True

    if changed:
        save_memory(entries, wrapped)
        print(f"✅ Migrated {len(entries)} entries.")
        if os.getenv("KIRA_EXPORT_FAISS"):
            try:
                from memory.vector_store import VectorStore

                backend = os.getenv("KIRA_VECTOR_BACKEND") or "faiss"
                store = VectorStore(backend=backend)
                store.ensure_indexed(entries, text_key="text", id_key="id")
                if store.faiss_index:
                    print(f"[faiss] Refreshed FAISS index at {store.faiss_index.index_path}")
                else:
                    print("[vector-store] Refreshed embeddings without FAISS backend.")
            except Exception as exc:  # pragma: no cover - optional
                print(f"⚠️ Unable to refresh FAISS index: {exc}")
    else:
        print("No changes required.")


if __name__ == "__main__":
    try:
        migrate_memory()
    except FileNotFoundError as exc:
        print(exc)
