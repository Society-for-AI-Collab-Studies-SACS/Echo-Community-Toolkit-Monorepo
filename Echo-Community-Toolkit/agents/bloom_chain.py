"""Bloom Chain adapter: mirrors state ledger entries into an append-only log."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


CHAIN_FILE = Path("artifacts/chain.log")


def _utc_timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class Block:
    index: int
    prev_hash: str
    hash: str
    section: str
    record_id: str
    timestamp: str
    payload: Dict[str, object]


class BloomChainAdapter:
    """Append-only hash chain fed by ledger create events."""

    def __init__(self, path: Path = CHAIN_FILE) -> None:
        self.path = path
        self._lock = threading.RLock()
        self._chain: list[Block] = []
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                block_dict = json.loads(line)
                self._chain.append(Block(**block_dict))

    # ------------------------------------------------------------------ #
    # Public interface                                                   #
    # ------------------------------------------------------------------ #

    def append_event(self, section: str, record_id: str, payload: Dict[str, object]) -> str:
        with self._lock:
            enriched_payload = {
                "type": section,
                "record_id": record_id,
                "data": payload,
            }
            block = self._build_block(section, record_id, enriched_payload)
            self._chain.append(block)
            self._write_block(block)
            return block.hash

    def record_event(self, section: str, record_id: str, payload: Dict[str, object]) -> str:
        """Compatibility shim for legacy JsonStateStore listeners."""
        return self.append_event(section, record_id, payload)

    def verify(self) -> bool:
        prev_hash = "GENESIS"
        for block in self._chain:
            if block.prev_hash != prev_hash:
                return False
            expected = self._compute_hash(block.index, block.prev_hash, block.payload)
            if expected != block.hash:
                return False
            prev_hash = block.hash
        return True

    def blocks(self) -> Iterable[Block]:
        with self._lock:
            return tuple(self._chain)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _build_block(self, section: str, record_id: str, payload: Dict[str, object]) -> Block:
        index = len(self._chain)
        prev_hash = self._chain[-1].hash if self._chain else "GENESIS"
        timestamp = _utc_timestamp()
        block_hash = self._compute_hash(index, prev_hash, payload)
        return Block(
            index=index,
            prev_hash=prev_hash,
            hash=block_hash,
            section=section,
            record_id=record_id,
            timestamp=timestamp,
            payload=payload,
        )

    @staticmethod
    def _compute_hash(
        index: int,
        prev_hash: str,
        payload: Dict[str, object],
    ) -> str:
        message = f"{index}|{prev_hash}|{json.dumps(payload, sort_keys=True)}".encode("utf-8")
        return hashlib.sha256(message).hexdigest()

    def _write_block(self, block: Block) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(block), separators=(",", ":")) + "\n")


_ADAPTER = BloomChainAdapter()


def adapter() -> BloomChainAdapter:
    return _ADAPTER


def register_with_state() -> None:
    # Late import to avoid circular dependency at module import time.
    from . import state

    def listener(section: str, record_id: str, payload: Dict[str, Any]) -> Optional[str]:
        block_hash = _ADAPTER.append_event(section, record_id, payload)
        return block_hash

    state.register_create_listener(listener)


register_with_state()
