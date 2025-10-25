#!/usr/bin/env python3
"""Build a FAISS index from existing Limnus SBERT vectors (optional Phase 2 helper)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np

try:
    import faiss  # type: ignore
except Exception:
    print("FAISS not available. Run `pip install faiss-cpu` on Linux hosts.")
    raise SystemExit(1)


ROOT = Path(__file__).resolve().parents[1]
MEM_PATH = ROOT / "state" / "limnus_memory.json"
INDEX_PATH = Path(os.getenv("KIRA_FAISS_INDEX", ROOT / "state" / "limnus.faiss"))
META_PATH = Path(os.getenv("KIRA_FAISS_META", ROOT / "state" / "limnus.faiss.meta.json"))


def _load_entries() -> List[dict]:
    if not MEM_PATH.exists():
        print(f"No Limnus memory file found at {MEM_PATH}")
        return []
    raw = MEM_PATH.read_text(encoding="utf-8")
    if not raw.strip():
        return []
    data = json.loads(raw)
    if isinstance(data, dict):
        entries = data.get("entries", [])
    elif isinstance(data, list):
        entries = data
    else:
        entries = []
    results: List[dict] = []
    for item in entries:
        if isinstance(item, dict):
            results.append(item)
    return results


def _vectors_and_ids(entries: Iterable[dict]) -> Tuple[np.ndarray, List[str]]:
    vectors: List[np.ndarray] = []
    ids: List[str] = []
    for entry in entries:
        vec = entry.get("vector") or entry.get("embedding")
        entry_id = entry.get("id") or entry.get("ts") or entry.get("timestamp")
        if not entry_id or not isinstance(vec, list):
            continue
        array = np.asarray(vec, dtype="float32")
        if array.ndim != 1:
            continue
        vectors.append(array)
        ids.append(str(entry_id))
    if not vectors:
        return np.zeros((0, 0), dtype="float32"), []
    matrix = np.vstack(vectors).astype("float32")
    return matrix, ids


def main() -> None:
    entries = _load_entries()
    if not entries:
        print("No memory entries available; nothing to index.")
        raise SystemExit(0)
    matrix, ids = _vectors_and_ids(entries)
    if matrix.size == 0:
        print("No vectors found in memory entries.")
        raise SystemExit(0)

    dim = int(matrix.shape[1])
    faiss.normalize_L2(matrix)
    index = faiss.IndexFlatIP(dim)
    index.add(matrix)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps({"ids": ids, "dim": dim}, indent=2), encoding="utf-8")
    print(f"✅ FAISS index written to {INDEX_PATH} ({len(ids)} vectors, dim={dim})")
    print(f"📄 Metadata written to {META_PATH}")


if __name__ == "__main__":
    main()
