"""Bloom Chain adapter that mirrors ledger writes into an append-only log."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class BloomChainAdapter:
    """Simple append-only chain that links ledger events via hashes."""

    def __init__(self, chain_path: str | Path = "artifacts/chain.log") -> None:
        self.chain_path = Path(chain_path)
        self.chain_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._chain: list[Dict[str, Any]] = []
        self._load_existing()

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def record_event(self, category: str, record_id: str, payload: Dict[str, Any]) -> str:
        """Append a block for the given ledger entry and return its hash."""
        with self._lock:
            block = self._build_block(category, record_id, payload)
            self._chain.append(block)
            with self.chain_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(block, sort_keys=True) + "\n")
            return block["hash"]

    def snapshot(self) -> Iterable[Dict[str, Any]]:
        with self._lock:
            return tuple(self._chain)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _load_existing(self) -> None:
        if not self.chain_path.exists():
            return
        with self.chain_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    block = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._chain.append(block)

    def _build_block(self, category: str, record_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        index = len(self._chain)
        prev_hash = self._chain[-1]["hash"] if self._chain else "GENESIS"
        timestamp = time.time()
        data = {
            "type": category,
            "record_id": record_id,
            "data": payload,
            "timestamp": timestamp,
        }
        content = f"{index}|{prev_hash}|{json.dumps(data, sort_keys=True)}".encode("utf-8")
        block_hash = hashlib.sha256(content).hexdigest()
        return {
            "index": index,
            "prev_hash": prev_hash,
            "hash": block_hash,
            "payload": data,
        }
